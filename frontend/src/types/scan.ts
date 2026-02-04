export interface ServerInput {
  host: string;
  user: string;
  keyBase64: string | null;
  keyFileName?: string;
}

export interface ScanStatus {
  job_id: string;
  status: "running" | "completed" | "error";
  progress: number;
  servers?: Record<string, ServerResult>;
  network_scans?: Record<string, NetworkScanResult>;
  error?: string;
  timestamp?: string;
}

export interface ServerResult {
  host: string;
  user: string;
  reachable: boolean;
  error?: string;
  checks?: Record<string, CheckResult>;
  lynis?: LynisResult;
}

export interface CheckResult {
  status: "pass" | "warn" | "fail" | "info" | "n/a";
  message?: string;
  findings?: string[];
}

export interface LynisResult {
  status: string;
  hardening_index?: number;
  warnings?: string[];
  suggestions?: string[];
}

export interface NetworkScanResult {
  status: string;
  message?: string;
}
