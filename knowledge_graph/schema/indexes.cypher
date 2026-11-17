// NF1-Swarm Neo4j Indexes

CREATE FULLTEXT INDEX claim_text_search IF NOT EXISTS FOR (c:Claim) ON EACH [c.claim_text];
CREATE FULLTEXT INDEX publication_title_search IF NOT EXISTS FOR (p:Publication) ON EACH [p.title];
CREATE INDEX claim_strength_idx IF NOT EXISTS FOR (c:Claim) ON (c.evidence_strength);
CREATE INDEX claim_status_idx IF NOT EXISTS FOR (c:Claim) ON (c.status);
CREATE INDEX claim_type_idx IF NOT EXISTS FOR (c:Claim) ON (c.claim_type);
CREATE INDEX gene_hgnc_idx IF NOT EXISTS FOR (g:Gene) ON (g.hgnc_id);
CREATE INDEX disease_omim_idx IF NOT EXISTS FOR (d:Disease) ON (d.omim_id);
CREATE INDEX phenotype_hpo_idx IF NOT EXISTS FOR (p:Phenotype) ON (p.hpo_id);
