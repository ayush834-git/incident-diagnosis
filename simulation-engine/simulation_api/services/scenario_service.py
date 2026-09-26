import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from core.config import SCENARIOS_DIR, EVAL_DIR


def load_scenario_file(scenario_id: str, kind: str = "observable") -> Dict[str, Any]:
    """Load JSON scenario file from disk."""
    base = SCENARIOS_DIR if kind == "observable" else EVAL_DIR
    path = base / f"{scenario_id.lower()}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found in {kind}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_observable_scenarios() -> List[Dict[str, Any]]:
    """List summary of all available observable scenarios."""
    scenarios = []
    if not SCENARIOS_DIR.exists():
        return scenarios

    for f in sorted(SCENARIOS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            scenarios.append({
                "incident_id": data.get("incident_id", f.stem.upper()),
                "severity": data.get("severity", "UNKNOWN"),
                "title": data.get("title", ""),
                "declared_at": data.get("declared_at", ""),
                "services": data.get("services", [])
            })
        except Exception:
            continue
    return scenarios


def get_observable_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    Get observable scenario data for Reasoning Engine.
    Strictly guarantees that ground truth is never included.
    """
    scenario = load_scenario_file(scenario_id, kind="observable")
    # Safeguard: ensure evaluation fields never leak even if present
    forbidden_keys = ["actual_root_cause", "correct_action", "rollback_safe", "evaluator_notes", "expected_health_after_correct_action"]
    clean_scenario = {k: v for k, v in scenario.items() if k not in forbidden_keys}
    return clean_scenario


def get_ground_truth(scenario_id: str) -> Dict[str, Any]:
    """
    Get ground truth data for Evaluation Harness only.
    Must never be called by Reasoning Engine or Control Plane during diagnosis.
    """
    return load_scenario_file(scenario_id, kind="evaluation")
