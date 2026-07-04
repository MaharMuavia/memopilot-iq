# I Gave an AI Agent a Memory That Knows What to Forget. Here's What Qwen Cloud Taught Me.

*How I built MemoPilot IQ, a transparent "MemoryOS" for LLM agents, for the Qwen Cloud Global AI Hackathon (Track 1: MemoryAgent), and the one number that changed how I think about agent memory.*

> Publish on Dev.to, Medium, Hashnode, or LinkedIn, then paste the public URL into your hackathon submission to qualify for the Blog Post Prize. Suggested cover image: the architecture diagram from the repo (`assets/architecture.png`).

---

## The bug that started everything

I told my AI assistant on Monday that I wanted a FastAPI backend. On Tuesday it suggested Flask. On Wednesday I said "actually, switch from React to Next.js," and for the rest of the week it kept recommending React.

This is not a small annoyance. It is the defining failure of stateless language models: the moment a conversation ends, everything you established is gone. Your stack, your constraints, your deadlines, the decision you made and then changed. The industry's usual answer is "stuff the whole chat history back into the context window," but that just replays stale facts next to fresh ones with no way to tell them apart, and attention degrades on long inputs anyway.

I did not want a bigger memory. I wanted a **smarter** one: an agent that remembers what matters, forgets what is outdated, and can explain every decision. So I built **MemoPilot IQ** on Qwen Cloud.

## The thesis: memory is a governance problem, not a storage problem

Most memory systems treat this as a database question (how do I store and retrieve facts?). I came to believe it is a **governance** question:

- What is worth remembering?
- What must never be dropped (a security rule like "never commit API keys")?
- What has become invalid because a later decision overturned it?
- And can the system **explain** every one of those choices?

That reframing drove the whole design. In MemoPilot IQ, every memory is a typed record with a lifecycle state (`active`, `pinned`, `superseded`, `expired`, `archived`, `deleted`). Forgetting is not a decay curve; it is an auditable state machine. And retrieval is not a black box; every answer ships with a **Memory Trace** that shows exactly which memories were used, which were skipped, their scores, and why.

## How Qwen Cloud does the heavy lifting

Everything intelligent in the system runs on Qwen Cloud through the Alibaba Cloud DashScope OpenAI-compatible endpoint, which meant one small client handled three very different jobs:

1. **Reasoning and answering** with `qwen3.7-max`.
2. **Memory extraction** with the same model, prompted as a "Memory Editor" that returns strict JSON describing new memories, updates, and things to forget.
3. **Semantic retrieval** with `text-embedding-v3` (1024-dim vectors).

Two Qwen-specific things genuinely improved the design:

- **`reasoning_content` is separate from `content`.** Because `qwen3.7-max` returns its chain of thought in its own field, my extraction prompt got clean JSON in `content` while the model still "thought hard" about whether a message contained a durable preference or just small talk. I did not have to fight the model to stop narrating.
- **The OpenAI-compatible endpoint made multi-backbone science trivial.** More on that below, but pointing the exact same client at OpenAI and Gemini later took about twenty lines.

Here is the entire integration surface, more or less:

```python
resp = await client.post("/chat/completions", json={
    "model": "qwen3.7-max",
    "messages": messages,
    "response_format": {"type": "json_object"},  # for extraction
})
```

I also built a deterministic **offline fallback** (a hashing embedding and a rule-based extractor) so the whole system, tests, and benchmarks run with zero credentials. That decision paid off constantly: every result in my research paper is reproducible on a laptop with no API key, and I could debug the mechanism without spending tokens.

## The moment I made my own numbers look worse (on purpose)

My first benchmark reported **1.00 accuracy vs a 0.33 baseline**. It looked amazing. It was also, frankly, not believable, because it was six hand-picked scenarios and I was grading whether the right memory got *retrieved*, not whether the model *answered* correctly.

So I did the opposite of what you would expect in a competition: I made the evaluation harder and the numbers smaller. I expanded to 24 scenarios across six capability categories, switched to grading the model's actual generated answer, and re-ran. The honest result:

| Answer backbone | Memory agent | No-memory baseline |
|---|---|---|
| Qwen (`qwen3.7-max`) | **0.75** | 0.50 |
| OpenAI (`gpt-4o`) | **0.79** | 0.67 |

This taught me the most important lesson of the project. **The interesting claim is not "my system scores high." It is "the memory layer helps regardless of the model."** The MemoryOS layer is identical in both rows; only the answer model changes, and the memory layer lifts both a Qwen model and a GPT model. That is evidence the benefit comes from the memory design, not from any single LLM. Qwen stayed the production model; the others were there purely to prove generalization.

## Proving the mechanism with an ablation

Judges and reviewers do not trust "it works." They trust "here is exactly *why* it works." So I ran an ablation that disables one governance mechanism at a time, deterministically and offline:

| Variant | Recall@5 | Leak rate |
|---|---|---|
| Full system | 0.95 | **0.04** |
| Remove lifecycle exclusion | 1.00 | **0.38** |

Removing the mechanism that hides superseded and expired memories raised the rate of outdated-memory leaks **ninefold**. Meanwhile, recall barely moved when I zeroed out the scoring weights. The takeaway is precise and a little counterintuitive: the system's trustworthiness comes from its **lifecycle governance**, not from delicately tuned ranking weights. That is a far stronger statement than any single accuracy number.

## The one number that reframed everything: 8.4x

For real credibility I needed the standard benchmark that Mem0 and Zep use, so I built an adapter for **LoCoMo**, a very-long-conversation memory dataset (about 19 sessions and hundreds of turns per conversation). I ingested every dialogue turn as a memory, then answered 150 questions with `qwen3.7-max` and graded with strict token-F1.

Overall F1 was a modest **0.252**. On its own, that looks unremarkable. But I added a metric I had not seen elsewhere: **evidence recall**, which checks whether the annotated evidence turn actually made it into the assembled context. Then I split the results:

| | F1 |
|---|---|
| When the evidence **was** retrieved into context | **0.572** |
| When the evidence was **missed** | 0.068 |

An **8.4x gap.** This is the finding I am proudest of, because it turns a boring average into a precise diagnosis: **the answer model is perfectly capable when the memory layer hands it the right evidence; the bottleneck is purely retrieval depth** (I was only injecting the top 8 memories from roughly 480 candidate turns). Depth is a dial I can turn, not a flaw in the design. A single conditional table told me exactly where to spend the next week.

## War stories, because nothing shipped smoothly

- **Supersession broke on paraphrasing.** My first "did the user change their mind?" detector assumed the new choice is mentioned first. Then live Qwen rephrased "use FastAPI instead of Flask" as "switch from Flask to FastAPI," the old option came first, and supersession silently failed. The fix was a cue-aware parser ("from X," "instead of X," "rather than X" mark X as the *old* choice) plus honoring the structured `updates` the model already returns.
- **A four-hour benchmark died at 72 of 150 answers.** A Windows file-lock race between my own progress monitor and the checkpoint writer killed the run. But because I had built per-question checkpointing, resuming was literally re-running the same command: zero repeated API calls, picked up at question 73, finished clean. The insurance policy paid for itself on its first outing.

## What it grew into

What started as a hackathon entry became a small platform:

- A **transparent MemoryOS** with typed memories, an interpretable linear score, a hard "always include critical memories" guarantee, and a per-answer trace.
- A **React dashboard** with a live Memory Graph (watch a superseded memory go gray and struck-through), an analytics view, and a self-improving Reflection pass.
- **Production plumbing**: optional API-key auth, rate limiting, Prometheus metrics, pagination, per-memory audit history, and a two-stage retrieval path that stays fast at 100k memories.
- A **Python SDK** so any agent can embed the memory layer in a few lines.
- A **research paper** with an ablation, cross-backbone generalization, and the LoCoMo analysis.

All of it open source (MIT) and, thanks to the offline fallback, runnable with zero credentials.

## What Qwen Cloud got right for a build like this

Three things stood out. The **OpenAI-compatible API** meant I never wrote a bespoke client and could run head-to-head model science for free. The **separation of reasoning from output** in `qwen3.7-max` made structured extraction clean instead of a parsing nightmare. And `text-embedding-v3` gave me solid semantic retrieval out of the same provider, so the entire stack, chat, extraction, and embeddings, lived behind one key.

If you are building agent memory, my advice is: treat it as governance, measure the mechanism and not just the outcome, and be honest enough to make your own numbers smaller when the big ones are not believable. The smaller, honest numbers are the ones that told me something true.

---

**Repo:** https://github.com/MaharMuavia/memopilot-iq
**Built with:** Qwen Cloud (`qwen3.7-max`, `text-embedding-v3`) · FastAPI · React + Vite · Alibaba Cloud

*#QwenCloud #Qwen #MemoryAgent #LLM #AIAgents #Hackathon #OpenSource*
