"""
Export endpoint.
"""

import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from backend.app.api.deps import get_artifact_store
from backend.app.services.artifact_store import ArtifactStore

router = APIRouter()

DISCLAIMER = (
    "# DISCLAIMER: Sistem ini hanya memberikan prioritas pemeriksaan berdasarkan pola data "
    "dan tidak dapat digunakan sebagai bukti fraud atau pelanggaran hukum."
)


@router.get(".csv", response_class=StreamingResponse)
def export_csv(
    year: int | None = Query(None, description="Filter by year"),
    work_unit: str | None = Query(None, description="Filter by work unit (substring match)"),
    procurement_method: str | None = Query(None, description="Filter by procurement method"),
    procurement_type: str | None = Query(None, description="Filter by procurement type"),
    supplier_name: str | None = Query(
        None, description="Filter by supplier name (substring match)"
    ),
    min_score: float | None = Query(None, description="Minimum anomaly score"),
    max_score: float | None = Query(None, description="Maximum anomaly score"),
    store: ArtifactStore = Depends(get_artifact_store),  # noqa: B008
) -> StreamingResponse:
    """
    Export ranking to CSV, matching the active filters.
    """
    df = store.ranking

    # Apply filters
    if year is not None:
        df = df[df["year"] == year]
    if work_unit:
        df = df[df["work_unit"].str.contains(work_unit, case=False, na=False)]
    if procurement_method:
        df = df[df["procurement_method"] == procurement_method]
    if procurement_type:
        df = df[df["procurement_type"] == procurement_type]
    if supplier_name:
        df = df[df["supplier_name"].str.contains(supplier_name, case=False, na=False)]
    if min_score is not None:
        df = df[df["anomaly_score"] >= min_score]
    if max_score is not None:
        df = df[df["anomaly_score"] <= max_score]

    # The dataframe is already sorted by anomaly_score DESC in ArtifactStore.

    # We need to serialize this to a CSV string buffer.
    # To include the disclaimer, we can write it as a comment at the top, or in metadata.
    # Standard CSV doesn't have comments natively, but often people put it in the first line.

    output = io.StringIO()
    output.write(DISCLAIMER + "\n")

    # We will export specific columns to match the API response.
    export_cols = [
        "package_id",
        "year",
        "supplier_name",
        "work_unit",
        "procurement_method",
        "procurement_type",
        "is_partial_snapshot_year",
        "anomaly_score",
        "anomaly_rank",
    ]
    df_export = df[export_cols]

    df_export.to_csv(output, index=False)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=dki_tender_ranking.csv"},
    )
