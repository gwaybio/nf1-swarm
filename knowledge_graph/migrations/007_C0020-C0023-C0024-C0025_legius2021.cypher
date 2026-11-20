// Migration 007: write accepted claims C0020, C0023, C0024, C0025 (PMID 34012067) - task issue #32, curated by Rey
// Idempotent - safe to re-run. Claim -> entity links use ABOUT (edge_constraints.yaml), not the per-claim FOUND_IN/ENCODES
// edge_type values, which are not valid from a Claim. Yeast Gene links (IRA1, IRA2, RAS2) are skipped - Gene requires an hgnc_id and yeast genes have none.
// Entity keys follow node_schemas.yaml unique_on, CURIE -> name/symbol resolved via OLS4 and HGNC REST.

MERGE (p:Publication {pmid: '34012067'})
ON CREATE SET p.title = 'Revised diagnostic criteria for neurofibromatosis type 1 and Legius syndrome: an international consensus recommendation', p.year = 2021, p.journal = 'Genet Med', p.first_author = 'Legius E', p.doi = '10.1038/s41436-021-01170-5';

MERGE (c:Claim {claim_id: 'C0020'})
SET c.claim_text = 'The 2021 consensus revised NF1 diagnostic criteria add a heterozygous pathogenic NF1 variant (variant allele fraction 50%) in apparently normal tissue such as white blood cells as a new diagnostic criterion, without implying that genetic testing is required.',
    c.claim_type = 'phenotype_association',
    c.evidence_strength = 2,
    c.evidence_type = 'expert_opinion',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Modified Delphi expert consensus (74/76 experts), rubric forbids expert_opinion at strength >=4, so capped at 2. Recommendation, not an empirical finding. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. NF1 variant as diagnostic criterion. Gene->Disease fits ASSOCIATED_WITH constraints.',
    c.curation_date = '2026-11-19',
    c.extraction_date = '2026-11-18';

MATCH (c:Claim {claim_id: 'C0020'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0020'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0020'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0000006'}) ON CREATE SET n.name = 'Autosomal dominant inheritance'
WITH n MATCH (c:Claim {claim_id: 'C0020'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0023'})
SET c.claim_text = 'The 2021 consensus states that identification of an NF1 variant in blood alone does not suffice to diagnose NF1, the variant must be confirmed pathogenic by an orthogonal method and classified as constitutional, mosaic, or somatic, and likely pathogenic variants should not count as a criterion.',
    c.claim_type = 'phenotype_association',
    c.evidence_strength = 2,
    c.evidence_type = 'expert_opinion',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Modified Delphi expert consensus (74/76 experts), rubric forbids expert_opinion at strength >=4, so capped at 2. Recommendation, not an empirical finding. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Variant classification requirements for NF1 diagnosis.',
    c.curation_date = '2026-11-19',
    c.extraction_date = '2026-11-18';

MATCH (c:Claim {claim_id: 'C0023'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0023'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0023'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0001442'}) ON CREATE SET n.name = 'Typified by somatic mosaicism'
WITH n MATCH (c:Claim {claim_id: 'C0023'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0024'})
SET c.claim_text = 'The 2021 consensus defines mosaic NF1 as a pathogenic heterozygous NF1 variant with a variant allele fraction significantly below 50% in apparently normal tissue plus one other NF1 criterion, or the identical pathogenic variant in two anatomically independent affected tissues.',
    c.claim_type = 'phenotype_association',
    c.evidence_strength = 2,
    c.evidence_type = 'expert_opinion',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Modified Delphi expert consensus (74/76 experts), rubric forbids expert_opinion at strength >=4, so capped at 2. Recommendation, not an empirical finding. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Mosaic NF1 definition. Same gene-disease relationship as C0023.',
    c.curation_date = '2026-11-19',
    c.extraction_date = '2026-11-18';

MATCH (c:Claim {claim_id: 'C0024'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0024'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0024'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0001442'}) ON CREATE SET n.name = 'Typified by somatic mosaicism'
WITH n MATCH (c:Claim {claim_id: 'C0024'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0025'})
SET c.claim_text = 'In a cohort of 2,432 individuals referred for NF1 molecular diagnosis, NIH criteria had sensitivity 58.2% and specificity 88.6% for detecting a pathogenic NF1 or SPRED1 variant in children under 7 years, versus sensitivity 85.3% and specificity 74.3% at age 7 or older.',
    c.claim_type = 'phenotype_association',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Data cited from a primary study (secondary citation in a consensus paper): Messiaen et al. (ref 14 of the consensus paper). Primary paper should be read directly and may support a higher strength. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Diagnostic test performance. SPRED1=NCBIGene:161742 included as it is part of the molecular diagnosis cohort.',
    c.curation_date = '2026-11-19',
    c.extraction_date = '2026-11-18';

MATCH (c:Claim {claim_id: 'C0025'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0025'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0025'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'SPRED1'}) ON CREATE SET n.hgnc_id = '20249', n.ncbi_gene_id = '161742', n.chromosome = '15q14'
WITH n MATCH (c:Claim {claim_id: 'C0025'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0007565'}) ON CREATE SET n.name = 'Multiple cafe-au-lait spots'
WITH n MATCH (c:Claim {claim_id: 'C0025'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0000997'}) ON CREATE SET n.name = 'Axillary freckling'
WITH n MATCH (c:Claim {claim_id: 'C0025'})
MERGE (c)-[:ABOUT]->(n);
