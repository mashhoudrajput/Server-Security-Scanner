"""Orchestrates security scans across servers and network tools."""

import base64
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from typing import Any, Callable, Optional

from .builtin import run_builtin_checks
from .executor import SSHExecutor
from .lynis import run_lynis
from .nikto import run_nikto
from .nmap import run_nmap
from .nuclei import run_nuclei
from .openvas import run_openvas
from .prowler import run_prowler
from .testssl import run_testssl
from .trivy import run_trivy
from .vuls import run_vuls
from .zmap import run_zmap

BUILTIN_TESTS = {
    "ssh_config", "firewall", "fail2ban", "updates", "open_ports", "disk_usage", "last_login",
    "clamav", "rkhunter", "chkrootkit", "auditd", "apparmor", "unattended_upgrades", "sudo_users", "ssl_cert",
}
ALL_TESTS = list(BUILTIN_TESTS) + ["lynis", "vuls", "nikto", "zmap", "nmap", "nuclei"]
ALL_TESTS += ["openvas", "testssl", "trivy", "prowler"]


def get_tool_availability() -> dict[str, dict[str, str | bool]]:
    """Return install availability for supported external tools."""
    checks = {
        "nmap": ["nmap", "--version"],
        "nikto": ["nikto", "-Version"],
        "nuclei": ["nuclei", "-version"],
        "zmap": ["zmap", "--version"],
        "vuls": ["vuls", "version"],
        "testssl": ["testssl.sh", "--version"],
        "trivy": ["trivy", "--version"],
    }

    availability: dict[str, dict[str, str | bool]] = {}
    for name, command in checks.items():
        binary = command[0]
        if not shutil.which(binary):
            availability[name] = {"available": False, "status": "not installed"}
            continue
        try:
            subprocess.run(command, capture_output=True, check=False, timeout=6)
            availability[name] = {"available": True, "status": "available"}
        except Exception:
            availability[name] = {"available": False, "status": "failed check"}

    openvas_available = False
    openvas_status = "python-gvm missing"
    try:
        from gvm.protocols.http.openvasd import OpenvasdHttpAPIv1  # noqa: F401

        host_cfg = bool(os.getenv("OPENVAS_HOST"))
        api_key_cfg = bool(os.getenv("OPENVAS_API_KEY"))
        openvas_available = host_cfg and api_key_cfg
        if openvas_available:
            openvas_status = "available (external server configured)"
        else:
            openvas_status = "python-gvm ready; set OPENVAS_HOST and OPENVAS_API_KEY"
    except Exception:
        openvas_available = False
    availability["openvas"] = {
        "available": openvas_available,
        "status": openvas_status,
    }

    prowler_available = False
    if shutil.which("prowler"):
        prowler_available = True
    else:
        try:
            subprocess.run(
                ["python3", "-m", "prowler", "--version"],
                capture_output=True,
                check=False,
                timeout=6,
            )
            prowler_available = True
        except Exception:
            prowler_available = False
    availability["prowler"] = {
        "available": prowler_available,
        "status": "available" if prowler_available else "not installed",
    }

    return availability


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


def _default_tests_for_profile(
    scan_profile: str,
    target_types: list[str] | None,
) -> list[str]:
    """Choose default tests for regulatory or advanced scans."""
    regulatory = {"nmap", "nikto", "nuclei", "lynis", "testssl", "trivy", "prowler", "vuls"}
    advanced_extra = {"zmap", "openvas"}

    by_target = {
        "host": BUILTIN_TESTS | {"lynis", "vuls"},
        "network": {"nmap", "zmap", "openvas"},
        "web": {"nikto", "nuclei", "testssl"},
        "api": {"nuclei"},
        "cloud": {"prowler"},
        "container": {"trivy"},
        "compliance": {"lynis", "testssl", "trivy", "prowler", "vuls"},
    }

    selected_targets = target_types or ["host", "network", "web", "compliance"]
    selected_tests: set[str] = set()
    for target in selected_targets:
        selected_tests |= by_target.get(target, set())

    selected_tests |= regulatory
    if scan_profile == "advanced":
        selected_tests |= advanced_extra

    return [t for t in ALL_TESTS if t in selected_tests or t in BUILTIN_TESTS]


def run_scan(
    servers: list[dict],
    tests: list[str] | None = None,
    urls: list[str] | None = None,
    subnet: str | None = None,
    openvas_config: dict | None = None,
    progress_callback: Optional[Callable[[int], None]] = None,
    auto_mode: bool = False,
    scan_profile: str = "regulatory",
    target_types: list[str] | None = None,
) -> dict[str, Any]:
    """
    Run security scans. If auto_mode or tests empty, runs ALL tests and auto-derives URLs/subnet.
    """
    if auto_mode or not tests:
        tests = _default_tests_for_profile(scan_profile=scan_profile, target_types=target_types)
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

    server_tests = [t for t in tests if t in BUILTIN_TESTS]
    total_steps += len(servers) * len(server_tests)
    if "lynis" in tests:
        total_steps += len(servers)
    if "vuls" in tests:
        total_steps += 1
    if "nikto" in tests and urls:
        total_steps += 1
    if "zmap" in tests and subnet:
        total_steps += 1
    if "nmap" in tests and servers:
        total_steps += 1
    if "nuclei" in tests and urls:
        total_steps += 1
    if "testssl" in tests and servers:
        total_steps += 1
    if "trivy" in tests:
        total_steps += 1
    if "prowler" in tests:
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

            builtin_tests = [t for t in tests if t in BUILTIN_TESTS]
            if builtin_tests:
                results["servers"][name]["checks"] = run_builtin_checks(executor, builtin_tests)
                update_progress()

            if "lynis" in tests:
                results["servers"][name]["lynis"] = run_lynis(executor)
                update_progress()
        finally:
            executor.close()

    if "vuls" in tests and servers:
        key_b64 = next((s.get("key_base64") for s in servers if s.get("key_base64")), "")
        if key_b64:
            key_data = base64.b64decode(key_b64)
            vuls_servers = [{"host": s["host"], "user": s.get("user", "ubuntu"), "name": s.get("name", s["host"])} for s in servers if s.get("host") and s.get("key_base64")]
            if vuls_servers:
                with tempfile.TemporaryDirectory() as tmp:
                    results["network_scans"]["vuls"] = run_vuls(vuls_servers, key_data, tmp)
        update_progress()

    if "nikto" in tests and urls:
        results["network_scans"]["nikto"] = run_nikto(urls)
        update_progress()

    if "zmap" in tests and subnet:
        results["network_scans"]["zmap"] = run_zmap(subnet)
        update_progress()

    if "nmap" in tests and servers:
        hosts = [s.get("host", "").strip() for s in servers if s.get("host", "").strip()]
        if hosts:
            results["network_scans"]["nmap"] = run_nmap(hosts)
        update_progress()

    if "nuclei" in tests and urls:
        results["network_scans"]["nuclei"] = run_nuclei(urls)
        update_progress()

    if "testssl" in tests and servers:
        hosts = [s.get("host", "").strip() for s in servers if s.get("host", "").strip()]
        if hosts:
            results["network_scans"]["testssl"] = run_testssl(hosts)
        update_progress()

    if "trivy" in tests:
        hosts = [s.get("host", "").strip() for s in servers if s.get("host", "").strip()]
        results["network_scans"]["trivy"] = run_trivy(hosts)
        update_progress()

    if "prowler" in tests:
        results["network_scans"]["prowler"] = run_prowler()
        update_progress()

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
