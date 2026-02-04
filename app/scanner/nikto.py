"""Nikto web vulnerability scanner."""

import subprocess
from typing import Any


def run_nikto(urls: list[str]) -> dict[str, Any]:
    """
    Run Nikto against list of URLs.
    Requires nikto binary on scan machine.
    """
    try:
        subprocess.run(["nikto", "-Version"], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {"status": "n/a", "message": "Nikto not installed", "results": []}

    results = []
    for url in urls:
        url = url.strip()
        if not url or not url.startswith(("http://", "https://")):
            continue
        try:
            r = subprocess.run(
                ["nikto", "-h", url, "-Format", "txt"],
                capture_output=True,
                timeout=300,
            )
            out = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
            results.append({"url": url, "output": out[:3000], "success": r.returncode == 0})
        except subprocess.TimeoutExpired:
            results.append({"url": url, "output": "Scan timed out", "success": False})
        except Exception as e:
            results.append({"url": url, "output": str(e), "success": False})

    return {"status": "info", "results": results}
