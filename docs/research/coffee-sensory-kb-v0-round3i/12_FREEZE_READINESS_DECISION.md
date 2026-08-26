# Freeze-readiness decision

## Evidence-plane result

Round 3I satisfies every mandatory data-coverage gate without changing the
pre-acquisition thresholds.

| Gate                                               | Minimum | Observed | Result    |
| -------------------------------------------------- | ------: | -------: | --------- |
| Independent contemporary tasting-language families |       3 |        3 | Hard pass |
| New contemporary tasting/evaluation documents      |     500 |    3,289 | Hard pass |
| Governed unique normalized expressions             |   2,500 |    2,996 | Hard pass |
| Independent source-authored `zh-Hans` families     |       2 |        2 | Hard pass |
| Source-local-supported memberships                 |       6 |        6 | Hard pass |
| Cross-source-supported memberships                 |       4 |        4 | Hard pass |
| Ranges with source-local evidence                  |       6 |        6 | Hard pass |
| Independent research-supported question targets    |       6 |       12 | Hard pass |

The governed vocabulary calculation is deliberately global:
`1,777 + 18 + 952 + 249 = 2,996`. It does not use the 1,239 Round 3I expression
rows as the novelty delta, because 20 of those rows overlap the governed
baseline.

The non-language evidence plane does not regress: 130 concepts, 92 active
sensory attributes, nine sensory source families, 4,344 source-local sensory
rows, 230 samples/configurations, 181 empirical cells, 20 features, and 12
partitions remain unchanged. Relationship claims rise from 96 to 97. Question
user-validation and information-gain counts remain zero.

## Preferred-state result

| Preferred gate                         | Preferred | Observed | Result     |
| -------------------------------------- | --------: | -------: | ---------- |
| Contemporary tasting-language families |         5 |        3 | Gap of 2   |
| Contemporary documents                 |     1,500 |    3,289 | Pass       |
| Governed unique expressions            |     3,500 |    2,996 | Gap of 504 |
| Source-authored `zh-Hans` families     |         3 |        2 | Gap of 1   |
| `zh-Hans` sensory expressions          |       200 |      249 | Pass       |
| Ranges with cross-source evidence      |         4 |        4 | Pass       |

The preferred 3,500-expression target is not met and must not be described as
met. It is not a hard gate. Because the `zh-Hans` sensory-depth and fourth-range
preferred gates both pass, `ZH_HANS_SENSORY_DEPTH_WARNING=false` and
`RANGE_CROSS_SOURCE_DEPTH_WARNING=false`. The remaining preferred family and
lexical-breadth gaps stay in the release limitations.

## Candidate decision

Condition A of the acquisition stop rule is satisfied: all mandatory coverage
gates pass. Broad Round 3I acquisition should stop and engineering closure
should begin. Additional low-yield collection is not justified merely to make
preferred numbers symmetric.

The data decision is:

`RESEARCH_DATABASE_FREEZE_STATE=FREEZE_CANDIDATE_WITH_PREFERRED_GAPS`

It may become `RESEARCH_DATABASE_V0_FROZEN` only after the same exact candidate
has all of the following evidence:

- source annotation, rights, privacy, file-hash, and relationship-provenance
  completeness each equal `1.0000`;
- canonical, schema-integrity, data-quality, leakage, and model-prebuild hard
  gates pass;
- eight approved current views and eight deprecated research views are
  registered;
- the manifest and all 10 other required inventories have verified SHA-256
  values;
- two clean PostgreSQL 17 rebuilds reproduce every database-derived hash;
- both remote CI jobs pass on the exact freeze-candidate SHA;
- that exact candidate is promoted without force push and remote main is
  verified; and
- the annotated `coffee-sensory-research-db-v0.1.0` tag points to that exact
  main SHA before the post-promotion attestation marks the release `FROZEN`.

No feature-branch SHA is the final frozen release. Failure of any integrity,
reproducibility, CI, promotion, or tag condition keeps
`RESEARCH_DATABASE_V0_FREEZE_READY=false` even though the coverage gates pass.

## Prohibition receipt

Round 3I closes only if all of these remain true:

- `RANKING_MODEL_TRAINED=false`
- `ADAPTIVE_POLICY_TRAINED=false`
- `DEEP_LEARNING_MODEL_RUN=false`
- `EMBEDDING_BASELINE_RUN=false`
- `PGVECTOR_REQUIRED=false`
- `REAL_HUMAN_COLLECTION_PERFORMED=false`
- `REAL_OBSERVATION_COUNT=0`
- `PRODUCT_FRONTEND_MODIFIED=false`
- `NEW_CANONICAL_CONCEPT_COUNT=0`
- `CANONICAL_CONCEPT_SPLIT_COUNT=0`
- `CANONICAL_CONCEPT_MERGE_COUNT=0`

The release is a governed research database baseline, not training truth, a
deployed model, or a claim that coffee flavor language is complete.
