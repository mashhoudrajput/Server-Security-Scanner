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

    html_content = template.render(
        servers=servers,
        network_scans=network_scans,
        timestamp=timestamp,
        server_count=len(servers),
        error=error,
    )

    html = HTML(string=html_content)
    html.write_pdf(output_path)
