"""
Tests for TASK-BE-008: Security and hardening.
"""

from fastapi.testclient import TestClient

from backend.app.api.deps import get_artifact_store
from backend.app.main import app


def test_security_headers_present() -> None:
    """All responses should include security headers."""
    with TestClient(app) as client:
        response = client.get("/api/v1/system/health")

        headers = response.headers
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

        assert "Strict-Transport-Security" in headers
        assert "max-age=" in headers["Strict-Transport-Security"]

        assert "X-XSS-Protection" in headers
        assert headers["X-XSS-Protection"] == "1; mode=block"


def test_global_exception_handler_hides_details() -> None:
    """A generic 500 should be returned on unhandled exceptions without leaking stack trace."""

    def override_get_artifact_store():
        raise RuntimeError("Secret DB error")

    app.dependency_overrides[get_artifact_store] = override_get_artifact_store

    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/v1/meta")
            assert response.status_code == 500

            data = response.json()
            assert "detail" in data
            assert data["detail"] == "An internal server error occurred. Please try again later."
            assert "Secret DB error" not in response.text
    finally:
        app.dependency_overrides.clear()
