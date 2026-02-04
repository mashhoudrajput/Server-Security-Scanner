"""Nuclei template-based vulnerability scanner."""

import subprocess
import tempfile
from pathlib import Path
from typing import Any


def run_nuclei(urls: list[str], severity: str = "critical,high,medium") -> dict[str, Any]:
    """
    Run Nuclei against list of URLs.
    Requires nuclei binary on scan machine.
    """
    try:
        subprocess.run(["nuclei", "-version"], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {"status": "n/a", "message": "Nuclei not installed", "results": []}

    results = []
    valid_urls = [u.strip() for u in urls if u.strip() and u.startswith(("http://", "https://"))]
    if not valid_urls:
        return {"status": "info", "message": "No valid URLs to scan", "results": []}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("\n".join(valid_urls))
        urls_file = f.name

    try:
        r = subprocess.run(
            [
                "nuclei",
                "-l", urls_file,
                "-severity", severity,
                "-silent",
                "-no-color",
            ],
            capture_output=True,
            timeout=600,
        )
        out = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
        err = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""
        raw = (out + "\n" + err).strip()
        findings = [line.strip() for line in raw.split("\n") if line.strip()] if raw else []
    except subprocess.TimeoutExpired:
        findings = ["Scan timed out"]
    except Exception as e:
        findings = [str(e)]
    finally:
        Path(urls_file).unlink(missing_ok=True)

    return {
        "status": "info",
        "message": f"{len(findings)} finding(s)" if findings else "No findings",
        "results": findings[:50],
        "raw_preview": "\n".join(findings[:30]),
    }
