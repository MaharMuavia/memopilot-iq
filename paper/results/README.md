# Reproducible paper results

These JSON files are generated from the current implementation in deterministic
offline mode:

```powershell
cd paper
..\backend\.venv\Scripts\python.exe run_reproducible_eval.py
```

The paper reports only retrieval and governance measurements from this run.
Answer accuracy produced by the offline fallback is retained in
`diagnostic.json` for debugging but is not a language-model result and must not
be cited as one. `manifest.json` records the exact subset used in the paper.

The LoCoMo adapter is available under `backend/app/eval/locomo.py`, but no
LoCoMo number is reported until a complete, versioned run finishes under a
declared protocol.
