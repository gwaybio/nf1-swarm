// NF1-Swarm Neo4j Constraints — run once after installation

CREATE CONSTRAINT gene_symbol_unique IF NOT EXISTS FOR (g:Gene) REQUIRE g.symbol IS UNIQUE;
CREATE CONSTRAINT protein_name_unique IF NOT EXISTS FOR (p:Protein) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT pathway_name_unique IF NOT EXISTS FOR (p:Pathway) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT disease_name_unique IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT drug_name_unique IF NOT EXISTS FOR (d:Drug) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT phenotype_hpo_unique IF NOT EXISTS FOR (p:Phenotype) REQUIRE p.hpo_id IS UNIQUE;
CREATE CONSTRAINT mutation_hgvs_unique IF NOT EXISTS FOR (m:Mutation) REQUIRE m.hgvs_cdna IS UNIQUE;
CREATE CONSTRAINT publication_pmid_unique IF NOT EXISTS FOR (p:Publication) REQUIRE p.pmid IS UNIQUE;
CREATE CONSTRAINT publication_doi_unique IF NOT EXISTS FOR (p:Publication) REQUIRE p.doi IS UNIQUE;
CREATE CONSTRAINT claim_id_unique IF NOT EXISTS FOR (c:Claim) REQUIRE c.claim_id IS UNIQUE;
CREATE CONSTRAINT trial_nct_unique IF NOT EXISTS FOR (t:ClinicalTrial) REQUIRE t.nct_id IS UNIQUE;
CREATE CONSTRAINT gene_symbol_exists IF NOT EXISTS FOR (g:Gene) REQUIRE g.symbol IS NOT NULL;
CREATE CONSTRAINT claim_text_exists IF NOT EXISTS FOR (c:Claim) REQUIRE c.claim_text IS NOT NULL;
