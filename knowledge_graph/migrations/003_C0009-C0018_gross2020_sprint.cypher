// Migration 003: write accepted claims C0009, C0010, C0011, C0013, C0014, C0015, C0016, C0017, C0018 (PMID 32187457) - task issue #32, curated by Rey
// Idempotent - safe to re-run. Claim -> entity links use ABOUT (edge_constraints.yaml), not the per-claim FOUND_IN/ENCODES
// edge_type values, which are not valid from a Claim. Mutation links are skipped (identifier is a gene CURIE, not an hgvs_cdna).
// Entity keys follow node_schemas.yaml unique_on, CURIE -> name/symbol resolved via OLS4 and HGNC REST.

MERGE (p:Publication {pmid: '32187457'})
ON CREATE SET p.title = 'Selumetinib in Children with Inoperable Plexiform Neurofibromas', p.year = 2020, p.journal = 'N Engl J Med', p.first_author = 'Gross AM', p.doi = '10.1056/NEJMoa1912735';

MERGE (c:Claim {claim_id: 'C0009'})
SET c.claim_text = 'In children aged 2-18 years with NF1 and inoperable symptomatic plexiform neurofibromas, selumetinib 25 mg/m2 every 12 hours produced a confirmed partial response (>=20% target-tumor volume decrease on consecutive MRIs >=3 months apart) in 35 of 50 patients (70%).',
    c.claim_type = 'drug_response',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = ' Full text (PMC7305659). Single-arm phase 2 (n=50, stratum 1 only), unblinded central MRI volumetry, capped at 3 because there is no randomized control (RCT/strength 4 criteria not met). | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. RTX-KG2 already has CHEBI:90227 treats_or_applied_or_studied_to_treat MONDO:0003304 (2 sources, PMIDs: 32108293, 32187457, 32272491).',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0009'}), (p:Publication {pmid: '32187457'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Drug {name: 'Selumetinib'})
WITH n MATCH (c:Claim {claim_id: 'C0009'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0009'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0009'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0010'})
SET c.claim_text = 'In children with NF1 and symptomatic plexiform neurofibromas treated with selumetinib, 28 of 50 patients (56%) had a durable partial response lasting at least 12 cycles (approximately 1 year).',
    c.claim_type = 'drug_response',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = ' Full text (PMC7305659). Single-arm phase 2 (n=50, stratum 1 only), unblinded central MRI volumetry, capped at 3 because there is no randomized control (RCT/strength 4 criteria not met). | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Durable response subset of C0009. Same RTX-KG2 edge applies.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0010'}), (p:Publication {pmid: '32187457'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Drug {name: 'Selumetinib'})
WITH n MATCH (c:Claim {claim_id: 'C0010'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0010'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0010'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0011'})
SET c.claim_text = 'In children with NF1 and symptomatic plexiform neurofibromas treated with selumetinib, progression-free survival was 84% at 3 years after treatment start, and median progression-free survival was not reached.',
    c.claim_type = 'clinical_outcome',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = ' Full text (PMC7305659). Single-arm phase 2 (n=50, stratum 1 only), unblinded central MRI volumetry, capped at 3 because there is no randomized control (RCT/strength 4 criteria not met). | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. PFS outcome, same CHEBI:90227->MONDO:0003304 edge.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0011'}), (p:Publication {pmid: '32187457'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Drug {name: 'Selumetinib'})
WITH n MATCH (c:Claim {claim_id: 'C0011'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0011'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0011'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0013'})
SET c.claim_text = 'After 12 months of selumetinib in children with NF1 plexiform neurofibromas, child-reported tumor pain intensity decreased by a mean of 2.14 points on the 11-point NRS (95% CI -3.14 to -1.14, 29 evaluable children).',
    c.claim_type = 'clinical_outcome',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = ' Full text (PMC7305659). Single-arm phase 2 (n=50, stratum 1 only), unblinded central MRI volumetry, capped at 3 because there is no randomized control (RCT/strength 4 criteria not met). Outcome measures other than Pain Interference Index and visual acuity are not validated in NF1 (per authors), uncontrolled, unblinded patient-reported outcomes. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Pain outcome of selumetinib treatment. Same edge as C0009.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0013'}), (p:Publication {pmid: '32187457'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Drug {name: 'Selumetinib'})
WITH n MATCH (c:Claim {claim_id: 'C0013'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0013'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0013'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0014'})
SET c.claim_text = 'After 12 cycles of selumetinib, 72% of children and 86% of parents with NF1 plexiform neurofibromas reported some improvement in tumor-related problems other than pain on the Global Impression of Change scale.',
    c.claim_type = 'clinical_outcome',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = ' Full text (PMC7305659). Single-arm phase 2 (n=50, stratum 1 only), unblinded central MRI volumetry, capped at 3 because there is no randomized control (RCT/strength 4 criteria not met). Outcome measures other than Pain Interference Index and visual acuity are not validated in NF1 (per authors), uncontrolled, unblinded patient-reported outcomes. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Patient/parent-reported outcomes. Same edge as C0009.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0014'}), (p:Publication {pmid: '32187457'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Drug {name: 'Selumetinib'})
WITH n MATCH (c:Claim {claim_id: 'C0014'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0014'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0014'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0015'})
SET c.claim_text = 'Among 18 evaluable children with NF1 plexiform neurofibroma-related motor dysfunction, 14 (78%) improved muscle strength by manual muscle testing after 12 cycles of selumetinib, with a median increase of 4.8% in total strength score.',
    c.claim_type = 'clinical_outcome',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = ' Full text (PMC7305659). Single-arm phase 2 (n=50, stratum 1 only), unblinded central MRI volumetry, capped at 3 because there is no randomized control (RCT/strength 4 criteria not met). Outcome measures other than Pain Interference Index and visual acuity are not validated in NF1 (per authors), uncontrolled, unblinded patient-reported outcomes. Small subgroup. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Motor dysfunction outcome. HP:0001324 (Muscle weakness) added as related phenotype.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0015'}), (p:Publication {pmid: '32187457'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Drug {name: 'Selumetinib'})
WITH n MATCH (c:Claim {claim_id: 'C0015'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0015'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0015'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0001324'}) ON CREATE SET n.name = 'Muscle weakness'
WITH n MATCH (c:Claim {claim_id: 'C0015'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0016'})
SET c.claim_text = 'In the selumetinib phase 2 trial in children with NF1 plexiform neurofibromas, no moderate or strong correlations were found between changes in functional or patient-reported outcomes and percentage change in tumor volume.',
    c.claim_type = 'clinical_outcome',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = ' Full text (PMC7305659). Single-arm phase 2 (n=50, stratum 1 only), unblinded central MRI volumetry, capped at 3 because there is no randomized control (RCT/strength 4 criteria not met). | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Negative correlation finding. Same entities as C0009.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0016'}), (p:Publication {pmid: '32187457'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Drug {name: 'Selumetinib'})
WITH n MATCH (c:Claim {claim_id: 'C0016'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0016'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0016'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0017'})
SET c.claim_text = 'The most common toxic effects of selumetinib in children with NF1 plexiform neurofibromas were grade 1-2 gastrointestinal symptoms, asymptomatic creatine phosphokinase elevation, acneiform rash, and paronychia.',
    c.claim_type = 'drug_response',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = ' Full text (PMC7305659). Single-arm phase 2 (n=50, stratum 1 only), unblinded central MRI volumetry, capped at 3 because there is no randomized control (RCT/strength 4 criteria not met). | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Toxicity profile claim. TREATS used as the drug-disease relationship, adverse effects are described in claim_text.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0017'}), (p:Publication {pmid: '32187457'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Drug {name: 'Selumetinib'})
WITH n MATCH (c:Claim {claim_id: 'C0017'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0017'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0017'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0018'})
SET c.claim_text = 'In the phase 2 selumetinib trial in 50 children with NF1 plexiform neurofibromas, 14 patients (28%) required dose reductions for toxic effects and 5 (10%) discontinued treatment because of toxic effects possibly related to selumetinib.',
    c.claim_type = 'drug_response',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = ' Full text (PMC7305659). Single-arm phase 2 (n=50, stratum 1 only), unblinded central MRI volumetry, capped at 3 because there is no randomized control (RCT/strength 4 criteria not met). | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Tolerability claim. Same entities as C0009.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0018'}), (p:Publication {pmid: '32187457'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Drug {name: 'Selumetinib'})
WITH n MATCH (c:Claim {claim_id: 'C0018'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0018'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0018'})
MERGE (c)-[:ABOUT]->(n);
