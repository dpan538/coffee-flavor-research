#!/usr/bin/env python3
"""R6 frozen four-cell acquisition experiment and nested small-head selection."""

from __future__ import annotations
import argparse
import copy
import datetime
import json
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
import run_supervision_r5 as io
import train_supervision_r5 as oldhead
import train_conditioning_r4 as conditioning
from train_coordination_r2 import audit_expert, expert_training_groups

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-sequential-model-v2/revisions/r6"
CELLS = {
    "C00": ("MAP_BASE", "POLICY_BASE"),
    "C10": ("MAP_PATCH", "POLICY_BASE"),
    "C01": ("MAP_BASE", "I2_LIVE"),
    "C11": ("MAP_PATCH", "I2_LIVE"),
}
RIDGES = [0.03, 0.1, 0.3]


def save(path, value):
    io.save(path, value)
    Path(path).parent.chmod(0o700)


def frozen(owner):
    c = io.read(OUT / "experiment_contract.json")
    paths = {
        "source_parse_sha256": owner / "revisions/r5/zenodo_source_parse.private.json",
        "r5_contract_sha256": ROOT
        / "db/data/backend-sequential-model-v2/revisions/r5/experiment_contract.json",
        "r5_metrics_sha256": ROOT
        / "db/data/backend-sequential-model-v2/revisions/r5/metrics.json",
        "metric_code_sha256": ROOT / "db/scripts/alignment_metrics_r3.py",
        "r5_head_code_sha256": ROOT / "db/scripts/train_supervision_r5.py",
    }
    if any(io.sha(p) != c["fixed"][k] for k, p in paths.items()):
        raise ValueError("R6_PRESERVED_INPUT_CHANGED")
    if c["fit"]["ridge_grid"] != RIDGES:
        raise ValueError("R6_UNREGISTERED_GRID")
    return c


def evaluated(row, ranking=None, logits=None):
    if row.get("failure"):
        ranking, logits = [], None
    ranking = row["ranking"] if ranking is None else ranking
    ranking = [r["candidate_id"] if isinstance(r, dict) else r for r in ranking]
    result = oldhead.evaluate(row, ranking, logits)
    result.update(
        failure=row.get("failure"), cell=row.get("cell"), fold=row.get("fold")
    )
    return result


def summarize_cells(cells):
    ids = {c: [r["record_id"] for r in rows] for c, rows in cells.items()}
    if any(len(v) != len(set(v)) or set(v) != set(ids["C00"]) for v in ids.values()):
        raise ValueError("FOUR_CELL_ID_ALIGNMENT_MISMATCH")
    rawbase = {r["record_id"]: r for r in cells["C00"]}
    scored = {c: [evaluated(r) for r in rows] for c, rows in cells.items()}
    summary = {c: oldhead.aggregate(rs) for c, rs in scored.items()}
    contrasts = {
        c + "-C00": oldhead.paired(scored["C00"], scored[c])
        for c in ("C10", "C01", "C11")
    }
    delta_rows = []
    indices = {c: {r["record_id"]: r for r in rows} for c, rows in scored.items()}
    for r in scored["C00"]:
        vals = {c: indices[c][r["record_id"]]["raw_gap"] for c in CELLS}
        delta_rows.append(
            {
                **r,
                "raw_gap": (
                    None
                    if vals["C00"] is None
                    else vals["C11"] - vals["C10"] - vals["C01"] + vals["C00"]
                ),
            }
        )
    zeros = [
        {**r, "raw_gap": None if r["raw_gap"] is None else 0.0} for r in delta_rows
    ]
    contrasts["interaction"] = oldhead.paired(zeros, delta_rows)
    for c, rows in cells.items():
        summary[c]["failures"] = sum(bool(r.get("failure")) for r in rows)
        summary[c]["prediction_changes_vs_C00"] = sum(
            r["ranking"] != rawbase[r["record_id"]]["ranking"] for r in rows
        )
    return {"cells": summary, "contrasts": contrasts}, scored


class Experiment:
    def __init__(self, owner):
        import semantic_mapping_r6 as semantic
        import information_supervision_r6 as information

        self.owner = owner
        self.semantic = semantic
        self.info = information
        self.contract = frozen(owner)
        self.records, self.units = semantic.load_inputs(owner)
        self.records = [r for r in self.records if r["old_split"] == "DEVELOPMENT"]
        self.folds = io.read(owner / "revisions/r1/D0_folds.private.json")
        self.original = io.read(owner / "recovery_records.json")
        self.audits = {}
        self.resources = {}
        self.trajectories = {}
        self.targets = {
            r["record_id"]: {
                "full": r["relevance_full"],
                "hidden": r["relevance_unexpressed"],
            }
            for r in self.records
        }
        self.private = owner / "revisions/r6"

    def expert(self, relative):
        path = self.owner / relative
        ex = io.read(path)
        groups = expert_training_groups(ex)
        if relative not in self.audits:
            train = [r for r in self.original if r["group_id"] in groups]
            held = [r for r in self.original if r["group_id"] not in groups]
            self.audits[relative] = {
                "sha256": io.sha(path),
                **audit_expert(ex, train, held),
            }
        return ex

    def rows(self, records, relative, cell, excluded):
        from r6_mapping_i2_helpers import TrainingB, fit_grouped_coverage

        ex = self.expert(relative)
        eg = expert_training_groups(ex)
        held = {r["group_id"] for r in records} | set(excluded)
        if eg & held:
            raise ValueError("QUESTION_EXPERT_GROUP_LEAKAGE")
        mapping, policy = CELLS[cell]
        key = (relative, mapping)
        if key not in self.resources:
            fitting = [r for r in self.records if r["group_id"] in eg]
            fg = {r["group_id"] for r in fitting}
            patch = (
                self.semantic.fit_patch(self.records, self.units, fg, held)
                if mapping == "MAP_PATCH"
                else None
            )
            mapped = (
                [self.semantic.apply_inputs(r, self.units, patch) for r in fitting]
                if patch
                else fitting
            )
            coverage = fit_grouped_coverage(
                [
                    TrainingB(
                        r["B_observation_unit_id"],
                        r["group_id"],
                        r["sample_id"],
                        frozenset(r["B"]),
                    )
                    for r in mapped
                ],
                evaluation_groups=frozenset(held),
            )
            self.resources[key] = {
                "patch": patch,
                "coverage": coverage,
                "training_groups": sorted(fg),
                "expert_path": relative,
                "expert_sha256": io.sha(self.owner / relative),
                "mapping": mapping,
            }
        resource = self.resources[key]
        if held & set(resource["training_groups"]):
            raise ValueError("COVERAGE_MAPPING_TRAIN_LEAKAGE")
        bundle = conditioning.model_bundle(ex)
        if not set(bundle["fixed_candidates"]) <= set(oldhead.CANDIDATES):
            raise ValueError("UNREGISTERED_GENERATED_CANDIDATE")
        rows = []
        for record in records:
            cachekey = (record["record_id"], relative, cell)
            if cachekey not in self.trajectories:
                mapped = (
                    self.semantic.apply_inputs(record, self.units, resource["patch"])
                    if resource["patch"]
                    else copy.deepcopy(record)
                )
                if (
                    mapped["relevance_full"] != record["relevance_full"]
                    or mapped["relevance_unexpressed"]
                    != record["relevance_unexpressed"]
                ):
                    raise ValueError("PATCH_MUTATED_EVALUATION_TARGET")
                row = self.info.generate_case(
                    mapped,
                    bundle,
                    resource["coverage"],
                    policy,
                    fold=self.folds[record["group_id"]],
                )
                import alignment_metrics_r3 as metric

                row["evaluation_universe"] = oldhead.CANDIDATES
                row["frozen_A0_generation_universe"] = bundle["fixed_candidates"]
                row["metrics"] = metric.evaluate(
                    row["ranking"], row["full_T"], oldhead.CANDIDATES
                )
                row["hidden_metrics"] = metric.evaluate(
                    row["ranking"], row["hidden_T"], oldhead.CANDIDATES
                )
                row.update(
                    cell=cell,
                    base_training_groups=sorted(eg),
                    input_training_groups=resource["training_groups"],
                    source_A=record["A"],
                    source_B=record["B"],
                )
                if policy == "I2_LIVE" and "/r1/cv/" in relative:
                    old = self.info.old_i2_diagnostic(
                        mapped, bundle, resource["coverage"]
                    )
                    row["old_full_A_trajectory_different"] = (
                        old["questions"] != row["questions"]
                    )
                    row["old_full_A_trajectory"] = old
                row["A"] = record[
                    "A"
                ]  # legacy hidden recovery reference remains frozen source A
                row["mapping_audit"] = mapped.get("mapping_input_trace", [])
                if (
                    row["full_T"] != self.targets[record["record_id"]]["full"]
                    or row["hidden_T"] != self.targets[record["record_id"]]["hidden"]
                ):
                    raise ValueError("INFORMATION_TARGET_CHANGED")
                self.trajectories[cachekey] = row
            rows.append(copy.deepcopy(self.trajectories[cachekey]))
        return rows

    def outer_path(self, o):
        return f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{o}.model.json"

    def inner_path(self, o, i):
        return f"revisions/r2/models/R2_R1_EXPERT_outer{o}_inner{i}.model.json"

    def deepest_path(self, o, i, d):
        return f"revisions/r3/models/R3_R1_EXPERT_outer{o}_inner{i}_deeper{d}_P1_INTERNAL.model.json"

    def inner_splits(self, o):
        train = [r for r in self.records if self.folds[r["group_id"]] != o]
        held = {r["group_id"] for r in self.records if self.folds[r["group_id"]] == o}
        seen = []
        splits = []
        for i in range(2):
            path = self.inner_path(o, i)
            eg = expert_training_groups(self.expert(path))
            fitting = [r for r in train if r["group_id"] in eg]
            validating = [r for r in train if r["group_id"] not in eg]
            seen.extend(r["record_id"] for r in validating)
            splits.append((i, path, fitting, validating, held))
        if sorted(seen) != sorted(r["record_id"] for r in train):
            raise ValueError("INNER_PARTITION_NOT_EXACT")
        return splits

    def seal_inputs(self, prefix="matrix", destination=None):
        directory = destination or self.private
        save(directory / "source_inputs.private.json", self.records)
        save(directory / (prefix + "_reused_expert_audits.private.json"), self.audits)
        save(
            directory / (prefix + "_input_resources.private.json"),
            [{"key": list(k), **v} for k, v in self.resources.items()],
        )


def matrix(owner, destination=None):
    exp = Experiment(owner)
    private = destination or exp.private
    if (private / "matrix_receipt.private.json").exists():
        raise ValueError("SEALED_MATRIX_EXISTS")
    started = io.now()
    cells = {c: [] for c in CELLS}
    nested = {}
    for o in range(3):
        held = [r for r in exp.records if exp.folds[r["group_id"]] == o]
        for c in CELLS:
            cells[c] += exp.rows(held, exp.outer_path(o), c, set())
        nested[str(o)] = {c: [] for c in CELLS}
        for i, path, _, val, outerheld in exp.inner_splits(o):
            for c in CELLS:
                rows = exp.rows(val, path, c, outerheld)
                for r in rows:
                    r["inner"] = i
                nested[str(o)][c] += rows
        print(
            json.dumps(
                {
                    "checkpoint": "R6_FROZEN_A0_OUTER_COMPLETE",
                    "outer": o,
                    "records": len(held),
                }
            ),
            flush=True,
        )
    for c in cells:
        cells[c].sort(key=lambda r: r["record_id"])
    summary, scored = summarize_cells(cells)
    summary["inner_selection"] = {
        o: summarize_cells(
            {c: sorted(rs, key=lambda r: r["record_id"]) for c, rs in cs.items()}
        )[0]
        for o, cs in nested.items()
    }
    import evaluate_sequential_v2 as legacy_eval

    b2 = []
    for row in cells["C00"]:
        ex = exp.expert(exp.outer_path(row["fold"]))
        base = legacy_eval.baseline_bundle(ex)
        payload = legacy_eval.legacy_payload(row["state"]["base_state"], base)
        live = legacy_eval.legacy.run(dict(payload, model="B2"), base)
        ranking = [r["candidate_id"] for r in live["candidate_state"]["candidates"]]
        b2.append(evaluated(row, ranking))
    summary["B2_compatible_transport"] = {
        "metrics": oldhead.aggregate(b2),
        "scope": "Frozen original B2 algorithm with outer TRAIN-only transported priors and same C00 actual offered answers; old family adapter loses unsupported concepts; full fixed T and fixed universe retain that loss; not relabeled A0 or deployed B2 validation",
    }
    scored["B2_compatible_transport"] = b2
    summary["primary_scope"] = (
        "Development coffee-held cross-grader corroboration; fixed T; no real user/time confirmation"
    )
    save(private / "matrix_cases.private.json", cells)
    save(private / "matrix_nested.private.json", nested)
    save(private / "matrix_predictions.private.json", scored)
    save(private / "matrix_summary.private.json", summary)
    exp.seal_inputs()
    receipt = {
        "started_utc": started,
        "completed_utc": io.now(),
        "new_scorer_fits": 0,
        "contract_sha256": io.sha(OUT / "experiment_contract.json"),
        "artifacts": {p.name: io.sha(p) for p in private.glob("matrix_*.private.json")},
    }
    save(private / "matrix_receipt.private.json", receipt)
    io.save(
        OUT / "results.json",
        {
            "checkpoint1": summary,
            "checkpoint2": "PENDING_ACTUAL_REFIT",
            "default": "B2_UNCHANGED_FOUNDATION_CHECK_OFF",
        },
        False,
    )
    return summary


def choose(scores, order):
    known = [(k, scores[k]) for k in order if scores.get(k) is not None]
    if not known:
        raise ValueError("NO_IDENTIFIABLE_SELECTION_REFERENCE")
    minimum = min(v for _, v in known)
    return next(k for k, v in known if v <= minimum + 1e-12)


def verify_matrix(owner):
    frozen(owner)
    private = owner / "revisions/r6"
    receipt = io.read(private / "matrix_receipt.private.json")
    if receipt["contract_sha256"] != io.sha(OUT / "experiment_contract.json"):
        raise ValueError("MATRIX_CONTRACT_CHANGED")
    for name, expected in receipt["artifacts"].items():
        if io.sha(private / name) != expected:
            raise ValueError("SEALED_MATRIX_ARTIFACT_CHANGED:" + name)
    return receipt


def training(owner, destination=None):
    import train_supervision_r6 as head

    exp = Experiment(owner)
    private = exp.private
    dst = destination or private / "training"
    if (dst / "receipt.private.json").exists():
        raise ValueError("SEALED_TRAINING_EXISTS")
    if not (private / "matrix_receipt.private.json").exists():
        raise ValueError("FOUR_CELLS_MUST_FINISH_BEFORE_FIT")
    verify_matrix(owner)
    started = io.now()
    outer = io.read(private / "matrix_cases.private.json")
    nested = io.read(private / "matrix_nested.private.json")
    choices = []
    out = {
        k: []
        for k in ("selected_A0", "selected_R5_head", "selected_R6_head", "C00_R5_head")
    }
    modelpaths = []
    inner_scores = []

    def fit(rows, ridge, tag):
        model = head.fit(
            [r for r in rows if not r.get("failure")],
            "T2",
            {
                "R6_contract_sha256": io.sha(OUT / "experiment_contract.json"),
                "tag": tag,
            },
            ridge=ridge,
        )
        path = dst / "models" / (tag + ".json")
        save(path, model)
        modelpaths.append(path)
        return model

    def evaluate_rows(rows, model, old=False):
        module = oldhead if old else head
        return [
            (
                evaluated(r, [])
                if r.get("failure")
                else evaluated(r, *module.predict(r, model))
            )
            for r in rows
        ]

    for o in range(3):
        base_scores = {
            c: oldhead.aggregate([evaluated(r) for r in nested[str(o)][c]])["raw_gap"]
            for c in CELLS
        }
        cell = choose(base_scores, list(CELLS))
        ridge_rows = {str(r): [] for r in RIDGES}
        for i, path, fitting, val, outerheld in exp.inner_splits(o):
            frows = []
            seen = []
            excluded = outerheld | {r["group_id"] for r in val}
            for d in range(2):
                dpath = exp.deepest_path(o, i, d)
                dg = expert_training_groups(exp.expert(dpath))
                dh = [r for r in fitting if r["group_id"] not in dg]
                seen.extend(r["record_id"] for r in dh)
                frows += exp.rows(dh, dpath, cell, excluded)
            if sorted(seen) != sorted(r["record_id"] for r in fitting):
                raise ValueError("DEEP_PARTITION_NOT_EXACT")
            vrows = [r for r in nested[str(o)][cell] if r["inner"] == i]
            if {r["group_id"] for r in frows} & {r["group_id"] for r in vrows}:
                raise ValueError("HEAD_INNER_GROUP_LEAKAGE")
            for ridge in RIDGES:
                model = fit(frows, ridge, f"outer{o}_inner{i}_ridge{ridge}")
                scores = evaluate_rows(vrows, model)
                ridge_rows[str(ridge)] += scores
                inner_scores.append(
                    {
                        "outer": o,
                        "inner": i,
                        "cell": cell,
                        "ridge": ridge,
                        "train": oldhead.aggregate(evaluate_rows(frows, model)),
                        "validation": oldhead.aggregate(scores),
                        "training_groups": len({r["group_id"] for r in frows}),
                        "validation_groups": len({r["group_id"] for r in vrows}),
                    }
                )
        losses = {r: oldhead.aggregate(rs)["raw_gap"] for r, rs in ridge_rows.items()}
        ridge = float(choose(losses, ["0.1", "0.3", "0.03"]))
        frows = nested[str(o)][cell]
        held = [r for r in outer[cell] if r["fold"] == o]
        model = fit(frows, ridge, f"R6_outer{o}")
        old = io.read(owner / f"revisions/r5/training/models/T2_AB_outer{o}.json")
        if set(old["training_groups"]) & {r["group_id"] for r in held}:
            raise ValueError("OLD_HEAD_HELD_LEAKAGE")
        out["selected_A0"] += [evaluated(r) for r in held]
        out["selected_R5_head"] += evaluate_rows(held, old, True)
        out["selected_R6_head"] += evaluate_rows(held, model)
        out["C00_R5_head"] += evaluate_rows(
            [r for r in outer["C00"] if r["fold"] == o], old, True
        )
        choices.append(
            {
                "outer": o,
                "selected_cell": cell,
                "cell_selection_raw_gap": base_scores,
                "selected_ridge": ridge,
                "ridge_selection_raw_gap": losses,
                "fit_training": oldhead.aggregate(evaluate_rows(frows, model)),
            }
        )
        print(
            json.dumps(
                {"checkpoint": "R6_ACTUAL_NESTED_REFIT_OUTER_COMPLETE", **choices[-1]}
            ),
            flush=True,
        )
    # Final development choice uses only the registered inner-selection evidence.
    eligible_cells = [c for c in CELLS if any(r["selected_cell"] == c for r in choices)]
    final_cell = choose(
        {
            c: float(np.mean([r["cell_selection_raw_gap"][c] for r in choices]))
            for c in eligible_cells
        },
        eligible_cells,
    )
    # Cell-dependent ridge validation is only eligible when the corresponding cell was used.
    eligible = [r for r in choices if r["selected_cell"] == final_cell]
    if not eligible:
        raise ValueError("FINAL_CELL_HAS_NO_REGISTERED_RIDGE_VALIDATION")
    final_ridge = float(
        choose(
            {
                str(r): float(
                    np.mean([x["ridge_selection_raw_gap"][str(r)] for x in eligible])
                )
                for r in RIDGES
            },
            ["0.1", "0.3", "0.03"],
        )
    )
    final = fit(outer[final_cell], final_ridge, "R6_RESEARCH_HEAD")
    summary = {
        "selection": choices,
        "final_candidate": {
            "cell": final_cell,
            "ridge": final_ridge,
            "selection_scope": "Repeatedly viewed development data; no fresh confirmation",
        },
        "models": {k: oldhead.aggregate(v) for k, v in out.items()},
        "comparisons": {
            "refit_minus_same_inputs_old_head": oldhead.paired(
                out["selected_R5_head"], out["selected_R6_head"]
            ),
            "refit_minus_selected_frozen_A0": oldhead.paired(
                out["selected_A0"], out["selected_R6_head"]
            ),
            "full_pipeline_minus_C00_old_head": oldhead.paired(
                out["C00_R5_head"], out["selected_R6_head"]
            ),
        },
        "inner_fit_diagnostics": inner_scores,
        "default": "B2_UNCHANGED_FOUNDATION_CHECK_OFF",
        "trigger_refits": 0,
    }
    save(dst / "predictions.private.json", out)
    save(dst / "summary.private.json", summary)
    save(
        dst / "inner_training_trajectories.private.json",
        list(exp.trajectories.values()),
    )
    exp.seal_inputs("training", dst if destination is not None else None)
    save(
        dst / "receipt.private.json",
        {
            "started_utc": started,
            "completed_utc": io.now(),
            "models": {str(p.relative_to(dst)): io.sha(p) for p in modelpaths},
            "matrix_sha256": io.sha(private / "matrix_cases.private.json"),
            "summary_sha256": io.sha(dst / "summary.private.json"),
            "contract_sha256": io.sha(OUT / "experiment_contract.json"),
        },
    )
    if destination is None:
        public = io.read(OUT / "results.json")
        public["checkpoint2"] = summary
        io.save(OUT / "results.json", public, False)
    return summary


def bundle(owner):
    import semantic_mapping_r6 as semantic
    import information_supervision_r6 as info
    import train_supervision_r6 as head

    private = owner / "revisions/r6"
    summary = io.read(private / "training/summary.private.json")
    model = io.read(private / "training/models/R6_RESEARCH_HEAD.json")
    head.check_model(model)
    records, units = semantic.load_inputs(owner)
    groups = {r["group_id"] for r in records}
    cell = summary["final_candidate"]["cell"]
    mapping, policy = CELLS[cell]
    patch = (
        semantic.fit_patch(records, units, groups) if mapping == "MAP_PATCH" else None
    )
    mapped = (
        [semantic.apply_inputs(r, units, patch) for r in records] if patch else records
    )
    base = conditioning.model_bundle(
        io.read(owner / "revisions/r4/models/R4_ALL_DEVELOPMENT_RESEARCH.model.json")[
            "r1_expert"
        ]
    )
    value = {
        "version": "m2-r6.research-runtime.v1",
        "contract_sha256": io.sha(OUT / "experiment_contract.json"),
        "head": model,
        "question_bundle": base,
        "mapping": mapping,
        "mapping_patch": patch,
        "coverage": info.coverage_for(mapped, set()),
        "policy": policy,
        "cell": cell,
        "information_protocol": info.protocol(),
        "mapping_protocol": semantic.protocol(),
        "default": "B2_UNCHANGED_FOUNDATION_CHECK_OFF",
        "final_scope": "R6 head read-only acquired-observation ranking; unchanged R4 final exposure/feedback is separate and never used as head success evidence",
    }
    save(private / "R6_RESEARCH_BUNDLE.private.json", value)
    save(
        private / "bundle_hash.private.json",
        {"sha256": io.sha(private / "R6_RESEARCH_BUNDLE.private.json")},
    )
    return {
        "bundle_sha256": io.sha(private / "R6_RESEARCH_BUNDLE.private.json"),
        "cell": cell,
        "ridge": model["ridge"],
    }


def infer(owner, request):
    import information_supervision_r6 as info
    import train_supervision_r6 as head
    import flavor_conditioning_r4 as rt
    import audit_revelation_r4 as audit

    frozen(owner)
    import semantic_mapping_r6 as semantic

    bp = owner / "revisions/r6/R6_RESEARCH_BUNDLE.private.json"
    if io.sha(bp) != io.read(owner / "revisions/r6/bundle_hash.private.json")["sha256"]:
        raise ValueError("LIVE_BUNDLE_HASH_CHANGED")
    b = io.read(bp)
    if b["mapping_protocol"] != semantic.protocol():
        raise ValueError("LIVE_MAPPING_PROTOCOL_CHANGED")
    if b["mapping_patch"] is not None:
        semantic.check_patch(b["mapping_patch"])
    if (
        b["contract_sha256"] != io.sha(OUT / "experiment_contract.json")
        or b["information_protocol"] != info.protocol()
    ):
        raise ValueError("LIVE_FROZEN_CONTRACT_CHANGED")
    if (
        not isinstance(request, dict)
        or set(request)
        - {"contract_version", "context", "answers", "final_comparison", "final_mode"}
        or request.get("contract_version") != b["version"]
    ):
        raise ValueError("R6_LIVE_REQUEST_SCHEMA")
    if not isinstance(request.get("answers", []), list):
        raise ValueError("ANSWERS_MUST_BE_LIST")
    state = info.initial_state(request["context"], b["question_bundle"])
    for answer in request.get("answers", []):
        if not isinstance(answer, dict):
            raise ValueError("ANSWER_MUST_BE_OBJECT")
        if answer.get("slot") not in state["base_state"]["answers_by_question"]:
            state, plan = info.select(
                state, b["question_bundle"], b["coverage"], b["policy"]
            )
            if plan["action"] != "ASK":
                raise ValueError("ANSWER_AFTER_Q4_ENDPOINT")
        state = info.update(state, answer, b["question_bundle"])
    state, plan = info.select(state, b["question_bundle"], b["coverage"], b["policy"])
    answers = state["base_state"]["answers_by_question"]
    initial = sorted(
        set().union(
            *(
                audit.canonical_selection(a)
                for k, a in answers.items()
                if k in {"Q0", "Q1"}
            )
        )
    )
    acquired = sorted(
        set().union(*(audit.canonical_selection(a) for a in answers.values()))
    )
    ranking, _ = head.predict(
        {"initial_selected": initial, "selected": {"ASK": acquired}}, b["head"]
    )
    product = rt.finalize_result(state, b["question_bundle"])
    if request.get("final_comparison") is not None:
        state = rt.apply_final_comparison(
            product["state"],
            request["final_comparison"],
            b["question_bundle"],
            request.get("final_mode", "F2"),
        )
        product = rt.finalize_result(state, b["question_bundle"])
    return {
        "contract_version": b["version"],
        "default": "B2_UNCHANGED_FOUNDATION_CHECK_OFF",
        "selected_research_cell": b["cell"],
        "stage": product["stage"],
        "next": plan if product["stage"] != "FINAL_RESULT" else {"action": "STOP"},
        "validated_existing_final_workflow": product,
        "research_head": {
            "main": ranking[:5] if "Q4" in answers else [],
            "secondary": ranking[5:8] if "Q4" in answers else [],
            "scope": b["final_scope"],
            "real_feedback_evaluated": False,
            "input_mode": "CANONICAL_EXPOSED_OPTION_IDS_ONLY; source-text patch belongs to training/answer-provider lineage, not an unverified free-text parser",
        },
        "costs": {
            "ordinary_questions": len(answers),
            "ordinary_options": sum(
                len(a["shown_option_ids"]) for a in answers.values()
            ),
            "final_exposed_candidates": (
                len(request["final_comparison"]["exposed_candidates"])
                if request.get("final_comparison")
                else len((product.get("exposure") or {}).get("candidate_ids", []))
            ),
            "final_exposure_counting": "One delivered JSON ballot; resubmitting its feedback does not create another exposure",
        },
    }


def replay(owner):
    import train_supervision_r6 as head

    private = owner / "revisions/r6"
    frozen(owner)
    receipt = io.read(private / "matrix_receipt.private.json")
    if receipt["contract_sha256"] != io.sha(OUT / "experiment_contract.json"):
        raise ValueError("MATRIX_CONTRACT_CHANGED")
    for name, sha in receipt["artifacts"].items():
        if io.sha(private / name) != sha:
            raise ValueError("MATRIX_ARTIFACT_CHANGED:" + name)
    cells = io.read(private / "matrix_cases.private.json")
    expected = io.read(private / "matrix_predictions.private.json")
    count = 0
    for c, rows in cells.items():
        actual = [evaluated(r) for r in rows]
        if actual != expected[c]:
            raise ValueError("SEALED_MATRIX_METRICS_CHANGED")
        count += len(actual)
    tr = io.read(private / "training/receipt.private.json")
    if tr["matrix_sha256"] != io.sha(private / "matrix_cases.private.json") or tr[
        "summary_sha256"
    ] != io.sha(private / "training/summary.private.json"):
        raise ValueError("TRAINING_INPUT_OR_SUMMARY_CHANGED")
    for path, sha in tr["models"].items():
        if io.sha(private / "training" / path) != sha:
            raise ValueError("SEALED_MODEL_CHANGED")
        head.check_model(io.read(private / "training" / path))
    scores = io.read(private / "training/predictions.private.json")
    summary = io.read(private / "training/summary.private.json")
    actual = []
    for choice in summary["selection"]:
        o = choice["outer"]
        model = io.read(private / f"training/models/R6_outer{o}.json")
        rows = [r for r in cells[choice["selected_cell"]] if r["fold"] == o]
        actual += [
            (
                evaluated(r, [])
                if r.get("failure")
                else evaluated(r, *head.predict(r, model))
            )
            for r in rows
        ]
    if actual != scores["selected_R6_head"]:
        raise ValueError("SEALED_REFIT_PREDICTIONS_CHANGED")
    verified = verify_completion(owner)
    return {
        "status": "PASS",
        **verified,
        "frozen_matrix_predictions": count,
        "refitted_outer_predictions": len(actual),
        "checked_models": len(tr["models"]),
        "fit_count": 0,
        "checked_utc": io.now(),
    }


def retrain(owner):
    import data_supervision_r5 as source
    import semantic_mapping_r6 as semantic

    verify_matrix(owner)
    started = io.now()
    private = owner / "revisions/r6"
    parsed = source.parse_source(owner)
    if source.contract_parse_digest(parsed) != source.contract_parse_digest(
        io.read(owner / "revisions/r5/zenodo_source_parse.private.json")
    ):
        raise ValueError("RAW_SOURCE_REBUILD_MISMATCH")
    exp = Experiment(owner)
    original = io.read(private / "matrix_cases.private.json")
    nested = io.read(private / "matrix_nested.private.json")
    rebuilt = {c: [] for c in CELLS}
    inner = {}
    for o in range(3):
        held = [r for r in exp.records if exp.folds[r["group_id"]] == o]
        for c in CELLS:
            rebuilt[c] += exp.rows(held, exp.outer_path(o), c, set())
        inner[str(o)] = {c: [] for c in CELLS}
        for i, path, _, val, excluded in exp.inner_splits(o):
            for c in CELLS:
                rows = exp.rows(val, path, c, excluded)
                for r in rows:
                    r["inner"] = i
                inner[str(o)][c] += rows
    for rows in rebuilt.values():
        rows.sort(key=lambda r: r["record_id"])
    if rebuilt != original or inner != nested:
        raise ValueError("RAW_SOURCE_TRAJECTORY_REBUILD_MISMATCH")
    dst = (
        private
        / "retrains"
        / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    )
    training(owner, dst)
    reference = io.read(private / "training/receipt.private.json")
    actual = io.read(dst / "receipt.private.json")
    exact = reference["models"] == actual["models"]
    if not exact:
        raise ValueError("RETRAIN_MODELS_NOT_IDENTICAL")
    value = {
        "status": "PASS",
        "started_utc": started,
        "completed_utc": io.now(),
        "raw_source_reparsed": True,
        "four_cell_outer_and_nested_trajectories_exact": True,
        "refitted_models_bitwise_exact": len(actual["models"]),
        "destination": str(dst),
        "not_artifact_replay": True,
    }
    save(dst / "retrain_verification.private.json", value)
    return value


def live_check(owner):
    import information_supervision_r6 as info
    import information_supervision_r5 as oldinfo
    import flavor_conditioning_r4 as rt
    import flavor_m2_r1 as r1

    b = io.read(owner / "revisions/r6/R6_RESEARCH_BUNDLE.private.json")
    base = b["question_bundle"]
    payload = {
        "contract_version": b["version"],
        "context": {"c0": r1.C0[0], "c1": "medium"},
        "answers": [],
    }
    state = info.initial_state(payload["context"], base)
    # Explicit engineering observations only, not new human feedback or evaluation coffee.
    for slot in info.BUDGETS:
        state, plan = info.select(state, base, b["coverage"], b["policy"])
        answer = oldinfo.source_answer(
            plan["question"],
            ["attribute.fruity", "sensory.apple", "broad.chocolate"],
            base["r1_expert"],
        )
        payload["answers"].append(answer)
        state = info.update(state, answer, base)
    pre = infer(owner, payload)
    ex = pre["validated_existing_final_workflow"]["exposure"]
    payload["final_comparison"] = {
        "exposed_candidates": ex["candidate_ids"],
        "selected_candidates": ex["candidate_ids"][:1],
        "feedback_source": "SIMULATED",
        "generation_version": base["bundle_id"],
    }
    final = infer(owner, payload)
    if final["stage"] != "FINAL_RESULT" or final["costs"]["ordinary_options"] != 19:
        raise ValueError("LIVE_ENDPOINT_OR_BUDGET_FAILURE")
    duplicate = infer(
        owner, {**payload, "answers": payload["answers"] + [payload["answers"][-1]]}
    )
    if duplicate != final:
        raise ValueError("DUPLICATE_Q4_NOT_IDEMPOTENT")
    finalstate = final["validated_existing_final_workflow"]["state"]
    try:
        rt.apply_final_comparison(finalstate, payload["final_comparison"], base)
    except ValueError as e:
        if str(e) != "FINAL_COMPARISON_ALREADY_USED":
            raise
    else:
        raise ValueError("SECOND_FINAL_ACCEPTED")
    rejected = []
    for context in ({"c0": r1.C0[0]}, {"c0": r1.C0[0], "c1": None}, {"c1": "medium"}):
        try:
            infer(owner, {**payload, "context": context})
        except ValueError:
            rejected.append(context)
        else:
            raise ValueError("INVALID_CONTEXT_ACCEPTED")
    save(owner / "revisions/r6/live_request.private.json", payload)
    save(owner / "revisions/r6/live_result.private.json", final)
    return {
        "status": "PASS",
        "stage": final["stage"],
        "questions": 5,
        "options": 19,
        "final_candidates": len(ex["candidate_ids"]),
        "second_final_rejected": True,
        "duplicate_Q4_idempotent": True,
        "session_scope": "Stateless transcript replay: one final per transcript; no cross-request persistence claim",
        "invalid_contexts_rejected": len(rejected),
        "scope": "ENGINEERING_FIXTURE_NOT_HUMAN_SENSORY_EVIDENCE",
    }


def complete_outputs(owner):
    """Recompute exact held rankings for every published comparison, without fitting."""
    import train_supervision_r6 as head
    import evaluate_sequential_v2 as legacy_eval

    private = owner / "revisions/r6"
    cells = io.read(private / "matrix_cases.private.json")
    summary = io.read(private / "training/summary.private.json")
    output = {c: [] for c in CELLS}
    output["B2_compatible_transport"] = []

    def one(row, ranking, logits=None):
        ids = [r["candidate_id"] if isinstance(r, dict) else r for r in ranking]
        if row.get("failure"):
            ids, logits = [], None
        return {
            "record_id": row["record_id"],
            "group_id": row["group_id"],
            "ranking": ids,
            "logits": None if logits is None else np.asarray(logits).tolist(),
            "metrics": evaluated(row, ids, logits),
        }

    for c, rows in cells.items():
        output[c] = [one(r, r["ranking"]) for r in rows]
    for row in cells["C00"]:
        ex = io.read(
            owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{row['fold']}.model.json"
        )
        b = legacy_eval.baseline_bundle(ex)
        payload = legacy_eval.legacy_payload(row["state"]["base_state"], b)
        live = legacy_eval.legacy.run(dict(payload, model="B2"), b)
        output["B2_compatible_transport"].append(
            one(row, live["candidate_state"]["candidates"])
        )
    for key in ["selected_A0", "selected_R5_head", "selected_R6_head", "C00_R5_head"]:
        output[key] = []
    for choice in summary["selection"]:
        o = choice["outer"]
        rows = [r for r in cells[choice["selected_cell"]] if r["fold"] == o]
        old = io.read(owner / f"revisions/r5/training/models/T2_AB_outer{o}.json")
        new = io.read(private / f"training/models/R6_outer{o}.json")
        output["selected_A0"] += [one(r, r["ranking"]) for r in rows]
        output["selected_R5_head"] += [one(r, *oldhead.predict(r, old)) for r in rows]
        output["selected_R6_head"] += [one(r, *head.predict(r, new)) for r in rows]
        output["C00_R5_head"] += [
            one(r, *oldhead.predict(r, old)) for r in cells["C00"] if r["fold"] == o
        ]
    return output


def seal(owner):
    private = owner / "revisions/r6"
    verify_matrix(owner)
    outputs = complete_outputs(owner)
    save(private / "exact_rankings_and_logits.private.json", outputs)
    files = [
        p
        for p in private.rglob("*.json")
        if "retrains" not in p.parts and p.name != "completion_manifest.private.json"
    ]
    paths = sorted(ROOT.joinpath("db/scripts").glob("*r6.py")) + [
        ROOT / "db/scripts/r6_mapping_i2_helpers.py",
        ROOT / "db/tests/test_semantic_mapping_r6.py",
    ]
    inherited = [
        "alignment_metrics_r3.py",
        "train_supervision_r5.py",
        "data_supervision_r5.py",
        "information_supervision_r5.py",
        "flavor_m2_r1.py",
        "flavor_conditioning_r4.py",
        "audit_revelation_r4.py",
        "train_conditioning_r4.py",
        "train_coordination_r2.py",
    ]
    paths += [ROOT / "db/scripts" / n for n in inherited]
    source = [
        owner / "revisions/r1/D0_folds.private.json",
        owner / "recovery_records.json",
        owner / "revisions/r5/zenodo_source_parse.private.json",
    ]
    source += [
        owner / f"revisions/r5/training/models/T2_AB_outer{o}.json" for o in range(3)
    ]
    for name in [
        "matrix_reused_expert_audits.private.json",
        "training_reused_expert_audits.private.json",
    ]:
        source += [owner / path for path in io.read(private / name)]
    manifest = {
        "sealed_utc": io.now(),
        "contract_sha256": io.sha(OUT / "experiment_contract.json"),
        "private_artifacts": {
            str(p.relative_to(private)): io.sha(p) for p in sorted(set(files))
        },
        "code_sha256": {
            str(p.relative_to(ROOT)): io.sha(p) for p in sorted(set(paths))
        },
        "inherited_input_sha256": {
            str(p.relative_to(owner)): io.sha(p) for p in sorted(set(source))
        },
        "scope": "All retained comparison rankings/logits, targets, input resources, fold assignments, private weights and inherited models; no raw data release",
    }
    save(private / "completion_manifest.private.json", manifest)
    return {
        "manifest_sha256": io.sha(private / "completion_manifest.private.json"),
        "private_artifacts": len(files),
    }


def verify_completion(owner):
    private = owner / "revisions/r6"
    m = io.read(private / "completion_manifest.private.json")
    if io.sha(OUT / "experiment_contract.json") != m["contract_sha256"]:
        raise ValueError("COMPLETION_CONTRACT_CHANGED")
    for field, root in [
        ("private_artifacts", private),
        ("code_sha256", ROOT),
        ("inherited_input_sha256", owner),
    ]:
        for path, sha in m[field].items():
            if io.sha(root / path) != sha:
                raise ValueError("COMPLETION_HASH_CHANGED:" + path)
    actual = complete_outputs(owner)
    if actual != io.read(private / "exact_rankings_and_logits.private.json"):
        raise ValueError("EXACT_RANKING_LOGITS_REPLAY_CHANGED")
    matrix = io.read(private / "matrix_predictions.private.json")
    training_scores = io.read(private / "training/predictions.private.json")
    for name, expected in {**matrix, **training_scores}.items():
        if [r["metrics"] for r in actual[name]] != expected:
            raise ValueError("PUBLISHED_CONTROL_REPLAY_MISMATCH:" + name)
    return {
        "all_comparison_rows": sum(len(rows) for rows in actual.values()),
        "rankings_logits_exact": True,
        "all_published_controls_verified": True,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "phase",
        choices=[
            "matrix",
            "train",
            "bundle",
            "replay",
            "retrain",
            "live-check",
            "infer",
            "seal",
        ],
    )
    p.add_argument("--owner-dir", type=Path, required=True)
    p.add_argument("--request", type=Path)
    args = p.parse_args()
    with threadpool_limits(limits=1):
        if args.phase == "infer":
            if args.request is None:
                raise ValueError("REQUEST_JSON_REQUIRED")
            value = infer(args.owner_dir, io.read(args.request))
        else:
            value = {
                "matrix": matrix,
                "train": training,
                "bundle": bundle,
                "replay": replay,
                "retrain": retrain,
                "live-check": live_check,
                "seal": seal,
            }[args.phase](args.owner_dir)
    print(json.dumps(value, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
