"""
Tests for TASK-BE-005: Ranking endpoints.
"""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_ranking_endpoint_default() -> None:
    """Ranking endpoint should return default page 1, size 20, sorted by score desc."""
    with TestClient(app) as client:
        response = client.get("/api/v1/rankings")
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]

        assert len(payload["items"]) == 20
        assert payload["pagination"]["page"] == 1
        assert payload["pagination"]["size"] == 20
        assert payload["pagination"]["total_items"] == 1276

        # Check sorting by score desc
        scores = [item["anomaly_score"] for item in payload["items"]]
        assert scores == sorted(scores, reverse=True)


def test_ranking_endpoint_pagination() -> None:
    """Ranking endpoint should respect page and size parameters."""
    with TestClient(app) as client:
        response = client.get("/api/v1/rankings?page=2&size=5")
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]

        assert len(payload["items"]) == 5
        assert payload["pagination"]["page"] == 2
        assert payload["pagination"]["size"] == 5
        assert payload["pagination"]["has_previous"] is True
        assert payload["pagination"]["has_next"] is True


def test_ranking_endpoint_filters() -> None:
    """Ranking endpoint should apply filters correctly."""
    with TestClient(app) as client:
        # Filter by year and procurement method
        response = client.get("/api/v1/rankings?year=2024&procurement_method=Tender")
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]

        for item in payload["items"]:
            assert item["year"] == 2024
            assert item["procurement_method"] == "Tender"

        # The metadata should reflect filters
        assert data["meta"]["filters"]["year"] == 2024
        assert data["meta"]["filters"]["procurement_method"] == "Tender"


def test_ranking_endpoint_substring_filters() -> None:
    """Ranking endpoint should apply substring filters (supplier_name, work_unit) correctly."""
    with TestClient(app) as client:
        response = client.get("/api/v1/rankings?supplier_name=PT")
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]

        for item in payload["items"]:
            assert "pt" in item["supplier_name"].lower()


def test_ranking_endpoint_score_filters() -> None:
    """Ranking endpoint should filter by min_score and max_score."""
    with TestClient(app) as client:
        response = client.get("/api/v1/rankings?min_score=0.60&max_score=0.65")
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]

        for item in payload["items"]:
            assert 0.60 <= item["anomaly_score"] <= 0.65


def test_ranking_endpoint_top_n() -> None:
    """Ranking endpoint should limit results before pagination when top_n is used."""
    with TestClient(app) as client:
        response = client.get("/api/v1/rankings?top_n=50&size=10")
        assert response.status_code == 200
        data = response.json()
        payload = data["data"]

        assert payload["pagination"]["total_items"] == 50
        assert payload["pagination"]["total_pages"] == 5
        assert len(payload["items"]) == 10


def test_ranking_endpoint_invalid_query() -> None:
    """Ranking endpoint should return 422 for invalid query params."""
    with TestClient(app) as client:
        response = client.get("/api/v1/rankings?page=0")
        assert response.status_code == 422

        response = client.get("/api/v1/rankings?size=200")
        assert response.status_code == 422
