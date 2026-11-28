# Otto's Ontology Grounding Guide

> **Python environment:** Always use `uv run python` (or activate `.venv` first).
> Never use bare `python3`, never `pip install`, never create a private venv.
> If an import fails, the interpreter is wrong — not the package. Fix: `cd ~/repos/nf1-swarm && uv run python <script>`.

## Grounding workflow (FETA Stage 2)

Otto receives claims Dirk already extracted (Stage 1) and fills `semantic_triple`
and optionally `bel_notation`. **Never ground during extraction** — Dirk's job is
text, Otto's job is CURIEs. Mixing the two causes LLMs to hallucinate IDs.

```python
from literature.rtx_kg2 import ground_entity, check_edge_exists, get_nf1_edges

# 1. Ground each entity mentioned in the claim_text
nodes = ground_entity("neurofibromin", categories=["biolink:Protein"])
# [{"id": "UniProtKB:P21359", "name": "Neurofibromin", "category": [...], "synonyms": [...]}]

# 2. Check whether the relationship already exists in RTX-KG2 — do this BEFORE
#    writing semantic_triple. If it exists with many sources, that corroborates
#    the claim and should feed Stan's confidence scoring later.
triples = check_edge_exists("UniProtKB:P21359", "HP:0009732", predicates=["biolink:causes"])
for t in triples:
    print(t.n_sources, t.pmids)

# 3. Survey everything already known about NF1 (useful context before grounding
#    a claim that touches the core gene)
edges = get_nf1_edges()
```

## Filling `semantic_triple` in the claim JSON

```json
"semantic_triple": {
  "subject": "Neurofibromin",
  "subject_id": "UniProtKB:P21359",
  "predicate": "ACTIVATES",
  "object": "RAS",
  "object_id": "UniProt:P01111"
}
```

- `predicate` must **exactly** match a key of `predicate_mapping` in
  `scientific-governance/scientific-claim-rules/edge_constraints.yaml`. The validator
  enforces this — any other predicate makes `claim_validator.py` FAIL.

  **Allowed predicates for `semantic_triple.predicate`** (the 13 biological predicates):

  `ACTIVATES`, `BENEFICIAL_IN_MODELS_OF`, `CAUSES`, `ENCODES`, `FOUND_IN`,
  `GENE_ASSOCIATED_WITH_CONDITION`, `HAS_PHENOTYPE`, `HOMOLOGOUS_TO`, `INHIBITS`,
  `IN_CLINICAL_TRIALS_FOR`, `PART_OF`, `TARGETS`, `TREATS`

  **Not valid as a `semantic_triple.predicate`:** the structural claim-reification edges
  `HAS_SUBJECT`, `HAS_OBJECT`, `EXTRACTED_FROM`, `SUPPORTS`, `CONTRADICTS`,
  `VALIDATED_IN`. They exist in `edge_types` for the graph, but the validator rejects them
  as claim predicates.

  **Retired (do not use):** `ABOUT` (hard FAIL) and `ASSOCIATED_WITH` (transitional:
  the validator prints a WARN, not a FAIL, until the 19 existing claims are re-grounded
  in #88 — do not use it in new claims). Anything not listed above also FAILS.

  Check `scientific-governance/scientific-claim-rules/edge_constraints.yaml` for the
  authoritative list and the allowed `from`/`to` node labels for each predicate.
- `subject`/`object` are human-readable names; `subject_id`/`object_id` are CURIEs.

## Grounding cell_type_id and tissue_id

When a claim has `cell_type` or `tissue` text filled by Dirk, ground them to CURIEs:

```python
from literature.rtx_kg2 import ground_entity

# Cell type → Cell Ontology (CL)
if claim.get("cell_type"):
    nodes = ground_entity(claim["cell_type"], categories=["biolink:Cell"])
    # Pick the best match; CL:0002573 = Schwann cell
    claim["cell_type_id"] = nodes[0]["id"] if nodes else None

# Tissue → UBERON anatomy
if claim.get("tissue"):
    nodes = ground_entity(claim["tissue"], categories=["biolink:GrossAnatomicalStructure"])
    # UBERON:0001021 = sciatic nerve
    claim["tissue_id"] = nodes[0]["id"] if nodes else None
```

If RTX-KG2 returns no match, leave the ID field `null` and add a note in `notes`:
`"cell_type_id: no CL match found for 'X' via RTX-KG2 (accessed YYYY-MM-DD)"`.
Do NOT invent CURIEs — a null ID is better than a wrong one.

## Filling `related_nodes` — use HAS_SUBJECT / HAS_OBJECT

`related_nodes` lists the graph entities the claim connects. For the dual-encoding
pattern use `HAS_SUBJECT` for the subject entity and `HAS_OBJECT` for the object entity.
Do not use `ABOUT` or `ASSOCIATED_WITH` (both retired).

```json
"related_nodes": [
  {"label": "Gene",    "identifier": "NCBIGene:4763",    "edge_type": "HAS_SUBJECT"},
  {"label": "Protein", "identifier": "UniProtKB:P21359", "edge_type": "HAS_OBJECT"}
]
```

Rules:
- The subject and object of `semantic_triple` each get exactly one entry, with the
  matching `edge_type`.
- **Do not** put biological predicates (`ENCODES`, `ACTIVATES`, ...) in `related_nodes`.
  Those are graph relationships Kim writes when inserting the claim into Neo4j, not
  claim metadata Otto sets.
- `edge_constraints.yaml` defines no edge type for any entity that is neither subject
  nor object, so do not invent one. If the claim mentions a third entity (a pathway,
  a disease) that matters, record it in `notes` and flag it to Graude.
- Kim uses these entries, plus `semantic_triple.predicate`, to write the dual-encoding
  edges to Neo4j.

> Existing claims written before v2.0 still carry `ABOUT` in `related_nodes`
> (the validator does not check `related_nodes[].edge_type`). Migration
> `008_dual_encoding_backfill` handles the graph side; do not copy that older
> pattern into new claims.

## Validator requirements (run before every commit)

```bash
uv run python scientific-governance/claim-validation-harness/claim_validator.py
```

The validator runs three post-grounding checks the moment `semantic_triple` is
present. All three must pass or the claim is rejected:

| Check | What it catches | Example failure |
|-------|----------------|-----------------|
| **CURIE format** | `subject_id`/`object_id` must match `PREFIX:identifier` — no pipes, no whitespace | `NCBIGene:4974\|NCBIGene:5921` (multi-CURIE) |
| **Predicate in spec** | predicate must exist in `edge_constraints.yaml` | `HOMOLOGOUS` (not a defined edge type) |
| **related_nodes not empty** | `related_nodes` must list at least subject and object when triple is set | `"related_nodes": []` with a populated triple |

The JSON Schema (`claims/schema.json`) also enforces the CURIE pattern directly
on `subject_id`/`object_id` — a malformed CURIE will fail JSON Schema validation
before even reaching the post-grounding checks.

### HOMOLOGOUS_TO (new — pending PR #19 merge)

For ortholog/paralog relationships between proteins or genes:
```json
"predicate": "HOMOLOGOUS_TO",
"subject_id": "UniProtKB:P21359",   // human neurofibromin
"object_id":  "UniProtKB:P97679"    // mouse Nf1 protein
```
`HOMOLOGOUS_TO` accepts `{from: [Protein, Gene], to: [Protein, Gene]}`.
Use it only after PR #19 merges to main (the predicate will fail validation
until it's in `edge_constraints.yaml`).

## BEL notation (optional, molecular_function / pathway_interaction only)

```
bel_notation: "p(HGNC:NF1) decreases act(p(HGNC:HRAS), ma(gtpBoundActivity))"
```

Only add this when the claim describes a molecular mechanism BEL can express
cleanly (activation/inhibition/translocation). Skip it for clinical_outcome or
genetic_association claims — forcing BEL onto those produces noise.

## Common pitfalls

1. **Ambiguous CURIEs — NF1 the gene vs NF1 the disease.** `NCBIGene:4763` is
   the gene; `MONDO:0009981` is the disease (Neurofibromatosis type 1). Read
   the claim_text's grammatical subject before picking — "NF1 encodes..." is
   the gene, "patients with NF1 show..." is the disease.
2. **SemMedDB is deprecated** (Dec 2024) — its content is now folded into
   RTX-KG2. Don't query it separately.
3. **`ground_entity()` can return multiple candidates.** Prefer the result
   whose `category` matches the claim's grammatical role (protein vs gene vs
   chemical), not just the first hit.
4. **If RTX-KG2 times out or 5xxs**, retry once with a longer `timeout=`, then
   fall back to HGNC REST (genes), OLS (HPO/MONDO/GO), or ChEMBL (drugs) per
   AGENTS.md. Don't block the whole claim on one grounding call — note the
   gap in `notes` and flag it on the issue.
5. **Always record the ontology version used** in the claim's `notes` field —
   RTX-KG2 content drifts over time and future audits need to know what you
   queried against.
6. **Document, don't duplicate.** If `check_edge_exists()` finds the exact
   relationship Dirk's claim describes with many independent sources, note the
   PMIDs in `notes` — don't silently drop the claim. Rey decides whether it's
   redundant.
7. **Never put multiple CURIEs in one field** — `subject_id` and `object_id`
   must each be a single CURIE. If a claim involves multiple objects, write
   multiple claims (one per CURIE). The validator will FAIL pipe-delimited
   values like `NCBIGene:4974|NCBIGene:2123`.
8. **`UniProt:` vs `UniProtKB:`** — the canonical prefix is `UniProtKB:`.
   Both may resolve in RTX-KG2 but `UniProtKB:` is the OBO-compliant form.

## Commit

```
git add claims/pending/C<id>.json
git commit -m "ontology(otto): ground C<id>"
```

## GitHub commenting rules

- **No `@handle` syntax anywhere** — not in issue comments, PR bodies, PR titles,
  or review comments. It fires email notifications to real people. Refer to
  teammates by name: Gregory, Rey, Graude, Otto, Dirk, Stan, Kim, Emily.
- Comments are factual status records for Gregory to read. Keep them concise:
  what was done, what IDs were assigned, what failed and why.
- Use `message_agent` (Hermes) for all agent-to-agent coordination — GitHub is
  for humans to track the science, not for agents to talk to each other.
