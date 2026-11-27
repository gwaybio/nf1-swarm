#!/usr/bin/env python3
"""
Shared text cleaner for literature extraction — thin wrapper around marker-pdf.

Converts a PDF or PMC HTML document to clean Markdown using the marker
library (https://github.com/datalab-to/marker, Apache 2.0 code licence).

MODEL WEIGHTS NOTICE: marker downloads model weights from datalab.to on first
use.  Those weights are licensed under the datalab.to MODEL_LICENSE (modified
AI Pubs Open Rail-M), NOT Apache 2.0.  Free for research/personal use and
startups < $5M funding/revenue; commercial use above that threshold requires
a paid licence.  Do NOT redistribute the downloaded weights.  See:
https://www.datalab.to/pricing

Usage:
    # Convert a local PDF (requires: uv sync --extra literature)
    uv run python literature/text_cleaner.py --input paper.pdf

    # Fetch and convert a PMC article
    uv run python literature/text_cleaner.py --pmcid PMC9629420

    # Write body text to a file and references to a separate file
    uv run python literature/text_cleaner.py --input paper.pdf \\
        --output body.md --refs-output references.txt

Output is clean Markdown with section headers preserved by marker.
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

# PMC printable URL — returns HTML that marker's HTMLProvider can parse
_PMC_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/?report=printable&format=html"

# Matches Markdown headings at any level (##, ###, # etc.) before reference section keywords
_REF_HEADING = re.compile(
    r"^#{1,4}\s+(References|Bibliography|Works Cited)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _require_marker() -> None:
    """Raise a clear error if marker-pdf is not installed."""
    try:
        import marker  # type: ignore[import-not-found]  # noqa: F401
    except ImportError:
        print(
            "ERROR: marker-pdf is not installed.\n"
            "Install it with:  uv sync --extra literature\n"
            "or:               uv add marker-pdf",
            file=sys.stderr,
        )
        sys.exit(1)


def _convert(filepath: str | Path, disable_ocr: bool = True) -> str:
    """
    Convert a PDF or HTML file to Markdown using marker.

    Parameters
    ----------
    filepath:
        Local path to a .pdf or .html file.
    disable_ocr:
        When True (default) uses marker's no-OCR path: extracts text
        directly from the PDF text layer, runs ONNX layout/reading-order
        models on CPU only.  No VLM started, ~24-33 pg/s on CPU.
        Set False only for scanned PDFs that have no embedded text.

    Returns
    -------
    str
        Clean Markdown string.
    """
    from marker.converters.pdf import PdfConverter  # type: ignore[import-not-found]
    from marker.models import create_model_dict  # type: ignore[import-not-found]
    from marker.output import text_from_rendered  # type: ignore[import-not-found]

    # Build a minimal config dict.  The 'disable_ocr' key maps to marker's
    # --disable_ocr flag which skips VLM calls entirely on clean digital PDFs.
    config: dict = {}
    if disable_ocr:
        config["disable_ocr"] = True

    model_dict = create_model_dict()
    converter = PdfConverter(config=config, artifact_dict=model_dict)
    rendered = converter(str(filepath))
    markdown, _metadata, _images = text_from_rendered(rendered)
    return markdown


def convert_pdf(path: str | Path, disable_ocr: bool = True) -> dict[str, str]:
    """
    Convert a local PDF to Markdown.

    Returns {'body': str, 'references': str, 'full': str}.
    """
    _require_marker()
    markdown = _convert(path, disable_ocr=disable_ocr)
    return _split_refs(markdown)


def convert_pmc(pmcid: str, disable_ocr: bool = False) -> dict[str, str]:
    """
    Fetch a PMC article as HTML and convert to Markdown via marker.

    disable_ocr is False by default for HTML (not a PDF scan).
    Returns {'body': str, 'references': str, 'full': str}.
    """
    _require_marker()
    url = _PMC_URL.format(pmcid=pmcid.upper().strip())
    with urllib.request.urlopen(url, timeout=30) as resp:
        html_bytes = resp.read()

    # Write to a named temp file so marker's provider_from_filepath picks HTML
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        tmp.write(html_bytes)
        tmp_path = tmp.name

    try:
        markdown = _convert(tmp_path, disable_ocr=disable_ocr)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return _split_refs(markdown)


def _split_refs(markdown: str) -> dict[str, str]:
    """
    Split markdown into body and references section.

    Matches heading at any Markdown level (# through ####).
    Returns {'body': str, 'references': str, 'full': str}.
    """
    m = _REF_HEADING.search(markdown)
    if m:
        body = markdown[:m.start()].rstrip()
        refs = markdown[m.start():].strip()
        return {"body": body, "references": refs, "full": markdown}
    return {"body": markdown.strip(), "references": "", "full": markdown}


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--input",  metavar="FILE",   help="Local PDF or HTML file")
    src.add_argument("--pmcid",  metavar="PMC_ID", help="Fetch from PMC (e.g. PMC9629420)")

    p.add_argument("--output",      metavar="FILE", help="Write full Markdown to file (default: stdout)")
    p.add_argument("--refs-output", metavar="FILE", help="Write references section to a separate file")
    p.add_argument("--force-ocr",   action="store_true",
                   help="Enable VLM/OCR path (slow, for scanned PDFs only)")
    p.add_argument("--body-only",   action="store_true",
                   help="Print body text without the references section")

    args = p.parse_args(argv)

    disable_ocr = not args.force_ocr

    if args.pmcid:
        result = convert_pmc(args.pmcid, disable_ocr=disable_ocr)
    else:
        result = convert_pdf(args.input, disable_ocr=disable_ocr)

    text = result["body"] if args.body_only else result["full"]

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Wrote {len(text):,} chars to {args.output}", file=sys.stderr)
    else:
        print(text)

    if args.refs_output:
        Path(args.refs_output).write_text(result["references"], encoding="utf-8")
        print(f"Wrote references ({len(result['references'])} chars) to {args.refs_output}",
              file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
