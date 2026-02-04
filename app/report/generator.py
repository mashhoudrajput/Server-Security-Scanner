"""PDF report generator using WeasyPrint and Jinja2."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


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
    )

    html = HTML(string=html_content)
    html.write_pdf(output_path)
