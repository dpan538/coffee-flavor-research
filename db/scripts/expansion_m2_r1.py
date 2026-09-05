"""D0 versus D0+D1 with locked M2 R1 model form, vocabulary and questions."""

from __future__ import annotations
import argparse, copy, json, time
from pathlib import Path
import train_m2_r1 as tr
import flavor_m2_r1 as rt
from run_m2_r1 import (
    OUT,
    ROOT,
    read,
    save,
    sha,
    freeze,
    old_s,
    enrich,
    compact_summary,
    comparison,
    scope_row,
    old_e,
)


def d0_inner_banks(records, vocabulary, outer_bank):
    split = tr.split_groups(records, 2)
    result = {}
    for fold in range(2):
        train = [r for r in records if split[r["group_id"]] != fold]
        stats = tr.statistics(train, vocabulary)
        attrs = {c: rt.PARENTS.get(c, []) for c in vocabulary}
        result[fold] = (
            tr.make_bank(stats, attrs)
            if "initial_pair_selection" in outer_bank
            else tr.legacy.make_bank(stats, attrs)
        )
    return result


def validate_cached_model(bundle, base, train, manifest, selected, locks):
    """Fail closed when a retained model belongs to a different experiment."""
    receipt = bundle["fit_receipt"]
    if (
        bundle["data_manifest_hash"] != manifest
        or bundle["training_split_hash"]
        != rt.digest(sorted({r["group_id"] for r in train}))
        or bundle["candidate_vocabulary"] != base["candidate_vocabulary"]
        or bundle["question_bank"] != base["question_bank"]
        or receipt["C"] != selected["C"]
        or receipt["loss_mode"] != selected["loss_mode"]
        or bundle.get("evidence_policy", {}).get("canonical_broad_feedback", False)
        != selected.get("canonical_broad_feedback", False)
    ):
        raise ValueError("D1_CACHED_MODEL_EXPERIMENT_MISMATCH")
    if locks is not None and [
        r["question_bank_hash"] for r in receipt["inner_feature_audit"]
    ] != [rt.digest(locks[i]) for i in range(2)]:
        raise ValueError("D1_CACHED_INNER_BANK_MISMATCH")


def run(owner, expanded=False, controlled=False):
    cfg = freeze(owner)
    dst = owner / "revisions/r1"
    selected = read(
        dst
        / (
            "final_fixed_selection.private.json"
            if expanded
            else "conditional_selection.private.json"
        )
    )
    suffix = ("_expanded" if expanded else "") + ("_controlled" if controlled else "")
    snapshot = dst / f"D1_recovery_snapshot{suffix}.private.json"
    if snapshot.exists():
        d1 = read(snapshot)
    else:
        d1 = read(
            dst
            / (
                "d1_recovery_expanded.private.json"
                if expanded
                else "d1_recovery_records.private.json"
            )
        )
        save(snapshot, d1)
        save(
            dst / f"D1_recovery_plan{suffix}.private.json",
            {
                "registered_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "input_sha256": sha(snapshot),
                "D0_selected_model": selected,
                "bank_vocabulary_hyperparameters": "D0 per-fold frozen, no D1 question or candidate pool changes",
                "weighting": "Same equal-source/equal-group/equal-within-group procedure. Coffee conditions and assessor counts do not become independent group weights.",
                "rights_and_scope": "Per source manifest; auxiliary storage narratives, not fresh-brew core labels",
                "new_confirmation": "All prospective source+group split assignments honored; no condition-level splitting.",
                "additional_CATA": "Separate masked sensory-view training, not fine-descriptor negative supervision.",
            },
        )
    assert all(
        r["role"] == "AUX_COFFEE_WEAK_LABEL"
        and (r["task_masks"]["leaf_recovery"] or not r["targets"])
        for r in d1
    )
    data = read(owner / "recovery_records.json")
    dev = [r for r in data if r["split"] == "DEVELOPMENT"]
    hist = [r for r in data if r["split"] == "HISTORICAL_REGRESSION"]
    assert not {r["group_id"] for r in d1} & {r["group_id"] for r in data}
    d1train = [r for r in d1 if r["split"] == "DEVELOPMENT"]
    confirm = [r for r in d1 if r["split"] == "CONFIRMATION"]
    folds = read(dst / "D0_folds.private.json")
    manifest = old_s.digest([selected["manifest_hash"], sha(snapshot)])
    label = (
        ("M2_R1_CONTROLLED_D0_D1" if expanded else "M2_R1_CONTROLLED_PERU_D0_D1")
        if controlled
        else "M2_R1_FINAL_D0_D1" if expanded else "M2_R1_D0_D1"
    )
    results = []
    fitlog = []
    for fold in range(3):
        base = read(dst / f"cv/{selected['model']}_fold{fold}.model.json")
        train = [r for r in dev if folds[r["group_id"]] != fold] + d1train
        held = [r for r in dev if folds[r["group_id"]] == fold]
        locks = (
            d0_inner_banks(
                [r for r in dev if folds[r["group_id"]] != fold],
                base["candidate_vocabulary"],
                base["question_bank"],
            )
            if controlled
            else None
        )
        path = dst / f"cv/{label}_fold{fold}.model.json"
        if path.exists():
            b = read(path)
        else:
            b, receipt = tr.fit(
                train,
                manifest,
                C=selected["C"],
                vocabulary=base["candidate_vocabulary"],
                tag=label + ":fold" + str(fold),
                bank_override=base["question_bank"],
                loss_mode=selected["loss_mode"],
                canonical_broad_feedback=selected.get(
                    "canonical_broad_feedback", False
                ),
                inner_bank_overrides=locks,
            )
            b["experiment_variant"] = label
            save(path, b)
        validate_cached_model(b, base, train, manifest, selected, locks)
        fitlog.append({"fold": fold, **b["fit_receipt"]})
        for r in held:
            row = enrich(tr.evaluate_record(r, b), r, rt, b)
            row["model"] = label
            row["fold"] = fold
            results.append(row)
        print(
            json.dumps(
                {
                    "phase": "D1_fit",
                    "fold": fold,
                    "NDCG5": compact_summary(results)["ndcg5"],
                }
            ),
            flush=True,
        )
    base = read(selected["model_file"])
    path = dst / f"models/{label}.model.json"
    locks = (
        d0_inner_banks(dev, base["candidate_vocabulary"], base["question_bank"])
        if controlled
        else None
    )
    if path.exists():
        b = read(path)
    else:
        b, receipt = tr.fit(
            dev + d1train,
            manifest,
            C=selected["C"],
            vocabulary=base["candidate_vocabulary"],
            tag=label + ":all-development",
            bank_override=base["question_bank"],
            loss_mode=selected["loss_mode"],
            canonical_broad_feedback=selected.get("canonical_broad_feedback", False),
            inner_bank_overrides=locks,
        )
        b["experiment_variant"] = label
        save(path, b)
    fitlog.append({"fold": "ALL_DEVELOPMENT", **b["fit_receipt"]})
    validate_cached_model(b, base, dev + d1train, manifest, selected, locks)
    baseline = read(dst / f"cv/{selected['model']}.private.json")
    historical = [enrich(tr.evaluate_record(r, b), r, rt, b) for r in hist]
    hbase = read(dst / f"cv/{selected['model']}_historical.private.json")
    save(dst / f"cv/{label}.private.json", results)
    save(dst / f"cv/{label}_historical.private.json", historical)
    save(dst / f"expansion_fit_log{suffix}.private.json", fitlog)
    metrics = read(OUT / "metrics.json")
    metrics[
        (
            "sample_value_controlled"
            if controlled
            else "sample_value_expanded" if expanded else "sample_value"
        )
    ] = {
        "D1_training_records": len(d1train),
        "D1_independent_groups": len({r["group_id"] for r in d1train}),
        "D1_source_families": sorted({r["source_family"] for r in d1train}),
        "models": {"D0": compact_summary(baseline), "D0_D1": compact_summary(results)},
        "D0_D1_minus_D0": comparison(results, baseline),
        "fine_comparison": comparison(
            [scope_row(r, kind="fine") for r in results],
            [scope_row(r, kind="fine") for r in baseline],
        ),
        "broad_comparison": comparison(
            [scope_row(r, kind="broad") for r in results],
            [scope_row(r, kind="broad") for r in baseline],
        ),
        "historical": {
            "D0": compact_summary(hbase),
            "D0_D1": compact_summary(historical),
            "delta": comparison(historical, hbase),
        },
        "independent_confirmation_groups": len({r["group_id"] for r in confirm}),
        "independent_confirmation": (
            "NOT_EVALUATED" if not confirm else "AUXILIARY_SOURCE_ONLY"
        ),
        "real_answers": "NOT_EVALUATED",
        "fit_count": len(fitlog),
        "comparability": {
            "same_vocabulary": True,
            "same_question_bank": True,
            "same_training_question_bank": controlled,
            "scope": (
                "All D0-only train-fold catalogs fixed"
                if controlled
                else "Outer evaluation bank fixed; inner train catalog changes with D1, so not a pure-label data effect"
            ),
            "same_hyperparameters": True,
            "same_target_partition": True,
            "same_group_denominator": True,
        },
        "new_context_pairs": 0,
        "new_core_professional_groups": 0,
        "limitations": "Auxiliary storage narratives and optional consumer citation profiles are not professional fresh-brew confirmation. Complete CATA training is a separate masked attribute task.",
    }
    if confirm:
        viewed_path = dst / "D1_confirmation_viewed.private.json"
        previous = read(viewed_path) if viewed_path.exists() else {"groups": []}
        groups = sorted({r["group_id"] for r in confirm})
        previous_files = list(dst.glob("D1_confirmation*.private.json"))
        previously_inspected = bool(set(previous["groups"]) & set(groups)) or bool(
            previous_files
        )
        save(
            viewed_path,
            {
                "groups": sorted(set(previous["groups"]) | set(groups)),
                "first_observation_known_before_this_run": previously_inspected,
                "scope": "Persistent viewed-group registry; rerunning cannot restore a fresh confirmation claim.",
            },
        )
        ca = [enrich(tr.evaluate_record(r, b), r, rt, b) for r in confirm]
        cb = [enrich(tr.evaluate_record(r, base), r, rt, base) for r in confirm]
        save(dst / f"D1_confirmation{suffix}.private.json", {"D0": cb, "D0_D1": ca})
        groups = sorted({r["group_id"] for r in confirm})
        aa = {r["group_id"]: r for r in ca}
        bb = {r["group_id"]: r for r in cb}
        delta = [
            aa[g]["ndcg5"] - bb[g]["ndcg5"]
            for g in groups
            if aa[g]["ndcg5"] is not None and bb[g]["ndcg5"] is not None
        ]
        metrics[
            (
                "sample_value_controlled"
                if controlled
                else "sample_value_expanded" if expanded else "sample_value"
            )
        ]["confirmation_comparison"] = {
            "D0": compact_summary(cb),
            "D0_D1": compact_summary(ca),
            "groups": len(groups),
            "per_group_ndcg5_delta": delta,
            "range": [min(delta), max(delta)] if delta else None,
            "mean_delta": sum(delta) / len(delta) if delta else None,
            "status": "INCONCLUSIVE",
            "scope": "Three commercial blends from one consumer-citation source; no narrow bootstrap claim or professional/user efficacy claim.",
            "previously_inspected_before_training_catalog_control_fix": controlled,
            "previously_inspected_before_this_run": previously_inspected,
            "fresh_confirmation_claim_allowed": not previously_inspected,
        }
    save(OUT / "metrics.json", metrics)
    print(
        json.dumps(
            metrics[
                (
                    "sample_value_controlled"
                    if controlled
                    else "sample_value_expanded" if expanded else "sample_value"
                )
            ]
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--owner-dir", type=Path, required=True)
    p.add_argument("--expanded", action="store_true")
    p.add_argument("--controlled", action="store_true")
    a = p.parse_args()
    run(a.owner_dir, a.expanded, a.controlled)
