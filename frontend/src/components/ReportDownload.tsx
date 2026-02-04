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
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Download PDF Report
          </a>
        </div>
      )}
    </section>
  );
}
