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


def full_development_protocol():
    return {
        "version": "r3-full-development-research-refit.v1",
        "basis": "OWNER_AUTHORIZED_FINAL_RESEARCH_ARTIFACT_AFTER_NESTED_EVALUATION",
        "scope": "ALL_211_DEVELOPMENT_RECORDS_187_COFFEE_GROUPS_NO_HISTORY",
        "base_expert": "REUSE_EXACT_AUDITED_ALL_DEVELOPMENT_M2_R1_FINAL_FIXED",
        "relation_training": "THREE_ORIGINAL_OUTER_R1_EXPERT_HELD_PREDICTIONS_UNION_ALL_DEV_BASE_OOF",
        "family_selection": "FROZEN_THREE_OUTER_RELATION_ASK_Q4_GROUP_MACRO_RAW_GAP_COMPLEXITY_TIE_E1_E2_E3",
        "trigger_training": "THREE_OUTER_RELATION_HELD_Q2_FEATURES_AND_A_DERIVED_ASK_SKIP_Q4_OUTCOMES_SELECTED_FAMILY",
        "parameters": "UNCHANGED_RIDGE10_SUPPORT_GATES_SHRINKAGE50_ASK_THRESHOLD0.01",
        "research_model": "R3_CONSTRAINTS_ALL_DEVELOPMENT.model.json",
        "performance_claim": "ONLY_EXISTING_NESTED_OUTER_POLICY_HELD_EVALUATION;FULL_TRAIN_OOF_NOT_GENERALIZATION",
        "default_B2_changed": False,
        "preservation": "ALL_OUTER_AND_INNER_MODELS_RETAINED_NO_REPLACEMENT",
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
        positive = (
            set(row["episode"]["hidden"])
            & set(candidates)
            & {item["candidate_id"] for item in row["base_rows"]}
        )
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
    known = [
        row
        for row in rows
        if set(row["episode"]["hidden"])
        & set(candidates)
        & {item["candidate_id"] for item in row["base_rows"]}
    ]
    if known and parameters:
        logits, q, active, mask, available = [], [], [], [], []
        for row in known:
            active_pairs = [
                term
                for term in pairs
                if term["term_id"] in {t["term_id"] for t in row["terms"]["2"]}
            ]
            base_rows = runtime.rank_from_base_rows(row["base_rows"], active_pairs)
            mapped = {item["candidate_id"]: item for item in base_rows}
            present_candidates = [c in mapped for c in candidates]
            available.append(present_candidates)
            logits.append(
                [mapped[c]["score"] if c in mapped else 0.0 for c in candidates]
            )
            relevance = row["episode"]["relevance"]
            target = np.array(
                [relevance.get(c, 0.0) if c in mapped else 0.0 for c in candidates],
                float,
            )
            q.append(target / target.sum())
            present = {term["term_id"] for term in row["terms"][str(order)]}
            active.append([float(identity in present) for identity in terms_index])
            mask.append([c in mapped and not mapped[c]["explicit"] for c in candidates])
        logits, q, active, mask, available = map(
            np.asarray, [logits, q, active, mask, available]
        )
        weights = group_weights(known)

        def objective(theta):
            matrix = np.zeros((len(terms), len(candidates)))
            for value, (i, j) in zip(theta, parameters, strict=True):
                matrix[i, j] = value
            z = logits + (active @ matrix) * mask
            # An OOF expert may lack a full-development vocabulary member.
            # Mask it out of the normalizer and loss; zero is only array padding.
            norm = logsumexp(z, b=available, axis=1)
            loss = np.sum(weights * (norm - np.sum(q * z, axis=1))) + 5 * (
                theta @ theta
            )
            residual = (
                (np.exp(z - norm[:, None]) * available - q) * weights[:, None] * mask
            )
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
            "row_candidate_availability_mask": "BASE_EXPERT_SCORED_IDS_ONLY_NO_FABRICATED_MISSING_LOGITS_OR_TARGET_ABSENCE",
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
        "stage": (
            "FINAL_RESULT"
            if slot == "FINAL_COMPARISON"
            else "FINAL" if slot == "Q4" else "CORRECTION"
        ),
        "model": model,
        "variant": state["variant"],
        "trigger_policy": state["trigger_policy"],
        **evaluated,
        "actual_main5": actual,
        "direct_visible_retention_at5": (
            len(visible & actual_ids) / len(visible) if visible else None
        ),
        "ordinary_questions": len(base["answers_by_question"]),
        "context_questions": 2,
        "context_offered_options": 15,
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
            "gap": macro(
                [
                    r
                    for r in rows
                    if r["model"] == name and r["slot"] in {"Q4", "FINAL_COMPARISON"}
                ]
            ),
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
    if (
        not relations_only
        and (dst / "constraints_completion_manifest.private.json").exists()
    ):
        return verify_completed(
            owner_dir,
            contract_path,
            expected_contract_sha256,
            expected_amendment_sha256,
        )["public_summary"]
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


def paired_summary(rows, treatment, control, field="gap"):
    """Fixed predictions, paired coffee bootstrap; no fitting or case selection."""
    keyed = {
        name: {
            (row["group_id"], row["record_id"]): row
            for row in rows
            if row["model"] == name
        }
        for name in [treatment, control]
    }
    if set(keyed[treatment]) != set(keyed[control]):
        raise ValueError("PAIRED_EVALUATION_COVERAGE_MISMATCH")
    pairs = [
        (keyed[treatment][key], keyed[control][key]) for key in sorted(keyed[treatment])
    ]
    labelled = [
        (a, b)
        for a, b in pairs
        if a.get(field) is not None and b.get(field) is not None
    ]
    groups = defaultdict(list)
    for a, b in labelled:
        groups[a["group_id"]].append(a[field] - b[field])
    values = np.array([np.mean(groups[g]) for g in sorted(groups)])
    rng = np.random.default_rng(20260906)
    boot = (
        np.mean(rng.choice(values, (2000, len(values)), replace=True), axis=1)
        if len(values)
        else np.array([])
    )
    options = defaultdict(list)
    for a, b in labelled:
        options[a["group_id"]].append(a["ordinary_options"] - b["ordinary_options"])
    option_delta = (
        float(np.mean([np.mean(v) for v in options.values()])) if options else None
    )
    return {
        "treatment": treatment,
        "control": control,
        "field": field,
        "all_case_records": len(pairs),
        "all_case_groups": len({a["group_id"] for a, _ in pairs}),
        "identifiable_records": len(labelled),
        "identifiable_groups": len(groups),
        "difference": float(np.mean(values)) if len(values) else None,
        "paired_coffee_bootstrap_95_interval": (
            np.quantile(boot, [0.025, 0.975]).tolist() if len(boot) else None
        ),
        "treatment_better_records": sum(
            a[field] < b[field] - 1e-12 for a, b in labelled
        ),
        "treatment_worse_records": sum(
            a[field] > b[field] + 1e-12 for a, b in labelled
        ),
        "tied_records": sum(abs(a[field] - b[field]) <= 1e-12 for a, b in labelled),
        "ordinary_option_delta_same_identifiable_cohort": option_delta,
        "operational_NI_and_lower_options": bool(
            len(boot) and np.quantile(boot, 0.975) <= 0.02 and option_delta < 0
        ),
        "interpretation": "FIXED_PREDICTION_PROXY_COFFEE_UNCERTAINTY_NOT_USER_ACCEPTABILITY_OR_REAL_TIME",
    }


def aggregate_terminal(rows):
    output = _summary(rows)
    for name in output:
        selected = [
            r
            for r in rows
            if r["model"] == name and r["slot"] in {"Q4", "FINAL_COMPARISON"}
        ]
        for key in [
            "ndcg",
            "recall",
            "ordinary_questions",
            "ordinary_options",
            "selected_retention_at5",
            "selected_retention_at8",
            "final_comparison_candidates",
        ]:
            output[name][key] = macro(selected, key)
        output[name]["ask_cases"] = sum(
            r.get("q2_decision", {}).get("action") == "ASK" for r in selected
        )
        output[name]["skip_cases"] = sum(
            r.get("q2_decision", {}).get("action") == "SKIP" for r in selected
        )
        output[name]["unidentifiable_records"] = sum(r["gap"] is None for r in selected)
        output[name]["source_results"] = {
            source: {
                "gap": macro([r for r in selected if r["source_family"] == source]),
                "all_records": sum(r["source_family"] == source for r in selected),
            }
            for source in sorted({r["source_family"] for r in selected})
        }
    return output


def relation_registry(models, relation_rows):
    registry = [
        {
            "id": "R3_K1_CONTRACT",
            "type": "HARD_CONTRACT",
            "status": "SUPPORTED_WITHIN_SCOPE",
            "condition": "C0_8_C1_7_ORDINARY_MAX4_OPTIONS_Q4_CLOSURE_ONE_FINAL_3_TO_8",
            "action": "REJECT_INVALID_CONTRACT_ONLY",
            "sensory_exclusion_accuracy": "NOT_ESTIMABLE",
        },
        {
            "id": "R3_K1_ENTAILMENT",
            "type": "SEMANTIC_ENTAILMENT",
            "status": "SUPPORTED_WITHIN_SCOPE",
            "condition": "CANONICAL_POSITIVE_PARENT_OR_FINE_CONCEPT",
            "action": "R1_EVIDENCE_ONCE_PARENT_NEVER_CHILD_ABSENCE_COMPOUND_WHOLE",
            "scope": "REGISTERED_SEMANTICS_NOT_NEW_SENSORY_MEASUREMENT",
        },
    ]
    for fold, model in enumerate(models):
        for order in ["pairs", "triples"]:
            for i, term in enumerate(model["relations"][order]):
                candidate_ids = set(term["coefficients"])
                active = [
                    row
                    for row in relation_rows
                    if row["fold"] == fold
                    and row["model"] == "E2"
                    and row["slot"] == "Q4"
                    and any(
                        term["term_id"] in candidate.get("relation_evidence_ids", [])
                        and candidate["relation_delta"] != 0
                        for candidate in row["ranking"]
                    )
                ]
                registry.append(
                    {
                        "id": f"R3_{order.upper()}_{fold}_{i}",
                        "outer_fold": fold,
                        "type": "EMPIRICAL_COMPATIBILITY",
                        "status": "SUPPORTED_WITHIN_SCOPE",
                        "scope": "TRAIN_GROUP_CONDITIONAL_MENTION_RETRIEVAL_NOT_CAUSAL_OR_ABSENCE",
                        "condition": term["pattern"],
                        "slots": term["slots"],
                        "candidate_effect_direction": {
                            candidate: (
                                "INCREASE_SOFT_PRIORITY"
                                if term["coefficients"][candidate] > 0
                                else (
                                    "DECREASE_SOFT_PRIORITY"
                                    if term["coefficients"][candidate] < 0
                                    else "NO_EFFECT"
                                )
                            )
                            for candidate in sorted(candidate_ids)
                        },
                        "training_group_support": term["training_group_support"],
                        "candidate_positive_group_support": term[
                            "candidate_positive_group_support"
                        ],
                        "held_Q4_active_records": len(active),
                        "hard_delete": False,
                        "training_evidence_group_hash": r1.digest(
                            term["training_groups"]
                        ),
                        "weights_release": False,
                    }
                )
        for name in ["trigger_a", "trigger_b"]:
            trigger = model[name]
            registry.append(
                {
                    "id": f"R3_{name.upper()}_{fold}",
                    "type": (
                        "LEARNED_QUESTION_TRIGGER"
                        if name == "trigger_a"
                        else "SEPARATE_RELATION_ACTIVATION_TRIGGER"
                    ),
                    "outer_fold": fold,
                    "status": (
                        "SUPPORTED_WITHIN_SCOPE" if trigger["enabled"] else "PROPOSED"
                    ),
                    "fit_status": trigger["fit_status"],
                    "labelled_groups": trigger["labelled_groups"],
                    "tied_training_rows_retained": trigger["tied_rows"],
                    "features": runtime.FEATURES,
                    "condition": "Q2_AFTER_CURRENT_ANSWERS_ONLY",
                    "action": (
                        "ASK_Q3_IF_GAIN_GT_0.01_ELSE_SKIP_TO_Q4"
                        if name == "trigger_a"
                        else "SEPARATE_ALWAYS_ASK_PATH_ACTIVATE_RELATION_IF_SUPPORTED_AND_GAIN_GT_0"
                    ),
                    "target": (
                        "SKIP_GAP_MINUS_ASK_GAP"
                        if name == "trigger_a"
                        else "E1_GAP_MINUS_SELECTED_RELATION_GAP"
                    ),
                    "default_changed": False,
                    "weights_release": False,
                }
            )
    return registry


def finish_evaluation(
    owner_dir, contract_path, expected_contract_sha256, expected_amendment_sha256
):
    """No-fit final feedback, counterfactual audit and compact private summaries."""
    _contract_check(contract_path, expected_contract_sha256)
    owner, dst = Path(owner_dir), Path(owner_dir) / "revisions/r3"
    ap = dst / "internal_feature_amendment.frozen.json"
    if (
        sha(ap) != expected_amendment_sha256
        or read(ap)["protocol"] != internal_feature_amendment()
    ):
        raise ValueError("FROZEN_INTERNAL_FEATURE_AMENDMENT_REQUIRED")
    records = [
        row
        for row in read(owner / "recovery_records.json")
        if row["split"] == "DEVELOPMENT"
    ]
    folds = read(owner / "revisions/r1/D0_folds.private.json")
    models, final_rows, counterfactual, checks = [], [], [], []
    before_hashes = {
        str(path.relative_to(dst)): sha(path)
        for path in (dst / "models").glob("*.json")
    }
    for outer in range(3):
        model = read(dst / f"models/R3_CONSTRAINTS_outer{outer}.model.json")
        runtime.check_bundle(model)
        if model["objective_contract_sha256"] != expected_contract_sha256:
            raise ValueError("RELOADED_CONSTRAINT_MODEL_CONTRACT_MISMATCH")
        models.append(model)
        train = [r for r in records if folds[r["group_id"]] != outer]
        held = [r for r in records if folds[r["group_id"]] == outer]
        for inner in range(2):
            innersplit = training.split_groups(train, 2)
            fitting = [r for r in train if innersplit[r["group_id"]] != inner]
            for deeper in range(2):
                deepsplit = training.split_groups(fitting, 2)
                deeptrain = [r for r in fitting if deepsplit[r["group_id"]] != deeper]
                path = (
                    dst
                    / f"models/R3_R1_EXPERT_outer{outer}_inner{inner}_deeper{deeper}_P1_INTERNAL.model.json"
                )
                deepmodel = read(path)
                if (
                    deepmodel.get("r3_internal_feature_amendment_sha256")
                    != expected_amendment_sha256
                ):
                    raise ValueError("DEEPER_RELOAD_AMENDMENT_MISMATCH")
                arrays = p1_internal_training_arrays(
                    deeptrain, deepmodel, expected_contract_sha256
                )
                scale = np.sqrt(np.mean(arrays[0] * arrays[0], axis=(0, 1)))
                scale[scale < 1e-8] = 1.0
                scale[r1.FEATURES.index("exposed_rejection")] = 1.0
                if arrays[3] != deepmodel["fit_receipt"][
                    "inner_feature_audit"
                ] or not np.allclose(
                    scale, deepmodel["scaler_parameters"]["scale"], rtol=0, atol=1e-12
                ):
                    raise ValueError(
                        "RELOADED_INTERNAL_BANK_FEATURE_OR_SCALER_MISMATCH"
                    )
                checks.append(
                    {
                        "model_owner_relative_path": str(path.relative_to(owner)),
                        "sha256": sha(path),
                        "internal_bank_hash_and_group_audit_recomputed_identical": True,
                        "scaler_recomputed_identical_at_1e12": True,
                    }
                )
        for record in held:
            ep, ask_states, ask_answers = trajectory(
                record, model, model["selected_variant"], "ALWAYS_ASK"
            )
            q2 = next(
                state
                for state in ask_states
                if set(state["base_state"]["answers_by_question"]) == {"Q0", "Q1", "Q2"}
            )
            skipped, _ = runtime.complete_branch(q2, ep["visible"], model, "SKIP")
            for action, state in [("ASK", ask_states[-1]), ("SKIP", skipped)]:
                counterfactual.append(
                    result_row(record, ep, state, model, "Q4", action, outer, action)
                )
            for policy in ["ALWAYS_ASK", "LEARNED"]:
                if policy == "ALWAYS_ASK":
                    states, answers = ask_states, ask_answers
                else:
                    _, states, answers = trajectory(
                        record, model, model["selected_variant"], policy
                    )
                pre = runtime.finalize_result(states[-1], model)
                exposure = pre["exposure"]
                if not exposure or not exposure["eligible_for_final_comparison"]:
                    raise ValueError(
                        "EVERY_REGISTERED_FINAL_CASE_REQUIRES_ACTUAL_EXPOSURE"
                    )
                selected = sorted(set(ep["visible"]) & set(exposure["candidate_ids"]))
                if set(selected) & set(ep["hidden"]):
                    raise ValueError("FROZEN_A_T_SEPARATION_FAILED")
                feedback = {
                    "exposed_candidates": exposure["candidate_ids"],
                    "selected_candidates": selected,
                    "feedback_source": "SIMULATED",
                    "generation_version": model["bundle_id"],
                }
                for mode in ["F0", "F1", "F2"]:
                    final = runtime.apply_final_comparison(
                        pre["state"], feedback, model, mode
                    )
                    finalized = runtime.finalize_result(final, model)
                    if (
                        finalized["stage"] != "FINAL_RESULT"
                        or finalized["next"]["action"] == "ASK"
                    ):
                        raise ValueError("FINAL_RESULT_NOT_TERMINAL")
                    row = result_row(
                        record,
                        ep,
                        final,
                        model,
                        "FINAL_COMPARISON",
                        policy + "/" + mode,
                        outer,
                    )
                    ids5 = {r["candidate_id"] for r in finalized["main"]}
                    ids8 = ids5 | {r["candidate_id"] for r in finalized["secondary"]}
                    row.update(
                        final_mode=mode,
                        feedback_source="SIMULATED",
                        selected_count=len(selected),
                        exposed_candidates=exposure["candidate_ids"],
                        selected_candidates=selected,
                        selected_retention_at5=(
                            len(set(selected) & ids5) / len(selected)
                            if selected
                            else None
                        ),
                        selected_retention_at8=(
                            len(set(selected) & ids8) / len(selected)
                            if selected
                            else None
                        ),
                        final_comparison_candidates=len(exposure["candidate_ids"]),
                        final_answer_basis="INDEPENDENT_FROZEN_A_INTERSECT_ACTUALLY_EXPOSED_POOL_NEVER_T",
                    )
                    final_rows.append(row)
                    # All live requests, including final once-only validation, are replayed.
                    payload = {
                        "contract_version": runtime.VERSION,
                        "context": ep["context"],
                        "variant": model["selected_variant"],
                        "trigger_policy": policy,
                        "answers": answers,
                        "final_comparison": feedback,
                        "final_mode": mode,
                    }
                    replayed = runtime.run(payload, model)
                    if [
                        (r["candidate_id"], r["score"])
                        for r in finalized["state"]["candidate_scores"]
                    ] != [
                        (r["candidate_id"], r["score"])
                        for r in replayed["state"]["candidate_scores"]
                    ]:
                        raise ValueError("FULL_LIVE_REPLAY_FINAL_RANK_PARITY_FAILED")
    after_hashes = {
        str(path.relative_to(dst)): sha(path)
        for path in (dst / "models").glob("*.json")
    }
    if before_hashes != after_hashes:
        raise ValueError("EVALUATION_MUTATED_MODEL_ARTIFACT")
    relations = read(dst / "relation_results.private.json")
    policies = read(dst / "policy_results.private.json")
    registry = relation_registry(models, relations)
    counter_pairs = {
        action: {
            row["record_id"]: row for row in counterfactual if row["model"] == action
        }
        for action in ["ASK", "SKIP"]
    }
    examples = []
    for record_id, asked in counter_pairs["ASK"].items():
        skipped = counter_pairs["SKIP"][record_id]
        if asked["gap"] is None:
            continue
        gain = skipped["gap"] - asked["gap"]
        before, after = [r["candidate_id"] for r in skipped["ranking"][:5]], [
            r["candidate_id"] for r in asked["ranking"][:5]
        ]
        if gain or before != after:
            examples.append(
                {
                    "record_id": record_id,
                    "group_id": asked["group_id"],
                    "source_family": asked["source_family"],
                    "fold": asked["fold"],
                    "Q3_gain": gain,
                    "ask_gap": asked["gap"],
                    "skip_gap": skipped["gap"],
                    "ask_ndcg": asked["ndcg"],
                    "skip_ndcg": skipped["ndcg"],
                    "extra_actual_options": asked["ordinary_options"]
                    - skipped["ordinary_options"],
                    "question_condition_features": asked["q2_decision"].get(
                        "feature_values"
                    ),
                    "added_main_candidates": sorted(set(after) - set(before)),
                    "removed_main_candidates": sorted(set(before) - set(after)),
                    "fixed_visible_count": len(asked["episode"]["visible"]),
                    "hidden_fine_target_count": sum(
                        c.startswith("sensory.") for c in asked["episode"]["hidden"]
                    ),
                    "episode": asked["episode"],
                    "kind": (
                        "Q3_GAIN"
                        if gain > 0
                        else (
                            "Q3_HARM"
                            if gain < 0
                            else "SET_MATCHING_TIE_WITH_RANK_CHANGE"
                        )
                    ),
                }
            )
    examples.sort(key=lambda row: (-abs(row["Q3_gain"]), row["record_id"]))
    selected_examples = []
    for kind in ["Q3_GAIN", "Q3_HARM", "SET_MATCHING_TIE_WITH_RANK_CHANGE"]:
        selected_examples.extend([row for row in examples if row["kind"] == kind][:4])
    public_examples = [
        {
            "case": f"R3_COUNTERFACTUAL_{i+1:02d}",
            **{
                k: v
                for k, v in row.items()
                if k not in {"record_id", "group_id", "episode"}
            },
        }
        for i, row in enumerate(selected_examples)
    ]
    summary = {
        "version": runtime.VERSION,
        "contract_sha256": expected_contract_sha256,
        "internal_feature_amendment_sha256": expected_amendment_sha256,
        "fixed_relation_Q4": aggregate_terminal(
            [r for r in relations if r["slot"] == "Q4"]
        ),
        "policy_Q4": aggregate_terminal(policies),
        "final_feedback": aggregate_terminal(final_rows),
        "relation_primary": paired_summary(
            [r for r in relations if r["slot"] == "Q4"], "E2", "E1"
        ),
        "policy_comparisons": [
            paired_summary(policies, policy, "ALWAYS_ASK")
            for policy in [
                "LEARNED",
                "SIMPLE_RULE",
                "TWO_STEP_EMPIRICAL",
                "TRIGGER_B_SEPARATE",
            ]
        ],
        "final_comparisons": [
            paired_summary(final_rows, policy + "/" + mode, policy + "/F0")
            for policy in ["ALWAYS_ASK", "LEARNED"]
            for mode in ["F1", "F2"]
        ],
        "counterfactual_Q3": paired_summary(counterfactual, "ASK", "SKIP"),
        "counterfactual_error_class_counts": dict(
            Counter(row["kind"] for row in examples)
        ),
        "counterfactual_cases_scope": "DETAILED_ACTUAL_PREDICTIONS_AND_CASE_IDENTITIES_PRIVATE_ONLY",
        "final_feedback_answer_scope": "FROZEN_A_INTERSECT_ACTUAL_POOL;T_NEVER_GENERATES_FEEDBACK;F0_COUNTS_SAME_EXPOSURE_WITHOUT_RANK_UPDATE",
        "selected_retention_separate_from_hidden_not_directly_selected_recovery": True,
        "full_case_denominator_preserved": True,
        "human_time": None,
        "context_information_cost": {
            "questions": 2,
            "offered_options": 15,
            "separate_from_ordinary_sensory_cost": True,
        },
        "no_fitting_in_this_evaluation": True,
        "all_private_model_hashes_unchanged": True,
        "deepest_internal_bank_and_scaler_recomputed_identical": len(checks),
        "full_final_live_replays_identical": len(final_rows),
        "default_B2_changed": False,
        "foundation_check_enabled": False,
    }
    save(dst / "final_feedback_results.private.json", final_rows)
    save(dst / "counterfactual_Q3_results.private.json", counterfactual)
    save(dst / "counterfactual_error_examples.private.json", selected_examples)
    save(dst / "constraint_relation_trigger_registry.private.json", registry)
    save(dst / "constraints_reload_audit.private.json", checks)
    save(dst / "constraints_public_summary.private.json", summary)
    save("/private/tmp/m2-r3-constraints-public-summary.json", summary)
    print(
        json.dumps(
            {
                "phase": "NO_FIT_FINAL_EVALUATION",
                "policies": summary["policy_comparisons"],
                "final_rows": len(final_rows),
                "deepest_scalers_recomputed": len(checks),
            }
        ),
        flush=True,
    )
    return summary


def fit_full_development(
    owner_dir, contract_path, contract_sha, amendment_sha, full_contract_sha
):
    """Exactly one all-development research refit from frozen expert OOF."""
    _contract_check(contract_path, contract_sha)
    owner, dst = Path(owner_dir), Path(owner_dir) / "revisions/r3"
    full_path = dst / "full_development_contract.frozen.json"
    if (
        sha(full_path) != full_contract_sha
        or read(full_path)["protocol"] != full_development_protocol()
    ):
        raise ValueError("FULL_DEVELOPMENT_FROZEN_CONTRACT_MISMATCH")
    if sha(dst / "internal_feature_amendment.frozen.json") != amendment_sha:
        raise ValueError("INTERNAL_AMENDMENT_SHA_MISMATCH")
    model_path = dst / "models/R3_CONSTRAINTS_ALL_DEVELOPMENT.model.json"
    receipt_path = dst / "full_development_fit_receipt.private.json"
    if model_path.exists():
        receipt = read(receipt_path)
        if (
            sha(model_path) != receipt["model_sha256"]
            or receipt["full_development_contract_sha256"] != full_contract_sha
        ):
            raise ValueError("FROZEN_FULL_DEVELOPMENT_MODEL_CHANGED")
        runtime.check_bundle(read(model_path))
        return receipt
    records = read(owner / "recovery_records.json")
    dev = [r for r in records if r["split"] == "DEVELOPMENT"]
    historical = [r for r in records if r["split"] != "DEVELOPMENT"]
    groups = {r["group_id"] for r in dev}
    folds = read(owner / "revisions/r1/D0_folds.private.json")
    expert_path = owner / "revisions/r1/models/M2_R1_FINAL_FIXED.model.json"
    expert = read(expert_path)
    audit = audit_expert(expert, dev, historical)
    relation_rows = []
    for outer in range(3):
        outer_expert = read(
            owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{outer}.model.json"
        )
        held = [r for r in dev if folds[r["group_id"]] == outer]
        train = [r for r in dev if folds[r["group_id"]] != outer]
        audit_expert(outer_expert, train, held)
        relation_rows.extend(collect_relation_rows(held, outer_expert))
    candidates = sorted(
        c for c in expert["candidate_vocabulary"] if c.startswith("sensory.")
    )
    pairs = fit_relations(relation_rows, candidates, groups)
    relations = fit_relations(
        relation_rows, candidates, groups, frozen_pairs=pairs["pairs"]
    )
    relations["pair_receipt"] = pairs["receipt"]
    fixed_rows = [
        r for r in read(dst / "relation_results.private.json") if r["slot"] == "Q4"
    ]
    losses = {
        variant: macro([r for r in fixed_rows if r["model"] == variant])
        for variant in runtime.VARIANTS
    }
    minimum = min(loss for loss in losses.values() if loss is not None)
    selected = next(
        v
        for v in runtime.VARIANTS
        if losses[v] is not None and losses[v] <= minimum + 1e-12
    )
    counter = read(dst / "counterfactual_Q3_results.private.json")
    mapped = {
        action: {r["record_id"]: r for r in counter if r["model"] == action}
        for action in ["ASK", "SKIP"]
    }
    trigger_rows = []
    for record in dev:
        asked, skipped = (
            mapped["ASK"][record["record_id"]],
            mapped["SKIP"][record["record_id"]],
        )
        if asked["variant"] != selected or skipped["variant"] != selected:
            raise ValueError("FULL_TRIGGER_REQUIRES_OUTER_OOF_SELECTED_FAMILY_OUTCOMES")
        trained = [r["group_id"] for r in dev if folds[r["group_id"]] != asked["fold"]]
        trigger_rows.append(
            {
                "group_id": record["group_id"],
                "record_id": record["record_id"],
                "slot": "Q2",
                "features": asked["q2_decision"]["feature_values"],
                "gain": (
                    skipped["gap"] - asked["gap"] if asked["gap"] is not None else None
                ),
                "relation_training_groups": sorted(set(trained)),
            }
        )
    trigger_a = fit_trigger_a(trigger_rows, groups)
    b_rows = copy.deepcopy(trigger_rows)
    fixed_map = {
        variant: {r["record_id"]: r for r in fixed_rows if r["model"] == variant}
        for variant in runtime.VARIANTS
    }
    for row in b_rows:
        first, second = (
            fixed_map["E1"][row["record_id"]]["gap"],
            fixed_map[selected][row["record_id"]]["gap"],
        )
        row["relation_gain"] = (
            first - second if first is not None and second is not None else None
        )
    trigger_b = fit_trigger_b(b_rows, groups)
    model = runtime.make_bundle(
        expert,
        relations,
        trigger_a,
        trigger_b,
        contract_sha,
        "ALL_DEVELOPMENT",
        empirical_support(dev, expert),
        selected,
        training_lineage={
            "full_development_contract_sha256": full_contract_sha,
            "internal_feature_amendment_sha256": amendment_sha,
            "base_oof_groups": len(groups),
            "full_training_oof_not_used_as_generalization": True,
            "research_artifact_default_unchanged": True,
        },
    )
    save(model_path, model)
    restored = read(model_path)
    for record in dev[:3]:
        for variant in runtime.VARIANTS:
            _, states, _ = trajectory(record, model, variant)
            for state in states:
                if runtime.rank_candidates(
                    state["base_state"], model, variant
                ) != runtime.rank_candidates(state["base_state"], restored, variant):
                    raise ValueError("FULL_DEVELOPMENT_MODEL_RELOAD_MISMATCH")
    receipt = {
        "full_development_contract_sha256": full_contract_sha,
        "internal_feature_amendment_sha256": amendment_sha,
        "original_contract_sha256": contract_sha,
        "model_owner_relative_path": str(model_path.relative_to(owner)),
        "model_sha256": sha(model_path),
        "bundle_id": model["bundle_id"],
        "selected_variant": selected,
        "selection_losses_after_nested_development_evaluation": losses,
        "training_records": len(dev),
        "training_groups": len(groups),
        "base_expert_audit": audit,
        "pair_receipt": pairs["receipt"],
        "triple_receipt": relations["receipt"],
        "trigger_a": trigger_a,
        "trigger_b": trigger_b,
        "exactly_one_logical_final_refit": True,
        "full_model_train_OOF_not_generalization": True,
        "reload_identical": True,
    }
    save(receipt_path, receipt)
    print(
        json.dumps(
            {
                "phase": "ALL_DEVELOPMENT_RESEARCH_REFIT",
                "selected_variant": selected,
                "pair_terms": len(relations["pairs"]),
                "triple_terms": len(relations["triples"]),
                "trigger_labelled_groups": trigger_a["labelled_groups"],
                "model_sha256": receipt["model_sha256"],
            }
        ),
        flush=True,
    )
    return receipt


def scoring_code_fingerprints():
    directory = Path(__file__).resolve().parent
    return {
        name: sha(directory / name)
        for name in [
            "flavor_constraints_r3.py",
            "train_constraints_r3.py",
            "alignment_metrics_r3.py",
        ]
    }


def audit_runtime_projection(owner_dir):
    """Check annotation additions against every retained inner OOF feature row."""
    owner, dst = Path(owner_dir), Path(owner_dir) / "revisions/r3"
    records = {r["record_id"]: r for r in read(owner / "recovery_records.json")}
    feature_count = rank_count = state_count = order_changes = revision_states = 0
    status_counts, retention = Counter(), []

    def score_identity(rows):
        return [(row["candidate_id"], row["score"], row["rank"]) for row in rows]

    for outer in range(3):
        for inner in range(2):
            model = read(
                dst / f"models/R3_INNER_RELATIONS_outer{outer}_inner{inner}.model.json"
            )
            expected_rows = read(
                dst / f"oof/trigger_outer{outer}_inner{inner}.private.json"
            )
            for expected in expected_rows:
                ep, states, _ = trajectory(
                    records[expected["record_id"]],
                    model,
                    expected["variant"],
                    "ALWAYS_ASK",
                )
                q2 = next(
                    s
                    for s in states
                    if set(s["base_state"]["answers_by_question"]) == {"Q0", "Q1", "Q2"}
                )
                if runtime.live_features(q2, model) != expected["features"]:
                    raise ValueError(
                        "AUDIT_PROJECTION_CHANGED_RETAINED_TRIGGER_FEATURES"
                    )
                feature_count += 1
                skipped, _ = runtime.complete_branch(q2, ep["visible"], model, "SKIP")
                for action, state in [("ASK", states[-1]), ("SKIP", skipped)]:
                    if score_identity(state["candidate_scores"]) != score_identity(
                        expected["outcomes"][action]["ranking"]
                    ):
                        raise ValueError(
                            "AUDIT_PROJECTION_CHANGED_RETAINED_BRANCH_RANKING"
                        )
                    rank_count += 1
                for state in states[2:]:
                    state_count += 1
                    status_counts.update(h["status"] for h in state["k1_hypotheses"])
                    revision_states += any(
                        h["status"] == "REVISED" for h in state["k1_hypotheses"]
                    )
                    order_changes += state["k1_diagnostics"][
                        "actual_candidate_order_changed_from_previous"
                    ]
                    value = state["k1_diagnostics"][
                        "target_direction_retention_from_previous_current_evidence"
                    ]
                    if value is not None:
                        retention.append(value)
    counter = read(dst / "counterfactual_Q3_results.private.json")
    matched = {
        action: {r["record_id"]: r for r in counter if r["model"] == action}
        for action in ["ASK", "SKIP"]
    }
    bins = defaultdict(list)
    for identity, asked in matched["ASK"].items():
        skipped = matched["SKIP"][identity]
        feature = asked["q2_decision"]["feature_values"]
        name = (
            (
                "DIMENSIONS_LE_1"
                if feature["dimension_count"] <= 1
                else "DIMENSIONS_GT_1"
            )
            + "/"
            + (
                "NO_EXPLICIT_FINE"
                if feature["explicit_fine_count"] == 0
                else "EXPLICIT_FINE_PRESENT"
            )
        )
        gain = skipped["gap"] - asked["gap"] if asked["gap"] is not None else None
        bins[name].append(
            {"record_id": identity, "group_id": asked["group_id"], "gain": gain}
        )
    coarse = {
        name: {
            "all_records": len(rows),
            "all_groups": len({r["group_id"] for r in rows}),
            "identifiable_records": sum(r["gain"] is not None for r in rows),
            "Q3_group_macro_gain": macro(rows, "gain"),
            "Q3_helped_records": sum(
                r["gain"] is not None and r["gain"] > 1e-12 for r in rows
            ),
            "Q3_harmed_records": sum(
                r["gain"] is not None and r["gain"] < -1e-12 for r in rows
            ),
            "Q3_tied_records": sum(
                r["gain"] is not None and abs(r["gain"]) <= 1e-12 for r in rows
            ),
        }
        for name, rows in sorted(bins.items())
    }
    original_path, enriched_path = (
        owner / "human_comparison_cases.private.json",
        owner / "revisions/r2/human_comparison_cases_r2.private.json",
    )
    original, enriched = read(original_path), read(enriched_path)
    if (
        len(original) != 20
        or len(enriched) != 20
        or {r["case_id"] for r in original} != {r["case_id"] for r in enriched}
    ):
        raise ValueError("ORIGINAL_TWENTY_HUMAN_CASE_IDENTITIES_CHANGED")
    completed = [
        r
        for r in enriched
        if r.get("corrective_selection") is not None
        or r.get("human_choice") is not None
    ]
    if completed:
        raise ValueError(
            "NEW_ACTUAL_HUMAN_FEEDBACK_REQUIRES_VALIDATED_ORIGINAL_EXPOSURE_IMPORT"
        )
    human = {
        "original_cases": len(original),
        "enriched_cases_reused_by_identity": len(enriched),
        "original_case_file_sha256": sha(original_path),
        "enriched_case_file_sha256": sha(enriched_path),
        "roles": dict(Counter(r["review_role"] for r in original)),
        "completed_human_judgments": 0,
        "actual_corrective_selections": 0,
        "human_rationales": sum(bool(r.get("human_rationale")) for r in enriched),
        "actual_human_seconds": None,
        "pending_cases": 20,
        "status": "NOT_EVALUATED_REAL_HUMAN_FEEDBACK_NOT_COLLECTED",
        "ordinary_answers": "EXISTING_SIMULATED_RECORD_DERIVED_INPUT_NOT_REAL_HUMAN_ANSWERS",
        "old_exposure_not_remapped_to_R3": True,
        "new_participants_or_responses_generated": False,
    }
    audit = {
        "audit_version": runtime.AUDIT_VERSION,
        "retained_inner_trigger_feature_rows_recomputed_identical": feature_count,
        "retained_inner_ASK_SKIP_full_rankings_recomputed_identical": rank_count,
        "audited_initial_correction_states": state_count,
        "hypothesis_status_counts": dict(status_counts),
        "states_with_revised_hypothesis": revision_states,
        "actual_candidate_order_change_states": order_changes,
        "mean_current_evidence_direction_retention": (
            float(np.mean(retention)) if retention else None
        ),
        "retention_observations": len(retention),
        "counts_are_repeated_oof_trajectory_states_not_independent_samples": True,
        "error_pruned_candidate_count": 0,
        "incompatibility_accuracy": "NOT_ESTIMABLE_WITHOUT_INDEPENDENT_DIRECTION_INCOMPATIBILITY_LABELS",
        "no_model_or_trigger_feature_change": True,
        "no_fit": True,
        "Q3_coarse_feature_bins": coarse,
        "original20_human_case_reuse": human,
    }
    save(dst / "constraints_runtime_projection_audit.private.json", audit)
    summary = read(dst / "constraints_public_summary.private.json")
    summary.update(
        runtime_K1_actual_audit=audit,
        original20_human_case_reuse=human,
        Q3_coarse_feature_bins=coarse,
    )
    summary.pop("counterfactual_examples", None)
    save(dst / "constraints_public_summary.private.json", summary)
    receipt_path = dst / "full_development_fit_receipt.private.json"
    receipt = read(receipt_path)
    receipt["implementation_attempts"] = [
        {
            "status": "PRE_OPTIMIZER_KEY_ERROR",
            "candidate": "sensory.hay",
            "reason": "ALL_DEVELOPMENT_CANDIDATE_MISSING_IN_ONE_OUTER_OOF_EXPERT_SCOPE",
            "no_completed_full_model_or_optimizer_fit": True,
        },
        {
            "status": "COMPLETED_AFTER_ROW_AVAILABILITY_MASK_FIX",
            "protocol_retuned": False,
            "outer_models_retrained": False,
        },
    ]
    receipt["full_candidate_vocabulary_exactly_all_DEVELOPMENT_TRAIN"] = True
    receipt[
        "missing_OOF_candidates_excluded_from_row_loss_not_from_any_evaluation_target_denominator"
    ] = True
    save(receipt_path, receipt)
    print(
        json.dumps(
            {
                "phase": "AUDIT_ONLY_PROJECTION_PARITY",
                "features": feature_count,
                "branch_rankings": rank_count,
                "hypothesis_statuses": dict(status_counts),
                "human_feedback": 0,
            }
        ),
        flush=True,
    )
    return audit


def evaluate_history(owner_dir):
    """One frozen-model evaluation of the already viewed historical 17 groups."""
    owner, dst = Path(owner_dir), Path(owner_dir) / "revisions/r3"
    summary_path = dst / "history_public_summary.private.json"
    if summary_path.exists():
        summary = read(summary_path)
        if (
            sha(dst / "models/R3_CONSTRAINTS_ALL_DEVELOPMENT.model.json")
            != summary["full_model_sha256"]
        ):
            raise ValueError("HISTORICAL_MODEL_HASH_CHANGED")
        return summary
    model_path = dst / "models/R3_CONSTRAINTS_ALL_DEVELOPMENT.model.json"
    before = sha(model_path)
    model = read(model_path)
    records = [
        r for r in read(owner / "recovery_records.json") if r["split"] != "DEVELOPMENT"
    ]
    if (
        len(records) != 17
        or len({r["group_id"] for r in records}) != 17
        or {r["group_id"] for r in records} & expert_training_groups(model["r1_expert"])
    ):
        raise ValueError("HISTORICAL_SEVENTEEN_GROUP_SCOPE_MISMATCH")
    rows = []
    for record in records:
        for policy in ["ALWAYS_ASK", "LEARNED"]:
            ep, states, answers = trajectory(
                record, model, model["selected_variant"], policy
            )
            pre = runtime.finalize_result(states[-1], model)
            rows.append(
                result_row(record, ep, pre["state"], model, "Q4", policy + "/Q4")
            )
            exposure = pre["exposure"]
            selected = sorted(set(ep["visible"]) & set(exposure["candidate_ids"]))
            feedback = {
                "exposed_candidates": exposure["candidate_ids"],
                "selected_candidates": selected,
                "feedback_source": "SIMULATED",
                "generation_version": model["bundle_id"],
            }
            state = runtime.apply_final_comparison(pre["state"], feedback, model)
            row = result_row(
                record, ep, state, model, "FINAL_COMPARISON", policy + "/F2"
            )
            row["final_comparison_candidates"] = len(exposure["candidate_ids"])
            rows.append(row)
    if before != sha(model_path):
        raise ValueError("HISTORICAL_EVALUATION_CHANGED_MODEL")
    summary = {
        "scope": "ALREADY_VIEWED_17_HISTORICAL_COFFEE_GROUPS_NOT_FRESH_CONFIRMATION",
        "records": 17,
        "groups": 17,
        "no_fit_or_selection": True,
        "full_model_sha256": before,
        "results": aggregate_terminal(rows),
        "actual_human_seconds": None,
        "answers_and_F2_selection": "FROZEN_SOURCE_RECORD_A_ONLY_NOT_HIDDEN_T",
        "R2_history_unchanged": True,
    }
    save(dst / "history_results.private.json", rows)
    save(summary_path, summary)
    print(
        json.dumps(
            {
                "phase": "HISTORICAL_NO_FIT_REGRESSION",
                "results": {k: v["gap"] for k, v in summary["results"].items()},
            }
        ),
        flush=True,
    )
    return summary


def direction_metrics(
    targets, fixed_candidates, preferred_candidates, hypothesis_directions
):
    fine = {c for c in targets if c.startswith("sensory.")}
    target_directions = {a for c in fine for a in r1.PARENTS.get(c, [])}
    legal = set(fixed_candidates)
    preferred = set(preferred_candidates) & legal
    legal_directions = {a for c in legal for a in r1.PARENTS.get(c, [])}
    hyp = set(hypothesis_directions)
    return {
        "hidden_fine_target_count": len(fine),
        "hidden_target_direction_count": len(target_directions),
        "hidden_targets_with_unknown_parent_count": sum(
            not r1.PARENTS.get(c) for c in fine
        ),
        "preferred_direction_coverage": (
            len(target_directions & hyp) / len(target_directions)
            if target_directions
            else None
        ),
        "fixed_universe_direction_coverage": (
            len(target_directions & legal_directions) / len(target_directions)
            if target_directions
            else None
        ),
        "target_direction_outside_preferred_scope": (
            len((target_directions & legal_directions) - hyp) / len(target_directions)
            if target_directions
            else None
        ),
        "preferred_exact_leaf_coverage": (
            len(fine & preferred) / len(fine) if fine else None
        ),
        "fixed_universe_exact_leaf_coverage": (
            len(fine & legal) / len(fine) if fine else None
        ),
        "legal_hidden_leaf_outside_preferred_scope": (
            len((fine & legal) - preferred) / len(fine) if fine else None
        ),
        "hard_pruned_candidates": 0,
    }


def evaluate_hidden_directions(owner_dir):
    """Descriptive held-T directions; never used to form a hypothesis or fit."""
    owner, dst = Path(owner_dir), Path(owner_dir) / "revisions/r3"
    records = [
        r for r in read(owner / "recovery_records.json") if r["split"] == "DEVELOPMENT"
    ]
    folds = read(owner / "revisions/r1/D0_folds.private.json")
    rows = []
    for outer in range(3):
        model = read(dst / f"models/R3_CONSTRAINTS_outer{outer}.model.json")
        for record in [r for r in records if folds[r["group_id"]] == outer]:
            ep, states, answers = trajectory(record, model, "E1", "ALWAYS_ASK")
            for state, answer in zip(states[1:], answers, strict=True):
                if answer["slot"] not in {"Q1", "Q2", "Q3"}:
                    continue
                active = [
                    h
                    for h in state["k1_hypotheses"]
                    if h["applicability"]["active_positive_support"]
                ]
                preferred = {c for h in active for c in h["preferred_legal_candidates"]}
                hypotheses = {h["dimension"] for h in active}
                values = direction_metrics(
                    ep["hidden"], model["fixed_candidates"], preferred, hypotheses
                )
                rows.append(
                    {
                        "record_id": record["record_id"],
                        "group_id": record["group_id"],
                        "source_family": record["source_family"],
                        "fold": outer,
                        "slot": answer["slot"],
                        **values,
                        "preferred_candidates": sorted(preferred),
                        "hypothesis_directions": sorted(hypotheses),
                        "episode": ep,
                    }
                )
    stage_summary = {}
    fields = [
        "preferred_direction_coverage",
        "fixed_universe_direction_coverage",
        "target_direction_outside_preferred_scope",
        "preferred_exact_leaf_coverage",
        "fixed_universe_exact_leaf_coverage",
        "legal_hidden_leaf_outside_preferred_scope",
    ]
    for slot in ["Q1", "Q2", "Q3"]:
        subset = [r for r in rows if r["slot"] == slot]
        stage_summary[slot] = {
            "all_records": len(subset),
            "all_groups": len({r["group_id"] for r in subset}),
            "identifiable_direction_records": sum(
                r["preferred_direction_coverage"] is not None for r in subset
            ),
            **{field: macro(subset, field) for field in fields},
        }
    pairs = {
        slot: {row["record_id"]: row for row in rows if row["slot"] == slot}
        for slot in ["Q2", "Q3"]
    }
    comparable = [
        (a, pairs["Q3"][identity])
        for identity, a in pairs["Q2"].items()
        if a["preferred_direction_coverage"] is not None
    ]
    summary = {
        "scope": "OUTER_HELD_SOURCE_RECORD_T_DIRECTION_PROXY_NOT_REAL_INDEPENDENT_K1_CORROBORATION",
        "variant": "E1_FIXED_ASK_SHARED_K1_RULES",
        "fine_target_parent_mapping": "FROZEN_R1_PARENTS_ONLY_NO_FITTED_RELATIONS_GRADE_THEMSELVES",
        "parent_relation_sha256": r1.digest(r1.PARENTS),
        "stages": stage_summary,
        "Q3_direction_corrections": {
            "identifiable_paired_records": len(comparable),
            "improved_preferred_direction_coverage": sum(
                b["preferred_direction_coverage"] > a["preferred_direction_coverage"]
                for a, b in comparable
            ),
            "worsened_preferred_direction_coverage": sum(
                b["preferred_direction_coverage"] < a["preferred_direction_coverage"]
                for a, b in comparable
            ),
            "unchanged": sum(
                b["preferred_direction_coverage"] == a["preferred_direction_coverage"]
                for a, b in comparable
            ),
        },
        "outside_preferred_scope_means": "HYPOTHETICAL_LOSS_IF_PRIORITY_WERE_A_HARD_FILTER;NO_ACTUAL_DELETION_WAS_PERFORMED",
        "actual_hard_pruning": 0,
        "current_A_direction_retention_is_contract_fidelity_not_independent_T_retention": True,
        "missing_fine_T_and_unknown_parent_masks_retained": True,
        "no_fit_or_selection": True,
    }
    save(dst / "k1_hidden_target_direction_diagnostics.private.json", rows)
    save(dst / "k1_hidden_target_direction_public_summary.private.json", summary)
    current = read(dst / "constraints_public_summary.private.json")
    current["K1_hidden_target_direction_diagnostic"] = summary
    save(dst / "constraints_public_summary.private.json", current)
    print(
        json.dumps(
            {
                "phase": "K1_HELD_DIRECTION_DIAGNOSTIC",
                "stages": stage_summary,
                "Q3": summary["Q3_direction_corrections"],
            }
        ),
        flush=True,
    )
    return summary


def seal_completed(
    owner_dir, contract_path, contract_sha, amendment_sha, full_contract_sha
):
    """Seal verified immutable parameters and all actual private result artifacts."""
    _contract_check(contract_path, contract_sha)
    owner, dst = Path(owner_dir), Path(owner_dir) / "revisions/r3"
    summary = read(dst / "constraints_public_summary.private.json")
    summary.pop("counterfactual_examples", None)
    receipt = read(dst / "full_development_fit_receipt.private.json")
    summary["full_development_research_artifact"] = {
        key: receipt[key]
        for key in [
            "model_owner_relative_path",
            "model_sha256",
            "selected_variant",
            "training_records",
            "training_groups",
            "exactly_one_logical_final_refit",
            "full_model_train_OOF_not_generalization",
            "reload_identical",
        ]
    }
    summary["full_development_contract_sha256"] = full_contract_sha
    summary["context_information_cost"] = {
        "questions": 2,
        "offered_options": 15,
        "separate_from_ordinary_sensory_cost": True,
    }
    summary["counterfactual_cases_private_sha256"] = sha(
        dst / "counterfactual_error_examples.private.json"
    )
    summary["runtime_audit_projection"] = {
        "version": runtime.AUDIT_VERSION,
        "changes_score_or_trigger_features": False,
        "explicit_types_statuses_and_one_shared_budget_candidate_group": True,
    }
    summary["historical17_regression"] = read(
        dst / "history_public_summary.private.json"
    )
    cli = read("/private/tmp/m2-r3-full-cli-parity.json")
    if cli["model_sha256"] != receipt["model_sha256"]:
        raise ValueError("FULL_CLI_PARITY_MODEL_HASH_MISMATCH")
    summary["full_CLI_reproducibility"] = cli
    save(dst / "constraints_cli_parity.private.json", cli)
    save(dst / "constraints_public_summary.private.json", summary)
    save("/private/tmp/m2-r3-constraints-public-summary.json", summary)
    paths = set((dst / "models").glob("R3*.json"))
    for folder, pattern in [
        ("oof", "*.private.json"),
        ("trajectories", "*.private.json"),
    ]:
        paths.update((dst / folder).glob(pattern))
    for name in [
        "constraint_isolation_audit.private.json",
        "constraints_reload_audit.private.json",
        "constraints_summary.private.json",
        "constraints_public_summary.private.json",
        "relation_results.private.json",
        "policy_results.private.json",
        "final_feedback_results.private.json",
        "counterfactual_Q3_results.private.json",
        "counterfactual_error_examples.private.json",
        "constraint_relation_trigger_registry.private.json",
        "full_development_fit_receipt.private.json",
        "first_relation_public_summary.private.json",
        "constraints_runtime_projection_audit.private.json",
        "history_results.private.json",
        "history_public_summary.private.json",
        "constraints_cli_parity.private.json",
        "k1_hidden_target_direction_diagnostics.private.json",
        "k1_hidden_target_direction_public_summary.private.json",
    ]:
        path = dst / name
        if not path.exists():
            raise ValueError("COMPLETED_R3_ARTIFACT_MISSING:" + name)
        paths.add(path)
    manifest = {
        "original_contract_sha256": contract_sha,
        "internal_feature_amendment_sha256": amendment_sha,
        "full_development_contract_sha256": full_contract_sha,
        "private_artifact_hashes": {
            str(path.relative_to(dst)): sha(path) for path in sorted(paths)
        },
        "code_fingerprints": scoring_code_fingerprints(),
        "audit_version": runtime.AUDIT_VERSION,
        "completed": True,
        "reproduction_policy": "VERIFY_AND_LOAD_NO_FIT_OR_RECOMPUTE",
    }
    save(dst / "constraints_completion_manifest.private.json", manifest)
    return verify_completed(owner_dir, contract_path, contract_sha, amendment_sha)


def verify_completed(owner_dir, contract_path, contract_sha, amendment_sha):
    """Read-only complete-run verification. No estimator or trajectory is invoked."""
    _contract_check(contract_path, contract_sha)
    dst = Path(owner_dir) / "revisions/r3"
    manifest = read(dst / "constraints_completion_manifest.private.json")
    if (
        not manifest["completed"]
        or manifest["original_contract_sha256"] != contract_sha
        or manifest["internal_feature_amendment_sha256"] != amendment_sha
    ):
        raise ValueError("COMPLETED_R3_CONTRACT_MISMATCH")
    if (
        sha(dst / "internal_feature_amendment.frozen.json") != amendment_sha
        or sha(dst / "full_development_contract.frozen.json")
        != manifest["full_development_contract_sha256"]
    ):
        raise ValueError("COMPLETED_AMENDMENT_OR_FULL_CONTRACT_CHANGED")
    for relative, expected in manifest["private_artifact_hashes"].items():
        if sha(dst / relative) != expected:
            raise ValueError("COMPLETED_PRIVATE_ARTIFACT_CHANGED:" + relative)
    if scoring_code_fingerprints() != manifest["code_fingerprints"]:
        raise ValueError(
            "COMPLETED_CODE_CHANGED_REQUIRES_EXPLICIT_NO_FIT_AUDIT_REFRESH"
        )
    return {
        "public_summary": read(dst / "constraints_public_summary.private.json"),
        "verification": {
            "private_artifacts_verified": len(manifest["private_artifact_hashes"]),
            "fit_calls": 0,
            "trajectory_recomputations": 0,
            "completion_manifest_sha256": sha(
                dst / "constraints_completion_manifest.private.json"
            ),
            "code_fingerprints_identical": True,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", action="store_true")
    parser.add_argument("--owner-dir")
    parser.add_argument("--contract")
    parser.add_argument("--expected-contract-sha256")
    parser.add_argument("--relations-only", action="store_true")
    parser.add_argument("--expected-amendment-sha256")
    parser.add_argument("--evaluate-existing", action="store_true")
    parser.add_argument("--fit-full", action="store_true")
    parser.add_argument("--seal-completed", action="store_true")
    parser.add_argument("--verify-completed", action="store_true")
    parser.add_argument("--audit-projection", action="store_true")
    parser.add_argument("--evaluate-history", action="store_true")
    parser.add_argument("--evaluate-hidden-directions", action="store_true")
    parser.add_argument("--expected-full-contract-sha256")
    parser.add_argument(
        "--summary-path", default="/private/tmp/m2-r3-constraints-summary.json"
    )
    args = parser.parse_args()
    if args.protocol:
        print(json.dumps(protocol(), sort_keys=True, indent=2))
    elif args.owner_dir and args.contract and args.expected_contract_sha256:
        with threadpool_limits(limits=1):
            if args.evaluate_hidden_directions:
                evaluate_hidden_directions(args.owner_dir)
            elif args.audit_projection:
                audit_runtime_projection(args.owner_dir)
            elif args.evaluate_history:
                evaluate_history(args.owner_dir)
            elif args.verify_completed:
                print(
                    json.dumps(
                        verify_completed(
                            args.owner_dir,
                            args.contract,
                            args.expected_contract_sha256,
                            args.expected_amendment_sha256,
                        )["verification"]
                    )
                )
            elif args.seal_completed:
                seal_completed(
                    args.owner_dir,
                    args.contract,
                    args.expected_contract_sha256,
                    args.expected_amendment_sha256,
                    args.expected_full_contract_sha256,
                )
            elif args.fit_full:
                fit_full_development(
                    args.owner_dir,
                    args.contract,
                    args.expected_contract_sha256,
                    args.expected_amendment_sha256,
                    args.expected_full_contract_sha256,
                )
            elif args.evaluate_existing:
                finish_evaluation(
                    args.owner_dir,
                    args.contract,
                    args.expected_contract_sha256,
                    args.expected_amendment_sha256,
                )
            else:
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
