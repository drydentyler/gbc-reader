# gbc-reader-prep

Desktop preprocessor for the Game Boy Color E-Reader project. Converts PDFs
into `.book` files that the handheld firmware can read directly without doing
any PDF parsing on the microcontroller.

See `GBC_Reader_Project_Plan.md` in the project root for the full design.

## Status

Ticket **A-1** — Python project skeleton only. The CLI exposes `--version` and
basic logging. Real preprocessing logic is tracked in tickets A-2 through A-9.

## Requirements

- Python 3.11 or newer

## Install (editable)

From this directory:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

```bash
gbc-reader-prep --version
gbc-reader-prep --verbose
```

## Run tests

```bash
pytest
```
