# Relationship constraint model

Status: permanent architecture source of truth from Round 3F.

`TEXT_FIRST_LEXICAL_CANDIDATE_IS_INTENTIONAL=true`

This model organizes existing evidence and candidates without requiring every
coffee expression to become a canonical ontology node. An association range is
a bounded, overlapping research grouping of expressions, concepts or
references that are frequently, relatively or contextually associated. It is
not an objective coffee-flavor cluster, universal dimension, ontology category,
latent biological truth, probability or final product section.

## Entity path and domain boundary

```text
raw phrase
  -> preserved/normalized expression
  -> text-first lexical mapping candidate
  -> zero, one, or multiple association-range memberships

canonical ontology assertions remain a separate reviewed path
```

The range path never requires `kb.concept`. Membership does not imply synonymy,
IS_A hierarchy, broader/narrower identity, sensory-neighbour status, fixed
distance, ingredient identity, causality, objective probability, universal
cross-cultural equivalence or transitive association. Source absence is not a
negative relation.

## Relationship identity matrix

Abbreviations: `0..n` means zero-to-many; `D` directional; `S` symmetric; `NT`
non-transitive; `NE` non-exclusive. `BT-only` permits same-type canonical
closure only for the already governed `broader_than` relation.

| RELATIONSHIP_KEY                          | RELATIONSHIP_DOMAIN    | SUBJECT_ENTITY_TYPE               | PREDICATE                        | OBJECT_ENTITY_TYPE       | CARDINALITY | DIRECTIONALITY | SYMMETRY       | TRANSITIVITY | EXCLUSIVITY                 |
| ----------------------------------------- | ---------------------- | --------------------------------- | -------------------------------- | ------------------------ | ----------- | -------------- | -------------- | ------------ | --------------------------- |
| `lexical.preferred-lexicalization`        | LEXICAL                | lexical expression                | preferred lexicalization of      | concept                  | 0..n        | D              | no             | NT           | mapping key governs         |
| `lexical.orthographic-variant`            | LEXICAL                | lexical expression                | orthographic variant of          | concept                  | 0..n        | D              | no             | NT           | NE                          |
| `lexical.language-variant`                | LEXICAL                | text expression                   | language-variant candidate of    | text expression          | 0..n        | D              | no             | NT           | NE                          |
| `lexical.source-local-expression`         | LEXICAL                | source record                     | contains source-local expression | preserved expression     | 0..n        | D              | no             | NT           | NE                          |
| `lexical.candidate-mapping`               | LEXICAL                | normalized expression             | candidate lexical mapping        | text mapping             | 0..n        | D              | no             | NT           | NE                          |
| `canonical.broader-than`                  | CANONICAL_ONTOLOGY     | concept                           | `broader_than`                   | concept                  | 0..n        | D              | no             | BT-only      | NE                          |
| `canonical.sensory-neighbour`             | CANONICAL_ONTOLOGY     | concept                           | `sensory_neighbour`              | concept                  | 0..n        | undirected     | S              | NT           | NE                          |
| `canonical.composite-has-component`       | CANONICAL_ONTOLOGY     | concept                           | `composite_has_component`        | concept                  | 0..n        | D              | no             | NT           | NE                          |
| `canonical.consumer-reference-for`        | CANONICAL_ONTOLOGY     | concept                           | `consumer_reference_for`         | concept                  | 0..n        | D              | no             | NT           | NE                          |
| `canonical.modifies`                      | CANONICAL_ONTOLOGY     | concept                           | `modifies`                       | concept                  | 0..n        | D              | no             | NT           | NE                          |
| `canonical.contrasts-with`                | CANONICAL_ONTOLOGY     | concept                           | `contrasts_with`                 | concept                  | 0..n        | undirected     | S              | NT           | NE                          |
| `empirical.co-occurs-with`                | SOURCE_LOCAL_EMPIRICAL | normalized expression             | co-occurs with                   | normalized expression    | 0..n        | undirected     | S              | NT           | NE                          |
| `empirical.co-selected-with`              | SOURCE_LOCAL_EMPIRICAL | source-local response             | co-selected with                 | source-local response    | 0..n        | undirected     | S              | NT           | NE                          |
| `empirical.same-source-record`            | SOURCE_LOCAL_EMPIRICAL | source-local expression           | appears in same source record    | source-local expression  | 0..n        | undirected     | S              | NT           | NE                          |
| `empirical.source-defined-grouping`       | SOURCE_LOCAL_EMPIRICAL | source-local expression           | source-defined grouping          | source-local grouping    | 0..n        | D              | no             | NT           | NE                          |
| `empirical.source-local-association`      | SOURCE_LOCAL_EMPIRICAL | source-local expression           | source-local association         | source-local expression  | 0..n        | method-defined | method-defined | NT           | NE                          |
| `range.anchor`                            | ASSOCIATION_RANGE      | expression/concept/text candidate | anchor of range                  | association range        | 0..n        | D              | no             | NT           | NE                          |
| `range.frequent-associate`                | ASSOCIATION_RANGE      | expression/concept/text candidate | frequent associate in range      | association range        | 0..n        | D              | no             | NT           | NE                          |
| `range.contextual-associate`              | ASSOCIATION_RANGE      | expression/concept/text candidate | contextual associate in range    | association range        | 0..n        | D              | no             | NT           | NE                          |
| `range.peripheral-candidate`              | ASSOCIATION_RANGE      | expression/concept/text candidate | peripheral candidate in range    | association range        | 0..n        | D              | no             | NT           | NE                          |
| `range.ambiguous`                         | ASSOCIATION_RANGE      | expression/concept/text candidate | ambiguous in range               | association range        | 0..n        | D              | no             | NT           | NE                          |
| `question.targets-range`                  | QUESTION               | logical question                  | targets range                    | association range        | 0..n        | D              | no             | NT           | NE                          |
| `question.option-indicates-range`         | QUESTION               | question option                   | indicates range                  | association range        | 0..n        | D              | no             | NT           | NE                          |
| `question.eligible-for-context`           | QUESTION               | logical question                  | eligible for context             | context hypothesis       | 0..n        | D              | no             | NT           | NE                          |
| `question.distinguishes-ranges`           | QUESTION               | logical question                  | distinguishes ranges             | association range        | 0..n        | D              | no             | NT           | NE                          |
| `evidence.supported-by-source`            | EVIDENCE               | assertion                         | supported by source              | versioned source/dataset | 0..n        | D              | no             | NT           | NE                          |
| `evidence.derived-from-snapshot`          | EVIDENCE               | derived record                    | derived from snapshot            | immutable snapshot       | n..1        | D              | no             | NT           | one owning snapshot         |
| `evidence.measured-by-method`             | EVIDENCE               | quantitative observation          | measured by method               | method/configuration     | n..1        | D              | no             | NT           | one declared method per row |
| `evidence.reviewed-under-protocol`        | EVIDENCE               | candidate/assertion               | reviewed under protocol          | review/protocol          | 0..n        | D              | no             | NT           | NE                          |
| `governance.candidate-promoted-by-review` | GOVERNANCE             | candidate                         | promoted by review               | canonical assertion      | 0..n        | D              | no             | NT           | explicit target             |
| `governance.superseded-by`                | GOVERNANCE             | historical assertion              | superseded by                    | replacement assertion    | 0..1        | D              | no             | NT           | one replacement             |
| `governance.rejected-by`                  | GOVERNANCE             | candidate                         | rejected by                      | review decision          | 0..n        | D              | no             | NT           | NE                          |
| `governance.requires-evidence`            | GOVERNANCE             | candidate/assertion               | requires evidence                | evidence gate            | 0..n        | D              | no             | NT           | NE                          |
| `governance.forbidden-from-promotion`     | GOVERNANCE             | source-local/candidate record     | forbidden from promotion         | canonical assertion      | 0..n        | D              | no             | NT           | NE                          |

## Relationship governance matrix

Every row below supplies the remaining required fields. `DB+CI` means the
database representation is checked by named constraints/triggers and the
Round 3F suite; `policy` means a conceptual boundary intentionally remains a
curation or documented rule.

| RELATIONSHIP_KEY                          | EVIDENCE_REQUIREMENT                     | PROVENANCE_PATH                                | LIFECYCLE                   | COMPUTATIONAL_ROLE         | ALLOWED_INFERENCE               | FORBIDDEN_INFERENCE                      | DATABASE_REPRESENTATION            | VALIDATION_METHOD   | NEGATIVE_TEST                                  |
| ----------------------------------------- | ---------------------------------------- | ---------------------------------------------- | --------------------------- | -------------------------- | ------------------------------- | ---------------------------------------- | ---------------------------------- | ------------------- | ---------------------------------------------- |
| `lexical.preferred-lexicalization`        | reviewed canonical lexical evidence      | lexicalization -> support/source when external | assertion lifecycle         | exact retrieval            | preferred project label only    | synonymy across languages                | `kb.lexicalization`                | DB+CI               | historical lexical tests                       |
| `lexical.orthographic-variant`            | explicit reviewed variant                | lexicalization -> support/source               | assertion lifecycle         | variant retrieval          | reviewed spelling/wording route | bilingual equivalence                    | `kb.lexicalization`                | DB+CI               | historical lexical tests                       |
| `lexical.language-variant`                | independent bilingual review             | source text -> review receipt                  | CANDIDATE until reviewed    | research only              | preserve candidate comparison   | literal translation = equivalence        | text-first records                 | policy+CI           | `literal_translation_to_bilingual_equivalence` |
| `lexical.source-local-expression`         | observed record                          | occurrence -> document -> snapshot/source      | snapshot-local              | corpus inventory           | occurrence at source            | canonical meaning                        | occurrence tables                  | FK/audit            | source-boundary tests                          |
| `lexical.candidate-mapping`               | evidence key and ambiguity note          | candidate -> occurrence/source                 | candidate lifecycle         | review queue               | possible textual interpretation | mandatory concept or automatic promotion | `corpus.lexical_mapping_candidate` | DB+CI               | `unresolved_candidate_forced_to_concept`       |
| `canonical.broader-than`                  | canonical support/review                 | relation -> relation support                   | canonical lifecycle         | typed graph                | same-type governed closure      | range co-membership hierarchy            | `kb.concept_relation`              | cycle/support gates | `range_copresence_to_hierarchy`                |
| `canonical.sensory-neighbour`             | explicit canonical support               | relation -> relation support                   | canonical lifecycle         | one-hop graph              | stored symmetric adjacency      | co-occurrence or range = neighbour       | `kb.concept_relation`              | typed trigger+CI    | `cooccurrence_to_sensory_neighbour`            |
| `canonical.composite-has-component`       | explicit component evidence              | relation -> relation support                   | canonical lifecycle         | one-hop composition        | named component only            | decomposition of arbitrary phrase        | `kb.concept_relation`              | typed trigger       | canonical negative suite                       |
| `canonical.consumer-reference-for`        | explicit reviewed communication relation | relation -> support                            | canonical lifecycle         | reference retrieval        | stored reference relation       | synonym or ingredient identity           | `kb.concept_relation`              | typed trigger       | canonical negative suite                       |
| `canonical.modifies`                      | explicit context evidence                | relation -> support                            | canonical lifecycle         | scoped graph               | stored modifier relation        | inferred decomposition                   | `kb.concept_relation`              | typed trigger       | canonical negative suite                       |
| `canonical.contrasts-with`                | explicit negative/contrast evidence      | relation -> support                            | canonical lifecycle         | contrast retrieval         | stored symmetric contrast       | absence = contrast                       | `kb.concept_relation`              | typed trigger+CI    | `source_absence_to_negative_relation`          |
| `empirical.co-occurs-with`                | reproducible snapshot statistic          | pair -> run -> corpus/dataset                  | immutable run               | source-local statistic     | pair co-occurrence only         | sensory similarity/validity              | pair-measurement tables            | method bounds+CI    | `cooccurrence_to_sensory_neighbour`            |
| `empirical.co-selected-with`              | observed selection protocol              | pair -> response/protocol                      | no admitted instance        | future audit only          | source-local co-selection       | cross-source or sensory truth            | intentionally absent               | documented boundary | `NOT_APPLICABLE`                               |
| `empirical.same-source-record`            | shared preserved record                  | expression -> record -> snapshot               | derived snapshot            | possible future derivation | common record only              | similarity or causality                  | not materialized in 3F             | audit boundary      | `NOT_APPLICABLE`                               |
| `empirical.source-defined-grouping`       | source's formal grouping                 | measurement -> source snapshot                 | source-local                | source structure           | source-local membership         | independent project truth                | method ledger                      | DB+CI               | source-scope gate                              |
| `empirical.source-local-association`      | source-local measurement                 | measurement -> snapshot/config                 | source-local                | research comparison        | result under named method       | transfer without stability evidence      | method ledger                      | DB+policy           | source-scope gate                              |
| `range.anchor`                            | allowed basis + evidence key/path        | membership -> governed question/source/review  | range-local                 | research navigation        | anchor under named evidence     | synonym/hierarchy/probability            | membership role                    | DB+CI               | range non-inference cases                      |
| `range.frequent-associate`                | reproducible frequency plus threshold    | membership -> measurement/run                  | range-local                 | research prioritization    | frequent under named corpus     | validity or promotion                    | membership + measurement           | DB+CI               | frequency cases                                |
| `range.contextual-associate`              | explicit contextual evidence             | membership -> evidence path                    | range-local                 | research grouping          | association under context       | universal association                    | membership                         | DB+CI               | range non-inference cases                      |
| `range.peripheral-candidate`              | weak but admissible named evidence       | membership -> evidence path                    | CANDIDATE                   | review queue               | peripheral candidacy            | padded completeness                      | membership                         | DB+curation         | evidence-required case                         |
| `range.ambiguous`                         | explicit ambiguity and evidence          | membership -> evidence path                    | CANDIDATE                   | preserve uncertainty       | ambiguous placement             | forced exclusive meaning                 | membership                         | DB+CI               | `exclusive_range_membership`                   |
| `question.targets-range`                  | governed question region                 | target -> question source                      | hypothesis                  | design documentation       | intended target                 | validated question                       | question target table              | DB+CI               | `question_target_to_validated`                 |
| `question.option-indicates-range`         | exact option/region evidence             | target -> option/question                      | hypothesis                  | design documentation       | option direction                | respondent comprehension                 | question target table              | DB+CI               | question nonvalidation case                    |
| `question.eligible-for-context`           | design rationale                         | eligibility -> question/context                | HYPOTHESIZED                | later study planning       | planned eligibility             | measured effect                          | eligibility tables/JSONB           | audit+CI            | `context_eligibility_to_measured_effect`       |
| `question.distinguishes-ranges`           | governed option set                      | target -> question options                     | hypothesis                  | broad-direction design     | intended distinction            | information gain                         | question target table              | DB+CI               | `information_gain_without_observations`        |
| `evidence.supported-by-source`            | versioned source or dataset              | assertion -> support -> version/license        | assertion lifecycle         | provenance                 | support presence                | reuse permission or truth strength       | evidence support tables            | deferred triggers   | provenance suites                              |
| `evidence.derived-from-snapshot`          | immutable snapshot link                  | derived row -> snapshot/file hash              | immutable                   | reproducibility            | derivation ownership            | independent evidence family              | snapshot FKs                       | DB+rebuild          | snapshot tests                                 |
| `evidence.measured-by-method`             | named method/configuration               | value -> method/run/snapshot                   | immutable run               | quantitative ledger        | method-local value              | universal score                          | measurement tables                 | bounds+rebuild      | empty configuration case                       |
| `evidence.reviewed-under-protocol`        | review receipt                           | candidate -> review -> reviewer/protocol       | review lifecycle            | governance                 | recorded decision               | automatic downstream promotion           | audit tables                       | DB+audit            | promotion tests                                |
| `governance.candidate-promoted-by-review` | permitting review plus event             | event -> review -> target                      | historical event            | explicit promotion         | named target promotion          | automatic promotion                      | `audit.promotion_event`            | deferred trigger    | recurrent promotion case                       |
| `governance.superseded-by`                | explicit lifecycle decision              | assertion -> replacement/event                 | historical                  | deprecation resolution     | named replacement               | semantic merge by proximity              | lifecycle fields                   | DB+CI               | canonical freeze                               |
| `governance.rejected-by`                  | review decision                          | candidate -> review                            | terminal review             | audit                      | rejection record                | deletion of history                      | audit review tables                | DB+audit            | review suites                                  |
| `governance.requires-evidence`            | registry-named gate                      | assertion -> evidence path                     | local                       | validation                 | fail closed                     | inference without support                | constraints/triggers               | CI                  | membership evidence case                       |
| `governance.forbidden-from-promotion`     | active prohibition                       | candidate -> prohibition rule                  | active until forward change | fail closed                | retain candidate                | canonical side effect                    | triggers/rule registry             | CI                  | 18 Round 3F cases                              |

## Range method-value separation

`corpus.association_measurement` retains method, version, snapshot, support
count, document count, independent-source count, source diversity, observed
value, value semantics and configuration. A PPMI value is not fuzzy membership,
expert grouping, Jaccard, or source-defined membership. There is no universal
`membership_weight`, `association_score`, `similarity`, `confidence` or
probability field.

## Lifecycle and promotion

Ranges use `CANDIDATE`, `SOURCE_LOCAL_SUPPORTED`, `CROSS_SOURCE_SUPPORTED`,
`RESEARCH_REVIEWED`, `BILINGUAL_REVIEWED`, `ACTIVE_FOR_CALIBRATION`, `REJECTED`
and `DEPRECATED`. Cross-source support requires two independent evidence
families or an explicit formal grouping. `ACTIVE_FOR_CALIBRATION` requires an
explicit review receipt. No range lifecycle changes the canonical ontology.

Future ontology suggestions belong only in the
`ONTOLOGY_CHANGE_CANDIDATE_REGISTER` section of the active round's gap report.
Additional project-level range proposals belong only in the
`ADDITIONAL_RANGE_CANDIDATE_REGISTER`. Both registers are empty in Round 3F.

## Round 3G evidence and review layer

Round 3G makes the source-to-decision path executable without changing the
relationship taxonomy:

```text
source family -> versioned source -> immutable snapshot/file
              -> relationship evidence claim -> explicit review decision
```

`evidence.relationship_evidence_claim` retains direction (`SUPPORTS`,
`CHALLENGES`, `MIXED`, `INSUFFICIENT` or `OUT_OF_SCOPE`) and an exact evidence
locator. `kb.relationship_review_decision` and the question/range decision
tables preserve the prior state, disposition, resulting state, reasons and
uncertainties. A source-local promotion requires a permitting review and
evidence from one family; cross-source promotion requires at least two distinct
independent family keys. Derived copies and mirrors never increase that count.

The expected-state gate measures acquisition and review completeness while
keeping evidence outcomes separate from engineering success. No minimum number
of promotions is encoded. Contradictory evidence is immutable audit material,
and no Round 3G source may feed a model run.
