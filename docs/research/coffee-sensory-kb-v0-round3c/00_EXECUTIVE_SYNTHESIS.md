# Round 3C executive synthesis

## Decision

`SUFFICIENT_PUBLIC_CALIBRATION_DATASET=false`

Ten candidate resources were reviewed and actual files were inspected where
lawful and accessible. Three rights-cleared resources provide reusable partial
evidence, but none supports the complete calibration task. Combining
incompatible protocols does not create a defensible crossed dataset.

Round 3C therefore freezes an original public calibration-dataset design,
adaptive context/question architecture, selected minimum pilot, analysis plan,
ethics/privacy gates, and forward-only PostgreSQL contract. It collects zero
human observations.

## Architecture

```text
C0 + C1 soft context support
-> adaptive Q1
-> candidate update
-> stop or conditional Q2-Q4
-> exceptional Q5
-> 5 primary + 3 secondary candidate references
```

Preparation and roast do not directly generate flavor and cannot hard-delete a
descriptor. Strong explicit user evidence may override a weak context prior.

## Selected minimum pilot

- two coffee lots;
- fourteen roast batches covering all seven project roast categories per lot;
- seven C0 families, with stovetop/boiled explicitly deferred;
- 66 condition cells and two independent beverage replicates;
- 132 beverage samples;
- 12 reference sensory assessors and 60 ordinary users; and
- separate calibration and product-simulation modes.

This scale tests feasibility and data mechanics. It is not powered for
production cell-level calibration.

## Human-participant gate

```text
HUMAN_PARTICIPANT_ETHICS_REQUIRED=true
INSTITUTIONAL_APPROVAL_STATUS=NOT_OBTAINED
PUBLIC_DATA_CONSENT_REQUIRED=true
```

Round 3D may implement engineering dry runs. It may not recruit, taste, or
collect real observations until ethics/approval, consent, and public-release
rights gates are all true.

## Non-claims

Round 3C does not create a public sensory dataset, estimate context effects,
calibrate question information gain, validate an adaptive policy, or show that
preparation and roast predict flavor.
