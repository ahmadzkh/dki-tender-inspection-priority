"""
DKI Jakarta Tender Inspection Priority — FastAPI application entry point.

Interpretation boundary: scores represent inspection-priority ranking based on
anomaly detection. A high score means a package warrants earlier review, not that
fraud, corruption, collusion, bid-rigging, or legal wrongdoing has occurred.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
)

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
