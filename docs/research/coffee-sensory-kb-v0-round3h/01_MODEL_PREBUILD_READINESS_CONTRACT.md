# Model-prebuild readiness contract

Frozen on 2026-08-25 before any Round 3H source download or import. The
machine-readable contract is
`db/data/round3h/model_prebuild_expected_state.tsv`. Its minimum and preferred
thresholds are immutable for this round unless a separately committed decision
record explains a scientifically necessary correction. A result may fail; the
thresholds must not be lowered merely to produce a pass.

## BASELINE

The verified starting checkpoint is
`aa6a18ca5f4c289d5fa588e1996c7fa219f99eca`. PostgreSQL 17 was rebuilt from all
42 frozen migrations (`000` through `041`) before these counts were recorded.

The whole governed evidence inventory—not only the Round 3G source-family
table—contains four independent sensory-outcome origins: Dryad Cotter black
coffee, Mendeley coffee taste sensitivity, Mendeley FT-NIR specialty-coffee
scores, and Mendeley Liberica RATA. The FT-NIR family has an undeclared assessor
method and therefore contributes a source family and source-local score rows,
but not a method or reference-panel count. The Cotter family contributes CATA
and JAR/liking; Liberica contributes RATA. Marketing language and chemistry-only
sources do not count as sensory outcomes.

The baseline sensory-row count is 3,689: 3,186 Cotter consumer rows, 320
source-local FT-NIR score/metadata rows, 93 taste-sensitivity consumer rows,
and 90 public Liberica aggregate cells (10 descriptors by 9 source-defined
configurations). The sample/configuration count is 101: 27 Cotter brew
configurations, 64 FT-NIR sample identities, one unidentified study-coffee
condition, and nine Liberica configurations. These are descriptive counts, not
pooled observations. Participant/panel count is 236 where disclosed (118
Cotter judges, 93 taste-sensitivity IDs, and 25 Liberica panelist codes); it is
not a readiness threshold.

Only filter/percolation has governed sensory-outcome preparation coverage.
Cotter medium and the three source-defined Liberica L/M/D configurations give
four source-local roast labels/categories, but only one observed
coffee/sample-family × preparation × roast cell has both a governed C0 family
and C1/category value. The existing empirical cube has exactly 52 observed
source-local cells. Chemistry, food descriptions, and lexical entities remain
visible but do not satisfy sensory gates.

There are 1,777 governed unique normalized corpus expressions. Firstbloom is
the only tasting-note corpus; there are zero additional contemporary
tasting-language families or documents. One conservative Wiktionary revision
family exists, but it contributes no admitted zh-Hans coffee sensory
expressions. Relationship evidence has 20 claims, one source-local supported
membership, no cross-source supported membership, and two question targets
with independent research context. No question is user validated and no
information gain is estimable.

## MINIMUM_MODEL_PREBUILD_STATE

The mandatory minimum is multidimensional. Every hard gate must pass:

- sensory: at least 5 independent coffee-sensory families, 3 genuine method
  families, 2 ordinary-user families, and 2 reference/trained-panel families;
- context: sensory outcomes in at least 3 preparation families, at least 4
  roast categories/schemes, at least 12 genuinely observed crossed cells, and
  at least 120 empirical coverage cells;
- language: at least 3 contemporary tasting-language families excluding
  Firstbloom, 500 new documents, 2,500 unique normalized expressions, and 2
  independent Simplified-Chinese lexical families;
- relationships: at least 80 evidence-specific claims, 6 source-local and 3
  cross-source supported memberships, and 5 ranges with a supported
  source-local membership path;
- questions: at least 6 targets with independent research support while user
  validation and information gain remain zero;
- governance and analysis: complete source annotation, rights, privacy, and
  hashes; explicit missingness/harmonization; a feature registry; federated
  source partitions; a future-split leakage audit; and a manifest that forbids
  incompatible pooling and all model/embedding execution.

Milk sensory evidence is not a hard minimum for a black-coffee-only result. If
all hard gates pass while actual milk sensory outcomes remain absent, the only
permitted positive state is `MODEL_PREBUILD_READY_BLACK_COFFEE_ONLY`, and the
manifest must set `MILK_MODE_MODEL_PREBUILD_ALLOWED=false`.

## PREFERRED_MODEL_PREBUILD_STATE

Preferred coverage raises the empirical cube to 180 cells, contemporary
tasting-language families to 5, new contemporary documents to 1,500, unique
normalized expressions to 3,500, Simplified-Chinese families to 3 and observed
Chinese sensory/tasting expressions to 200. It seeks 150 relationship claims,
10 source-local and 6 cross-source supported memberships, 4 ranges with
cross-source evidence, 10 independently researched question targets, and at
least one actual milk-sensory family. No single new tasting-language family
should exceed 60% of new documents or expressions; lawful concentration is
retained but must produce a warning.

## OBSERVED

At freeze time the readiness dimensions are all measured independently.
Rights and baseline reproducibility pass. Sensory, context, language,
relationship, question, and federated-analysis minimums do not all pass.
Consequently `MODEL_PREBUILD_DATA_READY=false` and the initial decision is
`COMPLETE_WITH_DATA_COVERAGE_GAP` pending acquisition, not a predictive claim.

## DELTA

The largest hard gaps at freeze time are: +1 sensory family, +2 preparation
families, +11 crossed cells, +68 empirical cells, +3 contemporary
tasting-language families, +500 contemporary documents, +723 unique
expressions, +2 independent zh-Hans families, +60 evidence claims, +5
source-local and +3 cross-source supported memberships, +4 locally evidenced
ranges, +4 independently researched question targets, and +1 reference/trained
panel family. Counts may rise only through lawful, versioned, source-local
evidence. An observed row may satisfy more than one dimension, but mirrors,
derived duplicates, inferred cells, translations, and mechanically generated
claims never count as independent evidence.

## READINESS_DECISION

`MODEL_PREBUILD_DATA_READY` becomes true only when every hard gate returned by
`audit.run_model_prebuild_readiness_gate()` passes. The result must be exactly
one of `MODEL_PREBUILD_READY`, `MODEL_PREBUILD_READY_BLACK_COFFEE_ONLY`,
`COMPLETE_WITH_DATA_COVERAGE_GAP`, `BLOCKED_RIGHTS`, `BLOCKED_PRIVACY`,
`BLOCKED_REPRODUCIBILITY`, or `BLOCKED_REMOTE_CI`. Acquisition stops when the
minimum is reached or when two consecutive targeted batches add no meaningful
coverage to the selected gap. No ranking model, adaptive policy, deep-learning
run, embedding, pgvector dependency, real-human collection, frontend change,
or canonical-concept expansion is authorized.
