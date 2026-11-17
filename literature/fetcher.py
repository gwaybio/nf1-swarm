"""
Literature fetcher for Dirk.

Provides a consistent interface to fetch NF1 papers from:
  - PubMed/NCBI E-utilities (abstracts, metadata, PMC links)
  - PubMed Central (full text for open-access papers)
  - bioRxiv / arXiv (preprints, always free)

Usage:
    from literature.fetcher import PaperFetcher
    f = PaperFetcher(email="gregory.way@gmail.com")

    # Find papers
    pmids = f.search("NF1 neurofibromatosis MEK inhibitor", max_results=10)

    # Fetch a paper
    paper = f.fetch(pmid="32187458")
    print(paper.title, paper.abstract, paper.full_text)
"""
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import quote

import requests


ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PMC_OA_BASE = "https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi"
BIORXIV_API = "https://api.biorxiv.org/details"


@dataclass
class Paper:
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    doi: Optional[str] = None
    title: str = ""
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    year: Optional[int] = None
    full_text: Optional[str] = None
    full_text_source: Optional[str] = None  # "pmc", "biorxiv", "arxiv", "unavailable"

    @property
    def has_full_text(self) -> bool:
        return self.full_text is not None

    @property
    def best_identifier(self) -> str:
        return self.doi or self.pmid or self.pmcid or "unknown"


class PaperFetcher:
    """Fetch papers from open academic sources."""

    def __init__(self, email: str = "gregory.way@gmail.com", rate_limit: float = 0.4):
        """
        Args:
            email: Required by NCBI for E-utilities (identifies your app).
            rate_limit: Seconds between requests (NCBI allows 3/sec without key).
        """
        self.email = email
        self.rate_limit = rate_limit
        self._last_request = 0.0

    def _get(self, url: str, params: dict = None, timeout: int = 30) -> requests.Response:
        """Rate-limited GET."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        resp = requests.get(url, params=params, timeout=timeout)
        self._last_request = time.time()
        resp.raise_for_status()
        return resp

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, query: str, max_results: int = 20, db: str = "pubmed") -> list[str]:
        """Search PubMed and return a list of PMIDs."""
        params = {
            "db": db,
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "email": self.email,
            "tool": "nf1-swarm",
        }
        resp = self._get(f"{ENTREZ_BASE}/esearch.fcgi", params=params)
        return resp.json().get("esearchresult", {}).get("idlist", [])

    # ── Fetch by PMID ─────────────────────────────────────────────────────────

    def fetch(self, pmid: str) -> Paper:
        """Fetch a paper by PMID. Attempts full text if available via PMC."""
        paper = self._fetch_summary(pmid)
        if paper.pmcid:
            full_text = self._fetch_pmc_fulltext(paper.pmcid)
            if full_text:
                paper.full_text = full_text
                paper.full_text_source = "pmc"
        if not paper.full_text:
            paper.full_text_source = "unavailable"
        return paper

    def fetch_by_doi(self, doi: str) -> Paper:
        """Fetch a paper by DOI via PubMed ID lookup."""
        pmids = self.search(f"{doi}[doi]", max_results=1)
        if not pmids:
            # Try as preprint
            if "biorxiv" in doi or "10.1101" in doi:
                return self._fetch_biorxiv(doi)
            return Paper(doi=doi, full_text_source="unavailable")
        return self.fetch(pmids[0])

    def _fetch_summary(self, pmid: str) -> Paper:
        """Fetch title, abstract, authors, year, PMCID from NCBI."""
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
            "email": self.email,
            "tool": "nf1-swarm",
        }
        resp = self._get(f"{ENTREZ_BASE}/efetch.fcgi", params=params)
        return _parse_pubmed_xml(resp.text, pmid)

    # ── PMC full text ─────────────────────────────────────────────────────────

    def _fetch_pmc_fulltext(self, pmcid: str) -> Optional[str]:
        """Fetch full text from PubMed Central OAI-PMH. Returns None if unavailable."""
        pmcid_clean = pmcid.replace("PMC", "")
        params = {
            "verb": "GetRecord",
            "identifier": f"oai:pubmedcentral.nih.gov:{pmcid_clean}",
            "metadataPrefix": "pmc",
        }
        try:
            resp = self._get(PMC_OA_BASE, params=params, timeout=45)
            return _extract_text_from_pmc_xml(resp.text)
        except Exception:
            return None

    def check_pmc_availability(self, pmid: str) -> Optional[str]:
        """Return PMCID if paper is in PMC open access, else None."""
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "json",
            "email": self.email,
            "tool": "nf1-swarm",
        }
        resp = self._get(f"{ENTREZ_BASE}/esummary.fcgi", params=params)
        data = resp.json().get("result", {}).get(pmid, {})
        return data.get("pmcid") or None

    # ── bioRxiv ───────────────────────────────────────────────────────────────

    def _fetch_biorxiv(self, doi: str) -> Paper:
        """Fetch preprint from bioRxiv API."""
        clean_doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
        try:
            resp = self._get(f"{BIORXIV_API}/biorxiv/{clean_doi}")
            collection = resp.json().get("collection", [])
            if not collection:
                return Paper(doi=doi, full_text_source="unavailable")
            item = collection[-1]  # Latest version
            return Paper(
                doi=doi,
                title=item.get("title", ""),
                abstract=item.get("abstract", ""),
                authors=[item.get("authors", "")],
                journal="bioRxiv",
                year=int(item.get("date", "2000")[:4]),
                full_text=item.get("abstract"),  # bioRxiv API only returns abstract
                full_text_source="biorxiv",
            )
        except Exception:
            return Paper(doi=doi, full_text_source="unavailable")


# ── XML parsers ───────────────────────────────────────────────────────────────

def _parse_pubmed_xml(xml: str, pmid: str) -> Paper:
    """Parse PubMed efetch XML into a Paper."""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        article = root.find(".//PubmedArticle")
        if article is None:
            return Paper(pmid=pmid)

        title = article.findtext(".//ArticleTitle") or ""
        abstract_parts = [t.text or "" for t in article.findall(".//AbstractText")]
        abstract = " ".join(abstract_parts)

        authors = []
        for a in article.findall(".//Author"):
            last = a.findtext("LastName") or ""
            fore = a.findtext("ForeName") or ""
            if last:
                authors.append(f"{last} {fore}".strip())

        year_text = article.findtext(".//PubDate/Year") or ""
        year = int(year_text) if year_text.isdigit() else None
        journal = article.findtext(".//Journal/Title") or ""

        pmcid = None
        for id_el in article.findall(".//ArticleId"):
            if id_el.get("IdType") == "pmc":
                pmcid = id_el.text

        doi = None
        for id_el in article.findall(".//ArticleId"):
            if id_el.get("IdType") == "doi":
                doi = id_el.text

        return Paper(
            pmid=pmid,
            pmcid=pmcid,
            doi=doi,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            year=year,
        )
    except Exception:
        return Paper(pmid=pmid)


def _extract_text_from_pmc_xml(xml: str) -> Optional[str]:
    """Extract readable text from PMC OAI-PMH XML response."""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        # Collect all text nodes from body sections
        ns = {"pmc": "https://jats.nlm.nih.gov/ns/archiving/1.1/"}
        parts = []
        for elem in root.iter():
            if elem.tag in {"p", "title", "sec", "abstract"}:
                text = "".join(elem.itertext()).strip()
                if text:
                    parts.append(text)
        text = "\n\n".join(parts)
        return text if len(text) > 200 else None
    except Exception:
        return None
