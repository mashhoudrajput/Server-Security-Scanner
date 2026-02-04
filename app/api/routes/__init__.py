"""API route modules."""

from fastapi import APIRouter

from app.api.routes.report import router as report_router
from app.api.routes.scan import router as scan_router

api_router = APIRouter(prefix="/api", tags=["api"])
api_router.include_router(scan_router, prefix="/scan", tags=["scan"])
api_router.include_router(report_router, prefix="/report", tags=["report"])
