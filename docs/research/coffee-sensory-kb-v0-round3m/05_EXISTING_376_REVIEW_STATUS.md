# Existing 376 review status

## Source audit result

The complete Round 3L staged gate-candidate ledger was traced to five governed
AVPA palmares PDFs from 2021 through 2025. The source artifacts contain 69, 50,
88, 87, and 82 candidate rows respectively, totaling 376.

Each candidate has an artifact SHA-256 and a bounded page/table/row locator.
The candidate field is a competition category classification, not a filled
coffee-specific sensory observation. Category labels cannot be converted into
flavor descriptors.

```text
EXISTING_CANDIDATE_COUNT=376
EXISTING_CANDIDATE_DISPOSITIONED_COUNT=376
NON_DESCRIPTOR_COUNT=376
DISPOSITION_COMPLETENESS_RATE=100%
HUMAN_CONFIRMED_REVIEW_COUNT=0
EXPERT_ADJUDICATED_REVIEW_COUNT=0
```

Every row receives exactly one current disposition, `NON_DESCRIPTOR`, and the
review state `REJECTED_NON_DESCRIPTOR`. The actor is Codex machine-assisted
source audit, never human or expert review. The five snapshots remain useful as
negative evidence and are not deleted from the source census.

The combined current review queue also contains 140 distinct live pilot rows
with disposition `HUMAN_REVIEW_REQUIRED`. That separate count must not be
mistaken for the existing-376 metric above: among the 376 existing candidates,
`HUMAN_REVIEW_REQUIRED_COUNT=0`; across the merged 516-row queue, the current
human-review-required count is 140.
