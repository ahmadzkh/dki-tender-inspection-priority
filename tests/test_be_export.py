"""
Tests for TASK-BE-007: CSV export endpoint.
"""

from fastapi.testclient import TestClient

from backend.app.main import app


def test_export_csv_default() -> None:
    """Should return full CSV without filters."""
    with TestClient(app) as client:
        response = client.get("/api/v1/export.csv")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/csv; charset=utf-8"

        content = response.text
        lines = content.strip().split("\n")

        # Check disclaimer
        assert lines[0].startswith("# DISCLAIMER:")

        # Check header
        assert "package_id,year,supplier_name" in lines[1]

        # Row count should be 1276 data rows + 1 disclaimer + 1 header
        assert len(lines) == 1276 + 2


def test_export_csv_with_filters() -> None:
    """Should respect filters for CSV export."""
    with TestClient(app) as client:
        response = client.get("/api/v1/export.csv?year=2024&procurement_method=Tender")
        assert response.status_code == 200
        content = response.text
        lines = content.strip().split("\n")

        import csv

        reader = csv.reader(lines)
        rows = list(reader)

        assert len(rows) > 2
        for cols in rows[2:]:
            # cols[1] is year, cols[4] is procurement_method
            assert cols[1] == "2024"
            assert cols[4] == "Tender"
