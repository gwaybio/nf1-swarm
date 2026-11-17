// Traverse from NF1 gene to downstream entities
MATCH path = (nf1:Gene {symbol: 'NF1'})-[:ENCODES]->(p:Protein)-[:INHIBITS|ACTIVATES*1..3]->(downstream)
RETURN path LIMIT 25;
