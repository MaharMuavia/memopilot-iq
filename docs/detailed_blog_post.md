---
title: "AI Agents Don’t Need More Memory. They Need Memory Governance."
published: false
description: "How I built MemoPilot IQ with Qwen Cloud: structured memory, hybrid retrieval, selective forgetting, strict token budgets, and explainable recall."
tags: ai, agents, qwen, opensource
---

Most AI assistants are impressive until the conversation ends.

Start a new session and the context disappears. Keep adding history and the
opposite problem appears: the model sees too much, including old decisions,
irrelevant details, and information the user no longer wants remembered.

That led me to a question that changed how I thought about agent memory:

> What if the difficult part is not remembering more, but governing what is
> remembered?

I built **MemoPilot IQ** to explore that question for the
[Qwen Cloud Global AI Hackathon](https://www.qwencloud.com/challenge/hackathon),
Track 1: MemoryAgent. It is an auditable memory layer that turns conversations
into structured records, retrieves the right records inside a hard context
budget, retires stale information without destroying the audit trail, and
explains every memory it uses or skips.

This article is the engineering story behind the project: the failure modes I
designed for, how Qwen Cloud fits into the architecture, what I learned while
building its memory-governance layer, and how I am testing claims that are easy to make but much
harder to prove.

## The real problem: memory can make an agent confidently wrong

Imagine that I tell a project assistant:

> Use React and Vite for the frontend.

A week later, in another session, I make a new decision:

> After this submission, we plan to migrate to Next.js.

A basic vector database can retrieve both statements because both are
semantically relevant to a question about the frontend stack. If the older
statement happens to score higher, the assistant may recommend React and Vite
again. The system remembered correctly and still produced the wrong result.

I found five recurring failure modes:

1. **Amnesia:** useful preferences and constraints disappear between sessions.
2. **Context flooding:** raw history consumes tokens without adding equivalent
   value.
3. **Stale recall:** an old decision competes with the decision that replaced
   it.
4. **Opaque retrieval:** the user cannot see why a memory influenced an answer.
5. **Irreversible storage:** users cannot meaningfully inspect, correct, export,
   or erase what the agent remembers.

These are lifecycle and governance problems, not only retrieval problems.

## From chat history to structured memory

MemoPilot IQ does not treat every message as permanent memory. A Qwen-powered
**Memory Editor** extracts candidate records and lifecycle actions from a turn.
Each record has an explicit type, status, source, confidence, importance,
timestamps, tags, privacy level, and optional expiration or supersession links.

The schema supports 12 memory categories, including preferences, project facts,
decisions, constraints, deadlines, mistakes, learning goals, tasks, critical
rules, and temporary information.

A simplified supersession result looks like this:

```json
{
  "type": "decision",
  "status": "superseded",
  "content": "Use React + Vite for the frontend",
  "superseded_by": "mem_nextjs"
}
```

The replacement stays active:

```json
{
  "memory_id": "mem_nextjs",
  "type": "decision",
  "status": "active",
  "content": "After this submission, migrate the frontend to Next.js",
  "supersedes": "mem_react_vite"
}
```

The old record is not silently deleted. It remains visible in the timeline for
accountability, but lifecycle filtering prevents it from entering future model
context.

That distinction became one of the core ideas in the project:

> Preserve history for auditability; select only current truth for reasoning.

## Architecture: three focused roles for Qwen Cloud

![MemoPilot IQ architecture showing the React + Vite frontend, FastAPI backend, MemoPilot memory layer, Qwen Cloud, Tablestore, OSS, and Alibaba deployment targets](https://raw.githubusercontent.com/MaharMuavia/memopilot-iq/main/assets/architecture.svg)

MemoPilot IQ separates the language model from the memory-governance logic.
When cloud credentials are configured, Qwen Cloud serves three focused roles:

1. **Answer generation:** `qwen-plus` reasons over the current question and the
   assembled, budgeted memory context.
2. **Structured extraction:** a JSON-only Memory Editor identifies new records,
   updates, supersession, archival, and forgetting actions.
3. **Semantic retrieval:** `text-embedding-v3` embeds queries and memory content
   for dense similarity search.

The rest is application logic I can test independently:

- a React and Vite interface for chat, traces, memory controls, timeline,
  analytics, evaluation, and a live memory graph;
- a FastAPI service that owns orchestration and API boundaries;
- MemoPilot memory-layer components for extraction, scoring, retrieval, context assembly,
  forgetting, reflection, and trace generation;
- SQLite and in-process vectors for local development;
- Alibaba Cloud Tablestore and OSS adapters for cloud persistence and redacted
  snapshots;
- container and deployment configuration targeting Alibaba Cloud compute.

Local mode deliberately includes a deterministic offline fallback. That lets a
contributor clone the project, exercise the complete workflow, and run the test
suite without receiving my credentials or spending API credit. It does **not**
pretend to be final model evidence; the final deployed Qwen-backed evaluation is
a separate release gate.

## What happens when a user asks a question?

The request path is designed to keep model context small and explainable.

### 1. Scope the candidates

Memory retrieval begins inside the current user and project boundary. Records
that are deleted, expired, or superseded are ineligible for injection. This
prevents a high semantic score from reviving information that lifecycle policy
has already retired.

### 2. Retrieve with more than vector similarity

The retriever combines dense similarity with sparse keyword and tag overlap,
then applies structured filters. This matters for exact technical tokens,
deadlines, names, and project-specific vocabulary that semantic similarity may
not rank reliably on its own.

### 3. Score with interpretable components

Each candidate receives a score built from semantic relevance, importance,
recency, confidence, usage, project match, criticality, and explicit penalties.
The current formula is intentionally visible:

```text
score = 0.40*semantic + 0.20*importance + 0.15*recency
      + 0.10*confidence + 0.10*usage + 0.15*project_match
      + 0.20*critical_bonus
      - 0.30*outdated - 0.25*privacy - 0.50*superseded
```

The weights are configuration and engineering choices, not universal truths.
Exposing them makes the system debuggable and gives future evaluation something
specific to challenge.

### 4. Enforce a hard context budget

The context builder has a default memory budget of 2,500 tokens. Critical and
pinned records are prioritized, but priority never overrides the configured
limit. The objective is to deliver the smallest useful set of memories, not to
dump the database into the prompt.

### 5. Return the answer and the evidence

The API returns the answer together with memory actions and a **Memory Trace**.
The trace shows:

- which memories were included;
- which candidates were skipped;
- the score components and selection reason;
- approximate token cost and remaining budget;
- the active runtime and provider mode.

In the planned React-to-Next.js migration scenario, the user can see the planned
Next.js decision in the included set and the older frontend preference marked as
superseded in the timeline. The answer still identifies React + Vite as the
current submitted implementation. The interface turns a hidden retrieval decision into something a
person can inspect.

## Forgetting should be a feature, not a failure

“Persistent memory” can sound like “store everything forever.” I think that is
the wrong product goal.

MemoPilot IQ treats forgetting as a lifecycle transition:

- temporary memories and deadlines can expire;
- low-value stale records can be archived;
- contradictory decisions can be superseded non-destructively;
- users can pin, archive, delete, export, or erase project memory;
- a reflection pass can consolidate duplicates and derive higher-level
  insights without claiming to retrain the model.

Before persistence, text passes through pattern-based secret detection and
redaction. The same boundary applies to stored turn snapshots. This is a useful
guardrail, not a promise that pattern matching catches every possible secret;
the safer rule remains not to paste credentials into a conversation.

## Testing the claim instead of marketing it

Memory products are easy to demo selectively. A single successful recall says
very little about stale-memory leakage, budget discipline, or behavior across
different scenarios.

I built a 24-scenario diagnostic that runs both a memory-enabled path and a
no-memory baseline. It reports:

- strict answer checks;
- whether the target fact reached assembled context;
- outdated-memory and privacy failures;
- context reduction compared with replaying history;
- retrieval and end-to-end latency.

The evaluation dashboard reads the report generated by the running build. It
does not display fixed “AI improvement” numbers. I also added an automated
backend suite, frontend production build, dependency audits, Docker validation,
and GitHub Actions CI.

One lesson arrived through a failed scenario. A fixture intended to test theme
preference contained the phrase “never dark mode.” A strict evaluator treated
the word “dark” as a leaked stale preference even though it appeared inside a
negation. The result looked like a model failure, but the fixture itself was
ambiguous. I replaced it with an unambiguous positive preference and added a
regression assertion for zero outdated-memory errors.

That small bug reinforced a larger point: an evaluation harness is also
software. Its labels, fixtures, and graders require the same skepticism as the
system being evaluated.

## Current status and the evidence I will publish next

At the time of writing, the complete local flow, persistent SQLite mode,
automated tests, offline diagnostic, Docker configuration, and CI are working.
The Qwen client and Alibaba Cloud Tablestore/OSS adapters are implemented.

The remaining release gate is operational evidence: deploy the exact final
commit on Alibaba Cloud, verify Qwen and storage status through the public
health endpoint, test persistence across a restart, and generate the final
model-backed report from that deployment.

I am stating that boundary plainly because “implemented,” “tested locally,” and
“proven in the submitted cloud environment” are different claims.

## Why this can matter beyond one hackathon

Agent memory is becoming infrastructure. Coding assistants, learning tools,
customer-support agents, and team copilots all need continuity, but continuity
without governance creates risk.

A reusable memory layer should answer more than “what is similar to this
query?” It should also answer:

- Is this memory still active?
- Did a newer decision replace it?
- Is it relevant to this user and project?
- Is it important enough to spend context tokens on?
- Is it safe to persist?
- Can the user inspect and reverse the decision?

MemoPilot IQ is my attempt to make those questions first-class. I designed it
as infrastructure rather than a chatbot skin: a service API, a Python SDK,
pluggable storage, observable decisions, and an evaluation path that can be
rerun against the submitted build.

## Try it, inspect it, challenge it

The project is open source under the MIT License:

**Repository:** [github.com/MaharMuavia/memopilot-iq](https://github.com/MaharMuavia/memopilot-iq)

The README includes local setup, architecture, API documentation, testing, the
memory-governance scoring model, and the judge-demo flow.

I would especially value feedback on one question:

> What should an AI assistant be allowed to remember—and what must it be
> designed to forget?

If you build agents, retrieval systems, or AI safety tooling, I would love to
hear how you approach that boundary.

---

*MemoPilot IQ is being built for the Qwen Cloud Global AI Hackathon, Track 1:
MemoryAgent. Final cloud and model-backed evaluation evidence will be linked
after it is generated from the submitted deployment.*
