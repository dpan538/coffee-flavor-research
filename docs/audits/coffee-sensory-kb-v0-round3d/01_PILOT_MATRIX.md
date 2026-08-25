# Pilot Matrix

Status: deterministic and frozen.

- Generator: `db/scripts/generate-round3d-pilot.py`
- Seed: `coffee-context-calibration-minimum-pilot-20260825-v1`
- Lots: 2 planned physical materials
- Roast batches: 14, covering all 7 C1 labels for each lot
- Preparation conditions: 7, including one separately paired milk condition
- Condition cells: 66, each with 2 planned independent beverage replicates
- Planned beverage samples: 132

The three full families cross both lots with all seven roast labels. Four
anchor families cross both lots at light, medium, and dark. This preserves
same-coffee cross-condition comparison without asserting equal roast distance
or a causal flavor effect.

```text
MATRIX_SHA256=dbd56b90672e00af5fe17a4d8c2c50b996d020a29e39dce04e9bd752de6d356b
PROTOCOL_SHA256=4c759fcae812203c40394d1f510e93c4a83430a3dfb298e832b5ffc49f5924ad
MATRIX_VALIDATION_PASS=true
```
