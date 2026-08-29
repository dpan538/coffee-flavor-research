# Public writing and claim style

## Purpose

Public copy must make the project clear without collapsing evidence roles or
turning plans into results. Current claims must resolve to a governed receipt,
generated fact, executable test, or clearly labelled design contract.

## Status vocabulary

Use only:

- `VALIDATED` — evidence was tested against a defined contract;
- `IMPLEMENTED` — the capability exists in the repository or interface;
- `IN_PROGRESS` — active work is incomplete;
- `PLANNED` — scoped but not implemented;
- `BLOCKED` — a named gate prevents progress;
- `HISTORICAL` — accurate for an earlier stage;
- `NOT_STARTED` — no work product or empirical run exists; and
- `NOT_APPLICABLE` — the status does not apply.

Avoid “basically complete,” “almost ready,” “AI-ready,” and “good enough.”

## Preferred expressions

- evidence-grounded
- research-grounded
- adaptive sensory reference
- candidate ranking
- professional sensory evidence
- source-native descriptor
- consumer-language evidence
- user-research-informed (only after actual research evidence exists)
- provenance-aware PostgreSQL knowledge base
- explicit uncertainty and abstention
- ML/DL-ready architecture
- staged model-readiness program
- current prototype
- validated database foundation
- planned or not-yet-trained model
- behavioral relevance signal
- perception-compatible reference

## Evidence-dependent or prohibited expressions

Reject or qualify:

| Expression                                        | Why it fails now                                  | Acceptable alternative                                       |
| ------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------ |
| “AI tastes coffee”                                | Anthropomorphizes a system with no sensory access | “Ranks sensory references from provided context and answers” |
| “detects the true flavor”                         | Erases perception and uncertainty                 | “offers perception-compatible references”                    |
| “predicts exact tasting notes”                    | No exact-label task or evidence                   | “future candidate-ranking task”                              |
| “expert-level accuracy”                           | No expert benchmark or model run                  | name the actual evaluation contract                          |
| “trained on 26,000 professional coffees”          | Publication rows are not labels or coffees        | “acquisition-scale publication rows”                         |
| “26,000 professional labels”                      | Collapses source population into label truth      | name descriptor assertion and review universe                |
| “fully verified global sensory dataset”           | Coverage and rights remain incomplete             | “reconciled source census”                                   |
| “consumer reviews prove the coffee tastes like X” | Consumer language is not professional truth       | “consumer wording shows how people communicate”              |
| unresolved fields called P1/P2                    | Provenance is not established                     | “provenance unresolved”                                      |
| “production-ready ML”                             | No trained or evaluated model                     | “staged ML-readiness program”                                |
| “deep-learning system”                            | No deep model was run                             | “deep-learning evaluation is planned behind gates”           |
| unqualified “production PWA”                      | Deployment and production monitoring are absent   | “installable deterministic PWA prototype”                    |
| “real-time personalization”                       | Not implemented                                   | “future adaptive interaction”                                |
| “complete”                                        | Stages remain blocked                             | name the exact validated scope                               |

## Four evidence tracks

1. **Professional sensory evidence** may ground normalization and evaluation
   only when tier, provenance, review, rights, and gate conditions pass.
2. **Industry and commercial language** supports vocabulary and mismatch
   research; it is not automatically professional ground truth.
3. **Consumer language** supports familiarity, ambiguity, comprehension, and UX
   research; it cannot become a core professional label.
4. **First-party user research and interaction data** may support behavioral
   relevance and product evaluation after consent; it is not objective flavor
   truth.

## Quantitative claim workflow

Quantitative claims in `README.md`, `PORTFOLIO.md`, and the public status route
must use a `claim: CLAIM_ID` marker and have a row in
[`PUBLIC_CLAIMS_REGISTER.tsv`](./PUBLIC_CLAIMS_REGISTER.tsv). The row points to
the authoritative evidence and states any qualification. Generated values come
from `scripts/generate-public-project-status.py`; public prose should not create
an independent data total.

## Current-versus-future test

Before writing a capability, ask:

1. Is there a repository artifact proving implementation?
2. Is there an executable or independently inspectable validation receipt?
3. Does the claim require user evidence, model results, rights, or expert review
   that is currently absent?
4. Could a reader mistake acquisition volume for qualified labels?
5. Is uncertainty or abstention preserved?

If the first two answers are no or the third is yes, label the capability
`PLANNED`, `BLOCKED`, or `NOT_STARTED`.
