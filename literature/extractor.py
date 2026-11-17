"""
FETA-inspired biomedical claim extractor for Dirk.

Implements the two-stage extraction protocol from:
  Shlyk, Montanelli, Mesiti, Hunter (2026).
  "Mind Your Steps in Biomedical Named Entity Recognition: First Extract,
  Tag Afterwards."
  Proceedings of the 1st Workshop on Linguistic Analysis for Health (HeaLing 2026),
  pp. 127-141. DOI: 10.18653/v1/2026.healing-1.11

Stage 1 — EXTRACT: Identify candidate claim sentences from full text,
  using instruction-guided prompting. No ontology grounding yet.

Stage 2 — TAG (Otto's job): Ground extracted entities to canonical CURIEs
  using RTX-KG2. Self-verification step confirms grounding is correct.

Relationship to other state-of-the-art methods:
  - SciClaims (EMNLP 2025): end-to-end claim extraction + verification, LLM-based.
    We draw on its pipeline design (extract -> retrieve evidence -> verify).
  - SemRep/SemMedDB (NLM): subject-PREDICATE-object triples over UMLS. Deprecated
    Dec 2024, superseded by RTX-KG2 which incorporates it plus 72 other sources.
  - BEL (Biological Expression Language): open standard for computable biology.
    We produce optional bel_notation for molecular_function/pathway claims.

Usage:
    from literature.extractor import extract_candidate_claims
    candidates = extract_candidate_claims(paper.full_text or paper.abstract,
                                          pmid=paper.pmid)
"""
import re
from dataclasses import dataclass, field
from typing import Optional


# NF1-relevant claim types (matches claims/schema.json)
CLAIM_TYPES = [
    "molecular_function",
    "pathway_interaction",
    "clinical_outcome",
    "genetic_association",
    "drug_response",
    "phenotype_association",
    "model_validation",
]

# Sentence-level patterns that often signal a biological claim
# (heuristic pre-filter before LLM extraction — reduces token cost)
CLAIM_SIGNAL_PATTERNS = [
    r'(causes?|leads? to|results? in|produces?)',
    r'(inhibits?|activates?|regulates?|modulates?|interacts? with)',
    r'(treats?|reduces?|improves?|decreases?|increases?)',
    r'(associated with|linked to|correlated with)',
    r'(pathogenic variant|mutation|loss.of.function|gain.of.function)',
    r'(significantly|p\s*[<=>]\s*0\.\d+|confidence interval|hazard ratio)',
    r'(approved|phase [123]|randomized|placebo.controlled)',
]
_SIGNAL_RE = re.compile('|'.join(CLAIM_SIGNAL_PATTERNS), re.IGNORECASE)


@dataclass
class CandidateClaim:
    """
    Stage 1 output: a candidate claim sentence before ontology grounding.
    Otto converts these to full Claim JSON with semantic_triple filled in.
    """
    sentence: str
    claim_type_hint: Optional[str] = None  # rough category, unverified
    entities_mentioned: list[str] = field(default_factory=list)  # raw names, not CURIEs yet
    source_pmid: Optional[str] = None
    source_doi: Optional[str] = None
    context_window: str = ""  # surrounding sentences for Otto


def extract_candidate_claims(text: str,
                              pmid: str = None,
                              doi: str = None,
                              min_sentence_len: int = 40) -> list[CandidateClaim]:
    """
    Stage 1 — EXTRACT: Find candidate claim sentences from paper text.

    This is a heuristic pre-filter. Dirk should then review these with
    biological understanding and pass confirmed candidates to Otto for
    Stage 2 grounding.

    The full FETA protocol additionally applies an LLM self-verification
    step — Dirk implements this by reviewing each candidate and confirming
    it is a genuinely falsifiable claim about NF1 biology before tagging.

    Args:
        text: Full text or abstract of a paper.
        pmid: PubMed ID of the source paper.
        doi: DOI of the source paper.
        min_sentence_len: Minimum sentence length to consider (filters noise).

    Returns:
        List of CandidateClaim objects ready for Dirk's review.
    """
    sentences = _split_sentences(text)
    candidates = []

    for i, sentence in enumerate(sentences):
        if len(sentence) < min_sentence_len:
            continue
        if not _SIGNAL_RE.search(sentence):
            continue

        # Build a context window (surrounding sentences)
        start = max(0, i - 1)
        end = min(len(sentences), i + 2)
        context = " ".join(sentences[start:end])

        entities = _extract_entity_mentions(sentence)
        claim_type = _guess_claim_type(sentence)

        candidates.append(CandidateClaim(
            sentence=sentence.strip(),
            claim_type_hint=claim_type,
            entities_mentioned=entities,
            source_pmid=pmid,
            source_doi=doi,
            context_window=context,
        ))

    return candidates


def _split_sentences(text: str) -> list[str]:
    """Simple sentence splitter adequate for biomedical text."""
    # Split on ". " followed by capital letter, or on newlines
    text = text.replace(chr(10), " ")  # normalize newlines
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

    return [s.strip() for s in sentences if s.strip()]


def _extract_entity_mentions(sentence: str) -> list[str]:
    """
    Rough entity detection — capitalized multi-word phrases and known NF1 terms.
    Otto will ground these to CURIEs in Stage 2.
    """
    entities = []

    # Known NF1-relevant terms (expand over time)
    known = [
        "NF1", "neurofibromin", "neurofibromatosis", "RAS", "MEK", "ERK",
        "selumetinib", "binimetinib", "MPNST", "plexiform neurofibroma",
        "optic pathway glioma", "cafe-au-lait", "Nf1", "MAPK", "mTOR", "PI3K",
    ]
    sentence_lower = sentence.lower()
    for term in known:
        if term.lower() in sentence_lower:
            entities.append(term)

    # Capitalized noun phrases (rough heuristic)
    caps = re.findall(r'[A-Z][A-Za-z0-9]+(?: [A-Z][A-Za-z0-9]+)*', sentence)
    for cap in caps:
        if cap not in entities and len(cap) > 2:
            entities.append(cap)

    return list(dict.fromkeys(entities))  # deduplicate, preserve order


def _guess_claim_type(sentence: str) -> Optional[str]:
    """Rough claim type classification — Dirk confirms in Stage 1 review."""
    s = sentence.lower()
    if any(w in s for w in ["treat", "trial", "patient", "clinical", "response rate"]):
        return "clinical_outcome"
    if any(w in s for w in ["mutation", "variant", "genotype", "allele", "loh"]):
        return "genetic_association"
    if any(w in s for w in ["inhibit", "drug", "compound", "ic50", "efficacy"]):
        return "drug_response"
    if any(w in s for w in ["phenotype", "feature", "freckling", "nodule", "fibroma"]):
        return "phenotype_association"
    if any(w in s for w in ["pathway", "signaling", "cascade", "activate", "phosphorylat"]):
        return "pathway_interaction"
    if any(w in s for w in ["mouse", "knockout", "cell line", "model", "in vitro", "in vivo"]):
        return "model_validation"
    return "molecular_function"
