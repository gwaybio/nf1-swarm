"""
RTX-KG2 client for nf1-swarm.

RTX-KG2 integrates 73+ biomedical knowledge sources (SemMedDB, UniProt,
DrugBank, ChEMBL, OMIM, Orphanet, HPO, Reactome, GO, DisGeNET, GTEx, STRING...)
into a Biolink-compliant graph queryable via TRAPI.

API: https://kg2cploverdb.transltr.io/query
Docs: https://ncatstranslator.github.io/TranslatorTechnicalDocumentation/

Used by:
  - Otto: entity grounding (name → CURIE)
  - Otto: edge existence check (does this relationship already exist?)
  - Stan: corroborating source count for confidence scoring
"""
import json
import requests
from dataclasses import dataclass, field
from typing import Optional


TRAPI_ENDPOINT = "https://kg2cploverdb.transltr.io/query"
ARAX_ENDPOINT = "https://arax.ncats.io/api/arax/v1.4/query"


@dataclass
class TripleResult:
    subject_id: str
    subject_name: str
    predicate: str
    object_id: str
    object_name: str
    sources: list[str] = field(default_factory=list)
    pmids: list[str] = field(default_factory=list)
    n_sources: int = 0


def _trapi_query(query_graph: dict, endpoint: str = TRAPI_ENDPOINT,
                 timeout: int = 30) -> dict:
    payload = {"message": {"query_graph": query_graph}}
    resp = requests.post(endpoint, json=payload, timeout=timeout,
                         headers={"accept": "application/json",
                                  "Content-Type": "application/json"})
    resp.raise_for_status()
    return resp.json()


def ground_entity(name: str, categories: list[str] = None,
                  timeout: int = 30) -> list[dict]:
    """
    Look up an entity name in RTX-KG2 and return matching nodes with CURIEs.

    Args:
        name: Entity name, e.g. "neurofibromin", "selumetinib", "cafe-au-lait spot"
        categories: Biolink categories to filter by, e.g. ["biolink:Protein"]

    Returns:
        List of dicts with keys: id, name, category, synonyms

    Example:
        nodes = ground_entity("NF1", ["biolink:Gene"])
        # [{"id": "NCBIGene:4763", "name": "NF1", "category": "biolink:Gene", ...}]
    """
    # Use the ARAX entity endpoint for name->CURIE lookup
    try:
        resp = requests.get(
            f"{ARAX_ENDPOINT.replace('/query', '')}/entity",
            params={"q": name, "limit": 10},
            timeout=timeout,
            headers={"accept": "application/json"},
        )
        resp.raise_for_status()
        results = resp.json()
        nodes = []
        for item in results:
            if categories and not any(c in item.get("category", []) for c in categories):
                continue
            nodes.append({
                "id": item.get("id", ""),
                "name": item.get("name", name),
                "category": item.get("category", []),
                "synonyms": item.get("synonyms", []),
            })
        return nodes
    except Exception as e:
        return [{"id": "", "name": name, "error": str(e)}]


def check_edge_exists(subject_curie: str, object_curie: str,
                      predicates: list[str] = None,
                      timeout: int = 30) -> list[TripleResult]:
    """
    Check if a relationship between two entities already exists in RTX-KG2.

    Args:
        subject_curie: e.g. "CHEMBL.COMPOUND:CHEMBL1614701"
        object_curie: e.g. "HP:0009732"
        predicates: Biolink predicates to filter, e.g. ["biolink:treats"]

    Returns:
        List of TripleResult objects with source counts and PMIDs.

    Use this BEFORE creating a new Claim — if RTX-KG2 already has this edge
    with 15 sources, that strengthens the claim AND should be reflected in
    supporting_dois and fed to Stan for confidence scoring.
    """
    edge_spec = {"subject": "n00", "object": "n01"}
    if predicates:
        edge_spec["predicates"] = predicates

    query_graph = {
        "nodes": {
            "n00": {"ids": [subject_curie]},
            "n01": {"ids": [object_curie]},
        },
        "edges": {"e00": edge_spec},
    }
    try:
        result = _trapi_query(query_graph, timeout=timeout)
        kg = result.get("message", {}).get("knowledge_graph", {})
        edges = kg.get("edges", {})
        nodes = kg.get("nodes", {})

        triples = []
        for edge_id, edge in edges.items():
            sources = [s.get("resource_id", "") for s in edge.get("sources", [])]
            # Extract PMIDs from attributes
            pmids = []
            for attr in edge.get("attributes", []):
                if "publications" in attr.get("attribute_type_id", ""):
                    pubs = attr.get("value", [])
                    if isinstance(pubs, list):
                        pmids.extend(p.replace("PMID:", "") for p in pubs if "PMID" in p)

            subj_node = nodes.get(edge.get("subject", ""), {})
            obj_node = nodes.get(edge.get("object", ""), {})
            triples.append(TripleResult(
                subject_id=edge.get("subject", ""),
                subject_name=subj_node.get("name", ""),
                predicate=edge.get("predicate", ""),
                object_id=edge.get("object", ""),
                object_name=obj_node.get("name", ""),
                sources=sources,
                pmids=pmids,
                n_sources=len(sources),
            ))
        return triples
    except Exception:
        return []


def get_nf1_edges(predicate: str = None, timeout: int = 45) -> list[TripleResult]:
    """
    Get all edges involving the NF1 gene (NCBIGene:4763) in RTX-KG2.

    Useful for Kim to see what relationships already exist before creating new nodes,
    and for Stan to build a baseline of known NF1 biology.
    """
    edge_spec = {"subject": "n00", "object": "n01"}
    if predicate:
        edge_spec["predicates"] = [predicate]

    query_graph = {
        "nodes": {
            "n00": {"ids": ["NCBIGene:4763"], "categories": ["biolink:Gene"]},
            "n01": {},
        },
        "edges": {"e00": edge_spec},
    }
    try:
        result = _trapi_query(query_graph, timeout=timeout)
        kg = result.get("message", {}).get("knowledge_graph", {})
        edges = kg.get("edges", {})
        nodes = kg.get("nodes", {})

        return [
            TripleResult(
                subject_id=e.get("subject", ""),
                subject_name=nodes.get(e.get("subject", ""), {}).get("name", ""),
                predicate=e.get("predicate", ""),
                object_id=e.get("object", ""),
                object_name=nodes.get(e.get("object", ""), {}).get("name", ""),
                n_sources=len(e.get("sources", [])),
            )
            for e in edges.values()
        ]
    except Exception:
        return []
