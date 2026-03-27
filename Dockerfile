FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system utilities needed for building packages
# GCC/G++ are optionally needed by some python dependencies compiling wheels
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies (will include spacy, presidio, prometheus-client, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Download Spacy model
RUN python -m spacy download en_core_web_lg

# Copy application code
COPY . .

# Ensure upload/output/quarantine directories exist inside container
RUN mkdir -p uploads output quarantine

# Expose FastAPI port
EXPOSE 8001

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
