// Migration 004: write accepted claims C0019, C0021, C0026, C0027, C0028, C0029 (PMID 34012067) - task issue #32, curated by Rey
// Idempotent - safe to re-run. Claim -> entity links use ABOUT (edge_constraints.yaml), not the per-claim FOUND_IN/ENCODES
// edge_type values, which are not valid from a Claim. Mutation links are skipped (identifier is a gene CURIE, not an hgvs_cdna).
// Entity keys follow node_schemas.yaml unique_on, CURIE -> name/symbol resolved via OLS4 and HGNC REST.

MERGE (p:Publication {pmid: '34012067'})
ON CREATE SET p.title = 'Revised diagnostic criteria for neurofibromatosis type 1 and Legius syndrome: an international consensus recommendation', p.year = 2021, p.journal = 'Genet Med', p.first_author = 'Legius E', p.doi = '10.1038/s41436-021-01170-5';

MERGE (c:Claim {claim_id: 'C0019'})
SET c.claim_text = 'The 2021 international consensus recommends that NF1 be diagnosed in an individual without a parent with NF1 if two or more are present: >=6 cafe-au-lait macules, axillary/inguinal freckling, >=2 neurofibromas or 1 plexiform neurofibroma, optic pathway glioma, >=2 Lisch nodules or choroidal abnormalities, a distinctive osseous lesion, or a heterozygous pathogenic NF1 variant at ~50% allele fraction.',
    c.claim_type = 'phenotype_association',
    c.evidence_strength = 2,
    c.evidence_type = 'expert_opinion',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Modified Delphi expert consensus (74/76 experts), rubric forbids expert_opinion at strength >=4, so capped at 2. Recommendation, not an empirical finding. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Diagnostic criteria claim — multiple phenotypes mentioned. Primary triple uses cafe-au-lait as exemplar, full phenotype list in related_nodes. ASSOCIATED_WITH used descriptively (Gene/Mutation->Phenotype/Disease in constraints, but subject is Disease here).',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0019'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0019'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0019'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0000957'}) ON CREATE SET n.name = 'Cafe-au-lait spot'
WITH n MATCH (c:Claim {claim_id: 'C0019'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0001480'}) ON CREATE SET n.name = 'Freckling'
WITH n MATCH (c:Claim {claim_id: 'C0019'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0009737'}) ON CREATE SET n.name = 'Lisch nodules'
WITH n MATCH (c:Claim {claim_id: 'C0019'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0019'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Optic pathway glioma'}) SET n.mondo_id = 'MONDO:0016167'
WITH n MATCH (c:Claim {claim_id: 'C0019'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0021'})
SET c.claim_text = 'The 2021 consensus added choroidal abnormalities (bright patchy nodules on OCT/near-infrared reflectance imaging) as an NF1 diagnostic criterion, counted interchangeably with >=2 iris Lisch nodules rather than as a separate criterion.',
    c.claim_type = 'phenotype_association',
    c.evidence_strength = 2,
    c.evidence_type = 'expert_opinion',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Modified Delphi expert consensus (74/76 experts), rubric forbids expert_opinion at strength >=4, so capped at 2. Recommendation, not an empirical finding. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Choroidal abnormalities and Lisch nodules as interchangeable criteria. No specific HPO for NF1-associated choroidal abnormalities, HP:0009737 (Lisch nodules) used as the grounded criterion.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0021'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0021'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0009737'}) ON CREATE SET n.name = 'Lisch nodules'
WITH n MATCH (c:Claim {claim_id: 'C0021'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0026'})
SET c.claim_text = 'SPRED1 pathogenic variants account for about 1% of sporadic and 19% of familial cases presenting with only the pigmentary features of NF1 (cafe-au-lait macules and freckling).',
    c.claim_type = 'genetic_association',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Data cited from a primary study (secondary citation in a consensus paper): Messiaen et al. (ref 14). Primary paper should be read directly and may support a higher strength. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. SPRED1=NCBIGene:161742, Legius syndrome=MONDO:0012669. RTX-KG2 has SPRED1 causes/biomarker_for Legius syndrome (5 edges). Mutation identifier uses gene CURIE (specific variants not cataloged here).',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0026'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'SPRED1'}) ON CREATE SET n.hgnc_id = '20249', n.ncbi_gene_id = '161742', n.chromosome = '15q14'
WITH n MATCH (c:Claim {claim_id: 'C0026'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0026'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Legius syndrome'}) SET n.mondo_id = 'MONDO:0012669'
WITH n MATCH (c:Claim {claim_id: 'C0026'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0000957'}) ON CREATE SET n.name = 'Cafe-au-lait spot'
WITH n MATCH (c:Claim {claim_id: 'C0026'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0027'})
SET c.claim_text = 'Legius syndrome, caused by heterozygous SPRED1 pathogenic variants, presents with multiple cafe-au-lait macules with or without freckling, and no individuals with Legius syndrome have been reported to develop Lisch nodules or neurofibromas.',
    c.claim_type = 'phenotype_association',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Data cited from a primary study (secondary citation in a consensus paper): refs 13, 14. Primary paper should be read directly and may support a higher strength. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. SPRED1=NCBIGene:161742 causes Legius syndrome=MONDO:0012669. RTX-KG2 confirms: NCBIGene:161742 biolink:causes MONDO:0012669 (2 sources). CAUSES predicate requires Mutation->Disease in edge_constraints, SPRED1 pathogenic variant class used as subject.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0027'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'SPRED1'}) ON CREATE SET n.hgnc_id = '20249', n.ncbi_gene_id = '161742', n.chromosome = '15q14'
WITH n MATCH (c:Claim {claim_id: 'C0027'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Legius syndrome'}) SET n.mondo_id = 'MONDO:0012669'
WITH n MATCH (c:Claim {claim_id: 'C0027'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0000957'}) ON CREATE SET n.name = 'Cafe-au-lait spot'
WITH n MATCH (c:Claim {claim_id: 'C0027'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0001480'}) ON CREATE SET n.name = 'Freckling'
WITH n MATCH (c:Claim {claim_id: 'C0027'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0028'})
SET c.claim_text = 'Dosage analysis plus DNA sequencing detects a pathogenic NF1 variant in about 90% of classic nonfounder NF1 patients, and adding RNA-based sequencing raises detection to 95-97%.',
    c.claim_type = 'genetic_association',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Data cited from a primary study (secondary citation in a consensus paper): ref 34. Primary paper should be read directly and may support a higher strength. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Variant detection methodology claim. Mutation identifier uses gene CURIE (class-level, not specific variant).',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0028'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0028'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibromatosis type 1'}) SET n.mondo_id = 'MONDO:0018975'
WITH n MATCH (c:Claim {claim_id: 'C0028'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0000957'}) ON CREATE SET n.name = 'Cafe-au-lait spot'
WITH n MATCH (c:Claim {claim_id: 'C0028'})
MERGE (c)-[:ABOUT]->(n);

MERGE (c:Claim {claim_id: 'C0029'})
SET c.claim_text = 'Somatic second-hit NF1 pathogenic variants are typically identified in every NF1-associated tumor, including cutaneous and plexiform neurofibromas, and in cafe-au-lait macules, resulting in biallelic NF1 inactivation.',
    c.claim_type = 'genetic_association',
    c.evidence_strength = 3,
    c.evidence_type = 'cohort_study',
    c.status = 'accepted',
    c.extracted_by = 'dirk',
    c.curated_by = 'rey',
    c.notes = 'Full text (PMC8354850). Data cited from a primary study (secondary citation in a consensus paper): refs incl. 37 (CALM melanocytes). Primary paper should be read directly and may support a higher strength. | Grounded by Otto via RTX-KG2c PloverDB + SRI Node Normalizer, accessed 2026-11-18. Biallelic NF1 inactivation (Knudson two-hit) in NF1-associated tumors. neurofibroma=MONDO:0016755, plexiform neurofibroma=MONDO:0003304, cafe-au-lait=HP:0000957.',
    c.curation_date = '2026-11-18',
    c.extraction_date = '2026-11-17';

MATCH (c:Claim {claim_id: 'C0029'}), (p:Publication {pmid: '34012067'})
MERGE (c)-[:EXTRACTED_FROM]->(p);

MERGE (n:Gene {symbol: 'NF1'}) ON CREATE SET n.hgnc_id = '7765', n.ncbi_gene_id = '4763', n.chromosome = '17q11.2'
WITH n MATCH (c:Claim {claim_id: 'C0029'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Neurofibroma'}) SET n.mondo_id = 'MONDO:0016755'
WITH n MATCH (c:Claim {claim_id: 'C0029'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Disease {name: 'Plexiform neurofibroma'}) SET n.mondo_id = 'MONDO:0003304'
WITH n MATCH (c:Claim {claim_id: 'C0029'})
MERGE (c)-[:ABOUT]->(n);

MERGE (n:Phenotype {hpo_id: 'HP:0000957'}) ON CREATE SET n.name = 'Cafe-au-lait spot'
WITH n MATCH (c:Claim {claim_id: 'C0029'})
MERGE (c)-[:ABOUT]->(n);
