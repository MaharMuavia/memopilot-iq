# Deploy MemoPilot IQ backend to Alibaba Cloud ECS

A copy-paste path to get the backend **running on Alibaba Cloud** for your
deployment-proof recording. ~10 minutes.

## 0. Create the ECS instance (Alibaba Cloud console)
1. **ECS → Instances → Create Instance** (Pay-as-you-go is fine for a demo).
2. Image: **Alibaba Cloud Linux 3** (or Ubuntu 22.04). Size: `ecs.e-c1m1` / 1 vCPU 2 GB is enough.
3. Assign a **public IP** (or bind an EIP).
4. **Security Group → inbound rules → Add:** allow TCP **80** (and **22** for SSH) from `0.0.0.0/0`.
5. Note the **public IP** and your SSH login (key pair or password).

## 1. SSH in and get the code
```bash
ssh root@<your-ecs-public-ip>

# install git, then clone
yum -y install git || apt-get update && apt-get -y install git
git clone https://github.com/MaharMuavia/memopilot-iq.git
cd memopilot-iq
```

## 2. Add your Qwen key (never committed)
```bash
cp deploy/.env.production.example deploy/.env.production
nano deploy/.env.production        # paste your QWEN_API_KEY, save (Ctrl+O, Enter, Ctrl+X)
```

## 3. Deploy (one command)
```bash
bash deploy/ecs_deploy.sh
```
The script installs Docker, builds the image, runs the container on port 80, and
prints `/health`. You should see `"qwen_configured": true`.

## 4. Verify it's live on Alibaba Cloud
From your own laptop:
```bash
curl http://<your-ecs-public-ip>/health
```
Open `http://<your-ecs-public-ip>/docs` for the interactive API, and try a real
memory turn:
```bash
curl -X POST http://<your-ecs-public-ip>/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"judge","project_id":"p","session_id":"s1","message":"I prefer FastAPI and Alibaba Cloud. Never commit API keys."}'
```

## 5. Record the proof video (~30–60s, separate from the demo)
Screen-record:
1. The Alibaba Cloud **ECS console** showing your running instance + public IP.
2. A terminal/browser hitting `http://<that-public-ip>/health` → response shows the service is up.
3. A real `POST /api/chat` returning an answer + extracted memories.
4. (Optional) The **Security Group** rules page, to prove it's the same instance.

That proves the backend is running on Alibaba Cloud compute and calling Alibaba
Cloud's Qwen API.

## (Optional) Full ALIBABA_CLOUD_MODE
To make `/health` report `"mode":"ALIBABA_CLOUD_MODE"`, also provision
**Tablestore** + **OSS**, fill the `ALIBABA_*` vars in `deploy/.env.production`,
set `APP_MODE=alibaba` and `MEMORY_STORE=alibaba`, then re-run
`bash deploy/ecs_deploy.sh`. See [../docs/deployment_alibaba.md](../docs/deployment_alibaba.md).

## Troubleshooting
- `curl` from laptop hangs → the Security Group isn't allowing port 80. Re-check inbound rules.
- `docker logs memopilot-backend` shows the app logs.
- Health shows `qwen_configured: false` → the key wasn't picked up; check `deploy/.env.production`.
- Re-deploy after a code change: `git pull && bash deploy/ecs_deploy.sh`.
