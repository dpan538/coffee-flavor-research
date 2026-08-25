# Calibration research questions

## Primary questions

1. Does a soft C0/C1 prior improve candidate usefulness and ranked reference
   quality over answers alone without suppressing explicit perceptions?
2. Which eligible Q1 maximizes useful discrimination for a context and
   candidate region?
3. What marginal benefit does Q2, Q3, Q4, or exceptional Q5 provide after the
   preceding answers?
4. Which stopping rule reduces burden without materially degrading the 5 + 3
   candidate set?
5. How often and how successfully does explicit user evidence override weak
   context support?
6. How sensitive is the result to an incorrect C0 or C1 selection?
7. Do black and milk modes require separate policies?
8. How stable are reference observations and ordinary-user answers across
   repeats, expertise, and language?

## Falsifying outcomes

The context layer is not justified if it adds no held-out ranking/usefulness
benefit, increases unsafe context conflict, or prevents coherent overrides. A
question is not justified if its marginal information or candidate benefit is
negligible relative to burden. Q5 should be removed if it rarely resolves
remaining ambiguity.

## Current estimability

All primary calibration effects are `NOT_ESTIMABLE` before real observations.
Dry-run fixtures test mechanics only.
