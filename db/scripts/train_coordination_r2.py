"""Nested coffee-group cross-fitting for the bounded R2 coordination study."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

import alignment_metrics_r2 as metric
import evaluate_sequential_v2 as previous
import flavor_coordination_r2 as runtime
import flavor_m2_r1 as r1
import train_m2_r1 as training

GRID = [0.0, 0.25, 0.5, 0.75, 1.0]
RIDGE_ALPHA = 10.0
SHRINKAGE_GROUPS = 50
TEMPERATURE = 0.1
PATHS = ["P1", "P4"]


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    path.chmod(0o600)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def registered_config():
    return {
        "version": runtime.VERSION,
        "formal_fit_requires_frozen_objective_contract_hash": True,
        "expert_ids": runtime.EXPERTS,
        "feature_names": runtime.FEATURES,
        "paths": PATHS,
        "policy": "fixed",
        "outer_coffee_group_folds": 3,
        "router_inner_coffee_group_folds": 2,
        "R1_internal_feature_folds": 2,
        "expert_fit_C": 0.1,
        "expert_fit_loss": "layered_conditional",
        "expert_fit_canonical_broad_feedback": True,
        "global_weight_grid": GRID,
        "global_tie_break": "LOWER_R1_ALPHA_AFTER_LOSS_TIE_WITHIN_1E-12",
        "stage_names": runtime.STAGES,
        "stage_shrinkage": "UNIQUE_LABELLED_INNER_OOF_GROUPS/(GROUPS+50)",
        "G3_ridge_alpha": RIDGE_ALPHA,
        "G3_ridge_convention": "GROUP_WEIGHTED_ERROR_SUM_PLUS_10_TIMES_BETA_SQUARED",
        "G3_target": "B2_TYPED_GAP_MINUS_R1_RESIDUAL_GAP;POSITIVE_FAVORS_R1",
        "G3_local_alpha": "SIGMOID(PREDICTED_GAP_ADVANTAGE/0.1)",
        "G3_shrinkage": "STAGE_LOCAL_N/(N+50)_TO_G1",
        "feature_scaler": "GROUP_WEIGHTED_INNER_OOF_TRAIN_MEAN_STD_ONLY",
        "inner_training_aggregation": "EQUAL_COFFEE_THEN_RECORD_THEN_PATH_THEN_STAGE;EQUAL_PREFIX_WITHIN_STAGE",
        "candidate_scope": "COMMON_FINE_IDS_FROM_OUTER_TRAIN_QUALIFIED_ONTOLOGY",
        "shared_semantics": runtime.SHARED,
        "experts_have_direct_broad_rejection_feedback_terms_removed": True,
        "foundation_check_enabled": False,
        "router_training_states": "ORDINARY_PREFIXES_ONLY_NO_FINAL_FEEDBACK_LABELS",
        "final_novelty_coefficient": "ZERO_IF_UNOBSERVED_IN_TRAINING",
        "historical_prior_selection": "R1_C_AND_OLD_OUTER_RESULTS_ALREADY_INSPECTED;NOT_FRESH_CONFIRMATION",
        "weights_public_release": False,
    }


def expert_training_groups(expert):
    return {row["group_id"] for row in expert["statistics"]["planning_records"]}


def audit_expert(expert, train, held, verify_bank=True):
    train_groups = {row["group_id"] for row in train}
    held_groups = {row["group_id"] for row in held}
    if train_groups & held_groups:
        raise ValueError("TRAIN_HELD_COFFEE_GROUP_OVERLAP")
    if expert_training_groups(expert) != train_groups:
        raise ValueError("EXPERT_TRAINING_GROUPS_NOT_EXACT")
    if expert["training_split_hash"] != r1.digest(sorted(train_groups)):
        raise ValueError("EXPERT_TRAINING_SPLIT_HASH_MISMATCH")
    stats = training.statistics(train, expert["candidate_vocabulary"])
    if verify_bank:
        expected_bank = training.legacy.make_bank(stats, expert["candidate_attributes"])
        if expected_bank != expert["question_bank"]:
            raise ValueError("EXPERT_QUESTION_BANK_NOT_FROM_EXACT_TRAIN_GROUPS")
    stats.pop("vocabulary")
    if stats != expert["statistics"]:
        raise ValueError("EXPERT_STATISTICS_NOT_FROM_EXACT_TRAIN_GROUPS")
    if (
        expert["fit_receipt"]["C"] != 0.1
        or expert["fit_receipt"]["loss_mode"] != "layered_conditional"
        or expert["evidence_policy"]["canonical_broad_feedback"] is not True
    ):
        raise ValueError("REGISTERED_R1_EXPERT_SETTINGS_MISMATCH")
    feature_audits = expert["fit_receipt"]["inner_feature_audit"]
    for audit in feature_audits:
        output = set(audit["feature_output_groups"])
        fitted = set(audit["feature_training_groups"])
        if output & fitted or output | fitted != train_groups:
            raise ValueError("EXPERT_INTERNAL_FEATURE_ISOLATION_FAILED")
    return {
        "expert_bundle_id": expert["bundle_id"],
        "training_groups": sorted(train_groups),
        "held_groups": sorted(held_groups),
        "training_group_sha256": r1.digest(sorted(train_groups)),
        "held_group_sha256": r1.digest(sorted(held_groups)),
        "training_statistics_recomputed_identical": True,
        "training_bank_recomputed_identical": verify_bank,
        "internal_feature_group_isolation_verified": True,
        "train_record_sha256": r1.digest(train),
    }


def collect_predictions(records, expert, contract_hash, outer_fold, inner_fold=None):
    """Held labels enter the offline loss record only, never runtime features."""
    train_groups = expert_training_groups(expert)
    if train_groups & {row["group_id"] for row in records}:
        raise ValueError("EXPERT_PREDICTION_IS_NOT_OUT_OF_GROUP")
    coordinator = runtime.make_bundle(
        expert, runtime.default_router(), contract_hash, "OOF"
    )
    rows = []
    for record in records:
        for path in PATHS:
            episode, states, answers = training.trajectory(
                record, expert, path, "fixed"
            )
            for index, state in enumerate(states):
                predicted = runtime.expert_predictions(state, coordinator)
                features = runtime.live_features(state, predicted, coordinator)
                rows.append(
                    {
                        "record_id": record["record_id"],
                        "group_id": record["group_id"],
                        "source_family": record["source_family"],
                        "outer_fold": outer_fold,
                        "inner_fold": inner_fold,
                        "path": path,
                        "slot": "CONTEXT" if index == 0 else answers[index - 1]["slot"],
                        "stage": predicted["stage"],
                        "ordinary_endpoint": index == len(states) - 1,
                        "runtime_stage": state["current_stage"],
                        "episode": episode,
                        "predictions": predicted,
                        "live_features": features,
                        "cost": metric.information_cost(state),
                        **({"base_state": state} if inner_fold is None else {}),
                        "payload_answers": answers[:index],
                        "expert_bundle_id": expert["bundle_id"],
                        "expert_training_groups_sha256": r1.digest(
                            sorted(train_groups)
                        ),
                        "expert_training_groups": sorted(train_groups),
                        "out_of_group_verified": True,
                    }
                )
    return rows


def score_row(row, alpha):
    rank = runtime.rank_from_predictions(row["predictions"], [1 - alpha, alpha])
    return metric.semantic_gap(
        rank,
        row["episode"]["hidden"],
        excluded_visible=row["episode"]["visible"],
        vocabulary=row["predictions"]["candidate_ids"],
    )


def hierarchical_row_weights(rows):
    records, paths, stages, cells = (
        defaultdict(set),
        defaultdict(set),
        defaultdict(set),
        Counter(),
    )
    for row in rows:
        group, record, path, stage = (
            row[k] for k in ["group_id", "record_id", "path", "stage"]
        )
        records[group].add(record)
        paths[group, record].add(path)
        stages[group, record, path].add(stage)
        cells[group, record, path, stage] += 1
    return np.asarray(
        [
            1
            / (
                len(records[row["group_id"]])
                * len(paths[row["group_id"], row["record_id"]])
                * len(stages[row["group_id"], row["record_id"], row["path"]])
                * cells[row["group_id"], row["record_id"], row["path"], row["stage"]]
            )
            for row in rows
        ]
    )


def group_macro(rows, values):
    known = [(row, value) for row, value in zip(rows, values) if value is not None]
    if not known:
        return None
    return float(
        np.average(
            [value for _, value in known],
            weights=hierarchical_row_weights([row for row, _ in known]),
        )
    )


def choose_alpha(rows):
    losses = {
        alpha: group_macro(rows, [score_row(row, alpha) for row in rows])
        for alpha in GRID
    }
    valid = {a: value for a, value in losses.items() if value is not None}
    if not valid:
        return 0.0, losses
    minimum = min(valid.values())
    alpha = min(a for a, value in valid.items() if value <= minimum + 1e-12)
    return alpha, losses


def fit_router(oof_rows, allowed_training_groups, outer_held_groups=()):
    allowed, held = set(allowed_training_groups), set(outer_held_groups)
    actual = {row["group_id"] for row in oof_rows}
    if allowed & held or actual != allowed or actual & held:
        raise ValueError("ROUTER_TRAINING_GROUP_SCOPE_MISMATCH")
    if any(row.get("out_of_group_verified") is not True for row in oof_rows):
        raise ValueError("ROUTER_REQUIRES_VERIFIED_EXPERT_OUT_OF_GROUP_PREDICTIONS")
    for row in oof_rows:
        fitted = set(row.get("expert_training_groups", []))
        if (
            not fitted
            or row["group_id"] in fitted
            or not fitted <= allowed
            or fitted & held
            or r1.digest(sorted(fitted)) != row["expert_training_groups_sha256"]
        ):
            raise ValueError("ROUTER_EXPERT_PREDICTION_TRAINING_PROVENANCE_LEAK")
    if any(set(row["live_features"]) != set(runtime.FEATURES) for row in oof_rows):
        raise ValueError("ROUTER_CANNOT_USE_ID_SOURCE_OR_TARGET_FEATURES")
    alpha, grid_losses = choose_alpha(oof_rows)
    first = group_macro(oof_rows, [score_row(row, 0.0) for row in oof_rows])
    second = group_macro(oof_rows, [score_row(row, 1.0) for row in oof_rows])
    single = int(first is not None and second is not None and second < first - 1e-12)
    stage_alpha, stage_shrinkage, stage_log = {}, {}, {}
    for stage in runtime.STAGES:
        local = [row for row in oof_rows if row["stage"] == stage]
        local_alpha, local_losses = choose_alpha(local)
        groups = {row["group_id"] for row in local if score_row(row, alpha) is not None}
        shrinkage = len(groups) / (len(groups) + SHRINKAGE_GROUPS)
        stage_alpha[stage] = (1 - shrinkage) * alpha + shrinkage * local_alpha
        stage_shrinkage[stage] = shrinkage
        stage_log[stage] = {
            "groups": len(groups),
            "grid_losses": local_losses,
            "local_grid_alpha": local_alpha,
        }
    labelled = []
    for row in oof_rows:
        left, right = score_row(row, 0.0), score_row(row, 1.0)
        if left is not None and right is not None:
            labelled.append((row, left - right))
    if not labelled:
        raise ValueError("ROUTER_HAS_NO_IDENTIFIABLE_TRAINING_LOSS")
    counts = Counter(row["group_id"] for row, _ in labelled)
    w = hierarchical_row_weights([row for row, _ in labelled])
    X = np.asarray(
        [[row["live_features"][f] for f in runtime.FEATURES] for row, _ in labelled]
    )
    y = np.asarray([value for _, value in labelled])
    mean = np.average(X, weights=w, axis=0)
    scale = np.sqrt(np.average((X - mean) ** 2, weights=w, axis=0))
    scale[scale < 1e-8] = 1.0
    Z = (X - mean) / scale
    intercept = float(np.average(y, weights=w))
    with threadpool_limits(limits=1):
        beta = np.linalg.solve(
            Z.T @ (w[:, None] * Z) + RIDGE_ALPHA * np.eye(len(runtime.FEATURES)),
            Z.T @ (w * (y - intercept)),
        )
    return {
        "feature_names": runtime.FEATURES,
        "fit_status": "FITTED_FROM_NESTED_INNER_EXPERT_OOF",
        "single_expert_index": single,
        "global_alpha": alpha,
        "global_grid_losses": grid_losses,
        "single_expert_training_gaps": [first, second],
        "stage_alpha": stage_alpha,
        "stage_shrinkage": stage_shrinkage,
        "stage_training_audit": stage_log,
        "feature_mean": mean.tolist(),
        "feature_scale": scale.tolist(),
        "advantage_intercept": intercept,
        "advantage_coefficients": beta.tolist(),
        "advantage_temperature": TEMPERATURE,
        "ridge_alpha": RIDGE_ALPHA,
        "ridge_convention": registered_config()["G3_ridge_convention"],
        "advantage_target": registered_config()["G3_target"],
        "training_groups": sorted(allowed),
        "outer_held_groups": sorted(held),
        "training_rows": len(oof_rows),
        "labelled_training_rows": len(labelled),
        "labelled_training_groups": len(counts),
        "training_oof_sha256": r1.digest(oof_rows),
        "no_hyperparameter_search_beyond_declared_grid": True,
    }


def result_row(row, ranking, model, vocabulary, route=None, original_vocabulary=None):
    episode = row["episode"]
    measured = metric.semantic_result(
        ranking, episode["hidden"], episode["visible"], vocabulary=vocabulary
    )
    actual = metric.semantic_result(
        ranking[:5], episode["hidden"], vocabulary=vocabulary
    )
    ids = [r["candidate_id"] if isinstance(r, dict) else r for r in ranking]
    direct = set(row["predictions"]["evidence"]["confirmed"])
    exclude = set(episode["visible"]) | {
        "attribute." + a for c in episode["visible"] for a in r1.PARENTS.get(c, [])
    }
    recovery = [c for c in ids if c not in exclude]
    hidden = set(episode["hidden"])
    original_scope = vocabulary if original_vocabulary is None else original_vocabulary
    fine_hidden = {c for c in hidden if c.startswith("sensory.")}
    return {
        **{
            k: row[k]
            for k in [
                "record_id",
                "group_id",
                "source_family",
                "outer_fold",
                "path",
                "slot",
                "stage",
            ]
        },
        "model": model,
        "variant": model,
        "fold": row["outer_fold"],
        "ordinary_endpoint": row["ordinary_endpoint"],
        "runtime_stage": row["runtime_stage"],
        **measured,
        "actual_display_top5_gap": actual["gap"],
        "direct_retention5": (
            len(set(ids[:5]) & direct) / len(direct) if direct else None
        ),
        "ndcg5_full_hierarchy": (
            training.ndcg(recovery, episode["relevance"]) if hidden else None
        ),
        "recall5_full_hierarchy": (
            len(set(recovery[:5]) & hidden) / len(hidden) if hidden else None
        ),
        "full_output_available": bool(ids[:5]),
        "output_candidate_count": len(ids[:5]),
        "ranking": ids,
        "recovery_ranking": recovery,
        "candidate_vocabulary": vocabulary,
        "original_candidate_vocabulary": original_scope,
        "original_fine_target_coverage": (
            len(fine_hidden & set(original_scope)) / len(fine_hidden)
            if fine_hidden
            else None
        ),
        "target_sha256": r1.digest(episode["hidden"]),
        "visible_sha256": r1.digest(episode["visible"]),
        "cost": row["cost"],
        **row["cost"],
        "episode": episode,
        "route": route,
        "proxy_status": "NESTED_DEVELOPMENT_RECORD_COMPLETION_NOT_REAL_USER_ALIGNMENT",
    }


def evaluate_outer(rows, bundle):
    results = []
    expert = bundle["r1_expert"]
    for row in rows:
        state = row["base_state"]
        for variant in ["G0", "G1", "G2", "G3"]:
            live = runtime.rank_candidates(state, bundle, variant)
            results.append(
                result_row(
                    row,
                    live["candidate_scores"],
                    variant,
                    bundle["candidate_vocabulary"],
                    {
                        "weights": live["routing_weights"],
                        "features": live["routing_features"],
                    },
                )
            )
        # The two eligible components are also retained individually; neither
        # should be labelled as the unchanged historical executable model.
        for index, name in enumerate(runtime.EXPERTS):
            ranked = runtime.rank_from_predictions(
                row["predictions"], [1 - index, index]
            )
            results.append(
                result_row(row, ranked, name, bundle["candidate_vocabulary"])
            )
        results.append(
            result_row(
                row,
                state["candidate_scores"],
                "M2_R1_FINAL_FIXED_ORIGINAL_CONTROL",
                bundle["candidate_vocabulary"],
                original_vocabulary=expert["candidate_vocabulary"],
            )
        )
        baseline = previous.baseline_bundle(expert)
        payload = previous.legacy_payload(state, baseline)
        scored = previous.legacy.run(dict(payload, model="B2"), baseline)
        results.append(
            result_row(
                row,
                scored["candidate_state"]["candidates"],
                "B2_ORIGINAL_CONTROL",
                bundle["candidate_vocabulary"],
                original_vocabulary=baseline["vocabulary"],
            )
        )
        losses = [score_row(row, index) for index in [0, 1]]
        oracle = min(
            (i for i in [0, 1] if losses[i] is not None),
            key=lambda i: (losses[i], i),
            default=0,
        )
        results.append(
            result_row(
                row,
                runtime.rank_from_predictions(row["predictions"], [1 - oracle, oracle]),
                "ORACLE_DIAGNOSTIC_UPPER_BOUND_NOT_DEPLOYABLE",
                bundle["candidate_vocabulary"],
            )
        )
    return results


def complementarity(results):
    entries = {expert: {} for expert in runtime.EXPERTS}
    for row in results:
        if row["model"] in entries:
            key = (row["group_id"], row["record_id"], row["path"], row["slot"])
            entries[row["model"]][key] = row
    pairs = [
        (a, entries[runtime.EXPERTS[1]][key])
        for key, a in entries[runtime.EXPERTS[0]].items()
        if a["gap"] is not None
    ]
    first = np.asarray([a["gap"] for a, _ in pairs])
    second = np.asarray([b["gap"] for _, b in pairs])
    return {
        "labelled_paired_states": len(pairs),
        "B2_component_better_states": int(np.sum(first < second - 1e-12)),
        "R1_component_better_states": int(np.sum(second < first - 1e-12)),
        "tied_states": int(np.sum(abs(first - second) <= 1e-12)),
        "state_loss_correlation_diagnostic": (
            float(np.corrcoef(first, second)[0, 1])
            if len(pairs) > 1 and first.std() > 0 and second.std() > 0
            else None
        ),
        "not_independent_state_sample_size": True,
        "oracle_is_retrospective_only": True,
    }


def run_nested(owner_dir, contract_path, expected_contract_sha256, summary_path):
    owner, contract_path = Path(owner_dir), Path(contract_path)
    if sha(contract_path) != expected_contract_sha256:
        raise ValueError("FROZEN_OBJECTIVE_CONTRACT_HASH_MISMATCH")
    records = read(owner / "recovery_records.json")
    dev = [r for r in records if r["split"] == "DEVELOPMENT"]
    folds = read(owner / "revisions/r1/D0_folds.private.json")
    if folds != training.split_groups(dev, 3):
        raise ValueError("R2_OUTER_FOLDS_DO_NOT_MATCH_RETAINED_R1")
    destination = owner / "revisions/r2"
    selection = read(owner / "revisions/r1/final_fixed_selection.private.json")
    if selection["C"] != 0.1 or selection["loss_mode"] != "layered_conditional":
        raise ValueError("FROZEN_R1_SELECTION_CHANGED")
    plan = {
        **registered_config(),
        "objective_contract_sha256": expected_contract_sha256,
        "data_sha256": sha(owner / "recovery_records.json"),
        "D0_folds_sha256": r1.digest(folds),
        "semantic_relation_sha256": metric.SEMANTIC_RELATION_HASH,
        "R1_selection_sha256": r1.digest(selection),
        "registered_before_fitting": True,
    }
    plan_path = destination / "coordination_plan.private.json"
    if plan_path.exists():
        if read(plan_path) != plan:
            raise ValueError("RETAINED_R2_PLAN_MISMATCH")
    else:
        save(plan_path, plan)
    all_results, audits, models, router_logs = [], [], [], []
    start = time.monotonic()
    for outer in range(3):
        train = [row for row in dev if folds[row["group_id"]] != outer]
        held = [row for row in dev if folds[row["group_id"]] == outer]
        outer_path = owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{outer}.model.json"
        outer_expert = read(outer_path)
        audit = audit_expert(outer_expert, train, held)
        audit.update(
            outer_fold=outer,
            role="REUSED_FROZEN_OUTER_R1_EXPERT",
            model_sha256=sha(outer_path),
        )
        audits.append(audit)
        inner_folds = training.split_groups(train, 2)
        inner_rows = []
        for inner in range(2):
            inner_train = [
                row for row in train if inner_folds[row["group_id"]] != inner
            ]
            inner_held = [row for row in train if inner_folds[row["group_id"]] == inner]
            model_path = (
                destination
                / f"models/R2_R1_EXPERT_outer{outer}_inner{inner}.model.json"
            )
            stats = training.statistics(
                inner_train, outer_expert["candidate_vocabulary"]
            )
            bank = training.legacy.make_bank(
                stats, outer_expert["candidate_attributes"]
            )
            if model_path.exists():
                fitted = read(model_path)
            else:
                fitted, _ = training.fit(
                    inner_train,
                    r1.digest(plan),
                    C=0.1,
                    vocabulary=outer_expert["candidate_vocabulary"],
                    tag=f"R2_outer{outer}_inner{inner}",
                    bank_override=bank,
                    loss_mode="layered_conditional",
                    canonical_broad_feedback=True,
                )
                save(model_path, fitted)
            inner_audit = audit_expert(fitted, inner_train, inner_held)
            inner_audit.update(
                outer_fold=outer,
                inner_fold=inner,
                role="NEW_INNER_EXPERT_FIT",
                model_sha256=sha(model_path),
            )
            audits.append(inner_audit)
            predicted = collect_predictions(
                inner_held, fitted, expected_contract_sha256, outer, inner
            )
            save(
                destination / f"oof/experts_outer{outer}_inner{inner}.private.json",
                predicted,
            )
            inner_rows.extend(predicted)
        router = fit_router(
            inner_rows, {r["group_id"] for r in train}, {r["group_id"] for r in held}
        )
        coordinator = runtime.make_bundle(
            outer_expert, router, expected_contract_sha256, f"outer{outer}"
        )
        coordinator_path = (
            destination / f"models/R2_COORDINATOR_outer{outer}.model.json"
        )
        save(coordinator_path, coordinator)
        restored = read(coordinator_path)
        outer_rows = collect_predictions(
            held, outer_expert, expected_contract_sha256, outer
        )
        for row in outer_rows:
            for variant in ["G0", "G1", "G2", "G3"]:
                if runtime.rank_candidates(
                    row["base_state"], coordinator, variant
                ) != runtime.rank_candidates(row["base_state"], restored, variant):
                    raise AssertionError("COORDINATOR_RELOAD_PARITY_FAILED")
        save(destination / f"oof/experts_outer{outer}_held.private.json", outer_rows)
        evaluated = evaluate_outer(outer_rows, restored)
        save(
            destination / f"trajectories/coordination_outer{outer}.private.json",
            evaluated,
        )
        all_results.extend(evaluated)
        models.append(
            {
                "outer_fold": outer,
                "model_path": str(coordinator_path),
                "sha256": sha(coordinator_path),
            }
        )
        router_logs.append({"outer_fold": outer, "router": router})
        print(
            json.dumps(
                {
                    "phase": "R2_NESTED_COORDINATION",
                    "outer_fold": outer,
                    "rows": len(evaluated),
                    "global_alpha": router["global_alpha"],
                    "stage_alpha": router["stage_alpha"],
                }
            ),
            flush=True,
        )
    summary = {
        "version": runtime.VERSION,
        "objective_contract_sha256": expected_contract_sha256,
        "config": registered_config(),
        "development_groups": len(folds),
        "new_inner_expert_fits": 6,
        "reused_outer_experts": 3,
        "fitted_routers": 3,
        "models": models,
        "expert_group_isolation_verified": True,
        "router_inner_OOF_only_verified": True,
        "reload_predictions_identical": True,
        "same_runtime_feature_and_score_path": True,
        "complementarity": complementarity(all_results),
        "descriptive_all_prefix_results": {
            name: metric.grouped_summary(
                [row for row in all_results if row["model"] == name]
            )
            for name in sorted({r["model"] for r in all_results})
        },
        "all_prefix_mean_is_not_primary_equal_budget_comparison": True,
        "primary_result_aggregation": "PARENT_FIXED_PATH_SLOT_AND_OPTION_BUDGET_AGGREGATION",
        "elapsed_seconds": time.monotonic() - start,
    }
    save(destination / "expert_isolation_audit.private.json", audits)
    save(destination / "router_fit_log.private.json", router_logs)
    save(destination / "alignment_cost_trajectories.private.json", all_results)
    save(destination / "coordination_summary.private.json", summary)
    save(summary_path, summary)
    return summary


def fit_full_development(owner_dir, contract_path, expected_contract_sha256):
    """Fit a reloadable research artifact from expert OOF, never score it on train.

    Nested evaluation remains the three outer-router held results. This final
    artifact is distinct from both those evaluated models and the default B2.
    """
    owner = Path(owner_dir)
    if sha(contract_path) != expected_contract_sha256:
        raise ValueError("FROZEN_OBJECTIVE_CONTRACT_HASH_MISMATCH")
    records = read(owner / "recovery_records.json")
    dev = [row for row in records if row["split"] == "DEVELOPMENT"]
    historical = [row for row in records if row["split"] == "HISTORICAL_REGRESSION"]
    dst = owner / "revisions/r2"
    source = owner / "revisions/r1/models/M2_R1_FINAL_FIXED.model.json"
    expert = read(source)
    audit = audit_expert(expert, dev, historical)
    rows = []
    for fold in range(3):
        incoming = read(dst / f"oof/experts_outer{fold}_held.private.json")
        for row in incoming:
            row.pop("base_state", None)
        rows.extend(incoming)
    router = fit_router(rows, {row["group_id"] for row in dev})
    model = runtime.make_bundle(
        expert, router, expected_contract_sha256, "ALL_DEVELOPMENT"
    )
    path = dst / "models/R2_COORDINATOR_ALL_DEVELOPMENT.model.json"
    save(path, model)
    restored = read(path)
    episode, states, _ = training.trajectory(dev[0], expert, "P1", "fixed")
    for state in states:
        for variant in ["G0", "G1", "G2", "G3"]:
            if runtime.rank_candidates(
                state, model, variant
            ) != runtime.rank_candidates(state, restored, variant):
                raise AssertionError("FULL_COORDINATOR_RELOAD_PARITY_FAILED")
    receipt = {
        "version": runtime.VERSION,
        "objective_contract_sha256": expected_contract_sha256,
        "model_path": str(path),
        "model_sha256": sha(path),
        "base_expert_audit": audit,
        "base_expert_sha256": sha(source),
        "router_fit": router,
        "router_training_basis": "UNION_OF_THREE_OUTER_BASE_EXPERT_OOF_PREDICTIONS",
        "training_oof_is_not_used_as_final_model_generalization_evaluation": True,
        "performance_reference": "THREE_NESTED_OUTER_ROUTER_HELD_EVALUATIONS_ONLY",
        "reload_predictions_identical": True,
        "runtime_default_changed": False,
        "router_fit_counts": {
            "nested_outer": 3,
            "all_development_research": 1,
            "total": 4,
        },
    }
    save(dst / "coordination_full_fit_receipt.private.json", receipt)
    summary_path = dst / "coordination_summary.private.json"
    if summary_path.exists():
        summary = read(summary_path)
        summary["router_fit_counts"] = receipt["router_fit_counts"]
        summary["full_development_research_model"] = {
            "model_path": str(path),
            "model_sha256": receipt["model_sha256"],
            "not_a_generalization_evaluation": True,
            "reload_predictions_identical": True,
        }
        save(summary_path, summary)
        save("/private/tmp/m2-r2-coordination-summary.json", summary)
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", required=True)
    parser.add_argument("--contract", required=True)
    parser.add_argument("--expected-contract-sha256", required=True)
    parser.add_argument(
        "--summary-path", default="/private/tmp/m2-r2-coordination-summary.json"
    )
    args = parser.parse_args()
    run_nested(
        args.owner_dir, args.contract, args.expected_contract_sha256, args.summary_path
    )


if __name__ == "__main__":
    main()
