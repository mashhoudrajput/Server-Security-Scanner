import { useState, useCallback, useEffect } from "react";
import { ServerForm } from "../components/ServerForm";
import { ProgressBar } from "../components/ProgressBar";
import { ScanResults } from "../components/ScanResults";
import { ReportDownload } from "../components/ReportDownload";
import { useScan } from "../hooks/useScan";
import { api } from "../services/api";
import type { ScanProfile, ServerInput, TargetType, ToolAvailability } from "../types/scan";

const INITIAL_SERVER: ServerInput = {
  host: "",
  hostName: undefined,
  user: "ubuntu",
  keyBase64: null,
};

export function ScanPage() {
  const [servers, setServers] = useState<ServerInput[]>([{ ...INITIAL_SERVER }]);
  const [scanProfile, setScanProfile] = useState<ScanProfile>("regulatory");
  const [targetTypes, setTargetTypes] = useState<TargetType[]>([
    "host",
    "network",
    "web",
    "compliance",
  ]);
  const [toolAvailability, setToolAvailability] = useState<ToolAvailability>({});
  const [toolStatusError, setToolStatusError] = useState<string | null>(null);
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
    const scanServers = validServers.map((s) => ({
      host: s.host.trim(),
      host_name: s.hostName?.trim() || undefined,
      user: s.user.trim() || "ubuntu",
      key_base64: s.keyBase64!,
    }));
    await startScan({
      servers: scanServers,
      scanProfile,
      targetTypes,
    });
  }, [scanProfile, startScan, targetTypes, validServers]);

  const toggleTargetType = useCallback((target: TargetType) => {
    setTargetTypes((prev) => {
      if (prev.includes(target)) {
        if (prev.length === 1) return prev;
        return prev.filter((t) => t !== target);
      }
      return [...prev, target];
    });
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .getToolsStatus()
      .then((data) => {
        if (!cancelled) {
          setToolAvailability(data.tools);
          setToolStatusError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setToolStatusError(err instanceof Error ? err.message : "Failed to load tool status");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <ServerForm
        servers={servers}
        onServersChange={setServers}
        onAddServer={handleAddServer}
        onRemoveServer={handleRemoveServer}
      />

      <section className="card actions">
        <div className="scan-options">
          <div className="scan-option-group">
            <label htmlFor="scanProfile">Scan profile</label>
            <select
              id="scanProfile"
              className="scan-select"
              value={scanProfile}
              onChange={(e) => setScanProfile(e.target.value as ScanProfile)}
              disabled={isScanning}
            >
              <option value="regulatory">Regulatory</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>

          <div className="scan-option-group">
            <span>Target types</span>
            <div className="target-grid">
              {(
                [
                  "host",
                  "network",
                  "web",
                  "api",
                  "cloud",
                  "container",
                  "compliance",
                ] as TargetType[]
              ).map((target) => (
                <label key={target} className="target-chip">
                  <input
                    type="checkbox"
                    checked={targetTypes.includes(target)}
                    onChange={() => toggleTargetType(target)}
                    disabled={isScanning}
                  />
                  <span>{target}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="scan-option-group">
            <span>Tool availability</span>
            {toolStatusError && <div className="hint">{toolStatusError}</div>}
            {!toolStatusError && (
              <div className="tool-grid">
                {Object.entries(toolAvailability).map(([tool, info]) => (
                  <div key={tool} className="tool-chip">
                    <span className="tool-name">{tool}</span>
                    <span className={`tool-badge ${info.available ? "ok" : "missing"}`}>
                      {info.available ? "Available" : "Missing"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

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
