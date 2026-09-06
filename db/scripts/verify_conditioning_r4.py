"""No-fit independent R4 trajectory, frozen-base and actual CLI verification.

Public output contains only aggregate engineering checks and private artifact
hashes. Per-coffee answers, rankings and losses are saved privately.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import alignment_metrics_r3 as metric
import flavor_conditioning_r4 as r4
import flavor_constraints_r3 as r3
import train_m2_r1 as episodes
from train_constraints_r3 import expert_training_groups

ROOT = Path(__file__).resolve().parents[2]
VERSION = "m2-r4-independent-execution-audit.v1"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_private(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(
            value, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
        )
        stream.write("\n")
    temporary.chmod(0o600)
    temporary.replace(path)
    return sha(path)


def check_contract(owner):
    private = owner / "revisions/r4/experiment_contract.frozen.json"
    public = (
        ROOT
        / "db/data/backend-sequential-model-v2/revisions/r4/experiment_contract.json"
    )
    if sha(private) != sha(public):
        raise ValueError("PUBLIC_PRIVATE_FROZEN_CONTRACT_MISMATCH")
    contract = read(private)
    if contract["runtime"] != r4.protocol():
        raise ValueError("RUNTIME_PROTOCOL_DIFFERS_FROM_FROZEN_CONTRACT")
    for relative, expected in contract["data_inputs"].items():
        if sha(owner / relative) != expected:
            raise ValueError("FROZEN_INPUT_CHANGED:" + relative)
    return sha(private)


def replay_visible(episode, bundle, backend, variant, policy="ALWAYS_ASK"):
    """Only episode A reaches the response function; T is evaluated afterwards."""
    current = backend.initial_state(episode["context"], bundle, variant, policy)
    states, answers = [copy.deepcopy(current)], []
    while True:
        nxt = backend.select_next_question(current, bundle)
        if nxt["action"] != "ASK":
            break
        question = nxt["question"]
        answer = episodes.answer_for(question, episode["visible"], bundle["r1_expert"])
        current = backend.update_state(current, answer, bundle)
        answers.append(answer)
        states.append(copy.deepcopy(current))
        if len(answers) > 5:
            raise ValueError("LEGAL_Q4_ENDPOINT_EXCEEDED")
    if "Q4" not in current["base_state"]["answers_by_question"]:
        raise ValueError("Q4_CLOSURE_REQUIRED")
    return states, answers


def ranking_signature(state):
    return [
        (row["candidate_id"], row["score"], row["rank"], row["raw_rank"])
        for row in state["candidate_scores"]
    ]


def compare_a0_record(record, old_bundle, new_bundle):
    episode = episodes.visible_episode(record)
    old, old_answers = replay_visible(episode, old_bundle, r3, "E1")
    new, new_answers = replay_visible(episode, new_bundle, r4, "A0")
    if old_answers != new_answers or len(old) != len(new):
        raise ValueError("A0_EXPOSURE_OR_ANSWER_TRAJECTORY_CHANGED")
    details = []
    for left, right in zip(old, new, strict=True):
        if ranking_signature(left) != ranking_signature(right):
            raise ValueError("A0_ORIGINAL_R3_RAW_SCORE_OR_RANK_CHANGED")
        a = metric.evaluate(
            left["candidate_scores"],
            episode["relevance"],
            old_bundle["fixed_candidates"],
            excluded_visible=episode["visible"],
        )
        b = metric.evaluate(
            right["candidate_scores"],
            episode["relevance"],
            new_bundle["fixed_candidates"],
            excluded_visible=episode["visible"],
        )
        if a != b:
            raise ValueError("A0_ORIGINAL_R3_METRIC_CHANGED")
        if any(row["conditioning_delta"] != 0 for row in right["candidate_scores"]):
            raise ValueError("A0_NONZERO_NEW_COMPONENT")
        details.append(
            {
                "slot": max(
                    right["base_state"]["answers_by_question"], default="INITIAL"
                ),
                "metrics": b,
                "ranking": right["candidate_scores"],
            }
        )
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "episode": episode,
        "answers": new_answers,
        "prefixes": details,
    }


def verify_outer_a0(owner, fold):
    owner = Path(owner)
    contract_sha = check_contract(owner)
    checkpoint = owner / f"revisions/r4/checkpoint_outer{fold}.private.json"
    if not checkpoint.exists():
        raise ValueError("R4_FIRST_FOLD_CHECKPOINT_REQUIRED_BEFORE_VERIFICATION")
    old_path = owner / f"revisions/r3/models/R3_CONSTRAINTS_outer{fold}.model.json"
    expert_path = owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{fold}.model.json"
    old, expert = read(old_path), read(expert_path)
    if old["r1_expert"] != expert:
        raise ValueError("ORIGINAL_R3_E1_EXPERT_BYTES_DIFFER")
    model = r4.make_bundle(expert, contract_hash=contract_sha, tag=f"A0_outer{fold}")
    records = read(owner / "recovery_records.json")
    folds = read(owner / "revisions/r1/D0_folds.private.json")
    held = sorted(
        [
            record
            for record in records
            if record["split"] == "DEVELOPMENT" and folds[record["group_id"]] == fold
        ],
        key=lambda row: row["record_id"],
    )
    if not held or expert_training_groups(expert) & {
        record["group_id"] for record in held
    }:
        raise ValueError("ACTUAL_HELD_COFFEE_GROUP_ISOLATION_REQUIRED")
    details = [compare_a0_record(record, old, model) for record in held]
    destination = (
        owner / f"revisions/r4/verification/A0_outer{fold}_recomputed.private.json"
    )
    detail_sha = save_private(
        destination,
        {
            "scope": "ACTUAL_RECOMPUTED_HELD_TRAJECTORIES_NOT_READING_RESULT_CACHE",
            "fold": fold,
            "rows": details,
        },
    )
    report = {
        "version": VERSION,
        "operation": "NO_FIT_ACTUAL_HELD_REPLAY",
        "fold": fold,
        "status": "PASS",
        "held_records": len(held),
        "held_coffee_groups": len({r["group_id"] for r in held}),
        "compared_prefixes": sum(len(row["prefixes"]) for row in details),
        "rank_and_raw_score_differences": 0,
        "metric_differences": 0,
        "actual_fit_count": 0,
        "same_question_bank_and_answer_trajectory": True,
        "group_isolation_checked": True,
        "contract_sha256": contract_sha,
        "r3_model_sha256": sha(old_path),
        "r1_expert_sha256": sha(expert_path),
        "private_detail_sha256": detail_sha,
        "interpretation": "Frozen A0 competence preservation and execution consistency, not new model efficacy evidence",
    }
    save_private(
        owner / f"revisions/r4/verification/A0_outer{fold}_public_summary.private.json",
        report,
    )
    return report


def _check_output(output, terminal=False):
    if (
        len(output["main"]) > 5
        or len(output["secondary"]) > 3
        or len(output["candidate_groups"]) != 1
    ):
        raise ValueError("GLOBAL_OUTPUT_BUDGET_VIOLATION")
    base = output["state"]["base_state"]
    if "Q4" not in base["answers_by_question"]:
        raise ValueError("MANDATORY_Q4_MISSING")
    decision = output["state"]["q2_decision"]
    if decision["action"] == "SKIP" and (
        "Q3" in base["answers_by_question"] or "Q3" not in base["skipped_slots"]
    ):
        raise ValueError("SKIP_CREATED_FICTITIOUS_Q3_ANSWER")
    if terminal:
        if (
            output["stage"] != "FINAL_RESULT"
            or output["exposure"] is not None
            or not base["final_comparison"]
        ):
            raise ValueError("FINAL_COMPARISON_NOT_ONCE_TERMINAL")
    else:
        exposure = output["exposure"]
        if (
            output["stage"] != "PRELIMINARY_RESULT"
            or not exposure
            or not 3 <= len(exposure["candidate_ids"]) <= 8
        ):
            raise ValueError("ACTUAL_FINAL_POOL_REQUIRED")
    if output["human_time"] is not None:
        raise ValueError("ENGINEERING_RUN_CANNOT_FABRICATE_HUMAN_TIME")


def _cli(model_path, payload, destination, seed):
    payload_path = destination.with_name(
        destination.stem + f".seed{seed}.payload.private.json"
    )
    save_private(payload_path, payload)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "db/scripts/flavor_conditioning_r4.py"),
            "--model",
            str(model_path),
            "--request",
            str(payload_path),
        ],
        text=True,
        capture_output=True,
        check=True,
        env={
            **os.environ,
            "PYTHONHASHSEED": str(seed),
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
        },
    )
    output = json.loads(result.stdout)
    output_path = destination.with_name(
        destination.stem + f".seed{seed}.output.private.json"
    )
    save_private(output_path, output)
    return (
        output,
        hashlib.sha256(result.stdout.encode()).hexdigest(),
        {"payload_sha256": sha(payload_path), "output_sha256": sha(output_path)},
    )


def new_legal_payload(bundle):
    """New deliberate engineering choices; no coffee record or hidden label read."""
    context = {"c0": r4.r1.C0[-1], "c1": r4.r1.C1[-1]}
    state = r4.initial_state(context, bundle, bundle["selected_variant"], "KEY_CASE")
    answers = []
    while True:
        nxt = r4.select_next_question(state, bundle)
        if nxt["action"] != "ASK":
            break
        question = nxt["question"]
        answer = {
            key: question[key]
            for key in ["slot", "question_id", "axis", "shown_option_ids"]
        }
        answer.update(
            selected_option_ids=question["shown_option_ids"][:2], state="SELECTED"
        )
        state = r4.update_state(state, answer, bundle)
        answers.append(answer)
        if len(answers) > 5:
            raise ValueError("NEW_ENGINEERING_PAYLOAD_EXCEEDED_Q4")
    payload = {
        "contract_version": r4.VERSION,
        "context": context,
        "variant": bundle["selected_variant"],
        "trigger_policy": "KEY_CASE",
        "answers": [answers[:2], answers[2:]],
    }
    return payload


def execute_payload(model_path, payload, destination, selected_from_visible=None):
    model_path, destination = Path(model_path), Path(destination)
    bundle = read(model_path)
    r4.check_bundle(bundle)
    preliminary, _, pre_artifacts = _cli(
        model_path, payload, destination.with_name(destination.stem + "_preliminary"), 1
    )
    _check_output(preliminary)
    pool = preliminary["exposure"]["candidate_ids"]
    # For a real held replay, only actual frozen A intersects the actual pool.
    # For a new engineering request these are deliberate synthetic selections.
    selected = (
        pool[:2]
        if selected_from_visible is None
        else [c for c in pool if c in set(selected_from_visible)]
    )
    final_payload = copy.deepcopy(payload)
    final_payload.update(
        final_mode="F2",
        final_comparison={
            "exposed_candidates": pool,
            "selected_candidates": selected,
            "feedback_source": "SIMULATED",
            "generation_version": bundle["bundle_id"],
        },
    )
    outputs, stdout_hashes, artifacts = [], [], []
    for seed in [1, 27, 314159]:
        output, stdout_hash, artifact = _cli(
            model_path,
            final_payload,
            destination.with_name(destination.stem + "_final"),
            seed,
        )
        _check_output(output, terminal=True)
        outputs.append(output)
        stdout_hashes.append(stdout_hash)
        artifacts.append(artifact)
    if len(set(stdout_hashes)) != 1 or any(
        output != outputs[0] for output in outputs[1:]
    ):
        raise ValueError("CROSS_HASHSEED_COMPLETE_CLI_OUTPUT_CHANGED")
    expected = r4.run(final_payload, bundle)
    if expected != outputs[0]:
        raise ValueError("IMPORTED_RUNTIME_AND_ACTUAL_CLI_DIFFER")
    try:
        r4.apply_final_comparison(
            outputs[0]["state"], final_payload["final_comparison"], bundle
        )
    except ValueError as error:
        if str(error) != "FINAL_COMPARISON_ALREADY_USED":
            raise
    else:
        raise ValueError("SECOND_FINAL_COMPARISON_WAS_ACCEPTED")
    return {
        "preliminary": preliminary,
        "final": outputs[0],
        "payload": final_payload,
        "public_summary": {
            "status": "PASS",
            "actual_cli_processes": 4,
            "hashseed_complete_output_identical": True,
            "legal_Q2_action_and_Q4_closure": True,
            "once_final_then_terminal": True,
            "ordinary_multi_select_present": any(
                len(a["selected_option_ids"]) > 1
                for group in payload["answers"]
                for a in (group if isinstance(group, list) else [group])
            ),
            "global_main5_secondary3_and_final3to8_budget": True,
            "imported_live_and_cli_identical": True,
            "human_time": None,
            "model_sha256": sha(model_path),
            "preliminary_artifacts": pre_artifacts,
            "final_artifacts": artifacts,
        },
    }


def verify_final(owner, held_fold=0):
    owner = Path(owner)
    contract_sha = check_contract(owner)
    final_path = owner / "revisions/r4/models/R4_ALL_DEVELOPMENT_RESEARCH.model.json"
    held_path = owner / f"revisions/r4/models/R4_POLICY_outer{held_fold}.model.json"
    final_bundle, held_bundle = read(final_path), read(held_path)
    for bundle in [final_bundle, held_bundle]:
        if bundle["objective_contract_sha256"] != contract_sha:
            raise ValueError("MODEL_FROZEN_CONTRACT_MISMATCH")
    destination = owner / "revisions/r4/verification"
    engineering = execute_payload(
        final_path,
        new_legal_payload(final_bundle),
        destination / "new_legal_multiselect",
    )
    records = read(owner / "recovery_records.json")
    folds = read(owner / "revisions/r1/D0_folds.private.json")
    all_dev_groups = set(folds)
    if (
        expert_training_groups(final_bundle["r1_expert"]) != all_dev_groups
        or set(final_bundle["trigger"].get("training_groups", [])) != all_dev_groups
        or set((final_bundle.get("training_lineage") or {}).get("training_groups", []))
        != all_dev_groups
    ):
        raise ValueError("FINAL_MODEL_MUST_BE_ALL_DEVELOPMENT_NOT_LAST_OUTER_FOLD")
    held = sorted(
        [
            r
            for r in records
            if r["split"] == "DEVELOPMENT" and folds[r["group_id"]] == held_fold
        ],
        key=lambda r: r["record_id"],
    )
    record = held[0]  # Frozen identity order; not selected by difficulty or loss.
    group = record["group_id"]
    lineage = held_bundle.get("training_lineage") or {}
    if (
        group in expert_training_groups(held_bundle["r1_expert"])
        or group in set(lineage.get("training_groups", []))
        or group in set(held_bundle["trigger"].get("training_groups", []))
    ):
        raise ValueError("LIVE_CASE_NOT_ACTUALLY_OUTER_HELD")
    if set(held_bundle["trigger"].get("training_groups", [])) != {
        identity for identity, fold in folds.items() if fold != held_fold
    }:
        raise ValueError("HELD_MODEL_TRIGGER_TRAIN_SCOPE_MISMATCH")
    episode = episodes.visible_episode(record)
    states, answers = replay_visible(
        episode, held_bundle, r4, held_bundle["selected_variant"], "KEY_CASE"
    )
    payload = {
        "contract_version": r4.VERSION,
        "context": episode["context"],
        "variant": held_bundle["selected_variant"],
        "trigger_policy": "KEY_CASE",
        "answers": answers,
    }
    actual = execute_payload(
        held_path,
        payload,
        destination / "actual_outer_held",
        selected_from_visible=episode["visible"],
    )
    if ranking_signature(states[-1]) != ranking_signature(
        actual["preliminary"]["state"]
    ):
        raise ValueError("ACTUAL_HELD_GENERATED_TRAJECTORY_AND_CLI_DIFFER")
    detail = {
        "record_id": record["record_id"],
        "group_id": group,
        "episode": episode,
        "actual_runtime_states": states,
        "actual_cli": actual,
        "metric_computed_after_answers": metric.evaluate(
            actual["preliminary"]["state"]["candidate_scores"],
            episode["relevance"],
            held_bundle["fixed_candidates"],
            excluded_visible=episode["visible"],
        ),
    }
    detail_sha = save_private(
        destination / "actual_outer_held_recomputed.private.json", detail
    )
    report = {
        "version": VERSION,
        "status": "PASS",
        "operation": "NO_FIT_NEW_LIVE_INPUT_AND_ACTUAL_HELD_REPLAY",
        "verified_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "contract_sha256": contract_sha,
        "actual_fit_count": 0,
        "new_input": engineering["public_summary"],
        "actual_outer_held_replay": actual["public_summary"],
        "actual_held_records": 1,
        "held_coffee_group_isolation_checked": True,
        "held_selection": "FIRST_FIXED_RECORD_ID_ORDER_NOT_METRIC_SELECTED",
        "private_held_detail_sha256": detail_sha,
        "interpretation": "Execution and model-isolation checks only; one case is not a generalization estimate and final full-DEV model is not used as the held model",
    }
    save_private(destination / "live_and_held_public_summary.private.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", required=True, type=Path)
    parser.add_argument("--phase", choices=["outer-a0", "final"], required=True)
    parser.add_argument("--fold", type=int, default=0, choices=[0, 1, 2])
    args = parser.parse_args()
    report = (
        verify_outer_a0(args.owner_dir, args.fold)
        if args.phase == "outer-a0"
        else verify_final(args.owner_dir, args.fold)
    )
    print(json.dumps(report, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
