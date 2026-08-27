# Round 3K executive synthesis

## Decision

Round 3K replaces the failed document-centric acquisition model with a
competition-native professional evidence model. The working branch is based on
the exact frozen release source SHA
`c3ae9b880d85507a0b8b0298bb94ef013d02f928`; the failed Round 3J branch remains
unchanged at `a92b448043e8dad468339b3ca2cdfd2b7f6aa772` and is not merged.

The core observation unit is not a document, page, judge row, descriptor
occurrence, or coffee identity by itself. It is one unique:

```text
competition series
x edition
x category
x round
x entry or lot
x preparation service
```

with verified fresh-preparation evidence, official professional provenance,
and at least one official score or professional descriptor. Repeated rounds
may form separate linked round-service observations. Judge rows remain judge
observations and do not multiply effective records.

## Why recovery is required

The user-supplied 20-page _Deep Research Round 2 - Global Professional Coffee
Competition Corpus, Fresh-Brew Sensory Evidence, Scale Gates, and Adaptive
Candidate Ranking_ report was inspected in full as mandatory design input. It
finds that Round 3J preserved useful governance but selected the wrong source
population and observation grain. Its six admitted documents comprise four
packaged ready-to-drink reviews and two consumer sensory studies; its 37 new
occurrences were structurally constrained to `UNRESOLVED`. Those items are not
part of the Round 3K professional corpus.

The report also identifies useful db/049 semantics: frozen-base binding,
source-family identity and independence, mirror handling, rights/privacy/model
decisions, acquisition-batch audit, duplicate and grouped-split governance,
task-specific candidates, readiness gates, and model-run prohibition. Round 3K
will re-port those semantics after a dependency audit. It will not blindly
cherry-pick db/049. The db/050 corpus contract is superseded as an active design
and remains only on the failed branch as audit history.

The dependency audit passed as a recovery decision: exact db/049 code is not
portable because it hard-codes Round 3J checkpoints, obsolete scale lanes and
release names, reads a deprecated readiness view, omits competition grouping
keys and the six Round 3K rights dimensions, and creates a permanent model guard
that would also block a later authorized Round 4. Its governance semantics will
therefore be reimplemented in forward Round 3K migrations.

## Two non-interchangeable milestones

- **Milestone A:** at least 7,000 observed P1/P2 professional round-service
  records, 40,000 professional descriptor assertions, and every accompanying
  provenance, diversity, context, anti-inflation, and holdout gate. This is a
  research-grade acquisition milestone only.
- **Milestone B:** at least 10,000 model-eligible P1/P2 professional
  round-service records, 60,000 assertions, affirmative model-research rights,
  complete governed label provenance, task-specific label counts, grouped
  split integrity, diversity, context coverage, and reproducibility. This may
  freeze a training-corpus candidate for a separately authorized Round 4.

Neither milestone authorizes training during Round 3K. `ML_BASELINE_RUN`,
`RANKING_MODEL_TRAINED`, `ADAPTIVE_POLICY_TRAINED`,
`DEEP_LEARNING_MODEL_RUN`, `EMBEDDING_BASELINE_RUN`, and
`CROSS_ENCODER_RUN` remain `false`; `MODEL_WEIGHT_FILE_COUNT` remains zero.

## Authority and resolved differences

The user's Round 3K request is the operative instruction. The attached report
is design evidence, not an independent command source. Where the two differ,
Round 3K applies the user's explicit contract:

- The operative scale cadence is 1,000, 3,000, 7,000, 10,000, with a 12,000
  forensic trigger. The report's earlier 5,000 checkpoint is not an additional
  Round 3K gate.
- Fresh cezve/ibrik and fresh cold extraction prepared for judging are
  core-eligible when every P1/P2 and protocol requirement passes. Milk and
  plant-milk espresso remain auxiliary. Capsule/pod preparation is not added
  because it is absent from the user-authorized eligible list.
- Cup of Excellence is the first **public** acquisition campaign. Golden Bean
  is the highest-priority **partnership** source. No request, form, purchase,
  subscription, or contract action is authorized in this round without a
  separate user instruction.
- `EVIDENCE_CLASS_COUNT` means distinct core professional assertion classes
  represented by acquired P1/P2 evidence (for example judge-level,
  panel-consensus, and organizer-aggregated evidence), not P0-P5 tier count.
- Numeric structured-score rows remain separate from textual/source-defined
  descriptor assertions and cannot inflate
  `PROFESSIONAL_DESCRIPTOR_ASSERTION_COUNT`.
- Product-query C0 remains the fixed eight-family interface taxonomy. The
  competition preparation-service taxonomy is more detailed and separately
  represents cupping, siphon, cezve/ibrik, and other governed services before
  any reviewed C0 projection.

## Phase A state

The authoritative expected-state, evidence-tier, effective-record, and scale
gate contracts are frozen in `db/data/round3k/`. No professional competition
record has been credited yet, no model-eligible record is claimed, no expert
review has been performed, and no outbound request has been sent. The next
authorized step is to push this rules checkpoint and require green remote CI
before adding the competition schema or adapter framework.

Current truthful result state:

```text
ROUND3K_PARTIAL_PROFESSIONAL_ACQUISITION
```

This is a phase-start state, not the final Round 3K receipt.
