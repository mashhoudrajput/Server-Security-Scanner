"""Scan API routes."""

from fastapi import APIRouter, HTTPException

from app.api.schemas import ScanRequest
from app.services.scan_service import scan_service

router = APIRouter()


@router.post("", response_model=dict)
def start_scan(request: ScanRequest) -> dict:
    """Start a new security scan. Returns job_id for polling."""
    if not request.servers:
        raise HTTPException(400, "At least one server required")

    servers = [s.model_dump() for s in request.servers]
    job_id = scan_service.start_scan(servers, auto_mode=request.auto_mode)
    return {"job_id": job_id}


@router.get("/{job_id}/status", response_model=dict)
def get_scan_status(job_id: str) -> dict:
    """Poll scan progress and results."""
    data = scan_service.get_status(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    return data
