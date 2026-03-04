from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.api.v1 import auth, evidence, analysis, admin

configure_logging()

app = FastAPI(
    title="CS Forensics — Evidence Tampering Detection API",
    description="Forensic-grade REST API for detecting tampering in digital images and videos.",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url="/redoc" if settings.APP_ENV == "development" else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,     prefix="/api/v1/auth",     tags=["Authentication"])
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["Evidence"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(admin.router,    prefix="/api/v1/admin",    tags=["Admin"])


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "service": "forensics-backend"}


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
