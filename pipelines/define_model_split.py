from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.build_canonical_dataset import CANONICAL_COLUMNS  # noqa: E402

DEFAULT_FEATURE_CSV = Path("datasets/processed/model_features.csv")
DEFAULT_CANONICAL_CSV = Path("datasets/processed/tenders_canonical.csv")
DEFAULT_FEATURE_SCHEMA_JSON = Path("artifacts/feature_schema.json")
DEFAULT_OUTPUT_MANIFEST = Path("datasets/manifests/model_split.json")
DEFAULT_EXPERIMENT_CONFIG = Path("artifacts/model_experiment_config.json")
DEFAULT_REPORT_MD = Path("reports/model/split_decision.md")
TRAIN_YEARS = ("2024", "2025")
EVALUATION_YEARS = ("2026",)
PARTIAL_SNAPSHOT_YEARS = ("2026",)


def _relative_path(path: Path, project_root: Path) -> str:
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


def _list_fingerprint(values: list[str]) -> str:
    payload = json.dumps(values, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = list(reader.fieldnames or [])
        rows = [{field: (row.get(field) or "").strip() for field in fieldnames} for row in reader]
    return fieldnames, rows


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _ensure_unique_package_ids(path: Path, rows: list[dict[str, str]]) -> None:
    package_ids = [row.get("package_id", "") for row in rows]
    if any(not package_id for package_id in package_ids):
        raise ValueError(f"{path}: blank package_id found")
    duplicate_count = len(package_ids) - len(set(package_ids))
    if duplicate_count:
        raise ValueError(f"{path}: duplicate package_id count={duplicate_count}")


def _validate_feature_matrix(
    feature_csv: Path,
    feature_rows: list[dict[str, str]],
    fieldnames: list[str],
    schema: dict[str, Any],
) -> tuple[list[str], list[str]]:
    metadata_columns = schema.get("metadata_columns")
    feature_columns = schema.get("feature_columns")
    if not isinstance(metadata_columns, list) or not isinstance(feature_columns, list):
        raise ValueError("feature schema must contain metadata_columns and feature_columns lists")
    if not all(isinstance(column, str) for column in (*metadata_columns, *feature_columns)):
        raise ValueError("feature schema columns must be strings")
    expected = metadata_columns + feature_columns
    if fieldnames != expected:
        raise ValueError(f"{feature_csv}: header must match metadata_columns + feature_columns")
    schema_row_count = schema.get("row_count")
    if schema_row_count != len(feature_rows):
        raise ValueError(
            f"{feature_csv}: row_count {len(feature_rows)} does not match schema {schema_row_count}"
        )
    for row in feature_rows:
        for column in feature_columns:
            value = row[column]
            if value == "":
                raise ValueError(f"{feature_csv}: blank feature {column} for {row['package_id']}")
            try:
                number = float(value)
            except ValueError as error:
                raise ValueError(
                    f"{feature_csv}: non-numeric feature {column} for {row['package_id']}"
                ) from error
            if not math.isfinite(number):
                raise ValueError(
                    f"{feature_csv}: non-finite feature {column} for {row['package_id']}"
                )
    return metadata_columns, feature_columns


def _split_name(year: str) -> str:
    if year in TRAIN_YEARS:
        return "train"
    if year in EVALUATION_YEARS:
        return "evaluation"
    raise ValueError(f"unsupported split year: {year}")


def _split_rows(feature_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    splits: dict[str, list[dict[str, str]]] = {"train": [], "evaluation": []}
    for row in feature_rows:
        splits[_split_name(row["year"])].append(row)
    return splits


def _split_summary(rows: list[dict[str, str]], years: tuple[str, ...]) -> dict[str, Any]:
    package_ids = [row["package_id"] for row in rows]
    observed_years = sorted({row["year"] for row in rows})
    return {
        "years": list(years),
        "observed_years": observed_years,
        "row_count": len(rows),
        "package_id_sha256": _list_fingerprint(package_ids),
        "package_ids": package_ids,
    }


def _excluded_records(canonical_csv: Path) -> dict[str, Any]:
    fieldnames, rows = _read_csv(canonical_csv)
    if fieldnames != CANONICAL_COLUMNS:
        raise ValueError(f"{canonical_csv}: schema mismatch; expected canonical columns")
    _ensure_unique_package_ids(canonical_csv, rows)
    records = [
        {
            "package_id": row["package_id"],
            "year": row["year"],
            "reason": row["canonicalization_status"] or "not_eligible_for_model",
        }
        for row in rows
        if row["eligible_for_model"].lower() != "true"
    ]
    return {"row_count": len(records), "records": records}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_report(path: Path, manifest: dict[str, Any]) -> None:
    train = manifest["splits"]["train"]
    evaluation = manifest["splits"]["evaluation"]
    excluded = manifest["excluded_records"]
    lines = [
        "# Temporal Model Split Decision",
        "",
        "This report is generated by `pipelines/define_model_split.py`. Do not edit manually.",
        "",
        "## Decision",
        "",
        "Training uses completed tender records from 2024-2025. Evaluation uses the "
        "2026 snapshot only.",
        "",
        f"- Training: {train['row_count']} records from {', '.join(train['years'])}",
        f"- Evaluation: {evaluation['row_count']} records from {', '.join(evaluation['years'])}",
        f"- Excluded records: {excluded['row_count']}",
        "- 2026 adalah snapshot parsial, bukan tahun kalender penuh.",
        "",
        "## Leakage policy",
        "",
        "- Evaluation rows are never used for training.",
        "- Aggregate features come from precomputed prior-observation features only.",
        "- No metric in this report is a fraud label or legal conclusion.",
        "",
        "## Artifact versions",
        "",
        f"- Feature CSV: `{manifest['feature_matrix']['path']}`",
        f"- Feature CSV SHA-256: `{manifest['feature_matrix']['sha256']}`",
        f"- Feature schema: `{manifest['feature_matrix']['schema_path']}`",
        f"- Canonical CSV: `{manifest['canonical_dataset']['path']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def define_model_split(
    feature_csv: Path = DEFAULT_FEATURE_CSV,
    canonical_csv: Path = DEFAULT_CANONICAL_CSV,
    feature_schema_json: Path = DEFAULT_FEATURE_SCHEMA_JSON,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    experiment_config_json: Path = DEFAULT_EXPERIMENT_CONFIG,
    report_md: Path = DEFAULT_REPORT_MD,
    project_root: Path | None = None,
) -> dict[str, Any]:
    project_root = (project_root or Path.cwd()).resolve()
    feature_csv = feature_csv if feature_csv.is_absolute() else project_root / feature_csv
    canonical_csv = canonical_csv if canonical_csv.is_absolute() else project_root / canonical_csv
    feature_schema_json = (
        feature_schema_json
        if feature_schema_json.is_absolute()
        else project_root / feature_schema_json
    )
    output_manifest = (
        output_manifest if output_manifest.is_absolute() else project_root / output_manifest
    )
    experiment_config_json = (
        experiment_config_json
        if experiment_config_json.is_absolute()
        else project_root / experiment_config_json
    )
    report_md = report_md if report_md.is_absolute() else project_root / report_md

    schema = _read_json(feature_schema_json)
    fieldnames, feature_rows = _read_csv(feature_csv)
    _ensure_unique_package_ids(feature_csv, feature_rows)
    metadata_columns, feature_columns = _validate_feature_matrix(
        feature_csv, feature_rows, fieldnames, schema
    )
    splits = _split_rows(feature_rows)
    train_ids = {row["package_id"] for row in splits["train"]}
    evaluation_ids = {row["package_id"] for row in splits["evaluation"]}
    overlap = sorted(train_ids & evaluation_ids)
    if overlap:
        raise ValueError(f"split package overlap detected: {overlap[:5]}")

    manifest = {
        "schema_version": 1,
        "strategy": "temporal_holdout",
        "feature_matrix": {
            "path": _relative_path(feature_csv, project_root),
            "sha256": _sha256(feature_csv),
            "schema_path": _relative_path(feature_schema_json, project_root),
            "schema_sha256": _sha256(feature_schema_json),
            "row_count": len(feature_rows),
            "feature_count": len(feature_columns),
            "feature_columns": feature_columns,
            "metadata_columns": metadata_columns,
        },
        "canonical_dataset": {
            "path": _relative_path(canonical_csv, project_root),
            "sha256": _sha256(canonical_csv),
        },
        "cutoff": {
            "train_start_year": TRAIN_YEARS[0],
            "train_end_year": TRAIN_YEARS[-1],
            "evaluation_start_year": EVALUATION_YEARS[0],
            "evaluation_end_year": EVALUATION_YEARS[-1],
            "partial_snapshot_years": list(PARTIAL_SNAPSHOT_YEARS),
        },
        "splits": {
            "train": _split_summary(splits["train"], TRAIN_YEARS),
            "evaluation": _split_summary(splits["evaluation"], EVALUATION_YEARS),
        },
        "excluded_records": _excluded_records(canonical_csv),
        "leakage_policy": {
            "evaluation_rows_used_for_training": False,
            "aggregate_features_are_prior_observation_only": True,
            "aggregate_feature_columns": [
                column
                for column in feature_columns
                if column.startswith("supplier_prior_") or "hhi_prior" in column
            ],
            "source_policy": schema.get("leakage_policy", ""),
        },
        "leakage_checks": {
            "split_overlap_count": len(overlap),
            "train_uses_future_years": any(
                row["year"] not in TRAIN_YEARS for row in splits["train"]
            ),
            "evaluation_used_for_training": False,
            "unsupported_year_count": 0,
        },
    }
    config = {
        "schema_version": 1,
        "experiment_name": "temporal_holdout_2024_2025_to_2026_snapshot",
        "split_manifest": _relative_path(output_manifest, project_root),
        "feature_schema": _relative_path(feature_schema_json, project_root),
        "feature_matrix": _relative_path(feature_csv, project_root),
        "train_split": "train",
        "evaluation_split": "evaluation",
        "random_seed": 42,
        "feature_columns": feature_columns,
        "unknown_category_code": schema.get("categorical_encoders", {}).get(
            "unknown_category_code", 0
        ),
        "score_direction": "higher score means higher inspection priority",
    }
    _write_json(output_manifest, manifest)
    _write_json(experiment_config_json, config)
    _write_report(report_md, manifest)
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Define temporal model split")
    parser.add_argument("--feature-csv", type=Path, default=DEFAULT_FEATURE_CSV)
    parser.add_argument("--canonical-csv", type=Path, default=DEFAULT_CANONICAL_CSV)
    parser.add_argument("--feature-schema-json", type=Path, default=DEFAULT_FEATURE_SCHEMA_JSON)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--experiment-config-json", type=Path, default=DEFAULT_EXPERIMENT_CONFIG)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        manifest = define_model_split(
            feature_csv=args.feature_csv,
            canonical_csv=args.canonical_csv,
            feature_schema_json=args.feature_schema_json,
            output_manifest=args.output_manifest,
            experiment_config_json=args.experiment_config_json,
            report_md=args.report_md,
            project_root=args.project_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Model split definition failed: {error}", file=sys.stderr)
        return 1
    print(
        "Wrote model split: "
        f"{args.output_manifest} | train={manifest['splits']['train']['row_count']} "
        f"evaluation={manifest['splits']['evaluation']['row_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
