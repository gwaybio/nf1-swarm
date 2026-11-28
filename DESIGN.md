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
HAS_SUBJECT         Claim ──► Gene/Protein/Pathway/Mutation/Phenotype/Disease/Drug/ClinicalTrial/CellLine/AnimalModel/Dataset
HAS_OBJECT          Claim ──► Gene/Protein/Pathway/Mutation/Phenotype/Disease/Drug/ClinicalTrial/CellLine/AnimalModel/Dataset
```

> **Note:** `ABOUT` edges are retired as of v2.0. Claims now use `HAS_SUBJECT` / `HAS_OBJECT` to link to entities (reification layer), plus a coalesced typed direct edge between entities (e.g. `Drug -[:TREATS]-> Disease`). See `scientific-governance/scientific-claim-rules/edge_constraints.yaml` for the full dual-encoding spec.

## Testing architecture

### 1. Tests as Data (Vaccari, 2026)

When agents write both production code and test code, the tests lose their protective value.
The solution: move the contract into *data*, not code.

- **`scientific-governance/scientific-claim-rules/`** — TRUSTED. Human-written YAML specs. Only Rey or Gregory may modify.
- **`scientific-governance/required-graph-assertions/`** — TEST DATA. Agents add rows to CSV/YAML tables.
- **`scientific-governance/claim-validation-harness/`** — PROTECTED. Human-owned Python test runner. CODEOWNERS-enforced.
- **`scientific-governance/approved-graph-snapshots/`** — APPROVAL SNAPSHOTS. Require explicit human approval to change.

### 2. Specification-first verification (AlphaProof Code, DeepMind, 2026)

Humans write the *specification* (what correctness means). Agents write claims that must comply.
Claims failing the validator are rejected regardless of who wrote them.

Trusted computing base:
- `scientific-governance/scientific-claim-rules/claim_contract.yaml`
- `scientific-governance/scientific-claim-rules/evidence_rubric.yaml`
- `scientific-governance/scientific-claim-rules/edge_constraints.yaml`
- `scientific-governance/scientific-claim-rules/node_schemas.yaml`

### Guard rails

- `scientific-governance/claim-validation-harness/` and `scientific-governance/scientific-claim-rules/` are CODEOWNERS-protected
- CI (`ci.yml`) runs `claim_validator.py` and `approval_checker.py` on every push to `main` and on manual dispatch; `daily-health.yml` re-runs them daily. There is currently **no pull-request-time validation gate** (the only PR-triggered workflow is the Discord notification), so run `scientific-governance/claim-validation-harness/run_tests.sh` locally before opening a PR
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
| **Asserted** | Claim node with `status: accepted`, `HAS_SUBJECT`/`HAS_OBJECT` edges to entities + coalesced typed direct edge between entities | Rey accepts |
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

## Temporal knowledge graph — point-in-time queries

**Decision:** The temporal history of NF1 science is encoded entirely in claim source dates.
No special event nodes, no bitemporal fields, no graph versioning infrastructure needed.

**Rationale:** Every claim knows when its source paper was published (`source_year`,
`source_date`). The graph state "as of year X" is simply the set of claims whose source
publications existed at that point. A claim that was accepted consensus in 1995 and refuted
in 2010 is correctly present in the 1995 graph and correctly qualified in the 2010 graph —
the refuting claim's source date handles this automatically.

**Point-in-time query:**
```cypher
MATCH (c:Claim)-[:EXTRACTED_FROM]->(p:Publication)
WHERE p.year <= 1995
RETURN c, p ORDER BY p.year
```

**Graph diff between two dates:**
```cypher
// What entered the graph between 1995 and 2010?
MATCH (c:Claim)-[:EXTRACTED_FROM]->(p:Publication)
WHERE p.year > 1995 AND p.year <= 2010
RETURN c, p ORDER BY p.year
```

**Schema:** `source_date` (ISO date string, YYYY-MM-DD) is added to Claim nodes alongside
the existing `source_year` integer. `source_year` is kept for fast year-level filtering.
Publication nodes carry both `year` (integer) and `date` (ISO string) properties.

---

## Temporal graph — tracking how knowledge changes over time

**Decision:** Implement a `ClaimEvent` node type to record every state change in a Claim's
lifecycle. The Claim node holds current state; the event chain holds history.

**Rationale:** Knowledge evolves. A claim accepted in 2026 may be refuted in 2027 and
resurrected in 2029 as new methods emerge. The git commit history provides transaction-time
audit (when did we record it) but not queryable temporal graph state (what did the graph
*believe* at a given point in time). We want to answer: "what did we know about NF1→RAS
signaling on January 1, 2027?" — that requires event history in the graph, not just in git.

**Two time dimensions:**
- **Valid time** — when was the claim true in the world (the biology)
- **Transaction time** — when did we record or change it (covered by git + ClaimEvent.date)

**ClaimEvent node schema:**
```
(c:Claim)-[:HAD_EVENT]->(e:ClaimEvent)

ClaimEvent properties:
  event_type:  extracted | grounded | verified | accepted | rejected | refuted | resurrected
  date:        ISO date
  agent:       dirk | otto | archie | rey | stan | kim | graude | human
  reason:      optional — reason for rejection/refutation/resurrection
  pmid:        optional — paper that triggered the event
```

**Example lifecycle:**
```
C0001 -[:HAD_EVENT]-> {extracted,  2026-11-17, dirk}
      -[:HAD_EVENT]-> {grounded,   2026-11-17, otto}
      -[:HAD_EVENT]-> {accepted,   2026-11-18, rey}
      -[:HAD_EVENT]-> {refuted,    2027-03-15, archie, 'contradicted by PMID:38291847'}
      -[:HAD_EVENT]-> {resurrected,2028-01-10, rey,    'new evidence PMID:40112934'}
```

**Temporal query pattern:**
```cypher
// What claims were accepted as of a given date?
MATCH (c:Claim)-[:HAD_EVENT]->(e:ClaimEvent {event_type: 'accepted'})
WHERE e.date <= date('2027-01-01')
AND NOT EXISTS {
  MATCH (c)-[:HAD_EVENT]->(e2:ClaimEvent)
  WHERE e2.event_type IN ['refuted', 'rejected']
  AND e2.date <= date('2027-01-01')
}
RETURN c
```

**Implementation status:** Designed, not yet built. See GitHub issue for implementation tasks.
Kim writes ClaimEvent nodes when changing Claim status. No breaking schema change required —
ClaimEvent is additive.

## Claim node: rejection classification

Claim nodes carry a `rejection_class` property when `status` is `rejected` or `refuted`:

| rejection_class | Meaning | Next action |
|----------------|---------|-------------|
| `structural` | Encoding problem (bad CURIE, wrong predicate, needs splitting) | Route back to Otto for re-grounding |
| `biological` | Biology is wrong, unsupported, or out of scope | Kim writes to graph as `status: refuted`; terminal |

Graude routes `structural` rejections back to Otto immediately.
`biological` rejections are routed to Kim for graph insertion as refuted claims.
