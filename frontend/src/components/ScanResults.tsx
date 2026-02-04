import type { ScanStatus } from "../types/scan";

interface ScanResultsProps {
  status: ScanStatus | null;
}

export function ScanResults({ status }: ScanResultsProps) {
  if (!status?.servers && !status?.network_scans) {
    return (
      <section className="card results-section">
        <h2>Results</h2>
        <div className="hint">
          Enter server details and click Start Full Scan.
        </div>
      </section>
    );
  }

  const servers = status.servers ?? {};
  const networkScans = status.network_scans ?? {};

  return (
    <section className="card results-section">
      <h2>Results</h2>
      {status.error && (
        <p className="status-fail">Error: {status.error}</p>
      )}
      {Object.entries(servers).map(([name, srv]) => (
        <div
          key={name}
          className={`result-server ${srv.reachable ? "reachable" : "unreachable"}`}
        >
          <h4>
            {name} ({srv.host}) — {srv.reachable ? "Reachable" : "Unreachable"}
          </h4>
          {srv.error && <p className="status-fail">{srv.error}</p>}
          {srv.checks &&
            Object.entries(srv.checks).map(([k, v]) => (
              <div key={k} className="result-check">
                <span>{k.replace(/_/g, " ")}</span>
                <span className={`status-${v.status}`}>
                  {v.status} {v.message ?? (v.findings?.[0] ?? "")}
                </span>
              </div>
            ))}
          {srv.lynis && srv.lynis.status !== "n/a" && (
            <div className="result-check">
              <span>Lynis</span>
              <span>Index: {srv.lynis.hardening_index ?? "N/A"}</span>
            </div>
          )}
        </div>
      ))}
      {Object.entries(networkScans).map(([tool, result]) => (
        <div key={tool} className="result-server">
          <h4>{tool.toUpperCase()}</h4>
          <p>{result.message ?? result.status ?? ""}</p>
        </div>
      ))}
    </section>
  );
}
