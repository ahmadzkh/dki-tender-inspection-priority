from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modeling.explain_anomaly_ranking import explain_anomaly_ranking  # noqa: E402
from modeling.train_isolation_forest import train_isolation_forest  # noqa: E402
from tests.test_evaluate_anomaly_ranking import (  # noqa: E402
    _write_baseline,
    _write_baseline_config,
)
from tests.test_train_isolation_forest import (  # noqa: E402
    _write_feature_csv,
    _write_split_manifest,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def _setup_artifacts(tmp_path: Path) -> dict[str, Path]:
    paths = {
        "feature_csv": tmp_path / "datasets" / "processed" / "model_features.csv",
        "split_manifest": tmp_path / "datasets" / "manifests" / "model_split.json",
        "model_ranking": tmp_path / "artifacts" / "isolation_forest_ranking.csv",
        "model_config": tmp_path / "artifacts" / "isolation_forest_config.json",
        "model_artifact": tmp_path / "artifacts" / "isolation_forest_model.joblib",
        "baseline_ranking": tmp_path / "artifacts" / "baseline_ranking.csv",
        "baseline_config": tmp_path / "artifacts" / "baseline_config.json",
        "output_json": tmp_path / "reports" / "model" / "explanation.json",
        "output_md": tmp_path / "reports" / "model" / "explanation.md",
        "tables_dir": tmp_path / "reports" / "model" / "tables",
        "explanation_artifact": tmp_path / "artifacts" / "ranking_explanations.json",
    }
    _write_feature_csv(paths["feature_csv"])
    _write_split_manifest(paths["split_manifest"], paths["feature_csv"])
    _write_baseline(paths["baseline_ranking"])
    _write_baseline_config(paths["baseline_config"], paths["feature_csv"], paths["split_manifest"])
    train_isolation_forest(
        feature_csv=paths["feature_csv"],
        split_manifest_json=paths["split_manifest"],
        ranking_csv=paths["model_ranking"],
        config_json=paths["model_config"],
        model_joblib=paths["model_artifact"],
        project_root=tmp_path,
        n_estimators=32,
        random_seed=42,
    )
    return paths


def test_explain_top_n_returns_factors(tmp_path: Path) -> None:
    p = _setup_artifacts(tmp_path)
    result = explain_anomaly_ranking(
        feature_csv=p["feature_csv"],
        split_manifest_json=p["split_manifest"],
        model_config_json=p["model_config"],
        model_ranking_csv=p["model_ranking"],
        output_json=p["output_json"],
        output_md=p["output_md"],
        tables_dir=p["tables_dir"],
        explanation_artifact=p["explanation_artifact"],
        project_root=tmp_path,
        top_n_values=(2, 3),
        n_permutations=5,
    )
    report = json.loads(p["output_json"].read_text(encoding="utf-8"))
    assert result["model_version"] == report["artifact_versions"]["model_version"]
    assert report["method"] == "permutation_importance"
    assert report["addressed_decisions"] == ["OD-5"]
    # Check each Top-N has explanations
    for top_n in [2, 3]:
        key = str(top_n)
        assert key in report["per_record"]
        assert len(report["per_record"][key]) == top_n
        for expl in report["per_record"][key]:
            assert "package_id" in expl
            assert "rank" in expl
            assert "anomaly_score" in expl
            assert "factors" in expl
            assert len(expl["factors"]) >= 1
            for factor in expl["factors"]:
                assert "feature" in factor
                assert "value" in factor
                assert "percentile" in factor
                assert "impact" in factor
    # Tables
    for top_n in [2, 3]:
        table = p["tables_dir"] / f"top_{top_n}_explanations.csv"
        assert table.exists()
        rows = _read_csv(table)
        assert len(rows) == top_n
        for row in rows:
            assert row["factor_1"]
    # Artifact
    assert p["explanation_artifact"].exists()
    artifact = json.loads(p["explanation_artifact"].read_text(encoding="utf-8"))
    assert "all" in artifact
    assert "2" in artifact
    assert "3" in artifact

    # Check explanations are not just hardcoded
    top2 = report["per_record"]["2"]
    assert top2[0]["package_id"] != top2[1]["package_id"]
    all_factors: set[str] = set()
    for expl in report["per_record"]["2"]:
        for f in expl["factors"]:
            all_factors.add(f["feature"])
    # At least 1 unique feature across all explanations
    assert len(all_factors) >= 1


def test_explanation_markdown_exists(tmp_path: Path) -> None:
    p = _setup_artifacts(tmp_path)
    explain_anomaly_ranking(
        feature_csv=p["feature_csv"],
        split_manifest_json=p["split_manifest"],
        model_config_json=p["model_config"],
        model_ranking_csv=p["model_ranking"],
        output_json=p["output_json"],
        output_md=p["output_md"],
        tables_dir=p["tables_dir"],
        explanation_artifact=p["explanation_artifact"],
        project_root=tmp_path,
        top_n_values=(2, 3),
        n_permutations=5,
    )
    assert p["output_md"].exists()
    text = p["output_md"].read_text(encoding="utf-8")
    assert "Permutation sensitivity" in text
    assert "OD-5" in text
    assert "limitations" in text.lower()
    assert "score" in text.lower()
