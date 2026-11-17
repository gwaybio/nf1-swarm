# Otto's Ontology Grounding Guide

## Grounding workflow (FETA Stage 2)

Otto receives claims Dirk already extracted (Stage 1) and fills `semantic_triple`
and optionally `bel_notation`. **Never ground during extraction** — Dirk's job is
text, Otto's job is CURIEs. Mixing the two causes LLMs to hallucinate IDs.

```python
from literature.rtx_kg2 import ground_entity, check_edge_exists, get_nf1_edges

# 1. Ground each entity mentioned in the claim_text
nodes = ground_entity("neurofibromin", categories=["biolink:Protein"])
# [{"id": "UniProt:P21359", "name": "Neurofibromin", "category": [...], "synonyms": [...]}]

# 2. Check whether the relationship already exists in RTX-KG2 — do this BEFORE
#    writing semantic_triple. If it exists with many sources, that corroborates
#    the claim and should feed Stan's confidence scoring later.
triples = check_edge_exists("UniProt:P21359", "HP:0009732", predicates=["biolink:causes"])
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
  "subject_id": "UniProt:P21359",
  "predicate": "ACTIVATES",
  "object": "RAS",
  "object_id": "UniProt:P01111"
}
```

- `predicate` must match an edge type in `testing/specs/edge_constraints.yaml`
  (`CAUSES`, `ENCODES`, `ACTIVATES`, `INHIBITS`, `TREATS`, `TARGETS`,
  `ASSOCIATED_WITH`, `PART_OF`, `VALIDATED_IN`, ...). Check the allowed
  `from`/`to` node labels there before picking one.
- `subject`/`object` are human-readable names; `subject_id`/`object_id` are CURIEs.

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

## Commit

```
git add claims/pending/C<id>.json
git commit -m "ontology(otto): ground C<id>"
```
