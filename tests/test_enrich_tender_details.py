from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENRICH_SCRIPT = PROJECT_ROOT / "pipelines" / "enrich_tender_details.py"
SPEC = importlib.util.spec_from_file_location("enrich_tender_details", ENRICH_SCRIPT)
assert SPEC is not None and SPEC.loader is not None
enrich_tender_details = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = enrich_tender_details
SPEC.loader.exec_module(enrich_tender_details)

EnrichmentConfig = enrich_tender_details.EnrichmentConfig
FetchResult = enrich_tender_details.FetchResult
fetch_package_detail = enrich_tender_details.fetch_package_detail
parse_detail_response = enrich_tender_details.parse_detail_response
run_enrichment = enrich_tender_details.run_enrichment


class FakeResponse:
    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body.encode("utf-8")

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def getcode(self) -> int:
        return self.status_code

    def read(self) -> bytes:
        return self.body


def _write_source_csv(path: Path, package_ids: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = ["kode_paket", *package_ids]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _config(tmp_path: Path, **overrides: Any) -> EnrichmentConfig:
    values = {
        "source_csv": tmp_path / "source.csv",
        "cache_dir": tmp_path / "cache",
        "base_url": "https://example.test/detail",
        "timeout_seconds": 7.0,
        "max_retries": 1,
        "delay_seconds": 0.0,
        "limit": None,
    }
    values.update(overrides)
    return EnrichmentConfig(**values)


def test_should_request_detail_with_kode_paket_timeout_and_bounded_retry(tmp_path: Path) -> None:
    calls: list[tuple[str, float]] = []

    def opener(request: Any, *, timeout: float) -> FakeResponse:
        calls.append((request.full_url, timeout))
        if len(calls) == 1:
            raise TimeoutError("temporary timeout")
        return FakeResponse(200, '{"data":{"nilai_hps":1000}}')

    result = fetch_package_detail("00123", _config(tmp_path), opener=opener)

    assert result.status_code == 200
    assert result.body == '{"data":{"nilai_hps":1000}}'
    assert result.attempts == 2
    assert calls == [
        ("https://example.test/detail?kode_paket=00123", 7.0),
        ("https://example.test/detail?kode_paket=00123", 7.0),
    ]


def test_should_stop_after_configured_retry_budget(tmp_path: Path) -> None:
    attempts = 0

    def opener(request: Any, *, timeout: float) -> FakeResponse:
        nonlocal attempts
        attempts += 1
        raise TimeoutError(f"timeout {attempts}")

    config = _config(tmp_path, max_retries=2)

    result = fetch_package_detail("00123", config, opener=opener)

    assert result.status_code is None
    assert result.attempts == 3
    assert result.error_type == "TimeoutError"
    assert attempts == 3


def test_should_retry_5xx_response_before_returning_success(tmp_path: Path) -> None:
    statuses = [500, 200]

    def opener(request: Any, *, timeout: float) -> FakeResponse:
        return FakeResponse(statuses.pop(0), '{"data":{"nilai_hps":1000}}')

    result = fetch_package_detail("00123", _config(tmp_path), opener=opener)

    assert result.status_code == 200
    assert result.attempts == 2
    assert statuses == []


@pytest.mark.parametrize(
    ("status_code", "body", "expected_status", "expected_error"),
    [
        (
            200,
            json.dumps(
                {
                    "data": {
                        "nilai_hps": None,
                        "nilai_pagu": 5000,
                        "metode_evaluasi": "Harga Terendah",
                        "jadwal": [{"nama": "Pengumuman"}],
                    }
                }
            ),
            "success",
            None,
        ),
        (200, "{not json", "invalid_response", "Response body is not valid JSON"),
        (200, '{"data":null}', "invalid_response", "Response data must be an object"),
        (404, '{"message":"not found"}', "http_error", "HTTP 404"),
        (500, '{"message":"server error"}', "http_error", "HTTP 500"),
    ],
)
def test_should_parse_success_null_malformed_4xx_and_5xx(
    status_code: int,
    body: str,
    expected_status: str,
    expected_error: str | None,
) -> None:
    parsed = parse_detail_response(
        package_id="00123",
        result=FetchResult(
            status_code=status_code,
            body=body,
            url="https://example.test/detail?kode_paket=00123",
            attempts=1,
        ),
    )

    assert parsed["status"] == expected_status
    assert parsed["http_status"] == status_code
    if expected_status == "success":
        assert parsed["detail"]["hps"] is None
        assert parsed["detail"]["pagu"] == 5000
        assert parsed["detail"]["metode_evaluasi"] == "Harga Terendah"
        assert parsed["detail"]["jadwal"] == [{"nama": "Pengumuman"}]
        assert parsed["raw_response"]["data"]["nilai_hps"] is None
    else:
        assert expected_error is not None
        assert expected_error in parsed["error_message"]


def test_should_log_transport_error_as_failed_package() -> None:
    parsed = parse_detail_response(
        package_id="00123",
        result=FetchResult(
            status_code=None,
            body="",
            url="https://example.test/detail?kode_paket=00123",
            attempts=2,
            error_type="TimeoutError",
            error_message="timeout",
        ),
    )

    assert parsed["status"] == "request_error"
    assert parsed["error_type"] == "TimeoutError"
    assert parsed["attempts"] == 2


def test_should_resume_without_duplicate_successful_request_after_interruption(
    tmp_path: Path,
) -> None:
    source_csv = tmp_path / "source.csv"
    _write_source_csv(source_csv, ["A", "B", "C", "A"])
    config = _config(tmp_path, source_csv=source_csv)
    first_calls: list[str] = []

    def interrupting_fetcher(package_id: str, _: EnrichmentConfig) -> FetchResult:
        first_calls.append(package_id)
        if package_id == "A":
            return FetchResult(200, '{"data":{"nilai_hps":100}}', "url-a", 1)
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_enrichment(config, fetcher=interrupting_fetcher)

    checkpoint = json.loads((config.cache_dir / "checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint["successful_package_ids"] == ["A"]
    assert first_calls == ["A", "B"]

    resume_calls: list[str] = []

    def resume_fetcher(package_id: str, _: EnrichmentConfig) -> FetchResult:
        resume_calls.append(package_id)
        body = json.dumps({"data": {"nilai_hps": package_id}})
        return FetchResult(200, body, f"url-{package_id}", 1)

    summary = run_enrichment(config, fetcher=resume_fetcher)

    assert resume_calls == ["B", "C"]
    assert summary["skipped_success_count"] == 1
    assert summary["success_count"] == 3


def test_should_delay_between_live_package_requests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_csv = tmp_path / "source.csv"
    _write_source_csv(source_csv, ["A", "B"])
    config = _config(tmp_path, source_csv=source_csv, delay_seconds=2.5)
    calls: list[str] = []
    sleeps: list[float] = []

    def fetcher(package_id: str, _: EnrichmentConfig) -> FetchResult:
        calls.append(package_id)
        return FetchResult(200, '{"data":{"nilai_hps":100}}', f"url-{package_id}", 1)

    monkeypatch.setattr(enrich_tender_details.time, "sleep", sleeps.append)

    run_enrichment(config, fetcher=fetcher)

    assert calls == ["A", "B"]
    assert sleeps == [2.5]


def test_should_record_http_error_and_invalid_response(tmp_path: Path) -> None:
    source_csv = tmp_path / "source.csv"
    _write_source_csv(source_csv, ["A", "B"])
    config = _config(tmp_path, source_csv=source_csv)

    def fetcher(package_id: str, _: EnrichmentConfig) -> FetchResult:
        if package_id == "A":
            return FetchResult(404, '{"message":"missing"}', "url-a", 1)
        return FetchResult(200, "{bad json", "url-b", 1)

    summary = run_enrichment(config, fetcher=fetcher)

    failure_lines = (config.cache_dir / "failures.jsonl").read_text(encoding="utf-8").splitlines()
    failures = [json.loads(line) for line in failure_lines]
    checkpoint = json.loads((config.cache_dir / "checkpoint.json").read_text(encoding="utf-8"))

    assert summary["failure_count"] == 2
    assert [failure["package_id"] for failure in failures] == ["A", "B"]
    assert [failure["status"] for failure in failures] == ["http_error", "invalid_response"]
    assert checkpoint["failed_package_ids"] == {
        "A": "http_error",
        "B": "invalid_response",
    }
