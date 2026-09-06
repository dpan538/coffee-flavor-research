"""Three frozen R7 interventions on R6 acquisition/observation channels.

No scorer, semantic rule, coverage statistic or trigger is fitted here. Detailed
source spans, answers and candidate outputs are written only to private storage.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

import alignment_metrics_r3 as metric
import audit_revelation_r4 as audit
import flavor_conditioning_r4 as runtime
import flavor_m2_r1 as r1
import information_supervision_r5 as provider
import information_supervision_r6 as information
import run_supervision_r6 as previous
import semantic_mapping_r6 as semantic
import train_conditioning_r4 as conditioning
import train_supervision_r5 as evaluation

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r7"
VERSION = "m2-r7.frozen-channel-diagnostics.v1"
DIAGNOSTICS = (
    "D_COVERAGE_ONLY",
    "D_OBSERVATION_ONLY",
    "D_FIXED_EXPOSURE",
)


def protocol():
    return {
        "version": VERSION,
        "D_COVERAGE_ONLY": "Frozen fold TRAIN patched B coverage; base source A/B interpretation; unchanged natural I2_LIVE",
        "D_OBSERVATION_ONLY": "Frozen fold TRAIN base B coverage; patched source A/B interpretation; unchanged natural I2_LIVE",
        "D_FIXED_EXPOSURE": "Original same-fold C01 complete ordered questions/options; patched source answers; unchanged A0 updates; OFFLINE_INTERVENTION_NOT_DEPLOYABLE",
        "models": "Exactly R6 outer-fold frozen A0/R1 weights, generation vocabulary and resources; no R6 linear head",
        "cohort": "All 79 R6 development episodes / 77 coffee groups, including 20 empty-T records; no new confirmation",
        "evaluation": "Existing 56 fine ontology, frozen full T weights/masks and original hidden subset; full target denominator retains unavailable fine concepts",
        "ordinary_budgets": dict(information.BUDGETS),
        "context": "Exact R6 historical simulation context copied for parity, never treated as observed source C0/C1 or independent context-effect evidence",
        "fit_count": 0,
        "statistics_fit_count": 0,
        "detail_selection": "At most 12 changed C11-vs-C01 cases; round robin regression/improvement/tie/no-evaluable-T, each sorted by absolute gap difference then SHA256(record_id); all cases audited separately",
        "classification": "Source mapping/support error requires independent source/contract proof; changed questions support budget-allocation classification; T nonmention alone never establishes sensory disagreement",
        "posthoc_target_measurement_audit": "After all trajectories/scores, inspect independent raw T whole spans using already reviewed R6 rules; flag exact positive fine references missing from frozen T as FIXED_TARGET_MAPPING_LOSS without changing targets or scores; broad references remain outside fine task",
        "interpretation": "Finite channel interventions are not additive causal decomposition; source interpretation changes do not prove real user answer changes",
        "repair": "No automatic repair; maximum one separately preregistered source-supported local mechanism correction if justified",
        "publication": "Aggregate values and hashes only; identities, source spans, questions, answers and detailed predictions private",
    }


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o700)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    )
    temporary.chmod(0o600)
    os.replace(temporary, path)


def check_contract(expected):
    path = PUBLIC / "experiment_contract.json"
    if not expected or sha(path) != expected:
        raise ValueError("R7_FROZEN_CONTRACT_HASH_REQUIRED")
    contract = read(path)
    if (
        not set(DIAGNOSTICS) <= set(contract["mechanism_diagnostics"])
        or contract["mechanism_diagnostics"]["scorer_refits"] != 0
        or contract["fixed"]["ordinary_options"] != 19
        or contract["fixed"]["option_budgets"] != list(information.BUDGETS.values())
        or contract["fixed"]["related_multiplier"] != 2.0
    ):
        raise ValueError("R7_DIAGNOSTIC_CONTRACT_MISMATCH")
    for name, expected_hash in contract["preserved"].items():
        if sha(previous.OUT / name) != expected_hash:
            raise ValueError("R7_PRESERVED_R6_CHANGED:" + name)
    return contract


def load_frozen(owner):
    owner = Path(owner)
    previous.verify_matrix(owner)
    sealed = read(owner / "revisions/r6/completion_manifest.private.json")
    for field, root in (
        ("private_artifacts", owner / "revisions/r6"),
        ("code_sha256", ROOT),
        ("inherited_input_sha256", owner),
    ):
        for relative, expected in sealed[field].items():
            if sha(root / relative) != expected:
                raise ValueError("R7_INHERITED_R6_SEAL_CHANGED:" + relative)
    cases = read(owner / "revisions/r6/matrix_cases.private.json")
    resources = read(owner / "revisions/r6/matrix_input_resources.private.json")
    resources = {(r["expert_path"], r["mapping"]): r for r in resources}
    records, units = semantic.load_inputs(owner)
    records = {r["record_id"]: r for r in records}
    ids = {r["record_id"] for r in cases["C01"]}
    if (
        len(ids) != 79
        or ids != set(records)
        or len({r["group_id"] for r in records.values()}) != 77
    ):
        raise ValueError("R7_FULL_COHORT_NOT_PRESERVED")
    for name in ("C00", "C01", "C10", "C11"):
        if len(cases[name]) != len(ids) or {r["record_id"] for r in cases[name]} != ids:
            raise ValueError("R7_CELL_IDS_NOT_EXACT")
        for row in cases[name]:
            record = records[row["record_id"]]
            if (
                row["full_T"] != record["relevance_full"]
                or row["hidden_T"] != record["relevance_unexpressed"]
            ):
                raise ValueError("R7_FROZEN_TARGET_MISMATCH")
    return {"records": records, "units": units, "cases": cases, "resources": resources}


def question_signature(question):
    return {
        k: copy.deepcopy(question[k])
        for k in ("slot", "question_id", "axis", "shown_option_ids", "options")
    }


def run_trajectory(
    initial_observations,
    later_observations,
    context,
    bundle,
    coverage,
    fixed_questions=None,
):
    """Only observations and a context enter execution; no target argument."""
    state = information.initial_state(context, bundle)
    states, questions, failure = [], [], None
    if fixed_questions is not None:
        if [q["slot"] for q in fixed_questions] != list(information.BUDGETS):
            raise ValueError("R7_FIXED_EXPOSURE_REQUIRES_COMPLETE_C01_PATH")
        if [len(q["options"]) for q in fixed_questions] != list(
            information.BUDGETS.values()
        ):
            raise ValueError("R7_FIXED_EXPOSURE_BUDGET_CHANGED")
    for index, slot in enumerate(information.BUDGETS):
        try:
            if fixed_questions is None:
                prepared, plan = information.select(state, bundle, coverage, "I2_LIVE")
                question = plan["question"]
            else:
                original = copy.deepcopy(fixed_questions[index])
                base = r1.expose_question(
                    state["base_state"], slot, original, bundle["r1_expert"]
                )
                prepared = runtime.wrap_state(
                    base, bundle, trigger_policy="ALWAYS_ASK", previous=state
                )
                question = runtime.select_next_question(prepared, bundle)["question"]
                if question_signature(question) != question_signature(original):
                    raise ValueError("R7_FROZEN_QUESTION_OR_OPTIONS_CHANGED")
        except ValueError as exc:
            if not str(exc).startswith("NO_LEGAL_AXIS_AT_FROZEN_BUDGET"):
                raise
            failure = {"slot": slot, "reason": str(exc)}
            break
        if (
            question["slot"] != slot
            or len(question["shown_option_ids"]) != information.BUDGETS[slot]
        ):
            raise ValueError("R7_FROZEN_SLOT_OR_BUDGET_CHANGED")
        visible = (
            initial_observations
            if slot in {"Q0", "Q1"}
            else sorted(set(initial_observations) | set(later_observations))
        )
        answer = provider.source_answer(question, visible, bundle["r1_expert"])
        state = information.update(prepared, answer, bundle)
        states.append(copy.deepcopy(state))
        questions.append(copy.deepcopy(question))
    return {
        "state": state,
        "states": states,
        "questions": questions,
        "failure": failure,
    }


def result_row(original, mapped, trajectory, diagnostic, bundle):
    states = trajectory["states"]
    state = trajectory["state"]
    failure = trajectory["failure"]
    ranking = [] if failure else copy.deepcopy(state["candidate_scores"])
    questions = trajectory["questions"]
    initial_state = next(
        (s for s in states if len(s["base_state"]["answers_by_question"]) == 2), None
    )
    initial = provider.selected(initial_state) if initial_state else []
    selected = provider.selected(state)
    row = {
        "record_id": original["record_id"],
        "group_id": original["group_id"],
        "source_family": original["source_family"],
        "fold": original["fold"],
        "diagnostic": diagnostic,
        "cell": diagnostic,
        "failure": failure,
        "deployable_policy": diagnostic != "D_FIXED_EXPOSURE",
        "scope": "HISTORICAL_DEVELOPMENT_MECHANISM_DIAGNOSTIC_NOT_CONFIRMATION",
        "full_T": copy.deepcopy(original["full_T"]),
        "hidden_T": copy.deepcopy(original["hidden_T"]),
        "A": copy.deepcopy(original["A"]),
        "interpreted_A": mapped["A"],
        "interpreted_B": mapped["B"],
        "initial_selected": initial,
        "selected": {"ASK": selected},
        "ranking": ranking,
        "questions": questions,
        "state": state,
        "stage_states": states,
        "mapping_audit": mapped.get("mapping_input_trace", []),
        "evaluation_universe": list(evaluation.CANDIDATES),
        "frozen_A0_generation_universe": list(bundle["fixed_candidates"]),
        "context_scope": "EXACT_R6_HISTORICAL_SIMULATION_ASSIGNMENT_NOT_OBSERVED_SOURCE_METADATA",
        "costs": {
            "ordinary_questions": len(questions),
            "ordinary_options": sum(len(q["shown_option_ids"]) for q in questions),
            "planned_ordinary_questions": 5,
            "planned_ordinary_options": 19,
            "actual_final_exposure": 0,
            "human_time": None,
        },
    }
    if not failure and row["costs"]["ordinary_options"] != 19:
        raise ValueError("R7_DIAGNOSTIC_BUDGET_MISMATCH")
    row["metrics"] = metric.evaluate(ranking, row["full_T"], evaluation.CANDIDATES)
    row["hidden_metrics"] = metric.evaluate(
        ranking, row["hidden_T"], evaluation.CANDIDATES
    )
    return row


def ranked_ids(row):
    return [r["candidate_id"] if isinstance(r, dict) else r for r in row["ranking"]]


def selected_concepts(row):
    return set(row["selected"]["ASK"])


def channel_inputs(name, record, mapped, base_coverage, patched_coverage, questions):
    if name not in DIAGNOSTICS:
        raise ValueError("R7_ONLY_THREE_REGISTERED_DIAGNOSTICS")
    return (
        record if name == "D_COVERAGE_ONLY" else mapped,
        patched_coverage if name == "D_COVERAGE_ONLY" else base_coverage,
        questions if name == "D_FIXED_EXPOSURE" else None,
    )


def target_measurement_audit(
    record, target_units, source_trace, additional_selected=()
):
    """Post-outcome measurement check only; never called by an execution path."""
    identities = record["T_observation_unit_ids"]
    if set(identities) & {
        record["A_observation_unit_id"],
        record["B_observation_unit_id"],
    }:
        raise ValueError("R7_POSTHOC_T_INPUT_UNIT_OVERLAP")
    additions = {c for trace in source_trace for c in trace["added_concepts"]} | set(
        additional_selected
    )
    rules = {r["normalized_span"]: r for r in semantic.reviewed_rules()}
    spans, evidence = [], []
    for identity in identities:
        unit = target_units[identity]
        if unit["group_id"] != record["group_id"]:
            raise ValueError("R7_POSTHOC_T_COFFEE_IDENTITY_MISMATCH")
        for span in semantic.extract_spans(unit):
            spans.append(span)
            rule = rules.get(span["normalized_span"])
            if rule is None or not span["positive_mapping_allowed"]:
                continue
            for concept in set(rule["concepts"]) & additions:
                status = (
                    "ALREADY_IN_FIXED_TARGET"
                    if record["relevance_full"].get(concept, 0) > 0
                    else (
                        "FIXED_TARGET_MAPPING_LOSS"
                        if concept.startswith("sensory.")
                        else "BROAD_TARGET_SUPPORT_OUTSIDE_FINE_TASK"
                    )
                )
                evidence.append(
                    {
                        "concept": concept,
                        "status": status,
                        "span": span,
                        "rule_id": rule["rule_id"],
                        "rule_relation": rule["relation"],
                        "rule_basis": rule["basis"],
                    }
                )
    missing_fine = sorted(
        {e["concept"] for e in evidence if e["status"] == "FIXED_TARGET_MAPPING_LOSS"}
    )
    return {
        "scope": "POSTHOC_MEASUREMENT_AUDIT_ONLY_FIXED_T_UNCHANGED",
        "target_observation_unit_ids": identities,
        "original_T_spans": spans,
        "verified_rule_matches": evidence,
        "fine_concepts_explicit_in_raw_T_but_missing_fixed_T": missing_fine,
        "input_additions_without_verified_positive_T_span": sorted(
            additions - {e["concept"] for e in evidence}
        ),
        "absence_interpretation": "No verified match is not evidence of sensory absence or disagreement; unknown/compound/negative scopes retained",
        "target_mutated": False,
    }


def retention(row):
    selected = {c for c in selected_concepts(row) if c.startswith("sensory.")}
    ids = ranked_ids(row)
    available = selected & set(ids)
    missed = available - set(ids[:5])
    return {
        "explicit_fine_selected": sorted(selected),
        "explicit_outside_generation": sorted(selected - set(ids)),
        "explicit_available": sorted(available),
        "explicit_available_retained_main5": sorted(available & set(ids[:5])),
        "explicit_available_missing_main5": sorted(missed),
        "available_explicit_exceeds_main_capacity": len(available) > 5,
        "possible_priority_contract_violation": bool(missed)
        and len(available) <= 5
        and not row.get("failure"),
        "interpretation": "A missed explicit candidate is audited separately from generation limits and unavoidable >5 capacity; this flag alone does not establish a source or support bug",
    }


def exposure_structure(before, after):
    """Separate changed content from same-ballot axis/option presentation order."""
    left, right = before["questions"], after["questions"]

    def content(q):
        return q["axis"], tuple(sorted(q["shown_option_ids"]))

    sequence_left, sequence_right = [content(q) for q in left], [
        content(q) for q in right
    ]
    whole_changed = sorted(sequence_left) != sorted(sequence_right)
    sequence_changed = sequence_left != sequence_right
    presentation_changed = [question_signature(q) for q in left] != [
        question_signature(q) for q in right
    ]
    return {
        "whole_exposure_content_changed": whole_changed,
        "axis_sequence_only_changed": sequence_changed and not whole_changed,
        "option_order_only_changed": presentation_changed and not sequence_changed,
        "question_instance_changed": presentation_changed,
        "axis_changed_slots": [
            s
            for s, a, b in zip(information.BUDGETS, left, right)
            if a["axis"] != b["axis"]
        ],
        "option_set_changed_slots": [
            s
            for s, a, b in zip(information.BUDGETS, left, right)
            if set(a["shown_option_ids"]) != set(b["shown_option_ids"])
        ],
    }


def category(before, after, source_trace):
    qchanged = exposure_structure(before, after)["whole_exposure_content_changed"]
    additional = selected_concepts(after) - selected_concepts(before)
    not_corroborated = sorted(
        c
        for c in additional
        if c.startswith("sensory.") and after["full_T"].get(c, 0) == 0
    )
    if qchanged:
        label = "VALID_MAPPING_CHANGED_BUDGET_ALLOCATION"
        status = (
            "OBSERVED_WHOLE_EXPOSURE_CONTENT_CHANGE_NOT_EXCLUSIVE_CAUSAL_ATTRIBUTION"
        )
    else:
        label = "UNRESOLVED"
        status = "CANDIDATE_COMPETITION_OR_UNOBSERVED_MECHANISM_REQUIRES_EVIDENCE"
    return {
        "classification": label,
        "status": status,
        "new_specific_not_corroborated_by_T": not_corroborated,
        "class4_disagreement_established": False,
        "nonmention_reason": "Positive-only T not mentioning a concept does not establish sensory disagreement or mapping error",
        "source_mapping_error_established": False,
        "support_semantics_error_established": False,
        "source_rule_statuses": sorted(
            {s.get("status", "UNRESOLVED") for s in source_trace}
        ),
        "repair_authorized_by_this_automatic_audit": False,
    }


def candidate_changes(before, after):
    left = {r["candidate_id"]: r for r in before["ranking"]}
    right = {r["candidate_id"]: r for r in after["ranking"]}
    result = []
    for candidate in sorted(set(left) | set(right)):
        a, b = left.get(candidate), right.get(candidate)
        if a == b:
            continue
        result.append(
            {
                "candidate_id": candidate,
                "rank_before": a["rank"] if a else None,
                "rank_after": b["rank"] if b else None,
                "score_before": a["score"] if a else None,
                "score_after": b["score"] if b else None,
                "score_delta": b["score"] - a["score"] if a and b else None,
                "components_before": a.get("components") if a else None,
                "components_after": b.get("components") if b else None,
                "explicit_before": a.get("explicit") if a else None,
                "explicit_after": b.get("explicit") if b else None,
            }
        )
    return result


def contrast(before, after, source_trace):
    left, right = ranked_ids(before), ranked_ids(after)
    old, new = set(left[:5]), set(right[:5])
    targets = {c for c, value in after["full_T"].items() if value > 0}
    a, b = previous.evaluated(before), previous.evaluated(after)
    gap = b["raw_gap"] - a["raw_gap"] if a["raw_gap"] is not None else None
    direction = (
        "NO_EVALUABLE_T"
        if gap is None
        else "REGRESSION" if gap > 1e-12 else "IMPROVEMENT" if gap < -1e-12 else "TIE"
    )
    answer_before = before["state"]["base_state"]["answers_by_question"]
    answer_after = after["state"]["base_state"]["answers_by_question"]
    answer_changes = [
        {
            "slot": slot,
            "before": answer_before.get(slot),
            "after": answer_after.get(slot),
        }
        for slot in information.BUDGETS
        if answer_before.get(slot) != answer_after.get(slot)
    ]
    score_changes = candidate_changes(before, after)
    return {
        "diagnostic": after.get("diagnostic", after.get("cell")),
        "metrics_before": a,
        "metrics_after": b,
        "gap_delta": gap,
        "outcome": direction,
        "question_changed": [question_signature(q) for q in before["questions"]]
        != [question_signature(q) for q in after["questions"]],
        "exposure_structure": exposure_structure(before, after),
        "questions_before": before["questions"],
        "questions_after": after["questions"],
        "answer_changes": answer_changes,
        "selected_added": sorted(selected_concepts(after) - selected_concepts(before)),
        "selected_removed": sorted(
            selected_concepts(before) - selected_concepts(after)
        ),
        "canonical_selected_changed": selected_concepts(before)
        != selected_concepts(after),
        "rank_order_changed": left != right,
        "candidate_changes": score_changes,
        "main5_before": left[:5],
        "main5_after": right[:5],
        "fine_primary_panel_before": [c for c in left if c in evaluation.CANDIDATES][
            :5
        ],
        "fine_primary_panel_after": [c for c in right if c in evaluation.CANDIDATES][
            :5
        ],
        "entered_fine_primary_panel": sorted(
            set([c for c in right if c in evaluation.CANDIDATES][:5])
            - set([c for c in left if c in evaluation.CANDIDATES][:5])
        ),
        "displaced_fine_primary_panel": sorted(
            set([c for c in left if c in evaluation.CANDIDATES][:5])
            - set([c for c in right if c in evaluation.CANDIDATES][:5])
        ),
        "displaced_fine_primary_exact_T": sorted(
            (
                set([c for c in left if c in evaluation.CANDIDATES][:5])
                - set([c for c in right if c in evaluation.CANDIDATES][:5])
            )
            & targets
        ),
        "entered_main5": sorted(new - old),
        "displaced_main5": sorted(old - new),
        "entered_exact_T": sorted((new - old) & targets),
        "displaced_exact_T": sorted((old - new) & targets),
        "full_T": copy.deepcopy(after["full_T"]),
        "explicit_retention_before": retention(before),
        "explicit_retention_after": retention(after),
        "classification": category(before, after, source_trace),
        "changed": bool(answer_changes or score_changes or left != right),
    }


def choose_details(audits, limit=12):
    buckets = defaultdict(list)
    for row in audits:
        comparison = row["comparisons"]["C11"]
        if row["changed"]:
            buckets[comparison["outcome"]].append(row)
    for bucket in buckets.values():
        bucket.sort(
            key=lambda r: (
                -abs(r["comparisons"]["C11"]["gap_delta"] or 0),
                hashlib.sha256(r["record_id"].encode()).hexdigest(),
            )
        )
    chosen = []
    while len(chosen) < limit:
        added = False
        for name in ("REGRESSION", "IMPROVEMENT", "TIE", "NO_EVALUABLE_T"):
            if buckets[name] and len(chosen) < limit:
                chosen.append(buckets[name].pop(0))
                added = True
        if not added:
            break
    return chosen


def aggregate_results(rows):
    metrics = [previous.evaluated(r) for r in rows]
    value = evaluation.aggregate(metrics)
    value.update(
        failures=sum(bool(r.get("failure")) for r in rows),
        empty_T_records=sum(not r["full_T"] for r in rows),
        actual_final_exposure=0,
        human_time=None,
        question_costs=sorted({r["costs"]["ordinary_questions"] for r in rows}),
        option_costs=sorted({r["costs"]["ordinary_options"] for r in rows}),
        generation_vocabulary_sizes=sorted(
            {len(r["frozen_A0_generation_universe"]) for r in rows}
        ),
    )
    return value


def run_diagnostics(owner, contract_sha256):
    owner = Path(owner)
    check_contract(contract_sha256)
    dst = owner / "revisions/r7"
    receipt_path = dst / "mechanism_receipt.private.json"
    if receipt_path.exists():
        raise ValueError("R7_DIAGNOSTICS_ALREADY_SEALED_USE_REPLAY")
    started = previous.io.now()
    frozen = load_frozen(owner)
    cases = {
        name: {r["record_id"]: r for r in rows}
        for name, rows in frozen["cases"].items()
    }
    output = {name: [] for name in DIAGNOSTICS}
    audits, parity = [], []
    for fold in range(3):
        relative = f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{fold}.model.json"
        base = frozen["resources"][(relative, "MAP_BASE")]
        patched = frozen["resources"][(relative, "MAP_PATCH")]
        if (
            sha(owner / relative) != base["expert_sha256"]
            or base["expert_sha256"] != patched["expert_sha256"]
        ):
            raise ValueError("R7_OUTER_SCORER_HASH_MISMATCH")
        bundle = conditioning.model_bundle(read(owner / relative))
        held = {r["group_id"] for r in cases["C01"].values() if r["fold"] == fold}
        if set(base["training_groups"]) != set(
            patched["training_groups"]
        ) or held & set(base["training_groups"]):
            raise ValueError("R7_RESOURCE_TRAIN_HELD_LEAKAGE")
        semantic.check_patch(patched["patch"])
        if held & set(patched["patch"]["training_groups"]):
            raise ValueError("R7_PATCH_TRAIN_HELD_LEAKAGE")
        coverage_changes = [
            {
                "concept": c,
                "base": base["coverage"].get(c, 0),
                "patched": patched["coverage"].get(c, 0),
                "delta": patched["coverage"].get(c, 0) - base["coverage"].get(c, 0),
            }
            for c in sorted(set(base["coverage"]) | set(patched["coverage"]))
            if base["coverage"].get(c, 0) != patched["coverage"].get(c, 0)
        ]
        for identity in sorted(cases["C01"]):
            original = cases["C01"][identity]
            if original["fold"] != fold:
                continue
            record = frozen["records"][identity]
            mapped = semantic.apply_inputs(record, frozen["units"], patched["patch"])
            context = copy.deepcopy(original["state"]["base_state"]["context"])
            if original["frozen_A0_generation_universe"] != bundle["fixed_candidates"]:
                raise ValueError("R7_GENERATION_UNIVERSE_CHANGED")
            # Historical trace parity uses the actual original whole exposure,
            # without selecting a fourth new diagnostic policy.
            replayed = run_trajectory(
                record["A"],
                record["B"],
                context,
                bundle,
                base["coverage"],
                original["questions"],
            )
            if (
                replayed["state"]["candidate_scores"] != original["ranking"]
                or replayed["questions"] != original["questions"]
            ):
                raise ValueError("R7_C01_FIXED_REPLAY_NOT_EXACT")
            parity.append(identity)
            local = {}
            for name in DIAGNOSTICS:
                observations, coverage, questions = channel_inputs(
                    name,
                    record,
                    mapped,
                    base["coverage"],
                    patched["coverage"],
                    original["questions"],
                )
                trajectory = run_trajectory(
                    observations["A"],
                    observations["B"],
                    context,
                    bundle,
                    coverage,
                    questions,
                )
                row = result_row(original, observations, trajectory, name, bundle)
                output[name].append(row)
                local[name] = row
            source_trace = mapped["mapping_input_trace"]
            comparisons = {
                name: contrast(original, row, source_trace)
                for name, row in {"C11": cases["C11"][identity], **local}.items()
            }
            audits.append(
                {
                    "record_id": identity,
                    "group_id": record["group_id"],
                    "fold": fold,
                    "source_interpretation": source_trace,
                    "source_A_added": sorted(set(mapped["A"]) - set(record["A"])),
                    "source_B_added": sorted(set(mapped["B"]) - set(record["B"])),
                    "coverage_changes": coverage_changes,
                    "comparisons": comparisons,
                    "changed": any(c["changed"] for c in comparisons.values())
                    or mapped["A"] != record["A"]
                    or mapped["B"] != record["B"],
                }
            )
        print(
            json.dumps(
                {
                    "checkpoint": "R7_DIAGNOSTIC_OUTER_COMPLETE",
                    "fold": fold,
                    "records": len(parity),
                    "fit_count": 0,
                }
            ),
            flush=True,
        )
    # Raw T text is loaded for explanation only after every execution and score
    # is complete. It cannot flow back into any question/answer/statistics path.
    parsed = read(owner / "revisions/r5/zenodo_source_parse.private.json")
    target_units = {u["observation_unit_id"]: u for u in parsed["observation_units"]}
    for row in audits:
        row["target_measurement_audit"] = target_measurement_audit(
            frozen["records"][row["record_id"]],
            target_units,
            row["source_interpretation"],
        )
    for rows in output.values():
        rows.sort(key=lambda r: r["record_id"])
    baselines = {name: list(cases[name].values()) for name in ("C00", "C01", "C11")}
    metrics = {
        name: aggregate_results(rows) for name, rows in {**baselines, **output}.items()
    }
    paired = {
        name
        + "-C01": evaluation.paired(
            [previous.evaluated(r) for r in baselines["C01"]],
            [previous.evaluated(r) for r in rows],
        )
        for name, rows in {"C11": baselines["C11"], **output}.items()
    }
    detail = choose_details(audits)
    counts = {}
    for name in ("C11", *DIAGNOSTICS):
        values = [r["comparisons"][name] for r in audits]
        counts[name] = {
            "changed_records": sum(v["changed"] for v in values),
            "question_changed_records": sum(v["question_changed"] for v in values),
            "answer_changed_records": sum(bool(v["answer_changes"]) for v in values),
            "rank_changed_records": sum(v["rank_order_changed"] for v in values),
            "main5_set_changed_records": sum(
                bool(v["entered_main5"] or v["displaced_main5"]) for v in values
            ),
            "outcome_counts_all_records": dict(Counter(v["outcome"] for v in values)),
            "classifications": dict(
                Counter(v["classification"]["classification"] for v in values)
            ),
            "possible_priority_contract_flags": sum(
                v["explicit_retention_after"]["possible_priority_contract_violation"]
                for v in values
            ),
            "additional_specific_noncorroboration_records": sum(
                bool(v["classification"]["new_specific_not_corroborated_by_T"])
                for v in values
            ),
        }
    summary = {
        "version": VERSION,
        "protocol": protocol(),
        "contract_sha256": contract_sha256,
        "fit_count": 0,
        "statistics_fit_count": 0,
        "historical_C01_exact_replay_records": len(parity),
        "metrics": metrics,
        "paired_contrasts": paired,
        "channel_counts": counts,
        "all_records_audited": len(audits),
        "changed_records_any_channel": sum(a["changed"] for a in audits),
        "detailed_examples": len(detail),
        "detail_outcome_counts": dict(
            Counter(r["comparisons"]["C11"]["outcome"] for r in detail)
        ),
        "posthoc_target_measurement_audit": {
            "records_with_verified_fixed_target_mapping_loss": sum(
                bool(
                    r["target_measurement_audit"][
                        "fine_concepts_explicit_in_raw_T_but_missing_fixed_T"
                    ]
                )
                for r in audits
            ),
            "record_concept_mapping_losses": sum(
                len(
                    r["target_measurement_audit"][
                        "fine_concepts_explicit_in_raw_T_but_missing_fixed_T"
                    ]
                )
                for r in audits
            ),
            "target_mutations": 0,
            "scope": "Raw independent T span audit after outcomes; fixed-target comparison unchanged, not evidence of interpersonal disagreement",
        },
        "repair_status": "NO_SOURCE_SUPPORTED_ERROR_ESTABLISHED_BY_AUTOMATIC_AUDIT; REVIEW_PRIVATE_EVIDENCE_BEFORE_PROPOSING_ANY_REPAIR",
        "negative_control_scope": "D_FIXED_EXPOSURE is fixed-exposure mechanism evidence, not a deployable acquisition result",
        "context_scope": protocol()["context"],
        "default": "B2_UNCHANGED_FOUNDATION_CHECK_OFF",
        "new_confirmation": "NOT_PART_OF_THIS_HISTORICAL_DIAGNOSTIC",
    }
    save(dst / "mechanism_trajectories.private.json", output)
    save(dst / "mechanism_all_case_audit.private.json", audits)
    save(dst / "mechanism_detailed_examples.private.json", detail)
    summary["private_evidence_hashes"] = {
        name: sha(dst / name)
        for name in (
            "mechanism_trajectories.private.json",
            "mechanism_all_case_audit.private.json",
            "mechanism_detailed_examples.private.json",
        )
    }
    save(dst / "mechanism_summary.private.json", summary)
    receipt = {
        "started_utc": started,
        "completed_utc": previous.io.now(),
        "contract_sha256": contract_sha256,
        "protocol_sha256": r1.digest(protocol()),
        "fit_count": 0,
        "r6_completion_manifest_sha256": sha(
            owner / "revisions/r6/completion_manifest.private.json"
        ),
        "code_sha256": sha(__file__),
        "artifacts": {
            name: sha(dst / name)
            for name in (
                *summary["private_evidence_hashes"],
                "mechanism_summary.private.json",
            )
        },
    }
    save(receipt_path, receipt)
    return summary


def refine_analysis(owner, contract_sha256, execution_code_snapshot):
    """Add finer reporting over already sealed outputs; never execute a policy."""
    owner = Path(owner)
    check_contract(contract_sha256)
    dst = owner / "revisions/r7"
    receipt = read(dst / "mechanism_receipt.private.json")
    if sha(execution_code_snapshot) != receipt["code_sha256"]:
        raise ValueError("R7_EXECUTION_SOURCE_SNAPSHOT_MISMATCH")
    if (dst / "mechanism_analysis_receipt.private.json").exists():
        raise ValueError("R7_REFINED_ANALYSIS_ALREADY_SEALED")
    for name, expected in receipt["artifacts"].items():
        if sha(dst / name) != expected:
            raise ValueError("R7_PRE_REFINEMENT_ARTIFACT_CHANGED:" + name)
    frozen = load_frozen(owner)
    output = read(dst / "mechanism_trajectories.private.json")
    old_audits = read(dst / "mechanism_all_case_audit.private.json")
    old_summary = read(dst / "mechanism_summary.private.json")
    cases = {
        name: {r["record_id"]: r for r in rows}
        for name, rows in frozen["cases"].items()
    }
    output = {name: {r["record_id"]: r for r in rows} for name, rows in output.items()}
    parsed = read(owner / "revisions/r5/zenodo_source_parse.private.json")
    units = {u["observation_unit_id"]: u for u in parsed["observation_units"]}
    audits = []
    for original in old_audits:
        row = copy.deepcopy(original)
        identity = row["record_id"]
        source_trace = row["source_interpretation"]
        row["comparisons"] = {
            name: contrast(cases["C01"][identity], value, source_trace)
            for name, value in {
                "C11": cases["C11"][identity],
                **{name: values[identity] for name, values in output.items()},
            }.items()
        }
        record = frozen["records"][identity]
        additions = {
            c
            for comparison in row["comparisons"].values()
            for c in comparison["selected_added"]
        }
        row["target_measurement_audit"] = target_measurement_audit(
            record, units, source_trace, additions
        )
        row["original_AB_spans"] = [
            {
                "role": role,
                "baseline_unit_concepts": units[record[role + "_observation_unit_id"]][
                    "strict_D0_concepts"
                ],
                **span,
            }
            for role in ("A", "B")
            for span in semantic.extract_spans(
                units[record[role + "_observation_unit_id"]]
            )
        ]
        audits.append(row)
    summary = copy.deepcopy(old_summary)
    for name, counts in summary["channel_counts"].items():
        values = [r["comparisons"][name] for r in audits]
        counts["question_instance_changed_records"] = counts.pop(
            "question_changed_records"
        )
        counts["answer_payload_changed_records"] = counts.pop("answer_changed_records")
        counts["whole_exposure_content_changed_records"] = sum(
            v["exposure_structure"]["whole_exposure_content_changed"] for v in values
        )
        counts["axis_sequence_only_changed_records"] = sum(
            v["exposure_structure"]["axis_sequence_only_changed"] for v in values
        )
        counts["option_order_only_changed_records"] = sum(
            v["exposure_structure"]["option_order_only_changed"] for v in values
        )
        counts["canonical_selected_changed_records"] = sum(
            v["canonical_selected_changed"] for v in values
        )
        counts["classifications"] = dict(
            Counter(v["classification"]["classification"] for v in values)
        )
        counts["fine_primary_panel_set_changed_records"] = sum(
            bool(v["entered_fine_primary_panel"] or v["displaced_fine_primary_panel"])
            for v in values
        )
        counts["displaced_fine_primary_exact_T_records"] = sum(
            bool(v["displaced_fine_primary_exact_T"]) for v in values
        )
    summary["posthoc_target_measurement_audit"].update(
        records_with_verified_fixed_target_mapping_loss=sum(
            bool(
                r["target_measurement_audit"][
                    "fine_concepts_explicit_in_raw_T_but_missing_fixed_T"
                ]
            )
            for r in audits
        ),
        record_concept_mapping_losses=sum(
            len(
                r["target_measurement_audit"][
                    "fine_concepts_explicit_in_raw_T_but_missing_fixed_T"
                ]
            )
            for r in audits
        ),
        evaluated_concepts="All added source interpretation concepts plus newly actually selected concepts across C11 and the three existing interventions; frozen reviewed whole-span rules only",
    )
    detail = choose_details(audits)
    summary["analysis_refinement"] = {
        "scope": "REPORTING_ONLY_FROM_SEALED_TRAJECTORIES_AND_FIXED_TARGETS",
        "reason": "Distinguish whole exposure content, axis sequence and option presentation order; canonical selected evidence versus answer JSON changes; inspect original A/B and T spans; retain actual main5 and the separate fine-primary panel",
        "additional_policy_runs": 0,
        "additional_scorer_fits": 0,
        "all_original_metrics_unchanged": summary["metrics"] == old_summary["metrics"],
        "original_execution_code_sha256": receipt["code_sha256"],
    }
    summary["repair_status"] = (
        "NO_SOURCE_SUPPORTED_INPUT_MAPPING_OR_SUPPORT_CONTRACT_ERROR_FOUND; CORRECT_EXPLICIT_EVIDENCE_RETAINED; NO_REPAIR_CANDIDATE"
    )
    summary["qualitative_mechanism"] = [
        "The coverage channel changes which concepts fit the fixed option budget; its nonzero aggregate loss is concentrated in one held development episode, not a broad population result.",
        "New correctly interpreted specific evidence can enter the five-fine evaluation panel and displace an inferred target. No available explicitly selected fine candidate was lost from actual main5.",
        "Fixed-exposure answer interpretation has a smaller aggregate change than the coverage intervention; the interventions are not an additive causal decomposition.",
        "Independent T nonmention is unresolved noncorroboration, not sensory absence. Raw T whole spans were checked without changing fixed targets or rescoring them.",
    ]
    save(dst / "mechanism_refined_case_audit.private.json", audits)
    save(dst / "mechanism_refined_detailed_examples.private.json", detail)
    snapshot = dst / "mechanism_execution_v1.private.py"
    snapshot.write_text(Path(execution_code_snapshot).read_text())
    snapshot.chmod(0o600)
    summary["private_evidence_hashes"] = {
        name: sha(dst / name)
        for name in (
            "mechanism_trajectories.private.json",
            "mechanism_refined_case_audit.private.json",
            "mechanism_refined_detailed_examples.private.json",
        )
    }
    save(dst / "mechanism_refined_summary.private.json", summary)
    save(
        dst / "mechanism_analysis_receipt.private.json",
        {
            "completed_utc": previous.io.now(),
            "contract_sha256": contract_sha256,
            "execution_receipt_sha256": sha(dst / "mechanism_receipt.private.json"),
            "execution_code_sha256": sha(snapshot),
            "analysis_code_sha256": sha(__file__),
            "artifacts": {
                name: sha(dst / name)
                for name in (
                    "mechanism_refined_case_audit.private.json",
                    "mechanism_refined_detailed_examples.private.json",
                    "mechanism_refined_summary.private.json",
                )
            },
            "scope": summary["analysis_refinement"],
        },
    )
    return summary


def replay(owner, contract_sha256):
    owner = Path(owner)
    check_contract(contract_sha256)
    dst = owner / "revisions/r7"
    receipt = read(dst / "mechanism_receipt.private.json")
    refined_receipt = dst / "mechanism_analysis_receipt.private.json"
    expected_execution_code = sha(__file__)
    if refined_receipt.exists():
        refined = read(refined_receipt)
        if refined["analysis_code_sha256"] != sha(__file__) or refined[
            "execution_receipt_sha256"
        ] != sha(dst / "mechanism_receipt.private.json"):
            raise ValueError("R7_REFINED_ANALYSIS_CODE_OR_RECEIPT_CHANGED")
        expected_execution_code = sha(dst / "mechanism_execution_v1.private.py")
        for name, expected in refined["artifacts"].items():
            if sha(dst / name) != expected:
                raise ValueError("R7_REFINED_ANALYSIS_ARTIFACT_CHANGED:" + name)
    if (
        receipt["contract_sha256"] != contract_sha256
        or receipt["protocol_sha256"] != r1.digest(protocol())
        or receipt["code_sha256"] != expected_execution_code
    ):
        raise ValueError("R7_MECHANISM_IMPLEMENTATION_OR_CONTRACT_CHANGED")
    if receipt["r6_completion_manifest_sha256"] != sha(
        owner / "revisions/r6/completion_manifest.private.json"
    ):
        raise ValueError("R7_INHERITED_COMPLETION_CHANGED")
    load_frozen(owner)
    for name, expected in receipt["artifacts"].items():
        if sha(dst / name) != expected:
            raise ValueError("R7_MECHANISM_ARTIFACT_CHANGED:" + name)
    rows = read(dst / "mechanism_trajectories.private.json")
    summary = read(dst / "mechanism_summary.private.json")
    if (
        refined_receipt.exists()
        and read(dst / "mechanism_refined_summary.private.json")["metrics"]
        != summary["metrics"]
    ):
        raise ValueError("R7_REPORTING_REFINEMENT_CHANGED_SCORES")
    for name, values in rows.items():
        if aggregate_results(values) != summary["metrics"][name]:
            raise ValueError("R7_MECHANISM_METRICS_CHANGED")
    return {
        "status": "PASS",
        "diagnostic_records": sum(len(v) for v in rows.values()),
        "fit_count": 0,
        "scope": "SEALED_ARTIFACT_AND_METRIC_REPLAY; initial execution receipt records real trajectories",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("run", "replay", "refine-analysis"))
    parser.add_argument("--owner-dir", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--execution-code-snapshot", type=Path)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.phase == "run":
            value = run_diagnostics(args.owner_dir, args.contract_sha256)
        elif args.phase == "refine-analysis":
            value = refine_analysis(
                args.owner_dir, args.contract_sha256, args.execution_code_snapshot
            )
        else:
            value = replay(args.owner_dir, args.contract_sha256)
    print(json.dumps(value, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
