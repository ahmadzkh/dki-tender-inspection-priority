"""
Schemas for ranking endpoint.
"""

from pydantic import BaseModel, ConfigDict


class RankingRecord(BaseModel):
    """A single package in the anomaly ranking."""

    model_config = ConfigDict(frozen=True)

    package_id: str
    year: int
    supplier_name: str
    work_unit: str
    procurement_method: str
    procurement_type: str
    is_partial_snapshot_year: bool
    split: str
    anomaly_score: float
    anomaly_rank: int


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""

    model_config = ConfigDict(frozen=True)

    page: int
    size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


class RankingResponse(BaseModel):
    """Paginated response for the ranking endpoint."""

    model_config = ConfigDict(frozen=True)

    items: list[RankingRecord]
    pagination: PaginationMeta
