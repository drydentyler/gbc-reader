# Project API Reference — gbc-reader-prep

> **Last updated:** GBCR-A4
> **Current version:** 0.1.0
> **Python floor:** `>=3.11`
> **Scope:** Desktop preprocessor subproject only. Firmware (Epic B+) is a separate codebase and not yet underway.

---

## State of this document

Updated at the close of A-3. Items still marked **⚠ unverified** are
reconstructions from earlier tickets' synopses rather than direct reads
of the corresponding source files in this session. Sanity-check them
against actual code at the start of the next ticket and correct here if
anything differs.

A-3 directly touched `chapters.py` (new), `preprocess.py` (rewritten in
A-3 from A-2's draft), and `test_chapters.py` (new); those entries are
verified-current. `extract.py`, `cli.py`, and `test_cli.py` were not
read in the A-3 session and remain as documented after A-2.

---

## Build configuration

### `pyproject.toml`

- **Build backend:** `hatchling`
- **Dynamic version:** read from `src/gbc_reader_prep/__init__.py` via
  ```toml
  [tool.hatch.version]
  path = "src/gbc_reader_prep/__init__.py"
  ```
- **Pytest config:** `testpaths = ["tests"]`, `addopts = "-ra"` in `[tool.pytest.ini_options]`

### Runtime dependencies

| Package | Pin | Added in |
|---|---|---|
| `pymupdf` | `>=1.27.2.3` | A-2 |

No new runtime dependencies in A-3 — `chapters.py` reuses the existing
`pymupdf` dependency.

### Dev / optional dependencies ⚠ unverified

A-1.md §1 shows `pip install -e ".[dev]"` working, which implies a `[project.optional-dependencies] dev = [...]` group exists. Exact contents not documented — verify in source.

| Package | Pin |
|---|---|
| `pytest` | unpinned ⚠ |

### CLI entry point

```toml
[project.scripts]
gbc-reader-prep = "gbc_reader_prep.cli:main"
```

### Outstanding `pyproject.toml` TODOs (per A-1.md §5)

- `[project].authors` — placeholder
- `[project].license` — `MIT` placeholder, awaiting user confirmation
- `[project.urls].Repository` — placeholder

---

## CLI surface

### `gbc-reader-prep` (top-level)

Single entry point for all preprocessor functionality.

| Flag | Type | Required | Default | Description |
|---|---|---|---|---|
| `--version` | flag | no | — | Print version and exit (argparse `action="version"`) |
| `-v`, `--verbose` | flag | no | `False` | Enable DEBUG-level logging |

When no subcommand is given, prints help and exits 0.

### `gbc-reader-prep preprocess`

Preprocess a PDF into reader-ready output. Currently writes a plain
`.txt` extraction (A-2 behaviour); later tickets evolve the output into
a `.book` file (A-8). The subcommand name does not change as it evolves.

| Argument | Type | Required | Default | Description |
|---|---|---|---|---|
| `pdf` (positional) | `pathlib.Path` | yes | — | Path to the input PDF |
| `-o`, `--output` | `pathlib.Path` | yes | — | Path to the output file (`.txt` during A-2 / A-3) |
| `--show-chapters` | flag | no | `False` | **(A-3, extended A-4)** After extraction, log the chapter list derived from the PDF's outline, falling back to heuristic text matching (`Chapter \d+`, `Prologue`, `Epilogue`, `Introduction`) if the PDF has no outline. Logged at INFO level. Temporary — likely folded into the `inspect` subcommand in A-5. |

Exit codes: `0` success, `2` input file not found, `1` other failure.

---

## Modules

### `src/gbc_reader_prep/__init__.py`

Package marker. Holds the project version (read dynamically by hatchling).

**Constants:**
- `__version__: str = "0.1.0"`
  Bumped only by editing this file (A-1.md §3.2). Do not add a literal `version = "..."` to `[project]` — would conflict with `dynamic = ["version"]`.

### `src/gbc_reader_prep/cli.py` ⚠ signatures reconstructed from A-1.md (unchanged in A-3)

Top-level CLI dispatcher. Builds the argparse parser, registers
subcommand groups, and routes execution to the chosen subcommand's
handler. **Unchanged in A-3** — A-3's `--show-chapters` is an argument
on the existing `preprocess` subparser, added in `preprocess.py`. No
modifications to `cli.py` were required.

**Third-party imports:** none (argparse, logging, sys are stdlib).
**Project imports:**
- `from gbc_reader_prep import __version__`
- `from . import preprocess` (added in A-2)

**Public functions:**

- `configure_logging(verbose: bool = False) -> None`
  Configures the project-wide logger. Root logger name `gbc_reader_prep`, format `%(asctime)s %(levelname)-7s %(name)s: %(message)s`, datefmt `%Y-%m-%d %H:%M:%S`. INFO by default; DEBUG when `verbose=True`.

- `build_parser() -> argparse.ArgumentParser`
  Builds the top-level parser. Adds `--version` and `--verbose`, then creates a subparsers group via `parser.add_subparsers(dest="command", metavar="<command>")` and calls `preprocess.add_subparser(subparsers)`. `required=True` is **not** passed so that `--version` continues to work without a subcommand.

- `main(argv: list[str] | None = None) -> int`
  Entry point. Parses args, calls `configure_logging(args.verbose)`, then dispatches to the chosen subcommand's handler via `getattr(args, "func", None)`. Returns the subcommand's exit code, or 0 when no subcommand is given (prints help).

### `src/gbc_reader_prep/extract.py` (A-2, unchanged in A-3)

Low-level PDF text extraction using PyMuPDF. Framework-agnostic — no argparse, no CLI concerns. Called by `preprocess.run`.

**Third-party imports:**
- `pymupdf`

**Module-level constants:**
- `PAGE_SEPARATOR: bytes = b"\x0c"` — form feed; written between pages in the output file. Lets later code split the file back into pages with `text.split(b"\x0c")`.

**Public functions:**

- `extract_text(pdf_path: Path | str, out_path: Path | str) -> int`
  Opens a PDF, extracts text from every page in PyMuPDF's default `"text"` mode, writes UTF-8 to `out_path` with `PAGE_SEPARATOR` between pages. Returns the page count. Creates parent directories of `out_path` if missing; overwrites an existing file at `out_path`. Logs a warning if any page produces only whitespace (covers scanned-without-OCR case).

  **Raises:**
  - `FileNotFoundError` if `pdf_path` does not exist
  - PyMuPDF exceptions propagate unchanged (corrupt / unsupported PDF)

### `src/gbc_reader_prep/preprocess.py` *(modified in A-3)*

Handler for the `preprocess` subcommand. A-3 adds the `--show-chapters`
flag and the chapter-listing block in `run`. Subcommand shape, exit
codes, and error handling for the extraction step are unchanged from A-2.

**Third-party imports:** none directly (PyMuPDF used transitively via `extract` and `chapters`).
**Project imports:**
- `from .chapters import detect_chapters_from_outline_path` *(new in A-3)*
- `from .extract import extract_text`

**Module-level constants:**
- `SUBCOMMAND: str = "preprocess"`

**Public functions:**

- `add_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser`
  Registers the `preprocess` subcommand on a parent subparsers group. Adds positional `pdf`, required `-o/--output`, and *(A-3)* optional `--show-chapters`. Sets `func=run` via `parser.set_defaults()` so `cli.main` can dispatch.

- `run(args: argparse.Namespace) -> int`
  Subcommand handler. Delegates to `extract_text(args.pdf, args.output)`, then if `args.show_chapters` is set, calls `detect_chapters_path(args.pdf)` *(A-4: outline, falling back to heuristic text matching)* and logs the result. Returns `0` on success, `2` on `FileNotFoundError` (from either step), `1` on any other exception (logged via `logger.exception`).

  Display convention: under `--show-chapters`, page numbers are logged
  as **1-based** (matching what PDF readers show); the `Chapter.start_page`
  values stored in memory remain 0-based.

### `src/gbc_reader_prep/chapters.py` *(modified in A-4)*

Framework-agnostic chapter detection from a PDF's outline / bookmark tree,
plus (A-4) a regex-based heuristic fallback for PDFs with no outline.
No argparse, no CLI concerns.

**Third-party imports:**
- `pymupdf` (imported lazily inside `detect_chapters_from_outline_path`
  so the `Chapter` dataclass and `top_level_chapters` filter can be
  used without paying the pymupdf import cost)

**Public symbols:**

- `Chapter` (frozen dataclass)
  ```python
  @dataclass(frozen=True)
  class Chapter:
      title: str
      start_page: int   # 0-indexed; converted from get_toc's 1-indexed page
      level: int        # 1-indexed; matches PyMuPDF's outline level
  ```
  Immutable and hashable. Suitable for use in sets, dict keys, and
  equality assertions in tests.

- `detect_chapters_from_outline(doc: pymupdf.Document) -> list[Chapter]`
  Reads `doc.get_toc(simple=True)`, converts each entry to a `Chapter`,
  converts page numbers from 1-based to 0-based. Skips entries whose
  page is non-positive (PyMuPDF emits `-1` for outline entries that
  don't resolve to a page) and logs a single summary warning if any
  were dropped. Returns empty list if the PDF has no outline (and logs
  a warning).

- `detect_chapters_from_outline_path(pdf_path: Path | str) -> list[Chapter]`
  Convenience wrapper: opens the PDF, calls
  `detect_chapters_from_outline`, closes the document. Lazily imports
  `pymupdf`.
  **Raises:** `FileNotFoundError` if `pdf_path` does not exist.

- `top_level_chapters(chapters: list[Chapter]) -> list[Chapter]`
  Pure-Python filter — returns only entries with `level == 1`,
  preserving input order. No `pymupdf` dependency.

- `detect_chapters_from_heuristic(doc: pymupdf.Document) -> list[Chapter]` *(A-4)*
  For each page, extracts text via `page.get_text()` and scans its lines
  for the first one matching `_HEURISTIC_PATTERNS` (regexes, anchored to
  line start, case-insensitive: `Chapter \d+`, `Prologue`, `Epilogue`,
  `Introduction`). Each match becomes a `Chapter` at `level=1` with
  `start_page` equal to the page's 0-based index and `title` set to the
  matched line verbatim (stripped, original case preserved). Pages with
  no matching line contribute nothing. Returns an empty list (with a
  logged warning) if no page matches.

- `detect_chapters_from_heuristic_path(pdf_path: Path | str) -> list[Chapter]` *(A-4)*
  Convenience wrapper: opens the PDF, calls
  `detect_chapters_from_heuristic`, closes the document. Lazily imports
  `pymupdf`. **Raises:** `FileNotFoundError` if `pdf_path` does not exist.

- `detect_chapters(doc: pymupdf.Document) -> list[Chapter]` *(A-4)*
  Calls `detect_chapters_from_outline`; if that returns a non-empty list,
  returns it unchanged. Otherwise falls back to
  `detect_chapters_from_heuristic`. This is the function `preprocess.run`
  uses under `--show-chapters`.

- `detect_chapters_path(pdf_path: Path | str) -> list[Chapter]` *(A-4)*
  Path-based wrapper around `detect_chapters`. **Raises:**
  `FileNotFoundError` if `pdf_path` does not exist.

---

## Test layout

### `tests/__init__.py`
Empty package marker.

### `tests/test_cli.py` ⚠ A-1 / A-2 test names not directly read in this session

Smoke tests for the CLI. A-1 ships 4 tests covering the A-1 acceptance criteria (`--version` output, `--verbose` log behavior, package install). A-2 adds at least one test for the `preprocess` subcommand wiring (e.g. `test_preprocess_help_runs`). No additional A-3 tests in this file; A-3's tests live in `tests/test_chapters.py`.

### `tests/test_chapters.py` *(modified in A-4, all 24 tests verified passing)*

Unit tests for `chapters.py`. Fixture PDFs are built in-test via
`pymupdf.open()` + `doc.new_page()` + `doc.set_toc()` (outline fixtures)
or `page.insert_text()` (heuristic-fallback fixtures); no external PDF
files are required. Imports skip gracefully via `pytest.importorskip`
if PyMuPDF isn't installed.

Tests cover (A-3, outline-based):
- Outline detection on a multi-chapter, multi-level fixture
- Empty-outline branch (no chapters returned, warning logged)
- Title whitespace stripping
- 0-vs-1 page indexing conversion correctness
- Preservation of outline order
- Hierarchy `level` field is populated correctly
- `top_level_chapters` filters to level 1
- `top_level_chapters` accepts empty input
- `detect_chapters_from_outline_path` raises `FileNotFoundError` for missing files
- `detect_chapters_from_outline` accepts an open `Document` directly

Tests cover (A-4, heuristic fallback and combined entry point):
- `detect_chapters_from_heuristic` matches `Chapter \d+` lines across pages
- Matches `Prologue` / `Epilogue` named sections
- Case-insensitive matching (`CHAPTER 1`)
- No-match case returns an empty list
- `detect_chapters_from_heuristic_path` raises `FileNotFoundError` for missing files
- `detect_chapters_from_heuristic` accepts an open `Document` directly
- `detect_chapters`/`detect_chapters_path` prefer the outline when present
- `detect_chapters`/`detect_chapters_path` fall back to heuristic matching when there is no outline
- `detect_chapters` accepts an open `Document` directly

---

## Conventions in force

- **Branch naming:** `A-{n}-{kebab-case-description}` (e.g. `A-3-outline-chapter-detection`). Same shape for B/C/D/E epics.
- **Ticket ID format (for git):** `GBCR-A{n}` (and `GBCR-B{n}`, etc.).
- **Commit message format:** Conventional Commits with the ticket ID — `feat(prep): GBCR-A3 <description>`. Body may include `Refs: A-{n}` for grep-ability.
- **Loggers:** `logging.getLogger("gbc_reader_prep.<submodule>")` — or equivalently `logging.getLogger(__name__)` from inside a submodule. All project logs share the `gbc_reader_prep` root for filtering.
- **CLI library:** `argparse` (stdlib) only. No `click`. Subcommands via `parser.add_subparsers()` from a single top-level `gbc-reader-prep` script.
- **Subcommand module shape** *(A-2 §4.4):* `SUBCOMMAND` constant, `add_subparser(subparsers)`, `run(args)`, and `parser.set_defaults(func=run)`. Dispatch via `args.func(args)` in `cli.main`.
- **Library / subcommand layering** *(A-2 §4.1):* library modules (e.g. `extract.py`, `chapters.py`) are framework-agnostic. Argparse / CLI logic lives only in `preprocess.py` (and future sibling subcommand modules). Don't add argparse imports to library modules.
- **Page indexing** *(A-3 §2.2):* internal page numbers are **0-based** throughout the project. The PyMuPDF boundary (which is 1-based for `get_toc()`) is converted once, in `chapters.py`. User-facing log lines under `--show-chapters` show 1-based numbers to match PDF readers.
- **Exit codes** *(A-2 §4.6):* `0` success, `2` file-not-found, `1` other failure. Future subcommand handlers should follow this.
- **Source layout:** `src/` layout (not flat). Run from installed package.
- **Version bumping:** Edit `src/gbc_reader_prep/__init__.py` only.
- **Per-ticket completion synopses:** `docs/tickets/A-{n}.md` (mirror layout for other epics).
- **Cumulative state docs:** `PROJECT_API.md` and `PROJECT_TREE.md` at repo root; read at start of every ticket, updated at close.
- **Test fixture strategy** *(A-3 §2.7):* prefer building fixture PDFs in-test via PyMuPDF over checking real PDFs into the repo.

---

## Verification status

**Directly verified in the A-3 session:**
- `chapters.py` syntax (via `py_compile`) and behaviour (via the test
  suite — 10/10 passing).
- `preprocess.py` syntax (via `py_compile`) and end-to-end behaviour
  (subparser registration, dispatch via `args.func`, success path,
  no-outline path, and missing-file path).
- `pymupdf>=1.27.2.3` resolves to exactly that version when installed
  fresh.
- `Document.get_toc(simple=True)` returns 1-based pages (verified via
  PyMuPDF docs and via test-fixture round-trip).
- `Document.set_toc`, `Document.new_page`, `Document.save`, and the
  no-arg `pymupdf.open()` constructor — all used by the test fixtures
  and observed working.

**Reconstructed from earlier ticket synopses, not verified against source:**
- `cli.py` function signatures (carried forward from A-2 doc).
- `tests/test_cli.py` test names and exact assertions.
- Existence and contents of `[project.optional-dependencies] dev` group.
- `__init__.py` contents beyond `__version__`.
- `extract.py` contents — A-2 drafted but not seen this session.

**Not yet verified anywhere:**
- That A-2's `preprocess` subcommand integration into `cli.py` was
  applied to the user's repo (A-2 was "drafted, not applied").
- That A-2's `extract.py` is present in the user's repo. If A-2 was not
  applied, `preprocess.py`'s `from .extract import extract_text` will
  fail at import time and so will A-3.
- That `pip install -e ".[dev]"` resolves successfully on the user's
  Windows + PyCharm setup with A-1, A-2, and A-3's content combined.
- The A-2 acceptance criterion (extraction against 3 real PDFs with
  findings in `docs/a2-findings.md`).
- The A-3 acceptance criterion against a real bookmarked PDF (synthetic
  fixtures all pass; real-PDF check is recommended).

The next agent should resolve any items above that A-4 touches against
real source, and update this document accordingly. The "code is the
ultimate truth" rule from the ticket prompt applies.
