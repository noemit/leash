# Ollama Browser Wrapper - Docker Image
# ========== ==============================
# For local machine development (Mac/Linux/Windows)
# NOT for Raspberry Pi deployment

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server/ ./server/
COPY web/ ./web/
COPY config/ ./config/

# Expose port (wrapper service only)
EXPOSE 8080

# Default command
CMD ["python", "server/api.py"]
