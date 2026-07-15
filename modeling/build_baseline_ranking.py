from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

DEFAULT_FEATURE_CSV = Path("datasets/processed/model_features.csv")
DEFAULT_SPLIT_MANIFEST = Path("datasets/manifests/model_split.json")
DEFAULT_OUTPUT_CSV = Path("artifacts/baseline_ranking.csv")
DEFAULT_CONFIG_JSON = Path("artifacts/baseline_config.json")
DEFAULT_REPORT_MD = Path("reports/model/baseline.md")
METHOD = "robust_zscore_topk_mean"
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def _median_absolute_deviation(values: list[float], median: float) -> float:
    return statistics.median(abs(value - median) for value in values)


def _feature_statistics(
    rows: list[dict[str, str]], train_ids: set[str], feature_columns: list[str]
) -> dict[str, dict[str, float]]:
    stats: dict[str, dict[str, float]] = {}
    train_rows = [row for row in rows if row["package_id"] in train_ids]
    for column in feature_columns:
        values = [
            _to_float(row[column], package_id=row["package_id"], column=column)
            for row in train_rows
        ]
        median = statistics.median(values)
        mad = _median_absolute_deviation(values, median)
        scale = 1.4826 * mad if mad > 0 else 0.0
        if scale == 0:
            different_values = [abs(value - median) for value in values if value != median]
            scale = min(different_values) if different_values else 1.0
        stats[column] = {"median": median, "scale": scale}
    return stats


def _score_row(
    row: dict[str, str], feature_columns: list[str], stats: dict[str, dict[str, float]], top_k: int
) -> tuple[float, list[tuple[str, float]]]:
    contributions = []
    for column in feature_columns:
        number = _to_float(row[column], package_id=row["package_id"], column=column)
        stat = stats[column]
        contribution = abs(number - stat["median"]) / stat["scale"]
        contributions.append((column, contribution))
    ordered = sorted(contributions, key=lambda item: (-item[1], item[0]))
    top = ordered[:top_k]
    score = sum(value for _, value in top) / top_k
    return score, top


def _split_for_package(package_id: str, train_ids: set[str], evaluation_ids: set[str]) -> str:
    if package_id in train_ids:
        return "train"
    if package_id in evaluation_ids:
        return "evaluation"
    raise ValueError(f"package_id {package_id} is not present in train/evaluation split")


def _ranking_rows(
    rows: list[dict[str, str]],
    metadata_columns: list[str],
    feature_columns: list[str],
    train_ids: set[str],
    evaluation_ids: set[str],
    stats: dict[str, dict[str, float]],
    top_k: int,
) -> list[dict[str, str]]:
    scored = []
    for row in rows:
        score, top = _score_row(row, feature_columns, stats, top_k)
        output = {column: row[column] for column in metadata_columns}
        output["split"] = _split_for_package(row["package_id"], train_ids, evaluation_ids)
        output["baseline_score"] = f"{score:.12g}"
        for index in range(3):
            if index < len(top):
                feature, contribution = top[index]
                output[f"top_feature_{index + 1}"] = feature
                output[f"top_feature_{index + 1}_contribution"] = f"{contribution:.12g}"
            else:
                output[f"top_feature_{index + 1}"] = ""
                output[f"top_feature_{index + 1}_contribution"] = ""
        scored.append(output)
    scored.sort(key=lambda row: (-float(row["baseline_score"]), row["package_id"]))
    for rank, row in enumerate(scored, start=1):
        row["baseline_rank"] = str(rank)
    return scored


def _write_ranking(path: Path, rows: list[dict[str, str]], metadata_columns: list[str]) -> None:
    fieldnames = [
        *metadata_columns,
        "split",
        "baseline_score",
        "baseline_rank",
        "top_feature_1",
        "top_feature_1_contribution",
        "top_feature_2",
        "top_feature_2_contribution",
        "top_feature_3",
        "top_feature_3_contribution",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_report(path: Path, config: dict[str, Any], row_count: int) -> None:
    limitations = config["limitations"]
    lines = [
        "# Transparent Baseline Ranking",
        "",
        "This report is generated by `modeling/build_baseline_ranking.py`. Do not edit manually.",
        "",
        "## Method",
        "",
        "The transparent baseline uses train-split medians and robust scales to compute "
        "absolute robust z-scores for every feature. The final score is the mean of the "
        f"top {config['top_k']} feature deviations.",
        "",
        f"- Method: `{config['method']}`",
        f"- Rows scored: {row_count}",
        f"- Train rows used for baseline statistics: {config['train_row_count']}",
        f"- Evaluation rows scored: {config['evaluation_row_count']}",
        f"- Score direction: {config['score_direction']}",
        "- The score is an inspection-priority comparator, not a legal conclusion.",
        "",
        "## Limitations",
        "",
        *[f"- {item}" for item in limitations],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_baseline_ranking(
    feature_csv: Path = DEFAULT_FEATURE_CSV,
    split_manifest_json: Path = DEFAULT_SPLIT_MANIFEST,
    output_csv: Path = DEFAULT_OUTPUT_CSV,
    config_json: Path = DEFAULT_CONFIG_JSON,
    report_md: Path = DEFAULT_REPORT_MD,
    project_root: Path | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    project_root = (project_root or Path.cwd()).resolve()
    feature_csv = _resolve(feature_csv, project_root)
    split_manifest_json = _resolve(split_manifest_json, project_root)
    output_csv = _resolve(output_csv, project_root)
    config_json = _resolve(config_json, project_root)
    report_md = _resolve(report_md, project_root)

    manifest = _read_json(split_manifest_json)
    feature_columns, train_ids, evaluation_ids = _validate_manifest(manifest)
    fieldnames, rows = _read_csv(feature_csv)
    metadata_columns = [column for column in fieldnames if column not in feature_columns]
    expected_columns = metadata_columns + feature_columns
    if fieldnames != expected_columns:
        raise ValueError(f"{feature_csv}: feature columns must follow metadata columns")
    if len({row["package_id"] for row in rows}) != len(rows):
        raise ValueError(f"{feature_csv}: duplicate package_id found")
    unknown_ids = {row["package_id"] for row in rows} - train_ids - evaluation_ids
    if unknown_ids:
        raise ValueError(f"feature rows missing from split manifest: {sorted(unknown_ids)[:5]}")
    if top_k < 1:
        raise ValueError("top_k must be positive")
    top_k = min(top_k, len(feature_columns))

    stats = _feature_statistics(rows, train_ids, feature_columns)
    ranking = _ranking_rows(
        rows, metadata_columns, feature_columns, train_ids, evaluation_ids, stats, top_k
    )
    _write_ranking(output_csv, ranking, metadata_columns)

    config = {
        "schema_version": 1,
        "method": METHOD,
        "feature_matrix": _relative(feature_csv, project_root),
        "feature_matrix_sha256": _sha256(feature_csv),
        "split_manifest": _relative(split_manifest_json, project_root),
        "split_manifest_sha256": _sha256(split_manifest_json),
        "output_csv": _relative(output_csv, project_root),
        "feature_columns": feature_columns,
        "top_k": top_k,
        "score_direction": SCORE_DIRECTION,
        "train_row_count": sum(1 for row in rows if row["package_id"] in train_ids),
        "evaluation_row_count": sum(1 for row in rows if row["package_id"] in evaluation_ids),
        "feature_statistics": stats,
        "limitations": [
            "Uses independent per-feature robust deviations; it does not learn "
            "multivariate interactions.",
            "Calibrated on 2024-2025 train rows; 2026 remains a partial snapshot.",
            "Ranking is a transparent comparator for inspection priority, not a violation label.",
        ],
    }
    _write_json(config_json, config)
    _write_report(report_md, config, len(rows))
    return {
        "method": METHOD,
        "row_count": len(rows),
        "feature_count": len(feature_columns),
        "train_row_count": config["train_row_count"],
        "evaluation_row_count": config["evaluation_row_count"],
        "output_csv": _relative(output_csv, project_root),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build transparent baseline ranking")
    parser.add_argument("--feature-csv", type=Path, default=DEFAULT_FEATURE_CSV)
    parser.add_argument("--split-manifest-json", type=Path, default=DEFAULT_SPLIT_MANIFEST)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--config-json", type=Path, default=DEFAULT_CONFIG_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        result = build_baseline_ranking(
            feature_csv=args.feature_csv,
            split_manifest_json=args.split_manifest_json,
            output_csv=args.output_csv,
            config_json=args.config_json,
            report_md=args.report_md,
            project_root=args.project_root,
            top_k=args.top_k,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Baseline ranking failed: {error}", file=sys.stderr)
        return 1
    print(
        "Wrote baseline ranking: "
        f"{args.output_csv} | rows={result['row_count']} features={result['feature_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
