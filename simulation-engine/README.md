# Simulation Engine — Person 1

**Port:** 5001  
**Owns:** Docker Compose (ES + Prometheus + Grafana), simulated microservices, fault injection, scenario data, ground truth API.

## Quick Start

```bash
docker-compose up -d
python scripts/load_scenarios.py
# API available at http://localhost:5001
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check endpoint and simulation status |
| GET | `/scenarios` | List all available incidents |
| POST | `/scenarios/{incident_id}/start` | Start an incident and index telemetry |
| POST | `/scenarios/{incident_id}/reset` | Reset an incident to healthy baseline |
| GET | `/scenarios/{incident_id}/status` | Inspect current simulation state |
| GET | `/scenarios/{incident_id}/logs` | Query structured logs (optional `?service=`) |
| GET | `/scenarios/{incident_id}/metrics` | Query metrics snapshot (optional `?service=`) |
| GET | `/scenarios/{incident_id}/traces` | Query distributed traces (optional `?service=`) |
| GET | `/scenarios/{incident_id}/deployments` | Query deployment metadata events |
| POST | `/faults/inject` | Inject targeted custom fault into a service |
| POST | `/faults/reset` | Reset custom faults for a service or all services |
| GET | `/scenarios/{incident_id}` | Observable scenario (ground truth strictly excluded) |
| GET | `/scenarios/{incident_id}/ground-truth` | Ground truth (evaluation harness only) |
| GET | `/metrics` | Prometheus metrics scrape endpoint |

## ES Indices

| Index | Content |
|---|---|
| `logs-{incident_id}` | Application logs |
| `traces-{incident_id}` | Distributed traces |
| `deployments-{incident_id}` | Deployment events |

## Scenarios

| ID | File | Root Cause |
|---|---|---|
| INC-001 | scenarios/observable/inc-001.json | Deployment regression (rollback safe) |
| INC-002 | scenarios/observable/inc-002.json | DB schema migration (rollback unsafe) |
| INC-003 | scenarios/observable/inc-003.json | Dependency cascade |
| INC-004 | scenarios/observable/inc-004.json | Insufficient evidence (supports `POST /scenarios/INC-004/request-evidence`) |

## Microservice Architecture

The engine simulates a realistic production e-commerce backend:

```
api-gateway (:8000)
    ↓
order-service (:8001)
    ├── payment-service (:8002)
    ├── inventory-service (:8003)
    └── database (:8004)
```

Each service:
- Generates structured JSON logs (`timestamp`, `incident_id`, `service`, `level`, `message`, `trace_id`, `span_id`).
- Propagates distributed trace IDs (`X-Trace-Id`, `X-Span-Id`, `X-Parent-Span-Id`).
- Emits Prometheus metrics on `/metrics` (requests, errors, latency, simulated CPU %, simulated memory %, active DB pool).
- Exposes `/health`, `/fault/inject`, and `/fault/resolve`.
- Ships live logs and trace spans asynchronously to Elasticsearch (`logs-{incident_id}`, `traces-{incident_id}`).
- `api-gateway` features a lightweight background synthetic traffic generator for continuous live telemetry.

