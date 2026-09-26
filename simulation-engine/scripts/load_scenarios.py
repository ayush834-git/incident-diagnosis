"""
Load all scenario data into Elasticsearch.
Run this after docker-compose up -d

Usage:
    python scripts/load_scenarios.py [--scenario INC-001]
"""
import json
import sys
import time
import argparse
from pathlib import Path

try:
    from elasticsearch import Elasticsearch, helpers
except ImportError:
    print("Run: pip install elasticsearch")
    sys.exit(1)

ES_HOST = "http://localhost:9200"
SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios" / "observable"


def wait_for_es(es: Elasticsearch, retries: int = 20):
    for i in range(retries):
        try:
            health = es.cluster.health(wait_for_status="yellow", timeout="5s")
            print(f"✅ Elasticsearch ready: {health['status']}")
            return
        except Exception as e:
            print(f"⏳ Waiting for ES ({i+1}/{retries})...")
            time.sleep(3)
    print("❌ Elasticsearch not available")
    sys.exit(1)


def create_index(es: Elasticsearch, index: str, mapping: dict):
    if es.indices.exists(index=index):
        es.indices.delete(index=index)
    es.indices.create(index=index, body={"mappings": {"properties": mapping}})
    print(f"  Created index: {index}")


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


def load_scenario(es: Elasticsearch, scenario_id: str):
    path = SCENARIOS_DIR / f"{scenario_id.lower()}.json"
    if not path.exists():
        print(f"❌ Scenario file not found: {path}")
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    sid = data.get("incident_id", scenario_id).upper()
    sid_lower = sid.lower()

    log_index = f"logs-{sid_lower}"
    trace_index = f"traces-{sid_lower}"
    dep_index = f"deployments-{sid_lower}"

    print(f"\n📦 Loading {sid}...")

    # Load logs
    create_index(es, log_index, LOG_MAPPING)
    logs = data.get("logs", [])
    if logs:
        docs = []
        for l in logs:
            doc = dict(l)
            doc["incident_id"] = sid
            docs.append(doc)
        actions = [{"_index": log_index, "_source": doc} for doc in docs]
        helpers.bulk(es, actions)
        es.indices.refresh(index=log_index)
        print(f"  Loaded {len(docs)} log entries → {log_index}")

    # Load traces
    create_index(es, trace_index, TRACE_MAPPING)
    traces = data.get("traces", [])
    if traces:
        docs = []
        for t in traces:
            doc = dict(t)
            doc["incident_id"] = sid
            docs.append(doc)
        actions = [{"_index": trace_index, "_source": doc} for doc in docs]
        helpers.bulk(es, actions)
        es.indices.refresh(index=trace_index)
        print(f"  Loaded {len(docs)} trace spans → {trace_index}")

    # Load deployments
    create_index(es, dep_index, DEPLOYMENT_MAPPING)
    deployments = data.get("deployments", [])
    if deployments:
        docs = []
        for d in deployments:
            doc = dict(d)
            doc["incident_id"] = sid
            if "timestamp" not in doc:
                doc["timestamp"] = doc.get("deployed_at", "")
            docs.append(doc)
        actions = [{"_index": dep_index, "_source": doc} for doc in docs]
        helpers.bulk(es, actions)
        es.indices.refresh(index=dep_index)
        print(f"  Loaded {len(docs)} deployment events → {dep_index}")

    print(f"✅ {sid} loaded successfully")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", help="Load specific scenario (e.g. INC-001), or all if omitted")
    parser.add_argument("--es-host", default=ES_HOST)
    args = parser.parse_args()

    es = Elasticsearch(args.es_host)
    wait_for_es(es)

    if args.scenario:
        load_scenario(es, args.scenario)
    else:
        for f in sorted(SCENARIOS_DIR.glob("*.json")):
            scenario_id = f.stem.upper()
            load_scenario(es, scenario_id)

    print("\n🎉 All scenarios loaded. ES is ready.")


if __name__ == "__main__":
    main()
