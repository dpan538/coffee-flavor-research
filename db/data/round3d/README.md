# Round 3D generated engineering pilot

`generated/` is produced by `db/scripts/generate-round3d-pilot.py` from the
Round 3C minimum feasibility design and the fixed seed
`coffee-context-calibration-minimum-pilot-20260825-v1`.

The package contains planned material identifiers, a 66-cell/132-beverage
matrix, unassigned cohort/session slots, deterministic blinded presentation
slots, conditional question-assignment envelopes, five conspicuous
`DRY_RUN_FIXTURE` mechanics cases, an abstaining baseline report, and an empty
three-way split inventory. It contains no recruited participant, physical
sample record, response, or sensory observation.

Run:

```bash
python3 db/scripts/generate-round3d-pilot.py
python3 db/scripts/validate-round3d-pilot.py
```

The validator regenerates and byte-compares the package before checking matrix
coverage, repeats, burden, randomization balance, question paths, fixture
separation, PII, and `NOT_ESTIMABLE` outputs.
