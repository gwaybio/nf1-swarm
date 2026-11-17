// Seed: NF1 treatments
// Source: FDA approval, SPRINT trial NCT01362803

MERGE (sel:Drug {name: 'Selumetinib'})
SET sel.mechanism = 'MEK1/2 inhibitor',
    sel.approval_status = 'FDA approved 2020 pediatric NF1 plexiform neurofibroma',
    sel.brand_name = 'Koselugo';

MERGE (bin:Drug {name: 'Binimetinib'})
SET bin.mechanism = 'MEK1/2 inhibitor', bin.approval_status = 'FDA approved melanoma';

MERGE (sprint:ClinicalTrial {nct_id: 'NCT01362803'})
SET sprint.phase = '2/3',
    sprint.outcome_summary = '71% partial response >= 20% volume reduction',
    sprint.year_start = 2015, sprint.status = 'Completed';

MATCH (a:Drug {name: 'Selumetinib'}), (b:Protein {name: 'MEK'})
MERGE (a)-[:INHIBITS]->(b);

MATCH (a:Drug {name: 'Binimetinib'}), (b:Protein {name: 'MEK'})
MERGE (a)-[:INHIBITS]->(b);

MATCH (a:Drug {name: 'Selumetinib'}), (b:Phenotype {hpo_id: 'HP:0009732'})
MERGE (a)-[:TREATS]->(b);
