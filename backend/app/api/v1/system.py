"""
System endpoints (health and metadata).
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from backend.app.api.deps import get_artifact_store
from backend.app.schemas.common import ApiResponse, Meta
from backend.app.schemas.system import HealthResponse, MetaResponse
from backend.app.services.artifact_store import ArtifactStore

router = APIRouter()


@router.get("/health", response_model=ApiResponse[HealthResponse])
def get_health(request: Request):
    """
    Check application health.
    Returns 200 OK if the process is alive and artifacts are loaded.
    Returns 503 if the process is alive but artifacts failed to load.
    """
    store = getattr(request.app.state, "store", None)
    is_ready = store is not None

    health_data = HealthResponse(
        status="ok" if is_ready else "error",
        process_alive=True,
        artifact_ready=is_ready,
    )

    response_payload = ApiResponse(
        data=health_data,
        meta=Meta(
            model_version=store.model_version if is_ready else "unknown",
            generated_at=store.generated_at if is_ready else "unknown",
        )
        if is_ready
        else None,
    )

    if not is_ready:
        return JSONResponse(status_code=503, content=response_payload.model_dump())

    return response_payload


@router.get("/meta", response_model=ApiResponse[MetaResponse])
def get_meta(store: ArtifactStore = Depends(get_artifact_store)):  # noqa: B008
    """
    Retrieve project and artifact metadata.
    """
    meta_data = MetaResponse(
        project_name=store.manifest.get("project_name", "dki-tender-inspection-priority"),
        model_version=store.model_version,
        schema_version=store.schema_version,
        generated_at=store.generated_at,
        artifact_count=store.manifest.get("integrity", {}).get("artifact_count", 0),
        total_records=store.manifest.get("summary", {}).get("total_record_count", 0),
        library_versions=store.manifest.get("model", {}).get("library_versions", {}),
    )

    return ApiResponse(
        data=meta_data,
        meta=Meta(
            model_version=store.model_version,
            generated_at=store.generated_at,
        ),
    )
