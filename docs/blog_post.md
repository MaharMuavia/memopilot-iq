# LinkedIn Post — MemoPilot IQ Build Journey

This is the publish-now social post for the Qwen Cloud Global AI Hackathon. It
is intentionally written as a progress story: the local product and automated
validation are working, while final Alibaba Cloud deployment and the live
Qwen-backed benchmark remain release gates.

## Ready-to-publish post

```text
AI agents do not only have a memory problem.

They have a memory-governance problem.

Remember everything: the context fills with noise, stale decisions, and sensitive data. Remember nothing: users repeat themselves every session. Keep the wrong thing: the agent becomes confidently outdated.

That tension led me to build MemoPilot IQ for the Qwen Cloud Global AI Hackathon (Track 1: MemoryAgent).

MemoPilot IQ is an auditable memory layer for AI agents. It structures conversations, recalls the right facts inside a hard token budget, retires outdated decisions, and explains every memory used or skipped.

Here is the demo that shaped the product:

1. I tell the agent: “Use React + Vite for this project.”
2. In a later session, I change the decision to Next.js.
3. MemoPilot IQ keeps the history but marks React + Vite as superseded.
4. On the next question, only Next.js enters the model context—and the Memory Trace shows why the old choice was excluded.

The goal is not perfect recall. It is safe, bounded, reversible recall.

Under the hood, I built a custom MemoryOS pipeline:

• 12 typed categories instead of raw chat logs
• hybrid retrieval across embeddings, keywords, tags, and structured filters
• interpretable scoring across relevance, importance, recency, usage, project match, and lifecycle state
• a hard 2,500-token memory budget
• non-destructive supersession, expiration, archiving, pinning, export, and erasure
• pre-storage secret redaction
• a Memory Trace, timeline, graph, analytics, and user controls

Qwen Cloud has three focused roles in the architecture:

1. qwen-plus generates answers from the assembled memory context.
2. A structured “Memory Editor” extracts new memories and lifecycle actions.
3. text-embedding-v3 powers semantic recall.

I also built a 24-scenario diagnostic against a no-memory baseline, checking answer accuracy, context recall, stale-memory leakage, context reduction, and latency. The dashboard shows the running build’s report—not hard-coded marketing numbers.

The hardest lesson was that retrieval quality alone is not enough. A useful memory system also needs lifecycle rules, privacy boundaries, observability, and a way for users to reverse its decisions.

The local flow, tests, CI, offline evaluation, and Docker setup are working. I am now completing the Alibaba Cloud deployment, then I will publish model-backed results from the submitted commit.

This is reusable infrastructure, not a chatbot skin: FastAPI, React, a Python SDK, an evaluation harness, and Tablestore/OSS adapters.

I would value feedback from people building agents: what should an AI be allowed to remember—and what must it be designed to forget?

Open-source repository: https://github.com/MaharMuavia/memopilot-iq

#QwenCloud #AlibabaCloud #MemoryAgent #AIAgents #AIEngineering #OpenSource
```

## Recommended media

Attach two or three images in this order:

1. A clean MemoPilot IQ Memory Trace screenshot showing the active Next.js
   decision and the superseded React + Vite decision.
2. [`../assets/architecture.png`](../assets/architecture.png).
3. A timeline or graph screenshot showing the supersession edge.

Suggested alt text for the architecture image:

> MemoPilot IQ architecture: a React interface calls a FastAPI service whose
> MemoryOS layer extracts, scores, retrieves, and governs memories using Qwen
> Cloud, with SQLite locally or Alibaba Cloud Tablestore and OSS in cloud mode.

## Before publishing

- Keep the post public.
- Confirm the repository link opens while signed out.
- Do not add deployment or benchmark claims until the matching public evidence
  exists.
- After publishing, add the LinkedIn post URL to the Devpost submission so the
  entry is eligible for the Blog Post bonus prize.
