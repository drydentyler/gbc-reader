"""Handler for the ``preprocess`` subcommand.

A-2 introduced this module as a thin argparse-facing wrapper around
:func:`gbc_reader_prep.extract.extract_text`. A-3 adds an optional
``--show-chapters`` flag that, after extraction, logs the chapter list
derived from the PDF's outline.

The shape of this module (``SUBCOMMAND`` constant, ``add_subparser``,
``run``) is the canonical pattern for all future subcommand modules in
this project (see A-2 §4.4).

Refs: A-3
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .chapters import detect_chapters_from_outline_path
from .extract import extract_text

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
        required=True,
        help="Path to the output file (.txt during A-2 / A-3).",
    )
    parser.add_argument(
        "--show-chapters",
        action="store_true",
        help=(
            "After extraction, log the chapter list derived from the "
            "PDF's outline (table of contents bookmarks). Logged at INFO "
            "level."
        ),
    )
    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the ``preprocess`` subcommand.

    Returns:
        0 on success, 2 if the input PDF does not exist, 1 on any other
        failure.
    """
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
            chapters = detect_chapters_from_outline_path(args.pdf)
        except FileNotFoundError as exc:
            # Unlikely to reach here (extract_text would have raised first),
            # but kept explicit for symmetry with the extraction branch.
            logger.error("%s", exc)
            return 2
        except Exception:  # noqa: BLE001
            logger.exception("Chapter detection failed")
            return 1

        if not chapters:
            logger.info("No chapters detected (PDF has no outline).")
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
