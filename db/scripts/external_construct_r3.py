#!/usr/bin/env python3
"""Fixed five-coffee external construct pilot; nominal language is not truth."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import unicodedata
from pathlib import Path

import numpy as np
from scipy.spatial.distance import jensenshannon
from scipy.stats import rankdata

VERSION = "m2-r3-croijmans-fixed-five-construct.v1"
SEED = 20260906


def protocol():
    return {
        "version": VERSION,
        "sources": {
            "expressions": {"path": "revisions/r2/croijmans_paired_responses.private.json", "sha256": "6536320695a7629b890ab9050e75ecf84468229721cc4193b06c029eac9c95c8"},
            "sorting": {"path": "revisions/r2/croijmans_sorting_distances.private.json", "sha256": "d37052cc5ef4c05a43668be254df7d71a3f32a80054e6726ba8c4a77d1636baa"},
        },
        "status": "EXTERNAL_CONSTRUCT_CHECK_PILOT",
        "implementation_status": "METRIC_IMPLEMENTATION_VERIFIED_AFTER_TESTS_ONLY",
        "stimuli": "ALL_FIVE_EXISTING_COFFEES_AND_TEN_UNORDERED_PAIRS;R2_CONFIRMATION_PREVIOUSLY_VIEWED_HISTORICAL",
        "expression_subset": "308_COMPLETE_PARTICIPANT_COFFEE_SMELL_TASTE_PAIRS;BOTH_MODALITIES_SAME_CASES;THREE_UNPAIRED_CLEAN_RESPONSES_EXCLUDED",
        "expression_encoding": "SOURCE_SA_TOKENS_NL_UNIQUE_PRESENCE_PER_RESPONSE;UNICODE_NFC_CASEFOLD_WHITESPACE_ONLY;NO_TRANSLATION_STEMMING_OR_SIGNED_SENSORY_LABELS",
        "vocabulary": "FIXED_ALL_PAIRED_EXPRESSION_TOKENS_ONLY;NO_SORTING_VALUES_OR_COFFEE_ID_FEATURES",
        "expression_profiles": "EQUAL_PARTICIPANT_MEAN_TOKEN_PRESENCE_BY_COFFEE_AND_MODALITY_THEN_L1_NORMALIZE",
        "primary_distance": "0.5_SQRT_JENSEN_SHANNON_SMELL_PLUS_0.5_SQRT_JENSEN_SHANNON_TASTE;NATURAL_LOG",
        "fixed_sensitivity": {"distances": ["sqrt_jensen_shannon", "cosine"], "smell_weights": [0.25, 0.5, 0.75], "selection": "NONE_ALL_SIX_REPORTED_PRIMARY_FIXED_BEFORE_RESULTS"},
        "sorting_reference": "TWENTY_INDEPENDENT_SORTING_PARTICIPANTS;DIVIDE_EACH_TEN_DISTANCE_VECTOR_BY_ITS_OWN_MEAN_THEN_EQUAL_PARTICIPANT_AVERAGE",
        "statistic": "SPEARMAN_OF_TEN_UPPER_TRIANGLE_EDGES;AVERAGE_RANK_TIES",
        "permutation": "ALL_120_BIJECTIVE_COFFEE_NODE_RELABELINGS_OF_EXPRESSION_MATRIX;TWO_SIDED_ABSOLUTE_RHO;EXACT_COUNT_DIVIDED_BY_120_INCLUDING_IDENTITY;NO_EDGEWISE_PERMUTATION",
        "uncertainty": "2000_INDEPENDENT_PARTICIPANT_BLOCK_RESAMPLES_OF_LANGUAGE_AND_SORTING_COHORTS;ALL_COFFEE_MODALITY_ROWS_FOR_SAMPLED_PERSON_TRAVEL_TOGETHER;FIXED_VOCABULARY_AND_FIVE_COFFEES;PERCENTILE_95_INTERVAL",
        "empty_or_constant": "ZERO_MASS_PROFILE_OR_CONSTANT_EDGE_RANK_VECTOR_IS_UNIDENTIFIABLE;DO_NOT_FILL_OR_DROP_COFFEES;REPORT_VALID_BOOTSTRAP_COUNT",
        "interpretation": "NOMINAL_EXPRESSION_GEOMETRY_VS_INDEPENDENT_SOURCE_SORTING_GEOMETRY;NOT_POSITIVE_FLAVOR_TRUTH_NOT_CALIBRATED_PSYCHOLOGICAL_DISTANCE_NOT_INDIVIDUAL_SYSTEM_ALIGNMENT",
        "generalization": "ONLY_THESE_FIVE_COFFEES;NO_NEW_COFFEE_OR_LOT_GENERALIZATION;NO_SOURCE_POPULATION_SUBGROUP_SEARCH",
        "main_M2_scoring_changed": False,
        "seed": SEED,
    }


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def contract_contains(tree, expected):
    if tree == expected:
        return True
    if isinstance(tree, dict):
        return any(contract_contains(v, expected) for v in tree.values())
    if isinstance(tree, list):
        return any(contract_contains(v, expected) for v in tree)
    return False


def normalized_token(token):
    return " ".join(unicodedata.normalize("NFC", token).casefold().split())


def prepare_expressions(package):
    if package["contract"]["source_id"] != "CROIJMANS_MAJID_COFFEE_LANGUAGE_2016":
        raise ValueError("UNREGISTERED_EXPRESSION_SOURCE")
    records = {r["record_id"]: r for r in package["records"]}
    if len(records) != len(package["records"]):
        raise ValueError("DUPLICATE_EXPRESSION_ID")
    paired = []
    seen = set()
    for pair in package["complete_pairs"]:
        a, b = records[pair["smell_record_id"]], records[pair["taste_record_id"]]
        identity = (a["participant_id"], a["coffee_group_id"])
        if (identity in seen or a["modality"] != "SMELL" or b["modality"] != "TASTE"
                or identity != (b["participant_id"], b["coffee_group_id"])
                or a["pair_id"] != pair["pair_id"] or b["pair_id"] != pair["pair_id"]
                or a.get("full_answer_mask") is not True or b.get("full_answer_mask") is not True
                or a.get("positive_sensory_truth_mask") is not False
                or b.get("positive_sensory_truth_mask") is not False):
            raise ValueError("INVALID_PAIRED_NOMINAL_LANGUAGE")
        seen.add(identity)
        paired.extend((a, b))
    participants = sorted({r["participant_id"] for r in paired})
    coffees = sorted({r["coffee_group_id"] for r in paired})
    vocabulary = sorted({normalized_token(t) for r in paired for t in r["source_SA_tokens_nl"] if normalized_token(t)})
    pi, ci, vi = ({x: i for i, x in enumerate(xs)} for xs in (participants, coffees, vocabulary))
    tensor = np.zeros((len(participants), len(coffees), 2, len(vocabulary)))
    mask = np.zeros(tensor.shape[:3], dtype=bool)
    for row in paired:
        p, c, m = pi[row["participant_id"]], ci[row["coffee_group_id"]], int(row["modality"] == "TASTE")
        if mask[p, c, m]:
            raise ValueError("DUPLICATE_PERSON_COFFEE_MODALITY")
        mask[p, c, m] = True
        for token in set(map(normalized_token, row["source_SA_tokens_nl"])):
            if token:
                tensor[p, c, m, vi[token]] = 1
    if not np.array_equal(mask[:, :, 0], mask[:, :, 1]):
        raise ValueError("PAIRED_MODALITY_MASK_MISMATCH")
    return {"tensor": tensor, "mask": mask, "participants": participants, "coffees": coffees,
            "vocabulary": vocabulary, "record_ids": sorted(r["record_id"] for r in paired),
            "excluded_unpaired": len(records) - len(paired)}


def prepare_sorting(package, coffees):
    if package["contract"]["source_id"] != "CROIJMANS_MAJID_INDEPENDENT_SORTING_2016":
        raise ValueError("UNREGISTERED_SORTING_SOURCE")
    participants = sorted({r["participant_id"] for r in package["records"]})
    ci, pi = {c: i for i, c in enumerate(coffees)}, {p: i for i, p in enumerate(participants)}
    matrices = np.zeros((len(participants), len(coffees), len(coffees)))
    seen = set()
    for row in package["records"]:
        if row["distance_mask"] is not True or row["distance_state"] != "OBSERVED":
            raise ValueError("MISSING_SORTING_DISTANCE")
        a, b = sorted((ci[row["coffee_a_id"]], ci[row["coffee_b_id"]]))
        p = pi[row["participant_id"]]
        d = float(row["distance_mm"])
        if a == b or not np.isfinite(d) or d < 0 or (p, a, b) in seen:
            raise ValueError("INVALID_OR_DUPLICATE_SORTING_PAIR")
        seen.add((p, a, b))
        matrices[p, a, b] = matrices[p, b, a] = d
    if len(seen) != len(participants) * len(coffees) * (len(coffees) - 1) // 2:
        raise ValueError("INCOMPLETE_SORTING_PARTICIPANT_MATRIX")
    tri = np.triu_indices(len(coffees), 1)
    means = matrices[:, tri[0], tri[1]].mean(axis=1)
    if np.any(means <= 0):
        raise ValueError("ZERO_SORTING_SCALE")
    return {"participants": participants, "raw_matrices": matrices,
            "normalized_matrices": matrices / means[:, None, None], "participant_mean_mm": means}


def expression_profiles(prepared, weights=None):
    n = len(prepared["participants"])
    weights = np.ones(n) if weights is None else np.asarray(weights, float)
    if weights.shape != (n,) or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("INVALID_PARTICIPANT_WEIGHTS")
    denominators = np.tensordot(weights, prepared["mask"], axes=1)
    if np.any(denominators <= 0):
        return None
    profile = np.tensordot(weights, prepared["tensor"], axes=1) / denominators[:, :, None]
    mass = profile.sum(axis=-1, keepdims=True)
    if np.any(mass <= 0):
        return None
    return profile / mass


def distance_matrix(profiles, metric, smell_weight):
    if metric not in ("sqrt_jensen_shannon", "cosine") or smell_weight not in (0.25, 0.5, 0.75):
        raise ValueError("UNREGISTERED_DISTANCE_SENSITIVITY")
    n = len(profiles)
    matrix = np.zeros((n, n))
    for a, b in itertools.combinations(range(n), 2):
        ds = []
        for modality in range(2):
            x, y = profiles[a, modality], profiles[b, modality]
            if metric == "sqrt_jensen_shannon":
                d = float(jensenshannon(x, y))
            else:
                d = float(np.clip(1 - np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y)), 0, 2))
            ds.append(d)
        matrix[a, b] = matrix[b, a] = smell_weight * ds[0] + (1 - smell_weight) * ds[1]
    return matrix


def matrix_correlation(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != b.shape or a.ndim != 2 or a.shape[0] != a.shape[1]:
        raise ValueError("MATCHED_SQUARE_MATRICES_REQUIRED")
    tri = np.triu_indices(len(a), 1)
    x, y = rankdata(a[tri]), rankdata(b[tri])
    x, y = x - x.mean(), y - y.mean()
    norm = np.linalg.norm(x) * np.linalg.norm(y)
    return float(np.clip(np.dot(x, y) / norm, -1, 1)) if norm > 0 else None


def node_permutation_test(expression, sorting):
    observed = matrix_correlation(expression, sorting)
    if observed is None:
        return {"rho": None, "p_two_sided": None, "permutations": [], "status": "UNIDENTIFIABLE"}
    permutations = []
    for permutation in itertools.permutations(range(len(expression))):
        permuted = expression[np.ix_(permutation, permutation)]
        permutations.append({"node_permutation": list(permutation), "rho": matrix_correlation(permuted, sorting)})
    exceedances = sum(abs(r["rho"]) >= abs(observed) - 1e-12 for r in permutations)
    return {"rho": observed, "p_two_sided": exceedances / len(permutations), "permutation_count": len(permutations),
            "extreme_or_equal_count": exceedances, "permutations": permutations,
            "status": "EXTERNAL_CONSTRUCT_CHECK_PILOT"}


def evaluate_pilot(expressions, sorting, bootstrap_count=2000):
    profiles = expression_profiles(expressions)
    if profiles is None:
        raise ValueError("UNIDENTIFIABLE_EXPRESSION_PROFILE")
    reference = sorting["normalized_matrices"].mean(axis=0)
    specs = [(metric, weight) for metric in ("sqrt_jensen_shannon", "cosine") for weight in (0.25, 0.5, 0.75)]
    results = {}
    for metric, weight in specs:
        key = f"{metric}_smell_{weight}"
        matrix = distance_matrix(profiles, metric, weight)
        results[key] = {"metric": metric, "smell_weight": weight, "primary": metric == "sqrt_jensen_shannon" and weight == 0.5,
                        "distance_matrix": matrix.tolist(), **node_permutation_test(matrix, reference), "bootstrap_rhos": []}
    rng = np.random.default_rng(SEED)
    n_language, n_sorting = len(expressions["participants"]), len(sorting["participants"])
    for _ in range(bootstrap_count):
        language_weights = np.bincount(rng.integers(n_language, size=n_language), minlength=n_language)
        p = expression_profiles(expressions, language_weights)
        reference_sample = sorting["normalized_matrices"][rng.integers(n_sorting, size=n_sorting)].mean(axis=0)
        for metric, weight in specs:
            rho = matrix_correlation(distance_matrix(p, metric, weight), reference_sample) if p is not None else None
            results[f"{metric}_smell_{weight}"]["bootstrap_rhos"].append(rho)
    for result in results.values():
        valid = [r for r in result["bootstrap_rhos"] if r is not None]
        result["bootstrap_valid"] = len(valid)
        result["bootstrap_attempted"] = bootstrap_count
        result["bootstrap_95_interval_fixed_five_coffees"] = np.quantile(valid, [0.025, 0.975]).tolist() if valid else None
    return {"reference_matrix": reference.tolist(), "profiles": profiles.tolist(), "sensitivities": results}


def run(owner, contract_path):
    owner, contract_path = Path(owner), Path(contract_path)
    frozen = json.loads(contract_path.read_text())
    if not contract_contains(frozen, protocol()):
        raise ValueError("EXACT_PROTOCOL_NOT_PRESENT_IN_FROZEN_CONTRACT")
    files = {key: owner / data["path"] for key, data in protocol()["sources"].items()}
    for key, path in files.items():
        if sha(path) != protocol()["sources"][key]["sha256"]:
            raise ValueError("FROZEN_SOURCE_HASH_MISMATCH:" + key)
    directory = owner / "revisions/r3"
    fingerprint = {"protocol_sha256": digest(protocol()), "contract_sha256": sha(contract_path), "code_sha256": sha(__file__),
                   "source_sha256": {key: sha(path) for key, path in files.items()}}
    receipt_path, detail_path = directory / "external_construct_receipt.private.json", directory / "external_construct_detail.private.json"
    summary_path = directory / "external_construct_public_summary.private.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["fingerprint"] != fingerprint or receipt["status"] != "COMPLETE":
            raise ValueError("PRESERVE_PRIOR_RUN_FINGERPRINT_OR_INCOMPLETE_RECEIPT")
        if sha(detail_path) != receipt["detail_sha256"] or sha(summary_path) != receipt["summary_sha256"]:
            raise ValueError("RETAINED_ARTIFACT_HASH_MISMATCH")
        return json.loads(summary_path.read_text())
    prepared = prepare_expressions(json.loads(files["expressions"].read_text()))
    sort = prepare_sorting(json.loads(files["sorting"].read_text()), prepared["coffees"])
    if (len(prepared["coffees"]), len(prepared["record_ids"]), len(prepared["participants"]), len(sort["participants"])) != (5, 616, 63, 20):
        raise ValueError("REGISTERED_SOURCE_DENOMINATOR_MISMATCH")
    if set(prepared["participants"]) & set(sort["participants"]):
        raise ValueError("INDEPENDENT_SORTING_COHORT_REQUIRED")
    save(receipt_path, {"fingerprint": fingerprint, "status": "RUNNING", "no_new_model_fit": True})
    with __import__("threadpoolctl").threadpool_limits(limits=1):
        result = evaluate_pilot(prepared, sort)
    result.update(protocol=protocol(), fingerprint=fingerprint, coffees=prepared["coffees"], vocabulary=prepared["vocabulary"],
                  expression_participants=prepared["participants"], expression_record_ids=prepared["record_ids"],
                  expression_mask=prepared["mask"].tolist(), sorting_participants=sort["participants"],
                  sorting_raw_matrices=sort["raw_matrices"].tolist(), sorting_participant_mean_mm=sort["participant_mean_mm"].tolist())
    summary = {"version": VERSION, "status": "EXTERNAL_CONSTRUCT_CHECK_PILOT", "metric_status": "METRIC_IMPLEMENTATION_VERIFIED",
               "coffees": 5, "dependent_pairs": 10, "language_participants": 63, "language_complete_pairs": 308,
               "language_records_used": 616, "language_unpaired_records_excluded": prepared["excluded_unpaired"],
               "independent_sorting_participants": 20, "sorting_measurements": 200, "vocabulary_size": len(prepared["vocabulary"]),
               "sensitivities": {key: {k: v for k, v in row.items() if k not in ("distance_matrix", "permutations", "bootstrap_rhos")}
                                 for key, row in result["sensitivities"].items()},
               "scope": protocol()["interpretation"], "generalization": protocol()["generalization"],
               "confirmation_status": "ALL_EXISTING_COFFEES_HISTORICAL_NO_FRESH_CONFIRMATION",
               "private_details_owner_relative": "revisions/r3/external_construct_detail.private.json", "main_M2_scoring_changed": False}
    save(detail_path, result)
    save(summary_path, summary)
    save(receipt_path, {"status": "COMPLETE", "fingerprint": fingerprint, "detail_sha256": sha(detail_path),
                        "summary_sha256": sha(summary_path), "cached_rerun_policy": "VERIFY_HASHES_RETURN_SAVED_NO_RECOMPUTATION"})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", required=True)
    parser.add_argument("--contract", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.owner_dir, args.contract), sort_keys=True, indent=2))
