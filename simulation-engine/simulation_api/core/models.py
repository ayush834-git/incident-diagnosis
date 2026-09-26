from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ── Health & Status ────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall service status")
    service: str = Field(default="simulation-engine", description="Service name")
    active_scenario: Optional[str] = Field(None, description="Currently running scenario ID, if any")
    elasticsearch_connected: bool = Field(..., description="Whether Elasticsearch is reachable")
    timestamp: str = Field(..., description="Current ISO timestamp")


class ScenarioSummary(BaseModel):
    incident_id: str
    severity: str
    title: str
    declared_at: str
    services: List[str]


class ScenarioListResponse(BaseModel):
    scenarios: List[ScenarioSummary]
    total: int


class ScenarioStatusResponse(BaseModel):
    incident_id: str
    status: str = Field(..., description="'active', 'idle', or 'resolved'")
    active_scenario: Optional[str] = Field(None, description="Active scenario ID")
    declared_at: Optional[str] = None
    services: List[str] = []
    metrics_snapshot: Dict[str, Any] = {}
    last_updated: str


# ── Telemetry Models ───────────────────────────────────────────────────────────

class LogEntry(BaseModel):
    timestamp: str
    incident_id: Optional[str] = None
    service: str
    level: str
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    version: Optional[str] = None


class LogsResponse(BaseModel):
    incident_id: str
    total: int
    logs: List[LogEntry]


class TraceSpan(BaseModel):
    incident_id: Optional[str] = None
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    service: str
    operation: str
    duration_ms: int
    status: str
    timestamp: Optional[str] = None
    start_time: Optional[str] = None
    error_reason: Optional[str] = None


class TracesResponse(BaseModel):
    incident_id: str
    total: int
    traces: List[TraceSpan]


class MetricsResponse(BaseModel):
    incident_id: str
    timestamp: str
    metrics: Dict[str, Any]


class DeploymentEvent(BaseModel):
    deployment_id: Optional[str] = None
    service: str
    version: str
    previous_version: Optional[str] = None
    deployed_at: Optional[str] = None
    timestamp: Optional[str] = None
    deployer: Optional[str] = None
    change_description: Optional[str] = None
    changes: Optional[List[str]] = None
    rollback_safe: Optional[bool] = None


class DeploymentsResponse(BaseModel):
    incident_id: str
    total: int
    deployments: List[DeploymentEvent]


# ── Action Responses ───────────────────────────────────────────────────────────

class ScenarioActionResponse(BaseModel):
    status: str
    incident_id: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ── Fault Injection Models ─────────────────────────────────────────────────────

class FaultInjectRequest(BaseModel):
    service: str = Field(..., description="Target service name (e.g. order-service, payment-service)")
    fault_type: str = Field(default="latency", description="Type of fault: 'latency', 'error', 'timeout', or 'cpu'")
    latency_ms: Optional[int] = Field(default=0, description="Artificial latency in milliseconds")
    error_rate: Optional[float] = Field(default=0.0, description="Error probability (0.0 to 1.0)")
    cpu_percent: Optional[int] = Field(default=0, description="Simulated CPU utilization percentage")
    incident_id: Optional[str] = Field(default=None, description="Associated incident ID")


class FaultInjectResponse(BaseModel):
    status: str
    service: str
    fault_type: str
    details: Dict[str, Any]
    message: str


class FaultResetRequest(BaseModel):
    service: Optional[str] = Field(default=None, description="Specific service to reset, or null to reset all")


class FaultResetResponse(BaseModel):
    status: str
    message: str
    affected_services: List[str]
