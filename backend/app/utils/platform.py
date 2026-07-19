"""Production platform middleware: API-key auth, rate limiting, metrics.

Production safeguards with zero friction for the local demo:

* **API-key auth** — set ``MEMOPILOT_API_KEYS`` (comma-separated) and every
  ``/api/*`` request must carry a matching ``X-API-Key`` header. When unset the
  API stays open (demo/local mode). ``/health``, ``/metrics``, ``/docs`` are
  always public.
* **Rate limiting** — sliding one-minute window per API key (or client IP),
  ``RATE_LIMIT_PER_MINUTE`` (default 120). Exceeding it returns 429 with a
  ``Retry-After`` hint.
* **Metrics** — request counters and latency aggregates per route template,
  exposed at ``GET /metrics`` in Prometheus text exposition format.

Everything is process-local and dependency-free by design; swap in Redis or a
gateway for multi-instance deployments without touching the app code.
"""
from __future__ import annotations

import hmac
import os
import re
import secrets
import time
from hashlib import sha256
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from .logging import get_logger

logger = get_logger("platform")

_PUBLIC_PREFIXES = ("/health", "/metrics", "/docs", "/openapi.json", "/redoc")
_TENANT_COOKIE = "memopilot_tenant"
_ANONYMOUS_NAMESPACE = re.compile(r"^anon_[A-Za-z0-9_-]{20,80}$")


def _configured_keys() -> set[str]:
    raw = os.getenv("MEMOPILOT_API_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}


def _rate_limit() -> int:
    try:
        return max(1, int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")))
    except ValueError:
        return 120


def _key_namespace(api_key: str) -> str:
    """Create a stable non-reversible user namespace for an API key."""
    return f"key_{sha256(api_key.encode('utf-8')).hexdigest()[:24]}"


def _public_isolation_enabled() -> bool:
    return os.getenv("MEMOPILOT_PUBLIC_DEMO_ISOLATION", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _secure_cookie_enabled(request: Request) -> bool:
    """Honor an explicit proxy-safe setting before inspecting request scheme."""
    configured = os.getenv("MEMOPILOT_COOKIE_SECURE", "").strip().lower()
    if configured:
        return configured in {"1", "true", "yes", "on"}
    return request.url.scheme == "https"


def _sign_namespace(namespace: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode("utf-8"), namespace.encode("utf-8"), sha256
    ).hexdigest()
    return f"{namespace}.{signature}"


def _anonymous_namespace(request: Request, secret: str) -> tuple[str, str | None]:
    """Validate or create a signed, opaque anonymous tenant namespace."""
    token = request.cookies.get(_TENANT_COOKIE, "")
    if "." in token:
        namespace, signature = token.rsplit(".", 1)
        expected = _sign_namespace(namespace, secret).rsplit(".", 1)[1]
        if _ANONYMOUS_NAMESPACE.fullmatch(namespace) and hmac.compare_digest(
            signature, expected
        ):
            return namespace, None
    namespace = f"anon_{secrets.token_urlsafe(24)}"
    return namespace, _sign_namespace(namespace, secret)


def require_admin(request: Request) -> None:
    """Protect expensive maintenance endpoints when an admin key is configured."""
    expected = os.getenv("MEMOPILOT_ADMIN_KEY", "").strip()
    if _public_isolation_enabled() and not expected:
        raise HTTPException(
            status_code=503,
            detail="Administrative evaluation is disabled until MEMOPILOT_ADMIN_KEY is configured.",
        )
    if expected and not hmac.compare_digest(
        request.headers.get("x-admin-key", ""), expected
    ):
        raise HTTPException(status_code=403, detail="Admin authorization required.")


class Metrics:
    """Tiny in-process metrics registry (Prometheus text format)."""

    def __init__(self) -> None:
        self.requests: Dict[Tuple[str, str, int], int] = defaultdict(int)
        self.latency_sum_ms: Dict[str, float] = defaultdict(float)
        self.latency_count: Dict[str, int] = defaultdict(int)
        self.rate_limited_total = 0
        self.unauthorized_total = 0
        self.started_at = time.time()

    def observe(self, method: str, route: str, status: int, ms: float) -> None:
        self.requests[(method, route, status)] += 1
        self.latency_sum_ms[route] += ms
        self.latency_count[route] += 1

    def render(self) -> str:
        lines = [
            "# HELP memopilot_uptime_seconds Process uptime.",
            "# TYPE memopilot_uptime_seconds gauge",
            f"memopilot_uptime_seconds {time.time() - self.started_at:.0f}",
            "# HELP memopilot_requests_total HTTP requests by method/route/status.",
            "# TYPE memopilot_requests_total counter",
        ]
        for (method, route, status), n in sorted(self.requests.items()):
            lines.append(
                f'memopilot_requests_total{{method="{method}",route="{route}",status="{status}"}} {n}'
            )
        lines += [
            "# HELP memopilot_request_latency_ms_sum Summed request latency per route.",
            "# TYPE memopilot_request_latency_ms_sum counter",
        ]
        for route, total in sorted(self.latency_sum_ms.items()):
            lines.append(f'memopilot_request_latency_ms_sum{{route="{route}"}} {total:.1f}')
            lines.append(
                f'memopilot_request_latency_ms_count{{route="{route}"}} {self.latency_count[route]}'
            )
        lines += [
            "# TYPE memopilot_rate_limited_total counter",
            f"memopilot_rate_limited_total {self.rate_limited_total}",
            "# TYPE memopilot_unauthorized_total counter",
            f"memopilot_unauthorized_total {self.unauthorized_total}",
        ]
        return "\n".join(lines) + "\n"


class SlidingWindowLimiter:
    """Per-identity sliding one-minute window."""

    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, identity: str, limit: int) -> bool:
        now = time.time()
        window = self._hits[identity]
        while window and now - window[0] > 60.0:
            window.popleft()
        if len(window) >= limit:
            return False
        window.append(now)
        return True


def install_platform(app: FastAPI) -> None:
    """Attach auth/rate-limit/metrics middleware and the /metrics endpoint."""
    metrics = Metrics()
    limiter = SlidingWindowLimiter()
    app.state.metrics = metrics
    identity_secret = os.getenv("MEMOPILOT_IDENTITY_SECRET", "").strip()
    if _public_isolation_enabled() and not identity_secret:
        identity_secret = secrets.token_urlsafe(48)
        logger.warning(
            "MEMOPILOT_PUBLIC_DEMO_ISOLATION is enabled without a persistent "
            "MEMOPILOT_IDENTITY_SECRET; anonymous namespaces will reset on restart."
        )
    elif _public_isolation_enabled() and len(identity_secret.encode("utf-8")) < 32:
        raise RuntimeError(
            "MEMOPILOT_IDENTITY_SECRET must contain at least 32 bytes when "
            "public demo isolation is enabled."
        )

    def attach_identity_cookie(response, token: str | None, request: Request):
        if token:
            response.set_cookie(
                _TENANT_COOKIE,
                token,
                max_age=30 * 24 * 60 * 60,
                httponly=True,
                secure=_secure_cookie_enabled(request),
                samesite="lax",
                path="/",
            )
        return response

    @app.middleware("http")
    async def platform_middleware(request: Request, call_next):
        path = request.url.path
        start = time.perf_counter()
        identity_cookie: str | None = None

        if path.startswith("/api"):
            keys = _configured_keys()
            api_key = request.headers.get("x-api-key", "")
            if keys and api_key not in keys:
                metrics.unauthorized_total += 1
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing or invalid X-API-Key."},
                )
            request.state.auth_enabled = bool(keys)
            if keys:
                request.state.authenticated_user_id = _key_namespace(api_key)
                request.state.identity_mode = "api-key"
            elif _public_isolation_enabled():
                namespace, identity_cookie = _anonymous_namespace(
                    request, identity_secret
                )
                request.state.authenticated_user_id = namespace
                request.state.identity_mode = "signed-anonymous-cookie"
            else:
                request.state.identity_mode = "caller-supplied-demo"
            identity = (
                getattr(request.state, "authenticated_user_id", None)
                or api_key
                or (request.client.host if request.client else "anon")
            )
            if not limiter.allow(identity, _rate_limit()):
                metrics.rate_limited_total += 1
                return attach_identity_cookie(
                    JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded."},
                        headers={"Retry-After": "60"},
                    ),
                    identity_cookie,
                    request,
                )

        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        route = request.scope.get("route")
        route_path = getattr(route, "path", path)
        if not path.startswith(("/docs", "/openapi", "/redoc")):
            metrics.observe(request.method, route_path, response.status_code, elapsed_ms)
        return attach_identity_cookie(response, identity_cookie, request)

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint() -> PlainTextResponse:
        return PlainTextResponse(metrics.render(), media_type="text/plain; version=0.0.4")
