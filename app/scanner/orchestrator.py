"""Orchestrates security scans across servers and network tools."""

import base64
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .builtin import run_builtin_checks
from .executor import SSHExecutor
from .lynis import run_lynis
from .nikto import run_nikto
from .openvas import run_openvas
from .vuls import run_vuls
from .zmap import run_zmap

BUILTIN_TESTS = {"ssh_config", "firewall", "fail2ban", "updates", "open_ports", "disk_usage", "last_login"}
ALL_TESTS = list(BUILTIN_TESTS) + ["lynis", "vuls", "nikto", "zmap"]


def _derive_subnet(host: str) -> str | None:
    """Derive /24 subnet from host IP for ZMap."""
    import ipaddress
    try:
        ip = ipaddress.ip_address(host)
        if ip.version == 4:
            return str(ipaddress.ip_network(f"{host}/24", strict=False))
    except ValueError:
        pass
    return None


def _derive_urls(servers: list[dict]) -> list[str]:
    """Auto-derive HTTP/HTTPS URLs from server hosts for Nikto."""
    urls = []
    seen = set()
    for s in servers:
        host = s.get("host", "").strip()
        if host and host not in seen:
            seen.add(host)
            urls.append(f"http://{host}")
            urls.append(f"https://{host}")
    return urls


def run_scan(
    servers: list[dict],
    tests: list[str] | None = None,
    urls: list[str] | None = None,
    subnet: str | None = None,
    openvas_config: dict | None = None,
    progress_callback: Optional[Callable[[int], None]] = None,
    auto_mode: bool = False,
) -> dict[str, Any]:
    """
    Run security scans. If auto_mode or tests empty, runs ALL tests and auto-derives URLs/subnet.
    """
    if auto_mode or not tests:
        tests = ALL_TESTS
        urls = urls or _derive_urls(servers)
        if not subnet and servers:
            subnet = _derive_subnet(servers[0].get("host", ""))

    results = {
        "job_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "servers": {},
        "network_scans": {},
        "status": "running",
        "progress": 0,
    }

    total_steps = 0
    done_steps = 0

    # Count steps for progress
    server_tests = [t for t in tests if t in BUILTIN_TESTS or t == "lynis"]
    total_steps += len(servers) * (len(server_tests) + (1 if "lynis" in tests else 0))
    if "vuls" in tests:
        total_steps += 1
    if "nikto" in tests and urls:
        total_steps += 1
    if "zmap" in tests and subnet:
        total_steps += 1
    if "openvas" in tests and openvas_config:
        total_steps += 1
    total_steps = max(total_steps, 1)

    def update_progress():
        nonlocal done_steps
        done_steps += 1
        results["progress"] = int(100 * done_steps / total_steps)
        if progress_callback:
            progress_callback(results["progress"])

    # Per-server scans
    for server in servers:
        host = server.get("host", "")
        user = server.get("user", "ubuntu")
        name = server.get("name", host)
        key_b64 = server.get("key_base64", "")
        if not host or not key_b64:
            continue

        key_data = base64.b64decode(key_b64)
        results["servers"][name] = {"host": host, "user": user, "checks": {}, "lynis": None, "reachable": False}

        executor = SSHExecutor(host=host, user=user, key_data=key_data)
        try:
            ok, err = executor.connect()
            if not ok:
                results["servers"][name]["error"] = err or "SSH connection failed"
                update_progress()
                continue

            results["servers"][name]["reachable"] = True

            # Built-in checks
            builtin_tests = [t for t in tests if t in BUILTIN_TESTS]
            if builtin_tests:
                results["servers"][name]["checks"] = run_builtin_checks(executor, builtin_tests)
                update_progress()

            # Lynis
            if "lynis" in tests:
                results["servers"][name]["lynis"] = run_lynis(executor)
                update_progress()
        finally:
            executor.close()

    # Vuls (all servers) - use first server's key
    if "vuls" in tests and servers:
        key_b64 = next((s.get("key_base64") for s in servers if s.get("key_base64")), "")
        if key_b64:
            key_data = base64.b64decode(key_b64)
            vuls_servers = [{"host": s["host"], "user": s.get("user", "ubuntu"), "name": s.get("name", s["host"])} for s in servers if s.get("host") and s.get("key_base64")]
            if vuls_servers:
                with tempfile.TemporaryDirectory() as tmp:
                    results["network_scans"]["vuls"] = run_vuls(vuls_servers, key_data, tmp)
        update_progress()

    # Nikto
    if "nikto" in tests and urls:
        results["network_scans"]["nikto"] = run_nikto(urls)
        update_progress()

    # ZMap
    if "zmap" in tests and subnet:
        results["network_scans"]["zmap"] = run_zmap(subnet)
        update_progress()

    # OpenVAS
    if "openvas" in tests and openvas_config:
        results["network_scans"]["openvas"] = run_openvas(
            host=openvas_config.get("host", ""),
            api_key=openvas_config.get("api_key", ""),
            targets=openvas_config.get("targets", []),
        )
        update_progress()

    results["status"] = "completed"
    results["progress"] = 100
    return results
