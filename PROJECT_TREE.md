# Project Directory Tree — gbc-reader-prep

> **Last updated:** GBCR-A4
> **Annotations reflect:** changes in A-4 only. A-3's `[NEW]` and `[MODIFIED]` tags were reset to `[UNCHANGED]` at the start of A-4 before applying A-4's changes. At the start of A-5, repeat that reset for the tags below before applying A-5's changes.

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
│       └── A-4.md                                  [NEW]
├── src/
│   └── gbc_reader_prep/
│       ├── __init__.py                             [UNCHANGED]
│       ├── cli.py                                  [UNCHANGED]
│       ├── extract.py                              [UNCHANGED]
│       ├── chapters.py                             [MODIFIED]
│       └── preprocess.py                           [MODIFIED]
└── tests/
    ├── __init__.py                                 [UNCHANGED]
    ├── test_cli.py                                 [UNCHANGED]
    └── test_chapters.py                            [MODIFIED]
```

## Per-file purpose

- **`.gitignore`** — Standard Python ignores (venv, caches, dist, build artifacts).
- **`README.md`** — Brief install + usage docs.
- **`pyproject.toml`** — Project metadata, hatchling build config, dynamic version, dependencies, pytest config, CLI entry point. Already includes `pymupdf>=1.27.2.3` from A-2; A-3 reuses it.
- **`GBC_Reader_Project_Plan.md`** — Source of truth for project scope, architecture, hardware decisions, and ticket list. Read first in every new conversation.
- **`PROJECT_API.md`** — Cumulative API reference for the project. Read at start of every ticket; updated at close. A-4 update adds `detect_chapters_from_heuristic`, `detect_chapters`, and their path wrappers, and updates the `--show-chapters` flag description.
- **`PROJECT_TREE.md`** — Current directory layout with per-ticket annotations. Read at start of every ticket; updated at close.
- **`docs/a2-findings.md`** — Findings template for the A-2 acceptance criterion: per-PDF observations from running text extraction on 3 sample PDFs. Still pending fill-in from the user.
- **`docs/tickets/A-1.md`** — Completion synopsis for A-1 (Python project skeleton). Decisions, conventions established, and hand-off notes.
- **`docs/tickets/A-2.md`** — Completion synopsis for A-2 (PDF text extraction PoC + subcommand layering pattern).
- **`docs/tickets/A-3.md`** — Completion synopsis for A-3 (outline-based chapter detection + `--show-chapters` flag).
- **`docs/tickets/A-4.md`** *(new in A-4)* — Completion synopsis for A-4 (regex heuristic chapter-detection fallback).
- **`src/gbc_reader_prep/__init__.py`** — Package marker. Holds `__version__ = "0.1.0"`.
- **`src/gbc_reader_prep/cli.py`** — Top-level CLI. Builds the argparse parser, registers subcommands, dispatches. Unchanged in A-4.
- **`src/gbc_reader_prep/extract.py`** — Low-level PDF text extraction with PyMuPDF. Single public function `extract_text`. Unchanged in A-4.
- **`src/gbc_reader_prep/chapters.py`** *(modified in A-4)* — Framework-agnostic chapter detection. A-4 adds `detect_chapters_from_heuristic` (regex matching on page text for `Chapter \d+`, `Prologue`, `Epilogue`, `Introduction`), `detect_chapters_from_heuristic_path`, and combined `detect_chapters`/`detect_chapters_path` helpers that try the outline first and fall back to the heuristic.
- **`src/gbc_reader_prep/preprocess.py`** *(modified in A-4)* — Handler for the `preprocess` subcommand. A-4 switches `--show-chapters` from the outline-only lookup to the combined `detect_chapters_path` (outline, falling back to heuristic).
- **`tests/__init__.py`** — Empty package marker.
- **`tests/test_cli.py`** — Smoke tests for the CLI. Unchanged in A-4.
- **`tests/test_chapters.py`** *(modified in A-4)* — Adds tests for `detect_chapters_from_heuristic` (chapter/prologue/epilogue/introduction matching, case-insensitivity, no-match case, missing file, direct `Document` entry point) and for the combined `detect_chapters`/`detect_chapters_path` fallback behaviour.

## Excluded from the tree

Generated / hidden / IDE directories: `.venv/`, `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.git/`, `.idea/`, `.pytest_cache/`.
