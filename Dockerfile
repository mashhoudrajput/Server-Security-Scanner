FROM python:3.11-slim

WORKDIR /app

# Enable non-free for nikto, then install WeasyPrint + Nikto + ZMap
RUN sed -i 's/Components: main/Components: main non-free/' /etc/apt/sources.list.d/debian.sources

# WeasyPrint + Nikto + ZMap
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    zmap \
    nikto \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY reports/ ./reports/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
