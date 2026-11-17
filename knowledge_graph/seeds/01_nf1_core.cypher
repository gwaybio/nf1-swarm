// Seed: NF1 core biology — gene, protein, pathways
// Source: OMIM #162200, UniProt P21359, HGNC 7765

MERGE (nf1:Gene {symbol: 'NF1'})
SET nf1.hgnc_id = '7765', nf1.chromosome = '17q11.2', nf1.ncbi_gene_id = '4763';

MERGE (nfm:Protein {name: 'Neurofibromin'})
SET nfm.uniprot_id = 'P21359',
    nfm.function_summary = 'RAS-GTPase activating protein converts RAS-GTP to RAS-GDP',
    nfm.molecular_weight_kda = 320;

MERGE (ras:Protein {name: 'RAS'}) SET ras.function_summary = 'Small GTPase active in GTP-bound form';
MERGE (mek:Protein {name: 'MEK'}) SET mek.uniprot_id = 'Q02750';
MERGE (erk:Protein {name: 'ERK'}) SET erk.uniprot_id = 'P28482';
MERGE (akt:Protein {name: 'AKT'}) SET akt.function_summary = 'PI3K/AKT/mTOR signaling kinase';
MERGE (mtor:Protein {name: 'mTOR'}) SET mtor.function_summary = 'mTORC1/2 nutrient sensing kinase';

MERGE (ras_mapk:Pathway {name: 'RAS/MAPK'})
SET ras_mapk.kegg_id = 'hsa04010', ras_mapk.reactome_id = 'R-HSA-5673001';

MERGE (pi3k:Pathway {name: 'PI3K/AKT/mTOR'})
SET pi3k.kegg_id = 'hsa04151';

MATCH (a:Gene {symbol: 'NF1'}), (b:Protein {name: 'Neurofibromin'})
MERGE (a)-[:ENCODES]->(b);

MATCH (a:Protein {name: 'Neurofibromin'}), (b:Pathway {name: 'RAS/MAPK'})
MERGE (a)-[:PART_OF]->(b);

MATCH (a:Protein {name: 'RAS'}), (b:Pathway {name: 'RAS/MAPK'})
MERGE (a)-[:PART_OF]->(b);

MATCH (a:Protein {name: 'MEK'}), (b:Pathway {name: 'RAS/MAPK'})
MERGE (a)-[:PART_OF]->(b);

MATCH (a:Protein {name: 'ERK'}), (b:Pathway {name: 'RAS/MAPK'})
MERGE (a)-[:PART_OF]->(b);

MATCH (a:Protein {name: 'AKT'}), (b:Pathway {name: 'PI3K/AKT/mTOR'})
MERGE (a)-[:PART_OF]->(b);

MATCH (a:Protein {name: 'mTOR'}), (b:Pathway {name: 'PI3K/AKT/mTOR'})
MERGE (a)-[:PART_OF]->(b);

MATCH (a:Protein {name: 'RAS'}), (b:Protein {name: 'MEK'})
MERGE (a)-[:ACTIVATES]->(b);

MATCH (a:Protein {name: 'MEK'}), (b:Protein {name: 'ERK'})
MERGE (a)-[:ACTIVATES]->(b);

MATCH (a:Protein {name: 'Neurofibromin'}), (b:Protein {name: 'RAS'})
MERGE (a)-[:INHIBITS]->(b);
