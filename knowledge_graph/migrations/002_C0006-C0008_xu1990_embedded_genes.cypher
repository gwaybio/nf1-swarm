// Migration 002: write accepted claims C0006, C0007, C0008 (PMID 2116237) - task issue #32, curated by Rey
// Idempotent - safe to re-run. Claim -> entity links use ABOUT (edge_constraints.yaml), not the per-claim FOUND_IN/ENCODES
// edge_type values, which are not valid from a Claim. Mutation links are skipped (identifier is a gene CURIE, not an hgvs_cdna).
// Entity keys follow node_schemas.yaml unique_on, CURIE -> name/symbol resolved via OLS4 and HGNC REST.

MERGE (p:Publication {pmid: '2116237'})
ON CREATE SET p.title = 'The neurofibromatosis type 1 gene encodes a protein related to GAP', p.year = 1990, p.journal = 'Cell', p.first_author = 'Xu GF';

MERGE (c:Claim {claim_id: 'C0006'})
SET c.claim_text = 'The EVI2B gene lies within an intron of NF1 and is transcribed in the orientation opposite to NF1.',
    c.claim_type = 'molecular_function',
    c.evidence_strength = 3,
    c.evidence_type = 'preclinical_in_vitro',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Split from C0005 (rejected: multi-CURIE object_id). Grounded by Otto via RTX-KG2c PloverDB (kg2cploverdb.transltr.io) and SRI Node Normalizer (nodenormalization-sri.renci.org), accessed 2026-11-17. EVI2B=NCBIGene:2124 (HGNC:3500), NF1=NCBIGene:4763. EVI2B resides within intron 27b of NF1 and is transcribed antisense to NF1. FOUND_IN used as the permitted edge type for Gene->Gene genomic containment per edge_constraints.yaml.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0006'}), (p:Publication {pmid: '2116237'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'EVI2B'}) ON CREATE SET n.hgnc_id = '3500', n.ncbi_gene_id = '2124', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0006'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0006'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Protein {name: 'Neurofibromin'})
WITH n MATCH (c:Claim {claim_id: 'C0006'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0007'})
SET c.claim_text = 'The EVI2A gene lies within an intron of NF1 and is transcribed in the orientation opposite to NF1.',
    c.claim_type = 'molecular_function',
    c.evidence_strength = 3,
    c.evidence_type = 'preclinical_in_vitro',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Split from C0005 (rejected: multi-CURIE object_id). Grounded by Otto via RTX-KG2c PloverDB (kg2cploverdb.transltr.io) and SRI Node Normalizer (nodenormalization-sri.renci.org), accessed 2026-11-17. EVI2A=NCBIGene:2123 (HGNC:3499), NF1=NCBIGene:4763. EVI2A resides within intron 27b of NF1 and is transcribed antisense to NF1. FOUND_IN used as the permitted edge type for Gene->Gene genomic containment per edge_constraints.yaml.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0007'}), (p:Publication {pmid: '2116237'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'EVI2A'}) ON CREATE SET n.hgnc_id = '3499', n.ncbi_gene_id = '2123', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0007'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0007'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Protein {name: 'Neurofibromin'})
WITH n MATCH (c:Claim {claim_id: 'C0007'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0008'})
SET c.claim_text = 'The OMG gene lies within an intron of NF1 and is transcribed in the orientation opposite to NF1.',
    c.claim_type = 'molecular_function',
    c.evidence_strength = 3,
    c.evidence_type = 'preclinical_in_vitro',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Split from C0005 (rejected: multi-CURIE object_id). Grounded by Otto via RTX-KG2c PloverDB (kg2cploverdb.transltr.io) and SRI Node Normalizer (nodenormalization-sri.renci.org), accessed 2026-11-17. OMG=NCBIGene:4974 (HGNC:8135), NF1=NCBIGene:4763. OMG resides within intron 27b of NF1 and is transcribed antisense to NF1. FOUND_IN used as the permitted edge type for Gene->Gene genomic containment per edge_constraints.yaml.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0008'}), (p:Publication {pmid: '2116237'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'OMG'}) ON CREATE SET n.hgnc_id = '8135', n.ncbi_gene_id = '4974', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0008'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0008'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Protein {name: 'Neurofibromin'})
WITH n MATCH (c:Claim {claim_id: 'C0008'})
MERGE (c)-[:ABOUT]->(n);
