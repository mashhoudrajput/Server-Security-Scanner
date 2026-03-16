FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/ ./
RUN npm install && npm run build

FROM python:3.11-slim

WORKDIR /app

RUN sed -i 's/Components: main/Components: main non-free/' /etc/apt/sources.list.d/debian.sources

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
    git \
    ca-certificates \
    curl \
    unzip \
    bsdextrautils \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sL "https://github.com/projectdiscovery/nuclei/releases/download/v3.6.2/nuclei_3.6.2_linux_amd64.zip" -o /tmp/nuclei.zip \
    && unzip -o /tmp/nuclei.zip -d /usr/local/bin \
    && rm /tmp/nuclei.zip \
    && nuclei -update-templates 2>/dev/null || true

RUN git clone --depth 1 https://github.com/drwetter/testssl.sh.git /opt/testssl.sh \
    && ln -sf /opt/testssl.sh/testssl.sh /usr/local/bin/testssl.sh || true

RUN curl -sfL https://github.com/aquasecurity/trivy/releases/download/v0.69.3/trivy_0.69.3_Linux-64bit.tar.gz \
    -o /tmp/trivy.tar.gz \
    && tar -xzf /tmp/trivy.tar.gz -C /tmp \
    && mv /tmp/trivy /usr/local/bin/trivy \
    && chmod +x /usr/local/bin/trivy \
    && rm -f /tmp/trivy.tar.gz || true

RUN curl -sfL https://github.com/future-architect/vuls/releases/download/v0.38.6/future-vuls_0.38.6_linux_amd64.tar.gz \
    -o /tmp/vuls.tar.gz \
    && tar -xzf /tmp/vuls.tar.gz -C /tmp \
    && mv /tmp/future-vuls /usr/local/bin/vuls \
    && chmod +x /usr/local/bin/vuls \
    && rm -f /tmp/vuls.tar.gz || true

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 5 --default-timeout 120 -r requirements.txt

COPY app/ ./app/
COPY reports/ ./reports/

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
