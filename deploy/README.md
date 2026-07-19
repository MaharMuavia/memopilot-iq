# Deploy MemoPilot IQ to Alibaba Cloud ECS

A copy-paste path to run the React/Nginx frontend and private FastAPI backend
on Alibaba Cloud ECS for deployment-proof recording. ~10 minutes.

## 0. Create the ECS instance (Alibaba Cloud console)
1. **ECS → Instances → Create Instance** (Pay-as-you-go is fine for a demo).
2. Image: **Alibaba Cloud Linux 3** (or Ubuntu 22.04). Size: `ecs.e-c1m1` / 1 vCPU 2 GB is enough.
3. Assign a **public IP** (or bind an EIP).
4. **Security Group → inbound rules → Add:** allow TCP **80** and **443** from
   `0.0.0.0/0`; restrict TCP **22** to your own public IP/CIDR.
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
The script installs Docker, builds both images, puts the backend on a private
Docker network, exposes only the Nginx frontend on port 80, and prints
`/health`. You should see `"qwen_configured": true` and the deployed Git SHA.

## 4. Enable HTTPS

Use a domain you control, or an IP-encoded `sslip.io` hostname for the demo.
The latter resolves automatically; replace the example with your ECS IP:

```bash
export PUBLIC_HOST=47-84-129-218.sslip.io
bash deploy/enable_https.sh
curl -I "https://$PUBLIC_HOST/health"
```

The Caddy gateway obtains and renews a public certificate and forwards HTTPS
to the existing port-80 frontend. Keep TCP 443 open in the ECS security group.

## 5. Verify it's live on Alibaba Cloud
From your own laptop:
```bash
PUBLIC_HOST=47-84-129-218.sslip.io
curl "https://$PUBLIC_HOST/health"
```
Open `https://<your-sslip-host>/app` for the application, and try a real
memory turn from a terminal:
```bash
curl -c cookies.txt -b cookies.txt -X POST "https://$PUBLIC_HOST/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"judge","project_id":"p","session_id":"s1","message":"I prefer FastAPI and Alibaba Cloud. Never commit API keys."}'
```

## 6. Record the proof video (~30–60s, separate from the demo)
Screen-record:
1. The Alibaba Cloud **ECS console** showing your running instance + public IP.
2. A terminal/browser hitting `https://<sslip-host>/health` → response shows
   the service, Alibaba store, isolation mode, and exact build SHA.
3. A real `POST /api/chat` returning an answer + extracted memories.
4. (Optional) The **Security Group** rules page, to prove it's the same instance.

That proves the full application is served from Alibaba Cloud compute and that
the backend calls Alibaba Cloud's Qwen API.

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
