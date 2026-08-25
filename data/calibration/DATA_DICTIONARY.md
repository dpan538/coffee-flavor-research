# Data dictionary

The templates preserve separate material, execution, observation, interaction,
judgment, and deviation layers. Keys are stable public or pseudonymous codes;
blank values mean missing/not-yet-captured, never an inferred value.

| Template | Unit | Required linkage | Epistemic role |
| --- | --- | --- | --- |
| `coffee_lots.csv` | green lot | study, protocol | physical material |
| `roast_batches.csv` | roast batch | coffee lot, C1 | physical condition |
| `preparation_conditions.csv` | recipe condition | C0, protocol | physical condition |
| `beverage_samples.csv` | independent beverage | lot, roast, preparation, replicate | physical sample |
| `assessors.csv` | pseudonymous assessor | study, cohort, language | participant metadata |
| `sessions.csv` | sensory session | assessor, protocol | execution |
| `presentations.csv` | blinded serving | session, sample, order | randomized execution |
| `descriptor_responses.csv` | descriptor response | presentation, canonical concept | raw sensory observation |
| `dimension_responses.csv` | taste/tactile response | presentation, governed dimension | raw sensory observation |
| `question_responses.csv` | adaptive interaction | presentation, question/version/option | ordinary-user response |
| `candidate_judgments.csv` | candidate usefulness | presentation, concept, rank | evaluation judgment |
| `protocol_deviations.csv` | deviation | protocol/session/sample | quality record |

All observation templates require `record_origin_code`; real collection uses
`real_observation`, while engineering rows must use `DRY_RUN_FIXTURE` or
`TEST_FIXTURE`. Fixture rows are excluded from public observation counts and
analysis inputs.
