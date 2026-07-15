from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modeling.train_isolation_forest import train_isolation_forest  # noqa: E402

DEFAULT_FEATURE_CSV = Path("datasets/processed/model_features.csv")
DEFAULT_SPLIT_MANIFEST = Path("datasets/manifests/model_split.json")
DEFAULT_MODEL_CONFIG = Path("artifacts/isolation_forest_config.json")
DEFAULT_MODEL_RANKING = Path("artifacts/isolation_forest_ranking.csv")
DEFAULT_BASELINE_CONFIG = Path("artifacts/baseline_config.json")
DEFAULT_BASELINE_RANKING = Path("artifacts/baseline_ranking.csv")
DEFAULT_OUTPUT_JSON = Path("reports/model/evaluation.json")
DEFAULT_OUTPUT_MD = Path("reports/model/evaluation.md")
DEFAULT_TABLES_DIR = Path("reports/model/tables")
DEFAULT_FIGURES_DIR = Path("reports/model/figures")
SCORE_DIRECTION = "higher score means higher inspection priority"


def _resolve(path: Path, project_root: Path) -> Path:
    return path if path.is_absolute() else project_root / path


def _relative(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _score(row: dict[str, str], column: str = "anomaly_score") -> float:
    value = float(row[column])
    if not math.isfinite(value):
        raise ValueError(f"non-finite {column} for {row.get('package_id', '<unknown>')}")
    return value


def _rank_map(rows: list[dict[str, str]], rank_column: str) -> dict[str, int]:
    return {row["package_id"]: int(row[rank_column]) for row in rows}


def _top_ids(rows: list[dict[str, str]], rank_column: str, top_n: int) -> set[str]:
    return {row["package_id"] for row in rows if int(row[rank_column]) <= top_n}


def _top_overlap(
    reference_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    reference_rank_column: str,
    candidate_rank_column: str,
    top_n: int,
) -> dict[str, Any]:
    reference_ids = _top_ids(reference_rows, reference_rank_column, top_n)
    candidate_ids = _top_ids(candidate_rows, candidate_rank_column, top_n)
    overlap = reference_ids & candidate_ids
    denominator = min(top_n, len(reference_ids), len(candidate_ids)) or 1
    return {
        "top_n": top_n,
        "overlap_count": len(overlap),
        "overlap_ratio": round(len(overlap) / denominator, 6),
    }


def _rank_correlation(
    first_rows: list[dict[str, str]],
    second_rows: list[dict[str, str]],
    first_rank_column: str,
    second_rank_column: str,
) -> float:
    first = _rank_map(first_rows, first_rank_column)
    second = _rank_map(second_rows, second_rank_column)
    package_ids = sorted(set(first) & set(second))
    if len(package_ids) < 2:
        return 1.0
    xs = [float(first[package_id]) for package_id in package_ids]
    ys = [float(second[package_id]) for package_id in package_ids]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    denominator_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denominator_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    denominator = denominator_x * denominator_y
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 6)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _distribution(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "min": 0.0,
            "p25": 0.0,
            "median": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "max": 0.0,
            "mean": 0.0,
            "std": 0.0,
        }
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return {
        "count": len(values),
        "min": round(min(values), 12),
        "p25": round(_percentile(values, 0.25), 12),
        "median": round(_percentile(values, 0.50), 12),
        "p75": round(_percentile(values, 0.75), 12),
        "p90": round(_percentile(values, 0.90), 12),
        "p95": round(_percentile(values, 0.95), 12),
        "max": round(max(values), 12),
        "mean": round(mean, 12),
        "std": round(math.sqrt(variance), 12),
    }


def _score_distribution(model_rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    groups = {
        "all": [_score(row) for row in model_rows],
        "train": [_score(row) for row in model_rows if row["split"] == "train"],
        "evaluation": [_score(row) for row in model_rows if row["split"] == "evaluation"],
    }
    return {name: _distribution(values) for name, values in groups.items()}


def _temporal_behavior(
    model_rows: list[dict[str, str]], top_n_values: tuple[int, ...]
) -> dict[str, Any]:
    by_split = {
        "train": [row for row in model_rows if row["split"] == "train"],
        "evaluation": [row for row in model_rows if row["split"] == "evaluation"],
    }
    result: dict[str, Any] = {}
    for split, rows in by_split.items():
        result[split] = _distribution([_score(row) for row in rows])
    top_n_summary = {}
    for top_n in top_n_values:
        top_rows = [row for row in model_rows if int(row["anomaly_rank"]) <= top_n]
        evaluation_count = sum(1 for row in top_rows if row["split"] == "evaluation")
        top_n_summary[str(top_n)] = {
            "evaluation_count": evaluation_count,
            "evaluation_share": round(evaluation_count / max(len(top_rows), 1), 6),
        }
    result["top_n_evaluation_share"] = top_n_summary
    return result


def _run_variant(
    feature_csv: Path,
    split_manifest_json: Path,
    temp_dir: Path,
    project_root: Path,
    seed: int,
    n_estimators: int,
    contamination: str | float,
    max_samples: str | int | float,
    name: str,
) -> list[dict[str, str]]:
    ranking_csv = temp_dir / f"{name}_ranking.csv"
    config_json = temp_dir / f"{name}_config.json"
    model_joblib = temp_dir / f"{name}_model.joblib"
    train_isolation_forest(
        feature_csv=feature_csv,
        split_manifest_json=split_manifest_json,
        ranking_csv=ranking_csv,
        config_json=config_json,
        model_joblib=model_joblib,
        project_root=project_root,
        n_estimators=n_estimators,
        contamination=contamination,
        max_samples=max_samples,
        random_seed=seed,
    )
    return _read_csv(ranking_csv)


def _seed_stability(
    model_rows: list[dict[str, str]],
    feature_csv: Path,
    split_manifest_json: Path,
    temp_dir: Path,
    project_root: Path,
    top_n_values: tuple[int, ...],
    seed_values: tuple[int, ...],
    n_estimators: int,
    contamination: str | float,
    max_samples: str | int | float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for seed in seed_values:
        variant_rows = _run_variant(
            feature_csv,
            split_manifest_json,
            temp_dir,
            project_root,
            seed,
            n_estimators,
            contamination,
            max_samples,
            f"seed_{seed}",
        )
        for top_n in top_n_values:
            overlap = _top_overlap(model_rows, variant_rows, "anomaly_rank", "anomaly_rank", top_n)
            rows.append(
                {
                    "variant": f"seed={seed}",
                    "seed": seed,
                    "n_estimators": n_estimators,
                    "contamination": contamination,
                    "max_samples": max_samples,
                    "top_n": top_n,
                    "top_n_overlap": overlap["overlap_count"],
                    "top_n_overlap_ratio": overlap["overlap_ratio"],
                    "rank_correlation": _rank_correlation(
                        model_rows, variant_rows, "anomaly_rank", "anomaly_rank"
                    ),
                }
            )
    return rows


def _sensitivity(
    model_rows: list[dict[str, str]],
    feature_csv: Path,
    split_manifest_json: Path,
    temp_dir: Path,
    project_root: Path,
    top_n_values: tuple[int, ...],
    base_seed: int,
    base_n_estimators: int,
    base_contamination: str | float,
    base_max_samples: str | int | float,
    estimator_values: tuple[int, ...],
    contamination_values: tuple[str | float, ...],
    max_samples_values: tuple[str | int | float, ...],
) -> list[dict[str, Any]]:
    variants: list[tuple[str, int, str | float, str | int | float]] = []
    for value in estimator_values:
        variants.append((f"n_estimators={value}", value, base_contamination, base_max_samples))
    for value in contamination_values:
        variants.append((f"contamination={value}", base_n_estimators, value, base_max_samples))
    for value in max_samples_values:
        variants.append((f"max_samples={value}", base_n_estimators, base_contamination, value))

    seen: set[tuple[int, str, str]] = set()
    rows: list[dict[str, Any]] = []
    for label, n_estimators, contamination, max_samples in variants:
        key = (n_estimators, str(contamination), str(max_samples))
        if key in seen:
            continue
        seen.add(key)
        variant_rows = _run_variant(
            feature_csv,
            split_manifest_json,
            temp_dir,
            project_root,
            base_seed,
            n_estimators,
            contamination,
            max_samples,
            label.replace("=", "_").replace(".", "_"),
        )
        for top_n in top_n_values:
            overlap = _top_overlap(model_rows, variant_rows, "anomaly_rank", "anomaly_rank", top_n)
            rows.append(
                {
                    "variant": label,
                    "seed": base_seed,
                    "n_estimators": n_estimators,
                    "contamination": contamination,
                    "max_samples": max_samples,
                    "top_n": top_n,
                    "top_n_overlap": overlap["overlap_count"],
                    "top_n_overlap_ratio": overlap["overlap_ratio"],
                    "rank_correlation": _rank_correlation(
                        model_rows, variant_rows, "anomaly_rank", "anomaly_rank"
                    ),
                }
            )
    return rows


def _baseline_comparison(
    model_rows: list[dict[str, str]],
    baseline_rows: list[dict[str, str]],
    top_n_values: tuple[int, ...],
) -> dict[str, Any]:
    overlaps = {
        str(top_n): _top_overlap(model_rows, baseline_rows, "anomaly_rank", "baseline_rank", top_n)
        for top_n in top_n_values
    }
    return {
        "top_n_overlap": overlaps,
        "rank_correlation": _rank_correlation(
            model_rows, baseline_rows, "anomaly_rank", "baseline_rank"
        ),
    }


def _write_distribution_svg(path: Path, model_rows: list[dict[str, str]]) -> None:
    scores = [_score(row) for row in model_rows]
    if not scores:
        return
    bins = 12
    low = min(scores)
    high = max(scores)
    width = 720
    height = 320
    padding = 40
    counts = [0 for _ in range(bins)]
    span = high - low or 1.0
    for score in scores:
        index = min(int((score - low) / span * bins), bins - 1)
        counts[index] += 1
    max_count = max(counts) or 1
    bar_width = (width - padding * 2) / bins
    rects = []
    for index, count in enumerate(counts):
        bar_height = (height - padding * 2) * count / max_count
        x = padding + index * bar_width
        y = height - padding - bar_height
        rects.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width - 3:.2f}" '
            f'height="{bar_height:.2f}" fill="#2563eb" />'
        )
    svg = "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff" />',
            f'<line x1="{padding}" y1="{height - padding}" '
            f'x2="{width - padding}" y2="{height - padding}" stroke="#111827" />',
            f'<line x1="{padding}" y1="{padding}" '
            f'x2="{padding}" y2="{height - padding}" stroke="#111827" />',
            *rects,
            f'<text x="{padding}" y="24" font-family="Arial" '
            'font-size="16" fill="#111827">Isolation Forest score distribution</text>',
            f'<text x="{padding}" y="{height - 10}" font-family="Arial" '
            f'font-size="12" fill="#374151">score range {low:.4f} to {high:.4f}</text>',
            "</svg>",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg + "\n", encoding="utf-8")


def _write_sensitivity_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    top_n = min(int(row["top_n"]) for row in rows)
    plot_rows = [row for row in rows if int(row["top_n"]) == top_n]
    width = 720
    height = 320
    padding = 42
    bar_width = (width - padding * 2) / max(len(plot_rows), 1)
    rects = []
    labels = []
    for index, row in enumerate(plot_rows):
        ratio = float(row["top_n_overlap_ratio"])
        bar_height = (height - padding * 2) * ratio
        x = padding + index * bar_width
        y = height - padding - bar_height
        rects.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width - 4:.2f}" '
            f'height="{bar_height:.2f}" fill="#059669" />'
        )
        labels.append(
            f'<text x="{x:.2f}" y="{height - 12}" font-family="Arial" '
            f'font-size="10" fill="#374151">{index + 1}</text>'
        )
    svg = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff" />',
            f'<line x1="{padding}" y1="{height - padding}" '
            f'x2="{width - padding}" y2="{height - padding}" stroke="#111827" />',
            f'<line x1="{padding}" y1="{padding}" '
            f'x2="{padding}" y2="{height - padding}" stroke="#111827" />',
            *rects,
            *labels,
            f'<text x="{padding}" y="24" font-family="Arial" '
            f'font-size="16" fill="#111827">Top-{top_n} sensitivity overlap</text>',
            "</svg>",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg + "\n", encoding="utf-8")


def _decisions(
    model_config: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
    top_n_values: tuple[int, ...],
) -> dict[str, Any]:
    top_n = top_n_values[0]
    top_seed = [row for row in seed_rows if row["top_n"] == top_n]
    top_sensitivity = [row for row in sensitivity_rows if row["top_n"] == top_n]
    min_seed_overlap = min((float(row["top_n_overlap_ratio"]) for row in top_seed), default=1.0)
    min_sensitivity_overlap = min(
        (float(row["top_n_overlap_ratio"]) for row in top_sensitivity), default=1.0
    )
    return {
        "OD-1": {
            "decision": (
                "retain current Isolation Forest configuration for the next evaluation stage"
            ),
            "model_version": model_config["model_version"],
            "hyperparameters": model_config["hyperparameters"],
            "minimum_seed_top_n_overlap_ratio": round(min_seed_overlap, 6),
            "minimum_sensitivity_top_n_overlap_ratio": round(min_sensitivity_overlap, 6),
        },
        "OD-2": {
            "decision": f"use Top-{top_n} as the default inspection-capacity view for reports",
            "default_top_n": top_n,
            "rationale": (
                "compact enough for manual review while preserving sensitivity tables for larger N"
            ),
        },
        "OD-4": {
            "decision": "retain the current 20-feature set through explanation validation",
            "status": "partial",
            "feature_count": len(model_config["feature_columns"]),
            "rationale": (
                "coverage and leakage policy are satisfied; "
                "feature influence validation remains next"
            ),
        },
    }


def _write_reports(
    output_md: Path,
    report: dict[str, Any],
    seed_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
) -> None:
    model_version = report["artifact_versions"]["model_version"]
    lines = [
        "# Model Evaluation",
        "",
        "This report is generated by `modeling/evaluate_anomaly_ranking.py`. Do not edit manually.",
        "",
        "## Scope",
        "",
        f"- Model version: `{model_version}`",
        f"- Rows evaluated: {report['row_count']}",
        f"- Feature count: {report['feature_count']}",
        f"- Top-N values: {', '.join(str(value) for value in report['top_n_values'])}",
        f"- Score direction: {SCORE_DIRECTION}",
        "- Scores prioritize inspection; they are not legal conclusions.",
        "- Evaluation uses unsupervised stability, sensitivity, distribution, "
        "temporal, and baseline checks because validated anomaly labels are unavailable.",
        "",
        "## Score Distribution",
        "",
    ]
    for split in ["all", "train", "evaluation"]:
        stats = report["score_distribution"][split]
        lines.append(
            f"- {split}: count={stats['count']}, median={stats['median']}, "
            f"p95={stats['p95']}, max={stats['max']}"
        )
    lines.extend(["", "## Temporal Behavior", ""])
    for top_n, summary in report["temporal_behavior"]["top_n_evaluation_share"].items():
        lines.append(
            f"- Top-{top_n}: evaluation_count={summary['evaluation_count']}, "
            f"evaluation_share={summary['evaluation_share']}"
        )
    lines.extend(["", "## Stability and Sensitivity", ""])
    if seed_rows:
        worst_seed = min(seed_rows, key=lambda row: float(row["top_n_overlap_ratio"]))
        lines.append(
            f"- Lowest seed overlap: {worst_seed['variant']} "
            f"Top-{worst_seed['top_n']} = {worst_seed['top_n_overlap_ratio']}"
        )
    if sensitivity_rows:
        worst_sensitivity = min(sensitivity_rows, key=lambda row: float(row["top_n_overlap_ratio"]))
        lines.append(
            f"- Lowest sensitivity overlap: {worst_sensitivity['variant']} "
            f"Top-{worst_sensitivity['top_n']} = "
            f"{worst_sensitivity['top_n_overlap_ratio']}"
        )
    lines.extend(["", "## Baseline Comparison", ""])
    for top_n, overlap in report["baseline_comparison"]["top_n_overlap"].items():
        lines.append(
            f"- Top-{top_n}: overlap={overlap['overlap_count']}, ratio={overlap['overlap_ratio']}"
        )
    lines.append(
        f"- Rank correlation with baseline: {report['baseline_comparison']['rank_correlation']}"
    )
    lines.extend(["", "## Decisions", ""])
    for decision_id, decision in report["decisions"].items():
        lines.append(f"- {decision_id}: {decision['decision']}")
    lines.extend(
        [
            "",
            "## Generated Artifacts",
            "",
            f"- JSON: `{report['outputs']['json']}`",
            f"- Tables: `{report['outputs']['tables_dir']}`",
            f"- Figure: `{report['outputs']['score_distribution_svg']}`",
            "",
        ]
    )
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")


def evaluate_anomaly_ranking(
    feature_csv: Path = DEFAULT_FEATURE_CSV,
    split_manifest_json: Path = DEFAULT_SPLIT_MANIFEST,
    model_config_json: Path = DEFAULT_MODEL_CONFIG,
    model_ranking_csv: Path = DEFAULT_MODEL_RANKING,
    baseline_config_json: Path = DEFAULT_BASELINE_CONFIG,
    baseline_ranking_csv: Path = DEFAULT_BASELINE_RANKING,
    output_json: Path = DEFAULT_OUTPUT_JSON,
    output_md: Path = DEFAULT_OUTPUT_MD,
    tables_dir: Path = DEFAULT_TABLES_DIR,
    figures_dir: Path = DEFAULT_FIGURES_DIR,
    project_root: Path | None = None,
    top_n_values: tuple[int, ...] = (20, 50),
    seed_values: tuple[int, ...] = (7, 42, 99),
    estimator_values: tuple[int, ...] = (100, 200, 300),
    contamination_values: tuple[str | float, ...] = ("auto", 0.05, 0.1),
    max_samples_values: tuple[str | int | float, ...] = ("auto", 0.7),
) -> dict[str, Any]:
    project_root = (project_root or Path.cwd()).resolve()
    feature_csv = _resolve(feature_csv, project_root)
    split_manifest_json = _resolve(split_manifest_json, project_root)
    model_config_json = _resolve(model_config_json, project_root)
    model_ranking_csv = _resolve(model_ranking_csv, project_root)
    baseline_config_json = _resolve(baseline_config_json, project_root)
    baseline_ranking_csv = _resolve(baseline_ranking_csv, project_root)
    output_json = _resolve(output_json, project_root)
    output_md = _resolve(output_md, project_root)
    tables_dir = _resolve(tables_dir, project_root)
    figures_dir = _resolve(figures_dir, project_root)

    model_config = _read_json(model_config_json)
    baseline_config = _read_json(baseline_config_json)
    split_manifest = _read_json(split_manifest_json)
    model_rows = _read_csv(model_ranking_csv)
    baseline_rows = _read_csv(baseline_ranking_csv)
    if len(model_rows) != int(model_config["scored_row_count"]):
        raise ValueError("model ranking row count differs from config")
    if model_config["score_direction"] != SCORE_DIRECTION:
        raise ValueError("unexpected model score direction")
    if baseline_config.get("feature_matrix_sha256") != model_config.get("feature_matrix_sha256"):
        raise ValueError("baseline and model use different feature matrix hashes")

    temp_parent = project_root / ".hermes-model-eval-tmp"
    temp_parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp_parent) as temp_name:
        temp_dir = Path(temp_name)
        hyperparameters = model_config["hyperparameters"]
        seed_rows = _seed_stability(
            model_rows,
            feature_csv,
            split_manifest_json,
            temp_dir,
            project_root,
            top_n_values,
            seed_values,
            int(hyperparameters["n_estimators"]),
            hyperparameters["contamination"],
            hyperparameters["max_samples"],
        )
        sensitivity_rows = _sensitivity(
            model_rows,
            feature_csv,
            split_manifest_json,
            temp_dir,
            project_root,
            top_n_values,
            int(model_config["random_seed"]),
            int(hyperparameters["n_estimators"]),
            hyperparameters["contamination"],
            hyperparameters["max_samples"],
            estimator_values,
            contamination_values,
            max_samples_values,
        )
    try:
        temp_parent.rmdir()
    except OSError:
        pass

    distribution = _score_distribution(model_rows)
    temporal = _temporal_behavior(model_rows, top_n_values)
    baseline = _baseline_comparison(model_rows, baseline_rows, top_n_values)
    decisions = _decisions(model_config, seed_rows, sensitivity_rows, top_n_values)
    score_svg = figures_dir / "score_distribution.svg"
    sensitivity_svg = figures_dir / "hyperparameter_sensitivity.svg"

    report = {
        "schema_version": 1,
        "artifact_versions": {
            "model_version": model_config["model_version"],
            "model_config": _relative(model_config_json, project_root),
            "model_config_sha256": _sha256(model_config_json),
            "model_ranking": _relative(model_ranking_csv, project_root),
            "model_ranking_sha256": _sha256(model_ranking_csv),
            "baseline_config": _relative(baseline_config_json, project_root),
            "baseline_config_sha256": _sha256(baseline_config_json),
            "baseline_ranking": _relative(baseline_ranking_csv, project_root),
            "baseline_ranking_sha256": _sha256(baseline_ranking_csv),
            "feature_matrix_sha256": model_config["feature_matrix_sha256"],
            "split_manifest_sha256": model_config["split_manifest_sha256"],
            "canonical_dataset_sha256": split_manifest.get("canonical_dataset", {}).get("sha256"),
        },
        "row_count": len(model_rows),
        "feature_count": len(model_config["feature_columns"]),
        "top_n_values": list(top_n_values),
        "score_direction": SCORE_DIRECTION,
        "score_distribution": distribution,
        "temporal_behavior": temporal,
        "seed_stability": seed_rows,
        "hyperparameter_sensitivity": sensitivity_rows,
        "baseline_comparison": baseline,
        "decisions": decisions,
        "limitations": [
            "No validated anomaly labels are available; evaluation uses stability "
            "and sensitivity evidence.",
            "The 2026 evaluation split is a partial snapshot, not a full calendar year.",
            "Scores are inspection-priority signals, not legal conclusions.",
        ],
        "outputs": {
            "json": _relative(output_json, project_root),
            "markdown": _relative(output_md, project_root),
            "tables_dir": _relative(tables_dir, project_root),
            "score_distribution_svg": _relative(score_svg, project_root),
            "hyperparameter_sensitivity_svg": _relative(sensitivity_svg, project_root),
        },
    }

    _write_csv(
        tables_dir / "seed_stability.csv",
        seed_rows,
        [
            "variant",
            "seed",
            "n_estimators",
            "contamination",
            "max_samples",
            "top_n",
            "top_n_overlap",
            "top_n_overlap_ratio",
            "rank_correlation",
        ],
    )
    _write_csv(
        tables_dir / "hyperparameter_sensitivity.csv",
        sensitivity_rows,
        [
            "variant",
            "seed",
            "n_estimators",
            "contamination",
            "max_samples",
            "top_n",
            "top_n_overlap",
            "top_n_overlap_ratio",
            "rank_correlation",
        ],
    )
    baseline_rows_for_csv = [
        {
            "top_n": top_n,
            "top_n_overlap": overlap["overlap_count"],
            "top_n_overlap_ratio": overlap["overlap_ratio"],
            "rank_correlation": baseline["rank_correlation"],
        }
        for top_n, overlap in baseline["top_n_overlap"].items()
    ]
    _write_csv(
        tables_dir / "baseline_comparison.csv",
        baseline_rows_for_csv,
        ["top_n", "top_n_overlap", "top_n_overlap_ratio", "rank_correlation"],
    )
    _write_distribution_svg(score_svg, model_rows)
    _write_sensitivity_svg(sensitivity_svg, sensitivity_rows)
    _write_json(output_json, report)
    _write_reports(output_md, report, seed_rows, sensitivity_rows)
    return {
        "model_version": model_config["model_version"],
        "row_count": len(model_rows),
        "feature_count": len(model_config["feature_columns"]),
        "output_json": _relative(output_json, project_root),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate unsupervised anomaly ranking")
    parser.add_argument("--feature-csv", type=Path, default=DEFAULT_FEATURE_CSV)
    parser.add_argument("--split-manifest-json", type=Path, default=DEFAULT_SPLIT_MANIFEST)
    parser.add_argument("--model-config-json", type=Path, default=DEFAULT_MODEL_CONFIG)
    parser.add_argument("--model-ranking-csv", type=Path, default=DEFAULT_MODEL_RANKING)
    parser.add_argument("--baseline-config-json", type=Path, default=DEFAULT_BASELINE_CONFIG)
    parser.add_argument("--baseline-ranking-csv", type=Path, default=DEFAULT_BASELINE_RANKING)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--tables-dir", type=Path, default=DEFAULT_TABLES_DIR)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES_DIR)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = evaluate_anomaly_ranking(
        feature_csv=args.feature_csv,
        split_manifest_json=args.split_manifest_json,
        model_config_json=args.model_config_json,
        model_ranking_csv=args.model_ranking_csv,
        baseline_config_json=args.baseline_config_json,
        baseline_ranking_csv=args.baseline_ranking_csv,
        output_json=args.output_json,
        output_md=args.output_md,
        tables_dir=args.tables_dir,
        figures_dir=args.figures_dir,
        project_root=args.project_root,
    )
    print(
        "Wrote model evaluation: "
        f"{result['output_json']} | rows={result['row_count']} features={result['feature_count']} "
        f"model_version={result['model_version']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
