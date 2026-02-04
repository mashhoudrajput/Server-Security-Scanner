"""Report download service."""

from pathlib import Path

from app.core.config import REPORTS_DIR


class ReportService:
    """Handles report file operations."""

    @staticmethod
    def get_report_path(filename: str) -> Path:
        """Get safe path for report file."""
        if ".." in filename or "/" in filename:
            raise ValueError("Invalid filename")
        return REPORTS_DIR / filename
