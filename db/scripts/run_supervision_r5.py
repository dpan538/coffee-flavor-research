#!/usr/bin/env python3
"""R5 actual registration, supervision fits, sealed replay and JSON inference."""

from __future__ import annotations
import argparse
import copy
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from threadpoolctl import threadpool_limits
import train_supervision_r5 as head

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-sequential-model-v2/revisions/r5"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value, private=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    )
    if private:
        path.chmod(0o600)


def freeze(owner):
    import data_supervision_r5 as data
    import information_supervision_r5 as information

    path = OUT / "experiment_contract.json"
    if path.exists():
        return read(path)
    deleted = sorted(
        subprocess.check_output(
            ["git", "ls-files", "--deleted"], cwd=ROOT, text=True
        ).splitlines()
    )
    if deleted != sorted(
        read(owner / "revisions/r3/excluded_worktree_deletions.private.json")
    ):
        raise ValueError("UNRELATED_DELETION_SCOPE_CHANGED")
    value = {
        "experiment_id": "M2_R5_SUPERVISION_AND_INFORMATION_VALUE",
        "registered_utc": now(),
        "data_supervision": data.proposal(),
        "source_parse_sha256": head.digest(
            read(owner / "revisions/r5/zenodo_source_parse.private.json")
        ),
        "mapping_choice": data.proposal()["mapping_choice"],
        "information_protocol": information.protocol(),
        "actual_baseline_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "expected_baseline_sha": "0eaea74f86660c1c186aec5ad72384493cde6cb0",
        "configuration": head.protocol(),
        "supervision": {
            "A": "First real grader row in frozen R4 global grader order, even if its strict mapped concepts are empty",
            "B": "Second distinct real grader row, even if strict mapping empty",
            "T": "All remaining distinct grader rows; positive mention frequencies, full fixed T retains concepts also present in A",
            "hidden_T": "Full fixed T minus exact source A concepts; never updated after B",
            "mapping": "Frozen strict D0 governed concepts; source-native ordinals audited separately, no quality/liking substitution",
            "roles": "Raw observation-unit isolation, not required conceptual disjointness; no role rotations",
            "cohort": "Named existing source samples with >=3 original grader observations; old95 development sample scope retained, old17 history separate; anonymous source identities excluded from cross-grader task",
            "increment": "Recover task-usable raw-role records dropped by nonempty mapped-grader rule; count as new task pairs, not new independent coffees or collection",
            "reference_limits": "Shared coffee/session, unverified blinding, shared graders across coffee folds; no personal sensory truth",
        },
        "information": {
            "scorer": "Existing isolated A0 R1 outer and R2 inner base experts wrapped by unchanged R4 A0",
            "I0": "Actual Q0/Q1 encoded selections",
            "I1": "Actual current-bank Q4 ASK selections; positive-text nonmention corrected to UNSURE in all R5 branches",
            "I2": "One existing-axis scheme: train-coffee-macro B coverage doubled for current A shared attribute, deterministic tie; same question/option budget, no current B/T choice",
            "I_FULL": "Keep I0 encoded A and add all actual B positive observations; same scorer, diagnostic outside budget; no source A unselected expansion",
            "legacy": "R4 negative/nonmention behavior preserved as history, not repeated in R5 input",
            "nested": "Each training row uses its inner-held question expert excluding the entire outer-held groups; no OOF-only shortcut",
            "context": "Fixed synthetic legal C0/C1 engineering context for description-source simulations, NOT observed production context or C0/C1 effect estimation",
            "oracle": "Posthoc best legal ASK/SKIP only diagnostic, never deployable",
            "effect_margin": "No new noninferiority gate; historical0.02 remains operational, not user acceptance",
        },
        "rights": "Source-specific restrictive intersection noncommercial research, private raw data and weights; publication rights separate",
        "new_sources": "Admission and any new task require typed identity/rights/measurement record before fit; predefined hash split for genuinely new groups, no effect-driven admission",
        "product": "B2 default; FOUNDATION_CHECK off; C0 eight/C1 seven required; ASK_Q3 or SKIP_Q3 to Q4; Q4/Q5 endpoint; one actual3–8 final comparison; main<=5 secondary<=3",
        "not_evaluated": ["REAL_USER_SENSORY_ALIGNMENT", "REAL_COMPLETION_TIME"],
        "preserved": {
            "R4_completion_manifest": (
                sha(
                    owner / "revisions/r4/conditioning_completion_manifest.private.json"
                )
                if (
                    owner / "revisions/r4/conditioning_completion_manifest.private.json"
                ).exists()
                else sha(
                    ROOT
                    / "db/data/backend-sequential-model-v2/revisions/r4/run_receipt.json"
                )
            ),
            "R4_metrics": sha(
                ROOT / "db/data/backend-sequential-model-v2/revisions/r4/metrics.json"
            ),
            "deleted_paths_sha256": head.digest(deleted),
            "deleted_count": len(deleted),
        },
    }
    save(path, value, False)
    save(owner / "revisions/r5/experiment_contract.frozen.json", value)
    return value


def adapt(row):
    selected = row["selected"]
    return {
        **row,
        "initial_selected": selected["I0"],
        "selected": {
            "ASK": selected["I1"],
            "SKIP": selected["SKIP"],
            "Q2": selected["Q2"],
        },
        "full_T": row["relevance"],
        "hidden_T": row["hidden_relevance"],
    }


def score_rows(rows, model, branch="ASK"):
    return [
        head.evaluate(row, *head.predict(row, model, branch), branch=branch)
        for row in rows
    ]


def train(owner, checkpoint=False, destination=None):
    private = owner / "revisions/r5"
    contract = read(OUT / "experiment_contract.json")
    if contract["configuration"] != head.protocol():
        raise ValueError("FROZEN_TRAINING_PROTOCOL_CHANGED")
    raw_held = read(private / "information_cases.private.json")
    raw_nested = read(private / "information_nested_training.private.json")
    held_all = [adapt(r) for r in raw_held]
    old_ids = {
        r["record_id"]
        for r in read(owner / "revisions/r4/cross_grader_episodes.private.json")
    }
    destination = destination or (
        private / ("checkpoint1" if checkpoint else "training")
    )
    if (destination / "receipt.private.json").exists():
        raise ValueError("SEALED_RUN_EXISTS_USE_REPLAY_OR_NEW_RETRAIN_DESTINATION")
    records, models, per_fold, mismatches = [], [], [], []
    input_hashes = {
        "information_cases.private.json": sha(
            private / "information_cases.private.json"
        ),
        "information_nested_training.private.json": sha(
            private / "information_nested_training.private.json"
        ),
        "experiment_contract.json": sha(OUT / "experiment_contract.json"),
    }
    started = now()
    for outer in ([0] if checkpoint else [0, 1, 2]):
        held = [r for r in held_all if r["fold"] == outer]
        train_rows = [adapt(r) for r in raw_nested[str(outer)]]
        train_groups = {r["group_id"] for r in train_rows}
        held_groups = {r["group_id"] for r in held}
        if train_groups & held_groups or not train_groups or not held_groups:
            raise ValueError("OUTER_COFFEE_GROUP_ISOLATION_FAILURE")
        for row in train_rows:
            if set(row["base_training_groups"]) & (held_groups | {row["group_id"]}):
                raise ValueError("NESTED_QUESTION_EXPERT_LEAKAGE")
        configurations = [("T1_A", train_rows, "T1"), ("T2_AB", train_rows, "T2")]
        if not checkpoint:
            original = [r for r in train_rows if r["record_id"] in old_ids]
            wrong, info = head.mismatch(train_rows)
            mismatches.append({"outer": outer, **info})
            configurations += [
                ("T3_BEFORE_RECOVERED_PAIRS", original, "T2"),
                ("T2_50_PERCENT_GROUPS", head.subset(train_rows, 0.5), "T2"),
                ("T2_MISMATCHED_B", wrong, "T2"),
            ]
        for name, fitting, variant in configurations:
            model = head.fit(
                fitting,
                variant,
                {"outer": outer, "input_sha256": input_hashes, "experiment": name},
            )
            model_path = (
                destination / "models" / (name + "_outer" + str(outer) + ".json")
            )
            save(model_path, model)
            models.append(
                {
                    "name": name,
                    "outer": outer,
                    "path": str(model_path.relative_to(destination)),
                    "sha256": sha(model_path),
                }
            )
            evaluated = score_rows(held, model)
            train_evaluated = score_rows(fitting, model)
            for row in evaluated:
                row.update(
                    outer=outer,
                    model=name,
                    original_R4_cohort=row["record_id"] in old_ids,
                )
            records += evaluated
            per_fold.append(
                {
                    "outer": outer,
                    "name": name,
                    "training": head.aggregate(train_evaluated),
                    "held": head.aggregate(evaluated),
                    "optimization": model["optimization"],
                }
            )
        # T0 is a training-side frequency ranking, not an incompatible B2 score.
        usable = [r for r in train_rows if head.targets(r) is not None]
        p = head.weights(usable) @ np.stack([head.targets(r) for r in usable])
        ranking = sorted(
            head.CANDIDATES, key=lambda c: (-float(p[head.CANDIDATES.index(c)]), c)
        )
        for row in held:
            value = head.evaluate(row, ranking, np.log(p + 1e-12))
            value.update(
                outer=outer,
                model="T0_TRAIN_FREQUENCY",
                original_R4_cohort=row["record_id"] in old_ids,
            )
            records.append(value)
    summaries = {
        name: head.aggregate([r for r in records if r["model"] == name])
        for name in sorted({r["model"] for r in records})
    }
    contrasts = {
        "T2_minus_T1": head.paired(
            [r for r in records if r["model"] == "T1_A"],
            [r for r in records if r["model"] == "T2_AB"],
        )
    }
    if not checkpoint:
        contrasts["T3_after_minus_before"] = head.paired(
            [r for r in records if r["model"] == "T3_BEFORE_RECOVERED_PAIRS"],
            [r for r in records if r["model"] == "T2_AB"],
        )
        contrasts["T2_real_B_minus_mismatched_B"] = head.paired(
            [r for r in records if r["model"] == "T2_MISMATCHED_B"],
            [r for r in records if r["model"] == "T2_AB"],
        )
        final = head.fit(
            held_all,
            "T2",
            {
                "scope": "All-development final refit from each group's outer-held question trace, no independent confirmation",
                "input_sha256": input_hashes,
            },
        )
        save(destination / "models/R5_RESEARCH_HEAD.json", final)
        models.append(
            {
                "name": "FINAL_RESEARCH_ONLY",
                "path": "models/R5_RESEARCH_HEAD.json",
                "sha256": sha(destination / "models/R5_RESEARCH_HEAD.json"),
            }
        )
    summary = {
        "status": "RESEARCH_ONLY_NO_DEFAULT_CHANGE",
        "task": head.protocol()["task"],
        "summaries": summaries,
        "contrasts": contrasts,
        "per_fold": per_fold,
        "negative_control": mismatches,
        "increment_cohorts": {
            label: {
                name: head.aggregate(
                    [
                        r
                        for r in records
                        if r["model"] == name and r["original_R4_cohort"] == old
                    ]
                )
                for name in summaries
            }
            for label, old in [
                ("ORIGINAL_R4_TASK", True),
                ("RECOVERED_TASK_PAIRS", False),
            ]
        },
        "interpretation": "Full independent-grader positive mention alignment, not absolute truth or observed sequential user benefit; all viewed data development scope",
        "real_user_judgment": "NOT_EVALUATED",
        "real_completion_time": "NOT_EVALUATED",
    }
    save(destination / "predictions.private.json", records)
    save(destination / "summary.private.json", summary)
    receipt = {
        "started_utc": started,
        "finished_utc": now(),
        "input_hashes": input_hashes,
        "code_sha256": {Path(p).name: sha(p) for p in [__file__, head.__file__]},
        "models": models,
        "artifacts": {
            name: sha(destination / name)
            for name in ["predictions.private.json", "summary.private.json"]
        },
    }
    save(destination / "receipt.private.json", receipt)
    return summary


def replay(owner, destination=None):
    destination = destination or owner / "revisions/r5/training"
    receipt = read(destination / "receipt.private.json")
    for name, expected in receipt["input_hashes"].items():
        path = (
            OUT / name
            if name == "experiment_contract.json"
            else owner / "revisions/r5" / name
        )
        if sha(path) != expected:
            raise ValueError("SEALED_INPUT_HASH_CHANGED:" + name)
    for name, expected in receipt["artifacts"].items():
        if sha(destination / name) != expected:
            raise ValueError("SEALED_ARTIFACT_HASH_CHANGED")
    raw = [
        adapt(r) for r in read(owner / "revisions/r5/information_cases.private.json")
    ]
    expected = read(destination / "predictions.private.json")
    checked, corrected = 0, []
    for entry in receipt["models"]:
        path = destination / entry["path"]
        if sha(path) != entry["sha256"]:
            raise ValueError("SEALED_MODEL_CHANGED")
        model = read(path)
        head.check_model(model)
        if "outer" not in entry:
            continue
        actual = score_rows([r for r in raw if r["fold"] == entry["outer"]], model)
        original = {
            r["record_id"]: r
            for r in expected
            if r["model"] == entry["name"] and r["outer"] == entry["outer"]
        }
        if len(original) != len(actual) or set(original) != {
            r["record_id"] for r in actual
        }:
            raise ValueError("SEALED_REPLAY_ID_SET_MISMATCH")
        for row in actual:
            stable = [
                "record_id",
                "group_id",
                "raw_gap",
                "hidden_gap",
                "ndcg",
                "hidden_ndcg",
                "legacy_R4_recovery_gap",
                "recall",
                "coverage",
                "positive_mention_CE",
            ]
            if any(row[k] != original[row["record_id"]][k] for k in stable):
                raise ValueError("SEALED_PREDICTION_REPLAY_MISMATCH")
            corrected.append({**original[row["record_id"]], **row})
            checked += 1
    return {
        "status": "PASS",
        "replayed_predictions": checked,
        "fit_count": 0,
        "checked_utc": now(),
        "reporting_correction": "Direct versus inferred contribution now uses all actually selected fine concepts at the evaluated branch; initial/later contributions separate. Original sealed reports retained; primary gap/ranking/loss values replay exactly.",
        "corrected_summaries": {
            name: head.aggregate([r for r in corrected if r["model"] == name])
            for name in sorted({r["model"] for r in corrected})
        },
    }


def prepare_from_source(owner):
    import data_supervision_r5 as source
    import information_supervision_r5 as information

    parsed = source.parse_source(owner)
    contract = read(OUT / "experiment_contract.json")
    if head.digest(parsed) != contract["source_parse_sha256"]:
        raise ValueError("RAW_SOURCE_REBUILD_DIFFERS_FROM_FROZEN_PARSE")
    if information.protocol() != contract["information_protocol"]:
        raise ValueError("RAW_SOURCE_REBUILD_INFORMATION_PROTOCOL_CHANGED")
    if head.digest(parsed) != head.digest(
        read(owner / "revisions/r5/zenodo_source_parse.private.json")
    ):
        raise ValueError("RAW_SOURCE_PARSE_CACHE_MISMATCH")
    information.run(owner, OUT / "experiment_contract.json")


def infer(owner, request, model_path=None):
    import flavor_conditioning_r4 as runtime
    import audit_revelation_r4 as audit

    base = read(owner / "revisions/r4/models/R4_ALL_DEVELOPMENT_RESEARCH.model.json")
    model = read(
        model_path or owner / "revisions/r5/training/models/R5_RESEARCH_HEAD.json"
    )
    # The original backend enforces context, actual exposure, path and final-once.
    product = runtime.run(request, base)
    state = runtime.initial_state(
        request["context"],
        base,
        request.get("variant", base["selected_variant"]),
        request.get("trigger_policy", "KEY_CASE"),
    )
    for batch in request.get("answers", []):
        for answer in batch if isinstance(batch, list) else [batch]:
            state = runtime.update_state(state, answer, base)
    answers = state["base_state"]["answers_by_question"]
    initial, total = set(), set()
    for slot, answer in answers.items():
        current = audit.canonical_selection(answer)
        total |= current
        if slot in {"Q0", "Q1"}:
            initial |= current
    row = {"initial_selected": sorted(initial), "selected": {"ASK": sorted(total)}}
    ranking, _ = head.predict(row, model)
    return {
        "contract_version": head.VERSION,
        "default_model": "B2_UNCHANGED",
        "validated_R4_workflow": product,
        "research_head": {
            "scope": "Read-only research scoring of validated acquired observations; does not alter frozen R4 question/final-feedback engine or default",
            "stage_eligible": "Q4" in answers or "Q5" in answers,
            "main": ranking[:5] if "Q4" in answers or "Q5" in answers else [],
            "secondary": ranking[5:8] if "Q4" in answers or "Q5" in answers else [],
            "final_feedback_training": "NOT_EVALUATED_NO_NEW_FEEDBACK_BRANCH",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "phase", choices=["freeze", "train", "checkpoint", "retrain", "replay", "infer"]
    )
    parser.add_argument("--owner-dir", required=True, type=Path)
    parser.add_argument("--request", type=Path)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.phase == "freeze":
            value = freeze(args.owner_dir)
        elif args.phase in {"train", "checkpoint", "retrain"}:
            if args.phase == "retrain":
                prepare_from_source(args.owner_dir)
            destination = (
                args.owner_dir
                / "revisions/r5/retrains"
                / datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y%m%dT%H%M%S%fZ"
                )
                if args.phase == "retrain"
                else None
            )
            value = train(args.owner_dir, args.phase == "checkpoint", destination)
        elif args.phase == "replay":
            value = replay(args.owner_dir)
        else:
            if args.request is None:
                raise ValueError("LIVE_REQUEST_FILE_REQUIRED")
            value = infer(args.owner_dir, read(args.request))
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
