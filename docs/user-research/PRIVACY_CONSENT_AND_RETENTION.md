# Privacy, consent, and retention

## Current state

`PRIVACY_ACTIVATION_STATUS=PLANNED`

No live participant or product-event collection is implemented. This document
sets conditions for a future separately authorized pilot; it is not legal or
ethics approval.

## Data minimization

- Do not require name, email, precise location, employer, or account identity to
  complete a research session.
- Keep recruitment contact details separate from pseudonymous research data.
- Collect only event precision needed for a defined metric.
- Make free text optional and warn about accidental personal disclosure.
- Do not put raw participant data, recruitment lists, or consent records in Git.

## Consent layers

Consent should be separable for:

1. participation in the stated study;
2. audio/video/screen recording, if any;
3. quotation in research or public writing;
4. retention for follow-up analysis;
5. model development or evaluation; and
6. recontact.

Refusal of optional layers must not invalidate the core session where it remains
feasible.

## Pseudonymization and access

Use non-guessable session IDs. Store any recontact mapping separately with
narrower access. Log exports, analyst access, transformations, and deletion
actions. Pseudonymization reduces risk but is not anonymization.

## Retention schedule requirements

Before collection, define a period and deletion event for each domain:

- contact/recruitment records;
- signed or recorded consent evidence;
- raw audio/video or screen capture;
- moderated notes and optional free text;
- structured interaction events;
- coded insights; and
- aggregate, de-identified reports.

Do not invent durations in this planning pass. The activated protocol must state
them and explain any legal, research-integrity, or backup limitation.

## Withdrawal and deletion

Provide a participant-accessible route using a study/session code. Authenticate
requests proportionately without collecting new excessive identity data. Mark
the request, suspend downstream use, remove linked raw/derived rows where
possible, record completion, and disclose any already anonymous aggregate that
cannot be reversed.

## Release and model-use policy

- Raw free text, audio, video, and fine-grained events are restricted by default.
- Public reporting should be aggregate and reviewed for small-cell or quotation
  re-identification.
- General research consent does not automatically permit model training.
- Model-use permission does not automatically permit public release.
- A later model dataset must record purpose, feature exclusions, split rules,
  withdrawal handling, and rights/consent version.
