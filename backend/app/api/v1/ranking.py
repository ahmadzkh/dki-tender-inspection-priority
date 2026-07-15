"""
Ranking list endpoint with filtering and pagination.
"""

import math

from fastapi import APIRouter, Depends, Query

from backend.app.api.deps import get_artifact_store
from backend.app.schemas.common import ApiResponse, Meta
from backend.app.schemas.ranking import PaginationMeta, RankingRecord, RankingResponse
from backend.app.services.artifact_store import ArtifactStore

router = APIRouter()


@router.get("", response_model=ApiResponse[RankingResponse])
def get_rankings(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    year: int | None = Query(None, description="Filter by year"),
    work_unit: str | None = Query(None, description="Filter by work unit (substring match)"),
    procurement_method: str | None = Query(None, description="Filter by procurement method"),
    procurement_type: str | None = Query(None, description="Filter by procurement type"),
    supplier_name: str | None = Query(
        None, description="Filter by supplier name (substring match)"
    ),
    min_score: float | None = Query(None, description="Minimum anomaly score"),
    max_score: float | None = Query(None, description="Maximum anomaly score"),
    top_n: int | None = Query(
        None, ge=1, description="Limit to top N highest scores before pagination"
    ),
    store: ArtifactStore = Depends(get_artifact_store),  # noqa: B008
):
    """
    Retrieve ranked packages with optional filtering, sorting by anomaly_score DESC by default.
    """
    df = store.ranking

    # Apply filters
    if year is not None:
        df = df[df["year"] == year]
    if work_unit:
        # Case-insensitive substring match
        df = df[df["work_unit"].str.contains(work_unit, case=False, na=False)]
    if procurement_method:
        df = df[df["procurement_method"] == procurement_method]
    if procurement_type:
        df = df[df["procurement_type"] == procurement_type]
    if supplier_name:
        # Case-insensitive substring match
        df = df[df["supplier_name"].str.contains(supplier_name, case=False, na=False)]
    if min_score is not None:
        df = df[df["anomaly_score"] >= min_score]
    if max_score is not None:
        df = df[df["anomaly_score"] <= max_score]

    # The dataframe is already sorted by anomaly_score DESC in ArtifactStore.
    # Apply top_n before pagination if requested
    if top_n is not None:
        df = df.head(top_n)

    total_items = len(df)
    total_pages = max(1, math.ceil(total_items / size)) if total_items > 0 else 1

    # Apply pagination
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_df = df.iloc[start_idx:end_idx]

    # Map to schema
    items = []
    for _, row in page_df.iterrows():
        items.append(
            RankingRecord(
                package_id=str(row["package_id"]),
                year=int(row["year"]),
                supplier_name=str(row["supplier_name"]) if not row.isna()["supplier_name"] else "",
                work_unit=str(row["work_unit"]) if not row.isna()["work_unit"] else "",
                procurement_method=str(row["procurement_method"])
                if not row.isna()["procurement_method"]
                else "",
                procurement_type=str(row["procurement_type"])
                if not row.isna()["procurement_type"]
                else "",
                is_partial_snapshot_year=bool(row["is_partial_snapshot_year"]),
                split=str(row["split"]),
                anomaly_score=float(row["anomaly_score"]),
                anomaly_rank=int(row["anomaly_rank"]),
            )
        )

    pagination = PaginationMeta(
        page=page,
        size=size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )

    data = RankingResponse(items=items, pagination=pagination)

    return ApiResponse(
        data=data,
        meta=Meta(
            model_version=store.model_version,
            generated_at=store.generated_at,
            total_records=total_items,
            filters={
                "year": year,
                "work_unit": work_unit,
                "procurement_method": procurement_method,
                "procurement_type": procurement_type,
                "supplier_name": supplier_name,
                "min_score": min_score,
                "max_score": max_score,
                "top_n": top_n,
            },
        ),
    )
