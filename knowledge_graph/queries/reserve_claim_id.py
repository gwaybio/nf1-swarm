"""
Helper: atomically reserve the next claim ID from Neo4j.
Agents MUST use this — never manually assign claim IDs.

Usage:
    from knowledge_graph.queries.reserve_claim_id import next_claim_id
    with driver.session() as session:
        cid = next_claim_id(session)   # e.g. "C0042"
"""
from neo4j import Session


def next_claim_id(session: Session) -> str:
    """Atomically increment the counter and return the next claim ID."""
    result = session.run("""
        MATCH (c:Counter {name: 'claim_id'})
        CALL apoc.lock.nodes([c])
        SET c.value = c.value + 1
        RETURN 'C' + right('0000' + toString(c.value), 4) AS claim_id
    """)
    return result.single()["claim_id"]
