# Repository Assets

- `architecture.mmd` — Mermaid source for the submitted Alibaba Cloud
  architecture.
- `architecture.svg` — canonical vector architecture diagram, rendered directly
  in GitHub and the README.
- `memopilot-iq-hackathon-deck.pptx` — editable 11-slide submission deck.

## Deployment proof screenshots

The images in [`proof/`](proof/) were captured from the public Alibaba Cloud
deployment and intentionally exclude credentials and private console details.

| File | What it proves |
|---|---|
| `proof/01-cloud-memory-retrieval.png` | A scored Alibaba Tablestore memory is injected into the Qwen context. |
| `proof/02-automatic-memory-creation.png` | An explicit user request creates durable memory automatically. |
| `proof/03-cross-session-recall.png` | A new session recalls the automatically created memory from Tablestore. |

See [the full proof narrative](../docs/alibaba_cloud_proof.md).
