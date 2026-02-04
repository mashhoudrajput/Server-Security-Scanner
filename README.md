# Server Security Scanner

Web-based security scanner. Enter host, username, SSH key → click Scan → get PDF report.

## Requirements

- Docker
- Docker Compose

## Run

**Using Docker Hub (quick start):**

```bash
docker pull mashhoud/server-security-scanner:latest
docker run -d --network host --cap-add NET_RAW -v $(pwd)/reports:/app/reports mashhoud/server-security-scanner:latest
```

**Using docker-compose (recommended):**

```bash
docker compose up --build
```

**Using docker build and run:**

```bash
docker build -t server-security-scanner .
docker run -d --network host --cap-add NET_RAW -v $(pwd)/reports:/app/reports server-security-scanner
```

Open http://localhost:8000

## Usage

1. Add server: Host (IP), Username (default: ubuntu), SSH key (.pem)
2. Click **Start Full Scan**
3. Wait for completion
4. Download PDF report (auto-generated)

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

## Project

```
├── app/           # FastAPI + scanner + report + static GUI
├── reports/       # Generated PDFs
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
