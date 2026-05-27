# GBCR-A2 Findings: PDF Text Extraction

> **Status:** To be completed after running `extract` against three test PDFs.
> **Ticket:** GBCR-A2
> **Last updated:** _yyyy-mm-dd_

For each PDF, record observations that will inform later tickets
(A-3 outline-based chapter detection, A-4 heuristic chapter detection,
A-5 front/back-matter trimming, A-7 pagination).

---

## Sample 1 — Novel

- **File:**
- **Source / license:**
- **Page count (reported by extractor):**
- **Has embedded text (vs scanned image)?**
- **Extraction completed without exceptions?**
- **Empty-page count (from warning):**

### Observations

- Were chapter titles preserved in the text?
- Did running headers and footers leak into the body text?
- Did page numbers appear inline with body text?
- Were paragraph breaks recognizable (e.g. preserved as blank lines)?
- Any garbled characters or encoding issues?
- Order of text on multi-column or sidebar pages (if any)?

### Notes

_(free-form)_

---

## Sample 2 — Technical book

- **File:**
- **Source / license:**
- **Page count:**
- **Has embedded text?**
- **Extraction completed?**
- **Empty-page count:**

### Observations

- Headings (chapter, section, subsection): preserved? distinguishable from body?
- Code blocks: preserved? formatting lost?
- Tables: how did they extract?
- Figure captions: present? in correct place?
- Footnotes: inline or separated?
- Index / TOC pages: any pattern that could be used for trimming?

### Notes

---

## Sample 3 — Illustrated book

- **File:**
- **Source / license:**
- **Page count:**
- **Has embedded text?**
- **Extraction completed?**
- **Empty-page count:**

### Observations

- How much usable text was actually extracted vs lost to image content?
- Captions and labels: present?
- Multi-column or non-linear page layouts: how did reading order come out?

### Notes

---

## Implications for later tickets

- **A-3 (outline-based chapter detection):**
- **A-4 (heuristic chapter detection):**
- **A-5 (front/back-matter trimming):**
- **A-7 (pagination):**
- **Out-of-scope items uncovered (candidates for v2):**
  - e.g. OCR for scanned PDFs?
  - e.g. `"blocks"`-mode extraction for multi-column layouts?
