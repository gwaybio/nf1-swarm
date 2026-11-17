// Seed: NF1 disease and core phenotypes
// Source: OMIM #162200, HPO, GeneReviews

MERGE (nf1d:Disease {name: 'Neurofibromatosis type 1'})
SET nf1d.omim_id = '162200', nf1d.orpha_id = '636',
    nf1d.icd10 = 'Q85.0', nf1d.prevalence = '1 in 3000 births';

MERGE (calm:Phenotype {hpo_id: 'HP:0000957'})
SET calm.name = 'Café-au-lait spot', calm.frequency_in_nf1 = '> 95%';

MERGE (cnf:Phenotype {hpo_id: 'HP:0001067'})
SET cnf.name = 'Cutaneous neurofibroma', cnf.frequency_in_nf1 = '> 95% in adults';

MERGE (pnf:Phenotype {hpo_id: 'HP:0009732'})
SET pnf.name = 'Plexiform neurofibroma', pnf.frequency_in_nf1 = '~30-50%';

MERGE (opg:Phenotype {hpo_id: 'HP:0009734'})
SET opg.name = 'Optic pathway glioma', opg.frequency_in_nf1 = '~15%';

MERGE (mpnst:Phenotype {hpo_id: 'HP:0100724'})
SET mpnst.name = 'Malignant peripheral nerve sheath tumor', mpnst.frequency_in_nf1 = '8-15% lifetime';

MERGE (nf1g:Gene {symbol: 'NF1'});
MATCH (nf1g:Gene {symbol: 'NF1'}), (nf1d:Disease {omim_id: '162200'})
MERGE (nf1g)-[:ASSOCIATED_WITH]->(nf1d);

MATCH (nf1d:Disease {omim_id: '162200'})
MERGE (nf1d)-[:ASSOCIATED_WITH]->(calm:Phenotype {hpo_id: 'HP:0000957'});
MATCH (nf1d:Disease {omim_id: '162200'})
MERGE (nf1d)-[:ASSOCIATED_WITH]->(pnf:Phenotype {hpo_id: 'HP:0009732'});
MATCH (nf1d:Disease {omim_id: '162200'})
MERGE (nf1d)-[:ASSOCIATED_WITH]->(opg:Phenotype {hpo_id: 'HP:0009734'});
MATCH (nf1d:Disease {omim_id: '162200'})
MERGE (nf1d)-[:ASSOCIATED_WITH]->(mpnst:Phenotype {hpo_id: 'HP:0100724'});
