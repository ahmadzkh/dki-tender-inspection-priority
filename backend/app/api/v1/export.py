"""Filter-consistent CSV export endpoint."""

import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from backend.app.api.deps import get_artifact_store
from backend.app.services.artifact_store import ArtifactStore
from backend.app.services.ranking_filters import filter_rankings

router = APIRouter()

DISCLAIMER = (
    "# DISCLAIMER: Sistem ini hanya memberikan prioritas pemeriksaan berdasarkan pola data "
    "dan tidak dapat digunakan sebagai bukti fraud atau pelanggaran hukum."
)


@router.get(".csv", response_class=StreamingResponse)
def export_csv(
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
) -> StreamingResponse:
    """Export ranking with the same filters and order as the JSON endpoint."""
    filtered = filter_rankings(
        store.ranking,
        year=year,
        work_unit=work_unit,
        procurement_method=procurement_method,
        procurement_type=procurement_type,
        supplier_name=supplier_name,
        min_score=min_score,
        max_score=max_score,
        min_contract_value=min_contract_value,
        max_contract_value=max_contract_value,
        top_n=top_n,
    )
    output = io.StringIO()
    output.write(DISCLAIMER + "\n")
    filtered[
        [
            "package_id",
            "year",
            "supplier_name",
            "work_unit",
            "procurement_method",
            "procurement_type",
            "is_partial_snapshot_year",
            "contract_value",
            "anomaly_score",
            "anomaly_rank",
        ]
    ].to_csv(output, index=False)

    filename = f"dki_tender_ranking_{store.model_version}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Model-Version": store.model_version,
            "X-Dataset-Version": store.dataset_version,
        },
    )
