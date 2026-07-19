"""
Session Service – Tracks student study sessions and publishes session events.

On startup this service:
1. Creates database tables.
2. Initializes an EventPublisher connected to RabbitMQ so that session-related
   events (started, completed) can be consumed by other services (e.g. readiness).
   If RabbitMQ is unavailable, the service continues without event publishing.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.v1 import sessions
from app.core.config import settings
from app.core.db import engine
from app.events import SessionEventPublisher
from app.models import Base
from shared.events import EventPublisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: sets up DB tables and the event publishing pipeline."""

    # Create tables on startup (use Alembic migrations for production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── Event Publisher Setup ──
    # The publisher connects to RabbitMQ and declares the shared topic exchange.
    # SessionEventPublisher wraps it with domain-specific event helpers.
    publisher = EventPublisher(settings.rabbitmq_url)
    try:
        await publisher.connect()
    except Exception:
        # RabbitMQ may not be running in dev – service remains functional
        # but won't emit events to downstream consumers.
        pass
    # Store the publisher on app.state so route handlers can access it
    app.state.event_publisher = SessionEventPublisher(publisher)

    yield

    # ── Shutdown: clean up connections ──
    await publisher.close()
    await engine.dispose()


app = FastAPI(
    title="StudyPilot Session Service",
    version=settings.service_version,
    lifespan=lifespan,
)

app.include_router(sessions.router, prefix="/api/v1")


@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "healthy", "service": settings.service_name}


@app.get("/ready")
async def ready():
    """Readiness probe – checks database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503
