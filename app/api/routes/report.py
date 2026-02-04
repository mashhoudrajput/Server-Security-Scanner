"""Report API routes."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.api.schemas import ReportRequest
from app.services.report_service import ReportService
from app.services.scan_service import scan_service

router = APIRouter()


@router.post("/generate", response_model=dict)
def generate_report(request: ReportRequest) -> dict:
    """Generate PDF report from completed scan."""
    try:
        filename = scan_service.generate_report(request.job_id)
        return {"filename": filename}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(404, str(e))
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Report generation failed: {str(e)}")


@router.get("/download/{filename}")
def download_report(filename: str) -> FileResponse:
    """Download generated PDF report."""
    try:
        filepath = ReportService.get_report_path(filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not filepath.exists():
        raise HTTPException(404, "Report not found")

    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/pdf",
    )
