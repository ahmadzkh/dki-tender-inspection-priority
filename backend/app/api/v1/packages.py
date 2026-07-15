"""
Package detail endpoint.
"""

import json
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_artifact_store
from backend.app.schemas.common import ApiResponse, Meta
from backend.app.schemas.package import (
    EnrichmentDetail,
    PackageDetailResponse,
    ScoreDetail,
    SourceDetail,
)
from backend.app.services.artifact_store import ArtifactStore

router = APIRouter()

DISCLAIMER = (
    "Sistem ini hanya memberikan prioritas pemeriksaan berdasarkan pola data "
    "dan tidak dapat digunakan sebagai bukti fraud atau pelanggaran hukum."
)


def _safe_float(val: Any) -> float | None:
    if pd.isna(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _parse_json(val: Any) -> Any:
    if pd.isna(val) or not val:
        return None
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return None
    return val


@router.get("/{package_id}", response_model=ApiResponse[PackageDetailResponse])
def get_package_detail(
    package_id: str,
    store: ArtifactStore = Depends(get_artifact_store),  # noqa: B008
):
    """
    Retrieve full details for a single package.
    """
    df = store.ranking
    # Find ranking row
    ranking_row = df[df["package_id"].astype(str) == package_id]
    if ranking_row.empty:
        raise HTTPException(status_code=404, detail=f"Package {package_id} not found in ranking.")
    ranking_data = ranking_row.iloc[0]

    # Get explanation
    explanation = store.explanations_by_id.get(package_id)

    # Get features
    feature_row = store.features_by_id.get(package_id, {})
    features_dict = {}
    for k, v in feature_row.items():
        if k not in ("package_id", "year", "split", "is_partial_snapshot_year"):
            val = _safe_float(v)
            if val is not None:
                features_dict[k] = val

    # Get canonical data
    canonical_row = store.canonical_by_id.get(package_id, {})

    # Construct SourceDetail
    package_name = canonical_row.get("package_name")
    if pd.isna(package_name):
        package_name = None
    if package_id.endswith("127"):
        url = f"https://lpse.jakarta.go.id/eproc4/lelang/{package_id}/pengumumanlelang"
    else:
        url = None

    source_detail = SourceDetail(
        package_name=str(package_name) if package_name else None,
        url=url,
        contract_value=_safe_float(canonical_row.get("contract_value")),
        hps=_safe_float(canonical_row.get("hps")),
        pagu=_safe_float(canonical_row.get("pagu")),
    )

    # Construct EnrichmentDetail
    enrichment_detail = EnrichmentDetail(
        jadwal=_parse_json(canonical_row.get("jadwal_json")),
        metadata=_parse_json(canonical_row.get("metadata_json")),
    )

    # Construct ScoreDetail
    score_detail = ScoreDetail(
        anomaly_score=float(ranking_data["anomaly_score"]),
        anomaly_rank=int(ranking_data["anomaly_rank"]),
    )

    def _safe_str(val: Any) -> str:
        return str(val) if not pd.isna(val) else ""

    data = PackageDetailResponse(
        package_id=package_id,
        year=int(ranking_data["year"]),
        supplier_name=_safe_str(ranking_data["supplier_name"]),
        work_unit=_safe_str(ranking_data["work_unit"]),
        procurement_method=_safe_str(ranking_data["procurement_method"]),
        procurement_type=_safe_str(ranking_data["procurement_type"]),
        is_partial_snapshot_year=bool(ranking_data["is_partial_snapshot_year"]),
        source=source_detail,
        enrichment=enrichment_detail,
        features=features_dict,
        score=score_detail,
        explanation=explanation,
    )

    return ApiResponse(
        data=data,
        meta=Meta(
            model_version=store.model_version,
            generated_at=store.generated_at,
            disclaimer=DISCLAIMER,
        ),
    )
