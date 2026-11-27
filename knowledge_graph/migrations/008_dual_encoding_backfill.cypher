// Migration 008: dual-encoding backfill for the 28 accepted claims (design issue #75, graph issues from #83)
// Idempotent - safe to re-run. ABOUT edges are intentionally kept, remove them in a later migration after validation.
// (1) Claim nodes get subject/subject_id/predicate/object/object_id properties from semantic_triple.
// (2) Cleanup: delete label-less, property-less nodes (10 strays left by the pre-fix bootstrap, commit bc6bf6c).
// (3) Merge Phenotype HP:0009732 into Disease MONDO:0003304 (same concept), keeping the Disease node and all edges,
//     the seeds recreate the Phenotype on every bootstrap, so this statement re-collapses it each run.
// (4) HAS_SUBJECT / HAS_OBJECT edges from each Claim, plus one coalesced typed edge per (subject, predicate, object)
//     carrying claim_ids and n_claims. Triples that violate edge_constraints.yaml, or that name a yeast gene with no
//     node, get no direct edge (and no HAS_SUBJECT/HAS_OBJECT for the missing yeast gene).

MATCH (n) WHERE size(labels(n)) = 0 AND size(keys(n)) = 0
DETACH DELETE n;

MATCH (p:Phenotype {hpo_id: 'HP:0009732'}), (d:Disease {mondo_id: 'MONDO:0003304'})
CALL apoc.refactor.mergeNodes([d, p], {properties: 'discard', mergeRels: true}) YIELD node
REMOVE node:Phenotype
RETURN count(node) AS merged;

MATCH (c:Claim {claim_id: 'C0001'})
SET c.subject = 'NF1', c.subject_id = 'NCBIGene:4763',
    c.predicate = 'ENCODES', c.object = 'neurofibromin', c.object_id = 'UniProtKB:P21359';

MATCH (c:Claim {claim_id: 'C0001'}), (s:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0001'}), (o:Protein {name: 'Neurofibromin'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0001'}), (s:Gene {symbol: 'NF1'}), (o:Protein {name: 'Neurofibromin'})
MERGE (s)-[r:ENCODES]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0002'})
SET c.subject = 'neurofibromin (NF1 GAP-related domain)', c.subject_id = 'UniProtKB:P21359',
    c.predicate = 'HOMOLOGOUS_TO', c.object = 'RASA1 (p120-RasGAP)', c.object_id = 'NCBIGene:5921';

MATCH (c:Claim {claim_id: 'C0002'}), (s:Protein {name: 'Neurofibromin'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0002'}), (o:Gene {symbol: 'RASA1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0002'}), (s:Protein {name: 'Neurofibromin'}), (o:Gene {symbol: 'RASA1'})
MERGE (s)-[r:HOMOLOGOUS_TO]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0003'})
SET c.subject = 'neurofibromin (NF1 GAP-related domain)', c.subject_id = 'UniProtKB:P21359',
    c.predicate = 'HOMOLOGOUS_TO', c.object = 'IRA1 (S. cerevisiae)', c.object_id = 'NCBIGene:852437';

MATCH (c:Claim {claim_id: 'C0003'}), (s:Protein {name: 'Neurofibromin'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0006'})
SET c.subject = 'EVI2B', c.subject_id = 'NCBIGene:2124',
    c.predicate = 'FOUND_IN', c.object = 'NF1', c.object_id = 'NCBIGene:4763';

MATCH (c:Claim {claim_id: 'C0006'}), (s:Gene {symbol: 'EVI2B'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0006'}), (o:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0006'}), (s:Gene {symbol: 'EVI2B'}), (o:Gene {symbol: 'NF1'})
MERGE (s)-[r:FOUND_IN]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0007'})
SET c.subject = 'EVI2A', c.subject_id = 'NCBIGene:2123',
    c.predicate = 'FOUND_IN', c.object = 'NF1', c.object_id = 'NCBIGene:4763';

MATCH (c:Claim {claim_id: 'C0007'}), (s:Gene {symbol: 'EVI2A'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0007'}), (o:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0007'}), (s:Gene {symbol: 'EVI2A'}), (o:Gene {symbol: 'NF1'})
MERGE (s)-[r:FOUND_IN]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0008'})
SET c.subject = 'OMG', c.subject_id = 'NCBIGene:4974',
    c.predicate = 'FOUND_IN', c.object = 'NF1', c.object_id = 'NCBIGene:4763';

MATCH (c:Claim {claim_id: 'C0008'}), (s:Gene {symbol: 'OMG'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0008'}), (o:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0008'}), (s:Gene {symbol: 'OMG'}), (o:Gene {symbol: 'NF1'})
MERGE (s)-[r:FOUND_IN]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0009'})
SET c.subject = 'selumetinib', c.subject_id = 'CHEBI:90227',
    c.predicate = 'TREATS', c.object = 'plexiform neurofibroma', c.object_id = 'MONDO:0003304';

MATCH (c:Claim {claim_id: 'C0009'}), (s:Drug {name: 'Selumetinib'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0009'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0009'}), (s:Drug {name: 'Selumetinib'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (s)-[r:TREATS]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0010'})
SET c.subject = 'selumetinib', c.subject_id = 'CHEBI:90227',
    c.predicate = 'TREATS', c.object = 'plexiform neurofibroma', c.object_id = 'MONDO:0003304';

MATCH (c:Claim {claim_id: 'C0010'}), (s:Drug {name: 'Selumetinib'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0010'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0010'}), (s:Drug {name: 'Selumetinib'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (s)-[r:TREATS]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0011'})
SET c.subject = 'selumetinib', c.subject_id = 'CHEBI:90227',
    c.predicate = 'TREATS', c.object = 'plexiform neurofibroma', c.object_id = 'MONDO:0003304';

MATCH (c:Claim {claim_id: 'C0011'}), (s:Drug {name: 'Selumetinib'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0011'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0011'}), (s:Drug {name: 'Selumetinib'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (s)-[r:TREATS]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0013'})
SET c.subject = 'selumetinib', c.subject_id = 'CHEBI:90227',
    c.predicate = 'TREATS', c.object = 'plexiform neurofibroma', c.object_id = 'MONDO:0003304';

MATCH (c:Claim {claim_id: 'C0013'}), (s:Drug {name: 'Selumetinib'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0013'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0013'}), (s:Drug {name: 'Selumetinib'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (s)-[r:TREATS]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0014'})
SET c.subject = 'selumetinib', c.subject_id = 'CHEBI:90227',
    c.predicate = 'TREATS', c.object = 'plexiform neurofibroma', c.object_id = 'MONDO:0003304';

MATCH (c:Claim {claim_id: 'C0014'}), (s:Drug {name: 'Selumetinib'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0014'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0014'}), (s:Drug {name: 'Selumetinib'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (s)-[r:TREATS]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0015'})
SET c.subject = 'selumetinib', c.subject_id = 'CHEBI:90227',
    c.predicate = 'TREATS', c.object = 'plexiform neurofibroma', c.object_id = 'MONDO:0003304';

MATCH (c:Claim {claim_id: 'C0015'}), (s:Drug {name: 'Selumetinib'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0015'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0015'}), (s:Drug {name: 'Selumetinib'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (s)-[r:TREATS]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0016'})
SET c.subject = 'selumetinib', c.subject_id = 'CHEBI:90227',
    c.predicate = 'TREATS', c.object = 'plexiform neurofibroma', c.object_id = 'MONDO:0003304';

MATCH (c:Claim {claim_id: 'C0016'}), (s:Drug {name: 'Selumetinib'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0016'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0016'}), (s:Drug {name: 'Selumetinib'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (s)-[r:TREATS]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0017'})
SET c.subject = 'selumetinib', c.subject_id = 'CHEBI:90227',
    c.predicate = 'TREATS', c.object = 'plexiform neurofibroma', c.object_id = 'MONDO:0003304';

MATCH (c:Claim {claim_id: 'C0017'}), (s:Drug {name: 'Selumetinib'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0017'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0017'}), (s:Drug {name: 'Selumetinib'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (s)-[r:TREATS]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0018'})
SET c.subject = 'selumetinib', c.subject_id = 'CHEBI:90227',
    c.predicate = 'TREATS', c.object = 'plexiform neurofibroma', c.object_id = 'MONDO:0003304';

MATCH (c:Claim {claim_id: 'C0018'}), (s:Drug {name: 'Selumetinib'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0018'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0018'}), (s:Drug {name: 'Selumetinib'}), (o:Disease {name: 'Plexiform neurofibroma'})
MERGE (s)-[r:TREATS]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0019'})
SET c.subject = 'neurofibromatosis type 1', c.subject_id = 'MONDO:0018975',
    c.predicate = 'ASSOCIATED_WITH', c.object = 'cafe-au-lait spot', c.object_id = 'HP:0000957';

MATCH (c:Claim {claim_id: 'C0019'}), (s:Disease {name: 'Neurofibromatosis type 1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0019'}), (o:Phenotype {hpo_id: 'HP:0000957'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0020'})
SET c.subject = 'NF1', c.subject_id = 'NCBIGene:4763',
    c.predicate = 'ASSOCIATED_WITH', c.object = 'neurofibromatosis type 1', c.object_id = 'MONDO:0018975';

MATCH (c:Claim {claim_id: 'C0020'}), (s:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0020'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0020'}), (s:Gene {symbol: 'NF1'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (s)-[r:ASSOCIATED_WITH]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0021'})
SET c.subject = 'neurofibromatosis type 1', c.subject_id = 'MONDO:0018975',
    c.predicate = 'ASSOCIATED_WITH', c.object = 'Lisch nodules', c.object_id = 'HP:0009737';

MATCH (c:Claim {claim_id: 'C0021'}), (s:Disease {name: 'Neurofibromatosis type 1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0021'}), (o:Phenotype {hpo_id: 'HP:0009737'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0023'})
SET c.subject = 'NF1', c.subject_id = 'NCBIGene:4763',
    c.predicate = 'ASSOCIATED_WITH', c.object = 'neurofibromatosis type 1', c.object_id = 'MONDO:0018975';

MATCH (c:Claim {claim_id: 'C0023'}), (s:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0023'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0023'}), (s:Gene {symbol: 'NF1'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (s)-[r:ASSOCIATED_WITH]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0024'})
SET c.subject = 'NF1', c.subject_id = 'NCBIGene:4763',
    c.predicate = 'ASSOCIATED_WITH', c.object = 'neurofibromatosis type 1', c.object_id = 'MONDO:0018975';

MATCH (c:Claim {claim_id: 'C0024'}), (s:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0024'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0024'}), (s:Gene {symbol: 'NF1'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (s)-[r:ASSOCIATED_WITH]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0025'})
SET c.subject = 'neurofibromatosis type 1', c.subject_id = 'MONDO:0018975',
    c.predicate = 'ASSOCIATED_WITH', c.object = 'NF1', c.object_id = 'NCBIGene:4763';

MATCH (c:Claim {claim_id: 'C0025'}), (s:Disease {name: 'Neurofibromatosis type 1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0025'}), (o:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0026'})
SET c.subject = 'SPRED1', c.subject_id = 'NCBIGene:161742',
    c.predicate = 'ASSOCIATED_WITH', c.object = 'neurofibromatosis type 1', c.object_id = 'MONDO:0018975';

MATCH (c:Claim {claim_id: 'C0026'}), (s:Gene {symbol: 'SPRED1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0026'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0026'}), (s:Gene {symbol: 'SPRED1'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (s)-[r:ASSOCIATED_WITH]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0027'})
SET c.subject = 'SPRED1', c.subject_id = 'NCBIGene:161742',
    c.predicate = 'CAUSES', c.object = 'Legius syndrome', c.object_id = 'MONDO:0012669';

MATCH (c:Claim {claim_id: 'C0027'}), (s:Gene {symbol: 'SPRED1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0027'}), (o:Disease {name: 'Legius syndrome'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0028'})
SET c.subject = 'NF1', c.subject_id = 'NCBIGene:4763',
    c.predicate = 'ASSOCIATED_WITH', c.object = 'neurofibromatosis type 1', c.object_id = 'MONDO:0018975';

MATCH (c:Claim {claim_id: 'C0028'}), (s:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0028'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0028'}), (s:Gene {symbol: 'NF1'}), (o:Disease {name: 'Neurofibromatosis type 1'})
MERGE (s)-[r:ASSOCIATED_WITH]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0029'})
SET c.subject = 'NF1', c.subject_id = 'NCBIGene:4763',
    c.predicate = 'ASSOCIATED_WITH', c.object = 'neurofibroma', c.object_id = 'MONDO:0016755';

MATCH (c:Claim {claim_id: 'C0029'}), (s:Gene {symbol: 'NF1'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0029'}), (o:Disease {name: 'Neurofibroma'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0029'}), (s:Gene {symbol: 'NF1'}), (o:Disease {name: 'Neurofibroma'})
MERGE (s)-[r:ASSOCIATED_WITH]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);

MATCH (c:Claim {claim_id: 'C0031'})
SET c.subject = 'neurofibromin (NF1 GAP-related domain)', c.subject_id = 'UniProtKB:P21359',
    c.predicate = 'ACTIVATES', c.object = 'IRA1 pathway (yeast RAS regulation)', c.object_id = 'NCBIGene:852437';

MATCH (c:Claim {claim_id: 'C0031'}), (s:Protein {name: 'Neurofibromin'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0032'})
SET c.subject = 'neurofibromin (NF1 GAP-related domain)', c.subject_id = 'UniProtKB:P21359',
    c.predicate = 'ACTIVATES', c.object = 'HRAS', c.object_id = 'NCBIGene:3265';

MATCH (c:Claim {claim_id: 'C0032'}), (s:Protein {name: 'Neurofibromin'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0032'}), (o:Gene {symbol: 'HRAS'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0035'})
SET c.subject = 'neurofibromin (NF1 GAP-related domain)', c.subject_id = 'UniProtKB:P21359',
    c.predicate = 'HOMOLOGOUS_TO', c.object = 'RASA1 (p120-RasGAP)', c.object_id = 'NCBIGene:5921';

MATCH (c:Claim {claim_id: 'C0035'}), (s:Protein {name: 'Neurofibromin'})
MERGE (c)-[:HAS_SUBJECT]->(s);

MATCH (c:Claim {claim_id: 'C0035'}), (o:Gene {symbol: 'RASA1'})
MERGE (c)-[:HAS_OBJECT]->(o);

MATCH (c:Claim {claim_id: 'C0035'}), (s:Protein {name: 'Neurofibromin'}), (o:Gene {symbol: 'RASA1'})
MERGE (s)-[r:HOMOLOGOUS_TO]->(o)
SET r.claim_ids = CASE WHEN c.claim_id IN coalesce(r.claim_ids, []) THEN r.claim_ids ELSE coalesce(r.claim_ids, []) + c.claim_id END
WITH r
SET r.n_claims = size(r.claim_ids);
