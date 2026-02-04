"""Scan orchestration service."""

import threading
import uuid
from datetime import datetime
from typing import Any

from app.core.config import REPORTS_DIR
from app.report import generate_pdf_report
from app.scanner import run_scan


class ScanService:
    """Manages scan jobs and report generation."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}

    def start_scan(self, servers: list[dict], auto_mode: bool = True) -> str:
        """Start a new scan. Returns job_id."""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {"job_id": job_id, "status": "running", "progress": 0}

        thread = threading.Thread(
            target=self._run_scan_task,
            args=(job_id, servers, auto_mode),
        )
        thread.daemon = True
        thread.start()

        return job_id

    def _run_scan_task(
        self,
        job_id: str,
        servers: list[dict],
        auto_mode: bool,
    ) -> None:
        """Background task to execute scan."""
        try:
            for s in servers:
                s["name"] = s.get("name") or s.get("host", "unknown")
            results = run_scan(
                servers=servers,
                tests=[],
                urls=None,
                subnet=None,
                openvas_config=None,
                progress_callback=lambda p: self._update_progress(job_id, p),
                auto_mode=auto_mode,
            )
            self._jobs[job_id] = results
        except Exception as e:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _update_progress(self, job_id: str, progress: int) -> None:
        """Update job progress."""
        if job_id in self._jobs and isinstance(self._jobs[job_id], dict):
            self._jobs[job_id]["progress"] = progress

    def get_status(self, job_id: str) -> dict[str, Any] | None:
        """Get scan status by job_id."""
        return self._jobs.get(job_id)

    def generate_report(self, job_id: str) -> str:
        """Generate PDF report. Returns filename."""
        data = self._jobs.get(job_id)
        if not data:
            raise ValueError("Job not found")
        if data.get("status") not in ("completed", "error"):
            raise ValueError("Scan not yet completed")

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"security_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = REPORTS_DIR / filename

        generate_pdf_report(data, str(filepath))
        return filename


# Singleton instance shared across routes
scan_service = ScanService()
