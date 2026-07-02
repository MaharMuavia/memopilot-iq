# MemoPilot IQ — Python SDK

Embed the MemoryOS layer in **any** agent or app in a few lines. Single file,
one dependency (`requests`); vendor `memopilot.py` into your project or keep it
on your path.

```python
from memopilot import MemoPilotClient

mp = MemoPilotClient("http://localhost:8000")          # api_key="mk-..." if auth is on

# Memory-augmented chat — answer + recalled memories + full decision trace
r = mp.chat("Design my backend.", user_id="alice", project_id="webapp")
print(r["answer"])
print("recalled:", [m["content"] for m in r["used_memories"]])
print("trace: injected", len(r["trace"]["included"]),
      "skipped", len(r["trace"]["skipped"]),
      f'({r["trace"]["tokens_used"]}/{r["trace"]["token_budget"]} tokens)')

# Direct memory operations
mp.add_memory("Prefers FastAPI for backends", type="preference",
              user_id="alice", project_id="webapp")
page = mp.memories(user_id="alice", project_id="webapp", q="fastapi", limit=20)
mp.pin(page["memories"][0]["memory_id"])
print(mp.history(page["memories"][0]["memory_id"]))    # full audit trail

# Intelligence operations
mp.reflect(user_id="alice", project_id="webapp")       # consolidate + derive insights
graph = mp.graph(user_id="alice", project_id="webapp") # nodes + supersession edges
```

## Surface

| Area | Methods |
|---|---|
| Chat | `chat` |
| Memories | `memories` (filters + pagination), `add_memory`, `history`, `pin`, `archive`, `forget`, `forget_all`, `export`, `timeline` |
| Intelligence | `reflect`, `graph`, `analytics` |
| Evaluation | `run_benchmark`, `run_ablation`, `run_demo` |
| Ops | `health` |

## Auth & errors

If the server sets `MEMOPILOT_API_KEYS`, pass `api_key=` — it is sent as
`X-API-Key`. Every non-2xx response raises `MemoPilotError` with
`.status_code` and `.detail` (including `429` when rate-limited).
