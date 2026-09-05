#!/usr/bin/env python3
"""Apply the newly frozen R2 metric to untouched R1/B2 outer-held outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from alignment_metrics_r2 import semantic_result, grouped_summary, paired_group_delta
from run_m2_r1 import read, save, old_e
from run_m2_r2 import OUT, verify_frozen, private_save


def run(owner):
    verify_frozen(owner)
    source = read(owner / "revisions/r1/cv/M2_R1_FINAL_FIXED.private.json")
    records = {r["record_id"]: r for r in read(owner / "recovery_records.json")}
    bundles = {
        i: read(owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{i}.model.json")
        for i in range(3)
    }
    rows = []
    for old in source:
        bundle = bundles[old["fold"]]
        vocabulary = set(old_e.baseline_bundle(bundle)["vocabulary"])
        baseline = next(
            r
            for r in old_e.baselines(records[old["record_id"]], old, bundle)
            if r["model"] == "B2"
        )
        for name, scored in [
            ("ORIGINAL_R1_CONTROL", old),
            ("ORIGINAL_B2_CONTROL", baseline),
        ]:
            result = semantic_result(
                scored["ranking"],
                old["episode"]["hidden"],
                old["episode"]["visible"],
                vocabulary=vocabulary,
            )
            rows.append(
                {
                    **result,
                    "model": name,
                    "record_id": old["record_id"],
                    "group_id": old["group_id"],
                    "source_family": old["source_family"],
                    "fold": old["fold"],
                    "path": "P1",
                    "stage": "PRELIMINARY_RESULT",
                    "ordinary_questions": len(old["payload"]["answers"]),
                    "ordinary_options": sum(
                        len(a["shown_option_ids"]) for a in old["payload"]["answers"]
                    ),
                    "final_comparison_candidates": 0,
                    "human_response_seconds": None,
                    "legacy_NDCG5_full_scope": scored["ndcg5"],
                    "legacy_Recall5_full_scope": scored["recall5"],
                    "legacy_Recall8_full_scope": scored["recall8"],
                }
            )
    bymodel = {
        name: [r for r in rows if r["model"] == name]
        for name in ["ORIGINAL_R1_CONTROL", "ORIGINAL_B2_CONTROL"]
    }
    result = {
        "scope": "New R2 metric applied to preserved R1 outer-held P1 outputs; not fresh validation or a refit",
        "models": {name: grouped_summary(rr) for name, rr in bymodel.items()},
        "R1_minus_B2": paired_group_delta(
            bymodel["ORIGINAL_R1_CONTROL"], bymodel["ORIGINAL_B2_CONTROL"]
        ),
        "per_source": {
            src: {
                name: grouped_summary([r for r in rr if r["source_family"] == src])
                for name, rr in bymodel.items()
            }
            for src in sorted({r["source_family"] for r in rows})
        },
        "costs": {
            name: {
                key: grouped_summary(rr, key)
                for key in [
                    "ordinary_questions",
                    "ordinary_options",
                    "final_comparison_candidates",
                ]
            }
            for name, rr in bymodel.items()
        },
        "R1_original_objective_results": "UNCHANGED; retained in revisions/r1",
        "real_user_alignment": "NOT_EVALUATED",
    }
    private_save(owner / "revisions/r2/frozen_output_alignment.private.json", rows)
    target = OUT / "alignment_cost_results.json"
    current = read(target) if target.exists() else {}
    current["frozen_output_baselines"] = result
    save(target, current)
    print(
        {name: values["group_macro_mean"] for name, values in result["models"].items()}
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    run(parser.parse_args().owner_dir)
