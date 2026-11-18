# Design — nf1-swarm

## Overview

This document records architectural decisions, their rationale, and the constraints they impose.

## Knowledge graph: Neo4j

**Decision:** Neo4j Community 5.x, bolt://localhost:7687, Cypher query language.

**Rationale:**
- Official MCP server (26 tools) makes Neo4j directly agentic-queryable without custom tooling
- GraphRAG for Python (`neo4j-graphrag`) enables semantic + graph retrieval in one pass
- Graph Data Science (GDS) library supports centrality, community detection, link prediction on the NF1 network
- Property graph model (nodes + edges + properties) cleanly maps to biological entity-relationship structure
- Precedent: RareGraph-AgenticAI (2026, CHOP/UPenn) used this stack for a 15,280-disease rare disease KG

**Constraints:**
- All schema changes require a migration file in `knowledge_graph/migrations/`
- No agent may introduce a new node label or edge type without a GitHub issue and Rey approval
- Production database URL: `bolt://localhost:7687` (dev default credentials changed on first run)

## Node types (13)

| Label | Key properties | Example |
|-------|---------------|---------|
| `Gene` | hgnc_id, symbol, chromosome | NF1, 17q11.2 |
| `Protein` | uniprot_id, name, function | Neurofibromin, RAS-GAP |
| `Pathway` | name, kegg_id | RAS/MAPK |
| `Mutation` | hgvs_cdna, clinvar_id, variant_class | NM_000267.3:c.2041C>T |
| `Phenotype` | hpo_id, name, onset | HP:0000957, Café-au-lait spot |
| `Disease` | omim_id, mondo_id, name | OMIM:162200, NF1 |
| `Drug` | name, mechanism, approval_status | Selumetinib, MEK inhibitor, FDA approved |
| `ClinicalTrial` | nct_id, phase, outcome | NCT01362803, Phase 3 |
| `Publication` | pmid, doi, year, journal | 1281417, Cell 1990 |
| `Claim` | claim_id, claim_text, evidence_strength | C0001 |
| `CellLine` | cellosaurus_id, name, nf1_status | CVCL_0001 |
| `AnimalModel` | name, background, nf1_genotype | Nf1+/- C57BL/6 |
| `Dataset` | name, source_url | NF Data Portal |

## Edge types (22)

```
CAUSES              Mutation ──► Disease/Phenotype
ENCODES             Gene ──► Protein
ACTIVATES           Protein ──► Protein/Pathway
INHIBITS            Drug/Protein ──► Protein/Pathway
TREATS              Drug ──► Disease/Phenotype
TARGETS             Drug ──► Gene/Protein
ASSOCIATED_WITH     Gene/Mutation ──► Phenotype/Disease
PART_OF             Gene/Protein ──► Pathway
EXTRACTED_FROM      Claim ──► Publication
SUPPORTS            Claim ──► Claim
CONTRADICTS         Claim ──► Claim
VALIDATED_IN        Claim ──► CellLine/AnimalModel
FOUND_IN            Gene/Dataset ──► Dataset/Gene
HOMOLOGOUS_TO       Protein/Gene ──► Protein/Gene
ABOUT               Claim ──► Gene/Protein/Pathway/Mutation/Phenotype/Disease/Drug/ClinicalTrial/CellLine/AnimalModel/Dataset
```

## Testing architecture

### 1. Tests as Data (Vaccari, 2026)

When agents write both production code and test code, the tests lose their protective value.
The solution: move the contract into *data*, not code.

- **`testing/specs/`** — TRUSTED. Human-written YAML specs. Only Rey or Gregory may modify.
- **`testing/acceptance/`** — TEST DATA. Agents add rows to CSV/YAML tables.
- **`testing/harness/`** — PROTECTED. Human-owned Python test runner. CODEOWNERS-enforced.
- **`testing/approved/`** — APPROVAL SNAPSHOTS. Require explicit human approval to change.

### 2. Specification-first verification (AlphaProof Code, DeepMind, 2026)

Humans write the *specification* (what correctness means). Agents write claims that must comply.
Claims failing the validator are rejected regardless of who wrote them.

Trusted computing base:
- `testing/specs/claim_contract.yaml`
- `testing/specs/evidence_rubric.yaml`
- `testing/specs/edge_constraints.yaml`
- `testing/specs/node_schemas.yaml`

### Guard rails

- `testing/harness/` and `testing/specs/` are CODEOWNERS-protected
- CI runs `testing/harness/run_tests.sh` on every PR touching claims or testing
- Agents write test DATA (new CSV rows, new YAML blocks) — never harness code

## Schema versioning

All Neo4j schema changes are numbered Cypher migration files in `knowledge_graph/migrations/`.
Migrations are idempotent (use MERGE/IF NOT EXISTS) and run in order by `bootstrap.py`.

---

## Graph epistemics — representing what we know, what we've ruled out, and what's untested

**Decision:** The graph distinguishes three epistemic states for any potential relationship.

**Rationale:** A missing edge between two nodes is ambiguous. It could mean:
1. Nobody has tested this relationship yet (untested)
2. Someone tested it and found no effect (null result, unpublished)
3. Someone tested it and it was explicitly refuted (falsified)
4. We haven't processed the relevant paper yet (pipeline gap)

Treating all four as "no edge" destroys information. Falsified claims have scientific value —
they tell future agents and researchers what has been ruled out, prevent redundant work, and
provide anchor points when knowledge evolves (a claim falsified with 1990 tools may warrant
re-examination in 2026).

**Three epistemic states:**

| State | Graph representation | When |
|-------|---------------------|------|
| **Asserted** | Claim node with `status: accepted`, ABOUT edges to entities | Rey accepts |
| **Refuted** | Claim node with `status: refuted`, CONTRADICTS edge to any conflicting accepted Claim | Rey rejects as `biological`, Archie returns CONTRADICTED |
| **Untested** | No Claim node — but discoverable: if RTX-KG2 also has no edge, it is genuinely untested; if RTX-KG2 has an edge we haven't processed, it is a pipeline gap |

**Key principle:** Biological rejections do NOT remove claims from the graph. Kim writes refuted
claims as Claim nodes with `status: refuted`. This creates a queryable record of what has been
tested and found false — essential for gap analysis and for agents that need to know what NOT
to re-derive.

**Future: gap map queries**
Milo will eventually run systematic gap queries: for every Gene-Disease pair in the graph,
is there an asserted relationship? A refuted one? Or silence? High-value missing edges
(entities that appear frequently but lack certain relationship types) surface as literature
queue candidates for Graude.

**Future: metadata annotation**
As knowledge accumulates, existing nodes and edges gain new properties:
- Stan updates `confidence_score` on Claim nodes as evidence accumulates
- Kim writes `MATCH ... SET` migrations to add properties to existing nodes
- Edges gain `{status: 'refuted', refuted_by: 'C0042'}` properties when contradicted
The numbered migration pattern already supports this — no architectural change needed.

## Claim node: rejection classification

Claim nodes carry a `rejection_class` property when `status` is `rejected` or `refuted`:

| rejection_class | Meaning | Next action |
|----------------|---------|-------------|
| `structural` | Encoding problem (bad CURIE, wrong predicate, needs splitting) | Route back to Otto for re-grounding |
| `biological` | Biology is wrong, unsupported, or out of scope | Kim writes to graph as `status: refuted`; terminal |

Graude routes `structural` rejections back to Otto immediately.
`biological` rejections are routed to Kim for graph insertion as refuted claims.
