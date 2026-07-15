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
    model_version: str
    schema_version: int
    generated_at: str
    artifact_count: int
    total_records: int
    library_versions: dict[str, str]
