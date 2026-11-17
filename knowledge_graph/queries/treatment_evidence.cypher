// Find all treatments and their supporting claims
MATCH (d:Drug)-[:TREATS]->(target)
OPTIONAL MATCH (c:Claim {claim_type: 'drug_response', status: 'accepted'})-[:EXTRACTED_FROM]->(pub:Publication)
RETURN d.name, target, c.claim_text, c.evidence_strength, pub.pmid
ORDER BY c.evidence_strength DESC;
