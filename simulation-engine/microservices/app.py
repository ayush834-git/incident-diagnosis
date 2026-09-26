"""
Lightweight simulated microservice for the Incident Simulation Engine.
Runs as any service based on SERVICE_NAME environment variable:
- api-gateway (port 8000)
- order-service (port 8001)
- payment-service (port 8002)
- inventory-service (port 8003)
- database (port 8004)
"""
import os
import sys
import time
import uuid
import random
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import httpx
from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel

# ── Configuration ─────────────────────────────────────────────────────────────
SERVICE_NAME = os.getenv("SERVICE_NAME", "api-gateway")
PORT = int(os.getenv("PORT", "8000"))
ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
AUTO_TRAFFIC = os.getenv("AUTO_TRAFFIC", "true").lower() in ("true", "1", "yes")

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8001")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8002")
INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8003")
DATABASE_URL = os.getenv("DATABASE_URL", "http://database:8004")

CURRENT_INCIDENT_ID = os.getenv("INCIDENT_ID", "INC-001")

# Fault injection runtime state
fault_state = {
    "active": False,
    "error_rate": 0.0,
    "latency_ms": 0,
    "cpu_percent": 15.0,
    "memory_percent": 30.0,
    "db_connections_active": 5,
}

# ── Prometheus Metrics ────────────────────────────────────────────────────────
request_counter = Counter(
    "http_requests_total",
    "Total HTTP requests received",
    ["service", "endpoint", "status"]
)
error_counter = Counter(
    "http_errors_total",
    "Total HTTP error responses",
    ["service", "endpoint"]
)
request_rate_gauge = Gauge("http_request_rate", "Current requests per second", ["service"])
error_rate_gauge = Gauge("http_error_rate", "HTTP error rate (0.0 to 1.0)", ["service"])
latency_p99_gauge = Gauge("http_latency_p99_ms", "p99 latency in milliseconds", ["service"])
cpu_gauge = Gauge("service_cpu_percent", "Simulated CPU utilization %", ["service"])
memory_gauge = Gauge("service_memory_percent", "Simulated Memory utilization %", ["service"])
memory_mb_gauge = Gauge("service_memory_mb", "Simulated Memory usage in MB", ["service"])
db_latency_gauge = Gauge("db_query_latency_ms", "Database query latency in milliseconds", ["service"])
db_pool_gauge = Gauge("db_pool_active", "Active DB connections", ["service"])
dependency_health_gauge = Gauge(
    "dependency_health_status",
    "Health status of downstream dependency (1=healthy, 0=degraded)",
    ["service", "dependency"]
)

# Initialize baseline gauges
error_rate_gauge.labels(service=SERVICE_NAME).set(0.002)
latency_p99_gauge.labels(service=SERVICE_NAME).set(45.0)
request_rate_gauge.labels(service=SERVICE_NAME).set(50.0)
cpu_gauge.labels(service=SERVICE_NAME).set(15.0)
memory_gauge.labels(service=SERVICE_NAME).set(30.0)
memory_mb_gauge.labels(service=SERVICE_NAME).set(180.0)
db_latency_gauge.labels(service=SERVICE_NAME).set(12.0)
db_pool_gauge.labels(service=SERVICE_NAME).set(5.0)

# Setup console logger
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(SERVICE_NAME)

# ── ES Telemetry Dispatcher ───────────────────────────────────────────────────
http_client = httpx.AsyncClient(timeout=3.0)


async def send_to_es(index: str, document: Dict[str, Any]):
    """Asynchronously ship log or trace document to Elasticsearch if available."""
    if not ES_HOST:
        return
    try:
        url = f"{ES_HOST}/{index}/_doc"
        await http_client.post(url, json=document)
    except Exception:
        pass  # Never break service path on ES logging failure


def log_event(level: str, message: str, trace_id: Optional[str] = None, span_id: Optional[str] = None):
    """Generate structured JSON log matching the required schema."""
    iso_timestamp = datetime.now(timezone.utc).isoformat()
    log_doc = {
        "timestamp": iso_timestamp,
        "incident_id": CURRENT_INCIDENT_ID,
        "service": SERVICE_NAME,
        "level": level.upper(),
        "message": message,
        "trace_id": trace_id,
        "span_id": span_id,
    }
    # Output to console
    import json
    logger.info(json.dumps(log_doc))

    # Send to Elasticsearch in background
    index_name = f"logs-{CURRENT_INCIDENT_ID.lower()}"
    asyncio.create_task(send_to_es(index_name, log_doc))


async def record_trace_span(
    trace_id: str,
    span_id: str,
    parent_span_id: Optional[str],
    operation: str,
    duration_ms: int,
    status: str,
    start_time: str
):
    """Ship trace span document to Elasticsearch."""
    trace_doc = {
        "incident_id": CURRENT_INCIDENT_ID,
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "service": SERVICE_NAME,
        "operation": operation,
        "duration_ms": duration_ms,
        "status": status,
        "timestamp": start_time,
    }
    index_name = f"traces-{CURRENT_INCIDENT_ID.lower()}"
    await send_to_es(index_name, trace_doc)


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title=f"Microservice: {SERVICE_NAME}")


class FaultPayload(BaseModel):
    error_rate: Optional[float] = None
    latency_ms: Optional[int] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    db_connections_active: Optional[int] = None
    incident_id: Optional[str] = None


@app.get("/health")
def health():
    """Health check endpoint."""
    status = "degraded" if fault_state["active"] and fault_state["error_rate"] > 0.2 else "healthy"
    return {
        "status": status,
        "service": SERVICE_NAME,
        "port": PORT,
        "incident_id": CURRENT_INCIDENT_ID,
        "fault_active": fault_state["active"],
    }


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/fault/inject")
def inject_fault(payload: FaultPayload):
    """Inject faults directly into this microservice instance."""
    global CURRENT_INCIDENT_ID
    fault_state["active"] = True
    if payload.error_rate is not None:
        fault_state["error_rate"] = payload.error_rate
        error_rate_gauge.labels(service=SERVICE_NAME).set(payload.error_rate)
    if payload.latency_ms is not None:
        fault_state["latency_ms"] = payload.latency_ms
        latency_p99_gauge.labels(service=SERVICE_NAME).set(payload.latency_ms)
    if payload.cpu_percent is not None:
        fault_state["cpu_percent"] = payload.cpu_percent
        cpu_gauge.labels(service=SERVICE_NAME).set(payload.cpu_percent)
    if payload.memory_percent is not None:
        fault_state["memory_percent"] = payload.memory_percent
        memory_gauge.labels(service=SERVICE_NAME).set(payload.memory_percent)
        memory_mb_gauge.labels(service=SERVICE_NAME).set(payload.memory_percent * 6.0)
    if payload.db_connections_active is not None:
        fault_state["db_connections_active"] = payload.db_connections_active
        db_pool_gauge.labels(service=SERVICE_NAME).set(payload.db_connections_active)
    if payload.incident_id:
        CURRENT_INCIDENT_ID = payload.incident_id.upper()

    log_event("WARN", f"Fault injected into {SERVICE_NAME}: error_rate={fault_state['error_rate']}, latency={fault_state['latency_ms']}ms")
    return {"status": "injected", "service": SERVICE_NAME, "fault_state": fault_state}


@app.post("/fault/resolve")
def resolve_fault():
    """Reset fault injection state to baseline."""
    fault_state["active"] = False
    fault_state["error_rate"] = 0.002
    fault_state["latency_ms"] = 45
    fault_state["cpu_percent"] = 15.0
    fault_state["memory_percent"] = 30.0
    fault_state["db_connections_active"] = 5

    error_rate_gauge.labels(service=SERVICE_NAME).set(0.002)
    latency_p99_gauge.labels(service=SERVICE_NAME).set(45.0)
    cpu_gauge.labels(service=SERVICE_NAME).set(15.0)
    memory_gauge.labels(service=SERVICE_NAME).set(30.0)
    memory_mb_gauge.labels(service=SERVICE_NAME).set(180.0)
    db_pool_gauge.labels(service=SERVICE_NAME).set(5.0)

    log_event("INFO", f"Fault resolved on {SERVICE_NAME}, baseline restored")
    return {"status": "resolved", "service": SERVICE_NAME}


# ── Downstream Operations ─────────────────────────────────────────────────────

@app.post("/api/v1/orders")
async def api_gateway_order(
    request: Request,
    x_trace_id: Optional[str] = Header(None),
    x_span_id: Optional[str] = Header(None),
):
    """Entrypoint on api-gateway: routes orders to order-service."""
    start_time = datetime.now(timezone.utc).isoformat()
    t0 = time.time()
    trace_id = x_trace_id or f"trace-{uuid.uuid4().hex[:8]}"
    span_id = f"span-gw-{uuid.uuid4().hex[:6]}"

    log_event("INFO", "Order request received", trace_id, span_id)
    request_counter.labels(service=SERVICE_NAME, endpoint="/api/v1/orders", status="received").inc()

    # Apply injected fault if any
    if fault_state["active"] and fault_state["latency_ms"] > 0:
        await asyncio.sleep(fault_state["latency_ms"] / 1000.0)

    try:
        headers = {"X-Trace-Id": trace_id, "X-Parent-Span-Id": span_id}
        resp = await http_client.post(f"{ORDER_SERVICE_URL}/orders", json={"item": "sample-item", "qty": 1}, headers=headers, timeout=10.0)
        duration_ms = int((time.time() - t0) * 1000)

        if resp.status_code == 200:
            status = "OK"
            request_counter.labels(service=SERVICE_NAME, endpoint="/api/v1/orders", status="200").inc()
            dependency_health_gauge.labels(service=SERVICE_NAME, dependency="order-service").set(1.0)
            log_event("INFO", f"api-gateway: order processed successfully in {duration_ms}ms", trace_id, span_id)
        else:
            status = "ERROR"
            error_counter.labels(service=SERVICE_NAME, endpoint="/api/v1/orders").inc()
            dependency_health_gauge.labels(service=SERVICE_NAME, dependency="order-service").set(0.0)
            log_event("ERROR", f"api-gateway: downstream error {resp.status_code}", trace_id, span_id)

        await record_trace_span(trace_id, span_id, None, "POST /api/v1/orders", duration_ms, status, start_time)
        return JSONResponse(status_code=resp.status_code, content=resp.json())

    except Exception as e:
        duration_ms = int((time.time() - t0) * 1000)
        error_counter.labels(service=SERVICE_NAME, endpoint="/api/v1/orders").inc()
        dependency_health_gauge.labels(service=SERVICE_NAME, dependency="order-service").set(0.0)
        log_event("ERROR", f"api-gateway: upstream call failed: {str(e)}", trace_id, span_id)
        await record_trace_span(trace_id, span_id, None, "POST /api/v1/orders", duration_ms, "ERROR", start_time)
        return JSONResponse(status_code=504, content={"error": f"Gateway timeout calling order-service: {str(e)}"})


@app.post("/orders")
async def order_service_process(
    request: Request,
    x_trace_id: Optional[str] = Header(None),
    x_parent_span_id: Optional[str] = Header(None),
):
    """order-service: coordinates payment, inventory, and database."""
    start_time = datetime.now(timezone.utc).isoformat()
    t0 = time.time()
    trace_id = x_trace_id or f"trace-{uuid.uuid4().hex[:8]}"
    span_id = f"span-ord-{uuid.uuid4().hex[:6]}"

    log_event("INFO", "Order request received in order-service", trace_id, span_id)
    request_counter.labels(service=SERVICE_NAME, endpoint="/orders", status="received").inc()

    headers = {"X-Trace-Id": trace_id, "X-Parent-Span-Id": span_id}
    status = "OK"

    try:
        # 1. Call payment-service
        pay_res = await http_client.post(f"{PAYMENT_SERVICE_URL}/charge", json={"amount": 49.99}, headers=headers, timeout=5.0)
        if pay_res.status_code != 200:
            dependency_health_gauge.labels(service=SERVICE_NAME, dependency="payment-service").set(0.0)
            raise RuntimeError(f"Payment failed with code {pay_res.status_code}")
        dependency_health_gauge.labels(service=SERVICE_NAME, dependency="payment-service").set(1.0)

        # 2. Call inventory-service
        inv_res = await http_client.post(f"{INVENTORY_SERVICE_URL}/reserve", json={"item_id": "SKU-99"}, headers=headers, timeout=5.0)
        if inv_res.status_code != 200:
            dependency_health_gauge.labels(service=SERVICE_NAME, dependency="inventory-service").set(0.0)
            raise RuntimeError("Inventory reservation failed")
        dependency_health_gauge.labels(service=SERVICE_NAME, dependency="inventory-service").set(1.0)

        # 3. Call database with latency & timeout checks
        t_db = time.time()
        try:
            db_res = await http_client.post(f"{DATABASE_URL}/query", json={"sql": "INSERT INTO orders VALUES (...)"}, headers=headers, timeout=5.0)
            db_duration = int((time.time() - t_db) * 1000)
            db_latency_gauge.labels(service=SERVICE_NAME).set(db_duration)
            if db_duration > 150:
                log_event("WARN", "Database latency increasing", trace_id, span_id)
            if db_res.status_code != 200:
                log_event("ERROR", "Database query timeout", trace_id, span_id)
                dependency_health_gauge.labels(service=SERVICE_NAME, dependency="database").set(0.0)
                raise RuntimeError("Database query timeout")
            dependency_health_gauge.labels(service=SERVICE_NAME, dependency="database").set(1.0)
        except Exception as dbe:
            dependency_health_gauge.labels(service=SERVICE_NAME, dependency="database").set(0.0)
            log_event("ERROR", "Database query timeout", trace_id, span_id)
            raise RuntimeError(f"Database query timeout: {str(dbe)}")

        duration_ms = int((time.time() - t0) * 1000)
        request_counter.labels(service=SERVICE_NAME, endpoint="/orders", status="200").inc()
        log_event("INFO", f"order-service: workflow completed in {duration_ms}ms", trace_id, span_id)
        await record_trace_span(trace_id, span_id, x_parent_span_id, "processOrder", duration_ms, "OK", start_time)
        return {"status": "success", "order_id": f"ord-{uuid.uuid4().hex[:6]}"}

    except Exception as e:
        duration_ms = int((time.time() - t0) * 1000)
        error_counter.labels(service=SERVICE_NAME, endpoint="/orders").inc()
        log_event("ERROR", f"order-service: workflow failed: {str(e)}", trace_id, span_id)
        await record_trace_span(trace_id, span_id, x_parent_span_id, "processOrder", duration_ms, "ERROR", start_time)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/charge")
async def payment_service_charge(
    request: Request,
    x_trace_id: Optional[str] = Header(None),
    x_parent_span_id: Optional[str] = Header(None),
):
    """payment-service: handles credit card authorization."""
    start_time = datetime.now(timezone.utc).isoformat()
    t0 = time.time()
    trace_id = x_trace_id or f"trace-{uuid.uuid4().hex[:8]}"
    span_id = f"span-pay-{uuid.uuid4().hex[:6]}"

    request_counter.labels(service=SERVICE_NAME, endpoint="/charge", status="received").inc()

    # Simulate injected latency or errors
    if fault_state["active"]:
        if fault_state["latency_ms"] > 0:
            await asyncio.sleep(fault_state["latency_ms"] / 1000.0)
        if random.random() < fault_state["error_rate"]:
            duration_ms = int((time.time() - t0) * 1000)
            error_counter.labels(service=SERVICE_NAME, endpoint="/charge").inc()
            log_event("ERROR", "PaymentGatewayClient: ConnectionTimeout to external gateway", trace_id, span_id)
            await record_trace_span(trace_id, span_id, x_parent_span_id, "chargePayment", duration_ms, "ERROR", start_time)
            return JSONResponse(status_code=504, content={"error": "Payment gateway timeout"})

    # Standard healthy execution
    await asyncio.sleep(0.03)  # 30ms baseline
    duration_ms = int((time.time() - t0) * 1000)
    request_counter.labels(service=SERVICE_NAME, endpoint="/charge", status="200").inc()
    log_event("INFO", f"payment-service: charged payment in {duration_ms}ms", trace_id, span_id)
    await record_trace_span(trace_id, span_id, x_parent_span_id, "chargePayment", duration_ms, "OK", start_time)
    return {"status": "charged", "transaction_id": f"txn-{uuid.uuid4().hex[:6]}"}


@app.post("/reserve")
async def inventory_service_reserve(
    request: Request,
    x_trace_id: Optional[str] = Header(None),
    x_parent_span_id: Optional[str] = Header(None),
):
    """inventory-service: reserves inventory in warehouse."""
    start_time = datetime.now(timezone.utc).isoformat()
    t0 = time.time()
    trace_id = x_trace_id or f"trace-{uuid.uuid4().hex[:8]}"
    span_id = f"span-inv-{uuid.uuid4().hex[:6]}"

    request_counter.labels(service=SERVICE_NAME, endpoint="/reserve", status="received").inc()
    await asyncio.sleep(0.015)  # 15ms baseline
    duration_ms = int((time.time() - t0) * 1000)

    request_counter.labels(service=SERVICE_NAME, endpoint="/reserve", status="200").inc()
    log_event("INFO", f"inventory-service: item SKU-99 reserved ({duration_ms}ms)", trace_id, span_id)
    await record_trace_span(trace_id, span_id, x_parent_span_id, "reserveInventory", duration_ms, "OK", start_time)
    return {"status": "reserved", "sku": "SKU-99"}


@app.post("/query")
async def database_query(
    request: Request,
    x_trace_id: Optional[str] = Header(None),
    x_parent_span_id: Optional[str] = Header(None),
):
    """database: simulates SQL query execution."""
    start_time = datetime.now(timezone.utc).isoformat()
    t0 = time.time()
    trace_id = x_trace_id or f"trace-{uuid.uuid4().hex[:8]}"
    span_id = f"span-db-{uuid.uuid4().hex[:6]}"

    request_counter.labels(service=SERVICE_NAME, endpoint="/query", status="received").inc()

    # Simulate injected database degradation if active
    if fault_state["active"]:
        if fault_state["latency_ms"] > 100:
            log_event("WARN", "Database latency increasing", trace_id, span_id)
            await asyncio.sleep(fault_state["latency_ms"] / 1000.0)
        if random.random() < fault_state["error_rate"]:
            error_counter.labels(service=SERVICE_NAME, endpoint="/query").inc()
            log_event("ERROR", "Database query timeout", trace_id, span_id)
            duration_ms = int((time.time() - t0) * 1000)
            await record_trace_span(trace_id, span_id, x_parent_span_id, "sqlExecute", duration_ms, "ERROR", start_time)
            return JSONResponse(status_code=504, content={"error": "Database query timeout"})

    await asyncio.sleep(0.01)  # 10ms baseline query
    duration_ms = int((time.time() - t0) * 1000)

    request_counter.labels(service=SERVICE_NAME, endpoint="/query", status="200").inc()
    log_event("INFO", f"database: query executed successfully ({duration_ms}ms)", trace_id, span_id)
    await record_trace_span(trace_id, span_id, x_parent_span_id, "sqlExecute", duration_ms, "OK", start_time)
    return {"status": "ok", "rows_affected": 1}


# ── Background Synthetic Traffic Generator ────────────────────────────────────
async def generate_synthetic_traffic():
    """Background task for api-gateway to periodically simulate realistic traffic."""
    if SERVICE_NAME != "api-gateway" or not AUTO_TRAFFIC:
        return

    logger.info("Starting background synthetic traffic generator on api-gateway...")
    await asyncio.sleep(5.0)  # Wait for services to initialize

    while True:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(f"http://127.0.0.1:{PORT}/api/v1/orders", json={"synthetic": True})
        except Exception as e:
            logger.debug(f"Synthetic traffic tick error: {e}")
        await asyncio.sleep(random.uniform(3.0, 6.0))


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(generate_synthetic_traffic())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
