from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modeling.evaluate_anomaly_ranking import evaluate_anomaly_ranking  # noqa: E402
from modeling.train_isolation_forest import train_isolation_forest  # noqa: E402
from tests.test_train_isolation_forest import (  # noqa: E402
    _write_feature_csv,
    _write_split_manifest,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def _write_baseline(path: Path) -> None:
    rows = [
        {"package_id": "eval-extreme", "baseline_score": "9.0", "baseline_rank": "1"},
        {"package_id": "train-d", "baseline_score": "4.0", "baseline_rank": "2"},
        {"package_id": "eval-normal", "baseline_score": "3.0", "baseline_rank": "3"},
        {"package_id": "train-c", "baseline_score": "2.0", "baseline_rank": "4"},
        {"package_id": "train-b", "baseline_score": "1.0", "baseline_rank": "5"},
        {"package_id": "train-a", "baseline_score": "0.0", "baseline_rank": "6"},
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_baseline_config(path: Path, feature_csv: Path, split_manifest: Path) -> None:
    feature_sha = hashlib.sha256(feature_csv.read_bytes()).hexdigest()
    split_sha = hashlib.sha256(split_manifest.read_bytes()).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "method": "fixture_baseline",
                "feature_matrix": feature_csv.as_posix(),
                "feature_matrix_sha256": feature_sha,
                "split_manifest": split_manifest.as_posix(),
                "split_manifest_sha256": split_sha,
                "top_k": 3,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_evaluation_report_covers_required_unsupervised_checks(tmp_path: Path) -> None:
    feature_csv = tmp_path / "datasets" / "processed" / "model_features.csv"
    split_manifest = tmp_path / "datasets" / "manifests" / "model_split.json"
    model_ranking = tmp_path / "artifacts" / "isolation_forest_ranking.csv"
    model_config = tmp_path / "artifacts" / "isolation_forest_config.json"
    model_artifact = tmp_path / "artifacts" / "isolation_forest_model.joblib"
    baseline_ranking = tmp_path / "artifacts" / "baseline_ranking.csv"
    baseline_config = tmp_path / "artifacts" / "baseline_config.json"
    output_json = tmp_path / "reports" / "model" / "evaluation.json"
    output_md = tmp_path / "reports" / "model" / "evaluation.md"
    tables_dir = tmp_path / "reports" / "model" / "tables"
    figures_dir = tmp_path / "reports" / "model" / "figures"

    _write_feature_csv(feature_csv)
    _write_split_manifest(split_manifest, feature_csv)
    _write_baseline(baseline_ranking)
    _write_baseline_config(baseline_config, feature_csv, split_manifest)
    train_isolation_forest(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest,
        ranking_csv=model_ranking,
        config_json=model_config,
        model_joblib=model_artifact,
        project_root=tmp_path,
        n_estimators=32,
        random_seed=42,
    )

    result = evaluate_anomaly_ranking(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest,
        model_config_json=model_config,
        model_ranking_csv=model_ranking,
        baseline_config_json=baseline_config,
        baseline_ranking_csv=baseline_ranking,
        output_json=output_json,
        output_md=output_md,
        tables_dir=tables_dir,
        figures_dir=figures_dir,
        project_root=tmp_path,
        top_n_values=(2, 3),
        seed_values=(7, 42),
        estimator_values=(16, 32),
        contamination_values=("auto", 0.2),
        max_samples_values=("auto", 0.8),
    )

    report = json.loads(output_json.read_text(encoding="utf-8"))
    assert result["model_version"] == report["artifact_versions"]["model_version"]
    assert report["row_count"] == 6
    assert report["feature_count"] == 2
    assert report["top_n_values"] == [2, 3]
    assert {"OD-1", "OD-2", "OD-4"} <= set(report["decisions"])
    assert report["score_distribution"]["all"]["count"] == 6
    assert report["temporal_behavior"]["evaluation"]["count"] == 2
    assert report["baseline_comparison"]["top_n_overlap"]["2"]["overlap_count"] >= 1
    assert report["seed_stability"]
    assert report["hyperparameter_sensitivity"]

    assert (tables_dir / "seed_stability.csv").exists()
    assert (tables_dir / "hyperparameter_sensitivity.csv").exists()
    assert (tables_dir / "baseline_comparison.csv").exists()
    assert (figures_dir / "score_distribution.svg").exists()
    assert (figures_dir / "hyperparameter_sensitivity.svg").exists()
    assert _read_csv(tables_dir / "seed_stability.csv")
    assert _read_csv(tables_dir / "hyperparameter_sensitivity.csv")

    report_text = output_md.read_text(encoding="utf-8").lower()
    for forbidden_metric in ["accuracy", "precision", "recall", "f1", "confusion matrix"]:
        assert forbidden_metric not in report_text


def test_evaluation_rerun_is_deterministic(tmp_path: Path) -> None:
    feature_csv = tmp_path / "datasets" / "processed" / "model_features.csv"
    split_manifest = tmp_path / "datasets" / "manifests" / "model_split.json"
    model_ranking = tmp_path / "artifacts" / "isolation_forest_ranking.csv"
    model_config = tmp_path / "artifacts" / "isolation_forest_config.json"
    model_artifact = tmp_path / "artifacts" / "isolation_forest_model.joblib"
    baseline_ranking = tmp_path / "artifacts" / "baseline_ranking.csv"
    baseline_config = tmp_path / "artifacts" / "baseline_config.json"

    _write_feature_csv(feature_csv)
    _write_split_manifest(split_manifest, feature_csv)
    _write_baseline(baseline_ranking)
    _write_baseline_config(baseline_config, feature_csv, split_manifest)
    train_isolation_forest(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest,
        ranking_csv=model_ranking,
        config_json=model_config,
        model_joblib=model_artifact,
        project_root=tmp_path,
        n_estimators=32,
        random_seed=42,
    )

    kwargs = {
        "feature_csv": feature_csv,
        "split_manifest_json": split_manifest,
        "model_config_json": model_config,
        "model_ranking_csv": model_ranking,
        "baseline_config_json": baseline_config,
        "baseline_ranking_csv": baseline_ranking,
        "project_root": tmp_path,
        "top_n_values": (2, 3),
        "seed_values": (7, 42),
        "estimator_values": (16, 32),
        "contamination_values": ("auto", 0.2),
        "max_samples_values": ("auto", 0.8),
    }
    evaluate_anomaly_ranking(
        output_json=tmp_path / "reports_a" / "evaluation.json",
        output_md=tmp_path / "reports_a" / "evaluation.md",
        tables_dir=tmp_path / "reports_a" / "tables",
        figures_dir=tmp_path / "reports_a" / "figures",
        **kwargs,
    )
    evaluate_anomaly_ranking(
        output_json=tmp_path / "reports_b" / "evaluation.json",
        output_md=tmp_path / "reports_b" / "evaluation.md",
        tables_dir=tmp_path / "reports_b" / "tables",
        figures_dir=tmp_path / "reports_b" / "figures",
        **kwargs,
    )

    report_a = json.loads((tmp_path / "reports_a" / "evaluation.json").read_text(encoding="utf-8"))
    report_b = json.loads((tmp_path / "reports_b" / "evaluation.json").read_text(encoding="utf-8"))
    report_a["outputs"] = report_b["outputs"]
    assert report_a == report_b
    assert (tmp_path / "reports_a" / "tables" / "seed_stability.csv").read_text(
        encoding="utf-8"
    ) == (tmp_path / "reports_b" / "tables" / "seed_stability.csv").read_text(encoding="utf-8")
