
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY resource_manager.py .
COPY tenant_manager.py .
COPY tenant_auth.py .
COPY enterprise_config.json .

EXPOSE 5003

CMD ["python", "resource_manager.py"]
