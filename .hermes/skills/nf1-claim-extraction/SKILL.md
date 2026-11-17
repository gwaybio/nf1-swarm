---
name: nf1-claim-extraction
description: FETA two-stage NF1 claim extraction and grounding.
version: 0.1.0
author: Gregory Way (gwaybio), Hermes Agent
license: BSD-3-Clause
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [NF1, claim-extraction, FETA, ontology, RTX-KG2, biomedical-NLP]
    related_skills: [arxiv, grounded-citations]
---

# NF1 Claim Extraction

Two-stage biomedical claim extraction protocol for the nf1-swarm project.
Full citations for all referenced work are in `CITATION.cff`.

## Methodological basis

The extraction protocol follows **FETA** (First Extract, Tag Afterwards):

> Shlyk D, Montanelli S, Mesiti M, Hunter L (2026). "Mind Your Steps in
> Biomedical Named Entity Recognition: First Extract, Tag Afterwards."
> *HeaLing 2026*, pp. 127–141. DOI: 10.18653/v1/2026.healing-1.11

FETA's core finding: separating entity extraction from ontology grounding
improves accuracy because LLMs hallucinate ontology identifiers when asked
to do both simultaneously. Stage 1 extracts; Stage 2 grounds.

The extract → verify → curate pipeline structure follows **SciClaims**
(Ortega & Gómez-Pérez, EMNLP 2025, DOI: 10.18653/v1/2025.emnlp-demos.11),
which integrates claim extraction, evidence retrieval, and LLM-based
SUPPORT/REFUTE/NEI verification into a single end-to-end system.

For entity grounding (Stage 2), we use **RTX-KG2** (Chamberlain et al., 2023)
as the primary oracle — 73+ biomedical knowledge sources in a single
Biolink-compliant TRAPI graph at `https://kg2cploverdb.transltr.io/query`.
This supersedes direct SemMedDB queries; SemMedDB (Kilicoglu & Shin, 2012)
was deprecated by NLM in December 2024 and is now incorporated into RTX-KG2.

For identifying knowledge gaps in the NF1 literature to prioritize reading,
see **GAPMAP** (Salem, White, Bada, Hunter, 2025, arXiv:2510.25055).

## When to Use

- Dirk: extracting structured claims from NF1 papers
- Otto: grounding extracted entities to canonical CURIEs via RTX-KG2
- Don't use for: general web research, non-NF1 biology

## Prerequisites

- Repo at `~/repos/nf1-swarm`
- Neo4j running: `sudo systemctl start neo4j`
- Python env: `cd ~/repos/nf1-swarm` (use `uv run python ...`)
- RTX-KG2 API: `https://kg2cploverdb.transltr.io/query`

## Stage 1 — Extract (Dirk)

**Goal:** Identify falsifiable claim sentences. Do NOT ground to ontology yet.

1. Fetch paper:
   ```python
   from literature.fetcher import PaperFetcher
   f = PaperFetcher()
   paper = f.fetch(pmid="32187458")
   ```

2. Run heuristic pre-filter:
   ```python
   from literature.extractor import extract_candidate_claims
   candidates = extract_candidate_claims(paper.full_text or paper.abstract,
                                         pmid=paper.pmid)
   ```

3. **Self-verification (the FETA step):** For each candidate, confirm:
   - Is this a declarative, falsifiable statement?
   - Does it concern NF1 biology or clinical outcomes?
   - Is the `claim_type_hint` correct?
   - Discard candidates that fail these checks.

4. Assign `evidence_strength` per `testing/specs/evidence_rubric.yaml`.
   Cap at 3 when only abstract is available.

5. Reserve a claim ID (never assign manually):
   ```python
   from neo4j import GraphDatabase
   from knowledge_graph.queries.reserve_claim_id import next_claim_id
   d = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "nf1swarm"))
   with d.session() as s:
       cid = next_claim_id(s)
   ```

6. Write JSON to `claims/pending/<cid>.json` per `claims/schema.json`.
   Leave `semantic_triple` and `bel_notation` as `null` — Otto fills these.

7. Validate: `uv run python testing/harness/claim_validator.py`

8. Commit: `git commit -m "claim(dirk): <paper short title>"`

## Stage 2 — Tag (Otto)

**Goal:** Ground entities to canonical CURIEs. Check RTX-KG2 for existing evidence.

1. Ground each entity:
   ```python
   from literature.rtx_kg2 import ground_entity
   nodes = ground_entity("neurofibromin", ["biolink:Protein"])
   # [{"id": "UniProt:P21359", "name": "Neurofibromin", ...}]
   ```

2. Self-verification: confirm the CURIE resolves to the intended concept.
   If ambiguous, use `claim_text` context to disambiguate.
   Document ontology version used in claim `notes`.

3. Check if the relationship already exists in RTX-KG2:
   ```python
   from literature.rtx_kg2 import check_edge_exists
   existing = check_edge_exists(
       "CHEMBL.COMPOUND:CHEMBL1614701", "HP:0009732",
       predicates=["biolink:treats"]
   )
   # If existing: add pmids to supporting_dois; report n_sources to Stan
   ```

4. Fill `semantic_triple`:
   ```json
   {
     "subject": "Selumetinib",
     "subject_id": "CHEMBL.COMPOUND:CHEMBL1614701",
     "predicate": "TREATS",
     "object": "Plexiform neurofibroma",
     "object_id": "HP:0009732"
   }
   ```

5. Optional `bel_notation` for molecular/pathway claims:
   `a(CHEBI:"selumetinib") -| kin(p(HGNC:MAP2K1))`

6. Commit: `git commit -m "ontology(otto): ground <claim_id>"`

## Quick Reference

```python
from literature.fetcher import PaperFetcher           # Stage 1: fetch
from literature.extractor import extract_candidate_claims  # Stage 1: extract
from literature.rtx_kg2 import ground_entity, check_edge_exists  # Stage 2: tag
from knowledge_graph.queries.reserve_claim_id import next_claim_id
```
```bash
uv run python testing/harness/claim_validator.py
```

## Pitfalls

1. **Never ground entities in Stage 1.** Core FETA principle.
2. **SemMedDB is deprecated** (Dec 2024). Use RTX-KG2.
3. **Ambiguous CURIEs:** NF1 gene = `NCBIGene:4763`; NF1 disease = `MONDO:0009981`.
4. **Abstract-only:** Cap `evidence_strength` at 3; note in `notes` field.

## Verification

- Stage 1: JSON in `claims/pending/`, passes `claim_validator.py`, committed
- Stage 2: `semantic_triple.subject_id` and `object_id` resolve in RTX-KG2;
  `bel_notation` set for molecular claims; committed
