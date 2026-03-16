import type { ScanProfile, TargetType, ToolAvailability } from "../types/scan";
const API_BASE = "/api";

export const api = {
  async startScan(input: {
    servers: Array<{ host: string; host_name?: string; user: string; key_base64: string }>;
    scanProfile: ScanProfile;
    targetTypes: TargetType[];
  }) {
    const res = await fetch(`${API_BASE}/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        servers: input.servers,
        auto_mode: true,
        scan_profile: input.scanProfile,
        target_types: input.targetTypes,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to start scan");
    return data as { job_id: string };
  },

  async getScanStatus(jobId: string) {
    const res = await fetch(`${API_BASE}/scan/${jobId}/status`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to get status");
    return data;
  },

  async generateReport(jobId: string) {
    const res = await fetch(`${API_BASE}/report/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Report generation failed");
    return data as { filename: string };
  },

  async getToolsStatus() {
    const res = await fetch(`${API_BASE}/scan/tools`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to get tools status");
    return data as { tools: ToolAvailability };
  },

  getReportDownloadUrl(filename: string): string {
    return `${API_BASE}/report/download/${filename}`;
  },
};
