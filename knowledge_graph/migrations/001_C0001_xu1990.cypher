// Migration 001: write accepted claim C0001 (Xu et al. 1990, PMID 2116237) - task issue #17, curated by Rey
// Idempotent - safe to re-run. Adds Claim + Publication nodes and one EXTRACTED_FROM edge.
// Gene:NF1 -[:ENCODES]-> Protein:Neurofibromin already exists in seeds/01_nf1_core.cypher.
// NOTE: C0001.json related_nodes lists ENCODES for Gene and Protein, but edge_constraints.yaml only
// permits ENCODES from Gene to Protein, so no Claim-[:ENCODES] edges are written here.

MERGE (p:Publication {pmid: '2116237'})
ON CREATE SET p.title = 'The neurofibromatosis type 1 gene encodes a protein related to GAP',
              p.year = 1990,
              p.journal = 'Cell',
              p.first_author = 'Xu GF',
              p.doi = '10.1016/0092-8674(90)90024-9';

MERGE (c:Claim {claim_id: 'C0001'})
SET c.claim_text = 'cDNA walking and sequencing extended the NF1 open reading frame so that it predicts an NF1 polypeptide of 2485 amino acids.',
    c.claim_type = 'molecular_function',
    c.evidence_strength = 3,
    c.evidence_type = 'computational',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text unavailable (not in PMC), extracted from abstract. Strength capped at 3 - sequence-similarity evidence, no biochemical GAP assay in this paper. Grounded by Otto via RTX-KG2c PloverDB and SRI Node Normalizer, accessed 2026-11-17. NF1 gene=NCBIGene:4763, neurofibromin=UniProtKB:P21359.';

MATCH (c:Claim {claim_id: 'C0001'}), (p:Publication {pmid: '2116237'})
MERGE (c)-[:EXTRACTED_FROM]->(p);
