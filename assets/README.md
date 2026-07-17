# Assets

- `architecture.mmd` — Mermaid source for the system architecture diagram.
- `architecture.svg` — Canonical rendered architecture diagram (vector, viewable on GitHub).
- `architecture.png` *(legacy optional raster export)* — Regenerate only when a
  platform requires PNG:
  ```bash
  npx -y @mermaid-js/mermaid-cli -i architecture.mmd -o architecture.png
  ```
- `memopilot-iq-hackathon-deck.pptx` — Editable 11-slide submission deck.
  Regenerate it with `python tools/build_submission_deck.py` after changing the
  presentation outline or verified deployment evidence.

## Screenshots to add before submission
Capture these from the running app (`npm run dev`) and drop them here:
- `screenshot_chat_trace.png` — Chat + Memory Trace side by side.
- `screenshot_timeline.png` — Memory Timeline with created/superseded events.
- `screenshot_eval.png` — Evaluation Dashboard after running the benchmark.
- `proof_health_alibaba.png`, `proof_tablestore.png`, `proof_oss.png` —
  Alibaba Cloud deployment proof (see `docs/deployment_alibaba.md`).
