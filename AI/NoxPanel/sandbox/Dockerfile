FROM python:3.11-slim

# Install security tools
RUN apt-get update && apt-get install -y \
    clamav \
    clamav-daemon \
    apparmor \
    && rm -rf /var/lib/apt/lists/*

# Create sandbox user
RUN useradd -m -s /bin/bash sandbox

# Set resource limits
USER sandbox
WORKDIR /home/sandbox

# Copy plugin isolation script
COPY sandbox_runner.py /home/sandbox/
COPY security_monitor.py /home/sandbox/

# Set environment variables
ENV PYTHONPATH=/home/sandbox
ENV PLUGIN_SANDBOX=1
ENV SECURITY_LEVEL=HIGH

# Run sandbox
CMD ["python", "sandbox_runner.py"]
