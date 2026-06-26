# Building MemoPilot IQ: Giving AI Agents a Memory That Knows What to Forget

*My journey building a MemoryOS platform on Qwen Cloud for the Qwen Global AI Hackathon (Track 1: MemoryAgent).*

> Draft blog post — publish on Dev.to / Medium / LinkedIn / X and paste the
> public URL into your submission to qualify for the Blog Post Prize.

## The problem that bugged me

Every AI assistant I used had amnesia. I'd tell it my stack on Monday and
re-explain it on Tuesday. Worse: when I changed my mind ("use Next.js, not
React + Vite"), it kept recommending the old choice. Chat history doesn't fix
this — it just floods the context window with stale text.

I wanted an agent that **remembers what matters, forgets what's outdated, and
can explain why** — so I built **MemoPilot IQ**, a MemoryOS layer on Qwen Cloud.

## What I built

MemoPilot IQ treats long-term memory as a *governance* problem, not a storage
problem. After every message a Qwen-powered "Memory Editor" extracts structured
memories (preferences, decisions, constraints, deadlines, critical rules). A
transparent scoring formula ranks them, a context-budget manager injects only
the best within 2,500 tokens, and a forgetting engine expires/supersedes
outdated ones — all visible in a per-answer **Memory Trace**.

It also has a self-improving **Reflection** pass, a **Live Memory Graph**, and
an **Evaluation** benchmark against a no-memory baseline.

## How Qwen Cloud powered it

I used Qwen Cloud (Alibaba Cloud DashScope) for three things through one
OpenAI-compatible client:
- **`qwen3.7-max`** for reasoning and answers,
- **`qwen3.7-max`** for strict-JSON memory extraction and contradiction
  detection,
- **`text-embedding-v3`** for semantic retrieval.

A nice surprise: `qwen3.7-max` returns a separate `reasoning_content`, so the
extraction stayed clean JSON while the model still "thought" about the message.

## The results that made me smile

On a six-scenario diagnostic benchmark with a live Qwen backend:

| Metric | Memory agent | No-memory baseline |
|---|---|---|
| Task accuracy | **1.00** | 0.33 |
| Recall@5 | **1.00** | — |
| Outdated-memory leaks | **0** | — |
| Token savings | **97%** | — |
| Retrieval latency | **8.9 ms** | — |

The baseline only solved the two questions answerable without memory. Everything
requiring *state* — cross-session recall, supersession — it failed, exactly as
expected.

## Hardest part

Supersession. Detecting that "use Next.js instead of React + Vite" should
*retire* the old memory (without deleting it) took a topic-aware engine that
picks the first-mentioned option as the new choice. Watching the old memory go
faded-and-struck-through in the Memory Graph was the most satisfying moment.

## What's next

A larger benchmark, learned (not hand-tuned) scoring weights, and team-shared
memory. The whole thing is open source (MIT) and runs with zero credentials via
an offline fallback.

**Repo:** https://github.com/MaharMuavia/memopilot-iq
**Built with:** Qwen Cloud · FastAPI · React + Vite · Alibaba Cloud

*#QwenCloud #MemoryAgent #AI #Hackathon*
