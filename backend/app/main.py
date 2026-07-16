"""
DKI Jakarta Tender Inspection Priority — FastAPI application entry point.

Interpretation boundary: scores represent inspection-priority ranking based on
anomaly detection. A high score means a package warrants earlier review, not that
fraud, corruption, collusion, bid-rigging, or legal wrongdoing has occurred.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.router import api_router
from backend.app.config import (
    ARTIFACT_DIR,
    CANONICAL_PATH,
    EVALUATION_PATH,
    EXPLANATIONS_PATH,
    FEATURES_PATH,
    MANIFEST_PATH,
    MODEL_CONFIG_PATH,
    PROJECT_ROOT,
    RANKING_PATH,
)
from backend.app.services.artifact_store import ArtifactStore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan — load and validate artifacts once at startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load artifacts at startup; yield to serve; no teardown needed (read-only)."""
    store = ArtifactStore.load(
        manifest_path=MANIFEST_PATH,
        ranking_path=RANKING_PATH,
        explanations_path=EXPLANATIONS_PATH,
        canonical_path=CANONICAL_PATH,
        features_path=FEATURES_PATH,
        evaluation_path=EVALUATION_PATH,
        model_config_path=MODEL_CONFIG_PATH,
        project_root=PROJECT_ROOT,
    )
    app.state.store = store
    app.state.artifact_dir = ARTIFACT_DIR
    logger.info("Application startup complete; model_version=%s", store.model_version)
    yield
    # Nothing to clean up — artifacts are read-only


# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------

_DESCRIPTION = (
    "Read-only API for the DKI Jakarta Government Tender Inspection Prioritization "
    "System. Anomaly scores reflect statistical unusualness relative to the 2024-2025 "
    "training baseline and are intended solely for ordering inspection workload. "
    "They do not constitute proof of fraud, corruption, collusion, bid-rigging, or any "
    "legal or administrative violation."
)

app = FastAPI(
    title="DKI Jakarta Tender Inspection Priority API",
    description=_DESCRIPTION,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.include_router(api_router)

# ---------------------------------------------------------------------------
# CORS — allowlist driven entirely by environment; no hardcoded origin
# ---------------------------------------------------------------------------

_cors_raw: str = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
_cors_origins: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ---------------------------------------------------------------------------
# Global Exception Handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )
