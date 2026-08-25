# Constraint coverage

The 35-entry semantic registry complements, rather than replaces, the full
PostgreSQL catalog inventory.

| Enforcement source    | Rule count | Meaning                                                     |
| --------------------- | ---------: | ----------------------------------------------------------- |
| PostgreSQL constraint |         15 | row/key/domain failure                                      |
| PostgreSQL trigger    |         10 | multi-row, lifecycle, promotion or freeze failure           |
| audit query           |          2 | inventory and provenance closure                            |
| CI gate               |          4 | repository/rebuild/non-inference closure                    |
| curation policy       |          4 | bilingual, future-round, tree and additional-range judgment |
| **Total**             |     **35** | —                                                           |

Category coverage is exposed by `audit.v_round3f_constraint_coverage` with rule,
database-enforced, audit-enforced, documentation-only, negative-test, passing
and unresolved counts. Thirty-three rules are `ENFORCED`; two packaging/review
rules are `DOCUMENTED_ONLY`. No registered rule is currently
`MISSING_BUT_ENFORCEABLE` or `UNRESOLVED`.

The Round 3F negative suite contains 18 exact failures and passes. Conceptual
rules are tested through a governed rejection function or retained as curation
policy where no honest database operation exists.
