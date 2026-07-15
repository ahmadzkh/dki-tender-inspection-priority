from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.build_canonical_dataset import CANONICAL_COLUMNS  # noqa: E402
from pipelines.build_model_features import (  # noqa: E402
    FEATURE_COLUMNS,
    METADATA_COLUMNS,
    build_model_features,
    encode_category,
)


def _schedule(start: str, end: str) -> str:
    return json.dumps(
        [
            {"tahapan": "Pengumuman", "mulai": start, "akhir": end},
            {
                "tahapan": "Upload Dokumen Penawaran",
                "mulai": "02 January 2024 00:00",
                "akhir": "05 January 2024 00:00",
            },
            {
                "tahapan": "Evaluasi Administrasi, Kualifikasi, Teknis, dan Harga",
                "mulai": "06 January 2024 00:00",
                "akhir": "08 January 2024 00:00",
            },
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _canonical_row(
    *,
    package_id: str,
    year: str,
    supplier_name: str,
    work_unit: str,
    contract_value: str,
    hps: str,
    pagu: str,
    pdn_value: str = "50",
    procurement_method: str = "Tender",
    procurement_type: str = "Jasa Lainnya",
    eligible_for_model: str = "true",
    jadwal_json: str | None = None,
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
            "supplier_name": supplier_name if eligible_for_model == "true" else "",
            "contract_value": contract_value if eligible_for_model == "true" else "",
            "pdn_value": pdn_value if eligible_for_model == "true" else "",
            "source_row_count": "1" if eligible_for_model == "true" else "2",
            "source_files_json": '["datasets/raw/fixture.csv"]',
            "source_row_numbers": "[2]",
            "source_supplier_names_json": json.dumps([supplier_name]) if supplier_name else "",
            "source_total_nilai_values_json": json.dumps([contract_value])
            if contract_value
            else "",
            "source_nilai_pdn_values_json": json.dumps([pdn_value]) if pdn_value else "",
            "is_multi_provider": "false" if eligible_for_model == "true" else "true",
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
            "metode_evaluasi": "Harga Terendah",
            "metode_evaluasi_available": "true",
            "metadata_available": "true",
            "metadata_json": '{"kode_tender":"' + package_id + '"}',
            "jadwal_available": "true" if jadwal_json else "false",
            "jadwal_json": jadwal_json or "",
        }
    )
    return row


def _write_canonical(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CANONICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def _float(row: dict[str, str], column: str) -> float:
    return float(row[column])


def test_should_build_manual_financial_temporal_and_prior_aggregate_features(
    tmp_path: Path,
) -> None:
    canonical_csv = tmp_path / "datasets" / "processed" / "tenders_canonical.csv"
    output_csv = tmp_path / "datasets" / "processed" / "model_features.csv"
    schema_json = tmp_path / "artifacts" / "feature_schema.json"
    _write_canonical(
        canonical_csv,
        [
            _canonical_row(
                package_id="002",
                year="2024",
                supplier_name="Supplier A",
                work_unit="Satker A",
                contract_value="200",
                hps="250",
                pagu="400",
                pdn_value="100",
                jadwal_json=_schedule("01 February 2024 00:00", "11 February 2024 00:00"),
            ),
            _canonical_row(
                package_id="001",
                year="2024",
                supplier_name="Supplier A",
                work_unit="Satker A",
                contract_value="100",
                hps="125",
                pagu="200",
                pdn_value="50",
                jadwal_json=_schedule("01 January 2024 00:00", "11 January 2024 00:00"),
            ),
            _canonical_row(
                package_id="003",
                year="2024",
                supplier_name="Supplier B",
                work_unit="Satker A",
                contract_value="300",
                hps="0",
                pagu="500",
                pdn_value="150",
                jadwal_json=_schedule("01 March 2024 00:00", "06 March 2024 00:00"),
            ),
            _canonical_row(
                package_id="004",
                year="2024",
                supplier_name="Supplier A",
                work_unit="Satker B",
                contract_value="400",
                hps="500",
                pagu="800",
                pdn_value="100",
                jadwal_json=_schedule("01 April 2024 00:00", "04 April 2024 00:00"),
            ),
            _canonical_row(
                package_id="005",
                year="2026",
                supplier_name="Supplier C",
                work_unit="Satker C",
                contract_value="500",
                hps="600",
                pagu="700",
                pdn_value="500",
                procurement_method="Seleksi",
                procurement_type="Pekerjaan Konstruksi",
                jadwal_json=_schedule("01 May 2026 00:00", "11 May 2026 00:00"),
            ),
            _canonical_row(
                package_id="999",
                year="2024",
                supplier_name="Supplier Z",
                work_unit="Satker Z",
                contract_value="900",
                hps="1000",
                pagu="1200",
                eligible_for_model="false",
            ),
        ],
    )

    schema = build_model_features(
        canonical_csv=canonical_csv,
        output_csv=output_csv,
        schema_json=schema_json,
    )

    rows = {row["package_id"]: row for row in _read_rows(output_csv)}
    assert list(rows) == ["001", "002", "003", "004", "005"]
    assert schema["metadata_columns"] == METADATA_COLUMNS
    assert schema["feature_columns"] == FEATURE_COLUMNS
    assert _read_rows(output_csv)[0].keys() == set(METADATA_COLUMNS + FEATURE_COLUMNS)

    first = rows["001"]
    assert math.isclose(_float(first, "log_contract_value"), math.log1p(100), rel_tol=1e-9)
    assert _float(first, "contract_to_hps_ratio") == 0.8
    assert _float(first, "hps_to_pagu_ratio") == 0.625
    assert _float(first, "savings_to_hps_ratio") == 0.2
    assert _float(first, "pdn_to_contract_ratio") == 0.5
    assert _float(first, "tender_duration_days") == 10.0
    assert _float(first, "bid_submission_duration_days") == 3.0
    assert _float(first, "evaluation_duration_days") == 2.0
    assert first["schedule_invalid_timestamp_count"] == "0"
    assert first["supplier_prior_package_count_year"] == "0"
    assert first["supplier_prior_contract_share_year"] == "0.0"

    second = rows["002"]
    assert second["supplier_prior_package_count_year"] == "1"
    assert second["supplier_prior_work_unit_package_count_year"] == "1"
    assert _float(second, "supplier_prior_contract_share_year") == 1.0
    assert _float(second, "supplier_prior_work_unit_contract_share_year") == 1.0
    assert _float(second, "work_unit_supplier_hhi_prior_package_count_year") == 1.0

    third = rows["003"]
    assert third["contract_to_hps_ratio"] == ""
    assert third["savings_to_hps_ratio"] == ""
    assert _float(third, "hps_to_pagu_ratio") == 0.0
    assert third["supplier_prior_package_count_year"] == "0"
    assert _float(third, "supplier_prior_work_unit_contract_share_year") == 0.0
    assert _float(third, "work_unit_supplier_hhi_prior_package_count_year") == 1.0

    fourth = rows["004"]
    assert fourth["supplier_prior_package_count_year"] == "2"
    assert _float(fourth, "supplier_prior_contract_share_year") == 0.5
    assert _float(fourth, "supplier_prior_work_unit_contract_share_year") == 0.0
    assert fourth["work_unit_supplier_hhi_prior_package_count_year"] == "0.0"

    snapshot = rows["005"]
    assert snapshot["is_partial_snapshot_year"] == "true"
    assert int(snapshot["procurement_method_code"]) > 0
    assert int(snapshot["procurement_type_code"]) > 0

    for row in rows.values():
        for column in FEATURE_COLUMNS:
            value = row[column]
            if value:
                assert math.isfinite(float(value)), (row["package_id"], column, value)


def test_should_encode_unknown_categories_as_zero(tmp_path: Path) -> None:
    schema = {"Tender": 1, "Seleksi": 2}
    assert encode_category("Tender", schema) == 1
    assert encode_category("Metode Baru", schema) == 0
    assert encode_category("", schema) == 0
