from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

SOURCE_CSV = Path("datasets/raw/realisasi_dki_jakarta_2024_2026.csv")
SOURCE_MANIFEST = Path("datasets/manifests/source_manifest.json")
DEFAULT_CACHE_DIR = Path("datasets/raw/enrichment/inaproc_tender_details")
DEFAULT_OUTPUT_CSV = Path("datasets/processed/tenders_canonical.csv")
DEFAULT_REPORT_JSON = Path("reports/data/canonical_data_quality.json")
DEFAULT_REPORT_MD = Path("reports/data/canonical_data_quality.md")

SOURCE_COLUMNS = [
    "nama_instansi",
    "nama_satuan_kerja",
    "kode_paket",
    "kode_rup",
    "tahun_anggaran",
    "sumber_transaksi",
    "sumber_dana",
    "nama_penyedia",
    "metode_pengadaan",
    "jenis_pengadaan",
    "nama_paket",
    "status_paket",
    "total_nilai",
    "nilai_pdn",
]

CANONICAL_COLUMNS = [
    "package_id",
    "year",
    "institution",
    "work_unit",
    "rup_code",
    "transaction_source",
    "funding_source",
    "procurement_method",
    "procurement_type",
    "package_name",
    "package_status",
    "supplier_name",
    "contract_value",
    "pdn_value",
    "source_row_count",
    "source_files_json",
    "source_row_numbers",
    "source_supplier_names_json",
    "source_total_nilai_values_json",
    "source_nilai_pdn_values_json",
    "is_multi_provider",
    "eligible_for_model",
    "canonicalization_status",
    "enrichment_status",
    "enrichment_response_path",
    "enrichment_http_status",
    "enrichment_fetched_at_utc",
    "hps",
    "hps_available",
    "pagu",
    "pagu_available",
    "metode_evaluasi",
    "metode_evaluasi_available",
    "metadata_available",
    "metadata_json",
    "jadwal_available",
    "jadwal_json",
]

ENRICHMENT_FIELDS = ("hps", "pagu", "metode_evaluasi", "metadata", "jadwal")


def _relative_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _manifest_fingerprint(manifest: dict[str, Any]) -> str:
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read_manifest(project_root: Path) -> dict[str, Any]:
    manifest_path = project_root / SOURCE_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"{SOURCE_MANIFEST}: manifest root must be an object")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError(f"{SOURCE_MANIFEST}: files must be a list")
    if not all(isinstance(entry, dict) for entry in files):
        raise ValueError(f"{SOURCE_MANIFEST}: every file entry must be an object")
    return manifest


def _read_source_rows(path: Path, project_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    relative = _relative_path(path, project_root)
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != SOURCE_COLUMNS:
            raise ValueError(f"{relative}: schema mismatch; expected exactly 14 source columns")
        for row_number, row in enumerate(reader, start=2):
            cleaned = {column: (row.get(column) or "").strip() for column in SOURCE_COLUMNS}
            package_id = cleaned["kode_paket"]
            if not package_id:
                raise ValueError(f"{relative}: blank kode_paket at row {row_number}")
            cleaned["_source_file"] = relative
            cleaned["_source_row_number"] = str(row_number)
            rows.append(cleaned)
    return rows


def _annual_source_paths(project_root: Path, manifest: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    for entry in manifest["files"]:
        if entry.get("role") != "annual_source":
            continue
        relative_path = entry.get("path")
        if not isinstance(relative_path, str):
            raise ValueError("annual_source manifest path must be a string")
        path = (project_root / relative_path).resolve()
        if not path.is_relative_to(project_root.resolve()):
            raise ValueError(f"Annual source path escapes project root: {relative_path}")
        paths.append(path)
    return paths


def _missing_supplier_exclusions(annual_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    exclusions: list[dict[str, Any]] = []
    for row in annual_rows:
        if row["nama_penyedia"]:
            continue
        exclusions.append(
            {
                "package_id": row["kode_paket"],
                "source_file": row["_source_file"],
                "source_row_number": int(row["_source_row_number"]),
                "year": row["tahun_anggaran"],
                "package_name": row["nama_paket"],
            }
        )
    return exclusions


def _group_by_package(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row["kode_paket"], []).append(row)
    return groups


def _unique_non_empty(rows: list[dict[str, str]], column: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for row in rows:
        value = row[column]
        if value and value not in seen:
            values.append(value)
            seen.add(value)
    return values


def _row_values(rows: list[dict[str, str]], column: str) -> list[str]:
    return [row[column] for row in rows]


def _is_available(value: Any) -> bool:
    return value not in (None, "", [], {})


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _json_cell(value: Any) -> str:
    if not _is_available(value):
        return ""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _response_path(cache_dir: Path, package_id: str) -> Path:
    return cache_dir / "responses" / f"{quote(package_id, safe='')}.json"


def _load_enrichment(cache_dir: Path, package_id: str) -> tuple[dict[str, Any] | None, Path]:
    path = _response_path(cache_dir, package_id)
    if not path.exists():
        return None, path
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError(f"{path}: enrichment response root must be an object")
    return record, path


def _canonicalization_status(source_row_count: int, is_multi_provider: bool) -> str:
    if is_multi_provider:
        return "multi_provider_ambiguous"
    if source_row_count > 1:
        return "repeated_package"
    return "single_source_row"


def _canonical_row(
    package_id: str,
    rows: list[dict[str, str]],
    *,
    project_root: Path,
    cache_dir: Path,
) -> tuple[dict[str, str], dict[str, Any]]:
    first = rows[0]
    supplier_names = _unique_non_empty(rows, "nama_penyedia")
    is_multi_provider = len(supplier_names) > 1
    source_row_count = len(rows)
    eligible_for_model = source_row_count == 1 and not is_multi_provider
    record, response_path = _load_enrichment(cache_dir, package_id)
    status = str(record.get("status")) if record else "missing_response"
    detail = record.get("detail") if record and status == "success" else {}
    detail = detail if isinstance(detail, dict) else {}

    source_files = _unique_non_empty(rows, "_source_file")
    row_numbers = [int(row["_source_row_number"]) for row in rows]
    canonical = {
        "package_id": package_id,
        "year": first["tahun_anggaran"],
        "institution": first["nama_instansi"],
        "work_unit": first["nama_satuan_kerja"],
        "rup_code": first["kode_rup"],
        "transaction_source": first["sumber_transaksi"],
        "funding_source": first["sumber_dana"],
        "procurement_method": first["metode_pengadaan"],
        "procurement_type": first["jenis_pengadaan"],
        "package_name": first["nama_paket"],
        "package_status": first["status_paket"],
        "supplier_name": supplier_names[0] if eligible_for_model and supplier_names else "",
        "contract_value": first["total_nilai"] if eligible_for_model else "",
        "pdn_value": first["nilai_pdn"] if eligible_for_model else "",
        "source_row_count": str(source_row_count),
        "source_files_json": _json_cell(source_files),
        "source_row_numbers": _json_cell(row_numbers),
        "source_supplier_names_json": _json_cell(supplier_names),
        "source_total_nilai_values_json": _json_cell(_row_values(rows, "total_nilai")),
        "source_nilai_pdn_values_json": _json_cell(_row_values(rows, "nilai_pdn")),
        "is_multi_provider": _cell(is_multi_provider),
        "eligible_for_model": _cell(eligible_for_model),
        "canonicalization_status": _canonicalization_status(source_row_count, is_multi_provider),
        "enrichment_status": status,
        "enrichment_response_path": _relative_path(response_path, project_root) if record else "",
        "enrichment_http_status": _cell(record.get("http_status") if record else None),
        "enrichment_fetched_at_utc": _cell(record.get("fetched_at_utc") if record else None),
    }
    for field in ENRICHMENT_FIELDS:
        value = detail.get(field)
        if field in {"metadata", "jadwal"}:
            canonical[f"{field}_available"] = _cell(_is_available(value))
            canonical[f"{field}_json"] = _json_cell(value)
        else:
            canonical[field] = _cell(value)
            canonical[f"{field}_available"] = _cell(_is_available(value))

    report_entry = {
        "source_row_count": source_row_count,
        "supplier_names": supplier_names,
        "source_row_numbers": row_numbers,
    }
    return canonical, report_entry


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CANONICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Canonical Dataset Data Quality Report",
        "",
        "This report is generated by `pipelines/build_canonical_dataset.py`. Do not edit manually.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Merged input rows | {report['input']['merged_row_count']} |",
        f"| Annual source rows | {report['input']['annual_source_row_count']} |",
        "| Annual missing supplier rows | "
        f"{report['input']['annual_missing_supplier_row_count']} |",
        f"| Canonical package rows | {report['output']['canonical_row_count']} |",
        f"| Eligible for model rows | {report['output']['eligible_for_model_count']} |",
        f"| Multi-provider packages | {report['output']['multi_provider_package_count']} |",
        f"| Missing enrichment responses | {report['enrichment']['missing_response_count']} |",
        "",
        "## Missing supplier exclusions",
        "",
    ]
    exclusions = report["missing_supplier_exclusions"]
    if exclusions:
        lines.extend(
            [
                "Annual source rows with missing supplier are excluded from the merged input and "
                "remain documented here.",
                "",
                "| Package ID | Year | Source file | Source row | Package name |",
                "|---|---:|---|---:|---|",
            ]
        )
        for exclusion in exclusions:
            lines.append(
                f"| `{exclusion['package_id']}` | {exclusion['year']} | "
                f"{exclusion['source_file']} | {exclusion['source_row_number']} | "
                f"{exclusion['package_name']} |"
            )
    else:
        lines.append("No missing supplier exclusions found in annual sources.")

    lines.extend(["", "## Multi-provider packages", ""])
    multi_provider_packages = report["multi_provider_packages"]
    if multi_provider_packages:
        lines.extend(
            [
                "These packages have one canonical row but are marked `eligible_for_model=false` "
                "until feature rules explicitly handle multiple suppliers.",
                "",
                "| Package ID | Source rows | Suppliers |",
                "|---|---:|---|",
            ]
        )
        for package_id, item in multi_provider_packages.items():
            suppliers = ", ".join(item["supplier_names"])
            lines.append(f"| `{package_id}` | {item['source_row_count']} | {suppliers} |")
    else:
        lines.append("No multi-provider packages found.")

    lines.extend(["", "## Enrichment availability", "", "| Status | Count |", "|---|---:|"])
    for status, count in report["enrichment"]["status_counts"].items():
        lines.append(f"| `{status}` | {count} |")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_canonical_dataset(
    project_root: Path,
    source_csv: Path = SOURCE_CSV,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    output_csv: Path = DEFAULT_OUTPUT_CSV,
    output_json: Path = DEFAULT_REPORT_JSON,
    output_md: Path = DEFAULT_REPORT_MD,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    source_csv = source_csv if source_csv.is_absolute() else project_root / source_csv
    cache_dir = cache_dir if cache_dir.is_absolute() else project_root / cache_dir
    output_csv = output_csv if output_csv.is_absolute() else project_root / output_csv
    output_json = output_json if output_json.is_absolute() else project_root / output_json
    output_md = output_md if output_md.is_absolute() else project_root / output_md

    manifest = _read_manifest(project_root)
    annual_paths = _annual_source_paths(project_root, manifest)
    annual_rows = [
        row for annual_path in annual_paths for row in _read_source_rows(annual_path, project_root)
    ]
    merged_rows = _read_source_rows(source_csv, project_root)
    groups = _group_by_package(merged_rows)
    missing_supplier_exclusions = _missing_supplier_exclusions(annual_rows)

    canonical_rows: list[dict[str, str]] = []
    multi_provider_packages: dict[str, dict[str, Any]] = {}
    status_counts: dict[str, int] = {}
    missing_response_count = 0

    for package_id, rows in groups.items():
        canonical, report_entry = _canonical_row(
            package_id,
            rows,
            project_root=project_root,
            cache_dir=cache_dir,
        )
        canonical_rows.append(canonical)
        status = canonical["enrichment_status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "missing_response":
            missing_response_count += 1
        if canonical["is_multi_provider"] == "true":
            multi_provider_packages[package_id] = report_entry

    report = {
        "schema_version": 1,
        "source_manifest": {
            "path": SOURCE_MANIFEST.as_posix(),
            "sha256": _manifest_fingerprint(manifest),
        },
        "source_csv": _relative_path(source_csv, project_root),
        "output_csv": _relative_path(output_csv, project_root),
        "enrichment_cache_dir": _relative_path(cache_dir, project_root),
        "input": {
            "annual_source_row_count": len(annual_rows),
            "merged_row_count": len(merged_rows),
            "annual_minus_merged_row_count": len(annual_rows) - len(merged_rows),
            "annual_missing_supplier_row_count": len(missing_supplier_exclusions),
            "unique_package_count": len(groups),
        },
        "output": {
            "canonical_row_count": len(canonical_rows),
            "eligible_for_model_count": sum(
                row["eligible_for_model"] == "true" for row in canonical_rows
            ),
            "multi_provider_package_count": len(multi_provider_packages),
        },
        "enrichment": {
            "status_counts": dict(sorted(status_counts.items())),
            "missing_response_count": missing_response_count,
        },
        "missing_supplier_exclusions": missing_supplier_exclusions,
        "multi_provider_packages": multi_provider_packages,
    }
    _write_csv(output_csv, canonical_rows)
    _write_json(output_json, report)
    _write_markdown(output_md, report)
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build one-package-per-record canonical dataset")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-csv", type=Path, default=SOURCE_CSV)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        report = build_canonical_dataset(
            project_root=args.project_root,
            source_csv=args.source_csv,
            cache_dir=args.cache_dir,
            output_csv=args.output_csv,
            output_json=args.output_json,
            output_md=args.output_md,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Canonical dataset build failed: {error}", file=sys.stderr)
        return 1

    print(
        "Wrote canonical dataset: "
        f"{args.output_csv} | rows={report['output']['canonical_row_count']} "
        f"multi_provider={report['output']['multi_provider_package_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
