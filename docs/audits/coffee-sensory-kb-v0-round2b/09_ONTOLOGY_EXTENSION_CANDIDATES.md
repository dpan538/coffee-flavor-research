# Round 2B ontology-extension candidates

Date: 2026-08-24

Status: feedback queue only; no canonical promotion

## Governance boundary

Corpus frequency can reveal language that the canonical ontology does not
represent precisely. It cannot establish sensory validity. Round 2B therefore
records an 11-item feedback queue in the corpus layer, copies exact frozen
frequency receipts into a separate versioned statistic run, and points to the
nearest existing canonical concepts through 14 adjudicated comparison links.

Every item has `evidence_status=REQUIRES_COFFEE_SENSORY_EVIDENCE`. Ten are
`OPEN`; `honey melon` is `DEFERRED` because the compound interpretation is not
yet clear. No item creates or modifies a `kb.concept`, lexicalization, relation,
source scheme, or promotion event.

Country diversity is unavailable because the source does not assert roaster
country. Publisher diversity means distinct Firstbloom publisher identities,
not independently licensed sources or geographic diversity.

## Candidate inventory

| Observed expression | Frequency | Publisher diversity | Nearest existing concept(s)                 | Information lost                                                                                         | Recommended action                                                                                       |
| ------------------- | --------: | ------------------: | ------------------------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| stone fruit         |        26 |                  22 | `category.orchard_fruit`                    | The existing parent does not preserve the repeated stone-fruit grouping as its own language abstraction. | Evaluate a category or controlled lexical abstraction; never a universal sensory axis.                   |
| watermelon          |        15 |                  13 | `category.fruit`                            | The generic fruit category loses the explicit reference.                                                 | Review as a candidate attribute against coffee-specific sensory evidence.                                |
| clementine          |        14 |                  14 | `sensory.orange`; `category.citrus`         | Orange/citrus preserves the family but not the narrower reference.                                       | Decide whether independent evidence supports a narrower attribute or a governed normalization to orange. |
| pecan               |        13 |                  12 | `category.nut_seed`                         | The broad category loses the explicit nut reference.                                                     | Review as a candidate attribute against coffee-specific sensory evidence.                                |
| passion fruit       |         6 |                   6 | `category.tropical_fruit`; `category.fruit` | The broad categories lose the explicit tropical-fruit reference.                                         | Review as a candidate attribute against coffee-specific sensory evidence.                                |
| cashew              |         5 |                   4 | `category.nut_seed`                         | The broad category loses the explicit nut reference.                                                     | Review conservatively and retain the limited pilot diversity in the evidence record.                     |
| gooseberry          |         4 |                   4 | `category.berry`; `category.fruit`          | The broad categories lose the explicit berry reference.                                                  | Review the attribute and adjudicate canonical grouping separately from source schemes.                   |
| lilac               |         4 |                   3 | `category.floral`                           | The broad category loses the explicit floral reference.                                                  | Review as a candidate attribute against coffee-specific sensory evidence.                                |
| macadamia           |         3 |                   3 | `category.nut_seed`                         | The broad category loses the reference; a separate macadamia-nut surface is also observed.               | If admitted later, govern the two surfaces lexically rather than creating duplicate concepts.            |
| honey melon         |         2 |                   2 | `category.fruit`                            | The surface may be a compound rather than a honey component.                                             | Defer pending semantic review and external coffee-specific evidence.                                     |
| rosemary            |         2 |                   2 | `category.green_herbal`                     | The broad category loses the explicit herbal reference.                                                  | Review as a candidate attribute and distinguish it carefully from rose.                                  |

The shortlist policy requires at least two retained occurrences and two
publisher identities, adjudicated information loss, and an existing nearest
concept comparison. These thresholds are triage rules, not ontology-admission
criteria.

The queue is closed against the frozen migration-016 audit and adjudicated
qrels. `persimmon` was not present in that frozen review evidence and is
therefore excluded despite appearing in the corpus; adding it afterward would
be post-hoc ontology feedback selection. A future review may reconsider it
through a newly frozen audit rather than mutating this receipt.

Each retained candidate is linked to its frozen audit case, and each of the 14
nearest-concept comparisons retains the exact adjudicated relevance-judgment
row that supports it. Frequency, semantic comparison, and curation state are
therefore traceable without treating any link as a canonical relation.

## Required next curation step

Any future promotion requires a separate forward-only ontology round that:

1. checks coffee-specific formal or peer-reviewed sensory evidence;
2. records source version, rights status, locator, and concept-level support;
3. distinguishes a sensory attribute from a category, composite reference,
   qualifier, or lexical-only observation;
4. evaluates semantic overlap with the existing canonical core and schemes;
5. adds an explicit governed promotion event only after approval.

Until then, all 11 remain corpus observations. Their frequency and publisher
diversity do not make them sensory truths. The Round 2A canonical boundary is
unchanged at 130 concepts, 110 stored relations, and 134 canonical
lexicalizations.

```text
ONTOLOGY_EXTENSION_CANDIDATE_COUNT=11
ONTOLOGY_EXTENSION_OPEN_COUNT=10
ONTOLOGY_EXTENSION_DEFERRED_COUNT=1
ONTOLOGY_EXTENSION_NEAREST_LINK_COUNT=14
AUTOMATIC_ONTOLOGY_PROMOTION_COUNT=0
PGVECTOR_REQUIRED=false
```
