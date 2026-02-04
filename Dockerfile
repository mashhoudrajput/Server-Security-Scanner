# Stage 1: Build React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/ ./
RUN npm install && npm run build

# Stage 2: Python backend + frontend
FROM python:3.11-slim

WORKDIR /app

# Enable non-free for nikto
RUN sed -i 's/Components: main/Components: main non-free/' /etc/apt/sources.list.d/debian.sources

# WeasyPrint + fonts + security tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fontconfig \
    fonts-liberation \
    fonts-dejavu-core \
    zmap \
    nikto \
    nmap \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Nuclei
RUN curl -sL "https://github.com/projectdiscovery/nuclei/releases/download/v3.6.2/nuclei_3.6.2_linux_amd64.zip" -o /tmp/nuclei.zip \
    && unzip -o /tmp/nuclei.zip -d /usr/local/bin \
    && rm /tmp/nuclei.zip \
    && nuclei -update-templates 2>/dev/null || true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY reports/ ./reports/

# Copy React build from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
