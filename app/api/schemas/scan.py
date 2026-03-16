"""Scan-related Pydantic schemas."""

from typing import Literal

from pydantic import BaseModel


class ServerInput(BaseModel):
    """Input for a single server to scan."""

    host: str
    host_name: str | None = None
    user: str = "ubuntu"
    key_base64: str


class ScanRequest(BaseModel):
    """Request body for starting a scan."""

    servers: list[ServerInput]
    auto_mode: bool = True
    scan_profile: Literal["regulatory", "advanced"] = "regulatory"
    target_types: list[
        Literal["host", "network", "web", "api", "cloud", "container", "compliance"]
    ] = ["host", "network", "web", "compliance"]
    tests: list[str] | None = None
    urls: list[str] | None = None
    subnet: str | None = None
    openvas_config: dict | None = None


class ReportRequest(BaseModel):
    """Request body for generating a report."""

    job_id: str
