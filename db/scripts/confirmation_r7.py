"""Frozen external C00/C01 comparison; no fitting or held-data statistics."""

from __future__ import annotations
import argparse
import copy
import datetime
import json
from pathlib import Path
import run_supervision_r5 as io
import train_supervision_r5 as metrics

VERSION = "m2-r7.fixed-independent-confirmation.v1"
REQUIRED = [
    "record_id",
    "group_id",
    "sample_id",
    "A",
    "B",
    "relevance_full",
    "A_observation_unit_id",
    "B_observation_unit_id",
    "T_observation_unit_ids",
]


def evaluation_code_hashes():
    base = Path(__file__).parent
    return {
        name: io.sha(base / name)
        for name in [
            "confirmation_r7.py",
            "train_supervision_r5.py",
            "alignment_metrics_r3.py",
            "audit_revelation_r4.py",
        ]
    }


def validate_records(records, development_groups):
    if not isinstance(records, list) or not records:
        raise ValueError("NO_CONFIRMATION_RECORDS")
    ids = set()
    observations = set()
    samples = {}
    for r in records:
        if not isinstance(r, dict):
            raise ValueError("TYPED_RECORD_REQUIRED")
        if set(REQUIRED) - set(r):
            raise ValueError("MISSING_SOURCE_ROLE_FIELDS")
        if any(
            not isinstance(r[k], str) or not r[k].strip()
            for k in ["record_id", "group_id", "sample_id"]
        ):
            raise ValueError("NONEMPTY_SOURCE_IDENTITIES_REQUIRED")
        if r["sample_id"] in samples and samples[r["sample_id"]] != r["group_id"]:
            raise ValueError("SAMPLE_GROUP_IDENTITY_CONFLICT")
        samples[r["sample_id"]] = r["group_id"]
        if r["record_id"] in ids:
            raise ValueError("DUPLICATE_RECORD_ID")
        ids.add(r["record_id"])
        if r["group_id"] in development_groups:
            raise ValueError("PREVIOUSLY_USED_COFFEE_GROUP")
        if not isinstance(r["T_observation_unit_ids"], list):
            raise ValueError("DISJOINT_SOURCE_OBSERVATIONS_REQUIRED")
        roles = [
            r["A_observation_unit_id"],
            r["B_observation_unit_id"],
            *r["T_observation_unit_ids"],
        ]
        if (
            not r["T_observation_unit_ids"]
            or any(not isinstance(x, str) or not x.strip() for x in roles)
            or len(roles) != len(set(roles))
        ):
            raise ValueError("DISJOINT_SOURCE_OBSERVATIONS_REQUIRED")
        if observations & set(roles):
            raise ValueError("OBSERVATION_REUSE_ACROSS_EPISODES")
        observations.update(roles)
        if (
            not isinstance(r["A"], list)
            or not isinstance(r["B"], list)
            or not isinstance(r["relevance_full"], dict)
        ):
            raise ValueError("TYPED_OBSERVATIONS_REQUIRED")
        if any(not isinstance(c, str) or not c for c in r["A"] + r["B"]):
            raise ValueError("CONCEPT_IDS_REQUIRED")
        for concept, weight in r["relevance_full"].items():
            if (
                not isinstance(concept, str)
                or not concept.startswith("sensory.")
                or isinstance(weight, bool)
                or not isinstance(weight, (int, float))
                or not 0 < weight < float("inf")
            ):
                raise ValueError("POSITIVE_FINE_OR_SOURCE_OOV_TARGET_REQUIRED")
    return {
        "records": len(records),
        "groups": len({r["group_id"] for r in records}),
        "observation_units": len(observations),
        "nonempty_fixed_T": sum(bool(r["relevance_full"]) for r in records),
    }


def freeze_cohort(owner, source_file, admission_file, candidate_file):
    """Run only after source identity/rights audit; no candidate predictions here."""
    import candidate_c01_r7 as candidate

    owner = Path(owner)
    records = io.read(source_file)
    admission = io.read(admission_file)
    bundle = candidate.load_bundle(candidate_file)
    for field in [
        "identity_verified",
        "license_verified",
        "observation_roles_verified",
        "previous_use_checked",
        "fixed_base_mapping_applied",
    ]:
        if admission.get(field) is not True:
            raise ValueError("SOURCE_ADMISSION_INCOMPLETE:" + field)
    if (
        not isinstance(admission.get("measurement_scope"), str)
        or not admission["measurement_scope"].strip()
    ):
        raise ValueError("MEASUREMENT_SCOPE_REQUIRED")
    if admission.get("records_sha256") != io.sha(source_file):
        raise ValueError("SOURCE_ADMISSION_HASH_MISMATCH")
    if admission.get("role") != "NEW_FIXED_CONFIRMATION":
        raise ValueError("SOURCE_NOT_RESERVED_FOR_CONFIRMATION")
    # The source audit must include content/alias checks, not only unequal hashed IDs.
    if not admission.get("identity_audit_evidence") or not admission.get(
        "license_evidence"
    ):
        raise ValueError("SOURCE_EVIDENCE_REQUIRED")
    groups = set(bundle["scorer_training_groups"]) | set(
        bundle["coverage_training_groups"]
    )
    historical = io.read(owner / "recovery_records.json")
    groups.update(r["group_id"] for r in historical)
    counts = validate_records(records, groups)
    source_id = admission["source_id"]
    if not source_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError("SAFE_SOURCE_ID_REQUIRED")
    destination = (
        owner / "revisions/r7/confirmation" / source_id / "frozen_cohort.private.json"
    )
    if destination.exists():
        raise ValueError("CONFIRMATION_ALREADY_FROZEN")
    contract = {
        "version": VERSION,
        "registered_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_id": source_id,
        "candidate_sha256": io.sha(candidate_file),
        "source_file": str(Path(source_file).resolve()),
        "source_sha256": io.sha(source_file),
        "admission_file": str(Path(admission_file).resolve()),
        "admission_sha256": io.sha(admission_file),
        "counts": counts,
        "record_ids": sorted(r["record_id"] for r in records),
        "fixed_targets": {r["record_id"]: r["relevance_full"] for r in records},
        "fixed_hidden_targets": {
            r["record_id"]: {
                k: v for k, v in r["relevance_full"].items() if k not in r["A"]
            }
            for r in records
        },
        "candidate_file": str(Path(candidate_file).resolve()),
        "primary": "gap(C01)-gap(C00)",
        "evaluation_panel": "Inherited R6 fine-only top5 from the full ranking; distinct from existing mixed broad/fine runtime main5 and actual final exposure",
        "metric_code_sha256": io.sha(
            Path(metrics.__file__).parent / "alignment_metrics_r3.py"
        ),
        "evaluation_code_hashes": evaluation_code_hashes(),
        "scope": admission.get("measurement_scope"),
        "coverage_updates": False,
        "mapping_updates": False,
        "fitting_allowed": False,
    }
    io.save(destination, contract)
    destination.parent.chmod(0o700)
    return contract


def evaluate_cohort(owner, contract_path, replay=False):
    import candidate_c01_r7 as candidate

    contract = io.read(contract_path)
    if contract["evaluation_code_hashes"] != evaluation_code_hashes():
        raise ValueError("FROZEN_EVALUATION_CODE_CHANGED")
    for path_key, sha_key in [
        ("source_file", "source_sha256"),
        ("candidate_file", "candidate_sha256"),
        ("admission_file", "admission_sha256"),
    ]:
        if io.sha(Path(contract[path_key])) != contract[sha_key]:
            raise ValueError("FROZEN_CONFIRMATION_INPUT_CHANGED")
    if (
        io.sha(Path(metrics.__file__).parent / "alignment_metrics_r3.py")
        != contract["metric_code_sha256"]
    ):
        raise ValueError("FROZEN_METRIC_CHANGED")
    destination = Path(contract_path).parent
    if (destination / "results.private.json").exists() and not replay:
        raise ValueError("USE_SEALED_CONFIRMATION_REPLAY")
    if replay:
        receipt = io.read(destination / "receipt.private.json")
        if receipt["cohort_sha256"] != io.sha(contract_path):
            raise ValueError("FROZEN_COHORT_CHANGED")
        for name, checksum in receipt["output_hashes"].items():
            if io.sha(destination / name) != checksum:
                raise ValueError("SEALED_CONFIRMATION_OUTPUT_CHANGED")
    bundle = candidate.load_bundle(Path(contract["candidate_file"]))
    before = copy.deepcopy(bundle)
    records = io.read(contract["source_file"])
    output = {p: [] for p in ["C00", "C01"]}
    for record in records:
        if record["relevance_full"] != contract["fixed_targets"][record["record_id"]]:
            raise ValueError("TARGET_CHANGED")
        record = {
            **record,
            "relevance_unexpressed": contract["fixed_hidden_targets"][
                record["record_id"]
            ],
        }
        for policy in output:
            row = candidate.offline_case(record, bundle, policy=policy)
            import audit_revelation_r4 as audit

            answers = row["state"]["base_state"]["answers_by_question"]
            initial = sorted(
                set().union(
                    *(
                        audit.canonical_selection(a)
                        for k, a in answers.items()
                        if k in {"Q0", "Q1"}
                    )
                )
            )
            adapted = {
                **row,
                "A": record["A"],
                "initial_selected": initial,
                "selected": {"ASK": row["selected"]},
            }
            row["evaluation"] = metrics.evaluate(
                adapted, [x["candidate_id"] for x in row["ranking"]]
            )
            output[policy].append(row)
    if bundle != before:
        raise ValueError("CONFIRMATION_MUTATED_CANDIDATE_OR_STATISTICS")
    # Runtime yields fixed-universe metric rows and separate trace/cost metadata.
    scored = {p: [r["evaluation"] for r in rows] for p, rows in output.items()}
    summary = {
        "source_id": contract["source_id"],
        "counts": contract["counts"],
        "scope": contract["scope"],
        "comparison": metrics.paired(scored["C00"], scored["C01"]),
        "C00": metrics.aggregate(scored["C00"]),
        "C01": metrics.aggregate(scored["C01"]),
        "fitted_models": 0,
        "candidate_and_coverage_unchanged": True,
        "development_results_not_pooled": True,
        "time": "NOT_EVALUATED",
        "status": "FIXED_EXTERNAL_PROXY_COMPARISON",
    }
    summary["comparison"][
        "scope"
    ] = "Fixed new source, paired actual coffee/product dependency groups; no pooling with R6 development; small-group bootstrap is descriptive only"
    summary["evaluation_panel"] = contract["evaluation_panel"]
    summary["coverage_definitions"] = {
        "aggregate_coverage": "Fixed56 ontology exact target coverage; not generation availability or answer success",
        "generation": "Actual frozen A0 generation subset; unavailable targets remain in primary loss",
        "contributions_and_retention": "Inherited R5 direct/inferred fields use first5 original ranking entries, possibly broad; primary gap/NDCG/Recall use the separate fine-only top5. These are not an additive decomposition of primary alignment.",
    }
    generated = set(bundle["generation_candidate_universe"])
    universe = set(bundle["fixed_evaluation_candidate_universe"])
    summary["generation_target_coverage"] = {
        "generation_fine_count": len(generated),
        "fixed_evaluation_count": len(universe),
        "record_targets_outside_generation": sum(
            len(set(r["relevance_full"]) - generated) for r in records
        ),
        "records_with_targets_outside_generation": sum(
            bool(set(r["relevance_full"]) - generated) for r in records
        ),
        "record_targets_outside_fixed_ontology": sum(
            len(set(r["relevance_full"]) - universe) for r in records
        ),
        "targets_removed": 0,
    }
    summary["group_deltas"] = {
        group: sum(deltas) / len(deltas)
        for group in sorted({r["group_id"] for r in scored["C00"]})
        if (
            deltas := [
                right["raw_gap"] - left["raw_gap"]
                for left, right in zip(scored["C00"], scored["C01"], strict=True)
                if left["group_id"] == group
                and left["raw_gap"] is not None
                and right["raw_gap"] is not None
            ]
        )
    }
    summary["costs"] = {
        p: {
            "ordinary_questions": [r["ordinary_questions"] for r in rows],
            "ordinary_options": [r["ordinary_options"] for r in rows],
            "actual_final_exposure": sum(r["actual_final_exposure"] for r in rows),
            "failures": sum(bool(r.get("failure")) for r in rows),
        }
        for p, rows in output.items()
    }
    if replay:
        if output != io.read(
            destination / "trajectories.private.json"
        ) or summary != io.read(destination / "results.private.json"):
            raise ValueError("CONFIRMATION_REPLAY_DIFFERENCE")
        return {
            "source_id": contract["source_id"],
            "status": "EXACT_SEALED_REPLAY",
            "case_policy_replays": sum(len(rows) for rows in output.values()),
            "new_fits": 0,
        }
    io.save(destination / "trajectories.private.json", output)
    io.save(destination / "results.private.json", summary)
    io.save(
        destination / "receipt.private.json",
        {
            "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "cohort_sha256": io.sha(contract_path),
            "evaluation_code_hashes": evaluation_code_hashes(),
            "output_hashes": {
                name: io.sha(destination / name)
                for name in ["trajectories.private.json", "results.private.json"]
            },
            "fitted_models": 0,
        },
    )
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=["freeze", "evaluate", "replay"])
    p.add_argument("--owner-dir", type=Path, required=True)
    p.add_argument("--records", type=Path)
    p.add_argument("--admission", type=Path)
    p.add_argument("--candidate", type=Path)
    p.add_argument("--contract", type=Path)
    a = p.parse_args()
    value = (
        freeze_cohort(a.owner_dir, a.records, a.admission, a.candidate)
        if a.phase == "freeze"
        else evaluate_cohort(a.owner_dir, a.contract, replay=a.phase == "replay")
    )
    print(json.dumps(value, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
