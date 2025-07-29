FROM python:3.9-slim

# Set labels for better Docker Hub presentation
LABEL maintainer="HobeLab <contact@hobelab.dev>"
LABEL description="Heimnetz - ADHD-friendly network management tool with AI assistant"
LABEL version="2.0.0"
LABEL org.opencontainers.image.source="https://github.com/HobeLab-Projects/Heimnetz"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HEIMNETZ_DOCKER=true \
    HEIMNETZ_CONFIG_PATH=/app/config \
    HEIMNETZ_DATA_PATH=/app/data

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Network tools
    iputils-ping \
    net-tools \
    nmap \
    curl \
    wget \
    # Audio support (for voice interface)
    pulseaudio \
    alsa-utils \
    portaudio19-dev \
    # Build dependencies
    gcc \
    g++ \
    make \
    # Git for version info
    git \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r heimnetz && useradd -r -g heimnetz heimnetz

# Set work directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/config /app/data /app/logs && \
    chown -R heimnetz:heimnetz /app

# Copy Docker-specific configuration
COPY docker/heimnetz_docker.json /app/config/heimnetz_unified.json

# Switch to non-root user
USER heimnetz

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose ports
EXPOSE 5000

# Volume for persistent data
VOLUME ["/app/config", "/app/data", "/app/logs"]

# Default command
CMD ["python", "main.py", "--web", "--host", "0.0.0.0", "--port", "5000"]
