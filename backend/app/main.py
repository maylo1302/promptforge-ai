from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1 import admin, auth, dashboard, prompts, users
from app.core.config import settings
from app.core.rate_limit import rate_limiter
from app.db import Base, engine
from app import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Produkcja używa Alembic; create_all przyspiesza pierwsze uruchomienie lokalne.
    if not settings.is_production:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="PromptForge AI API", version="0.1.0", docs_url="/docs", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"], max_age=600)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.url.path not in {"/health", "/healthz"}:
        try:
            rate_limiter.check(request)
        except Exception as exc:
            if hasattr(exc, "status_code"):
                return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
            raise
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    return response


@app.get("/health", tags=["System"])
@app.get("/healthz", include_in_schema=False)
def health() -> dict[str, str]:
    return {"status": "ok", "service": "promptforge-api"}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
