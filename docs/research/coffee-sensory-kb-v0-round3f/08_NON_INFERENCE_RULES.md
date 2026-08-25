# Non-inference rules

Fourteen active rules are registered in `audit.forbidden_inference_rule`.

| Source fact               | Forbidden claim              |
| ------------------------- | ---------------------------- |
| same range                | synonym                      |
| same range                | hierarchy                    |
| same range                | sensory neighbour            |
| co-occurrence             | sensory neighbour/similarity |
| frequency                 | sensory validity             |
| frequency                 | canonical promotion          |
| range membership          | probability                  |
| question target           | validated question           |
| literal translation       | bilingual equivalence        |
| source absence            | negative association         |
| text candidate            | mandatory canonical concept  |
| one range membership      | exclusive membership         |
| context eligibility       | measured context effect      |
| two pairwise associations | transitive association       |

The database rejects writeable forms (promotion, exclusivity, probability,
question status, model input and canonical mutation). The CI negative suite
calls the governed rejection function for conceptual inference paths that have
no legitimate storage operation. Curation policies remain necessary for human
claims in prose.

`FORBIDDEN_INFERENCE_RULE_COUNT=14`

`FORBIDDEN_INFERENCE_TEST_PASS=true`
