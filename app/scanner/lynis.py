"""Lynis security audit check."""

from typing import Any

from .executor import SSHExecutor


def run_lynis(executor: SSHExecutor) -> dict[str, Any]:
    """Run Lynis audit on remote server. Returns parsed results or N/A if not installed."""
    r = executor.run(
        "lynis audit system --quick 2>/dev/null || lynis audit system 2>/dev/null || echo 'LYNIS_NOT_INSTALLED'",
        timeout=300,
    )
    out = r.get("stdout", "")
    if "LYNIS_NOT_INSTALLED" in out or not out.strip():
        return {"status": "n/a", "message": "Lynis not installed on server"}

    result = {"status": "info", "hardening_index": None, "warnings": [], "suggestions": []}

    for line in out.split("\n"):
        line = line.strip()
        if "hardening_index=" in line:
            try:
                result["hardening_index"] = int(line.split("=")[-1].strip())
            except (ValueError, IndexError):
                pass
        elif "[warning]" in line.lower():
            result["warnings"].append(line.replace("[warning]", "").strip()[:200])
        elif "[suggestion]" in line.lower():
            result["suggestions"].append(line.replace("[suggestion]", "").strip()[:200])

    result["warnings"] = result["warnings"][:10]
    result["suggestions"] = result["suggestions"][:10]
    result["raw_preview"] = out[:1500]
    return result
