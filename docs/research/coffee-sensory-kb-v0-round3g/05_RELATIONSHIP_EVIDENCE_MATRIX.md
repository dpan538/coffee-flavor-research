# Relationship evidence matrix

The authoritative 20-row matrix is
`db/data/round3g/relationship_evidence_claims.tsv` and
`evidence.relationship_evidence_claim`.

| Direction      | Count | Main interpretation                                                                                                                     |
| -------------- | ----: | --------------------------------------------------------------------------------------------------------------------------------------- |
| `SUPPORTS`     |     1 | Smoky Aroma supplies threshold-qualified source-local evidence for the exact smoke membership                                           |
| `CHALLENGES`   |     3 | smoky versus roasty, sour versus broader acidity wording, and body versus astringent/other texture terms are separately operationalized |
| `MIXED`        |     1 | direct Sweet ratings are relevant but do not associate caramel or honey                                                                 |
| `INSUFFICIENT` |    15 | source inventory, question context and lexical title evidence do not meet relationship, bilingual or user-validation requirements       |

Every claim has a target type/key, source family/key/snapshot, basis,
direction, scope, locator, method, frozen threshold configuration, support and
document counts, source diversity, review status and limitation. `CHALLENGES`
and `MIXED` rows are deletion-protected. No claim uses an embedding, LLM
similarity, pooled global score or general sensory intuition.

The Liberica family is method-specific and source-local. The Wiktionary family
records exact title/revision attestation only. Missing titles are explicitly
`INSUFFICIENT`, never negative association evidence.
