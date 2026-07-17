# Submission Readiness — Qwen Cloud Global AI Hackathon

This is the release gate for **MemoPilot IQ · Track 1: MemoryAgent**. It
separates repository work that is complete from live evidence that must still
be produced from the final Alibaba Cloud deployment.

## Deadline and official requirements

- **Deadline:** July 20, 2026 at 2:00 PM Pacific Time (July 21 at 2:00 AM PKT).
- The project must use Qwen models available through Qwen Cloud and must run as
  depicted in the submission.
- The submission needs a public open-source repository, project description,
  architecture diagram, proof of Alibaba Cloud use, a publicly viewable demo
  video, and access to a working website, demo, or test build.
- Keep the video **under three minutes**. The event page says five minutes is
  the maximum, but the official Devpost rules say under three minutes and warn
  that judges need not watch beyond that point. The stricter limit is safer.
- The Qwen Cloud event page also requests a presentation deck.

Official sources: [Qwen Cloud hackathon page](https://www.qwencloud.com/challenge/hackathon)
and [Devpost official rules](https://qwencloud-hackathon.devpost.com/rules).

## Current release gate

| Deliverable | Status | Acceptance check |
|---|---|---|
| Public source repository and MIT license | Ready | Repository is public; LICENSE is visible |
| Setup, architecture, algorithm, and security docs | Ready | A new judge can run local mode from the README |
| Qwen chat, extraction, and embedding integration | Ready in code | Final deployment reports `qwen_configured: true` |
| MemoryAgent lifecycle and transparent trace | Ready | Demo proves recall, supersession, and exclusion of stale memory |
| Automated backend/frontend validation | Ready | Final commit passes tests, build, audits, and Docker config validation |
| Alibaba Cloud deployment | **Blocking** | Public backend is running on Alibaba infrastructure |
| Public working-project URL | **Blocking** | Opens without private credentials and remains available through judging |
| Cloud proof | **Blocking** | Capture `/health`, service URL, and Tablestore/OSS evidence without secrets |
| Final model-backed benchmark | **Blocking** | Run on the deployed commit and download the JSON report |
| Public demo video | **Blocking** | Under 3:00, English or English subtitles, no copyrighted music |
| Presentation deck | **Blocking** | Export the 11-slide outline to PPT/PDF and verify every link |
| Devpost submission | **Blocking** | Add track, description, repository, working URL, video, deck, and optional blog |

“Blocking” means the artifact requires the final cloud environment or the
entrant's account. It must not be represented as completed before evidence is
captured.

## Critical path

Complete these in order so every artifact describes the same build:

1. **Freeze and deploy the final commit.** Use the Alibaba deployment guide and
   configure Qwen Cloud, Tablestore, OSS, CORS, TLS, and a public frontend URL.
2. **Run a cloud smoke test.** Confirm `/health` reports the intended model,
   `qwen_configured: true`, and the actual storage mode. Create a memory,
   restart the service, and verify that the memory persists.
3. **Generate final evidence.** Run the 24-scenario evaluation once on the
   deployed build, download its JSON, and save it under `assets/evaluation/`
   with the UTC date, model, and commit SHA.
4. **Capture judge-facing media.** Take clean screenshots and record the
   documented demo scenario in under three minutes. Never show credentials,
   account numbers, or private console details.
5. **Finish the deck and Devpost page.** Use the presentation outline, add the
   verified benchmark figures and public URL, then test every link in a signed-
   out browser.
6. **Perform a final consistency check.** The video, screenshots, health
   response, benchmark, README, deck, public deployment, and submitted commit
   must agree on model, features, and runtime mode.

## Judge-facing positioning

Lead with this sentence:

> MemoPilot IQ is an auditable memory-governance layer for AI agents: it turns
> conversations into structured memory, retires stale decisions, recalls
> critical constraints inside a hard token budget, and explains every choice.

This positions the project as reusable agent infrastructure rather than a
generic chatbot. The strongest proof sequence is:

1. Cross-session recall solves repeated context loss.
2. A changed decision supersedes the old one without destroying the audit
   trail.
3. The Memory Trace proves why the active decision was selected and why the
   stale one was excluded.
4. The final Qwen-backed evaluation quantifies the behavior against the
   no-memory baseline.

Do not claim production-scale retrieval, completed cloud deployment, or
benchmark superiority beyond the evidence included in the final submission.

## Final go/no-go check

Submit only when all answers are **yes**:

- Does the public URL work in a signed-out browser?
- Does the deployed app persist memory across a service restart?
- Does health show live Qwen configuration and the actual storage backend?
- Is the benchmark JSON generated by the exact submitted commit?
- Is the video public, under three minutes, and easy to understand without
  reading the repository?
- Does the deck contain the architecture, value, technical differentiator,
  verified evidence, limitations, and public links?
- Are all secrets absent from Git history, screenshots, logs, and commands?
- Does Devpost identify **Track 1: MemoryAgent** and link the original public
  repository?
