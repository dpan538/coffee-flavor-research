"""Execute the bounded M2 R1 foundation experiment; retain private artifacts."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import time
import traceback
from collections import defaultdict
from pathlib import Path

import numpy as np

import flavor_foundation_r1 as foundation
import flavor_m2_r1 as backend
import train_m2_r1 as trainer

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r1"
DEFAULT_OWNER = (
    Path.home()
    / "Library/Application Support/Coffee Flavor Research/backend-sequential-model-v2"
)
BASE_NAME = "M2_R1_CONDITIONAL_C0.1"


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".writing")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    temporary.replace(path)


def paired(left, right, metric="ndcg5", resamples=2000, higher_is_better=True):
    lookup = {r["record_id"]: r for r in left}
    groups = defaultdict(list)
    for row in right:
        previous = lookup[row["record_id"]]
        if previous.get(metric) is not None and row.get(metric) is not None:
            groups[row["group_id"]].append(float(row[metric]) - float(previous[metric]))
    values = np.array([np.mean(v) for _, v in sorted(groups.items())])
    if not len(values):
        return {
            "status": "NOT_ESTIMABLE",
            "groups": 0,
            "mean_delta": None,
            "group_bootstrap_95_interval": None,
        }
    rng = np.random.default_rng(trainer.SEED)
    means = values[rng.integers(0, len(values), (resamples, len(values)))].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975]).tolist()
    improvement = low > 0 if higher_is_better else high < 0
    no_improvement = high <= 0 if higher_is_better else low >= 0
    return {
        "status": (
            "PROXY_IMPROVEMENT_SUPPORTED"
            if improvement
            else "NO_IMPROVEMENT" if no_improvement else "INCONCLUSIVE"
        ),
        "improvement_direction": "HIGHER" if higher_is_better else "LOWER",
        "groups": len(values),
        "mean_delta": float(values.mean()),
        "group_bootstrap_95_interval": [low, high],
        "resamples": resamples,
        "basis": "COFFEE_GROUP_PAIRED_DEVELOPMENT_PROXY_NOT_INDEPENDENT_CONFIRMATION",
    }


def summaries(rows):
    result = foundation.summarize(rows)
    result["by_source"] = {
        source: foundation.summarize([r for r in rows if r["source_family"] == source])
        for source in sorted({r["source_family"] for r in rows})
    }
    return result


def resampling_stability(train, held, bundle, models, repeats=3):
    states = {
        r["record_id"]: foundation.trajectory(r, bundle, backend, "V0")[1][-1]
        for r in held
    }
    rows = []
    for repeat in range(repeats):
        subset = [
            r
            for r in train
            if int(
                backend.digest(["foundation-stability", repeat, r["group_id"]])[:8], 16
            )
            % 5
            != 0
        ]
        for name, original in models.items():
            resampled = foundation.fit_foundation(
                subset,
                bundle,
                original["representation"],
                rank=original["rank"],
                alpha=original["alpha"],
            )
            for record in held:
                state = states[record["record_id"]]
                original_profile = foundation.predict_foundation(
                    state, bundle, original
                )
                changed_profile = foundation.predict_foundation(
                    state, bundle, resampled
                )
                delta = np.asarray(
                    list(changed_profile["dimension_values"].values())
                ) - np.asarray(list(original_profile["dimension_values"].values()))
                rows.append(
                    {
                        "record_id": record["record_id"],
                        "group_id": record["group_id"],
                        "source_family": record["source_family"],
                        "model": name,
                        "repeat": repeat,
                        "profile_mean_absolute_change": float(np.mean(abs(delta))),
                        "profile_max_absolute_change": float(np.max(abs(delta))),
                        "lead_changed": max(
                            original_profile["dimension_values"],
                            key=original_profile["dimension_values"].get,
                        )
                        != max(
                            changed_profile["dimension_values"],
                            key=changed_profile["dimension_values"].get,
                        ),
                        "refit_training_groups": len({r["group_id"] for r in subset}),
                    }
                )
    return rows


def aggregate_stability(rows):
    result = {}
    for name in sorted({r["model"] for r in rows}):
        selected = [r for r in rows if r["model"] == name]
        group_values = defaultdict(list)
        for row in selected:
            group_values[row["group_id"]].append(row["profile_mean_absolute_change"])
        result[name] = {
            "coffee_groups": len(group_values),
            "group_mean_absolute_support_change": float(
                np.mean([np.mean(v) for v in group_values.values()])
            ),
            "maximum_absolute_support_change": max(
                r["profile_max_absolute_change"] for r in selected
            ),
            "lead_change_fraction": float(
                np.mean([r["lead_changed"] for r in selected])
            ),
            "interpretation": "THREE_GROUP_SUBSAMPLE_REFITS_OF_FOUNDATION_CONDITIONAL_ON_FIXED_OUTER_R1_AND_CATALOG; STABILITY_IS_NOT_CORRECTNESS",
            "by_source": {
                source: float(
                    np.mean(
                        [
                            r["profile_mean_absolute_change"]
                            for r in selected
                            if r["source_family"] == source
                        ]
                    )
                )
                for source in sorted({r["source_family"] for r in selected})
            },
        }
    return result


def emit_public(report):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    fields = [
        "model",
        "variant",
        "scope",
        "groups",
        "ndcg5",
        "recall5",
        "recall8",
        "attribute_mae",
        "wrong_initial_count",
        "wrong_direction_correction_rate",
        "correct_initial_count",
        "correct_direction_loss_rate",
        "direction_not_identifiable_count",
        "duplicate_evidence_max_gain",
        "real_answer_evaluation",
    ]
    with (PUBLIC / "foundation_checks.tsv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for key, summary in report["summaries"].items():
            name, variant = key.split(":") if ":" in key else ("M2_R1_FIXED", "V0")
            for scope, values in [("ALL_DEVELOPMENT_GROUPS", summary)] + list(
                summary["by_source"].items()
            ):
                writer.writerow(
                    {
                        "model": name,
                        "variant": variant,
                        "scope": scope,
                        "groups": values["coffee_groups"],
                        "ndcg5": values["ndcg5"],
                        "recall5": values["recall5"],
                        "recall8": values["recall8"],
                        "attribute_mae": values["measured_attribute_mae"],
                        "wrong_initial_count": values["proxy_wrong_initial_count"],
                        "wrong_direction_correction_rate": values[
                            "proxy_wrong_direction_correction_rate"
                        ],
                        "correct_initial_count": values["proxy_correct_initial_count"],
                        "correct_direction_loss_rate": values[
                            "proxy_correct_direction_loss_rate"
                        ],
                        "direction_not_identifiable_count": values.get(
                            "proxy_direction_not_identifiable_count", 0
                        ),
                        "duplicate_evidence_max_gain": values[
                            "duplicate_evidence_max_gain"
                        ],
                        "real_answer_evaluation": "NOT_EVALUATED",
                    }
                )
    metrics_path = PUBLIC / "metrics.json"
    metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
    metrics["foundation"] = report
    save(metrics_path, metrics)


def refresh_evaluation(owner=DEFAULT_OWNER):
    """Reevaluate retained weights after runtime/diagnostic review; never refit."""
    private = owner / "revisions/r1"
    result_dir = private / "foundation"
    report = json.loads((result_dir / "report.private.json").read_text())
    if not (result_dir / "report.before_runtime_review.private.json").exists():
        save(result_dir / "report.before_runtime_review.private.json", report)
    records = json.loads((owner / "recovery_records.json").read_text())
    development = [r for r in records if r["split"] == "DEVELOPMENT"]
    split = trainer.split_groups(development, 3)
    all_rows = defaultdict(list)
    for fold in range(3):
        file = result_dir / ("fold" + str(fold) + ".private.json")
        result = json.loads(file.read_text())
        previous_file = result_dir / (
            "fold" + str(fold) + ".before_runtime_review.private.json"
        )
        if not previous_file.exists():
            save(previous_file, result)
        held = [r for r in development if split[r["group_id"]] == fold]
        base = json.loads(
            (
                private
                / "cv"
                / (report["base_repaired_model"] + "_fold" + str(fold) + ".model.json")
            ).read_text()
        )
        for key, old_rows in result["rows"].items():
            active = copy.deepcopy(base)
            if key == "V0":
                variant = "V0"
            else:
                name, variant = key.split(":")
                active["foundation_model"] = result["models"][name]
            rows = [
                foundation.evaluate_record(record, active, backend, variant)
                for record in held
            ]
            old_lookup = {r["record_id"]: r for r in old_rows}
            for row in rows:
                old = old_lookup[row["record_id"]]
                for metric in ["ndcg5", "recall5", "recall8", "measured_attribute_mae"]:
                    if (
                        row.get(metric) is not None
                        and abs(row[metric] - old[metric]) > 1e-12
                    ):
                        raise AssertionError(
                            "RUNTIME_REVIEW_CHANGED_FITTED_PREDICTION:"
                            + key
                            + ":"
                            + metric
                        )
                if row["ranking"] != old["ranking"]:
                    raise AssertionError("RUNTIME_REVIEW_CHANGED_RANKING")
            result["rows"][key], result["summary"][key] = rows, foundation.summarize(
                rows
            )
            all_rows[key].extend(rows)
        save(file, result)
        print(
            json.dumps(
                {
                    "event": "foundation_review_refresh_fold",
                    "fold": fold,
                    "trained_predictions_unchanged": True,
                }
            ),
            flush=True,
        )
    report["summaries"] = {name: summaries(rows) for name, rows in all_rows.items()}
    for name, comparisons in report["paired_comparisons"].items():
        comparisons["V1_attribute_mae_minus_explicit"] = paired(
            all_rows["explicit_attributes:V1"],
            all_rows[name + ":V1"],
            "measured_attribute_mae",
            higher_is_better=False,
        )
    report["protocol"][
        "direction_diagnostic_denominator"
    ] = "ONLY_T_WITH_AT_LEAST_ONE_INTERPRETABLE_ATTRIBUTE_DIRECTION; EMPTY_OR_UNMAPPED_T_NOT_IDENTIFIABLE; ALL_ROWS_RETAINED_IN_RECOVERY_AND_COVERAGE"
    report["protocol"]["foundation_check_supported_paths"] = ["P1"]
    report["numerical_limitations"] = [
        "At least one supervised nonnegative low-rank approximation reached its 2000-iteration limit during the completed run. All such feasible approximations remain in the reported comparisons; convergence is not claimed for every factor fit."
    ]
    report["engineering"]["runtime_review_corrections"] = {
        "all_saved_candidate_rankings_and_attribute_predictions_unchanged": True,
        "weights_refitted": False,
        "empty_T_not_classified_as_wrong": True,
        "MAE_improvement_direction": "LOWER",
        "duplicate_Q3_preserves_immediate_check": True,
        "signed_rejection_is_new_evidence": True,
        "batch_and_existing_answer_replay": True,
        "check_path_contract": "P1_ONLY; OTHER_PATHS_REJECTED_WHEN_CHECK_ENABLED",
        "component_decomposition_includes_foundation": True,
    }
    for name in ["M2_R1_FOUNDATION", "M2_R1_FOUNDATION_CHECK"]:
        model_path = private / "models" / (name + ".model.json")
        bundle = json.loads(model_path.read_text())
        request = json.loads(
            (result_dir / (name + "_example_request.private.json")).read_text()
        )
        output = foundation.run(request, bundle)
        reloaded = foundation.run(request, json.loads(json.dumps(bundle)))
        if output != reloaded:
            raise AssertionError("REVIEWED_RUNTIME_RELOAD_MISMATCH")
        save(result_dir / (name + "_example_result.private.json"), output)
    save(result_dir / "all_rows.private.json", all_rows)
    save(result_dir / "report.private.json", report)
    emit_public(report)
    print(
        json.dumps(
            {
                "event": "foundation_review_refresh_complete",
                "selection": report["selection"],
            }
        ),
        flush=True,
    )
    return report


def execute(owner=DEFAULT_OWNER, base_name=BASE_NAME):
    started = time.time()
    private = owner / "revisions/r1"
    result_dir = private / "foundation"
    records = json.loads((owner / "recovery_records.json").read_text())
    development = [r for r in records if r["split"] == "DEVELOPMENT"]
    assignment = trainer.split_groups(development, 3)
    all_rows, stability_rows, fits = defaultdict(list), [], []
    for fold in range(3):
        train = [r for r in development if assignment[r["group_id"]] != fold]
        held = [r for r in development if assignment[r["group_id"]] == fold]
        bundle = json.loads(
            (
                private / "cv" / (base_name + "_fold" + str(fold) + ".model.json")
            ).read_text()
        )
        print(
            json.dumps(
                {
                    "event": "foundation_outer_fold_start",
                    "fold": fold,
                    "train_groups": len({r["group_id"] for r in train}),
                    "held_groups": len({r["group_id"] for r in held}),
                }
            ),
            flush=True,
        )
        result = foundation.evaluate_experiment(
            train, held, bundle, backend, extra_soft_ranks=(2,)
        )
        save(result_dir / ("fold" + str(fold) + ".private.json"), result)
        for name, rows in result["rows"].items():
            all_rows[name].extend(rows)
        fits.append(result["training_audit"])
        stability_rows.extend(
            resampling_stability(train, held, bundle, result["models"])
        )
        print(
            json.dumps(
                {
                    "event": "foundation_outer_fold_complete",
                    "fold": fold,
                    "ndcg5": {k: v["ndcg5"] for k, v in result["summary"].items()},
                }
            ),
            flush=True,
        )
    report = {
        "version": foundation.VERSION,
        "base_repaired_model": base_name,
        "evaluation_type": foundation.PROXY,
        "real_answer_evaluation": "NOT_EVALUATED",
        "independent_confirmation": "NOT_EVALUATED",
        "development_records": len(development),
        "development_groups": len({r["group_id"] for r in development}),
        "protocol": {
            "path": "P1",
            "ordinary_slots": ["Q0", "Q1", "Q2", "Q3", "Q4"],
            "check_slot": "Q3",
            "A_B_T": "Group fold first; hash concept partition; Q0-Q2 use A, Q3 all variants use B, Q4 uses A+B; T never generates any question or answer.",
            "target": "FIXED_T_WITH_A_B_DIRECT_AND_DERIVED_PARENT_HITS_EXCLUDED_FROM_RECOVERY",
            "no_target_cases": "KEPT_AS_ZERO_IN_FULL_DENOMINATOR",
            "catalog": foundation.CHECK_CATALOG,
            "inner_fitting": "FOUNDATION_AND_BASE_M2_MODELS_SCALERS_STATISTICS_AND_QUESTION_BANKS_REFIT_ON_INNER_TRAIN; LIVE_SCORE_FOR_OOF_FUSION",
            "fusion_grid": [0.0, 0.15],
            "ranks": [3, 2],
            "negative_evidence": "EXPOSED_BROAD_NONE_ONLY_FIXED_NEGATIVE_EFFECT; NO_REAL_NONE_RESPONSE_EVALUATION_IN_D0",
        },
        "summaries": {name: summaries(rows) for name, rows in all_rows.items()},
        "paired_comparisons": {},
        "resampling_stability": aggregate_stability(stability_rows),
    }
    model_keys = [name.removesuffix(":V1") for name in all_rows if name.endswith(":V1")]
    for name in model_keys:
        comparisons = {
            "V1_minus_V0": paired(all_rows["V0"], all_rows[name + ":V1"]),
            "V2_minus_V1": paired(all_rows[name + ":V1"], all_rows[name + ":V2"]),
            "V2_minus_V0": paired(all_rows["V0"], all_rows[name + ":V2"]),
            "V1_attribute_mae_minus_explicit": paired(
                all_rows["explicit_attributes:V1"],
                all_rows[name + ":V1"],
                "measured_attribute_mae",
                higher_is_better=False,
            ),
            "by_source": {
                source: {
                    "V2_minus_V1": paired(
                        [
                            r
                            for r in all_rows[name + ":V1"]
                            if r["source_family"] == source
                        ],
                        [
                            r
                            for r in all_rows[name + ":V2"]
                            if r["source_family"] == source
                        ],
                    ),
                    "V1_minus_V0": paired(
                        [r for r in all_rows["V0"] if r["source_family"] == source],
                        [
                            r
                            for r in all_rows[name + ":V1"]
                            if r["source_family"] == source
                        ],
                    ),
                }
                for source in sorted({r["source_family"] for r in development})
            },
        }
        report["paired_comparisons"][name] = comparisons
    # Selection uses development comparisons only, never the 17 historical cases.
    selected = min(
        model_keys,
        key=lambda key: (
            -report["summaries"][key + ":V1"]["ndcg5"],
            report["summaries"][key + ":V1"].get("measured_attribute_mae") or 0,
            key,
        ),
    )
    fusion_supported = (
        report["paired_comparisons"][selected]["V1_minus_V0"]["status"]
        == "PROXY_IMPROVEMENT_SUPPORTED"
    )
    check_supported = (
        report["paired_comparisons"][selected]["V2_minus_V1"]["status"]
        == "PROXY_IMPROVEMENT_SUPPORTED"
    )
    base = json.loads((private / "models" / (base_name + ".model.json")).read_text())
    representation = (
        "supervised_soft_profile"
        if selected.startswith("supervised_soft_profile")
        else selected
    )
    rank = 2 if selected.endswith("rank2") else 3
    model = foundation.fit_foundation(development, base, representation, rank=rank)
    oof, audit = foundation.cross_fit_foundation(
        development, base, representation, rank=rank
    )
    coefficient, fit_audit = foundation.fit_fusion(oof, development, base)
    model["fusion_strength"] = coefficient if fusion_supported else 0.0
    for enabled, name in [
        (False, "M2_R1_FOUNDATION"),
        (True, "M2_R1_FOUNDATION_CHECK"),
    ]:
        retained = copy.deepcopy(base)
        retained["foundation_model"] = model
        retained["foundation_check_enabled"] = enabled
        retained["foundation_check_slot"] = "Q3"
        retained["bundle_id"] = (
            "m2-r1-foundation:"
            + backend.digest([base["bundle_id"], model, enabled])[:20]
        )
        retained["foundation_research_status"] = {
            "research_only": True,
            "fusion_supported_on_development": fusion_supported,
            "check_supported_on_development": check_supported,
            "real_answer_evaluation": "NOT_EVALUATED",
            "default_backend": "B2_UNCHANGED",
        }
        path = private / "models" / (name + ".model.json")
        save(path, retained)
        # Exercise actual saved-model reload through the live entry and verify
        # the same question instances/scores and once-only comparison boundary.
        ep, states, answers = foundation.trajectory(
            development[0], retained, backend, "V2" if enabled else "V1"
        )
        payload = {
            "contract_version": backend.VERSIONS["contract_version"],
            "context": ep["context"],
            "answers": answers,
        }
        reloaded = json.loads(path.read_text())
        output = foundation.run(payload, reloaded)
        if output["state"]["candidate_scores"] != states[-1]["candidate_scores"]:
            raise AssertionError("RELOADED_FOUNDATION_RUNTIME_SCORE_MISMATCH")
        save(result_dir / (name + "_example_request.private.json"), payload)
        save(result_dir / (name + "_example_result.private.json"), output)
    report["selection"] = {
        "representation": selected,
        "fusion_strength_retained": model["fusion_strength"],
        "fusion_decision": (
            "PROXY_IMPROVEMENT_SUPPORTED"
            if fusion_supported
            else "SCORING_DISABLED_NO_CLEAR_DOWNSTREAM_GAIN"
        ),
        "check_decision": (
            "PROXY_IMPROVEMENT_SUPPORTED"
            if check_supported
            else "RESEARCH_COMPONENT_ONLY_NO_CLEAR_VERIFICATION_GAIN"
        ),
        "models": ["M2_R1_FOUNDATION", "M2_R1_FOUNDATION_CHECK"],
        "backend_default": "B2_UNCHANGED",
        "development_selection_bias": "EXPLORATORY_MODEL_CHOICE; NO_NEW_CONFIRMATION_CLAIM",
    }
    report["engineering"] = {
        "model_reload": "PASSED",
        "same_runtime_trajectory_and_score_path": True,
        "full_fit_training_groups": len(model["training_groups"]),
        "elapsed_seconds": time.time() - started,
        "foundation_tests": "EXECUTE_TEST_FOUNDATION_R1_SEPARATELY",
        "frontend_changes": False,
    }
    save(result_dir / "all_rows.private.json", all_rows)
    save(result_dir / "stability.private.json", stability_rows)
    save(
        result_dir / "fit_audit.private.json",
        {"outer": fits, "final_inner": audit, "final_fusion": fit_audit},
    )
    save(result_dir / "report.private.json", report)
    emit_public(report)
    print(
        json.dumps(
            {
                "event": "foundation_experiment_complete",
                "selection": report["selection"],
                "elapsed_seconds": report["engineering"]["elapsed_seconds"],
            }
        ),
        flush=True,
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", type=Path, default=DEFAULT_OWNER)
    parser.add_argument("--base-name", default=BASE_NAME)
    parser.add_argument("--refresh-evaluation", action="store_true")
    args = parser.parse_args()
    try:
        (
            refresh_evaluation(args.owner)
            if args.refresh_evaluation
            else execute(args.owner, args.base_name)
        )
    except Exception:
        receipt = {
            "status": "FAILED_NOT_REPORTED_AS_PASS",
            "traceback": traceback.format_exc(),
            "time": time.time(),
        }
        destination = (
            args.owner
            / "revisions/r1/foundation"
            / ("failed_run_" + str(int(time.time())) + ".private.json")
        )
        save(destination, receipt)
        raise
