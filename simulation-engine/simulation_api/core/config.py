import os
from pathlib import Path

# Paths: check container path first (/app/scenarios), fallback to local path
CONTAINER_SCENARIOS = Path("/app/scenarios")
LOCAL_SCENARIOS = Path(__file__).resolve().parent.parent.parent / "scenarios"

BASE_SCENARIOS_DIR = CONTAINER_SCENARIOS if CONTAINER_SCENARIOS.exists() else LOCAL_SCENARIOS
SCENARIOS_DIR = BASE_SCENARIOS_DIR / "observable"
EVAL_DIR = BASE_SCENARIOS_DIR / "evaluation"

ES_HOST = os.getenv("ES_HOST", "http://elasticsearch:9200")
PROMETHEUS_HOST = os.getenv("PROMETHEUS_HOST", "http://prometheus:9090")
SIMULATION_PORT = int(os.getenv("PORT", "5001"))
