# Archive: the adaptive-question policy line (2026-08-24 → 2026-09-12)

Archived on 2026-09-12 by owner decision R3-D5 (`db/data/backend-sequential-model-v2/revisions/round3/owner_decisions_round3.json`).
Superseded by **[Flavor Vector Design V1](../../product/FLAVOR_VECTOR_DESIGN_V1.md)**: an 8-dimension flavor vector space,
a projection matrix, a set of coffee vectors and a cosine — no state machine, no proposition lattice, no training.

Nothing listed here is deleted or moved. Several artefacts are sha256 lineage inputs of committed manifests and the CI
still reproduces them; they are frozen, not extended.

## What the line was

Round 3C (2026-08-25) froze an adaptive-question product: a finite-state inference over a concept registry, questions chosen
by which axis best splits the remaining candidate set, propositions with declared extents and entailment, a 3+2+3 output
policy, and an offline 120-case policy checkpoint with an owner review packet. Round 2 (2026-09) rebuilt the inference as
`evidence_reader` → `proposition_lattice` → `inference_state_machine`. It worked; its ceiling was the reachable concept space
(15 concepts reachable, 36 of 56 registry words unreachable), not the algorithm.

## Archived documents

| Document | Was | Now |
|---|---|---|
| `docs/product/PRODUCT_CONTRACT_V0.md` | product-semantics source of truth (frozen 27d257c) | ARCHIVED banner; still a lineage input of `product-inference-v0` |
| `docs/product/PRODUCT_CONTRACT_V1.md` | draft, never approved | ARCHIVED banner |
| `docs/architecture/ADAPTIVE_CONTEXT_QUESTION_ARCHITECTURE.md` | question-selection architecture | ARCHIVED banner |
| `docs/decisions/CONTEXT_INTERACTION_DECISION_20260825.md` | Round 3C decision record | ARCHIVED banner |
| `docs/decisions/ROUND3_CONTEXT_CALIBRATION_ARCHITECTURE_20260825.md` | C0/C1 calibration architecture | ARCHIVED banner; the C0/C1 *data* (`db/data/round3m/C0_C1_EVIDENCE_RECEIPT.json`) is reused by V1 §2 |

## Archived scripts (frozen; ARCHIVED line added to each docstring)

`db/scripts/evidence_reader_round2.py`, `proposition_lattice_round2.py`, `inference_state_machine_round2.py`,
`output_generator_round2.py`, `generate-product-inference-v0.py`, `generate-product-inference-v02.py`,
`run-product-inference-v0.py`. Their data: `db/data/product-inference-v0/`, `db/data/product-inference-v0.2/`,
`db/data/backend-sequential-model-v2/revisions/round2/` (concept_extents.json and the round-2 findings).

## What carries over

- The concept registry (94 canonical `sensory.*` concepts) and the 83K corpus / semantic layer — V1 projects them.
- C0 (preparation family) and C1 (roast) as context; V1 adds C2 (variety + processing).
- Governance: per-dataset owner approval; scores are similarities, not probabilities; no training run; rights per purpose.
- The F19 lesson (a dead join read as "no evidence" for months): V1 §7 measures its signals end to end before trusting them.
