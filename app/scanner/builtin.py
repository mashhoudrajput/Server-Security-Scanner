"""Built-in security checks run via SSH on each server."""

from typing import Any

from .executor import SSHExecutor

CHECKS = {
    "ssh_config": {
        "command": "sshd -T 2>/dev/null || true",
        "timeout": 10,
        "parse": lambda r: _parse_ssh_config(r),
    },
    "firewall": {
        "command": "ufw status 2>/dev/null || iptables -L -n 2>/dev/null || echo 'No firewall found'",
        "timeout": 10,
        "parse": lambda r: _parse_firewall(r),
    },
    "fail2ban": {
        "command": "fail2ban-client status 2>/dev/null || echo 'fail2ban not installed'",
        "timeout": 10,
        "parse": lambda r: _parse_fail2ban(r),
    },
    "updates": {
        "command": "apt list --upgradable 2>/dev/null | tail -n +2 || (yum check-update 2>/dev/null | tail -n +2 || echo '')",
        "timeout": 60,
        "parse": lambda r: _parse_updates(r),
    },
    "open_ports": {
        "command": "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null || echo 'N/A'",
        "timeout": 15,
        "parse": lambda r: _parse_open_ports(r),
    },
    "disk_usage": {
        "command": "df -h 2>/dev/null | grep -E '^/dev|^Filesystem'",
        "timeout": 10,
        "parse": lambda r: _parse_disk(r),
    },
    "last_login": {
        "command": "last -n 5 2>/dev/null || echo 'N/A'",
        "timeout": 10,
        "parse": lambda r: {"raw": r.get("stdout", "")[:500]},
    },
}


def _parse_ssh_config(r: dict) -> dict:
    out = r.get("stdout", "")
    status = "pass"
    findings = []
    fixes = []
    if "permitrootlogin yes" in out.lower():
        status = "fail"
        findings.append("PermitRootLogin is yes")
        fixes.append("Set PermitRootLogin no in /etc/ssh/sshd_config")
    elif "permitrootlogin" in out.lower():
        findings.append("PermitRootLogin configured")
    if "passwordauthentication yes" in out.lower():
        status = "fail" if status != "fail" else status
        findings.append("PasswordAuthentication is yes")
        fixes.append("Set PasswordAuthentication no in /etc/ssh/sshd_config")
    return {"status": status, "findings": findings, "fixes": fixes, "raw_preview": out[:500]}


def _parse_firewall(r: dict) -> dict:
    out = r.get("stdout", "").lower()
    if "inactive" in out or "disabled" in out:
        return {"status": "warn", "message": "Firewall inactive or disabled", "fixes": ["Enable UFW: sudo ufw enable", "Configure default policy: sudo ufw default deny incoming"]}
    if "active" in out or "status: active" in out:
        return {"status": "pass", "message": "Firewall active"}
    return {"status": "info", "message": "Firewall status unknown", "fixes": ["Install UFW: sudo apt install ufw", "Enable: sudo ufw enable"], "raw_preview": out[:500]}


def _parse_fail2ban(r: dict) -> dict:
    out = r.get("stdout", "")
    if "not installed" in out.lower():
        return {"status": "warn", "message": "Fail2ban not installed", "fixes": ["Install: sudo apt install fail2ban", "Enable: sudo systemctl enable fail2ban"]}
    if "Status" in out:
        return {"status": "pass", "message": "Fail2ban running", "raw_preview": out[:300]}
    return {"status": "info", "raw_preview": out[:200]}


def _parse_updates(r: dict) -> dict:
    out = r.get("stdout", "").strip()
    packages = []
    for line in out.split("\n"):
        line = line.strip()
        if not line or "Listing" in line:
            continue
        # apt format: package/arch version repo
        pkg = line.split("/")[0].strip() if "/" in line else line.split()[0] if line.split() else ""
        if pkg:
            packages.append(pkg)
    count = len(packages)
    status = "warn" if count > 0 else "pass"
    fixes = ["Run: sudo apt update && sudo apt upgrade -y"] if count > 0 else []
    return {
        "status": status,
        "pending_count": count,
        "message": f"{count} updates pending",
        "packages": packages,
        "raw": out[:5000],
        "fixes": fixes,
    }


def _parse_open_ports(r: dict) -> dict:
    out = r.get("stdout", "")
    lines = [l.strip() for l in out.split("\n") if l.strip()]
    fixes = ["Review open ports and close unnecessary services", "Use firewall to restrict access to required ports only"]
    return {"status": "info", "ports": lines, "raw": out, "fixes": fixes}


def _parse_disk(r: dict) -> dict:
    out = r.get("stdout", "")
    status = "pass"
    findings = []
    for line in out.split("\n"):
        parts = line.split()
        if len(parts) >= 5:
            try:
                pct = int(parts[4].replace("%", ""))
                if pct >= 90:
                    status = "fail"
                    findings.append(f"{parts[5] if len(parts) > 5 else '?'}: {pct}% full")
                elif pct >= 80:
                    status = "warn" if status != "fail" else status
                    findings.append(f"{parts[5] if len(parts) > 5 else '?'}: {pct}% full")
            except (ValueError, IndexError):
                pass
    fixes = []
    if status == "fail":
        fixes.append("Free disk space or expand volume")
    elif status == "warn":
        fixes.append("Monitor disk usage and plan cleanup")
    return {"status": status, "findings": findings or ["OK"], "fixes": fixes, "raw_preview": out[:500]}


def run_builtin_checks(
    executor: SSHExecutor, tests: list[str]
) -> dict[str, Any]:
    """Run selected built-in checks and return results."""
    results = {}
    for name in tests:
        if name not in CHECKS:
            continue
        cfg = CHECKS[name]
        r = executor.run(cfg["command"], timeout=cfg["timeout"])
        if r.get("error"):
            results[name] = {"status": "error", "error": r["error"]}
        else:
            results[name] = cfg["parse"](r)
            results[name]["success"] = r.get("success", False)
    return results
