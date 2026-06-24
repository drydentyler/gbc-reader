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

from .book import write_book_path
from .chapters import detect_chapters_path
from .cover import extract_cover
from .extract import extract_text, extract_text_pages
from .paginate import DEFAULT_FONT_METRICS, FontMetrics, load_font_metrics, paginate_chapters
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
        "--extract-cover",
        action="store_true",
        help=(
            "Extract the first page of the PDF as a cover image, "
            "downscaled to 400x240 with 1-bit Floyd-Steinberg dithering. "
            "Saved as cover.png alongside --output."
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
    parser.add_argument(
        "--paginate",
        action="store_true",
        help=(
            "After chapter/bounds detection, lay out the main-content "
            "text into 400x240 display pages and log the resulting page "
            "count (overall and per-chapter), for manual sanity-checking. "
            "Works with or without --inspect."
        ),
    )
    parser.add_argument(
        "--font-metrics",
        type=Path,
        default=None,
        help=(
            "Path to a JSON font metrics file "
            '({"char_width_px": <int>, "line_height_px": <int>}) used by '
            "--paginate to compute characters-per-line and lines-per-page. "
            "Defaults to a placeholder 6x10px grid until the firmware's "
            "real font (B-4) is finalized."
        ),
    )
    parser.add_argument(
        "--paginate-output",
        type=Path,
        default=None,
        help=(
            "Used with --paginate. Path to a .txt file to write the "
            "full laid-out page contents (one block per display page, "
            "each line padded/truncated to the character grid, with a "
            "header marking the page number and chapter), for manual "
            "review of where page/chapter breaks actually fall."
        ),
    )
    parser.set_defaults(func=run)
    return parser


def _load_font_metrics(args: argparse.Namespace) -> FontMetrics:
    """Resolve the font metrics to use for ``--paginate``.

    Returns:
        :data:`gbc_reader_prep.paginate.DEFAULT_FONT_METRICS` if
        ``--font-metrics`` was not given, otherwise the metrics loaded
        from that file.

    Raises:
        FileNotFoundError: If ``--font-metrics`` points at a missing file.
    """
    if args.font_metrics is None:
        return DEFAULT_FONT_METRICS
    return load_font_metrics(args.font_metrics)


def _report_pagination(
    pdf_path: Path,
    chapters: list,
    start_page: int,
    end_page: int,
    font_metrics: FontMetrics,
    paginate_output: Path | None = None,
) -> None:
    """Run the pagination engine and log a summary: total page count and a
    per-chapter breakdown. Logged at INFO level.

    If ``paginate_output`` is given, also writes the full laid-out page
    contents to that path for manual review (see
    :func:`_write_paginate_output`).
    """
    page_texts = extract_text_pages(pdf_path)
    pages = paginate_chapters(
        page_texts,
        chapters,
        font_metrics=font_metrics,
        start_page=start_page,
        end_page=end_page,
    )

    # Page.chapter_id indexes into the in-range, start_page-sorted subset
    # of `chapters` that paginate_chapters actually laid out (see its
    # docstring) — not `chapters` itself. Rebuild that same subset here so
    # _write_paginate_output can look up the right title.
    relevant_chapters = sorted(
        (c for c in chapters if start_page <= c.start_page <= end_page),
        key=lambda c: c.start_page,
    )
    if not relevant_chapters:
        from .chapters import Chapter

        relevant_chapters = [Chapter(title="", start_page=start_page, level=1)]

    logger.info(
        "Pagination: %d display page(s) for main content pages %d-%d (1-based)",
        len(pages),
        start_page + 1,
        end_page + 1,
    )

    counts: dict[int, int] = {}
    for page in pages:
        counts[page.chapter_id] = counts.get(page.chapter_id, 0) + 1
    for chapter_id in sorted(counts):
        logger.info("  Chapter %d: %d page(s)", chapter_id, counts[chapter_id])

    if paginate_output is not None:
        _write_paginate_output(paginate_output, pages, relevant_chapters)
        logger.info("Wrote laid-out page contents to %s", paginate_output)


def _write_paginate_output(path: Path, pages: list, chapters: list) -> None:
    """Write the full laid-out page contents to ``path`` for manual review.

    Each display page is rendered as a fixed-width block (one line per
    grid row, so short lines/blank padding are visible exactly as they'll
    appear on the device), preceded by a header naming the page number
    (1-based) and the chapter it belongs to.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as out:
        for i, page in enumerate(pages):
            title = chapters[page.chapter_id].title if page.chapter_id < len(chapters) else ""
            tag = " [TITLE PAGE]" if page.is_title_page else ""
            out.write(f"===== Page {i + 1} (chapter {page.chapter_id}: {title!r}){tag} =====\n")
            for line in page.lines:
                out.write(line + "\n")
            out.write("\n")


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

    if args.paginate:
        try:
            font_metrics = _load_font_metrics(args)
        except FileNotFoundError as exc:
            logger.error("%s", exc)
            return 2
        try:
            _report_pagination(
                args.pdf, chapters, start_page, end_page, font_metrics, args.paginate_output
            )
        except Exception:  # noqa: BLE001
            logger.exception("Pagination failed")
            return 1

    return 0


def _write_book(args: argparse.Namespace) -> int:
    """A-8: assemble and write a full ``.book`` JSON file.

    Triggered when ``--output`` ends in ``.book``, in place of the plain
    ``.txt`` extraction path. Chapters, content bounds, pagination, and
    the cover image are all (re-)derived here regardless of
    ``--show-chapters``/``--extract-cover``/``--paginate``, since a
    ``.book`` file always needs all four.

    Returns:
        0 on success, 2 if the input PDF (or ``--font-metrics`` file)
        does not exist, 1 on any other failure.
    """
    try:
        font_metrics = _load_font_metrics(args)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2

    try:
        book = write_book_path(
            args.pdf,
            args.output,
            font_metrics=font_metrics,
            start_page=args.start_page,
            end_page=args.end_page,
        )
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2
    except Exception:  # noqa: BLE001
        logger.exception("Writing .book file failed")
        return 1

    logger.info(
        "Wrote %s: %d page(s), %d chapter(s)",
        args.output,
        book["total_pages"],
        len(book["chapters"]),
    )
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

    if args.output.suffix.lower() == ".book":
        return _write_book(args)

    try:
        page_count = extract_text(args.pdf, args.output)
        logger.info("Extracted %d page(s) to %s", page_count, args.output)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2
    except Exception:  # noqa: BLE001 — surface as a single user-visible failure
        logger.exception("Preprocessing failed")
        return 1

    if args.extract_cover:
        try:
            cover_path, _ = extract_cover(args.pdf, args.output.parent)
            logger.info("Extracted cover image to %s", cover_path)
        except FileNotFoundError as exc:
            logger.error("%s", exc)
            return 2
        except Exception:  # noqa: BLE001
            logger.exception("Cover extraction failed")
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

    if args.paginate:
        try:
            font_metrics = _load_font_metrics(args)
        except FileNotFoundError as exc:
            logger.error("%s", exc)
            return 2
        try:
            chapters = detect_chapters_path(args.pdf)
            page_texts = extract_text_pages(args.pdf)
            bounds = detect_content_bounds(chapters, len(page_texts))
            start_page = args.start_page if args.start_page is not None else bounds.start_page
            end_page = args.end_page if args.end_page is not None else bounds.end_page
            _report_pagination(
                args.pdf, chapters, start_page, end_page, font_metrics, args.paginate_output
            )
        except Exception:  # noqa: BLE001
            logger.exception("Pagination failed")
            return 1

    return 0
