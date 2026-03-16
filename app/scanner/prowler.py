"""Cloud security posture scanner wrapper using Prowler."""

import subprocess
from typing import Any


def run_prowler() -> dict[str, Any]:
    """
    Run Prowler for cloud posture checks.
    Requires cloud credentials to be configured in environment.
    """
    command = ["prowler"]
    try:
        subprocess.run(command + ["--version"], capture_output=True, check=True, timeout=8)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        command = ["python3", "-m", "prowler"]
        try:
            subprocess.run(command + ["--version"], capture_output=True, check=True, timeout=8)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return {"status": "n/a", "message": "Prowler not installed", "results": []}

    try:
        proc = subprocess.run(
            command + ["aws", "-M", "json-ocsf", "--quiet"],
            capture_output=True,
            timeout=900,
        )
        out = proc.stdout.decode("utf-8", errors="replace")
        err = proc.stderr.decode("utf-8", errors="replace")
        raw = (out + "\n" + err).strip()
        lines = [line for line in raw.splitlines() if line.strip()]
        return {
            "status": "info",
            "message": "Cloud posture scan complete",
            "results": lines[:50],
            "raw_preview": "\n".join(lines[:30]) if lines else "No output",
        }
    except subprocess.TimeoutExpired:
        return {"status": "warn", "message": "Prowler scan timed out", "results": []}
    except Exception as exc:
        return {"status": "warn", "message": str(exc), "results": []}
