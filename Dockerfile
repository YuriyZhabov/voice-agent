# Voice Agent Docker Container
FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent/ ./agent/

# Expose health check port
EXPOSE 8081

# Run the agent
CMD ["python", "-m", "agent.main", "start"]
