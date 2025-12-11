# Voice Agent Docker Container
# Based on LiveKit Agents deployment best practices
FROM python:3.12-slim

# Keeps Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Create a non-privileged user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Install build dependencies for native extensions
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Silero VAD model (doesn't need config)
RUN python -c "from livekit.plugins import silero; silero.VAD.load()"

# Copy application code
COPY agent/ ./agent/

# Change ownership to non-privileged user
RUN chown -R appuser:appuser /app

# Switch to non-privileged user
USER appuser

# Run the agent in production mode
CMD ["python", "-m", "agent.main", "start"]
