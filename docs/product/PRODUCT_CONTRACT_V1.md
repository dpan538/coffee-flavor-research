# Product Contract V1

**Status:** DRAFT — requires owner approval before it supersedes anything.
**Supersedes:** `docs/product/PRODUCT_CONTRACT_V0.md` (frozen at commit `27d257c`), on
approval.
**Drafted by:** Claude, acting operator for R12C, from owner decisions D1–D11 recorded in
`db/data/backend-sequential-model-v2/revisions/r12c/owner_scope_decision_r12c.json`.

## 0. Relationship to V0

V0 is not withdrawn and is not erroneous. It is an accurate record of the prototype design
authored before any training attempt. V1 records the post-prototype design, which until now
existed only as owner statements and was never written down.

Everything computed against V0 — the `product-inference-v0` package, its 120 policy cases,
the R9 three-policy comparison — describes the prototype, not this contract. Nothing has yet
been computed against V1.

## 1. Product

A fully online, installable, mobile-first web application at `flavorwords.com`.

For people who can tell that two coffees taste different but do not always have words for
the difference. The interaction moves someone from a broad impression toward more specific,
understandable sensory references.

It is not a tasting exam, not a flavor wheel reproduction, and it does not claim to detect a
coffee's true flavor.

**Offline capability is not a requirement.** The usage environment is online throughout.
The PWA scope is installability and mobile-first delivery: no offline app shell, no offline
fallback, no offline cache-invalidation strategy.

## 2. Interaction flow

Both context and sensory questions are zero-indexed.

### Round 1 — mandatory

```text
C0  preparation / beverage context
C1  roast context
Q0  sensory
Q1  sensory
```

### Round 2 — mandatory

```text
path A:  Q2
path B:  Q2, Q3
```

### Round 3 — mandatory

```text
path A:  Q3, Q4
path B:  Q4, Q5
```

Q2 through Q4 are **mandatory**. What is conditional is their sequencing, not whether they
are asked. The mandatory set does not terminate early.

### The two paths

```text
path A   C0 C1 Q0 Q1 Q2 Q3 Q4              7 steps
path B   C0 C1 Q0 Q1 Q2 Q3 Q4 Q5  → Q6     9 steps
```

Path A is the seven-question algorithm.

### Function of Q4 and Q5

Reinforcement always occurs. What varies is where it lands.

| Path | Q4 | Q5 |
| --- | --- | --- |
| A — rounds 2 and 3 sufficient | reinforcement | not asked |
| B — round 2 insufficient | strong correction | reinforcement |

Q5 is not an exception or an overflow slot. It is the compensating step that carries
reinforcement when Q4 has been promoted to correction.

### Q6 — strong fallback

Triggered when Q5 has occurred, or when the candidate set is confused.

The user is shown the 3 main + 5 secondary list and selects the three they are absolutely
certain of. The system re-summarises and regenerates 3 main + 5 secondary.

Q6 is a user-in-the-loop disambiguation step, not a sensory question.

**Expected frequency.** Path B and Q6 are expected to occur less often than earlier design
work assumed. See §8 on the epistemic status of that earlier assumption.

## 3. Output

```text
3 main
5 secondary
```

Superseding V0's 5 primary + 3 secondary. The main count aligns with the three items Q6
asks the user to select.

Overall direction remains in a separate `overall_profile` field and is not mixed into main
or secondary. This carries forward the owner-approved `OUT_SEPARATED` policy from R9
unchanged.

The output must not be described as a true-flavor probability or as an accuracy figure.
Scores remain uncalibrated decision scores.

## 4. Abstention

Abstention remains in the contract. What is constrained is its exposure in the interface.

- Exactly **one** question may carry a "none of the above" option.
- All other questions may carry at most an "uncertain" option.
- Uncertainty-semantics options must not proliferate across the interface.

Rationale: placing uncertainty-like options broadly in the frontend confuses the user's
perceptual judgement, and a user offered "not sure" everywhere will take it, yielding no
signal.

**Inference-layer withholding is unaffected.** The R9 abstention rule stands. Candidates
without sufficient evidence continue to be withheld regardless of what the interface offers.

## 5. Context and consistency

C0 and C1 are **stated by the user**, not inferred. They provide a soft candidate-space
prior and do not directly generate flavor labels.

Mouthfeel and texture terms act as **auxiliary verification**: after the user has stated
roast and preparation, they confirm or discriminate candidates against that stated context.
They do not infer context and they never appear as flavor output.

## 6. Retention and visibility

**Every keyword is retained in the system. Classification decides only where a term
operates, never whether it is kept.**

Three visibility tiers:

| Tier | Meaning |
| --- | --- |
| `FRONTEND` | may reach the user interface |
| `BACKEND` | operates in inference, never displayed |
| `RESEARCH_AND_TRAINING_ONLY` | fully isolated to the research and training layer |

Visibility is an axis independent of semantic role. A term has both.

### Semantic roles required beyond the current registry

The current registry holds only `NAMED_DESCRIPTOR`, `PROFILE_DIRECTION` and
`OTHER_NATIVE_MEASUREMENT`. The following are implied by V1 and are **not yet specified or
created**:

| Role | Tier | Notes |
| --- | --- | --- |
| `DEFECT_DESCRIPTOR` | RESEARCH_AND_TRAINING_ONLY | clustered, low-weight attachment to parent flavours |
| `CONTEXT_CONSISTENCY_CHECK` | BACKEND | mouthfeel and texture; verifies against stated C0/C1 |
| `ROAST_INFORMATION` | FRONTEND | roast level as a first-class concept |
| `COFFEE_KIND` | FRONTEND | species and variety |
| `RETAINED_NON_DESCRIPTOR` | RESEARCH_AND_TRAINING_ONLY | recorded, never emitted, no operational authority |

### Defect layer

Defects are grouped into clusters and attached to parent flavour concepts with a low score.

- **Never emitted.** No defect may reach main, secondary or `overall_profile`. This is an
  enforceable invariant and should carry a contract test.
- **Pruning authority only.** Association may reduce the candidate set. It must not drive
  ranking or precise inference. Candidate reduction and candidate ranking remain separable
  and separately auditable.
- Multi-attachment is permitted under that restriction.

### Term rulings carried forward

| Terms | Disposition |
| --- | --- |
| green, pungent | admitted as flavour descriptors |
| fatty, oily, waxy, creamy | `CONTEXT_CONSISTENCY_CHECK` |
| spicy | C1 evidence — incidental to light and medium roast |
| burnt | C1 evidence — attributed to dark roast |
| musty, rancid, sweaty, soapy, phenolic, sulfury, cheesy, cheese | `DEFECT_DESCRIPTOR` |
| pyrazine, aldehydic, ethereal | not percepts — research tier |
| fresh, clean, mild, coffee | `RETAINED_NON_DESCRIPTOR` |

## 7. What V1 does not decide

- The Option A / B / C architecture question. `owner_decision.json` stays pending.
- Whether training resumes. The training pause stands.
- Any individual R6 rule, concept id, or formal relation edge. None are created by this
  contract.
- The 46 category-C vocabulary terms individually. Only the policy clusters were ruled on.

## 8. Epistemic status of the Q4 / Q5 / Q6 design

**These are design decisions, not measurement-driven findings, and must not be cited as
evidence.**

The evolution from the prototype was produced by agent inference over R8 and R9 data
outputs. Those outputs came through the pipeline whose defects R12C documented: a discovery
layer that captured 0.75% of the licence-filtered addressable pool for its largest query,
admission gates that rejected 71.9% of detected tables through wrong-granularity keyword
tests, and outputs of which only 24.05% carried a direct evidence trace.

"The algorithm needs stronger correction and a fallback" and "the data feeding the algorithm
was defective" produce similar symptoms. Neither R12C nor the original inference can
separate them.

This does not make Q5 or Q6 wrong. Dynamic correction and a user-in-the-loop fallback may be
correct regardless. It means the underlying figures must be re-derived after the R12C
repairs before they can support the design in writing.

The owner's observation that path B and Q6 occur less often than earlier work assumed is
consistent with this concern.
