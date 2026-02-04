import { useState, useCallback } from "react";
import { api } from "../services/api";
import type { ScanStatus } from "../types/scan";

const POLL_INTERVAL_MS = 1500;

export function useScan() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<ScanStatus | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [reportFilename, setReportFilename] = useState<string | null>(null);
  const [reportError, setReportError] = useState<string | null>(null);

  const pollStatus = useCallback(async (id: string) => {
    const data = await api.getScanStatus(id);
    setStatus(data);

    if (data.status === "completed" || data.status === "error") {
      setIsScanning(false);
      try {
        const { filename } = await api.generateReport(id);
        setReportFilename(filename);
        setReportError(null);
      } catch (err) {
        setReportError(err instanceof Error ? err.message : "Report generation failed");
      }
      return;
    }

    setTimeout(() => pollStatus(id), POLL_INTERVAL_MS);
  }, []);

  const startScan = useCallback(
    async (servers: Array<{ host: string; user: string; key_base64: string; host_name?: string }>) => {
      setReportFilename(null);
      setReportError(null);
      setStatus(null);
      setIsScanning(true);

      const { job_id } = await api.startScan(servers);
      setJobId(job_id);
      pollStatus(job_id);
    },
    [pollStatus]
  );

  const reset = useCallback(() => {
    setJobId(null);
    setStatus(null);
    setIsScanning(false);
    setReportFilename(null);
    setReportError(null);
  }, []);

  return {
    jobId,
    status,
    isScanning,
    reportFilename,
    reportError,
    startScan,
    reset,
  };
}
