from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.v1 import auth, users
from app.core.config import settings
from app.core.db import engine, async_session_factory
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (use migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Bootstrap admin account if not exists
    from app.repositories import UserRepository
    from app.models import User, UserProfile
    from shared.auth import hash_password

    async with async_session_factory() as db:
        repo = UserRepository(db)
        admin = await repo.get_by_email("admin@studypilot.com")
        if not admin:
            admin_user = User(
                name="Admin User",
                email="admin@studypilot.com",
                password_hash=hash_password("Admin@1234"),
                college="StudyPilot",
                university="StudyPilot",
                current_semester=1,
            )
            admin_user = await repo.create(admin_user)
            await repo.create_profile(UserProfile(
                user_id=admin_user.id,
                daily_study_hours_target=2.0,
                goal_type="semester_exam",
            ))

    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="StudyPilot User Service",
    version=settings.service_version,
    lifespan=lifespan,
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


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
