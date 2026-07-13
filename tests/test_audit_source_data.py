from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = PROJECT_ROOT / "pipelines" / "audit_source_data.py"


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


def _row(
    *,
    package_code: str,
    rup_code: str,
    year: str,
    provider: str,
    work_unit: str,
) -> list[str]:
    values = {
        "nama_instansi": "Provinsi DKI Jakarta",
        "nama_satuan_kerja": work_unit,
        "kode_paket": package_code,
        "kode_rup": rup_code,
        "tahun_anggaran": year,
        "sumber_transaksi": "Tender",
        "sumber_dana": "APBD",
        "nama_penyedia": provider,
        "metode_pengadaan": "Tender Cepat",
        "jenis_pengadaan": "Jasa Lainnya",
        "nama_paket": "Paket Uji",
        "status_paket": "SELESAI",
        "total_nilai": "1000",
        "nilai_pdn": "100",
    }
    return [values[column] for column in EXPECTED_COLUMNS]


def _write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(EXPECTED_COLUMNS)
        writer.writerows(rows)


def _write_manifest(project_root: Path, annual_path: Path, merged_path: Path) -> None:
    manifest = {
        "manifest_version": 1,
        "files": [
            {
                "path": annual_path.relative_to(project_root).as_posix(),
                "role": "annual_source",
                "source_years": [2024],
            },
            {
                "path": merged_path.relative_to(project_root).as_posix(),
                "role": "preexisting_merged_input",
                "source_years": [2024],
            },
        ],
    }
    manifest_path = project_root / "datasets" / "manifests" / "source_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def _run_audit(project_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, AUDIT_SCRIPT, "--project-root", project_root],
        capture_output=True,
        check=False,
        text=True,
    )


def test_should_report_source_quality_without_mutating_raw_files(tmp_path: Path) -> None:
    annual_path = tmp_path / "datasets" / "raw" / "annual.csv"
    merged_path = tmp_path / "datasets" / "raw" / "merged.csv"
    annual_rows = [
        _row(
            package_code="00123",
            rup_code="RUP-001",
            year="2024",
            provider="Penyedia A",
            work_unit="Satker A",
        ),
        _row(
            package_code="00123",
            rup_code="RUP-001",
            year="2024",
            provider="Penyedia B",
            work_unit="Satker A",
        ),
        _row(
            package_code="00456",
            rup_code="RUP-002",
            year="2024",
            provider="",
            work_unit="Satker B",
        ),
    ]
    merged_rows = annual_rows[:2]
    _write_csv(annual_path, annual_rows)
    _write_csv(merged_path, merged_rows)
    _write_manifest(tmp_path, annual_path, merged_path)
    annual_before = annual_path.read_bytes()
    merged_before = merged_path.read_bytes()

    result = _run_audit(tmp_path)

    assert result.returncode == 0, result.stderr
    json_path = tmp_path / "reports" / "data" / "source_audit.json"
    markdown_path = tmp_path / "reports" / "data" / "source_audit.md"
    report = json.loads(json_path.read_text(encoding="utf-8"))

    annual_audit = report["audit_groups"]["annual_sources"]
    merged_audit = report["audit_groups"]["merged_input"]
    assert annual_audit["row_count"] == 3
    assert annual_audit["missing_values"]["nama_penyedia"] == 1
    assert annual_audit["repeated_package_codes"] == {"00123": 2}
    assert annual_audit["multi_provider_package_codes"] == {"00123": 2}
    assert annual_audit["distributions"]["tahun_anggaran"] == {"2024": 3}
    assert annual_audit["distributions"]["nama_penyedia"]["Penyedia A"] == 1
    assert annual_audit["distributions"]["nama_satuan_kerja"] == {"Satker A": 2, "Satker B": 1}
    assert merged_audit["row_count"] == 2
    assert report["reconciliation"]["annual_minus_merged_row_count"] == 1
    assert report["reconciliation"]["annual_missing_supplier_count"] == 1
    assert json.loads(json_path.read_text(encoding="utf-8")) == report
    assert "# Source Data Audit" in markdown_path.read_text(encoding="utf-8")
    assert annual_path.read_bytes() == annual_before
    assert merged_path.read_bytes() == merged_before


def test_should_distinguish_identical_rows_from_repeated_package_codes(tmp_path: Path) -> None:
    annual_path = tmp_path / "datasets" / "raw" / "annual.csv"
    merged_path = tmp_path / "datasets" / "raw" / "merged.csv"
    provider_a = _row(
        package_code="00123",
        rup_code="RUP-001",
        year="2024",
        provider="Penyedia A",
        work_unit="Satker A",
    )
    provider_b = _row(
        package_code="00123",
        rup_code="RUP-001",
        year="2024",
        provider="Penyedia B",
        work_unit="Satker A",
    )
    _write_csv(annual_path, [provider_a, provider_b])
    _write_csv(merged_path, [provider_a])
    _write_manifest(tmp_path, annual_path, merged_path)

    result = _run_audit(tmp_path)

    assert result.returncode == 0, result.stderr
    report = json.loads(
        (tmp_path / "reports" / "data" / "source_audit.json").read_text(encoding="utf-8")
    )
    annual_audit = report["audit_groups"]["annual_sources"]
    assert annual_audit["identical_duplicate_row_count"] == 0
    assert annual_audit["repeated_package_code_row_count"] == 2
    assert annual_audit["repeated_package_codes"] == {"00123": 2}


def test_should_keep_manifest_fingerprint_stable_across_line_endings(tmp_path: Path) -> None:
    annual_path = tmp_path / "datasets" / "raw" / "annual.csv"
    merged_path = tmp_path / "datasets" / "raw" / "merged.csv"
    row = _row(
        package_code="00123",
        rup_code="RUP-001",
        year="2024",
        provider="Penyedia A",
        work_unit="Satker A",
    )
    _write_csv(annual_path, [row])
    _write_csv(merged_path, [row])
    _write_manifest(tmp_path, annual_path, merged_path)
    manifest_path = tmp_path / "datasets" / "manifests" / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_text = json.dumps(manifest, indent=2) + "\n"

    manifest_path.write_bytes(manifest_text.encode("utf-8"))
    assert _run_audit(tmp_path).returncode == 0
    lf_report = json.loads(
        (tmp_path / "reports" / "data" / "source_audit.json").read_text(encoding="utf-8")
    )
    manifest_path.write_bytes(manifest_text.replace("\n", "\r\n").encode("utf-8"))
    assert _run_audit(tmp_path).returncode == 0
    crlf_report = json.loads(
        (tmp_path / "reports" / "data" / "source_audit.json").read_text(encoding="utf-8")
    )

    assert lf_report["source_manifest"]["sha256"] == crlf_report["source_manifest"]["sha256"]


def test_should_reject_manifest_entry_when_it_is_not_an_object(tmp_path: Path) -> None:
    manifest_path = tmp_path / "datasets" / "manifests" / "source_manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps({"files": [None]}), encoding="utf-8")

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert "Each source manifest file entry must be an object" in result.stderr
    assert "Traceback" not in result.stderr


def test_should_reject_source_when_schema_is_not_expected_14_columns(tmp_path: Path) -> None:
    annual_path = tmp_path / "datasets" / "raw" / "annual.csv"
    merged_path = tmp_path / "datasets" / "raw" / "merged.csv"
    valid_row = _row(
        package_code="00123",
        rup_code="RUP-001",
        year="2024",
        provider="Penyedia A",
        work_unit="Satker A",
    )
    annual_path.parent.mkdir(parents=True)
    with annual_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(EXPECTED_COLUMNS[:-1])
        writer.writerow(valid_row[:-1])
    _write_csv(merged_path, [valid_row])
    _write_manifest(tmp_path, annual_path, merged_path)

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert "annual.csv: schema mismatch; expected exactly 14 source columns" in result.stderr


@pytest.mark.parametrize(
    ("column", "invalid_value", "expected_error"),
    [
        ("kode_paket", "", "kode_paket contains 1 blank identifier(s)"),
        ("kode_rup", "", "kode_rup contains 1 blank identifier(s)"),
        ("tahun_anggaran", "2027", "tahun_anggaran contains unexpected value(s): 2027"),
        ("status_paket", "DRAFT", "status_paket must contain only SELESAI; found DRAFT"),
        (
            "sumber_transaksi",
            "NonTender",
            "sumber_transaksi must contain only Tender; found NonTender",
        ),
    ],
)
def test_should_reject_source_when_required_value_is_invalid(
    tmp_path: Path, column: str, invalid_value: str, expected_error: str
) -> None:
    annual_path = tmp_path / "datasets" / "raw" / "annual.csv"
    merged_path = tmp_path / "datasets" / "raw" / "merged.csv"
    annual_row = _row(
        package_code="00123",
        rup_code="RUP-001",
        year="2024",
        provider="Penyedia A",
        work_unit="Satker A",
    )
    annual_row[EXPECTED_COLUMNS.index(column)] = invalid_value
    merged_row = _row(
        package_code="00456",
        rup_code="RUP-002",
        year="2024",
        provider="Penyedia B",
        work_unit="Satker B",
    )
    _write_csv(annual_path, [annual_row])
    _write_csv(merged_path, [merged_row])
    _write_manifest(tmp_path, annual_path, merged_path)

    result = _run_audit(tmp_path)

    assert result.returncode == 1
    assert f"annual.csv: {expected_error}" in result.stderr
