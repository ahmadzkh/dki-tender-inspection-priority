"""
Schemas for package detail endpoint.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict


class SourceDetail(BaseModel):
    """Source details for a package."""

    model_config = ConfigDict(frozen=True)

    package_name: str | None
    url: str | None
    contract_value: float | None
    hps: float | None
    pagu: float | None


class EnrichmentDetail(BaseModel):
    """Enrichment details for a package."""

    model_config = ConfigDict(frozen=True)

    jadwal: list[dict[str, Any]] | None
    metadata: dict[str, Any] | None


class ScoreDetail(BaseModel):
    """Score details for a package."""

    model_config = ConfigDict(frozen=True)

    anomaly_score: float
    anomaly_rank: int


class PackageDetailResponse(BaseModel):
    """Full detail response for a single package."""

    model_config = ConfigDict(frozen=True)

    package_id: str
    year: int
    supplier_name: str
    work_unit: str
    procurement_method: str
    procurement_type: str
    is_partial_snapshot_year: bool

    source: SourceDetail
    enrichment: EnrichmentDetail
    features: dict[str, float]
    score: ScoreDetail
    explanation: dict[str, Any] | None
