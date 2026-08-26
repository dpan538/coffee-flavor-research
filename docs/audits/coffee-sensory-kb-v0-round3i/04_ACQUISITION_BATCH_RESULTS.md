# Acquisition batch results

Four targeted batches were completed and pushed before freeze engineering.

| Batch                                          | Sources reviewed/admitted | New independent families |   Rows | Documents | Unique gain | `zh-Hans` gain | Relationship gain | Result after batch                                                   |
| ---------------------------------------------- | ------------------------: | -----------------------: | -----: | --------: | ----------: | -------------: | ----------------: | -------------------------------------------------------------------- |
| `round3i.batch1.evaluation-language`           |                       3/3 |                        3 | 11,444 |     3,289 |          18 |              0 |                 0 | Contemporary family and document gates pass.                         |
| `round3i.batch2.firstbloom-language-expansion` |                       1/1 |                        0 |  1,058 |       840 |         952 |              0 |                 0 | Global expression minimum becomes reachable; `zh-Hans` remains open. |
| `round3i.batch3.zh-hans-language-closure`      |                       2/2 |                        2 |    253 |         8 |         249 |            249 |                 0 | All mandatory language gates pass.                                   |
| `round3i.batch4.relationship-depth`            |                       1/1 |                        0 |      1 |         0 |           0 |              0 |                 1 | Fourth cross-source range-evidence breadth preference passes.        |

The four batches reviewed seven role-specific source entries and admitted all
seven for their scoped roles. They represent six canonical origins because
Cotter is reused across language and relationship evidence. The broader
candidate register names 10 candidates; rejected or pending candidates do not
enter the batch gain totals.

Accordingly, `NEW_IMMUTABLE_SNAPSHOT_COUNT=7`: three evaluation snapshots, one
Firstbloom snapshot, two `zh-Hans` snapshots, and one Cotter relationship
source/version-role snapshot.

The evaluation and Firstbloom generators were reconciled against the complete
governed baseline rather than only the Round 2B pilot file. Five evaluation
terms (`astringent`, `bitter`, `burnt`, `rubber`, and `sour`) overlap canonical
lexical identities beyond the pilot overlaps, and Firstbloom's `musty` also
overlaps. Corrected global gains are 18 and 952, not 23 and 953.

The normalized evaluation batch receipt now explicitly records
`rows_added=11444`, `coverage_cells_added=0`,
`relationship_support_added=0`, and `access_blocked_count=0`. Its exact SHA-256
is `b1555abead882226d5fc48e28595003a2fc8728dfe00f28f21f1231b2507815e`.

Acquisition stop condition A is satisfied because every mandatory coverage
gate passes. Further broad acquisition is not warranted merely to close
preferred breadth. Rights-blocked and access-blocked rows are not converted
into artificial no-gain imports.
