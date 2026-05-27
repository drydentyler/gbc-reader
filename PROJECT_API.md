# Project API Reference — gbc-reader-prep

> **Last updated:** GBCR-A2 (draft state — A-2 changes not yet applied to repo)
> **Current version:** 0.1.0
> **Python floor:** `>=3.11`
> **Scope:** Desktop preprocessor subproject only. Firmware (Epic B+) is a separate codebase and not yet underway.

---

## State of this document

Generated to capture the cumulative state after A-1 (completed) and A-2 (drafted, not yet integrated into the repo). Items marked **⚠ unverified** are reconstructions from `docs/tickets/A-1.md` rather than direct reads of source files — sanity-check them against actual code at the start of the next ticket and correct here if anything differs. See "Verification status" at the end.

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

### `gbc-reader-prep preprocess` (added in A-2)

Preprocess a PDF into reader-ready output. GBCR-A2 stub: writes plain extracted text to a `.txt` file. Later tickets (A-3 through A-8) progressively replace this with chapter detection, trimming, pagination, and a `.book` writer. The subcommand name does not change as it evolves.

| Argument | Type | Required | Default | Description |
|---|---|---|---|---|
| `pdf` (positional) | `pathlib.Path` | yes | — | Path to the input PDF |
| `-o`, `--output` | `pathlib.Path` | yes | — | Path to the output file (`.txt` for A-2) |

Exit codes: `0` success, `2` input file not found, `1` other failure.

---

## Modules

### `src/gbc_reader_prep/__init__.py`

Package marker. Holds the project version (read dynamically by hatchling).

**Constants:**
- `__version__: str = "0.1.0"`
  Bumped only by editing this file (A-1.md §3.2). Do not add a literal `version = "..."` to `[project]` — would conflict with `dynamic = ["version"]`.

### `src/gbc_reader_prep/cli.py` ⚠ signatures reconstructed from A-1.md

Top-level CLI dispatcher. Builds the argparse parser, registers subcommand groups, and routes execution to the chosen subcommand's handler.

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

### `src/gbc_reader_prep/extract.py` *(new in A-2)*

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

### `src/gbc_reader_prep/preprocess.py` *(new in A-2)*

Handler for the `preprocess` subcommand. Currently a thin wrapper around `extract_text`; will expand significantly in A-3 onward.

**Third-party imports:** none directly (PyMuPDF is used transitively via `extract`).
**Project imports:**
- `from .extract import extract_text`

**Module-level constants:**
- `SUBCOMMAND: str = "preprocess"`

**Public functions:**

- `add_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser`
  Registers the `preprocess` subcommand on a parent subparsers group. Adds positional `pdf` and required `-o/--output` arguments. Sets `func=run` via `parser.set_defaults()` so `cli.main` can dispatch.

- `run(args: argparse.Namespace) -> int`
  Subcommand handler. Delegates to `extract_text(args.pdf, args.output)`. Returns `0` on success, `2` on `FileNotFoundError`, `1` on any other exception (logged via `logger.exception`).

---

## Test layout

### `tests/__init__.py`
Empty package marker.

### `tests/test_cli.py` ⚠ A-1's exact test names not documented

Smoke tests for the CLI. A-1 ships 4 tests covering the A-1 acceptance criteria (`--version` output, `--verbose` log behavior, package install). A-2 adds at least one test for the `preprocess` subcommand wiring (suggested: `test_preprocess_help_runs` — invokes `main(["preprocess", "--help"])`, asserts `SystemExit(0)` and that "preprocess" appears in stdout). No PDF fixtures yet; end-to-end validation for A-2 is manual per the project plan acceptance criteria.

---

## Conventions in force

- **Branch naming:** `A-{n}-{kebab-case-description}` (e.g. `A-2-pdf-text-extraction`). Same shape for B/C/D/E epics.
- **Ticket ID format (for git):** `GBCR-A{n}` (and `GBCR-B{n}`, etc.).
- **Commit message format:** Conventional Commits with the ticket ID — `feat(prep): GBCR-A2 <description>`. Body may include `Refs: A-{n}` for grep-ability.
- **Loggers:** `logging.getLogger("gbc_reader_prep.<submodule>")` — or equivalently `logging.getLogger(__name__)` from inside a submodule. All project logs share the `gbc_reader_prep` root for filtering.
- **CLI library:** `argparse` (stdlib) only. No `click`. Subcommands via `parser.add_subparsers()` from a single top-level `gbc-reader-prep` script.
- **Source layout:** `src/` layout (not flat). Run from installed package.
- **Version bumping:** Edit `src/gbc_reader_prep/__init__.py` only.
- **Per-ticket completion synopses:** `docs/tickets/A-{n}.md` (mirror layout for other epics).
- **Cumulative state docs:** `PROJECT_API.md` and `PROJECT_TREE.md` at repo root; read at start of every ticket, updated at close.

---

## Verification status

**Directly verified in this turn:**
- `extract.py` and `preprocess.py` contents — drafted in A-2 work, syntax-checked.
- `pymupdf>=1.27.2.3` pin — user-confirmed current release (2026-05-27).
- `doc.page_count` and `doc.close()` API usage — user-confirmed.
- Logger naming convention follows A-1.md §3.7 — verified by inspecting drafted modules' `__name__` resolution.

**Reconstructed from `docs/tickets/A-1.md`, not verified against source:**
- `cli.py` function signatures (return types, parameter defaults).
- `tests/test_cli.py` test names and exact assertions.
- Existence and contents of `[project.optional-dependencies] dev` group.
- `__init__.py` contents beyond `__version__`.
- Exact `[project].authors`, `[project].license`, `[project.urls]` values.

**Not yet verified anywhere:**
- The integration of A-2's `preprocess` subcommand into A-1's `cli.py` — `cli-modifications.md` describes the changes but they haven't been applied or run.
- That `pip install -e ".[dev]"` succeeds with `pymupdf>=1.27.2.3` resolved on the user's Windows + PyCharm setup (A-1.md §6 documents Windows gotchas).

The next agent should resolve the reconstructed items against real source at the start of A-3 and update this document if anything differs. The "code is the ultimate truth" rule from the ticket prompt applies.
