# Remote CI

Promotion policy requires both feature-branch jobs—`Format, typecheck, test,
and build` and `PostgreSQL 17 ontology and corpus gates`—to pass at the final
feature SHA before a fast-forward-only update of `main`. The same two jobs must
then pass for the promoted main SHA.

Run identities and final booleans are reported in the release receipt after
the immutable CI results exist. No force push is permitted.
