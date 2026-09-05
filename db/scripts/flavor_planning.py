"""Bounded one/two-step planning from TRAIN-only softly conditioned records."""

from __future__ import annotations
import copy, math, random
from collections import defaultdict
import numpy as np
import flavor_sequential as legacy_s

_CACHE = {}


def backend(bundle):
    if bundle.get("semantic_version") == "typed-support.v2.r1":
        import flavor_m2_r1

        return flavor_m2_r1
    return legacy_s


def future_slots(state):
    limit = 6 if state["path"] == "P4" else 5
    return [
        "Q" + str(i)
        for i in range(2, limit)
        if "Q" + str(i) not in state["answers_by_question"]
        and "Q" + str(i) not in state["skipped_slots"]
    ]


def soft_weights(state, bundle):
    s = backend(bundle)
    ev = s.evidence(state, bundle)
    rows = bundle["statistics"]["planning_records"]
    scores = []
    for r in rows:
        targets = set(r["targets"])
        attrs = {a for c in targets for a in bundle["candidate_attributes"].get(c, [])}
        if bundle.get("semantic_version") == "typed-support.v2.r1":
            # Positive-only source records offer positive matching support;
            # missing mentions do not establish contradictory sensory evidence.
            # Final selections merge with direct concepts once, and explicit
            # NONE retains the actual exposed broad or concrete scope.
            value = (
                sum(1.0 for c in ev["confirmed"] if c in targets)
                + sum(0.5 for a in ev["independent_broad"] if a in attrs)
                - sum(0.25 for c in ev["explicit_none"] if c in targets)
                - sum(
                    0.25
                    for a in ev["negative_broad"]
                    if a in attrs and "attribute." + a not in targets
                )
            )
        else:
            value = (
                sum(1.0 if c in targets else -0.15 for c in ev["specific"])
                + sum(0.5 if a in attrs else -0.075 for a in ev["independent_broad"])
                + sum(1.25 if c in targets else -0.15 for c in ev["feedback"])
                - sum(0.25 for c in ev["explicit_none"] if c in targets)
            )
        scores.append(value)
    if not scores:
        return np.array([])
    w = np.exp(np.array(scores) - max(scores))
    w /= w.sum()
    neff = 1 / float(np.square(w).sum())
    shrink = neff / (neff + 10.0)
    # Continuous shrinkage preserves history at all support levels.
    return shrink * w + (1 - shrink) / len(w)


def available(state, bundle):
    s = backend(bundle)
    used = {a["axis"] for a in state["answers_by_question"].values()}
    already = {
        x
        for a in state["answers_by_question"].values()
        for x in a["selected_option_ids"]
    }
    return [
        q
        for q in bundle["question_bank"]["correction"]
        if q["axis"] not in used and any(o["id"] not in already for o in q["options"])
    ]


def simulate_answer(state, q, pattern, bundle):
    s = backend(bundle)
    st = copy.deepcopy(state)
    slot = future_slots(st)[0]
    instance = s.make_instance(slot, q, st, bundle)
    st["answers_by_question"][slot] = {
        **instance,
        "selected_option_ids": list(pattern),
        "state": "SELECTED" if pattern else "UNSURE",
    }
    return s.recompute(st, bundle)


def response_groups(state, q, bundle):
    s = backend(bundle)
    weights = soft_weights(state, bundle)
    parts = defaultdict(list)
    for i, r in enumerate(bundle["statistics"]["planning_records"]):
        targets = set(r["targets"])
        attrs = {a for c in targets for a in bundle["candidate_attributes"].get(c, [])}
        pattern = tuple(
            o["id"]
            for o in q["options"]
            if (o["kind"] == "specific" and o["id"] in targets)
            or (o["kind"] == "broad" and o["attribute"] in attrs)
        )
        parts[pattern].append(i)
    result = [
        (pattern, float(weights[idx].sum()), idx) for pattern, idx in parts.items()
    ]
    return sorted(result, key=lambda x: (-x[1], x[0]))


def utility(rank, rows, weights, exclude):
    candidates = [r["candidate_id"] for r in rank if r["candidate_id"] not in exclude][
        :5
    ]
    total = 0.0
    for row, w in zip(rows, weights):
        target = set(row["targets"]) - exclude
        ideal = sum(1 / math.log2(i + 2) for i in range(min(5, len(target))))
        if ideal:
            total += (
                w
                * sum(
                    (c in target) / math.log2(i + 2) for i, c in enumerate(candidates)
                )
                / ideal
            )
    return float(total)


def question_value(state, q, bundle, depth=1):
    s = backend(bundle)
    train = bundle["statistics"]["planning_records"]
    weights = soft_weights(state, bundle)
    exclude = set(s.evidence(state, bundle)["specific"])
    base = utility(state["candidate_scores"], train, weights, exclude)
    expected = 0.0
    support = 0
    outcomes = response_groups(state, q, bundle)
    for pattern, p, indices in outcomes:
        child = simulate_answer(state, q, pattern, bundle)
        conditional = weights[indices]
        conditional = conditional / conditional.sum()
        subset = [train[i] for i in indices]
        # The fixed utility target omits only already explicit information. It is
        # TRAIN record recovery utility, not a test-label entropy shortcut.
        u = utility(child["candidate_scores"], subset, conditional, exclude)
        if depth == 2 and future_slots(child):
            second = available(child, bundle)
            # Bounded beam chosen without held-out targets. Same pool for controls.
            second = sorted(second, key=lambda z: z["priority"], reverse=True)[:2]
            u += max(
                [0.0]
                + [
                    max(0.0, question_value(child, nxt, bundle, 1)["net_value"])
                    for nxt in second
                ]
            )
        expected += p * u
        if len(indices) >= 2:
            support += 1
    return {
        "net_value": expected - base - bundle.get("question_cost", 0.01),
        "expected_utility_after": expected,
        "current_utility": base,
        "supported_response_patterns": support,
        "response_pattern_count": len(outcomes),
        "basis": "PROXY_POLICY_SIMULATION_TRAIN_RECORD_UTILITY",
        "depth": depth,
    }


def choose(state, bundle):
    s = backend(bundle)
    questions = available(state, bundle)
    if not questions:
        return None
    policy = state["policy"]
    if policy == "fixed":
        return {
            "question": questions[0],
            "net_value": None,
            "basis": "FIXED_TRAIN_QUALIFIED_ORDER",
        }
    if policy == "random":
        order = list(questions)
        random.Random(bundle["seed"]).shuffle(order)
        return {
            "question": order[0],
            "net_value": None,
            "basis": "FIXED_SEEDED_TRAIN_QUALIFIED_ORDER",
        }
    # Same predeclared eligible pool; bounded first-step beam for two-step cost.
    scored = [(q, question_value(state, q, bundle, 1)) for q in questions]
    if policy == "two_step":
        scored = sorted(scored, key=lambda x: (-x[1]["net_value"], x[0]["axis"]))[:2]
        scored = [
            (q, question_value(state, q, bundle, min(2, len(future_slots(state)))))
            for q, _ in scored
        ]
    q, v = max(scored, key=lambda x: (x[1]["net_value"], x[0]["axis"]))
    return {"question": q, **v}


def plan_stage(state, bundle):
    s = backend(bundle)
    if state["final_comparison"]:
        return {
            "action": "FINAL_RESULT",
            "reason": "FINAL_COMPARISON_CONSUMED",
            "question": None,
        }
    used = set(state["answers_by_question"])
    path = state["path"]
    for slot, key in [("Q0", "initial_0"), ("Q1", "initial_1")]:
        if slot not in used:
            return {
                "action": "ASK",
                "reason": "MANDATORY_COMPLEMENTARY_INITIAL_EXTRACTION",
                "question": s.make_instance(
                    slot, bundle["question_bank"][key], state, bundle
                ),
            }
    key = s.digest(
        [
            bundle["bundle_id"],
            bundle["model_parameters"],
            state["context"],
            state["answers_by_question"],
            state["path"],
            state["policy"],
            state["skipped_slots"],
        ]
    )
    if key in _CACHE:
        return copy.deepcopy(_CACHE[key])
    if "Q4" in used and (
        path != "P4" or "Q5" in used or "Q5" in state["skipped_slots"]
    ):
        return {
            "action": "PRELIMINARY_RESULT",
            "reason": "AUTHORIZED_Q4_OR_Q5_CLOSURE",
            "question": None,
        }
    choice = choose(state, bundle)
    if not choice:
        # No invented fallback. A qualified bank must contain enough distinct axes
        # to execute the authorized path; insufficiency is a technical contract error.
        raise ValueError("INSUFFICIENT_QUALIFIED_QUESTION_AXES_FOR_AUTHORIZED_PATH")
    if "Q2" not in used:
        slot = "Q2"
    elif "Q3" not in used and "Q3" not in state["skipped_slots"] and "Q4" not in used:
        optional = path in {"P2", "P4"}
        slot = (
            "Q4"
            if optional and choice["net_value"] is not None and choice["net_value"] <= 0
            else "Q3"
        )
    elif "Q4" not in used:
        slot = "Q4"
    elif path == "P4" and "Q5" not in used:
        if choice["net_value"] is not None and choice["net_value"] <= 0:
            return {
                "action": "PRELIMINARY_RESULT",
                "reason": "Q4_COMPLETE_Q5_NOT_WORTH_COST",
                "question": None,
            }
        slot = "Q5"
    else:
        raise ValueError("INVALID_STAGE")
    result = {
        "action": "ASK",
        "reason": (
            "CONDITIONAL_SECOND_QUESTION_AFTER_ACTUAL_FIRST_ANSWER"
            if slot in {"Q3", "Q4", "Q5"}
            else "CORRECTION_STAGE"
        ),
        "question": s.make_instance(slot, choice["question"], state, bundle),
        "value_estimate": {k: v for k, v in choice.items() if k != "question"},
    }
    if len(_CACHE) > 10000:
        _CACHE.clear()
    _CACHE[key] = copy.deepcopy(result)
    return result


def select_next_question(state, bundle):
    s = backend(bundle)
    return plan_stage(state, bundle)
