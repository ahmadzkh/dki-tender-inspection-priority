from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.analyze_tender_data import (  # noqa: E402
    CANONICAL_COLUMNS,
    NUMERIC_FIELDS,
    RATIO_FIELDS,
    analyze_tender_data,
)


def _canonical_row(
    *,
    package_id: str,
    year: str,
    work_unit: str,
    supplier_name: str,
    contract_value: str,
    pdn_value: str,
    hps: str,
    pagu: str,
    procurement_method: str = "Tender Cepat",
    procurement_type: str = "Jasa Lainnya",
    eligible_for_model: str = "true",
    is_multi_provider: str = "false",
    source_row_count: str = "1",
) -> dict[str, str]:
    row = {column: "" for column in CANONICAL_COLUMNS}
    row.update(
        {
            "package_id": package_id,
            "year": year,
            "institution": "PROVINSI DKI JAKARTA",
            "work_unit": work_unit,
            "rup_code": f"RUP-{package_id}",
            "transaction_source": "Tender",
            "funding_source": "APBD",
            "procurement_method": procurement_method,
            "procurement_type": procurement_type,
            "package_name": f"Paket {package_id}",
            "package_status": "SELESAI",
            "supplier_name": supplier_name,
            "contract_value": contract_value,
            "pdn_value": pdn_value,
            "source_row_count": source_row_count,
            "source_files_json": '["datasets/raw/fixture.csv"]',
            "source_row_numbers": "[2]",
            "source_supplier_names_json": json.dumps([supplier_name]) if supplier_name else "",
            "source_total_nilai_values_json": json.dumps([contract_value])
            if contract_value
            else "",
            "source_nilai_pdn_values_json": json.dumps([pdn_value]) if pdn_value else "",
            "is_multi_provider": is_multi_provider,
            "eligible_for_model": eligible_for_model,
            "canonicalization_status": "single_source_row"
            if eligible_for_model == "true"
            else "multi_provider_ambiguous",
            "enrichment_status": "success",
            "enrichment_response_path": f"datasets/raw/enrichment/{package_id}.json",
            "enrichment_http_status": "200",
            "enrichment_fetched_at_utc": "2026-07-15T00:00:00+00:00",
            "hps": hps,
            "hps_available": "true" if hps else "false",
            "pagu": pagu,
            "pagu_available": "true" if pagu else "false",
            "metode_evaluasi": "Harga Terendah" if eligible_for_model == "true" else "",
            "metode_evaluasi_available": eligible_for_model,
            "metadata_available": eligible_for_model,
            "metadata_json": '{"kode_tender":"' + package_id + '"}'
            if eligible_for_model == "true"
            else "",
            "jadwal_available": eligible_for_model,
            "jadwal_json": '[{"tahapan":"Pengumuman"}]' if eligible_for_model == "true" else "",
        }
    )
    return row


def _write_canonical(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CANONICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def test_should_generate_reproducible_eda_summary_tables_and_figures(tmp_path: Path) -> None:
    canonical_csv = tmp_path / "datasets" / "processed" / "tenders_canonical.csv"
    output_dir = tmp_path / "reports" / "eda"
    _write_canonical(
        canonical_csv,
        [
            _canonical_row(
                package_id="00123",
                year="2024",
                work_unit="Satker A",
                supplier_name="Penyedia A",
                contract_value="100",
                pdn_value="100",
                hps="120",
                pagu="150",
            ),
            _canonical_row(
                package_id="00456",
                year="2024",
                work_unit="Satker A",
                supplier_name="Penyedia A",
                contract_value="110",
                pdn_value="55",
                hps="130",
                pagu="150",
            ),
            _canonical_row(
                package_id="00789",
                year="2025",
                work_unit="Satker B",
                supplier_name="Penyedia B",
                contract_value="120",
                pdn_value="0",
                hps="",
                pagu="200",
                procurement_type="Pekerjaan Konstruksi",
            ),
            _canonical_row(
                package_id="00999",
                year="2026",
                work_unit="Satker B",
                supplier_name="Penyedia C",
                contract_value="5000",
                pdn_value="2500",
                hps="5500",
                pagu="6000",
            ),
            _canonical_row(
                package_id="01000",
                year="2025",
                work_unit="Satker C",
                supplier_name="",
                contract_value="",
                pdn_value="",
                hps="1000",
                pagu="1200",
                eligible_for_model="false",
                is_multi_provider="true",
                source_row_count="2",
            ),
        ],
    )

    summary = analyze_tender_data(canonical_csv=canonical_csv, output_dir=output_dir)

    assert summary["dataset"]["row_count"] == 5
    assert summary["dataset"]["unique_package_count"] == 5
    assert summary["dataset"]["eligible_for_model_count"] == 4
    assert summary["dataset"]["multi_provider_count"] == 1
    assert summary["missingness"]["hps"]["missing_count"] == 1
    assert set(summary["outliers"]) == {*NUMERIC_FIELDS, *RATIO_FIELDS}
    assert summary["outliers"]["contract_value"]["upper_outlier_count"] == 1
    assert summary["concentration"]["supplier_hhi_by_package_count"] > 0
    assert summary["year_summary"]["2026"]["is_partial_snapshot"] is True
    assert "canonical_csv_sha256" in summary["dataset"]

    table_dir = output_dir / "tables"
    figure_dir = output_dir / "figures"
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "summary.md").exists()
    assert (table_dir / "value_summary.csv").exists()
    assert (table_dir / "missingness.csv").exists()
    assert (table_dir / "year_summary.csv").exists()
    assert (table_dir / "supplier_concentration.csv").exists()
    assert (table_dir / "work_unit_concentration.csv").exists()
    assert (table_dir / "category_summary.csv").exists()
    assert (table_dir / "outlier_summary.csv").exists()
    assert (figure_dir / "contract_value_distribution.svg").exists()
    assert (figure_dir / "supplier_concentration_top10.svg").exists()

    markdown = (output_dir / "summary.md").read_text(encoding="utf-8")
    assert "5 canonical rows" in markdown
    assert "2026 adalah snapshot parsial" in markdown
    assert "bukan label fraud" in markdown

    with (table_dir / "outlier_summary.csv").open(encoding="utf-8", newline="") as csv_file:
        outlier_rows = list(csv.DictReader(csv_file))
    assert {row["field"] for row in outlier_rows} == {*NUMERIC_FIELDS, *RATIO_FIELDS}
    assert "top_upper_outliers" not in outlier_rows[0]


def test_should_fail_when_canonical_identifiers_are_not_unique(tmp_path: Path) -> None:
    canonical_csv = tmp_path / "datasets" / "processed" / "tenders_canonical.csv"
    _write_canonical(
        canonical_csv,
        [
            _canonical_row(
                package_id="00123",
                year="2024",
                work_unit="Satker A",
                supplier_name="Penyedia A",
                contract_value="100",
                pdn_value="100",
                hps="120",
                pagu="150",
            ),
            _canonical_row(
                package_id="00123",
                year="2025",
                work_unit="Satker B",
                supplier_name="Penyedia B",
                contract_value="200",
                pdn_value="100",
                hps="250",
                pagu="300",
            ),
        ],
    )

    try:
        analyze_tender_data(canonical_csv=canonical_csv, output_dir=tmp_path / "reports" / "eda")
    except ValueError as error:
        assert "package_id must be unique" in str(error)
    else:
        raise AssertionError("Expected duplicate package_id validation failure")
