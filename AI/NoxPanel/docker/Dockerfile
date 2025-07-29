# NoxPanel - Core Flask Application Dockerfile
# Audit Gate 1: Core Docker Containerization
# No multi-container orchestration until audit gates are passed

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/logs data/cache

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash noxpanel
RUN chown -R noxpanel:noxpanel /app
USER noxpanel

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=10)"

# Start application
CMD ["python", "main.py"]
