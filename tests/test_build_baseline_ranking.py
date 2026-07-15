from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modeling.build_baseline_ranking import build_baseline_ranking  # noqa: E402

METADATA_COLUMNS = [
    "package_id",
    "year",
    "supplier_name",
    "work_unit",
    "procurement_method",
    "procurement_type",
    "is_partial_snapshot_year",
]
FEATURE_COLUMNS = ["log_contract_value", "contract_to_hps_ratio"]


def _write_feature_csv(path: Path) -> None:
    rows = [
        _row("train-normal-a", "2024", "10.0", "0.90"),
        _row("train-normal-b", "2025", "10.2", "0.92"),
        _row("eval-normal", "2026", "10.1", "0.91"),
        _row("eval-extreme", "2026", "25.0", "2.50"),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=METADATA_COLUMNS + FEATURE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row(package_id: str, year: str, log_value: str, ratio: str) -> dict[str, str]:
    return {
        "package_id": package_id,
        "year": year,
        "supplier_name": "Supplier " + package_id,
        "work_unit": "Satker A",
        "procurement_method": "Tender",
        "procurement_type": "Jasa Lainnya",
        "is_partial_snapshot_year": "true" if year == "2026" else "false",
        "log_contract_value": log_value,
        "contract_to_hps_ratio": ratio,
    }


def _write_split_manifest(path: Path, feature_csv: Path) -> None:
    manifest = {
        "schema_version": 1,
        "strategy": "temporal_holdout",
        "feature_matrix": {
            "path": feature_csv.as_posix(),
            "sha256": "fixture-sha",
            "row_count": 4,
            "feature_count": len(FEATURE_COLUMNS),
            "feature_columns": FEATURE_COLUMNS,
            "metadata_columns": METADATA_COLUMNS,
        },
        "splits": {
            "train": {
                "years": ["2024", "2025"],
                "row_count": 2,
                "package_ids": ["train-normal-a", "train-normal-b"],
            },
            "evaluation": {
                "years": ["2026"],
                "row_count": 2,
                "package_ids": ["eval-normal", "eval-extreme"],
            },
        },
        "excluded_records": {"row_count": 0, "records": []},
        "leakage_policy": {
            "evaluation_rows_used_for_training": False,
            "aggregate_features_are_prior_observation_only": True,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _read_ranking(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def test_baseline_scores_extreme_record_above_normal_and_has_no_label(tmp_path: Path) -> None:
    feature_csv = tmp_path / "datasets" / "processed" / "model_features.csv"
    split_manifest = tmp_path / "datasets" / "manifests" / "model_split.json"
    output_csv = tmp_path / "artifacts" / "baseline_ranking.csv"
    config_json = tmp_path / "artifacts" / "baseline_config.json"
    report_md = tmp_path / "reports" / "model" / "baseline.md"
    _write_feature_csv(feature_csv)
    _write_split_manifest(split_manifest, feature_csv)

    result = build_baseline_ranking(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest,
        output_csv=output_csv,
        config_json=config_json,
        report_md=report_md,
        project_root=tmp_path,
    )

    rows = _read_ranking(output_csv)
    by_id = {row["package_id"]: row for row in rows}
    assert result["row_count"] == 4
    assert result["method"] == "robust_zscore_topk_mean"
    assert float(by_id["eval-extreme"]["baseline_score"]) > float(
        by_id["eval-normal"]["baseline_score"]
    )
    assert by_id["eval-extreme"]["baseline_rank"] == "1"
    assert by_id["eval-extreme"]["split"] == "evaluation"
    assert by_id["train-normal-a"]["split"] == "train"
    assert "fraud" not in {column.lower() for column in rows[0]}
    assert rows[0]["top_feature_1"] in FEATURE_COLUMNS

    config = json.loads(config_json.read_text(encoding="utf-8"))
    assert config["feature_matrix"] == "datasets/processed/model_features.csv"
    assert config["feature_columns"] == FEATURE_COLUMNS
    assert config["score_direction"] == "higher score means higher inspection priority"
    assert "limitations" in config and config["limitations"]

    report = report_md.read_text(encoding="utf-8")
    assert "transparent baseline" in report
    assert "not a legal conclusion" in report


def test_baseline_ranking_is_deterministic(tmp_path: Path) -> None:
    feature_csv = tmp_path / "datasets" / "processed" / "model_features.csv"
    split_manifest = tmp_path / "datasets" / "manifests" / "model_split.json"
    output_a = tmp_path / "artifacts" / "baseline_ranking_a.csv"
    output_b = tmp_path / "artifacts" / "baseline_ranking_b.csv"
    config_a = tmp_path / "artifacts" / "baseline_config_a.json"
    config_b = tmp_path / "artifacts" / "baseline_config_b.json"
    report_a = tmp_path / "reports" / "model" / "baseline_a.md"
    report_b = tmp_path / "reports" / "model" / "baseline_b.md"
    _write_feature_csv(feature_csv)
    _write_split_manifest(split_manifest, feature_csv)

    build_baseline_ranking(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest,
        output_csv=output_a,
        config_json=config_a,
        report_md=report_a,
        project_root=tmp_path,
    )
    build_baseline_ranking(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest,
        output_csv=output_b,
        config_json=config_b,
        report_md=report_b,
        project_root=tmp_path,
    )

    assert output_a.read_text(encoding="utf-8") == output_b.read_text(encoding="utf-8")
    config_a_payload = json.loads(config_a.read_text(encoding="utf-8"))
    config_b_payload = json.loads(config_b.read_text(encoding="utf-8"))
    assert config_a_payload["method"] == config_b_payload["method"]
    assert config_a_payload["feature_statistics"] == config_b_payload["feature_statistics"]
