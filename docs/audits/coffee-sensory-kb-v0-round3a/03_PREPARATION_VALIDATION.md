# Preparation validation

## Inventory

```text
PREPARATION_FAMILY_COUNT=8
PREPARATION_LEAF_COUNT=22
RECOMMENDED_C0_TOP_LEVEL_CHOICE_COUNT=8
UNRESOLVED_PREPARATION_LABEL_COUNT=2
```

## Required semantic cases

| Case                   | Representation                                             | Test result |
| ---------------------- | ---------------------------------------------------------- | ----------- |
| Flat white / latte     | distinct leaves; same espresso-plus-milk parent            | PASS        |
| Americano / long black | distinct leaves; explicit symmetric `related_to`           | PASS        |
| Long black / cold brew | distinct identities and families; no collapse edge         | PASS        |
| AeroPress              | one identity with two broader parents                      | PASS        |
| Unknown preparation    | observation status; no taxonomy value                      | PASS        |
| Milk context           | preparation/addition context only; no `kb` attribute       | PASS        |
| Flavored syrup         | strong-interference addition; no sensory concept promotion | PASS        |

Every active preparation identity has at least one source support row. All 26 stored preparation relations carry a direct source version, assertion role, and locator.

## Negative cases

- reverse AeroPress/hybrid edge creates a cycle and fails `preparation_relation_acyclic_ck`;
- self-parent fails `preparation_relation_no_self_ck`;
- a competing exact Americano expression mapping to long black fails `context_expression_mapping_ambiguity_ck`;
- an addition row attached to explicit `absent` status fails `observation_addition_presence_ck`;
- deleting a source version referenced by preparation support fails `preparation_concept_support_source_fk`.

All cases run inside rolled-back transactions. Expected SQLSTATE/constraint diagnostics are asserted in `db/tests/round3a_negative.sql`.
