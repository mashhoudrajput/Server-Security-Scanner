"""Scan-related Pydantic schemas."""

from pydantic import BaseModel


class ServerInput(BaseModel):
    """Input for a single server to scan."""

    host: str
    user: str = "ubuntu"
    key_base64: str


class ScanRequest(BaseModel):
    """Request body for starting a scan."""

    servers: list[ServerInput]
    auto_mode: bool = True
    tests: list[str] | None = None
    urls: list[str] | None = None
    subnet: str | None = None
    openvas_config: dict | None = None


class ReportRequest(BaseModel):
    """Request body for generating a report."""

    job_id: str
