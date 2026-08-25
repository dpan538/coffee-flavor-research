# Architecture files

The following current documents carry the frozen Round 3C architecture:

- `docs/architecture/ADAPTIVE_CONTEXT_QUESTION_ARCHITECTURE.md`;
- `docs/decisions/ROUND3_CONTEXT_CALIBRATION_ARCHITECTURE_20260825.md`;
- `docs/data/COFFEE_SENSORY_CONTEXT_CALIBRATION_DATASET_SPEC_V0.md`;
- `docs/protocols/COFFEE_SENSORY_CONTEXT_CALIBRATION_PROTOCOL_V0.md`;
- `docs/product/PRODUCT_CONTRACT_V0.md`;
- `docs/methodology/METHODOLOGY_OVERVIEW.md`;
- `docs/research/RESEARCH_ROADMAP.md`;
- `README.md` and `docs/ARCHITECTURE.md`.

C0 and C1 are soft contextual support. Q1 is mandatory and context-adaptive;
Q2-Q4 are conditional and Q5 is exceptional. Explicit user perception may
override a weak prior. Context never hard-deletes a descriptor solely because
of roast or preparation. Output remains five primary plus three secondary
candidate references, not flavor probabilities.

No product frontend file changed in Round 3C.
