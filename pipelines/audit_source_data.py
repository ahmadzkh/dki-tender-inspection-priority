from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

EXPECTED_COLUMNS = [
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
MANIFEST_PATH = Path("datasets/manifests/source_manifest.json")
REPORT_DIR = Path("reports/data")


def _clean_values(frame: pd.DataFrame, column: str) -> pd.Series:
    return frame[column].astype(str).str.strip()


def _distribution(values: pd.Series) -> dict[str, int]:
    counts = values.value_counts(dropna=False)
    items = ((str(value), int(count)) for value, count in counts.items())
    return dict(sorted(items, key=lambda item: (-item[1], item[0])))


def _resolve_source_path(project_root: Path, relative_path: str) -> Path:
    source_path = (project_root / relative_path).resolve()
    if not source_path.is_relative_to(project_root):
        raise ValueError(f"Source path escapes project root: {relative_path}")
    return source_path


def _read_source_frame(project_root: Path, entry: dict[str, Any]) -> tuple[str, pd.DataFrame]:
    relative_path = entry.get("path")
    if not isinstance(relative_path, str):
        raise ValueError("Manifest source path must be a string")
    source_years = entry.get("source_years")
    if not isinstance(source_years, list) or not source_years:
        raise ValueError(f"{relative_path}: source_years must be a non-empty list")

    source_path = _resolve_source_path(project_root, relative_path)
    raw_dir = (project_root / "datasets/raw").resolve()
    if not source_path.is_relative_to(raw_dir):
        raise ValueError(f"Source file must be inside datasets/raw: {relative_path}")

    frame = pd.read_csv(source_path, dtype=str, keep_default_na=False, na_filter=False)
    if list(frame.columns) != EXPECTED_COLUMNS:
        raise ValueError(f"{relative_path}: schema mismatch; expected exactly 14 source columns")

    for column in ("kode_paket", "kode_rup"):
        blank_count = int(_clean_values(frame, column).eq("").sum())
        if blank_count:
            raise ValueError(
                f"{relative_path}: {column} contains {blank_count} blank identifier(s)"
            )

    expected_years = {str(year) for year in source_years}
    actual_years = set(_clean_values(frame, "tahun_anggaran"))
    unexpected_years = sorted(actual_years - expected_years)
    if unexpected_years:
        raise ValueError(
            f"{relative_path}: tahun_anggaran contains unexpected value(s): "
            f"{', '.join(unexpected_years)}"
        )

    invalid_statuses = sorted(set(_clean_values(frame, "status_paket")) - {"SELESAI"})
    if invalid_statuses:
        raise ValueError(
            f"{relative_path}: status_paket must contain only SELESAI; found "
            f"{', '.join(invalid_statuses)}"
        )

    invalid_transactions = sorted(set(_clean_values(frame, "sumber_transaksi")) - {"Tender"})
    if invalid_transactions:
        raise ValueError(
            f"{relative_path}: sumber_transaksi must contain only Tender; found "
            f"{', '.join(invalid_transactions)}"
        )

    return relative_path, frame


def _audit_group(name: str, frames: list[tuple[str, pd.DataFrame]]) -> dict[str, Any]:
    combined = pd.concat([frame for _, frame in frames], ignore_index=True)
    missing_values = {
        column: int(_clean_values(combined, column).eq("").sum()) for column in EXPECTED_COLUMNS
    }
    package_counts = _distribution(_clean_values(combined, "kode_paket"))
    repeated_package_codes = {
        package_code: count for package_code, count in package_counts.items() if count > 1
    }
    multi_provider_package_codes: dict[str, int] = {}
    for package_code in repeated_package_codes:
        providers = _clean_values(
            combined.loc[_clean_values(combined, "kode_paket").eq(package_code)], "nama_penyedia"
        ).replace("", pd.NA)
        provider_count = int(providers.nunique(dropna=True))
        if provider_count > 1:
            multi_provider_package_codes[package_code] = provider_count

    return {
        "name": name,
        "source_files": {path: int(len(frame)) for path, frame in frames},
        "row_count": int(len(combined)),
        "column_count": len(EXPECTED_COLUMNS),
        "unique_package_code_count": int(_clean_values(combined, "kode_paket").nunique()),
        "unique_provider_count": int(
            _clean_values(combined, "nama_penyedia").replace("", pd.NA).nunique()
        ),
        "unique_work_unit_count": int(_clean_values(combined, "nama_satuan_kerja").nunique()),
        "validation": {
            "schema": {"passed": True, "expected_column_count": len(EXPECTED_COLUMNS)},
            "identifier_columns_read_as_strings": ["kode_paket", "kode_rup"],
            "tahun_anggaran": {"passed": True},
            "status_paket": {"passed": True, "required_value": "SELESAI"},
            "sumber_transaksi": {"passed": True, "required_value": "Tender"},
        },
        "missing_values": missing_values,
        "identical_duplicate_row_count": int(
            combined.duplicated(subset=EXPECTED_COLUMNS, keep=False).sum()
        ),
        "repeated_package_code_row_count": int(sum(repeated_package_codes.values())),
        "repeated_package_codes": repeated_package_codes,
        "multi_provider_package_codes": multi_provider_package_codes,
        "distributions": {
            "tahun_anggaran": _distribution(_clean_values(combined, "tahun_anggaran")),
            "nama_penyedia": _distribution(_clean_values(combined, "nama_penyedia")),
            "nama_satuan_kerja": _distribution(_clean_values(combined, "nama_satuan_kerja")),
        },
    }


def audit_source_data(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    manifest_path = project_root / MANIFEST_PATH
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict):
        raise ValueError("Source manifest root must be an object")
    manifest_fingerprint = hashlib.sha256(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
    ).hexdigest()
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("Source manifest must contain a files list")
    if not all(isinstance(entry, dict) for entry in entries):
        raise ValueError("Each source manifest file entry must be an object")

    annual_entries = [entry for entry in entries if entry.get("role") == "annual_source"]
    merged_entries = [entry for entry in entries if entry.get("role") == "preexisting_merged_input"]
    if not annual_entries:
        raise ValueError("Source manifest must contain annual_source entries")
    if len(merged_entries) != 1:
        raise ValueError("Source manifest must contain exactly one preexisting_merged_input entry")

    annual_group = _audit_group(
        "annual_sources", [_read_source_frame(project_root, entry) for entry in annual_entries]
    )
    merged_group = _audit_group(
        "merged_input", [_read_source_frame(project_root, merged_entries[0])]
    )
    return {
        "audit_version": 1,
        "source_manifest": {
            "path": MANIFEST_PATH.as_posix(),
            "sha256": manifest_fingerprint,
        },
        "expected_columns": EXPECTED_COLUMNS,
        "audit_groups": {
            "annual_sources": annual_group,
            "merged_input": merged_group,
        },
        "reconciliation": {
            "annual_minus_merged_row_count": annual_group["row_count"] - merged_group["row_count"],
            "annual_missing_supplier_count": annual_group["missing_values"]["nama_penyedia"],
            "merged_missing_supplier_count": merged_group["missing_values"]["nama_penyedia"],
        },
    }


def _top_rows(distribution: dict[str, int], limit: int = 10) -> list[str]:
    rows = []
    for value, count in list(distribution.items())[:limit]:
        label = value if value else "(empty)"
        rows.append(f"| {label} | {count} |")
    return rows


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Source Data Audit",
        "",
        "This report is generated by `pipelines/audit_source_data.py`. Do not edit manually.",
        "",
        f"- Source manifest canonical JSON SHA-256: `{report['source_manifest']['sha256']}`",
        f"- Expected source columns: {len(report['expected_columns'])}",
        "",
    ]
    for group_key, group in report["audit_groups"].items():
        repeated_codes = json.dumps(group["repeated_package_codes"])
        multi_provider_codes = json.dumps(group["multi_provider_package_codes"])
        lines.extend(
            [
                f"## {group_key}",
                "",
                f"- Rows: {group['row_count']}",
                f"- Unique package codes: {group['unique_package_code_count']}",
                f"- Unique providers: {group['unique_provider_count']}",
                f"- Unique work units: {group['unique_work_unit_count']}",
                f"- Identical duplicate rows: {group['identical_duplicate_row_count']}",
                f"- Rows with repeated package code: {group['repeated_package_code_row_count']}",
                "",
                "### Missing values",
                "",
                "| Column | Missing rows |",
                "|---|---:|",
            ]
        )
        lines.extend(f"| {column} | {count} |" for column, count in group["missing_values"].items())
        lines.extend(
            [
                "",
                "### Duplicate and multi-provider package codes",
                "",
                f"- Repeated package codes: `{repeated_codes}`",
                f"- Multi-provider package codes: `{multi_provider_codes}`",
                "",
            ]
        )
        for distribution_name in ("tahun_anggaran", "nama_penyedia", "nama_satuan_kerja"):
            lines.extend(
                [
                    f"### Top 10 {distribution_name}",
                    "",
                    "| Value | Rows |",
                    "|---|---:|",
                    *_top_rows(group["distributions"][distribution_name]),
                    "",
                ]
            )
    reconciliation = report["reconciliation"]
    lines.extend(
        [
            "## Reconciliation",
            "",
            f"- Annual minus merged rows: {reconciliation['annual_minus_merged_row_count']}",
            f"- Annual missing suppliers: {reconciliation['annual_missing_supplier_count']}",
            f"- Merged missing suppliers: {reconciliation['merged_missing_supplier_count']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_audit_reports(project_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    report_dir = project_root / REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "source_audit.json"
    markdown_path = report_dir / "source_audit.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit immutable INAPROC source data")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        report = audit_source_data(args.project_root)
        json_path, markdown_path = write_audit_reports(args.project_root, report)
    except (OSError, ValueError, json.JSONDecodeError, pd.errors.ParserError) as error:
        print(f"Source data audit failed: {error}", file=sys.stderr)
        return 1

    print(f"Wrote source audit: {json_path} and {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
