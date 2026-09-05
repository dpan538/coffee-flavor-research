# Engineering disposition of independent GPT findings

The imported GPT review is independent feedback, not an owner decision. Its
original findings remain preserved in `GPT_BEHAVIOR_REVIEW.md` and the review
import ledger. No human acceptability cells were populated during fixes.

| Finding | Engineering change | Validation |
| --- | --- | --- |
| Accepted Q5 followed by early return prevented export | Acceptance records a click; completing five answers is a separate derived measure. Four-answer partial export remains valid and the eligible Q5 can be reopened. | Browser paths at 390, 768 and 1440px cover Q5 acceptance then early return and successful export, and a separate five-answer completion path. |
| Cancelling the outside-vocabulary flag retained its stop reason | On cancellation, derive the ordinary stop reason from the restored state, or record a participant-requested partial result. | Browser checkbox toggle and exported openSet/earlyStopReason assertions. |
| Export accepted fabricated question IDs and inconsistent counters | Replay catalog question order, semantic keys, presented and selected options, candidate sets, remaining axes, Q5 offer and visible tiers. Reject event/inference-answer divergence before serialization. | Negative unit tests alter IDs, flags, candidate sets and headline counts; complete browser downloads pass the same validator before a Blob is created. |
| Weak closed-none adjustment also withheld disputed results | Preserve numeric candidate support; explicitly document the additional conservative display guard. | Conflict and bounded-adjustment unit tests. Product suitability remains an owner-review item. |

The Node 24 browser-test worker process initially stalled during teardown after
all assertions. The suite completed normally with the local Node 22 test
runtime. This was a local verification-runtime issue; no CI workflow or
application dependency was changed to bypass a check. Static build and type
checks used the available bundled runtime that satisfies the frontend engine
requirement. The remote CI continues to use its existing Node 22 configuration.

There were no actual user sessions in this review. The next study still needs
the owner to review wording, closed-none conflicts, question stopping, result
tiers and the proposed formative thresholds.
