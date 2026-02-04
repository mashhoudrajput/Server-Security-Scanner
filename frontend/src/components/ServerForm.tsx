import type { ServerInput } from "../types/scan";

interface ServerFormProps {
  servers: ServerInput[];
  onServersChange: (servers: ServerInput[]) => void;
  onAddServer: () => void;
  onRemoveServer: (index: number) => void;
}

async function readFileAsBase64(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  bytes.forEach((b) => (binary += String.fromCharCode(b)));
  return btoa(binary);
}

export function ServerForm({
  servers,
  onServersChange,
  onAddServer,
  onRemoveServer,
}: ServerFormProps) {
  const handleHostChange = (index: number, host: string) => {
    const next = [...servers];
    next[index] = { ...next[index], host };
    onServersChange(next);
  };

  const handleUserChange = (index: number, user: string) => {
    const next = [...servers];
    next[index] = { ...next[index], user: user || "ubuntu" };
    onServersChange(next);
  };

  const handleKeyChange = async (index: number, file: File | null) => {
    const keyBase64 = file ? await readFileAsBase64(file) : null;
    const keyFileName = file?.name;
    const next = [...servers];
    next[index] = { ...next[index], keyBase64, keyFileName };
    onServersChange(next);
  };

  const handleHostNameChange = (index: number, hostName: string) => {
    const next = [...servers];
    next[index] = { ...next[index], hostName: hostName || undefined };
    onServersChange(next);
  };

  return (
    <section className="card scan-form">
      <h2>Add Server</h2>
      <div className="servers-header">
        <span>Host name <em>(optional)</em></span>
        <span>Host</span>
        <span>Username</span>
        <span>SSH Key</span>
        <span></span>
      </div>
      {servers.map((server, index) => (
        <div key={index} className="server-row">
          <input
            type="text"
            placeholder="e.g. Production Server"
            value={server.hostName ?? ""}
            onChange={(e) => handleHostNameChange(index, e.target.value)}
            className="host-name-input"
          />
          <input
            type="text"
            placeholder="IP or hostname"
            value={server.host}
            onChange={(e) => handleHostChange(index, e.target.value)}
          />
          <input
            type="text"
            placeholder="ubuntu"
            value={server.user}
            onChange={(e) => handleUserChange(index, e.target.value)}
          />
          <label className="file-label">
            <input
              type="file"
              className="file-input"
              accept=".pem,.key,*"
              onChange={(e) => handleKeyChange(index, e.target.files?.[0] ?? null)}
            />
            <span className="file-btn">
              {server.keyFileName ?? (server.keyBase64 ? "Key loaded" : "Choose file")}
            </span>
          </label>
          <button
            type="button"
            className="btn btn-danger"
            onClick={() => onRemoveServer(index)}
          >
            Remove
          </button>
        </div>
      ))}
      <button type="button" className="btn btn-secondary" onClick={onAddServer}>
        + Add Another Server
      </button>
    </section>
  );
}
