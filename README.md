# Server Security Scanner

Web-based security scanner. Enter host, optional name, username, SSH key → click Scan → get PDF report.

## Requirements

- Docker
- Docker Compose

## Run

**Using docker-compose (recommended):**

```bash
docker compose up --build
```

**Using docker build and run:**

```bash
docker build -t server-security-scanner .
mkdir -p reports && chown 999:999 reports  # or chmod 777 reports
docker run -d --network host --cap-add NET_RAW -v $(pwd)/reports:/app/reports \
  --read-only --security-opt no-new-privileges:true \
  --tmpfs /tmp:noexec,nosuid,size=64m \
  server-security-scanner
```

Open http://localhost:8000

## Security

- **Non-root**: Runs as `appuser` (UID 999)
- **No SSH**: No openssh-server in container
- **Hardened**: Read-only root, no-new-privileges, minimal capabilities (NET_RAW only)
- **No shell**: `nologin` shell prevents interactive exec

## Usage

1. Add server: Host (IP), Name (optional display name), Username (default: ubuntu), SSH key (.pem)
2. Click **Start Full Scan**
3. Wait for completion
4. Download PDF report (auto-generated, luxury-styled)

## What It Scans

**On-target (via SSH):**
- SSH config, firewall, fail2ban, updates, open ports, disk usage, last logins
- ClamAV, rkhunter, chkrootkit (if installed on target)
- auditd, AppArmor, unattended-upgrades, sudo users, SSL cert
- Lynis (if installed on target)

**From scanner:**
- Nmap (port/service scan)
- Nikto (HTTP/HTTPS on host)
- Nuclei (template-based vulnerability scan)
- ZMap (subnet from host IP)
- Vuls (requires separate setup)

## Project Structure

```
├── app/                  # Backend (FastAPI)
│   ├── api/              # API routes & schemas
│   ├── core/              # Config
│   ├── report/            # PDF generation
│   ├── scanner/           # Security scan modules
│   └── services/          # Business logic
├── frontend/              # React (Vite + TypeScript)
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
├── reports/               # Generated PDFs
├── Dockerfile             # Single container (React + Python)
├── docker-compose.yml
└── requirements.txt
```

**Development:** Run `npm run dev` in `frontend/` for hot reload; backend at `http://localhost:8000`.
