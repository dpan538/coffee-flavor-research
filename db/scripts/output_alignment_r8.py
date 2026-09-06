"""Frozen-state -> actual R4 return -> R8 fine-reference output evaluation.

No model fitting, question selection, output-policy change or source acquisition.
Raw IDs, targets, states and returns are retained only in owner storage.
"""

from __future__ import annotations
import argparse
import copy
from collections import Counter, defaultdict
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment
import alignment_metrics_r3 as legacy
import flavor_conditioning_r4 as runtime
import flavor_m2_r1 as r1
import train_conditioning_r4 as assembly
from train_coordination_r2 import expert_training_groups
from train_supervision_r5 import CANDIDATES, paired
from information_supervision_r5 import selected
from r8_output_alignment_helper import returned_views, score_returned_panel
from acquire_supervision_r5 import save

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r8"
VERSION = "m2-r8.returned-output-evaluation.v1"
LAYERS = {"L": 5, "M": 5, "U": 8, "P": 8}
FINAL_ARTIFACTS = Path("revisions/r8/verified")


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def digest(v):
    return hashlib.sha256(
        json.dumps(v, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def matching(predicted, targets, k):
    return legacy.maximum_matching(predicted, targets, k, mode="parent")


def measure(ids, targets, k):
    return score_returned_panel(
        ids, targets, k=k, fine_universe=CANDIDATES, maximum_matching=matching
    )


def verify_inputs(owner):
    c = read(PUBLIC / "evaluation_contract.json")
    if c["version"] != VERSION or c["fit_count"] != 0:
        raise ValueError("R8_CONTRACT_MISMATCH")
    for name, expected in c["input_hashes"].items():
        p = owner / name
        if not p.exists():
            raise FileNotFoundError("MISSING_ARTIFACT:" + name)
        if sha(p) != expected:
            raise ValueError("FROZEN_ARTIFACT_HASH_CHANGED:" + name)
    for name, expected in c["frozen_code_hashes"].items():
        if sha(ROOT / "db/scripts" / name) != expected:
            raise ValueError("FROZEN_RUNTIME_OR_METRIC_CHANGED:" + name)
    for name, expected in c["r7_public_hashes"].items():
        if sha(PUBLIC.parent / "r7" / name) != expected:
            raise ValueError("R7_RESULT_CHANGED:" + name)
    if len(CANDIDATES) != 56 or any(not c.startswith("sensory.") for c in CANDIDATES):
        raise ValueError("FROZEN_EVALUATION_UNIVERSE_CHANGED")
    return c


def pair_index(cells):
    indices = {}
    for policy in ("C00", "C01"):
        index = {r["record_id"]: r for r in cells[policy]}
        if len(index) != len(cells[policy]):
            raise ValueError("DUPLICATE_RECORD_ID")
        indices[policy] = index
    if set(indices["C00"]) != set(indices["C01"]):
        raise ValueError("PAIRED_RECORD_IDS_DIFFER")
    for identity, left in indices["C00"].items():
        right = indices["C01"][identity]
        for key in ("group_id", "fold", "full_T", "hidden_T", "evaluation_universe"):
            if left[key] != right[key]:
                raise ValueError("PAIRED_FIXED_REFERENCE_MISMATCH:" + key)
    return indices


def directions(ids):
    out = set()
    for c in ids:
        if c.startswith("attribute."):
            out.add(c.split(".", 1)[1])
        else:
            out.update(r1.PARENTS.get(c, []))
    return out


def return_audit(final, bundle):
    views = returned_views(final)
    known = set(bundle["r1_expert"]["candidate_vocabulary"])
    # The actual R4 generated rows must also identify their candidate class.
    for row in final["main"] + final["secondary"]:
        if row["candidate_id"] not in known:
            raise ValueError("UNREGISTERED_RETURNED_ID")
    for ids in (views["main"], views["secondary"], views["proposed_pool"]):
        if ids is not None and any(c not in known for c in ids):
            raise ValueError("UNREGISTERED_RETURNED_ID")
    if views["stage"] != "PRELIMINARY_RESULT":
        raise ValueError("PRE_FEEDBACK_ENDPOINT_REQUIRED")
    pool = views["proposed_pool"]
    if pool is not None:
        exposure = final["exposure"]
        if exposure["generation_version"] != bundle["bundle_id"]:
            raise ValueError("EXPOSURE_MODEL_VERSION_MISMATCH")
        valid = 3 <= len(pool) <= 8 and len(set(pool)) == len(pool)
        size_eligible = 3 <= len(pool) <= 8
        if exposure["eligible_for_final_comparison"] != size_eligible:
            raise ValueError("EXPOSURE_ELIGIBILITY_FLAG_MISMATCH")
    else:
        valid = None
    return views, valid


def witness(ids, targets):
    """One deterministic optimum for attribution audit, not unique causal credit."""
    eligible = list(dict.fromkeys(c for c in ids if c in CANDIDATES))
    target = sorted(c for c, w in targets.items() if w > 0)
    if not eligible or not target:
        return []
    scores = np.array(
        [[legacy.similarity(c, t, "parent") for t in target] for c in eligible]
    )
    ri, ti = linear_sum_assignment(-scores)
    result = [
        {"candidate": eligible[i], "target": target[j], "weight": float(scores[i, j])}
        for i, j in zip(ri, ti, strict=True)
        if scores[i, j] > 0
    ]
    if abs(sum(x["weight"] for x in result) - matching(eligible, target, 5)) > 1e-12:
        raise ValueError("MATCHING_WITNESS_DISAGREES")
    return result


def outside_diagnostic(legacy_ids, returned, targets):
    if returned is None:
        return None
    targets = {c: w for c, w in targets.items() if w > 0}
    outside = [c for c in legacy_ids if c not in set(returned)]
    full_match = matching(legacy_ids, list(targets), 5)
    kept_match = matching(
        [c for c in legacy_ids if c in set(returned)], list(targets), 5
    )
    edges = witness(legacy_ids, targets)
    return {
        "outside_ids": outside,
        "outside_exact_target_hits": sorted(set(outside) & set(targets)),
        "necessary_matching_loss_without_replacement": full_match - kept_match,
        "one_optimal_witness_outside_edges": [
            e for e in edges if e["candidate"] in outside
        ],
        "witness_scope": "One deterministic optimum; tie-equivalent assignments may differ. Marginal loss is not sum of independent interface matches.",
    }


def extract(row, bundle, model_sha):
    if row.get("state") is None:
        raise FileNotFoundError("MISSING_ARTIFACT:complete endpoint state required")
    if row["group_id"] in expert_training_groups(bundle["r1_expert"]):
        raise ValueError("HELD_COFFEE_IN_SCORER_TRAINING")
    if row["state"]["variant"] != "A0":
        raise ValueError("FROZEN_OUTER_A0_REQUIRED")
    if row["state"]["base_state"].get("final_comparison"):
        raise ValueError("FUTURE_FINAL_FEEDBACK_PRESENT")
    before, model_before = digest(row), digest(bundle)
    original_state = row["state"]
    if row["ranking"] != original_state["candidate_scores"]:
        raise ValueError("ARCHIVED_RANKING_STATE_DISAGREES")
    final = runtime.finalize_result(copy.deepcopy(original_state), bundle)
    if digest(row) != before or digest(bundle) != model_before:
        raise ValueError("FINALIZER_MUTATED_FROZEN_INPUT")
    views, valid = return_audit(final, bundle)
    if sorted(row["evaluation_universe"]) != CANDIDATES:
        raise ValueError("ARCHIVED_TARGET_UNIVERSE_MISMATCH")
    L = legacy.evaluate(row["ranking"], row["full_T"], CANDIDATES)
    for key in ("raw_gap", "ndcg", "recall", "M"):
        if L[key] != row["metrics"][key]:
            raise ValueError("LEGACY_SCORE_CHANGED:" + key)
    lids = list(
        dict.fromkeys(
            r["candidate_id"] for r in row["ranking"] if r["candidate_id"] in CANDIDATES
        )
    )[:5]
    ids = {
        "L": lids,
        "M": list(views["main"]),
        "U": list(views["main_plus_secondary"]),
        "P": None if views["proposed_pool"] is None else list(views["proposed_pool"]),
    }
    panels = {
        layer: None if value is None else measure(value, row["full_T"], LAYERS[layer])
        for layer, value in ids.items()
    }
    for key, oldkey in [
        ("raw_gap", "raw_gap"),
        ("recall", "recall"),
        ("ndcg_actual_positions", "ndcg"),
    ]:
        if panels["L"][key] != L[oldkey]:
            raise ValueError("LEGACY_HELPER_PARITY_FAILED")
    selected_fine = [c for c in selected(original_state) if c.startswith("sensory.")]
    generated = set(row["frozen_A0_generation_universe"])
    t = {c for c, w in row["full_T"].items() if w > 0}
    target_dirs = directions(t)
    faithful = {
        "selected_fine_ids": selected_fine,
        "generated_ids": sorted(set(selected_fine) & generated),
        "not_generated_ids": sorted(set(selected_fine) - generated),
    }
    for layer in ("M", "U", "P"):
        faithful[layer] = (
            None if ids[layer] is None else sorted(set(selected_fine) & set(ids[layer]))
        )
    faithful.update(
        selected_exceeds_main_capacity=len(selected_fine) > 5,
        generated_selected_exceeds_main_capacity=len(set(selected_fine) & generated)
        > 5,
        selected_exceeds_pool_capacity=len(selected_fine) > 8,
    )
    original_ids = [r["candidate_id"] for r in row["ranking"]]
    transitions = []
    for c in lids:
        rank = original_ids.index(c)
        transitions.append(
            {
                "candidate_id": c,
                "original_mixed_position": rank + 1,
                "preceding_broad": sum(
                    x.startswith(("attribute.", "broad.")) for x in original_ids[:rank]
                ),
                "preceding_fine": sum(
                    x.startswith("sensory.") for x in original_ids[:rank]
                ),
                "in_main": c in ids["M"],
                "in_U": c in ids["U"],
                "in_P": None if ids["P"] is None else c in ids["P"],
                "exact_T": c in t,
            }
        )
    return {
        "record_id": row["record_id"],
        "group_id": row["group_id"],
        "policy": row["cell"],
        "outer_fold": row["fold"],
        "model_sha256": model_sha,
        "bundle_id": bundle["bundle_id"],
        "input_row_sha256": before,
        "state_sha256": digest(original_state),
        "returned_state_sha256": digest(final["state"]),
        "T_sha256": digest(row["full_T"]),
        "hidden_T_sha256": digest(row["hidden_T"]),
        "full_T": row["full_T"],
        "hidden_T": row["hidden_T"],
        "questions": row["questions"],
        "answers": original_state["base_state"]["answers_by_question"],
        "original_ranking": row["ranking"],
        "actual_return": final,
        "stage": views["stage"],
        "ids": ids,
        "returned_layout": {
            layer: (
                None
                if values is None
                else [
                    {"candidate_id": c, "type": c.split(".", 1)[0], "position": i + 1}
                    for i, c in enumerate(values)
                ]
            )
            for layer, values in ids.items()
        },
        "panels": panels,
        "hidden_panels": {
            layer: (
                None
                if value is None
                else measure(value, row["hidden_T"], LAYERS[layer])
            )
            for layer, value in ids.items()
        },
        "pool_valid": valid,
        "pool_matches_U_order": views["pool_matches_combined"],
        "pool_matches_U_set": (
            None if ids["P"] is None else set(ids["P"]) == set(ids["U"])
        ),
        "finalizer_ranking_changed": original_state["candidate_scores"]
        != final["state"]["candidate_scores"],
        "secondary_exact_target_additions": sorted(
            (set(views["secondary"]) & t) - set(ids["M"])
        ),
        "faithfulness": faithful,
        "direction_coverage": {
            layer: (
                None
                if value is None or not target_dirs
                else len(directions(value) & target_dirs) / len(target_dirs)
            )
            for layer, value in ids.items()
        },
        "outside_U": outside_diagnostic(lids, ids["U"], row["full_T"]),
        "outside_P": outside_diagnostic(lids, ids["P"], row["full_T"]),
        "L_M_set_differs": set(lids) != set(ids["M"]),
        "transitions": transitions,
        "costs": row["costs"],
        "failure": row["failure"]
        or ("REPRODUCIBLE_EMPTY_MAIN" if not ids["M"] else None),
        "contract_issues": (
            ["RETURNED_POOL_ABSENT"]
            if ids["P"] is None
            else ["INVALID_PROPOSED_POOL"] if valid is False else []
        )
        + [
            "DUPLICATE_IDS_" + l
            for l, panel in panels.items()
            if panel is not None and panel["duplicate_output_ids"]
        ],
        "missing_artifact": False,
        "input_unchanged": True,
    }


def macro(rows, fn):
    groups = defaultdict(list)
    for row in rows:
        value = fn(row)
        if value is not None:
            groups[row["group_id"]].append(value)
    return float(np.mean([np.mean(v) for v in groups.values()])) if groups else None


def sign(delta):
    return "IMPROVEMENT" if delta < -1e-12 else "REGRESSION" if delta > 1e-12 else "TIE"


def comparisons(rows, layer, hidden=False):
    field = "hidden_panels" if hidden else "panels"
    sides = {
        p: [
            {
                "record_id": r["record_id"],
                "group_id": r["group_id"],
                **({} if r[field][layer] is None else r[field][layer]),
            }
            for r in rows
            if r["policy"] == p
        ]
        for p in ("C00", "C01")
    }
    stats = {
        k: paired(sides["C00"], sides["C01"], k)
        for k in ("raw_gap", "recall", "ndcg_actual_positions")
    }
    right = {r["record_id"]: r for r in sides["C01"]}
    for key in stats:
        pairs = [
            (l, right[l["record_id"]])
            for l in sides["C00"]
            if l.get(key) is not None and right[l["record_id"]].get(key) is not None
        ]
        stats[key].update(
            paired_records=len(pairs),
            paired_C00_mean=macro([l for l, r in pairs], lambda row: row[key]),
            paired_C01_mean=macro([r for l, r in pairs], lambda row: row[key]),
        )
    group = defaultdict(list)
    outcomes = Counter()
    for l in sides["C00"]:
        r = right[l["record_id"]]
        if l.get("raw_gap") is None or r.get("raw_gap") is None:
            outcomes["NOT_EVALUABLE"] += 1
            continue
        d = r["raw_gap"] - l["raw_gap"]
        group[l["group_id"]].append(d)
        outcomes[sign(d)] += 1
    group_values = {g: float(np.mean(v)) for g, v in group.items()}
    return {
        "metrics": stats,
        "record_outcomes": dict(outcomes),
        "group_outcomes": dict(Counter(sign(d) for d in group_values.values())),
        "not_evaluable_groups": len({r["group_id"] for r in sides["C00"]})
        - len(group_values),
    }, group_values


def aggregate(rows):
    result = {
        "version": VERSION,
        "scope": "REPEATEDLY_VIEWED_DEVELOPMENT_RETURNED_OUTPUT_COMPARISON_NOT_NEW_CONFIRMATION",
        "fit_count": 0,
        "policies": {},
        "paired": {},
        "hidden_paired": {},
        "default": "B2_UNCHANGED_CHECK_OFF",
        "real_user_feedback": "NOT_EVALUATED",
        "real_time": "NOT_EVALUATED",
    }
    for policy in ("C00", "C01"):
        rs = [r for r in rows if r["policy"] == policy]
        summaries = {}
        for layer, k in LAYERS.items():
            summaries[layer] = {
                key: macro(
                    rs,
                    lambda r: (
                        r["panels"][layer][key]
                        if r["panels"][layer] is not None
                        else None
                    ),
                )
                for key in (
                    "raw_gap",
                    "recall",
                    "ndcg_actual_positions",
                    "returned_slots_scored",
                    "fine_unique_count",
                    "non_fine_or_outside_universe_slots",
                )
            }
            summaries[layer].update(
                mean_scope="Available-case coffee macro; full-reference effects exclude empty T; layout averages retain all output records. Paired means and denominators are separately reported.",
                evaluable_coffee_groups=len(
                    {
                        r["group_id"]
                        for r in rs
                        if r["panels"][layer] is not None
                        and r["panels"][layer]["evaluable"]
                    }
                ),
                k=k,
                records=len(rs),
                coffee_groups=len({r["group_id"] for r in rs}),
                evaluable_records=sum(
                    r["panels"][layer] is not None and r["panels"][layer]["evaluable"]
                    for r in rs
                ),
                empty_T_records=sum(not r["panels"]["L"]["evaluable"] for r in rs),
                returned_panel_absent_records=sum(
                    r["panels"][layer] is None for r in rs
                ),
                actual_empty_output_records=sum(r["ids"][layer] == [] for r in rs),
                duplicate_records=sum(
                    bool(r["panels"][layer]["duplicate_output_ids"])
                    for r in rs
                    if r["panels"][layer] is not None
                ),
                candidate_count_histogram=dict(
                    Counter(
                        len(r["ids"][layer]) for r in rs if r["ids"][layer] is not None
                    )
                ),
                direction_coverage=macro(rs, lambda r: r["direction_coverage"][layer]),
            )
        diag = {}
        for field in ("outside_U", "outside_P"):
            valid = [r[field] for r in rs if r[field] is not None]
            diag[field] = {
                "records_with_outside_L_candidates": sum(
                    bool(x["outside_ids"]) for x in valid
                ),
                "outside_candidate_occurrences": sum(
                    len(x["outside_ids"]) for x in valid
                ),
                "records_with_outside_exact_T_hits": sum(
                    bool(x["outside_exact_target_hits"]) for x in valid
                ),
                "outside_exact_hit_occurrences": sum(
                    len(x["outside_exact_target_hits"]) for x in valid
                ),
                "records_with_necessary_matching_loss": sum(
                    x["necessary_matching_loss_without_replacement"] > 1e-12
                    for x in valid
                ),
                "sum_necessary_matching_loss": sum(
                    x["necessary_matching_loss_without_replacement"] for x in valid
                ),
                "records_with_one_optimum_outside_match": sum(
                    bool(x["one_optimal_witness_outside_edges"]) for x in valid
                ),
                "sum_one_optimum_outside_match_weight": sum(
                    e["weight"]
                    for x in valid
                    for e in x["one_optimal_witness_outside_edges"]
                ),
            }
        faith = {
            "selected_occurrences": sum(
                len(r["faithfulness"]["selected_fine_ids"]) for r in rs
            ),
            "generated_occurrences": sum(
                len(r["faithfulness"]["generated_ids"]) for r in rs
            ),
            "not_generated_occurrences": sum(
                len(r["faithfulness"]["not_generated_ids"]) for r in rs
            ),
        }
        for layer in ("M", "U", "P"):
            faith[layer + "_retained_occurrences"] = sum(
                len(r["faithfulness"][layer])
                for r in rs
                if r["faithfulness"][layer] is not None
            )
        for key in (
            "selected_exceeds_main_capacity",
            "generated_selected_exceeds_main_capacity",
            "selected_exceeds_pool_capacity",
        ):
            faith[key + "_records"] = sum(r["faithfulness"][key] for r in rs)
        result["policies"][policy] = {
            "layers": summaries,
            "diagnostics": diag,
            "faithfulness": faith,
            "L_M_set_different_records": sum(r["L_M_set_differs"] for r in rs),
            "finalizer_ranking_changed_records": sum(
                r["finalizer_ranking_changed"] for r in rs
            ),
            "U_P_order_equal_records": sum(
                r["pool_matches_U_order"] is True for r in rs
            ),
            "U_P_set_equal_records": sum(r["pool_matches_U_set"] is True for r in rs),
            "valid_proposed_pool_records": sum(r["pool_valid"] is True for r in rs),
            "secondary_adds_exact_T_records": sum(
                bool(r["secondary_exact_target_additions"]) for r in rs
            ),
            "secondary_new_exact_hit_occurrences": sum(
                len(r["secondary_exact_target_additions"]) for r in rs
            ),
            "failures": sum(bool(r["failure"]) for r in rs),
            "missing_artifacts": sum(r["missing_artifact"] for r in rs),
            "contract_issue_counts": dict(
                Counter(issue for r in rs for issue in r["contract_issues"])
            ),
            "question_costs": dict(
                Counter(r["costs"]["ordinary_questions"] for r in rs)
            ),
            "option_costs": dict(Counter(r["costs"]["ordinary_options"] for r in rs)),
            "actual_final_exposures": sum(
                r["costs"]["actual_final_exposure"] for r in rs
            ),
        }
    groups = {}
    for layer in LAYERS:
        result["paired"][layer], groups[layer] = comparisons(rows, layer)
        result["hidden_paired"][layer], _ = comparisons(rows, layer, True)
    result["interpretation_limits"] = [
        "U/P equal outputs are two interface roles, not independent successes.",
        "Broad slots receive zero fine-reference credit but may have unmeasured user value.",
        "All intervals are descriptive old-development coffee bootstrap, not new confirmation or participant-independent uncertainty.",
        "Matching credit is one-to-one within a panel; never add layers or secondary matching scores.",
    ]
    transfer = {}
    for target_layer in ("M", "P"):
        counts = Counter()
        for g, legacy_delta in groups["L"].items():
            if legacy_delta < -1e-12:
                counts[
                    (
                        sign(groups[target_layer][g])
                        if g in groups[target_layer]
                        else "NOT_EVALUABLE"
                    )
                ] += 1
        transfer[target_layer] = {
            "among_legacy_improved_coffee_groups": dict(counts),
            "legacy_improved_groups": sum(d < -1e-12 for d in groups["L"].values()),
            "scope": "Same groups, original L improvement versus separately evaluated actual-output change; no cross-budget pooled effect",
        }
    result["gain_transfer"] = transfer
    return result, groups


def cases(rows):
    idx = {(r["policy"], r["record_id"]): r for r in rows}
    details = []
    buckets = defaultdict(list)
    for r in rows:
        if r["policy"] != "C00":
            continue
        other = idx[("C01", r["record_id"])]
        if not r["panels"]["L"]["evaluable"]:
            continue
        delta = {
            l: (
                other["panels"][l]["raw_gap"] - r["panels"][l]["raw_gap"]
                if other["panels"][l] is not None and r["panels"][l] is not None
                else None
            )
            for l in LAYERS
        }
        tags = []
        if delta["L"] < -1e-12 and delta["M"] < -1e-12:
            tags.append("GAIN_RETAINED")
        if delta["L"] < -1e-12 and delta["M"] >= -1e-12:
            tags.append("LEGACY_GAIN_LOST")
        if delta["P"] is not None and delta["P"] < -1e-12 and delta["M"] >= -1e-12:
            tags.append("POOL_GAIN_WITHOUT_MAIN")
        if delta["M"] > 1e-12 or (delta["P"] is not None and delta["P"] > 1e-12):
            tags.append("REGRESSION")
        if not tags:
            tags.append("TIE_OR_MIXED")
        for tag in tags:
            buckets[tag].append(
                {
                    "record_id": r["record_id"],
                    "group_id": r["group_id"],
                    "category": tag,
                    "all_categories": tags,
                    "delta": delta,
                    "C00": r,
                    "C01": other,
                }
            )
    for values in buckets.values():
        values.sort(key=lambda x: digest(x["record_id"]))
    while len(details) < 8:
        progressed = False
        for key in (
            "GAIN_RETAINED",
            "LEGACY_GAIN_LOST",
            "POOL_GAIN_WITHOUT_MAIN",
            "REGRESSION",
            "TIE_OR_MIXED",
        ):
            while buckets[key] and buckets[key][0]["record_id"] in {
                d["record_id"] for d in details
            }:
                buckets[key].pop(0)
            if buckets[key] and len(details) < 8:
                details.append(buckets[key].pop(0))
                progressed = True
        if not progressed:
            break
    return details


def execute(owner, checkpoint=False):
    verify_inputs(owner)
    data = read(owner / "revisions/r6/matrix_cases.private.json")
    indices = pair_index(data)
    bundles = {
        i: assembly.model_bundle(
            read(owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{i}.model.json")
        )
        for i in range(3)
    }
    ids = sorted(indices["C00"], key=digest)
    if checkpoint:
        ids = ids[:3]
    rows = []
    for p in ("C00", "C01"):
        for identity in ids:
            row = indices[p][identity]
            rows.append(
                extract(
                    row,
                    bundles[row["fold"]],
                    sha(
                        owner
                        / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{row['fold']}.model.json"
                    ),
                )
            )
    verify_inputs(owner)
    output = owner / FINAL_ARTIFACTS
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o700)
    if checkpoint:
        receipt = save(
            output / "checkpoint1.private.json",
            {
                "created_utc": now(),
                "records": len(rows),
                "extraction": "actual R4 finalizer from original held states",
                "unchanged_inputs": all(r["input_unchanged"] for r in rows),
                "fit_count": 0,
                "rows": rows,
            },
        )
        print(
            json.dumps(
                {
                    "checkpoint1": "PASS",
                    "case_policy_returns": len(rows),
                    "sha256": receipt["sha256"],
                    "fit_count": 0,
                }
            )
        )
        return
    summary, groups = aggregate(rows)
    details = cases(rows)
    artifact = save(output / "actual_returns.private.json", rows)
    detail = save(output / "chain_examples.private.json", details)
    group = save(output / "paired_group_deltas.private.json", groups)
    summary["detail_categories"] = dict(Counter(r["category"] for r in details))
    summary["contract_sha256"] = sha(PUBLIC / "evaluation_contract.json")
    summary["private_artifact_hashes"] = {
        x["filename"]: x["sha256"] for x in (artifact, detail, group)
    }
    save(output / "aggregate_results.private.json", summary)
    receipt = {
        "created_utc": now(),
        "version": VERSION,
        "fit_count": 0,
        "contract_sha256": summary["contract_sha256"],
        "code_hashes": {
            n: sha(ROOT / "db/scripts" / n)
            for n in ("output_alignment_r8.py", "r8_output_alignment_helper.py")
        },
        "artifacts": summary["private_artifact_hashes"],
        "summary_sha256": sha(output / "aggregate_results.private.json"),
        "actual_returns": len(rows),
        "original_finalizer_calls": len(rows),
        "question_reselection_count": 0,
        "input_hashes_verified_before_after": True,
    }
    save(output / "execution_receipt.private.json", receipt)
    print(
        json.dumps(
            {
                "status": "PASS",
                "returns": len(rows),
                "layers": {
                    l: summary["paired"][l]["metrics"]["raw_gap"] for l in LAYERS
                },
                "private_receipt_sha256": sha(
                    output / "execution_receipt.private.json"
                ),
            },
            indent=2,
        )
    )


def replay(owner):
    verify_inputs(owner)
    p = owner / FINAL_ARTIFACTS
    receipt = read(p / "execution_receipt.private.json")
    if receipt["contract_sha256"] != sha(PUBLIC / "evaluation_contract.json"):
        raise ValueError("CONTRACT_CHANGED")
    for n, h in receipt["code_hashes"].items():
        if sha(ROOT / "db/scripts" / n) != h:
            raise ValueError("R8_CODE_CHANGED")
    for n, h in receipt["artifacts"].items():
        if sha(p / n) != h:
            raise ValueError("SEALED_OUTPUT_CHANGED")
    if sha(p / "aggregate_results.private.json") != receipt["summary_sha256"]:
        raise ValueError("SEALED_SUMMARY_CHANGED")
    rows = read(p / "actual_returns.private.json")
    original = read(owner / "revisions/r6/matrix_cases.private.json")
    indices = pair_index(original)
    bundles = {
        i: assembly.model_bundle(
            read(owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{i}.model.json")
        )
        for i in range(3)
    }
    rebuilt = []
    for row in rows:
        out = extract(
            indices[row["policy"]][row["record_id"]],
            bundles[row["outer_fold"]],
            row["model_sha256"],
        )
        if out != row:
            raise ValueError("RETURN_OR_METRIC_REPLAY_MISMATCH")
        rebuilt.append(out)
    summary, groups = aggregate(rebuilt)
    saved = read(p / "aggregate_results.private.json")
    for key, value in summary.items():
        if json.loads(json.dumps(value)) != saved[key]:
            raise ValueError("AGGREGATE_REPLAY_MISMATCH:" + key)
    if groups != read(p / "paired_group_deltas.private.json"):
        raise ValueError("GROUP_REPLAY_MISMATCH")
    verify_inputs(owner)
    print(
        json.dumps(
            {
                "status": "PASS",
                "operation": "original_held_state_to_actual_return_and_new_metrics_replay",
                "returns": len(rows),
                "fit_count": 0,
                "question_reselection_count": 0,
            }
        )
    )


def synthetic_cli(owner):
    import candidate_c01_r7 as candidate

    bundle_path = owner / "revisions/r7/C01_ALL_DEVELOPMENT.v3.package.json"
    package = candidate.load_bundle(bundle_path)
    original_hash = sha(bundle_path)
    payload = {
        "contract_version": candidate.VERSION,
        "context": {"c0": r1.C0[2], "c1": "medium"},
        "answers": [],
    }
    responses = []
    for step in range(6):
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "db/scripts/candidate_c01_r7.py"),
                "infer",
                "--bundle",
                str(bundle_path),
            ],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
        )
        response = json.loads(completed.stdout)
        responses.append(response)
        if step == 5:
            break
        q = response["next"]["question"]
        answer = {k: q[k] for k in ("slot", "question_id", "axis", "shown_option_ids")}
        answer.update(
            state="SELECTED",
            selected_option_ids=[
                q["shown_option_ids"][step % len(q["shown_option_ids"])]
            ],
        )
        payload["answers"].append(answer)
    views, valid = return_audit(response, package["runtime_bundle"])
    if (
        not valid
        or response["ordinary_options"] != 19
        or response["ordinary_questions"] != 5
        or response["final_comparison"]
    ):
        raise ValueError("SYNTHETIC_CLI_CONTRACT_FAILURE")
    if sha(bundle_path) != original_hash:
        raise ValueError("SYNTHETIC_TEST_MUTATED_PACKAGE")
    p = owner / "revisions/r8"
    p.mkdir(exist_ok=True, parents=True)
    p.chmod(0o700)
    save(p / "synthetic_request.private.json", payload)
    save(p / "synthetic_cli_responses.private.json", responses)
    receipt = {
        "created_utc": now(),
        "status": "PASS",
        "scope": "NEW_LEGAL_SYNTHETIC_JSON_ENGINEERING_ONLY_NOT_COFFEE_EFFECT",
        "cli_subprocess_calls": 6,
        "full_development_package_used_only_here": True,
        "package_sha256": original_hash,
        "stage": response["stage"],
        "main_count": len(views["main"]),
        "secondary_count": len(views["secondary"]),
        "proposed_pool_count": len(views["proposed_pool"]),
        "pool_equals_U": views["pool_matches_combined"],
        "ordinary_questions": 5,
        "ordinary_options": 19,
        "final_feedback_injected": False,
        "fit_count": 0,
    }
    save(p / "synthetic_cli_receipt.private.json", receipt)
    print(json.dumps(receipt))


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("operation", choices=["checkpoint", "run", "replay", "synthetic"])
    a.add_argument("--owner-dir", type=Path, required=True)
    args = a.parse_args()
    if args.operation == "synthetic":
        synthetic_cli(args.owner_dir)
    elif args.operation == "replay":
        replay(args.owner_dir)
    else:
        execute(args.owner_dir, args.operation == "checkpoint")


if __name__ == "__main__":
    main()
