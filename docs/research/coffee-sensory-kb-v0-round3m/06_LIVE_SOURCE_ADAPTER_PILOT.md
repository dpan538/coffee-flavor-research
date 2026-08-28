# Live source adapter pilot

## CoE schema classes

Round 3M validates separate adapters for three non-interchangeable CoE schema
classes:

1. Honduras 2017 explicit `Top Jury Descriptions`, treated as P2 candidates
   because the source explicitly pairs the field with international-judge
   scoring.
2. Colombia South 2008 frequency-coded sensory fields, retained as unresolved
   P1 candidates because the public field does not establish what each
   frequency counts.
3. Peru 2025 and Mexico 2023 generic sensory fields, retained as provenance
   unresolved because organizer hosting does not identify the author.

Producer or farm narratives remain separate P3 layers. Secondary sensory
tables remain separate and cannot double-credit the primary field. Scores are
metadata, not descriptors.

## Verified pilot output

```text
GENERIC_SOURCE_PROFILE_COUNT=11
LIVE_SOURCE_ADAPTER_COUNT=4
LIVE_SOURCE_ADAPTER_VALIDATED_COUNT=3
COE_EXPLICIT_JURY_ADAPTER_PASS=true
COE_FREQUENCY_CODED_ADAPTER_PASS=true
COE_GENERIC_FIELD_ADAPTER_PASS=true
MEXICO_2023_LIVE_FIXTURE_PASS=false
MEXICO_2023_STATUS=SOURCE_DRIFT_DETAIL_BODY_UNAVAILABLE
```

Three bounded captures cover five Honduras records, two Colombia South
records, and one Peru record. They produce 73 explicit-jury P2 assertions (41
strict, 32 broad), 54 unresolved frequency-coded assertions, and 13 unresolved
generic-field assertions. Mexico contributes zero rows because its detail body
was unavailable. The total is 140 provisional assertions under eight effective
records.

The capture manifest SHA-256 is
`b36fbe8a959b099b1a3a073b045c3d6ac74e31043f090d2fd88bd78c3290e51d`.
The three capture hashes are
`2ecb916106615174a12a05a01589ef2799d168765880a5b83e5416540f562053`,
`717b9e1a3ef6400fa334ddbaf80cb592125ddbdecaf67b0d6271f94bf7878033`,
and `44b83f0786a9909c3f55fa4ba0f148aee15d75e54ae571918cc4350372b2a0f9`.
They are owner-controlled web-index field captures, not full official page
bodies, and are not redistributed in Git.

## WCC route

Only authoritative, completed, filled official scoresheets qualify as a live
positive. The governed WCC material available to this round consists of blank
forms, rules, and result/ranking metadata. The adapter therefore records zero
completed positive fixtures and passes the required zero-yield negative path;
it does not broaden acquisition into generic WCC results.

```text
COMPLETED_WCC_SCORESHEET_ADAPTER_PASS=false
WCC_ZERO_YIELD_NEGATIVE_PASS=true
```

Fixture hashes, route locators, parser versions, expected tiers, classes,
layers, and rights states are listed in
`db/data/round3m/SOURCE_ROUTE_SCHEMA_SIGNATURE.tsv`.
