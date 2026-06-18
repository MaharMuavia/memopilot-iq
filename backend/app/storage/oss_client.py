"""Alibaba Cloud Object Storage Service (OSS) client.

Used to persist raw conversation logs, memory snapshots and evaluation reports
to an OSS bucket. This is part of the Alibaba Cloud deployment proof: the code
integrates the official ``oss2`` SDK using credentials/endpoint from settings.

When OSS is not configured (local dev) the client no-ops gracefully and writes
snapshots to a local ``./snapshots`` directory instead, so nothing breaks.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..config import Settings
from ..utils.logging import get_logger

logger = get_logger("oss")


class OSSClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._bucket = None

    @property
    def enabled(self) -> bool:
        return self.settings.oss_configured

    def _get_bucket(self):
        if self._bucket is None:
            import oss2  # type: ignore

            s = self.settings
            auth = oss2.Auth(s.alibaba_access_key_id, s.alibaba_access_key_secret)
            self._bucket = oss2.Bucket(auth, s.alibaba_oss_endpoint, s.alibaba_oss_bucket)
            logger.info("Connected to Alibaba Cloud OSS bucket '%s'", s.alibaba_oss_bucket)
        return self._bucket

    def put_snapshot(self, name: str, payload: Dict[str, Any]) -> str:
        """Upload a JSON snapshot. Returns the OSS object key or local path."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        key = f"memopilot/{name}/{ts}.json"
        body = json.dumps(payload, default=str, indent=2)

        if self.enabled:
            try:
                self._get_bucket().put_object(key, body)
                logger.info("Uploaded snapshot to OSS: %s", key)
                return f"oss://{self.settings.alibaba_oss_bucket}/{key}"
            except Exception as exc:  # pragma: no cover - network path
                logger.warning("OSS upload failed (%s); writing local snapshot.", exc)

        # Local fallback.
        os.makedirs("./snapshots", exist_ok=True)
        local_path = os.path.join("./snapshots", key.replace("/", "_"))
        with open(local_path, "w", encoding="utf-8") as fh:
            fh.write(body)
        return local_path
