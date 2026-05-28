# Project Directory Tree — gbc-reader-prep

> **Last updated:** GBCR-A3
> **Annotations reflect:** changes in A-3 only. A-2's `[NEW]` and `[MODIFIED]` tags were reset to `[UNCHANGED]` at the start of A-3 before applying A-3's changes. At the start of A-4, repeat that reset for the tags below before applying A-4's changes.

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
│       └── A-3.md                                  [NEW]
├── src/
│   └── gbc_reader_prep/
│       ├── __init__.py                             [UNCHANGED]
│       ├── cli.py                                  [UNCHANGED]
│       ├── extract.py                              [UNCHANGED]
│       ├── chapters.py                             [NEW]
│       └── preprocess.py                           [MODIFIED]
└── tests/
    ├── __init__.py                                 [UNCHANGED]
    ├── test_cli.py                                 [UNCHANGED]
    └── test_chapters.py                            [NEW]
```

## Per-file purpose

- **`.gitignore`** — Standard Python ignores (venv, caches, dist, build artifacts).
- **`README.md`** — Brief install + usage docs.
- **`pyproject.toml`** — Project metadata, hatchling build config, dynamic version, dependencies, pytest config, CLI entry point. Already includes `pymupdf>=1.27.2.3` from A-2; A-3 reuses it.
- **`GBC_Reader_Project_Plan.md`** — Source of truth for project scope, architecture, hardware decisions, and ticket list. Read first in every new conversation.
- **`PROJECT_API.md`** — Cumulative API reference for the project. Read at start of every ticket; updated at close. A-3 update adds the `chapters` module and the `--show-chapters` flag.
- **`PROJECT_TREE.md`** — Current directory layout with per-ticket annotations. Read at start of every ticket; updated at close.
- **`docs/a2-findings.md`** — Findings template for the A-2 acceptance criterion: per-PDF observations from running text extraction on 3 sample PDFs. Still pending fill-in from the user.
- **`docs/tickets/A-1.md`** — Completion synopsis for A-1 (Python project skeleton). Decisions, conventions established, and hand-off notes.
- **`docs/tickets/A-2.md`** — Completion synopsis for A-2 (PDF text extraction PoC + subcommand layering pattern).
- **`docs/tickets/A-3.md`** *(new in A-3)* — Completion synopsis for A-3 (outline-based chapter detection + `--show-chapters` flag).
- **`src/gbc_reader_prep/__init__.py`** — Package marker. Holds `__version__ = "0.1.0"`.
- **`src/gbc_reader_prep/cli.py`** — Top-level CLI. Builds the argparse parser, registers subcommands, dispatches. Unchanged in A-3.
- **`src/gbc_reader_prep/extract.py`** — Low-level PDF text extraction with PyMuPDF. Single public function `extract_text`. Unchanged in A-3.
- **`src/gbc_reader_prep/chapters.py`** *(new in A-3)* — Framework-agnostic chapter detection from a PDF's outline. Exposes `Chapter` (frozen dataclass), `detect_chapters_from_outline`, `detect_chapters_from_outline_path`, and `top_level_chapters`.
- **`src/gbc_reader_prep/preprocess.py`** *(modified in A-3)* — Handler for the `preprocess` subcommand. A-3 adds the `--show-chapters` flag and the post-extraction chapter-listing block in `run`.
- **`tests/__init__.py`** — Empty package marker.
- **`tests/test_cli.py`** — Smoke tests for the CLI. Unchanged in A-3.
- **`tests/test_chapters.py`** *(new in A-3)* — 10 tests covering outline-based chapter detection, with fixture PDFs built in-test via PyMuPDF's `set_toc`.

## Excluded from the tree

Generated / hidden / IDE directories: `.venv/`, `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.git/`, `.idea/`, `.pytest_cache/`.
