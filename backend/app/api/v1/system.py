"""System endpoints (health and metadata)."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from backend.app.api.deps import get_artifact_store
from backend.app.schemas.common import ApiResponse, Meta
from backend.app.schemas.system import HealthResponse, MetaResponse
from backend.app.services.artifact_store import ArtifactStore

router = APIRouter()


def _meta(store: ArtifactStore) -> Meta:
    return Meta(
        model_version=store.model_version,
        dataset_version=store.dataset_version,
        generated_at=store.generated_at,
    )


@router.get("/health", response_model=ApiResponse[HealthResponse])
def get_health(request: Request):
    """Return process and artifact readiness separately."""
    store = getattr(request.app.state, "store", None)
    is_ready = store is not None
    payload = ApiResponse(
        data=HealthResponse(
            status="ok" if is_ready else "error",
            process_alive=True,
            artifact_ready=is_ready,
        ),
        meta=_meta(store) if is_ready else None,
    )
    if not is_ready:
        return JSONResponse(status_code=503, content=payload.model_dump())
    return payload


@router.get("/meta", response_model=ApiResponse[MetaResponse])
def get_meta(store: ArtifactStore = Depends(get_artifact_store)):  # noqa: B008
    """Return public dataset, artifact, and model metadata without local paths."""
    summary = store.manifest["summary"]
    data = MetaResponse(
        project_name=store.manifest.get("project_name", "dki-tender-inspection-priority"),
        dataset_version=store.dataset_version,
        model_version=store.model_version,
        schema_version=store.schema_version,
        generated_at=store.generated_at,
        artifact_count=store.manifest["integrity"]["artifact_count"],
        total_records=summary["total_record_count"],
        annual_source_row_count=summary["annual_source_row_count"],
        merged_row_count=summary["merged_row_count"],
        canonical_record_count=summary["canonical_record_count"],
        eligible_record_count=summary["eligible_record_count"],
        missing_supplier_row_count=summary["missing_supplier_row_count"],
        multi_provider_package_count=summary["multi_provider_package_count"],
        enrichment_success_count=summary["enrichment_success_count"],
        enrichment_coverage_pct=summary["enrichment_coverage_pct"],
        library_versions=store.manifest.get("model", {}).get("library_versions", {}),
    )
    return ApiResponse(data=data, meta=_meta(store))
