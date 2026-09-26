from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query
from starlette.responses import Response

from core.metrics import (
    get_latest_metrics,
    set_metrics_from_snapshot,
    CONTENT_TYPE_LATEST,
)
from core.models import (
    HealthResponse,
    ScenarioListResponse,
    ScenarioStatusResponse,
    LogsResponse,
    TracesResponse,
    MetricsResponse,
    DeploymentsResponse,
    ScenarioActionResponse,
    FaultInjectRequest,
    FaultInjectResponse,
    FaultResetRequest,
    FaultResetResponse,
)
from services.scenario_service import (
    list_observable_scenarios,
    get_observable_scenario,
    get_ground_truth,
)
from services.injector_service import (
    inject_fault,
    resolve_fault,
    get_active_scenario,
    inject_custom_fault,
    reset_custom_fault,
    get_active_faults,
)
from services.es_service import (
    is_es_healthy,
    seed_all_scenarios_into_es,
    seed_scenario_into_es,
    get_es_client,
)
from services.telemetry_generator import (
    get_scenario_telemetry,
    get_additional_evidence_inc_004,
)

router = APIRouter()


# ── 1. Health Endpoint ─────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint reporting simulation engine state and ES connectivity."""
    return HealthResponse(
        status="ok",
        service="simulation-engine",
        active_scenario=get_active_scenario(),
        elasticsearch_connected=is_es_healthy(),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ── 2. Prometheus Metrics Scrape ───────────────────────────────────────────────

@router.get("/metrics")
def metrics():
    """Exposes real-time Prometheus metrics for scraping."""
    return Response(get_latest_metrics(), media_type=CONTENT_TYPE_LATEST)


# ── 3. Scenarios List ──────────────────────────────────────────────────────────

@router.get("/scenarios", response_model=ScenarioListResponse)
def list_scenarios():
    """List all available observable scenarios."""
    scenarios = list_observable_scenarios()
    return ScenarioListResponse(
        scenarios=scenarios,
        total=len(scenarios),
    )


# ── 4. Scenario Lifecycle: Start & Reset ───────────────────────────────────────

@router.post("/scenarios/{incident_id}/start", response_model=ScenarioActionResponse)
def start_scenario(incident_id: str):
    """
    Start an incident scenario:
    1. Injects the fault snapshot into Prometheus gauges and microservices.
    2. Indexes pre- and post-incident logs, traces, and deployment events into Elasticsearch.
    """
    sid = incident_id.upper()
    obs_data = get_observable_scenario(sid)

    # 1. Inject fault metrics
    inject_res = inject_fault(sid)

    # 2. Seed ES if available
    es_status = "skipped"
    counts = None
    if is_es_healthy():
        try:
            es = get_es_client()
            counts = seed_scenario_into_es(es, sid)
            es_status = "indexed"
        except Exception as e:
            es_status = f"error: {str(e)}"

    return ScenarioActionResponse(
        status="active",
        incident_id=sid,
        message=f"Scenario {sid} started. Telemetry active and indexed in Elasticsearch ({es_status}).",
        details={
            "title": obs_data.get("title", ""),
            "declared_at": obs_data.get("declared_at", ""),
            "services": obs_data.get("services", []),
            "metrics_applied": inject_res.get("metrics_applied", {}),
            "elasticsearch": es_status,
            "indexed_counts": counts,
        }
    )


@router.post("/scenarios/{incident_id}/reset", response_model=ScenarioActionResponse)
@router.post("/scenarios/{incident_id}/resolve", response_model=ScenarioActionResponse)
def reset_scenario(incident_id: str):
    """
    Reset an incident scenario:
    Restores Prometheus gauges to healthy baseline and clears active scenario state.
    """
    sid = incident_id.upper()
    res = resolve_fault(sid)
    return ScenarioActionResponse(
        status="resolved",
        incident_id=sid,
        message=f"Scenario {sid} reset. Metrics restored to healthy baseline.",
        details=res,
    )


# ── 5. Scenario Status ─────────────────────────────────────────────────────────

@router.get("/scenarios/{incident_id}/status", response_model=ScenarioStatusResponse)
def get_scenario_status(incident_id: str):
    """Inspect current simulation state for an incident."""
    sid = incident_id.upper()
    obs_data = get_observable_scenario(sid)
    active = get_active_scenario()

    is_active = (active == sid)
    status_str = "active" if is_active else "idle"

    return ScenarioStatusResponse(
        incident_id=sid,
        status=status_str,
        active_scenario=active,
        declared_at=obs_data.get("declared_at"),
        services=obs_data.get("services", []),
        metrics_snapshot=obs_data.get("metrics_snapshot", {}),
        last_updated=datetime.now(timezone.utc).isoformat(),
    )


# ── 6. Telemetry Slices: Logs, Metrics, Traces, Deployments ────────────────────

@router.get("/scenarios/{incident_id}/logs", response_model=LogsResponse)
def get_scenario_logs(incident_id: str, service: Optional[str] = Query(None)):
    """
    Get structured logs for an incident.
    Ground truth is strictly excluded.
    """
    sid = incident_id.upper()
    telemetry = get_scenario_telemetry(sid)
    all_logs = telemetry.get("logs", [])

    if service:
        filtered = [l for l in all_logs if l.get("service") == service]
    else:
        filtered = all_logs

    return LogsResponse(
        incident_id=sid,
        total=len(filtered),
        logs=filtered,
    )


@router.get("/scenarios/{incident_id}/metrics", response_model=MetricsResponse)
def get_scenario_metrics(incident_id: str, service: Optional[str] = Query(None)):
    """
    Get metrics snapshot for an incident.
    Ground truth is strictly excluded.
    """
    sid = incident_id.upper()
    telemetry = get_scenario_telemetry(sid)
    all_metrics = telemetry.get("metrics_snapshot", {})

    if service:
        filtered = {service: all_metrics.get(service, {})} if service in all_metrics else {}
    else:
        filtered = all_metrics

    return MetricsResponse(
        incident_id=sid,
        timestamp=datetime.now(timezone.utc).isoformat(),
        metrics=filtered,
    )


@router.get("/scenarios/{incident_id}/traces", response_model=TracesResponse)
def get_scenario_traces(incident_id: str, service: Optional[str] = Query(None)):
    """
    Get distributed trace spans for an incident.
    Ground truth is strictly excluded.
    """
    sid = incident_id.upper()
    telemetry = get_scenario_telemetry(sid)
    all_traces = telemetry.get("traces", [])

    if service:
        filtered = [t for t in all_traces if t.get("service") == service]
    else:
        filtered = all_traces

    return TracesResponse(
        incident_id=sid,
        total=len(filtered),
        traces=filtered,
    )


@router.get("/scenarios/{incident_id}/deployments", response_model=DeploymentsResponse)
def get_scenario_deployments(incident_id: str):
    """
    Get deployment events for an incident.
    Ground truth is strictly excluded.
    """
    sid = incident_id.upper()
    telemetry = get_scenario_telemetry(sid)
    deployments = telemetry.get("deployments", [])

    return DeploymentsResponse(
        incident_id=sid,
        total=len(deployments),
        deployments=deployments,
    )


# ── 7. Fault Injection Endpoints ───────────────────────────────────────────────

@router.post("/faults/inject", response_model=FaultInjectResponse)
def post_fault_inject(req: FaultInjectRequest):
    """
    Inject custom faults into a target service:
    latency, error rate, timeout, or high CPU utilization.
    Updates Prometheus gauges and broadcasts to the live microservice if running.
    """
    res = inject_custom_fault(
        service=req.service,
        fault_type=req.fault_type,
        latency_ms=req.latency_ms or 0,
        error_rate=req.error_rate or 0.0,
        cpu_percent=req.cpu_percent or 0,
        incident_id=req.incident_id,
    )
    return FaultInjectResponse(
        status="injected",
        service=res["service"],
        fault_type=res["fault_type"],
        details=res["details"],
        message=res["message"],
    )


@router.post("/faults/reset", response_model=FaultResetResponse)
def post_fault_reset(req: Optional[FaultResetRequest] = None):
    """
    Reset custom injected faults for a specific service or all services.
    Restores gauges to healthy baseline.
    """
    target_service = req.service if req else None
    res = reset_custom_fault(service=target_service)
    return FaultResetResponse(
        status="reset",
        message=res["message"],
        affected_services=res["affected_services"],
    )


# ── 8. Observable Scenario & Ground Truth Endpoints ────────────────────────────

@router.get("/scenarios/{incident_id}")
def get_scenario(incident_id: str):
    """
    Returns observable scenario data for Reasoning Engine.
    Ground truth is strictly excluded to prevent evaluation leakage.
    """
    return get_observable_scenario(incident_id)


@router.get("/scenarios/{incident_id}/ground-truth")
def get_scenario_ground_truth(incident_id: str):
    """
    Returns ground truth for the evaluation harness only.
    WARNING: Must never be called by Reasoning Engine or Control Plane during diagnosis.
    """
    return get_ground_truth(incident_id)


@router.get("/scenarios/{incident_id}/dependencies")
def get_scenario_dependencies(incident_id: str):
    """Returns service dependency graph metadata for this scenario."""
    telemetry = get_scenario_telemetry(incident_id)
    return {
        "incident_id": telemetry.get("incident_id", incident_id.upper()),
        "service_dependencies": telemetry.get("service_dependencies", {}),
    }


@router.get("/scenarios/{incident_id}/telemetry")
def get_raw_telemetry(incident_id: str):
    """
    Inspect the generated correlated telemetry (logs, traces, deployments, metrics).
    Ground truth is strictly excluded.
    """
    return get_scenario_telemetry(incident_id)


@router.post("/scenarios/{incident_id}/inject")
def trigger_inject_fault_alias(incident_id: str):
    """Trigger fault injection snapshot for a specific scenario."""
    return inject_fault(incident_id)


# ── 9. Additional Diagnostic Evidence (INC-004 Support) ────────────────────────

@router.get("/scenarios/{incident_id}/additional-evidence")
def get_additional_evidence(incident_id: str):
    """
    Returns additional diagnostic evidence definition for scenarios with insufficient initial evidence.
    """
    sid = incident_id.upper()
    if sid == "INC-004":
        return get_additional_evidence_inc_004()
    return {
        "incident_id": sid,
        "additional_evidence_available": False,
        "message": f"Scenario {sid} already contains sufficient telemetry for diagnosis.",
    }


@router.post("/scenarios/{incident_id}/request-evidence")
@router.post("/scenarios/{incident_id}/enrich")
def request_diagnostic_evidence(incident_id: str, payload: dict = None):
    """
    Simulates additional diagnostic data becoming available upon explicit request from Reasoning Engine.
    Indexes diagnostic logs and traces into Elasticsearch if available.
    """
    sid = incident_id.upper()
    if sid != "INC-004":
        return {
            "incident_id": sid,
            "status": "not_applicable",
            "message": f"Scenario {sid} does not require additional evidence.",
        }

    evidence_type = (payload or {}).get("evidence_type", "network_diagnostics")
    evidence = get_additional_evidence_inc_004(evidence_type)

    if is_es_healthy():
        try:
            es = get_es_client()
            for log_doc in evidence.get("diagnostic_logs", []):
                es.index(index=f"logs-{sid.lower()}", document=log_doc)
            for trace_doc in evidence.get("diagnostic_traces", []):
                es.index(index=f"traces-{sid.lower()}", document=trace_doc)
        except Exception:
            pass

    return evidence


# ── 10. Elasticsearch Seeding ──────────────────────────────────────────────────

@router.post("/scenarios/{incident_id}/seed")
def seed_single_scenario(incident_id: str):
    """Index logs, traces, and deployments for this scenario into Elasticsearch."""
    try:
        es = get_es_client()
        result = seed_scenario_into_es(es, incident_id)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed ES: {str(e)}")


@router.post("/seed")
def seed_all():
    """Seed all observable scenarios into Elasticsearch."""
    try:
        es = get_es_client()
        results = seed_all_scenarios_into_es(es)
        return {"status": "success", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed ES: {str(e)}")
