#!/usr/bin/env python3
"""Verify retained R1 models through the live JSON entry; no synthetic accuracy."""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

import flavor_m2_r1 as backend
import flavor_foundation_r1 as foundation
from infer_m2_r1 import run
from run_m2_r1 import OUT, ROOT, freeze, read, save, sha


def verify(owner):
    freeze(owner)  # Verify the immutable D0 hashes before any replay.
    private = owner / "revisions/r1"
    models = ["M2_R1_FINAL_FIXED", "M2_R1_FOUNDATION", "M2_R1_FOUNDATION_CHECK"]
    results = {}
    for name in models:
        model_path = private / "models" / (name + ".model.json")
        bundle = read(model_path)
        latencies, sessions, cli_comparisons = [], 0, 0
        paths = (
            ["P1"] if bundle.get("foundation_check_enabled") else list(backend.PATHS)
        )
        for c0 in backend.C0:
            for c1 in backend.C1:
                for path in paths:
                    request = {
                        "contract_version": backend.VERSIONS["contract_version"],
                        "context": {"c0": c0, "c1": c1},
                        "path": path,
                        "answers": [],
                    }
                    response = run(request, bundle)
                    while response["next"]["action"] == "ASK":
                        q = response["next"]["question"]
                        assert len(q["shown_option_ids"]) <= 4
                        answer = {
                            key: q[key]
                            for key in [
                                "slot",
                                "question_id",
                                "axis",
                                "shown_option_ids",
                            ]
                        }
                        # Mechanical contract exercise, not a sensory judgment.
                        answer.update(
                            state="SELECTED",
                            selected_option_ids=q["shown_option_ids"][:1],
                        )
                        request["answers"].append(answer)
                        assert len(request["answers"]) <= 6
                        response = run(request, bundle)
                    assert response["stage"] == "PRELIMINARY_RESULT"
                    assert (
                        len(response["main"]) <= 5 and len(response["secondary"]) <= 3
                    )
                    if bundle.get("foundation_check_enabled"):
                        checks = [
                            a
                            for a in request["answers"]
                            if a["axis"].startswith("foundation.")
                        ]
                        assert len(checks) == 1 and checks[0]["slot"] == "Q3"
                    repeated = copy.deepcopy(request)
                    repeated["answers"].append(request["answers"][-1])
                    assert run(repeated, bundle) == response
                    batched = dict(
                        request,
                        answers=[request["answers"][:2], request["answers"][2:]],
                    )
                    assert run(batched, bundle) == response
                    exposure = response["exposure"]
                    assert exposure["eligible_for_final_comparison"]
                    ids = exposure["candidate_ids"]
                    assert 3 <= len(ids) <= 8
                    request["final_comparison"] = {
                        "exposed_candidates": ids,
                        "selected_candidates": ids[:2],
                        "feedback_source": "SIMULATED",
                        "generation_version": bundle["bundle_id"],
                    }
                    start = time.perf_counter()
                    final = run(request, bundle)
                    latencies.append(1000 * (time.perf_counter() - start))
                    assert final["stage"] == "FINAL_RESULT"
                    assert final["next"]["action"] != "ASK"
                    assert len(final["main"]) <= 5 and len(final["secondary"]) <= 3
                    update = (
                        foundation.update_state
                        if bundle.get("foundation_model")
                        else backend.update_joint_state
                    )
                    args = [final["state"], request["answers"][-1], bundle]
                    if bundle.get("foundation_model"):
                        args.append(backend)
                    try:
                        update(*args)
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("ANSWER_AFTER_FINAL_ACCEPTED")
                    try:
                        backend.apply_final_comparison(
                            final["state"],
                            ids,
                            ids[:1],
                            bundle,
                            feedback_source="SIMULATED",
                            generation_version=bundle["bundle_id"],
                        )
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("SECOND_FINAL_COMPARISON_ACCEPTED")
                    if sessions == 0:
                        with tempfile.TemporaryDirectory(prefix="m2-r1-live-") as temp:
                            input_path = Path(temp) / "request.json"
                            save(input_path, request)
                            for seed in ["0", "1"]:
                                output = subprocess.check_output(
                                    [
                                        sys.executable,
                                        str(ROOT / "db/scripts/infer_m2_r1.py"),
                                        "--model-file",
                                        str(model_path),
                                        "--input",
                                        str(input_path),
                                    ],
                                    text=True,
                                    env={**os.environ, "PYTHONHASHSEED": seed},
                                )
                                assert json.loads(output) == final
                                cli_comparisons += 1
                    sessions += 1
        for field, invalid in [
            ("c0", None),
            ("c0", "unknown"),
            ("c1", None),
            ("c1", "unknown"),
            ("c1", "unsure"),
            ("c1", "skip"),
        ]:
            context = {"c0": backend.C0[0], "c1": "medium", field: invalid}
            try:
                run(
                    {
                        "contract_version": backend.VERSIONS["contract_version"],
                        "context": context,
                    },
                    bundle,
                )
            except ValueError:
                pass
            else:
                raise AssertionError("INVALID_CONTEXT_ACCEPTED")
        results[name] = {
            "model_sha256": sha(model_path),
            "completed_synthetic_contract_sessions": sessions,
            "context_combinations": 56,
            "paths": paths,
            "cli_saved_model_exact_matches": cli_comparisons,
            "terminal_replay_and_second_feedback_rejected": True,
            "batches_and_replay_identical": True,
            "invalid_context_rejected": True,
            "main_limit": 5,
            "secondary_limit": 3,
            "full_request_median_ms": float(np.median(latencies)),
            "full_request_p95_ms": float(np.percentile(latencies, 95)),
        }
        print(json.dumps({"verified_model": name, "sessions": sessions}), flush=True)
    report = {
        "evaluation_type": "SYNTHETIC_ENGINEERING_CONTRACT_ONLY",
        "models": results,
        "old_D0_models_and_results_byte_identical": True,
        "frontend_changes": 0,
        "real_sensory_accuracy": "NOT_EVALUATED",
    }
    save(private / "engineering_checks.private.json", report)
    metrics = read(OUT / "metrics.json")
    metrics["engineering"] = report
    save(OUT / "metrics.json", metrics)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    verify(parser.parse_args().owner_dir)
