"""R4 source-verified cross-grader A/B/T adapter; no training or inferred answers.

Code is MIT. Source descriptions stay private under the documented CC BY/NC
intersection. This reveals another grader's report, not a live user's answer.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from flavor_m2_r1 import PARENTS
from prepare_sequential_data import BROAD_WORDS

ROOT = Path(__file__).resolve().parents[2]
FAMILY = "family.zenodo_golovinsky_q_grader_dataset"
VERSION = "m2-r4.source-verified-cross-grader-abt.v1"
SOURCE_SHA = "85df699ea18f5849ef3104100a20570d5df13e7d6cc7ce53e20c3df8a5219150"
ORDER_SEED = "M2_R4_AUX_PANEL_ORDER_V1"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def protocol():
    return {
        "version": VERSION,
        "role": "AUX_CROSS_GRADER_RECORDED_DESCRIPTOR_REVEAL_PROXY",
        "source": "https://zenodo.org/records/20840464",
        "source_sha256": SOURCE_SHA,
        "rights": "Machine CC BY 4.0 and author CC BY-NC 4.0 notice; restrictive shared noncommercial research scope; source text and model weights private; attribution retained",
        "admission": "Existing DEVELOPMENT Zenodo records with at least 3 distinct source graders having governed positive mentions; retain all admitted records including empty T",
        "expected_admission_before_target_filter": {"records": 61, "coffee_name_dependency_groups": 59},
        "identity": "Original sample ID joins source cells; original D0 normalized coffee-name group joins repeated samples; globally stable source grader hash; duplicate sample/grader rows rejected",
        "grader_order": "Ascending sha256 of " + ORDER_SEED + "| plus existing global grader identity hash; same ordering for every sample, no outcome-based ordering",
        "A": "All retained governed fine/broad mentions of first available ordered grader; Q0/Q1 visibility only",
        "B": "All retained governed fine/broad mentions of second available ordered grader; available from Q2 through Q4; selected answers must still be restricted to actually exposed options",
        "T": "Positive sensory.* mention frequency from all remaining ordered graders, excluding A exact concepts and their logically implied registered broad parents; because T is fine-only this removes only A's explicitly identical fine terms; computed once and fixed through reveal",
        "semantic_closure": "Fine implies itself and registered broad parents; neither a broad observation nor a fine term implies specific children or sibling fine terms. Shared-parent overlap is a retained related-evidence diagnostic, never equivalence or target removal",
        "parents_sha256": digest(PARENTS),
        "negative_mask": "Unmentioned, unmapped or unexposed concepts are unknown; no absent/negative labels from incomplete descriptions",
        "target_access": "T only in training loss/evaluation; no question generation or visibility function reads T; B is observed source text, never model-generated or reverse-engineered from T",
        "split": "Reuse original D0 3 outer coffee-group folds and corresponding train/held membership; shared graders across coffee folds; no participant-generalization claim",
        "comparison": "One AKR_AUX versus AKR on identical main held cases and separately identical auxiliary held cases; no additional auxiliary task",
        "loss": "main group-weighted CE + 0.25*(n_main_training_groups/n_aux_training_groups)*aux group-weighted CE + ridge10/2; same fixed 22 candidate features",
        "auxiliary_weight": 0.25,
        "ridge": 10.0,
        "historical": "Old historical regression records are audited for connectivity only; excluded from this auxiliary fitting and evaluation; no fresh confirmation",
        "interpretation": "Distinct named grader reports of a source sample, with shared coffee/session dependence and unverified rating blinding; not independent coffee samples, statistically independent truth, personalized perception or real same-person question answering",
        "new_source_count": 0,
        "new_data_connection": "Previously unused source-resolved cross-grader A/B/T on existing permitted records",
    }


def semantic_closure(concepts, parents=PARENTS):
    concepts = set(concepts)
    roots = {p for c in concepts for p in parents.get(c, ())}
    return concepts | {"attribute." + p for p in roots}


def related_by_parent(concepts, reference, parents=PARENTS):
    roots = {p for c in reference for p in parents.get(c, ())}
    return {c for c in concepts if roots.intersection(parents.get(c, ()))}


def ordered_graders(reports):
    return sorted(reports, key=lambda g: hashlib.sha256((ORDER_SEED + "|" + g).encode()).hexdigest())


def episode_from_reports(record, reports, parents=PARENTS):
    if len(reports) < 3 or any(not g or not values for g, values in reports.items()):
        raise ValueError("THREE_DISTINCT_NONEMPTY_SOURCE_GRADERS_REQUIRED")
    order = ordered_graders(reports)
    a, b = set(reports[order[0]]), set(reports[order[1]])
    excluded = semantic_closure(a, parents)
    original = Counter(c for g in order[2:] for c in set(reports[g]) if c.startswith("sensory."))
    target = {c: float(n) for c, n in sorted(original.items()) if c not in excluded}
    return {
        "record_id": record["record_id"], "group_id": record["group_id"],
        "source_family": "zenodo", "A": sorted(a), "B": sorted(b),
        "relevance": target, "targets": sorted(target),
        "split": "DEVELOPMENT", "aux_origin": VERSION,
        "identity_hash": digest({"record": record["record_id"], "ordered_graders": order}),
        "evidence_dependency_group": record["group_id"],
        "reference_grader_count": len(order) - 2,
        "source_grader_count": len(order),
        "B_new_exact_concepts": sorted(b - a),
        "B_new_semantic_directions": sorted(b - a - related_by_parent(b, a, parents)),
        "B_new_related_dependent_concepts": sorted((b - a) & related_by_parent(b, a, parents)),
        "B_repeated_exact_concepts": sorted(b & a),
        "target_before_A_closure_count": len(original),
        "target_removed_A_closure_count": len(original) - len(target),
        "target_related_parent_overlap_count": len(related_by_parent(target, a, parents)),
        "evaluation_identifiable": bool(target),
    }


def available_evidence(episode, slot):
    """Visibility has no dependency on reference T or fitted predictions."""
    if slot not in {"Q0", "Q1", "Q2", "Q3", "Q4"}:
        raise ValueError("UNREGISTERED_QUESTION_SLOT")
    return sorted(set(episode["A"]) | (set(episode["B"]) if slot in {"Q2", "Q3", "Q4"} else set()))


def _read_tsv(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def input_paths(owner):
    owner = Path(owner)
    prior = owner.parent / "backend-model-20260905"
    return {
        "workbook": prior / "sources/zenodo-panelists.xlsx",
        "metadata": prior / "sources/zenodo-metadata.json",
        "original_records": prior / "records.json",
        "recovery_records": owner / "recovery_records.json",
        "source_ledger": ROOT / "db/data/current/CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv",
        "atom_ledger": ROOT / "db/data/current/CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv",
        "original_broad_parser": ROOT / "db/scripts/prepare_sequential_data.py",
        "registered_parents": ROOT / "db/scripts/flavor_m2_r1.py",
        "readme": owner / "revisions/r4/sources/zenodo_20840464_readme.md",
    }


def restore_reports(owner):
    """Reconstruct the frozen D0 panel sets with row-level identity proofs."""
    import openpyxl
    paths = input_paths(owner)
    if sha(paths["workbook"]) != SOURCE_SHA:
        raise ValueError("SOURCE_WORKBOOK_HASH_CHANGED")
    meta = json.loads(paths["metadata"].read_text())["metadata"]
    if meta["license"]["id"] != "cc-by-4.0" or "Non-commercial research only" not in meta["description"]:
        raise ValueError("SOURCE_RIGHTS_INTERSECTION_CHANGED")
    workbook = openpyxl.load_workbook(paths["workbook"], read_only=True, data_only=True)
    cells = list(workbook["All Panelists"].values)
    raw_rows = {rn: row for rn, row in enumerate(cells, 1) if rn >= 3 and row[0] is not None and row[1]}
    pairs = [(str(row[0]), str(row[1])) for row in raw_rows.values()]
    if len(pairs) != len(set(pairs)):
        raise ValueError("DUPLICATE_SOURCE_SAMPLE_GRADER")
    # Named individual sheets are source mirrors, never additional observations.
    mirrors = Counter(tuple(row) for sheet in workbook if sheet.title != "All Panelists" for row in list(sheet.values)[2:] if row[0] is not None and row[1])
    if mirrors != Counter(tuple(row) for row in raw_rows.values()):
        raise ValueError("INDIVIDUAL_SHEETS_DISAGREE_WITH_ALL_PANELISTS")
    old = json.loads(paths["original_records"].read_text())
    recovery = json.loads(paths["recovery_records"].read_text())
    by_coffee = {r["coffee_id"]: r for r in old}
    old_by_id = {r["record_id"]: r for r in old}
    evidence_to_record = {eid: r for r in old for eid in r["evidence_ids"]}
    ledger = {r["descriptor_assertion_id"]: r for r in _read_tsv(paths["source_ledger"]) if r["source_family_id"] == FAMILY}
    reports = defaultdict(lambda: defaultdict(set))
    trace = defaultdict(lambda: defaultdict(list))
    identities = defaultdict(set)
    sample_ids = defaultdict(set)
    checked = {}
    for aid, source in ledger.items():
        if source["coffee_identity_id"] not in by_coffee:
            continue
        match = re.fullmatch(r"sheet:All Panelists#row=(\d+);column=(\d+)", source["source_locator"])
        if not match:
            raise ValueError("UNRESOLVED_SOURCE_CELL")
        rn, column = map(int, match.groups())
        row = raw_rows[rn]
        value = row[column - 1]
        if hashlib.sha256(str(value).encode()).hexdigest() != source["raw_field_text_sha256"]:
            raise ValueError("GOVERNED_SOURCE_CELL_HASH_MISMATCH")
        grader = source["judge_observation_id_sha256"]
        if not grader or source["publication_layer"] != "JUDGE_LEVEL_OBSERVATION":
            raise ValueError("INDIVIDUAL_GRADER_IDENTITY_REQUIRED")
        identities[grader].add(str(row[1]))
        sample_ids[source["effective_record_id"]].add(str(row[0]))
        checked[aid] = {"source_row": rn, "source_column": column, "source_sample_id": str(row[0]),
                        "grader_hash": grader, "raw_field_sha256": source["raw_field_text_sha256"],
                        "source_field": cells[1][column - 1]}
    if any(len(names) != 1 for names in identities.values()) or len({next(iter(v)) for v in identities.values()}) != len(identities):
        raise ValueError("GRADER_HASH_IDENTITY_NOT_ONE_TO_ONE")
    if any(len(ids) != 1 for ids in sample_ids.values()):
        raise ValueError("EFFECTIVE_RECORD_CROSSES_SOURCE_SAMPLE_IDS")
    for atom in _read_tsv(paths["atom_ledger"]):
        old_record = evidence_to_record.get(atom["cleaned_output_atom_id"])
        if old_record is None:
            continue
        proof = checked[atom["descriptor_assertion_id"]]
        if proof["grader_hash"] != atom["judge_observation_id_sha256"]:
            raise ValueError("ATOM_GRADER_IDENTITY_MISMATCH")
        concept = atom["canonical_concept_id"]
        reports[old_record["coffee_id"]][proof["grader_hash"]].add(concept)
        trace[old_record["record_id"]][proof["grader_hash"]].append({**proof, "concept": concept, "evidence_id": atom["cleaned_output_atom_id"], "mapping": atom["mapping_state"]})
    # Reproduce only the original explicit broad-fragment rule, never infer a leaf.
    for aid, proof in checked.items():
        source = ledger[aid]
        raw = str(cells[proof["source_row"] - 1][proof["source_column"] - 1] or "")
        for part in re.split(r"[,;\n]", raw):
            concept = BROAD_WORDS.get(part.strip().lower().strip(". "))
            if concept:
                record = by_coffee[source["coffee_identity_id"]]
                reports[record["coffee_id"]][proof["grader_hash"]].add(concept)
                trace[record["record_id"]][proof["grader_hash"]].append({**proof, "concept": concept, "evidence_id": aid + ":EXPLICIT_BROAD", "mapping": "ORIGINAL_EXPLICIT_BROAD_FRAGMENT"})
    restored, candidates, historical = {}, [], []
    for record in recovery:
        if record["source_family"] != "zenodo":
            continue
        values = reports[old_by_id[record["record_id"]]["coffee_id"]]
        if sorted(sorted(v) for v in values.values()) != sorted(record["panelist_mention_sets"]):
            raise ValueError("RESTORED_REPORTS_DIFFER_FROM_FROZEN_D0")
        restored[record["record_id"]] = values
        if len(values) >= 3:
            (candidates if record["split"] == "DEVELOPMENT" else historical).append(record)
    episodes = [episode_from_reports(r, restored[r["record_id"]]) for r in sorted(candidates, key=lambda r: r["record_id"])]
    detailed = {r["record_id"]: {"group_id": r["group_id"], "ordered_graders": ordered_graders(restored[r["record_id"]]), "source_evidence": trace[r["record_id"]]} for r in candidates}
    audit = {
        "raw_source_sample_ids": len({pair[0] for pair in pairs}), "raw_source_grader_rows": len(raw_rows),
        "global_named_graders": len(identities), "duplicate_sample_grader_rows": 0,
        "individual_sheet_mirrors_verified": True, "individual_sheet_new_observations": 0,
        "recovered_D0_records_exactly_verified": len(restored),
        "old_historical_connected_records_not_evaluated": len(historical),
        "old_historical_connected_groups_not_evaluated": len({r["group_id"] for r in historical}),
        "eligible_records": len(episodes), "eligible_coffee_dependency_groups": len({r["group_id"] for r in episodes}),
        "nonempty_T_records": sum(bool(r["relevance"]) for r in episodes),
        "nonempty_T_coffee_groups": len({r["group_id"] for r in episodes if r["relevance"]}),
        "empty_T_records_retained": sum(not r["relevance"] for r in episodes),
        "B_with_new_exact_concepts_records": sum(bool(r["B_new_exact_concepts"]) for r in episodes),
        "B_with_new_semantic_directions_records": sum(bool(r["B_new_semantic_directions"]) for r in episodes),
        "B_exact_reuse_only_records": sum(not r["B_new_exact_concepts"] for r in episodes),
        "T_total_distinct_record_concepts": sum(len(r["relevance"]) for r in episodes),
        "T_total_removed_A_closure_concepts": sum(r["target_removed_A_closure_count"] for r in episodes),
        "T_related_parent_overlap_concepts_retained": sum(r["target_related_parent_overlap_count"] for r in episodes),
        "all_source_missing_or_unmentioned_labels": "UNKNOWN_NOT_NEGATIVE",
        "rights": {"attribution": meta["creators"], "title": meta["title"], "source_url": protocol()["source"], "machine_license": "CC-BY-4.0", "author_usage_notice": "CC-BY-NC-4.0; Non-commercial research only", "reuse_scope": "LOCAL_NONCOMMERCIAL_RESEARCH_NO_RAW_OR_WEIGHT_REDISTRIBUTION", "modification": "Governed exact/alias/morphological mentions plus original explicit broad fragments; source-row identity restoration; fixed cross-grader partition; target-only A-family masking"},
    }
    if (audit["eligible_records"], audit["eligible_coffee_dependency_groups"]) != (61, 59):
        raise ValueError("PREDECLARED_ADMISSION_COUNTS_CHANGED")
    return episodes, detailed, audit


def _save_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    path.chmod(0o600)


def load_episodes(owner):
    private = Path(owner) / "revisions/r4"
    contract = json.loads((private / "auxiliary_contract.frozen.json").read_text())
    if contract["protocol"] != protocol() or contract["adapter_sha256"] != sha(__file__):
        raise ValueError("FROZEN_AUXILIARY_PROTOCOL_OR_ADAPTER_CHANGED")
    for key, path in input_paths(owner).items():
        if contract["input_sha256"][key] != sha(path):
            raise ValueError("FROZEN_AUXILIARY_INPUT_CHANGED:" + key)
    for name, expected in contract["artifact_sha256"].items():
        if sha(private / name) != expected:
            raise ValueError("FROZEN_AUXILIARY_ARTIFACT_CHANGED:" + name)
    return json.loads((private / "cross_grader_episodes.private.json").read_text())


def run(owner):
    """Freeze the data-only contract before caller may fit the single auxiliary."""
    private = Path(owner) / "revisions/r4"
    if (private / "auxiliary_contract.frozen.json").exists():
        load_episodes(owner)
        return json.loads((private / "data_connections_summary.private.json").read_text())
    episodes, detail, summary = restore_reports(owner)
    summary = {"version": VERSION, "status": "SOURCE_CONNECTION_IMPLEMENTED_NO_FIT_OR_EVALUATION", "scope": protocol()["interpretation"], "connection": summary, "new_sources": 0,
               "private_artifacts": ["revisions/r4/cross_grader_episodes.private.json", "revisions/r4/data_connections_trace.private.json"]}
    artifacts = {"cross_grader_episodes.private.json": episodes, "data_connections_trace.private.json": detail, "data_connections_summary.private.json": summary}
    for name, value in artifacts.items():
        _save_new(private / name, value)
    contract = {"frozen_at_utc": datetime.now(timezone.utc).isoformat(), "first_use": "SOURCE_CONNECTION_FREEZE_BEFORE_ANY_R4_AUXILIARY_FIT_OR_EVALUATION", "protocol": protocol(), "protocol_sha256": digest(protocol()), "adapter_sha256": sha(__file__), "input_sha256": {key: sha(path) for key, path in input_paths(owner).items()}, "artifact_sha256": {name: sha(private / name) for name in artifacts}, "episode_payload_sha256": digest(episodes)}
    _save_new(private / "auxiliary_contract.frozen.json", contract)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.owner_dir), ensure_ascii=False, sort_keys=True, indent=2))
