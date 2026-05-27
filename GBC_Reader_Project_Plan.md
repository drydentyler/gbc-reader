# Game Boy Color E‑Reader — Project Plan

> **Version:** 0.1 (initial)
> **Status:** Planning complete, ready to begin work
> **Last updated:** May 23, 2026

---

## 0. Notes on This Document

- Every part number, link, dimension, and price in this document should be **independently verified** before you commit money to it. Prices, stock levels, and even part availability shift constantly. Where I list prices, treat them as approximate ranges meant for budgeting, not quotes.
- I have flagged items I am not fully certain about with **⚠ verify**.
- This is a working document. Edit it as decisions firm up or change.

---

## 1. Project Overview

### Goal
Build a Kindle-like e-reader in the shell of a Nintendo Game Boy Color (GBC). The device displays pre-processed books from a micro-SD card on a low-power display, navigated entirely with the original GBC face buttons.

### Architecture (Two-Part System)

```
┌──────────────────────────┐         ┌────────────────────────────────┐
│   DESKTOP (one-time      │  USB    │   HANDHELD (run continuously)  │
│   per book)              │  MSC    │                                │
│                          │  ──or── │   ┌─────────────────────────┐  │
│   PDF → preprocessed     │  micro- │   │ ESP32-S3 reads .book    │  │
│   .book file             │  SD     │   │ files from SD, displays │  │
│                          │ ──────► │   │ pages on memory LCD     │  │
│   (Python script)        │         │   └─────────────────────────┘  │
└──────────────────────────┘         └────────────────────────────────┘
```

- **Desktop preprocessor** (Python): parses PDFs once, outputs a flat per-book file with chapter index, cover image, and pre-paginated text.
- **Handheld firmware** (ESP32-S3): just reads, renders, and tracks position. No parsing.

### Why This Split

PDF is a complex container format. Reliable libraries (MuPDF, Poppler) need tens of MB of RAM and a real filesystem. I am not aware of any production-quality PDF parser that runs on hobby microcontrollers. Doing parsing on a desktop once, then shipping a simple pre-rendered file to the handheld, is how the well-known DIY e-readers (e.g., the atomic14 ESP32 ePub reader) handle similar problems — they avoid PDF entirely and use ePub. We get PDF support by moving parsing off the device.

---

## 2. Hardware

### 2.1 Game Boy Color Shell

- **Shell internal dimensions:** approximately 78 × 133.5 × 27.4 mm (W × H × D) ⚠ verify with the specific shell you buy
- **Screen cutout area:** approximately 65 × 48 mm ⚠ verify
- **Stock features to reuse:**
  - **Power slide switch** on top edge of the unit. Standard GBC shells ship with this slide switch and a small flex PCB. Replacement parts are widely available on eBay/Amazon (~$3–6). This will be the **hardware power switch** — it interrupts battery to the rest of the circuit. No need to assign software power on/off to a face button.
  - **Cartridge slot opening** at top — repurpose for USB-C port, BOOT/RESET access, or SD card slot.
  - **Battery compartment** on back — fits a flat LiPo of 1000–2000 mAh comfortably.
  - **Silicone button pads** for A, B, D-pad, Start, Select — these mate with carbon-printed PCB footprints.
- **Where to buy:** Hand Held Legend, Stone Age Gamer, RetroSix, Funnyplaying, AliExpress (lower quality but cheaper). Approximate price: $8–25 depending on quality and color.

### 2.2 Display Recommendation

You asked whether there's a better-fitting display for the 65 × 48 mm cutout than the 2.7" Sharp. Short answer: **the 2.7" Sharp is still the best landscape fit available in the memory-LCD family.** Here's the honest comparison:

| Part | Type | Active area (mm) | Outline (mm) | Resolution | Notes |
|------|------|------------------|--------------|------------|-------|
| **Sharp LS027B7DH01A** | Memory LCD (mono) | 58.8 × 35.28 | 62.8 × 42.82 | 400 × 240 | Best landscape fit. Sits inside cutout with ~1 mm margin per side. |
| Sharp LS021B7DD02 | Memory LCD (color, 64) | 32.4 × 43.2 | 35.4 × 48.6 | 240 × 320 | Portrait, color, but much smaller usable area. Harder to source. ⚠ verify breakout availability |
| Sharp LS018B7DH02 | Memory LCD (mono) | 27.6 × 36.36 | 31 × 41.46 | 230 × 303 | Too small for the cutout; would leave large black borders. Portrait orientation. |
| Waveshare 2.9" e-ink | E-paper (mono) | ~66.9 × 29.05 | ~79 × 36.7 | 296 × 128 | Outline too wide for 65 mm cutout. Slow refresh (~1.5 s), ghosting. |
| Waveshare 2.13" e-ink | E-paper (mono) | ~48.55 × 23.7 | ~59.2 × 29.2 | 250 × 122 | Fits with margin, but lower resolution and slow refresh. |
| 2.4" SPI TFT (ILI9341) | Color IPS LCD | varies (~48.96 × 36.72) | ~70 × 50 | 320 × 240 | Outline usually too wide; backlit (battery hit); not great for reading. |

**Recommendation: Sharp LS027B7DH01A on Adafruit's breakout (product 4694).**

Reasoning matches your "easy to build, lots of tutorials" priority:
- Adafruit ships a fully-assembled breakout with regulator, level shifter, and a 5 V boost converter — you don't deal with the bare FPC connector.
- Active area 58.8 × 35.28 mm fills most of the 65 × 48 cutout; a 3D-printed or laser-cut bezel insert hides the gap.
- Fast refresh (no ghosting) preserves the snappy feel a Game Boy-shaped device should have.
- Daylight readable, no backlight needed.
- Mature Arduino libraries (`Adafruit_SHARP_Memory_Display` + `Adafruit_GFX`).

Tradeoffs to accept: monochrome (cover images will be 1-bit dithered), no backlight (add side-fired LEDs as a v2 if you want night reading).

### 2.3 Microcontroller Recommendation

**ESP32-S3 with PSRAM.**

Specific board options (pick one based on size/availability):

| Board | PSRAM | Flash | Form factor | Notes |
|-------|-------|-------|-------------|-------|
| **Adafruit ESP32-S3 Feather (PSRAM variant)** | 2 MB | 8 MB | Feather | Best documented, native USB, LiPo charging built in |
| Unexpected Maker FeatherS3 | 8 MB | 16 MB | Feather | More memory, LiPo charging built in |
| Unexpected Maker TinyS3 | 8 MB | 8 MB | Tiny | Smallest option, LiPo charging built in |
| Waveshare ESP32-S3-Mini | varies | varies | Small | ⚠ verify PSRAM on the variant you buy |
| LilyGo T-Display-S3 | 8 MB | 16 MB | Built-in LCD | The built-in LCD is wasted here, but the board is plentiful and cheap |

Why ESP32-S3 over RP2040 or plain ESP32:
- **PSRAM** is needed for buffering pre-paginated text and the framebuffer comfortably.
- **Native USB** allows software to present the device as USB Mass Storage to the host computer — drop-in book loading without removing the SD card. Also enables firmware flashing without a USB-to-serial bridge.
- **Plenty of GPIO** for 8 buttons + SPI display + SPI SD + power-monitoring ADC.
- Active library ecosystem and well-trodden Arduino/PlatformIO/ESP-IDF support.

### 2.4 Bootloader Entry Strategy

You preferred software-triggered bootloader entry, with Start button as a fallback.

**The ESP32-S3 supports both:**

1. **Software trigger (primary):** `esptool` can request the chip enter bootloader mode using `--before usb_reset` when the firmware exposes a USB CDC interface. Many ESP32-S3 dev boards also implement a custom serial command that causes the firmware to call `esp_restart()` after switching to bootloader mode. This works most of the time. ⚠ verify on the specific board you choose; it's not 100% reliable across all USB host setups.
2. **Hardware trigger (fallback):** wire Start button to GPIO0 (the BOOT line) on the ESP32-S3 in addition to its normal use as the Start button input. The firmware reads Start as Start during normal operation. To enter ROM bootloader: hold Start, toggle the power switch off then on. GPIO0 low during reset = bootloader mode.

Wiring Start to both a regular input GPIO **and** the BOOT line is a small extra trace, no extra hardware, and gives you a guaranteed escape hatch if software flashing ever fails.

### 2.5 Battery and Power

You opted for flat LiPo. Recommended setup:

| Component | Purpose | Suggested part | Approx. price |
|-----------|---------|----------------|---------------|
| **LiPo cell** | Energy storage | 1200–2000 mAh flat LiPo, single cell (3.7 V nominal). Pick one that fits the battery compartment — measure first. | $7–15 |
| **Charging IC + protection** | USB-C charging, over-current/over-discharge protection | MCP73831 (single-cell linear charger) **or** TP4056 module with onboard protection MOSFETs | $1–5 (module) |
| **Regulator** | Step down to 3.3 V for MCU and SD card | The Feather boards above include this on-board. If you choose a non-Feather S3, add an AP2112K-3.3 or MCP1700 LDO. | $1–2 |
| **Power switch** | Hard on/off | Stock GBC slide switch wired in series with battery output (or as EN to the regulator) | $3–6 |
| **Battery monitor** | Fuel gauge | MAX17048 breakout (optional but very nice for a percentage indicator) | $7–12 |
| **USB-C port** | Charging + data | If your Feather doesn't expose one, use an Adafruit USB-C breakout. Many Feather S3 boards already have USB-C. | $0–5 |

**Recommended path of least resistance:** pick a Feather S3 that has LiPo charging built in (Adafruit, Unexpected Maker). That collapses the charging IC, regulator, and USB-C into the dev board itself. You add only the slide switch and the cell.

**Power switch wiring:** put the slide switch in series with the LiPo's positive lead, between the cell and the Feather's BAT pin. When off, the entire board is unpowered — zero quiescent current.

If you want a soft power option later (long-press a button to wake/sleep without flipping the slide), the ESP32-S3 can deep-sleep at very low current. But for v1, just use the hardware slide switch.

### 2.6 Storage (Micro-SD)

- **Adafruit Micro-SD card breakout board+** (product 254 or the newer 4682) — SPI interface, 3.3 V logic, level shifters on board. ⚠ verify current part number on Adafruit.
- A 4–32 GB SD card formatted FAT32 is plenty. Pre-paginated book files are tiny; even huge libraries fit on 4 GB.
- **SD access on the ESP32-S3 SPI bus is shared with the Sharp display** — same MOSI/SCK lines, separate CS pins. Standard SPI sharing.

### 2.7 Buttons

You need 8 inputs: A, B, Up, Down, Left, Right, Start, Select.

- The stock GBC silicone pads work on a custom PCB with carbon-pad footprints.
- Each pad shorts a GPIO to ground when pressed. Use ESP32 internal pull-ups; no external resistors needed.
- Footprint reference: search the GBC modding community (Funnyplaying, RetroSix, BoxyPixel) for reference Gerbers/KiCad libraries you can study. ⚠ I do not have a single verified link to share — search "GBC custom PCB Gerber" and verify what you find.

### 2.8 Price Breakdown (Estimates)

These are approximate budgeting ranges, not quotes. Always verify before ordering.

#### Recommended ("easy to build") build

| Item | Approx. price |
|------|----------------|
| GBC replacement shell with buttons + screws | $10–20 |
| Adafruit Sharp 2.7" Memory LCD breakout (4694) ⚠ verify | $40–55 |
| Adafruit ESP32-S3 Feather with 2 MB PSRAM ⚠ verify | $15–25 |
| Adafruit Micro-SD breakout ⚠ verify | $8–10 |
| LiPo cell (1500 mAh flat) | $8–12 |
| Replacement GBC power slide switch | $4–8 |
| Micro-SD card (8–32 GB) | $5–10 |
| Custom PCB (JLCPCB, 5 boards, 2-layer) | $5–15 + shipping |
| Headers, wire, misc passives | $5–10 |
| **Subtotal** | **~$100–165** |

#### Budget build (more soldering, more sourcing time)

| Item | Approx. price |
|------|----------------|
| AliExpress GBC shell | $8–12 |
| Bare Sharp LS027B7DH01A panel + own breakout PCB | $25–40 |
| Generic ESP32-S3 module (WROOM-1 with 8 MB PSRAM) | $5–8 |
| TP4056 charging module | $1–2 |
| AP2112K-3.3 LDO | $0.50 |
| Generic micro-SD slot SMD | $1 |
| LiPo, switch, card, PCB | $20–35 |
| **Subtotal** | **~$60–100** |

#### Higher-end / nicer build

| Item | Approx. price |
|------|----------------|
| Funnyplaying or BoxyPixel premium shell | $25–45 |
| Sharp display + acrylic lens cut to size | $50–65 |
| Unexpected Maker FeatherS3 (8 MB PSRAM) ⚠ verify | $20–30 |
| MAX17048 fuel gauge | $10–12 |
| Larger LiPo (2000 mAh) | $12–18 |
| Premium PCB (JLCPCB ENIG finish, assembled) | $30–60 |
| Glass screen lens, custom bezel | $10–20 |
| **Subtotal** | **~$160–260** |

---

## 3. Software

### 3.1 Desktop PDF Preprocessor

#### Goal
Convert any PDF into a `.book` file the firmware can read sequentially without parsing.

#### Stack
- **Python 3.11+**
- **PyMuPDF** (`pymupdf` on PyPI) — text extraction with positioning. Wraps MuPDF. ⚠ verify current license terms; MuPDF is dual-licensed (AGPL + commercial), which is fine for personal use.
- **Pillow** — cover image processing and 1-bit dithering for the display.
- **click** or `argparse` — CLI.

#### Output format

A single `.book` file per book. Suggested structure (binary, fixed header + JSON manifest + page payloads). For v1, a simpler all-JSON-with-base64-images approach is easier to debug:

```json
{
  "schema_version": 1,
  "title": "Book Title",
  "author": "Author Name",
  "display": { "width_px": 400, "height_px": 240, "font": "default-12" },
  "cover_png_base64": "...1-bit dithered cover image...",
  "chapters": [
    { "id": 0, "title": "Chapter 1", "start_page": 0 },
    { "id": 1, "title": "Chapter 2", "start_page": 14 },
    ...
  ],
  "pages": [
    { "chapter_id": 0, "lines": ["Line 1 text", "Line 2 text", ...] },
    ...
  ],
  "total_pages": 312
}
```

Reasons to keep it JSON for v1: easy to inspect, easy to write the firmware parser against, easy to extend. If file size or load time becomes a problem, switch to CBOR or a custom binary format in v2.

#### Trimming logic (hybrid)

1. Read PDF outline (bookmarks) if present.
2. Heuristics to find "main content start":
   - First page whose extracted text starts with "Chapter 1" / "Prologue" / "Introduction" (case-insensitive)
   - Or first outline entry whose title matches that pattern
3. Heuristics to find "main content end":
   - Last outline entry before titles like "Appendix", "Notes", "Bibliography", "Index", "About the Author", "Acknowledgments"
   - Or the last page with substantial body text before a page that's mostly references-style formatting
4. **Show a dry-run summary to the user**: "I'll keep pages 12–387. Cover = page 1. Chapters: …" and ask for confirmation, with overrides for start/end pages and chapter boundaries.
5. **If trimming fails or user declines:** keep the entire PDF, but:
   - Still extract the cover (first page) as a standalone display page.
   - Still treat each detected section/heading as a new "page boundary" so chapters start at the top.
   - Treat front/back matter as additional chapters in the chapter list.

#### Pagination
- Render text into the target display dimensions (400 × 240 by default for Sharp 2.7").
- Use a fixed bitmap font; the firmware will render glyphs identically.
- Hard rule: a chapter's first page always begins with that chapter's first line at the top of the display. Pad the previous page with blank lines if needed.
- The cover image is a single special page (page 0), rendered as a 1-bit dithered image filling the display.

#### CLI design (proposed)
```
preprocess-book input.pdf --output mybook.book
preprocess-book input.pdf --output mybook.book --skip-trim
preprocess-book input.pdf --output mybook.book --start-page 12 --end-page 387
preprocess-book input.pdf --inspect   # dry run, prints proposed trim and chapter map
```

### 3.2 Firmware

#### Stack
- **Arduino framework on PlatformIO** (easiest given your experience level)
- **Adafruit_SHARP_Memory_Display** + **Adafruit_GFX** for display
- **SD** (Arduino core) or **SdFat** for SD card
- **ArduinoJson** for parsing `.book` files and the per-book state file. ⚠ verify ArduinoJson's memory usage on your typical book size; stream-parse if needed.

#### State persistence

Per book, on the SD card:
```
/books/<book_id>/book.book          (the preprocessed file)
/books/<book_id>/state.json         (current position)
```

`state.json`:
```json
{
  "current_page": 47,
  "last_opened": "2026-05-23T14:22:00Z"
}
```

Write on every page turn (or batch every N turns to reduce SD wear).

#### State machine

```
       ┌────────────────────┐
       │  Book Selection    │ ◄────────┐
       └─────────┬──────────┘          │
                 │ A                   │
                 ▼                     │
       ┌────────────────────┐          │
       │  Current Page      │          │
       └─────────┬──────────┘          │
                 │ Start/Select         │
                 ▼                     │
       ┌────────────────────┐          │
       │  Transitional Menu │ ────────►│  (selects Book Selection)
       └─────────┬──────────┘          │
                 │ A (Chapter Select)  │
                 ▼                     │
       ┌────────────────────┐          │
       │  Chapter Select    │ ─────────┘  (B returns to Transitional)
       └────────────────────┘
```

#### Button map (final, accounting for your feedback)

| Screen | A | B | D-pad | Start | Select |
|--------|---|---|-------|-------|--------|
| **Book Selection** | Open selected book to its current page | – | Up/Down: move selector; L/R: – | – | – |
| **Current Page** | Next page | Previous page | Up/Right: next; Down/Left: previous | Transitional Menu | Transitional Menu |
| **Transitional Menu** | Select highlighted item (Chapter Select or Book Selection) | Return to Current Page | Up/Down: move selector | Return to Current Page | Return to Current Page |
| **Chapter Select** | Jump to first page of chapter; update Current Page Position | Return to Transitional Menu | Up/Down: move selector | Return to Current Page | Return to Current Page |

**Power on/off** is handled by the hardware slide switch.

**Bootloader entry (special, not part of normal UX):** software-triggered via USB CDC command from the host (preferred). Hardware fallback: hold Start while toggling power switch off then on; this pulls GPIO0 low during reset and enters ROM bootloader. The firmware does not consume the Start button differently during this — it's a hardware-level effect of GPIO0 being held low at reset.

#### Display rendering
- Framebuffer: 400 × 240 / 8 = 12,000 bytes for 1bpp. Fits trivially in RAM.
- Render workflow: clear framebuffer → for each line in the current page, draw with `Adafruit_GFX::print()` at a fixed y-offset → push framebuffer to display via `Adafruit_SHARP_Memory_Display::refresh()`.

#### USB Mass Storage mode for book loading
- When USB cable detected and Start is held at boot (or by default, depending on what's nicer), present the SD card to the host as USB Mass Storage so the user can drag-and-drop `.book` files to `/books/<book_id>/`.
- Use **TinyUSB** (built into Arduino-ESP32 for S3) for the MSC interface. ⚠ verify; there are known limitations with simultaneous SD access from MCU and host.

---

## 4. Work Breakdown (Tickets)

Each ticket is sized to be a meaningful, self-contained chunk. Order matters — earlier tickets unblock later ones.

### Epic A — Desktop Preprocessor

- **A-1. Set up Python project skeleton.** `pyproject.toml`, `src/gbc_reader_prep/` package, CLI entry point, `--version` flag, basic logging. Acceptance: `pip install -e .` works; `gbc-reader-prep --version` prints a version.

- **A-2. PDF text extraction proof-of-concept.** Open a sample PDF with PyMuPDF, extract text from each page, save to a `.txt` for visual inspection. Test against 3 PDFs of different types (novel, technical book, illustrated book). Acceptance: text output for each is recognizable and readable.

- **A-3. Chapter detection from outline.** If the PDF has a bookmark tree, parse it into a chapter list with start pages. Acceptance: tested PDF with bookmarks produces a chapter list matching the table of contents.

- **A-4. Chapter detection heuristic fallback.** For PDFs without bookmarks, detect chapter starts via regex on page text (`^Chapter \d+`, `^Prologue`, `^Introduction`, etc.). Acceptance: works on at least one PDF without bookmarks.

- **A-5. Front/back matter trimming.** Implement the start/end page detection from §3.1. Output a dry-run report (`--inspect` flag). Acceptance: dry run shows proposed start/end pages and the user can override.

- **A-6. Cover image extraction.** Pull the first page as an image, downscale to display resolution, 1-bit dither (Floyd–Steinberg), embed as base64 in the output. Acceptance: opening the embedded base64 in an image viewer shows a recognizable cover.

- **A-7. Pagination engine.** Given extracted text + a font metrics file matching the firmware's font, lay out text into 400 × 240 pages. Enforce chapter-start-at-top rule. Acceptance: a 50-page novel produces a reasonable page count (rough sanity: ~250 words per page × 200 pages ≈ 50,000 words for a short novel).

- **A-8. `.book` file writer.** Assemble manifest + chapters + pages + cover into the JSON file. Acceptance: file opens, schema validates, contains expected counts.

- **A-9. End-to-end CLI test.** Run the full pipeline on 3 books, manually inspect the output `.book` files. Acceptance: subjectively good output for all three; chapter boundaries correct; cover recognizable.

- **A-10. (Optional, v2) Switch to binary format** if `.book` files exceed ~5 MB or load times on the MCU are slow.

### Epic B — Firmware Bring-Up (Breadboard)

- **B-1. Pick MCU board, order it.** Document which board variant (Adafruit Feather ESP32-S3, etc.). Verify PSRAM, flash size, LiPo charger presence.

- **B-2. PlatformIO project skeleton.** Empty `main.cpp` with `setup()`/`loop()` that blinks the onboard LED and prints "hello" over USB CDC. Acceptance: serial monitor shows the hello at the expected rate.

- **B-3. Sharp display driver.** Wire up the Adafruit Sharp 2.7" breakout on a breadboard. Run the Adafruit library's example sketch. Acceptance: example demo renders correctly.

- **B-4. Custom font and "page renderer" function.** Pick or generate a fixed bitmap font appropriate for 400 × 240. Write a function `renderPage(const Page& p)` that takes a parsed page struct and draws all lines. Acceptance: hardcoded test page renders cleanly.

- **B-5. SD card driver.** Wire up the SD breakout (shared SPI bus). Read a test file. Acceptance: contents of `/test.txt` print to serial.

- **B-6. `.book` file parser.** Use ArduinoJson to parse a sample `.book` file off the SD card. Stream-parse to keep RAM use bounded. Acceptance: parsing reports correct title, page count, chapter count.

- **B-7. Button input handling.** Wire 8 tactile buttons to GPIOs with internal pull-ups. Implement debouncing (10 ms is typical). Acceptance: serial log prints every press cleanly with no duplicates.

- **B-8. State machine implementation.** Implement the four screens from §3.2 with proper button-to-action mapping. Acceptance: can navigate Book Selection → Current Page → Transitional → Chapter Select → back, all transitions correct.

- **B-9. Per-book state persistence.** Read/write `state.json`. Open a book, advance a few pages, power-cycle, confirm position restored. Acceptance: position survives reboot.

- **B-10. Cover image rendering.** Decode the base64 cover, render as the first page of every book. Acceptance: cover shows recognizable, dithered.

- **B-11. End-to-end breadboard test.** Load 3 books, navigate, read for a while, power-cycle, resume. Acceptance: no crashes, no UI bugs, positions preserved.

### Epic C — Power and USB Polish

- **C-1. LiPo wiring on breadboard.** Wire a LiPo through the slide switch to the Feather's BAT pin. Verify charging works over USB while the slide is on. Acceptance: charge LED reports correctly; system runs from battery when USB disconnected.

- **C-2. Battery percentage indicator.** Read battery voltage via ADC (Feather S3 boards typically have a voltage divider on a known pin — ⚠ verify per board) and convert to a rough percentage. Display in Book Selection header. Acceptance: percentage drops over usage, rises while charging.

- **C-3. USB Mass Storage mode.** Implement TinyUSB MSC presenting the SD card to the host. Verify dragging a `.book` file appears in the Book Selection list on next boot. Acceptance: book loaded over USB shows up correctly.

- **C-4. Software bootloader trigger.** Validate `esptool --before usb_reset` flashes successfully without touching any buttons. Document the exact command in `BUILD.md`. Acceptance: one-command reflash from desktop.

- **C-5. Deep-sleep on idle (optional).** After N minutes of no input, sleep the MCU; wake on any button. Sharp memory LCD retains its image with no power. Acceptance: measured idle current drops by an order of magnitude.

### Epic D — Custom PCB

- **D-1. Choose EDA tool and complete a tutorial.** KiCad 9 is the right choice. Work through at least one full tutorial start to finish (see §5).

- **D-2. Source GBC button-pad footprints.** Find or create KiCad footprints that match the stock GBC silicone pad contacts (A, B, D-pad, Start, Select). The GBC modding community has reference files — verify before using.

- **D-3. Draw schematic.** ESP32-S3 module (or socket header for the Feather), Sharp display connector, SD card connector, 8 button footprints, BOOT-line tie for Start, USB-C connector if not on the Feather, LiPo connector, slide switch breakout. Run electrical rules check.

- **D-4. Lay out PCB.** Match the GBC mainboard outline so it fits the shell's mounting posts. Place button footprints where the silicone pads will sit. Place display connector and SD card socket where they fit physically. Run design rules check. Order 5 boards from JLCPCB or PCBWay.

- **D-5. Assemble first PCB.** Solder MCU module, passives, connectors, headers. Power on, verify all signals with multimeter before connecting display/SD. Re-flash firmware. Acceptance: full firmware runs on the custom PCB.

- **D-6. Mechanical fit in the GBC shell.** Insert PCB, display, battery, micro-SD. Close the shell. Verify all buttons feel right, screen aligns to bezel, USB-C is accessible, slide switch operates correctly. Iterate the PCB layout if needed.

### Epic E — Polish and Documentation

- **E-1. Write a build guide.** `BUILD.md` with parts list, assembly photos, flashing instructions, troubleshooting.
- **E-2. Write a user guide.** How to preprocess a PDF, how to load books, button reference, troubleshooting.
- **E-3. v1 retrospective.** What broke, what should change for v2.

---

## 5. PCB Design Resources

Since this is your first custom PCB, here's a curated set of resources. I have verified each link exists at the time of writing; the *content* of each I am less certain about, so treat them as starting points, not gospel.

### Free software
- **KiCad 9** — open-source, current industry standard for hobbyists. Download at `kicad.org`.

### Tutorials and courses
- **Phil's Lab (YouTube)** — high-quality electronics design content, mix of KiCad, signal integrity, and real-world board design. Search "Phil's Lab KiCad". ⚠ verify channel is still active.
- **Predictable Designs — "How to design an ESP32 PCB with KiCad (in less than 25 minutes)"** — direct match for our target chip. (YouTube; ⚠ verify the specific video link works.)
- **DigiKey YouTube — KiCad tutorial series** — DigiKey publishes structured beginner content.
- **Tech Explorations — "Mastering KiCad: Open-Source PCB Design for Beginners"** — paid course on Coursera; mixed reviews (some find it fast), but structured. ⚠ verify current price and reviews.
- **DeepBlue Embedded — "ESP32 PCB Design in KiCAD: ESP32-C3 + Chip Antenna"** — written tutorial with photos. The general workflow translates to ESP32-S3.

I cannot give you specific verified video URLs without risking outdated or moved links. **Search YouTube for the exact phrases above and pick the most-watched, most-recently-uploaded result.**

### PCB fabrication
- **JLCPCB** — cheapest, large catalog of pre-stocked parts for assembly (LCSC). Quality is good for hobby work.
- **PCBWay** — slightly pricier, similar quality, sometimes faster.
- **OSH Park** (US-based, purple boards) — slower and pricier but excellent quality.

### Reference designs to study
- **Espressif's ESP32-S3 reference schematics** — published on the Espressif website. ⚠ verify URL.
- **Adafruit's open-source Feather schematics** — every Adafruit Feather has a downloadable schematic PDF. Reading the Feather S3 schematic is the single best way to learn the right way to wire an ESP32-S3 module.
- **GBC modding community projects** — Funnyplaying, RetroSix, BoxyPixel publish photos of their custom GBC PCBs. Use these to learn how button footprints, screen mounts, and shell-fit dimensions are typically handled. ⚠ I do not have specific verified open-source GBC PCB designs to recommend.

### KiCad-specific habits to develop early
- Annotate (assign references) and run ERC after every schematic edit.
- Always use 3D models so you can preview the physical board before ordering.
- Run DRC before generating Gerbers.
- Order a paper printout of the board at 1:1 scale and lay your parts on top of it as a sanity check before sending it to fab.

---

## 6. Open Questions and Things to Verify Before Spending Money

These are decisions still pending or assumptions I made. Confirm or correct each before proceeding past the listed ticket.

| # | Question | Block before ticket |
|---|----------|---------------------|
| Q1 | Which exact ESP32-S3 board (Feather, FeatherS3, generic) — driven by what's in stock + budget | B-1 |
| Q2 | Confirm the Adafruit Sharp 2.7" breakout (4694) is in stock at a reasonable price; if not, where to source the bare panel + driver circuit | B-3 |
| Q3 | Verify shell internal dimensions and screen cutout for the specific shell you buy — measurements above are typical, not guaranteed | D-4 |
| Q4 | Verify ArduinoJson can stream-parse a 2–5 MB `.book` file without exhausting heap, or pick a different parsing strategy | B-6 |
| Q5 | Confirm TinyUSB MSC on Arduino-ESP32 supports concurrent host + firmware access to the SD card. If not, design a "USB mode" the user explicitly enters, during which the firmware suspends SD access | C-3 |
| Q6 | Verify MuPDF/PyMuPDF licensing satisfies your intent (personal use, distribution, etc.) | A-2 |
| Q7 | Pick a final font and confirm its glyph dimensions; the desktop preprocessor and firmware must agree exactly | A-7 / B-4 |
| Q8 | Decide on USB MSC trigger behavior — automatic on cable detect, or hold-Start-at-boot. Different UX implications | C-3 |

---

## 7. Glossary

- **MCU** — microcontroller unit (the brain).
- **PSRAM** — pseudo-static RAM, external memory chip used by the ESP32-S3 to extend RAM beyond the chip's built-in SRAM.
- **MIP** — Memory In Pixel; the technology family Sharp memory LCDs belong to.
- **MSC** — Mass Storage Class, the USB protocol used by thumb drives.
- **DFU** — Device Firmware Update; one way an MCU can present itself to a host for firmware updates over USB.
- **CDC** — Communications Device Class; the USB protocol that makes an MCU look like a serial port to the host.
- **ERC / DRC** — Electrical / Design Rules Check; KiCad's two main correctness checks.
- **EDA** — Electronic Design Automation; the category of software KiCad belongs to.
