from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote

SOURCE_CSV = Path("datasets/raw/realisasi_dki_jakarta_2024_2026.csv")
DEFAULT_CACHE_DIR = Path("datasets/raw/enrichment/inaproc_tender_details")
DEFAULT_OUTPUT_JSON = Path("reports/data/enrichment_coverage.json")
DEFAULT_OUTPUT_MD = Path("reports/data/enrichment_coverage.md")
COVERAGE_FIELDS = ("hps", "pagu", "metode_evaluasi", "metadata", "jadwal")


def _is_available(value: Any) -> bool:
    return value not in (None, "", [], {})


def _read_unique_packages(source_csv: Path) -> list[dict[str, str]]:
    packages: list[dict[str, str]] = []
    seen: set[str] = set()
    with source_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = reader.fieldnames or []
        required = {"kode_paket", "tahun_anggaran"}
        missing_columns = required - set(fieldnames)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"{source_csv}: missing required column(s): {missing}")
        for row in reader:
            package_id = (row.get("kode_paket") or "").strip()
            year = (row.get("tahun_anggaran") or "").strip()
            if not package_id:
                raise ValueError(f"{source_csv}: blank kode_paket found")
            if package_id in seen:
                continue
            seen.add(package_id)
            packages.append({"package_id": package_id, "year": year or "unknown"})
    return packages


def _response_path(cache_dir: Path, package_id: str) -> Path:
    return cache_dir / "responses" / f"{quote(package_id, safe='')}.json"


def _load_record(cache_dir: Path, package_id: str) -> dict[str, Any] | None:
    path = _response_path(cache_dir, package_id)
    if not path.exists():
        return None
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError(f"{path}: response cache root must be an object")
    return record


def _new_bucket() -> dict[str, Any]:
    return {
        "eligible_package_count": 0,
        "attempted_package_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "missing_response_count": 0,
        "field_available_counts": dict.fromkeys(COVERAGE_FIELDS, 0),
    }


def _add_field_counts(bucket: dict[str, Any], record: dict[str, Any] | None) -> None:
    if not record or record.get("status") != "success":
        return
    detail = record.get("detail")
    detail = detail if isinstance(detail, dict) else {}
    for field in COVERAGE_FIELDS:
        if _is_available(detail.get(field)):
            bucket["field_available_counts"][field] += 1


def _finalize_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    total = bucket["eligible_package_count"]
    field_coverage = {}
    for field in COVERAGE_FIELDS:
        available = bucket["field_available_counts"][field]
        missing = total - available
        pct = round((available / total) * 100, 2) if total else 0.0
        field_coverage[field] = {
            "available_count": available,
            "missing_count": missing,
            "coverage_pct": pct,
        }

    return {
        "eligible_package_count": total,
        "attempted_package_count": bucket["attempted_package_count"],
        "success_count": bucket["success_count"],
        "failure_count": bucket["failure_count"],
        "missing_response_count": bucket["missing_response_count"],
        "field_coverage": field_coverage,
    }


def build_coverage_report(
    source_csv: Path,
    cache_dir: Path,
    output_json: Path,
    output_md: Path,
) -> dict[str, Any]:
    packages = _read_unique_packages(source_csv)
    global_bucket = _new_bucket()
    year_buckets: dict[str, dict[str, Any]] = {}
    status_counts: Counter[str] = Counter()
    http_status_counts: Counter[str] = Counter()
    missing_package_ids: list[str] = []
    failed_package_ids: dict[str, str] = {}

    for package in packages:
        package_id = package["package_id"]
        year = package["year"]
        year_bucket = year_buckets.setdefault(year, _new_bucket())
        for bucket in (global_bucket, year_bucket):
            bucket["eligible_package_count"] += 1

        record = _load_record(cache_dir, package_id)
        if record is None:
            status = "missing_response"
            missing_package_ids.append(package_id)
            for bucket in (global_bucket, year_bucket):
                bucket["missing_response_count"] += 1
            status_counts[status] += 1
            continue

        status = str(record.get("status") or "unknown")
        status_counts[status] += 1
        http_status = record.get("http_status")
        if http_status is not None:
            http_status_counts[str(http_status)] += 1

        for bucket in (global_bucket, year_bucket):
            bucket["attempted_package_count"] += 1
            if status == "success":
                bucket["success_count"] += 1
            else:
                bucket["failure_count"] += 1
            _add_field_counts(bucket, record)

        if status != "success":
            failed_package_ids[package_id] = status

    report = {
        "schema_version": 1,
        "source_csv": source_csv.as_posix(),
        "cache_dir": cache_dir.as_posix(),
        **_finalize_bucket(global_bucket),
        "status_counts": dict(sorted(status_counts.items())),
        "http_status_counts": dict(sorted(http_status_counts.items())),
        "by_year": {year: _finalize_bucket(year_buckets[year]) for year in sorted(year_buckets)},
        "missing_package_ids": missing_package_ids,
        "failed_package_ids": dict(sorted(failed_package_ids.items())),
    }
    _write_json(output_json, report)
    _write_markdown(output_md, report)
    return report


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _pct(value: float) -> str:
    return f"{value:.2f}%"


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Enrichment Coverage Report",
        "",
        "This report is generated by `pipelines/report_enrichment_coverage.py`. "
        "Do not edit manually.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Eligible unique packages | {report['eligible_package_count']} |",
        f"| Attempted packages | {report['attempted_package_count']} |",
        f"| Successful packages | {report['success_count']} |",
        f"| Failed packages | {report['failure_count']} |",
        f"| Missing response cache | {report['missing_response_count']} |",
        "",
        "## Field Coverage",
        "",
        "| Field | Available | Missing | Coverage |",
        "|---|---:|---:|---:|",
    ]
    for field, stats in report["field_coverage"].items():
        lines.append(
            f"| `{field}` | {stats['available_count']} | {stats['missing_count']} | "
            f"{_pct(stats['coverage_pct'])} |"
        )

    lines.extend(
        [
            "",
            "## Coverage by Year",
            "",
            "| Year | Eligible | Attempted | Success | Failure | Missing cache | "
            "HPS | Pagu | Method | Metadata | Jadwal |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for year, stats in report["by_year"].items():
        fields = stats["field_coverage"]
        lines.append(
            f"| {year} | {stats['eligible_package_count']} | "
            f"{stats['attempted_package_count']} | {stats['success_count']} | "
            f"{stats['failure_count']} | {stats['missing_response_count']} | "
            f"{_pct(fields['hps']['coverage_pct'])} | "
            f"{_pct(fields['pagu']['coverage_pct'])} | "
            f"{_pct(fields['metode_evaluasi']['coverage_pct'])} | "
            f"{_pct(fields['metadata']['coverage_pct'])} | "
            f"{_pct(fields['jadwal']['coverage_pct'])} |"
        )

    lines.extend(
        [
            "",
            "## Status Counts",
            "",
            "| Status | Count |",
            "|---|---:|",
        ]
    )
    for status, count in report["status_counts"].items():
        lines.append(f"| `{status}` | {count} |")

    lines.extend(
        [
            "",
            "## HTTP Status Counts",
            "",
            "| HTTP Status | Count |",
            "|---|---:|",
        ]
    )
    for status, count in report["http_status_counts"].items():
        lines.append(f"| `{status}` | {count} |")

    if report["missing_package_ids"]:
        lines.extend(
            [
                "",
                "## Missing Response Package IDs",
                "",
                ", ".join(f"`{package_id}`" for package_id in report["missing_package_ids"]),
            ]
        )
    if report["failed_package_ids"]:
        lines.extend(
            [
                "",
                "## Failed Package IDs",
                "",
                "| Package ID | Status |",
                "|---|---|",
            ]
        )
        for package_id, status in report["failed_package_ids"].items():
            lines.append(f"| `{package_id}` | `{status}` |")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish INAPROC enrichment coverage report")
    parser.add_argument("--source-csv", type=Path, default=SOURCE_CSV)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        report = build_coverage_report(
            source_csv=args.source_csv,
            cache_dir=args.cache_dir,
            output_json=args.output_json,
            output_md=args.output_md,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Coverage report failed: {error}")
        return 1

    print(
        "Wrote enrichment coverage: "
        f"{args.output_json} and {args.output_md} | "
        f"success={report['success_count']} missing_cache={report['missing_response_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
