"""One preregistered source-view restriction; frozen R6 scorer and rules.

Body ``tea`` remains a source-native expression of unresolved meaning. This
adapter prevents that span from supplying new green flavour evidence; it never
removes MAP_BASE evidence or changes actual user answer handling.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

import mechanism_diagnostics_r7 as m

VERSION = "m2-r7.body-tea-source-role-scope.v1"
CANDIDATE = "C11_BODY_TEA_SOURCE_INTERPRETATION_ONLY"
CONTRACT_SHA256 = "9b615deadc3f482b8d7e91b5b45a4386a32fa0a523e8a8f2ee7415a163093dd9"
GREEN = "attribute.green_vegetative"
FILES = {
    "checks": "local_repair_checks.private.json",
    "rows": "local_repair_trajectories.private.json",
    "resources": "local_repair_resources.private.json",
    "audit": "local_repair_case_audit.private.json",
    "details": "local_repair_detailed_examples.private.json",
    "summary": "local_repair_summary.private.json",
    "receipt": "local_repair_receipt.private.json",
}
REPORTING = {
    "rows": "local_repair_reporting_trajectories.private.json",
    "summary": "local_repair_reporting_summary.private.json",
    "receipt": "local_repair_reporting_receipt.private.json",
    "execution_source": "local_repair_execution_v1.private.py",
}


def blocked(span):
    return span["field"] == "body_description" and span["normalized_span"] == "tea"


def protected(record):
    return {
        k: v
        for k, v in record.items()
        if k
        not in {
            "A",
            "B",
            "mapping_input_trace",
            "mapping_patch_sha256",
            "source_scope_repair",
        }
    }


def apply_inputs(record, units, patch):
    """Use the frozen patch, reaccumulating eligible evidence from MAP_BASE."""
    result = m.semantic.apply_inputs(record, units, patch)
    concepts = {role: set(record[role]) for role in ("A", "B")}
    for trace in result["mapping_input_trace"]:
        if blocked(trace):
            trace["legacy_projected_concepts"] = copy.deepcopy(trace["concepts"])
            trace["legacy_added_concepts"] = copy.deepcopy(trace["added_concepts"])
            trace["concepts"] = []
            trace["added_concepts"] = []
            trace["status"] = "UNRESOLVED_SOURCE_FIELD_MEANING"
            trace["evidence_role"] = "SOURCE_INTERPRETATION_ONLY"
            trace["flavour_support_allowed"] = False
            trace["scope_reason"] = (
                "Body tea is not source-asserted green flavour; native meaning retained, no absence inference"
            )
        else:
            trace["added_concepts"] = sorted(
                set(trace["concepts"]) - concepts[trace["role"]]
            )
            concepts[trace["role"]].update(trace["concepts"])
    for role in ("A", "B"):
        result[role] = sorted(concepts[role])
        if not set(record[role]) <= concepts[role]:
            raise ValueError("R7_REPAIR_REMOVED_MAP_BASE")
    result["source_scope_repair"] = {
        "version": VERSION,
        "contract_sha256": CONTRACT_SHA256,
    }
    if protected(result) != protected(record):
        raise ValueError("R7_REPAIR_PROTECTED_TARGET_MASK_OR_ROLE_CHANGED")
    return result


def coverage_inputs(records, units, patch, held):
    """Subset before inspecting A/B; frozen patch's TRAIN groups only."""
    m.semantic.check_patch(patch)
    training = set(patch["training_groups"])
    if training & set(held):
        raise ValueError("R7_REPAIR_COVERAGE_TRAIN_HELD_OVERLAP")
    selected = [r for r in records if r["group_id"] in training]
    if {r["group_id"] for r in selected} != training:
        raise ValueError("R7_REPAIR_TRAIN_GROUPS_NOT_COMPLETE")
    return [apply_inputs(r, units, patch) for r in selected]


def verify_contract(owner, expected):
    path = Path(owner) / "revisions/r7/local_repair_contract.private.json"
    if expected != CONTRACT_SHA256 or m.sha(path) != expected:
        raise ValueError("R7_LOCAL_REPAIR_FROZEN_CONTRACT_REQUIRED")
    value = m.read(path)
    if value["version"] != VERSION or value["candidate"] != CANDIDATE:
        raise ValueError("R7_LOCAL_REPAIR_CONTRACT_MISMATCH")
    if (
        value["predicate"]["field"] != "body_description"
        or value["predicate"]["normalized_span"] != "tea"
    ):
        raise ValueError("R7_LOCAL_REPAIR_PREDICATE_CHANGED")
    m.check_contract(value["r7_contract_sha256"])
    return value


def synthetic_inputs():
    record = {
        "record_id": "synthetic-only",
        "group_id": "synthetic-coffee",
        "A": [],
        "B": [],
        "A_observation_unit_id": "A",
        "B_observation_unit_id": "B",
        "T_observation_unit_ids": ["T"],
        "relevance_full": {"sensory.apple": 1},
        "relevance_unexpressed": {"sensory.apple": 1},
        "masks": {"leaf_recovery": True},
        "source_family": "SYNTHETIC_MECHANISM_FIXTURE",
    }
    units = {
        role: {
            "observation_unit_id": role,
            "group_id": record["group_id"],
            "strict_D0_concepts": [],
            "description_fields": {
                "body_description": {"source_text": "light, tea", "source_column": 20},
                "aroma": {"source_text": "herbaceous", "source_column": 5},
            },
        }
        for role in ("A", "B")
    }
    patch = m.semantic.fit_patch([record], units, {record["group_id"]})
    return record, units, patch


def synthetic_checks():
    record, units, patch = synthetic_inputs()
    checks = {}
    body_only = copy.deepcopy(units)
    for u in body_only.values():
        del u["description_fields"]["aroma"]
    result = apply_inputs(record, body_only, patch)
    checks["body_only_no_new_green"] = GREEN not in result["A"] + result["B"]
    checks["raw_body_text_and_native_uncertainty_retained"] = all(
        t["source_text"] == "light, tea"
        and t["status"] == "UNRESOLVED_SOURCE_FIELD_MEANING"
        and t["evidence_role"] == "SOURCE_INTERPRETATION_ONLY"
        and not t["concepts"]
        for t in result["mapping_input_trace"]
    )
    checks["independent_herb_support_retained"] = all(
        GREEN in apply_inputs(record, units, patch)[r] for r in ("A", "B")
    )
    for field in ("aroma", "bouquet", "aftertaste", "bitterness_description"):
        other = copy.deepcopy(body_only)
        for u in other.values():
            u["description_fields"] = {
                field: {"source_text": "tea", "source_column": field}
            }
        checks["non_body_tea_unchanged_" + field] = all(
            GREEN in apply_inputs(record, other, patch)[r] for r in ("A", "B")
        )
    base = copy.deepcopy(record)
    base["A"] = [GREEN]
    checks["every_MAP_BASE_concept_preserved"] = (
        GREEN in apply_inputs(base, body_only, patch)["A"]
    )
    checks["complete_targets_masks_roles_unchanged"] = protected(result) == protected(
        record
    )
    # Adding a held row whose units are unavailable must not cause a read.
    held = {
        **record,
        "record_id": "held",
        "group_id": "held",
        "A_observation_unit_id": "MISSING_A",
        "B_observation_unit_id": "MISSING_B",
    }
    train = coverage_inputs([record, held], body_only, patch, {"held"})
    coverage = m.information.coverage_for(train, {"held"})
    checks["TRAIN_B_body_only_no_green_coverage"] = coverage.get(GREEN, 0) == 0
    checks["held_units_not_inspected"] = len(train) == 1
    return checks


def mechanism_checks(owner, expected):
    verify_contract(owner, expected)
    checks = synthetic_checks()
    relative = "revisions/r1/cv/M2_R1_FINAL_FIXED_fold0.model.json"
    bundle = m.conditioning.model_bundle(m.read(Path(owner) / relative))
    # New, explicitly chosen answer; neither source mapping nor T supplies it.
    state = m.information.initial_state(
        {"c0": "preparation.family.filter_percolation", "c1": "medium"}, bundle
    )
    for slot in ("Q0", "Q1"):
        prepared, plan = m.information.select(state, bundle, {}, "I2_LIVE")
        q = plan["question"]
        selection = [GREEN] if GREEN in q["shown_option_ids"] else []
        answer = {
            k: copy.deepcopy(q[k])
            for k in ("slot", "question_id", "axis", "shown_option_ids")
        }
        answer.update(
            selected_option_ids=selection, state="SELECTED" if selection else "UNSURE"
        )
        state = m.information.update(prepared, answer, bundle)
        untouched = m.runtime.update_state(prepared, answer, bundle)
        checks["actual_user_update_exact_unchanged_runtime_" + slot] = (
            state == untouched
        )
    checks["actual_user_green_selection_preserved"] = GREEN in m.provider.selected(
        state
    )
    value = {
        "version": VERSION,
        "contract_sha256": expected,
        "checked_utc": m.previous.io.now(),
        "code_sha256": m.sha(__file__),
        "checks": checks,
        "all_passed": all(checks.values()),
        "scorer_sha256": m.sha(Path(owner) / relative),
        "real_data_fit_count": 0,
        "fixture_scope": "Synthetic mapping checks plus real frozen scorer actual-user answer check; no held outcome inspection",
    }
    if not value["all_passed"]:
        raise ValueError("R7_LOCAL_MECHANISM_CHECK_FAILED:" + str(checks))
    m.save(Path(owner) / "revisions/r7" / FILES["checks"], value)
    return value


def public_summary(rows, baselines, audits, resources, expected):
    values = {**baselines, CANDIDATE: rows}
    paired = {
        CANDIDATE
        + "-"
        + name: m.evaluation.paired(
            [m.previous.evaluated(r) for r in old],
            [m.previous.evaluated(r) for r in rows],
        )
        for name, old in baselines.items()
    }
    counts = {}
    for name in baselines:
        cs = [a["comparisons"][name] for a in audits]
        counts[name] = {
            "outcomes_all_records": dict(Counter(c["outcome"] for c in cs)),
            "rank_changed_records": sum(c["rank_order_changed"] for c in cs),
            "scores_changed_records": sum(bool(c["candidate_changes"]) for c in cs),
            "canonical_selected_changed_records": sum(
                c["canonical_selected_changed"] for c in cs
            ),
            "whole_exposure_content_changed_records": sum(
                c["exposure_structure"]["whole_exposure_content_changed"] for c in cs
            ),
            "main5_set_changed_records": sum(
                bool(c["entered_main5"] or c["displaced_main5"]) for c in cs
            ),
            "fine5_set_changed_records": sum(
                bool(
                    c["entered_fine_primary_panel"] or c["displaced_fine_primary_panel"]
                )
                for c in cs
            ),
        }
    return {
        "version": VERSION,
        "candidate": CANDIDATE,
        "contract_sha256": expected,
        "scope": "PREVIOUSLY_VIEWED_DEVELOPMENT_LOCAL_SOURCE_SCOPE_CHECK_NOT_CONFIRMATION",
        "fit_count": 0,
        "rule_selection_count": 0,
        "coverage_recomputations": len(resources),
        "records": len(rows),
        "coffee_groups": len({r["group_id"] for r in rows}),
        "metrics": {name: m.aggregate_results(rs) for name, rs in values.items()},
        "paired_contrasts": paired,
        "change_counts": counts,
        "held_records_with_scoped_body_tea": sum(
            any(blocked(t) for t in a["source_interpretation"]) for a in audits
        ),
        "held_records_with_changed_mapped_AB": sum(
            a["mapped_AB_changed"] for a in audits
        ),
        "scoped_body_trace_count": sum(
            sum(blocked(t) for t in a["source_interpretation"]) for a in audits
        ),
        "possible_priority_contract_flags": sum(
            m.retention(r)["possible_priority_contract_violation"] for r in rows
        ),
        "coverage_scope": "Only corresponding frozen outer TRAIN B; same frozen rule eligibility, no held or target inputs",
        "metric_scope": "Fixed 56 fine task first5 filtered ranking; full fixed T including generation-unavailable targets; actual mixed-layer main5 separate",
        "conclusion_scope": "Provenance support correction is independent of alignment outcome; no claim tea flavour absent or word translation resolved",
        "default": "B2_UNCHANGED_FOUNDATION_CHECK_OFF_NO_PROMOTION",
    }


def preserved_r7(owner):
    dst = Path(owner) / "revisions/r7"
    files = [p for p in dst.glob("mechanism*.private.*") if p.is_file()]
    return {p.name: m.sha(p) for p in files}


def run(owner, expected):
    owner = Path(owner)
    contract = verify_contract(owner, expected)
    dst = owner / "revisions/r7"
    if (dst / FILES["receipt"]).exists() or (
        dst / "local_repair_execution_started.private.json"
    ).exists():
        raise ValueError("R7_LOCAL_CANDIDATE_ALREADY_EXECUTED_OR_STARTED_USE_REPLAY")
    checks = m.read(dst / FILES["checks"])
    if (
        not checks["all_passed"]
        or checks["code_sha256"] != m.sha(__file__)
        or checks["contract_sha256"] != expected
    ):
        raise ValueError("R7_LOCAL_PASSING_PRECOMPARISON_MECHANISM_CHECK_REQUIRED")
    frozen = m.load_frozen(owner)
    protected_hashes = preserved_r7(owner)
    started = m.previous.io.now()
    m.save(
        dst / "local_repair_execution_started.private.json",
        {
            "started_utc": started,
            "contract_sha256": expected,
            "code_sha256": m.sha(__file__),
        },
    )
    baselines = {name: frozen["cases"][name] for name in ("C01", "C11")}
    lookup = {
        name: {r["record_id"]: r for r in rows} for name, rows in baselines.items()
    }
    rows, audits, resources = [], [], []
    for fold in range(3):
        relative = f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{fold}.model.json"
        old = frozen["resources"][(relative, "MAP_PATCH")]
        if m.sha(owner / relative) != old["expert_sha256"]:
            raise ValueError("R7_LOCAL_FROZEN_SCORER_CHANGED")
        bundle = m.conditioning.model_bundle(m.read(owner / relative))
        held = {r["group_id"] for r in baselines["C11"] if r["fold"] == fold}
        train = coverage_inputs(
            list(frozen["records"].values()), frozen["units"], old["patch"], held
        )
        if {r["group_id"] for r in train} != set(old["training_groups"]):
            raise ValueError("R7_LOCAL_COVERAGE_TRAINING_SCOPE_CHANGED")
        coverage = m.information.coverage_for(train, held)
        resource = {
            "fold": fold,
            "expert_path": relative,
            "expert_sha256": old["expert_sha256"],
            "patch": old["patch"],
            "training_groups": sorted(old["training_groups"]),
            "excluded_groups": sorted(held),
            "coverage": coverage,
            "original_C11_coverage": old["coverage"],
            "training_input_traces": [
                {
                    "record_id": r["record_id"],
                    "group_id": r["group_id"],
                    "B_observation_unit_id": r["B_observation_unit_id"],
                    "B": r["B"],
                    "mapping_input_trace": r["mapping_input_trace"],
                }
                for r in train
            ],
        }
        resources.append(resource)
        for original in sorted(baselines["C11"], key=lambda r: r["record_id"]):
            if original["fold"] != fold:
                continue
            record = frozen["records"][original["record_id"]]
            mapped = apply_inputs(record, frozen["units"], old["patch"])
            context = original["state"]["base_state"]["context"]
            if original["frozen_A0_generation_universe"] != bundle["fixed_candidates"]:
                raise ValueError("R7_LOCAL_GENERATION_UNIVERSE_CHANGED")
            trajectory = m.run_trajectory(
                mapped["A"], mapped["B"], context, bundle, coverage
            )
            row = m.result_row(original, mapped, trajectory, CANDIDATE, bundle)
            rows.append(row)
            oldmapped = m.semantic.apply_inputs(record, frozen["units"], old["patch"])
            comparisons = {
                name: m.contrast(
                    lookup[name][row["record_id"]], row, mapped["mapping_input_trace"]
                )
                for name in baselines
            }
            # Labels from the channel diagnostic cannot certify mapping validity.
            for comparison in comparisons.values():
                comparison["classification"][
                    "classification"
                ] = "REGISTERED_SOURCE_ROLE_SCOPE_CORRECTION_WITH_DOWNSTREAM_BUDGET_AND_RANK_EFFECTS"
            audits.append(
                {
                    "record_id": row["record_id"],
                    "group_id": row["group_id"],
                    "fold": fold,
                    "source_interpretation": mapped["mapping_input_trace"],
                    "legacy_source_interpretation": oldmapped["mapping_input_trace"],
                    "mapped_AB_changed": any(
                        mapped[r] != oldmapped[r] for r in ("A", "B")
                    ),
                    "original_mapped_A": oldmapped["A"],
                    "original_mapped_B": oldmapped["B"],
                    "scoped_mapped_A": mapped["A"],
                    "scoped_mapped_B": mapped["B"],
                    "comparisons": comparisons,
                    "changed": any(c["changed"] for c in comparisons.values()),
                }
            )
        print(
            {
                "checkpoint": "LOCAL_SCOPE_OUTER_COMPLETE",
                "fold": fold,
                "records": len(rows),
                "fit_count": 0,
            },
            flush=True,
        )
    rows.sort(key=lambda r: r["record_id"])
    audits.sort(key=lambda r: r["record_id"])
    summary = public_summary(rows, baselines, audits, resources, expected)
    details = m.choose_details(audits)
    for key, value in (
        ("rows", rows),
        ("resources", resources),
        ("audit", audits),
        ("details", details),
    ):
        m.save(dst / FILES[key], value)
    summary["private_evidence_hashes"] = {
        FILES[k]: m.sha(dst / FILES[k])
        for k in ("rows", "resources", "audit", "details")
    }
    summary["development_mechanism_checks"] = checks["checks"]
    m.save(dst / FILES["summary"], summary)
    if preserved_r7(owner) != protected_hashes:
        raise ValueError("R7_LOCAL_REPAIR_ALTERED_OLD_DIAGNOSTICS")
    receipt = {
        "started_utc": started,
        "completed_utc": m.previous.io.now(),
        "contract_sha256": expected,
        "code_sha256": m.sha(__file__),
        "diagnostic_helper_sha256": m.sha(m.__file__),
        "r6_completion_manifest_sha256": m.sha(
            owner / "revisions/r6/completion_manifest.private.json"
        ),
        "preserved_r7_sha256": protected_hashes,
        "fit_count": 0,
        "candidate_executions": 1,
        "coverage_recomputations": 3,
        "artifacts": {
            FILES[k]: m.sha(dst / FILES[k])
            for k in ("checks", "rows", "resources", "audit", "details", "summary")
        },
    }
    m.save(dst / FILES["receipt"], receipt)
    return summary


def corrected_reporting_rows(rows, original_rows):
    """Restore the fixed legacy exclusion set, never candidate evidence or T."""
    original = {r["record_id"]: r for r in original_rows}
    result = copy.deepcopy(rows)
    for row in result:
        row["A"] = copy.deepcopy(original[row["record_id"]]["A"])
        # B was an accidental extra key in v1. Interpreted_B is the source input.
        row.pop("B", None)
    return result


def verify_original_receipt(owner, expected, execution_source):
    owner = Path(owner)
    verify_contract(owner, expected)
    dst = owner / "revisions/r7"
    receipt = m.read(dst / FILES["receipt"])
    if receipt["code_sha256"] != m.sha(execution_source) or receipt[
        "diagnostic_helper_sha256"
    ] != m.sha(m.__file__):
        raise ValueError("R7_LOCAL_REPLAY_CODE_CHANGED")
    if receipt["contract_sha256"] != expected or receipt[
        "r6_completion_manifest_sha256"
    ] != m.sha(owner / "revisions/r6/completion_manifest.private.json"):
        raise ValueError("R7_LOCAL_REPLAY_LINEAGE_CHANGED")
    for name, digest in {
        **receipt["artifacts"],
        **receipt["preserved_r7_sha256"],
    }.items():
        if m.sha(dst / name) != digest:
            raise ValueError("R7_LOCAL_REPLAY_ARTIFACT_CHANGED:" + name)
    return receipt


def correct_reporting(owner, expected, execution_source):
    """Post-execution wiring correction; old receipts/rows remain immutable."""
    owner = Path(owner)
    dst = owner / "revisions/r7"
    receipt = verify_original_receipt(owner, expected, execution_source)
    if (dst / REPORTING["receipt"]).exists():
        raise ValueError("R7_LOCAL_REPORTING_CORRECTION_ALREADY_SEALED")
    frozen = m.load_frozen(owner)
    old_rows = m.read(dst / FILES["rows"])
    baselines = {name: frozen["cases"][name] for name in ("C01", "C11")}
    rows = corrected_reporting_rows(old_rows, baselines["C11"])
    for before, after in zip(old_rows, rows, strict=True):
        if {k: v for k, v in before.items() if k not in {"A", "B"}} != {
            k: v for k, v in after.items() if k not in {"A", "B"}
        }:
            raise ValueError("R7_REPORTING_CORRECTION_ALTERED_TRAJECTORY_OR_TARGET")
    old_summary = m.read(dst / FILES["summary"])
    summary = public_summary(
        rows,
        baselines,
        m.read(dst / FILES["audit"]),
        m.read(dst / FILES["resources"]),
        expected,
    )
    changed_metrics = {
        model: {
            key: {"before": old_summary["metrics"][model][key], "after": val}
            for key, val in metrics.items()
            if old_summary["metrics"][model][key] != val
        }
        for model, metrics in summary["metrics"].items()
    }
    if any(
        set(values) - {"legacy_R4_recovery_gap"} for values in changed_metrics.values()
    ):
        raise ValueError("R7_UNEXPECTED_NONLEGACY_REPORTING_METRIC_CHANGE")
    correction = {
        "status": "CORRECTED_FIXED_A_REPORTING_WIRING_ERROR",
        "reason": "v1 overwrote frozen MAP_BASE A with interpreted_A; legacy_R4 exclusion then used a different reference set from original C11. This was a reporting error, not a scientific regression caused by Body tea scope.",
        "corrected_utc": m.previous.io.now(),
        "rows_with_fixed_A_restored": sum(
            a["A"] != b["A"] for a, b in zip(old_rows, rows, strict=True)
        ),
        "preserved_interpreted_AB_and_all_rankings_states_targets": True,
        "changed_metrics": changed_metrics,
        "new_policy_executions": 0,
        "new_candidate_comparisons": 0,
        "fit_count": 0,
        "coverage_recomputations": 0,
        "original_execution_receipt_sha256": m.sha(dst / FILES["receipt"]),
        "original_erroneous_summary_sha256": m.sha(dst / FILES["summary"]),
    }
    summary["reporting_correction"] = correction
    summary["development_mechanism_checks"] = old_summary[
        "development_mechanism_checks"
    ]
    m.save(dst / REPORTING["rows"], rows)
    summary["private_evidence_hashes"] = {
        **old_summary["private_evidence_hashes"],
        REPORTING["rows"]: m.sha(dst / REPORTING["rows"]),
    }
    m.save(dst / REPORTING["summary"], summary)
    snapshot = dst / REPORTING["execution_source"]
    snapshot.write_bytes(Path(execution_source).read_bytes())
    snapshot.chmod(0o600)
    if m.sha(snapshot) != receipt["code_sha256"]:
        raise ValueError("R7_LOCAL_EXECUTION_SNAPSHOT_COPY_CHANGED")
    m.save(
        dst / REPORTING["receipt"],
        {
            "contract_sha256": expected,
            "code_sha256": m.sha(__file__),
            "correction": correction,
            "original_execution_receipt_sha256": m.sha(dst / FILES["receipt"]),
            "artifacts": {
                REPORTING[k]: m.sha(dst / REPORTING[k])
                for k in ("rows", "summary", "execution_source")
            },
        },
    )
    return summary


def replay(owner, expected):
    owner = Path(owner)
    dst = owner / "revisions/r7"
    reporting = (
        m.read(dst / REPORTING["receipt"])
        if (dst / REPORTING["receipt"]).exists()
        else None
    )
    source = dst / REPORTING["execution_source"] if reporting else Path(__file__)
    verify_original_receipt(owner, expected, source)
    if reporting:
        if (
            reporting["code_sha256"] != m.sha(__file__)
            or reporting["contract_sha256"] != expected
        ):
            raise ValueError("R7_REPORTING_REPLAY_CODE_OR_CONTRACT_CHANGED")
        if reporting["original_execution_receipt_sha256"] != m.sha(
            dst / FILES["receipt"]
        ):
            raise ValueError("R7_REPORTING_ORIGINAL_RECEIPT_CHANGED")
        for name, expected_hash in reporting["artifacts"].items():
            if m.sha(dst / name) != expected_hash:
                raise ValueError("R7_REPORTING_ARTIFACT_CHANGED:" + name)
    frozen = m.load_frozen(owner)
    rows = m.read(dst / (REPORTING if reporting else FILES)["rows"])
    baseline_A = {r["record_id"]: r["A"] for r in frozen["cases"]["C11"]}
    for row in rows:
        original = frozen["records"][row["record_id"]]
        if row["A"] != baseline_A[row["record_id"]]:
            raise ValueError("R7_LOCAL_LEGACY_FIXED_A_EXCLUSION_CHANGED")
        if (
            row["full_T"] != original["relevance_full"]
            or row["hidden_T"] != original["relevance_unexpressed"]
        ):
            raise ValueError("R7_LOCAL_REPLAY_TARGET_CHANGED")
        if (
            m.metric.evaluate(row["ranking"], row["full_T"], m.evaluation.CANDIDATES)
            != row["metrics"]
        ):
            raise ValueError("R7_LOCAL_REPLAY_METRIC_MISMATCH")
        if (
            m.metric.evaluate(row["ranking"], row["hidden_T"], m.evaluation.CANDIDATES)
            != row["hidden_metrics"]
        ):
            raise ValueError("R7_LOCAL_REPLAY_HIDDEN_METRIC_MISMATCH")
    baselines = {name: frozen["cases"][name] for name in ("C01", "C11")}
    summary = m.read(dst / (REPORTING if reporting else FILES)["summary"])
    check = public_summary(
        rows,
        baselines,
        m.read(dst / FILES["audit"]),
        m.read(dst / FILES["resources"]),
        expected,
    )
    if any(summary[k] != value for k, value in check.items()):
        raise ValueError("R7_LOCAL_REPLAY_AGGREGATE_MISMATCH")
    return {
        "status": "PASSED",
        "replayed_sealed_rows": len(rows),
        "metric_recomputations": 2 * len(rows),
        "fit_count": 0,
        "policy_executions": 0,
        "summary": summary,
        "reporting_correction": reporting["correction"] if reporting else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation", choices=("check", "run", "replay", "correct-reporting")
    )
    parser.add_argument("--owner-dir", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--execution-code-snapshot", type=Path)
    args = parser.parse_args()
    with m.threadpool_limits(limits=1):
        if args.operation == "correct-reporting":
            if not args.execution_code_snapshot:
                parser.error("correct-reporting requires --execution-code-snapshot")
            value = correct_reporting(
                args.owner_dir, args.contract_sha256, args.execution_code_snapshot
            )
        else:
            value = {"check": mechanism_checks, "run": run, "replay": replay}[
                args.operation
            ](args.owner_dir, args.contract_sha256)
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(
            json.dumps(
                value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
            )
            + "\n"
        )
        args.summary.chmod(0o600)
    print({"operation": args.operation, "status": "PASSED", "fit_count": 0}, flush=True)


if __name__ == "__main__":
    main()
