# Project Directory Tree — gbc-reader-prep

> **Last updated:** GBCR-A7 follow-up (chapter title pages + `--paginate-output`)
> **Annotations reflect:** changes in the A-7 follow-up (chapter title pages, the `--paginate-output` flag, and the "fits on a 400x240 display by construction" clarification) layered on top of the original A-7 delivery. Tags from A-4 and earlier are reset to `[UNCHANGED]`.

## Tree

> Layout assumes `GBC_Reader_Project_Plan.md` lives at the gbc-reader-prep repo root alongside the Python package. If your actual layout keeps the project plan at a higher-level repo (with gbc-reader-prep as a subdirectory under it), move `PROJECT_API.md` and `PROJECT_TREE.md` to the same level as the plan and adjust mental paths accordingly.

```
gbc-reader-prep/
├── .gitignore                                      [UNCHANGED]
├── README.md                                       [UNCHANGED]
├── pyproject.toml                                  [UNCHANGED]
├── GBC_Reader_Project_Plan.md                      [UNCHANGED]
├── PROJECT_API.md                                  [MODIFIED]
├── PROJECT_TREE.md                                 [MODIFIED]
├── docs/
│   ├── a2-findings.md                              [UNCHANGED]
│   └── tickets/
│       ├── A-1.md                                  [UNCHANGED]
│       ├── A-2.md                                  [UNCHANGED]
│       ├── A-3.md                                  [UNCHANGED]
│       ├── A-4.md                                  [UNCHANGED]
│       ├── A-5.md                                  [UNCHANGED]
│       ├── A-6.md                                  [UNCHANGED]
│       └── A-7.md                                  [NEW]
├── src/
│   └── gbc_reader_prep/
│       ├── __init__.py                             [UNCHANGED]
│       ├── cli.py                                  [UNCHANGED]
│       ├── extract.py                              [MODIFIED]
│       ├── chapters.py                             [UNCHANGED]
│       ├── trim.py                                 [UNCHANGED]
│       ├── cover.py                                [UNCHANGED]
│       ├── paginate.py                             [NEW]
│       └── preprocess.py                           [MODIFIED]
└── tests/
    ├── __init__.py                                 [UNCHANGED]
    ├── test_cli.py                                 [UNCHANGED]
    ├── test_chapters.py                            [UNCHANGED]
    ├── test_trim.py                                [UNCHANGED]
    ├── test_cover.py                               [UNCHANGED]
    └── test_paginate.py                            [NEW]
```

## Per-file purpose

- **`.gitignore`** — Standard Python ignores (venv, caches, dist, build artifacts).
- **`README.md`** — Brief install + usage docs.
- **`pyproject.toml`** — Project metadata, hatchling build config, dynamic version, dependencies, pytest config, CLI entry point. No new dependencies in A-7 (pagination is pure stdlib).
- **`GBC_Reader_Project_Plan.md`** — Source of truth for project scope, architecture, hardware decisions, and ticket list. Read first in every new conversation.
- **`PROJECT_API.md`** — Cumulative API reference for the project. Read at start of every ticket; updated at close. A-7 adds `paginate.py`'s full surface and the `--paginate`/`--font-metrics` CLI flags.
- **`PROJECT_TREE.md`** — Current directory layout with per-ticket annotations. Read at start of every ticket; updated at close.
- **`docs/a2-findings.md`** — Findings template for the A-2 acceptance criterion: per-PDF observations from running text extraction on 3 sample PDFs. Still pending fill-in from the user.
- **`docs/tickets/A-1.md`** through **`A-6.md`** — Completion synopses for the corresponding tickets.
- **`docs/tickets/A-7.md`** *(new in A-7)* — Completion synopsis for A-7 (pagination engine).
- **`src/gbc_reader_prep/__init__.py`** — Package marker. Holds `__version__ = "0.1.0"`.
- **`src/gbc_reader_prep/cli.py`** — Top-level CLI. Builds the argparse parser, registers subcommands, dispatches. Unchanged in A-7.
- **`src/gbc_reader_prep/extract.py`** *(modified in A-7)* — Low-level PDF text extraction with PyMuPDF. A-7 adds `extract_text_pages(pdf_path) -> list[str]`, an in-memory per-page text extractor used by the pagination engine (existing `extract_text` file-writer is unchanged).
- **`src/gbc_reader_prep/chapters.py`** — Framework-agnostic chapter detection (outline + heuristic fallback). Unchanged in A-7.
- **`src/gbc_reader_prep/trim.py`** — Front/back matter trimming. Unchanged in A-7; `detect_content_bounds` is reused by `--paginate` to pick default page bounds.
- **`src/gbc_reader_prep/cover.py`** — Cover image extraction. Unchanged in A-7.
- **`src/gbc_reader_prep/paginate.py`** *(new in A-7, modified in the A-7 follow-up)* — Pagination engine: lays out per-page extracted text into fixed-size 400x240 display pages against a `FontMetrics` character grid, enforcing the chapter-start-at-top rule. Follow-up adds `center_line`/`make_title_page` and a blank, horizontally+vertically centered title page inserted ahead of each named chapter's body text in `paginate_chapters`. See `PROJECT_API.md` for the full symbol list.
- **`src/gbc_reader_prep/preprocess.py`** *(modified in A-7, modified again in the A-7 follow-up)* — Handler for the `preprocess` subcommand. A-7 adds `--paginate` (lay out and log a page-count summary) and `--font-metrics` (override the character grid), wired into both the normal run path and `--inspect`. Follow-up adds `--paginate-output` (dump the full laid-out page contents, including chapter title pages, to a `.txt` file for manual review).
- **`tests/__init__.py`** — Empty package marker.
- **`tests/test_cli.py`**, **`tests/test_chapters.py`**, **`tests/test_trim.py`**, **`tests/test_cover.py`** — Unchanged in A-7 / its follow-up.
- **`tests/test_paginate.py`** *(new in A-7, extended in the A-7 follow-up)* — Unit tests for `paginate.py` (font metrics, word-wrap, chapter-start-at-top enforcement, page-range bounds, sanity word-count check, `center_line`/`make_title_page` centering and wrapping) plus CLI integration tests for `--paginate`/`--font-metrics`/`--paginate-output`.

## Excluded from the tree

Generated / hidden / IDE directories: `.venv/`, `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.git/`, `.idea/`, `.pytest_cache/`.
