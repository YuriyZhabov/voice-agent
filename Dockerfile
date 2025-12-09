# Voice Agent Docker Container
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent/ ./agent/

# Expose health check port
EXPOSE 8081

# Run the agent (use 'dev' for development, 'start' for production)
CMD ["python", "-m", "agent.main", "start"]
