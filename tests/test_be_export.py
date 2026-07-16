"""
Tests for TASK-BE-007: CSV export endpoint.
"""

import csv
import io

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

        reader = csv.reader(lines)
        rows = list(reader)

        assert len(rows) > 2
        for cols in rows[2:]:
            # cols[1] is year, cols[4] is procurement_method
            assert cols[1] == "2024"
            assert cols[4] == "Tender"


def test_export_matches_filtered_top_n_ranking_record_for_record() -> None:
    query = "year=2024&procurement_method=Tender&top_n=10"
    with TestClient(app) as client:
        ranking = client.get(f"/api/v1/rankings?{query}&size=100").json()["data"]
        exported = client.get(f"/api/v1/export.csv?{query}")

    csv_body = "\n".join(exported.text.splitlines()[1:])
    rows = list(csv.DictReader(io.StringIO(csv_body)))
    expected = ranking["items"]
    assert len(rows) == ranking["pagination"]["total_items"] == len(expected)
    assert [row["package_id"] for row in rows] == [item["package_id"] for item in expected]
    assert [int(row["anomaly_rank"]) for row in rows] == [item["anomaly_rank"] for item in expected]
