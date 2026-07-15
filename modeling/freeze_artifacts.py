from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

MANIFEST = Path("artifacts/manifest.json")

REQUIRED_ARTIFACTS: dict[str, list[str]] = {
    "datasets": [
        "datasets/manifests/source_manifest.json",
        "datasets/manifests/model_split.json",
        "datasets/processed/tenders_canonical.csv",
    ],
    "features": [
        "artifacts/feature_schema.json",
        "datasets/processed/model_features.csv",
    ],
    "model": [
        "artifacts/isolation_forest_config.json",
        "artifacts/isolation_forest_model.joblib",
        "artifacts/isolation_forest_ranking.csv",
    ],
    "evaluation": [
        "reports/model/evaluation.json",
    ],
    "explanation": [
        "artifacts/ranking_explanations.json",
    ],
    "baseline": [
        "artifacts/baseline_config.json",
        "artifacts/baseline_ranking.csv",
    ],
}


def _file_info(path: Path, project_root: Path) -> dict[str, str | int | None]:
    real = path if path.is_absolute() else project_root / path
    if not real.exists():
        return {
            "path": str(path),
            "exists": False,
            "size_bytes": None,
            "sha256": None,
        }
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": real.stat().st_size,
        "sha256": hashlib.sha256(real.read_bytes()).hexdigest(),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def freeze_artifacts(
    project_root: Path | None = None,
    manifest_path: Path = MANIFEST,
) -> dict[str, Any]:
    project_root = (project_root or Path.cwd()).resolve()
    manifest_path = manifest_path if manifest_path.is_absolute() else project_root / manifest_path

    model_config_path = project_root / "artifacts" / "isolation_forest_config.json"
    model_config: dict[str, Any] = {}
    if model_config_path.exists():
        model_config = json.loads(model_config_path.read_text(encoding="utf-8"))

    feature_schema_path = project_root / "artifacts" / "feature_schema.json"
    feature_schema: dict[str, Any] = {}
    if feature_schema_path.exists():
        feature_schema = json.loads(feature_schema_path.read_text(encoding="utf-8"))

    ranking_path = project_root / "artifacts" / "isolation_forest_ranking.csv"
    ranking_rows: list[dict[str, str]] = []
    if ranking_path.exists():
        with ranking_path.open("r", encoding="utf-8", newline="") as csv_file:
            ranking_rows = list(csv.DictReader(csv_file))

    top_n_20 = sorted(
        ranking_rows,
        key=lambda r: int(r.get("anomaly_rank", "999999")),
    )[:20]
    top_n_50 = sorted(
        ranking_rows,
        key=lambda r: int(r.get("anomaly_rank", "999999")),
    )[:50]

    summary: dict[str, Any] = {
        "total_record_count": len(ranking_rows),
        "eligible_record_count": feature_schema.get("row_count", len(ranking_rows)),
        "feature_count": feature_schema.get(
            "feature_count",
            len(feature_schema.get("feature_columns", [])),
        ),
        "top_20_package_ids": [row.get("package_id", "") for row in top_n_20],
        "top_50_package_ids": [row.get("package_id", "") for row in top_n_50],
        "year_counts": {},
        "split_counts": {},
    }
    for row in ranking_rows:
        year = row.get("year", "unknown")
        split = row.get("split", "unknown")
        summary["year_counts"][year] = summary["year_counts"].get(year, 0) + 1
        summary["split_counts"][split] = summary["split_counts"].get(split, 0) + 1

    filtered_artifacts: dict[str, list[dict[str, str | int | None]]] = {}
    for category, paths in REQUIRED_ARTIFACTS.items():
        filtered_artifacts[category] = [_file_info(Path(p), project_root) for p in paths]

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "project_name": "dki-tender-inspection-priority",
        "version": model_config.get("model_version", "unknown"),
        "model": {
            "model_version": model_config.get("model_version"),
            "model_type": model_config.get("model_type"),
            "feature_columns": model_config.get("feature_columns"),
            "scored_row_count": model_config.get("scored_row_count"),
            "library_versions": model_config.get("library_versions"),
        },
        "feature_schema": {
            "row_count": feature_schema.get("row_count"),
            "feature_count": len(feature_schema.get("feature_columns", [])),
            "feature_columns": feature_schema.get("feature_columns"),
            "metadata_columns": feature_schema.get("metadata_columns"),
            "canonical_csv_sha256": feature_schema.get("canonical_csv_sha256"),
        },
        "summary": summary,
        "artifacts": filtered_artifacts,
        "integrity": {
            "artifact_count": sum(len(v) for v in filtered_artifacts.values()),
            "all_artifacts_exist": all(
                info["exists"] for category in filtered_artifacts.values() for info in category
            ),
        },
    }

    _write_json(manifest_path, manifest)
    return manifest


def main() -> int:
    manifest = freeze_artifacts()
    n = manifest["integrity"]["artifact_count"]
    ok = manifest["integrity"]["all_artifacts_exist"]
    print(f"Wrote artifact manifest: {MANIFEST} | {n} artifacts, all_exist={ok}")
    if not ok:
        missing = [
            info["path"]
            for category in manifest["artifacts"].values()
            for info in category
            if not info["exists"]
        ]
        for path in missing:
            print(f"  MISSING: {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
