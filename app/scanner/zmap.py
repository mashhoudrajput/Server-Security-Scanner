"""ZMap subnet/port scanner."""

import subprocess
from typing import Any


def run_zmap(subnet: str, ports: str = "22,80,443") -> dict[str, Any]:
    """
    Run ZMap to discover responsive hosts on subnet.
    Requires zmap binary (often needs root for raw sockets).
    """
    try:
        subprocess.run(["zmap", "--version"], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {"status": "n/a", "message": "ZMap not installed or insufficient privileges"}

    results = {}
    for port in ports.split(","):
        port = port.strip()
        if not port.isdigit():
            continue
        try:
            r = subprocess.run(
                ["zmap", "-p", port, subnet, "-o", "-"],
                capture_output=True,
                timeout=120,
            )
            out = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
            ips = [ip.strip() for ip in out.split("\n") if ip.strip()]
            results[port] = ips[:100]
        except subprocess.TimeoutExpired:
            results[port] = ["Scan timed out"]
        except Exception as e:
            results[port] = [str(e)]

    return {"status": "info", "subnet": subnet, "ports": results}
