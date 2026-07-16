# Security & Privacy

## Secret handling

- `.env` is git-ignored and examples contain only blank placeholders. Never
  paste a working credential into chat, screenshots, a Docker command, or a
  public repository.
- Messages are redacted before memory extraction. Secret-like extracted
  memories are dropped, while manual creation and edits reject them with HTTP
  400.
- Turn snapshots redact the user message and answer before writing to local
  snapshots or Alibaba OSS. This protects persistence; it does not turn a chat
  box into a credential vault, so users must not submit real secrets to an LLM.
- Tests cover both memory storage and snapshot redaction.

## Namespaces and access

- Local demo mode is deliberately open and uses the caller-provided `user_id`.
  It must not be exposed as a multi-user service.
- When `MEMOPILOT_API_KEYS` is configured, every valid API key is mapped to a
  non-reversible server-side memory namespace. Request `user_id` values cannot
  select another key's memories, and trace/update/delete operations enforce the
  same namespace.
- API keys are a small deployment safeguard, not full user authentication.
  Internet-facing production deployments still need TLS, an identity provider,
  key rotation, and a gateway-backed distributed rate limiter.

## User data controls

- Soft delete preserves an audit record; hard delete removes the memory row.
  Use **Forget all** when the user also wants the prior timeline erased.
- **Forget all** removes both memory records and their previous timeline events
  for the selected project, then creates a content-free deletion receipt.
- Export returns the current memory records for the active namespace. Add an
  authenticated, audited data-erasure workflow before handling regulated data.

## Deployment checklist

1. Rotate any API key accidentally shown in a terminal, build log, recording,
   or chat transcript.
2. Store Qwen and Alibaba credentials in an Alibaba secret manager or encrypted
   service environment—not in image layers or source-controlled files.
3. Scope RAM permissions to the required Tablestore instance and OSS bucket.
4. Add `gitleaks` (or equivalent) to CI and verify that no `.env` file is
   tracked before publishing.
