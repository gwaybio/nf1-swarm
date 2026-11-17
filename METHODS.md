# Methods — nf1-swarm

This document describes the methodological foundations of the nf1-swarm knowledge graph
pipeline and situates our approach relative to the state of the art.

---

## Claim extraction

### FETA two-stage protocol

The extraction protocol follows FETA (First Extract, Tag Afterwards) [1].

Stage 1 (Dirk) identifies candidate claim sentences from full text using
heuristic pattern matching followed by LLM review. No ontology grounding
at this stage — LLMs hallucinate ontology identifiers when asked to extract
and ground simultaneously [1].

Stage 2 (Otto) grounds each extracted entity to a canonical CURIE using
RTX-KG2 [3] as the primary oracle, with a self-verification step to confirm
the CURIE resolves to the intended concept.

### Evidence retrieval and verification

The extract → verify → curate pipeline structure follows SciClaims [2],
which integrates claim extraction, PubMed evidence retrieval, and LLM-based
SUPPORT/REFUTE/NEI verdict into a single system. This pipeline uses separate
agents (Dirk, Otto, Archie, Rey) for each stage rather than a single model.

### Comparison to other approaches

| Method | Reference | Our use |
|--------|-----------|---------|
| FETA | Shlyk et al., HeaLing 2026 [1] | Extraction protocol |
| SciClaims | Ortega & Gómez-Pérez, EMNLP 2025 [2] | Pipeline structure |
| SemRep/SemMedDB | Kilicoglu et al. [5,6] | Predicate vocabulary; deprecated Dec 2024 |
| BEL | OpenBEL Community | Optional `bel_notation` field |
| Biolink Model | NCATS Translator | Edge type vocabulary |

### Pipeline design

The pipeline couples FETA extraction (Dirk/Otto) with claim verification
(Archie), statistical confidence assessment (Stan), PI-level curation (Rey),
and graph insertion (Kim). Each step is logged to Git and tracked via GitHub
issues.


---

## Knowledge graph backbone: RTX-KG2

We use RTX-KG2 [3] as our external knowledge oracle:

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

We draw on the meta-analysis literature for a separate `confidence_score` [7,8,9]:

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

## References

Full citation metadata for all referenced works is in `CITATION.cff`.

1. Shlyk D, Montanelli S, Mesiti M, Hunter L. "Mind Your Steps in Biomedical Named Entity Recognition: First Extract, Tag Afterwards." *HeaLing 2026*, pp. 127–141. DOI: [10.18653/v1/2026.healing-1.11](https://doi.org/10.18653/v1/2026.healing-1.11)

2. Ortega R, Gómez-Pérez JM. "SciClaims: An End-to-End Generative System for Biomedical Claim Analysis." *EMNLP 2025 Demos*, pp. 141–154. DOI: [10.18653/v1/2025.emnlp-demos.11](https://doi.org/10.18653/v1/2025.emnlp-demos.11)

3. Chamberlain MT et al. "RTX-KG2: a system for building a semantically standardized knowledge graph for translational biomedicine." *BMC Bioinformatics* 2023. DOI: [10.1186/s12859-023-05311-2](https://doi.org/10.1186/s12859-023-05311-2)

4. Salem NM, White E, Bada M, Hunter L. "GAPMAP: Mapping Scientific Knowledge Gaps in Biomedical Literature Using Large Language Models." arXiv:2510.25055 (2025).

5. Kilicoglu H. "Broad-coverage biomedical relation extraction with SemRep." *BMC Bioinformatics* 2020. DOI: [10.1186/s12859-020-3517-7](https://doi.org/10.1186/s12859-020-3517-7)

6. Kilicoglu H, Shin D et al. "SemMedDB: a PubMed-scale repository of biomedical semantic predications." *Bioinformatics* 2012. DOI: [10.1093/bioinformatics/bts591](https://doi.org/10.1093/bioinformatics/bts591)

7. Ioannidis JPA. "Why Most Published Research Findings Are False." *PLOS Medicine* 2005. DOI: [10.1371/journal.pmed.0020124](https://doi.org/10.1371/journal.pmed.0020124)

8. Bartoš F et al. "Footprint of publication selection bias on meta-analyses in medicine, environmental sciences, psychology, and economics." *Research Synthesis Methods* 2024. DOI: [10.1002/jrsm.1703](https://doi.org/10.1002/jrsm.1703)

9. Langan D et al. "Rethinking publication bias analysis methods in clinical meta-analyses." PMC13244164 (2026).

10. Gargano MA et al. "The Human Phenotype Ontology in 2024." *Nucleic Acids Research* 2024. DOI: [10.1093/nar/gkad1005](https://doi.org/10.1093/nar/gkad1005)
