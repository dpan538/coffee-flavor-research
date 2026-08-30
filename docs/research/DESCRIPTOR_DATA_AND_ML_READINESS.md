# Descriptor Data and ML Readiness

Last updated: 30 August 2026
Active branch: `research/coffee-sensory-data-ml-readiness`  
Current decision: `ENGINEERING_SMOKE_PASS_LEXICAL_MEMORIZATION_ONLY;FIXED_NORMALIZATION_BASELINE_COMPLETE`

## Batch 5 normalization engineering result

The project-owner authorization in Batch 5 was applied only to restricted,
professional sensory-language normalization. The exact eligible intersection
is narrower than the independent Batch 4 smoke indicators: 4,096
rights-permitted strict outputs and 9,439 machine-governed strict outputs
intersect at 1,005 outputs with governed targets. They cover 198 connected
coffee/sample lineage groups, 219 effective records, three professional source
families, three years, and 52 target concepts. Post-30k data was excluded and
the immutable 20k, 30k, and 40,030 acquisition checkpoints were not mutated.

The deterministic grouped split assigns 139/30/29 groups and 730/148/127
outputs to train/dev/test. Sample, coffee, publication, and duplicate-group
leakage are all zero. A simultaneous lexical-form-disjoint split is not
feasible: two connected components remain, and the largest contains 1,004 of
1,005 outputs and 197 of 198 groups. Twenty-nine targets meet the declared
closed-set support rule; 23 remain low-support. Supported targets cover 115 of
127 test outputs.

Six preregistered configurations ran offline with seed `20260829`. DEV
macro-F1 selected the character 3–5-gram TF-IDF SGD log-loss configuration.
On grouped TEST it has top-1/top-3 `0.984252` and supported-target macro-F1
`1.000000`, but 125 of 127 test outputs use forms already seen in training.
Both unseen forms score zero at top-1 and top-3. The Zenodo leave-one-family-out
macro-F1 is `0.151142`, compared with `1.000000` for each small Frontiers
holdout. The governed interpretation is therefore
`SEEN_FORM_LOOKUP_ONLY`, not cross-form or cross-family normalization signal.

No fitted estimator was serialized, committed, released, or uploaded. The
results contain hashes and governed IDs only and reproduced byte-identically
from the restricted offline inputs. Human-reviewed and model-eligible counts
remain zero, the corpus is not frozen for training, and ranking, commercial,
product, frontend, PWA, deep-learning, embedding, and further model work remain
unauthorized.

## Batch 4 current position

The immutable acquisition snapshot
`professional-descriptor-candidate-v1-30k` contains 30,010 mechanically
de-inflated source assertions, 1,247 effective records, and seven source
families. It preserves the earlier 20,003-assertion snapshot and its V1 cleaned
view by hash. The post-30k extension is explicitly excluded, and neither
snapshot is a training corpus.

One V2 cleaner (`batch4.semantic-cleaner.v2`) was applied to the frozen 20k,
the 10,007-assertion extension, and the combined 30k. It retains 26,956 valid
source assertions and emits 27,472 cleaned descriptor output atoms, including
24,132 record-unique record/concept targets. The remaining source dispositions
are 3,014 non-descriptor, quality, modifier, or metadata rows and 40 ambiguous
or unresolved rows. V2 raises the 20k valid-source count by 45 and the 20k
output-atom count by 6 relative to the preserved V1 view; the full 20,003-row
V1/V2 receipt is reversible to source assertion and restricted pointer.

The 4,281 source-native hash identities consolidate to 2,860 valid cleaned
forms and 2,208 reversible concept clusters. Machine-governed authority is
limited to exact, approved-alias, and safe morphological mappings: 106 unique
form/concept mappings and 9,579 output atoms. No mapping is owner-reviewed or
expert-adjudicated. The 250-item project-owner packet and blind 900-item human
audit template contain empty decision fields.

Purpose-specific rights are complete for all 965 candidate-bearing source
artifacts across eight purposes. For noncommercial model research, 4,431
cleaned outputs are affirmative with conditions, 253 are pending, 22,788 are
unknown, and none is recorded as prohibited. Commercial-model rights are more
restrictive: 660 pending, 23,041 unknown, 3,771 prohibited, and no affirmative
outputs. These purpose vectors propagate separately through source assertions,
output atoms, clusters, and candidate subsets; general public access is not
treated as commercial-model permission.

Grouped-split feasibility passes for samples, effective records, held-out
families, and held-out years on both all-candidate and noncommercial-permitted
surfaces. The deterministic feasibility buckets have zero sample, coffee,
publication-lineage, or duplicate-group leakage. They are engineering checks,
not a train/evaluation split. The record-unique pair surface contains 301,648
events and 127,176 unique pairs; per-record P50/P90/P95/P99 are
153/528/903/1,485, the maximum is 2,346, and duplicate credit remains capped at
one per record/pair.

The Batch 4 engineering-smoke candidate manifest passed its feasibility thresholds
with 206 grouped samples, three purpose-permitted professional families, 4,096
strict outputs, 1,137 machine-governed outputs, and 60 concept targets. Its
status was `ENGINEERING_SMOKE_MANIFEST_READY_NO_TRAINING`. Batch 5 supplied the
one-time authorization and produced the restricted fixed result documented
above; the candidate manifest remains an immutable pre-run checkpoint.

Post-30k acquisition resumed from the exact page-75/detail-2 CoE cursor and
stopped at the first complete record boundary at 40,030 total candidates. The
isolated extension contains 10,020 de-inflated assertions across 309 effective
records: 8,101 CoE and 1,919 from a new CC BY 4.0 certified-Q-grader MDPI
source family whose original Spanish narratives remain restricted and
untranslated. Six of seven discovery attempts were non-CoE. The next cursor is
page 100/detail 3; CoE is neither exhausted nor blocked. The acquisition was
reproduced byte-identically from its restricted offline cache.

## Batch 3 current position

The 20,003 mechanically de-inflated candidate assertions are frozen as
`professional-descriptor-candidate-v0-20k`. Batch 3 assigned a semantic
cleaning disposition to every one of the 20,245 raw rows and a normalization
disposition to every one of the 2,459 source-form or cleaned-form identities.
The frozen snapshot remains a candidate acquisition denominator, not reviewed
or model-ready data.

The cleaned view contains 17,787 semantically valid source assertions and 35
semantically unresolved assertions. Safe compound expansion yields 17,976
cleaned descriptor assertions, of which 16,294 are record-unique. The semantic
retention rate is 0.889217. Cleaning removed 2,181 non-descriptor source
assertions and no established cross-domain publication duplicate because none
of the seven acquired old-domain/new-domain candidates met the identity rule.

Lexically, 3,467 source-native hash identities became 2,915 first-pass
provisional forms and 2,339 cleaned forms. Deterministic decisions comprise
5,567 exact canonical assertion mappings, 152 approved-alias mappings, 222
morphological mappings, 10,173 ontology-candidate mappings, 1,862 ambiguous
mappings, and 3,002 non-descriptor mappings. No semantic mapping was
provisionally promoted to a canonical concept. Seventy-seven governed concepts
receive defensible mappings; 2,222 unique valid forms remain ontology
candidates. The 247-cluster active queue covers every support-20+ cluster, the
top coverage set, ambiguous Gold clusters, and the previous top-200 queue.

## Semantic QA and cleaned distributions

The source-stratified machine QA covers 5,744 assertions: all 5,055 Gold
assertions, all Project Origin, India Fine Cup, and Sheba assertions, 300
stratified CoE generic assertions, and all 360 Zenodo panelist/sample
observations. It is machine semantic QA, not human or sensory-expert review.
The aggregate estimates are 0.712221 valid atomic, 0.046483 valid broad,
0.049791 compound/under-segmented, 0 over-segmented, 0.190460 non-descriptor
leakage, and 0.280989 strict/broad classification error. Wilson 95% intervals
and per-source estimates are preserved in
`db/data/current/SEMANTIC_AUDIT_METRICS.json`.

The cleaned descriptor classes are 16,489 strict flavor, 1,438 broad sensory,
49 defect/negative sensory, 831 quality evaluation, 2,042 modifier-only, and 6
composite-unresolved atoms. The cleaned family distribution is 13,867 CoE,
3,771 Zenodo, and 338 across the other three families. CoE therefore remains
the anchor at a 0.771417 share; it was not downsampled to cosmetically rebalance
the chart.

The pair-ready surface contains 211,176 within-record pair events and 80,749
unique pairs. Of those, 23,416 have multi-record support, 14,751 have
multi-year support, and 3,556 have multi-family support. The maximum
contribution from one record to one pair is one. The separate Zenodo
sample-consensus view contains 112 effective samples and 847 pair events while
preserving all 360 panelist/sample observations in the source ledger.

## Isolated post-20k extension

Acquisition resumed from the exact preserved Batch 2 cursor and stopped at the
first complete effective-record boundary at or above 30,000. The isolated
extension has 10,023 raw rows, 10,007 de-inflated assertions, 9,528
record-unique assertions, and 455 effective records. Combined candidate volume
is 30,010; none of the extension is a member of the frozen 20k snapshot.

The extension contributes 9,298 CoE assertions and 709 affirmative-rights P2
assertions from two new non-CoE professional families: the CC BY 4.0 Frontiers
/ INERA Robusta Q-grader frequency dataset (590), and the CC BY Frontiers
Lengupá trained-Cenicafé-cupper table (119). Six of seven discovery-route
attempts were non-CoE, a rate of 0.857143. The requested diversification
targets of three positive families and 3,000 assertions were not met and are
reported as gaps rather than inferred or padded.

The next CoE cursor is
`archive-page=75;detail-index=2;url=https://farmdirectory.cupofexcellence.org/listing/2-don-dario-hacienda-san-isidro-labrador-costa-rica-2024-experimental/`.
The route is neither exhausted nor blocked. An offline replay from the
owner-controlled cache reproduced every committed extension file byte for
byte.

## Readiness decision and next work

Candidate volume now passes the 30k checkpoint, but model work remains blocked.
No form is human reviewed or expert adjudicated, no assertion is model
eligible, and 13,952 cleaned assertions still have unknown rights while 253
remain pending. The next cleaning work is human review of ambiguous Gold and
high-impact machine-provisional clusters. The next ontology work is definition
and alias review for the highest-support hashed gap candidates, beginning with
`ontology-gap:ac6ad6be092475b1b77b13f9`. The next acquisition work is a third
independent open professional non-CoE family with row-level observations; the
documented UFLa trained-TDS route remains aggregate-only until an open matrix
is available. The next rights work is CoE reuse permission and author/jury
provenance resolution.

No model, model weights, training-corpus freeze, canonical ontology edit,
database schema, migration, gate SQL, frontend, PWA, or service-worker change
was made.

## Archived Batch 2 acquisition position

The descriptor-first scale-up reached the first complete-record boundary at or
above the amended hard stop: **20,003 assertion-level de-inflated professional
sensory candidates**. The run added 19,846 candidates to the 157-candidate
starting current snapshot. It created no model, model weights, database schema,
migration, product feature, PWA, service worker, or frontend change.

The attached Descriptor-First Census report was directly inspected and its
SHA-256 (`d3192363…8069e0`) matches the existing external receipt. Its reviewed
lower bound of 303 assertions remains contextual: the report's nine-file
machine bundle is still unavailable, so no PDF rows were reconstructed or
arithmetically added. The operative scale-up policy superseded the report's
earlier low-yield stopping recommendation.

## Current corpus and delta

| Surface                                   | Current | Delta from initial snapshot |
| ----------------------------------------- | ------: | --------------------------: |
| Raw segmented assertion rows              |  20,245 |                     +20,087 |
| Assertion-level de-inflated               |  20,003 |                     +19,846 |
| Effective-record-level unique descriptors |  18,069 |                     +17,914 |
| Descriptor-bearing effective records      |     792 |                        +783 |
| Judge-observation records                 |     360 |                        +360 |
| Strict flavor assertions                  |  15,783 |                     +15,687 |
| Broad sensory assertions                  |   4,220 |                      +4,159 |
| Source-native hash identities             |   3,467 |                      +3,337 |
| Provisional normalized forms              |   2,915 |                      +2,915 |
| Assertions with provisional mappings      |  19,846 |                     +19,846 |
| Unmapped baseline assertions              |     157 |                           0 |
| Candidate pair events                     | 258,727 |                    +258,066 |
| Provisional normalized pair events        | 257,351 |                    +257,351 |
| Model-eligible assertions                 |       0 |                           0 |

Provisional mapping coverage is 99.2151%. These are machine proposals, not
human-reviewed canonical labels. The active review queue contains the 200
highest-priority clusters, ranked deterministically by assertion count, source-
family diversity, year diversity, unresolved-origin risk, then stable ID.

## Evidence and collection tiers

| Tier                  | Assertions | Treatment                                                      |
| --------------------- | ---------: | -------------------------------------------------------------- |
| Gold candidates       |      5,055 | P1/P2 candidate evidence; review and rights still gate use     |
| Silver candidates     |     14,618 | Official sensory fields with unresolved author/jury origin     |
| Bronze candidates     |        330 | Professional commercial/auction sensory fields; auxiliary only |
| P1                    |      4,785 | Judge-level Q-grader observations                              |
| P2                    |        270 | Explicit jury fields, including the 73-row baseline            |
| P3                    |          0 | None acquired                                                  |
| P4                    |        330 | Professional auxiliary fields                                  |
| Provenance unresolved |     14,618 | Retained and distribution-countable, not P1/P2/model eligible  |

Model-research rights are affirmative for 4,785 assertions, pending for 270,
unknown for 14,948, and prohibited for 0. Affirmative rights alone do not make
an assertion model eligible: human review, evidence, label support, source-
family, held-out, and distribution gates still fail.

## Distribution diagnosis

Five positive source families contribute candidates: ACE/Cup of Excellence
14,829 (74.1339%), the Zenodo Q-grader dataset 4,785 (23.9214%), Project Origin
302, Coffee Board of India Fine Cup 59, and Sheba Coffee 28. Largest-family
share is 0.741339 and HHI is 0.607045, so concentration remains material.

The corpus covers 19 years and 28 edition/release identities. Cupping is direct
for 19,846 assertions across 783 records; the 157-row baseline remains
preparation-unresolved. Direct roast hashes cover 4,028 assertions across 88
records, concentrated in the Zenodo family. Filter/pour-over and espresso remain
empty target cells.

Provisional effective-record support bands are: 1,891 singleton forms; 579 at
2–4 records; 184 at 5–9; 103 at 10–19; 73 at 20–49; 47 at 50–99; and 38 at
100+. There are 790 set-level multi-target records, 111,953 unique provisional
pairs, 3,845 provisional pairs supported by multiple source families, and
17,521 supported in multiple years. None is eligible training evidence before
review and rights gates pass.

## Acquisition execution

The batch inspected 16 route/schema strata, including reused negative-route
receipts, and produced candidates from 6 routes across 5 source families. It
acquired 971 artifacts including robots, search, archive, detail, workbook,
PDF, and HTML artifacts—below the 2,000-artifact cap. The live automated run
took 1,057.548111 seconds; analyst-equivalent minutes are
`NA_AUTOMATED_ACQUISITION_NO_MANUAL_TIMING`.

Principal positive routes were the [Zenodo Q-grader dataset](https://zenodo.org/records/20840464),
the [Cup of Excellence farm directory](https://farmdirectory.cupofexcellence.org/listings/),
[Project Origin lots](https://projectorigin.coffee/intl-home/intl-our-coffee/intl-high-end-lots/),
the [India Fine Cup brochure](https://hcikl.gov.in/pdf/Winning_Coffees_Brochure.pdf),
and the [Sheba Haraz auction](https://shebacoffee.com/blogs/auctions-and-listings/haraz-auction-2021).
Source-native text and raw artifacts remain in the owner-controlled restricted
root; Git receives hashes, locators, tier/rights states, and provisional IDs.

## Milestones and continuation

The immutable acquisition-local 10k receipt recorded 10,006 candidates and the
next URL at search index 306. Merge reconciliation found that one 18-row Batch 1
publication reappeared in Batch 2. Those rows remain as false-count audit rows.
The corrected merged corpus therefore stood at 9,988 at the original cursor and
crossed the healthy milestone at the next complete record boundary: 10,009
after index 306, with continuation at index 307. Both the immutable receipt and
the deterministic reconciliation are retained.

The hard stop completed at 20,003. Exact continuation cursor:

```text
archive-page=12;detail-index=10;url=https://farmdirectory.cupofexcellence.org/listing/9-liquidambar-honduras-2026-parainema-catracha/
```

## Gate decision and next work

Candidate-volume criteria now pass at the 500, 2,000, 5,000, 10,000, and
20,000 checkpoints. Every full training gate still fails because reviewed P1/P2
strict assertions, reviewed normalized forms, eligible records, eligible source
families, eligible pair events, preparation diversity, and held-out eligibility
remain insufficient or zero. No model baseline is justified.

Next work is review-first and distribution-directed: adjudicate the 200 active
clusters; resolve organizer provenance for Silver candidates; obtain purpose-
specific rights decisions; add filled filter/pour-over and espresso judge
fields; and add at least one independent professional family capable of a true
held-out evaluation. The broad-collection policy remains active without
relaxing evidence claims.

Machine-readable current evidence is in `db/data/current/`; public-safe staged
evidence and milestone receipts are in
`db/data/professional-descriptor-staging/`.

---

## Archived Batch 1 snapshot

The remainder of this file is the preserved pre-scale Batch 1 snapshot. Its
counts are historical and are superseded by the Batch 2 current section above.

Historical decision: `MERGE_COMPLETE_STRICTNESS_POLICY_REVIEW_REQUIRED`

## Current position

The available row-level professional descriptor evidence has been merged into
one deterministic, public-safe current view. The current view is derived from
the governed Round 3M ledger, its effective-record, provenance, rights, review,
duplicate and pair-event relations, plus one bounded hash-only acquisition from
an official 2009 Cup of Excellence listing.

The external Descriptor-First Census remains an aggregate receipt only. Its
required nine-file machine-readable bundle and the named report PDF were not
present in the verified repository or supplied attachment directory. The
external 305/303/302 counts were not reconstructed, added to the live-pilot
counts, or converted into synthetic rows.

Round 4A remains preserved and unmerged. Its 140 assertions, 8 records and 508
pair events are an exact derived view of Round 3M, not new evidence. Seven useful
data-health semantics were regenerated in the rolling package; four redundant
or unusable reports were rejected. No product, PWA, recommendation, event,
service-worker or frontend file was imported.

## Current corpus counts

| Surface                              | Count | Meaning                                                      |
| ------------------------------------ | ----: | ------------------------------------------------------------ |
| Raw segmented assertion rows         |   158 | 140 Round 3M rows plus 18 new hash-only source atoms         |
| Assertion-level de-inflated          |   157 | One Round 3M exact within-field repeat removed               |
| Effective-record-level unique        |   155 | Two additional cross-observation repeats excluded            |
| Descriptor-bearing effective records |     9 | Eight Round 3M records plus one 2009 official-field record   |
| Strict flavor assertions             |    96 | Assertion-level de-inflated                                  |
| Broad sensory assertions             |    61 | Assertion-level de-inflated                                  |
| P2 assertions                        |    73 | Machine-audited explicit jury fields; not human reviewed     |
| Provenance-unresolved assertions     |    84 | Kept in the official-field quarantine stratum                |
| Source-native hash identities        |   130 | Restricted lexical forms counted by SHA-256 identity         |
| Reviewed normalized forms            |     0 | No human-reviewed canonical mapping exists                   |
| Unmapped assertions                  |   157 | 100% of the de-inflated current ledger                       |
| Candidate pair events                |   661 | 508 Round 3M P2 events plus 153 unresolved candidate events  |
| Unique source-atom hash pairs        |   659 | Not canonical normalized descriptor pairs                    |
| Multi-target records                 |     0 | Coassertion is not treated as reviewed multi-target labeling |
| Model-eligible assertions            |     0 | Review, rights, normalization and distribution gates fail    |

The Round 3M headline class totals remain historically preserved as 86 strict
and 54 broad across 140 segmented rows. The current strict/broad surface uses
the assertion-level de-inflated denominator, so the Round 3M contribution is 85
strict plus 54 broad before the 11 strict and 7 broad new candidates are added.

## Distribution diagnosis

The current corpus has four edition years (2008, 2009, 2017 and 2025) but only
one independent professional source family. The largest-family share is 1.0 and
source-family HHI is 1.0. All nine records have unresolved preparation service,
no direct source roast value, and no reviewed C1 mapping. A held-out year or
source-family evaluation is therefore not feasible for an eligible corpus.

No descriptor support band is populated because source-native hashes have not
been human-normalized. Singleton and tail rates are `NA_NO_NORMALIZED_LABELS`,
not zero-evidence claims. The unmapped assertion rate is 1.0.

The master corpus remains complete: common observations were not deleted,
downsampled or relabeled to improve the distribution. Distribution correction
is represented as an acquisition and review queue.

## Bounded targeted acquisition

Batch `descriptor-data-integration-batch-1-20260829` was preregistered with a
maximum of six artifacts, 45 analyst-equivalent minutes, two target cells and
the mandated stop rules. Four artifacts across three route strata were
inspected.

- An official Brazil Pulped Naturals 2009 CoE detail route yielded one new
  coffee-specific record with 18 de-inflated descriptor candidates: 11 strict
  and 7 broad. The field author is not explicit and model-use rights are
  unknown, so every assertion remains hash-only in
  `C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED`.
- A public CQI sample-grade route exposed professional grading context but no
  visible filled descriptor values.
- A 2026 Alishan government competition results release documented professional
  blind evaluation and winners but no filled coffee-specific descriptor
  passage.

The batch stopped at two consecutive zero-yield target route strata. Analyst
minutes are `NA_NOT_INSTRUMENTED_DURING_INTERACTIVE_BROWSER_PASS`; no estimate
was invented.

## Acquisition priorities

The rolling queue prioritizes:

1. a filled explicit judge or panel route from an independent non-CoE family;
2. explicit CoE Top Jury fields in additional years;
3. organizer provenance resolution for the generic and frequency-coded CoE
   fields;
4. owner-controlled normalization review of the 157 current hash-only atoms;
5. filled Brewers Cup judge feedback for filter/pour-over coverage;
6. filled roasting-production cupping evidence with direct roast and C1 context;
7. a genuinely filled CQI sample-grade surface, without rescanning the current
   empty route.

Expected yield is `UNKNOWN` unless measured history exists. The only measured
estimate retained is the prior governed Top Jury capture: 73 P2 assertions per
governed capture in the Round 3M pilot.

## Review and rights

The rolling review packet contains all 157 de-inflated current assertions and
stays under `MAX_REVIEW_PACKET_SIZE=200`. The 18 newly acquired unresolved
official-field rows are first, followed by the 73 P2 rows and the remaining
unresolved rows. Reviewer decision and reason columns are empty.

Current model-research rights are:

- affirmative: 0 assertions;
- pending: 73 assertions;
- unknown: 84 assertions;
- prohibited: 0 assertions.

All 157 assertions are source-audited candidates requiring human review. None is
human confirmed, expert adjudicated, core eligible or model eligible.

## Strictness impact

`SI-001-OFFICIAL-FIELD-ORIGIN-UNRESOLVED` is triggered because 100% of each
affected official-field route is quarantined for the same unresolved-origin
reason. The constraint affects four effective records and 84 de-inflated
assertions (55 strict and 29 broad).

The safe interim state is
`C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED`; the recommended action is
`REQUEST_ORGANIZER_PROVENANCE`. Relaxing the evidence tier is not authorized.
The data remain retained, reviewable and model-ineligible while the policy or
source-provenance decision is outstanding.

## Training gates

All five operational gates fail. Observed reviewed P1/P2 strict assertions,
reviewed normalized forms, eligible records, eligible families, eligible pair
events and multi-target records are all zero. The 84 unresolved current
challenge cases are retained but do not satisfy a reviewed challenge-case gate.

No classical model, ranking model, deep model, embedding baseline,
cross-encoder, adaptive policy or model weight was created. No training corpus
was frozen.

## Next batch decision

Continue with organizer provenance resolution and the 157-row review packet,
while seeking one bounded independent filled judge/panel route and one explicit
preparation or roast-context route. A user policy decision is required before
any official-field-origin rule is relaxed; until then the current quarantine
state remains mandatory.

Machine-readable evidence is in `db/data/current/`. The deterministic generator
and fail-closed contract test are
`db/scripts/generate-current-descriptor-data.py` and
`db/scripts/test-current-descriptor-data.py`.

## Batch 6 — 40k semantic corpus and cross-form benchmark construction

Batch 6 freezes `professional-descriptor-candidate-v2-40k` as an acquisition
checkpoint of 40,030 de-inflated assertions. It is not a training corpus and
does not change the immutable 20k, 30k, or Batch 5 receipts. The existing
`batch4.semantic-cleaner.v2` was reapplied to the isolated 10,020 post-30k
assertions and reconciled with the 30k V2 view.

The resulting public-safe semantic layer separates lexical equivalence,
hierarchy, modifier/compound, observational co-assertion and contextual edges.
Only S0 deterministic morphology and S1 governed mapping/alias edges are
governed. S3 machine candidates remain explicitly review-required; no relation
is marked project-owner reviewed or sensory-expert adjudicated.

The future benchmark separates seen-form controls, known-target held-form
cases, held-family shared-target cases, open-set targets and structured
compound/modifier cases. The Batch 5 addendum records that its two unseen test
forms were unseen targets, not known-target cross-form outputs. No model was
run in Batch 6.

The 40k semantic layer is review-required. A 200-item owner-review packet and
500-item human benchmark template are public-safe/hash-only; restricted review
context stays in the owner-controlled restricted root. The post-40k CoE
continuation is isolated in `db/data/post40k-extension-staging/` and must not
be merged into the frozen 40k cleaned view.
