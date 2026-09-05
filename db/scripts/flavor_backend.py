#!/usr/bin/env python3
"""Backend-only live flavor ranking; no case-table lookup, server or UI dependency."""

from __future__ import annotations
import argparse, copy, hashlib, json, math
from collections import Counter, defaultdict
from pathlib import Path

C0 = [
    "preparation.family." + x
    for x in [
        "filter_percolation",
        "immersion",
        "hybrid",
        "espresso_pressure",
        "diluted_espresso",
        "stovetop_boiled",
        "cold_extraction",
        "espresso_milk",
    ]
]
C1 = [
    "extremely_light",
    "light",
    "medium_light",
    "medium",
    "medium_dark",
    "dark",
    "extremely_dark",
]
GROUPS = {
    "fruit": "apple orange lemon cherry grape strawberry bergamot raisin grapefruit peach raspberry prune blackcurrant lime pineapple pear blueberry mango blackberry plum banana pomegranate",
    "floral": "jasmine rose orange_blossom chamomile",
    "sweet": "honey caramel brown_sugar vanilla molasses",
    "nut_cocoa": "cocoa dark_chocolate almond hazelnut walnut peanut",
    "spice_roasted": "tobacco cardamom black_pepper malt cinnamon nutmeg smoky clove",
    "tea_green": "black_tea green_tea lemongrass hay woody cedar earthy",
    "fermented": "alcoholic wine_like_character fermented_character",
    "taste": "bitter",
}
FAMILY = {f"sensory.{x}": g for g, words in GROUPS.items() for x in words.split()}
BASE_CANDIDATES = sorted(FAMILY)
STATES = {"SELECTED", "UNSURE", "NONE_OF_THESE", "SKIP"}
RELATION_TYPES = [
    "EQUIVALENT",
    "HIERARCHICAL",
    "MODIFIER",
    "COMPOUND",
    "COOCCURRENCE",
    "DIRECT_OBSERVATION",
]


def fingerprint(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_context(context):
    if not isinstance(context, dict) or set(context) != {"c0", "c1"}:
        raise ValueError("Context requires exactly c0 and c1")
    if not isinstance(context["c0"], str) or context["c0"] not in C0:
        raise ValueError("c0 must be one existing family ID")
    if not isinstance(context["c1"], str) or context["c1"] not in C1:
        raise ValueError(
            "c1 must be one of seven explicit levels; no missing/default branch"
        )
    return dict(context)


def question_bank(vocabulary):
    bank = [
        {
            "question_id": "q.direction",
            "semantic_key": "broad_direction",
            "options": [
                {
                    "option_id": "family." + g,
                    "concept_ids": [c for c in vocabulary if FAMILY.get(c) == g],
                    "relation_type": "HIERARCHICAL",
                }
                for g in GROUPS
                if any(FAMILY.get(c) == g for c in vocabulary)
            ],
        }
    ]
    for g in GROUPS:
        options = [
            {"option_id": c, "concept_ids": [c], "relation_type": "DIRECT_OBSERVATION"}
            for c in vocabulary
            if FAMILY.get(c) == g
        ]
        if options:
            bank.append(
                {
                    "question_id": "q." + g,
                    "semantic_key": "specific_" + g,
                    "options": options,
                }
            )
    return bank


def interpret_answer(answer, bundle):
    required = {"question_id", "shown_option_ids", "selected_option_ids", "state"}
    if not isinstance(answer, dict) or set(answer) != required:
        raise ValueError("Answer fields differ from contract")
    bank = {q["question_id"]: q for q in question_bank(bundle["vocabulary"])}
    if not isinstance(answer["question_id"], str) or answer["question_id"] not in bank:
        raise ValueError("Unknown question")
    q = bank[answer["question_id"]]
    options = {o["option_id"]: o for o in q["options"]}
    for key in ["shown_option_ids", "selected_option_ids"]:
        a = answer[key]
        if (
            not isinstance(a, list)
            or any(not isinstance(x, str) for x in a)
            or len(a) != len(set(a))
        ):
            raise ValueError("Option lists must contain unique strings")
    shown = set(answer["shown_option_ids"])
    selected = set(answer["selected_option_ids"])
    if not shown or not shown <= set(options) or not selected <= shown:
        raise ValueError("Selected/shown options outside catalog")
    if (
        not isinstance(answer["state"], str)
        or answer["state"] not in STATES
        or (answer["state"] == "SELECTED") != bool(selected)
    ):
        raise ValueError("Typed state and selected set disagree")
    a = copy.deepcopy(answer)
    a["shown_option_ids"] = sorted(shown)
    a["selected_option_ids"] = sorted(selected)
    a["semantic_key"] = q["semantic_key"]
    a["relations"] = []
    if a["state"] in {"UNSURE", "SKIP"}:
        return a
    active = selected if a["state"] == "SELECTED" else shown
    answer_evidence = "answer:" + fingerprint({k: a[k] for k in required})
    for oid in sorted(active):
        o = options[oid]
        for c in o["concept_ids"]:
            a["relations"].append(
                {
                    "candidate_id": c,
                    "option_id": oid,
                    "relation_type": o["relation_type"],
                    "polarity": 1 if a["state"] == "SELECTED" else -1,
                    "evidence_id": answer_evidence + ":" + oid,
                }
            )
    return a


def interpret_semantic_evidence(claims, permissions):
    """Use explicit typed source relations, never keywords in a method description.

    Permissions are keyed by the exact artifact, not by concept or source family.
    Multiple paths from one observation are one evidence unit. Compound,
    modifier and cooccurrence claims never confirm an individual child label.
    """
    accepted = {}
    withheld = []
    for claim in claims:
        required = {
            "evidence_id",
            "artifact_id",
            "subject_id",
            "object_id",
            "relation_type",
            "support",
            "role",
        }
        if not required <= set(claim):
            raise ValueError("Semantic evidence missing explicit relation fields")
        p = permissions.get(claim["artifact_id"], {})
        if (
            p.get("use_basis") != "NONCOMMERCIAL_RESEARCH_USE"
            or p.get("conditions_satisfied") is not True
        ):
            withheld.append(
                {**claim, "reason": "EXACT_ARTIFACT_PERMISSION_NOT_SATISFIED"}
            )
            continue
        if claim["relation_type"] not in RELATION_TYPES:
            raise ValueError("Unrecognized semantic relation")
        support = claim["support"]
        if (
            not isinstance(support, (float, int))
            or isinstance(support, bool)
            or not math.isfinite(support)
            or not 0 <= support <= 1
        ):
            raise ValueError("Support must be finite and bounded")
        kind = claim["relation_type"]
        confirmed = (
            kind in {"DIRECT_OBSERVATION", "EQUIVALENT"}
            and claim["role"] == "CORE_PROFESSIONAL"
        )
        row = {
            **claim,
            "confirms_candidate": confirmed,
            "bounded_support": (
                support
                if confirmed
                else min(support, 0.25) if kind == "HIERARCHICAL" else 0.0
            ),
        }
        key = (claim["artifact_id"], claim["evidence_id"], claim["object_id"])
        # Correlated paths cannot accumulate; retain the strongest permitted effect.
        if (
            key not in accepted
            or row["bounded_support"] > accepted[key]["bounded_support"]
        ):
            accepted[key] = row
    return {"accepted": list(accepted.values()), "withheld": withheld}


def observations(answers, bundle):
    leaves = set()
    families = set()
    negative = set()
    for raw in answers:
        a = interpret_answer(raw, bundle)
        if a["state"] == "SELECTED":
            # All broad options selected conveys no discriminating direction.
            broad_all = a["question_id"] == "q.direction" and set(
                a["selected_option_ids"]
            ) == set(a["shown_option_ids"])
            for r in a["relations"]:
                if r["relation_type"] == "DIRECT_OBSERVATION":
                    leaves.add(r["candidate_id"])
                elif not broad_all:
                    families.add(FAMILY[r["candidate_id"]])
        elif a["state"] == "NONE_OF_THESE":
            negative.update(r["candidate_id"] for r in a["relations"])
    return leaves, families, negative


def features(answers, context, bundle, ablate=()):
    observed, families, negative = observations(answers, bundle)
    f = {}
    if "semantic" not in ablate:
        for c in observed:
            f["observed:" + c] = 1.0
        for g in families | {FAMILY[c] for c in observed}:
            f["family:" + g] = 1.0
        for c in bundle["vocabulary"]:
            f["cooccurrence:" + c] = sum(
                bundle["conditional"].get(x, {}).get(c, 0) for x in observed
            ) / max(len(observed), 1)
    if "interaction" not in ablate:
        for pair in bundle.get("interaction_pairs", []):
            if set(pair) <= observed:
                f["pair:" + "|".join(pair)] = 1.0
    for key in ["c0", "c1"]:
        if key not in ablate and context.get(key) is not None:
            f[key + ":" + context[key]] = 1.0
    return f


def _scores(answers, context, bundle, model, ablate=()):
    if not isinstance(model, str) or model not in {"B0", "B1", "B2", "M1"}:
        raise ValueError("Unknown model")
    out = {
        c: {
            "candidate_id": c,
            "base_component": bundle["priors"].get(c, 0),
            "context_component": 0.0,
            "direct_answer_component": 0.0,
            "semantic_component": 0.0,
            "interaction_component": 0.0,
            "evidence_ids": list(bundle.get("evidence_by_candidate", {}).get(c, [])),
            "directly_expressed": False,
        }
        for c in bundle["vocabulary"]
    }
    for c, row in out.items():
        for key in ["c0", "c1"]:
            if key not in ablate and context.get(key):
                row["context_component"] += (
                    bundle.get("context_adjustments", {})
                    .get(key + ":" + context[key], {})
                    .get(c, 0)
                )
    if model == "B0":
        return _finish_scores(out)
    interpreted = [interpret_answer(a, bundle) for a in answers]
    for a in interpreted:
        if a["state"] in {"UNSURE", "SKIP"}:
            continue
        relations = a["relations"]
        seen = set()
        broad_all = a["question_id"] == "q.direction" and set(
            a["selected_option_ids"]
        ) == set(a["shown_option_ids"])
        n = max(len({r["candidate_id"] for r in relations}), 1)
        for r in relations:
            c = r["candidate_id"]
            row = out[c]
            key = (r["evidence_id"], c)
            if model != "B1" and c in seen:
                continue
            seen.add(c)
            if model == "B1":
                # Frozen legacy effect coefficients with train-only base statistics.
                delta = 3.0 if r["polarity"] > 0 else -1.25
                row["direct_answer_component"] += delta
            elif r["relation_type"] == "DIRECT_OBSERVATION":
                row["direct_answer_component"] += (
                    3.0 if r["polarity"] > 0 else -1.25
                ) / n
            elif not broad_all and "semantic" not in ablate:
                row["semantic_component"] += 1.25 * r["polarity"] / n
            row["directly_expressed"] |= (
                r["polarity"] > 0 and r["relation_type"] == "DIRECT_OBSERVATION"
            )
            row["evidence_ids"].append(r["evidence_id"])
    if model == "M1":
        if "model_weights" not in bundle:
            raise ValueError("M1 requires a fitted retained model")
        f = features(answers, context, bundle, ablate)
        for c, row in out.items():
            row["base_component"] = bundle["model_intercepts"].get(
                c, bundle["priors"].get(c, 0)
            )
            row["context_component"] = 0
            for name, w in bundle["model_weights"].get(c, {}).items():
                if name == "observed:" + c:
                    continue  # explicit identity remains a declared answer effect
                value = w * f.get(name, 0)
                field = (
                    "context_component"
                    if name.startswith(("c0:", "c1:"))
                    else (
                        "interaction_component"
                        if name.startswith("pair:")
                        else "semantic_component"
                    )
                )
                row[field] += value
            if f:
                row["evidence_ids"].append("fitted-model:" + bundle["fit_id"])
    return _finish_scores(out)


def _finish_scores(out):
    rows = []
    for row in out.values():
        row["score"] = sum(
            row[k]
            for k in [
                "base_component",
                "context_component",
                "direct_answer_component",
                "semantic_component",
                "interaction_component",
            ]
        )
        row["evidence_ids"] = sorted(set(row["evidence_ids"]))
        rows.append(row)
    rows.sort(key=lambda r: (-r["score"], r["candidate_id"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def build_candidate_state(context, bundle, model="B2"):
    validated = validate_context(context)
    return {
        "context": validated,
        "model": model,
        "answers": [],
        "candidates": _scores([], validated, bundle, model, ("c0", "c1")),
        "updates": [],
        "bundle_id": bundle["bundle_id"],
        "context_effect_status": "MASKED_NO_VALIDATED_SOURCE_TO_PRODUCT_C0_C1_MAPPING",
    }


def update_candidate_state(state, answer, bundle):
    validate_context(state["context"])
    if state["bundle_id"] != bundle["bundle_id"]:
        raise ValueError("Candidate state belongs to a different bundle")
    a = interpret_answer(answer, bundle)
    canonical = {
        k: a[k]
        for k in ["question_id", "shown_option_ids", "selected_option_ids", "state"]
    }
    answers = copy.deepcopy(state["answers"])
    index = next(
        (i for i, x in enumerate(answers) if x["question_id"] == a["question_id"]), None
    )
    if index is not None and answers[index] == canonical:
        return copy.deepcopy(state)
    reason = "REPLACE_PREVIOUS_ANSWER" if index is not None else "ADD_NEW_ANSWER"
    if index is None:
        if len(answers) >= 5:
            raise ValueError("At most five distinct questions")
        answers.append(canonical)
    else:
        answers[index] = canonical
    old = {r["candidate_id"]: r for r in state["candidates"]}
    ranked = _scores(answers, state["context"], bundle, state["model"], ("c0", "c1"))
    updates = []
    for r in ranked:
        c = r["candidate_id"]
        before = old[c]
        updates.append(
            {
                "question_id": a["question_id"],
                "shown_option_ids": a["shown_option_ids"],
                "selected_option_ids": a["selected_option_ids"],
                "candidate_id": c,
                "score_before": before["score"],
                "base_component": r["base_component"],
                "context_component": r["context_component"],
                "direct_answer_component": r["direct_answer_component"],
                "semantic_component": r["semantic_component"],
                "interaction_component": r["interaction_component"],
                "score_after": r["score"],
                "rank_before": before["rank"],
                "rank_after": r["rank"],
                "evidence_ids": r["evidence_ids"],
                "update_reason": reason + "; FULL_RECOMPUTE_NO_ACCUMULATION",
            }
        )
    return {
        **state,
        "answers": answers,
        "candidates": ranked,
        "updates": state["updates"] + [updates],
    }


def rank_candidates(state, bundle, ablate=()):
    return _scores(
        state["answers"],
        state["context"],
        bundle,
        state["model"],
        tuple(set(ablate) | {"c0", "c1"}),
    )


def _entropy(rows, vocabulary):
    counts = Counter(c for r in rows for c in r["targets"] if c in vocabulary)
    total = sum(counts.values())
    return (
        -sum((v / total) * math.log2(v / total) for v in counts.values())
        if total
        else 0
    )


def select_next_question(state, bundle):
    if len(state["answers"]) >= 5:
        return {"action": "STOP", "reason": "QUESTION_BUDGET", "question_id": None}
    observed, _, _ = observations(state["answers"], bundle)
    all_rows = bundle.get("train_records", [])
    conditioned = [r for r in all_rows if observed <= set(r["targets"])]
    if len({r["group_id"] for r in conditioned}) < 5:
        conditioned = all_rows
    used = {interpret_answer(a, bundle)["semantic_key"] for a in state["answers"]}
    entropy = _entropy(conditioned, bundle["vocabulary"])
    choices = []
    for q in question_bank(bundle["vocabulary"]):
        if q["semantic_key"] in used:
            continue
        partitions = defaultdict(list)
        for r in conditioned:
            pattern = tuple(
                o["option_id"]
                for o in q["options"]
                if set(o["concept_ids"]) & set(r["targets"])
            )
            partitions[pattern].append(r)
        valid = {
            k: v for k, v in partitions.items() if len({r["group_id"] for r in v}) >= 2
        }
        if len(valid) < 2:
            continue
        expected = sum(
            len(v) / max(len(conditioned), 1) * _entropy(v, bundle["vocabulary"])
            for v in partitions.values()
        )
        gain = entropy - expected
        if gain <= bundle.get("question_gain_threshold", 0.01):
            continue
        outcomes = set()
        for pattern in valid:
            a = {
                "question_id": q["question_id"],
                "shown_option_ids": [o["option_id"] for o in q["options"]],
                "selected_option_ids": list(pattern),
                "state": "SELECTED" if pattern else "UNSURE",
            }
            candidate = update_candidate_state(state, a, bundle)
            outcomes.add(tuple(r["candidate_id"] for r in candidate["candidates"][:5]))
        if len(outcomes) < 2:
            continue
        choices.append(
            {
                "question_id": q["question_id"],
                "estimated_gain_bits": gain,
                "supported_response_patterns": len(valid),
                "source_group_count": len({r["group_id"] for r in conditioned}),
                "question": q,
            }
        )
    if not choices:
        return {
            "action": "STOP",
            "reason": "NO_SUPPORTED_MATERIAL_QUESTION",
            "question_id": None,
        }
    choices.sort(key=lambda x: (-x["estimated_gain_bits"], x["question_id"]))
    return {
        "action": "ASK",
        "reason": "TRAIN_RECORD_PROXY_INFORMATION_GAIN_NOT_USER_VALIDATED",
        **choices[0],
    }


def finalize_result(state, bundle):
    ranked = rank_candidates(state, bundle)
    vocabulary = set(bundle["vocabulary"])
    eligible = [
        r
        for r in ranked
        if r["candidate_id"] in vocabulary
        and bundle.get("candidate_rights", {}).get(r["candidate_id"])
        == "ADMITTED_SOURCE_CONDITIONS_SATISFIED"
    ]
    return {
        "main": eligible[:5],
        "secondary": eligible[5:8],
        "next": select_next_question(state, bundle),
        "answer_count": len(state["answers"]),
        "interpretation": "Candidate references; fitted results are RECORD_RECOVERY_PROXY only, not sensory accuracy or calibrated probabilities",
        "abstention": not eligible,
    }


def run(payload, bundle):
    if (
        not isinstance(payload, dict)
        or set(payload) - {"context", "answers", "model"}
        or "context" not in payload
    ):
        raise ValueError("Unknown input fields or missing context")
    answers = payload.get("answers", [])
    if not isinstance(answers, list):
        raise ValueError("answers must be a list")
    state = build_candidate_state(
        payload["context"], bundle, payload.get("model", "B2")
    )
    for answer in answers:
        state = update_candidate_state(state, answer, bundle)
    return {"final_result": finalize_result(state, bundle), "candidate_state": state}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-file", type=Path, required=True)
    p.add_argument("--input", type=Path)
    a = p.parse_args()
    import sys

    payload = json.loads(a.input.read_text() if a.input else sys.stdin.read())
    bundle = json.loads(a.model_file.read_text())
    try:
        print(
            json.dumps(
                run(payload, bundle), sort_keys=True, ensure_ascii=False, indent=2
            )
        )
    except ValueError as e:
        print(json.dumps({"error": "INPUT_VALIDATION_ERROR", "message": str(e)}))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
