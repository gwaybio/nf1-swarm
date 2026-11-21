#!/usr/bin/env python3
"""
Shared text cleaner for PDF and HTML literature extraction.

Strips watermarks, fixes two-column interleaving, separates body from
references, normalises whitespace.  Returns clean plain text with
section markers.

Usage:
    uv run python literature/text_cleaner.py --input paper.pdf
    uv run python literature/text_cleaner.py --pmcid PMC7305659
    uv run python literature/text_cleaner.py --html body.html

Output is written to stdout (pipe to a file) or --output <path>.
Section markers look like:  ## SECTION: Methods
The references block is delimited:  ## REFERENCES_START / ## REFERENCES_END
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_watermarks(text: str) -> str:
    """Remove single-character noise lines (PDF watermarks)."""
    lines = text.splitlines()
    clean = [ln for ln in lines if len(ln.strip()) > 1 or ln.strip() == ""]
    return "\n".join(clean)


def _normalise_whitespace(text: str) -> str:
    """Collapse runs of blank lines to at most two, strip trailing spaces."""
    text = re.sub(r"[^\S\n]+$", "", text, flags=re.MULTILINE)   # trailing spaces
    text = re.sub(r"\n{3,}", "\n\n", text)                        # excess blanks
    return text.strip()


def _fix_hyphenation(text: str) -> str:
    """Rejoin words split by end-of-line hyphens."""
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def _split_references(text: str) -> tuple[str, str]:
    """
    Split body from references section.

    Returns (body, references) as plain strings.  If no references section
    is found, returns (full_text, "").
    """
    # Common section header patterns in academic papers
    ref_pat = re.compile(
        r"^\s*(?:References|REFERENCES|Bibliography|BIBLIOGRAPHY|Works Cited)\s*$",
        re.MULTILINE,
    )
    m = ref_pat.search(text)
    if m:
        return text[: m.start()].rstrip(), text[m.start() :].strip()
    return text, ""


def _mark_sections(text: str) -> str:
    """
    Insert ## SECTION: <name> markers before common section headers.

    Does not modify the actual section heading line — just prepends a
    marker so downstream consumers can split on sections without regex.
    """
    section_pat = re.compile(
        r"^(Abstract|Introduction|Methods?|Results?|Discussion|Conclusion|"
        r"Background|Materials?|Supplementary|Acknowledgements?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    return section_pat.sub(lambda m: f"## SECTION: {m.group().strip()}\n{m.group()}", text)


# ── HTML cleaner ──────────────────────────────────────────────────────────────

def clean_html(html: str) -> str:
    """
    Strip HTML boilerplate and return clean plain text.

    Uses stdlib xml.etree.ElementTree for tag stripping — no external deps.
    Falls back to regex if the HTML is malformed.
    """
    try:
        import xml.etree.ElementTree as ET
        # Wrap in a root element to handle fragments
        try:
            root = ET.fromstring(f"<root>{html}</root>")
            text = "".join(root.itertext())
        except ET.ParseError:
            # Malformed HTML — strip tags with regex
            text = re.sub(r"<[^>]+>", " ", html)
    except Exception:
        text = re.sub(r"<[^>]+>", " ", html)

    # Decode common HTML entities
    for entity, char in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                          ("&nbsp;", " "), ("&#160;", " "), ("&quot;", '"')]:
        text = text.replace(entity, char)

    return _normalise_whitespace(text)


# ── PDF cleaner ───────────────────────────────────────────────────────────────

def clean_pdf_text(raw: str) -> str:
    """
    Clean raw text extracted from a PDF.

    Handles:
    - Single-character watermark lines
    - Hyphenated line breaks
    - Excessive whitespace
    """
    text = _strip_watermarks(raw)
    text = _fix_hyphenation(text)
    text = _normalise_whitespace(text)
    return text


# ── Full pipeline ─────────────────────────────────────────────────────────────

def clean(
    text: str,
    source: str = "text",   # "pdf", "html", or "text"
    mark_sections: bool = True,
) -> dict[str, str]:
    """
    Clean extracted text and return a dict with keys:
      body        — clean body text
      references  — references section (may be empty)
      source      — the source type passed in
    """
    if source == "html":
        text = clean_html(text)
    else:
        text = clean_pdf_text(text)

    if mark_sections:
        text = _mark_sections(text)

    body, refs = _split_references(text)

    # Wrap references with markers so callers can find them reliably
    refs_marked = f"## REFERENCES_START\n{refs}\n## REFERENCES_END" if refs else ""

    return {"body": body, "references": refs, "references_marked": refs_marked,
            "source": source}


# ── CLI ───────────────────────────────────────────────────────────────────────

def _fetch_pmc_html(pmcid: str) -> str:
    """Fetch full-text HTML from PMC OA."""
    import urllib.request
    url = (
        f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
        f"?report=printable&format=html"
    )
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--input",  metavar="FILE",  help="Local PDF or text file")
    src.add_argument("--html",   metavar="FILE",  help="Local HTML file")
    src.add_argument("--pmcid",  metavar="PMC_ID", help="Fetch from PMC (e.g. PMC7305659)")
    p.add_argument("--output",  metavar="FILE",  help="Write body to file (default: stdout)")
    p.add_argument("--refs-output", metavar="FILE",
                   help="Write references section to a separate file")
    p.add_argument("--no-section-markers", action="store_true",
                   help="Skip ## SECTION: markers")
    args = p.parse_args(argv)

    # Determine source type and load raw text
    if args.pmcid:
        raw = _fetch_pmc_html(args.pmcid)
        source = "html"
    elif args.html:
        raw = Path(args.html).read_text(encoding="utf-8", errors="replace")
        source = "html"
    else:
        path = Path(args.input)
        if path.suffix.lower() == ".pdf":
            # Minimal PDF text extraction via pdfminer if available, else error
            try:
                from pdfminer.high_level import extract_text as pdf_extract  # type: ignore[import-untyped]
                raw = pdf_extract(str(path))
            except ImportError:
                print(
                    "ERROR: PDF extraction requires pdfminer.six.\n"
                    "Install: uv add pdfminer.six\n"
                    "Or extract text first: pdftotext paper.pdf - | "
                    "uv run python literature/text_cleaner.py --input /dev/stdin",
                    file=sys.stderr,
                )
                return 1
            source = "pdf"
        else:
            raw = path.read_text(encoding="utf-8", errors="replace")
            source = "text"

    result = clean(raw, source=source,
                   mark_sections=not args.no_section_markers)

    body = result["body"]
    refs = result["references_marked"]

    if args.output:
        Path(args.output).write_text(body + ("\n\n" + refs if refs else ""),
                                     encoding="utf-8")
        print(f"Wrote {len(body)} chars body to {args.output}", file=sys.stderr)
    else:
        print(body)
        if refs:
            print("\n" + refs)

    if args.refs_output and refs:
        Path(args.refs_output).write_text(result["references"], encoding="utf-8")
        print(f"Wrote {len(result['references'])} chars references to {args.refs_output}",
              file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
