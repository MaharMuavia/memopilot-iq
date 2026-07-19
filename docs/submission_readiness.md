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
| Automated backend/frontend validation | Ready | 92 backend tests and the frontend production build pass |
| Alibaba Cloud deployment | Ready | Public backend runs on ECS in `ALIBABA_CLOUD_MODE` |
| Public working-project URL | Ready | [http://47.84.129.218/app](http://47.84.129.218/app) opens without credentials |
| Cloud proof | Ready | [Proof gallery](alibaba_cloud_proof.md) shows automatic creation and cross-session Tablestore recall |
| Architecture diagram | Ready | SVG, Mermaid source, and architecture guide are committed |
| Project description and track | Ready | `SUBMISSION.md` identifies Track 1: MemoryAgent and includes submission copy |
| Optional blog prize | Ready | Published Dev.to build journey is linked from the README and submission package |
| Presentation deck | Ready | Editable deck is committed at `assets/memopilot-iq-hackathon-deck.pptx` |
| Final evaluation evidence | In progress | Comparative evaluator is implemented; commit the raw report from the exact deployed revision before recording |
| Public demo video | **Blocking** | Under 3:00, public, English or English subtitles, no copyrighted music |
| Devpost submission | **Blocking** | Add track, description, repository, working URL, proof code link, architecture, video, and optional blog |

"Blocking" means the artifact requires the entrant's publishing account. It
must not be represented as completed before the public link or form exists.

## Remaining critical path

The repository code and cloud deployment are validated, but the release is not
complete until the final evaluation artifact and entrant-owned media are done:

1. **Capture final evaluation evidence.** Run the comparative evaluator against
   the deployed revision and commit its raw JSON plus a concise summary.
2. **Record the public deployment.** Follow `docs/demo_script.md`, stay under
   three minutes, and never show credentials, account numbers, or cloud-console
   details.
3. **Upload the video publicly.** Use YouTube, Vimeo, or Facebook Video and
   verify playback in a signed-out window.
4. **Complete the submission form.** Add Track 1: MemoryAgent, the project
   description, repository, live URL, Alibaba proof code link, architecture,
   video, and optional blog URL.
5. **Perform a final link check.** Open the form links signed out and confirm
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
