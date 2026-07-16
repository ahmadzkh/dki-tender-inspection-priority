"""
Tests for TASK-BE-003: System endpoints (health and meta).
"""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_ready() -> None:
    """Health endpoint should return 200 and indicate readiness when artifacts are loaded."""
    with TestClient(app) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "ok"
        assert data["data"]["process_alive"] is True
        assert data["data"]["artifact_ready"] is True
        assert data["meta"]["model_version"] != "unknown"


def test_health_endpoint_not_ready() -> None:
    """Health endpoint should return 503 when app.state.store is missing."""
    with TestClient(app) as client:
        # Simulate artifact load failure or unreadiness
        client.app.state.store = None
        response = client.get("/api/v1/health")
        assert response.status_code == 503
        data = response.json()
        assert data["data"]["status"] == "error"
        assert data["data"]["process_alive"] is True
        assert data["data"]["artifact_ready"] is False
        assert data.get("meta") is None


def test_meta_endpoint_success() -> None:
    """Meta endpoint should return project metadata without exposing local paths."""
    with TestClient(app) as client:
        response = client.get("/api/v1/meta")
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]

        assert payload["project_name"] == "dki-tender-inspection-priority"
        assert payload["schema_version"] == 1
        assert "model_version" in payload
        assert "generated_at" in payload
        assert payload["artifact_count"] > 0
        assert payload["total_records"] == 1276
        assert payload["annual_source_row_count"] == 1284
        assert payload["merged_row_count"] == 1279
        assert payload["canonical_record_count"] == 1277
        assert payload["eligible_record_count"] == 1276
        assert payload["missing_supplier_row_count"] == 5
        assert payload["multi_provider_package_count"] == 1
        assert payload["enrichment_success_count"] == 1277
        assert payload["enrichment_coverage_pct"] == 100.0
        assert payload["dataset_version"] == data["meta"]["dataset_version"]

        # Ensure no local machine paths are leaked in the stringified response
        response_text = response.text
        assert "C:\\" not in response_text
        assert "/home/" not in response_text
        assert "backend\\" not in response_text
