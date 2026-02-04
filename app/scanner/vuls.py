"""Vuls CVE scanner integration."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .executor import SSHExecutor


def run_vuls(
    servers: list[dict], key_data: bytes, work_dir: str
) -> dict[str, Any]:
    """
    Run Vuls scan. Requires vuls binary and CVE DB.
    servers: [{host, user, name?}]
    Returns results per server or error if vuls not available.
    """
    try:
        subprocess.run(["vuls", "version"], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {"status": "n/a", "message": "Vuls not installed or CVE DB not initialized"}

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pem", delete=False) as f:
        f.write(key_data)
        key_path = f.name

    try:
        config_path = Path(work_dir) / "vuls_config.toml"
        config = _build_vuls_config(servers, key_path)
        config_path.write_text(config)

        result = subprocess.run(
            ["vuls", "scan", "-config", str(config_path)],
            capture_output=True,
            timeout=600,
            cwd=work_dir,
        )

        report_path = Path(work_dir) / "results"
        if report_path.exists():
            json_files = list(report_path.glob("*.json"))
            if json_files:
                with open(json_files[0]) as jf:
                    data = json.load(jf)
                return {"status": "info", "data": data, "scanned": True}
        return {"status": "info", "message": "Vuls scan completed", "stdout": result.stdout.decode()[:500] if result.stdout else ""}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try:
            os.unlink(key_path)
        except OSError:
            pass


def _build_vuls_config(servers: list[dict], key_path: str) -> str:
    lines = ['[default]\nscanMode = ["fast"]\n']
    for i, s in enumerate(servers):
        host = s.get("host", "")
        user = s.get("user", "root")
        name = "".join(c if c.isalnum() or c in "-_" else "_" for c in (s.get("name") or f"server{i}"))
        if not name:
            name = f"server{i}"
        lines.append(f'[servers.{name}]\nhost = "{host}"\nuser = "{user}"\nkeyPath = "{key_path}"\n')
    return "\n".join(lines)
