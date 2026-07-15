"""
FastAPI dependency injection functions.
"""

from fastapi import Request

from backend.app.services.artifact_store import ArtifactStore


def get_artifact_store(request: Request) -> ArtifactStore:
    """Retrieve the globally loaded ArtifactStore from app state."""
    store = getattr(request.app.state, "store", None)
    if not store:
        raise RuntimeError("ArtifactStore is not initialized in app state.")
    return store
