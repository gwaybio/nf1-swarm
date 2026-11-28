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
- **APOC plugin required** — `reserve_claim_id()` uses `apoc.lock.nodes()` for atomic counter increment. APOC is a Neo4j server-side plugin, not a Python package. In CI it is enabled via `NEO4J_PLUGINS='["apoc"]'` on the Docker run command. Locally: install via `neo4j-admin plugin install apoc` or set in `neo4j.conf`.
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

4. Assign `evidence_strength` per `scientific-governance/scientific-claim-rules/evidence_rubric.yaml`.
   Cap at 3 when only abstract is available.

5. Assign an ID. Check `scripts/reserve_claim_id.py` and `claims/schema.json` first: the repo moved to a two-stage ID system.
   - Current: `from scripts.reserve_claim_id import generate_pending_id, pending_filename`; write `claims/pending/pending_<hex>.json` with `claim_id: null` and `pending_id: <hex>`. Rey assigns `C####` on acceptance.
   - Legacy (only if the repo still says so): `next_claim_id(session)` against Neo4j (needs APOC).
   Never hand-assign IDs either way.

6. Write JSON per `claims/schema.json`. Leave `semantic_triple`, `bel_notation` null and `related_nodes` empty — Otto fills them. Use `source_pmid` + `source_doi` of the PAPER ITSELF (the schema now uses `anyOf`; older `oneOf` rejected both together). Take `extraction_date` from `date +%F`, never typed by hand.

7. Validate: `uv run python scientific-governance/claim-validation-harness/claim_validator.py` (all must PASS).

8. Commit and push — see "Git on the shared checkout" below. Message `claim(dirk): <paper short title>` + body `Refs #<issue>` + trailer `Co-authored-by: Gregory Way <gregory.way@gmail.com>`.

9. Report: STATUS comment on the GitHub issue (plain prose, no `@handles` anywhere in GitHub) AND a brief `message_agent` to Graude (what was done, flags, next stage ready). Graude routes on the message, not the comment. If the tool refuses because Graude's last message was "no reply needed", say so to the user and retry next turn.

Details (fetching, strength/type mapping, review articles): `references/stage1-extraction-details.md`.

## Git on the shared checkout

Several agents share `~/repos/nf1-swarm`; branch and identity change under you.
- Before EVERY commit: `git checkout main && git pull --rebase --autostash origin main`, then confirm `git branch --show-current` prints `main`. Printing it is not enough — switch if it doesn't. A commit on another agent's local branch is never pushed by `git push origin main`.
- Set identity per command, not via repo config (other agents overwrite it between your `git config` and `git commit`): `git -c user.name="Otto (nf1-swarm)" -c user.email="otto@nf1-swarm.bot" commit -m "..."`. The `-c` flags are atomic with the commit and cannot be raced. If you used `git config` and the commit shows the wrong author, `git commit --amend --reset-author --no-edit` fixes it (but needs a force-push if already pushed).
- Stage only your claim files by name; `git stash -u` unrelated changes before switching branches and `git stash pop` after.
- If a commit landed on the wrong branch: `git cherry-pick <sha>` onto main, re-validate, push. Do not rewrite someone else's branch unless it is your own mistaken push, and then use `--force-with-lease` pinned to the exact sha.
- Commit-msg hook requires the Co-authored-by trailer (`uv run pre-commit install --hook-type pre-commit --hook-type commit-msg` once).
- Always `uv run python`; never bare python3/pip for repo code.

## Stage 2 — Tag (Otto)

**Goal:** Ground entities to canonical CURIEs. Check RTX-KG2 for existing evidence.

### Grounding procedure

1. **Resolve names to CURIEs via SRI Name Resolver + Node Normalizer** (preferred over `ground_entity()` — see pitfall below):
   ```python
   import requests
   # Name -> candidate CURIEs
   resp = requests.post('https://name-resolution-sri.renci.org/lookup',
       params={'string': 'selumetinib', 'offset': 0, 'limit': 5,
               'biolink_type': 'biolink:SmallMolecule'}, timeout=30)
   candidates = resp.json()  # list of {curie, label, taxa, ...}

   # Verify canonical CURIE
   resp = requests.post(
       'https://nodenormalization-sri.renci.org/get_normalized_nodes',
       json={'curies': ['CHEBI:90227']}, timeout=30)
   data = resp.json()  # {curie: {id: {identifier, label}, equivalent_identifiers: [...]}}
   ```
   Always filter Name Resolver results by taxon — it returns non-human orthologs first (e.g. horse NF1 as top hit for "NF1"). Check `taxa` field for `NCBITaxon:9606` (human).

2. **Self-verification:** confirm the CURIE resolves to the intended concept. Use `claim_text` context to disambiguate. Document grounding source and date in claim `notes`.

3. **Check RTX-KG2 for existing edges:**
   ```python
   from literature.rtx_kg2 import check_edge_exists
   existing = check_edge_exists('CHEBI:90227', 'MONDO:0003304',
       predicates=['biolink:treats'])
   # If existing: note n_sources and PMIDs in claim notes for Stan
   ```

4. **Fill `semantic_triple`:** predicate must exist in `scientific-governance/scientific-claim-rules/edge_constraints.yaml`.
   ```json
   {
     "subject": "selumetinib",
     "subject_id": "CHEBI:90227",
     "predicate": "TREATS",
     "object": "plexiform neurofibroma",
     "object_id": "MONDO:0003304"
   }
   ```
   For **negative result claims** ("does NOT stimulate/activate X"): set `semantic_triple` to `null`, preserve entities in `related_nodes`, document the negative finding in `notes` with BEL `cnc` (causesNoChange) notation. No predicate in edge_constraints represents negative functional results yet.

5. **Fill `related_nodes`** — always use `"edge_type": "ABOUT"` (the ABOUT edge links Claim to subject entities). Never use biological edge types (ENCODES, ASSOCIATED_WITH, etc.) in related_nodes.

6. **Optional `bel_notation`** for molecular/pathway claims:
   `a(CHEBI:selumetinib) -| path(MONDO:"plexiform neurofibroma")`

7. **Fix rubric conflicts during grounding** when you spot them: `biochemical_proof` requires strength 4-5 per rubric; abstract-only claims are capped at 3. Change `evidence_type` to `preclinical_in_vitro` rather than inflating strength.

8. **When re-grounding rejected claims:** clear `rejection_reason`, `rejection_class`, `curated_by`, `curation_date`, and reset `status` to `"pending"`.

9. **Validate, commit, push, report:** run `uv run python scientific-governance/claim-validation-harness/claim_validator.py` (all must PASS), commit per "Git on the shared checkout", push, then post a factual STATUS comment on the GitHub issue AND send a brief `message_agent` to Graude (what was done, any flags, next stage ready).

## Quick Reference

```python
# Stage 1: fetch and extract
from literature.fetcher import PaperFetcher
from literature.extractor import extract_candidate_claims
from scripts.reserve_claim_id import generate_pending_id, pending_filename

# Stage 2: ground (use SRI APIs directly; ground_entity() is buggy)
import requests
NAME_RESOLVER = 'https://name-resolution-sri.renci.org/lookup'
NODE_NORMALIZER = 'https://nodenormalization-sri.renci.org/get_normalized_nodes'
from literature.rtx_kg2 import check_edge_exists  # edge lookup works fine
```
```bash
uv run python scientific-governance/claim-validation-harness/claim_validator.py
```

## Pitfalls

1. **Never ground entities in Stage 1.** Core FETA principle — LLMs hallucinate ontology IDs when asked to extract and ground simultaneously.
2. **SemMedDB is deprecated** (Dec 2024). Use RTX-KG2 — SemMedDB content is now incorporated into RTX-KG2.
3. **Ambiguous CURIEs:** NF1 gene = `NCBIGene:4763`; NF1 disease = `MONDO:0018975` (not MONDO:0009981, which is an obsolete/narrower OMIM-mapped term). Always use `claim_text` context to disambiguate before accepting a CURIE.
4. **Abstract-only:** Cap `evidence_strength` at 3; note `"Full text unavailable, extracted from abstract"` in `notes` field.
5. **APOC is a server plugin, not a pip package** — do not add it to `pyproject.toml`. It must be installed into Neo4j itself. If `reserve_claim_id()` raises a procedure-not-found error, APOC is not installed on the server.
6. **Never manually assign claim IDs** — use the repo's ID generator. Manual IDs cause collisions and break the counter.
7. **Verify the assignment's PMID/DOI against NCBI before reading** (`esummary`/`efetch`); issue bodies have carried wrong PMIDs and DOIs. Use the verified one and report the correction in a STATUS comment.
8. **Never `@tag` anyone in GitHub** (users or bot handles) — email notifications. Refer by plain name; coordinate via `message_agent`.
9. **Do mechanical fixes yourself** — when a claim was rejected for a structural reason you can fix (wrong predicate, missing field, rubric conflict), just fix it. Do not delegate back to the agent who extracted it or propose a roundtrip through Graude. If the edge type or schema needed for the fix now exists, apply it.
10. **Do not edit protected files** (`scientific-governance/scientific-claim-rules/`, `scientific-governance/claim-validation-harness/`, `claims/schema.json`) or another specialist's code (e.g. `literature/fetcher.py`); report the bug to Graude instead.
11. **`ground_entity()` in `literature/rtx_kg2.py` is buggy** — the ARAX `/entity` endpoint returns a dict keyed by query term, but the function iterates it as a list and fails with `'str' object has no attribute 'get'`. Use the SRI Name Resolver + Node Normalizer directly (see Stage 2 procedure above) until the module is fixed.
12. **Canonical CURIEs for common NF1 entities** (verified via SRI Node Normalizer): selumetinib=CHEBI:90227, mirdametinib=CHEBI:88249, trametinib=CHEBI:75998, binimetinib=CHEBI:145371, plexiform neurofibroma=MONDO:0003304, optic pathway glioma=MONDO:0016167, low-grade glioma=MONDO:0021637, MPNST=MONDO:0017827, Legius syndrome=MONDO:0012669, SPRED1=NCBIGene:161742, neurofibromin=UniProtKB:P21359, RASA1=NCBIGene:5921, HRAS=NCBIGene:3265, KRAS=NCBIGene:3845, MAP2K1=NCBIGene:5604. Full table in `references/curie-registry.md`.

## Graude: Issue triage procedure

Before opening new issues, audit existing open issues for staleness:
```bash
gh issue list --state open --limit 50
gh issue view <N>  # read body to understand original intent
```

Close issues that are already done by a later commit — do not leave them open as noise:
```bash
gh issue close <N> --comment "DONE — implemented in commit <sha>. <one-line summary>. Closed by @graude."
```

Re-title and re-label stale `[INFRA]` issues when a specialist now owns them:
```bash
gh issue edit <N> --title "[EMILY] <new title>" --add-label "engineering,emily" --remove-label "infrastructure"
```

Create labels before using them — `gh issue edit` fails silently if a label doesn't exist:
```bash
gh label create "emily" --description "Assigned to Emily" --color "e4e669" 2>&1 || true
```

## Graude: PR authority

Graude proposes harness/spec changes via PR; never self-merges. The gate:
- `scientific-governance/scientific-claim-rules/`, `claims/schema.json`: Gregory must approve; Rey reviews
- `scientific-governance/claim-validation-harness/`: Gregory must approve; CodeRabbit reviews
- Everything else: direct push to main is fine

When Graude catches a bug in infrastructure (bootstrap, CI, seed Cypher), he opens an `[EMILY]` issue with his diagnosis, then Emily executes. Graude fixed the bootstrap bug himself only because Emily didn't exist yet; that precedent does not repeat.
