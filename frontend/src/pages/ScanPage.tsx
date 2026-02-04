import { useState, useCallback } from "react";
import { ServerForm } from "../components/ServerForm";
import { ProgressBar } from "../components/ProgressBar";
import { ScanResults } from "../components/ScanResults";
import { ReportDownload } from "../components/ReportDownload";
import { useScan } from "../hooks/useScan";
import type { ServerInput } from "../types/scan";

const INITIAL_SERVER: ServerInput = {
  host: "",
  user: "ubuntu",
  keyBase64: null,
};

export function ScanPage() {
  const [servers, setServers] = useState<ServerInput[]>([{ ...INITIAL_SERVER }]);
  const {
    status,
    isScanning,
    reportFilename,
    reportError,
    startScan,
  } = useScan();

  const validServers = servers.filter((s) => s.host.trim() && s.keyBase64);
  const canStartScan = validServers.length > 0 && !isScanning;

  const handleAddServer = useCallback(() => {
    setServers((prev) => [...prev, { ...INITIAL_SERVER }]);
  }, []);

  const handleRemoveServer = useCallback((index: number) => {
    setServers((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleStartScan = useCallback(async () => {
    const payload = validServers.map((s) => ({
      host: s.host.trim(),
      user: s.user.trim() || "ubuntu",
      key_base64: s.keyBase64!,
      host_name: s.hostName?.trim() || undefined,
    }));
    await startScan(payload);
  }, [validServers, startScan]);

  return (
    <>
      <ServerForm
        servers={servers}
        onServersChange={setServers}
        onAddServer={handleAddServer}
        onRemoveServer={handleRemoveServer}
      />

      <section className="card actions">
        <button
          type="button"
          className={`btn btn-primary btn-scan ${canStartScan ? "btn-scan-ready" : ""}`}
          onClick={handleStartScan}
          disabled={!canStartScan}
        >
          <span className="btn-text">Start Full Scan</span>
          <span className="btn-desc">Runs all security checks automatically</span>
        </button>
        <ProgressBar
          progress={status?.progress ?? 0}
          text={status?.progress === 100 ? "Complete" : `Scanning... ${status?.progress ?? 0}%`}
          isVisible={isScanning || (status?.progress === 100 && !!status)}
        />
      </section>

      <ScanResults status={status} />
      <ReportDownload
        filename={reportFilename}
        error={reportError}
        isScanning={isScanning}
      />
    </>
  );
}
