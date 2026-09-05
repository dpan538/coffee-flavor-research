# Product-task benchmark v0.2

Twenty-eight deterministic cases cover clear, partial, exploration-only,
low-information, extra-question, open-set, conflict, typed no-answer, context,
redundancy and rights scenarios. `result_json` is current policy behavior, not
an approved human answer key. Cases marked `ENGINE_POLICY_FIXTURE_NOT_USER_SESSION`
inject a bounded state or evidence condition for negative testing. They are not
claimed to be the deterministic next-question order of a live participant.
Cases marked `PARTICIPANT_FLOW_FIXTURE` follow or stop an executable flow; missing
context in these pure-engine cases is intentionally neutral. The UI requires C0
and either a roast selection or an explicit C1 unsure response.

`PRODUCT_TASK_OWNER_REVIEW_TEMPLATE.tsv` contains blank human decisions.
`PRODUCT_TASK_AGENT_REVIEW_TEMPLATE.tsv` has independent Claude, DeepSeek and GPT
rows. No Claude or DeepSeek execution is claimed by preparing those rows.
`PRODUCT_TASK_REVIEW_IMPORT.tsv` contains only actual imported agent reviews,
with source notes, scope, confidence limitations and blank owner decisions.

Review headline, expanded-main and exploration acceptability separately. Name
any candidate to remove or add, assess the extra-question offer and abstention,
and judge explanation comprehension. Provide a reason, reviewer and date. A
reviewer is not a participant. Do not aggregate agent votes into approval.

Regenerate policy cases and fresh blank templates with:

```bash
node scripts/generate-product-benchmark.mjs
```

Before regeneration, keep completed review files under a separate restricted
or owner-governed review path; do not fill the blank template in place. The
generator preserves the separately maintained review-import file. Human final
decisions require an explicit owner-authored import and are not synthesized by
the generator. All current owner decisions are blank.
