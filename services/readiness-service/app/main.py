from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.v1 import readiness
from app.core.config import settings
from app.core.db import engine
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="StudyPilot Readiness Service",
    version=settings.service_version,
    lifespan=lifespan,
)

app.include_router(readiness.router, prefix="/api/v1")


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
