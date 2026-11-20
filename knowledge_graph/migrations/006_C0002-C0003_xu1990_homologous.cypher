// Migration 006: write accepted claims C0002, C0003 (PMID 2116237) - task issue #32, curated by Rey
// Idempotent - safe to re-run. Claim -> entity links use ABOUT (edge_constraints.yaml), not the per-claim FOUND_IN/ENCODES
// edge_type values, which are not valid from a Claim. Yeast Gene links (IRA1, IRA2, RAS2) are skipped - Gene requires an hgnc_id and yeast genes have none.
// Entity keys follow node_schemas.yaml unique_on, CURIE -> name/symbol resolved via OLS4 and HGNC REST.

MERGE (p:Publication {pmid: '2116237'})
ON CREATE SET p.title = 'The neurofibromatosis type 1 gene encodes a protein related to GAP', p.year = 1990, p.journal = 'Cell', p.first_author = 'Xu GF';

MERGE (c:Claim {claim_id: 'C0002'})
SET c.claim_text = 'A 360-residue region of the predicted NF1 protein shows significant sequence similarity to the catalytic domains of both human and bovine GAP (GTPase activating protein).',
    c.claim_type = 'molecular_function',
    c.evidence_strength = 3,
    c.evidence_type = 'computational',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text unavailable (not in PMC), extracted from abstract. Strength capped at 3: sequence-similarity evidence, no biochemical GAP assay in this paper. DOI: 10.1016/0092-8674(90)90024-9 (omitted from source_doi because schema oneOf rejects pmid+doi together). | Grounded by Otto via RTX-KG2c PloverDB (kg2cploverdb.transltr.io) and SRI Node Normalizer (nodenormalization-sri.renci.org), accessed 2026-11-17. neurofibromin=UniProtKB:P21359, RASA1 (human p120-RasGAP)=NCBIGene:5921 (UniProtKB:P20936). Predicate is sequence homology (biolink:homologous_to), now mapped to HOMOLOGOUS_TO per edge_constraints.yaml v1.0 (added 2026-11-17). NOTE: No NF1-RASA1 edge exists in RTX-KG2 (1531 NF1 edges checked). The 360-residue GAP-related domain (GRD, now known as NF1-GRD, residues ~1198-1530 of human neurofibromin) was first identified in this paper. | Re-grounded 2026-11-17: predicate corrected from ASSOCIATED_WITH to HOMOLOGOUS_TO after edge type was added to edge_constraints.yaml.',
    c.curation_date = '2026-11-19',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0002'}), (p:Publication {pmid: '2116237'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Protein {name: 'Neurofibromin'})
WITH n MATCH (c:Claim {claim_id: 'C0002'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'RASA1'}) ON CREATE SET n.hgnc_id = '9871', n.ncbi_gene_id = '5921', n.chromosome = '5q14.3'
WITH n MATCH (c:Claim {claim_id: 'C0002'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0003'})
SET c.claim_text = 'A broad region of the predicted NF1 protein, centered on the GAP-related 360-residue segment, is strikingly similar in sequence to the yeast IRA1 product, a functional homolog of mammalian GAP.',
    c.claim_type = 'molecular_function',
    c.evidence_strength = 3,
    c.evidence_type = 'computational',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text unavailable (not in PMC), extracted from abstract. Strength capped at 3: sequence-similarity evidence, no biochemical GAP assay in this paper. DOI: 10.1016/0092-8674(90)90024-9 (omitted from source_doi because schema oneOf rejects pmid+doi together). | Grounded by Otto via RTX-KG2c PloverDB (kg2cploverdb.transltr.io) and SRI Node Normalizer (nodenormalization-sri.renci.org), accessed 2026-11-17. neurofibromin=UniProtKB:P21359, yeast IRA1=NCBIGene:852437 (SGD:S000000344, UniProtKB:P18963). Predicate is cross-species sequence homology (biolink:homologous_to/orthologous_to), now mapped to HOMOLOGOUS_TO per edge_constraints.yaml v1.0 (added 2026-11-17). No NF1-IRA1 edge exists in RTX-KG2. IRA1 is a functional RAS-GAP homolog in S. cerevisiae, this paper established the NF1-IRA1 evolutionary link. | Re-grounded 2026-11-17: predicate corrected from ASSOCIATED_WITH to HOMOLOGOUS_TO after edge type was added to edge_constraints.yaml.',
    c.curation_date = '2026-11-19',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0003'}), (p:Publication {pmid: '2116237'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Protein {name: 'Neurofibromin'})
WITH n MATCH (c:Claim {claim_id: 'C0003'})
MERGE (c)-[:ABOUT]->(n);
