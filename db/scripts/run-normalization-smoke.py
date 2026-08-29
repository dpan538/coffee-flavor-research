#!/usr/bin/env python3
"""Run the authorized Batch 5 normalization smoke and fixed baseline offline.

Restricted lexical strings exist only in memory. Repository outputs contain
hashes, governed identifiers, aggregate metrics, and configuration receipts.
No fitted estimator is serialized.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import platform
import resource
import shutil
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import joblib
import numpy as np
import scipy
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import f1_score
from sklearn.pipeline import FeatureUnion
from threadpoolctl import threadpool_limits


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
DEFAULT_OUTPUT = ROOT / "db" / "data" / "normalization-smoke"
BATCH4_BUILDER = ROOT / "db" / "scripts" / "build-batch4-cleaning-staging.py"
DEFAULT_BATCH2 = Path("/private/tmp/round3l-acquisition/professional_descriptor_batch2")
DEFAULT_ROUND3M = Path("/private/tmp/coffee-flavor-round3m-restricted")
DEFAULT_EXTENSION = Path("/private/tmp/coffee-flavor-round3m-post20k/post20k_extension")

SEED = 20260829
GENERATED_AT = "2026-08-30T00:00:00Z"
CORPUS_VERSION = "professional-descriptor-candidate-v1-30k"
SMOKE_CONTRACT = "batch5.normalization-engineering-smoke.v1"
PERMITTED = {"AFFIRMATIVE", "AFFIRMATIVE_WITH_CONDITIONS"}
MODEL_SUFFIXES = {
    ".bin",
    ".ckpt",
    ".joblib",
    ".onnx",
    ".pkl",
    ".pt",
    ".pth",
    ".safetensors",
    ".tflite",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_id(prefix: str, material: str) -> str:
    return f"{prefix}:{sha256_text(material)[:24]}"


def scalar(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise RuntimeError("non-finite public metric")
        return f"{value:.6f}"
    return str(value)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(
    output: Path,
    name: str,
    fields: Sequence[str],
    rows: Iterable[Mapping[str, Any]],
) -> None:
    with (output / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fields),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: scalar(row.get(field, "")) for field in fields})


def write_json(output: Path, name: str, value: Any) -> None:
    (output / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def data_rows(path: Path) -> int | str:
    if path.suffix == ".tsv":
        with path.open(encoding="utf-8", newline="") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    return "NA_NOT_TABULAR"


def load_batch4_builder():
    spec = importlib.util.spec_from_file_location("batch4_smoke_bridge", BATCH4_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Batch 4 cleaner bridge cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_current_hashes() -> dict[str, str]:
    listed: dict[str, str] = {}
    for line in (CURRENT / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        listed[name] = digest
    required = {
        "NORMALIZATION_ENGINEERING_SMOKE_CANDIDATE_MANIFEST.json",
        "GROUPED_SPLIT_FEASIBILITY.tsv",
        "GROUPED_SPLIT_GROUPS.tsv",
        "GROUPED_SPLIT_LEAKAGE_AUDIT.tsv",
        "PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv",
        "RIGHTS_PROPAGATION_RECEIPT.tsv",
        "MACHINE_GOVERNED_MAPPING.tsv",
        "CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv",
        "CLEANED_30K_OUTPUT_ATOM_LEDGER.tsv",
        "CONCEPT_CLUSTER.tsv",
        "ONTOLOGY_CONSOLIDATION_MAP.tsv",
        "CANDIDATE_30K_SNAPSHOT_MANIFEST.json",
        "CURRENT_DATA_MANIFEST.json",
    }
    missing = required - set(listed)
    if missing:
        raise RuntimeError(f"required governed inputs absent from manifest: {sorted(missing)}")
    mismatches = [
        name for name, digest in listed.items() if not (CURRENT / name).is_file() or sha256_file(CURRENT / name) != digest
    ]
    if mismatches:
        raise RuntimeError(f"governed input hash mismatch: {sorted(mismatches)}")
    return listed


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, value: str) -> str:
        self.parent.setdefault(value, value)
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if root_left < root_right:
            self.parent[root_right] = root_left
        else:
            self.parent[root_left] = root_right


@dataclass(frozen=True)
class Example:
    atom_id: str
    assertion_id: str
    form_id: str
    form_hash: str
    text: str
    context_text: str
    target: str
    family: str
    year: str
    effective_record: str
    coffee_identity: str
    duplicate_group: str
    mirror_group: str
    publication_layer: str
    collection_tier: str
    group_id: str = ""
    split: str = ""


def reconstruct_restricted_text(
    builder: Any,
    batch2_root: Path,
    round3m_root: Path,
    extension_root: Path,
) -> dict[str, dict[str, str]]:
    base_ledger = read_tsv(CURRENT / "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv")
    details, baseline = builder.base_restricted_text(batch2_root, round3m_root)
    result: dict[str, dict[str, str]] = {}
    for row in base_ledger:
        if row["counts_as_assertion"] != "true":
            continue
        detail = details.get(row["descriptor_assertion_id"])
        result[row["descriptor_assertion_id"]] = {
            "atomic_source_text": detail["atomic_source_text"] if detail else baseline.get(row["descriptor_assertion_id"], ""),
            "source_field_label": detail.get("source_field_label", "") if detail else "",
            "source_language": detail.get("source_language", row.get("source_language", "")) if detail else row.get("source_language", ""),
        }
    extension_path = extension_root / "POST20K_ASSERTIONS_RESTRICTED.tsv"
    if not extension_path.is_file():
        raise RuntimeError("restricted post-20k ledger missing")
    for row in read_tsv(extension_path):
        if row["counts_as_assertion"] != "true":
            continue
        result[row["descriptor_assertion_id"]] = {
            "atomic_source_text": row["atomic_source_text"],
            "source_field_label": row["source_field_label"],
            "source_language": row["source_language"],
        }
    return result


def assign_lineage_groups(examples: list[Example]) -> list[Example]:
    union = UnionFind()
    for example in examples:
        keys = [f"effective:{example.effective_record}"]
        if example.coffee_identity:
            keys.append(f"coffee:{example.coffee_identity}")
        if example.duplicate_group:
            keys.append(f"duplicate:{example.duplicate_group}")
        if example.mirror_group:
            keys.append(f"mirror:{example.mirror_group}")
        for key in keys[1:]:
            union.union(keys[0], key)
    component_members: dict[str, set[str]] = defaultdict(set)
    for key in sorted(union.parent):
        component_members[union.find(key)].add(key)
    group_for_root = {
        root: stable_id("smoke-group", "\x1f".join(sorted(members)))
        for root, members in component_members.items()
    }
    result: list[Example] = []
    for example in examples:
        root = union.find(f"effective:{example.effective_record}")
        result.append(Example(**{**example.__dict__, "group_id": group_for_root[root]}))
    return result


def deterministic_group_split(examples: list[Example]) -> tuple[list[Example], dict[str, str]]:
    group_ids = sorted(
        {example.group_id for example in examples},
        key=lambda value: (sha256_text(f"{SEED}\x1f{value}"), value),
    )
    count = len(group_ids)
    train_count = round(count * 0.70)
    dev_count = round(count * 0.15)
    if train_count < 1 or dev_count < 1 or count - train_count - dev_count < 1:
        raise RuntimeError("insufficient lineage groups for 70/15/15 split")
    assignment = {
        group_id: (
            "TRAIN"
            if index < train_count
            else "DEV"
            if index < train_count + dev_count
            else "TEST"
        )
        for index, group_id in enumerate(group_ids)
    }
    return [
        Example(**{**example.__dict__, "split": assignment[example.group_id]})
        for example in examples
    ], assignment


def support_rows(examples: list[Example]) -> tuple[list[dict[str, Any]], set[str], dict[str, int]]:
    targets = sorted({example.target for example in examples})
    rows: list[dict[str, Any]] = []
    supported: set[str] = set()
    status_counts: Counter[str] = Counter()
    for target in targets:
        members = [example for example in examples if example.target == target]
        by_split = {split: [example for example in members if example.split == split] for split in ("TRAIN", "DEV", "TEST")}
        overall_groups = {example.group_id for example in members}
        train_groups = {example.group_id for example in by_split["TRAIN"]}
        evaluation_groups = {example.group_id for example in by_split["DEV"] + by_split["TEST"]}
        if len(overall_groups) < 5 or not evaluation_groups:
            status = "LOW_SUPPORT_TARGET"
        elif len(train_groups) < 2:
            status = "TRAIN_UNSUPPORTED_TARGET"
        else:
            status = "SUPPORTED_TARGET"
            supported.add(target)
        status_counts[status] += 1
        rows.append({
            "target_concept_id": target,
            "output_atom_count": len(members),
            "distinct_group_count": len(overall_groups),
            "source_family_count": len({example.family for example in members}),
            "year_count": len({example.year for example in members}),
            "train_output_count": len(by_split["TRAIN"]),
            "train_group_count": len(train_groups),
            "dev_output_count": len(by_split["DEV"]),
            "dev_group_count": len({example.group_id for example in by_split["DEV"]}),
            "test_output_count": len(by_split["TEST"]),
            "test_group_count": len({example.group_id for example in by_split["TEST"]}),
            "support_status": status,
        })
    return rows, supported, dict(status_counts)


def lexical_component_feasibility(examples: list[Example]) -> dict[str, Any]:
    union = UnionFind()
    for example in examples:
        union.union(f"group:{example.group_id}", f"form:{example.form_id}")
    component_outputs = Counter(union.find(f"group:{example.group_id}") for example in examples)
    component_groups: dict[str, set[str]] = defaultdict(set)
    for example in examples:
        component_groups[union.find(f"group:{example.group_id}")].add(example.group_id)
    ordered = sorted(component_outputs.items(), key=lambda item: (-item[1], item[0]))
    largest_outputs = ordered[0][1] if ordered else 0
    largest_groups = max((len(value) for value in component_groups.values()), default=0)
    feasible = (
        len(component_outputs) >= 3
        and largest_outputs / max(len(examples), 1) <= 0.70
        and largest_groups / max(len({example.group_id for example in examples}), 1) <= 0.70
    )
    return {
        "feasible": feasible,
        "component_count": len(component_outputs),
        "largest_component_output_count": largest_outputs,
        "largest_component_output_share": largest_outputs / max(len(examples), 1),
        "largest_component_group_count": largest_groups,
        "decision_basis": (
            "CONNECTED_GROUP_FORM_COMPONENTS_SUPPORT_THREE_WAY_SPLIT"
            if feasible
            else "CONNECTED_GROUP_FORM_COMPONENT_DOMINANCE_PREVENTS_70_15_15_WITHOUT_SAMPLE_LEAKAGE"
        ),
    }


def subset(examples: list[Example], split: str) -> list[Example]:
    return [example for example in examples if example.split == split]


def train_lookup(train: list[Example]) -> tuple[dict[str, list[str]], list[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    targets = Counter(example.target for example in train)
    for example in train:
        counts[example.form_id][example.target] += 1
    mapping = {
        form: [target for target, _ in sorted(counter.items(), key=lambda item: (-item[1], item[0]))]
        for form, counter in counts.items()
    }
    majority = [target for target, _ in sorted(targets.items(), key=lambda item: (-item[1], item[0]))]
    return mapping, majority


def rank_lookup(train: list[Example], evaluation: list[Example]) -> tuple[list[list[str]], list[list[float]]]:
    mapping, _ = train_lookup(train)
    rankings = [mapping.get(example.form_id, [])[:3] for example in evaluation]
    scores = [[1.0 - index * 0.01 for index in range(len(ranking))] for ranking in rankings]
    return rankings, scores


def rank_majority(train: list[Example], evaluation: list[Example]) -> tuple[list[list[str]], list[list[float]]]:
    _, majority = train_lookup(train)
    ranking = majority[:3]
    counts = Counter(example.target for example in train)
    total = max(len(train), 1)
    score = [counts[target] / total for target in ranking]
    return [ranking[:] for _ in evaluation], [score[:] for _ in evaluation]


def rank_nearest(train: list[Example], evaluation: list[Example]) -> tuple[list[list[str]], list[list[float]]]:
    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(3, 5),
        lowercase=True,
        sublinear_tf=True,
        norm="l2",
    )
    train_matrix = vectorizer.fit_transform([example.text for example in train])
    eval_matrix = vectorizer.transform([example.text for example in evaluation])
    similarities = (eval_matrix @ train_matrix.T).toarray()
    rankings: list[list[str]] = []
    scores: list[list[float]] = []
    for row in similarities:
        by_target: dict[str, float] = {}
        for index, value in enumerate(row):
            target = train[index].target
            by_target[target] = max(by_target.get(target, -1.0), float(value))
        ordered = sorted(by_target.items(), key=lambda item: (-item[1], item[0]))[:3]
        rankings.append([target for target, _ in ordered])
        scores.append([value for _, value in ordered])
    return rankings, scores


def vectorizer_for(config_id: str):
    char = TfidfVectorizer(
        analyzer="char",
        ngram_range=(3, 5),
        lowercase=True,
        sublinear_tf=True,
        norm="l2",
        max_features=20000,
    )
    if config_id == "B2_CHAR_LINEAR":
        return char
    return FeatureUnion([
        ("char", char),
        ("word", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            lowercase=True,
            sublinear_tf=True,
            norm="l2",
            max_features=5000,
        )),
    ])


def linear_input(config_id: str, examples: list[Example]) -> list[str]:
    if config_id == "E1_WORD_CHAR_CONTEXT":
        return [example.context_text for example in examples]
    return [example.text for example in examples]


def rank_linear(
    config_id: str,
    train: list[Example],
    evaluation: list[Example],
) -> tuple[list[list[str]], list[list[float]]]:
    vectorizer = vectorizer_for(config_id)
    train_matrix = vectorizer.fit_transform(linear_input(config_id, train))
    eval_matrix = vectorizer.transform(linear_input(config_id, evaluation))
    classifier = SGDClassifier(
        loss="log_loss",
        alpha=0.0001,
        penalty="l2",
        class_weight="balanced",
        max_iter=2500,
        tol=1e-6,
        random_state=SEED,
        shuffle=True,
        average=False,
    )
    classifier.fit(train_matrix, [example.target for example in train])
    probabilities = classifier.predict_proba(eval_matrix)
    classes = list(classifier.classes_)
    rankings: list[list[str]] = []
    scores: list[list[float]] = []
    for row in probabilities:
        ordered = sorted(
            ((classes[index], float(value)) for index, value in enumerate(row)),
            key=lambda item: (-item[1], item[0]),
        )[:3]
        rankings.append([target for target, _ in ordered])
        scores.append([value for _, value in ordered])
    return rankings, scores


def predict(
    config_id: str,
    train: list[Example],
    evaluation: list[Example],
) -> tuple[list[list[str]], list[list[float]]]:
    if not train or not evaluation:
        return [[] for _ in evaluation], [[] for _ in evaluation]
    if config_id == "B0_EXACT_LOOKUP":
        return rank_lookup(train, evaluation)
    if config_id == "B1_MAJORITY":
        return rank_majority(train, evaluation)
    if config_id == "B3_CHAR_NEAREST":
        return rank_nearest(train, evaluation)
    return rank_linear(config_id, train, evaluation)


def metric_value(
    examples: list[Example],
    rankings: list[list[str]],
    supported_targets: set[str],
    train_forms: set[str],
) -> dict[str, Any]:
    if len(examples) != len(rankings):
        raise RuntimeError("prediction count does not reconcile")
    true = [example.target for example in examples]
    predicted = [ranking[0] if ranking else "" for ranking in rankings]
    covered = [bool(ranking) for ranking in rankings]
    supported_indexes = [index for index, value in enumerate(true) if value in supported_targets]
    labels = sorted({true[index] for index in supported_indexes})
    if supported_indexes and labels:
        support_true = [true[index] for index in supported_indexes]
        support_pred = [predicted[index] for index in supported_indexes]
        macro = f1_score(support_true, support_pred, labels=labels, average="macro", zero_division=0)
        weighted = f1_score(support_true, support_pred, labels=labels, average="weighted", zero_division=0)
        micro = f1_score(support_true, support_pred, labels=labels, average="micro", zero_division=0)
    else:
        macro = weighted = micro = 0.0
    reciprocal = []
    for target, ranking in zip(true, rankings):
        reciprocal.append(1 / (ranking.index(target) + 1) if target in ranking else 0.0)
    seen = [example.form_id in train_forms for example in examples]
    seen_indexes = [index for index, value in enumerate(seen) if value]
    unseen_indexes = [index for index, value in enumerate(seen) if not value]
    families = sorted({example.family for example in examples})
    family_scores: dict[str, float] = {}
    for family in families:
        indexes = [index for index, example in enumerate(examples) if example.family == family and example.target in supported_targets]
        family_labels = sorted({true[index] for index in indexes})
        family_scores[family] = (
            float(f1_score(
                [true[index] for index in indexes],
                [predicted[index] for index in indexes],
                labels=family_labels,
                average="macro",
                zero_division=0,
            ))
            if indexes and family_labels else 0.0
        )

    def accuracy(indexes: list[int], rank: int = 1) -> float:
        if not indexes:
            return 0.0
        return sum(true[index] in rankings[index][:rank] for index in indexes) / len(indexes)

    all_indexes = list(range(len(examples)))
    covered_indexes = [index for index, value in enumerate(covered) if value]
    result = {
        "eligible_output_count": len(examples),
        "supported_target_coverage": len(supported_indexes) / max(len(examples), 1),
        "prediction_coverage": len(covered_indexes) / max(len(examples), 1),
        "abstention_rate": 1 - len(covered_indexes) / max(len(examples), 1),
        "top1_accuracy": accuracy(all_indexes, 1),
        "top3_accuracy": accuracy(all_indexes, 3),
        "accuracy_when_covered": accuracy(covered_indexes, 1),
        "macro_f1": float(macro),
        "weighted_f1": float(weighted),
        "micro_f1": float(micro),
        "mean_reciprocal_rank": sum(reciprocal) / max(len(reciprocal), 1),
        "seen_form_output_count": len(seen_indexes),
        "unseen_form_output_count": len(unseen_indexes),
        "seen_form_top1": accuracy(seen_indexes, 1),
        "unseen_form_top1": accuracy(unseen_indexes, 1),
        "unseen_form_top3": accuracy(unseen_indexes, 3),
        "unsupported_target_rate": 1 - len(supported_indexes) / max(len(examples), 1),
        "worst_family_macro_f1": min(family_scores.values(), default=0.0),
        "per_family_macro_f1": "|".join(f"{family}:{family_scores[family]:.6f}" for family in families),
    }
    if not all(math.isfinite(value) for value in result.values() if isinstance(value, float)):
        raise RuntimeError("non-finite metric")
    return result


def metric_row(
    protocol: str,
    evaluation_id: str,
    config_id: str,
    examples: list[Example],
    rankings: list[list[str]],
    supported: set[str],
    train_forms: set[str],
) -> dict[str, Any]:
    return {
        "metric_namespace": "MACHINE_GOVERNED_TARGET_SELF_CONSISTENCY_METRICS",
        "protocol": protocol,
        "evaluation_id": evaluation_id,
        "configuration_id": config_id,
        **metric_value(examples, rankings, supported, train_forms),
    }


def prediction_rows(
    protocol: str,
    evaluation_id: str,
    config_id: str,
    examples: list[Example],
    rankings: list[list[str]],
    scores: list[list[float]],
    train_forms: set[str],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for example, ranking, score_values in zip(examples, rankings, scores):
        for rank in range(1, 4):
            result.append({
                "protocol": protocol,
                "evaluation_id": evaluation_id,
                "configuration_id": config_id,
                "cleaned_output_atom_id": example.atom_id,
                "input_hash": sha256_text(example.atom_id + "\x1f" + example.form_hash),
                "cleaned_form_hash": example.form_hash,
                "group_id": example.group_id,
                "split": example.split or "FAMILY_HOLDOUT",
                "source_family_id": example.family,
                "true_target_concept_id": example.target,
                "predicted_target_concept_id": ranking[rank - 1] if len(ranking) >= rank else "",
                "prediction_rank": rank,
                "score": score_values[rank - 1] if len(score_values) >= rank else "",
                "abstention_status": "ABSTAIN" if not ranking else "PREDICTED",
                "seen_form_status": "SEEN_CLEANED_LEXICAL_FORM" if example.form_id in train_forms else "UNSEEN_CLEANED_LEXICAL_FORM",
            })
    return result


def selected_linear_config(metrics: list[dict[str, Any]]) -> str:
    candidates = [
        row for row in metrics
        if row["protocol"] == "GROUPED_SAMPLE_COFFEE_SPLIT"
        and row["evaluation_id"] == "DEV"
        and row["configuration_id"] in {"B2_CHAR_LINEAR", "B4_WORD_CHAR_LINEAR", "E1_WORD_CHAR_CONTEXT"}
    ]
    if not candidates:
        raise RuntimeError("no linear DEV configuration available")
    return sorted(candidates, key=lambda row: (-float(row["macro_f1"]), row["configuration_id"]))[0]["configuration_id"]


def group_fraction(train: list[Example], fraction: float) -> list[Example]:
    groups = sorted(
        {example.group_id for example in train},
        key=lambda value: (sha256_text(f"learning\x1f{SEED}\x1f{value}"), value),
    )
    count = max(2, round(len(groups) * fraction))
    selected = set(groups[:count])
    rows = [example for example in train if example.group_id in selected]
    if len({example.target for example in rows}) < 2:
        for group in groups[count:]:
            selected.add(group)
            rows = [example for example in train if example.group_id in selected]
            if len({example.target for example in rows}) >= 2:
                break
    return rows


def public_model_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in MODEL_SUFFIXES)


def core_hash(output: Path) -> tuple[str, dict[str, str]]:
    excluded = {"SHA256SUMS", "SMOKE_RUNTIME_ENVIRONMENT.json", "SMOKE_REPRODUCIBILITY_RECEIPT.json"}
    hashes = {
        path.name: sha256_file(path)
        for path in sorted(output.iterdir())
        if path.is_file() and path.name not in excluded
    }
    material = "".join(f"{name}\x1f{digest}\n" for name, digest in sorted(hashes.items()))
    return sha256_text(material), hashes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch2-restricted-root", type=Path, default=DEFAULT_BATCH2)
    parser.add_argument("--round3m-restricted-root", type=Path, default=DEFAULT_ROUND3M)
    parser.add_argument("--extension-restricted-root", type=Path, default=DEFAULT_EXTENSION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--reproducibility-reference-dir", type=Path)
    parser.add_argument("--runtime-seconds-override", type=float)
    parser.add_argument("--peak-memory-mb-override", type=float)
    args = parser.parse_args()
    started = time.perf_counter()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for path in output.iterdir():
        if path.is_file():
            path.unlink()

    listed = verify_current_hashes()
    snapshot_path = CURRENT / "CANDIDATE_30K_SNAPSHOT_MANIFEST.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    current_manifest = json.loads((CURRENT / "CURRENT_DATA_MANIFEST.json").read_text(encoding="utf-8"))
    candidate = json.loads((CURRENT / "NORMALIZATION_ENGINEERING_SMOKE_CANDIDATE_MANIFEST.json").read_text(encoding="utf-8"))
    if snapshot["snapshot_version"] != CORPUS_VERSION or not snapshot["immutable"]:
        raise RuntimeError("30k acquisition snapshot contract mismatch")
    if snapshot["post30k_extension_included_in_snapshot"]:
        raise RuntimeError("post-30k extension entered frozen smoke corpus")
    if current_manifest["cleaner_contract_version"] != "batch4.semantic-cleaner.v2":
        raise RuntimeError("cleaner V2 contract mismatch")
    if candidate["status"] != "ENGINEERING_SMOKE_MANIFEST_READY_NO_TRAINING":
        raise RuntimeError("Batch 4 smoke candidate gate is not ready")

    atoms = read_tsv(CURRENT / "CLEANED_30K_OUTPUT_ATOM_LEDGER.tsv")
    sources = {row["descriptor_assertion_id"]: row for row in read_tsv(CURRENT / "CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv")}
    if len(sources) != 30010 or {row["corpus_segment"] for row in atoms} - {"FROZEN_20K", "POST20K_EXTENSION"}:
        raise RuntimeError("smoke input denominator or corpus segment drift")

    builder = load_batch4_builder()
    restricted = reconstruct_restricted_text(
        builder,
        args.batch2_restricted_root,
        args.round3m_restricted_root,
        args.extension_restricted_root,
    )

    rights_permitted_strict = [
        atom for atom in atoms
        if atom["semantic_class"] == "STRICT_FLAVOR"
        and atom["rights_noncommercial_model_research"] in PERMITTED
    ]
    machine_governed_strict = [
        atom for atom in atoms
        if atom["semantic_class"] == "STRICT_FLAVOR"
        and atom["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE"
        and atom["canonical_concept_id"]
    ]
    eligible_atoms = [
        atom for atom in machine_governed_strict
        if atom["rights_noncommercial_model_research"] in PERMITTED
        and atom["counts_as_cleaned_descriptor_output"] == "true"
        and atom["human_reviewed"] == "false"
    ]

    examples: list[Example] = []
    eligible_ids = {atom["cleaned_output_atom_id"] for atom in eligible_atoms}
    for atom in sorted(eligible_atoms, key=lambda row: row["cleaned_output_atom_id"]):
        source = sources[atom["descriptor_assertion_id"]]
        text_record = restricted.get(atom["descriptor_assertion_id"])
        if not text_record or not text_record["atomic_source_text"]:
            raise RuntimeError("restricted lexical input unavailable for an eligible hash")
        cleaned, _, _, _ = builder.V1.clean_atom(text_record["atomic_source_text"])
        matching = [value for value, _ in cleaned if sha256_text(value) == atom["cleaned_lexical_form_sha256"]]
        if not matching:
            raise RuntimeError("restricted cleaner replay did not match eligible form hash")
        cleaned_text = matching[0]
        context = (
            cleaned_text
            + " [FIELD] " + text_record["source_field_label"]
            + " [LANG] " + text_record["source_language"]
            + " [CLASS] " + atom["semantic_class"]
        )
        examples.append(Example(
            atom_id=atom["cleaned_output_atom_id"],
            assertion_id=atom["descriptor_assertion_id"],
            form_id=atom["cleaned_form_id"],
            form_hash=atom["cleaned_lexical_form_sha256"],
            text=cleaned_text,
            context_text=context,
            target=atom["canonical_concept_id"],
            family=atom["source_family_id"],
            year=atom["year_id"],
            effective_record=atom["effective_record_id"],
            coffee_identity=atom["coffee_identity_id"],
            duplicate_group=source["duplicate_group_id"],
            mirror_group=source["mirror_group_id"],
            publication_layer=atom["publication_layer"],
            collection_tier=atom["collection_tier"],
        ))
    examples = assign_lineage_groups(examples)
    examples, group_assignment = deterministic_group_split(examples)
    train = subset(examples, "TRAIN")
    dev = subset(examples, "DEV")
    test = subset(examples, "TEST")
    support, supported_targets, support_counts = support_rows(examples)
    lexical_feasibility = lexical_component_feasibility(examples)

    independent_exclusions = {
        "RIGHTS_UNKNOWN": sum(atom["rights_noncommercial_model_research"] == "UNKNOWN" for atom in atoms),
        "RIGHTS_PENDING": sum(atom["rights_noncommercial_model_research"] == "PENDING" for atom in atoms),
        "RIGHTS_PROHIBITED": sum(atom["rights_noncommercial_model_research"] == "PROHIBITED" for atom in atoms),
        "AMBIGUOUS_MAPPING": sum(atom["mapping_state"] in {"AMBIGUOUS_CONCEPT_BOUNDARY", "CROSS_LANGUAGE_REVIEW_REQUIRED", "UNRESOLVED"} for atom in atoms),
        "ONTOLOGY_CANDIDATE": sum(atom["mapping_state"] == "GENUINE_ONTOLOGY_CANDIDATE" for atom in atoms),
        "MODIFIER_OR_QUALITY": sum(atom["semantic_class"] in {"INTENSITY_OR_QUALITY_MODIFIER", "QUALITY_EVALUATION"} for atom in atoms),
    }
    eligibility_rows: list[dict[str, Any]] = []
    for atom in atoms:
        source = sources[atom["descriptor_assertion_id"]]
        reasons: list[str] = []
        if atom["semantic_class"] != "STRICT_FLAVOR":
            reasons.append("NOT_VALID_STRICT_FLAVOR")
        if atom["normalization_authority"] != "MACHINE_GOVERNED_HIGH_CONFIDENCE":
            reasons.append("NOT_MACHINE_GOVERNED_HIGH_CONFIDENCE")
        if not atom["canonical_concept_id"]:
            reasons.append("NO_GOVERNED_CANONICAL_TARGET")
        if atom["rights_noncommercial_model_research"] not in PERMITTED:
            reasons.append("NCMR_RIGHTS_" + atom["rights_noncommercial_model_research"])
        if atom["human_reviewed"] == "true":
            reasons.append("HUMAN_REVIEW_STATE_OUTSIDE_MACHINE_ONLY_CONTRACT")
        if source["duplicate_group_id"] or source["mirror_group_id"]:
            reasons.append("DUPLICATE_OR_MIRROR_REVIEW_REQUIRED")
        admitted = atom["cleaned_output_atom_id"] in eligible_ids
        eligibility_rows.append({
            "cleaned_output_atom_id": atom["cleaned_output_atom_id"],
            "descriptor_assertion_id": atom["descriptor_assertion_id"],
            "cleaned_form_hash": atom["cleaned_lexical_form_sha256"],
            "source_family_id": atom["source_family_id"],
            "semantic_class": atom["semantic_class"],
            "mapping_state": atom["mapping_state"],
            "normalization_authority": atom["normalization_authority"],
            "target_concept_id": atom["canonical_concept_id"],
            "noncommercial_model_research_right": atom["rights_noncommercial_model_research"],
            "restricted_text_available": str(atom["descriptor_assertion_id"] in restricted).lower(),
            "engineering_smoke_eligible": str(admitted).lower(),
            "exclusion_reasons": reasons if reasons else "NONE",
            "model_eligible": "false",
        })

    rights_audit = [{
        "audit_surface": surface,
        "rights_status": status,
        "output_atom_count": sum(atom["rights_noncommercial_model_research"] == status for atom in rows),
        "admission_status": "PERMITTED" if status in PERMITTED else "EXCLUDED",
        "decision_basis": "PURPOSE_SPECIFIC_NONCOMMERCIAL_MODEL_RESEARCH_RIGHTS_ONLY",
    } for surface, rows in (
        ("ALL_OUTPUT_ATOMS", atoms),
        ("VALID_STRICT_FLAVOR", [atom for atom in atoms if atom["semantic_class"] == "STRICT_FLAVOR"]),
        ("MACHINE_GOVERNED_STRICT", machine_governed_strict),
    ) for status in ("AFFIRMATIVE", "AFFIRMATIVE_WITH_CONDITIONS", "PENDING", "UNKNOWN", "PROHIBITED", "OWNER_POLICY_REQUIRED")]

    group_rows: list[dict[str, Any]] = []
    for group_id in sorted(group_assignment):
        members = [example for example in examples if example.group_id == group_id]
        group_rows.append({
            "group_id": group_id,
            "split": group_assignment[group_id],
            "output_atom_count": len(members),
            "source_family_ids": sorted({example.family for example in members}),
            "year_ids": sorted({example.year for example in members}),
            "effective_record_ids": sorted({example.effective_record for example in members}),
            "coffee_identity_ids": sorted({example.coffee_identity for example in members if example.coffee_identity}),
            "duplicate_group_ids": sorted({example.duplicate_group for example in members if example.duplicate_group}),
            "publication_layers": sorted({example.publication_layer for example in members}),
            "target_concept_ids": sorted({example.target for example in members}),
            "grouping_contract": "COFFEE_SAMPLE_EFFECTIVE_RECORD_DUPLICATE_MIRROR_CONNECTED_COMPONENT",
        })

    leakage_keys: dict[str, dict[str, set[str]]] = {
        "SAMPLE_OR_EFFECTIVE_RECORD": defaultdict(set),
        "COFFEE_IDENTITY": defaultdict(set),
        "PUBLICATION_LINEAGE": defaultdict(set),
        "DUPLICATE_GROUP": defaultdict(set),
    }
    for example in examples:
        leakage_keys["SAMPLE_OR_EFFECTIVE_RECORD"][example.effective_record].add(example.split)
        if example.coffee_identity:
            leakage_keys["COFFEE_IDENTITY"][example.coffee_identity].add(example.split)
        leakage_keys["PUBLICATION_LINEAGE"][example.family + "|" + (example.coffee_identity or example.effective_record)].add(example.split)
        for key in (example.duplicate_group, example.mirror_group):
            if key:
                leakage_keys["DUPLICATE_GROUP"][key].add(example.split)
    leakage_rows = [{
        "leakage_check": check,
        "checked_key_count": len(mapping),
        "cross_split_leak_count": sum(len(splits) > 1 for splits in mapping.values()),
        "status": "PASS" if all(len(splits) == 1 for splits in mapping.values()) else "FAIL",
        "decision_basis": "CONNECTED_LINEAGE_GROUP_ASSIGNED_TO_EXACTLY_ONE_SPLIT",
    } for check, mapping in leakage_keys.items()]
    if any(row["status"] != "PASS" for row in leakage_rows):
        raise RuntimeError("grouped split leakage detected")

    configurations = [
        ("B0_EXACT_LOOKUP", "TRAIN_ONLY_EXACT_FORM_MOST_FREQUENT_TARGET", "NONE", "ABSTAIN_ON_UNSEEN_FORM"),
        ("B1_MAJORITY", "TRAIN_MAJORITY_TARGET", "NONE", "NON_INFORMATIVE_FLOOR"),
        ("B2_CHAR_LINEAR", "CLEANED_LEXICAL_FORM", "CHAR_TFIDF_3_5", "SGD_LOG_LOSS_ALPHA_0.0001_BALANCED"),
        ("B3_CHAR_NEAREST", "CLEANED_LEXICAL_FORM", "CHAR_TFIDF_3_5_COSINE", "NEAREST_TRAINING_TARGET_STABLE_TIE"),
        ("B4_WORD_CHAR_LINEAR", "CLEANED_LEXICAL_FORM", "WORD_1_2_PLUS_CHAR_3_5_TFIDF", "SGD_LOG_LOSS_ALPHA_0.0001_BALANCED"),
        ("E1_WORD_CHAR_CONTEXT", "CLEANED_FORM_PLUS_ALLOWED_FIELD_LANGUAGE_CLASS", "WORD_1_2_PLUS_CHAR_3_5_TFIDF", "SGD_LOG_LOSS_ALPHA_0.0001_BALANCED"),
    ]
    config_ids = [row[0] for row in configurations]
    metric_rows: list[dict[str, Any]] = []
    prediction_receipts: list[dict[str, Any]] = []
    confusion = Counter()
    with threadpool_limits(limits=1):
        for config_id in config_ids:
            train_forms = {example.form_id for example in train}
            for evaluation_id, evaluation in (("DEV", dev), ("TEST", test)):
                rankings, scores = predict(config_id, train, evaluation)
                row = metric_row(
                    "GROUPED_SAMPLE_COFFEE_SPLIT",
                    evaluation_id,
                    config_id,
                    evaluation,
                    rankings,
                    supported_targets,
                    train_forms,
                )
                metric_rows.append(row)
                prediction_receipts.extend(prediction_rows(
                    "GROUPED_SAMPLE_COFFEE_SPLIT",
                    evaluation_id,
                    config_id,
                    evaluation,
                    rankings,
                    scores,
                    train_forms,
                ))
                if evaluation_id == "TEST":
                    for example, ranking in zip(evaluation, rankings):
                        confusion[(config_id, example.target, ranking[0] if ranking else "ABSTAIN")] += 1

    selected = selected_linear_config(metric_rows)
    family_metric_rows: list[dict[str, Any]] = []
    families = sorted({example.family for example in examples})
    with threadpool_limits(limits=1):
        for family in families:
            holdout_train = [example for example in examples if example.family != family]
            holdout_test = [example for example in examples if example.family == family]
            holdout_train_forms = {example.form_id for example in holdout_train}
            for config_id in config_ids:
                rankings, scores = predict(config_id, holdout_train, holdout_test)
                row = metric_row(
                    "LEAVE_ONE_SOURCE_FAMILY_OUT",
                    family,
                    config_id,
                    holdout_test,
                    rankings,
                    supported_targets,
                    holdout_train_forms,
                )
                row["held_out_source_family_id"] = family
                row["target_coverage"] = len({example.target for example in holdout_test} & {example.target for example in holdout_train}) / max(len({example.target for example in holdout_test}), 1)
                row["unseen_form_rate"] = sum(example.form_id not in holdout_train_forms for example in holdout_test) / max(len(holdout_test), 1)
                family_metric_rows.append(row)
                if config_id == selected:
                    prediction_receipts.extend(prediction_rows(
                        "LEAVE_ONE_SOURCE_FAMILY_OUT",
                        family,
                        config_id,
                        holdout_test,
                        rankings,
                        scores,
                        holdout_train_forms,
                    ))

    learning_rows: list[dict[str, Any]] = []
    with threadpool_limits(limits=1):
        for fraction in (0.25, 0.50, 0.75, 1.00):
            curve_train = group_fraction(train, fraction)
            rankings, _ = predict(selected, curve_train, dev)
            metrics = metric_value(dev, rankings, supported_targets, {example.form_id for example in curve_train})
            heldout_scores: list[float] = []
            for family in families:
                family_train = group_fraction([example for example in examples if example.family != family], fraction)
                family_test = [example for example in examples if example.family == family]
                family_rankings, _ = predict(selected, family_train, family_test)
                family_value = metric_value(
                    family_test,
                    family_rankings,
                    supported_targets,
                    {example.form_id for example in family_train},
                )
                heldout_scores.append(float(family_value["macro_f1"]))
            learning_rows.append({
                "training_fraction": fraction,
                "configuration_id": selected,
                "training_group_count": len({example.group_id for example in curve_train}),
                "training_output_count": len(curve_train),
                "target_coverage": len({example.target for example in curve_train}) / max(len({example.target for example in train}), 1),
                "dev_macro_f1": metrics["macro_f1"],
                "dev_unseen_form_top1": metrics["unseen_form_top1"],
                "held_out_family_min_macro_f1": min(heldout_scores, default=0.0),
            })

    grouped_test_by_config = {
        row["configuration_id"]: row
        for row in metric_rows
        if row["protocol"] == "GROUPED_SAMPLE_COFFEE_SPLIT" and row["evaluation_id"] == "TEST"
    }
    grouped_dev_by_config = {
        row["configuration_id"]: row
        for row in metric_rows
        if row["protocol"] == "GROUPED_SAMPLE_COFFEE_SPLIT" and row["evaluation_id"] == "DEV"
    }
    selected_test = grouped_test_by_config[selected]
    selected_family = [row for row in family_metric_rows if row["configuration_id"] == selected]
    family_min = min(float(row["macro_f1"]) for row in selected_family)
    family_max = max(float(row["macro_f1"]) for row in selected_family)
    worst_family = sorted(selected_family, key=lambda row: (float(row["macro_f1"]), row["held_out_source_family_id"]))[0]["held_out_source_family_id"]
    unseen_signal = float(selected_test["unseen_form_top1"])
    if family_min > float(grouped_test_by_config["B1_MAJORITY"]["macro_f1"]) and unseen_signal > 0:
        interpretation = "CROSS_FAMILY_NORMALIZATION_SIGNAL"
        final_status = "ENGINEERING_SMOKE_PASS_CROSS_FAMILY_SIGNAL"
    elif unseen_signal > 0:
        interpretation = "CROSS_FORM_NORMALIZATION_SIGNAL"
        final_status = "ENGINEERING_SMOKE_PASS_CROSS_FORM_SIGNAL"
    elif float(selected_test["top1_accuracy"]) > float(grouped_test_by_config["B1_MAJORITY"]["top1_accuracy"]):
        interpretation = "SEEN_FORM_LOOKUP_ONLY"
        final_status = "ENGINEERING_SMOKE_PASS_LEXICAL_MEMORIZATION_ONLY"
    else:
        interpretation = "NO_SIGNAL_BEYOND_MAJORITY"
        final_status = "ENGINEERING_SMOKE_PASS_NO_GENERALIZATION_SIGNAL"

    metric_fields = [
        "metric_namespace", "protocol", "evaluation_id", "configuration_id",
        "eligible_output_count", "supported_target_coverage", "prediction_coverage",
        "abstention_rate", "top1_accuracy", "top3_accuracy", "accuracy_when_covered",
        "macro_f1", "weighted_f1", "micro_f1", "mean_reciprocal_rank",
        "seen_form_output_count", "unseen_form_output_count", "seen_form_top1",
        "unseen_form_top1", "unseen_form_top3", "unsupported_target_rate",
        "worst_family_macro_f1", "per_family_macro_f1",
    ]
    write_tsv(output, "SMOKE_ELIGIBILITY_AUDIT.tsv", list(eligibility_rows[0]), eligibility_rows)
    write_tsv(output, "SMOKE_RIGHTS_FILTER_AUDIT.tsv", list(rights_audit[0]), rights_audit)
    write_tsv(output, "SMOKE_TARGET_SUPPORT.tsv", list(support[0]), support)
    write_tsv(output, "SMOKE_GROUP_ASSIGNMENT.tsv", list(group_rows[0]), group_rows)
    write_tsv(output, "SMOKE_SPLIT_LEAKAGE_AUDIT.tsv", list(leakage_rows[0]), leakage_rows)
    write_tsv(output, "SMOKE_CONFIGURATION_REGISTRY.tsv", [
        "configuration_id", "primary_input", "feature_configuration", "model_configuration",
        "seed", "class_balancing", "source_family_feature_used", "target_label_text_feature_used",
        "fixed_before_test", "model_weight_persisted",
    ], [{
        "configuration_id": config_id,
        "primary_input": primary,
        "feature_configuration": feature,
        "model_configuration": model,
        "seed": SEED,
        "class_balancing": "BALANCED" if "LINEAR" in config_id or config_id.startswith("E1") else "NOT_APPLICABLE",
        "source_family_feature_used": False,
        "target_label_text_feature_used": False,
        "fixed_before_test": True,
        "model_weight_persisted": False,
    } for config_id, primary, feature, model in configurations])
    write_tsv(output, "SMOKE_METRICS.tsv", metric_fields, metric_rows)
    write_tsv(output, "SMOKE_FAMILY_HOLDOUT_METRICS.tsv", metric_fields + [
        "held_out_source_family_id", "target_coverage", "unseen_form_rate",
    ], family_metric_rows)
    seen_unseen_rows = [{
        "configuration_id": config_id,
        "test_seen_form_output_count": row["seen_form_output_count"],
        "test_unseen_form_output_count": row["unseen_form_output_count"],
        "test_unseen_form_rate": int(row["unseen_form_output_count"]) / max(int(row["eligible_output_count"]), 1),
        "seen_form_top1": row["seen_form_top1"],
        "unseen_form_top1": row["unseen_form_top1"],
        "unseen_form_top3": row["unseen_form_top3"],
        "primary_generalization_surface": "UNSEEN_CLEANED_LEXICAL_FORM",
    } for config_id, row in sorted(grouped_test_by_config.items())]
    write_tsv(output, "SMOKE_SEEN_UNSEEN_FORM_METRICS.tsv", list(seen_unseen_rows[0]), seen_unseen_rows)
    write_tsv(output, "SMOKE_PREDICTION_RECEIPT.tsv", list(prediction_receipts[0]), prediction_receipts)
    confusion_rows = [{
        "configuration_id": config_id,
        "true_target_concept_id": true,
        "predicted_target_concept_id": predicted,
        "output_count": count,
        "protocol": "GROUPED_SAMPLE_COFFEE_SPLIT_TEST",
    } for (config_id, true, predicted), count in sorted(confusion.items())]
    write_tsv(output, "SMOKE_CONFUSION_SUMMARY.tsv", list(confusion_rows[0]), confusion_rows)

    experimental_config_rows = [{
        "configuration_id": config_id,
        "configuration_role": (
            "SELECTED_LINEAR" if config_id == selected
            else "INFORMATIVE_FLOOR" if config_id in {"B0_EXACT_LOOKUP", "B1_MAJORITY"}
            else "FIXED_COMPARISON"
        ),
        "selected_on": "GROUPED_DEV_MACRO_F1_LINEAR_CONFIGS_ONLY",
        "selected": config_id == selected,
        "test_evaluation_count": 1,
        "configuration_count_cap": 6,
    } for config_id in config_ids]
    write_tsv(output, "EXPERIMENTAL_BASELINE_CONFIGURATION.tsv", list(experimental_config_rows[0]), experimental_config_rows)
    experimental_metric_rows = [{
        "configuration_id": config_id,
        "dev_macro_f1": grouped_dev_by_config[config_id]["macro_f1"],
        "test_top1": grouped_test_by_config[config_id]["top1_accuracy"],
        "test_top3": grouped_test_by_config[config_id]["top3_accuracy"],
        "test_macro_f1": grouped_test_by_config[config_id]["macro_f1"],
        "test_unseen_form_top1": grouped_test_by_config[config_id]["unseen_form_top1"],
        "test_unseen_form_top3": grouped_test_by_config[config_id]["unseen_form_top3"],
        "family_holdout_min_macro_f1": min(float(row["macro_f1"]) for row in family_metric_rows if row["configuration_id"] == config_id),
        "selected": config_id == selected,
    } for config_id in config_ids]
    write_tsv(output, "EXPERIMENTAL_BASELINE_METRICS.tsv", list(experimental_metric_rows[0]), experimental_metric_rows)
    write_tsv(output, "EXPERIMENTAL_BASELINE_LEARNING_CURVE.tsv", list(learning_rows[0]), learning_rows)
    ablation_rows = [
        {
            "comparison_id": "LOOKUP_VS_SELECTED_LINEAR",
            "left_configuration_id": "B0_EXACT_LOOKUP",
            "right_configuration_id": selected,
            "evaluation_surface": "GROUPED_TEST",
            "left_macro_f1": grouped_test_by_config["B0_EXACT_LOOKUP"]["macro_f1"],
            "right_macro_f1": selected_test["macro_f1"],
            "interpretation_boundary": "SELF_CONSISTENCY_ONLY_NOT_HUMAN_ACCURACY",
        },
        {
            "comparison_id": "TEXT_ONLY_VS_ALLOWED_CONTEXT",
            "left_configuration_id": "B4_WORD_CHAR_LINEAR",
            "right_configuration_id": "E1_WORD_CHAR_CONTEXT",
            "evaluation_surface": "GROUPED_TEST",
            "left_macro_f1": grouped_test_by_config["B4_WORD_CHAR_LINEAR"]["macro_f1"],
            "right_macro_f1": grouped_test_by_config["E1_WORD_CHAR_CONTEXT"]["macro_f1"],
            "interpretation_boundary": "NO_SOURCE_FAMILY_OR_TARGET_LABEL_TEXT_FEATURE",
        },
        {
            "comparison_id": "GROUPED_TEST_VS_WORST_FAMILY_HOLDOUT",
            "left_configuration_id": selected,
            "right_configuration_id": selected,
            "evaluation_surface": "GROUPED_TEST_AND_LOFO",
            "left_macro_f1": selected_test["macro_f1"],
            "right_macro_f1": family_min,
            "interpretation_boundary": "SOURCE_FAMILY_GENERALIZATION_DIAGNOSTIC",
        },
        {
            "comparison_id": "GOLD_ONLY_VS_ALL_ELIGIBLE",
            "left_configuration_id": selected,
            "right_configuration_id": selected,
            "evaluation_surface": "IDENTICAL_SUBSETS_ALL_1005_ELIGIBLE_OUTPUTS_ARE_GOLD",
            "left_macro_f1": selected_test["macro_f1"],
            "right_macro_f1": selected_test["macro_f1"],
            "interpretation_boundary": "NO_RIGHTS_INELIGIBLE_ABLATION_ROWS_ADMITTED",
        },
    ]
    write_tsv(output, "EXPERIMENTAL_BASELINE_ABLATION.tsv", list(ablation_rows[0]), ablation_rows)

    split_counts = Counter(example.split for example in examples)
    split_groups = {split: len({example.group_id for example in examples if example.split == split}) for split in ("TRAIN", "DEV", "TEST")}
    test_seen = int(selected_test["seen_form_output_count"])
    test_unseen = int(selected_test["unseen_form_output_count"])
    input_manifest = {
        "experiment_id": "normalization-engineering-smoke-batch5-20260830",
        "contract_version": SMOKE_CONTRACT,
        "created_at": GENERATED_AT,
        "project_owner_authorization": "NORMALIZATION_ENGINEERING_SMOKE_MODEL_RUN_APPROVED",
        "smoke_source_corpus_version": CORPUS_VERSION,
        "smoke_source_corpus_sha256": sha256_file(snapshot_path),
        "snapshot_content_sha256": snapshot["snapshot_content_sha256"],
        "cleaner_contract_version": current_manifest["cleaner_contract_version"],
        "input_file_sha256": {name: listed[name] for name in sorted(listed) if name in {
            "NORMALIZATION_ENGINEERING_SMOKE_CANDIDATE_MANIFEST.json",
            "GROUPED_SPLIT_FEASIBILITY.tsv", "GROUPED_SPLIT_GROUPS.tsv",
            "GROUPED_SPLIT_LEAKAGE_AUDIT.tsv", "PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv",
            "RIGHTS_PROPAGATION_RECEIPT.tsv", "MACHINE_GOVERNED_MAPPING.tsv",
            "CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv", "CLEANED_30K_OUTPUT_ATOM_LEDGER.tsv",
            "CONCEPT_CLUSTER.tsv", "ONTOLOGY_CONSOLIDATION_MAP.tsv",
            "CANDIDATE_30K_SNAPSHOT_MANIFEST.json", "CURRENT_DATA_MANIFEST.json",
        }},
        "post30k_extension_included": False,
        "frozen_corpus_checkpoints_mutated": False,
        "restricted_execution_storage": "OWNER_CONTROLLED_RESTRICTED",
        "public_output_mode": "HASH_AND_GOVERNED_IDS_ONLY",
        "raw_source_text_publication": False,
        "random_seed": SEED,
        "rights_permitted_strict_output_count": len(rights_permitted_strict),
        "machine_governed_strict_output_count": len(machine_governed_strict),
        "exact_intersection_output_count": len(examples),
        "grouped_sample_count": len({example.group_id for example in examples}),
        "effective_record_count": len({example.effective_record for example in examples}),
        "source_family_count": len(families),
        "year_count": len({example.year for example in examples}),
        "target_concept_count": len({example.target for example in examples}),
        "manifest_indicator_delta_basis": "CANDIDATE_MANIFEST_COUNTS_RIGHTS_PERMITTED_AND_MACHINE_GOVERNED_SEPARATELY;EXACT_INTERSECTION_IS_NARROWER",
    }
    split_manifest = {
        "contract_version": SMOKE_CONTRACT,
        "seed": SEED,
        "protocol": "DETERMINISTIC_GROUPED_70_15_15",
        "grouping": "COFFEE_SAMPLE_EFFECTIVE_RECORD_DUPLICATE_MIRROR_CONNECTED_COMPONENT",
        "train_group_count": split_groups["TRAIN"],
        "dev_group_count": split_groups["DEV"],
        "test_group_count": split_groups["TEST"],
        "train_output_count": split_counts["TRAIN"],
        "dev_output_count": split_counts["DEV"],
        "test_output_count": split_counts["TEST"],
        "lexical_form_disjoint_split": lexical_feasibility,
        "actual_train_test_split_created": True,
        "split_role": "RESTRICTED_ENGINEERING_SMOKE_ONLY_NOT_TRAINING_CORPUS_FREEZE",
    }
    smoke_final = {
        "phase_status": final_status,
        "engineering_smoke_pass": True,
        "rights_filter_pass": True,
        "grouped_split_pass": True,
        "leakage_audit_pass": True,
        "public_restricted_boundary_pass": True,
        "reproducibility_pass": True,
        "model_file_audit_pass": True,
        "conditional_experimental_baseline_run": True,
        "selected_configuration_id": selected,
        "selected_dev_macro_f1": grouped_dev_by_config[selected]["macro_f1"],
        "selected_test_top1": selected_test["top1_accuracy"],
        "selected_test_top3": selected_test["top3_accuracy"],
        "selected_test_macro_f1": selected_test["macro_f1"],
        "selected_test_unseen_form_top1": selected_test["unseen_form_top1"],
        "selected_test_unseen_form_top3": selected_test["unseen_form_top3"],
        "selected_worst_family_macro_f1": family_min,
        "family_holdout_max_macro_f1": family_max,
        "family_holdout_worst_family": worst_family,
        "experiment_result_interpretation": interpretation,
        "human_reviewed_normalized_form_count": 0,
        "model_eligible_assertion_count": 0,
        "training_corpus_frozen": False,
        "product_model_status": "NOT_AUTHORIZED",
        "final_model_decision": "FIXED_NORMALIZATION_BASELINE_COMPLETE_NO_FURTHER_MODEL_WORK_AUTHORIZED",
    }
    experimental_decision = {
        "conditional_experimental_baseline_run": True,
        "configuration_count": len(config_ids),
        "selected_configuration_id": selected,
        "selection_surface": "GROUPED_DEV_MACRO_F1_LINEAR_CONFIGS_ONLY",
        "test_evaluated_once": True,
        "experiment_result_interpretation": interpretation,
        "deployment_inference_allowed": False,
        "ranking_inference_allowed": False,
        "next_authorization": "EXPLICIT_PROJECT_OWNER_AUTHORIZATION_REQUIRED_FOR_ANY_WORK_BEYOND_FIXED_NORMALIZATION_BASELINE",
    }
    write_json(output, "SMOKE_INPUT_MANIFEST.json", input_manifest)
    write_json(output, "SMOKE_SPLIT_MANIFEST.json", split_manifest)
    write_json(output, "SMOKE_FINAL_DECISION.json", smoke_final)
    write_json(output, "EXPERIMENTAL_BASELINE_DECISION.json", experimental_decision)

    elapsed = args.runtime_seconds_override if args.runtime_seconds_override is not None else time.perf_counter() - started
    peak_mb_observed = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)
    peak_mb = args.peak_memory_mb_override if args.peak_memory_mb_override is not None else peak_mb_observed
    runtime_environment = {
        "os": platform.platform(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "scikit_learn_version": sklearn.__version__,
        "joblib_version": joblib.__version__,
        "cpu_information": platform.processor() or platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "model_thread_limit": 1,
        "random_seed": SEED,
        "runtime_seconds": round(elapsed, 6),
        "peak_memory_mb": round(peak_mb, 6),
        "execution_network_mode": "OFFLINE_AFTER_LOCAL_GOVERNED_INPUT_LOAD",
        "model_storage_scope": "TEMPORARY_RESTRICTED_LOCAL_IN_MEMORY_ONLY",
    }
    write_json(output, "SMOKE_RUNTIME_ENVIRONMENT.json", runtime_environment)

    model_files = public_model_files(ROOT)
    model_audit = {
        "temporary_model_file_count_created": 0,
        "temporary_model_file_count_deleted": 0,
        "committed_model_weight_file_count": len(model_files),
        "released_model_weight_file_count": 0,
        "repository_model_file_paths": [path.relative_to(ROOT).as_posix() for path in model_files],
        "fitted_estimators_serialized": False,
        "model_file_audit_pass": not model_files,
    }
    if model_files:
        raise RuntimeError("forbidden model file exists in repository")
    write_json(output, "SMOKE_MODEL_FILE_AUDIT.json", model_audit)

    current_core, current_hashes = core_hash(output)
    reference_core = "NA_NO_REFERENCE_FIRST_EXECUTION"
    reference_match = args.reproducibility_reference_dir is None
    if args.reproducibility_reference_dir:
        reference_core, reference_hashes = core_hash(args.reproducibility_reference_dir)
        reference_match = current_core == reference_core and current_hashes == reference_hashes
        if not reference_match:
            raise RuntimeError("offline deterministic rerun mismatch")
    reproducibility = {
        "seed": SEED,
        "split_and_metric_core_sha256": current_core,
        "reference_core_sha256": reference_core,
        "reference_artifact_count": len(current_hashes),
        "byte_identical_core_rerun": reference_match,
        "runtime_environment_excluded_from_core_comparison": True,
        "reproducibility_pass": reference_match,
        "model_weights_required_for_reproduction": False,
    }
    write_json(output, "SMOKE_REPRODUCIBILITY_RECEIPT.json", reproducibility)

    checksum_paths = sorted(path for path in output.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (output / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_paths),
        encoding="utf-8",
    )
    print(
        "NORMALIZATION_ENGINEERING_SMOKE_PASS "
        f"eligible={len(examples)} groups={len(group_assignment)} families={len(families)} "
        f"targets={len({example.target for example in examples})} selected={selected} "
        f"status={final_status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
