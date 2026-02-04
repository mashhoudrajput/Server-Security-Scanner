const API_BASE = "/api";

export const api = {
  async startScan(servers: Array<{ host: string; host_name?: string; user: string; key_base64: string }>) {
    const res = await fetch(`${API_BASE}/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ servers, auto_mode: true }),
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

  getReportDownloadUrl(filename: string): string {
    return `${API_BASE}/report/download/${filename}`;
  },
};
