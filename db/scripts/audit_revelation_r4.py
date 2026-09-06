"""No-fit audit of actual held cross-grader revelation through frozen R4 models.

Post-fit descriptive audit only. Stage differences include question budget;
same-exposure B attribution is not a causal policy or personal-perception claim.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import data_connections_r4 as connection
import flavor_m2_r1 as r1

VERSION = "m2-r4.actual-held-source-revelation-audit.v1"


def protocol():
    return {
        "version": VERSION,
        "status": "POST_FIT_DESCRIPTIVE_AUDIT_NO_NEW_FIT_SELECTION_OR_TRIGGER",
        "models": "Exactly three previously fitted AKR_AUX outer models named by auxiliary_results.private.json.summary.models; verify model hashes and held coffee identity",
        "cohort": "All 61 admitted source episodes / 59 original coffee groups, including all empty T",
        "source_novelty": "B minus A exact concepts; same-parent but distinct specifics remain new content and are separately counted",
        "system_novelty": "Canonical selected concepts in Q2-Q4 minus the logically entailed closure of Q0-Q1 selected concepts; fine implies only itself and broad parents, never siblings",
        "B_attribution": "For each actual exposed Q2-Q4 question, selected options under A union B minus selected options under A, using the same frozen answer generator and exact same exposure; not a counterfactual adaptive policy effect",
        "deduplication": "Repeated same canonical selections count once per episode; a later broad parent of already confirmed fine is reuse",
        "stages": ["Q1", "Q2", "Q4_ASK", "Q4_SKIP"],
        "target": "One unchanged source T relevance dictionary and original fixed model candidate universe excluding only fixed A at every stage; absent targets remain unidentifiable",
        "stage_contrasts": "Q2 minus Q1 and Q4_ASK minus Q1 are descriptive trajectory changes and include additional question budget; no isolated B causal claim",
        "branch_contrast": "Same actual Q2 state, frozen model, source A union B, and fixed T; gain=raw_gap_SKIP minus raw_gap_ASK; descriptive practical key threshold greater than 0.01 inherited from R4, no fitting or threshold search",
        "aggregation": "Equal record mean within original coffee group, then equal group mean; report full records/groups, identifiable coverage, and both record and any-record group counts",
        "independence": "Source grader reports share coffee/session; graders also span folds. Coffee holdout only; no new source, independent-person generalization or real same-person QA",
        "public": "Aggregate values, source/code/model/artifact hashes and owner-relative paths only; all case IDs, selected concepts, rankings and trajectories private",
    }


def canonical_selection(answer):
    options = {o["id"]: o for o in answer["options"]}
    selected = set(answer["selected_option_ids"])
    if not selected <= set(answer["shown_option_ids"]) or not selected <= set(options):
        raise ValueError("SELECTED_CONCEPT_NOT_ACTUALLY_EXPOSED")
    return {
        "attribute." + options[c]["attribute"] if options[c]["kind"] == "broad" else c
        for c in selected
    }


def exposure_novelty(episode, answers, answer_for, expert):
    """Read only A/B and actual exposures. Target cannot affect this function."""
    ordered = sorted(answers, key=lambda a: a["slot"])
    if len({a["slot"] for a in ordered}) != len(ordered):
        raise ValueError("ONE_ACTIVE_ANSWER_PER_SLOT_REQUIRED")
    a, b = set(episode["A"]), set(episode["B"])
    prefix, selected, attributable, specific, diagnostics = set(), set(), set(), set(), []
    for answer in ordered:
        current = canonical_selection(answer)
        expected_visible = a if answer["slot"] in {"Q0", "Q1"} else a | b
        expected = answer_for(answer, sorted(expected_visible), expert)
        if set(expected["selected_option_ids"]) != set(answer["selected_option_ids"]) or expected["state"] != answer["state"]:
            raise ValueError("ACTUAL_ANSWER_NOT_FROM_FROZEN_A_B_SOURCE")
        if answer["slot"] in {"Q0", "Q1"}:
            prefix |= current
        else:
            a_only = answer_for(answer, sorted(a), expert)
            extra_ids = set(answer["selected_option_ids"]) - set(a_only["selected_option_ids"])
            proof = {**answer, "selected_option_ids": sorted(extra_ids)}
            extra = canonical_selection(proof)
            new = current - connection.semantic_closure(selected)
            attributable |= extra
            opts = {o["id"]: o for o in answer["options"]}
            specific |= {c for c in extra_ids if opts[c]["kind"] == "specific"}
            diagnostics.append({
                "slot": answer["slot"], "question_id": answer["question_id"],
                "shown_option_ids": answer["shown_option_ids"],
                "selected_canonical": sorted(current),
                "new_canonical_at_this_stage": sorted(new),
                "same_exposure_A_only_selected": a_only["selected_option_ids"],
                "B_attributable_selected_canonical": sorted(extra),
            })
        selected |= current
    novel_system = selected - connection.semantic_closure(prefix)
    novel_b = attributable - connection.semantic_closure(prefix)
    source_new = b - a
    actual_new_specific_b = specific & source_new
    if specific - source_new:
        raise ValueError("B_ATTRIBUTED_SPECIFIC_NOT_PRESENT_IN_SOURCE_B_MINUS_A")
    related = connection.related_by_parent(actual_new_specific_b, a)
    return {
        "source_B_new_exact": sorted(source_new),
        "source_B_new_related_specific": sorted(connection.related_by_parent({c for c in source_new if c.startswith("sensory.")}, a)),
        "prefix_selected_canonical": sorted(prefix), "all_selected_canonical": sorted(selected),
        "actual_new_system_canonical": sorted(novel_system),
        "B_same_exposure_extra_selected_canonical": sorted(attributable),
        "B_new_system_canonical": sorted(novel_b),
        "B_actual_new_specific": sorted(actual_new_specific_b),
        "B_actual_new_related_specific": sorted(related),
        "B_actual_new_direction_specific": sorted(actual_new_specific_b - related),
        "A_only_later_new_system_canonical": sorted(novel_system - novel_b),
        "source_B_new_specific_not_selected": sorted({c for c in source_new if c.startswith("sensory.")} - actual_new_specific_b),
        "exposure_trace": diagnostics,
    }


def _group_mean(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        if row[key] is not None:
            grouped[row["group_id"]].append(float(row[key]))
    return float(np.mean([np.mean(v) for v in grouped.values()])) if grouped else None


def aggregate(rows):
    fields = [
        "source_B_new_exact", "source_B_new_related_specific", "actual_new_system_canonical",
        "B_same_exposure_extra_selected_canonical", "B_new_system_canonical", "B_actual_new_specific",
        "B_actual_new_related_specific", "B_actual_new_direction_specific", "A_only_later_new_system_canonical",
        "source_B_new_specific_not_selected",
    ]
    novelty = {}
    for field in fields:
        counts = [{"group_id": r["group_id"], "count": len(r["novelty"][field])} for r in rows]
        novelty[field] = {
            "record_concept_total": sum(r["count"] for r in counts),
            "records_with_any": sum(bool(r["count"]) for r in counts),
            "coffee_groups_with_any_record": len({r["group_id"] for r in counts if r["count"]}),
            "coffee_macro_concepts_per_record": _group_mean(counts, "count"),
        }
    stages = {}
    for stage in protocol()["stages"]:
        values = [{"group_id": r["group_id"], **r["stages"][stage]} for r in rows]
        stages[stage] = {key: _group_mean(values, key) for key in ["raw_gap", "ndcg", "recall", "ordinary_questions", "ordinary_options"]}
        stages[stage].update(identifiable_records=sum(r["raw_gap"] is not None for r in values), identifiable_coffee_groups=len({r["group_id"] for r in values if r["raw_gap"] is not None}))
    known = [r for r in rows if r["gain_ASK_over_SKIP"] is not None]
    key = [r for r in known if r["gain_ASK_over_SKIP"] > 0.01]
    q2_delta = [{"group_id": r["group_id"], "value": r["stages"]["Q2"]["raw_gap"] - r["stages"]["Q1"]["raw_gap"] if r["stages"]["Q1"]["raw_gap"] is not None else None} for r in rows]
    q4_delta = [{"group_id": r["group_id"], "value": r["stages"]["Q4_ASK"]["raw_gap"] - r["stages"]["Q1"]["raw_gap"] if r["stages"]["Q1"]["raw_gap"] is not None else None} for r in rows]
    return {
        "records": len(rows), "coffee_groups": len({r["group_id"] for r in rows}),
        "fixed_target_verified_records": sum(r["fixed_target_verified"] for r in rows),
        "empty_target_records_retained": len(rows) - len(known),
        "novelty": novelty, "stages": stages,
        "descriptive_stage_changes": {"Q2_minus_Q1_raw_gap_coffee_macro": _group_mean(q2_delta, "value"), "Q4_ASK_minus_Q1_raw_gap_coffee_macro": _group_mean(q4_delta, "value"), "interpretation": protocol()["stage_contrasts"]},
        "descriptive_same_Q2_branch": {
            "identifiable_records": len(known), "identifiable_coffee_groups": len({r["group_id"] for r in known}),
            "key_records_gain_over_0_01": len(key), "coffee_groups_with_any_key_record": len({r["group_id"] for r in key}),
            "key_records_with_actual_B_new_system_information": sum(bool(r["novelty"]["B_new_system_canonical"]) for r in key),
            "positive_gain_records": sum(r["gain_ASK_over_SKIP"] > 1e-12 for r in known),
            "negative_gain_records": sum(r["gain_ASK_over_SKIP"] < -1e-12 for r in known),
            "tie_records": sum(abs(r["gain_ASK_over_SKIP"]) <= 1e-12 for r in known),
            "gain_coffee_macro": _group_mean(rows, "gain_ASK_over_SKIP"),
            "positive_gain_max": max([0.0] + [r["gain_ASK_over_SKIP"] for r in known]) if known else None,
            "new_trigger_fits": 0,
        },
    }


def audit_case(record, bundle, fold):
    import alignment_metrics_r3 as metric
    import flavor_conditioning_r4 as runtime
    import train_conditioning_r4 as training

    if record["group_id"] in set((bundle.get("training_lineage") or {}).get("training_groups", [])):
        raise ValueError("AUXILIARY_AUDIT_CASE_IS_NOT_HELD_COFFEE")
    target = copy.deepcopy(record["relevance"])
    target_hash = connection.digest(target)
    episode, states, _ = training.trajectory(record, bundle, policy="ALWAYS_ASK", auxiliary=True)
    by_slot = {max(s["base_state"]["answers_by_question"]): s for s in states if s["base_state"]["answers_by_question"]}
    q2 = by_slot["Q2"]
    end_skip, _ = runtime.complete_branch(q2, sorted(set(record["A"]) | set(record["B"])), bundle, "SKIP")
    stage_states = {"Q1": by_slot["Q1"], "Q2": q2, "Q4_ASK": by_slot["Q4"], "Q4_SKIP": end_skip}
    stages = {}
    for stage, state in stage_states.items():
        if connection.digest(episode["relevance"]) != target_hash or connection.digest(record["relevance"]) != target_hash:
            raise ValueError("REFERENCE_TARGET_CHANGED_DURING_REVELATION")
        values = metric.evaluate(state["candidate_scores"], target, bundle["fixed_candidates"], excluded_visible=record["A"])
        answers = state["base_state"]["answers_by_question"]
        stages[stage] = {**values, "ordinary_questions": len(answers), "ordinary_options": sum(len(a["shown_option_ids"]) for a in answers.values()), "fixed_target_sha256": target_hash}
    ask, skip = stages["Q4_ASK"]["raw_gap"], stages["Q4_SKIP"]["raw_gap"]
    answers = by_slot["Q4"]["base_state"]["answers_by_question"]
    novelty = exposure_novelty(record, list(answers.values()), training.base_training.answer_for, bundle["r1_expert"])
    return {"record_id": record["record_id"], "group_id": record["group_id"], "fold": fold,
            "bundle_id": bundle["bundle_id"], "episode": episode, "novelty": novelty,
            "stages": stages, "gain_ASK_over_SKIP": skip - ask if ask is not None and skip is not None else None,
            "fixed_target_verified": True, "stage_states_private": stage_states}


def run(owner):
    import alignment_metrics_r3 as metric
    import flavor_conditioning_r4 as runtime
    import train_conditioning_r4 as training

    owner = Path(owner)
    private = owner / "revisions/r4"
    auxiliary_file = private / "auxiliary_results.private.json"
    if not auxiliary_file.exists():
        raise FileNotFoundError("AUXILIARY_RESULTS_NOT_YET_READY_NO_FIT_OR_POLL")
    source = json.loads(auxiliary_file.read_text())
    models = source["summary"]["models"]
    if sorted(m["outer"] for m in models) != [0, 1, 2]:
        raise ValueError("EXACTLY_THREE_PREVIOUS_AUXILIARY_MODELS_REQUIRED")
    files = {"auxiliary_results": auxiliary_file, "auxiliary_contract": private / "auxiliary_contract.frozen.json",
             "episodes": private / "cross_grader_episodes.private.json", "folds": owner / "revisions/r1/D0_folds.private.json",
             "audit_code": Path(__file__), "runtime_code": Path(runtime.__file__), "metric_code": Path(metric.__file__), "trajectory_code": Path(training.__file__), "source_adapter_code": Path(connection.__file__)}
    files.update({name: Path(__file__).parent / (name + ".py") for name in ["train_m2_r1", "train_sequential", "flavor_m2_r1"]})
    for m in models:
        path = owner / m["on_owner_relative_path"]
        if not path.resolve().is_relative_to(owner.resolve()) or connection.sha(path) != m["on_model_sha256"]:
            raise ValueError("PREVIOUS_AUXILIARY_MODEL_PATH_OR_HASH_CHANGED")
        files["model_outer" + str(m["outer"])] = path
    fingerprint = connection.digest({"protocol": protocol(), "files": {k: connection.sha(p) for k, p in files.items()}})
    receipt_path = private / "revelation_audit_receipt.private.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["input_fingerprint"] != fingerprint:
            raise ValueError("PRESERVE_PRIOR_AUDIT_INPUT_FINGERPRINT_CHANGED")
        for name, expected in receipt["artifact_sha256"].items():
            if connection.sha(private / name) != expected:
                raise ValueError("PRIOR_AUDIT_ARTIFACT_CHANGED")
        return json.loads((private / "revelation_audit_summary.private.json").read_text())
    episodes = connection.load_episodes(owner)
    folds = json.loads(files["folds"].read_text())
    if len(episodes) != 61 or len({r["group_id"] for r in episodes}) != 59:
        raise ValueError("FULL_AUXILIARY_COHORT_REQUIRED")
    rows = []
    for model in sorted(models, key=lambda m: m["outer"]):
        bundle = json.loads(files["model_outer" + str(model["outer"])].read_text())
        runtime.check_bundle(bundle)
        if bundle["selected_variant"] != "AKR" or not bundle["training_lineage"].get("auxiliary_rows"):
            raise ValueError("PREVIOUS_ACTUAL_AKR_AUX_MODEL_REQUIRED")
        for record in episodes:
            if folds[record["group_id"]] == model["outer"]:
                rows.append(audit_case(record, bundle, model["outer"]))
    if len(rows) != 61 or len({r["record_id"] for r in rows}) != 61:
        raise ValueError("EVERY_AUXILIARY_CASE_ONCE_REQUIRED")
    saved = {r["record_id"]: r for r in source["rows"] if r["task"] == "CROSS_GRADER_REVELATION" and r["model"] == "AKR_AUX"}
    if set(saved) != {r["record_id"] for r in rows}:
        raise ValueError("ORIGINAL_AUXILIARY_HELD_COHORT_CHANGED")
    for row in rows:
        for key in ["raw_gap", "ndcg", "recall"]:
            a, b = row["stages"]["Q4_ASK"][key], saved[row["record_id"]][key]
            if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-12):
                raise ValueError("REPLAYED_ASK_PATH_DISAGREES_WITH_EXISTING_RESULT")
    summary = {"version": VERSION, "status": "ACTUAL_HELD_MODEL_REPLAY_DESCRIPTIVE_NO_FIT", "protocol": protocol(),
               "results": aggregate(rows), "fit_calls": 0, "model_parameter_changes": 0, "new_sources": 0,
               "artifacts": {"case_trace_owner_relative_path": "revisions/r4/revelation_audit_cases.private.json"},
               "input_sha256": {k: connection.sha(p) for k, p in files.items()}, "input_fingerprint": fingerprint}
    if connection.digest({"protocol": protocol(), "files": summary["input_sha256"]}) != fingerprint:
        raise ValueError("INPUT_CODE_OR_MODEL_CHANGED_DURING_NO_FIT_AUDIT")
    connection._save_new(private / "revelation_audit_cases.private.json", rows)
    connection._save_new(private / "revelation_audit_summary.private.json", summary)
    receipt = {"completed_utc": datetime.now(timezone.utc).isoformat(), "input_fingerprint": fingerprint,
               "artifact_sha256": {name: connection.sha(private / name) for name in ["revelation_audit_cases.private.json", "revelation_audit_summary.private.json"]}, "fit_calls": 0}
    connection._save_new(receipt_path, receipt)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.owner_dir), ensure_ascii=False, sort_keys=True, indent=2))
