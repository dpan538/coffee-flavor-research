"""Frozen-protocol, nested coffee-group R3 relation and trigger fitting.

Mention retrieval is a record-recovery proxy. Its normalization competitors are
not negative sensory observations. Raw observations and fitted weights are private.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from threadpoolctl import threadpool_limits

import alignment_metrics_r3 as metric
import flavor_constraints_r3 as runtime
import flavor_m2_r1 as r1
import train_m2_r1 as training
from train_coordination_r2 import audit_expert, expert_training_groups


def protocol():
    """The exact bounded proposal; fitting additionally requires root's SHA."""
    return {
        "version": "m2-constraints.r3.v1",
        "formal_fit_requires_frozen_contract_sha256": True,
        "data": {
            "development_records": 211,
            "development_coffee_groups": 187,
            "outer_folds": "FROZEN_R1_D0_THREE_COFFEE_GROUP_FOLDS",
            "relation_inner_folds": 2,
            "trigger_inner_folds": 2,
            "base_expert_internal_feature_folds": 2,
            "history_groups": 17,
            "history_role": "ALREADY_INSPECTED_REGRESSION_ONLY_NO_FIT_OR_SELECTION",
            "reuse": "EXACT_TRAIN_RECORD_STATISTICS_BANK_AND_INTERNAL_SCALER_AUDIT_REQUIRED",
            "nested_scope": "TRIGGER_LABELS_FROM_INNER_HELD_RELATIONS;RELATION_TRAIN_STATES_FROM_BASE_EXPERT_OOF;OUTER_HELD_NEVER_SELECTS",
        },
        "base_expert": {
            "id": "M2_R1_FINAL_FIXED",
            "C": 0.1,
            "loss_mode": "layered_conditional",
            "canonical_broad_feedback": True,
            "E1": "ORIGINAL_RAW_R1_SCORES_AND_EXPLICIT_PRIORITY_WITH_TYPED_K1_AUDIT",
            "score_normalization": "NONE",
            "shared_evidence": "R1_CANONICAL_ENCODING_ONCE_NO_EXTRA_DIRECT_BROAD_NONE_BONUS",
            "prior_selection_scope": "R1_SETTINGS_ALREADY_INSPECTED_NOT_FRESH_CONFIRMATION",
        },
        "relation": {
            "variants": ["E1", "E2", "E3"],
            "primary_contrast": "E2_MINUS_E1_AT_FIXED_ASK_Q4_EQUAL_BUDGET",
            "secondary": "E3_MINUS_E2_AT_FIXED_ASK_Q4_EQUAL_BUDGET",
            "selection": "INNER_HELD_GROUP_MACRO_RAW_GAP_AT_FIXED_ASK_Q4_ONLY",
            "selection_tie": "LOSS_WITHIN_1E-12_COMPLEXITY_E1_THEN_E2_THEN_E3",
            "semantic_question_key": "SLOT_AXIS_SORTED_TYPED_OFFERED_CONCEPT_IDS",
            "answer_pattern": "EXACT_CANONICAL_POSITIVE_SELECTED_CONCEPT_SET;UNSURE_NONE_EMPTY_HAVE_NO_POSITIVE_TERM",
            "pair_slots": [["Q0", "Q1"], ["Q0", "Q2"], ["Q1", "Q2"]],
            "max_pairs": 12,
            "max_pairs_per_slot_pair": 4,
            "triple_slots": [["Q0", "Q1", "Q2"]],
            "max_triples": 4,
            "minimum_term_training_coffee_groups": 4,
            "minimum_term_candidate_positive_mention_groups": 3,
            "term_selection": "DESCENDING_DISTINCT_TRAIN_GROUP_SUPPORT_THEN_SUPPORTED_CANDIDATE_COUNT_THEN_CANONICAL_TERM_KEY",
            "candidate_scope": "EXPERT_TRAIN_QUALIFIED_FINE_IDS_FIXED_BEFORE_ANY_SOFT_RELATION_EFFECT",
            "ridge": 10.0,
            "optimizer": {
                "method": "L-BFGS-B",
                "maxiter": 150,
                "ftol": 1e-10,
                "gtol": 1e-7,
            },
            "objective": "SUM_g MEAN_record_stage[LOGSUMEXP_c(z_ic)-SUM_c(q_ic*z_ic)]+10/2*SUM(theta^2)",
            "z": "FROZEN_ORIGINAL_R1_RAW_SCORE_PLUS_ACTIVE_TERM_CANDIDATE_DELTAS;DELTA_ZERO_FOR_EXPLICIT_CANDIDATES",
            "q": "POSITIVE_SOURCE_RELEVANCE_OF_HIDDEN_FINE_MENTIONS_NORMALIZED_WITHIN_FIXED_CANDIDATES",
            "normalizer_semantics": "UNMENTIONED_CANDIDATES_ARE_RETRIEVAL_CONTRASTS_NOT_SENSORY_ABSENCE_LABELS",
            "missing_or_oov_only_hidden_targets": "NO_SUPERVISED_LOSS_BUT_RETAIN_ALL_COVERAGE_AND_EVALUATION_ROWS",
            "training_stages": ["Q1", "Q2", "Q3", "Q4"],
            "E3": "FREEZE_E1_AND_E2_PAIR_COEFFICIENTS_FIT_ONLY_TRIPLE_COEFFICIENTS",
            "source_native_attribute_frequency_quality": "EXCLUDED_FROM_FINE_MENTION_LOSS",
            "compounds": "WHOLE_CONCEPT_ONLY",
        },
        "K1": {
            "types": [
                "HARD_CONTRACT",
                "SEMANTIC_ENTAILMENT",
                "EMPIRICAL_COMPATIBILITY",
            ],
            "statuses": ["PROPOSED", "SUPPORTED_WITHIN_SCOPE", "REVISED"],
            "provenance": "CANONICAL_CURRENT_ANSWER_EVIDENCE_IDS_OR_PRIVATE_TRAIN_SUPPORT_IDS",
            "hard_delete": "INVALID_CONTRACT_OR_LOGIC_ONLY_NEVER_CONTEXT_LOW_SCORE_OR_UNKNOWN_COMPATIBILITY",
            "empirical_effect": "REVERSIBLE_SOFT_PRIORITY_NO_MEASURED_EXCLUSION_ACCURACY_CLAIM",
            "broad_parent": "POSITIVE_PARENT_SUPPORT_WITHOUT_CHILD_ABSENCE_OR_DUPLICATE_UPGRADE",
        },
        "trigger_A": {
            "model": "GROUP_WEIGHTED_STANDARDIZED_RIDGE",
            "ridge": 10.0,
            "target": "RAW_GAP_SKIP_Q3_TO_Q4_MINUS_RAW_GAP_ASK_Q3_THEN_Q4",
            "positive_target_means": "ASK_GAIN",
            "prediction_shrinkage": "N_LABELLED_UNIQUE_TRAIN_GROUPS/(N+50)_TO_TRAIN_GLOBAL_MEAN_GAIN",
            "ask_if_prediction_strictly_greater_than": 0.01,
            "margin_semantics": "OPERATIONAL_ONE_ADDITIONAL_QUESTION_PENALTY_NOT_USER_ACCEPTABILITY_OR_TIME",
            "features": [
                "stage_q2",
                "k1_supported_count",
                "k1_empirical_count",
                "k1_revised_count",
                "independent_broad_count",
                "explicit_fine_count",
                "dimension_count",
                "log_training_support",
                "relation_top5_disagreement",
                "previous_answer_top5_change",
            ],
            "forbidden_features": [
                "coffee_id",
                "record_id",
                "source_family",
                "future_answer",
                "hidden_target",
                "laboratory_value",
            ],
            "ties": "RETAIN_GAIN_ZERO_IN_TRAINING_AND_ALL_CASE_EVALUATION",
            "primary": "LEARNED_VERSUS_ALWAYS_ASK_ALL_CASES_AT_Q4",
            "policies": ["ALWAYS_ASK", "SIMPLE_RULE", "LEARNED", "TWO_STEP_EMPIRICAL"],
            "simple_rule": "ASK_IF_INDEPENDENT_DIMENSIONS_LE_1_OR_NO_EXPLICIT_FINE_ELSE_SKIP",
            "undefined_training_label": "NO_REGRESSION_LABEL_RETAIN_CASE_IN_POLICY_COVERAGE",
        },
        "trigger_B": {
            "role": "SEPARATE_RELATION_COMPONENT_ACTIVATION_NOT_TRIGGER_A",
            "model": "GROUP_WEIGHTED_STANDARDIZED_RIDGE",
            "ridge": 10.0,
            "target": "E1_RAW_GAP_MINUS_SELECTED_RELATION_RAW_GAP_AT_SAME_Q4",
            "minimum_labelled_unique_groups": 20,
            "support_gate": "BOTH_POSITIVE_AND_NONPOSITIVE_GROUP_OUTCOMES_REQUIRED_ELSE_FIXED_OFF",
            "activate_if_prediction_strictly_greater_than": 0.0,
            "selection": "NO_ADDITIONAL_GRID_OR_OUTER_HELD_SELECTION",
        },
        "two_step": {
            "decision_stage": "AFTER_Q2_ONLY",
            "actions": {"SKIP": ["Q4"], "ASK": ["Q3", "Q4"]},
            "maximum_simulated_followup_questions_per_action_per_train_record": 2,
            "question_policy": "EXISTING_FIXED_TRAIN_QUALIFIED_R1_BANK",
            "branch_support": "ALL_TRAIN_FROZEN_A_RECORDS_ONLY;NO_HELD_ANSWERS_OR_TARGETS",
            "matching_units": "CANONICAL_POSITIVE_CONCEPTS_AND_ENTAILED_PARENT_DIMENSIONS_FROM_CURRENT_EVIDENCE",
            "matching_weight": "ONE_PLUS_CARDINALITY_CURRENT_POSITIVE_UNITS_INTERSECT_TRAIN_A_POSITIVE_UNITS",
            "aggregation": "NORMALIZE_RECORD_WEIGHTS_WITHIN_COFFEE_THEN_EQUAL_COFFEE_WEIGHT",
            "answers": "TRAIN_A_SELECTED_POSITIVE_OPTIONS;NO_MATCH_IS_ORDINARY_UNSURE_NEVER_NONE_OF_THESE",
            "utility": "TRAIN_HIDDEN_T_MEAN_RAW_GAP_AT_Q4_PLUS_0.01_TIMES_FOLLOWUP_QUESTIONS",
            "tie": "WITHIN_1E-12_FEWER_QUESTIONS_SKIP",
            "undefined_support": "REPORT_NOT_ESTIMABLE_AND_DETERMINISTIC_SKIP",
            "scope": "TRAIN_EMPIRICAL_PROXY_BRANCH_EXPECTATION_NOT_WORLD_MODEL_NOT_RESPONSE_PROBABILITY",
        },
        "runtime": {
            "path": "P1_WITH_EXPLICIT_R3_Q2_ASK_OR_SKIP_Q3_TO_Q4",
            "question_limit": 6,
            "options_per_question_limit": 4,
            "mandatory_C0_families": 8,
            "mandatory_C1_levels": 7,
            "main_limit": 5,
            "secondary_limit": 3,
            "final_comparison_candidates": [3, 8],
            "final_comparison_count": 1,
            "final_comparison_then": "FINAL_RESULT_TERMINAL",
            "foundation_check_enabled": False,
            "default_B2_changed": False,
            "human_time": None,
            "session_parameters": "FROZEN_HASH_VALIDATED;REPLAY_REPLACEMENT_IDEMPOTENT_CANONICAL_EVIDENCE",
        },
        "metric": {
            "primary": "alignment_metrics_r3.evaluate.raw_gap_FINE_K5_EXACT1_REGISTERED_SHARED_PARENT0.25_OTHER0",
            "fixed_candidates": "PRE_SOFT_E1_UNIVERSE_IDENTICAL_ACROSS_E1_E2_E3",
            "excluded_visible": "ENTIRE_FROZEN_A_FOR_COUNTERFACTUAL_COMPLETION_PANEL_ONLY",
            "actual_main5": "SEPARATE_ACTUAL_DISPLAY_AND_DIRECT_RETENTION_PANEL",
            "M_star": "DIAGNOSTIC_FIXED_CANDIDATE_SUPERSET_ONLY_NOT_SELECTION",
            "NI_margin": 0.02,
            "NI_scope": "RESEARCH_OPERATIONAL_MARGIN_NOT_USER_ACCEPTANCE_THRESHOLD",
            "primary_information_cost": "ACTUALLY_EXPOSED_ORDINARY_OPTION_COUNT",
        },
        "public_release": "AGGREGATES_PROTOCOL_HASHES_ONLY_NO_RAW_ROWS_OR_MODEL_WEIGHTS",
    }


def read(path):
    return json.loads(Path(path).read_text())


def internal_feature_amendment():
    """Narrow proposal after observed finite-axis support failure; not auto-approved."""
    return {
        "version": "r3-deepest-base-p1-feature-path.v1",
        "reason": "FOUR_OF_24_DEEPEST_INTERNAL_TRAIN_FOLDS_HAVE_THREE_QUALIFIED_AXES_OLD_P4_REQUIRES_FOUR",
        "scope": "ALL_12_NEW_DEEPEST_BASE_EXPERT_FITS_ONLY",
        "training_feature_trajectory": "P1_Q0_Q1_Q2_Q3_Q4_THEN_EXISTING_A_DERIVED_FINAL_F2",
        "minimum_correction_axes": 3,
        "individual_axis_qualification": "UNCHANGED_AT_LEAST_TWO_RESPONSE_PATTERNS_EACH_WITH_TWO_TRAIN_GROUP_RECORDS",
        "question_option_selection": "UNCHANGED_TRAIN_COUNTS_PRIORITY_AND_FOUR_OPTION_LIMIT",
        "feature_and_loss": "UNCHANGED_R1_SHARED_ENCODER_MASKS_LAYERED_CONDITIONAL_C0.1_RMS_INNER_OOF",
        "internal_feature_folds": 2,
        "leakage": "ALL_BANK_COUNTS_PATTERNS_AND_SCALER_FROM_RESPECTIVE_INTERNAL_TRAIN_GROUPS_ONLY",
        "failure_if_fewer_than_three": "STOP_AND_REPORT_NOT_ESTIMABLE_NO_BORROWED_BANK",
        "retained_attempt": "ORIGINAL_ONE_DEEPER_P4_FIT_RETAINED_EXCLUDED_NEW_MODELS_USE_P1_INTERNAL_SUFFIX",
        "outer_and_relation_contract": "UNCHANGED",
    }


def train_qualified_p1_bank(stats, attributes):
    """Exact legacy axis qualification with the explicitly amended P1 count."""
    vocab, counts = stats["vocabulary"], stats["counts"]
    attrcounts = {
        a: sum(counts.get(c, 0) for c in vocab if a in attributes.get(c, []))
        for a in r1.ATTRS
    }
    ordered = sorted(r1.ATTRS, key=lambda a: (-attrcounts[a], a))

    def broad(axis, attrs):
        return {
            "axis": axis,
            "options": [
                {"id": "attribute." + a, "kind": "broad", "attribute": a} for a in attrs
            ],
            "priority": sum(attrcounts[a] for a in attrs),
        }

    bank = {
        "initial_0": broad("broad.initial0", ordered[:4]),
        "initial_1": broad("broad.initial1", ordered[4:8]),
        "correction": [],
    }
    for a in ordered:
        choices = sorted(
            [
                c
                for c in vocab
                if a in attributes.get(c, []) and c.startswith("sensory.")
            ],
            key=lambda c: (-counts.get(c, 0), c),
        )[:4]
        if not choices and "attribute." + a in vocab:
            choices = ["attribute." + a]
        options = [
            {
                "id": c,
                "kind": "specific" if c.startswith("sensory.") else "broad",
                "attribute": a,
            }
            for c in choices
        ]
        patterns = Counter(
            tuple(option["id"] for option in options if option["id"] in row["targets"])
            for row in stats["planning_records"]
        )
        if options and sum(n >= 2 for n in patterns.values()) >= 2:
            bank["correction"].append(
                {"axis": "refine." + a, "options": options, "priority": attrcounts[a]}
            )
    if len(bank["correction"]) < 3:
        raise ValueError("R3_P1_INTERNAL_TRAIN_HAS_FEWER_THAN_THREE_QUALIFIED_AXES")
    return bank


def p1_internal_training_arrays(records, outer_bundle, manifest_hash):
    """R1-compatible arrays, solely the separately frozen P1 feature-path amendment."""
    folds = training.split_groups(records, 2)
    vocab = outer_bundle["candidate_vocabulary"]
    index = {c: i for i, c in enumerate(vocab)}
    source_groups = Counter(
        next(row["source_family"] for row in records if row["group_id"] == group)
        for group in {row["group_id"] for row in records}
    )
    group_rows = Counter(row["group_id"] for row in records)
    X, Y, weights, audit, task_rows = [], [], [], [], []
    for fold in range(2):
        train = [row for row in records if folds[row["group_id"]] != fold]
        held = [row for row in records if folds[row["group_id"]] == fold]
        stats = training.statistics(train, vocab)
        attrs = {c: r1.PARENTS.get(c, []) for c in vocab}
        bank = train_qualified_p1_bank(stats, attrs)
        inner = training.make_bundle(
            train,
            outer_bundle["model_kind"],
            manifest_hash,
            vocab,
            f"R3_P1_internal{fold}",
            bank,
            canonical_broad_feedback=True,
        )
        audit.append(
            {
                "feature_training_groups": sorted({r["group_id"] for r in train}),
                "feature_output_groups": sorted({r["group_id"] for r in held}),
                "cluster_fit": "NOT_USED",
                "question_bank_scope": "R3_P1_INTERNAL_EXACT_TRAIN_ONLY",
                "question_bank_hash": r1.digest(bank),
                "source_truth_as_runtime_features": False,
                "feature_path": "P1",
                "qualified_correction_axes": len(bank["correction"]),
                "amendment_sha256": r1.digest(internal_feature_amendment()),
            }
        )
        for record in held:
            ep, states, answers = training.trajectory(record, inner, "P1", "fixed")
            pre = r1.finalize_result(states[-1], inner)
            exposure = pre["exposure"]
            if exposure and exposure["eligible_for_final_comparison"]:
                chosen = [c for c in exposure["candidate_ids"] if c in ep["visible"]]
                states.append(
                    r1.apply_final_comparison(
                        states[-1],
                        exposure["candidate_ids"],
                        chosen,
                        inner,
                        feedback_source="SIMULATED",
                        generation_version=inner["bundle_id"],
                    )
                )
            mass = 1 / (
                group_rows[record["group_id"]]
                * source_groups[record["source_family"]]
                * len(states)
            )
            for state in states:
                hidden = [c for c in ep["hidden"] if c in index]
                if not hidden:
                    continue
                X.append(r1.encode_features(state, inner)["raw_features"])
                task_rows.append(training.supervision_targets(record, ep, state, inner))
                direct = [
                    c for c in r1.evidence(state, inner)["confirmed"] if c in index
                ]
                y = np.zeros(len(vocab))
                for c in hidden:
                    y[index[c]] += (
                        (0.7 if direct else 1.0)
                        * record["relevance"][c]
                        / sum(record["relevance"][h] for h in hidden)
                    )
                for c in direct:
                    y[index[c]] += 0.3 / len(direct)
                Y.append(y)
                weights.append(mass)
    tasks = {
        task: {
            key: np.asarray([row[task][key] for row in task_rows])
            for key in ["values", "mask"]
        }
        for task in ["attr", "leaf", "recovery"]
    }
    tasks["recovery"]["mention_mass"] = np.asarray(
        [row["recovery"]["mention_mass"] for row in task_rows]
    )
    tasks["recovery"]["candidate_levels"] = [
        (
            "leaf"
            if c.startswith("sensory.")
            else "broad_descriptor" if c.startswith("broad.") else "attribute"
        )
        for c in vocab
    ]
    return np.asarray(X), np.asarray(Y), np.asarray(weights), audit, tasks


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    path.chmod(0o600)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def group_weights(rows):
    """One unit per coffee, equal record and available stage within coffee."""
    records, stages = defaultdict(set), defaultdict(set)
    cells = Counter()
    for row in rows:
        g, r, s = row["group_id"], row["record_id"], row.get("slot", "Q2")
        records[g].add(r)
        stages[g, r].add(s)
        cells[g, r, s] += 1
    return np.array(
        [
            1
            / (
                len(records[row["group_id"]])
                * len(stages[row["group_id"], row["record_id"]])
                * cells[row["group_id"], row["record_id"], row.get("slot", "Q2")]
            )
            for row in rows
        ]
    )


def macro(rows, key="gap"):
    labelled = [row for row in rows if row.get(key) is not None]
    return (
        float(
            np.average([row[key] for row in labelled], weights=group_weights(labelled))
        )
        if labelled
        else None
    )


def collect_relation_rows(records, expert):
    fitted = expert_training_groups(expert)
    if fitted & {row["group_id"] for row in records}:
        raise ValueError("RELATION_BASE_PREDICTIONS_MUST_BE_OUT_OF_COFFEE_GROUP")
    rows = []
    for record in records:
        episode, states, answers = training.trajectory(record, expert, "P1", "fixed")
        for state, answer in zip(states[1:], answers, strict=True):
            if answer["slot"] not in protocol()["relation"]["training_stages"]:
                continue
            rows.append(
                {
                    "group_id": record["group_id"],
                    "record_id": record["record_id"],
                    "source_family": record["source_family"],
                    "slot": answer["slot"],
                    "episode": episode,
                    "base_rows": state["candidate_scores"],
                    "terms": {
                        str(order): runtime.available_terms(state, order)
                        for order in [2, 3]
                    },
                    "expert_bundle_id": expert["bundle_id"],
                    "base_expert_training_groups": sorted(fitted),
                    "out_of_group_verified": True,
                }
            )
    return rows


def choose_terms(rows, candidates, order):
    catalog, group_support, positive_support = (
        {},
        defaultdict(set),
        defaultdict(lambda: defaultdict(set)),
    )
    for row in rows:
        positive = set(row["episode"]["hidden"]) & set(candidates)
        for term in row["terms"][str(order)]:
            identity = term["term_id"]
            catalog[identity] = copy.deepcopy(term)
            group_support[identity].add(row["group_id"])
            for candidate in positive:
                positive_support[identity][candidate].add(row["group_id"])
    eligible = []
    for identity, term in catalog.items():
        candidates_here = sorted(
            c for c, groups in positive_support[identity].items() if len(groups) >= 3
        )
        if len(group_support[identity]) < 4 or not candidates_here:
            continue
        term.update(
            training_group_support=len(group_support[identity]),
            training_evidence_ids=[
                "train-coffee:" + r1.digest(g) for g in sorted(group_support[identity])
            ],
            training_groups=sorted(group_support[identity]),
            candidate_positive_group_support={
                c: len(positive_support[identity][c]) for c in candidates_here
            },
            coefficients=dict.fromkeys(candidates_here, 0.0),
        )
        eligible.append(term)
    eligible.sort(
        key=lambda term: (
            -term["training_group_support"],
            -len(term["coefficients"]),
            r1.digest(term["pattern"]),
        )
    )
    chosen, per_pair = [], Counter()
    for term in eligible:
        slot_key = tuple(term["slots"])
        if order == 2 and per_pair[slot_key] >= 4:
            continue
        chosen.append(term)
        per_pair[slot_key] += 1
        if len(chosen) >= (12 if order == 2 else 4):
            break
    return chosen, {
        "observed_terms": len(catalog),
        "support_eligible_terms": len(eligible),
        "selected_terms": len(chosen),
    }


def fit_relations(
    rows, candidates, allowed_training_groups, held_groups=(), frozen_pairs=None
):
    """Conditional mention CE with TRAIN sparse feature selection and ridge10."""
    allowed, held = set(allowed_training_groups), set(held_groups)
    if allowed & held or {row["group_id"] for row in rows} != allowed:
        raise ValueError("RELATION_TRAINING_COFFEE_SCOPE_MISMATCH")
    for row in rows:
        if (
            row["group_id"] in row["base_expert_training_groups"]
            or set(row["base_expert_training_groups"]) & held
            or not set(row["base_expert_training_groups"]) <= allowed
        ):
            raise ValueError("RELATION_BASE_OOF_ISOLATION_FAILED")
    order = 2 if frozen_pairs is None else 3
    terms, support = choose_terms(rows, candidates, order)
    pairs = copy.deepcopy(frozen_pairs or [])
    index = {c: i for i, c in enumerate(candidates)}
    terms_index = {term["term_id"]: i for i, term in enumerate(terms)}
    parameters = [
        (i, index[c])
        for i, term in enumerate(terms)
        for c in sorted(term["coefficients"])
    ]
    known = [row for row in rows if set(row["episode"]["hidden"]) & set(candidates)]
    if known and parameters:
        logits, q, active, mask = [], [], [], []
        for row in known:
            active_pairs = [
                term
                for term in pairs
                if term["term_id"] in {t["term_id"] for t in row["terms"]["2"]}
            ]
            base_rows = runtime.rank_from_base_rows(row["base_rows"], active_pairs)
            mapped = {item["candidate_id"]: item for item in base_rows}
            logits.append([mapped[c]["score"] for c in candidates])
            relevance = row["episode"]["relevance"]
            target = np.array([relevance.get(c, 0.0) for c in candidates], float)
            q.append(target / target.sum())
            present = {term["term_id"] for term in row["terms"][str(order)]}
            active.append([float(identity in present) for identity in terms_index])
            mask.append([not mapped[c]["explicit"] for c in candidates])
        logits, q, active, mask = map(np.asarray, [logits, q, active, mask])
        weights = group_weights(known)

        def objective(theta):
            matrix = np.zeros((len(terms), len(candidates)))
            for value, (i, j) in zip(theta, parameters, strict=True):
                matrix[i, j] = value
            z = logits + (active @ matrix) * mask
            norm = logsumexp(z, axis=1)
            loss = np.sum(weights * (norm - np.sum(q * z, axis=1))) + 5 * (
                theta @ theta
            )
            residual = (np.exp(z - norm[:, None]) - q) * weights[:, None] * mask
            grad_matrix = active.T @ residual
            grad = np.array([grad_matrix[i, j] for i, j in parameters]) + 10 * theta
            return float(loss), grad

        fitted = minimize(
            objective,
            np.zeros(len(parameters)),
            jac=True,
            method="L-BFGS-B",
            options={"maxiter": 150, "ftol": 1e-10, "gtol": 1e-7},
        )
        if not np.all(np.isfinite(fitted.x)):
            raise ValueError("NONFINITE_RELATION_FIT")
        for value, (i, j) in zip(fitted.x, parameters, strict=True):
            terms[i]["coefficients"][candidates[j]] = float(value)
        receipt = {
            "optimizer_success": bool(fitted.success),
            "optimizer_message": str(fitted.message),
            "objective": float(fitted.fun),
            "iterations": int(fitted.nit),
            "coefficient_l2": float(np.linalg.norm(fitted.x)),
        }
    else:
        receipt = {
            "optimizer_success": True,
            "optimizer_message": "NO_SUPPORTED_PARAMETERS_OR_IDENTIFIABLE_TARGETS",
            "objective": None,
            "iterations": 0,
            "coefficient_l2": 0.0,
        }
    return {
        "pairs": terms if order == 2 else pairs,
        "triples": terms if order == 3 else [],
        "fit_status": "FITTED_CONDITIONAL_MENTION_RETRIEVAL",
        "receipt": {
            **receipt,
            **support,
            "order": order,
            "fitted_parameters": len(parameters),
            "training_groups": sorted(allowed),
            "held_groups": sorted(held),
            "identifiable_training_rows": len(known),
            "all_training_rows": len(rows),
            "train_group_hash": r1.digest(sorted(allowed)),
            "normalization_is_not_sensory_negative_supervision": True,
        },
    }


def trajectory(
    record,
    bundle,
    variant="E1",
    trigger_policy="ALWAYS_ASK",
    relation_activation="ALWAYS",
):
    episode = training.visible_episode(record)
    state = runtime.initial_state(
        episode["context"], bundle, variant, trigger_policy, relation_activation
    )
    states, answers = [copy.deepcopy(state)], []
    while True:
        nxt = runtime.select_next_question(state, bundle)
        if nxt["action"] != "ASK":
            break
        answer = training.answer_for(
            nxt["question"], episode["visible"], bundle["r1_expert"]
        )
        state = runtime.update_state(state, answer, bundle)
        answers.append(answer)
        states.append(copy.deepcopy(state))
        if len(answers) > 5:
            raise ValueError("REGISTERED_R3_Q4_ENDPOINT_EXCEEDED")
    if "Q4" not in state["base_state"]["answers_by_question"]:
        raise ValueError("Q4_ENDPOINT_REQUIRED")
    return episode, states, answers


def result_row(record, episode, state, bundle, slot, model, fold=None, action=None):
    base = state["base_state"]
    ranking = state["candidate_scores"]
    evaluated = metric.evaluate(
        ranking,
        episode["relevance"],
        bundle["fixed_candidates"],
        excluded_visible=episode["visible"],
    )
    actual = metric.evaluate(
        ranking[:5], episode["relevance"], bundle["fixed_candidates"]
    )
    visible = {c for c in episode["visible"] if c.startswith("sensory.")}
    actual_ids = {r["candidate_id"] for r in ranking[:5]}
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "source_family": record["source_family"],
        "fold": fold,
        "path": "R3_P1",
        "slot": slot,
        "stage": "FINAL" if slot == "Q4" else "CORRECTION",
        "model": model,
        "variant": state["variant"],
        "trigger_policy": state["trigger_policy"],
        **evaluated,
        "actual_main5": actual,
        "direct_visible_retention_at5": (
            len(visible & actual_ids) / len(visible) if visible else None
        ),
        "ordinary_questions": len(base["answers_by_question"]),
        "ordinary_options": sum(
            len(a["shown_option_ids"]) for a in base["answers_by_question"].values()
        ),
        "final_comparison_candidates": 0,
        "human_time": None,
        "ranking": ranking,
        "episode": episode,
        "fixed_candidates": bundle["fixed_candidates"],
        "q2_decision": state["q2_decision"],
        "action": action,
        "k1": state["k1"],
        "bundle_id": bundle["bundle_id"],
    }


def collect_branches(records, bundle, fold=None):
    """Paired ASK/SKIP outcomes from A only; targets are evaluated afterwards."""
    fitted_groups = expert_training_groups(bundle["r1_expert"])
    if fitted_groups & {r["group_id"] for r in records}:
        raise ValueError("TRIGGER_RELATION_PREDICTIONS_MUST_BE_OUT_OF_GROUP")
    rows = []
    for record in records:
        for variant in runtime.VARIANTS:
            episode, states, _ = trajectory(record, bundle, variant, "ALWAYS_ASK")
            q2 = next(
                state
                for state in states
                if set(state["base_state"]["answers_by_question"]) == {"Q0", "Q1", "Q2"}
            )
            outcomes = {}
            for action in ["ASK", "SKIP"]:
                end, answers = runtime.complete_branch(
                    q2, episode["visible"], bundle, action
                )
                outcomes[action] = result_row(
                    record, episode, end, bundle, "Q4", variant, fold, action
                )
            ask, skip = outcomes["ASK"]["raw_gap"], outcomes["SKIP"]["raw_gap"]
            rows.append(
                {
                    "record_id": record["record_id"],
                    "group_id": record["group_id"],
                    "source_family": record["source_family"],
                    "slot": "Q2",
                    "variant": variant,
                    "features": runtime.live_features(q2, bundle),
                    "gain": (
                        skip - ask if skip is not None and ask is not None else None
                    ),
                    "outcomes": outcomes,
                    "episode": episode,
                    "relation_training_groups": sorted(fitted_groups),
                    "out_of_group_verified": True,
                }
            )
    return rows


def fit_trigger_a(
    rows, allowed_training_groups, held_groups=(), target_key="gain", support_gate=False
):
    allowed, held = set(allowed_training_groups), set(held_groups)
    if allowed & held or {row["group_id"] for row in rows} != allowed:
        raise ValueError("TRIGGER_TRAINING_COFFEE_SCOPE_MISMATCH")
    for row in rows:
        fitted = set(row["relation_training_groups"])
        if row["group_id"] in fitted or fitted & held or not fitted <= allowed:
            raise ValueError("TRIGGER_RELATION_OOF_ISOLATION_FAILED")
    labelled = [row for row in rows if row.get(target_key) is not None]
    groups = {row["group_id"] for row in labelled}
    outcomes = [row[target_key] for row in labelled]
    enabled = bool(labelled) and (
        not support_gate
        or (
            len(groups) >= 20
            and any(v > 0 for v in outcomes)
            and any(v <= 0 for v in outcomes)
        )
    )
    model = runtime.empty_trigger()
    model.update(
        labelled_groups=len(groups),
        training_groups=sorted(allowed),
        held_groups=sorted(held),
        all_case_rows=len(rows),
        labelled_rows=len(labelled),
        tied_rows=sum(v == 0 for v in outcomes),
        enabled=enabled,
    )
    if not enabled:
        model["fit_status"] = (
            "SUPPORT_GATE_NOT_MET_FIXED_OFF"
            if support_gate
            else "NO_IDENTIFIABLE_TRAINING_LABELS"
        )
        return model
    x = np.array(
        [[row["features"][name] for name in runtime.FEATURES] for row in labelled]
    )
    y, w = np.asarray(outcomes), group_weights(labelled)
    mean = np.average(x, axis=0, weights=w)
    scale = np.sqrt(np.average((x - mean) ** 2, axis=0, weights=w))
    scale[scale < 1e-12] = 1.0
    z = (x - mean) / scale
    intercept = float(np.average(y, weights=w))
    beta = np.linalg.solve(
        z.T @ (w[:, None] * z) + 10 * np.eye(len(runtime.FEATURES)),
        z.T @ (w * (y - intercept)),
    )
    model.update(
        mean=mean.tolist(),
        scale=scale.tolist(),
        coefficients=beta.tolist(),
        intercept=intercept,
        global_mean=intercept,
        shrinkage=len(groups) / (len(groups) + 50),
        fit_status="FITTED_GROUP_ISOLATED_RIDGE",
        target_semantics=target_key,
        coffee_equal_weight=True,
    )
    return model


def fit_trigger_b(rows, allowed_training_groups, held_groups=()):
    return fit_trigger_a(
        rows, allowed_training_groups, held_groups, "relation_gain", support_gate=True
    )


def empirical_support(records, expert):
    result = []
    for record in records:
        ep = training.visible_episode(record)
        units = set(ep["visible"]) | {
            "attribute." + a
            for c in ep["visible"]
            for a in expert["candidate_attributes"].get(c, [])
        }
        result.append(
            {
                "group_id": record["group_id"],
                "record_id": record["record_id"],
                "visible": ep["visible"],
                "visible_units": sorted(units),
                "relevance": ep["relevance"],
            }
        )
    return result


def evaluate_fixed(records, bundle, fold):
    results = []
    for record in records:
        for variant in runtime.VARIANTS:
            episode, states, answers = trajectory(record, bundle, variant, "ALWAYS_ASK")
            for state, answer in zip(states[1:], answers, strict=True):
                results.append(
                    result_row(
                        record, episode, state, bundle, answer["slot"], variant, fold
                    )
                )
    return results


def _summary(rows):
    return {
        name: {
            "gap": macro([r for r in rows if r["model"] == name and r["slot"] == "Q4"]),
            "records": len({r["record_id"] for r in rows if r["model"] == name}),
            "groups": len({r["group_id"] for r in rows if r["model"] == name}),
            "labelled_records": len(
                {
                    r["record_id"]
                    for r in rows
                    if r["model"] == name and r["gap"] is not None
                }
            ),
        }
        for name in sorted({r["model"] for r in rows})
    }


def _contract_check(contract_path, expected_sha):
    if sha(contract_path) != expected_sha:
        raise ValueError("FROZEN_CONTRACT_SHA_MISMATCH")

    # Locate our exact serializable subobject without assuming parent field names.
    def contains(value):
        return (
            value == protocol()
            or isinstance(value, dict)
            and any(contains(v) for v in value.values())
            or isinstance(value, list)
            and any(contains(v) for v in value)
        )

    if not contains(read(contract_path)):
        raise ValueError("FROZEN_RELATION_PROTOCOL_CHANGED")


def run_nested(
    owner_dir,
    contract_path,
    expected_contract_sha256,
    summary_path="/private/tmp/m2-r3-constraints-summary.json",
    relations_only=False,
    expected_amendment_sha256=None,
):
    _contract_check(contract_path, expected_contract_sha256)
    owner, dst = Path(owner_dir), Path(owner_dir) / "revisions/r3"
    amendment_path = dst / "internal_feature_amendment.frozen.json"
    if not relations_only:
        if (
            not expected_amendment_sha256
            or sha(amendment_path) != expected_amendment_sha256
            or read(amendment_path)["protocol"] != internal_feature_amendment()
        ):
            raise ValueError("FROZEN_INTERNAL_FEATURE_AMENDMENT_REQUIRED")
    records = read(owner / "recovery_records.json")
    dev = [r for r in records if r["split"] == "DEVELOPMENT"]
    folds = read(owner / "revisions/r1/D0_folds.private.json")
    if folds != training.split_groups(dev, 3) or len(dev) != 211 or len(folds) != 187:
        raise ValueError("FROZEN_DEVELOPMENT_SCOPE_CHANGED")
    audits, model_entries, all_fixed, all_policies = [], [], [], []
    for outer in range(3):
        train = [r for r in dev if folds[r["group_id"]] != outer]
        held = [r for r in dev if folds[r["group_id"]] == outer]
        train_groups, held_groups = {r["group_id"] for r in train}, {
            r["group_id"] for r in held
        }
        expert_path = (
            owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{outer}.model.json"
        )
        expert = read(expert_path)
        audits.append(
            {
                "role": "REUSED_OUTER_R1",
                "outer": outer,
                "sha256": sha(expert_path),
                **audit_expert(expert, train, held),
            }
        )
        candidates = sorted(
            c for c in expert["candidate_vocabulary"] if c.startswith("sensory.")
        )
        inner_folds = training.split_groups(train, 2)
        inner_experts, inner_splits, relation_rows = [], [], []
        for inner in range(2):
            fitting = [r for r in train if inner_folds[r["group_id"]] != inner]
            validating = [r for r in train if inner_folds[r["group_id"]] == inner]
            model_path = (
                owner
                / f"revisions/r2/models/R2_R1_EXPERT_outer{outer}_inner{inner}.model.json"
            )
            inner_expert = read(model_path)
            audits.append(
                {
                    "role": "REUSED_INNER_R1",
                    "outer": outer,
                    "inner": inner,
                    "sha256": sha(model_path),
                    **audit_expert(inner_expert, fitting, validating),
                }
            )
            relation_rows.extend(collect_relation_rows(validating, inner_expert))
            inner_experts.append(inner_expert)
            inner_splits.append((fitting, validating))
        pairs = fit_relations(relation_rows, candidates, train_groups, held_groups)
        relations = fit_relations(
            relation_rows, candidates, train_groups, held_groups, pairs["pairs"]
        )
        relations["pair_receipt"] = pairs["receipt"]
        relation_bundle = runtime.make_bundle(
            expert,
            relations,
            contract_hash=expected_contract_sha256,
            tag=f"RELATIONS_outer{outer}",
        )
        model_path = dst / f"models/R3_RELATIONS_outer{outer}.model.json"
        save(model_path, relation_bundle)
        restored = read(model_path)
        fixed = evaluate_fixed(held, restored, outer)
        save(dst / f"trajectories/relations_outer{outer}.private.json", fixed)
        save(dst / f"oof/relation_training_outer{outer}.private.json", relation_rows)
        all_fixed.extend(fixed)
        model_entries.append(
            {
                "role": "RELATIONS",
                "outer": outer,
                "path": str(model_path),
                "sha256": sha(model_path),
            }
        )
        checkpoint = {
            "stage": "ACTUAL_RELATION_FIT_CHECKPOINT",
            "contract_sha256": expected_contract_sha256,
            "completed_outer_folds": outer + 1,
            "fixed_ASK_Q4": _summary(all_fixed),
            "models": model_entries,
            "latest_pair_receipt": pairs["receipt"],
            "latest_triple_receipt": relations["receipt"],
        }
        save(dst / "relation_checkpoint.private.json", checkpoint)
        save("/private/tmp/m2-r3-first-relation-checkpoint.json", checkpoint)
        print(
            json.dumps(
                {
                    "phase": "RELATIONS",
                    "outer": outer,
                    "pairs": len(relations["pairs"]),
                    "triples": len(relations["triples"]),
                    "fixed_Q4": _summary(fixed),
                }
            ),
            flush=True,
        )
        if relations_only:
            continue
        branch_rows = []
        for inner, (fitting, validating) in enumerate(inner_splits):
            deeper_folds = training.split_groups(fitting, 2)
            inner_relation_rows = []
            for deeper in range(2):
                deeper_train = [
                    r for r in fitting if deeper_folds[r["group_id"]] != deeper
                ]
                deeper_held = [
                    r for r in fitting if deeper_folds[r["group_id"]] == deeper
                ]
                path = (
                    dst
                    / f"models/R3_R1_EXPERT_outer{outer}_inner{inner}_deeper{deeper}_P1_INTERNAL.model.json"
                )
                if path.exists():
                    deeper_expert = read(path)
                    if (
                        deeper_expert.get("r3_internal_feature_amendment_sha256")
                        != expected_amendment_sha256
                    ):
                        raise ValueError("RELOADED_DEEPER_MODEL_AMENDMENT_MISMATCH")
                else:
                    stats = training.statistics(
                        deeper_train, expert["candidate_vocabulary"]
                    )
                    bank = training.legacy.make_bank(
                        stats, expert["candidate_attributes"]
                    )
                    array_bundle = training.make_bundle(
                        deeper_train,
                        manifest_hash=expected_contract_sha256,
                        vocabulary=expert["candidate_vocabulary"],
                        bank_override=bank,
                        canonical_broad_feedback=True,
                    )
                    arrays = p1_internal_training_arrays(
                        deeper_train, array_bundle, expected_contract_sha256
                    )
                    deeper_expert, _ = training.fit(
                        deeper_train,
                        expected_contract_sha256,
                        C=0.1,
                        vocabulary=expert["candidate_vocabulary"],
                        tag=f"R3_{outer}_{inner}_{deeper}",
                        bank_override=bank,
                        loss_mode="layered_conditional",
                        canonical_broad_feedback=True,
                        arrays=arrays,
                    )
                    deeper_expert["r3_internal_feature_amendment_sha256"] = (
                        expected_amendment_sha256
                    )
                    save(path, deeper_expert)
                audits.append(
                    {
                        "role": "NEW_DEEPER_BASE_R1",
                        "outer": outer,
                        "inner": inner,
                        "deeper": deeper,
                        "sha256": sha(path),
                        **audit_expert(deeper_expert, deeper_train, deeper_held),
                    }
                )
                inner_relation_rows.extend(
                    collect_relation_rows(deeper_held, deeper_expert)
                )
            fitting_groups = {r["group_id"] for r in fitting}
            excluded_groups = {r["group_id"] for r in validating + held}
            inner_pair = fit_relations(
                inner_relation_rows, candidates, fitting_groups, excluded_groups
            )
            inner_relation = fit_relations(
                inner_relation_rows,
                candidates,
                fitting_groups,
                excluded_groups,
                inner_pair["pairs"],
            )
            inner_bundle = runtime.make_bundle(
                inner_experts[inner],
                inner_relation,
                contract_hash=expected_contract_sha256,
                tag=f"INNER_RELATIONS_{outer}_{inner}",
            )
            save(
                dst / f"models/R3_INNER_RELATIONS_outer{outer}_inner{inner}.model.json",
                inner_bundle,
            )
            incoming = collect_branches(validating, inner_bundle, outer)
            save(dst / f"oof/trigger_outer{outer}_inner{inner}.private.json", incoming)
            branch_rows.extend(incoming)
        losses = {
            variant: macro(
                [
                    row["outcomes"]["ASK"]
                    for row in branch_rows
                    if row["variant"] == variant
                ]
            )
            for variant in runtime.VARIANTS
        }
        known = {v: loss for v, loss in losses.items() if loss is not None}
        minimum = min(known.values()) if known else None
        selected = next(
            (v for v in runtime.VARIANTS if v in known and known[v] <= minimum + 1e-12),
            "E1",
        )
        trigger_rows = [row for row in branch_rows if row["variant"] == selected]
        trigger_a = fit_trigger_a(trigger_rows, train_groups, held_groups)
        e1 = {row["record_id"]: row for row in branch_rows if row["variant"] == "E1"}
        b_rows = copy.deepcopy(trigger_rows)
        for row in b_rows:
            baseline = e1[row["record_id"]]["outcomes"]["ASK"]["gap"]
            selected_loss = row["outcomes"]["ASK"]["gap"]
            row["relation_gain"] = (
                baseline - selected_loss
                if baseline is not None and selected_loss is not None
                else None
            )
        trigger_b = fit_trigger_b(b_rows, train_groups, held_groups)
        full = runtime.make_bundle(
            expert,
            relations,
            trigger_a,
            trigger_b,
            expected_contract_sha256,
            f"NESTED_outer{outer}",
            empirical_support(train, expert),
            selected,
        )
        full_path = dst / f"models/R3_CONSTRAINTS_outer{outer}.model.json"
        save(full_path, full)
        model_entries.append(
            {
                "role": "CONSTRAINTS_AND_TRIGGERS",
                "outer": outer,
                "path": str(full_path),
                "sha256": sha(full_path),
            }
        )
        policy_results = []
        for record in held:
            for policy in runtime.POLICIES:
                ep, states, answers = trajectory(record, full, selected, policy)
                policy_results.append(
                    result_row(record, ep, states[-1], full, "Q4", policy, outer)
                )
            ep, states, answers = trajectory(
                record, full, selected, "ALWAYS_ASK", "TRIGGER_B"
            )
            policy_results.append(
                result_row(
                    record, ep, states[-1], full, "Q4", "TRIGGER_B_SEPARATE", outer
                )
            )
        all_policies.extend(policy_results)
        save(dst / f"trajectories/policies_outer{outer}.private.json", policy_results)
        save(
            dst / f"selection_outer{outer}.private.json",
            {
                "inner_fixed_ASK_Q4_losses": losses,
                "selected_variant": selected,
                "trigger_a": trigger_a,
                "trigger_b": trigger_b,
            },
        )
        print(
            json.dumps(
                {
                    "phase": "TRIGGERS",
                    "outer": outer,
                    "selected_variant": selected,
                    "inner_losses": losses,
                    "policies": _summary(policy_results),
                }
            ),
            flush=True,
        )
    summary = {
        "version": runtime.VERSION,
        "contract_sha256": expected_contract_sha256,
        "internal_feature_amendment_sha256": expected_amendment_sha256,
        "formal_nested_outer_folds": 3,
        "development_records": len(dev),
        "development_groups": len(folds),
        "fixed_ASK_Q4": _summary(all_fixed),
        "policy_Q4": _summary(all_policies),
        "models": model_entries,
        "reused_outer_experts": 3,
        "reused_inner_experts": 6,
        "new_deeper_experts": 0 if relations_only else 12,
        "scope": "COFFEE_GROUP_HELD_RECORD_RECOVERY_PROXY_NOT_REAL_INDIVIDUAL_ANSWER_VALIDATION",
        "default_B2_changed": False,
        "foundation_check_enabled": False,
    }
    save(dst / "constraint_isolation_audit.private.json", audits)
    save(dst / "relation_results.private.json", all_fixed)
    save(dst / "policy_results.private.json", all_policies)
    save(dst / "constraints_summary.private.json", summary)
    save(summary_path, summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", action="store_true")
    parser.add_argument("--owner-dir")
    parser.add_argument("--contract")
    parser.add_argument("--expected-contract-sha256")
    parser.add_argument("--relations-only", action="store_true")
    parser.add_argument("--expected-amendment-sha256")
    parser.add_argument(
        "--summary-path", default="/private/tmp/m2-r3-constraints-summary.json"
    )
    args = parser.parse_args()
    if args.protocol:
        print(json.dumps(protocol(), sort_keys=True, indent=2))
    elif args.owner_dir and args.contract and args.expected_contract_sha256:
        with threadpool_limits(limits=1):
            run_nested(
                args.owner_dir,
                args.contract,
                args.expected_contract_sha256,
                args.summary_path,
                args.relations_only,
                args.expected_amendment_sha256,
            )
    else:
        parser.error(
            "Formal fitting requires owner directory, frozen contract and expected SHA"
        )


if __name__ == "__main__":
    main()
