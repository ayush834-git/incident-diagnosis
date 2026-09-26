"""
Simulation Engine API
Person 1 owns this.

IMPORTANT: Ground truth is NEVER included in /scenarios/:id response.
           It is ONLY available at /scenarios/:id/ground-truth for the evaluation harness.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.metrics import (
    error_rate_gauge,
    latency_p99_gauge,
    request_rate_gauge,
    cpu_gauge,
    db_connections_gauge,
)
from services.es_service import is_es_healthy, seed_all_scenarios_into_es
from api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("simulation-engine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Simulation Engine on port 5001...")
    if is_es_healthy():
        logger.info("Elasticsearch is healthy and reachable. Checking index seeding...")
        try:
            results = seed_all_scenarios_into_es()
            logger.info(f"Auto-seeded {len(results)} scenarios into Elasticsearch.")
        except Exception as e:
            logger.warning(f"Could not auto-seed ES indices at startup: {e}")
    else:
        logger.warning("Elasticsearch is not yet reachable. Telemetry can be seeded via POST /seed once ready.")
    yield
    logger.info("Shutting down Simulation Engine.")


app = FastAPI(
    title="Simulation Engine",
    description="Simulates production incidents with Elasticsearch, Prometheus, and Grafana telemetry.",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    from core.config import SIMULATION_PORT
    uvicorn.run("main:app", host="0.0.0.0", port=SIMULATION_PORT, reload=True)
