// Atomic counters — idempotent, safe to re-run
// claim_id: advances only on acceptance (C#### namespace)
// rejection_id: advances only on rejection (R#### namespace)
//
// Initial values are set to the highest ID already in use so a re-run
// on an existing database never reuses an ID.
MERGE (c:Counter {name: 'claim_id'})
ON CREATE SET c.value = 0;

MERGE (c:Counter {name: 'rejection_id'})
ON CREATE SET c.value = 0;
