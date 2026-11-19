// Migration 005: write accepted claims C0031, C0032, C0035 (PMID 2121369) - task issue #32, curated by Rey
// Idempotent - safe to re-run. Claim -> entity links use ABOUT (edge_constraints.yaml), not the per-claim FOUND_IN/ENCODES
// edge_type values, which are not valid from a Claim. Yeast Gene links (IRA1, IRA2, RAS2) are skipped - Gene requires an hgnc_id and yeast genes have none.
// Entity keys follow node_schemas.yaml unique_on, CURIE -> name/symbol resolved via OLS4 and HGNC REST.

MERGE (p:Publication {pmid: '2121369'})
ON CREATE SET p.title = 'The catalytic domain of the neurofibromatosis type 1 gene product stimulates ras GTPase and complements ira mutants of S. cerevisiae', p.year = 1990, p.journal = 'Cell', p.first_author = 'Xu GF', p.doi = '10.1016/0092-8674(90)90149-9';

MERGE (c:Claim {claim_id: 'C0031'})
SET c.claim_text = 'Expression of the GAP-related domain of the NF1 protein suppresses the heat shock-sensitive phenotype of yeast ira1 and ira2 mutants.',
    c.claim_type = 'molecular_function',
    c.evidence_strength = 3,
    c.evidence_type = 'preclinical_in_vivo',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text unavailable, extracted from abstract. Capped at 3 per abstract-only rule, the underlying experiments are foundational and replicated for decades, so Rey may upgrade (strength 5 needs full-text/independent replication linked via supporting_dois). | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. neurofibromin=UniProtKB:P21359, IRA1=NCBIGene:852437 (SGD:S000000344), IRA2=NCBIGene:854073. ACTIVATES used: NF1 GRD functionally complements yeast IRA loss (Protein->Protein per edge_constraints). Yeast complementation assay = preclinical_in_vivo (whole organism).',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0031'}), (p:Publication {pmid: '2121369'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Protein {name: 'Neurofibromin'})
WITH n MATCH (c:Claim {claim_id: 'C0031'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0031'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0032'})
SET c.claim_text = 'The GAP-related NF1 domain, purified as a GST fusion protein, strongly stimulates the GTPase activity of yeast RAS2 and human H-ras proteins.',
    c.claim_type = 'molecular_function',
    c.evidence_strength = 3,
    c.evidence_type = 'preclinical_in_vitro',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text unavailable, extracted from abstract. Capped at 3 per abstract-only rule, the underlying experiments are foundational and replicated for decades, so Rey may upgrade (strength 5 needs full-text/independent replication linked via supporting_dois). | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. evidence_type changed from biochemical_proof to preclinical_in_vitro (abstract-only cap at strength 3, biochemical_proof requires 4-5). neurofibromin=UniProtKB:P21359, HRAS=NCBIGene:3265, yeast RAS2=NCBIGene:855625. ACTIVATES: NF1 GRD stimulates GTPase activity (Protein->Protein).',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0032'}), (p:Publication {pmid: '2121369'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Protein {name: 'Neurofibromin'})
WITH n MATCH (c:Claim {claim_id: 'C0032'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0032'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'HRAS'}) ON CREATE SET n.hgnc_id = '5173', n.ncbi_gene_id = '3265', n.chromosome = '11p15.5'
WITH n MATCH (c:Claim {claim_id: 'C0032'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0035'})
SET c.claim_text = 'The GAP-related domain of the NF1 protein has ras GAP activity similar to that of yeast IRA2 protein and mammalian GAP.',
    c.claim_type = 'molecular_function',
    c.evidence_strength = 3,
    c.evidence_type = 'preclinical_in_vitro',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text unavailable, extracted from abstract. Capped at 3 per abstract-only rule, the underlying experiments are foundational and replicated for decades, so Rey may upgrade (strength 5 needs full-text/independent replication linked via supporting_dois). | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. evidence_type changed from biochemical_proof to preclinical_in_vitro. HOMOLOGOUS_TO: functional equivalence of NF1 GRD, IRA2, and mammalian GAP in RAS-GAP activity. neurofibromin=UniProtKB:P21359, RASA1=NCBIGene:5921, IRA2=NCBIGene:854073.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0035'}), (p:Publication {pmid: '2121369'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Protein {name: 'Neurofibromin'})
WITH n MATCH (c:Claim {claim_id: 'C0035'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0035'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'RASA1'}) ON CREATE SET n.hgnc_id = '9871', n.ncbi_gene_id = '5921', n.chromosome = '5q14.3'
WITH n MATCH (c:Claim {claim_id: 'C0035'})
MERGE (c)-[:ABOUT]->(n);
