"""
Integration, OpenAPI, and performance checks for TASK-BE-009.
"""

from __future__ import annotations

import csv
import io
import time
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app

EXPECTED_OPENAPI_PATHS = {
    "/api/v1/health": {"get"},
    "/api/v1/meta": {"get"},
    "/api/v1/summary": {"get"},
    "/api/v1/filters": {"get"},
    "/api/v1/rankings": {"get"},
    "/api/v1/packages/{package_id}": {"get"},
    "/api/v1/export.csv": {"get"},
    "/api/v1/evaluation": {"get"},
}


def _assert_api_envelope(payload: dict) -> None:
    assert set(payload) == {"data", "meta", "error"}
    assert payload["data"] is not None
    assert payload["error"] is None
    assert payload["meta"]["model_version"] != "unknown"
    assert "inspection priority" in payload["meta"]["score_direction"]
    disclaimer = payload["meta"]["disclaimer"].lower()
    assert "fraud" in disclaimer
    assert "not" in disclaimer or "tidak" in disclaimer


def test_p1_endpoints_should_return_safe_versioned_contracts() -> None:
    with TestClient(app) as client:
        for path in [
            "/api/v1/health",
            "/api/v1/meta",
            "/api/v1/summary",
            "/api/v1/filters",
            "/api/v1/rankings?top_n=20&size=20",
            "/api/v1/evaluation",
        ]:
            response = client.get(path)
            assert response.status_code == 200, path
            _assert_api_envelope(response.json())

        ranking_payload = client.get("/api/v1/rankings?top_n=1&size=1").json()
        package_id = ranking_payload["data"]["items"][0]["package_id"]

        detail_response = client.get(f"/api/v1/packages/{package_id}")
        assert detail_response.status_code == 200
        detail_payload = detail_response.json()
        _assert_api_envelope(detail_payload)
        assert detail_payload["data"]["package_id"] == package_id
        assert detail_payload["data"]["score"]["anomaly_rank"] >= 1

        export_response = client.get("/api/v1/export.csv?year=2026")
        assert export_response.status_code == 200
        assert export_response.headers["content-type"].startswith("text/csv")
        assert export_response.text.startswith("# DISCLAIMER:")
        rows = list(csv.DictReader(io.StringIO("\n".join(export_response.text.splitlines()[1:]))))
        assert rows
        assert {row["year"] for row in rows} == {"2026"}


def test_invalid_api_inputs_should_return_4xx_without_stack_trace() -> None:
    with TestClient(app) as client:
        for path in [
            "/api/v1/rankings?size=0",
            "/api/v1/rankings?page=0",
            "/api/v1/packages/UNKNOWN_PACKAGE",
        ]:
            response = client.get(path)
            assert 400 <= response.status_code < 500, path
            assert "Traceback" not in response.text
            assert "C:\\" not in response.text


def test_openapi_should_match_backend_contract_snapshot() -> None:
    snapshot_path = Path("reports/backend/openapi_paths.json")
    assert snapshot_path.exists()

    with TestClient(app) as client:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()

    paths = schema["paths"]
    for path, methods in EXPECTED_OPENAPI_PATHS.items():
        assert path in paths
        assert methods.issubset(set(paths[path]))

    schema_text = response.text
    assert "C:\\" not in schema_text
    assert "/home/" not in schema_text
    assert "password" not in schema_text.lower()


def test_summary_and_ranking_p95_should_stay_under_one_second() -> None:
    durations: list[float] = []
    with TestClient(app) as client:
        for _ in range(3):
            assert client.get("/api/v1/summary").status_code == 200
            assert client.get("/api/v1/rankings?top_n=20&size=20").status_code == 200

        for _ in range(20):
            start = time.perf_counter()
            summary = client.get("/api/v1/summary")
            ranking = client.get("/api/v1/rankings?top_n=20&size=20")
            durations.append(time.perf_counter() - start)
            assert summary.status_code == 200
            assert ranking.status_code == 200

    p95 = sorted(durations)[int(len(durations) * 0.95) - 1]
    assert p95 < 1.0
