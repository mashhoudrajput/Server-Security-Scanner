"""Container security scanner wrapper using Trivy."""

import subprocess
from typing import Any


def run_trivy(hosts: list[str]) -> dict[str, Any]:
    """
    Run Trivy in config mode for local/containerized assets.
    Host list is kept for reporting context.
    """
    try:
        subprocess.run(["trivy", "--version"], capture_output=True, check=True, timeout=8)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {"status": "n/a", "message": "Trivy not installed", "results": []}

    target = "."
    try:
        proc = subprocess.run(
            ["trivy", "config", "--severity", "CRITICAL,HIGH,MEDIUM", "--no-progress", target],
            capture_output=True,
            timeout=300,
        )
        out = proc.stdout.decode("utf-8", errors="replace")
        err = proc.stderr.decode("utf-8", errors="replace")
        raw = (out + "\n" + err).strip()
        return {
            "status": "info",
            "message": "Container/config scan complete",
            "targets": hosts,
            "raw_preview": raw[:4000] if raw else "No output",
            "results": [line for line in raw.splitlines() if line.strip()][:60],
        }
    except subprocess.TimeoutExpired:
        return {"status": "warn", "message": "Trivy scan timed out", "results": []}
    except Exception as exc:
        return {"status": "warn", "message": str(exc), "results": []}
