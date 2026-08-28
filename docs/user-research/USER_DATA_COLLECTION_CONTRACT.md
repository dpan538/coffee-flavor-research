# First-party user-data collection contract

## Status

`LIVE_COLLECTION_STATUS=NOT_STARTED`

This document defines a future minimum event model. It does not create a
collector, database table, tracking script, participant record, or authorization
to recruit. Activation requires separate ethics, consent, privacy, security,
retention, and purpose review.

## Data domains

### Consent and session envelope

| Field                          | Purpose                                     | Required? | Notes                                   |
| ------------------------------ | ------------------------------------------- | --------- | --------------------------------------- |
| `pseudonymous_session_id`      | join events within one session              | yes       | non-guessable; no direct identifier     |
| `consent_version`              | prove accepted notice                       | yes       | immutable for the session               |
| `study_or_product_mode`        | separate moderated research and product use | yes       | controlled vocabulary                   |
| `started_at`                   | session ordering                            | yes       | minimize precision if not needed        |
| `completed_at`                 | completion and time                         | optional  | null for drop-off                       |
| `withdrawal_or_deletion_state` | govern removal                              | yes       | active, requested, completed, exception |

### Context and question events

| Field                             | Purpose                | Interpretation                          |
| --------------------------------- | ---------------------- | --------------------------------------- |
| `C0_family`                       | preparation context    | product feature, not sensory truth      |
| `C0_source_wording`               | wording shown/selected | versioning and comprehension            |
| `C1_category`                     | roast context          | user-reported category                  |
| `C1_confidence`                   | uncertainty            | do not infer from descriptors           |
| `question_id`, `question_version` | prompt identity        | reproducibility                         |
| `question_order`                  | exposure order         | burden and leakage analysis             |
| `answer`                          | selected response      | behavioral observation                  |
| `answer_latency_ms`               | interaction burden     | coarse/granular policy must be approved |

### Candidate and outcome events

| Field                      | Purpose                  | Interpretation                         |
| -------------------------- | ------------------------ | -------------------------------------- |
| `candidate_set_version`    | exact candidate universe | reproducibility                        |
| `candidate_exposure`       | what was shown           | required to interpret selection        |
| `primary_candidate_rank`   | displayed primary rank   | exposure, not truth                    |
| `secondary_candidate_rank` | displayed secondary rank | exposure, not truth                    |
| `candidate_selected`       | behavioral choice        | possible relevance label after consent |
| `none_of_these_selected`   | abstention               | valid product outcome                  |
| `result_confidence`        | self-report              | not calibrated sensory probability     |
| `optional_free_text`       | participant wording      | high privacy/re-identification risk    |
| `package_note_comparison`  | agreement/disagreement   | perception comparison, not correctness |

## Separation of roles

- **Identity data:** should not be required; any recruitment contact list must be
  stored separately with an independent deletion schedule.
- **Research session data:** protocol, consent, task, moderated observations,
  and session-level outcomes.
- **Product analytics:** minimal operational events, disabled by default until a
  lawful basis and notice are active.
- **Optional free text:** restricted, reviewed for identifiers, and excluded
  from public exports by default.
- **Model features:** a governed subset derived only after feature, rights,
  purpose, and leakage review.
- **Evaluation labels:** task-specific behavioral or comprehension outcomes;
  never silently reclassified as professional flavor truth.

## Consent and lifecycle requirements

- explain purpose, procedures, recording, optionality, risks, retention, and
  contact/deletion route in accessible language;
- make research participation and model-use consent separable;
- permit withdrawal without requiring a reason;
- map pseudonymous sessions to deletion requests through a protected mechanism;
- document retention by data domain, then delete or irreversibly aggregate;
- avoid public raw event or free-text release by default;
- use aggregate reporting with minimum-cell and re-identification review; and
- record any lawful retention exception without silently marking deletion done.

## Activation gate

Collection remains blocked until all are true:

```text
APPROVED_PROTOCOL
AND APPROVED_CONSENT_NOTICE
AND PRIVACY_AND_RETENTION_PLAN
AND SECURE_STORAGE_AND_ACCESS_CONTROL
AND WITHDRAWAL_AND_DELETION_TEST
AND SEPARATELY_AUTHORIZED_RECRUITMENT
```
