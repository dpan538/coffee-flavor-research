"""R6 thin observable-only acquisition over the frozen R4/R1 state machine."""

from __future__ import annotations
import copy
from pathlib import Path
import json
import audit_revelation_r4 as audit
import alignment_metrics_r3 as metric
import flavor_m2_r1 as r1
import flavor_conditioning_r4 as runtime
import information_supervision_r5 as previous
from r6_mapping_i2_helpers import (
    Option,
    Question,
    TrainingB,
    choose_i2_live,
    fit_grouped_coverage,
)

VERSION = "m2-r6.observable-acquisition.v1"
BUDGETS = {"Q0": 4, "Q1": 4, "Q2": 4, "Q3": 4, "Q4": 3}


def protocol():
    return {
        "version": VERSION,
        "budgets": BUDGETS,
        "path": ["Q0", "Q1", "Q2", "Q3", "Q4"],
        "selector_scope": "State Q0/Q1 actual selected canonical concepts and their registered parents; used axes; isolated TRAIN B coverage; no source record, raw A/B or T",
        "POLICY_BASE": "Original R5 fixed selection with original option order truncated to predeclared slot budgets; short legal question is capacity failure, not padded or repaired",
        "I2_LIVE": "Frozen helper coverage score; related multiplier2; no target tuning",
        "failure": "Retain record, fixed target and universe; missing output evaluated as failure for nonempty T; report capacity and common all-cell success scope separately",
        "coverage": "Equal coffee group, sample, then observation; caller must exclude inner held and outer held groups",
        "old_I2": "Historical diagnostic only; full source A direction support is not live information",
    }


def attribute_id(value):
    return value if value.startswith("attribute.") else "attribute." + value


def initial_concepts(state):
    answers = state["base_state"]["answers_by_question"]
    if not {"Q0", "Q1"} <= answers.keys():
        raise ValueError("Q0_Q1_REQUIRED")
    return frozenset(
        c for slot in ("Q0", "Q1") for c in audit.canonical_selection(answers[slot])
    )


def directions(concepts):
    return sorted(
        {attribute_id(a) for c in concepts for a in r1.PARENTS.get(c, [])}
        | {c for c in concepts if c.startswith("attribute.")}
    )


def _select_with_observed(state, expert, train_coverage, observed, option_budget):
    native = expert["question_bank"]["correction"]
    questions = tuple(
        Question(
            q["axis"],
            tuple(
                Option(
                    o["id"],
                    o["id"],
                    (
                        frozenset({attribute_id(o["attribute"])})
                        if o.get("attribute")
                        else frozenset()
                    ),
                )
                for o in q["options"]
            ),
        )
        for q in native
    )
    chosen = choose_i2_live(
        questions,
        initial_observed_concepts=frozenset(observed),
        used_axes=frozenset(
            a["axis"] for a in state["base_state"]["answers_by_question"].values()
        ),
        train_coverage=train_coverage,
        fixed_parents={
            c: frozenset(attribute_id(a) for a in attrs)
            for c, attrs in r1.PARENTS.items()
        },
        option_budget=option_budget,
        related_multiplier=2.0,
    )
    out = copy.deepcopy(next(q for q in native if q["axis"] == chosen.axis))
    opts = {o["id"]: o for o in out["options"]}
    out["options"] = [opts[o.option_id] for o in chosen.options]
    return out


def select_r6_question(state, expert, train_coverage, option_budget=4):
    """Live selector boundary intentionally has no source-record parameter."""
    return _select_with_observed(
        state, expert, train_coverage, initial_concepts(state), option_budget
    )


def coverage_for(records, excluded_groups):
    rows = [
        TrainingB(
            r["B_observation_unit_id"],
            r["group_id"],
            str(r.get("sample_id", r["record_id"])),
            frozenset(r["B"]),
        )
        for r in records
    ]
    return fit_grouped_coverage(rows, evaluation_groups=frozenset(excluded_groups))


def initial_state(context, bundle):
    return runtime.initial_state(context, bundle, trigger_policy="ALWAYS_ASK")


def select(state, bundle, train_coverage, policy):
    if policy not in {"POLICY_BASE", "I2_LIVE"}:
        raise ValueError("R6_POLICY_REQUIRED")
    plan = runtime.select_next_question(state, bundle)
    if plan["action"] != "ASK":
        return copy.deepcopy(state), plan
    slot = plan["question"]["slot"]
    if slot not in BUDGETS:
        raise ValueError("R6_FIXED_Q4_ENDPOINT_REQUIRED")
    budget = BUDGETS[slot]
    question = (
        select_r6_question(state, bundle["r1_expert"], train_coverage, budget)
        if policy == "I2_LIVE" and slot in {"Q2", "Q3", "Q4"}
        else copy.deepcopy(plan["question"])
    )
    if len(question["options"]) < budget:
        raise ValueError("NO_LEGAL_AXIS_AT_FROZEN_BUDGET:" + slot)
    question["options"] = question["options"][:budget]
    base = r1.expose_question(state["base_state"], slot, question, bundle["r1_expert"])
    prepared = runtime.wrap_state(
        base, bundle, trigger_policy="ALWAYS_ASK", previous=state
    )
    return prepared, runtime.select_next_question(prepared, bundle)


def update(state, answer, bundle):
    slot = answer.get("slot")
    if slot not in BUDGETS or len(answer.get("shown_option_ids", [])) != BUDGETS[slot]:
        raise ValueError("R6_PREDECLARED_SLOT_OPTION_BUDGET_REQUIRED")
    return runtime.update_state(state, answer, bundle)


def generate_case(record, bundle, coverage, policy, fold=None):
    """Offline provider alone sees A/B; target is read only after acquisition."""
    if record["group_id"] in previous.expert_training_groups(bundle["r1_expert"]):
        raise ValueError("SCORER_SAW_COFFEE")
    context = record.get("context") or {"c0": r1.C0[0], "c1": "medium"}
    state = initial_state(context, bundle)
    by_slot = {}
    questions = []
    failure = None
    old_diff = []
    for slot in BUDGETS:
        try:
            prepared, plan = select(state, bundle, coverage, policy)
        except ValueError as exc:
            if not str(exc).startswith("NO_LEGAL_AXIS_AT_FROZEN_BUDGET"):
                raise
            failure = {"slot": slot, "reason": str(exc)}
            break
        question = plan["question"]
        if question["slot"] != slot:
            raise ValueError("FIXED_SLOT_MISMATCH")
        if policy == "I2_LIVE" and slot in {"Q2", "Q3", "Q4"}:
            try:
                old = _select_with_observed(
                    state, bundle["r1_expert"], coverage, record["A"], BUDGETS[slot]
                )
                old_diff.append(
                    {
                        "slot": slot,
                        "different_axis": old["axis"] != question["axis"],
                        "different_options": [o["id"] for o in old["options"]]
                        != question["shown_option_ids"],
                        "scope": "Same live state local old full-A selector diagnostic; not full historical old-I2 trajectory",
                    }
                )
            except ValueError as exc:
                old_diff.append({"slot": slot, "old_capacity_failure": str(exc)})
        visible = (
            record["A"]
            if slot in {"Q0", "Q1"}
            else sorted(set(record["A"]) | set(record["B"]))
        )
        answer = previous.source_answer(question, visible, bundle["r1_expert"])
        state = update(prepared, answer, bundle)
        by_slot[slot] = copy.deepcopy(state)
        questions.append(question)
    if not ({"relevance_full", "relevance"} & record.keys()) or not (
        {"relevance_unexpressed", "hidden_relevance"} & record.keys()
    ):
        raise ValueError(
            "FIXED_FULL_AND_HIDDEN_TARGETS_REQUIRED_NO_RECOMPUTATION_FROM_PATCHED_A"
        )
    full = copy.deepcopy(record.get("relevance_full", record.get("relevance")))
    hidden = copy.deepcopy(
        record.get("relevance_unexpressed", record.get("hidden_relevance"))
    )
    ranking = [] if failure else state["candidate_scores"]
    selected_initial = previous.selected(by_slot["Q1"]) if "Q1" in by_slot else []
    selected_end = previous.selected(state)
    costs = {
        "ordinary_questions": len(questions),
        "ordinary_options": sum(len(q["shown_option_ids"]) for q in questions),
        "planned_ordinary_questions": 5,
        "planned_ordinary_options": sum(BUDGETS.values()),
        "options_by_slot": {q["slot"]: len(q["shown_option_ids"]) for q in questions},
        "proposed_final_candidate_count": (
            0
            if failure
            else len(
                runtime.finalize_result(state, bundle)["exposure"]["candidate_ids"]
            )
        ),
        "actual_final_exposure": 0,
        "human_time": None,
    }
    fullmetric = metric.evaluate(ranking, full, bundle["fixed_candidates"])
    hiddenmetric = metric.evaluate(ranking, hidden, bundle["fixed_candidates"])
    novelty = (
        previous.audit.exposure_novelty(
            record,
            list(state["base_state"]["answers_by_question"].values()),
            previous.source_answer,
            bundle["r1_expert"],
        )
        if "Q1" in by_slot
        else None
    )
    targetdirs = set(directions(full))
    preddirs = set(directions([r["candidate_id"] for r in ranking[:5]]))
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "source_family": record.get("source_family", "zenodo"),
        "fold": fold,
        "full_T": full,
        "hidden_T": hidden,
        "A": record["A"],
        "B": record["B"],
        "relevance": full,
        "hidden_relevance": hidden,
        "policy": policy,
        "status": "CAPACITY_FAILURE" if failure else "COMPLETE",
        "failure": failure,
        "selected": {
            "I0": selected_initial,
            "Q2": previous.selected(by_slot["Q2"]) if "Q2" in by_slot else [],
            "I1": selected_end,
            "ASK": selected_end,
            policy: selected_end,
        },
        "initial_selected": selected_initial,
        "endpoint_selected": selected_end,
        "ranking": ranking,
        "metrics": fullmetric,
        "hidden_metrics": hiddenmetric,
        "target_direction_coverage": (
            len(targetdirs & preddirs) / len(targetdirs) if targetdirs else None
        ),
        "costs": costs,
        "novelty": novelty,
        "full_A_direction_not_observed": sorted(
            set(directions(record["A"])) - set(directions(selected_initial))
        ),
        "old_full_A_selector_local_differences": old_diff,
        "questions": questions,
        "state": state,
    }


def audit_banks(owner):
    """Read existing banks only; no outcome-dependent budget selection."""
    owner = Path(owner)
    paths = (
        list((owner / "revisions/r1/cv").glob("M2_R1_FINAL_FIXED_fold*.model.json"))
        + list(
            (owner / "revisions/r2/models").glob(
                "R2_R1_EXPERT_outer*_inner*.model.json"
            )
        )
        + list(
            (owner / "revisions/r3/models").glob(
                "R3_R1_EXPERT_outer*_inner*_deeper*_P1_INTERNAL.model.json"
            )
        )
    )
    rows = []
    for path in sorted(paths):
        expert = json.loads(path.read_text())
        state = r1.initial_state({"c0": r1.C0[0], "c1": "medium"}, expert)
        widths = {
            k: len(expert["question_bank"][k]["options"])
            for k in ["initial_0", "initial_1"]
        }
        rows.append(
            {
                "model": path.name,
                "initial_widths": widths,
                "initial_valid": all(v >= 4 for v in widths.values()),
                "correction_axes_at_least4": sum(
                    len(q["options"]) >= 4
                    for q in expert["question_bank"]["correction"]
                ),
                "correction_axes_at_least3": sum(
                    len(q["options"]) >= 3
                    for q in expert["question_bank"]["correction"]
                ),
            }
        )
    return rows


def old_i2_diagnostic(record, bundle, coverage):
    """Full-A historical selector replay at R6 fixed budgets; never a live policy."""
    state = initial_state(
        record.get("context") or {"c0": r1.C0[0], "c1": "medium"}, bundle
    )
    questions = []
    for slot, budget in BUDGETS.items():
        try:
            if slot in {"Q0", "Q1"}:
                prepared, plan = select(state, bundle, coverage, "POLICY_BASE")
            else:
                question = _select_with_observed(
                    state, bundle["r1_expert"], coverage, record["A"], budget
                )
                base = r1.expose_question(
                    state["base_state"], slot, question, bundle["r1_expert"]
                )
                prepared = runtime.wrap_state(
                    base, bundle, trigger_policy="ALWAYS_ASK", previous=state
                )
                plan = runtime.select_next_question(prepared, bundle)
        except ValueError as exc:
            if not str(exc).startswith("NO_LEGAL_AXIS_AT_FROZEN_BUDGET"):
                raise
            return {
                "status": "CAPACITY_FAILURE",
                "slot": slot,
                "questions": questions,
                "scope": "OFFLINE_FULL_A_SELECTOR_DIAGNOSTIC_AT_R6_BUDGET",
            }
        q = plan["question"]
        visible = (
            record["A"]
            if slot in {"Q0", "Q1"}
            else sorted(set(record["A"]) | set(record["B"]))
        )
        state = update(
            prepared, previous.source_answer(q, visible, bundle["r1_expert"]), bundle
        )
        questions.append(q)
    return {
        "status": "COMPLETE",
        "questions": questions,
        "endpoint_selected": previous.selected(state),
        "scope": "OFFLINE_FULL_A_SELECTOR_DIAGNOSTIC_AT_R6_BUDGET_NOT_ORIGINAL_R5_METRIC",
    }
