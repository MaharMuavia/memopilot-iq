#!/usr/bin/env bash
# Deploy the complete MemoPilot IQ web application to an Alibaba Cloud ECS host.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_IMAGE="memopilot-backend:latest"
FRONTEND_IMAGE="memopilot-frontend:latest"
BACKEND_CONTAINER="memopilot-backend"
FRONTEND_CONTAINER="memopilot-frontend"
NETWORK="memopilot-network"
DATA_VOLUME="memopilot-data"
HOST_PORT="${HOST_PORT:-80}"
ENV_FILE="${ENV_FILE:-$REPO_DIR/deploy/.env.production}"
BUILD_SHA="${APP_BUILD_SHA:-$(git -C "$REPO_DIR" rev-parse --short=12 HEAD 2>/dev/null || printf unknown)}"

green() { printf '\033[0;32m%s\033[0m\n' "$1"; }
red() { printf '\033[0;31m%s\033[0m\n' "$1" >&2; }

if [[ ! -f "$ENV_FILE" ]]; then
  red "Missing environment file: $ENV_FILE"
  printf 'Create it from deploy/.env.production.example and add server-side secrets.\n'
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  green "Installing Docker"
  if command -v dnf >/dev/null 2>&1; then
    dnf -y install docker || yum -y install docker
  elif command -v yum >/dev/null 2>&1; then
    yum -y install docker
  elif command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get -y install docker.io
  else
    red "Unsupported package manager; install Docker and run this script again."
    exit 1
  fi
  systemctl enable --now docker
fi

green "Building backend revision $BUILD_SHA"
docker build -t "$BACKEND_IMAGE" "$REPO_DIR/backend"
green "Building frontend"
docker build -t "$FRONTEND_IMAGE" "$REPO_DIR/frontend"

docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK" >/dev/null
docker volume create "$DATA_VOLUME" >/dev/null
docker rm -f "$FRONTEND_CONTAINER" "$BACKEND_CONTAINER" >/dev/null 2>&1 || true

green "Starting private backend"
docker run -d \
  --name "$BACKEND_CONTAINER" \
  --restart unless-stopped \
  --network "$NETWORK" \
  --network-alias backend \
  --env-file "$ENV_FILE" \
  -e APP_BUILD_SHA="$BUILD_SHA" \
  -e PORT=8000 \
  -e DATABASE_URL=sqlite:////data/memopilot.db \
  -e EVAL_REPORT_PATH=/data/latest-eval-report.json \
  -v "$DATA_VOLUME":/data \
  "$BACKEND_IMAGE" >/dev/null

green "Starting public frontend on port $HOST_PORT"
docker run -d \
  --name "$FRONTEND_CONTAINER" \
  --restart unless-stopped \
  --network "$NETWORK" \
  -p "$HOST_PORT":80 \
  "$FRONTEND_IMAGE" >/dev/null

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:$HOST_PORT/health" >/dev/null 2>&1; then
    green "Deployment healthy: revision $BUILD_SHA"
    curl -fsS "http://127.0.0.1:$HOST_PORT/health"
    printf '\nOpen http://<ecs-public-ip>:%s/app\n' "$HOST_PORT"
    exit 0
  fi
  sleep 1
done

red "Health check failed. Backend and frontend logs follow."
docker logs --tail 80 "$BACKEND_CONTAINER" >&2 || true
docker logs --tail 80 "$FRONTEND_CONTAINER" >&2 || true
exit 1
