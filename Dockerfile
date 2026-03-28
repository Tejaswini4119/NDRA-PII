FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Runtime defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system utilities needed for building packages
# GCC/G++ are optionally needed by some python dependencies compiling wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies (will include spacy, presidio, prometheus-client, etc.)
RUN pip install --upgrade pip && pip install -r requirements.txt

# Download Spacy model
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY . .

# Ensure runtime directories exist inside container
RUN mkdir -p uploads output quarantine artifacts audit

# Expose FastAPI port
EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8001/ || exit 1

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
