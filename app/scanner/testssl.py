"""SSL/TLS scanner wrapper using testssl.sh."""

import subprocess
from typing import Any


def run_testssl(hosts: list[str]) -> dict[str, Any]:
    """Run testssl.sh for HTTPS targets derived from hosts."""
    try:
        subprocess.run(["testssl.sh", "--version"], capture_output=True, check=True, timeout=8)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {"status": "n/a", "message": "testssl.sh not installed", "results": []}

    results = []
    for host in hosts:
        host = host.strip()
        if not host:
            continue
        target = f"{host}:443"
        try:
            proc = subprocess.run(
                ["testssl.sh", "--warnings", "off", "--color", "0", "--fast", target],
                capture_output=True,
                timeout=360,
            )
            out = proc.stdout.decode("utf-8", errors="replace")
            err = proc.stderr.decode("utf-8", errors="replace")
            raw = (out + "\n" + err).strip()
            results.append(
                {
                    "host": host,
                    "output": raw[:3000] if raw else "No output",
                    "success": proc.returncode in (0, 3),
                }
            )
        except subprocess.TimeoutExpired:
            results.append({"host": host, "output": "testssl scan timed out", "success": False})
        except Exception as exc:
            results.append({"host": host, "output": str(exc), "success": False})

    return {
        "status": "info",
        "message": f"SSL/TLS checks finished for {len(results)} host(s)",
        "results": results,
    }
