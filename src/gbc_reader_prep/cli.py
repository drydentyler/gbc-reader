"""Command-line interface for ``gbc-reader-prep``.

Ticket: A-1 — Set up Python project skeleton.

At this stage the CLI only exposes ``--version`` and basic logging.
Subsequent tickets (A-2 through A-9) will add the actual
preprocessing subcommands.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Sequence

from gbc_reader_prep import __version__

log = logging.getLogger("gbc_reader_prep")


def configure_logging(verbose: bool = False) -> None:
    """Configure root logging for the CLI.

    INFO level by default; DEBUG when ``--verbose`` is passed.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gbc-reader-prep",
        description=(
            "Desktop preprocessor that converts PDFs into .book files "
            "for the Game Boy Color E-Reader."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable debug logging",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a POSIX-style exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    log.debug("Parsed args: %s", args)
    log.info(
        "gbc-reader-prep %s ready. No subcommands implemented yet "
        "(see tickets A-2 through A-9 in the project plan).",
        __version__,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
