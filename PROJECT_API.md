# Project API Reference — gbc-reader-prep

> **Last updated:** GBCR-A7
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
| `-o`, `--output` | `pathlib.Path` | no (required unless `--inspect`) | — | Path to the output file (`.txt` during A-2 / A-3) |
| `--show-chapters` | flag | no | `False` | **(A-3, extended A-4)** After extraction, log the chapter list derived from the PDF's outline, falling back to heuristic text matching (`Chapter \d+`, `Prologue`, `Epilogue`, `Introduction`) if the PDF has no outline. Logged at INFO level. |
| `--inspect` | flag | no | `False` | **(A-5)** Dry run: detect chapters and the proposed main-content page range (trimming detected back matter — Appendix/Notes/Bibliography/Index/About the Author/Acknowledg(e)ments), log a report, and exit without writing any output file. `--output` is not required with this flag. |
| `--start-page` | `int` | no | `None` | **(A-5)** Override the auto-detected main-content start page (0-indexed). Works with or without `--inspect`. |
| `--end-page` | `int` | no | `None` | **(A-5)** Override the auto-detected main-content end page (0-indexed, inclusive). Works with or without `--inspect`. |
| `--extract-cover` | flag | no | `False` | **(A-6)** After extraction, render the PDF's first page as a cover image: downscale to 400x240 and apply 1-bit Floyd-Steinberg dithering. Saved as `cover.png` in the same directory as `--output`. |
| `--paginate` | flag | no | `False` | **(A-7)** Lay out the detected main-content text into 400x240 display pages and log the resulting page count (overall and per-chapter), for manual sanity-checking. Works with or without `--inspect`; uses the same `--start-page`/`--end-page` bounds. |
| `--font-metrics` | `pathlib.Path` | no | `None` | **(A-7)** Path to a JSON font metrics file (`{"char_width_px": <int>, "line_height_px": <int>}`) used by `--paginate` to compute characters-per-line and lines-per-page. Defaults to a placeholder 6x10px grid (`paginate.DEFAULT_FONT_METRICS`) until the firmware's real font (B-4) is finalized. |
| `--paginate-output` | `pathlib.Path` | no | `None` | **(A-7)** Used with `--paginate`. Path to a `.txt` file to write the full laid-out page contents (one fixed-width block per display page — including chapter title pages, marked `[TITLE PAGE]` — preceded by a header naming the 1-based page number and chapter), for manual review of where page/chapter breaks and title pages actually fall. |

Exit codes: `0` success, `2` input file not found (or missing `-o/--output` when `--inspect` is absent, or `--font-metrics` file not found), `1` other failure.

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

### `src/gbc_reader_prep/extract.py` *(modified in A-7)*

Low-level PDF text extraction using PyMuPDF. Framework-agnostic — no argparse, no CLI concerns. Called by `preprocess.run` and (A-7) by `paginate.paginate_path`.

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

- `extract_text_pages(pdf_path: Path | str) -> list[str]` *(new in A-7)*
  In-memory counterpart to `extract_text`: opens the PDF and returns a list of per-page text (0-indexed, document order), with no file I/O and no page separator. Used by `paginate.paginate_path` so the pagination engine doesn't have to re-parse a form-feed-delimited `.txt` file.
  **Raises:** `FileNotFoundError` if `pdf_path` does not exist.

### `src/gbc_reader_prep/preprocess.py` *(modified in A-7)*

Handler for the `preprocess` subcommand. A-3 adds the `--show-chapters`
flag and the chapter-listing block in `run`. A-6 adds the
`--extract-cover` flag. A-7 adds `--paginate` and `--font-metrics`,
wired into both `run` (the normal extraction path) and `_report_trim`
(the `--inspect` dry-run path). Subcommand shape, exit codes, and error
handling for the extraction step are unchanged from A-2.

**Third-party imports:** none directly (PyMuPDF/Pillow used transitively via `extract`, `chapters`, `cover`, and `paginate`).
**Project imports:**
- `from .chapters import detect_chapters_path`
- `from .cover import extract_cover`
- `from .extract import extract_text, extract_text_pages` *(`extract_text_pages` new in A-7)*
- `from .paginate import DEFAULT_FONT_METRICS, FontMetrics, load_font_metrics, paginate_chapters` *(new in A-7)*
- `from .trim import detect_content_bounds`

**Module-level constants:**
- `SUBCOMMAND: str = "preprocess"`

**Public functions:**

- `add_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser`
  Registers the `preprocess` subcommand on a parent subparsers group. Adds positional `pdf`, required `-o/--output`, optional `--show-chapters`, `--inspect`, `--start-page`/`--end-page`, `--extract-cover`, and *(A-7)* `--paginate`/`--font-metrics`. Sets `func=run` via `parser.set_defaults()` so `cli.main` can dispatch.

- `run(args: argparse.Namespace) -> int`
  Subcommand handler. Delegates to `extract_text(args.pdf, args.output)`, then if `args.extract_cover` is set, calls `extract_cover(args.pdf, args.output.parent)` to render and save `cover.png`, then if `args.show_chapters` is set, calls `detect_chapters_path(args.pdf)` (outline, falling back to heuristic text matching) and logs the result, then *(A-7)* if `args.paginate` is set, resolves font metrics (`_load_font_metrics`), detects chapters and content bounds, and calls `_report_pagination` to log a page-count summary. Returns `0` on success, `2` on `FileNotFoundError` (from any step, including a missing `--font-metrics` file), `1` on any other exception (logged via `logger.exception`).

  Display convention: under `--show-chapters`, page numbers are logged
  as **1-based** (matching what PDF readers show); the `Chapter.start_page`
  values stored in memory remain 0-based.

**Private helpers** *(new in A-7)*:

- `_load_font_metrics(args: argparse.Namespace) -> FontMetrics`
  Returns `DEFAULT_FONT_METRICS` if `args.font_metrics` is `None`, otherwise loads and returns `load_font_metrics(args.font_metrics)`. **Raises:** `FileNotFoundError` if the given path doesn't exist (caught by both call sites and mapped to exit code `2`).

- `_report_pagination(pdf_path: Path, chapters: list[Chapter], start_page: int, end_page: int, font_metrics: FontMetrics, paginate_output: Path | None = None) -> None`
  Calls `extract_text_pages(pdf_path)` and `paginate_chapters(...)`, then logs (INFO level) the total page count for the given bounds and a per-chapter page-count breakdown (`Chapter <id>: <n> page(s)`, sorted by chapter id, counting each chapter's title page in its total). If `paginate_output` is given, also calls `_write_paginate_output(...)` to dump the full laid-out page contents and logs the output path.

- `_write_paginate_output(path: Path, pages: list[Page], chapters: list[Chapter]) -> None`
  Writes one fixed-width block per page to `path` (lines as-is, including blank padding), preceded by a header: `===== Page <n> (chapter <id>: '<title>')[ [TITLE PAGE]] =====`. The `[TITLE PAGE]` suffix is appended when `page.is_title_page` is `True`. Resolves `<title>` against the same in-range, `start_page`-sorted chapter subset (with the single-fallback-chapter rule) that `paginate_chapters` itself uses to assign `Page.chapter_id` — not the raw, unfiltered `chapters` list — so titles line up correctly even when chapters were trimmed/reordered by content bounds.

- `_report_trim(args: argparse.Namespace) -> int` *(modified in A-7)*
  Unchanged `--inspect` behavior (detect chapters + content bounds, apply overrides, log report), plus: if `args.paginate` is set, resolves font metrics and calls `_report_pagination` with the same bounds used in the trim report, before returning. Still writes no output file.

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

### `src/gbc_reader_prep/trim.py` *(new in A-5)*

Front/back matter trimming. Framework-agnostic — no argparse, no CLI
concerns, no PyMuPDF import (operates only on `Chapter` records and a
page count).

**Public symbols:**

- `TrimResult` (frozen dataclass): `start_page: int`, `end_page: int`
  (inclusive), `back_matter_title: str | None`,
  `back_matter_start_page: int | None`.

- `detect_back_matter_chapter(chapters: list[Chapter]) -> Chapter | None`
  Returns the earliest chapter (by `start_page`) whose title matches a
  back-matter pattern (`Appendix`, `Notes`, `Bibliography`, `Index`,
  `About the Author`, `Acknowledgments`/`Acknowledgements`; all
  case-insensitive, anchored to the start of the title). `None` if no
  chapter matches.

- `detect_content_bounds(chapters: list[Chapter], page_count: int) -> TrimResult`
  `start_page` is the first detected chapter's start page (or `0` if no
  chapters). `end_page` is `page_count - 1` unless a back-matter chapter
  is detected *after* `start_page`, in which case it is the page
  immediately before that chapter. A back-matter match at or before
  `start_page` (e.g. a heuristic false positive on the very first
  detected chapter) is ignored, so the whole book is never trimmed away.
  **Raises:** `ValueError` if `page_count < 1`.

### `src/gbc_reader_prep/cover.py` *(new in A-6)*

Cover image extraction. Framework-agnostic — no argparse, no CLI
concerns. Called by `preprocess.run` under `--extract-cover`.

**Third-party imports:**
- `pymupdf`
- `PIL.Image` (Pillow)

**Module-level constants:**
- `COVER_WIDTH: int = 400`, `COVER_HEIGHT: int = 240` — target display resolution.
- `_RENDER_ZOOM: float = 2.0` — PyMuPDF render zoom factor applied before downscaling, so the Lanczos resize + dither has real detail to work with instead of upscaled blur.

**Public functions:**

- `render_cover(pdf_path: Path | str) -> PIL.Image.Image`
  Opens the PDF, renders page `0` via `page.get_pixmap(matrix=...)` at `_RENDER_ZOOM`, converts to grayscale, resizes to `(COVER_WIDTH, COVER_HEIGHT)` with `Image.LANCZOS`, then converts to mode `"1"` (Pillow's default 1-bit conversion applies Floyd-Steinberg dithering). Returns the dithered image.
  **Raises:** `FileNotFoundError` if `pdf_path` does not exist; `ValueError` if the PDF has zero pages; PyMuPDF exceptions propagate unchanged.

- `cover_to_base64(image: PIL.Image.Image) -> str`
  Encodes the image as PNG in memory and returns a base64 ASCII string. No file I/O.

- `extract_cover(pdf_path: Path | str, out_dir: Path | str) -> tuple[Path, str]`
  Calls `render_cover`, saves the result as `out_dir / "cover.png"` (creating `out_dir` if missing), and returns `(cover_path, cover_to_base64(image))`. This is the function `preprocess.run` calls under `--extract-cover`, and the function A-8's `.book` writer should call to populate the `cover_png_base64` field.

### `src/gbc_reader_prep/paginate.py` *(new in A-7)*

Pagination engine. Framework-agnostic — no argparse, no CLI concerns. Lays
out per-page extracted text into fixed-size 400x240 display pages against
a fixed-width character grid (`FontMetrics`), enforcing the rule that a
chapter's first page always begins with that chapter's first line at the
top of the display.

**Third-party imports:** none directly (lazily imports `pymupdf`/etc. transitively via `chapters`/`extract`/`trim` inside `paginate_path` only).
**Project imports:**
- `from .chapters import Chapter` (module level)
- `from .chapters import detect_chapters_path`, `from .extract import extract_text_pages`, `from .trim import detect_content_bounds` (lazily, inside `paginate_path`)

**Module-level constants:**
- `DISPLAY_WIDTH: int = 400`, `DISPLAY_HEIGHT: int = 240` — target display resolution, matching `cover.py`'s constants.
- `DEFAULT_FONT_METRICS: FontMetrics = FontMetrics(char_width_px=6, line_height_px=10)` — placeholder 6x10px monospace grid, chosen to land near the ~250 words/page acceptance-criterion ballpark. **Must be replaced** with values matching the real firmware font once B-4 (custom bitmap font) lands; pass real values via `--font-metrics` / `load_font_metrics` in the meantime. See project plan Q7.

**Public symbols:**

- `FontMetrics` (frozen dataclass): `char_width_px: int`, `line_height_px: int`. Pixel dimensions of one fixed-width character cell.

- `Page` (frozen dataclass): `chapter_id: int`, `lines: list[str]`, `is_title_page: bool = False` *(`is_title_page` new in A-7 follow-up)*. `chapter_id` is a 0-based index into the in-range chapter list (intended to line up with the `.book` schema's `chapters[].id` once A-8 writes it). `lines` always has exactly `lines_per_page(...)` entries — short pages are padded with empty strings. `is_title_page` is `True` for the blank chapter-title page produced by `make_title_page` and inserted by `paginate_chapters`, `False` for body-text pages.

- `load_font_metrics(path: Path | str) -> FontMetrics`
  Reads `{"char_width_px": <int>, "line_height_px": <int>}` from a JSON file. **Raises:** `FileNotFoundError` if `path` does not exist.

- `chars_per_line(font_metrics: FontMetrics, display_width: int = 400) -> int`
  `max(1, display_width // font_metrics.char_width_px)`.

- `lines_per_page(font_metrics: FontMetrics, display_height: int = 240) -> int`
  `max(1, display_height // font_metrics.line_height_px)`.

- `wrap_text(text: str, max_chars: int) -> list[str]`
  Greedy word-wrap. Collapses all whitespace (including the extracted PDF text's internal newlines) and rejoins words with single spaces. A single word longer than `max_chars` is hard-split across multiple lines rather than overflowing. Returns `[]` for blank input.

- `center_line(text: str, width: int) -> str` *(new in A-7 follow-up)*
  Centers `text` within a line of `width` characters using spaces (left gets the smaller half of an odd-length pad). If `text` is at least as long as `width`, truncates to `width` instead of overflowing.

- `make_title_page(chapter_id: int, title: str, font_metrics: FontMetrics = DEFAULT_FONT_METRICS, display_width: int = 400, display_height: int = 240) -> Page` *(new in A-7 follow-up)*
  Builds a blank chapter title page with `title` centered both horizontally and vertically. Word-wraps `title` (via `wrap_text`) if it doesn't fit one line, clamps to `lines_per_page(...)` lines, then centers that whole block of lines vertically (splitting blank padding above/below, extra row going below on an odd split) and centers each line horizontally (via `center_line`). All other lines on the page are blank. Returns a `Page` with `is_title_page=True`.

- `strip_chapter_heading(text: str, title: str) -> str` *(new in A-7 follow-up)*
  Collapses `text`'s whitespace to single spaces, then repeatedly strips, from the start, any combination (in either order) of a known heading-prefix pattern (`Chapter N`, `Part N`/roman numeral, `Section N`, `Prologue`, `Epilogue`, `Introduction`; case-insensitive) and/or a literal restatement of `title` (case-insensitive), until neither matches any more. Used so a chapter's body text doesn't visibly repeat the heading already shown on its `make_title_page` title page. No-op (aside from whitespace collapsing) if no heading match is found at the start.

- `paginate_chapters(page_texts: list[str], chapters: list[Chapter], font_metrics: FontMetrics = DEFAULT_FONT_METRICS, display_width: int = 400, display_height: int = 240, start_page: int = 0, end_page: int | None = None) -> list[Page]`
  Core layout function. Groups chapters whose `start_page` falls in `[start_page, end_page]` (sorted by `start_page`; if none fall in range, treats the whole range as one unnamed chapter), concatenates each chapter's page texts, *(A-7 follow-up)* strips a leading heading restatement via `strip_chapter_heading(...)` when the chapter has a non-blank title, word-wraps to `chars_per_line(...)`, and chunks into pages of `lines_per_page(...)` lines. Before starting each chapter's text, flushes (and blank-pads) any non-empty page buffer left over from the previous chapter — this is what enforces the chapter-start-at-top rule. *(A-7 follow-up)* Immediately after that flush, if the chapter's title is non-blank, inserts a `make_title_page(...)` page (with that chapter's `chapter_id`) before its body text; the synthetic single-chapter fallback (blank title) gets no title page (and no heading-stripping). `end_page` defaults to `len(page_texts) - 1`.

- `paginate_path(pdf_path: Path | str, font_metrics: FontMetrics = DEFAULT_FONT_METRICS, display_width: int = 400, display_height: int = 240, start_page: int | None = None, end_page: int | None = None) -> list[Page]`
  Path-based convenience wrapper: detects chapters (`detect_chapters_path`), extracts per-page text (`extract_text_pages`), and — if `start_page`/`end_page` are omitted — auto-detects main-content bounds via `detect_content_bounds`. This is the function later tickets (A-8's `.book` writer) should call directly.
  **Raises:** `FileNotFoundError` if `pdf_path` does not exist.

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

### `tests/test_paginate.py` *(new in A-7, extended in A-7 follow-up; 33 tests verified passing)*

Unit tests for `paginate.py`, plus CLI integration via `main()`. Fixture
PDFs are built in-test via `pymupdf.open()` + `doc.new_page()` +
`page.insert_text()` + `doc.set_toc()`; no external PDF files required.

Tests cover:
- `chars_per_line`/`lines_per_page` arithmetic, including clamping to 1
- `wrap_text`: basic word wrap, hard-splitting an over-long word, blank
  input, whitespace collapsing
- `load_font_metrics`: JSON round-trip, missing-file `FileNotFoundError`
- `center_line`: even/odd padding split, truncation when text is too long
- `make_title_page`: title centered both horizontally (full line width,
  text centered within it) and vertically (single non-blank line/block
  roughly in the middle of the page), and word-wrapping a too-long title
  across multiple centered lines
- `strip_chapter_heading`: stripping a `Chapter N <title>` restatement,
  stripping a `Part N <title>` restatement with trailing junk text
  preserved after it, leaving unrelated text unchanged (aside from
  whitespace collapsing), and stripping a known prefix pattern even with
  a blank title
- `paginate_chapters`: no-chapters fallback to a single chapter (no title
  page emitted for the blank-title fallback), blank-line padding on a
  short final page, chapter-start-at-top enforcement (a title page plus
  the short chapter's leftover body page are both flushed before the next
  chapter's title page begins), a chapter's body text not repeating its
  own heading (already shown on its title page), `start_page`/`end_page`
  bounds excluding out-of-range chapters (including their title pages),
  and a sanity check that ~50,000 words land in the acceptance criterion's
  ballpark (100-400 pages) under the default font metrics
- `paginate_path`: end-to-end against a fixture PDF, missing-file
  `FileNotFoundError`
- CLI `--paginate` flag logs a page-count summary (both with `-o/--output`
  and combined with `--inspect`)
- CLI `--paginate --font-metrics <path>` uses the custom grid
- CLI `--paginate --font-metrics <missing-path>` returns exit code `2`
- CLI `--paginate --paginate-output <path>` writes the full laid-out page
  contents, including a `[TITLE PAGE]`-tagged header for each chapter's
  title page (both standalone and combined with `--inspect`)

### `tests/test_cover.py` *(new in A-6, 6 tests verified passing)*

Unit tests for `cover.py`, plus CLI integration via `main()`. Fixture
PDFs are built in-test via `pymupdf.open()` + `doc.new_page()` +
`page.insert_text()`; no external PDF files are required. Imports skip
gracefully via `pytest.importorskip` if PyMuPDF isn't installed.

Tests cover:
- `render_cover` returns a mode `"1"` image sized `400x240`
- `render_cover` raises `FileNotFoundError` for a missing PDF
- `cover_to_base64` round-trips to a valid PNG (magic-byte check)
- `extract_cover` saves `cover.png` and returns matching base64
- CLI `--extract-cover` flag saves `cover.png` alongside `--output`
- CLI `--extract-cover` on a missing PDF returns exit code `2`

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
