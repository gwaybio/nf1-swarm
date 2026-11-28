# Kim's Graph-Building Guide

> **Python environment:** Always use `uv run python` (or activate `.venv` first).
> Never use bare `python3`, never `pip install`, never create a private venv.
> If an import fails, the interpreter is wrong — not the package. Fix: `cd ~/repos/nf1-swarm && uv run python <script>`.

## Writing an accepted claim to Neo4j

Only write claims that are in `claims/accepted/` (Rey moved them there).
Never write from `claims/pending/`.

```python
import json
from pathlib import Path
import yaml
from neo4j import GraphDatabase

claim = json.loads(Path("claims/accepted/C0042.json").read_text())
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.environ["NEO4J_PASSWORD"]))

with driver.session() as session:
    # 1. Create the Claim node itself
    session.run("""
        MERGE (c:Claim {claim_id: $claim_id})
        SET c.claim_text = $claim_text,
            c.evidence_strength = $evidence_strength,
            c.claim_type = $claim_type,
            c.evidence_type = $evidence_type,
            c.status = $status,
            c.curated_by = $curated_by
    """, **claim)

    # 2. Link it to its source publication (EXTRACTED_FROM)
    session.run("""
        MATCH (c:Claim {claim_id: $claim_id})
        MERGE (p:Publication {pmid: $source_pmid})
        ON CREATE SET p.doi = $source_doi, p.year = $source_year
        MERGE (c)-[:EXTRACTED_FROM]->(p)
    """, **claim)

    # 3. Dual encoding (edge_constraints.yaml v2.0). Write BOTH layers from the claim's
    #    semantic_triple. related_nodes only tells you each entity's label; its edge_type
    #    is NOT a graph edge to write (ABOUT is retired, ASSOCIATED_WITH is transitional).
    spec = yaml.safe_load(open("scientific-governance/scientific-claim-rules/edge_constraints.yaml"))
    node_schemas = yaml.safe_load(open("scientific-governance/scientific-claim-rules/node_schemas.yaml"))["node_schemas"]
    triple = claim["semantic_triple"]            # subject/subject_id, predicate, object/object_id
    predicate = triple["predicate"]
    if predicate not in spec["predicate_mapping"]:  # Cypher cannot parameterise a relationship
        raise ValueError(f"{predicate} is not a v2.0 predicate - send back to Otto")  # type, so allowlist it

    def resolve_node(end):                       # end = "subject" or "object"
        curie = triple[f"{end}_id"]
        label = next(n["label"] for n in claim["related_nodes"] if n["identifier"] == curie)
        # unique_on is NOT the CURIE: Gene -> symbol, Disease/Protein/Drug -> name,
        # Phenotype -> hpo_id. Never invent a property.
        key = node_schemas[label]["unique_on"][0]
        value = curie if key in ("hpo_id", "nct_id") else triple[end]
        # Reuse the existing node's stored value: names are curated ('Selumetinib'), the
        # claim text is not ('selumetinib'), and a casing difference would create a duplicate.
        row = session.run(
            f"MATCH (n:{label}) WHERE toLower(n.{key}) = toLower($v) RETURN n.{key} AS v LIMIT 1",
            v=value).single()
        if row:
            value = row["v"]
        else:  # genuinely new entity: create it, but say so, and check the name with Otto
            print(f"NEW {label} {value!r} created for {claim['claim_id']} - confirm the name with Otto")
            session.run(f"MERGE (:{label} {{{key}: $v}})", v=value)
        return label, key, value

    s_label, s_key, s_val = resolve_node("subject")
    o_label, o_key, o_val = resolve_node("object")
    match = f"""
        MATCH (c:Claim {{claim_id: $claim_id}}),
              (s:{s_label} {{{s_key}: $s_val}}), (o:{o_label} {{{o_key}: $o_val}})
    """
    params = dict(claim_id=claim["claim_id"], s_val=s_val, o_val=o_val)

    # Layer 2: the Claim points at its subject and object.
    session.run(match + "MERGE (c)-[:HAS_SUBJECT]->(s) MERGE (c)-[:HAS_OBJECT]->(o)", **params)

    # Layer 1: one coalesced direct edge per (subject, predicate, object) that carries every
    # supporting claim_id. Skip this layer for a negative-result claim until issue #93
    # (result_polarity) is decided, or it would merge into a positive edge.
    session.run(match + f"""
        MERGE (s)-[r:{predicate}]->(o)
        SET r.biolink_predicate = $biolink,
            r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, [])
                               THEN r.claim_ids
                               ELSE coalesce(r.claim_ids, []) + c.claim_id END
        SET r.n_claims = size(r.claim_ids)
    """, biolink=spec["predicate_mapping"][predicate], **params)

driver.close()
```

If the claim's `related_nodes` entry doesn't carry enough info to MERGE on
the schema's real key, go back to Dirk/Otto before writing it — a malformed
MERGE key creates duplicate nodes instead of
matching an existing one.

**Always `MERGE`, never `CREATE`**, for both nodes and edges — the graph must
stay idempotent so bootstrap/migrations can re-run safely.

## Migration file format

New node labels or edge types require a GitHub issue **and Rey's approval
first** (`DESIGN.md` constraint) — do not just add one because a claim seems
to need it.

Once approved, add a numbered file to `knowledge_graph/migrations/`:

```
knowledge_graph/migrations/004_add_biomarker_label.cypher
```

```cypher
// Migration 004: add Biomarker node label (approved in issue #N by @rey)
// Idempotent — safe to re-run.
CREATE CONSTRAINT biomarker_name IF NOT EXISTS
FOR (b:Biomarker) REQUIRE b.name IS UNIQUE;
```

- Number sequentially after the highest existing migration.
- Use `MERGE`/`IF NOT EXISTS` only — `bootstrap.py` runs every migration file
  in order on every bootstrap, so a non-idempotent statement breaks future
  runs.
- Never edit a migration file after it has run against the shared dev graph
  or CI — add a new migration instead.
- Reference the approving issue number in a comment at the top of the file.

## Graph query patterns

```cypher
// All accepted claims ordered by evidence strength (see
// knowledge_graph/queries/claims_by_evidence.cypher for the saved version)
MATCH (c:Claim {status: 'accepted'})
RETURN c.claim_id, c.claim_text, c.evidence_strength, c.claim_type
ORDER BY c.evidence_strength DESC;

// Check whether a claim already exists before creating a new one
// (AGENTS.md communication convention — ALWAYS do this first)
MATCH (c:Claim {claim_text: $text}) RETURN c;

// Traverse downstream from NF1 (see pathway_traversal.cypher)
MATCH path = (nf1:Gene {symbol: 'NF1'})-[:ENCODES]->(p:Protein)
             -[:INHIBITS|ACTIVATES*1..3]->(downstream)
RETURN path LIMIT 25;
```

Save new, reusable queries you write under `knowledge_graph/queries/` as
`.cypher` files (not ad-hoc in a notebook) so other agents can find them.

## Reserving claim IDs

Never hand-assign a `claim_id`. Always:
```python
from knowledge_graph.queries.reserve_claim_id import next_claim_id
with driver.session() as session:
    cid = next_claim_id(session)   # e.g. "C0042" — atomic via apoc.lock.nodes()
```
This requires APOC to be installed on the Neo4j server (it's a server plugin,
not a pip package — already enabled locally and in CI).

## Common pitfalls

1. **Schema integrity first.** Check `scientific-governance/scientific-claim-rules/node_schemas.yaml` for
   `required`/`unique_on` properties and `scientific-governance/scientific-claim-rules/edge_constraints.yaml`
   for valid `from`/`to` label pairs before writing any node or edge — these
   files are the trusted contract, and a write that violates them (even if
   Neo4j itself allows it, since it's schema-less) breaks graph integrity
   that `scientific-governance/claim-validation-harness/approval_checker.py` checks for.
2. **No ad-hoc node types or edge types.** If a claim needs a label or
   relationship not in `DESIGN.md`'s 13 node types / 20 edge types, that's a
   schema change — open the issue and get Rey's approval before writing
   anything, even in a dev/test graph.
3. **Query before you write.** `AGENTS.md`: "Never duplicate a claim already
   in the graph — query first." The same applies to entities — MERGE
   (not CREATE) is how you avoid duplicate Gene/Protein/Disease nodes across
   claims written by different runs.
4. **Commit your migration, not just run it against the live graph.** A
   Cypher change that only exists in the Neo4j instance you ran it in is
   invisible to CI's bootstrap and to anyone who re-clones the repo.

## Writing refuted claims to Neo4j

Claims with `rejection_class: biological` are **not discarded** — the biology
was judged wrong or unsupported, but that is itself a scientific fact worth
preserving. Write them to the graph with `status: refuted`.

**When to write:** Rey sets status=refuted and rejection_class=biological.
Graude opens a `[KIM]` issue. Kim writes the node.

**Pattern — same as accepted claims, with two differences:**

```python
# 1. Set status=refuted on the Claim node (not "accepted")
session.run("""
    MERGE (c:Claim {claim_id: $claim_id})
    SET c.claim_text   = $claim_text,
        c.status       = 'refuted',
        c.rejection_class = 'biological',
        c.rejection_reason = $rejection_reason,
        c.curated_by   = $curated_by,
        c.curation_date = $curation_date
""", **claim)

# 2. EXTRACTED_FROM edge to Publication (same as accepted)
session.run("""
    MATCH (c:Claim {claim_id: $cid})
    MERGE (p:Publication {pmid: $pmid})
    MERGE (c)-[:EXTRACTED_FROM]->(p)
""", cid=claim["claim_id"], pmid=claim["source_pmid"])

# 3. CONTRADICTS edge to any conflicting accepted Claim (optional but preferred)
#    Only add if Rey identified a specific conflicting claim.
session.run("""
    MATCH (refuted:Claim {claim_id: $refuted_id})
    MATCH (accepted:Claim {claim_id: $accepted_id, status: 'accepted'})
    MERGE (refuted)-[:CONTRADICTS]->(accepted)
""", refuted_id="C0004", accepted_id="C0001")
```

**Do NOT write HAS_SUBJECT / HAS_OBJECT or a direct entity edge** for refuted
claims — they connect a claim to the entities it describes, and a refuted claim's
entity links are scientifically unreliable. EXTRACTED_FROM (source) and
CONTRADICTS (conflict) are sufficient. (ABOUT, which these replace, is retired.)

**Migration file naming:** use the same `NNN_description.cypher` pattern as
accepted claims. Mark it clearly:
```
knowledge_graph/migrations/005_refuted_C0004.cypher
```

## Commit

```
git commit -m "feat(graph): write C0042 to Neo4j, migration 004"
```

## GitHub commenting rules

- **No `@handle` syntax anywhere** — not in issue comments, PR bodies, PR titles,
  or review comments. It fires email notifications to real people. Refer to
  teammates by name: Gregory, Rey, Graude, Otto, Dirk, Stan, Kim, Emily.
- Comments are factual status records for Gregory to read. Keep them concise:
  what was done, what IDs were assigned, what failed and why.
- Use `message_agent` (Hermes) for all agent-to-agent coordination — GitHub is
  for humans to track the science, not for agents to talk to each other.
