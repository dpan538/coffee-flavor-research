# Round 3J global stop-rule decision

The machine-readable decision is
`db/data/round3j/global_stop_rule_decision.tsv`.

## Preserved result

The original 17-candidate register, outcome ledger, four acquisition batches,
and `CONDITION_B_MET_STOP_ACQUISITION` result retain their exact meanings and
hashes. The completed regional coverage audit and its prepared dossiers also
remain unchanged.

## Superseded global effect

Regional candidate coverage no longer blocks broad global acquisition. The
original chronological three-batch no-gain result cannot close unrelated
global source classes. Source classes A through I now govern search saturation.

```ini
ORIGINAL_STOP_RULE_PRESERVED=true
ORIGINAL_STOP_RULE_GLOBAL_EFFECT_SUPERSEDED=true
ROUND3J_REGIONAL_AUDIT_COMPLETE=true
ROUND3J_REGIONAL_DATA_ACQUISITION_COMPLETE=false
REGIONAL_SOURCE_FRAME_BLOCKS_GLOBAL_ACQUISITION=false
REGIONAL_REPRESENTATIVENESS_CLAIM=false
GLOBAL_FLAVOR_ACQUISITION_COMPLETE=false
```

A class closes only after its candidate-coverage gate and two consecutive
class-targeted batches with no material gain. Global acquisition closes only
when every class is closed, blocked, or saturated; no rights-cleared
high-yield source remains unprocessed; and all permission/commercial options
are documented. A regional deficit becomes `REGIONAL_COVERAGE_WARNING`, not a
global failure.
