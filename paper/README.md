# MemoPilot IQ research paper

This directory contains the source and reproducibility artifacts for the
technical report:

> **MemoPilot IQ: Auditable Lifecycle Governance for Persistent Agent Memory**

The report is written as a mechanism and systems paper. It does not reuse the
archived Qwen, GPT-4o, LoCoMo, latency, or 98% context-reduction claims that
predated the current evaluator. Its numerical claims come only from the current
deterministic diagnostic and ablation under `results/`.

## Publication status

The report is suitable for publication as an open technical report after the
authors approve the final PDF and authorship metadata. It is **not yet a strong
empirical conference submission**: it has no complete external benchmark, no
versioned live-Qwen answer evaluation, no human evaluation, and no scale or
security study. The paper states those limits directly.

Before any external submission, every listed author must confirm:

- name spelling and order;
- contribution and consent to publication;
- affiliation and corresponding-author address;
- conflicts of interest and venue-specific disclosure requirements.

No authorship or equal-contribution claim should be inferred from repository
access alone.

## Files

- `main.tex` - paper source.
- `references.bib` - references checked against primary publication pages.
- `figure_architecture.tex` - native TikZ architecture figure.
- `figure_lifecycle.tex` - native TikZ lifecycle figure.
- `run_reproducible_eval.py` - credential-free diagnostic generator.
- `results/diagnostic.json` - full current diagnostic output.
- `results/ablation.json` - current one-factor ablation output.
- `results/manifest.json` - exact values cited by the paper and values excluded
  from publication claims.
- `../output/pdf/memopilot-iq-research-paper.pdf` - compiled and visually
  inspected publication artifact.

## Regenerate the reported evidence

From the repository root on Windows:

```powershell
cd paper
..\backend\.venv\Scripts\python.exe run_reproducible_eval.py
```

The script blanks all supported provider keys before importing application
configuration, uses an isolated temporary SQLite database, and removes the
database when the run finishes. The offline answer fields are test-double
output and are deliberately excluded from the paper.

## Build the PDF

### Overleaf

1. Create a blank project at [overleaf.com](https://www.overleaf.com/).
2. Upload `main.tex`, `references.bib`, `figure_architecture.tex`, and
   `figure_lifecycle.tex`.
3. Select **pdfLaTeX** and compile.

### Local TeX installation

```powershell
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

If `latexmk` is available:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

With Tectonic:

```powershell
tectonic -X compile main.tex
```

## Final submission gate

- Build the PDF from a clean directory and resolve every warning about missing
  references, citations, or overfull content.
- Inspect every rendered page at normal zoom and on a mobile-sized viewer.
- Confirm the title, author list, affiliation, contact address, and date.
- Keep `results/manifest.json` with the submitted source archive.
- Add any live-model or LoCoMo result only after saving the complete raw output,
  provider configuration, prompts, failures, and source commit.
- Follow the target venue's policy for disclosure of language or editing tools;
  do not claim human-only authorship if the venue requires disclosure.
