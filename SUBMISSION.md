# MemoPilot IQ — Submission Package

**Qwen Cloud Global AI Hackathon · Track 1: MemoryAgent**

> Naming disclosure: this hackathon project is not affiliated with the separate
> 2026 research system named MemoPilot ([arXiv:2606.08656](https://arxiv.org/abs/2606.08656)).

| Requirement | Status | Submission artifact |
|---|---|---|
| Public, open-source repository | Ready | [MaharMuavia/memopilot-iq](https://github.com/MaharMuavia/memopilot-iq) · [MIT License](LICENSE) |
| Source, assets, and run instructions | Ready | [README](README.md) · [Docker deployment](deploy/README.md) |
| Alibaba Cloud deployment proof | Verified | [Proof gallery](docs/alibaba_cloud_proof.md) · [Tablestore adapter](backend/app/memory/store_alibaba.py) · [Qwen client](backend/app/qwen_client.py) |
| Architecture diagram | Ready | [SVG](assets/architecture.svg) · [architecture guide](docs/architecture.md) |
| Final Qwen evaluation | Verified | [Results](docs/evaluation_results.md) · [raw artifacts](assets/evaluation/) |
| Project description | Ready | [below](#project-description) |
| Track | Ready | **Track 1: MemoryAgent** |
| Public demo video | Linked — verify | [Watch on YouTube](https://youtu.be/UE2h4K_VaL8) · [video script](docs/demo_script.md) |
| Optional blog-post prize | Ready | [AI Agents Don't Need More Memory. They Need Memory Governance.](https://dev.to/muhammad_muavia/ai-agents-dont-need-more-memory-they-need-memory-governance-15ej) |

**Live demo:** [https://47-84-129-218.sslip.io/app](https://47-84-129-218.sslip.io/app)

**Public video demo:** [Watch MemoPilot IQ on YouTube](https://youtu.be/UE2h4K_VaL8)

## Project Description

**MemoPilot IQ** is an auditable memory-governance layer for AI agents. It
turns conversations into structured long-term memories, selects only relevant
and valid context inside a strict token budget, retires stale decisions, and
shows an explainable **Memory Trace** for every answer.

The submitted deployment runs on **Alibaba Cloud ECS** and uses **Qwen Cloud
(DashScope)** for chat, JSON memory extraction, and embeddings. It persists
memories and lifecycle events in **Alibaba Tablestore**, and writes redacted
turn snapshots and evaluation artifacts to **Alibaba OSS**.

### What judges can verify

- Persistent, cross-session memory created automatically from a user message.
- Transparent retrieval: candidates, scores, token budget, injected records,
  and skipped records are visible in Memory Trace.
- Memory lifecycle controls: pin, archive, forget, export, contradiction
  supersession, expiry, and a complete event timeline.
- A public Alibaba Cloud deployment that recalls a memory in a new session.

## Alibaba Cloud Proof

The live deployment was verified with a cross-session memory test:

1. The app stored the user’s final demo label automatically.
2. A new browser session recalled the exact label from Alibaba Tablestore.
3. Memory Trace showed the injected record, scoring components, and context
   budget.

See the [deployment proof gallery](docs/alibaba_cloud_proof.md). The primary
code evidence is the [Alibaba Tablestore adapter](backend/app/memory/store_alibaba.py),
which uses the official `tablestore` SDK, and the
[OSS client](backend/app/storage/oss_client.py).

## How to run locally

```bash
docker compose up --build
```

For detailed setup, testing, environment variables, and the Alibaba ECS deploy
path, see [README.md](README.md) and [deploy/README.md](deploy/README.md).

## Final submission checklist

- [x] Public repository with a detectable MIT license.
- [x] Alibaba Cloud code links, architecture diagram, and proof screenshots.
- [x] Public project URL and text description.
- [x] Track identified as **Track 1: MemoryAgent**.
- [x] Optional published Qwen Cloud build-journey blog post.
- [x] Final Qwen-backed benchmark and ablation from deployed build
  `97b1ff57f36c` with raw JSON evidence.
- [x] Demo video link: [YouTube](https://youtu.be/UE2h4K_VaL8).
- [ ] Verify the video while signed out, then paste its public URL into the
  hackathon submission form.
