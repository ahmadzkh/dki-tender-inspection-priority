from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modeling.train_isolation_forest import train_isolation_forest  # noqa: E402

METADATA_COLUMNS = [
    "package_id",
    "year",
    "supplier_name",
    "work_unit",
    "procurement_method",
    "procurement_type",
    "is_partial_snapshot_year",
]
FEATURE_COLUMNS = ["feature_a", "feature_b"]


def _row(package_id: str, year: str, feature_a: str, feature_b: str) -> dict[str, str]:
    return {
        "package_id": package_id,
        "year": year,
        "supplier_name": "Supplier " + package_id,
        "work_unit": "Satker A",
        "procurement_method": "Tender",
        "procurement_type": "Jasa Lainnya",
        "is_partial_snapshot_year": "true" if year == "2026" else "false",
        "feature_a": feature_a,
        "feature_b": feature_b,
    }


def _write_feature_csv(path: Path) -> None:
    rows = [
        _row("train-a", "2024", "0.0", "0.0"),
        _row("train-b", "2024", "0.1", "-0.1"),
        _row("train-c", "2025", "-0.1", "0.2"),
        _row("train-d", "2025", "0.2", "0.1"),
        _row("eval-normal", "2026", "0.05", "0.0"),
        _row("eval-extreme", "2026", "9.0", "9.0"),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=METADATA_COLUMNS + FEATURE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_split_manifest(path: Path, feature_csv: Path) -> None:
    manifest = {
        "schema_version": 1,
        "strategy": "temporal_holdout",
        "feature_matrix": {
            "path": feature_csv.as_posix(),
            "sha256": "fixture-feature-sha",
            "row_count": 6,
            "feature_count": len(FEATURE_COLUMNS),
            "feature_columns": FEATURE_COLUMNS,
            "metadata_columns": METADATA_COLUMNS,
        },
        "cutoff": {
            "train_start_year": "2024",
            "train_end_year": "2025",
            "evaluation_start_year": "2026",
            "evaluation_end_year": "2026",
            "partial_snapshot_years": ["2026"],
        },
        "splits": {
            "train": {
                "years": ["2024", "2025"],
                "row_count": 4,
                "package_ids": ["train-a", "train-b", "train-c", "train-d"],
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


def test_isolation_forest_trains_reproducible_artifacts_and_ranks_extreme(
    tmp_path: Path,
) -> None:
    feature_csv = tmp_path / "datasets" / "processed" / "model_features.csv"
    split_manifest = tmp_path / "datasets" / "manifests" / "model_split.json"
    ranking_csv = tmp_path / "artifacts" / "isolation_forest_ranking.csv"
    config_json = tmp_path / "artifacts" / "isolation_forest_config.json"
    model_joblib = tmp_path / "artifacts" / "isolation_forest_model.joblib"
    _write_feature_csv(feature_csv)
    _write_split_manifest(split_manifest, feature_csv)

    result = train_isolation_forest(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest,
        ranking_csv=ranking_csv,
        config_json=config_json,
        model_joblib=model_joblib,
        project_root=tmp_path,
        n_estimators=64,
        random_seed=123,
    )

    rows = _read_ranking(ranking_csv)
    by_id = {row["package_id"]: row for row in rows}
    assert result["row_count"] == 6
    assert result["feature_count"] == 2
    assert result["train_row_count"] == 4
    assert result["evaluation_row_count"] == 2
    assert model_joblib.exists()
    assert float(by_id["eval-extreme"]["anomaly_score"]) > float(
        by_id["eval-normal"]["anomaly_score"]
    )
    assert by_id["eval-extreme"]["split"] == "evaluation"
    assert all(math.isfinite(float(row["anomaly_score"])) for row in rows)
    assert all(str(index) == row["anomaly_rank"] for index, row in enumerate(rows, start=1))

    config = json.loads(config_json.read_text(encoding="utf-8"))
    assert config["model_type"] == "sklearn.ensemble.IsolationForest"
    assert config["random_seed"] == 123
    assert config["hyperparameters"]["n_estimators"] == 64
    assert config["feature_columns"] == FEATURE_COLUMNS
    assert config["score_direction"] == "higher score means higher inspection priority"
    assert config["cpu_only"] is True
    assert config["library_versions"]["scikit_learn"]
    assert "feature_matrix_sha256" in config
    assert "split_manifest_sha256" in config

    artifact = joblib.load(model_joblib)
    assert artifact["feature_columns"] == FEATURE_COLUMNS
    assert artifact["metadata"]["random_seed"] == 123


def test_isolation_forest_repeated_run_has_same_scores_and_ranking(tmp_path: Path) -> None:
    feature_csv = tmp_path / "datasets" / "processed" / "model_features.csv"
    split_manifest = tmp_path / "datasets" / "manifests" / "model_split.json"
    _write_feature_csv(feature_csv)
    _write_split_manifest(split_manifest, feature_csv)

    output_a = tmp_path / "artifacts" / "ranking_a.csv"
    output_b = tmp_path / "artifacts" / "ranking_b.csv"
    config_a = tmp_path / "artifacts" / "config_a.json"
    config_b = tmp_path / "artifacts" / "config_b.json"
    model_a = tmp_path / "artifacts" / "model_a.joblib"
    model_b = tmp_path / "artifacts" / "model_b.joblib"

    train_isolation_forest(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest,
        ranking_csv=output_a,
        config_json=config_a,
        model_joblib=model_a,
        project_root=tmp_path,
        n_estimators=64,
        random_seed=123,
    )
    train_isolation_forest(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest,
        ranking_csv=output_b,
        config_json=config_b,
        model_joblib=model_b,
        project_root=tmp_path,
        n_estimators=64,
        random_seed=123,
    )

    rows_a = _read_ranking(output_a)
    rows_b = _read_ranking(output_b)
    assert [row["package_id"] for row in rows_a] == [row["package_id"] for row in rows_b]
    assert [row["anomaly_rank"] for row in rows_a] == [row["anomaly_rank"] for row in rows_b]
    for row_a, row_b in zip(rows_a, rows_b, strict=True):
        assert math.isclose(
            float(row_a["anomaly_score"]),
            float(row_b["anomaly_score"]),
            rel_tol=0,
            abs_tol=1e-12,
        )
