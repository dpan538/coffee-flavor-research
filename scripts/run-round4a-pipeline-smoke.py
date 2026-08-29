#!/usr/bin/env python3
"""Rollback-only synthetic smoke test for the future classical pipeline API."""

from __future__ import annotations

import json
import tempfile
from collections import Counter
from pathlib import Path


fixtures = [
    {"coffee_group": "synthetic-coffee-a", "source_family": "fixture-a", "features": [1, 0, 1], "label": "fruit"},
    {"coffee_group": "synthetic-coffee-b", "source_family": "fixture-b", "features": [0, 1, 1], "label": "cocoa"},
    {"coffee_group": "synthetic-coffee-c", "source_family": "fixture-c", "features": [1, 1, 0], "label": "fruit"},
]
train = fixtures[:2]
holdout = fixtures[2:]
assert {row["coffee_group"] for row in train}.isdisjoint(row["coffee_group"] for row in holdout)
assert {row["source_family"] for row in train}.isdisjoint(row["source_family"] for row in holdout)
majority = Counter(row["label"] for row in train).most_common(1)[0][0]
prediction = [majority for _ in holdout]
accuracy = sum(prediction[index] == row["label"] for index, row in enumerate(holdout)) / len(holdout)

with tempfile.TemporaryDirectory(prefix="coffee-round4a-smoke-") as temp:
    root = Path(temp)
    model_path = root / "synthetic-majority-model.json"
    card_path = root / "MODEL_CARD.json"
    model_path.write_text(json.dumps({"type": "MAJORITY_FIXTURE", "label": majority}), encoding="utf-8")
    card_path.write_text(json.dumps({
        "model_run_type": "PIPELINE_SMOKE_TEST",
        "empirical_model": False,
        "performance_claim_allowed": False,
        "model_weight_release_allowed": False,
        "synthetic_fixture_count": len(fixtures),
        "metric_api_output": {"fixture_accuracy": accuracy, "claimable": False},
    }, sort_keys=True), encoding="utf-8")
    assert json.loads(model_path.read_text(encoding="utf-8"))["label"] == majority
    assert "restricted://" not in model_path.read_text(encoding="utf-8")

print("MODEL_RUN_TYPE=PIPELINE_SMOKE_TEST")
print("PIPELINE_SMOKE_TEST_PASS=true")
print("EMPIRICAL_MODEL=false")
print("PERFORMANCE_CLAIM_ALLOWED=false")
print("MODEL_WEIGHT_RELEASE_ALLOWED=false")
print("PERSISTED_SYNTHETIC_TRAINING_ROW_COUNT=0")
