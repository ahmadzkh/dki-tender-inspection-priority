"""
Tests for TASK-BE-006: Package detail endpoint.
"""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_get_package_detail_success() -> None:
    """Should return complete details for an existing package."""
    with TestClient(app) as client:
        # Get a package ID from the ranking list
        res = client.get("/api/v1/rankings?size=1")
        pkg_id = res.json()["data"]["items"][0]["package_id"]

        response = client.get(f"/api/v1/packages/{pkg_id}")
        assert response.status_code == 200
        data = response.json()

        # Check disclaimer
        assert "disclaimer" in data["meta"]
        assert "fraud" in data["meta"]["disclaimer"].lower()

        payload = data["data"]
        assert payload["package_id"] == pkg_id

        # Check structure
        assert "source" in payload
        assert "enrichment" in payload
        assert "features" in payload
        assert "score" in payload
        assert "explanation" in payload

        # Check source
        assert "package_name" in payload["source"]
        assert "contract_value" in payload["source"]

        # Check score
        assert payload["score"]["anomaly_rank"] >= 1
        assert 0.0 <= payload["score"]["anomaly_score"] <= 1.0


def test_get_package_detail_not_found() -> None:
    """Should return 404 for unknown package ID."""
    with TestClient(app) as client:
        response = client.get("/api/v1/packages/999999999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
