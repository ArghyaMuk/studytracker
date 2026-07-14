import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.middleware.auth import verify_jwt_middleware
from app.middleware.rate_limiter import check_rate_limit

app = FastAPI(
    title="StudyPilot API Gateway",
    version="1.0.0",
    description="Single entry point for all StudyPilot services",
)

# CORS - allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route prefix -> downstream service URL
ROUTE_MAP = {
    "/api/v1/auth": settings.user_service_url,
    "/api/v1/users": settings.user_service_url,
    "/api/v1/programs": settings.curriculum_service_url,
    "/api/v1/subjects": settings.curriculum_service_url,
    "/api/v1/materials": settings.curriculum_service_url,
    "/api/v1/admin/materials": settings.curriculum_service_url,
    "/api/v1/admin/programs": settings.curriculum_service_url,
    "/api/v1/admin/quizzes": settings.quiz_service_url,
    "/api/v1/admin": settings.curriculum_service_url,
    "/api/v1/sessions": settings.session_service_url,
    "/api/v1/revision": settings.repetition_service_url,
    "/api/v1/quizzes": settings.quiz_service_url,
    "/api/v1/pyq": settings.quiz_service_url,
    "/api/v1/readiness": settings.readiness_service_url,
    "/api/v1/notifications": settings.notification_service_url,
}


def resolve_upstream(path: str) -> str | None:
    """Find the upstream service URL for a given path."""
    for prefix, url in ROUTE_MAP.items():
        if path.startswith(prefix):
            return url
    return None


@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(request: Request, path: str):
    """Reverse proxy to downstream services."""
    full_path = f"/api/v1/{path}"

    # JWT verification
    user_payload = await verify_jwt_middleware(request)

    # Rate limiting
    user_id = user_payload.get("sub") if user_payload else None
    await check_rate_limit(request, user_id)

    # Resolve upstream
    upstream_url = resolve_upstream(full_path)
    if not upstream_url:
        return JSONResponse(status_code=404, content={"detail": "Service not found"})

    # Build target URL
    target_url = f"{upstream_url}{full_path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Forward request
    headers = dict(request.headers)
    headers.pop("host", None)
    if user_payload:
        headers["X-User-Id"] = str(user_payload.get("sub", ""))
        headers["X-User-Email"] = user_payload.get("email", "")
        headers["X-User-Role"] = user_payload.get("role", "student")

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=502, content={"detail": "Upstream service timeout"}
        )
    except httpx.ConnectError:
        return JSONResponse(
            status_code=502, content={"detail": "Upstream service unavailable"}
        )


@app.get("/health")
async def health():
    """Consolidated health check."""
    services = {
        "user-service": settings.user_service_url,
        "curriculum-service": settings.curriculum_service_url,
        "session-service": settings.session_service_url,
        "repetition-service": settings.repetition_service_url,
        "quiz-service": settings.quiz_service_url,
        "readiness-service": settings.readiness_service_url,
        "notification-service": settings.notification_service_url,
    }

    statuses = {}
    all_healthy = True
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in services.items():
            try:
                resp = await client.get(f"{url}/health")
                statuses[name] = "healthy" if resp.status_code == 200 else "unhealthy"
            except Exception:
                statuses[name] = "unhealthy"
                all_healthy = False

    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": statuses,
    }
