# MemoPilot IQ — Research Paper

Archived preliminary LaTex draft describing MemoPilot IQ / MemoryOS. It is not
submission-ready: its experimental tables predate the final evaluator and
strict-budget fixes. Regenerate every reported metric and remove the visible
draft notice in `main.tex` before sending it to arXiv, judges, or customers.

## Files
- `main.tex` — the paper source.
- `references.bib` — bibliography.
- `figure_architecture.tex` — Figure 1, the architecture diagram (native TikZ).
- `figure_lifecycle.tex` — Figure 2, the memory lifecycle state machine (TikZ).
  Both are pulled in by `main.tex` via `\input{...}`; no external images needed.
  Upload all four files to Overleaf.

## Build

### Option A — Overleaf (no install)
1. Create a new project on [overleaf.com](https://www.overleaf.com).
2. Upload `main.tex` and `references.bib`.
3. Set the compiler to **pdfLaTeX** (Menu → Compiler). Click **Recompile**.

### Option B — Local (needs a TeX distribution: TeX Live / MiKTeX)
```bash
pdflatex main.tex
bibtex   main
pdflatex main.tex
pdflatex main.tex
```
or, if `latexmk` is available:
```bash
latexmk -pdf main.tex
```

## Before submitting to arXiv
- **Figures.** Done — both figures are native TikZ (vector, scale cleanly,
  match the paper fonts). Edit the `figure_*.tex` files to tweak them.
- **Author/affiliation.** Update the `\author` / `\affil` lines as needed
  (name spelling, ORCID, institution).
- **Numbers.** Do not quote the existing values. Rerun the 24-scenario
  benchmark (`POST /api/eval/run`), the governance ablation
  (`POST /api/eval/ablation`), and the LoCoMo runner
  (`backend/scripts/run_locomo.py`) against the finalized build, then retain
  the raw reports alongside the revised tables.
- **arXiv upload.** Upload `main.tex`, `references.bib`, and both
  `figure_*.tex` files. arXiv runs BibTeX automatically; no need to upload a
  `.bbl` (though you can).
