---
name: New Claim Investigation
about: Assign Dirk to read a paper and extract claims
title: '[DIRK] Read: '
labels: claim, dirk
assignees: ''
---

## Paper

- **Title:**
- **DOI/PMID:**
- **Source:** (PubMed / bioRxiv / PMC / arXiv)

## Task

Directed by: @graude

Dirk: Please read this paper and extract all relevant claims about NF1 biology or clinical outcomes.

For each claim:
1. Create a JSON file in `claims/pending/` conforming to `claims/schema.json`
2. Assign evidence_strength per `testing/specs/evidence_rubric.yaml`
3. Run `python3 testing/harness/claim_validator.py` before committing
4. Commit with message: `claim(dirk): <paper short title>`
5. Comment on this issue with claim IDs extracted
