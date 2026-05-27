# Project Directory Tree — gbc-reader-prep

> **Last updated:** GBCR-A2 (draft state — A-2 changes not yet applied to repo)
> **Annotations reflect:** changes in A-2 only. Files unchanged in A-2 are tagged `[UNCHANGED]`. At the start of A-3, all `[NEW]` and `[MODIFIED]` tags below should be reset to `[UNCHANGED]` before A-3's changes are applied.

## Tree

> Layout assumes `GBC_Reader_Project_Plan.md` lives at the gbc-reader-prep repo root alongside the Python package. If your actual layout keeps the project plan at a higher-level repo (with gbc-reader-prep as a subdirectory under it), move `PROJECT_API.md` and `PROJECT_TREE.md` to the same level as the plan and adjust mental paths accordingly.

```
gbc-reader-prep/
├── .gitignore                                      [UNCHANGED]
├── README.md                                       [UNCHANGED]
├── pyproject.toml                                  [MODIFIED]
├── GBC_Reader_Project_Plan.md                      [UNCHANGED]
├── PROJECT_API.md                                  [NEW]
├── PROJECT_TREE.md                                 [NEW]
├── docs/
│   ├── a2-findings.md                              [NEW]
│   └── tickets/
│       └── A-1.md                                  [UNCHANGED]
├── src/
│   └── gbc_reader_prep/
│       ├── __init__.py                             [UNCHANGED]
│       ├── cli.py                                  [MODIFIED]
│       ├── extract.py                              [NEW]
│       └── preprocess.py                           [NEW]
└── tests/
    ├── __init__.py                                 [UNCHANGED]
    └── test_cli.py                                 [MODIFIED]
```

## Per-file purpose

- **`.gitignore`** — Standard Python ignores (venv, caches, dist, build artifacts).
- **`README.md`** — Brief install + usage docs.
- **`pyproject.toml`** — Project metadata, hatchling build config, dynamic version, dependencies, pytest config, CLI entry point. A-2 adds `pymupdf>=1.27.2.3` to runtime dependencies.
- **`GBC_Reader_Project_Plan.md`** — Source of truth for project scope, architecture, hardware decisions, and ticket list. Read first in every new conversation.
- **`PROJECT_API.md`** — Cumulative API reference for the project. Read at start of every ticket; updated at close.
- **`PROJECT_TREE.md`** — Current directory layout with per-ticket annotations. Read at start of every ticket; updated at close.
- **`docs/a2-findings.md`** — Findings template for the A-2 acceptance criterion: per-PDF observations from running text extraction on 3 sample PDFs. To be filled in during A-2 close-out.
- **`docs/tickets/A-1.md`** — Completion synopsis for A-1 (Python project skeleton). Narrative record of decisions, conventions established, and hand-off notes.
- **`src/gbc_reader_prep/__init__.py`** — Package marker. Holds `__version__ = "0.1.0"`.
- **`src/gbc_reader_prep/cli.py`** — Top-level CLI. Builds the argparse parser, registers subcommands, dispatches. A-2 adds subparsers wiring and the `preprocess` registration.
- **`src/gbc_reader_prep/extract.py`** *(new in A-2)* — Low-level PDF text extraction with PyMuPDF. Single public function `extract_text`.
- **`src/gbc_reader_prep/preprocess.py`** *(new in A-2)* — Handler for the `preprocess` subcommand. Exposes `add_subparser` and `run`.
- **`tests/__init__.py`** — Empty package marker.
- **`tests/test_cli.py`** — Smoke tests for the CLI. A-1's 4 tests plus a new A-2 test for `preprocess` subcommand wiring.

## Files expected to be created when A-2 closes (not yet in tree)

- **`docs/tickets/A-2.md`** — Completion synopsis for A-2, following the A-1.md pattern (decisions made, hand-off notes, what's deliberately not done yet). When written, add to the tree as `[NEW]` in the same edit that closes the ticket.

## Excluded from the tree

Generated / hidden / IDE directories: `.venv/`, `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.git/`, `.idea/`, `.pytest_cache/`.
