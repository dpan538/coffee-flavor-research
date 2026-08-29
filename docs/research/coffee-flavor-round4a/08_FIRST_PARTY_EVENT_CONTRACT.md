# First-party event contract

The future event schema includes pseudonymous participant/session IDs, consent
version and model-use consent, C0/C1, question identity/version/order, answer
and latency, candidate-set version/rank, selection/rejection/none-of-these,
confidence, completion, and withdrawal state.

Round 4A defaults are `NO_REMOTE_COLLECTION` and `LOCAL_ONLY_OR_NO_OP`. The UI
offers an explicitly synthetic local preview, export preview, and local
withdrawal/deletion path. It does not send research events over the network and
does not collect real participant data.

First-party behavioral ranking is post-initial-model. It is not required for
the initial professional-reference model, but is required for later
personalization and behavioral policy refinement.
