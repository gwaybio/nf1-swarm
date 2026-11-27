#!/usr/bin/env python3
"""
Citation-to-PMID resolver with title verification.

Resolves free-text reference entries to verified PMIDs using NCBI
E-utilities.  Designed to process the references section output from
text_cleaner.py.

Usage:
    # Resolve a references file (one ref per line or numbered list)
    uv run python literature/cite_resolver.py --refs references.txt

    # Verify a single PMID matches expected paper
    uv run python literature/cite_resolver.py --verify 2116237 \
        --expected-title "neurofibromatosis type 1 gene encodes"

    # Resolve a single DOI
    uv run python literature/cite_resolver.py --doi 10.1056/NEJMoa1912735

Output is compact JSON: ref_number, pmid, title, match_confidence.
Never dumps full abstracts — IDs and short titles only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from urllib.request import urlopen

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_RATE_DELAY = 0.34   # seconds between calls without API key (3/sec limit)
_CACHE_PATH = Path(__file__).parent.parent / "data" / ".cite_cache.json"


# ── NCBI helpers ──────────────────────────────────────────────────────────────

def _load_cache() -> dict[str, str]:
    if _CACHE_PATH.exists():
        try:
            return json.loads(_CACHE_PATH.read_text())
        except Exception:
            pass
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _entrez_get(endpoint: str, params: str) -> str:
    url = f"{ENTREZ_BASE}/{endpoint}.fcgi?{params}&retmode=json"
    with urlopen(url, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _esearch(query: str, retmax: int = 3) -> list[str]:
    """Return up to retmax PMIDs matching the query."""
    time.sleep(_RATE_DELAY)
    q = quote(query)
    raw = _entrez_get("esearch", f"db=pubmed&term={q}&retmax={retmax}")
    data = json.loads(raw)
    return data.get("esearchresult", {}).get("idlist", [])


def _efetch_summary(pmid: str) -> dict:
    """Fetch the esummary for a single PMID."""
    time.sleep(_RATE_DELAY)
    raw = _entrez_get("esummary", f"db=pubmed&id={pmid}")
    data = json.loads(raw)
    result = data.get("result", {})
    return result.get(pmid, {})


# ── Citation parsing ──────────────────────────────────────────────────────────

_REF_LINE = re.compile(
    r"^\s*(?P<num>\d+)[.\)]\s+(?P<body>.+)$"
)

def parse_reference_lines(text: str) -> list[dict]:
    """
    Parse a references section into individual entries.

    Returns list of {num, raw} dicts.  Handles both numbered (1. ...) and
    un-numbered references.
    """
    entries = []
    current: Optional[dict] = None

    for line in text.splitlines():
        m = _REF_LINE.match(line)
        if m:
            if current:
                entries.append(current)
            current = {"num": int(m.group("num")), "raw": m.group("body").strip()}
        elif current and line.strip():
            # Continuation of previous reference
            current["raw"] += " " + line.strip()

    if current:
        entries.append(current)

    if not entries:
        # Fallback: treat each non-empty line as one reference
        for i, ln in enumerate(text.splitlines(), 1):
            if ln.strip():
                entries.append({"num": i, "raw": ln.strip()})

    return entries


def _extract_query_parts(raw: str) -> tuple[str, str]:
    """
    Extract (title_fragment, first_author_surname) from a raw reference string.

    Heuristic: title is the longest quoted string, or the text between the
    first '. ' and the next '. '.  Author surname is the first token that
    looks like a capitalized word before a comma.
    """
    # Try to find a quoted title
    quoted = re.findall(r'"([^"]{10,})"', raw)
    if quoted:
        title = quoted[0]
    else:
        # Take everything after the first author block (up to next period)
        # Remove year patterns like (2020) or 2020;
        no_year = re.sub(r"\(\d{4}\)|\b\d{4}\b", "", raw)
        # Try: "Surname X, Surname2 Y. Title fragment. Journal..."
        parts = no_year.split(". ")
        title = parts[1].strip() if len(parts) > 1 else parts[0].strip()

    # First author surname: first word-group before a comma or space+initial
    author_m = re.match(r"([A-Z][a-zA-Z\-]+)", raw)
    author = author_m.group(1) if author_m else ""

    return title[:120], author


def _confidence(summary: dict, title_fragment: str) -> float:
    """Return 0–1 confidence score based on title similarity."""
    pub_title = (summary.get("title") or "").lower()
    fragment = title_fragment.lower()
    if not pub_title or not fragment:
        return 0.0
    words = [w for w in fragment.split() if len(w) > 3]
    # Short but meaningful biomedical terms (e.g. "NF1", "RAS") must still be compared.
    if not words:
        words = [w for w in fragment.split() if len(w) >= 2]
    if not words:
        return 0.0   # nothing to compare — do not spuriously pass
    hits = sum(1 for w in words if w in pub_title)
    return round(hits / len(words), 2)


# ── Core API ──────────────────────────────────────────────────────────────────

def resolve_pmid(raw_ref: str, cache: Optional[dict] = None) -> dict:
    """
    Resolve a single raw reference string to a PMID.

    Returns:
        {pmid, title, year, match_confidence, query_used, cached}
    """
    if cache is None:
        cache = {}

    cache_key = raw_ref  # use full text — truncation causes collisions
    if cache_key in cache:
        return {**json.loads(cache[cache_key]), "cached": True}

    title_frag, author = _extract_query_parts(raw_ref)
    query = f"{title_frag} {author}".strip()

    pmids = _esearch(query)
    if not pmids:
        # Broaden: title only
        pmids = _esearch(title_frag)

    if not pmids:
        return {"pmid": None, "title": None, "year": None,
                "match_confidence": 0.0, "query_used": query, "cached": False}

    pmid = pmids[0]
    summary = _efetch_summary(pmid)
    pub_title = summary.get("title", "")
    pub_year = summary.get("pubdate", "")[:4]
    conf = _confidence(summary, title_frag)

    result = {"pmid": pmid, "title": pub_title[:120], "year": pub_year,
              "match_confidence": conf, "query_used": query, "cached": False}
    cache[cache_key] = json.dumps({k: v for k, v in result.items() if k != "cached"})
    return result


def verify_pmid(pmid: str, expected_title_fragment: str) -> dict:
    """
    Verify that a PMID matches an expected title fragment.

    Returns {pmid, title, year, match_confidence, verified}.
    """
    summary = _efetch_summary(pmid)
    pub_title = summary.get("title", "")
    pub_year = summary.get("pubdate", "")[:4]
    authors = [a.get("name", "") for a in summary.get("authors", [])[:3]]
    conf = _confidence(summary, expected_title_fragment)
    return {
        "pmid": pmid,
        "title": pub_title,
        "year": pub_year,
        "first_authors": authors,
        "match_confidence": conf,
        "verified": conf >= 0.5,
    }


def resolve_doi(doi: str) -> dict:
    """Resolve a DOI to a PMID via PubMed esearch."""
    clean_doi = doi.strip().lstrip("https://doi.org/").lstrip("http://doi.org/")
    pmids = _esearch(f"{clean_doi}[doi]")
    if not pmids:
        return {"pmid": None, "doi": doi, "match_confidence": 0.0}
    pmid = pmids[0]
    summary = _efetch_summary(pmid)
    return {
        "pmid": pmid,
        "doi": doi,
        "title": summary.get("title", "")[:120],
        "year": summary.get("pubdate", "")[:4],
        "match_confidence": 1.0,  # DOI match is exact
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--refs",   metavar="FILE",
                      help="Resolve all references in a file (one per line or numbered)")
    mode.add_argument("--verify", metavar="PMID",
                      help="Verify a PMID matches expected title")
    mode.add_argument("--doi",    metavar="DOI",
                      help="Resolve a DOI to PMID")

    p.add_argument("--expected-title", metavar="FRAGMENT",
                   help="Title fragment for --verify mode")
    p.add_argument("--output",   metavar="FILE",
                   help="Write JSON to file (default: stdout)")
    p.add_argument("--min-confidence", type=float, default=0.0,
                   metavar="N", help="Only output results with confidence >= N")
    p.add_argument("--no-cache", action="store_true",
                   help="Skip the PMID resolution cache")
    args = p.parse_args(argv)

    cache = {} if args.no_cache else _load_cache()

    if args.verify:
        if not args.expected_title:
            print("ERROR: --verify requires --expected-title", file=sys.stderr)
            return 1
        result = verify_pmid(args.verify, args.expected_title)
        output = json.dumps(result, indent=2)

    elif args.doi:
        result = resolve_doi(args.doi)
        output = json.dumps(result, indent=2)

    else:
        text = Path(args.refs).read_text(encoding="utf-8", errors="replace")
        entries = parse_reference_lines(text)
        results = []
        for e in entries:
            r = resolve_pmid(e["raw"], cache)
            if r["match_confidence"] >= args.min_confidence:
                results.append({"ref_num": e["num"], **r})
            # Print progress to stderr so stdout stays clean JSON
            status = r["pmid"] or "UNRESOLVED"
            print(f"  [{e['num']:>3}] {status}  conf={r['match_confidence']:.2f}",
                  file=sys.stderr)
        output = json.dumps(results, indent=2)
        if not args.no_cache:
            _save_cache(cache)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote to {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
