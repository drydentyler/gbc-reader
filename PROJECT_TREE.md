# Project Directory Tree — gbc-reader-prep

> **Last updated:** GBCR-A8 (`.book` file writer)
> **Annotations reflect:** the A-8 delivery (new `book.py` module, `preprocess.py` dispatching to it when `--output` ends in `.book`) layered on top of the A-7 follow-up. Tags from A-7 and earlier are reset to `[UNCHANGED]` except where A-8 directly touched a file.

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
│       ├── A-7.md                                  [UNCHANGED]
│       └── A-8.md                                  [NEW]
├── src/
│   └── gbc_reader_prep/
│       ├── __init__.py                             [UNCHANGED]
│       ├── cli.py                                  [UNCHANGED]
│       ├── extract.py                              [UNCHANGED]
│       ├── chapters.py                             [UNCHANGED]
│       ├── trim.py                                 [UNCHANGED]
│       ├── cover.py                                [UNCHANGED]
│       ├── paginate.py                             [UNCHANGED]
│       ├── book.py                                 [NEW]
│       └── preprocess.py                           [MODIFIED]
└── tests/
    ├── __init__.py                                 [UNCHANGED]
    ├── test_cli.py                                 [UNCHANGED]
    ├── test_chapters.py                            [UNCHANGED]
    ├── test_trim.py                                [UNCHANGED]
    ├── test_cover.py                               [UNCHANGED]
    ├── test_paginate.py                            [UNCHANGED]
    └── test_book.py                                [NEW]
```

## Per-file purpose

- **`.gitignore`** — Standard Python ignores (venv, caches, dist, build artifacts).
- **`README.md`** — Brief install + usage docs.
- **`pyproject.toml`** — Project metadata, hatchling build config, dynamic version, dependencies, pytest config, CLI entry point. No new dependencies in A-7 (pagination is pure stdlib).
- **`GBC_Reader_Project_Plan.md`** — Source of truth for project scope, architecture, hardware decisions, and ticket list. Read first in every new conversation.
- **`PROJECT_API.md`** — Cumulative API reference for the project. Read at start of every ticket; updated at close. A-8 adds `book.py`'s full surface and documents the `.book`-suffix dispatch in `preprocess.run`.
- **`PROJECT_TREE.md`** — Current directory layout with per-ticket annotations. Read at start of every ticket; updated at close.
- **`docs/a2-findings.md`** — Findings template for the A-2 acceptance criterion: per-PDF observations from running text extraction on 3 sample PDFs. Still pending fill-in from the user.
- **`docs/tickets/A-1.md`** through **`A-7.md`** — Completion synopses for the corresponding tickets.
- **`docs/tickets/A-8.md`** *(new in A-8)* — Completion synopsis for A-8 (`.book` file writer).
- **`src/gbc_reader_prep/__init__.py`** — Package marker. Holds `__version__ = "0.1.0"`.
- **`src/gbc_reader_prep/cli.py`** — Top-level CLI. Builds the argparse parser, registers subcommands, dispatches. Unchanged in A-8.
- **`src/gbc_reader_prep/extract.py`** — Low-level PDF text extraction with PyMuPDF. Unchanged in A-8; `extract_text_pages` is reused by `book.build_book`.
- **`src/gbc_reader_prep/chapters.py`** — Framework-agnostic chapter detection (outline + heuristic fallback). Unchanged in A-8; `detect_chapters_path` is reused by `book.build_book`.
- **`src/gbc_reader_prep/trim.py`** — Front/back matter trimming. Unchanged in A-8; `detect_content_bounds` is reused by `book.build_book` to pick default page bounds.
- **`src/gbc_reader_prep/cover.py`** — Cover image extraction. Unchanged in A-8; `book.build_book` calls `render_cover`/`cover_to_base64` directly (not `extract_cover`, to avoid writing a stray `cover.png` next to the source PDF).
- **`src/gbc_reader_prep/paginate.py`** — Pagination engine. Unchanged in A-8; `paginate_chapters` is reused by `book.build_book`.
- **`src/gbc_reader_prep/book.py`** *(new in A-8)* — `.book` file writer. `build_book(pdf_path, ...)` assembles the full manifest dict (schema, title/author, display, cover, chapters, pages); `write_book_path(pdf_path, out_path, ...)` builds and writes it as JSON. See `PROJECT_API.md` for the full symbol list.
- **`src/gbc_reader_prep/preprocess.py`** *(modified in A-8)* — Handler for the `preprocess` subcommand. A-8 adds `_write_book(args)`, dispatched from `run()` when `--output`'s suffix is `.book`: assembles and writes a full `.book` JSON file via `book.write_book_path` instead of the plain `.txt` extraction path. `--extract-cover`/`--show-chapters`/`--paginate` are unaffected (still drive the legacy `.txt`-extraction diagnostics path); `--start-page`/`--end-page`/`--font-metrics` are honored on both paths.
- **`tests/__init__.py`** — Empty package marker.
- **`tests/test_cli.py`**, **`tests/test_chapters.py`**, **`tests/test_trim.py`**, **`tests/test_cover.py`**, **`tests/test_paginate.py`** — Unchanged in A-8.
- **`tests/test_book.py`** *(new in A-8)* — Unit tests for `book.py` (schema fields, title/author metadata fallback, chapter/page id consistency, cover base64 round-trip, `include_cover=False`, start/end page overrides, missing-PDF error) plus CLI integration tests for `preprocess -o *.book` (success, missing PDF, missing font-metrics file, page overrides).

## Excluded from the tree

Generated / hidden / IDE directories: `.venv/`, `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.git/`, `.idea/`, `.pytest_cache/`.
