// Find all accepted claims ordered by evidence strength
MATCH (c:Claim {status: 'accepted'})
RETURN c.claim_id, c.claim_text, c.evidence_strength, c.claim_type
ORDER BY c.evidence_strength DESC;
