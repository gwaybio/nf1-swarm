# Stage 1 extraction details

## Fetching text
- Verify identifiers: `curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=<PMID>&retmode=json"` (title, DOI, PMCID in articleids). Abstract: `efetch ... rettype=abstract&retmode=text`. Find a PMID from a title/DOI with `esearch ... [title]`; DOI searches with uppercase suffix can miss.
- `literature/fetcher.py` may be broken; fetch directly instead of editing it.
- Full text order: (1) NCBI `efetch db=pmc&id=<numeric>&retmode=xml` — works for OA papers, but some publishers embed only the abstract (look for the XML comment "does not allow downloading of the full text"); (2) Europe PMC `fullTextXML` (can return 500); (3) the PMC article HTML with a browser User-Agent via curl, parsed with `uv run --no-project --with beautifulsoup4 --with lxml python` (body paragraphs, tables, and the `ref-list` with PubMed/DOI hrefs). `web_extract` may truncate long pages.
- Save text under the profile workspace, then read it with the file reader; don't paste into prompts.

## Strength / type mapping that passes the validator
- Check `testing/specs/claim_contract.yaml`: each claim_type restricts evidence_type (e.g. `genetic_association` needs cohort/systematic_review/biochemical/in-vivo; `expert_opinion` only fits `phenotype_association`; `clinical_outcome` allows rct/cohort/case_report/systematic_review; `drug_response` allows rct/cohort/preclinical).
- Gene-structure or sequence-homology findings: `molecular_function` + `computational`/`preclinical_in_vitro`, strength 3 max.
- Abstract-only: cap 3. Single-arm phase 2 with external comparator: 3, not 4 (4 needs RCT or multiple independent cohorts). Expert/Delphi consensus recommendations: `expert_opinion`, strength 2 (rubric forbids it at 4-5). Data from conference abstracts/presentations: 2. Rubric lists `cohort_study` under 3-4 only but the validator accepts it at 2.
- Do not inflate to match an issue's "expect strength N"; report why in the STATUS comment.
- Rejected claims often fail because a claim_type requires a node label in `related_nodes` (phenotype_association needs a Phenotype). When fixing: look up HPO IDs in OLS (`https://www.ebi.ac.uk/ols4/api/search?q=<term>&ontology=hp&rows=3`) — never recall IDs; reset status to pending, clear rejection fields, null semantic triples Rey called wrong.

## Review articles / consensus papers
- Two outputs: (1) claims the review makes with explicit citations, each flagged as a secondary citation in `notes` and `independence_flags` (so Stan does not count it as independent evidence) with the primary PMID in the notes; (2) a catalogue of cited primary studies posted as an issue comment: PMID/DOI from the PMC reference links (not memory), title, claim territory, conference abstracts listed separately (no IDs), non-NF1 items excluded, and a suggested queue order.
- Cross-check numbers against the primary paper you already read; report discrepancies instead of choosing silently.
- Re-read each drafted claim against the source sentence before committing: attribute results to the right trial/drug (one draft mixed two trials).
- Note when a flagged target (e.g. a trial) is not cited because the review predates it.
