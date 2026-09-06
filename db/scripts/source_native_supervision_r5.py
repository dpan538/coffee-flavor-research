"""One bounded new-source response-value diagnostic, not a product Q3 model.

Blendstat author-released data: native Flavour score -> native Bitterness score.
No quality Score, mixture identity, processing or inferred participant labels.
"""

from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
from pathlib import Path

import numpy as np

from run_supervision_r5 import now, read, save, sha

VERSION = "m2-r5.blendstat-native-response-ridge.v1"
SOURCE_SHA = "212804677b04f16f6f74b2c0192afa05b5c23cf0d98c93383e79ce4528efb676"


def protocol():
    return {
        "version": VERSION,
        "task": "AUX_SOURCE_NATIVE_AGGREGATE_RESPONSE",
        "A": "No additional sensory measurement; training-side mean baseline",
        "B": "Actually recorded native.Flavour field only",
        "T": "Fixed actually recorded native.Bitterness field; same source record, not an independent grader/reference",
        "role": "Static masked-field prediction, not a product question, calibrated intensity, descriptor presence, cross-grader truth or extra user slot",
        "unit": "Source condition-level row without participant IDs; no reconstruction of the paper's five tasters",
        "scale": "Author's native continuous0–10 response; divide by known10, do not fit scaler on held data",
        "model": "Identical intercept+slope allocation: baseline slope zero; observed-B ridge coefficient penalty0.1; group-normalized half squared error, unpenalized intercept; closed form",
        "prediction": "Clip to known source response range0–10; not a presence probability",
        "grouping": "All equal four-component proportions coheld across both processing views and all concentrations;16 design groups share a small constituent pool, not16 independent beans",
        "split": "Sort composition groups by SHA256(R5_BLEND_CONFIRM|group); first4 held for small new-source confirmation, remaining12 deterministic3fold development; no outcome-based selection",
        "configuration_selection": "One fixed setting; no response-dependent tuning, exclusions or weights; schema/marginal ranges inspected before split, no earlier model outcomes",
        "controls": "Train-group half versus all; B rotated as whole design-group blocks with matching processing/concentration/multiplicity signatures; singleton strata unchanged",
        "aggregation": "Mean row squared error within held composition group, then equal group mean; report MSE and RMSE on native0–10 units",
        "prohibited_inputs": [
            "Score",
            "Body",
            "Acidity",
            "mixture proportions",
            "Conc",
            "process",
            "Exp",
            "Sample",
            "identities",
        ],
        "source_license": "Author-released Blendstat1.0.6 CRAN GPL-3 with dataset Rd and no separate dataset exception; source and weights private",
        "transfer": "No numeric score pooled with descriptor logits or primary R5 metrics; no production/trigger use",
    }


def load(owner):
    path = owner / "revisions/r5/sources/blendstat_native_observations.private.json"
    if sha(path) != SOURCE_SHA:
        raise ValueError("NEW_SOURCE_TYPED_HASH_CHANGED")
    admission = read(
        owner / "revisions/r5/sources/blendstat_data_role_summary.private.json"
    )
    for filename, expected in admission["source_file_sha256"].items():
        if sha(owner / "revisions/r5/sources" / filename) != expected:
            raise ValueError("NEW_SOURCE_CSV_HASH_CHANGED")
    rows = read(path)
    if len(rows) != 72 or len({r["observation_id"] for r in rows}) != len(rows):
        raise ValueError("SOURCE_ROW_IDENTITY_MISMATCH")
    for row in rows:
        x, y = values(row)
        if not 0 <= x <= 1 or not 0 <= y <= 1:
            raise ValueError("SOURCE_SCALE_OR_MISSING_RESPONSE_INVALID")
        if (
            row["participant_id"] is not None
            or row["available_runtime_question_answers"]
        ):
            raise ValueError("UNREGISTERED_PARTICIPANT_OR_PRODUCT_ROLE")
    return rows


def values(row):
    view = row["minimum_auxiliary_view"]
    return (
        float(view["B"]["native.Flavour"]) / 10,
        float(view["T"]["native.Bitterness"]) / 10,
    )


def group(row):
    return row["conservative_split_group"]


def weights(rows):
    counts = Counter(group(r) for r in rows)
    return np.array([1 / len(counts) / counts[group(r)] for r in rows])


def freeze(owner):
    dst = owner / "revisions/r5/source_native"
    path = dst / "contract.frozen.json"
    rows = load(owner)
    groups = sorted(
        {group(r) for r in rows},
        key=lambda g: hashlib.sha256(("R5_BLEND_CONFIRM|" + g).encode()).hexdigest(),
    )
    if len(groups) != 16:
        raise ValueError("FIXED_COMPOSITION_GROUP_COUNT_CHANGED")
    if path.exists():
        contract = read(path)
        if (
            contract["protocol"] != protocol()
            or contract["source_sha256"] != SOURCE_SHA
        ):
            raise ValueError("SEALED_AUXILIARY_PROTOCOL_CHANGED")
        for field, filename in [
            ("admission_summary_sha256", "blendstat_data_role_summary.private.json"),
            (
                "admission_manifest_sha256",
                "blendstat_admission_manifest_v2.private.json",
            ),
        ]:
            if sha(owner / "revisions/r5/sources" / filename) != contract[field]:
                raise ValueError("SEALED_AUXILIARY_ADMISSION_CHANGED")
        return contract
    contract = {
        "registered_utc": now(),
        "protocol": protocol(),
        "source_sha256": SOURCE_SHA,
        "admission_summary_sha256": sha(
            owner / "revisions/r5/sources/blendstat_data_role_summary.private.json"
        ),
        "admission_manifest_sha256": sha(
            owner / "revisions/r5/sources/blendstat_admission_manifest_v2.private.json"
        ),
        "confirmation_groups": groups[:4],
        "development_folds": {g: i % 3 for i, g in enumerate(groups[4:])},
    }
    save(path, contract)
    return contract


def fit(rows, use_B):
    xy = np.array([values(r) for r in rows])
    x = np.column_stack(
        [np.ones(len(rows)), xy[:, 0] if use_B else np.zeros(len(rows))]
    )
    w = weights(rows)
    coef = np.linalg.solve(
        x.T @ (w[:, None] * x) + np.diag([0.0, 0.1]), x.T @ (w * xy[:, 1])
    )
    return {
        "version": VERSION,
        "use_B": use_B,
        "coefficients": coef.tolist(),
        "training_groups": sorted({group(r) for r in rows}),
        "training_rows": len(rows),
        "source_sha256": SOURCE_SHA,
    }


def predict(row, model):
    if model["version"] != VERSION or model["source_sha256"] != SOURCE_SHA:
        raise ValueError("NATIVE_RESPONSE_MODEL_CONTRACT_MISMATCH")
    x = (
        float(row["minimum_auxiliary_view"]["B"]["native.Flavour"]) / 10
        if model["use_B"]
        else 0.0
    )
    return float(
        np.clip(model["coefficients"][0] + model["coefficients"][1] * x, 0, 1) * 10
    )


def evaluate(rows, model):
    return [
        {
            "record_id": r["observation_id"],
            "group_id": group(r),
            "prediction": predict(r, model),
            "squared_error": (predict(r, model) - values(r)[1] * 10) ** 2,
        }
        for r in rows
    ]


def summary(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["group_id"]].append(row["squared_error"])
    mse = float(np.mean([np.mean(v) for v in groups.values()]))
    return {
        "records": len(rows),
        "design_groups": len(groups),
        "MSE_native_units_squared": mse,
        "RMSE_native_units": mse**0.5,
    }


def wrong_B(rows):
    import copy

    grouped = defaultdict(list)
    for row in rows:
        grouped[group(row)].append(row)
    strata = defaultdict(list)

    def order(row):
        return (row["process"], row["native_concentration_wv"], row["observation_id"])

    for g, values_ in grouped.items():
        signature = tuple(
            sorted(
                Counter(
                    (r["process"], r["native_concentration_wv"]) for r in values_
                ).items()
            )
        )
        strata[signature].append(g)
    result, moved = [], 0
    for members in strata.values():
        members.sort()
        for i, g in enumerate(members):
            donors = grouped[members[(i + 1) % len(members)]]
            for row, donor in zip(
                sorted(grouped[g], key=order), sorted(donors, key=order), strict=True
            ):
                new = copy.deepcopy(row)
                new["minimum_auxiliary_view"]["B"] = dict(
                    donor["minimum_auxiliary_view"]["B"]
                )
                result.append(new)
                moved += len(members) > 1
    return result, moved


def run(owner):
    contract = freeze(owner)
    dst = owner / "revisions/r5/source_native"
    if (dst / "receipt.private.json").exists():
        raise ValueError("AUXILIARY_RUN_EXISTS_USE_REPLAY")
    rows = load(owner)
    folds = contract["development_folds"]
    dev = [r for r in rows if group(r) in folds]
    confirm = [r for r in rows if group(r) in contract["confirmation_groups"]]
    model_entries, outcomes, diagnostics = [], [], []
    started = now()
    for outer in [0, 1, 2]:
        fitting = [r for r in dev if folds[group(r)] != outer]
        held = [r for r in dev if folds[group(r)] == outer]
        gs = sorted(
            {group(r) for r in fitting},
            key=lambda g: hashlib.sha256(("R5_BLEND_CURVE|" + g).encode()).hexdigest(),
        )
        half = [r for r in fitting if group(r) in gs[: len(gs) // 2]]
        wrong, moved = wrong_B(fitting)
        for name, training, use_B in [
            ("T1_MEAN", fitting, False),
            ("T2_FLAVOUR", fitting, True),
            ("T2_HALF_GROUPS", half, True),
            ("T2_WRONG_B", wrong, True),
        ]:
            model = fit(training, use_B)
            path = dst / "models" / f"{name}_outer{outer}.json"
            save(path, model)
            evaluated = evaluate(held, model)
            for row in evaluated:
                row.update(model=name, outer=outer, split="DEVELOPMENT_OOF")
            outcomes += evaluated
            model_entries.append(
                {
                    "path": str(path.relative_to(dst)),
                    "sha256": sha(path),
                    "name": name,
                    "outer": outer,
                }
            )
            diagnostics.append(
                {
                    "name": name,
                    "outer": outer,
                    "training": summary(evaluate(training, model)),
                    "held": summary(evaluated),
                    "training_groups": len(model["training_groups"]),
                    "mismatched_records": moved if name == "T2_WRONG_B" else None,
                }
            )
    # No development-driven selection: both frozen controls refit only on DEV.
    for name, use_B in [("T1_MEAN", False), ("T2_FLAVOUR", True)]:
        model = fit(dev, use_B)
        path = dst / "models" / f"{name}_DEV_REFIT.json"
        save(path, model)
        evaluated = evaluate(confirm, model)
        for row in evaluated:
            row.update(model=name, outer=None, split="SMALL_NEW_SOURCE_CONFIRMATION")
        outcomes += evaluated
        model_entries.append(
            {
                "path": str(path.relative_to(dst)),
                "sha256": sha(path),
                "name": name,
                "outer": None,
            }
        )
    result = {
        "task": protocol()["task"],
        "source_rows": len(rows),
        "development_groups": len(folds),
        "confirmation_groups": 4,
        "outcomes": {
            s: {
                name: summary(
                    [r for r in outcomes if r["split"] == s and r["model"] == name]
                )
                for name in sorted({r["model"] for r in outcomes if r["split"] == s})
            }
            for s in sorted({r["split"] for r in outcomes})
        },
        "per_fold": diagnostics,
        "product_alignment": "NOT_EVALUATED",
        "Q3_value": "NOT_ESTIMABLE_FROM_THIS_SOURCE",
        "scope": protocol()["role"],
        "generalization": protocol()["grouping"],
    }
    save(dst / "predictions.private.json", outcomes)
    save(dst / "summary.private.json", result)
    save(
        dst / "receipt.private.json",
        {
            "started_utc": started,
            "finished_utc": now(),
            "contract_sha256": sha(dst / "contract.frozen.json"),
            "code_sha256": sha(__file__),
            "source_sha256": SOURCE_SHA,
            "models": model_entries,
            "summary_sha256": sha(dst / "summary.private.json"),
            "predictions_sha256": sha(dst / "predictions.private.json"),
        },
    )
    return result


def replay(owner):
    dst = owner / "revisions/r5/source_native"
    receipt, contract = read(dst / "receipt.private.json"), freeze(owner)
    if (
        sha(dst / "contract.frozen.json") != receipt["contract_sha256"]
        or sha(dst / "predictions.private.json") != receipt["predictions_sha256"]
        or sha(dst / "summary.private.json") != receipt["summary_sha256"]
    ):
        raise ValueError("SEALED_AUXILIARY_ARTIFACT_CHANGED")
    rows, original = load(owner), read(dst / "predictions.private.json")
    checked = 0
    for item in receipt["models"]:
        path = dst / item["path"]
        if sha(path) != item["sha256"]:
            raise ValueError("SEALED_AUXILIARY_MODEL_CHANGED")
        held = [
            r
            for r in rows
            if (
                group(r) in contract["confirmation_groups"]
                if item["outer"] is None
                else contract["development_folds"].get(group(r)) == item["outer"]
            )
        ]
        expected = {
            r["record_id"]: r
            for r in original
            if r["model"] == item["name"] and r["outer"] == item["outer"]
        }
        if set(expected) != {r["observation_id"] for r in held}:
            raise ValueError("SEALED_AUXILIARY_ID_ALIGNMENT")
        for row in evaluate(held, read(path)):
            if any(row[k] != expected[row["record_id"]][k] for k in row):
                raise ValueError("AUXILIARY_PREDICTION_MISMATCH")
            checked += 1
    return {
        "status": "PASS",
        "replayed_predictions": checked,
        "fit_count": 0,
        "checked_utc": now(),
    }


if __name__ == "__main__":
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["freeze", "train", "replay"])
    parser.add_argument("--owner-dir", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            {"freeze": freeze, "train": run, "replay": replay}[args.phase](
                args.owner_dir
            ),
            sort_keys=True,
            allow_nan=False,
        )
    )
