"""R5 no-fit, fixed-source information diagnostics; all case artifacts private."""

from __future__ import annotations
import copy
import json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import alignment_metrics_r3 as metric
import audit_revelation_r4 as audit
import data_connections_r4 as connection
import flavor_m2_r1 as r1
import flavor_conditioning_r4 as runtime
import train_conditioning_r4 as training
from train_constraints_r3 import expert_training_groups

VERSION = "m2-r5-fixed-a0-information.v1"


def protocol():
    return {
        "version": VERSION,
        "fit_count": 0,
        "I0": "Actual Q0/Q1 initial selected evidence",
        "I1": "Actual frozen current-bank Q4 ASK trajectory",
        "I2": "Same Q0/Q1; choose unused registered correction axis maximizing train-group mean B coverage, doubled for current A shared attribute; deterministic axis tie; exact I1 slot option budget; never current B or T for question choice",
        "I_FULL": "Initial selected A retained plus complete source B positive evidence batch; outside product question/option budget, no inferred unmentioned negatives",
        "target": "Full independent fixed T; separately fixed T minus source A exact",
        "answer_limit": "Positive-text source nonmention becomes UNSURE, never sensory absence; legacy NONE_OF_THESE conversion count retained; T never supplies answers",
        "gain": "Fixed A0 SKIP gap minus ASK gap, ties retained, empty T null",
        "key_threshold": 0.01,
        "independence": "Coffee held out; shared graders; static cross-grader corroboration, not sequential human QA",
    }


def source_answer(question, visible, expert):
    answer = training.base_training.answer_for(question, visible, expert)
    if answer["state"] == "NONE_OF_THESE":
        answer["state"] = "UNSURE"
    return answer


def source_trajectory(record, bundle):
    state = runtime.initial_state(
        {"c0": r1.C0[0], "c1": "medium"}, bundle, trigger_policy="ALWAYS_ASK"
    )
    states = [copy.deepcopy(state)]
    while True:
        nxt = runtime.select_next_question(state, bundle)
        if nxt["action"] != "ASK":
            break
        q = nxt["question"]
        visible = (
            record["A"]
            if q["slot"] in {"Q0", "Q1"}
            else sorted(set(record["A"]) | set(record["B"]))
        )
        state = runtime.update_state(
            state, source_answer(q, visible, bundle["r1_expert"]), bundle
        )
        states.append(copy.deepcopy(state))
        if len(states) > 6:
            raise ValueError("R5_Q4_BUDGET_EXCEEDED")
    return states


def source_skip(q2, record, bundle):
    state = runtime.apply_q2_action(q2, bundle, "SKIP")
    while True:
        nxt = runtime.select_next_question(state, bundle)
        if nxt["action"] != "ASK":
            break
        q = nxt["question"]
        state = runtime.update_state(
            state,
            source_answer(
                q, sorted(set(record["A"]) | set(record["B"])), bundle["r1_expert"]
            ),
            bundle,
        )
    return state


def selected(state):
    return sorted(
        set().union(
            *(
                audit.canonical_selection(a)
                for a in state["base_state"]["answers_by_question"].values()
            )
        )
    )


def full_state(record, bundle, initial):
    """Scorer diagnostic only; never a live legal-question implementation."""
    base = copy.deepcopy(initial["base_state"])
    concepts = sorted(set(record["B"]))
    options = []
    for c in concepts:
        if c.startswith("sensory."):
            options.append(
                {
                    "id": c,
                    "kind": "specific",
                    "attribute": r1.PARENTS.get(c, ["unregistered"])[0],
                }
            )
        elif c.startswith("attribute."):
            options.append({"id": c, "kind": "broad", "attribute": c.split(".", 1)[1]})
    base["answers_by_question"]["Q2"] = {
        "slot": "Q2",
        "axis": "diagnostic.all_observed",
        "question_id": "R5_DIAGNOSTIC_POSITIVE_BATCH",
        "options": options,
        "shown_option_ids": [o["id"] for o in options],
        "selected_option_ids": [o["id"] for o in options],
        "state": "SELECTED" if options else "UNSURE",
    }
    return runtime.wrap_state(r1.recompute(base, bundle["r1_expert"]), bundle)


def coverage_counts(records):
    bygroup = defaultdict(list)
    for row in records:
        bygroup[row["group_id"]].append(set(row["B"]))
    out = defaultdict(float)
    for rows in bygroup.values():
        for obs in rows:
            for c in obs:
                out[c] += 1 / len(rows) / max(1, len(bygroup))
    return dict(out)


def alternative_state(record, initial, standard, bundle, counts):
    state = copy.deepcopy(initial)
    aattrs = {a for c in record["A"] for a in r1.PARENTS.get(c, [])}
    for slot in ["Q2", "Q3", "Q4"]:
        budget = len(standard[slot]["shown_option_ids"])
        used = {a["axis"] for a in state["base_state"]["answers_by_question"].values()}
        candidates = []
        for q in bundle["r1_expert"]["question_bank"]["correction"]:
            if q["axis"] in used or len(q["options"]) < budget:
                continue
            q = copy.deepcopy(q)
            q["options"] = sorted(
                q["options"], key=lambda o: (-counts.get(o["id"], 0), o["id"])
            )[:budget]
            value = sum(
                counts.get(o["id"], 0) * (2 if o.get("attribute") in aattrs else 1)
                for o in q["options"]
            )
            candidates.append((-value, q["axis"], q))
        if not candidates:
            return None
        question = sorted(candidates, key=lambda x: x[:2])[0][2]
        base = r1.expose_question(
            state["base_state"], slot, question, bundle["r1_expert"]
        )
        state = runtime.wrap_state(
            base, bundle, trigger_policy="ALWAYS_ASK", previous=state
        )
        q = runtime.select_next_question(state, bundle)["question"]
        answer = source_answer(
            q, sorted(set(record["A"]) | set(record["B"])), bundle["r1_expert"]
        )
        state = runtime.update_state(state, answer, bundle)
    return state


def generate_case(record, bundle, fold=None, coverage=None, diagnostics=True):
    trained = set(expert_training_groups(bundle["r1_expert"]))
    if record["group_id"] in trained:
        raise ValueError("BASE_EXPERT_SAW_CURRENT_COFFEE")
    record = {
        **record,
        "relevance": record.get("relevance_full", record.get("relevance", {})),
    }
    states = source_trajectory(record, bundle)
    byslot = {
        max(s["base_state"]["answers_by_question"]): s
        for s in states
        if s["base_state"]["answers_by_question"]
    }
    skip = source_skip(byslot["Q2"], record, bundle)
    views = {"I0": byslot["Q1"], "Q2": byslot["Q2"], "I1": byslot["Q4"], "SKIP": skip}
    full_t = copy.deepcopy(record["relevance"])
    hidden = {c: v for c, v in full_t.items() if c not in set(record["A"])}
    result = {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "fold": fold,
        "source_family": record.get("source_family", "zenodo"),
        "condition_key": record.get("condition_key"),
        "A": record["A"],
        "B": record["B"],
        "relevance": full_t,
        "hidden_relevance": hidden,
        "base_expert_id": bundle["r1_expert"]["bundle_id"],
        "base_training_groups": sorted(trained),
        "selected": {k: selected(v) for k, v in views.items()},
    }
    result["costs"] = {}
    for name, state in views.items():
        answers = state["base_state"]["answers_by_question"]
        exposure = (
            runtime.finalize_result(state, bundle)["exposure"]
            if name in {"I1", "SKIP"}
            else None
        )
        result["costs"][name] = {
            "ordinary_questions": len(answers),
            "ordinary_options": sum(
                len(a["shown_option_ids"]) for a in answers.values()
            ),
            "proposed_final_candidate_count": (
                len(exposure["candidate_ids"]) if exposure else None
            ),
            "actual_final_exposure": 0,
            "human_time": None,
            "final_feedback": "NOT_EVALUATED_NO_REAL_RESPONSE",
        }
    if not diagnostics:
        return result
    views["I_FULL"] = full_state(record, bundle, byslot["Q1"])
    views["I2"] = alternative_state(
        record,
        byslot["Q1"],
        byslot["Q4"]["base_state"]["answers_by_question"],
        bundle,
        coverage or {},
    )
    scores = {}
    for name, state in views.items():
        if state is None:
            scores[name] = {
                "status": "NOT_ESTIMABLE_NO_UNUSED_REGISTERED_AXIS_AT_EXACT_BUDGET"
            }
            continue
        answers = state["base_state"]["answers_by_question"]
        scores[name] = {
            "full": metric.evaluate(
                state["candidate_scores"], full_t, bundle["fixed_candidates"]
            ),
            "hidden": metric.evaluate(
                state["candidate_scores"], hidden, bundle["fixed_candidates"]
            ),
            "ordinary_questions": None if name == "I_FULL" else len(answers),
            "ordinary_options": (
                None
                if name == "I_FULL"
                else sum(len(a["shown_option_ids"]) for a in answers.values())
            ),
            "ranking": state["candidate_scores"],
            "selected": selected(state),
        }
    result["legacy_nonmention_corrected"] = sum(
        training.base_training.answer_for(
            a,
            (
                record["A"]
                if a["slot"] in {"Q0", "Q1"}
                else sorted(set(record["A"]) | set(record["B"]))
            ),
            bundle["r1_expert"],
        )["state"]
        == "NONE_OF_THESE"
        for a in byslot["Q4"]["base_state"]["answers_by_question"].values()
    )
    result["stages"] = scores
    result["novelty"] = audit.exposure_novelty(
        record,
        list(byslot["Q4"]["base_state"]["answers_by_question"].values()),
        source_answer,
        bundle["r1_expert"],
    )
    ask, sk = scores["I1"]["full"]["raw_gap"], scores["SKIP"]["full"]["raw_gap"]
    result["gain"] = None if ask is None or sk is None else sk - ask
    result["q3_new"] = sorted(
        set(
            audit.canonical_selection(
                byslot["Q4"]["base_state"]["answers_by_question"]["Q3"]
            )
        )
        - connection.semantic_closure(selected(byslot["Q2"]))
    )
    result["source_B_related_to_T"] = sorted(set(record["B"]) & set(full_t))
    result["candidate_features_changed"] = (
        r1.encode_features(byslot["Q1"]["base_state"], bundle["r1_expert"])[
            "raw_features"
        ]
        != r1.encode_features(byslot["Q4"]["base_state"], bundle["r1_expert"])[
            "raw_features"
        ]
    )
    result["B_revealed_related_to_T"] = sorted(
        set(result["novelty"]["B_actual_new_specific"]) & set(full_t)
    )
    result["I1_improves_full"] = (
        ask is not None and ask < scores["I0"]["full"]["raw_gap"] - 1e-12
    )
    result["I1_improves_hidden"] = (
        scores["I1"]["hidden"]["raw_gap"] is not None
        and scores["I1"]["hidden"]["raw_gap"]
        < scores["I0"]["hidden"]["raw_gap"] - 1e-12
    )
    return result


def macro(rows, key):
    groups = defaultdict(list)
    for r in rows:
        if r[key] is not None:
            groups[r["group_id"]].append(r[key])
    return float(np.mean([np.mean(v) for v in groups.values()])) if groups else None


def summarize(rows):
    known = [r for r in rows if r["gain"] is not None]
    stages = {}
    for name in ["I0", "Q2", "I1", "SKIP", "I2", "I_FULL"]:
        stages[name] = {}
        for task in ["full", "hidden"]:
            valid = [r for r in rows if task in r["stages"][name]]
            stages[name][task] = {
                k: macro(
                    [
                        {"group_id": r["group_id"], k: r["stages"][name][task][k]}
                        for r in valid
                    ],
                    k,
                )
                for k in ["raw_gap", "ndcg", "recall"]
            }
            stages[name][task]["identifiable_records"] = sum(
                r["stages"][name][task]["raw_gap"] is not None for r in valid
            )
        for k in ["ordinary_questions", "ordinary_options"]:
            stages[name][k] = macro(
                [
                    {"group_id": r["group_id"], k: r["stages"][name].get(k)}
                    for r in rows
                ],
                k,
            )
    fields = [
        "source_B_new_exact",
        "B_actual_new_specific",
        "B_new_system_canonical",
        "source_B_new_specific_not_selected",
    ]
    return {
        "records": len(rows),
        "coffee_groups": len({r["group_id"] for r in rows}),
        "stages": stages,
        "funnel": {
            f: {
                "records": sum(bool(r["novelty"][f]) for r in rows),
                "record_concepts": sum(len(r["novelty"][f]) for r in rows),
            }
            for f in fields
        },
        "B_exact_overlap_independent_T_records": sum(
            bool(r["source_B_related_to_T"]) for r in rows
        ),
        "Q3_new_canonical_records": sum(bool(r["q3_new"]) for r in rows),
        "gain": {
            "identifiable": len(known),
            "unknown": len(rows) - len(known),
            "positive": sum(r["gain"] > 1e-12 for r in known),
            "tie": sum(abs(r["gain"]) <= 1e-12 for r in known),
            "negative": sum(r["gain"] < -1e-12 for r in known),
            "macro": macro(rows, "gain"),
            "key_groups": len({r["group_id"] for r in known if r["gain"] > 0.01}),
            "outer_training_key_groups": {
                str(f): len(
                    {
                        r["group_id"]
                        for r in known
                        if r["fold"] != f and r["gain"] > 0.01
                    }
                )
                for f in sorted({r["fold"] for r in rows})
            },
        },
        "protocol": protocol(),
    }


def human_audit(owner):
    paths = [
        Path(owner) / "human_comparison_cases.private.json",
        Path(owner) / "revisions/r2/human_comparison_cases_r2.private.json",
    ]
    original, enriched = [json.loads(p.read_text()) for p in paths]
    if {r["case_id"] for r in original} != {r["case_id"] for r in enriched}:
        raise ValueError("HUMAN_CASE_ID_MISMATCH")
    completed = {
        r["case_id"]
        for r in original + enriched
        if r.get("human_choice") is not None
        or r.get("corrective_selection") is not None
    }
    review = []
    for row in sorted(
        enriched,
        key=lambda r: (-len(r.get("professional_observed_evidence", [])), r["case_id"]),
    )[:12]:
        review.append(
            {
                "case_id": row["case_id"],
                "existing_case": row,
                "review_scope": "Mapping, observation roles, unsupported specificity and whether answers add information; not tasting truth",
                "semantic_mapping_review": None,
                "observation_role_review": None,
                "unsupported_specificity_review": None,
                "new_information_review": None,
            }
        )
    summary = {
        "original_cases": len(original),
        "enriched_cases": len(enriched),
        "completed_human_judgments": len(completed),
        "rationales": sum(bool(r.get("human_rationale")) for r in enriched),
        "measured_times": sum(
            r.get("actual_response_seconds") is not None for r in enriched
        ),
        "review_items": len(review),
        "source_sha256": [connection.sha(p) for p in paths],
        "status": (
            "NOT_EVALUATED"
            if not completed
            else "REQUIRES_VALIDATED_ORIGINAL_EXPOSURE_IMPORT"
        ),
    }
    return summary, review


def run(owner, contract_path):
    import data_supervision_r5 as source

    owner = Path(owner)
    parsed = json.loads(
        (owner / "revisions/r5/zenodo_source_parse.private.json").read_text()
    )
    examples = source.build_examples(parsed, contract_path)
    units = {u["observation_unit_id"]: u for u in parsed["observation_units"]}
    for record in examples:
        literals = {
            units[x]["source_roast_grind_literal"]
            for x in [
                record["A_observation_unit_id"],
                record["B_observation_unit_id"],
                *record["T_observation_unit_ids"],
            ]
        }
        if len(literals) != 1:
            raise ValueError("WITHIN_SAMPLE_CONDITION_LITERAL_DISAGREEMENT")
        record["condition_key"] = connection.digest(sorted(literals))
    records = [r for r in examples if r["old_split"] == "DEVELOPMENT"]
    folds = json.loads((owner / "revisions/r1/D0_folds.private.json").read_text())
    allrows = []
    nested = {}
    lineage = []
    for outer in range(3):
        held = [r for r in records if folds[r["group_id"]] == outer]
        fitting = [r for r in records if folds[r["group_id"]] != outer]
        expertpath = owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{outer}.model.json"
        expert = json.loads(expertpath.read_text())
        if expert_training_groups(expert) & {r["group_id"] for r in held}:
            raise ValueError("OUTER_BASE_LEAKAGE")
        bundle = training.model_bundle(expert)
        coverage = coverage_counts(fitting)
        allrows.extend(generate_case(r, bundle, outer, coverage) for r in held)
        inner = []
        for index in range(2):
            path = (
                owner
                / f"revisions/r2/models/R2_R1_EXPERT_outer{outer}_inner{index}.model.json"
            )
            ex = json.loads(path.read_text())
            if expert_training_groups(ex) & {r["group_id"] for r in held}:
                raise ValueError("INNER_BASE_SAW_OUTER_HELD")
            inner.append((training.model_bundle(ex), set(expert_training_groups(ex))))
            lineage.append(
                {"outer": outer, "inner": index, "model_sha256": connection.sha(path)}
            )
        rows = []
        for record in fitting:
            eligible = [
                (i, b)
                for i, (b, groups) in enumerate(inner)
                if record["group_id"] not in groups
            ]
            if not eligible:
                raise ValueError("NO_COFFEE_OOF_INNER_EXPERT")
            i, b = eligible[0]
            row = generate_case(record, b, outer, diagnostics=False)
            row["inner"] = i
            rows.append(row)
        nested[str(outer)] = rows
    summary = summarize(allrows)
    human, review = human_audit(owner)
    summary["human_review"] = human
    summary["legacy_nonmention_corrected_answers"] = sum(
        r["legacy_nonmention_corrected"] for r in allrows
    )
    summary["nested_base_lineage"] = lineage
    summary["information_utilization_counts"] = {
        k: sum(bool(r[k]) for r in allrows)
        for k in [
            "candidate_features_changed",
            "B_revealed_related_to_T",
            "I1_improves_full",
            "I1_improves_hidden",
        ]
    }
    summary["posthoc_best_ask_skip_gap"] = macro(
        [
            {
                "group_id": r["group_id"],
                "best": (
                    min(
                        r["stages"]["I1"]["full"]["raw_gap"],
                        r["stages"]["SKIP"]["full"]["raw_gap"],
                    )
                    if r["gain"] is not None
                    else None
                ),
            }
            for r in allrows
        ],
        "best",
    )
    summary["posthoc_best_status"] = "DIAGNOSTIC_ONLY_USES_FIXED_T_NOT_DEPLOYABLE"
    for name, value in [
        ("information_cases.private.json", allrows),
        ("information_nested_training.private.json", nested),
        ("information_summary.private.json", summary),
        ("information_human_review.private.json", review),
    ]:
        destination = owner / "revisions/r5" / name
        if destination.exists():
            if json.loads(destination.read_text()) != value:
                raise ValueError("SEALED_INFORMATION_ARTIFACT_CHANGED:" + name)
        else:
            connection._save_new(destination, value)
    return summary


def trigger_case(record, bundle):
    """New gain for this exact frozen scorer; independent B attribution retained."""
    states = source_trajectory(record, bundle)
    byslot = {
        max(s["base_state"]["answers_by_question"]): s
        for s in states
        if s["base_state"]["answers_by_question"]
    }
    skip = source_skip(byslot["Q2"], record, bundle)
    target = record.get("relevance_full", record.get("relevance", {}))
    askgap = metric.evaluate(
        byslot["Q4"]["candidate_scores"], target, bundle["fixed_candidates"]
    )["raw_gap"]
    skipgap = metric.evaluate(
        skip["candidate_scores"], target, bundle["fixed_candidates"]
    )["raw_gap"]
    novelty = audit.exposure_novelty(
        record,
        list(byslot["Q4"]["base_state"]["answers_by_question"].values()),
        source_answer,
        bundle["r1_expert"],
    )
    q3 = next(x for x in novelty["exposure_trace"] if x["slot"] == "Q3")
    new = set(q3["selected_canonical"]) - connection.semantic_closure(
        selected(byslot["Q2"])
    )
    attributable = new & set(q3["B_attributable_selected_canonical"])
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "gain": None if askgap is None else skipgap - askgap,
        "Q3_new_B_canonical": sorted(attributable),
        "Q3_new_canonical": sorted(new),
        "base_expert_id": bundle["r1_expert"]["bundle_id"],
    }


def run_trigger_audit(owner):
    owner = Path(owner)
    private = owner / "revisions/r5"
    outerrows = json.loads((private / "information_cases.private.json").read_text())
    nested = json.loads(
        (private / "information_nested_training.private.json").read_text()
    )
    rows = []
    for outer, fitting in nested.items():
        bundles = {
            i: training.model_bundle(
                json.loads(
                    (
                        owner
                        / f"revisions/r2/models/R2_R1_EXPERT_outer{outer}_inner{i}.model.json"
                    ).read_text()
                )
            )
            for i in range(2)
        }
        held = {r["group_id"] for r in outerrows if str(r["fold"]) == outer}
        for record in fitting:
            bundle = bundles[record["inner"]]
            if (held | {record["group_id"]}) & expert_training_groups(
                bundle["r1_expert"]
            ):
                raise ValueError("TRIGGER_GAIN_BASE_LEAKAGE")
            rows.append({"outer": outer, **trigger_case(record, bundle)})

    def counts(rs):
        known = [r for r in rs if r["gain"] is not None]
        keys = [r for r in known if r["gain"] > 0.01 and r["Q3_new_B_canonical"]]
        return {
            "records": len(rs),
            "identifiable": len(known),
            "unknown": len(rs) - len(known),
            "Q3_new_B_records": sum(bool(r["Q3_new_B_canonical"]) for r in rs),
            "positive": sum(r["gain"] > 1e-12 for r in known),
            "negative": sum(r["gain"] < -1e-12 for r in known),
            "ties": sum(abs(r["gain"]) <= 1e-12 for r in known),
            "key_with_new_B_records": len(keys),
            "key_with_new_B_groups": len({r["group_id"] for r in keys}),
        }

    outer = []
    for r in outerrows:
        q3 = next(x for x in r["novelty"]["exposure_trace"] if x["slot"] == "Q3")
        outer.append(
            {
                **r,
                "Q3_new_B_canonical": sorted(
                    set(r["q3_new"]) & set(q3["B_attributable_selected_canonical"])
                ),
            }
        )
    summary = {
        "outer_held": counts(outer),
        "nested_training": {
            f: counts([r for r in rows if r["outer"] == f]) for f in nested
        },
        "status": "NO_TRIGGER_FIT_INFORMATION_DIAGNOSTIC_ONLY",
        "gain_scorer": "FIXED_A0_NOT_NEW_R5_HEAD; regenerate gain for any newhead before training",
        "key_gate": "gain>0.01 AND truly new B-derived Q3 canonical observation",
    }
    for name, value in [
        ("information_trigger_gain_cases.private.json", rows),
        ("information_trigger_diagnostic.private.json", summary),
    ]:
        path = private / name
        if path.exists():
            if json.loads(path.read_text()) != value:
                raise ValueError("TRIGGER_DIAGNOSTIC_CHANGED")
        else:
            connection._save_new(path, value)
    return summary


def run_new_head_trigger_audit(owner):
    """Evaluate frozen R5 head action values; no gain fit, threshold search or train-label claim."""
    import train_supervision_r5 as head
    from run_supervision_r5 import adapt

    owner = Path(owner)
    private = owner / "revisions/r5"
    source_rows = json.loads((private / "information_cases.private.json").read_text())
    models = {
        f: json.loads((private / f"training/models/T2_AB_outer{f}.json").read_text())
        for f in range(3)
    }
    policies = {
        f: json.loads(
            (owner / f"revisions/r4/models/R4_POLICY_outer{f}.model.json").read_text()
        )
        for f in range(3)
    }
    rows = []
    for raw in source_rows:
        fold = raw["fold"]
        model = models[fold]
        bundle = policies[fold]
        if raw["group_id"] in model["training_groups"] or raw[
            "group_id"
        ] in expert_training_groups(bundle["r1_expert"]):
            raise ValueError("NEW_HEAD_POLICY_AUDIT_LEAKAGE")
        row = adapt(raw)
        scores = {
            branch: head.evaluate(row, *head.predict(row, model, branch))
            for branch in ["ASK", "SKIP"]
        }
        state = runtime.initial_state(
            {"c0": r1.C0[0], "c1": "medium"}, bundle, trigger_policy="KEY_CASE"
        )
        for slot in ["Q0", "Q1", "Q2"]:
            q = runtime.select_next_question(state, bundle)["question"]
            if q["slot"] != slot:
                raise ValueError("OLD_POLICY_Q2_PATH_MISMATCH")
            answer = source_answer(
                q,
                (
                    raw["A"]
                    if slot in {"Q0", "Q1"}
                    else sorted(set(raw["A"]) | set(raw["B"]))
                ),
                bundle["r1_expert"],
            )
            state = runtime.update_state(state, answer, bundle)
        if selected(state) != raw["selected"]["Q2"]:
            raise ValueError("OLD_POLICY_OBSERVATION_TRANSPORT_NOT_IDENTICAL")
        action = state["q2_decision"]["action"]
        ask, skip = scores["ASK"]["raw_gap"], scores["SKIP"]["raw_gap"]
        gain = None if ask is None else skip - ask
        trace = next(x for x in raw["novelty"]["exposure_trace"] if x["slot"] == "Q3")
        true_b = sorted(
            set(raw["q3_new"]) & set(trace["B_attributable_selected_canonical"])
        )
        rows.append(
            {
                "record_id": raw["record_id"],
                "group_id": raw["group_id"],
                "fold": fold,
                "gain": gain,
                "Q3_true_B_new": true_b,
                "scores": scores,
                "old_R4_action": action,
                "costs": {"ASK": raw["costs"]["I1"], "SKIP": raw["costs"]["SKIP"]},
            }
        )
    known = [r for r in rows if r["gain"] is not None]
    keys = [r for r in known if r["gain"] > 0.01 and r["Q3_true_B_new"]]
    result = {
        "status": "NO_NEW_TRIGGER_FIT",
        "gain_scorer": "FROZEN_R5_T2_AB_OUTER_HELD",
        "records": len(rows),
        "groups": len({r["group_id"] for r in rows}),
        "identifiable": len(known),
        "unknown": len(rows) - len(known),
        "positive": sum(r["gain"] > 1e-12 for r in known),
        "zero": sum(abs(r["gain"]) <= 1e-12 for r in known),
        "negative": sum(r["gain"] < -1e-12 for r in known),
        "true_B_new_records": sum(bool(r["Q3_true_B_new"]) for r in rows),
        "key_true_B_records": len(keys),
        "key_true_B_groups": len({r["group_id"] for r in keys}),
        "held_key_true_B_groups_by_outer": {
            str(f): len({r["group_id"] for r in keys if r["fold"] == f})
            for f in range(3)
        },
        "other_outer_OOF_candidate_key_groups_NOT_TRAIN_LABELS": {
            str(f): len({r["group_id"] for r in keys if r["fold"] != f})
            for f in range(3)
        },
        "actual_nested_new_head_training_gain": "NOT_ESTIMATED; other outer OOF rows are not valid nested train labels",
        "gain_macro": macro(rows, "gain"),
        "gain_min": min((r["gain"] for r in known), default=None),
        "gain_max": max((r["gain"] for r in known), default=None),
        "policies": {},
    }
    for policy in ["ALWAYS_ASK", "ALWAYS_SKIP", "R4_OLD", "POSTHOC_BEST"]:
        values = []
        for r in rows:
            action = (
                "ASK"
                if policy == "ALWAYS_ASK"
                else (
                    "SKIP"
                    if policy == "ALWAYS_SKIP"
                    else (
                        r["old_R4_action"]
                        if policy == "R4_OLD"
                        else (
                            "ASK" if r["gain"] is not None and r["gain"] > 0 else "SKIP"
                        )
                    )
                )
            )
            cost = r["costs"][action]
            gap = r["scores"][action]["raw_gap"]
            best = (
                min(r["scores"]["ASK"]["raw_gap"], r["scores"]["SKIP"]["raw_gap"])
                if r["gain"] is not None
                else None
            )
            values.append(
                {
                    "group_id": r["group_id"],
                    "gap": gap,
                    "ndcg": r["scores"][action]["ndcg"],
                    "ask": int(action == "ASK"),
                    "questions": cost["ordinary_questions"],
                    "options": cost["ordinary_options"],
                    "proposed_final_candidates": cost["proposed_final_candidate_count"],
                    "regret": None if gap is None else gap - best,
                    "missed_gain": (
                        max(r["gain"], 0)
                        if r["gain"] is not None and action == "SKIP"
                        else 0 if r["gain"] is not None else None
                    ),
                    "unnecessary_ask": (
                        int(action == "ASK" and r["gain"] <= 1e-12)
                        if r["gain"] is not None
                        else None
                    ),
                }
            )
        result["policies"][policy] = {
            k: macro(values, k)
            for k in [
                "gap",
                "ndcg",
                "ask",
                "questions",
                "options",
                "proposed_final_candidates",
                "regret",
                "missed_gain",
                "unnecessary_ask",
            ]
        }
        result["policies"][policy]["actual_final_exposure"] = 0
        result["policies"][policy]["human_time"] = "NOT_EVALUATED"
    result["decision"] = (
        "NO_IDENTIFIABLE_NEW_B_KEY_SIGNAL_DO_NOT_TRAIN"
        if not keys
        else (
            "KEY_SIGNAL_CONCENTRATED_IN_ONE_GROUP_DO_NOT_TRAIN"
            if len({r["group_id"] for r in keys}) == 1
            else "SUPPORT_REQUIRES_NESTED_NEW_HEAD_GAIN_BEFORE_ANY_TRAINING"
        )
    )
    result["posthoc_limit"] = (
        "Uses T to choose action; diagnostic only; unknown gain assigned SKIP solely for reporting minimum proposed cost, not fabricated label"
    )
    for name, value in [
        ("information_new_head_trigger_cases.private.json", rows),
        ("information_new_head_trigger.private.json", result),
    ]:
        path = private / name
        if path.exists():
            if json.loads(path.read_text()) != value:
                raise ValueError("SEALED_NEW_HEAD_GAIN_CHANGED")
        else:
            connection._save_new(path, value)
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", required=True)
    parser.add_argument("--contract", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.owner_dir, args.contract), indent=2))
