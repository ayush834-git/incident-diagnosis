"""
Telemetry Generator CLI for Simulation Engine.
Generates and loads correlated logs, traces, deployments, and dependency metadata into Elasticsearch.

Usage:
    python scripts/generate_telemetry.py [--scenario INC-001] [--es-host http://localhost:9200]
"""
import sys
import time
import argparse
from pathlib import Path

# Add simulation_api to sys.path to reuse the generator and mappings
SIM_API_DIR = Path(__file__).resolve().parent.parent / "simulation_api"
if str(SIM_API_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_API_DIR))

try:
    from elasticsearch import Elasticsearch
    from services.es_service import seed_scenario_into_es, seed_all_scenarios_into_es, wait_for_es
    from services.telemetry_generator import get_scenario_telemetry
except ImportError:
    # If elasticsearch package missing, gracefully inform
    print("Run: pip install elasticsearch httpx")
    sys.exit(1)

ES_HOST = "http://localhost:9200"


def wait_for_elasticsearch(es: Elasticsearch, retries: int = 15):
    for i in range(retries):
        try:
            health = es.cluster.health(wait_for_status="yellow", timeout="5s")
            print(f"✅ Elasticsearch ready: {health.get('status')}")
            return True
        except Exception:
            print(f"⏳ Waiting for ES ({i+1}/{retries})...")
            time.sleep(2)
    print("❌ Elasticsearch not reachable")
    return False


def main():
    parser = argparse.ArgumentParser(description="Generate and load realistic telemetry into Elasticsearch")
    parser.add_argument("--scenario", help="Target scenario (e.g. INC-001, INC-002, INC-003, INC-004), or all if omitted")
    parser.add_argument("--es-host", default=ES_HOST, help="Elasticsearch URL")
    args = parser.parse_args()

    es = Elasticsearch(args.es_host)
    if not wait_for_elasticsearch(es):
        sys.exit(1)

    scenarios = [args.scenario.upper()] if args.scenario else ["INC-001", "INC-002", "INC-003", "INC-004"]

    print("\n🚀 Generating realistic correlated telemetry (Logs, Traces, Deployments)...")
    for sid in scenarios:
        res = seed_scenario_into_es(es, sid)
        print(f"  [{res['scenario_id']}] -> logs: {res['logs_indexed']}, traces: {res['traces_indexed']}, deployments: {res['deployments_indexed']}")

    print("\n🎉 Telemetry successfully generated and indexed into Elasticsearch.")


if __name__ == "__main__":
    main()
