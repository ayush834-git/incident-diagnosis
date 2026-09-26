import httpx
import logging
from typing import Optional, Dict, Any
from services.scenario_service import load_scenario_file
from core.metrics import set_metrics_from_snapshot, reset_metrics_to_baseline

logger = logging.getLogger("simulation-api.injector")
ACTIVE_SCENARIO: Optional[str] = None

# Microservice endpoints inside Docker network
SERVICE_ENDPOINTS = {
    "api-gateway": "http://api-gateway:8000",
    "order-service": "http://order-service:8001",
    "payment-service": "http://payment-service:8002",
    "inventory-service": "http://inventory-service:8003",
    "database": "http://database:8004",
}


def get_active_scenario() -> Optional[str]:
    """Get currently injected scenario ID."""
    return ACTIVE_SCENARIO


def _notify_microservices_inject(snapshot: Dict[str, Any], incident_id: str):
    """Optionally broadcast fault state to live microservices if reachable."""
    with httpx.Client(timeout=1.0) as client:
        for svc_name, base_url in SERVICE_ENDPOINTS.items():
            metrics = snapshot.get(svc_name, {})
            payload = {
                "error_rate": metrics.get("error_rate", 0.0),
                "latency_ms": metrics.get("p99_latency_ms", 0),
                "cpu_percent": metrics.get("cpu_percent", 15.0),
                "db_connections_active": metrics.get("db_connections_active", 5),
                "incident_id": incident_id,
            }
            try:
                client.post(f"{base_url}/fault/inject", json=payload)
            except Exception:
                pass


def _notify_microservices_resolve():
    """Optionally broadcast fault resolution to live microservices."""
    with httpx.Client(timeout=1.0) as client:
        for base_url in SERVICE_ENDPOINTS.values():
            try:
                client.post(f"{base_url}/fault/resolve")
            except Exception:
                pass


def inject_fault(scenario_id: str) -> Dict[str, Any]:
    """
    Trigger fault injection:
    Loads scenario metrics_snapshot and updates Prometheus gauges.
    """
    global ACTIVE_SCENARIO
    scenario = load_scenario_file(scenario_id, kind="observable")
    snapshot = scenario.get("metrics_snapshot", {})

    set_metrics_from_snapshot(snapshot)
    ACTIVE_SCENARIO = scenario.get("incident_id", scenario_id).upper()

    # Broadcast to live microservices if running
    _notify_microservices_inject(snapshot, ACTIVE_SCENARIO)

    return {
        "status": "injected",
        "scenario_id": ACTIVE_SCENARIO,
        "message": f"Fault injected for {ACTIVE_SCENARIO}. Prometheus metrics updated to incident state.",
        "services_affected": list(snapshot.keys()),
        "metrics_applied": snapshot
    }


def resolve_fault(scenario_id: str) -> Dict[str, Any]:
    """
    Reset metrics to known good baseline after mitigation/remediation.
    """
    global ACTIVE_SCENARIO
    scenario = load_scenario_file(scenario_id, kind="observable")
    reset_metrics_to_baseline(scenario)
    resolved_id = scenario.get("incident_id", scenario_id).upper()
    ACTIVE_SCENARIO = None

    # Broadcast resolution to live microservices if running
    _notify_microservices_resolve()

    return {
        "status": "resolved",
        "scenario_id": resolved_id,
        "message": f"Scenario {resolved_id} resolved. Gauges restored to healthy baseline."
    }


ACTIVE_FAULTS: Dict[str, Dict[str, Any]] = {}


def get_active_faults() -> Dict[str, Dict[str, Any]]:
    """Return all active custom injected faults."""
    return ACTIVE_FAULTS


def inject_custom_fault(
    service: str,
    fault_type: str = "latency",
    latency_ms: int = 0,
    error_rate: float = 0.0,
    cpu_percent: int = 0,
    incident_id: Optional[str] = None
) -> Dict[str, Any]:
    """Inject a targeted fault on a specific service."""
    from core.metrics import set_service_metrics

    metrics: Dict[str, Any] = {}
    if fault_type == "latency" or latency_ms > 0:
        metrics["p99_latency_ms"] = latency_ms if latency_ms > 0 else 3000
    if fault_type == "error" or error_rate > 0:
        metrics["error_rate"] = error_rate if error_rate > 0 else 0.40
    if fault_type == "timeout":
        metrics["p99_latency_ms"] = 5500
        metrics["error_rate"] = 0.50
    if fault_type == "cpu" or cpu_percent > 0:
        metrics["cpu_percent"] = cpu_percent if cpu_percent > 0 else 92

    set_service_metrics(service, metrics)

    fault_record = {
        "service": service,
        "fault_type": fault_type,
        "latency_ms": latency_ms,
        "error_rate": error_rate,
        "cpu_percent": cpu_percent,
        "incident_id": incident_id or ACTIVE_SCENARIO or "CUSTOM",
        "applied_metrics": metrics
    }
    ACTIVE_FAULTS[service] = fault_record

    # Broadcast to live microservice if reachable
    base_url = SERVICE_ENDPOINTS.get(service)
    if base_url:
        try:
            with httpx.Client(timeout=1.0) as client:
                client.post(f"{base_url}/fault/inject", json=fault_record)
        except Exception:
            pass

    return {
        "status": "injected",
        "service": service,
        "fault_type": fault_type,
        "details": metrics,
        "message": f"Fault '{fault_type}' successfully injected into {service}."
    }


def reset_custom_fault(service: Optional[str] = None) -> Dict[str, Any]:
    """Reset faults for a single service or all services."""
    from core.metrics import (
        error_rate_gauge,
        latency_p99_gauge,
        cpu_gauge,
        memory_gauge,
    )

    services_to_reset = [service] if service else list(SERVICE_ENDPOINTS.keys())
    affected = []

    for svc in services_to_reset:
        error_rate_gauge.labels(service=svc).set(0.001)
        latency_p99_gauge.labels(service=svc).set(40.0)
        cpu_gauge.labels(service=svc).set(20.0)
        memory_gauge.labels(service=svc).set(35.0)
        if svc in ACTIVE_FAULTS:
            del ACTIVE_FAULTS[svc]
        affected.append(svc)

        base_url = SERVICE_ENDPOINTS.get(svc)
        if base_url:
            try:
                with httpx.Client(timeout=1.0) as client:
                    client.post(f"{base_url}/fault/resolve")
            except Exception:
                pass

    return {
        "status": "reset",
        "message": f"Faults reset to healthy baseline for {', '.join(affected)}.",
        "affected_services": affected
    }

