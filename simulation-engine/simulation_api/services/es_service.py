import logging
from typing import Dict, Any, List, Optional
from elasticsearch import Elasticsearch, helpers
from core.config import ES_HOST, SCENARIOS_DIR
from services.scenario_service import load_scenario_file
from services.telemetry_generator import get_scenario_telemetry

logger = logging.getLogger("simulation-api.es")

LOG_MAPPING = {
    "incident_id": {"type": "keyword"},
    "timestamp":   {"type": "date"},
    "service":     {"type": "keyword"},
    "level":       {"type": "keyword"},
    "message":     {"type": "text"},
    "trace_id":    {"type": "keyword"},
    "span_id":     {"type": "keyword"},
    "version":     {"type": "keyword"},
}

TRACE_MAPPING = {
    "incident_id":    {"type": "keyword"},
    "trace_id":       {"type": "keyword"},
    "span_id":        {"type": "keyword"},
    "parent_span_id": {"type": "keyword"},
    "service":        {"type": "keyword"},
    "operation":      {"type": "keyword"},
    "duration_ms":    {"type": "integer"},
    "status":         {"type": "keyword"},
    "timestamp":      {"type": "date"},
    "start_time":     {"type": "date"},
}

DEPLOYMENT_MAPPING = {
    "deployment_id":        {"type": "keyword"},
    "incident_id":          {"type": "keyword"},
    "service":              {"type": "keyword"},
    "version":              {"type": "keyword"},
    "previous_version":     {"type": "keyword"},
    "commit":               {"type": "keyword"},
    "deployed_at":          {"type": "date"},
    "timestamp":            {"type": "date"},
    "change_description":   {"type": "text"},
    "changes":              {"type": "text"},
    "rollback_safe":        {"type": "boolean"},
    "deployer":             {"type": "keyword"},
    "health_status_before": {"type": "keyword"},
}


def get_es_client(host: Optional[str] = None) -> Elasticsearch:
    """Instantiate an Elasticsearch client."""
    return Elasticsearch(host or ES_HOST)


def is_es_healthy(client: Optional[Elasticsearch] = None) -> bool:
    """Check if Elasticsearch cluster is responsive."""
    es = client or get_es_client()
    try:
        health = es.cluster.health(timeout="3s")
        return health.get("status") in ["green", "yellow"]
    except Exception:
        return False


def create_index_if_needed(es: Elasticsearch, index: str, mapping: Dict[str, Any], recreate: bool = True):
    """Create or recreate an Elasticsearch index with specific mappings."""
    if recreate and es.indices.exists(index=index):
        es.indices.delete(index=index)
    if not es.indices.exists(index=index):
        es.indices.create(index=index, body={"mappings": {"properties": mapping}})


def seed_scenario_into_es(es: Elasticsearch, scenario_id: str) -> Dict[str, Any]:
    """
    Index logs, traces, and deployments for a specific scenario into Elasticsearch.
    Uses telemetry generator to supply realistic, correlated telemetry.
    """
    # Prefer generated correlated telemetry package
    gen_telemetry = get_scenario_telemetry(scenario_id)
    sid = gen_telemetry.get("incident_id", scenario_id).upper()
    sid_lower = sid.lower()

    log_index = f"logs-{sid_lower}"
    trace_index = f"traces-{sid_lower}"
    dep_index = f"deployments-{sid_lower}"

    # 1. Index Logs
    create_index_if_needed(es, log_index, LOG_MAPPING, recreate=True)
    raw_logs = gen_telemetry.get("logs", [])
    logs_to_index = []
    for entry in raw_logs:
        doc = dict(entry)
        doc["incident_id"] = sid
        logs_to_index.append(doc)

    if logs_to_index:
        actions = [{"_index": log_index, "_source": doc} for doc in logs_to_index]
        helpers.bulk(es, actions)
        es.indices.refresh(index=log_index)

    # 2. Index Traces
    create_index_if_needed(es, trace_index, TRACE_MAPPING, recreate=True)
    raw_traces = gen_telemetry.get("traces", [])
    traces_to_index = []
    for entry in raw_traces:
        doc = dict(entry)
        doc["incident_id"] = sid
        if "start_time" not in doc:
            doc["start_time"] = doc.get("timestamp", "")
        traces_to_index.append(doc)

    if traces_to_index:
        actions = [{"_index": trace_index, "_source": doc} for doc in traces_to_index]
        helpers.bulk(es, actions)
        es.indices.refresh(index=trace_index)

    # 3. Index Deployments
    create_index_if_needed(es, dep_index, DEPLOYMENT_MAPPING, recreate=True)
    raw_deps = gen_telemetry.get("deployments", [])
    deps_to_index = []
    for entry in raw_deps:
        doc = dict(entry)
        doc["incident_id"] = sid
        if "timestamp" not in doc:
            doc["timestamp"] = doc.get("deployed_at", "")
        if "deployment_id" not in doc:
            doc["deployment_id"] = f"DEP-{sid}"
        deps_to_index.append(doc)

    if deps_to_index:
        actions = [{"_index": dep_index, "_source": doc} for doc in deps_to_index]
        helpers.bulk(es, actions)
        es.indices.refresh(index=dep_index)

    return {
        "scenario_id": sid,
        "logs_indexed": len(logs_to_index),
        "traces_indexed": len(traces_to_index),
        "deployments_indexed": len(deps_to_index),
    }


def seed_all_scenarios_into_es(es: Optional[Elasticsearch] = None) -> List[Dict[str, Any]]:
    """Seed all observable scenarios into Elasticsearch."""
    client = es or get_es_client()
    results = []
    scenarios = ["INC-001", "INC-002", "INC-003", "INC-004"]
    for sid in scenarios:
        res = seed_scenario_into_es(client, sid)
        results.append(res)
    return results
