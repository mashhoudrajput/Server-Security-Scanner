"""FastAPI application for Server Security Scanner."""

import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.report import generate_pdf_report
from app.scanner import run_scan

app = FastAPI(title="NGI Security Scanner", version="1.0.0")

# In-memory store for scan jobs (use Redis/DB in production)
scan_jobs: dict[str, dict[str, Any]] = {}
REPORTS_DIR = Path(__file__).parent.parent / "reports"


class ServerInput(BaseModel):
    host: str
    user: str = "ubuntu"
    key_base64: str


class ScanRequest(BaseModel):
    servers: list[ServerInput]
    auto_mode: bool = True
    tests: list[str] | None = None
    urls: list[str] | None = None
    subnet: str | None = None
    openvas_config: dict | None = None


class ReportRequest(BaseModel):
    job_id: str


def _run_scan_task(job_id: str, req: ScanRequest):
    """Background task to run scan."""
    try:
        servers = [s.model_dump() for s in req.servers]
        for s in servers:
            s["name"] = s.get("host", "unknown")
        results = run_scan(
            servers=servers,
            tests=[],
            urls=None,
            subnet=None,
            openvas_config=None,
            progress_callback=lambda p: _update_progress(job_id, p),
            auto_mode=req.auto_mode,
        )
        scan_jobs[job_id] = results
    except Exception as e:
        scan_jobs[job_id] = {
            "job_id": job_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def _update_progress(job_id: str, progress: int):
    if job_id in scan_jobs and isinstance(scan_jobs[job_id], dict):
        scan_jobs[job_id]["progress"] = progress


@app.post("/api/scan")
def start_scan(req: ScanRequest):
    """Start a new security scan. Returns job_id for polling."""
    if not req.servers:
        raise HTTPException(400, "At least one server required")

    job_id = str(uuid.uuid4())

    scan_jobs[job_id] = {"job_id": job_id, "status": "running", "progress": 0}

    thread = threading.Thread(target=_run_scan_task, args=(job_id, req))
    thread.daemon = True
    thread.start()

    return {"job_id": job_id}


@app.get("/api/scan/{job_id}/status")
def get_scan_status(job_id: str):
    """Poll scan progress and results."""
    if job_id not in scan_jobs:
        raise HTTPException(404, "Job not found")
    return scan_jobs[job_id]


@app.post("/api/report/generate")
def generate_report(req: ReportRequest):
    """Generate PDF report from completed scan."""
    if req.job_id not in scan_jobs:
        raise HTTPException(404, "Job not found")
    data = scan_jobs[req.job_id]
    if data.get("status") not in ("completed", "error"):
        raise HTTPException(400, "Scan not yet completed")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"security_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = REPORTS_DIR / filename

    try:
        generate_pdf_report(data, str(filepath))
        return {"filename": filename}
    except Exception as e:
        raise HTTPException(500, f"Report generation failed: {str(e)}")


@app.get("/api/report/download/{filename}")
def download_report(filename: str):
    """Download generated PDF report."""
    if ".." in filename or "/" in filename:
        raise HTTPException(400, "Invalid filename")
    filepath = REPORTS_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "Report not found")
    return FileResponse(filepath, filename=filename, media_type="application/pdf")


# Serve static files (GUI)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def serve_gui():
    """Serve the main GUI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Server Security Scanner API", "docs": "/docs"}
