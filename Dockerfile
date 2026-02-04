FROM python:3.11-slim

WORKDIR /app

# Enable non-free for nikto, then install WeasyPrint + Nikto + ZMap
RUN sed -i 's/Components: main/Components: main non-free/' /etc/apt/sources.list.d/debian.sources

# WeasyPrint + Nikto + ZMap + Nmap + curl/unzip for Nuclei
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    zmap \
    nikto \
    nmap \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Nuclei vulnerability scanner
RUN curl -sL "https://github.com/projectdiscovery/nuclei/releases/download/v3.6.2/nuclei_3.6.2_linux_amd64.zip" -o /tmp/nuclei.zip \
    && unzip -o /tmp/nuclei.zip -d /usr/local/bin \
    && rm /tmp/nuclei.zip \
    && nuclei -update-templates 2>/dev/null || true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY reports/ ./reports/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
