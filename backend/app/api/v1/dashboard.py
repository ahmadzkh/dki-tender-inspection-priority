"""Dashboard summary and filter options endpoints."""

import numpy as np
from fastapi import APIRouter, Depends

from backend.app.api.deps import get_artifact_store
from backend.app.schemas.common import ApiResponse, Meta
from backend.app.schemas.dashboard import FilterOptionsResponse, ScoreBin, SummaryResponse
from backend.app.services.artifact_store import ArtifactStore

router = APIRouter()


def _meta(store: ArtifactStore) -> Meta:
    return Meta(
        model_version=store.model_version,
        dataset_version=store.dataset_version,
        generated_at=store.generated_at,
    )


@router.get("/summary", response_model=ApiResponse[SummaryResponse])
def get_summary(store: ArtifactStore = Depends(get_artifact_store)):  # noqa: B008
    """Return aggregate dashboard statistics from frozen artifacts."""
    df = store.ranking
    year_counts = df["year"].value_counts().to_dict()
    packages_by_year = {
        f"{year} (Snapshot)" if year == 2026 else str(year): int(count)
        for year, count in sorted(year_counts.items())
    }

    bins = np.linspace(
        float(df["anomaly_score"].min()),
        float(df["anomaly_score"].max()),
        11,
    )
    counts, _ = np.histogram(df["anomaly_score"].astype(float), bins=bins)
    score_distribution = [
        ScoreBin(
            range_label=f"{bins[index]:.2f} - {bins[index + 1]:.2f}",
            count=int(count),
        )
        for index, count in enumerate(counts)
    ]

    data = SummaryResponse(
        total_packages=len(df),
        total_contract_value=float(df["contract_value"].sum()),
        unique_suppliers=df["supplier_name"].nunique(),
        unique_work_units=df["work_unit"].nunique(),
        packages_by_year=packages_by_year,
        score_distribution=score_distribution,
    )
    return ApiResponse(data=data, meta=_meta(store))


@router.get("/filters", response_model=ApiResponse[FilterOptionsResponse])
def get_filters(store: ArtifactStore = Depends(get_artifact_store)):  # noqa: B008
    """Return stable filter options frozen in the artifact manifest."""
    options = store.manifest["filter_options"]
    data = FilterOptionsResponse(
        years=options["years"],
        procurement_methods=options["procurement_methods"],
        procurement_types=options["procurement_types"],
        work_units=options["work_units"],
    )
    return ApiResponse(data=data, meta=_meta(store))
