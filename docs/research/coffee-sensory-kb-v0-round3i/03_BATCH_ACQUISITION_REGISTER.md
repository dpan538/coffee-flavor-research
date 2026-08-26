# Batch acquisition register

This register is initialized before the first Round 3I import. Counts become
final only after the corresponding generated artifacts and database migration
pass their hash, rights, privacy, and independence checks.

| Batch | Targeted gap | Named sources under review | Intended count boundary | Initial state |
| --- | --- | --- | --- | --- |
| `round3i.batch1.research-language` | contemporary families and documents | Cotter v4; Bollen v1; Vezzulli Table 2 | three independent origins; evaluation records only | `TARGETED` |
| `round3i.batch2.firstbloom-long-tail` | unique normalized expressions | Firstbloom commit `a6cb0026…` | existing family; only previously uncaptured release IDs and consensus-reviewed phrases | `TARGETED` |
| `round3i.batch3.zh-hans` | source-authored Simplified Chinese | open Chinese publications/datasets with explicit reuse terms | independent origins; no translations | `TARGETED` |
| `round3i.batch4.evidence` | preferred context/relationship depth | lane A–F residual candidates | material coverage gain only | `CONDITIONAL` |

For each completed batch, append an immutable result containing:

- `BATCH_KEY`
- `TARGETED_GAP`
- `NAMED_SOURCES_REVIEWED`
- `SOURCES_ADMITTED`
- `SOURCE_FAMILIES_ADDED`
- `ROWS_ADDED`
- `DOCUMENTS_ADDED`
- `UNIQUE_EXPRESSIONS_ADDED`
- `ZH_HANS_EXPRESSIONS_ADDED`
- `COVERAGE_CELLS_ADDED`
- `RELATIONSHIP_SUPPORT_ADDED`
- `RIGHTS_BLOCKED_COUNT`
- `ACCESS_BLOCKED_COUNT`
- the readiness result after the batch

No batch may split one origin into artificial families or silently revise the
pre-acquisition target.
