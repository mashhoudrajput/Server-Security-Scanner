"""PDF report generator using WeasyPrint and Jinja2."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


def _compute_compliance_summary(scan_data: dict) -> list[dict]:
    """Map scan outcomes to common control frameworks."""
    status_counts = {"pass": 0, "warn": 0, "fail": 0}

    for server in scan_data.get("servers", {}).values():
        for check_data in server.get("checks", {}).values():
            status = check_data.get("status", "info")
            if status in status_counts:
                status_counts[status] += 1

    for result in scan_data.get("network_scans", {}).values():
        status = result.get("status", "info")
        if status in status_counts:
            status_counts[status] += 1

    total = status_counts["pass"] + status_counts["warn"] + status_counts["fail"]
    if total == 0:
        return []

    pass_rate = round((status_counts["pass"] / total) * 100, 1)
    frameworks = [
        ("CIS Controls v8", "IG1/IG2 Baseline"),
        ("NIST 800-53", "RA/SI/CM"),
        ("ISO 27001:2022", "Annex A"),
        ("PCI-DSS 4.0", "Req 2, 6, 11"),
        ("SOC 2", "CC6/CC7"),
    ]

    summary = []
    for framework, focus in frameworks:
        summary.append(
            {
                "framework": framework,
                "focus": focus,
                "pass": status_counts["pass"],
                "warn": status_counts["warn"],
                "fail": status_counts["fail"],
                "score": pass_rate,
            }
        )

    return summary


def generate_pdf_report(scan_data: dict, output_path: str) -> None:
    """
    Generate a PDF report from scan results.
    scan_data: dict from run_scan (servers, network_scans, timestamp, etc.)
    output_path: path to write PDF file
    """
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("report.html.j2")

    servers = scan_data.get("servers", {})
    network_scans = scan_data.get("network_scans", {})
    timestamp = scan_data.get("timestamp", "Unknown")
    error = scan_data.get("error")
    compliance_summary = _compute_compliance_summary(scan_data)

    # Compute pass/warn/fail summary from all checks
    summary = {"pass": 0, "warn": 0, "fail": 0}
    if not error:
        for data in servers.values():
            for check_data in data.get("checks", {}).values():
                s = check_data.get("status", "info")
                if s == "pass":
                    summary["pass"] += 1
                elif s == "warn":
                    summary["warn"] += 1
                elif s == "fail":
                    summary["fail"] += 1

    html_content = template.render(
        servers=servers,
        network_scans=network_scans,
        timestamp=timestamp,
        server_count=len(servers),
        error=error,
        summary=summary,
        compliance_summary=compliance_summary,
    )

    html = HTML(string=html_content, base_url=str(template_dir))
    html.write_pdf(output_path)
