# Product inference v0.2 research checkpoint

This adds an isolated, flag-enabled participant harness to the existing static
React Router application. It uses the frozen v0.1 candidate, source-local C0
prior and governed question-axis lineage. All twenty concept identities remain
unchanged, including four blocked from research output. All eight C0 families,
seven C1 levels and 56 context combinations remain. C1 contributes zero at every
level and for unsure; no descriptor-to-roast inference or joint-cell expansion
is performed. The old `product-inference-v0` directory is unchanged.

The pure engine and export validator live under `packages/flavor-data/src/research`.
The React route imports that package; it does not fork descriptor data under
`app`. The runtime JSON is generated from the frozen tables and the proposed
language TSV, whose professional label, question wording, result label and
explanation are separate fields. No external assets, copied professional
definitions or source sensory data have been added.

Two between-subject wording variants are research candidates. A has four broad
cards with examples. B has three broad cards and an eligible branch-specific
second question. The extra fruit/flower branch inherits the governed broad-axis
lineage; it is not a new independently validated sensory axis. Nine question
records include alternative first-question presentations and a derived B branch;
the frozen evidence register still has eight axes. `fruit_region` and
`acidity_character` share one semantic key and cannot both occur in a session.

Selected options add positive support once per concept per question. Unselected
options remain neutral. UNSURE and SKIP are separately recorded and change no
scores. NONE_OF_THESE applies a -1.25 heuristic adjustment only to concepts in the
displayed options. It is never generated from nonselection or missing answers.

There is an additional conservative display guard: a previously supported
concept disputed by a subsequent closed-none response is withheld from visible
tiers, although its numeric support is retained. When all rights-eligible
supported candidates are disputed, the engine abstains with a conflict state
and does not ask another question. This guard is an explicit unvalidated product
decision, not a measured strength of negative sensory evidence. It is a priority
for owner review; negative labels are not created for a corpus or model.

Question selection requires two live candidate partitions, nonzero deterministic
separation and different possible visible outputs. It skips used semantic keys.
The candidate-count instrumentation refers to the positive-evidence working set,
or all eligible concepts when support is empty. It is not elimination of neutral
concepts and can grow under multi-select. Recorded separation is a heuristic,
not an empirical information-gain estimate.

Q1 requires a recorded sensory or typed escape response. Q2–Q4 are conditional,
with early stop after two answers and three supported headlines, or earlier for
no eligible split, conflict, open-set or participant-requested partial results.
Q5 requires four completed answers, fewer than three headlines, a material
eligible question, no conflict/open-set state, and explicit acceptance. No sixth
question exists. Q5 acceptance is a click; Q5 completion is `questionCount == 5`.
Accepting and then returning without answering is a valid partial session.

The display is up to three headline candidates, two expanded-main candidates and
three exploration candidates. It never fills a tier merely to reach its maximum.
Rights-blocked or unresolved candidates cannot appear, and review-only support
cannot independently enter a main tier. Redundancy groups are unique across all
tiers. Explanations are proposed reference language, not unique sensory truth.
No probability percentage is shown.

## Local use and verification

```bash
python3 db/scripts/generate-product-inference-v02.py
node scripts/generate-product-benchmark.mjs
python3 scripts/seal-round3o.py
VITE_COFFEE_RESEARCH=1 npm run build
VITE_COFFEE_RESEARCH=1 npm run test:smoke -- tests/e2e/research.spec.ts
```

Serve the research build locally with the repository preview command and open
`/research/user-study`. The default build excludes the route. The harness uses
an in-memory state and a locally created download Blob. It has no analytics,
remote participant write, authentication, service worker or offline redesign.
Individual session exports must remain in restricted owner storage.

Reproducibility uses fixed artifact version/date, ordered input tables and stable
serialization. Run `scripts/seal-round3o.py --check` to verify checksums. No shared
corpus generator, database migration, semantic snapshot or CI workflow changed;
historical replay is not part of this batch. The policy is deterministic,
uncalibrated and not scientifically validated. Formative local user testing is
authorized; production deployment and model training remain unauthorized.
