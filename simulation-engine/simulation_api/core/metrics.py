from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any

# Prometheus metrics matching contracts and Reasoning Engine queries
error_rate_gauge = Gauge("http_error_rate", "HTTP error rate (0.0 to 1.0)", ["service"])
latency_p99_gauge = Gauge("http_latency_p99_ms", "p99 latency in milliseconds", ["service"])
request_rate_gauge = Gauge("http_request_rate", "Requests/sec", ["service"])
cpu_gauge = Gauge("service_cpu_percent", "CPU utilization percentage (0 to 100)", ["service"])
memory_gauge = Gauge("service_memory_percent", "Memory utilization percentage (0 to 100)", ["service"])
db_latency_gauge = Gauge("db_query_latency_ms", "Database query latency in milliseconds", ["service"])
db_connections_gauge = Gauge("db_pool_active", "Active DB connections", ["service"])
dependency_health_gauge = Gauge(
    "dependency_health_status",
    "Health status of downstream dependency (1=healthy, 0=degraded)",
    ["service", "dependency"]
)


def set_service_metrics(service: str, metrics: Dict[str, Any]):
    """Set Prometheus gauge values for a given service."""
    if "error_rate" in metrics:
        error_rate_gauge.labels(service=service).set(float(metrics["error_rate"]))
    if "p99_latency_ms" in metrics:
        latency_p99_gauge.labels(service=service).set(float(metrics["p99_latency_ms"]))
    if "request_rate" in metrics:
        request_rate_gauge.labels(service=service).set(float(metrics["request_rate"]))
    if "cpu_percent" in metrics:
        cpu_gauge.labels(service=service).set(float(metrics["cpu_percent"]))
    if "memory_percent" in metrics:
        memory_gauge.labels(service=service).set(float(metrics["memory_percent"]))
    else:
        # Default baseline memory if not explicitly provided
        memory_gauge.labels(service=service).set(35.0)
    if "db_latency_ms" in metrics:
        db_latency_gauge.labels(service=service).set(float(metrics["db_latency_ms"]))
    if "db_connections_active" in metrics:
        db_connections_gauge.labels(service=service).set(float(metrics["db_connections_active"]))


def set_dependency_health(service: str, dependency: str, is_healthy: bool):
    """Set health status for a downstream dependency."""
    dependency_health_gauge.labels(service=service, dependency=dependency).set(1.0 if is_healthy else 0.0)


def set_metrics_from_snapshot(snapshot: Dict[str, Dict[str, Any]], dependencies: Dict[str, Any] = None):
    """Update all gauges from a scenario's metrics_snapshot and dependencies."""
    for service, metrics in snapshot.items():
        set_service_metrics(service, metrics)

    if dependencies:
        for svc, deps in dependencies.items():
            for dep in deps:
                # If either service is in error, set dependency status degraded
                svc_err = snapshot.get(svc, {}).get("error_rate", 0.0)
                dep_err = snapshot.get(dep, {}).get("error_rate", 0.0)
                is_ok = (svc_err < 0.1 and dep_err < 0.1)
                set_dependency_health(svc, dep, is_ok)


def reset_metrics_to_baseline(scenario: Dict[str, Any]):
    """Reset service gauges to known good baselines or healthy defaults."""
    services = scenario.get("services", [])
    known_good = scenario.get("known_good_versions", {})
    dependencies = scenario.get("service_dependencies", {})

    for service in services:
        kg = known_good.get(service, {})
        base_metrics = kg.get("baseline_metrics", {})

        err = float(base_metrics.get("error_rate", 0.002))
        p99 = float(base_metrics.get("p99_latency_ms", 120))

        error_rate_gauge.labels(service=service).set(err)
        latency_p99_gauge.labels(service=service).set(p99)
        request_rate_gauge.labels(service=service).set(250.0)
        cpu_gauge.labels(service=service).set(20.0)
        memory_gauge.labels(service=service).set(35.0)
        db_latency_gauge.labels(service=service).set(12.0)
        db_connections_gauge.labels(service=service).set(10.0)

    for svc, deps in dependencies.items():
        for dep in deps:
            set_dependency_health(svc, dep, True)


def get_latest_metrics() -> bytes:
    """Return raw prometheus metrics payload."""
    return generate_latest()
