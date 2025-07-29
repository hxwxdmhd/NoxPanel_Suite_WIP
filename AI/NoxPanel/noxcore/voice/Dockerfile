# 🐳 VOXTRAL MICROSERVICE DOCKER CONFIGURATION
# =============================================

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    portaudio19-dev \
    python3-pyaudio \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements-voxtral.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-voxtral.txt

# Copy application code
COPY voxtral_service.py .
COPY voice_api.py .
COPY __init__.py .

# Create necessary directories
RUN mkdir -p /app/audio_temp /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV VOXTRAL_HOST=0.0.0.0
ENV VOXTRAL_PORT=8080
ENV VOXTRAL_WORKERS=4
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Run the service
CMD ["python", "-m", "uvicorn", "voxtral_service:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
