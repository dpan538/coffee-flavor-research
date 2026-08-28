# User insight traceability

## Rule

A proposed product decision is not a user insight until it has traceable user
evidence. Desk research and researcher hypotheses remain labelled as such.

## Insight record schema

| Field                         | Requirement                                                                                     |
| ----------------------------- | ----------------------------------------------------------------------------------------------- |
| `insight_id`                  | immutable identifier                                                                            |
| `claim`                       | bounded, falsifiable interpretation                                                             |
| `evidence_type`               | interview, usability observation, interaction metric, desk research, external language analysis |
| `source_session_or_artifact`  | pseudonymous session receipt or governed artifact locator                                       |
| `participant_or_source_scope` | who/what the evidence covers; no unnecessary identity                                           |
| `contradictory_evidence`      | linked conflicting observations or explicit none found                                          |
| `confidence`                  | low / medium / high with rationale, never statistical unless estimated                          |
| `product_implication`         | proposed decision, not automatic mandate                                                        |
| `status`                      | required research-state label                                                                   |
| `coded_by` and `coded_at`     | accountable synthesis event                                                                     |
| `supersedes_insight_id`       | versioned correction; do not overwrite history                                                  |

## Empty current register

| Insight ID | Claim                             | Evidence type | Source | Scope         | Contradiction | Confidence | Implication                         | Status         |
| ---------- | --------------------------------- | ------------- | ------ | ------------- | ------------- | ---------- | ----------------------------------- | -------------- |
| —          | No empirical user insight claimed | —             | —      | zero sessions | —             | —          | Run separately authorized fieldwork | NOT_YET_TESTED |

## Example structure, not an empirical finding

The following is a field-shape example only and must never be copied into the
findings register as evidence:

```text
insight_id: EXAMPLE_ONLY
claim: <bounded claim>
evidence_type: <type>
source_session_or_artifact: <governed locator>
participant_or_source_scope: <scope>
contradictory_evidence: <links>
confidence: <level + rationale>
product_implication: <proposal>
status: <research-state label>
```

Quotes require a source session, quotation consent, access policy, and faithful
transcription. Synthetic user quotes are prohibited.
