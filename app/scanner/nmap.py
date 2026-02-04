"""Nmap port and service scanner."""

import subprocess
from typing import Any


def run_nmap(hosts: list[str], ports: str = "22,80,443,8080") -> dict[str, Any]:
    """
    Run Nmap against list of hosts for port/service detection.
    Requires nmap binary on scan machine.
    Uses -sT (TCP connect) for speed; -sV adds service version but is slower.
    """
    try:
        subprocess.run(["nmap", "--version"], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {"status": "n/a", "message": "Nmap not installed", "results": []}

    results = []
    port_list = ",".join(p.strip() for p in ports.split(",") if p.strip().isdigit()) or "22,80,443"

    for host in hosts:
        host = host.strip()
        if not host:
            continue
        try:
            r = subprocess.run(
                ["nmap", "-sT", "-sV", "-T4", "-p", port_list, host, "-oG", "-"],
                capture_output=True,
                timeout=300,
            )
            out = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
            err = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""
            results.append({
                "host": host,
                "output": out or err,
                "success": r.returncode == 0,
                "raw": out[:5000],
            })
        except subprocess.TimeoutExpired:
            results.append({"host": host, "output": "Scan timed out", "success": False, "raw": ""})
        except Exception as e:
            results.append({"host": host, "output": str(e), "success": False, "raw": ""})

    return {"status": "info", "results": results, "ports": port_list}
