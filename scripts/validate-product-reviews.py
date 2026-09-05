#!/usr/bin/env python3
"""Validate the committed independent review import without approving it."""
import csv
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/"db/data/product-benchmark-v0.2"
with (folder/"PRODUCT_TASK_REVIEW_IMPORT.tsv").open(newline="") as f:
    rows=list(csv.DictReader(f,delimiter="\t"))
assert len({r["review_item_id"] for r in rows})==len(rows), "Duplicate review IDs"
required=("review_item_id","case_id","intended_reviewer","reviewer_agent","decision","reason","confidence","identified_risk","suggested_revision","model_version","review_timestamp")
for row in rows:
    assert all(row[k].strip() for k in required), "Incomplete review import"
    assert row["intended_reviewer"] in ("Claude","DeepSeek","GPT","project owner")
    assert row["decision"] in ("approve","reject","revise","defer")
    datetime.fromisoformat(row["review_timestamp"].replace("Z","+00:00"))
    assert row["final_owner_decision"]=="", "This checkpoint has no authorized final owner decisions"
for name in ("PRODUCT_TASK_OWNER_REVIEW_TEMPLATE.tsv","PRODUCT_TASK_AGENT_REVIEW_TEMPLATE.tsv"):
    with (folder/name).open(newline="") as f:
        for row in csv.DictReader(f,delimiter="\t"):
            for key in ("headline_acceptable","expanded_main_acceptable","exploration_acceptable","decision","final_owner_decision"):
                if key in row: assert row[key]=="", "Review templates must not fabricate decisions"
print(f"IMPORTED_AGENT_REVIEW_COUNT={len(rows)}; OWNER_DECISION_COUNT=0; HUMAN_FINAL_DECISION_COUNT=0")
