#!/usr/bin/env bash
# =============================================================================
# MemoPilot IQ — Alibaba Cloud ECS one-shot deploy script.
#
# Run this ON your Alibaba Cloud ECS instance (Alibaba Cloud Linux 3 / Ubuntu).
# It installs Docker if needed, builds the backend image from this repo, and
# runs it as a container exposed on $HOST_PORT. Re-running it redeploys cleanly.
#
#   1) SSH into your ECS box:           ssh root@<your-ecs-public-ip>
#   2) Install git + clone the repo:    yum -y install git || apt -y install git
#                                       git clone https://github.com/MaharMuavia/memopilot-iq.git
#   3) Create the env file (NEVER commit it — see deploy/.env.production.example):
#                                       cd memopilot-iq
#                                       cp deploy/.env.production.example deploy/.env.production
#                                       nano deploy/.env.production      # paste your QWEN_API_KEY
#   4) Run this script:                 bash deploy/ecs_deploy.sh
#
# Open $HOST_PORT (default 80) in your ECS Security Group inbound rules first.
# =============================================================================
set -euo pipefail

# ---- Config (override by exporting before running) --------------------------
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # repo root
IMAGE_NAME="memopilot-iq-backend"
CONTAINER_NAME="memopilot-backend"
HOST_PORT="${HOST_PORT:-80}"          # public port (open this in the Security Group)
CONTAINER_PORT="8000"
ENV_FILE="${ENV_FILE:-$REPO_DIR/deploy/.env.production}"
DATA_VOLUME="memopilot-data"

green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
red()   { printf '\033[0;31m%s\033[0m\n' "$1"; }

# ---- 1. Ensure the env file exists ------------------------------------------
if [[ ! -f "$ENV_FILE" ]]; then
  red "Missing env file: $ENV_FILE"
  echo "Create it first:"
  echo "  cp deploy/.env.production.example deploy/.env.production"
  echo "  nano deploy/.env.production   # add your QWEN_API_KEY"
  exit 1
fi

# ---- 2. Install Docker if missing -------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  green "Installing Docker..."
  if command -v dnf >/dev/null 2>&1; then
    dnf -y install docker || yum -y install docker
  elif command -v yum >/dev/null 2>&1; then
    yum -y install docker
  elif command -v apt-get >/dev/null 2>&1; then
    apt-get update && apt-get -y install docker.io
  else
    red "Unsupported package manager. Install Docker manually and re-run."
    exit 1
  fi
  systemctl enable --now docker
fi
green "Docker: $(docker --version)"

# ---- 3. Build the backend image ---------------------------------------------
green "Building image $IMAGE_NAME from $REPO_DIR/backend ..."
docker build -t "$IMAGE_NAME" "$REPO_DIR/backend"

# ---- 4. (Re)create the container --------------------------------------------
green "Replacing any existing container..."
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker volume create "$DATA_VOLUME" >/dev/null 2>&1 || true

green "Starting container on host port $HOST_PORT ..."
docker run -d \
  --name "$CONTAINER_NAME" \
  --restart unless-stopped \
  --env-file "$ENV_FILE" \
  -e DATABASE_URL="sqlite:////data/memopilot.db" \
  -e PORT="$CONTAINER_PORT" \
  -v "$DATA_VOLUME":/data \
  -p "$HOST_PORT":"$CONTAINER_PORT" \
  "$IMAGE_NAME"

# ---- 5. Health check --------------------------------------------------------
green "Waiting for the backend to come up..."
for i in $(seq 1 20); do
  if curl -fs "http://localhost:$HOST_PORT/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo
green "=== /health ==="
curl -s "http://localhost:$HOST_PORT/health" || red "Health check failed — see: docker logs $CONTAINER_NAME"
echo
echo
PUBLIC_IP="$(curl -s http://100.100.100.200/latest/meta-data/eipv4 2>/dev/null || curl -s ifconfig.me 2>/dev/null || echo '<your-ecs-public-ip>')"
green "Deployed. Test from anywhere:"
echo "  curl http://$PUBLIC_IP:$HOST_PORT/health"
echo "  open http://$PUBLIC_IP:$HOST_PORT/docs   (interactive API)"
echo
echo "Logs:    docker logs -f $CONTAINER_NAME"
echo "Restart: docker restart $CONTAINER_NAME"
