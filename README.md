# nf1-swarm

An agentic AI swarm compiling the known history of NF1 (Neurofibromatosis type 1) biology and clinical outcomes into a structured, traversable knowledge graph.

<!-- STATS_START -->
| 🧬 Accepted claims | ⏳ Pending claims | 📄 Papers processed | 🕐 Updated |
|:-----------------:|:-----------------:|:-------------------:|:----------:|
| 28 | 142 | 4 | 2026-11-22 UTC |
<!-- STATS_END -->

## What this is

NF1 is a rare genetic disease (OMIM #162200) caused by loss-of-function mutations in the *NF1* gene encoding neurofibromin, a RAS-GTPase activating protein. It is one of the most common single-gene disorders affecting the nervous system (1:3000 births), with broad phenotypic expression spanning skin, nervous system, eyes, bones, vasculature, and cognition.

This repository is the working home of an AI agent swarm that reads primary literature, extracts structured claims, grounds them to canonical ontology identifiers, verifies them against raw data, curates them through PI-level review, and deposits them into a Neo4j knowledge graph. All work is auditable, versioned, and traceable to source via git history.

## The team

| Agent | Role |
|-------|------|
| **Graude** | Orchestrator — owns GitHub issues as task board, routes work, tracks pipeline state |
| **Dirk** | Reads primary literature, extracts falsifiable claims (FETA Stage 1) |
| **Otto** | Grounds extracted entities to canonical CURIEs via RTX-KG2 (FETA Stage 2) |
| **Archie** | Fact-checks claims against raw data; returns SUPPORTED / CONTRADICTED / INCONCLUSIVE |
| **Stan** | Statistician — publication bias analysis, confidence scoring (PET-PEESE / RoBMA-PSMA) |
| **Kim** | Builds and traverses the Neo4j knowledge graph |
| **Rey** | PI/senior curator — final accept/reject decisions on all claims |
| **Emily** | Software engineer — CI, tooling, schema mechanics, infrastructure |
| **Milo** | Memory & context manager — episodic store, nightly dreaming, DACS registry, retrieval |

All bot commits are co-authored by Gregory Way (PI). See `.github/bot_identities.md` for git identities.

## Claim pipeline

Claims flow through a strict per-claim lifecycle. Across papers and claims, agents work concurrently.

```
Dirk          →  Otto          →  [Archie]      →  Rey           →  Kim           →  [Stan]
Stage 1:          Stage 2:          optional:        curate:          write to         confidence
extract           ground to         deep verify      accept /         Neo4j            scoring
falsifiable       CURIEs via        against raw      reject
sentences         RTX-KG2           data
```

GitHub issues are the audit trail — every agent comments their stage output on the originating paper issue. Hermes `message_agent` is how agents coordinate with each other (never GitHub comments).

## Communication model

**GitHub issues** — human-readable audit trail for Gregory. Factual STATUS updates only. No agent-to-agent routing.

**Hermes `message_agent`** — all agent coordination flows through Graude. Agents do not message each other directly.

## Quick start

```bash
# 1. Install dependencies (Python 3.11+, uv required)
uv sync

# 2. Install git hooks (enforces co-author trailer on bot commits)
uv run pre-commit install

# 3. Start Neo4j (bolt://localhost:7687, credentials: neo4j/<see secrets>)
sudo systemctl start neo4j

# 4. Bootstrap the knowledge graph
uv run python knowledge_graph/seeds/bootstrap.py

# 5. Run the test harness
uv run python testing/harness/claim_validator.py
uv run python testing/harness/approval_checker.py
```

> **Always use `uv run python`** — never bare `python3`. The project venv at `.venv/` has all required packages.

## Repository structure

```
nf1-swarm/
├── AGENTS.md                    # Agent roles, pipeline protocol, communication rules
├── DESIGN.md                    # Architecture, node/edge schema, design decisions
├── METHODS.md                   # FETA extraction, RTX-KG2, publication bias methodology
├── CITATION.cff                 # Full reference list for all methods used
│
├── claims/
│   ├── pending/                 # Claims awaiting curation (Dirk deposits, Otto grounds, Rey curates)
│   ├── accepted/                # Rey-accepted claims awaiting graph insertion by Kim
│   └── schema.json              # JSON Schema for all claims
│
├── literature/
│   ├── queue.md                 # Papers assigned to Dirk (PENDING / IN_PROGRESS / DONE)
│   ├── processed.md             # Papers completed with claim IDs
│   ├── fetcher.py               # PubMed / PMC / bioRxiv fetcher
│   ├── extractor.py             # FETA Stage 1 heuristic pre-filter
│   └── rtx_kg2.py               # RTX-KG2 TRAPI client for Otto
│
├── knowledge_graph/
│   ├── seeds/                   # Bootstrap Cypher (core NF1 biology, phenotypes, treatments)
│   ├── migrations/              # Numbered idempotent Cypher migrations (Kim writes)
│   ├── queries/                 # Read queries + reserve_claim_id.py
│   └── schema/                  # Constraints and indexes
│
├── swarm_memory/                # Milo's shared episodic memory store
│   ├── registry.md              # DACS ≤200-token status per agent
│   ├── episodes/                # Completed work-phase summaries
│   ├── pruning_log.md           # Audit trail for memory pruning decisions
│   └── milo_dream.py            # Nightly consolidation script (02:00 UTC cron)
│
├── scripts/
│   ├── verify_paper.py          # Pre-flight PMID/DOI verification (Graude uses before assigning)
│   ├── enforce_coauthor.sh      # commit-msg hook — blocks bot commits missing co-author trailer
│   ├── backup_graph.sh          # Neo4j dump (7-day retention)
│   └── restore_graph.sh         # Neo4j restore from dump
│
├── testing/
│   ├── specs/                   # TRUSTED: human-written scientific contract (TCB — Gregory only)
│   ├── harness/                 # PROTECTED: human-owned test runner (TCB — Gregory only)
│   ├── acceptance/              # Agent-writable test data tables
│   └── approved/                # Approval snapshots of known-good graph state
│
└── .hermes/
    ├── context.md               # Auto-loaded repo context for all agents
    ├── skills/                  # Shared Hermes skills (nf1-claim-extraction)
    └── profiles/                # Agent identity files (SOUL.md, profile.yaml, gitconfig)
```

## Knowledge graph

Neo4j Community Edition, `bolt://localhost:7687`. Schema spans 13 node types and 20+ relationship types: Gene, Protein, Pathway, Mutation, Phenotype, Disease, Drug, ClinicalTrial, Publication, Claim, CellLine, AnimalModel, Dataset.

RTX-KG2 (73+ integrated biomedical sources) is the external knowledge oracle for entity grounding and edge existence checks. See `METHODS.md` for full methodology.

## Testing philosophy

This project adopts two principles for agentic codebases:

1. **Tests as data** (Vaccari, 2026): Acceptance tests live as tables and YAML files, not code. Agents write rows into test tables — they never modify the harness. `testing/harness/` is human-owned and CODEOWNERS-protected.

2. **Specification-first verification** (AlphaProof Code, DeepMind, 2026): Humans write the specifications (`testing/specs/`). Agents prove compliance. A claim failing the validator is rejected regardless of who wrote it.

## Trusted Computing Base (TCB)

The TCB is kept minimal so the swarm moves fast everywhere else. Only these paths require Gregory's approval to merge:

- `testing/specs/` — scientific contract
- `testing/harness/` — enforcement code
- `testing/approved/` — gold standard snapshots
- `.github/CODEOWNERS` — the ownership rules themselves

Everything else is fast-path: Emily reviews, no human gate needed.

## References

See `CITATION.cff` for the full reference list covering FETA extraction, RTX-KG2, publication bias methodology, MemGPT, DACS, and all other methods implemented in this project.

---

## Evidence strength scale

Every claim carries an `evidence_strength` (1–5) and `evidence_type`. These are assigned by Dirk at extraction and may be revised by Rey at curation.

| Strength | Label | Meaning | Allowed evidence types |
|----------|-------|---------|----------------------|
| **5** | Definitive | Scientific consensus — multiple independent replications, systematic review with meta-analysis, or foundational biochemical proof replicated across labs | `biochemical_proof`, `systematic_review`, `rct` |
| **4** | Strong | Single well-powered RCT, multiple independent cohort studies, or replicated preclinical studies in validated models | `rct`, `cohort_study`, `systematic_review`, `preclinical_in_vivo` |
| **3** | Moderate | Preclinical evidence in validated NF1 models, small but well-designed clinical studies, cross-validated computational predictions. Also: any claim extracted from abstract-only (no full text) is capped at 3 regardless of underlying evidence | `preclinical_in_vivo`, `preclinical_in_vitro`, `cohort_study`, `computational` |
| **2** | Preliminary | Single small study, case reports, early-phase clinical observations, unvalidated computational predictions | `case_report`, `preclinical_in_vitro`, `computational`, `expert_opinion` |
| **1** | Speculative | Expert opinion, theoretical framework, hypothesis not yet experimentally tested | `expert_opinion`, `computational` |

**On `biochemical_proof`:** This evidence type measures mechanism directly — purified protein, direct assay, observed activity. It is not correlative. For molecular function claims (what does neurofibromin *do*?), biochemical proof is the gold standard and the only path to strength 5. Example: Xu et al. 1990 expressed the NF1 catalytic domain, added it to RAS-GTP, and directly measured GTP hydrolysis rate — that is biochemical proof.

**On convergent evidence:** `evidence_strength` reflects a single paper. As more supporting papers accumulate in `supporting_dois`, Stan computes a `confidence_score` (0–1) adjusted for publication bias, correlated evidence, and independence. A claim at strength 3 with five independent replications may carry a higher confidence_score than a strength 4 claim with a single study.

## Biological context fields

Claims carry optional biological context that scopes where the evidence was obtained:

| Field | Type | Description | Grounded by |
|-------|------|-------------|-------------|
| `organism` | enum | `human`, `mouse`, `rat`, `zebrafish`, `drosophila`, `yeast`, `in_vitro`, `other` | Dirk (at extraction) |
| `cell_type` | free text | E.g. "Schwann cell", "astrocyte", "mast cell" | Dirk (at extraction) |
| `cell_type_id` | CL CURIE | Cell Ontology identifier. E.g. `CL:0002573` | Otto (at grounding) |
| `tissue` | free text | E.g. "peripheral nerve", "optic nerve", "skin" | Dirk (at extraction) |
| `tissue_id` | UBERON CURIE | Anatomy ontology identifier. E.g. `UBERON:0001021` | Otto (at grounding) |

These fields are optional — not all claims have cell-type or tissue specificity. When present, they make the graph queryable by biological context: "which claims about NF1 were demonstrated specifically in Schwann cells?" or "which drug response claims come from human tissue vs. mouse models?"

NF1's phenotypic diversity is partly explained by cell-type-specific effects of neurofibromin loss. A claim true in Schwann cells may not hold in astrocytes. These fields make that distinction computable.
