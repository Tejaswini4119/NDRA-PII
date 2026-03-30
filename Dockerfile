FROM prom/prometheus:latest AS prometheus-bin

FROM python:3.10-slim-bookworm

# Set working directory
WORKDIR /app

# Runtime defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=20

# Copy requirements file
COPY requirements.txt .

# Install dependencies (will include spacy, presidio, prometheus-client, etc.)
RUN set -eux; \
        for i in 1 2 3 4 5; do \
            pip install --retries 20 --timeout 120 -r requirements.txt && break; \
            echo "pip install failed (attempt ${i}/5), retrying..."; \
            if [ "$i" -eq 5 ]; then exit 1; fi; \
            sleep $((i * 10)); \
        done

# Download Spacy model
RUN set -eux; \
        for i in 1 2 3 4 5; do \
            python -m spacy download en_core_web_lg && break; \
            echo "spaCy model download failed (attempt ${i}/5), retrying..."; \
            if [ "$i" -eq 5 ]; then exit 1; fi; \
            sleep $((i * 10)); \
        done

# Copy application code
COPY . .

# Copy Prometheus binary from official image so one container can run
# API + metrics scraper for native UI observability.
COPY --from=prometheus-bin /bin/prometheus /usr/local/bin/prometheus

# Ensure runtime directories exist inside container
RUN mkdir -p uploads output quarantine artifacts audit

# Startup script launches Prometheus in background and API in foreground.
COPY docker/start.sh /app/docker/start.sh
RUN chmod +x /app/docker/start.sh

# Expose FastAPI port
EXPOSE 8001
EXPOSE 9090

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/', timeout=3)"

# Run the app
CMD ["/app/docker/start.sh"]
