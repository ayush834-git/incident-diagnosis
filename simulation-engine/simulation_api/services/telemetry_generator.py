"""
Telemetry Generation Layer for the Simulation Engine.
Generates realistic, fully correlated observability data:
- Structured Logs
- Distributed Traces
- Multi-dimensional Metrics
- Deployment Events
- Service Dependency Metadata

Rules:
- Correlated by incident_id, timestamp, service, and trace_id.
- Evidence-based: provides factual observations and symptoms, NOT explicit root-cause statements.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


def get_scenario_telemetry(scenario_id: str) -> Dict[str, Any]:
    """Generate or retrieve complete correlated telemetry package for a scenario."""
    sid = scenario_id.upper()
    if sid == "INC-001":
        return _telemetry_inc_001()
    elif sid == "INC-002":
        return _telemetry_inc_002()
    elif sid == "INC-003":
        return _telemetry_inc_003()
    elif sid == "INC-004":
        return _telemetry_inc_004()
    else:
        return _telemetry_generic(sid)


# ── Scenario INC-001: Deployment Regression ──────────────────────────────────
def _telemetry_inc_001() -> Dict[str, Any]:
    incident_id = "INC-001"
    deployments = [
        {
            "deployment_id": "DEP-INC-001",
            "incident_id": incident_id,
            "service": "order-service",
            "version": "v1.1.0",
            "previous_version": "v1.0.0",
            "commit": "a1b2c3d4e5f6",
            "timestamp": "2026-09-26T10:00:00Z",
            "deployed_at": "2026-09-26T10:00:00Z",
            "change_description": "Order repository refactoring for checkout history retrieval and connection pool tuning",
            "changes": [
                "Refactored order history query to perform unindexed table join",
                "Adjusted DB connection pool size to 50"
            ],
            "rollback_safe": True,
            "deployer": "ci-pipeline",
            "health_status_before": "healthy"
        }
    ]

    service_dependencies = {
        "api-gateway": ["order-service"],
        "order-service": ["database", "payment-service", "inventory-service"]
    }

    logs = [
        {"timestamp": "2026-09-26T09:50:00Z", "incident_id": incident_id, "service": "order-service", "level": "INFO",  "message": "order-service initialized version v1.0.0", "trace_id": None, "span_id": None, "version": "v1.0.0"},
        {"timestamp": "2026-09-26T09:52:10Z", "incident_id": incident_id, "service": "order-service", "level": "INFO",  "message": "Order request received for cart-101", "trace_id": "trace-001", "span_id": "span-ord-001", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T09:52:10Z", "incident_id": incident_id, "service": "database",      "level": "INFO",  "message": "database: query executed successfully (12ms)", "trace_id": "trace-001", "span_id": "span-db-001", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T09:52:10Z", "incident_id": incident_id, "service": "order-service", "level": "INFO",  "message": "order-service: workflow completed in 45ms", "trace_id": "trace-001", "span_id": "span-ord-001", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T09:55:00Z", "incident_id": incident_id, "service": "api-gateway",    "level": "INFO",  "message": "Order request received for cart-102", "trace_id": "trace-000", "span_id": "span-gw-000", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T09:55:00Z", "incident_id": incident_id, "service": "order-service", "level": "INFO",  "message": "order-service: workflow completed in 42ms", "trace_id": "trace-000", "span_id": "span-ord-000", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T10:00:05Z", "incident_id": incident_id, "service": "order-service", "level": "INFO",  "message": "Deployment v1.1.0 started. Rolling out new version.", "trace_id": None, "span_id": None, "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:00:18Z", "incident_id": incident_id, "service": "order-service", "level": "INFO",  "message": "Deployment v1.1.0 complete. Service healthy. Traffic shifted.", "trace_id": None, "span_id": None, "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:02:15Z", "incident_id": incident_id, "service": "order-service", "level": "INFO",  "message": "Order request received for cart-5402", "trace_id": "trace-002", "span_id": "span-ord-002", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:03:30Z", "incident_id": incident_id, "service": "order-service", "level": "WARN",  "message": "Database latency increasing: query execution took 850ms (threshold: 100ms)", "trace_id": "trace-002", "span_id": "span-ord-002", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:04:10Z", "incident_id": incident_id, "service": "order-service", "level": "WARN",  "message": "Database connection pool saturated: 48/50 active connections", "trace_id": "trace-002", "span_id": "span-ord-002", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:04:45Z", "incident_id": incident_id, "service": "order-service", "level": "ERROR", "message": "Database query timeout: SELECT orders join failed to return within 5000ms", "trace_id": "trace-003", "span_id": "span-ord-003", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:05:00Z", "incident_id": incident_id, "service": "order-service", "level": "ERROR", "message": "order-service: workflow failed: Database query timeout", "trace_id": "trace-003", "span_id": "span-ord-003", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:05:05Z", "incident_id": incident_id, "service": "api-gateway",    "level": "ERROR", "message": "Upstream order-service returned 504 Gateway Timeout", "trace_id": "trace-003", "span_id": "span-gw-003", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T10:05:30Z", "incident_id": incident_id, "service": "order-service", "level": "ERROR", "message": "Database query timeout: Connection acquisition timed out after 5000ms", "trace_id": "trace-004", "span_id": "span-ord-004", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:05:40Z", "incident_id": incident_id, "service": "order-service", "level": "ERROR", "message": "HTTP 500 Internal Server Error: Failed to process order due to database timeout", "trace_id": "trace-004", "span_id": "span-ord-004", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:05:45Z", "incident_id": incident_id, "service": "api-gateway",    "level": "ERROR", "message": "order-service returned HTTP 500: Internal Server Error", "trace_id": "trace-004", "span_id": "span-gw-004", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T10:06:00Z", "incident_id": incident_id, "service": "order-service", "level": "WARN",  "message": "order-service p99 latency spiked to 2400ms (baseline: 45ms)", "trace_id": None, "span_id": None, "version": "v1.1.0"},
        {"timestamp": "2026-09-26T10:07:00Z", "incident_id": incident_id, "service": "api-gateway",    "level": "CRITICAL", "message": "P1 Incident Declared: order-service error rate 28% exceeds critical threshold", "trace_id": None, "span_id": None, "version": "v1.0.0"}
    ]

    traces = [
        {"incident_id": incident_id, "trace_id": "trace-001", "span_id": "span-gw-001",  "parent_span_id": None,          "service": "api-gateway",   "operation": "POST /api/v1/orders", "duration_ms": 48,   "status": "OK",    "timestamp": "2026-09-26T09:52:10Z", "start_time": "2026-09-26T09:52:10Z"},
        {"incident_id": incident_id, "trace_id": "trace-001", "span_id": "span-ord-001", "parent_span_id": "span-gw-001",  "service": "order-service", "operation": "processOrder",        "duration_ms": 45,   "status": "OK",    "timestamp": "2026-09-26T09:52:10Z", "start_time": "2026-09-26T09:52:10Z"},
        {"incident_id": incident_id, "trace_id": "trace-001", "span_id": "span-db-001",  "parent_span_id": "span-ord-001", "service": "database",      "operation": "sqlExecute",          "duration_ms": 12,   "status": "OK",    "timestamp": "2026-09-26T09:52:10Z", "start_time": "2026-09-26T09:52:10Z"},
        {"incident_id": incident_id, "trace_id": "trace-002", "span_id": "span-gw-002",  "parent_span_id": None,          "service": "api-gateway",   "operation": "POST /api/v1/orders", "duration_ms": 2450, "status": "SLOW",  "timestamp": "2026-09-26T10:02:15Z", "start_time": "2026-09-26T10:02:15Z"},
        {"incident_id": incident_id, "trace_id": "trace-002", "span_id": "span-ord-002", "parent_span_id": "span-gw-002",  "service": "order-service", "operation": "processOrder",        "duration_ms": 2420, "status": "SLOW",  "timestamp": "2026-09-26T10:02:15Z", "start_time": "2026-09-26T10:02:15Z"},
        {"incident_id": incident_id, "trace_id": "trace-002", "span_id": "span-db-002",  "parent_span_id": "span-ord-002", "service": "database",      "operation": "sqlExecute",          "duration_ms": 2350, "status": "SLOW",  "timestamp": "2026-09-26T10:02:15Z", "start_time": "2026-09-26T10:02:15Z"},
        {"incident_id": incident_id, "trace_id": "trace-003", "span_id": "span-gw-003",  "parent_span_id": None,          "service": "api-gateway",   "operation": "POST /api/v1/orders", "duration_ms": 5100, "status": "ERROR", "timestamp": "2026-09-26T10:04:45Z", "start_time": "2026-09-26T10:04:45Z"},
        {"incident_id": incident_id, "trace_id": "trace-003", "span_id": "span-ord-003", "parent_span_id": "span-gw-003",  "service": "order-service", "operation": "processOrder",        "duration_ms": 5080, "status": "ERROR", "timestamp": "2026-09-26T10:04:45Z", "start_time": "2026-09-26T10:04:45Z"},
        {"incident_id": incident_id, "trace_id": "trace-003", "span_id": "span-db-003",  "parent_span_id": "span-ord-003", "service": "database",      "operation": "sqlExecute",          "duration_ms": 5000, "status": "ERROR", "timestamp": "2026-09-26T10:04:45Z", "start_time": "2026-09-26T10:04:45Z"}
    ]

    metrics = {
        "order-service": {"error_rate": 0.28, "p99_latency_ms": 2400, "request_rate": 350, "cpu_percent": 74, "memory_percent": 65, "db_latency_ms": 2200, "db_connections_active": 48},
        "api-gateway":   {"error_rate": 0.15, "p99_latency_ms": 2600, "request_rate": 750, "cpu_percent": 42, "memory_percent": 40, "db_latency_ms": 0,    "db_connections_active": 0},
        "database":      {"error_rate": 0.25, "p99_latency_ms": 2350, "request_rate": 350, "cpu_percent": 85, "memory_percent": 70, "db_latency_ms": 2200, "db_connections_active": 48}
    }

    return {
        "incident_id": incident_id,
        "deployments": deployments,
        "service_dependencies": service_dependencies,
        "logs": logs,
        "traces": traces,
        "metrics_snapshot": metrics
    }


# ── Scenario INC-002: DB Schema Migration ─────────────────────────────────────
def _telemetry_inc_002() -> Dict[str, Any]:
    incident_id = "INC-002"
    deployments = [
        {
            "deployment_id": "DEP-INC-002",
            "incident_id": incident_id,
            "service": "order-service",
            "version": "v2.0.0",
            "previous_version": "v1.1.0",
            "commit": "c4d5e6f7a8b9",
            "timestamp": "2026-09-26T09:00:00Z",
            "deployed_at": "2026-09-26T09:00:00Z",
            "change_description": "Database schema migration: added NOT NULL column tax_code to orders table and updated order creation repository",
            "changes": [
                "Database schema migration: ALTER TABLE orders ADD COLUMN tax_code VARCHAR NOT NULL",
                "Added tax calculation and validation to checkout flow",
                "Updated OrderRepository to persist tax_code on order placement"
            ],
            "rollback_safe": False,
            "deployer": "ci-pipeline",
            "health_status_before": "healthy"
        }
    ]

    service_dependencies = {
        "api-gateway": ["order-service"],
        "order-service": ["database", "payment-service", "inventory-service"]
    }

    logs = [
        {"timestamp": "2026-09-26T09:00:05Z", "incident_id": incident_id, "service": "order-service", "level": "INFO",  "message": "Deployment v2.0.0 started. Running database migrations.", "trace_id": None, "span_id": None, "version": "v2.0.0"},
        {"timestamp": "2026-09-26T09:02:10Z", "incident_id": incident_id, "service": "database",      "level": "INFO",  "message": "Migration complete: ALTER TABLE orders ADD COLUMN tax_code VARCHAR NOT NULL.", "trace_id": None, "span_id": None, "version": "v2.0.0"},
        {"timestamp": "2026-09-26T09:02:30Z", "incident_id": incident_id, "service": "order-service", "level": "INFO",  "message": "Deployment v2.0.0 complete. Health check passed.", "trace_id": None, "span_id": None, "version": "v2.0.0"},
        {"timestamp": "2026-09-26T09:12:00Z", "incident_id": incident_id, "service": "order-service", "level": "WARN",  "message": "Database latency increasing: query execution average 480ms (baseline: 12ms)", "trace_id": "trace-m001", "span_id": "span-ord-m01", "version": "v2.0.0"},
        {"timestamp": "2026-09-26T09:14:20Z", "incident_id": incident_id, "service": "database",      "level": "WARN",  "message": "Exclusive lock acquired on table orders during index build; transactions queued", "trace_id": "trace-m001", "span_id": "span-db-m01", "version": "v2.0.0"},
        {"timestamp": "2026-09-26T09:15:10Z", "incident_id": incident_id, "service": "order-service", "level": "ERROR", "message": "Database query timeout: INSERT INTO orders failed to acquire lock within 3000ms", "trace_id": "trace-m001", "span_id": "span-ord-m01", "version": "v2.0.0"},
        {"timestamp": "2026-09-26T09:15:45Z", "incident_id": incident_id, "service": "database",      "level": "ERROR", "message": "DBConstraintError: null value in column 'tax_code' violates not-null constraint on orders", "trace_id": "trace-m002", "span_id": "span-db-m02", "version": "v2.0.0"},
        {"timestamp": "2026-09-26T09:16:00Z", "incident_id": incident_id, "service": "order-service", "level": "ERROR", "message": "HTTP 500: Failed to persist order due to database constraint violation", "trace_id": "trace-m002", "span_id": "span-ord-m02", "version": "v2.0.0"},
        {"timestamp": "2026-09-26T09:16:30Z", "incident_id": incident_id, "service": "api-gateway",    "level": "ERROR", "message": "order-service upstream call failed with status 500", "trace_id": "trace-m002", "span_id": "span-gw-m02", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T09:18:00Z", "incident_id": incident_id, "service": "order-service", "level": "WARN",  "message": "order-service p99 latency spiked to 1250ms (baseline: 45ms)", "trace_id": None, "span_id": None, "version": "v2.0.0"},
        {"timestamp": "2026-09-26T09:20:00Z", "incident_id": incident_id, "service": "api-gateway",    "level": "CRITICAL", "message": "P1 Incident Declared: checkout failure rate at 18% following database migration", "trace_id": None, "span_id": None, "version": "v1.0.0"}
    ]

    traces = [
        {"incident_id": incident_id, "trace_id": "trace-m001", "span_id": "span-gw-m01",  "parent_span_id": None,           "service": "api-gateway",   "operation": "POST /api/v1/orders", "duration_ms": 1600, "status": "ERROR", "timestamp": "2026-09-26T09:15:08Z", "start_time": "2026-09-26T09:15:08Z"},
        {"incident_id": incident_id, "trace_id": "trace-m001", "span_id": "span-ord-m01", "parent_span_id": "span-gw-m01",   "service": "order-service", "operation": "processOrder",        "duration_ms": 1580, "status": "ERROR", "timestamp": "2026-09-26T09:15:08Z", "start_time": "2026-09-26T09:15:08Z"},
        {"incident_id": incident_id, "trace_id": "trace-m001", "span_id": "span-db-m01",  "parent_span_id": "span-ord-m01",  "service": "database",      "operation": "INSERT INTO orders",   "duration_ms": 1500, "status": "ERROR", "timestamp": "2026-09-26T09:15:09Z", "start_time": "2026-09-26T09:15:09Z"},
        {"incident_id": incident_id, "trace_id": "trace-m002", "span_id": "span-gw-m02",  "parent_span_id": None,           "service": "api-gateway",   "operation": "POST /api/v1/orders", "duration_ms": 850,  "status": "ERROR", "timestamp": "2026-09-26T09:15:44Z", "start_time": "2026-09-26T09:15:44Z"},
        {"incident_id": incident_id, "trace_id": "trace-m002", "span_id": "span-ord-m02", "parent_span_id": "span-gw-m02",   "service": "order-service", "operation": "processOrder",        "duration_ms": 840,  "status": "ERROR", "timestamp": "2026-09-26T09:15:44Z", "start_time": "2026-09-26T09:15:44Z"},
        {"incident_id": incident_id, "trace_id": "trace-m002", "span_id": "span-db-m02",  "parent_span_id": "span-ord-m02",  "service": "database",      "operation": "INSERT INTO orders",   "duration_ms": 800,  "status": "ERROR", "timestamp": "2026-09-26T09:15:45Z", "start_time": "2026-09-26T09:15:45Z"}
    ]

    metrics = {
        "order-service": {"error_rate": 0.18, "p99_latency_ms": 1250, "request_rate": 340, "cpu_percent": 45, "memory_percent": 52, "db_latency_ms": 850, "db_connections_active": 46},
        "api-gateway":   {"error_rate": 0.08, "p99_latency_ms": 1350, "request_rate": 820, "cpu_percent": 36, "memory_percent": 40, "db_latency_ms": 0,   "db_connections_active": 0},
        "database":      {"error_rate": 0.18, "p99_latency_ms": 1200, "request_rate": 340, "cpu_percent": 68, "memory_percent": 62, "db_latency_ms": 850, "db_connections_active": 46}
    }

    return {
        "incident_id": incident_id,
        "deployments": deployments,
        "service_dependencies": service_dependencies,
        "logs": logs,
        "traces": traces,
        "metrics_snapshot": metrics
    }


# ── Scenario INC-003: Dependency Cascade ──────────────────────────────────────
def _telemetry_inc_003() -> Dict[str, Any]:
    incident_id = "INC-003"
    deployments: List[Dict[str, Any]] = []

    service_dependencies = {
        "api-gateway": ["order-service"],
        "order-service": ["payment-service", "database", "inventory-service"],
        "payment-service": ["external-payment-gateway"]
    }

    logs = [
        {"timestamp": "2026-09-26T10:58:00Z", "incident_id": incident_id, "service": "api-gateway",     "level": "INFO",  "message": "Order request received for cart-901", "trace_id": "trace-c001", "span_id": "span-gw-c01", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T10:58:00Z", "incident_id": incident_id, "service": "order-service",   "level": "INFO",  "message": "order-service: workflow completed in 45ms", "trace_id": "trace-c001", "span_id": "span-ord-c01", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T11:00:05Z", "incident_id": incident_id, "service": "payment-service", "level": "WARN",  "message": "Payment processing latency increasing: upstream payment authorization took 4200ms", "trace_id": "trace-c002", "span_id": "span-pay-c02", "version": "v41"},
        {"timestamp": "2026-09-26T11:00:30Z", "incident_id": incident_id, "service": "payment-service", "level": "WARN",  "message": "Payment gateway slow: 8200ms — retry attempt 1 of 3", "trace_id": "trace-c002", "span_id": "span-pay-c02", "version": "v41"},
        {"timestamp": "2026-09-26T11:01:00Z", "incident_id": incident_id, "service": "payment-service", "level": "ERROR", "message": "Payment authorization timeout after 15000ms: retries exhausted", "trace_id": "trace-c002", "span_id": "span-pay-c02", "version": "v41"},
        {"timestamp": "2026-09-26T11:02:00Z", "incident_id": incident_id, "service": "payment-service", "level": "ERROR", "message": "Thread pool saturated: 96/100 active connections waiting on payment gateway", "trace_id": None, "span_id": None, "version": "v41"},
        {"timestamp": "2026-09-26T11:03:00Z", "incident_id": incident_id, "service": "order-service",   "level": "WARN",  "message": "payment-service dependency latency high: request took 5020ms", "trace_id": "trace-c002", "span_id": "span-ord-c02", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T11:03:30Z", "incident_id": incident_id, "service": "payment-service", "level": "WARN",  "message": "Circuit breaker approaching trip threshold: failure rate 38% exceeds warning level 25%", "trace_id": None, "span_id": None, "version": "v41"},
        {"timestamp": "2026-09-26T11:04:00Z", "incident_id": incident_id, "service": "payment-service", "level": "CRITICAL", "message": "Circuit breaker OPEN on payment-service: failing fast to isolate downstream failure", "trace_id": None, "span_id": None, "version": "v41"},
        {"timestamp": "2026-09-26T11:04:15Z", "incident_id": incident_id, "service": "order-service",   "level": "ERROR", "message": "Downstream payment-service timed out: charge request failed after 5000ms", "trace_id": "trace-c002", "span_id": "span-ord-c02", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T11:04:30Z", "incident_id": incident_id, "service": "order-service",   "level": "ERROR", "message": "Cannot process orders: payment-service circuit breaker open — returning 503", "trace_id": "trace-c003", "span_id": "span-ord-c03", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T11:05:00Z", "incident_id": incident_id, "service": "api-gateway",     "level": "WARN",  "message": "order-service response time degraded: 5120ms", "trace_id": "trace-c002", "span_id": "span-gw-c02", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T11:05:30Z", "incident_id": incident_id, "service": "api-gateway",     "level": "ERROR", "message": "api-gateway: upstream order-service returned 504 Gateway Timeout", "trace_id": "trace-c002", "span_id": "span-gw-c02", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T11:06:00Z", "incident_id": incident_id, "service": "api-gateway",     "level": "ERROR", "message": "order-service returning 503: payment dependency unavailable", "trace_id": "trace-c003", "span_id": "span-gw-c03", "version": "v1.0.0"},
        {"timestamp": "2026-09-26T11:08:00Z", "incident_id": incident_id, "service": "api-gateway",     "level": "CRITICAL", "message": "P1 Incident Declared: 35% checkout failure rate cascading across services", "trace_id": None, "span_id": None, "version": "v1.0.0"}
    ]

    traces = [
        {"incident_id": incident_id, "trace_id": "trace-c001", "span_id": "span-gw-c01",  "parent_span_id": None,          "service": "api-gateway",     "operation": "POST /api/v1/orders", "duration_ms": 48,   "status": "OK",    "timestamp": "2026-09-26T10:58:00Z", "start_time": "2026-09-26T10:58:00Z"},
        {"incident_id": incident_id, "trace_id": "trace-c001", "span_id": "span-ord-c01", "parent_span_id": "span-gw-c01",  "service": "order-service",   "operation": "processOrder",        "duration_ms": 45,   "status": "OK",    "timestamp": "2026-09-26T10:58:00Z", "start_time": "2026-09-26T10:58:00Z"},
        {"incident_id": incident_id, "trace_id": "trace-c001", "span_id": "span-pay-c01", "parent_span_id": "span-ord-c01", "service": "payment-service", "operation": "chargePayment",       "duration_ms": 30,   "status": "OK",    "timestamp": "2026-09-26T10:58:00Z", "start_time": "2026-09-26T10:58:00Z"},
        {"incident_id": incident_id, "trace_id": "trace-c002", "span_id": "span-gw-c02",  "parent_span_id": None,          "service": "api-gateway",     "operation": "POST /api/v1/orders", "duration_ms": 5150, "status": "ERROR", "timestamp": "2026-09-26T11:04:10Z", "start_time": "2026-09-26T11:04:10Z"},
        {"incident_id": incident_id, "trace_id": "trace-c002", "span_id": "span-ord-c02", "parent_span_id": "span-gw-c02",  "service": "order-service",   "operation": "processOrder",        "duration_ms": 5120, "status": "ERROR", "timestamp": "2026-09-26T11:04:10Z", "start_time": "2026-09-26T11:04:10Z"},
        {"incident_id": incident_id, "trace_id": "trace-c002", "span_id": "span-pay-c02", "parent_span_id": "span-ord-c02", "service": "payment-service", "operation": "chargePayment",       "duration_ms": 5000, "status": "ERROR", "timestamp": "2026-09-26T11:04:10Z", "start_time": "2026-09-26T11:04:10Z"},
        {"incident_id": incident_id, "trace_id": "trace-c003", "span_id": "span-gw-c03",  "parent_span_id": None,          "service": "api-gateway",     "operation": "POST /api/v1/orders", "duration_ms": 120,  "status": "ERROR", "timestamp": "2026-09-26T11:06:00Z", "start_time": "2026-09-26T11:06:00Z"},
        {"incident_id": incident_id, "trace_id": "trace-c003", "span_id": "span-ord-c03", "parent_span_id": "span-gw-c03",  "service": "order-service",   "operation": "processOrder",        "duration_ms": 115,  "status": "ERROR", "timestamp": "2026-09-26T11:06:00Z", "start_time": "2026-09-26T11:06:00Z"},
        {"incident_id": incident_id, "trace_id": "trace-c003", "span_id": "span-pay-c03", "parent_span_id": "span-ord-c03", "service": "payment-service", "operation": "chargePayment",       "duration_ms": 5,    "status": "ERROR", "timestamp": "2026-09-26T11:06:00Z", "start_time": "2026-09-26T11:06:00Z"}
    ]

    metrics = {
        "payment-service": {"error_rate": 0.45, "p99_latency_ms": 5000, "request_rate": 400, "cpu_percent": 88, "memory_percent": 75, "db_latency_ms": 15, "db_connections_active": 95},
        "order-service":   {"error_rate": 0.32, "p99_latency_ms": 5150, "request_rate": 410, "cpu_percent": 72, "memory_percent": 60, "db_latency_ms": 14, "db_connections_active": 22},
        "api-gateway":     {"error_rate": 0.25, "p99_latency_ms": 5200, "request_rate": 850, "cpu_percent": 58, "memory_percent": 45, "db_latency_ms": 0,  "db_connections_active": 0}
    }

    return {
        "incident_id": incident_id,
        "deployments": deployments,
        "service_dependencies": service_dependencies,
        "logs": logs,
        "traces": traces,
        "metrics_snapshot": metrics
    }


# ── Scenario INC-004: Insufficient Evidence ───────────────────────────────────
def _telemetry_inc_004() -> Dict[str, Any]:
    incident_id = "INC-004"
    deployments = [
        {
            "deployment_id": "dep-bot-882",
            "service": "api-gateway",
            "version": "v1.1.2-patch",
            "previous_version": "v1.1.1",
            "deployed_at": "2026-09-26T00:30:00Z",
            "deployer": "auto-rebase-bot",
            "change_description": "Routine security dependency updates and container base image rebuild",
            "rollback_safe": False
        }
    ]

    service_dependencies = {
        "api-gateway": ["order-service"],
        "order-service": ["payment-service", "database"]
    }

    # Ambiguous, low-volume, multi-service logs without a clear dominant root cause
    logs = [
        {"timestamp": "2026-09-26T14:00:12Z", "incident_id": incident_id, "service": "api-gateway",     "level": "ERROR", "message": "502 Bad Gateway: upstream connection reset by peer (errno 104 ECONNRESET)", "trace_id": "trace-s001", "span_id": "span-gw-s01", "version": "v1.1.2-patch"},
        {"timestamp": "2026-09-26T14:01:45Z", "incident_id": incident_id, "service": "order-service",   "level": "WARN",  "message": "Transient client abort: Connection reset by peer during payload stream", "trace_id": "trace-s002", "span_id": "span-ord-s02", "version": "v1.1.0"},
        {"timestamp": "2026-09-26T14:03:10Z", "incident_id": incident_id, "service": "payment-service", "level": "INFO",  "message": "JVM GC pause [young gen]: 142ms; memory pressure normal at 35%", "trace_id": None, "span_id": None, "version": "v41"},
        {"timestamp": "2026-09-26T14:05:30Z", "incident_id": incident_id, "service": "database",        "level": "INFO",  "message": "Query performance notice: SELECT FROM schema_migrations took 120ms (normal variance)", "trace_id": None, "span_id": None, "version": "v14"},
        {"timestamp": "2026-09-26T14:08:22Z", "incident_id": incident_id, "service": "api-gateway",     "level": "ERROR", "message": "502 Bad Gateway: upstream connection reset by peer (errno 104 ECONNRESET)", "trace_id": "trace-s003", "span_id": "span-gw-s03", "version": "v1.1.2-patch"},
        {"timestamp": "2026-09-26T14:10:00Z", "incident_id": incident_id, "service": "api-gateway",     "level": "INFO",  "message": "Cluster health check: 4/4 pods reporting 200 OK; error rate currently 0.9%", "trace_id": None, "span_id": None, "version": "v1.1.2-patch"}
    ]

    # Incomplete traces: missing parent or child spans, un-instrumented hops
    traces = [
        {"incident_id": incident_id, "trace_id": "trace-s001", "span_id": "span-gw-s01",  "parent_span_id": None,                 "service": "api-gateway",   "operation": "POST /api/v1/orders", "duration_ms": 18, "status": "ERROR", "timestamp": "2026-09-26T14:00:12Z", "start_time": "2026-09-26T14:00:12Z"},
        {"incident_id": incident_id, "trace_id": "trace-s002", "span_id": "span-ord-s02", "parent_span_id": "span-orphan-dropped", "service": "order-service", "operation": "processOrder",        "duration_ms": 22, "status": "ERROR", "timestamp": "2026-09-26T14:01:45Z", "start_time": "2026-09-26T14:01:45Z"},
        {"incident_id": incident_id, "trace_id": "trace-s003", "span_id": "span-gw-s03",  "parent_span_id": None,                 "service": "api-gateway",   "operation": "GET /api/v1/health",  "duration_ms": 14, "status": "ERROR", "timestamp": "2026-09-26T14:08:22Z", "start_time": "2026-09-26T14:08:22Z"}
    ]

    # Mild metrics without clear spikes: error rates under 1.2%, p99 latency normal
    metrics = {
        "api-gateway":     {"error_rate": 0.012, "p99_latency_ms": 145, "request_rate": 890, "cpu_percent": 28, "memory_percent": 32, "db_latency_ms": 0,  "db_connections_active": 0},
        "order-service":   {"error_rate": 0.008, "p99_latency_ms": 110, "request_rate": 460, "cpu_percent": 26, "memory_percent": 34, "db_latency_ms": 12, "db_connections_active": 18},
        "payment-service": {"error_rate": 0.004, "p99_latency_ms": 95,  "request_rate": 440, "cpu_percent": 31, "memory_percent": 35, "db_latency_ms": 11, "db_connections_active": 15},
        "database":        {"error_rate": 0.000, "p99_latency_ms": 18,  "request_rate": 400, "cpu_percent": 22, "memory_percent": 42, "db_latency_ms": 14, "db_connections_active": 20}
    }

    return {
        "incident_id": incident_id,
        "deployments": deployments,
        "service_dependencies": service_dependencies,
        "logs": logs,
        "traces": traces,
        "metrics_snapshot": metrics,
        "additional_evidence_available": True,
        "evidence_request_instructions": "Telemetry is insufficient. Reasoning Engine should recommend 'investigate_further' and request diagnostic data via POST /scenarios/INC-004/request-evidence."
    }


def get_additional_evidence_inc_004(evidence_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Simulates additional diagnostic evidence becoming available after an explicit request.
    Reveals the underlying MTU / network packet drop issue without requiring guessing.
    """
    diagnostic_logs = [
        {
            "timestamp": "2026-09-26T14:16:00Z",
            "incident_id": "INC-004",
            "service": "kernel-ebpf",
            "level": "WARN",
            "message": "NET_DEV_XMIT: packet length 8420 exceeds path MTU 1500; ICMP Type 3 Code 4 (Fragmentation Needed) dropped by intermediate firewall",
            "trace_id": "trace-s001",
            "span_id": "span-kernel-01",
            "version": "v1.1.2-patch"
        },
        {
            "timestamp": "2026-09-26T14:16:05Z",
            "incident_id": "INC-004",
            "service": "cloud-load-balancer",
            "level": "ERROR",
            "message": "ALB ingress: client TCP reset on MTU blackhole at router hop 10.0.12.1 — Path MTU Discovery failed",
            "trace_id": "trace-s001",
            "span_id": "span-alb-01",
            "version": "alb-v2"
        }
    ]

    diagnostic_traces = [
        {
            "incident_id": "INC-004",
            "trace_id": "trace-s001",
            "span_id": "span-alb-01",
            "parent_span_id": None,
            "service": "cloud-load-balancer",
            "operation": "FORWARD /api/v1/orders",
            "duration_ms": 19,
            "status": "ERROR",
            "timestamp": "2026-09-26T14:00:12Z",
            "start_time": "2026-09-26T14:00:12Z",
            "error_reason": "TCP RST received: MTU blackhole"
        },
        {
            "incident_id": "INC-004",
            "trace_id": "trace-s001",
            "span_id": "span-gw-s01",
            "parent_span_id": "span-alb-01",
            "service": "api-gateway",
            "operation": "POST /api/v1/orders",
            "duration_ms": 18,
            "status": "ERROR",
            "timestamp": "2026-09-26T14:00:12Z",
            "start_time": "2026-09-26T14:00:12Z"
        }
    ]

    diagnostic_metrics = {
        "api-gateway": {
            "tcp_retransmissions_percent": 14.8,
            "packet_drops_ingress": 1240,
            "path_mtu_discovery_status": "blackhole_detected",
            "effective_mtu": 1500,
            "advertised_mss": 8960
        }
    }

    return {
        "status": "additional_evidence_provided",
        "incident_id": "INC-004",
        "requested_evidence_type": evidence_type or "network_diagnostics",
        "diagnostic_summary": "Extended eBPF kernel network probe and Cloud Load Balancer access logs reveal Path MTU Discovery blackhole: Jumbo frame packets (>1500 bytes) dropped with DF flag set.",
        "diagnostic_metrics": diagnostic_metrics,
        "diagnostic_logs": diagnostic_logs,
        "diagnostic_traces": diagnostic_traces,
        "conclusion": "With this additional evidence, the root cause is confirmed as network MTU configuration rather than application code regression or database degradation."
    }


def _telemetry_generic(scenario_id: str) -> Dict[str, Any]:
    """Default fallback telemetry generator for ad-hoc scenarios."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "incident_id": scenario_id,
        "deployments": [],
        "service_dependencies": {"api-gateway": ["order-service"]},
        "logs": [
            {"timestamp": now, "incident_id": scenario_id, "service": "api-gateway", "level": "INFO", "message": "Order request received", "trace_id": "trace-gen-01", "span_id": "span-gw-01", "version": "v1"},
            {"timestamp": now, "incident_id": scenario_id, "service": "order-service", "level": "WARN", "message": "Database latency increasing", "trace_id": "trace-gen-01", "span_id": "span-ord-01", "version": "v1"},
            {"timestamp": now, "incident_id": scenario_id, "service": "order-service", "level": "ERROR", "message": "Database query timeout", "trace_id": "trace-gen-01", "span_id": "span-ord-01", "version": "v1"},
        ],
        "traces": [
            {"incident_id": scenario_id, "trace_id": "trace-gen-01", "span_id": "span-gw-01", "parent_span_id": None, "service": "api-gateway", "operation": "POST /api/v1/orders", "duration_ms": 3500, "status": "ERROR", "timestamp": now, "start_time": now},
            {"incident_id": scenario_id, "trace_id": "trace-gen-01", "span_id": "span-ord-01", "parent_span_id": "span-gw-01", "service": "order-service", "operation": "processOrder", "duration_ms": 3480, "status": "ERROR", "timestamp": now, "start_time": now}
        ],
        "metrics_snapshot": {
            "api-gateway": {"error_rate": 0.10, "p99_latency_ms": 3500, "request_rate": 500, "cpu_percent": 50, "memory_percent": 50, "db_latency_ms": 0, "db_connections_active": 0},
            "order-service": {"error_rate": 0.15, "p99_latency_ms": 3480, "request_rate": 200, "cpu_percent": 65, "memory_percent": 55, "db_latency_ms": 2500, "db_connections_active": 50}
        }
    }
