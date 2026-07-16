"""Precomputed model evaluation endpoint."""

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_artifact_store
from backend.app.schemas.common import ApiResponse, Meta
from backend.app.services.artifact_store import ArtifactStore

router = APIRouter()


@router.get("", response_model=ApiResponse[dict[str, Any]])
def get_evaluation(
    store: ArtifactStore = Depends(get_artifact_store),  # noqa: B008
) -> ApiResponse[dict[str, Any]]:
    """Return evaluation artifacts validated and loaded during startup."""
    return ApiResponse(
        data={
            "evaluation": store.evaluation,
            "model_config": store.model_config,
        },
        meta=Meta(
            model_version=store.model_version,
            dataset_version=store.dataset_version,
            generated_at=store.generated_at,
        ),
    )
