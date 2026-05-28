# GBCR-A2 Findings: PDF Text Extraction

> **Status:** Complete
> **Ticket:** GBCR-A2
> **Last updated:** 2026-05-27

---

## Scope decision (reduced from project plan)

The project plan (§4 A-2) calls for testing against three PDF types: novel,
technical book, and illustrated book. **Scope reduced to two prose books
(novel + general non-fiction)** by user decision on 2026-05-27.

**Rationale:** This is a personal-use project. The user has no intent to
read technical or illustrated books on the Game Boy Color form factor.
The original three-category test was meant to stress different extraction
behaviors (flowing prose vs. complex layout vs. heavy graphics); for the
actual intended use, only the prose path matters.

**Downstream implications for later tickets:**

- **A-7 (pagination):** Can assume single-column flowing text. Multi-column
  layout handling, code-block preservation, and table extraction are out
  of scope for v1.
- **A-6 (cover image):** Still needs to handle illustrated covers (most
  novel PDFs have one) even though interior pages are prose.
- **No new ticket is required** to support technical/illustrated content.
  If desired later, it becomes a v2 candidate.

---

## Sample 1 — Novel: Star Wars: Darth Plagueis (James Luceno)

- **File:** `_OceanofPDF.com_SW0201_Darth_Plagueis_-_James_Lucerno.pdf`
- **Source:** User's personal library
- **Page count (reported by extractor):** 450
- **Has embedded text (vs. scanned image):** Yes — only 20/450 blank
- **Extraction completed:** Yes, no exceptions
- **Empty-page count (from warning):** 20
- **Visual inspection:** Output is recognizable and readable. **Acceptance met.**

### Notes

The empty-page warning fired but is misleading in this context. With 430
of 450 pages extracting cleanly, the 20 blanks are almost certainly
chapter dividers, part-title verso pages, or full-page art — not
scanned-without-OCR. See "Suggested follow-ups" below.

---

## Sample 2 — General non-fiction: If Anyone Builds It, Everyone Dies (Eliezer Yudkowsky)

- **File:** `_OceanofPDF.com_If_Anyone_Builds_It_Everyone_Die_-_Eliezer_Yudkowsky.pdf`
- **Source:** User's personal library
- **Page count (reported by extractor):** 228
- **Has embedded text:** Yes — only 3/228 blank
- **Extraction completed:** Yes, no exceptions
- **Empty-page count:** 3
- **Visual inspection:** Output is recognizable and readable. **Acceptance met.**

### Notes

Prose non-fiction; not a stress test of technical-book features (code blocks,
multi-column layout, dense tables) — see scope decision above. The 3 blank
pages are likely chapter-end versos or front-matter pages.

---

## Implications for later tickets

- **A-3 (outline-based chapter detection):** Both test PDFs are commercial
  trade paperbacks and most likely carry full bookmark trees. A-3 should
  work cleanly against them. Re-run A-3 against the same two PDFs as part
  of A-3 acceptance.
- **A-4 (heuristic chapter detection):** Not exercised here, but still
  needed as a fallback for PDFs without bookmarks.
- **A-5 (front/back-matter trimming):** Should handle any
  distribution-inserted pages (covers, watermarks, source notices) that
  appear before or after the actual book content. The manual override
  mechanism (`--start-page`, `--end-page`, per project plan §3.1) is the
  right escape hatch when heuristics misfire.
- **A-7 (pagination):** Must handle interior blank pages gracefully — do
  not render them as empty pages in the reader's page sequence. Either
  skip them outright or treat them as chapter separators.

## Suggested follow-ups (low priority, not blocking)

- **Soften the empty-page warning copy in `extract.py`.** Current text
  attributes blank pages to "scanned PDF without OCR," which was
  misleading in both samples (neither was scanned). A more accurate
  phrasing would name the common causes: chapter dividers, part-title
  pages, full-page images, *or* scanned-without-OCR. Defer to a future
  cleanup pass; not worth bumping a ticket.

- **Use distinct output filenames per run.** During testing both
  extractions wrote to `sample.txt`, so the first output was overwritten
  by the second. Future runs should use names like `darth.txt` /
  `ifanyone.txt` so multiple outputs can be inspected side-by-side. Not
  a code issue — just a usage note.
