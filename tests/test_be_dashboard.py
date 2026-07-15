"""
Tests for TASK-BE-004: Dashboard summary and filter options.
"""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_summary_endpoint_success() -> None:
    """Summary endpoint should return correct aggregated statistics."""
    with TestClient(app) as client:
        response = client.get("/api/v1/summary")
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]

        assert payload["total_packages"] == 1276
        assert payload["unique_suppliers"] > 0
        assert payload["unique_work_units"] > 0

        # Check packages_by_year
        assert "2024" in payload["packages_by_year"]
        assert "2025" in payload["packages_by_year"]
        assert "2026 (Snapshot)" in payload["packages_by_year"]

        # Check score distribution
        assert len(payload["score_distribution"]) > 0
        assert sum(bin["count"] for bin in payload["score_distribution"]) == 1276

        # Check meta
        assert data["meta"]["model_version"] != "unknown"
        assert "score_direction" in data["meta"]


def test_filters_endpoint_success() -> None:
    """Filters endpoint should return sorted unique options."""
    with TestClient(app) as client:
        response = client.get("/api/v1/filters")
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]

        assert 2026 in payload["years"]
        assert 2024 in payload["years"]
        assert len(payload["years"]) == 3

        assert len(payload["procurement_methods"]) > 0
        assert len(payload["procurement_types"]) > 0
        assert len(payload["work_units"]) > 0

        # Ensure it's sorted
        assert payload["years"] == sorted(payload["years"], reverse=True)
        assert payload["procurement_methods"] == sorted(payload["procurement_methods"])
