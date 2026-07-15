"""
Main API router.
"""

from fastapi import APIRouter

from backend.app.api.v1.system import router as system_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system_router, tags=["system"])
