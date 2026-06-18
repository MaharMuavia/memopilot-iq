# Assets

- `architecture.mmd` — Mermaid source for the system architecture diagram.
- `architecture.svg` — Rendered architecture diagram (vector, viewable on GitHub).
- `architecture.png` *(optional)* — Raster export. Generate with:
  ```bash
  npx -y @mermaid-js/mermaid-cli -i architecture.mmd -o architecture.png
  ```

## Screenshots to add before submission
Capture these from the running app (`npm run dev`) and drop them here:
- `screenshot_chat_trace.png` — Chat + Memory Trace side by side.
- `screenshot_timeline.png` — Memory Timeline with created/superseded events.
- `screenshot_eval.png` — Evaluation Dashboard after running the benchmark.
- `proof_health_alibaba.png`, `proof_tablestore.png`, `proof_oss.png` —
  Alibaba Cloud deployment proof (see `docs/deployment_alibaba.md`).
