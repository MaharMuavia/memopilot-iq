# Submission Readiness - Qwen Cloud Global AI Hackathon

This is the release gate for **MemoPilot IQ - Track 1: MemoryAgent**. It
separates completed repository and cloud work from artifacts that require the
entrant's publishing account.

## Deadline and official requirements

- **Deadline:** July 20, 2026 at 2:00 PM Pacific Time (July 21 at 2:00 AM PKT).
- The project must use Qwen models available through Qwen Cloud and run as
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
| Public source repository and MIT license | Ready | GitHub reports the repository as public with a detected MIT license |
| Setup, architecture, algorithm, and security docs | Ready | A new judge can run local mode from the README |
| Qwen chat, extraction, and embedding integration | Ready | Public health reports Qwen configured and online |
| MemoryAgent lifecycle and transparent trace | Ready | Public demos prove recall, supersession, and stale-memory exclusion |
| Automated backend/frontend validation | Ready | 101 backend tests and the frontend production build pass |
| Alibaba Cloud deployment | Ready | Public backend runs on ECS in `ALIBABA_CLOUD_MODE` |
| Public working-project URL | Ready | [HTTPS deployment](https://47-84-129-218.sslip.io/app) opens without credentials and returns HSTS |
| Cloud proof | Ready | [Proof gallery](alibaba_cloud_proof.md) shows automatic creation and cross-session Tablestore recall |
| Architecture diagram | Ready | SVG, Mermaid source, and architecture guide are committed |
| Project description and track | Ready | `SUBMISSION.md` identifies Track 1: MemoryAgent and includes submission copy |
| Optional blog prize | Ready | Published Dev.to build journey is linked from the README and submission package |
| Presentation deck | Ready | Editable deck is committed at `assets/memopilot-iq-hackathon-deck.pptx` |
| Final evaluation evidence | Ready | [Qwen report and ablation](evaluation_results.md) embed deployed SHA `97b1ff57f36c`; provider online, zero fallbacks |
| Public demo video | Linked — verify | [YouTube demo](https://youtu.be/UE2h4K_VaL8); verify public playback, duration, captions, and no copyrighted music before submitting |
| Devpost submission | **Blocking** | Add track, description, repository, working URL, proof code link, architecture, video, and optional blog |

"Blocking" means the artifact requires the entrant's publishing account. It
must not be represented as completed before the public link or form exists.

## Remaining critical path

The repository code, cloud deployment, and evaluation evidence are ready. The
demo-video link is included; the remaining entrant-owned actions are validating
its public playback and completing the submission form:

1. **Verify the public video.** Open [the YouTube demo](https://youtu.be/UE2h4K_VaL8)
   in a signed-out window. Confirm it meets the event's duration and language
   requirements and exposes no credentials, account numbers, or cloud-console
   details.
2. **Complete the submission form.** Add Track 1: MemoryAgent, the project
   description, repository, live URL, Alibaba proof code link, architecture,
   video, and optional blog URL.
3. **Perform a final link check.** Open the form links signed out and confirm
   the repository still shows the MIT license and latest `main` commit.

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
4. The Qwen-backed evaluation provides supplementary evidence against
   no-memory, raw full-history, and model-generated history-summary baselines.

Do not claim production-scale retrieval or benchmark superiority beyond the
evidence included in the final submission. The Alibaba Cloud deployment claim
is supported by the [public proof gallery](alibaba_cloud_proof.md) and the
source-level [Tablestore adapter](../backend/app/memory/store_alibaba.py).

## Final go/no-go check

Submit only when all answers are **yes**:

- Does the public URL work in a signed-out browser?
- Does the deployed app persist memory across a service restart?
- Does health show live Qwen configuration and the actual storage backend?
- Is the video public, under three minutes, and easy to understand without
  reading the repository?
- Does the deck contain the architecture, value, technical differentiator,
  verified evidence, limitations, and public links?
- Are all secrets absent from Git history, screenshots, logs, and commands?
- Does Devpost identify **Track 1: MemoryAgent** and link the original public
  repository?
