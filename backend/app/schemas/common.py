"""
Common Pydantic response schemas for the DKI Jakarta Tender Inspection API.

All API responses use the ApiResponse envelope:
    {
        "data": <payload or null>,
        "meta": { "model_version": ..., ... },
        "error": <null or ErrorDetail>
    }

Interpretation contract:
  - `score_direction` in Meta signals that higher score = higher inspection priority.
  - `disclaimer` must accompany any ranked output visible to end users.
  - Null fields remain null; they must not be coerced to zero or empty string.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Shared interpretation constants (propagated into Meta responses)
# ---------------------------------------------------------------------------

SCORE_DIRECTION = "higher score means higher inspection priority"

DISCLAIMER = (
    "Scores represent statistical unusualness relative to the 2024-2025 training "
    "baseline and are intended solely for ordering inspection workload. They do not "
    "constitute proof of fraud, corruption, collusion, bid-rigging, or any legal or "
    "administrative violation."
)


# ---------------------------------------------------------------------------
# Schema types
# ---------------------------------------------------------------------------


class Meta(BaseModel):
    """Version and provenance metadata attached to every successful response."""

    model_config = ConfigDict(frozen=True)

    model_version: str
    dataset_version: str
    generated_at: str
    score_direction: str = SCORE_DIRECTION
    disclaimer: str = DISCLAIMER
    total_records: int | None = None
    filters: dict | None = None


class ErrorDetail(BaseModel):
    """Safe error payload — never contains stack traces or local paths."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str


class ApiResponse(BaseModel, Generic[T]):
    """Envelope for all API endpoints."""

    model_config = ConfigDict(frozen=True)

    data: T | None = None
    meta: Meta | None = None
    error: ErrorDetail | None = None
