# Schema-freeze results

Round 3I adds four forward migrations after the immutable 45-migration Round 3H
checkpoint:

| Migration                                           | Purpose                                                                                                                                                                                           |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `045_round3i_research_database_freeze_contract.sql` | Language family/source/document/expression/occurrence governance, dual-review evidence, release lifecycle, row-hashed members, artifact/surface registries, attestation, and immutability guards. |
| `046_round3i_language_and_evidence_seed.sql`        | Deterministic import of the three language batches and one Cotter relationship claim.                                                                                                             |
| `047_round3i_current_surfaces.sql`                  | Eight approved read views, a current-surface registry view, and post-attestation DDL guards.                                                                                                      |
| `048_round3i_research_database_freeze_seed.sql`     | Freeze-candidate seed, source row accounting, 11 artifact registrations, updated readiness calculation, research-database freeze gate, and final hard-gate assertion.                             |

Total migration count after Round 3I is 49. Migrations `000`--`044` remain
protected by `db/migration-baselines/round3h.sha256`; no historical migration is
edited.

The new language layer enforces:

- one independent family per canonical origin;
- exact source/version/license/privacy/file-manifest annotation;
- source-to-document and document/expression-to-occurrence foreign keys;
- unique source-row and normalized-expression identities;
- no machine-translated, artificial, preparation, or roast count inflation;
- two independent Firstbloom review passes over a hash-bound candidate;
- raw and derivative export no broader than source rights; and
- immutable frozen documents and attested release members.

The release layer registers eight `CURRENT_APPROVED` views and eight
`DEPRECATED_RESEARCH` historical views. It requires 11 verified artifact hashes
and a complete row-hashed release membership before final attestation. The
candidate lifecycle is separate from exact-main `FROZEN`; the annotated tag
target and main SHA must match, while the tag object must remain distinct.

`audit.run_research_database_freeze_gate()` exposes key, required, observed,
passed, severity, evidence path, and limitation. Hard failures block the
candidate; preferred failures remain visible. Migration 048 also captures a
Round 3I execution baseline for model runs, model versions, and embedding
configurations. A hard `0/0/0` delta gate verifies that none were added, while
row triggers prohibit later model-run or model-version creation or mutation
once the Round 3I release row exists.

External reproducibility is deliberately not self-attested by a migration. An
immutable attestation row must record exactly two PostgreSQL 17 rebuilds, 11
matching freeze artifacts, and equality with the committed artifacts before the
final release attestation can be inserted. Artifact rows are immutable and one
freeze version cannot bind to two manifest hashes.

| Receipt field              | Current audit value                                     |
| -------------------------- | ------------------------------------------------------- |
| Forward migration count    | 4                                                       |
| Total migration count      | 49                                                      |
| Approved current views     | 8                                                       |
| Deprecated research views  | 8                                                       |
| New relational constraints | 71 from migration 044 to 048                            |
| New triggers               | 33: 31 table triggers plus 2 event triggers             |
| Schema integrity pass      | true locally; exact-candidate 35-test CI still required |

The static design review and executable schema suite pass. Migration 048 now
contains the real artifact hashes and the executed local PostgreSQL 17 suite
returns `DATABASE_TEST_PASS=true` with 33 Round 3I core rejection tests. Two
explicit language-closure fixtures were then added, bringing the final source
suite to 35; exact-candidate CI must bind the 35/35 receipt. Release
reproducibility remains separate
from the migration: two clean PostgreSQL 17 rebuilds now match, and their
external receipt must be supplied during final release attestation rather than
seeded as self-certification.

`NEW_CONSTRAINT_COUNT=71` counts net-new relational `pg_constraint` entries in
the governed schemas and excludes ordinary triggers and constraint-trigger
catalog aliases. `NEW_USER_TRIGGER_COUNT=31` counts non-internal `pg_trigger`
rows; `NEW_EVENT_TRIGGER_COUNT=2` is separate, so `NEW_TRIGGER_COUNT=33` and
`NEW_CONSTRAINT_AND_TRIGGER_COUNT=104`. This reports implemented integrity
scope; it is not used as a quality target.

The catalog receipt is:

| Catalog measure                                      | Migration 044 | Migration 048 | Delta |
| ---------------------------------------------------- | ------------: | ------------: | ----: |
| Relational `pg_constraint` (`contype <> 't'`)        |         1,483 |         1,554 |    71 |
| Non-internal table `pg_trigger`                      |           148 |           179 |    31 |
| User event triggers                                  |             0 |             2 |     2 |
| Constraint-trigger catalog aliases, excluded from 71 |            14 |            19 |    +5 |

The two event triggers are the post-attestation DDL guards created by migration 047. They are counted separately from `pg_trigger`; the final PostgreSQL 17 CI
receipt will independently repeat this catalog query on the exact candidate.
