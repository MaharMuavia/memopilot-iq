# Alibaba Cloud Deployment

MemoPilot IQ has Alibaba Cloud integration code for **Qwen Cloud (DashScope)**
AI calls, **Tablestore** persistent memory, and **OSS** redacted turn
snapshots and evaluation reports. The backend is containerised and can be
deployed to **ECS**, **Function Compute (FC3.0)**, or **Container Service for
Kubernetes (ACK)**. The submitted build is live on **Alibaba Cloud ECS** in
`ALIBABA_CLOUD_MODE`; see [the proof gallery](alibaba_cloud_proof.md).

## Alibaba Cloud integration in the codebase

| Concern | File | What it does |
|---|---|---|
| Qwen Cloud API | `backend/app/qwen_client.py` | Chat, JSON extraction, embeddings against the DashScope OpenAI-compatible endpoint. |
| Persistent memory | `backend/app/memory/store_alibaba.py` | Tablestore (OTS) tables for memories + events. |
| Object storage | `backend/app/storage/oss_client.py` | Uploads turn logs / snapshots / eval reports to an OSS bucket. |
| Deployment | `backend/Dockerfile`, `backend/serverless.yaml` | Container image + Serverless Devs descriptor for FC3.0. |

## 1. Provision services

```bash
# Tablestore (OTS): create an instance, note endpoint + instance name.
# OSS: create a bucket, note endpoint (e.g. oss-ap-southeast-1.aliyuncs.com).
# DashScope: create an API key for Qwen (international endpoint).
# RAM: create an AccessKey pair with OTS + OSS permissions.
```

## 2. Configure environment (never commit real values)

```bash
export APP_MODE=alibaba
export MEMORY_STORE=alibaba
export QWEN_API_KEY=sk-********
export QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
export QWEN_CHAT_MODEL=qwen-plus
export QWEN_EMBEDDING_MODEL=text-embedding-v3
export ALIBABA_ACCESS_KEY_ID=********
export ALIBABA_ACCESS_KEY_SECRET=********
export ALIBABA_REGION=ap-southeast-1
export ALIBABA_OSS_BUCKET=memopilot-iq
export ALIBABA_OSS_ENDPOINT=oss-ap-southeast-1.aliyuncs.com
export ALIBABA_TABLESTORE_ENDPOINT=https://memopilot.ap-southeast-1.ots.aliyuncs.com
export ALIBABA_TABLESTORE_INSTANCE=memopilot
```

When these are present, `GET /health` reports `"mode": "ALIBABA_CLOUD_MODE"`
and the UI header switches to the orange **Alibaba Cloud** badge.

## 3a. Deploy to ECS (Docker)

```bash
# On an ECS instance with deploy/.env.production configured:
bash deploy/ecs_deploy.sh
# This builds React/Nginx and runs FastAPI on a private Docker network.
```

For the single-instance demo, [`deploy/enable_https.sh`](../deploy/enable_https.sh)
runs a Caddy TLS gateway on port 443. Set `PUBLIC_HOST` to a real domain or an
IP-encoded `sslip.io` hostname and keep ports 80/443 open. A managed domain and
Alibaba Cloud load balancer remain the recommended long-lived deployment.

## 3b. Deploy to Function Compute (Serverless Devs)

```bash
npm i -g @serverless-devs/s
cd backend
s deploy           # uses serverless.yaml; inject secrets as encrypted env vars
```

## 3c. Deploy to ACK (Kubernetes)

Push the image to Alibaba Container Registry (ACR), then apply a Deployment +
Service that mounts the secrets from a Kubernetes `Secret`.

## 4. Submission evidence

The repository includes a safe, public proof package in
[`docs/alibaba_cloud_proof.md`](alibaba_cloud_proof.md):

- public deployed-app retrieval from Alibaba Tablestore;
- automatic memory creation; and
- cross-session recall with an explainable Memory Trace.

The source-level proof is [`backend/app/memory/store_alibaba.py`](../backend/app/memory/store_alibaba.py)
for Tablestore, [`backend/app/storage/oss_client.py`](../backend/app/storage/oss_client.py)
for OSS, and [`backend/app/qwen_client.py`](../backend/app/qwen_client.py) for
Qwen Cloud / DashScope.
