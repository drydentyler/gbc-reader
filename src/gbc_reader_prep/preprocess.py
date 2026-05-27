"""'preprocess' subcommand for gbc-reader-prep.

GBCR-A2 scope: the subcommand structure is in place per the A-1 hand-off
(`docs/tickets/A-1.md` §3.4 and §8.5), but the implementation is a stub
that writes plain extracted text to a .txt file. Later tickets (A-3
through A-8) will progressively replace the text-writing step with
chapter detection, trimming, pagination, and ultimately a .book file
writer. The subcommand name does not change as we go.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .extract import extract_text

logger = logging.getLogger(__name__)

SUBCOMMAND = "preprocess"


def add_subparser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Register the preprocess subcommand on a top-level subparsers group.

    Called from `cli.build_parser()`.
    """
    parser = subparsers.add_parser(
        SUBCOMMAND,
        help="Preprocess a PDF into reader-ready output.",
        description=(
            "Preprocess a PDF for the GBC Reader. "
            "GBCR-A2 stub: currently writes plain extracted text to a .txt "
            "file. Later tickets will produce a .book file."
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
        help="Path to the output file. For GBCR-A2 this is a .txt file.",
    )
    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the preprocess subcommand.

    Returns a process exit code (0 success, non-zero failure) so the
    top-level `cli.main()` can pass it to `sys.exit`.
    """
    try:
        page_count = extract_text(args.pdf, args.output)
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 2
    except Exception:  # noqa: BLE001 — CLI top-level catch
        logger.exception("preprocess failed")
        return 1

    logger.info(
        "preprocess complete: %d page(s) -> %s", page_count, args.output
    )
    return 0
