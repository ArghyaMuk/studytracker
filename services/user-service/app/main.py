"""
User Service – Handles authentication, registration, and user profile management.

On startup this service:
1. Creates database tables if they don't exist (dev convenience; use migrations in prod).
2. Bootstraps a default admin account from environment variables so the system is
   immediately usable after a fresh deployment.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.v1 import auth, users
from app.core.config import settings
from app.core.db import engine, async_session_factory
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager – runs startup and shutdown logic."""

    # ── Startup: ensure schema exists ──
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── Admin Bootstrap ──
    # Creates the admin account on first launch so admin routes are accessible
    # without needing a manual registration step.
    from app.repositories import UserRepository
    from app.models import User, UserProfile
    from shared.auth import hash_password

    async with async_session_factory() as db:
        repo = UserRepository(db)
        admin = await repo.get_by_email(settings.admin_email)
        if not admin:
            # No admin exists yet – seed one with env-configured credentials
            admin_user = User(
                name="Admin User",
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                college="StudyPilot",
                university="StudyPilot",
                current_semester=1,
                role="admin",  # Grants full access to admin-only endpoints
            )
            admin_user = await repo.create(admin_user)
            # Attach a default study profile for the admin user
            await repo.create_profile(UserProfile(
                user_id=admin_user.id,
                daily_study_hours_target=2.0,
                goal_type="semester_exam",
            ))

    yield

    # ── Shutdown: dispose database engine connections ──
    await engine.dispose()


app = FastAPI(
    title="StudyPilot User Service",
    version=settings.service_version,
    lifespan=lifespan,
)

# Register API route modules
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


@app.get("/health")
async def health():
    """Liveness probe – returns immediately if the process is running."""
    return {"status": "healthy", "service": settings.service_name}


@app.get("/ready")
async def ready():
    """Readiness probe – confirms the database is reachable."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503
