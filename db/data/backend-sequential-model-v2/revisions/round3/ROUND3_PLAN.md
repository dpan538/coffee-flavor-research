# Round 3 Plan — Full Research and Mapping

**Status:** ACTIVE. Phase 0 decided 2026-09-11 (R3-D1..D3 in `owner_decisions_round3.json`): restricted root approved; posture is per-dataset owner approval after manual review; option A recorded. Phase 2 has begun: CoffeeReview parser v1 ingested (`coffeereview_ingestion_finding.json`).
**Written:** 2026-09-11, on the owner's redirection: the project leaves the fall-recruitment
timeline and becomes a polish-first personal research project. "We absolutely need more data
or corpus support."
**Supersedes:** the acquisition-first posture of R10 through round 2.

---

## 0. The reframe

Rounds R10, R11, R12 and round 2 all pursued the same strategy: acquire more openly licensed
literature. Measured results of that strategy, in order:

| Round | Effort | Yield |
|---|---|---|
| R11 | 248 candidates | 6 groups |
| Round 2 | 300-candidate sample, repaired gates | 19 on-subject named groups, from 3 candidates |
| Round 2 ext | 61 minutes, 4 new families | 88 net new DOIs, 76% overlap with what was held |

Meanwhile, the project's own ledger holds:

| Tier | Atoms | Coffees | Groups (≥2 descriptors) | Descriptors |
|---|---|---|---|---|
| Licensed (CC BY / CC BY-NC) | 7,855 | 204 | **181** | 53 |
| Publicly discovered, no licence claimed (ACE etc.) | 44,656 | 1,450 | **1,420** | 55 |
| **Total** | 52,511 | 1,654 | **1,601** | 56 |

The licensed tier is at ceiling: 204 coffees, upper bound 214 if every unmapped atom were
mapped. The unlicensed tier is **7.8x** larger and comes with a ranked 200-item owner review
packet and 1,989 unmapped descriptor clusters, 56 of them with 100+ supporting assertions —
none of it touched.

The bottleneck was never availability. It was the rights posture, which was appropriate for a
credential-bearing public product on a deadline, and is now an open question.

**What changes in how we think:**
- From *acquire more literature* → *map what is already held*.
- From *licence-first* → *purpose-first*. The project's rights matrix already carries eight
  purposes, including `INTERNAL_RESEARCH_ANALYSIS`; its `human_owner_decision` column is empty
  for all 7,720 rows.
- From *ship by the deadline* → *the user research is the product*. Eight question axes exist and
  none has ever been validated with a person.
- Literature capture is **deprioritised**, not abandoned: 0.063 specific-word groups per
  candidate, wide intervals, throttled by a fake `mailto`. It is the most expensive path to the
  least data.

---

## 1. The dataset list the owner pasted, assessed

| Dataset | What it is | Serves option A (named descriptors)? | Rights | Status in project |
|---|---|---|---|---|
| CQI (Kaggle) | ~1,300 lots, Aroma/Flavor/Acidity/Body scored 0–10 | **No** — dimension-level intensity, the B-type supervision the owner did not select | Scraped from CQI; unclear | Never assessed. Auxiliary at most (T4-like dimension track). |
| RoasterDB | Roaster tasting notes normalised to the SCA wheel | **Yes** — this is exactly named-descriptor-per-coffee | Scraped roaster copy; "free sample" on Kaggle | Never assessed. **Same posture question as ACE.** |
| Great American Coffee Taste Test | 4,000+ consumers rating **4 coffees** | **No** — four coffees cannot ground 56 descriptors | Publicly released | Never assessed. T2-like consumer auxiliary. |
| Dryad black coffee (B8993H) | 118 consumers, physicochemical + intensity | Partial — intensity, not named words | CC0 | **Sibling B8C91C already held** as `family.pmc8774372_brewed_black_coffee`. Check whether B8993H is distinct. |
| CoffeeReview scrapes | Editorial prose: "honeysuckle, cashew, baker's chocolate" | **Yes** — rich named descriptors | Scraped **copyrighted editorial content**; no licence | Never assessed. Same posture question as ACE, and a weaker case: editorial prose, not competition results. |

Two of five are genuinely useful for the selected architecture, and **both sit behind the same
decision as ACE**. The list does not change the shape of the problem; it confirms it.

---

## 2. Phases

### Phase 0 — Posture decision (owner; blocks everything else)

One decision, recorded in `PURPOSE_SPECIFIC_RIGHTS_MATRIX.human_owner_decision`:

> Under what purpose does this project now operate, and which rights tiers does that purpose
> admit?

| Option | Admits | Groups | New sources it also covers |
|---|---|---|---|
| P0-A | Licensed only (status quo) | 181 | Dryad only |
| P0-B | + publicly posted **factual** competition/auction results for personal research analysis | ~1,600 | RoasterDB (roaster notes are marketing copy — borderline) |
| P0-C | + scraped editorial content | ~1,600 + CoffeeReview | CoffeeReview, RoasterDB |

Facts for the decision, not advice:
- The matrix's `PRODUCT_DEPLOYMENT` row already marks CC BY-NC zenodo as PROHIBITED (F15) —
  that classification treated deployment as inherently commercial and should be revisited under
  the same decision.
- Descriptor terms are short factual observations about a coffee; databases of facts carry thin
  copyright in most jurisdictions. Editorial prose (CoffeeReview) is a different category.
- CC BY-NC attribution obligations still apply to the licensed tier regardless.
- Nothing here is legal advice. It is what the licences and the project's own labels say.

Outputs: the matrix column filled; `KNOWN_PIPELINE_DEFECTS` updated with the decision; R11's
`owner_decision.json` gets `selected_option: A` recorded (already decided in conversation, never
written).

### Phase 1 — Full mapping (the core work of the round)

Prerequisite: F17 — replace `mailto=research@example.org` with a real address in all three
capture scripts. One line. Everything network-bound in this round waits on it.

1. **Ontology gap register.** 1,989 STRICT_FLAVOR clusters, `human_reviewed=false` for all.
   Work in support order: 56 at 100+, then 87 at 20–99, then 191 at 5–19. Each cluster resolves
   to MAP_TO_EXISTING / NEW_CONCEPT / MODIFIER / DEFECT / DISCARD.
2. **Owner review packet.** 200 ranked items, `project_owner_decision` empty for all, 160
   already tagged MAP_TO_EXISTING. Process it.
3. **Cross-language review.** 1,893 atoms blocked on `CROSS_LANGUAGE_REVIEW_REQUIRED` — the
   product is bilingual and this is directly on its path.
4. **Extents.** Every concept admitted to the registry gets a declared extent in
   `concept_extents.json`. The lattice refuses undeclared category concepts by design.
5. **Registry growth target:** from 56 specific descriptors toward whatever the corpus supports
   at support ≥5 — on current counts, roughly 150–200.

Measured on completion: `max_class_size`, `equivalence_class_count`, per-column variance —
all three, per the contract's representation-progress rule. Never spectral gap alone.

### Phase 2 — New source intake (conditional on Phase 0)

- CoffeeReview: **INGESTED v1** — `acquire-coffeereview-round3.py`, 8,387 reviews → 6,180 with a descriptor sentence → 27,011 atoms; 4,670 records carry ≥2 registry words (26x the licensed corpus). **CR-1 DONE (clean stage)**: 77K checkpoint opened on the 40K→50K pattern — 77,038 source assertions, 81,175 atoms, 4,670 records with ≥2 registry words now in the cleaned view; `clean77k` subcommand, 14th route, 4th adapter, owner-review branch in `purpose_rights`. Gates updated loudly (14/4, EXPECTED_FILES, receipt 98→102), two silent-drop gates caught (`stale_gate_audit_round3.json`). B4 left unchanged — correct for its scope. Remaining: CR-1b (semantic on 77K), CR-1c (rights matrix to 77K), CR-2 (parser v2).
- RoasterDB: not yet supplied by the owner; assess when it is. Both go through the **existing** cleaning pipeline
  (`SEMANTIC_CLEANING_V2` → `ONTOLOGY_CONSOLIDATION` → gap register). No new pipeline.
- OpenAIRE and Semantic Scholar: G1-5 — resolve licences for the novel DOIs, apply
  `relevant()`, and report *would-be-captured*, not *novel*. Both need a real `mailto`.
- CQI and the Hoffmann test: ingest as auxiliary tiers (T4 dimension track, T2 consumer track)
  if at all. They do not feed named-descriptor supervision and must not be counted as groups.
- F16: every future capture persists rejected identifiers with their reason.

### Phase 3 — Question coverage

With the expanded registry: design axes that reach it. Fruit subdivision becomes groundable on
1,400+ groups rather than the 68 used in round 2 (which gave lift 1.01 on co-occurrence and
p = 0.04 on distributional similarity — a weak result on thin data). Every axis carries
partitions with declared extents, so the machine's entailment rule applies unchanged.

### Phase 4 — User validation (the research project proper)

Every one of the 8 axes carries `product_use_eligible=false`, reason
`INFORMATION_GAIN_AND_USER_COMPREHENSION_NOT_VALIDATED`. The 12 supporting evidence rows are
unanimous: `NOT_USER_VALIDATED`, `NOT_ESTIMABLE`. No corpus size changes this.

Design and run the study: wording comprehension, response behaviour, information gain per
axis. `generate_user_study_pack_r9` exists and is the starting infrastructure. This is the phase
that turns axes from research constructs into product questions.

### Phase 5 — Evaluation, freeze, product

- Evaluate the proposition lattice on the full admitted corpus. 181 groups was adequate for a
  paired comparison; 1,600 is adequate for per-dimension breakdowns.
- Owner gate 2: freeze, in the `FREEZE_MANIFEST.json` shape (row_count + sha256 per file,
  `contains_model_weights: false`).
- Owner gate 3: product plan — D5, F4, the relation-edge queue, output schema with empty cases.
- Only then: push.

---

## 3. What is explicitly not in this round

- ANFIS or any fitted model. Abandoned; the lattice does no fitting and 1,600 groups does not
  change that.
- Literature capture to a volume target. The 15,000–20,000 target is withdrawn; the measured
  unique ceiling is ~4,300–4,700 and the yield is 0.063 groups per candidate.
- Any push to origin. Gates 1–3 stand as the owner set them.

---

## 4. Open items carried in

| ID | Item | Owner? |
|---|---|---|
| Phase 0 | Posture decision | **Yes** |
| F15 | CC BY-NC marked PROHIBITED for PRODUCT_DEPLOYMENT | Yes, under Phase 0 |
| F16 | Rejected DOIs discarded, exhaustion unmeasurable | No — pipeline change |
| F17 | Fake `mailto` in all capture scripts | No — one line |
| G1-5 | Convert OpenAIRE/S2 novelty into would-be-captured | No — after F17 |
| D5 | `suppress_profile_when_secondary` | Yes |
| D15 | R11 option A — decided in conversation, not yet written | No — record it |
| — | B8993H vs B8C91C: same study or distinct? | No — check |
