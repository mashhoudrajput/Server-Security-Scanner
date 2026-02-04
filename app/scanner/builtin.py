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
    "clamav": {
        "command": "clamscan --version 2>/dev/null && clamscan -r /tmp --infected 2>/dev/null | tail -5 || echo 'CLAMAV_NOT_INSTALLED'",
        "timeout": 60,
        "parse": lambda r: _parse_clamav(r),
    },
    "rkhunter": {
        "command": "rkhunter --version 2>/dev/null && rkhunter -c --skip-keypress 2>/dev/null | tail -50 || echo 'RKHUNTER_NOT_INSTALLED'",
        "timeout": 120,
        "parse": lambda r: _parse_rkhunter(r),
    },
    "chkrootkit": {
        "command": "chkrootkit -V 2>/dev/null && chkrootkit 2>/dev/null | tail -30 || echo 'CHKROOTKIT_NOT_INSTALLED'",
        "timeout": 120,
        "parse": lambda r: _parse_chkrootkit(r),
    },
    "auditd": {
        "command": "systemctl is-active auditd 2>/dev/null; auditctl -s 2>/dev/null || echo 'AUDITD_NOT_AVAILABLE'",
        "timeout": 10,
        "parse": lambda r: _parse_auditd(r),
    },
    "apparmor": {
        "command": "aa-status 2>/dev/null || (cat /sys/module/apparmor/parameters/enabled 2>/dev/null || echo 'APPARMOR_NOT_AVAILABLE')",
        "timeout": 10,
        "parse": lambda r: _parse_apparmor(r),
    },
    "unattended_upgrades": {
        "command": "(dpkg -l unattended-upgrades 2>/dev/null | grep -q ^ii && cat /etc/apt/apt.conf.d/50unattended-upgrades 2>/dev/null) || echo 'UNATTENDED_UPGRADES_NOT_INSTALLED'",
        "timeout": 10,
        "parse": lambda r: _parse_unattended_upgrades(r),
    },
    "sudo_users": {
        "command": "getent group sudo 2>/dev/null || grep -E '^sudo:' /etc/group 2>/dev/null || echo 'N/A'",
        "timeout": 10,
        "parse": lambda r: _parse_sudo_users(r),
    },
    "ssl_cert": {
        "command": "timeout 5 openssl s_client -connect 127.0.0.1:443 -servername localhost 2>/dev/null | openssl x509 -noout -dates -subject 2>/dev/null || echo 'SSL_CERT_NOT_AVAILABLE'",
        "timeout": 15,
        "parse": lambda r: _parse_ssl_cert(r),
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


def _parse_clamav(r: dict) -> dict:
    out = r.get("stdout", "")
    if "CLAMAV_NOT_INSTALLED" in out or not out.strip():
        return {"status": "n/a", "message": "ClamAV not installed", "fixes": ["Install: sudo apt install clamav clamav-daemon", "Update: sudo freshclam"]}
    if "Infected files: 0" in out or "OK" in out:
        return {"status": "pass", "message": "ClamAV installed, quick scan OK", "raw_preview": out[:400]}
    if "Infected files:" in out and "Infected files: 0" not in out:
        return {"status": "fail", "message": "ClamAV found infected files", "raw_preview": out[:500], "fixes": ["Review infected files and remove malware"]}
    return {"status": "info", "message": "ClamAV installed", "raw_preview": out[:400]}


def _parse_rkhunter(r: dict) -> dict:
    out = r.get("stdout", "")
    if "RKHUNTER_NOT_INSTALLED" in out or "command not found" in out.lower():
        return {"status": "n/a", "message": "rkhunter not installed", "fixes": ["Install: sudo apt install rkhunter", "Update: sudo rkhunter --update"]}
    warnings = [l.strip() for l in out.split("\n") if "[ Warning ]" in l or "Warning" in l][:5]
    if warnings:
        return {"status": "warn", "message": "rkhunter found warnings", "findings": warnings, "raw_preview": out[:800], "fixes": ["Review: sudo rkhunter -c --skip-keypress"]}
    return {"status": "pass", "message": "rkhunter scan completed", "raw_preview": out[:500]}


def _parse_chkrootkit(r: dict) -> dict:
    out = r.get("stdout", "")
    if "CHKROOTKIT_NOT_INSTALLED" in out or "command not found" in out.lower():
        return {"status": "n/a", "message": "chkrootkit not installed", "fixes": ["Install: sudo apt install chkrootkit"]}
    if "INFECTED" in out or "Warning:" in out:
        return {"status": "fail", "message": "chkrootkit found potential issues", "raw_preview": out[:800], "fixes": ["Investigate reported files manually"]}
    return {"status": "pass", "message": "chkrootkit scan completed", "raw_preview": out[:500]}


def _parse_auditd(r: dict) -> dict:
    out = r.get("stdout", "")
    if "AUDITD_NOT_AVAILABLE" in out:
        return {"status": "n/a", "message": "auditd not available", "fixes": ["Install: sudo apt install auditd", "Enable: sudo systemctl enable auditd"]}
    if "inactive" in out.lower() or "failed" in out.lower():
        return {"status": "warn", "message": "auditd not active", "fixes": ["Enable: sudo systemctl enable auditd", "Start: sudo systemctl start auditd"]}
    return {"status": "pass", "message": "auditd active", "raw_preview": out[:300]}


def _parse_apparmor(r: dict) -> dict:
    out = r.get("stdout", "")
    if "APPARMOR_NOT_AVAILABLE" in out or "No such file" in out:
        return {"status": "n/a", "message": "AppArmor not available", "fixes": ["AppArmor is typically on Ubuntu; check kernel support"]}
    if "Y" in out or "enabled" in out.lower() or "profiles are loaded" in out:
        return {"status": "pass", "message": "AppArmor enabled", "raw_preview": out[:400]}
    return {"status": "info", "message": "AppArmor status", "raw_preview": out[:300]}


def _parse_unattended_upgrades(r: dict) -> dict:
    out = r.get("stdout", "")
    if "UNATTENDED_UPGRADES_NOT_INSTALLED" in out or not out.strip():
        return {"status": "n/a", "message": "unattended-upgrades not installed", "fixes": ["Install: sudo apt install unattended-upgrades", "Enable: sudo dpkg-reconfigure -plow unattended-upgrades"]}
    return {"status": "pass", "message": "unattended-upgrades configured", "raw_preview": out[:500]}


def _parse_sudo_users(r: dict) -> dict:
    out = r.get("stdout", "")
    if "N/A" in out or not out.strip():
        return {"status": "info", "message": "Could not list sudo group", "raw_preview": out[:200]}
    # Format: sudo:x:1000:user1,user2
    parts = out.split(":")
    if len(parts) >= 4 and parts[3].strip():
        users = parts[3].strip().split(",")
        return {"status": "info", "message": f"{len(users)} sudo user(s)", "users": users, "raw_preview": out[:300]}
    return {"status": "info", "message": "Sudo group empty or N/A", "raw_preview": out[:200]}


def _parse_ssl_cert(r: dict) -> dict:
    out = r.get("stdout", "")
    if "SSL_CERT_NOT_AVAILABLE" in out or not out.strip():
        return {"status": "n/a", "message": "No HTTPS on localhost:443 or openssl unavailable"}
    status = "info"
    fixes = []
    if "notAfter=" in out:
        # Check expiry - notAfter=Feb  4 12:00:00 2026 GMT
        import re
        m = re.search(r"notAfter=([^\n]+)", out)
        if m:
            return {"status": status, "message": "SSL cert found", "raw_preview": out[:400], "fixes": ["Monitor cert expiry and renew before expiration"]}
    return {"status": status, "message": "SSL cert info", "raw_preview": out[:400]}


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
