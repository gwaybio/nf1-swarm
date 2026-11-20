# CURIE Registry for NF1-Swarm Grounding

Verified via SRI Node Normalizer (nodenormalization-sri.renci.org).
Use these as the canonical CURIEs when grounding claims. Always re-verify
against the Node Normalizer if more than a few weeks have passed.

## Genes
| Entity | CURIE | HGNC | Notes |
|--------|-------|------|-------|
| NF1 (human) | NCBIGene:4763 | HGNC:7765 | UniProtKB:P21359 normalizes here |
| SPRED1 | NCBIGene:161742 | HGNC:20249 | Legius syndrome gene |
| HRAS | NCBIGene:3265 | HGNC:5173 | |
| KRAS | NCBIGene:3845 | HGNC:6407 | |
| BRAF | NCBIGene:673 | HGNC:1097 | |
| MAP2K1 (MEK1) | NCBIGene:5604 | HGNC:6840 | MEK inhibitor target |
| MTOR | NCBIGene:2475 | HGNC:3942 | |
| RASA1 (p120GAP) | NCBIGene:5921 | HGNC:9871 | UniProtKB:P20936 |
| IRA1 (yeast) | NCBIGene:852437 | SGD:S000000344 | UniProtKB:P18963 |
| IRA2 (yeast) | NCBIGene:854073 | SGD | |
| RAS2 (yeast) | NCBIGene:855625 | SGD | |
| OMG | NCBIGene:4974 | HGNC:8135 | Embedded in NF1 intron 27b |
| EVI2A | NCBIGene:2123 | HGNC:3499 | Embedded in NF1 intron 27b |
| EVI2B | NCBIGene:2124 | HGNC:3500 | Embedded in NF1 intron 27b |

## Proteins
| Entity | CURIE | Notes |
|--------|-------|-------|
| Neurofibromin | UniProtKB:P21359 | Normalizes to NCBIGene:4763 in SRI; use UniProtKB when protein-level specificity matters |

## Drugs
| Entity | CURIE | Notes |
|--------|-------|-------|
| Selumetinib | CHEBI:90227 | MEK1/2 inhibitor; FDA-approved for NF1 PN |
| Mirdametinib | CHEBI:88249 | MEK1/2 inhibitor |
| Trametinib | CHEBI:75998 | MEK1/2 inhibitor |
| Binimetinib | CHEBI:145371 | MEK1/2 inhibitor |
| NFX-179 (CT-179) | CHEBI:234076 | Topical MEK inhibitor |
| Carboplatin | CHEBI:31355 | Platinum chemotherapy |

## Diseases
| Entity | CURIE | Notes |
|--------|-------|-------|
| Neurofibromatosis type 1 | MONDO:0018975 | NOT MONDO:0009981 (obsolete/narrower) |
| Plexiform neurofibroma | MONDO:0003304 | |
| Neurofibroma | MONDO:0016755 | General (cutaneous + other) |
| Optic pathway glioma | MONDO:0016167 | |
| Low-grade glioma | MONDO:0021637 | |
| MPNST | MONDO:0017827 | Malignant peripheral nerve sheath tumor |
| Legius syndrome | MONDO:0012669 | SPRED1 mutations |
| CMMRD | MONDO:0031219 | Constitutional mismatch repair deficiency |
| Myeloproliferative neoplasm | MONDO:0020076 | |

## Phenotypes (HPO)
| Entity | CURIE |
|--------|-------|
| Cafe-au-lait spot | HP:0000957 |
| Freckling | HP:0001480 |
| Axillary freckling | HP:0000997 |
| Inguinal freckling | HP:0030052 |
| Lisch nodules | HP:0009737 |
| Sphenoid wing dysplasia | HP:6001124 |
| Muscle weakness | HP:0001324 |
| Autosomal dominant | HP:0000006 |

## Name Resolver taxon filtering

The SRI Name Resolver returns all species. For human genes, filter by
`NCBITaxon:9606` in the `taxa` field. The top hit for "NF1" is horse
(NCBITaxon:9798), not human — always check taxon.

For yeast genes (IRA1, IRA2, RAS2), filter by `NCBITaxon:559292`
(S. cerevisiae S288C) or `NCBITaxon:4932`.
