from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import chain
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

SOURCE_CSV = Path("datasets/raw/realisasi_dki_jakarta_2024_2026.csv")
DEFAULT_CACHE_DIR = Path("datasets/raw/enrichment/inaproc_tender_details")
USER_AGENT = "dki-tender-inspection-priority/0.1"

DETAIL_FIELD_ALIASES = {
    "hps": ("hps", "nilai_hps", "nilaiHps", "nilaiHPS"),
    "pagu": ("pagu", "nilai_pagu", "nilaiPagu"),
    "metode_evaluasi": (
        "metode_evaluasi",
        "metodeEvaluasi",
        "metode_evaluasi_tender",
        "metodeEvaluasiTender",
    ),
    "jadwal": ("jadwal", "jadwal_tender", "jadwalTender", "tahapan"),
}
CORE_DETAIL_KEYS = set(chain.from_iterable(DETAIL_FIELD_ALIASES.values())) | {"metadata"}


@dataclass(frozen=True)
class EnrichmentConfig:
    source_csv: Path
    cache_dir: Path
    base_url: str
    timeout_seconds: float
    max_retries: int
    delay_seconds: float
    limit: int | None = None

    @property
    def response_dir(self) -> Path:
        return self.cache_dir / "responses"

    @property
    def checkpoint_path(self) -> Path:
        return self.cache_dir / "checkpoint.json"

    @property
    def failure_log_path(self) -> Path:
        return self.cache_dir / "failures.jsonl"

    @property
    def summary_path(self) -> Path:
        return self.cache_dir / "run_summary.json"


@dataclass(frozen=True)
class FetchResult:
    status_code: int | None
    body: str
    url: str
    attempts: int
    error_type: str | None = None
    error_message: str | None = None


Fetcher = Callable[[str, EnrichmentConfig], FetchResult]
Opener = Callable[..., Any]


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def build_detail_url(base_url: str, package_id: str) -> str:
    if "{kode_paket}" in base_url:
        return base_url.replace("{kode_paket}", quote(package_id, safe=""))

    split = urlsplit(base_url)
    query = split.query
    extra_query = urlencode({"kode_paket": package_id})
    query = f"{query}&{extra_query}" if query else extra_query
    return urlunsplit((split.scheme, split.netloc, split.path, query, split.fragment))


def fetch_package_detail(
    package_id: str,
    config: EnrichmentConfig,
    *,
    opener: Opener = urlopen,
) -> FetchResult:
    if config.timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    if config.max_retries < 0:
        raise ValueError("max_retries must be zero or greater")

    url = build_detail_url(config.base_url, package_id)
    last_error_type: str | None = None
    last_error_message: str | None = None
    total_attempts = config.max_retries + 1

    for attempt in range(1, total_attempts + 1):
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with opener(request, timeout=config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                status_code = int(response.getcode())
                if status_code >= 500 and attempt < total_attempts:
                    last_error_type = "HTTPError"
                    last_error_message = f"HTTP {status_code}"
                    if config.delay_seconds > 0:
                        time.sleep(config.delay_seconds)
                    continue
                return FetchResult(
                    status_code=status_code,
                    body=body,
                    url=url,
                    attempts=attempt,
                )
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            if error.code < 500 or attempt == total_attempts:
                return FetchResult(
                    status_code=int(error.code),
                    body=body,
                    url=url,
                    attempts=attempt,
                )
            last_error_type = type(error).__name__
            last_error_message = str(error)
        except (TimeoutError, URLError, OSError) as error:
            last_error_type = type(error).__name__
            last_error_message = str(error)
            if attempt == total_attempts:
                break

        if config.delay_seconds > 0 and attempt < total_attempts:
            time.sleep(config.delay_seconds)

    return FetchResult(
        status_code=None,
        body="",
        url=url,
        attempts=total_attempts,
        error_type=last_error_type,
        error_message=last_error_message,
    )


def _first_present(payload: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in payload:
            return payload[alias]
    return None


def _json_or_none(body: str) -> Any:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def _detail_payload(payload: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    if "data" in payload:
        data = payload["data"]
        if not isinstance(data, dict):
            return data, payload
        detail = data.get("detail")
        return (detail, data) if isinstance(detail, dict) else (data, data)

    detail = payload.get("detail")
    return (detail, payload) if isinstance(detail, dict) else (payload, payload)


def _metadata_from(detail_payload: dict[str, Any]) -> dict[str, Any] | None:
    metadata = detail_payload.get("metadata")
    if metadata not in (None, "", [], {}):
        return metadata if isinstance(metadata, dict) else {"value": metadata}

    metadata = {
        key: value
        for key, value in detail_payload.items()
        if key not in CORE_DETAIL_KEYS and value not in (None, "", [], {})
    }
    return metadata or None


def parse_detail_response(package_id: str, result: FetchResult) -> dict[str, Any]:
    base_record: dict[str, Any] = {
        "schema_version": 1,
        "package_id": package_id,
        "request": {"parameter": "kode_paket", "package_id": package_id},
        "http_status": result.status_code,
        "attempts": result.attempts,
        "fetched_at_utc": _utc_now(),
    }

    if result.status_code is None:
        return {
            **base_record,
            "status": "request_error",
            "error_type": result.error_type,
            "error_message": result.error_message or "Request failed",
            "raw_body": result.body,
        }

    if result.status_code < 200 or result.status_code >= 300:
        raw_response = _json_or_none(result.body)
        record = {
            **base_record,
            "status": "http_error",
            "error_type": "HTTPError",
            "error_message": f"HTTP {result.status_code}",
        }
        if raw_response is None:
            record["raw_body"] = result.body
        else:
            record["raw_response"] = raw_response
        return record

    try:
        payload = json.loads(result.body)
    except json.JSONDecodeError as error:
        return {
            **base_record,
            "status": "invalid_response",
            "error_type": "JSONDecodeError",
            "error_message": f"Response body is not valid JSON: {error.msg}",
            "raw_body": result.body,
        }

    if not isinstance(payload, dict):
        return {
            **base_record,
            "status": "invalid_response",
            "error_type": "InvalidResponse",
            "error_message": "Response root must be an object",
            "raw_response": payload,
        }

    detail_payload, response_payload = _detail_payload(payload)
    if not isinstance(detail_payload, dict):
        return {
            **base_record,
            "status": "invalid_response",
            "error_type": "InvalidResponse",
            "error_message": "Response data must be an object",
            "raw_response": payload,
        }

    detail = {
        field_name: _first_present(detail_payload, aliases)
        for field_name, aliases in DETAIL_FIELD_ALIASES.items()
    }
    if detail["jadwal"] is None:
        detail["jadwal"] = _first_present(response_payload, DETAIL_FIELD_ALIASES["jadwal"])
    detail["metadata"] = _metadata_from(detail_payload)

    return {
        **base_record,
        "status": "success",
        "detail": detail,
        "raw_response": payload,
    }


def _read_package_ids(source_csv: Path, limit: int | None) -> list[str]:
    package_ids: list[str] = []
    seen: set[str] = set()
    with source_csv.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if "kode_paket" not in (reader.fieldnames or []):
            raise ValueError(f"{source_csv}: missing kode_paket column")
        for row in reader:
            package_id = (row.get("kode_paket") or "").strip()
            if not package_id:
                raise ValueError(f"{source_csv}: blank kode_paket found")
            if package_id in seen:
                continue
            seen.add(package_id)
            package_ids.append(package_id)
            if limit is not None and len(package_ids) >= limit:
                break
    return package_ids


def _cache_file(config: EnrichmentConfig, package_id: str) -> Path:
    return config.response_dir / f"{quote(package_id, safe='')}.json"


def _load_cached_success(config: EnrichmentConfig, package_id: str) -> dict[str, Any] | None:
    path = _cache_file(config, package_id)
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if isinstance(record, dict) and record.get("status") == "success":
        return record
    return None


def _load_checkpoint(config: EnrichmentConfig) -> dict[str, Any]:
    if not config.checkpoint_path.exists():
        return {
            "schema_version": 1,
            "successful_package_ids": [],
            "failed_package_ids": {},
            "updated_at_utc": None,
        }
    checkpoint = json.loads(config.checkpoint_path.read_text(encoding="utf-8"))
    if not isinstance(checkpoint, dict):
        raise ValueError(f"{config.checkpoint_path}: checkpoint root must be an object")
    checkpoint.setdefault("schema_version", 1)
    checkpoint.setdefault("successful_package_ids", [])
    checkpoint.setdefault("failed_package_ids", {})
    return checkpoint


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _save_checkpoint(config: EnrichmentConfig, checkpoint: dict[str, Any]) -> None:
    checkpoint["updated_at_utc"] = _utc_now()
    _write_json(config.checkpoint_path, checkpoint)


def _record_checkpoint(
    config: EnrichmentConfig,
    checkpoint: dict[str, Any],
    record: dict[str, Any],
) -> None:
    package_id = str(record["package_id"])
    successful = checkpoint["successful_package_ids"]
    failed = checkpoint["failed_package_ids"]
    if record["status"] == "success":
        if package_id not in successful:
            successful.append(package_id)
        failed.pop(package_id, None)
    else:
        failed[package_id] = record["status"]
    checkpoint["last_package_id"] = package_id
    _save_checkpoint(config, checkpoint)


def _append_failure(config: EnrichmentConfig, record: dict[str, Any]) -> None:
    failure = {
        "package_id": record["package_id"],
        "status": record["status"],
        "http_status": record.get("http_status"),
        "error_type": record.get("error_type"),
        "error_message": record.get("error_message"),
        "attempts": record.get("attempts"),
        "logged_at_utc": _utc_now(),
    }
    config.failure_log_path.parent.mkdir(parents=True, exist_ok=True)
    with config.failure_log_path.open("a", encoding="utf-8") as failure_log:
        failure_log.write(json.dumps(failure, ensure_ascii=False) + "\n")


def run_enrichment(
    config: EnrichmentConfig,
    *,
    fetcher: Fetcher = fetch_package_detail,
) -> dict[str, Any]:
    package_ids = _read_package_ids(config.source_csv, config.limit)
    config.response_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = _load_checkpoint(config)
    skipped_success_count = 0
    attempted_count = 0
    status_counts: dict[str, int] = {}
    live_request_count = 0

    for package_id in package_ids:
        cached_record = _load_cached_success(config, package_id)
        if cached_record is not None:
            skipped_success_count += 1
            _record_checkpoint(config, checkpoint, cached_record)
            continue

        if live_request_count > 0 and config.delay_seconds > 0:
            time.sleep(config.delay_seconds)

        result = fetcher(package_id, config)
        live_request_count += 1
        record = parse_detail_response(package_id, result)
        _write_json(_cache_file(config, package_id), record)
        _record_checkpoint(config, checkpoint, record)
        attempted_count += 1
        status_counts[record["status"]] = status_counts.get(record["status"], 0) + 1
        if record["status"] != "success":
            _append_failure(config, record)

    checkpoint = _load_checkpoint(config)
    summary = {
        "schema_version": 1,
        "source_csv": config.source_csv.as_posix(),
        "cache_dir": config.cache_dir.as_posix(),
        "package_count": len(package_ids),
        "attempted_count": attempted_count,
        "skipped_success_count": skipped_success_count,
        "success_count": len(checkpoint["successful_package_ids"]),
        "failure_count": len(checkpoint["failed_package_ids"]),
        "status_counts": status_counts,
        "updated_at_utc": _utc_now(),
    }
    _write_json(config.summary_path, summary)
    return summary


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return default if value in (None, "") else float(value)


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return default if value in (None, "") else int(value)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch resumable INAPROC package details")
    parser.add_argument("--source-csv", type=Path, default=SOURCE_CSV)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--base-url", default=os.environ.get("INAPROC_DETAIL_API_BASE_URL", ""))
    parser.add_argument(
        "--timeout",
        type=float,
        default=_env_float("INAPROC_REQUEST_TIMEOUT_S", 20.0),
        help="Per-request timeout in seconds",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=_env_int("INAPROC_MAX_RETRIES", 2),
        help="Retries after the first failed request",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=_env_float("INAPROC_REQUEST_DELAY_S", 0.0),
        help="Delay between retry attempts and live package requests in seconds",
    )
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.base_url:
        print(
            "INAPROC detail API base URL is required. Set --base-url or "
            "INAPROC_DETAIL_API_BASE_URL.",
            file=sys.stderr,
        )
        return 2

    config = EnrichmentConfig(
        source_csv=args.source_csv,
        cache_dir=args.cache_dir,
        base_url=args.base_url,
        timeout_seconds=args.timeout,
        max_retries=args.max_retries,
        delay_seconds=args.delay,
        limit=args.limit,
    )
    try:
        summary = run_enrichment(config)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Enrichment failed: {error}", file=sys.stderr)
        return 1

    print(
        "Wrote enrichment checkpoint: "
        f"{config.checkpoint_path} | success={summary['success_count']} "
        f"failures={summary['failure_count']} skipped={summary['skipped_success_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
