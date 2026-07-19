"""
API Gateway – Single entry point for all StudyPilot microservices.

This module implements a reverse-proxy pattern: every incoming request is
matched against a prefix-based route map, authenticated via JWT, rate-limited,
and then forwarded to the appropriate downstream service. It also exposes a
consolidated health-check endpoint that polls every registered service.
"""

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

# ── CORS Configuration ──
# Allow the Flask frontend (port 3000) to make cross-origin requests.
# Credentials are enabled so session cookies / Authorization headers pass through.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route Map ──
# Maps URL path prefixes to the internal service base URLs.
# Order matters: more specific prefixes (e.g. /admin/quizzes) must appear
# before shorter ones (e.g. /admin) so they match first.
ROUTE_MAP = {
    "/api/v1/auth": settings.user_service_url,
    "/api/v1/users": settings.user_service_url,
    "/api/v1/programs": settings.curriculum_service_url,
    "/api/v1/subjects": settings.curriculum_service_url,
    "/api/v1/materials": settings.curriculum_service_url,
    "/api/v1/exams": settings.curriculum_service_url,
    "/api/v1/enrollments": settings.curriculum_service_url,
    "/api/v1/admin/enrollments": settings.curriculum_service_url,
    "/api/v1/admin/exams": settings.curriculum_service_url,
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
    """Find the upstream service URL for a given request path.

    Iterates through ROUTE_MAP and returns the first matching service URL,
    or None if no prefix matches (resulting in a 404 to the client).
    """
    for prefix, url in ROUTE_MAP.items():
        if path.startswith(prefix):
            return url
    return None


@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(request: Request, path: str):
    """Reverse-proxy handler: authenticates, rate-limits, and forwards requests."""
    full_path = f"/api/v1/{path}"

    # Step 1: Verify JWT – returns decoded payload or None for public routes
    user_payload = await verify_jwt_middleware(request)

    # Step 2: Rate limiting – keyed by user_id (or IP for anonymous requests)
    user_id = user_payload.get("sub") if user_payload else None
    await check_rate_limit(request, user_id)

    # Step 3: Resolve which downstream service should handle this path
    upstream_url = resolve_upstream(full_path)
    if not upstream_url:
        return JSONResponse(status_code=404, content={"detail": "Service not found"})

    # Step 4: Build the full target URL, preserving the original query string
    target_url = f"{upstream_url}{full_path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Step 5: Prepare forwarded headers – inject user identity for downstream services
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove original Host header to avoid routing issues
    if user_payload:
        # Downstream services use these headers to identify the caller
        headers["X-User-Id"] = str(user_payload.get("sub", ""))
        headers["X-User-Email"] = user_payload.get("email", "")
        headers["X-User-Role"] = user_payload.get("role", "student")

    body = await request.body()

    # Step 6: Forward the request and relay the response back to the client
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
    """Aggregated health check – polls every registered service and reports overall status.

    Returns "healthy" only if all downstream services respond 200;
    otherwise returns "degraded" with per-service breakdown.
    """
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
