# Round 1 questionnaire intake

Eleven original files reconcile to ten distinct SHA-256 payloads. F003 and
F004 form D001. They do not establish two independent response events; this
does not identify two people as one person. Both files remain in the restricted
inventory. F003 represents the cluster in the primary analysis; exchanging it
for F004 cannot change any count. The eleven-file sensitivity is separate.

The response ledger contains all 220 primary question records, including F002
from the original Numbers submission. The third-party Numbers reader omitted
cells, including Q2; native Numbers export recovered all twenty responses.
The original Numbers file, its hash and the derivative export hash are retained.

F001 Q13 remains OPEN. Its three qualitative categories do not enter A–D
counts. Supplementary letter responses remain separate from primary answers.
Raw free text, notes, metadata, original filenames and participant-label
mappings exist only under the owner-controlled
`COFFEE_FLAVOR_USER_RESEARCH_ROOT`, outside Git. The repository exposes codes,
hashes and restricted pointers only. Participant IDs are intake pseudonyms,
not verified identities. The user authorized this coded public-safe surface;
raw responses are not relicensed or redistributed.

The supplied analytical aid matches all 80 recomputed A–D counts. Its claim of
repeated single-digit note values was not reproducible in these original
files. Zero such note values were observed. The anomaly register includes this
unverified claim, the Numbers extraction issue, the open primary response,
two supplementary letters and one explicit nonresponse marker: six entries.

`COFFEE_WEEKLY_OR_MORE_COUNT` is a conservative count of Q1 A/B, which guarantee
at least twice weekly. Q1 C says fewer than twice weekly and may include once
weekly. Therefore 9/10 is a lower bound for weekly exposure, not an exact count
of everyone who drinks weekly. This wording limitation also affects the aid.

The primary findings support testing multi-select, clearer floral/fruit
language, typed escape states, layered results and optional recovery. These
remain formative proposals. The sample is small and coffee-exposed, answers
are self-reports, and stated willingness is not actual repeat use. Neither
the deduplicated nor raw sensitivity supports a statistical generalization.

Reproduce privately with Python 3.12 and openpyxl, a native Numbers export,
the restricted inventory and analytical aid:

```bash
python3 db/scripts/ingest-user-research-round1.py
```

Set `COFFEE_FLAVOR_USER_RESEARCH_ROOT` beforehand. Restricted source roots must
have mode 700. Never add the restricted root or original spreadsheets to Git.
The generator validates hashes and stops on duplicate-cluster discrepancies.
Questionnaire responses have no professional-sensory-label or ML-training role.
