"""Portable C01 research candidate: frozen A0 + MAP_BASE + I2_LIVE.

Not B2 and not the archived R6 linear head. No fitting in this module.
"""

from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter
import flavor_m2_r1 as r1
import flavor_conditioning_r4 as runtime
import information_supervision_r6 as acquisition
import train_conditioning_r4 as training
from train_coordination_r2 import audit_expert, expert_training_groups
from flavor_backend import validate_context, C0, C1
from train_supervision_r5 import CANDIDATES as EVALUATION_CANDIDATES

VERSION = "m2-r7-c01-portable.v1"
MODEL_KIND = "M2_R7_C01_A0_MAP_BASE_I2_LIVE"
OFFLINE = "OFFLINE_EXISTING_NEUTRAL_CONTEXT_EFFECTS_DISABLED"
ROOT = Path(__file__).resolve().parents[2]


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_hashes():
    names = [
        "candidate_c01_r7.py",
        "information_supervision_r6.py",
        "r6_mapping_i2_helpers.py",
        "information_supervision_r5.py",
        "flavor_conditioning_r4.py",
        "flavor_m2_r1.py",
        "flavor_planning.py",
        "flavor_context.py",
        "alignment_metrics_r3.py",
    ]
    return {n: sha(Path(__file__).parent / n) for n in names}


def check(package, verify_code=True):
    if package.get("model_kind") != MODEL_KIND or package.get("version") != VERSION:
        raise ValueError("C01_MODEL_IDENTITY_REQUIRED_NOT_R6_HEAD_OR_B2")
    content = {k: v for k, v in package.items() if k != "package_id"}
    if package.get("package_id") != "C01:" + digest(content):
        raise ValueError("C01_PACKAGE_HASH_MISMATCH")
    if verify_code and package["code_hashes"] != code_hashes():
        raise ValueError("C01_CODE_VERSION_MISMATCH")
    if (
        package["ordinary_option_budgets"] != acquisition.BUDGETS
        or package["related_multiplier"] != 2.0
    ):
        raise ValueError("FROZEN_ACQUISITION_CHANGED")
    b = package["runtime_bundle"]
    runtime.check_bundle(b)
    if b["selected_variant"] != "A0" or b["r1_expert"]["model_kind"] != "M2_R1_FIXED":
        raise ValueError("C01_REQUIRES_FROZEN_A0")
    if package["A0_parameter_sha256"] != digest(b["r1_expert"]["model_parameters"]):
        raise ValueError("A0_PARAMETERS_CHANGED")
    expert = b["r1_expert"]
    groups = sorted(expert_training_groups(expert))
    if (
        package["scorer_training_groups"] != groups
        or package["audit"]["training_groups"] != groups
    ):
        raise ValueError("C01_SCORER_LINEAGE_METADATA_MISMATCH")
    if (
        package["source_feature_vocabulary"] != expert["candidate_vocabulary"]
        or package["generation_candidate_universe"] != b["fixed_candidates"]
        or package["fixed_evaluation_candidate_universe"] != EVALUATION_CANDIDATES
    ):
        raise ValueError("C01_VOCABULARY_METADATA_MISMATCH")
    if (
        package["question_bank_sha256"] != digest(expert["question_bank"])
        or package["parent_relations_sha256"] != digest(r1.PARENTS)
        or package["A0_expert_content_sha256"] != digest(expert)
    ):
        raise ValueError("C01_EXPERT_METADATA_MISMATCH")
    if not set(package["coverage_training_groups"]) <= set(groups):
        raise ValueError("C01_COVERAGE_OUTSIDE_DECLARED_TRAINING")
    if (
        package["scorer_training_records"] != package["audit"]["training_record_count"]
        or package["scorer_source_families"]
        != package["audit"]["training_source_family_counts"]
        or sum(package["scorer_source_families"].values())
        != package["scorer_training_records"]
    ):
        raise ValueError("C01_TRAINING_COUNTS_METADATA_MISMATCH")
    role = package["artifact_role"]
    if role == "FULL_DEVELOPMENT_CANDIDATE":
        if (
            package.get("outer_fold") is not None
            or package["A0_source_owner_relative_path"]
            != "revisions/r4/models/R4_ALL_DEVELOPMENT_RESEARCH.model.json"
        ):
            raise ValueError("C01_FULL_DEVELOPMENT_IDENTITY_MISMATCH")
    elif role == "HISTORICAL_OUTER_FOLD_REPLAY":
        if (
            package.get("outer_fold") not in [0, 1, 2]
            or package["A0_source_owner_relative_path"]
            != f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{package['outer_fold']}.model.json"
        ):
            raise ValueError("C01_OUTER_IDENTITY_MISMATCH")
    else:
        raise ValueError("C01_EXPLICIT_ARTIFACT_ROLE_REQUIRED")
    return package


def load_bundle(path):
    return check(json.loads(Path(path).read_text()))


def neutral_eligible(package):
    e = package["runtime_bundle"]["r1_expert"]
    names = e["model_parameters"]["feature_names"]
    weights = e["model_parameters"]["weights"]
    if any(
        weights[names.index(n)] != 0
        for n in ["context_c0", "context_c1", "context_answer_interaction"]
    ):
        raise ValueError("OFFLINE_NEUTRAL_REQUIRES_ZERO_CONTEXT_WEIGHTS")
    for context in ({"c0": C0[0], "c1": C1[0]}, {"c0": C0[-1], "c1": C1[-1]}):
        encoded = r1.encode_features(r1.initial_state(context, e), e)
        if any(
            row[names.index(n)] != 0
            for row in encoded["raw_features"]
            for n in ["context_c0", "context_c1", "context_answer_interaction"]
        ):
            raise ValueError("OFFLINE_NEUTRAL_REQUIRES_ZERO_RAW_CONTEXT")
    return True


def initial(context, package, mode="PRODUCTION"):
    check(package)
    if mode == "PRODUCTION":
        validate_context(context)
    elif mode == OFFLINE:
        if context is not None:
            raise ValueError("OFFLINE_NEUTRAL_REQUIRES_EXPLICIT_MISSING_SOURCE_CONTEXT")
        neutral_eligible(package)
        context = {"c0": C0[0], "c1": "medium"}
    else:
        raise ValueError("DECLARED_EXECUTION_MODE_REQUIRED")
    state = acquisition.initial_state(context, package["runtime_bundle"])
    state["r7_execution_mode"] = mode
    state["r7_source_context_observed"] = mode == "PRODUCTION"
    return state


def select(state, package, policy="I2_LIVE"):
    check(package)
    policy = {"C00": "POLICY_BASE", "C01": "I2_LIVE"}.get(policy, policy)
    if policy not in {"I2_LIVE", "POLICY_BASE"}:
        raise ValueError("FIXED_C00_C01_POLICY_REQUIRED")
    prepared, plan = acquisition.select(
        state, package["runtime_bundle"], package["training_B_coverage"], policy
    )
    for k in ["r7_execution_mode", "r7_source_context_observed"]:
        prepared[k] = state[k]
    return prepared, plan


def update(state, answer, package):
    check(package)
    out = acquisition.update(state, answer, package["runtime_bundle"])
    for k in ["r7_execution_mode", "r7_source_context_observed"]:
        out[k] = state[k]
    return out


def run(payload, package, policy=None):
    check(package)
    allowed = {
        "contract_version",
        "context",
        "execution_mode",
        "policy",
        "answers",
        "final_comparison",
        "final_mode",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) - allowed
        or payload.get("contract_version") != VERSION
    ):
        raise ValueError("R7_REQUEST_SCHEMA")
    mode = payload.get("execution_mode", "PRODUCTION")
    if mode != "PRODUCTION":
        raise ValueError(
            "INFER_REQUIRES_PRODUCTION_CONTEXT_USE_OFFLINE_CASE_FOR_SOURCE_RECORDS"
        )
    policy = policy or payload.get("policy", "I2_LIVE")
    state = initial(payload.get("context"), package, mode)
    answers = payload.get("answers", [])
    if not isinstance(answers, list):
        raise ValueError("ANSWERS_ARRAY_REQUIRED")
    for answer in answers:
        if answer.get("slot") in state["base_state"]["answers_by_question"]:
            state = update(state, answer, package)
        else:
            prepared, plan = select(state, package, policy)
            if plan["action"] != "ASK":
                raise ValueError("NO_MORE_ORDINARY_QUESTIONS")
            state = update(prepared, answer, package)
    if "final_comparison" in payload:
        state = runtime.apply_final_comparison(
            state,
            payload["final_comparison"],
            package["runtime_bundle"],
            payload.get("final_mode", "F2"),
        )
    state["r7_execution_mode"] = mode
    state["r7_source_context_observed"] = mode == "PRODUCTION"
    prepared, nextplan = select(state, package, policy)
    # Result availability and one-final semantics remain the original backend's.
    final = runtime.finalize_result(state, package["runtime_bundle"])
    out = {
        "contract_version": VERSION,
        "package_id": package["package_id"],
        "model_kind": MODEL_KIND,
        "default": "B2_UNCHANGED",
        "policy": policy,
        "execution_mode": mode,
        "source_context_observed": mode == "PRODUCTION",
        "context_descriptor_effects": "DISABLED_UNSUPPORTED_ZERO_FEATURES",
        "next": nextplan,
        "main": (
            final["main"] if "Q4" in state["base_state"]["answers_by_question"] else []
        ),
        "secondary": (
            final["secondary"]
            if "Q4" in state["base_state"]["answers_by_question"]
            else []
        ),
        "stage": final["stage"],
        "exposure": final["exposure"],
        "final_comparison": final["state"]["base_state"].get("final_comparison"),
        "ordinary_questions": len(state["base_state"]["answers_by_question"]),
        "ordinary_options": sum(
            len(a["shown_option_ids"])
            for a in state["base_state"]["answers_by_question"].values()
        ),
        "source_native_context_attribute_predictions": "NOT_EVALUATED_IN_C01",
        "real_human_time": "NOT_EVALUATED",
    }
    return out


def build(owner, contract_path):
    owner = Path(owner)
    contract_path = Path(contract_path)
    if not contract_path.exists():
        raise ValueError("R7_CONTRACT_MUST_EXIST_BEFORE_PACKAGE_BUILD")
    sourcepath = owner / "revisions/r4/models/R4_ALL_DEVELOPMENT_RESEARCH.model.json"
    expert = json.loads(sourcepath.read_text())["r1_expert"]
    records = json.loads((owner / "recovery_records.json").read_text())
    groups = expert_training_groups(expert)
    fitted = [r for r in records if r["group_id"] in groups]
    held = [r for r in records if r["group_id"] not in groups]
    audit = audit_expert(expert, fitted, held)
    audit.update(
        training_record_count=len(fitted),
        training_source_family_counts=dict(Counter(r["source_family"] for r in fitted)),
    )
    source = owner / "revisions/r6/source_inputs.private.json"
    coverage_rows = json.loads(source.read_text())
    if any(
        r["old_split"] != "DEVELOPMENT" or r["group_id"] not in groups
        for r in coverage_rows
    ):
        raise ValueError("COVERAGE_REQUIRES_DECLARED_DEVELOPMENT_ONLY")
    coverage = acquisition.coverage_for(coverage_rows, {r["group_id"] for r in held})
    bundle = training.model_bundle(expert, tag="R7_C01_FROZEN_ALL_DEVELOPMENT_A0")
    package = {
        "version": VERSION,
        "model_kind": MODEL_KIND,
        "role": "PRIORITY_CONFIRMATION_CANDIDATE",
        "artifact_role": "FULL_DEVELOPMENT_CANDIDATE",
        "outer_fold": None,
        "A0_expert_content_sha256": digest(expert),
        "runtime_bundle": bundle,
        "A0_parameter_sha256": digest(expert["model_parameters"]),
        "A0_source_artifact_sha256": sha(sourcepath),
        "A0_source_owner_relative_path": str(sourcepath.relative_to(owner)),
        "scorer_training_groups": sorted(groups),
        "scorer_training_records": len(fitted),
        "scorer_source_families": dict(Counter(r["source_family"] for r in fitted)),
        "training_B_coverage": coverage,
        "coverage_training_groups": sorted({r["group_id"] for r in coverage_rows}),
        "coverage_records": len(coverage_rows),
        "coverage_source_artifact_sha256": sha(source),
        "MAP_BASE_version": json.loads(
            (
                ROOT
                / "db/data/backend-sequential-model-v2/revisions/r5/experiment_contract.json"
            ).read_text()
        )["mapping_choice"],
        "question_bank_sha256": digest(expert["question_bank"]),
        "parent_relations_sha256": digest(r1.PARENTS),
        "related_multiplier": 2.0,
        "ordinary_option_budgets": copy.deepcopy(acquisition.BUDGETS),
        "source_feature_vocabulary": expert["candidate_vocabulary"],
        "generation_candidate_universe": bundle["fixed_candidates"],
        "fixed_evaluation_candidate_universe": EVALUATION_CANDIDATES,
        "code_hashes": code_hashes(),
        "contract_sha256": sha(contract_path),
        "new_scorer_fits": 0,
        "refit_status": "NOT_EXECUTED_EXISTING_A0_REUSE_VERIFIED",
        "scope": "Repeatedly viewed development data; independent confirmation pending; full-development package has no inherited outer-held effect estimate",
        "excluded_claims": [
            "B2_DEFAULT",
            "R6_ARCHIVED_LINEAR_HEAD",
            "VALIDATED_CONTEXT_EFFECT",
            "REAL_HUMAN_DURATION",
        ],
        "audit": audit,
    }
    package["package_id"] = "C01:" + digest(package)
    check(package)
    neutral_eligible(package)
    return package


def offline_case(record, package, policy="C01", allow_development=False):
    """Static independent provider; never creates real sequential user observations."""
    seen = set(package["scorer_training_groups"]) | set(
        package["coverage_training_groups"]
    )
    if not allow_development and record["group_id"] in seen:
        raise ValueError("CONFIRMATION_GROUP_PREVIOUSLY_USED")
    context = (
        {"c0": record["source_C0"], "c1": record["source_C1"]}
        if record.get("source_C0") is not None and record.get("source_C1") is not None
        else None
    )
    mode = "PRODUCTION" if context is not None else OFFLINE
    state = initial(context, package, mode)
    questions = []
    failure = None
    for slot in acquisition.BUDGETS:
        try:
            prepared, plan = select(state, package, policy)
        except ValueError as exc:
            if not str(exc).startswith("NO_LEGAL_AXIS_AT_FROZEN_BUDGET"):
                raise
            failure = {"slot": slot, "reason": str(exc)}
            break
        q = plan["question"]
        if q["slot"] != slot:
            raise ValueError("OFFLINE_FIXED_SLOT_MISMATCH")
        visible = (
            record["A"]
            if slot in {"Q0", "Q1"}
            else sorted(set(record["A"]) | set(record["B"]))
        )
        answer = acquisition.previous.source_answer(
            q, visible, package["runtime_bundle"]["r1_expert"]
        )
        state = update(prepared, answer, package)
        questions.append(q)
    final = runtime.finalize_result(state, package["runtime_bundle"])
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "questions": questions,
        "state": state,
        "ranking": [] if failure else state["candidate_scores"],
        "failure": failure,
        "status": "CAPACITY_FAILURE" if failure else "COMPLETE",
        "full_T": copy.deepcopy(record["relevance_full"]),
        "hidden_T": copy.deepcopy(record["relevance_unexpressed"]),
        "context_mode": mode,
        "source_context_observed": context is not None,
        "ordinary_questions": len(questions),
        "ordinary_options": sum(len(q["shown_option_ids"]) for q in questions),
        "proposed_final_candidates": (
            0 if failure else len(final["exposure"]["candidate_ids"])
        ),
        "actual_final_exposure": 0,
        "selected": acquisition.previous.selected(state),
    }


load = load_bundle


def context_audit(package):
    baseline = None
    contexts = 0
    for c0 in C0:
        for c1 in C1:
            state = initial({"c0": c0, "c1": c1}, package)
            trace = []
            for slot in acquisition.BUDGETS:
                prepared, plan = select(state, package)
                q = plan["question"]
                answer = {
                    k: q[k] for k in ["slot", "question_id", "axis", "shown_option_ids"]
                }
                answer.update(
                    selected_option_ids=q["shown_option_ids"][:1], state="SELECTED"
                )
                state = update(prepared, answer, package)
                trace.append(
                    {
                        "axis": q["axis"],
                        "options": q["shown_option_ids"],
                        "ranking": state["candidate_scores"],
                    }
                )
            signature = digest(trace)
            if baseline is None:
                baseline = signature
            if signature != baseline:
                raise ValueError("CONTEXT_CHANGES_C01_DESCRIPTOR_OUTPUT")
            contexts += 1
    return {
        "context_combinations": contexts,
        "all_descriptor_rankings_and_questions_identical": True,
        "scope": "Synthetic selected-option software test; not observed coffee context validation",
        "context_weights_and_raw_features_zero": neutral_eligible(package),
    }


def replay_r6(owner, package):
    owner = Path(owner)
    prior = owner / "revisions/r6"
    records = {
        r["record_id"]: r
        for r in json.loads((prior / "source_inputs.private.json").read_text())
    }
    cells = json.loads((prior / "matrix_cases.private.json").read_text())
    resources = json.loads((prior / "matrix_input_resources.private.json").read_text())
    original_records = json.loads((owner / "recovery_records.json").read_text())
    passed = 0
    counts = {}
    packages = {}
    for f in range(3):
        path = f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{f}.model.json"
        ex = json.loads((owner / path).read_text())
        resource = next(r for r in resources if r["key"] == [path, "MAP_BASE"])
        fold = copy.deepcopy(package)
        fold["runtime_bundle"] = training.model_bundle(ex)
        fold["A0_parameter_sha256"] = digest(ex["model_parameters"])
        fold["scorer_training_groups"] = sorted(expert_training_groups(ex))
        fold["coverage_training_groups"] = resource["training_groups"]
        fold["training_B_coverage"] = resource["coverage"]
        fold["scope"] = "R6_OUTER_HELD_REPLAY_ONLY_NOT_FULL_DEVELOPMENT_PACKAGE"
        fold["artifact_role"] = "HISTORICAL_OUTER_FOLD_REPLAY"
        fold["role"] = "HISTORICAL_REPLAY_NOT_CONFIRMATION_CANDIDATE"
        fold["outer_fold"] = f
        fold["A0_source_artifact_sha256"] = sha(owner / path)
        fold["A0_source_owner_relative_path"] = path
        fold["A0_expert_content_sha256"] = digest(ex)
        fold["source_feature_vocabulary"] = ex["candidate_vocabulary"]
        fold["generation_candidate_universe"] = fold["runtime_bundle"][
            "fixed_candidates"
        ]
        fold["question_bank_sha256"] = digest(ex["question_bank"])
        fitted = [
            r
            for r in original_records
            if r["group_id"] in set(fold["scorer_training_groups"])
        ]
        held = [
            r
            for r in original_records
            if r["group_id"] not in set(fold["scorer_training_groups"])
        ]
        fold["scorer_training_records"] = len(fitted)
        fold["scorer_source_families"] = dict(
            Counter(r["source_family"] for r in fitted)
        )
        fold["audit"] = audit_expert(ex, fitted, held)
        fold["audit"].update(
            training_record_count=len(fitted),
            training_source_family_counts=fold["scorer_source_families"],
        )
        fold["coverage_source_artifact_sha256"] = sha(
            prior / "matrix_input_resources.private.json"
        )
        fold["coverage_records"] = sum(
            r["group_id"] in set(resource["training_groups"]) for r in records.values()
        )

        fold["package_id"] = "C01:" + digest(
            {k: v for k, v in fold.items() if k != "package_id"}
        )
        packages[f] = fold
    for cell, policy in [("C00", "C00"), ("C01", "C01")]:
        counts[cell] = 0
        for original in cells[cell]:
            row = offline_case(
                records[original["record_id"]], packages[original["fold"]], policy
            )
            for a, b, name in [
                (row["questions"], original["questions"], "questions"),
                (row["ranking"], original["ranking"], "ranking"),
                (row["full_T"], original["full_T"], "fullT"),
                (row["hidden_T"], original["hidden_T"], "hiddenT"),
            ]:
                if a != b:
                    raise ValueError("R6_C01_REPLAY_CHANGED:" + name)
            if (
                row["ordinary_options"] != original["costs"]["ordinary_options"]
                or row["ordinary_questions"] != original["costs"]["ordinary_questions"]
            ):
                raise ValueError("R6_REPLAY_COST_CHANGED")
            passed += 1
            counts[cell] += 1
    return {
        "case_policy_replays": passed,
        "cells": counts,
        "questions_full_rankings_targets_costs_exact": True,
        "new_fits": 0,
        "source_matrix_sha256": sha(prior / "matrix_cases.private.json"),
        "source_resources_sha256": sha(prior / "matrix_input_resources.private.json"),
        "identity": "THREE_ORIGINAL_OUTER_HELD_A0_PACKAGES; full-development candidate is separate",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["build", "infer", "replay"])
    parser.add_argument("--owner-dir")
    parser.add_argument("--contract")
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--request")
    args = parser.parse_args()
    if args.phase == "build":
        package = build(args.owner_dir, args.contract)
        path = Path(args.bundle)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as out:
            json.dump(package, out, ensure_ascii=False, sort_keys=True, indent=2)
            out.write("\n")
        path.chmod(0o600)
        print(
            json.dumps(
                {
                    "package_id": package["package_id"],
                    "artifact_sha256": sha(path),
                    "new_fits": 0,
                }
            )
        )
    elif args.phase == "replay":
        print(
            json.dumps(
                replay_r6(args.owner_dir, load_bundle(args.bundle)), sort_keys=True
            )
        )
    else:
        payload = json.loads(
            Path(args.request).read_text() if args.request else sys.stdin.read()
        )
        print(
            json.dumps(
                run(payload, load_bundle(args.bundle)),
                ensure_ascii=False,
                allow_nan=False,
            )
        )


if __name__ == "__main__":
    main()
