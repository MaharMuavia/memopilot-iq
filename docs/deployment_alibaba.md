# Alibaba Cloud Deployment

MemoPilot IQ has Alibaba Cloud integration code for **Qwen Cloud (DashScope)**
AI calls, **Tablestore** persistent memory, and **OSS** redacted turn
snapshots and evaluation reports. The backend is containerised and can be
deployed to **ECS**, **Function Compute (FC3.0)**, or **Container Service for
Kubernetes (ACK)**. This repository does not yet claim a completed deployment;
use the evidence checklist below after deploying.

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
# On an ECS instance with Docker installed:
docker build -t memopilot-iq-backend ./backend
docker run -d --env-file backend/.env -p 8000:8000 memopilot-iq-backend
# Front with Nginx/SLB for TLS + the built frontend (frontend/dist).
```

## 3b. Deploy to Function Compute (Serverless Devs)

```bash
npm i -g @serverless-devs/s
cd backend
s deploy           # uses serverless.yaml; inject secrets as encrypted env vars
```

## 3c. Deploy to ACK (Kubernetes)

Push the image to Alibaba Container Registry (ACR), then apply a Deployment +
Service that mounts the secrets from a Kubernetes `Secret`.

## 4. Deployment proof to include in the repo

Add the following to `docs/` or `assets/` before submission (screenshots are
acceptable proof):

- `assets/proof_health_alibaba.png` — `GET /health` showing `ALIBABA_CLOUD_MODE`.
- `assets/proof_tablestore.png` — Tablestore console showing the
  `memopilot_memories` table with rows.
- `assets/proof_oss.png` — OSS bucket showing `memopilot/turns/*.json` snapshots.
- `assets/proof_ecs_or_fc.png` — the running ECS instance / FC function URL.

> The configuration selects cloud mode when credentials are supplied. Validate
> the running health endpoint and the actual Tablestore/OSS writes before
> representing the deployment as complete.
