"""
System schemas for health and metadata endpoints.
"""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(frozen=True)

    status: str
    process_alive: bool
    artifact_ready: bool


class MetaResponse(BaseModel):
    """Project and artifact metadata."""

    model_config = ConfigDict(frozen=True)

    project_name: str
    dataset_version: str
    model_version: str
    schema_version: int
    generated_at: str
    artifact_count: int
    total_records: int
    annual_source_row_count: int
    merged_row_count: int
    canonical_record_count: int
    eligible_record_count: int
    missing_supplier_row_count: int
    multi_provider_package_count: int
    enrichment_success_count: int
    enrichment_coverage_pct: float
    library_versions: dict[str, str]
