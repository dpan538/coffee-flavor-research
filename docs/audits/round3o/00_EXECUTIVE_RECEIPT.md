# Round 3O / Batch 9 product research checkpoint

`PHASE_STATUS=ROUND3O_PRODUCT_BENCHMARK_REVIEW_REQUIRED`

The requested local research prototype and review kit are implemented. The
next decision belongs to the project owner: approve or revise the language,
question policy and reference-result tiers using the prepared cases before the
next formative study. This checkpoint does not establish sensory accuracy,
validated wording, product readiness, retained use or permission to train.

## Source, scope and Git custody

The starting source is `e4eced41e2233c76c4645287fba2ecedddd03561` on the existing
`research/coffee-sensory-data-ml-readiness` branch. Its merge base and both remote
branch tips matched at intake. Survey ingestion is commit `95282b5`; the defining
implementation is `736f21806fb21e522b160cc698f879dc980756c9`. This audit is the third
and final planned commit. No new branch, new worktree, reset, rebase, force push,
main promotion, release or deployment is part of this round.

The desktop checkout was already dirty and behind the requested source; its
changes were left untouched. The previously registered research worktree had
lost its link and tracked files during temporary-directory cleanup. Surviving
tracked files and the index were checked before only missing baseline files and
the existing worktree link were restored. This repaired the registered worktree;
it did not create another checkout or overwrite user changes.

All requested public artifacts, code and this audit are committed. The eleven
original submissions, their filename mapping, original text, native Numbers
export and analytical workbook are retained outside Git in owner-controlled
storage (directory mode 700, files 600). Private intake is addressed through
`COFFEE_FLAVOR_USER_RESEARCH_ROOT`; no source name or local identity path is
published. The separate database-course PDF was excluded as explicitly directed
by the user. Instructions inside that PDF were not treated as task authority.

## Reanalysis and interpretation

The original sources reconcile to eleven submitted files and ten distinct
SHA-256 payloads. F003 and F004 are byte-identical, not merely matching answers.
One representative enters the primary denominator of ten; the eleven-file
sensitivity and both source files remain. This is not a claim about the identity
of two people. All 220 primary question records are retained, of which 200 enter
the deduplicated analysis. Native Numbers export recovered all twenty F002
answers after a third-party reader omitted cells.

The supplied reanalysis workbook agrees with all 80 A–D option counts. F001 Q13
remains an open primary answer with separate qualitative codes. Two supplementary
letters do not override primary answers. The six anomaly-register entries cover
reader loss, the open answer, two supplementary letters, an explicit nonresponse
marker and an unverified claim in the analytical aid. The sources contain zero
observed single-digit note artifacts; the earlier claim of repeated digits was
not reproduced. The parser nevertheless retains and excludes such ambiguous
notes if encountered. Qualitative codes remain analyst proposals pending review.

All following counts use N=10:

| Requested measure                      | Count |
| -------------------------------------- | ----: |
| COFFEE_WEEKLY_OR_MORE_COUNT            |     9 |
| FLAVOR_DESCRIPTION_EXPOSURE_COUNT      |     9 |
| C0_FINDABLE_COUNT                      |    10 |
| C1_ROUGHLY_SELECTABLE_COUNT            |     9 |
| SEVEN_LEVEL_ACCEPTANCE_COUNT           |     8 |
| FIRST_QUESTION_ANSWERABLE_COUNT        |     9 |
| FRUIT_LANGUAGE_DIFFICULTY_COUNT        |     4 |
| WHITE_FLORAL_EXPLANATION_COUNT         |     8 |
| UNLIMITED_MULTISELECT_PREFERENCE_COUNT |     8 |
| EXTRA_QUESTION_PREFERENCE_COUNT        |     6 |
| WILLING_TO_TRY_OR_USE_COUNT            |     9 |
| ACTIVE_USE_INTENT_COUNT                |     2 |

The weekly count is a lower bound: Q1 A/B guarantee at least twice weekly, while
Q1 C may include once weekly. White-floral explanation is the union of seven
primary A responses and one explicitly coded open answer. Stated preference and
willingness are neither observed behavior nor retained use. The sample is small
and coffee-exposed, so it cannot represent all novice users.

## Executable policy and participant flow

The twenty concept IDs and their v0.1 rights, source and evidence lineage remain.
Four rights-blocked concepts are withheld. Eight C0 families, seven C1 levels and
56 combinations remain; C1 unsure is a null state and every C1 contribution is
zero. C0 retains only its frozen weak source-local prior. No scores were fitted,
no roast was inferred from flavor words and no joint evidence was manufactured.

Variant A uses four example-based cards; B uses three cards with an eligible
fruit/flower/tea branch. Odd/even research codes assign one variant for a session.
Twenty proposed wording records distinguish professional identities, question
wording, result labels and explanations. Wording is not yet user-validated.

Multi-select adds a union of positive support once per concept and question.
Unselected options, UNSURE and SKIP are neutral. NONE_OF_THESE records a bounded
negative adjustment only for displayed options. A separately documented,
conservative display guard withholds supported concepts disputed by closed-none
feedback and abstains when all supported eligible concepts are disputed. This
guard is an unvalidated product decision requiring owner review; it creates no
negative corpus labels.

Q1 requires a recorded sensory or escape response. Q2–Q4 require a remaining
governed semantic axis with candidate separation and materially different
possible visible outputs. Equivalent fruit/acidity axes cannot both be asked.
Q5 requires four answers, insufficient headlines, an eligible material axis,
absence of conflict/open-set and an explicit click. Acceptance and completion
are separate; returning after accepting still allows a four-answer export.
Results contain up to three headlines, two additional main and three exploration
references, without forced filling or repeated redundancy groups. Partial and
complete abstention are valid results.

The plain research route is disabled in default builds and absent from public
navigation. A flagged local build provides value paraphrase, C0/C1 timing,
question and candidate instrumentation, result expansion, Q5 behavior and six
post-task questions. A strict replay validator checks the session before a local
JSON Blob download. No identity fields, remote participant writes, analytics,
service-worker changes, authentication or external assets were introduced.

## Review kit and evidence boundaries

There are 28 deterministic cases: eleven follow participant flows and seventeen
are explicitly labeled engine-policy fixtures. Generated outputs are current
policy behavior, not an owner-approved answer key. Owner review has 28 blank
rows; the Claude/DeepSeek/GPT template has 84 blank rows. Three actual GPT reviews
are imported with reasons, limitations and provenance: language, behavior and
bounded evidence gaps. These comprise three review records from two independent
agents, not three independently executed model families. Claude and DeepSeek
were not run. Owner decisions and human final decisions both remain zero.

The independent behavior review enumerated 3,382 synthetic states, including
192 Q5 offers. Its engineering findings and fixes are preserved in the review
packet; it is not a participant sample. All product acceptability remains open.

The next study kit targets 8–10 new users, at least four novices, three or four
regular users and at most two experienced users, with paired A/B allocation
within exposure strata. Six post-task questions, missingness, abandonment and
Q5 acceptance versus completion have explicit denominators. Numerical decision
triggers are labeled formative proposals, not significance thresholds.

Eight bounded source routes were inspected. Five evidence gaps remain open.
No new dataset, source forms, source observations or professional definitions
were imported. Source-local two/three-level roast designs do not establish a
seven-level mapping; immersion temperature comparisons do not fill C0 families;
article access is not permission for unverified underlying files. Details and
verified primary-source links are in the gap package.

## Validation recorded before the audit commit

| Gate                         | Recorded outcome                                                                                                                                                                                                                  |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Format and TypeScript        | Full formatting check and default/research type checks passed.                                                                                                                                                                    |
| Unit tests                   | 35 tests in four files passed; 26 target the new product and survey work.                                                                                                                                                         |
| Research browser flow        | 9 enabled tests passed at 390, 768 and 1440px, covering A/B, multi-select, exports, Q5 and partial exits. Three default-only checks were intentionally skipped.                                                                   |
| Public browser compatibility | 15 original smoke paths passed at all three widths. The three new default-route checks passed after correcting the test to assert router-level 404 UI rather than transport status.                                               |
| Builds                       | Default and research static builds passed; default excludes the research artifact.                                                                                                                                                |
| Existing public contracts    | Public status, claims, documentation, screenshots and CI fail-fast contracts passed.                                                                                                                                              |
| Byte reproducibility         | All 41 public files across the four new directories matched before and after two complete generations, including private-source ingestion.                                                                                        |
| Checksums                    | Four SHA256SUMS files cover all other files in their respective directories.                                                                                                                                                      |
| Privacy and model files      | All 62 changed text files scanned before this prose-only audit; no raw submissions, original participant names/paths or model files. Public academic author attribution was distinguished from a same-name participant substring. |
| Frozen boundaries            | v0.1 inference artifacts, descriptor scores, lockfile, database migrations and CI workflows are unchanged.                                                                                                                        |

Node 24 browser assertions completed but initially stalled in worker teardown.
Node 22 completed the browser suite normally with exit code zero; no dependency
or CI change bypassed a check. The static SPA fallback returns HTTP 200 for an
unknown path, while React Router displays its 404 page. The default-route test
now verifies that actual exclusion behavior and the absence of the task entry.

Training runs are zero, training authorization is false and the model-file delta
is zero. Only Round 3O generators were run for local byte verification. Shared
corpus generators, migrations, snapshot generation and CI contracts did not
change, so no manual historical replay was introduced. The existing push-required
CI runs once on the final three-commit checkpoint. At the time this immutable
audit is authored, that push and its remote result are pending; this paragraph
does not claim a result before it exists.

## Final SHA and remote verification resolution

An audit cannot embed the hash of the commit that contains itself. Resolve this
audit's final local SHA from its introducing commit, and compare it with the
remote research ref and the existing CI run's head SHA. The delivered resolved
receipt supplies those literal hashes, run ID, outcome and every requested
key/value field after the single push. GitHub retains the CI result against that
exact immutable commit. No follow-up commit is created solely to copy CI status.

The active research worktree must be clean after this commit. `WORKTREE_CLEAN`
refers to that checkout; it does not misrepresent the pre-existing dirty desktop
checkout. Verify remote main still equals the starting SHA. Do not promote main.

## Owner handoff

Start with `db/data/product-benchmark-v0.2/PRODUCT_TASK_REVIEW_PACKET.md` and the
blank owner template. Prioritize broad fruit/floral wording, the combined fourth
family, closed-none conflicts, the stopping/Q5 policy and tier acceptability.
Then run the prepared study using `NEXT_USER_STUDY_PROTOCOL.md`, measuring novice
comprehension and independent task completion before interpreting preference.

For C0, seek underrepresented preparation contrasts with documented composition.
For C1, seek rights-cleared calibrated roast measurements and an explicitly
reviewed mapping; retain neutral behavior until then. Structured contrast work
needs known comparison sets, denominators, missingness and bounded negatives.
The next ML authorization remains withheld until a human-reviewed, rights-cleared
product-task benchmark supports a separate proposal.
