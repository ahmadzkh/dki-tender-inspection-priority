from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.build_canonical_dataset import CANONICAL_COLUMNS  # noqa: E402
from pipelines.define_model_split import define_model_split  # noqa: E402

METADATA_COLUMNS = [
    "package_id",
    "year",
    "supplier_name",
    "work_unit",
    "procurement_method",
    "procurement_type",
    "is_partial_snapshot_year",
]
FEATURE_COLUMNS = [
    "log_contract_value",
    "contract_to_hps_ratio",
    "supplier_prior_package_count_year",
]


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _canonical_row(
    *, package_id: str, year: str, eligible: str, status: str = "single_source_row"
) -> dict[str, str]:
    row = {column: "" for column in CANONICAL_COLUMNS}
    row.update(
        {
            "package_id": package_id,
            "year": year,
            "supplier_name": "Supplier " + package_id,
            "work_unit": "Satker A",
            "procurement_method": "Tender",
            "procurement_type": "Jasa Lainnya",
            "eligible_for_model": eligible,
            "is_multi_provider": "false" if eligible == "true" else "true",
            "canonicalization_status": status,
        }
    )
    return row


def _feature_row(package_id: str, year: str, prior_count: str = "0") -> dict[str, str]:
    return {
        "package_id": package_id,
        "year": year,
        "supplier_name": "Supplier " + package_id,
        "work_unit": "Satker A",
        "procurement_method": "Tender",
        "procurement_type": "Jasa Lainnya",
        "is_partial_snapshot_year": "true" if year == "2026" else "false",
        "log_contract_value": "4.6151205168",
        "contract_to_hps_ratio": "0.8",
        "supplier_prior_package_count_year": prior_count,
    }


def _write_schema(path: Path, feature_csv: Path, row_count: int = 4) -> None:
    schema = {
        "schema_version": 1,
        "canonical_csv": "datasets/processed/tenders_canonical.csv",
        "canonical_csv_sha256": "fixture-canonical-sha",
        "output_csv": str(feature_csv.as_posix()),
        "row_count": row_count,
        "excluded_row_count": 1,
        "metadata_columns": METADATA_COLUMNS,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_encoders": {"unknown_category_code": 0},
        "leakage_policy": "aggregate features use only prior rows within the same year",
        "partial_snapshot_years": ["2026"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


def test_should_write_reproducible_temporal_split_manifest_and_report(tmp_path: Path) -> None:
    feature_csv = tmp_path / "datasets" / "processed" / "model_features.csv"
    canonical_csv = tmp_path / "datasets" / "processed" / "tenders_canonical.csv"
    schema_json = tmp_path / "artifacts" / "feature_schema.json"
    manifest_json = tmp_path / "datasets" / "manifests" / "model_split.json"
    config_json = tmp_path / "artifacts" / "model_experiment_config.json"
    report_md = tmp_path / "reports" / "model" / "split_decision.md"

    _write_csv(
        feature_csv,
        METADATA_COLUMNS + FEATURE_COLUMNS,
        [
            _feature_row("001", "2024"),
            _feature_row("002", "2025", "1"),
            _feature_row("003", "2026"),
            _feature_row("004", "2026", "1"),
        ],
    )
    _write_csv(
        canonical_csv,
        CANONICAL_COLUMNS,
        [
            _canonical_row(package_id="001", year="2024", eligible="true"),
            _canonical_row(package_id="002", year="2025", eligible="true"),
            _canonical_row(package_id="003", year="2026", eligible="true"),
            _canonical_row(package_id="004", year="2026", eligible="true"),
            _canonical_row(
                package_id="999",
                year="2025",
                eligible="false",
                status="multi_provider_ambiguous",
            ),
        ],
    )
    _write_schema(schema_json, feature_csv)

    manifest = define_model_split(
        feature_csv=feature_csv,
        canonical_csv=canonical_csv,
        feature_schema_json=schema_json,
        output_manifest=manifest_json,
        experiment_config_json=config_json,
        report_md=report_md,
        project_root=tmp_path,
    )

    assert manifest["strategy"] == "temporal_holdout"
    assert manifest["cutoff"]["train_end_year"] == "2025"
    assert manifest["cutoff"]["evaluation_start_year"] == "2026"
    assert manifest["splits"]["train"]["row_count"] == 2
    assert manifest["splits"]["train"]["years"] == ["2024", "2025"]
    assert manifest["splits"]["evaluation"]["row_count"] == 2
    assert manifest["splits"]["evaluation"]["years"] == ["2026"]
    assert manifest["splits"]["train"]["package_ids"] == ["001", "002"]
    assert manifest["splits"]["evaluation"]["package_ids"] == ["003", "004"]
    assert manifest["excluded_records"]["row_count"] == 1
    assert manifest["excluded_records"]["records"][0]["package_id"] == "999"
    assert manifest["leakage_checks"]["split_overlap_count"] == 0
    assert manifest["leakage_checks"]["train_uses_future_years"] is False
    assert manifest["leakage_checks"]["evaluation_used_for_training"] is False
    assert manifest["leakage_policy"]["aggregate_features_are_prior_observation_only"] is True

    config = json.loads(config_json.read_text(encoding="utf-8"))
    assert config["train_split"] == "train"
    assert config["evaluation_split"] == "evaluation"
    assert config["feature_columns"] == FEATURE_COLUMNS
    assert config["unknown_category_code"] == 0

    report = report_md.read_text(encoding="utf-8")
    assert "2026 adalah snapshot parsial" in report
    assert "Training: 2 records" in report
    assert "Evaluation: 2 records" in report


def test_should_fail_when_train_and_evaluation_years_overlap(tmp_path: Path) -> None:
    feature_csv = tmp_path / "datasets" / "processed" / "model_features.csv"
    canonical_csv = tmp_path / "datasets" / "processed" / "tenders_canonical.csv"
    schema_json = tmp_path / "artifacts" / "feature_schema.json"
    _write_csv(
        feature_csv,
        METADATA_COLUMNS + FEATURE_COLUMNS,
        [_feature_row("001", "2023")],
    )
    _write_csv(
        canonical_csv,
        CANONICAL_COLUMNS,
        [_canonical_row(package_id="001", year="2023", eligible="true")],
    )
    _write_schema(schema_json, feature_csv, row_count=1)

    try:
        define_model_split(
            feature_csv=feature_csv,
            canonical_csv=canonical_csv,
            feature_schema_json=schema_json,
            output_manifest=tmp_path / "datasets" / "manifests" / "model_split.json",
            experiment_config_json=tmp_path / "artifacts" / "model_experiment_config.json",
            report_md=tmp_path / "reports" / "model" / "split_decision.md",
            project_root=tmp_path,
        )
    except ValueError as error:
        assert "unsupported split year" in str(error)
    else:
        raise AssertionError("Expected unsupported split year validation failure")
