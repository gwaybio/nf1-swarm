# Methods — nf1-swarm

This document describes the methodological foundations of the nf1-swarm knowledge graph
pipeline and situates our approach relative to the state of the art.

---

## Claim extraction

### Our approach: FETA-inspired two-stage extraction

We implement a protocol inspired by FETA (First Extract, Tag Afterwards):

> Shlyk D, Montanelli S, Mesiti M, Hunter L. "Mind Your Steps in Biomedical Named
> Entity Recognition: First Extract, Tag Afterwards."
> *Proceedings of the 1st Workshop on Linguistic Analysis for Health (HeaLing 2026)*,
> pp. 127–141. DOI: [10.18653/v1/2026.healing-1.11](https://doi.org/10.18653/v1/2026.healing-1.11)

**Stage 1 — Extract (Dirk):** Identify candidate claim sentences from full text using
heuristic pattern matching followed by LLM review. Each candidate is a falsifiable,
declarative statement. No ontology grounding at this stage — this separation is the
key FETA insight: LLMs hallucinate ontology IDs when asked to do both steps simultaneously.

**Stage 2 — Tag (Otto):** Ground each extracted entity to a canonical CURIE using
RTX-KG2 as the primary oracle. Self-verification step: Otto confirms the CURIE resolves
to the intended concept before accepting it. Fills `semantic_triple` and optional
`bel_notation` in the claim JSON.

### Comparison to other state-of-the-art methods

| Method | Approach | Coverage | Our use |
|--------|----------|----------|---------|
| **FETA** (Shlyk et al., 2026) | Two-stage LLM NER | Multiple biomedical benchmarks | Direct inspiration for extraction protocol |
| **SciClaims** (EMNLP 2025) | End-to-end extraction + verification | SciFact benchmark | Inspires our extract→verify→curate pipeline |
| **SemRep/SemMedDB** (NLM) | Rule-based, UMLS-grounded | 37M PubMed abstracts | Deprecated Dec 2024; superseded by RTX-KG2 |
| **BEL** (OpenBEL) | Formal language for biology | Standard | Optional `bel_notation` field in claim schema |
| **Biolink Model** (NCATS) | Standardized predicates | 73 KG sources | Edge types in DESIGN.md aligned to Biolink |

### Pipeline design

The pipeline couples FETA extraction (Dirk/Otto) with claim verification (Archie),
statistical confidence assessment (Stan), PI-level curation (Rey), and graph
insertion (Kim). Each step is logged to Git and tracked via GitHub issues.

SciClaims (EMNLP 2025) describes a related end-to-end automated pipeline for claim
extraction, evidence retrieval, and verification. This pipeline follows a similar
structure but includes manual curation steps appropriate for a small, high-stakes
rare disease knowledge base.

---

## Knowledge graph backbone: RTX-KG2

We use RTX-KG2 as our external knowledge oracle rather than querying each upstream
source individually:

> Chamberlain MT et al. "RTX-KG2: a system for building a semantically standardized
> knowledge graph for translational biomedicine."
> *BMC Bioinformatics* 2023. PMID: 36604637

RTX-KG2 integrates 73+ sources (SemMedDB, UniProt, DrugBank, ChEMBL, DisGeNET,
OMIM, Orphanet, HPO, Reactome, GO, GTEx, STRING, and more) into a single
Biolink-compliant graph queryable via TRAPI at `https://kg2cploverdb.transltr.io/query`.

**We use RTX-KG2 for three distinct purposes:**
1. **Otto:** Entity grounding (name → canonical CURIE)
2. **Otto / Kim:** Edge existence check — before writing a Claim edge to our graph,
   check whether RTX-KG2 already has this relationship and how many sources support it
3. **Stan:** Corroborating source enumeration for publication bias analysis —
   how many independent sources in RTX-KG2 support a claimed relationship?

**Periodic validation:** Because RTX-KG2 represents the aggregate literature up to
its last build, we periodically re-run Otto's grounding on accepted claims to catch
any CURIE deprecations or ontology term merges.

---

## Publication bias and confidence scoring

Evidence_strength (1–5) is a human judgment about a **single paper**. It does not
account for the possibility that multiple confirmatory papers reflect publication bias,
same-lab replication, or correlated datasets.

We draw on the meta-analysis literature for a separate `confidence_score`:

> Bartoš F et al. "Footprint of publication selection bias on meta-analyses in
> medicine, environmental sciences, psychology, and economics."
> *Research Synthesis Methods* 2024. DOI: 10.1002/jrsm.1703

> Langan D et al. "Rethinking publication bias analysis methods in clinical
> meta-analyses." *[PMC13244164]* 2026.

**Stan's approach:**
- N=1,2: confidence scoring premature; flag as "insufficient replication"
- N≥3: apply RoBMA-PSMA (Bayesian model averaging) if study precision estimates
  available; otherwise report descriptive heterogeneity
- N≥10: full PET-PEESE; Egger's test for small-study effects
- Always report both unadjusted and bias-adjusted estimates
- Flag `independence_flags` when correlated evidence is detected

**Key principle:** `confidence_score` is Stan's output, not a replacement for
`evidence_strength`. Rey uses both when making curation decisions.

---

## Acknowledgements

This project is inspired by and builds on the work of:

- **Lawrence E. Hunter** (University of Chicago) — foundational biomedical NLP,
  FETA extraction framework, BioCreative evaluation standards
- **NCATS Translator Program** — RTX-KG2 and the TRAPI standard
- **NLM/NCBI** — PubMed, PMC E-utilities, SemMedDB (now incorporated into RTX-KG2)
- **OpenBEL Community** — Biological Expression Language standard
- **Biolink Model** — standardized biomedical knowledge graph predicates
- **Ioannidis JPA** (2005) — "Why Most Published Research Findings Are False" —
  the founding paper for our skepticism about raw citation counts
