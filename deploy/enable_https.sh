#!/usr/bin/env bash
# Add an automatically renewed HTTPS endpoint in front of the port-80 app.
set -euo pipefail

if [[ -z "${PUBLIC_HOST:-}" ]]; then
  echo "PUBLIC_HOST is required (for example: 47-84-129-218.sslip.io)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker rm -f memopilot-tls >/dev/null 2>&1 || true
docker volume create memopilot-caddy-data >/dev/null
docker volume create memopilot-caddy-config >/dev/null
docker run -d \
  --name memopilot-tls \
  --restart unless-stopped \
  --network host \
  -e PUBLIC_HOST="$PUBLIC_HOST" \
  -v "$SCRIPT_DIR/Caddyfile:/etc/caddy/Caddyfile:ro" \
  -v memopilot-caddy-data:/data \
  -v memopilot-caddy-config:/config \
  caddy:2.10-alpine

echo "HTTPS gateway started: https://$PUBLIC_HOST/app"
echo "Certificate issuance can take up to one minute. Check: docker logs memopilot-tls"
