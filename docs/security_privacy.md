# Security & Privacy

## Secret handling
- **No secrets in the repo.** `.env` is git-ignored; `.env.example` holds empty
  placeholders only. API keys are read from the environment at runtime.
- **Secrets never enter memory.** Every message is passed through
  `redact_secrets()` (`app/utils/security.py`) before extraction, and any
  extracted memory that still matches a secret pattern is dropped. Patterns
  cover OpenAI/DashScope `sk-` keys, AWS/Alibaba access keys, GitHub tokens,
  bearer tokens, JWTs, private-key blocks, and `key=...`/`password=...` assigns.
- **Manual creation guarded.** `POST /api/memories` and `PATCH` reject
  secret-like content with HTTP 400.
- **Secret-scan test.** `tests/test_api_chat.py::test_secret_is_redacted`
  asserts a pasted fake key is never stored.

## Privacy controls
- Per-memory `privacy_level` (`public` / `private` / `sensitive`) with scoring
  penalties (−0.25 weight) so sensitive memories are de-prioritised.
- Per-user + per-project filtering on every read (`store.list`), so users only
  see their own memories.
- **User data rights:** "Forget this memory" (DELETE), "Forget all" (clears the
  project), "Export memories as JSON". Forgetting is non-destructive by default
  (status transitions) unless the user explicitly hard-deletes.

## Recommended hardening before production
- Put the API behind authentication (the demo uses a fixed `demo-user`).
- Enable TLS at the SLB/Nginx layer.
- Scope Alibaba RAM AccessKeys to only OTS + the specific OSS bucket.
- Add a pre-commit secret scanner (e.g. `gitleaks`) in CI.
