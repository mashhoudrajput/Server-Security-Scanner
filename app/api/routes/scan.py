"""Scan API routes."""

from fastapi import APIRouter, HTTPException

from app.api.schemas import ScanRequest
from app.scanner import get_tool_availability
from app.services.scan_service import scan_service

router = APIRouter()


@router.post("", response_model=dict)
def start_scan(request: ScanRequest) -> dict:
    """Start a new security scan. Returns job_id for polling."""
    if not request.servers:
        raise HTTPException(400, "At least one server required")

    servers = [s.model_dump() for s in request.servers]
    job_id = scan_service.start_scan(
        servers=servers,
        auto_mode=request.auto_mode,
        tests=request.tests,
        urls=request.urls,
        subnet=request.subnet,
        openvas_config=request.openvas_config,
        scan_profile=request.scan_profile,
        target_types=request.target_types,
    )
    return {"job_id": job_id}


@router.get("/{job_id}/status", response_model=dict)
def get_scan_status(job_id: str) -> dict:
    """Poll scan progress and results."""
    data = scan_service.get_status(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    return data


@router.get("/tools", response_model=dict)
def get_tools_status() -> dict:
    """Return availability status of external scan tools."""
    return {"tools": get_tool_availability()}
