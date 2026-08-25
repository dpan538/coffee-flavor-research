# Relationship coverage

`audit.v_round3f_relationship_coverage` reports governed instance counts. A
provenance rate means the registry can reach a source, snapshot, question,
review or documented project-authored boundary; it does not rate evidential
strength.

| Domain                 |  Types |  Instances | Source/provenance-unit count | Unresolved |
| ---------------------- | -----: | ---------: | ---------------------------: | ---------: |
| ASSOCIATION_RANGE      |      5 |         18 |                           18 |          0 |
| CANONICAL_ONTOLOGY     |      6 |        110 |                            4 |          0 |
| EVIDENCE               |      4 |      6,696 |                           66 |          0 |
| GOVERNANCE             |      5 |         19 |                            5 |          0 |
| LEXICAL                |      5 |      6,021 |                          220 |          0 |
| QUESTION               |      4 |         48 |                            5 |          0 |
| SOURCE_LOCAL_EMPIRICAL |      5 |      4,600 |                            1 |          1 |
| **Total**              | **34** | **17,512** |                            — |      **1** |

`RELATION_WITH_PROVENANCE_RATE=1.0000`. Zero-instance types are excluded from
the rate rather than called 100% covered. `co_selected_with` is the sole
unresolved registered type because no admitted selection protocol or instance
exists.

Higher counts do not imply better quality. The 4,600 co-occurrence measurements
remain source-local language observations; they are not sensory similarity.
