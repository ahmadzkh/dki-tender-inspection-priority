from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.build_canonical_dataset import CANONICAL_COLUMNS  # noqa: E402

DEFAULT_CANONICAL_CSV = Path("datasets/processed/tenders_canonical.csv")
DEFAULT_OUTPUT_CSV = Path("datasets/processed/model_features.csv")
DEFAULT_SCHEMA_JSON = Path("artifacts/feature_schema.json")
PARTIAL_SNAPSHOT_YEARS = {"2026"}

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
    "year_value",
    "partial_snapshot_year_flag",
    "procurement_method_code",
    "procurement_type_code",
    "log_contract_value",
    "log_hps",
    "log_pagu",
    "contract_to_hps_ratio",
    "hps_to_pagu_ratio",
    "savings_to_hps_ratio",
    "pdn_to_contract_ratio",
    "tender_duration_days",
    "bid_submission_duration_days",
    "evaluation_duration_days",
    "schedule_invalid_timestamp_count",
    "supplier_prior_package_count_year",
    "supplier_prior_work_unit_package_count_year",
    "supplier_prior_contract_share_year",
    "supplier_prior_work_unit_contract_share_year",
    "work_unit_supplier_hhi_prior_package_count_year",
]

DATETIME_FORMATS = (
    "%d %B %Y %H:%M",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
)


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


def _read_canonical(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != CANONICAL_COLUMNS:
            raise ValueError(f"{path}: schema mismatch; expected canonical dataset columns")
        rows = [
            {column: (row.get(column) or "").strip() for column in CANONICAL_COLUMNS}
            for row in reader
        ]
    package_ids = [row["package_id"] for row in rows]
    if any(not package_id for package_id in package_ids):
        raise ValueError(f"{path}: package_id contains blank value(s)")
    duplicate_count = len(package_ids) - len(set(package_ids))
    if duplicate_count:
        raise ValueError(
            f"{path}: package_id must be unique; found {duplicate_count} duplicate row(s)"
        )
    return rows


def _number(value: str) -> float | None:
    if not value:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _log1p(value: float | None) -> float | None:
    if value is None or value < 0:
        return None
    return math.log1p(value)


def _format(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return str(round(value, 10))
    return str(value)


def _parse_datetime(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    for fmt in DATETIME_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        return parsed.replace(tzinfo=None)
    return None


def _load_schedule(value: str) -> tuple[list[dict[str, Any]], int]:
    if not value:
        return [], 0
    try:
        schedule = json.loads(value)
    except json.JSONDecodeError:
        return [], 1
    if not isinstance(schedule, list):
        return [], 1
    valid_entries: list[dict[str, Any]] = []
    invalid_count = 0
    for item in schedule:
        if not isinstance(item, dict):
            invalid_count += 1
            continue
        start = _parse_datetime(str(item.get("mulai") or ""))
        end = _parse_datetime(str(item.get("akhir") or ""))
        if start is None or end is None or end < start:
            invalid_count += 1
            continue
        valid_entries.append(
            {
                "stage": str(item.get("tahapan") or ""),
                "start": start,
                "end": end,
                "days": (end - start).total_seconds() / 86400,
            }
        )
    return valid_entries, invalid_count


def _schedule_features(value: str) -> dict[str, Any]:
    entries, invalid_count = _load_schedule(value)
    if not entries:
        return {
            "schedule_start": None,
            "tender_duration_days": None,
            "bid_submission_duration_days": None,
            "evaluation_duration_days": None,
            "schedule_invalid_timestamp_count": invalid_count,
        }
    start = min(entry["start"] for entry in entries)
    end = max(entry["end"] for entry in entries)
    bid_days = sum(
        entry["days"] for entry in entries if "Upload Dokumen Penawaran" in entry["stage"]
    )
    evaluation_days = sum(entry["days"] for entry in entries if "Evaluasi" in entry["stage"])
    return {
        "schedule_start": start,
        "tender_duration_days": (end - start).total_seconds() / 86400,
        "bid_submission_duration_days": bid_days,
        "evaluation_duration_days": evaluation_days,
        "schedule_invalid_timestamp_count": invalid_count,
    }


def build_category_mapping(values: list[str]) -> dict[str, int]:
    categories = sorted({value for value in values if value})
    return {value: index for index, value in enumerate(categories, start=1)}


def encode_category(value: str, mapping: dict[str, int]) -> int:
    return mapping.get(value, 0)


def _hhi(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    return sum((count / total) ** 2 for count in counts.values())


def _feature_row(
    row: dict[str, str],
    method_mapping: dict[str, int],
    type_mapping: dict[str, int],
) -> dict[str, Any]:
    contract_value = _number(row["contract_value"])
    hps = _number(row["hps"])
    pagu = _number(row["pagu"])
    pdn_value = _number(row["pdn_value"])
    contract_to_hps = _ratio(contract_value, hps)
    hps_to_pagu = _ratio(hps, pagu)
    return {
        "package_id": row["package_id"],
        "year": row["year"],
        "supplier_name": row["supplier_name"],
        "work_unit": row["work_unit"],
        "procurement_method": row["procurement_method"],
        "procurement_type": row["procurement_type"],
        "is_partial_snapshot_year": row["year"] in PARTIAL_SNAPSHOT_YEARS,
        "year_value": _number(row["year"]),
        "partial_snapshot_year_flag": 1 if row["year"] in PARTIAL_SNAPSHOT_YEARS else 0,
        "procurement_method_code": encode_category(row["procurement_method"], method_mapping),
        "procurement_type_code": encode_category(row["procurement_type"], type_mapping),
        "log_contract_value": _log1p(contract_value),
        "log_hps": _log1p(hps),
        "log_pagu": _log1p(pagu),
        "contract_to_hps_ratio": contract_to_hps,
        "hps_to_pagu_ratio": hps_to_pagu,
        "savings_to_hps_ratio": None if contract_to_hps is None else 1 - contract_to_hps,
        "pdn_to_contract_ratio": _ratio(pdn_value, contract_value),
        "_contract_value_number": contract_value or 0.0,
    }


def _sort_key(row: dict[str, Any]) -> tuple[int, datetime, str]:
    year = int(row["year"]) if str(row["year"]).isdigit() else 9999
    schedule_start = row.get("_schedule_start")
    if not isinstance(schedule_start, datetime):
        schedule_start = datetime.max
    return year, schedule_start, str(row["package_id"])


def _add_prior_aggregate_features(rows: list[dict[str, Any]]) -> None:
    year_total_contract: dict[str, float] = defaultdict(float)
    supplier_contract_by_year: dict[tuple[str, str], float] = defaultdict(float)
    supplier_count_by_year: dict[tuple[str, str], int] = defaultdict(int)
    work_unit_supplier_count_by_year: dict[tuple[str, str, str], int] = defaultdict(int)
    work_unit_supplier_contract_by_year: dict[tuple[str, str, str], float] = defaultdict(float)
    work_unit_total_contract_by_year: dict[tuple[str, str], float] = defaultdict(float)
    work_unit_counts_by_year: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)

    for row in rows:
        year = str(row["year"])
        supplier = str(row["supplier_name"])
        work_unit = str(row["work_unit"])
        contract_value = float(row.pop("_contract_value_number"))
        prior_year_total = year_total_contract[year]
        supplier_key = (year, supplier)
        work_supplier_key = (year, work_unit, supplier)
        work_unit_key = (year, work_unit)
        prior_supplier_contract = supplier_contract_by_year[supplier_key]
        prior_work_unit_total = work_unit_total_contract_by_year[work_unit_key]
        prior_work_unit_supplier_contract = work_unit_supplier_contract_by_year[work_supplier_key]

        row["supplier_prior_package_count_year"] = supplier_count_by_year[supplier_key]
        row["supplier_prior_work_unit_package_count_year"] = work_unit_supplier_count_by_year[
            work_supplier_key
        ]
        row["supplier_prior_contract_share_year"] = (
            prior_supplier_contract / prior_year_total if prior_year_total > 0 else 0.0
        )
        row["supplier_prior_work_unit_contract_share_year"] = (
            prior_work_unit_supplier_contract / prior_work_unit_total
            if prior_work_unit_total > 0
            else 0.0
        )
        row["work_unit_supplier_hhi_prior_package_count_year"] = _hhi(
            work_unit_counts_by_year[work_unit_key]
        )

        year_total_contract[year] += contract_value
        supplier_contract_by_year[supplier_key] += contract_value
        supplier_count_by_year[supplier_key] += 1
        work_unit_supplier_count_by_year[work_supplier_key] += 1
        work_unit_supplier_contract_by_year[work_supplier_key] += contract_value
        work_unit_total_contract_by_year[work_unit_key] += contract_value
        counts = work_unit_counts_by_year[work_unit_key]
        counts[supplier] = counts.get(supplier, 0) + 1


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = METADATA_COLUMNS + FEATURE_COLUMNS
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _format(row.get(column)) for column in columns})


def _write_schema(path: Path, schema: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_model_features(
    canonical_csv: Path = DEFAULT_CANONICAL_CSV,
    output_csv: Path = DEFAULT_OUTPUT_CSV,
    schema_json: Path = DEFAULT_SCHEMA_JSON,
    project_root: Path | None = None,
) -> dict[str, Any]:
    project_root = (project_root or Path.cwd()).resolve()
    canonical_csv = canonical_csv if canonical_csv.is_absolute() else project_root / canonical_csv
    output_csv = output_csv if output_csv.is_absolute() else project_root / output_csv
    schema_json = schema_json if schema_json.is_absolute() else project_root / schema_json

    canonical_rows = _read_canonical(canonical_csv)
    eligible_rows = [row for row in canonical_rows if row["eligible_for_model"].lower() == "true"]
    method_mapping = build_category_mapping([row["procurement_method"] for row in eligible_rows])
    type_mapping = build_category_mapping([row["procurement_type"] for row in eligible_rows])

    feature_rows: list[dict[str, Any]] = []
    for row in eligible_rows:
        schedule = _schedule_features(row["jadwal_json"])
        feature_row = _feature_row(row, method_mapping, type_mapping)
        feature_row.update(
            {
                "tender_duration_days": schedule["tender_duration_days"],
                "bid_submission_duration_days": schedule["bid_submission_duration_days"],
                "evaluation_duration_days": schedule["evaluation_duration_days"],
                "schedule_invalid_timestamp_count": schedule["schedule_invalid_timestamp_count"],
                "_schedule_start": schedule["schedule_start"],
            }
        )
        feature_rows.append(feature_row)

    feature_rows.sort(key=_sort_key)
    _add_prior_aggregate_features(feature_rows)
    for row in feature_rows:
        row.pop("_schedule_start", None)

    schema = {
        "schema_version": 1,
        "canonical_csv": _relative_path(canonical_csv, project_root),
        "canonical_csv_sha256": _sha256(canonical_csv),
        "output_csv": _relative_path(output_csv, project_root),
        "row_count": len(feature_rows),
        "excluded_row_count": len(canonical_rows) - len(feature_rows),
        "metadata_columns": METADATA_COLUMNS,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_encoders": {
            "procurement_method": method_mapping,
            "procurement_type": type_mapping,
            "unknown_category_code": 0,
        },
        "leakage_policy": (
            "Supplier and work-unit aggregate features use only prior rows within the same "
            "year after sorting by schedule start and package_id."
        ),
        "partial_snapshot_years": sorted(PARTIAL_SNAPSHOT_YEARS),
    }
    _write_csv(output_csv, feature_rows)
    _write_schema(schema_json, schema)
    return schema


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build leakage-safe model features")
    parser.add_argument("--canonical-csv", type=Path, default=DEFAULT_CANONICAL_CSV)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--schema-json", type=Path, default=DEFAULT_SCHEMA_JSON)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        schema = build_model_features(
            canonical_csv=args.canonical_csv,
            output_csv=args.output_csv,
            schema_json=args.schema_json,
            project_root=args.project_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Feature build failed: {error}", file=sys.stderr)
        return 1
    print(
        "Wrote model features: "
        f"{args.output_csv} | rows={schema['row_count']} features={len(schema['feature_columns'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
