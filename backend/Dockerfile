# MemoPilot IQ backend image.
# Deployable to Alibaba Cloud ECS, Container Service for Kubernetes (ACK),
# or Serverless App Engine (SAE). See docs/deployment_alibaba.md.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Honour the platform-provided PORT if present (SAE/Function Compute).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
