"""
Dashboard summary and filter options endpoints.
"""

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_artifact_store
from backend.app.schemas.common import ApiResponse, Meta
from backend.app.schemas.dashboard import FilterOptionsResponse, ScoreBin, SummaryResponse
from backend.app.services.artifact_store import ArtifactStore

router = APIRouter()


@router.get("/summary", response_model=ApiResponse[SummaryResponse])
def get_summary(store: ArtifactStore = Depends(get_artifact_store)):  # noqa: B008
    """
    Retrieve aggregate statistics for the dashboard.
    """
    df = store.ranking

    # Packages by year with 2026 marked as snapshot
    year_counts = df["year"].value_counts().to_dict()
    packages_by_year = {}
    for y, count in sorted(year_counts.items()):
        label = f"{y} (Snapshot)" if y == 2026 else str(y)
        packages_by_year[label] = int(count)

    # Score distribution using fixed bins
    # Scores are typically distributed between somewhat normal ranges, let's use 10 bins
    # between min and max or just 0.0-0.1, 0.1-0.2, etc.
    min_score = float(df["anomaly_score"].min())
    max_score = float(df["anomaly_score"].max())

    # We can just create 5-10 equal-width bins
    import numpy as np

    bins = np.linspace(min_score, max_score, 11)
    counts, _ = np.histogram(df["anomaly_score"].astype(float), bins=bins)

    score_distribution = []
    for i in range(len(counts)):
        lower = bins[i]
        upper = bins[i + 1]
        score_distribution.append(
            ScoreBin(range_label=f"{lower:.2f} - {upper:.2f}", count=int(counts[i]))
        )

    data = SummaryResponse(
        total_packages=len(df),
        unique_suppliers=df["supplier_name"].nunique(),
        unique_work_units=df["work_unit"].nunique(),
        packages_by_year=packages_by_year,
        score_distribution=score_distribution,
    )

    return ApiResponse(
        data=data,
        meta=Meta(
            model_version=store.model_version,
            generated_at=store.generated_at,
        ),
    )


@router.get("/filters", response_model=ApiResponse[FilterOptionsResponse])
def get_filters(store: ArtifactStore = Depends(get_artifact_store)):  # noqa: B008
    """
    Retrieve available options for dashboard filters.
    """
    df = store.ranking

    years = sorted(df["year"].dropna().unique().tolist(), reverse=True)
    methods = sorted(df["procurement_method"].dropna().unique().tolist())
    types = sorted(df["procurement_type"].dropna().unique().tolist())
    units = sorted(df["work_unit"].dropna().unique().tolist())

    data = FilterOptionsResponse(
        years=[int(y) for y in years],
        procurement_methods=[str(m) for m in methods],
        procurement_types=[str(t) for t in types],
        work_units=[str(u) for u in units],
    )

    return ApiResponse(
        data=data,
        meta=Meta(
            model_version=store.model_version,
            generated_at=store.generated_at,
        ),
    )
