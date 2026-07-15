from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

DEFAULT_FEATURE_CSV = Path("datasets/processed/model_features.csv")
DEFAULT_SPLIT_MANIFEST = Path("datasets/manifests/model_split.json")
DEFAULT_RANKING_CSV = Path("artifacts/isolation_forest_ranking.csv")
DEFAULT_CONFIG_JSON = Path("artifacts/isolation_forest_config.json")
DEFAULT_MODEL_JOBLIB = Path("artifacts/isolation_forest_model.joblib")
MODEL_TYPE = "sklearn.ensemble.IsolationForest"
SCORE_DIRECTION = "higher score means higher inspection priority"


def _resolve(path: Path, project_root: Path) -> Path:
    return path if path.is_absolute() else project_root / path


def _relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = list(reader.fieldnames or [])
        rows = [{field: (row.get(field) or "").strip() for field in fieldnames} for row in reader]
    return fieldnames, rows


def _validate_manifest(manifest: dict[str, Any]) -> tuple[list[str], set[str], set[str]]:
    feature_columns = manifest.get("feature_matrix", {}).get("feature_columns")
    if not isinstance(feature_columns, list) or not all(
        isinstance(column, str) for column in feature_columns
    ):
        raise ValueError("split manifest must contain feature_matrix.feature_columns")
    splits = manifest.get("splits")
    if not isinstance(splits, dict):
        raise ValueError("split manifest must contain splits")
    train_ids = set(splits.get("train", {}).get("package_ids") or [])
    evaluation_ids = set(splits.get("evaluation", {}).get("package_ids") or [])
    if not train_ids:
        raise ValueError("train split is empty")
    if train_ids & evaluation_ids:
        raise ValueError("train/evaluation package overlap found")
    return feature_columns, train_ids, evaluation_ids


def _to_float(value: str, *, package_id: str, column: str) -> float:
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError(f"non-numeric feature {column} for {package_id}") from error
    if not math.isfinite(number):
        raise ValueError(f"non-finite feature {column} for {package_id}")
    return number


def _feature_matrix(rows: list[dict[str, str]], feature_columns: list[str]) -> np.ndarray:
    return np.array(
        [
            [
                _to_float(row[column], package_id=row["package_id"], column=column)
                for column in feature_columns
            ]
            for row in rows
        ],
        dtype=np.float64,
    )


def _split_for_package(package_id: str, train_ids: set[str], evaluation_ids: set[str]) -> str:
    if package_id in train_ids:
        return "train"
    if package_id in evaluation_ids:
        return "evaluation"
    raise ValueError(f"package_id {package_id} is not present in train/evaluation split")


def _validate_feature_rows(
    feature_csv: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    feature_columns: list[str],
    train_ids: set[str],
    evaluation_ids: set[str],
) -> list[str]:
    metadata_columns = [column for column in fieldnames if column not in feature_columns]
    if fieldnames != metadata_columns + feature_columns:
        raise ValueError(f"{feature_csv}: feature columns must follow metadata columns")
    package_ids = [row.get("package_id", "") for row in rows]
    if any(not package_id for package_id in package_ids):
        raise ValueError(f"{feature_csv}: blank package_id found")
    if len(set(package_ids)) != len(package_ids):
        raise ValueError(f"{feature_csv}: duplicate package_id found")
    unknown_ids = set(package_ids) - train_ids - evaluation_ids
    if unknown_ids:
        raise ValueError(f"feature rows missing from split manifest: {sorted(unknown_ids)[:5]}")
    _feature_matrix(rows, feature_columns)
    return metadata_columns


def _write_ranking(
    path: Path,
    rows: list[dict[str, str]],
    metadata_columns: list[str],
    scores: np.ndarray,
    train_ids: set[str],
    evaluation_ids: set[str],
) -> None:
    output_rows = []
    for row, score in zip(rows, scores, strict=True):
        output = {column: row[column] for column in metadata_columns}
        output["split"] = _split_for_package(row["package_id"], train_ids, evaluation_ids)
        output["anomaly_score"] = f"{float(score):.12g}"
        output_rows.append(output)
    output_rows.sort(key=lambda row: (-float(row["anomaly_score"]), row["package_id"]))
    for rank, row in enumerate(output_rows, start=1):
        row["anomaly_rank"] = str(rank)
    fieldnames = [*metadata_columns, "split", "anomaly_score", "anomaly_rank"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _model_version(feature_sha: str, split_sha: str, random_seed: int, n_estimators: int) -> str:
    payload = f"{feature_sha}:{split_sha}:{random_seed}:{n_estimators}:isolation_forest_v1"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def train_isolation_forest(
    feature_csv: Path = DEFAULT_FEATURE_CSV,
    split_manifest_json: Path = DEFAULT_SPLIT_MANIFEST,
    ranking_csv: Path = DEFAULT_RANKING_CSV,
    config_json: Path = DEFAULT_CONFIG_JSON,
    model_joblib: Path = DEFAULT_MODEL_JOBLIB,
    project_root: Path | None = None,
    n_estimators: int = 200,
    contamination: str | float = "auto",
    max_samples: str | int | float = "auto",
    random_seed: int = 42,
) -> dict[str, Any]:
    project_root = (project_root or Path.cwd()).resolve()
    feature_csv = _resolve(feature_csv, project_root)
    split_manifest_json = _resolve(split_manifest_json, project_root)
    ranking_csv = _resolve(ranking_csv, project_root)
    config_json = _resolve(config_json, project_root)
    model_joblib = _resolve(model_joblib, project_root)

    manifest = _read_json(split_manifest_json)
    feature_columns, train_ids, evaluation_ids = _validate_manifest(manifest)
    fieldnames, rows = _read_csv(feature_csv)
    metadata_columns = _validate_feature_rows(
        feature_csv, fieldnames, rows, feature_columns, train_ids, evaluation_ids
    )
    train_rows = [row for row in rows if row["package_id"] in train_ids]
    evaluation_rows = [row for row in rows if row["package_id"] in evaluation_ids]
    if not evaluation_rows:
        raise ValueError("evaluation split is empty")

    train_matrix = _feature_matrix(train_rows, feature_columns)
    full_matrix = _feature_matrix(rows, feature_columns)
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_matrix)
    full_scaled = scaler.transform(full_matrix)
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        max_samples=max_samples,
        random_state=random_seed,
        n_jobs=1,
    )
    model.fit(train_scaled)
    normality_scores = model.score_samples(full_scaled)
    anomaly_scores = -normality_scores
    if not np.isfinite(anomaly_scores).all():
        raise ValueError("Isolation Forest produced non-finite scores")

    feature_sha = _sha256(feature_csv)
    split_sha = _sha256(split_manifest_json)
    version = _model_version(feature_sha, split_sha, random_seed, n_estimators)
    artifact = {
        "model": model,
        "preprocessor": scaler,
        "feature_columns": feature_columns,
        "metadata": {
            "model_version": version,
            "model_type": MODEL_TYPE,
            "random_seed": random_seed,
            "score_direction": SCORE_DIRECTION,
            "cpu_only": True,
        },
    }
    model_joblib.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_joblib)
    _write_ranking(ranking_csv, rows, metadata_columns, anomaly_scores, train_ids, evaluation_ids)

    config = {
        "schema_version": 1,
        "model_version": version,
        "model_type": MODEL_TYPE,
        "model_artifact": _relative(model_joblib, project_root),
        "ranking_csv": _relative(ranking_csv, project_root),
        "feature_matrix": _relative(feature_csv, project_root),
        "feature_matrix_sha256": feature_sha,
        "split_manifest": _relative(split_manifest_json, project_root),
        "split_manifest_sha256": split_sha,
        "feature_columns": feature_columns,
        "preprocessing": {"scaler": "sklearn.preprocessing.StandardScaler"},
        "hyperparameters": {
            "n_estimators": n_estimators,
            "contamination": contamination,
            "max_samples": max_samples,
            "n_jobs": 1,
        },
        "random_seed": random_seed,
        "score_direction": SCORE_DIRECTION,
        "cpu_only": True,
        "train_row_count": len(train_rows),
        "evaluation_row_count": len(evaluation_rows),
        "scored_row_count": len(rows),
        "library_versions": {
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
            "joblib": joblib.__version__,
        },
    }
    _write_json(config_json, config)
    return {
        "model_version": version,
        "row_count": len(rows),
        "feature_count": len(feature_columns),
        "train_row_count": len(train_rows),
        "evaluation_row_count": len(evaluation_rows),
        "ranking_csv": _relative(ranking_csv, project_root),
        "model_artifact": _relative(model_joblib, project_root),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train reproducible Isolation Forest model")
    parser.add_argument("--feature-csv", type=Path, default=DEFAULT_FEATURE_CSV)
    parser.add_argument("--split-manifest-json", type=Path, default=DEFAULT_SPLIT_MANIFEST)
    parser.add_argument("--ranking-csv", type=Path, default=DEFAULT_RANKING_CSV)
    parser.add_argument("--config-json", type=Path, default=DEFAULT_CONFIG_JSON)
    parser.add_argument("--model-joblib", type=Path, default=DEFAULT_MODEL_JOBLIB)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument("--random-seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = train_isolation_forest(
            feature_csv=args.feature_csv,
            split_manifest_json=args.split_manifest_json,
            ranking_csv=args.ranking_csv,
            config_json=args.config_json,
            model_joblib=args.model_joblib,
            project_root=args.project_root,
            n_estimators=args.n_estimators,
            random_seed=args.random_seed,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Isolation Forest training failed: {error}", file=sys.stderr)
        return 1
    print(
        "Wrote Isolation Forest artifacts: "
        f"{args.ranking_csv} | rows={result['row_count']} features={result['feature_count']} "
        f"model_version={result['model_version']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
