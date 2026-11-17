"""
verify_paper.py — Pre-flight PMID/DOI verification for Graude.

Graude calls this before opening any [DIRK] issue to confirm the paper
identifier is correct and resolves to the expected title/journal/year.
Prevents hallucinated or misremembered PMIDs from reaching Dirk.

Usage:
    uv run python scripts/verify_paper.py 2116237
    uv run python scripts/verify_paper.py --doi 10.1016/0092-8674(90)90024-9
    uv run python scripts/verify_paper.py --search "NF1 neurofibromin RAS-GAP Xu 1990"
"""
import argparse
import json
import sys
import time
import urllib.request
from urllib.parse import quote

ENTREZ = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EMAIL = "gregory.way@gmail.com"


def _get(url: str) -> dict:
    req = urllib.request.Request(
        url, headers={"Accept": "application/json", "User-Agent": f"nf1-swarm ({EMAIL})"}
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def verify_pmid(pmid: str) -> dict:
    """Fetch paper metadata from PubMed by PMID."""
    url = f"{ENTREZ}/esummary.fcgi?db=pubmed&id={pmid}&retmode=json&tool=nf1-swarm&email={EMAIL}"
    data = _get(url)
    rec = data.get("result", {}).get(str(pmid), {})
    if not rec or rec.get("error"):
        return {"error": f"PMID {pmid} not found in PubMed"}
    doi = next((x["value"] for x in rec.get("articleids", []) if x["idtype"] == "doi"), None)
    pmcid = next((x["value"] for x in rec.get("articleids", []) if x["idtype"] == "pmc"), None)
    return {
        "pmid": pmid,
        "title": rec.get("title", ""),
        "journal": rec.get("source", ""),
        "year": rec.get("pubdate", "")[:4],
        "authors": [a["name"] for a in rec.get("authors", [])[:3]],
        "doi": doi,
        "pmcid": pmcid,
        "open_access": pmcid is not None,
    }


def search_pmid(query: str, max_results: int = 5) -> list[dict]:
    """Search PubMed and return top matches."""
    url = (f"{ENTREZ}/esearch.fcgi?db=pubmed&term={quote(query)}"
           f"&retmax={max_results}&retmode=json&tool=nf1-swarm&email={EMAIL}")
    data = _get(url)
    pmids = data.get("esearchresult", {}).get("idlist", [])
    results = []
    for pmid in pmids:
        time.sleep(0.35)  # NCBI rate limit
        results.append(verify_pmid(pmid))
    return results


def _print_result(r: dict):
    if "error" in r:
        print(f"  ERROR: {r['error']}")
        return
    authors = ", ".join(r.get("authors", [])) + (" et al." if len(r.get("authors", [])) == 3 else "")
    oa = "✓ Open Access (PMC)" if r.get("open_access") else "✗ Not in PMC (abstract only)"
    print(f"  PMID:    {r['pmid']}")
    print(f"  Title:   {r['title'][:90]}")
    print(f"  Journal: {r['journal']}  ({r['year']})")
    print(f"  Authors: {authors}")
    print(f"  DOI:     {r.get('doi', 'none')}")
    print(f"  Access:  {oa}")


def main():
    parser = argparse.ArgumentParser(description="Verify a paper PMID or DOI before assigning to Dirk")
    parser.add_argument("pmid", nargs="?", help="PubMed ID to verify")
    parser.add_argument("--doi", help="DOI to look up (finds PMID first)")
    parser.add_argument("--search", help="Free-text query to find the right PMID")
    args = parser.parse_args()

    if args.pmid:
        print(f"\nVerifying PMID {args.pmid}...\n")
        _print_result(verify_pmid(args.pmid))

    elif args.doi:
        print(f"\nSearching for DOI {args.doi}...\n")
        results = search_pmid(f"{args.doi}[doi]", max_results=1)
        if results:
            _print_result(results[0])
        else:
            print("  Not found via DOI search.")

    elif args.search:
        print(f"\nSearching PubMed for: {args.search!r}\n")
        results = search_pmid(args.search)
        for i, r in enumerate(results, 1):
            print(f"  --- Result {i} ---")
            _print_result(r)
            print()

    else:
        parser.print_help()
        sys.exit(1)

    print()


if __name__ == "__main__":
    main()
