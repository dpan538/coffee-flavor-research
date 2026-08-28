# Coffee Flavor Atlas — portfolio overview

## Project in one sentence

Coffee Flavor Atlas is an evidence-grounded mobile-first web prototype that
investigates whether a short, low-burden interaction can help ordinary coffee
drinkers translate broad perceptions into understandable professional sensory
references.

## The user problem

People often perceive a real difference between coffees but lack the vocabulary
to name it. Professional descriptors may be unfamiliar; package notes may feel
like answers the user is expected to reproduce; full tasting forms can turn a
curious moment into an exam. The project treats that gap as a product and
research problem, not as evidence that a user's perception is wrong.

## Target users

The primary audience is the curious café customer, home brewer, beginner
specialty-coffee drinker, or anyone comparing a personal impression with a bean
or menu card. Professional cuppers are relevant evidence stakeholders, not the
primary product user.

## Research questions

Can a small number of questions improve descriptive specificity without
suggestion bias? How much do preparation and roast context help? When should an
explicit sensory answer override a context prior? Can people understand a
ranked set of five primary and three secondary references, and when do they
prefer “none of these”? <!-- claim: PRODUCT_INTERACTION_CONTRACT -->

## Product concept

The intended journey collects preparation (C0) and roast (C1), asks one
mandatory adaptive question and up to four more only while useful, then offers
perception-compatible references for comparison, vocabulary learning, and
memory. Context remains a soft prior. Uncertainty, abstention, and disagreement
with package language remain valid outcomes.

The current interface implements a bilingual atlas, search and filtering,
descriptor detail, comparison, and a methodology/status surface. The adaptive
question policy and ranked output are designed but not trained or calibrated.

## What the project built

- a mobile-first React Router and Vite interface with schema-validated pilot
  descriptors;
- a provenance-aware PostgreSQL knowledge base for concepts, observations,
  evidence, context, review, rights, calibration, model experiments, and audit;
- deterministic lexical and typed-relationship retrieval with abstention;
- preparation/roast and low-burden adaptive-interaction contracts;
- professional-source discovery, duplicate/publication-layer controls, and
  descriptor-first acquisition receipts;
- fail-closed human-review evidence binding; and
- a reproducible research, CI, documentation, and public-claim verification
  system.

Contribution history does not resolve human versus automated or collaborative
scope, so this overview uses project-centric language. See the
[contribution-scope review](./docs/portfolio/CONTRIBUTION_SCOPE_REVIEW.md).

## Research methods

The work combines desk research, standards and source auditing, corpus and
schema design, data-rights review, source-specific parsing, duplicate forensics,
product semantics, protocol design, deterministic retrieval evaluation, and
planned human-centered research. Planned interviews and usability sessions are
not presented as completed fieldwork. Current counts remain zero.

<!-- claim: USER_INTERVIEW_COUNT --> <!-- claim: USER_USABILITY_COUNT -->

## Database and data-engineering work

The database distinguishes canonical knowledge from source-native observations,
and both from model inferences. Its frozen inventory includes 130 canonical
concepts and 92 active sensory attributes. <!-- claim: DATABASE_CANONICAL_CONCEPTS -->

<!-- claim: DATABASE_ACTIVE_SENSORY --> The implementation has 60 forward

migrations. <!-- claim: DATABASE_MIGRATIONS --> Source file hashes, bounded
locators, rights dimensions, evidence tiers, effective record identity,
publication layers, repeated preparation services, review lineage, and
model-eligible universes are represented explicitly.

## User-feedback and language-mining work

The project defines four separate tracks: professional sensory evidence;
industry and commercial language; consumer language; and future first-party
research/interaction data. Consumer reviews may illuminate vocabulary,
familiarity, ambiguity, expectation, and question wording. They do not supply
core professional label truth. Interaction choices may later become behavioral
relevance signals only after consent, privacy, rights, and evaluation gates.

## Important negative findings

The acquisition census contains 848 artifacts and 26,515 staged publication
rows. <!-- claim: ACQUISITION_ARTIFACTS --> <!-- claim: ACQUISITION_STAGED_ROWS -->
Those totals did not produce an equivalent professional descriptor universe.
Scores, rankings, blank forms, duplicated publications, repeated services, and
consumer-heavy sources could not be relabelled as professional sensory truth.

The descriptor-first pilot admits 140 assertions, de-inflated to 139 assertion
observations and 137 record-level unique observations.

<!-- claim: PILOT_ADMITTED_ASSERTIONS --> <!-- claim: PILOT_DEINFLATED_ASSERTIONS -->
<!-- claim: PILOT_RECORD_UNIQUE --> It yields 508 within-record pair events,

which are association evidence rather than independent coffee labels.

<!-- claim: PILOT_PAIR_EVENTS --> Current reviewed professional,

human-confirmed, and model-eligible counts remain zero.

<!-- claim: REVIEWED_PROFESSIONAL_ASSERTIONS -->
<!-- claim: HUMAN_CONFIRMED_ASSERTIONS --> <!-- claim: MODEL_ELIGIBLE_ASSERTIONS -->

This is a useful research outcome: the assumed scale was tested, the evidence
grain failed, and the system was redesigned around auditable descriptor
assertions and fail-closed review.

## ML/DL readiness strategy

No model has been run. <!-- claim: MODEL_RUN_COUNT --> Deterministic retrieval is
the current baseline. Future tasks are separated into descriptor normalization,
five-plus-three candidate ranking, association estimation, adaptive question
selection/stopping, and consumer-language comprehension. Each task requires its
own labels, rights, split groups, metrics, abstention behavior, and deployment
interpretation.

Interpretable statistical methods come before learning-to-rank, embeddings,
neural reranking, or policy learning. Coffee identity, source family, edition,
mirror, repeated service, review batch, and user identity must be grouped to
prevent leakage. A complex model advances only if it beats the simpler baseline
on held-out evidence and satisfies rights and label gates.

## Current prototype status

- **IMPLEMENTED:** responsive atlas and comparison prototype, deterministic
  retrieval foundations, governed PostgreSQL schema, migrations, tests, and
  public status generation.
- **VALIDATED:** database reconstruction and invariants recorded by Round 3M;
  frontend checks and governed artifact contracts.
- **PLANNED:** installable/offline PWA shell and first-party user study.
- **BLOCKED:** model tasks that require reviewed, rights-cleared evidence and
  grouped evaluation data.
- **NOT_STARTED:** statistical, ranking, embedding, neural, and adaptive-policy
  model runs.

## Current limitations

The frontend uses a small project-curated descriptor pilot and is not a live
PostgreSQL client. No participant data exists. No calibrated question policy,
sensory probabilities, or model performance claim exists. Rights uncertainty
and absent qualified review prevent current model eligibility. The app is a
mobile-first web prototype, not an implemented installable PWA.

## Next validated step

The strongest next evidence step is a separately authorized, consented user
research pilot or continued rights-cleared professional descriptor review. A
minimum PWA shell is also separable frontend work. A model baseline should wait
until a task has enough governed labels, rights, and leakage-safe splits.

## Read more

- [Try and explain the current interface](./docs/portfolio/DEMO_SCRIPT.md)
- [Long-form human-centered case study](./docs/portfolio/CASE_STUDY.md)
- [Research and correction timeline](./docs/portfolio/PROJECT_TIMELINE.md)
- [User-research program](./docs/user-research/USER_RESEARCH_OVERVIEW.md)
- [ML readiness matrix](./docs/ml/ML_DATA_READINESS_MATRIX.md)
- [Current generated status](./PROJECT_STATUS.md)
- [Authoritative technical evidence](./docs/audits/INDEX.md)
