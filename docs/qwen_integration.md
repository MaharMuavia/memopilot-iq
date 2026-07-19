# Qwen Cloud Integration

All AI in MemoPilot IQ runs through a single client,
[`backend/app/qwen_client.py`](../backend/app/qwen_client.py), which targets the
Alibaba Cloud **DashScope** OpenAI-compatible endpoint.

## Where Qwen is used

| Capability | Method | Model (default) | Purpose |
|---|---|---|---|
| Chat / reasoning | `QwenClient.chat` | `qwen-plus` | Generates the final answer from the budgeted memory context. |
| Memory extraction | `QwenClient.extract_json` | `qwen-plus` | The "Memory Editor" prompt returns strict JSON of `new_memories`, `updates`, `forget`. |
| General contradiction updates | `QwenClient.extract_json` | `qwen-plus` | The structured pass flags updates outside the deterministic taxonomy; ownership checks and lifecycle rules apply them. |
| Embeddings | `QwenClient.embed` | `text-embedding-v3` | Vectorises memories + queries for semantic retrieval. |

## Configuration

```bash
QWEN_API_KEY=sk-********
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_CHAT_MODEL=qwen-plus
QWEN_EMBEDDING_MODEL=text-embedding-v3
```

`GET /health` reports `"qwen_configured": true/false`, and the dashboard header
shows a **Qwen Online / Qwen Offline** badge.

## Safe local fallback

Robustness is a hard requirement: the entire app, test suite, and evaluation
benchmark must run with **no API key**. When `QWEN_API_KEY` is unset (or a call
fails), the client transparently switches to a deterministic offline
implementation:

- **chat** → a grounded response synthesised from the injected memory block.
- **extract_json** → a heuristic extractor that classifies clauses into memory
  types (preference/decision/critical/temporary/…), so creation, supersession,
  and expiry are all observable offline.
- **embed** → a deterministic hashing embedding (bag-of-words → fixed dim).

This means a judge can clone and run the project with zero credentials and still
see every MemoPilot memory-layer behaviour; adding a real key simply upgrades answer quality.

## Strict JSON handling

`extract_json` requests `response_format={"type": "json_object"}`, strips
markdown fences if present, and falls back to a brace-matching parse. If parsing
still fails, it returns an empty action set rather than raising — extraction can
never crash a chat turn.
