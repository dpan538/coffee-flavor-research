# Draft data-retention plan — not approved

| Data class                                   | Proposed location                   | Proposed retention | End action                        |
| -------------------------------------------- | ----------------------------------- | ------------------ | --------------------------------- |
| contact, eligibility and payment             | separate restricted system          | `TBD`              | verified deletion                 |
| signed consent and withdrawal linkage        | restricted governance store         | `TBD`              | archive or delete per approval    |
| coded raw sensory responses                  | encrypted research store            | `TBD`              | delete or controlled archive      |
| audit/import records                         | restricted append-only audit store  | `TBD`              | controlled archive                |
| consented public de-identified release       | named versioned public repository   | persistent         | correction/version policy applies |
| non-consented or rejected public-export rows | private only; excluded from release | `TBD`              | verified deletion                 |

The final plan must specify jurisdiction, backup copies, key ownership,
destruction verification, public repository/license and post-release correction
limits. No participant record currently exists.
