import { useEffect, useRef } from "react";
import { api } from "../services/api";

interface ReportDownloadProps {
  filename: string | null;
  error: string | null;
  isScanning: boolean;
}

export function ReportDownload({
  filename,
  error,
  isScanning,
}: ReportDownloadProps) {
  const sectionRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (filename && sectionRef.current) {
      sectionRef.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [filename]);

  const getPlaceholderText = () => {
    if (isScanning) return "Scan in progress...";
    if (error) return `Report generation failed. ${error}`;
    if (filename) return "Report ready.";
    return "Report will be generated automatically when scan completes.";
  };

  return (
    <section className="card report-section" ref={sectionRef}>
      <h2>Report</h2>
      <div className="hint">{getPlaceholderText()}</div>
      {filename && (
        <div className="download-container">
          <a
            href={api.getReportDownloadUrl(filename)}
            download={filename}
            className="btn btn-success download-btn"
          >
            Download PDF Report
          </a>
        </div>
      )}
    </section>
  );
}
