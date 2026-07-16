"""
Main API router.
"""

from fastapi import APIRouter

from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.evaluation import router as evaluation_router
from backend.app.api.v1.export import router as export_router
from backend.app.api.v1.packages import router as packages_router
from backend.app.api.v1.ranking import router as ranking_router
from backend.app.api.v1.system import router as system_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system_router, tags=["system"])
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(ranking_router, prefix="/rankings", tags=["rankings"])
api_router.include_router(packages_router, prefix="/packages", tags=["packages"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
api_router.include_router(evaluation_router, prefix="/evaluation", tags=["evaluation"])
