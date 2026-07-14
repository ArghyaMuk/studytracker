import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.v1 import revision
from app.core.config import settings
from app.core.db import engine
from app.events.consumers import register_consumers
from app.models import Base
from shared.events import EventConsumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start RabbitMQ event consumer
    consumer = EventConsumer(settings.rabbitmq_url, settings.service_name)
    register_consumers(consumer)
    asyncio.create_task(consumer.start())
    app.state.consumer = consumer

    yield

    await app.state.consumer.close()
    await engine.dispose()


app = FastAPI(
    title="StudyPilot Spaced Repetition Service",
    version=settings.service_version,
    lifespan=lifespan,
)

app.include_router(revision.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.service_name}


@app.get("/ready")
async def ready():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503
