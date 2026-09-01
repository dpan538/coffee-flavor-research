# Product task contract

The machine-readable contract is
`db/data/product-inference-v0/PRODUCT_TASK_CONTRACT.json`. It preserves the
current database-backed sequence: mandatory C0, mandatory seven-level C1,
mandatory adaptive Q1, conditional Q2–Q4, and exceptional Q5.

The Round 3N brief describes the ordinary target flow as “up to four” sensory
questions. That is consistent with Q1–Q4 in the approved contract; it does not
retire the separately governed exceptional Q5 escape hatch. The simulator
limits ordinary next-question selection to Q1–Q4 and records Q5 only as an
unvalidated exceptional maximum.

Inputs carry locale plus product, question-bank, and policy versions. Question
instances carry an axis, selected option IDs, and explicit unsure/no-selection
states. Observation states such as `NOT_REPORTED` are not user C0 choices.

Evidence precedence is explicit user answer, direct professional assertion,
direct structured context evidence, governed normalization/semantic evidence,
weak evidence-supported context prior, then neutral missing evidence. Context
cannot create a precise descriptor or override a clear answer. Scores are
uncalibrated decision scores, never probabilities.

The rights flag is intentionally scoped to public research simulation.
`PRODUCT_DEPLOYMENT` remains `UNKNOWN_NOT_AUTHORIZED` for every candidate.
