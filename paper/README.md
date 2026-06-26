# MemoPilot IQ — Research Paper

Submission-ready arXiv preprint (LaTeX) describing the MemoPilot IQ / MemoryOS system.

## Files
- `main.tex` — the paper source.
- `references.bib` — bibliography.
- `figure_architecture.tex` — the architecture diagram (native TikZ, vector).
  Pulled in by `main.tex` via `\input{figure_architecture}`; no external image
  needed.

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
- **Architecture figure.** Done — Figure 1 is a native TikZ diagram in
  `figure_architecture.tex` (vector, scales cleanly, matches the paper fonts).
  No image export needed. Edit that file to tweak it.
- **Author/affiliation.** Update the `\author` / `\affil` lines as needed
  (ORCID, institution).
- **Numbers.** The results in Table 2 are the representative offline-backend
  figures from the system's own benchmark harness (`/api/eval/run`). Re-run the
  benchmark with a live Qwen key and update the table if you want live-model
  numbers; keep the offline note for reproducibility.
- **arXiv upload.** Upload `main.tex` + `references.bib` + the figure. arXiv runs
  BibTeX automatically; no need to upload a `.bbl` (though you can).
