"""Ranked package endpoint with shared filtering and pagination."""

import math

from fastapi import APIRouter, Depends, Query

from backend.app.api.deps import get_artifact_store
from backend.app.schemas.common import ApiResponse, Meta
from backend.app.schemas.ranking import PaginationMeta, RankingRecord, RankingResponse
from backend.app.services.artifact_store import ArtifactStore
from backend.app.services.ranking_filters import filter_rankings

router = APIRouter()


@router.get("", response_model=ApiResponse[RankingResponse])
def get_rankings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    year: int | None = Query(None),
    work_unit: str | None = Query(None),
    procurement_method: str | None = Query(None),
    procurement_type: str | None = Query(None),
    supplier_name: str | None = Query(None),
    min_score: float | None = Query(None),
    max_score: float | None = Query(None),
    min_contract_value: float | None = Query(None, ge=0),
    max_contract_value: float | None = Query(None, ge=0),
    top_n: int | None = Query(None, ge=1),
    store: ArtifactStore = Depends(get_artifact_store),  # noqa: B008
) -> ApiResponse[RankingResponse]:
    """Return frozen anomaly ranking after active filters."""
    filters = {
        "year": year,
        "work_unit": work_unit,
        "procurement_method": procurement_method,
        "procurement_type": procurement_type,
        "supplier_name": supplier_name,
        "min_score": min_score,
        "max_score": max_score,
        "min_contract_value": min_contract_value,
        "max_contract_value": max_contract_value,
        "top_n": top_n,
    }
    filtered = filter_rankings(store.ranking, **filters)
    total_items = len(filtered)
    total_pages = max(1, math.ceil(total_items / size))
    start = (page - 1) * size
    page_frame = filtered.iloc[start : start + size]

    items = [
        RankingRecord(
            package_id=str(row.package_id),
            year=int(row.year),
            supplier_name=str(row.supplier_name),
            work_unit=str(row.work_unit),
            procurement_method=str(row.procurement_method),
            procurement_type=str(row.procurement_type),
            is_partial_snapshot_year=bool(row.is_partial_snapshot_year),
            split=str(row.split),
            contract_value=float(row.contract_value),
            anomaly_score=float(row.anomaly_score),
            anomaly_rank=int(row.anomaly_rank),
        )
        for row in page_frame.itertuples(index=False)
    ]
    data = RankingResponse(
        items=items,
        pagination=PaginationMeta(
            page=page,
            size=size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ),
    )
    return ApiResponse(
        data=data,
        meta=Meta(
            model_version=store.model_version,
            dataset_version=store.dataset_version,
            generated_at=store.generated_at,
            total_records=total_items,
            filters=filters,
        ),
    )
