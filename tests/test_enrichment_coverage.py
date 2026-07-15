from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCRIPT = PROJECT_ROOT / "pipelines" / "report_enrichment_coverage.py"
SPEC = importlib.util.spec_from_file_location("report_enrichment_coverage", REPORT_SCRIPT)
assert SPEC is not None and SPEC.loader is not None
report_enrichment_coverage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = report_enrichment_coverage
SPEC.loader.exec_module(report_enrichment_coverage)

build_coverage_report = report_enrichment_coverage.build_coverage_report


def _write_source_csv(path: Path) -> None:
    path.write_text(
        "kode_paket,tahun_anggaran\nA,2024\nB,2024\nC,2025\nD,2025\n",
        encoding="utf-8",
    )


def _write_response(cache_dir: Path, package_id: str, record: dict[str, object]) -> None:
    response_dir = cache_dir / "responses"
    response_dir.mkdir(parents=True, exist_ok=True)
    (response_dir / f"{quote(package_id, safe='')}.json").write_text(
        json.dumps({"schema_version": 1, "package_id": package_id, **record}, indent=2) + "\n",
        encoding="utf-8",
    )


def test_should_publish_coverage_report_from_enrichment_cache(tmp_path: Path) -> None:
    source_csv = tmp_path / "source.csv"
    cache_dir = tmp_path / "cache"
    output_json = tmp_path / "coverage.json"
    output_md = tmp_path / "coverage.md"
    _write_source_csv(source_csv)
    _write_response(
        cache_dir,
        "A",
        {
            "status": "success",
            "http_status": 200,
            "detail": {
                "hps": 100,
                "pagu": 150,
                "metode_evaluasi": "Harga Terendah",
                "metadata": {"last_update_ref": "ref-a"},
                "jadwal": [{"tahapan": "Pengumuman"}],
            },
        },
    )
    _write_response(
        cache_dir,
        "B",
        {
            "status": "success",
            "http_status": 200,
            "detail": {
                "hps": None,
                "pagu": 250,
                "metode_evaluasi": "",
                "metadata": None,
                "jadwal": [],
            },
        },
    )
    _write_response(
        cache_dir,
        "C",
        {
            "status": "http_error",
            "http_status": 404,
            "error_message": "HTTP 404",
        },
    )

    report = build_coverage_report(source_csv, cache_dir, output_json, output_md)

    assert output_json.exists()
    assert output_md.exists()
    assert report["eligible_package_count"] == 4
    assert report["attempted_package_count"] == 3
    assert report["success_count"] == 2
    assert report["failure_count"] == 1
    assert report["missing_response_count"] == 1
    assert report["http_status_counts"] == {"200": 2, "404": 1}
    assert report["status_counts"] == {"http_error": 1, "missing_response": 1, "success": 2}
    assert report["field_coverage"]["hps"] == {
        "available_count": 1,
        "missing_count": 3,
        "coverage_pct": 25.0,
    }
    assert report["field_coverage"]["pagu"]["available_count"] == 2
    assert report["field_coverage"]["metode_evaluasi"]["available_count"] == 1
    assert report["field_coverage"]["metadata"]["available_count"] == 1
    assert report["field_coverage"]["jadwal"]["available_count"] == 1
    assert report["by_year"]["2024"]["eligible_package_count"] == 2
    assert report["by_year"]["2024"]["success_count"] == 2
    assert report["by_year"]["2025"]["failure_count"] == 1
    assert report["by_year"]["2025"]["missing_response_count"] == 1
    assert "A" not in report["missing_package_ids"]
    assert report["missing_package_ids"] == ["D"]
    assert "## Field Coverage" in output_md.read_text(encoding="utf-8")
