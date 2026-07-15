from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.build_canonical_dataset import build_canonical_dataset  # noqa: E402

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


def _row(
    *,
    package_id: str,
    provider: str,
    total_value: str = "1000",
    pdn_value: str = "900",
    year: str = "2024",
    work_unit: str = "Satker A",
) -> dict[str, str]:
    return {
        "nama_instansi": "PROVINSI DKI JAKARTA",
        "nama_satuan_kerja": work_unit,
        "kode_paket": package_id,
        "kode_rup": "RUP-001",
        "tahun_anggaran": year,
        "sumber_transaksi": "Tender",
        "sumber_dana": "APBD",
        "nama_penyedia": provider,
        "metode_pengadaan": "Tender",
        "jenis_pengadaan": "Jasa Lainnya",
        "nama_paket": "Paket Uji",
        "status_paket": "SELESAI",
        "total_nilai": total_value,
        "nilai_pdn": pdn_value,
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=SOURCE_COLUMNS)
        writer.writeheader()
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
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def _write_response(cache_dir: Path, package_id: str, detail: dict[str, object]) -> None:
    response_dir = cache_dir / "responses"
    response_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": 1,
        "package_id": package_id,
        "http_status": 200,
        "fetched_at_utc": "2026-07-14T00:00:00+00:00",
        "status": "success",
        "detail": detail,
    }
    (response_dir / f"{quote(package_id, safe='')}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def test_should_build_one_canonical_record_per_package_with_enrichment_flags(
    tmp_path: Path,
) -> None:
    annual_path = tmp_path / "datasets" / "raw" / "annual.csv"
    merged_path = tmp_path / "datasets" / "raw" / "merged.csv"
    output_csv = tmp_path / "datasets" / "processed" / "tenders_canonical.csv"
    output_json = tmp_path / "reports" / "data" / "canonical_data_quality.json"
    output_md = tmp_path / "reports" / "data" / "canonical_data_quality.md"
    cache_dir = tmp_path / "datasets" / "raw" / "enrichment" / "inaproc_tender_details"
    rows = [
        _row(package_id="00123", provider="Penyedia A"),
        _row(package_id="00456", provider="Penyedia B"),
        _row(package_id="00999", provider="Penyedia M1", total_value="1000"),
        _row(package_id="00999", provider="Penyedia M2", total_value="1500"),
    ]
    _write_csv(annual_path, rows)
    _write_csv(merged_path, rows)
    _write_manifest(tmp_path, annual_path, merged_path)
    _write_response(
        cache_dir,
        "00123",
        {
            "hps": None,
            "pagu": 2000,
            "metode_evaluasi": "Harga Terendah",
            "metadata": {"tautan_detail_tender": "https://example.test/00123"},
            "jadwal": [{"tahapan": "Pengumuman"}],
        },
    )
    _write_response(
        cache_dir,
        "00999",
        {
            "hps": 777,
            "pagu": 999,
            "metode_evaluasi": "Harga Terendah Sistem Gugur",
            "metadata": {"kode_tender": "00999"},
            "jadwal": [{"tahapan": "Penetapan"}],
        },
    )

    report = build_canonical_dataset(
        project_root=tmp_path,
        source_csv=merged_path,
        cache_dir=cache_dir,
        output_csv=output_csv,
        output_json=output_json,
        output_md=output_md,
    )

    canonical_rows = {row["package_id"]: row for row in _read_rows(output_csv)}
    assert list(canonical_rows) == ["00123", "00456", "00999"]
    assert canonical_rows["00123"]["package_id"] == "00123"
    assert canonical_rows["00123"]["source_row_count"] == "1"
    assert canonical_rows["00123"]["source_row_numbers"] == "[2]"
    assert canonical_rows["00123"]["supplier_name"] == "Penyedia A"
    assert canonical_rows["00123"]["contract_value"] == "1000"
    assert canonical_rows["00123"]["hps"] == ""
    assert canonical_rows["00123"]["hps_available"] == "false"
    assert canonical_rows["00123"]["pagu"] == "2000"
    assert canonical_rows["00123"]["pagu_available"] == "true"
    assert json.loads(canonical_rows["00123"]["jadwal_json"]) == [{"tahapan": "Pengumuman"}]

    assert canonical_rows["00456"]["enrichment_status"] == "missing_response"
    assert canonical_rows["00456"]["pagu"] == ""
    assert canonical_rows["00456"]["pagu_available"] == "false"

    multi_provider = canonical_rows["00999"]
    assert multi_provider["is_multi_provider"] == "true"
    assert multi_provider["eligible_for_model"] == "false"
    assert multi_provider["supplier_name"] == ""
    assert multi_provider["contract_value"] == ""
    assert json.loads(multi_provider["source_supplier_names_json"]) == [
        "Penyedia M1",
        "Penyedia M2",
    ]
    assert json.loads(multi_provider["source_total_nilai_values_json"]) == ["1000", "1500"]

    assert report["input"]["merged_row_count"] == 4
    assert report["output"]["canonical_row_count"] == 3
    assert report["output"]["eligible_for_model_count"] == 2
    assert report["multi_provider_packages"]["00999"]["source_row_count"] == 2
    assert report["enrichment"]["missing_response_count"] == 1
    assert output_json.exists()
    assert "00999" in output_md.read_text(encoding="utf-8")


def test_should_document_annual_missing_supplier_exclusions(tmp_path: Path) -> None:
    annual_path = tmp_path / "datasets" / "raw" / "annual.csv"
    merged_path = tmp_path / "datasets" / "raw" / "merged.csv"
    output_csv = tmp_path / "datasets" / "processed" / "tenders_canonical.csv"
    output_json = tmp_path / "reports" / "data" / "canonical_data_quality.json"
    output_md = tmp_path / "reports" / "data" / "canonical_data_quality.md"
    cache_dir = tmp_path / "datasets" / "raw" / "enrichment" / "inaproc_tender_details"
    annual_rows = [
        _row(package_id="00123", provider="Penyedia A"),
        _row(package_id="00777", provider="", year="2026"),
    ]
    _write_csv(annual_path, annual_rows)
    _write_csv(merged_path, annual_rows[:1])
    _write_manifest(tmp_path, annual_path, merged_path)
    _write_response(
        cache_dir,
        "00123",
        {
            "hps": 1000,
            "pagu": 2000,
            "metode_evaluasi": "Harga Terendah",
            "metadata": {"kode_tender": "00123"},
            "jadwal": [{"tahapan": "Pengumuman"}],
        },
    )

    report = build_canonical_dataset(
        project_root=tmp_path,
        source_csv=merged_path,
        cache_dir=cache_dir,
        output_csv=output_csv,
        output_json=output_json,
        output_md=output_md,
    )

    canonical_rows = _read_rows(output_csv)
    assert [row["package_id"] for row in canonical_rows] == ["00123"]
    assert report["input"]["annual_missing_supplier_row_count"] == 1
    assert report["input"]["annual_minus_merged_row_count"] == 1
    assert report["missing_supplier_exclusions"] == [
        {
            "package_id": "00777",
            "source_file": "datasets/raw/annual.csv",
            "source_row_number": 3,
            "year": "2026",
            "package_name": "Paket Uji",
        }
    ]
    markdown = output_md.read_text(encoding="utf-8")
    assert "missing supplier" in markdown
    assert "00777" in markdown
