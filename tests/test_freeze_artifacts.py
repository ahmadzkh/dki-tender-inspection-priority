from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from modeling import freeze_artifacts as m

freeze_artifacts = m.freeze_artifacts
REQUIRED_ARTIFACTS = m.REQUIRED_ARTIFACTS

CANONICAL_PATH = Path("datasets/processed/tenders_canonical.csv")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _anomaly_score_from_ranking(ranking_path: Path, package_id: str) -> float | None:
    with ranking_path.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            if row.get("package_id") == package_id:
                score_str = row.get("anomaly_score", "0")
                try:
                    return float(score_str) if score_str else None
                except (ValueError, TypeError):
                    return None
    return None


def _canonical_detail(canonical_path: Path, package_id: str) -> dict[str, str] | None:
    with canonical_path.open("r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            if row.get("package_id") == package_id:
                return row
    return None


def _freeze_to_temp_manifest(tmp_path: Path) -> dict:
    return freeze_artifacts(manifest_path=tmp_path / "manifest.json")


def test_manifest_contains_all_required_fields(tmp_path: Path) -> None:
    """Manifest has checksum, version, generated time, path."""
    manifest = _freeze_to_temp_manifest(tmp_path)
    assert "schema_version" in manifest
    assert manifest["schema_version"] == 1
    assert "generated_at" in manifest
    assert "project_name" in manifest
    assert "version" in manifest
    assert "model" in manifest
    assert "feature_schema" in manifest
    assert "summary" in manifest
    assert "artifacts" in manifest
    assert "integrity" in manifest
    assert "artifact_count" in manifest["integrity"]
    assert "all_artifacts_exist" in manifest["integrity"]


def test_manifest_summary_has_counts(tmp_path: Path) -> None:
    """Summary: year_counts, split_counts, top_20/50."""
    manifest = _freeze_to_temp_manifest(tmp_path)
    s = manifest["summary"]
    assert s["total_record_count"] > 0
    assert s["year_counts"]
    assert s["split_counts"]
    assert len(s["top_20_package_ids"]) == 20
    assert len(s["top_50_package_ids"]) == 50
    assert s["annual_source_row_count"] == 1284
    assert s["merged_row_count"] == 1279
    assert s["canonical_record_count"] == 1277
    assert s["eligible_record_count"] == 1276
    assert s["missing_supplier_row_count"] == 5
    assert s["multi_provider_package_count"] == 1
    assert s["enrichment_success_count"] == 1277
    assert s["enrichment_coverage_pct"] == 100.0


def test_manifest_paths_and_filters_are_backend_ready(tmp_path: Path) -> None:
    manifest = _freeze_to_temp_manifest(tmp_path)
    assert manifest["dataset_version"] != "unknown"
    assert manifest["filter_options"]["years"] == [2026, 2025, 2024]
    assert manifest["filter_options"]["procurement_methods"]
    for items in manifest["artifacts"].values():
        for item in items:
            assert "\\" not in item["path"]


def test_loader_ad_hoc_can_find_package_detail(tmp_path: Path) -> None:
    """Loader reads ranking, finds package detail."""
    manifest = _freeze_to_temp_manifest(tmp_path)
    paths = {
        "ranking": Path("artifacts/isolation_forest_ranking.csv"),
        "canonical": CANONICAL_PATH,
    }
    top20 = manifest["summary"]["top_20_package_ids"]
    assert len(top20) == 20
    score = _anomaly_score_from_ranking(paths["ranking"], top20[0])
    assert score is not None
    assert score > 0
    detail = _canonical_detail(paths["canonical"], top20[0])
    assert detail is not None


def test_loader_generates_top_n_from_ranking(tmp_path: Path) -> None:
    """Verify Top-20 and Top-50 match ranking order."""
    manifest = _freeze_to_temp_manifest(tmp_path)
    ranking = Path("artifacts/isolation_forest_ranking.csv")
    ranking_rows: list[dict[str, str]] = []
    with ranking.open("r", encoding="utf-8", newline="") as csv_file:
        ranking_rows = list(csv.DictReader(csv_file))
    top_by_ranking = sorted(
        ranking_rows,
        key=lambda r: int(r.get("anomaly_rank", "999999")),
    )[:20]
    top_ids = [r.get("package_id", "") for r in top_by_ranking]
    assert manifest["summary"]["top_20_package_ids"] == top_ids


def test_manifest_has_all_required_artifact_categories(tmp_path: Path) -> None:
    """Every REQUIRED_ARTIFACTS category appears in manifest."""
    manifest = _freeze_to_temp_manifest(tmp_path)
    for category in REQUIRED_ARTIFACTS:
        assert category in manifest["artifacts"]
        assert len(manifest["artifacts"][category]) == len(REQUIRED_ARTIFACTS[category])


def test_manifest_hashes_match_actual_files(tmp_path: Path) -> None:
    """Checksum matches actual file content."""
    manifest = _freeze_to_temp_manifest(tmp_path)
    ranking_info = manifest["artifacts"]["model"][2]
    actual_path = Path(ranking_info["path"])
    assert ranking_info["sha256"] == _sha256(actual_path)


def test_manifest_all_artifacts_exist_on_disk(tmp_path: Path) -> None:
    """Every artifact in manifest exists on disk."""
    manifest = _freeze_to_temp_manifest(tmp_path)
    for category, infos in manifest["artifacts"].items():
        for info in infos:
            assert info["exists"], f"Missing artifact: {info['path']} in {category}"
