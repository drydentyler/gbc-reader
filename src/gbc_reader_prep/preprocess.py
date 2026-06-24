"""Handler for the ``preprocess`` subcommand.

A-2 introduced this module as a thin argparse-facing wrapper around
:func:`gbc_reader_prep.extract.extract_text`. A-3 adds an optional
``--show-chapters`` flag that, after extraction, logs the chapter list
derived from the PDF's outline. A-4 extends ``--show-chapters`` to fall
back to heuristic text-based detection for PDFs with no outline. A-5
adds front/back matter trimming: an ``--inspect`` flag that runs a dry
run reporting the proposed start/end page range (and any detected back
matter) without writing output, plus ``--start-page``/``--end-page``
overrides usable with or without ``--inspect``.

The shape of this module (``SUBCOMMAND`` constant, ``add_subparser``,
``run``) is the canonical pattern for all future subcommand modules in
this project (see A-2 §4.4).

Refs: A-3, A-4, A-5
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .chapters import detect_chapters_path
from .extract import extract_text
from .trim import detect_content_bounds

logger = logging.getLogger(__name__)

SUBCOMMAND = "preprocess"


def add_subparser(
    subparsers: "argparse._SubParsersAction",
) -> argparse.ArgumentParser:
    """Register the ``preprocess`` subcommand on the given subparsers group.

    Sets ``func=run`` on the parser's defaults so ``cli.main`` can
    dispatch via ``args.func(args)``.
    """
    parser = subparsers.add_parser(
        SUBCOMMAND,
        help="Preprocess a PDF into reader-ready output.",
        description=(
            "Preprocess a PDF into reader-ready output. In the current "
            "ticket sequence (A-2 through A-8) this command's output "
            "evolves from a plain .txt extraction (A-2) toward a fully "
            "preprocessed .book file (A-8). The subcommand name does not "
            "change as it evolves."
        ),
    )
    parser.add_argument(
        "pdf",
        type=Path,
        help="Path to the input PDF.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=False,
        help=(
            "Path to the output file (.txt during A-2 / A-3). Required "
            "unless --inspect is given."
        ),
    )
    parser.add_argument(
        "--show-chapters",
        action="store_true",
        help=(
            "After extraction, log the chapter list derived from the "
            "PDF's outline (table of contents bookmarks), falling back "
            "to heuristic text matching (e.g. 'Chapter 1', 'Prologue') "
            "if the PDF has no outline. Logged at INFO level."
        ),
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help=(
            "Dry run: detect chapters and the proposed main-content "
            "page range (trimming detected back matter such as "
            "Appendix/Notes/Bibliography/Index/About the "
            "Author/Acknowledgments), print a report, and exit without "
            "writing any output file. --output is not required with "
            "this flag."
        ),
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=None,
        help=(
            "Override the detected main-content start page (0-indexed). "
            "Takes precedence over auto-detection."
        ),
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help=(
            "Override the detected main-content end page (0-indexed, "
            "inclusive). Takes precedence over auto-detection."
        ),
    )
    parser.set_defaults(func=run)
    return parser


def _report_trim(args: argparse.Namespace) -> int:
    """Implements ``--inspect``: detect chapters and content bounds, apply
    any ``--start-page``/``--end-page`` overrides, and print a dry-run
    report. Writes no output file.

    Returns:
        0 on success, 2 if the input PDF does not exist, 1 on any other
        failure.
    """
    import pymupdf

    if not args.pdf.exists():
        logger.error("PDF not found: %s", args.pdf)
        return 2

    try:
        chapters = detect_chapters_path(args.pdf)
        doc = pymupdf.open(str(args.pdf))
        try:
            page_count = doc.page_count
        finally:
            doc.close()
    except Exception:  # noqa: BLE001
        logger.exception("Inspection failed")
        return 1

    bounds = detect_content_bounds(chapters, page_count)
    start_page = args.start_page if args.start_page is not None else bounds.start_page
    end_page = args.end_page if args.end_page is not None else bounds.end_page

    logger.info("Inspected %s (%d page(s)):", args.pdf, page_count)
    logger.info(
        "  Proposed main content: pages %d-%d (1-based)",
        start_page + 1,
        end_page + 1,
    )
    if args.start_page is not None:
        logger.info("  (start page overridden via --start-page)")
    if args.end_page is not None:
        logger.info("  (end page overridden via --end-page)")
    if bounds.back_matter_title is not None:
        logger.info(
            "  Detected back matter: %r starting at page %d (1-based)",
            bounds.back_matter_title,
            bounds.back_matter_start_page + 1,
        )
    else:
        logger.info("  No back matter detected.")

    if not chapters:
        logger.info("  No chapters detected.")
    else:
        logger.info("  Detected %d chapter entry/entries:", len(chapters))
        for ch in chapters:
            indent = "  " * ch.level
            logger.info("%s- %s (page %d)", indent, ch.title, ch.start_page + 1)

    return 0


def run(args: argparse.Namespace) -> int:
    """Execute the ``preprocess`` subcommand.

    Returns:
        0 on success, 2 if the input PDF does not exist, 1 on any other
        failure.
    """
    if args.inspect:
        return _report_trim(args)

    if args.output is None:
        logger.error("-o/--output is required unless --inspect is given")
        return 2

    try:
        page_count = extract_text(args.pdf, args.output)
        logger.info("Extracted %d page(s) to %s", page_count, args.output)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2
    except Exception:  # noqa: BLE001 — surface as a single user-visible failure
        logger.exception("Preprocessing failed")
        return 1

    if args.show_chapters:
        try:
            chapters = detect_chapters_path(args.pdf)
        except FileNotFoundError as exc:
            # Unlikely to reach here (extract_text would have raised first),
            # but kept explicit for symmetry with the extraction branch.
            logger.error("%s", exc)
            return 2
        except Exception:  # noqa: BLE001
            logger.exception("Chapter detection failed")
            return 1

        if not chapters:
            logger.info(
                "No chapters detected (no outline, and no heuristic "
                "pattern matched any page)."
            )
        else:
            logger.info("Detected %d chapter entry/entries:", len(chapters))
            for ch in chapters:
                indent = "  " * (ch.level - 1)
                # Display page numbers as 1-based in user-facing log lines
                # so they match what a PDF reader shows; the stored value
                # in Chapter.start_page remains 0-based.
                logger.info(
                    "%s- %s (page %d)", indent, ch.title, ch.start_page + 1
                )

    return 0
