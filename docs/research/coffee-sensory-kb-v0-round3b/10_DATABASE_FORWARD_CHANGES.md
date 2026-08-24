# Database forward changes

Round 3B appends four migrations (`022`–`025`); migrations `000`–`021` are
unchanged and fingerprinted by the new Round 3A baseline manifest.

- `022` adds roast-scheme lifecycle/supersession metadata, preserves and
  freezes V0, creates/promotes V1, maps compatible historical categories, and
  publishes the current C0/C1 views and promotion guards.
- `023` adds governed source review/file/snapshot/raw-record, lexical rule,
  approval, benchmark, result, and context-statistic tables plus integrity and
  freeze triggers.
- `024` records exact source/version/license/file metadata, imports 4,817 raw
  records, 102 lexical rules, 102 frozen cases/results, and three statistic
  receipts, then freezes the snapshot.
- `025` preserves the historical Round 3A coverage/validator semantics and adds
  Round 3B coverage, source, metric, sufficiency, and expected-zero validation
  views/functions.

The current seven-level projection cannot be replaced by a five-level scheme
or one missing medium-light/medium-dark. V0 rows and frozen snapshot rows are
immutable. Context remains outside `kb.concept`, and the 130/92 ontology
inventory and Round 2B corpus remain unchanged.
