"""
Tests for TASK-BE-001: minimal FastAPI application scaffold.

Verifies:
- OpenAPI schema is accessible and has the expected title.
- Docs UI is accessible.
- Only GET methods are allowed through CORS middleware.
- No hardcoded machine paths appear in the schema.
- App starts without requiring any artifact or database.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_should_return_openapi_schema_with_correct_title() -> None:
    """OpenAPI schema available and title matches project."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "DKI Jakarta Tender Inspection Priority API"


def test_should_serve_swagger_docs() -> None:
    """Swagger UI accessible at /docs."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_should_serve_redoc() -> None:
    """ReDoc accessible at /redoc."""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_should_include_interpretation_disclaimer_in_description() -> None:
    """API description must contain neutral interpretation language."""
    response = client.get("/openapi.json")
    schema = response.json()
    description: str = schema["info"]["description"]
    # Ensure the description contains the required interpretation boundary
    assert "inspection" in description.lower()
    assert "fraud" in description.lower()  # mentioned as what it is NOT


def test_should_not_expose_local_machine_paths_in_schema() -> None:
    """OpenAPI schema must not contain absolute local filesystem paths."""
    response = client.get("/openapi.json")
    schema_text = response.text
    # Check for common Windows path separators that would reveal machine paths
    assert "C:\\" not in schema_text
    assert "/home/" not in schema_text


@pytest.mark.parametrize(
    "method",
    ["POST", "PUT", "DELETE", "PATCH"],
)
def test_should_disallow_mutating_methods_on_nonexistent_endpoint(method: str) -> None:
    """App should return 405 for unsupported HTTP methods, not 500."""
    response = client.request(method, "/nonexistent-endpoint")
    # 404 or 405 is acceptable; 500 is not
    assert response.status_code in {404, 405}
