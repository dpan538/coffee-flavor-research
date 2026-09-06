"""R5 Zenodo observation-unit conversion audit, without model fitting.

All source rows and text remain private. Existing D0 and R1 lexical mappings
are reported separately; this module neither adds terms nor revises old data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import itertools
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

import acquire_m2_r1 as legacy
import data_connections_r4 as r4
from prepare_sequential_data import BROAD_WORDS

VERSION = "m2-r5.zenodo-observation-supervision-audit.v1"
ROOT = Path(__file__).resolve().parents[2]
DESCRIPTION_COLUMNS = {4: "aroma", 6: "bouquet", 8: "aftertaste", 10: "acidity_description", 13: "sweetness_description", 16: "bitterness_description", 19: "body_description"}
ORDINAL_COLUMNS = {11: "native.acidity_intensity", 14: "taste.sweetness", 17: "taste.bitterness"}
QUALITY_COLUMNS = [5, 7, 9, 12, 15, 18, 20]


def proposal():
    """Data proposal only; root owns the task/model freeze."""
    return {
        "version": VERSION,
        "observation_unit": "One actual source sample x named grader row, all seven descriptions and scores attached to that row; fields do not become independent people",
        "roles": "Fixed existing global grader-hash order, first actual grader row=A, second=B, all remaining=T; do not drop a grader because lexical mapping is empty; no role rotation",
        "A_B_T_independence": "Disjoint original grader-row IDs; shared coffee/session and repeated global graders remain dependent; blinding unverified; CROSS_GRADER_CORROBORATION",
        "full_reference": "All positive fine concepts from T rows, including concepts also expressed in A or B; T-grader mention frequency; no target grader inside input consensus",
        "unexpressed_reference": "Separate fixed subset of full T excluding only A exact fine concepts; do not delete siblings, do not update the subset as questions reveal B",
        "numeric_reference": "Three existing source-native ordinal intensity fields, ranks0..4; report reference grader distributions/masks, no interval-average target unless separately registered; zero means low, not absence",
        "quality": "Seven source quality score columns remain excluded from sensory-intensity supervision",
        "grouping": "Original sample IDs join actual grader rows; normalized coffee names reuse exact old D0 group; same-name samples remain one group; anonymous samples are unresolved possible prior overlap and not independent new coffees",
        "historical": "All 526 rows were parsed or inspected in R1; old17 and prior R4 rows are historical development, never fresh confirmation",
        "new_confirmations": 0,
        "new_traceable_coffee_groups": 0,
        "maximum_disjoint_three_grader_cohort": {"sample_records": 95, "coffee_name_dependency_groups": 93, "primary_old_DEV_records": 79, "primary_old_DEV_groups": 77, "historical_records_separate_not_training": 16, "historical_groups": 16},
        "mapping_choice": "STRICT_D0_GOVERNED_PLUS_ORIGINAL_EXPLICIT_BROAD",
        "alternate_mapping_role": "FROZEN_R1_EXACT_LEXICAL_PARSER audit comparison only, not selected for training or evaluation",
        "mapping_guard": "No new exact term, compound split, parent-child equivalence, source-label reclassification or target-based mapping choice",
        "context": "Missing production C0/C1 masks context effects only, not sensory-task eligibility; source roast/grind literals retained privately, never fabricated production C1",
        "formal_examples": "build_examples requires root's frozen JSON to embed proposal() exactly and specify mapping_choice before data become a training input",
    }


def _read_tsv(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def diagnostic_unmapped_reason(term):
    """Loss diagnostics only, never a new semantic mapper."""
    if re.search(r"\b(no|not|without|none|lack|lacks)\b", term):
        return "NEGATION_OR_ABSENCE_SCOPE_NOT_POSITIVE_EXACT"
    if re.search(r"[/+&]", term):
        return "JOINED_OR_ALTERNATIVE_FORM_NOT_SPLIT"
    if re.search(r"[а-яё]", term, re.I):
        return "NON_ENGLISH_FORM_OUTSIDE_FROZEN_LEXICON"
    if term in {"low", "middle", "high", "medium", "short", "long", "strong", "weak", "above average", "below average", "above middle", "below middle"}:
        return "INTENSITY_DURATION_OR_QUALITY_WORD_NOT_FINE_DESCRIPTOR"
    if " " in term:
        return "MODIFIED_COMPOSITE_OR_OTHER_MULTIWORD_UNMAPPED"
    return "OTHER_UNMAPPED_SINGLE_FORM"


def _source_paths(owner):
    owner = Path(owner)
    return {
        **r4.input_paths(owner),
        "r1_observations": owner / "revisions/r1/zenodo_attribute_observations.private.json",
        "r4_connection_summary": owner / "revisions/r4/data_connections_summary.private.json",
        "r4_auxiliary_episodes": owner / "revisions/r4/cross_grader_episodes.private.json",
        "r1_lexical_parser": Path(legacy.__file__),
    }


def parse_source(owner):
    paths = _source_paths(owner)
    if r4.sha(paths["workbook"]) != r4.SOURCE_SHA:
        raise ValueError("ORIGINAL_ZENODO_SOURCE_CHANGED")
    metadata = json.loads(paths["metadata"].read_text())["metadata"]
    if metadata["license"]["id"] != "cc-by-4.0" or "Non-commercial research only" not in metadata["description"]:
        raise ValueError("NONCOMMERCIAL_RIGHTS_INTERSECTION_NOT_VERIFIED")
    workbook = openpyxl.load_workbook(paths["workbook"], read_only=True, data_only=True)
    cells = list(workbook["All Panelists"].values)
    raw = {rn: row for rn, row in enumerate(cells, 1) if rn >= 3 and row[0] is not None and row[1]}
    keys = [(str(row[0]), str(row[1])) for row in raw.values()]
    if len(keys) != len(set(keys)):
        raise ValueError("DUPLICATE_SAMPLE_GRADER_UNIT")
    mirror = Counter(tuple(row) for sheet in workbook if sheet.title != "All Panelists" for row in list(sheet.values)[2:] if row[0] is not None and row[1])
    if mirror != Counter(tuple(row) for row in raw.values()):
        raise ValueError("SOURCE_PANELIST_SHEET_MIRROR_MISMATCH")
    original = json.loads(paths["original_records"].read_text())
    recovery = json.loads(paths["recovery_records"].read_text())
    original_by_id = {r["record_id"]: r for r in original}
    recovery_by_id = {r["record_id"]: r for r in recovery if r["source_family"] == "zenodo"}
    accepted_atoms = {eid for record in original for eid in record["evidence_ids"]}
    ledger = {r["descriptor_assertion_id"]: r for r in _read_tsv(paths["source_ledger"]) if r["source_family_id"] == r4.FAMILY}
    proofs, sample_old, grader_hashes = {}, {}, {}
    d0_concepts, d0_evidence = defaultdict(set), defaultdict(list)
    for identity, row in ledger.items():
        rn, column = map(int, re.fullmatch(r"sheet:All Panelists#row=(\d+);column=(\d+)", row["source_locator"]).groups())
        source = raw[rn]
        value = source[column - 1]
        if hashlib.sha256(str(value).encode()).hexdigest() != row["raw_field_text_sha256"]:
            raise ValueError("GOVERNED_SOURCE_CELL_NO_LONGER_MATCHES")
        if row["publication_layer"] != "JUDGE_LEVEL_OBSERVATION" or not row["judge_observation_id_sha256"]:
            raise ValueError("ACTUAL_GRADER_UNIT_REQUIRED")
        sample = str(source[0])
        old_record = original_by_id[row["effective_record_id"]]
        if sample in sample_old and sample_old[sample] != old_record["record_id"]:
            raise ValueError("SOURCE_SAMPLE_ID_AMBIGUOUS_OLD_JOIN")
        sample_old[sample] = old_record["record_id"]
        name = str(source[1])
        if name in grader_hashes and grader_hashes[name] != row["judge_observation_id_sha256"]:
            raise ValueError("GLOBAL_GRADER_IDENTITY_CONFLICT")
        grader_hashes[name] = row["judge_observation_id_sha256"]
        proofs[identity] = {"source_row": rn, "source_column": column, "raw_text_sha256": row["raw_field_text_sha256"]}
        for phrase in re.split(r"[,;\n]", str(value or "")):
            target = BROAD_WORDS.get(phrase.strip().lower().strip(". "))
            if target:
                d0_concepts[rn].add(target)
                d0_evidence[rn].append({**proofs[identity], "concept": target, "mapping": "ORIGINAL_D0_EXPLICIT_BROAD_FRAGMENT"})
    for row in _read_tsv(paths["atom_ledger"]):
        if row["cleaned_output_atom_id"] not in accepted_atoms:
            continue
        proof = proofs[row["descriptor_assertion_id"]]
        d0_concepts[proof["source_row"]].add(row["canonical_concept_id"])
        d0_evidence[proof["source_row"]].append({**proof, "concept": row["canonical_concept_id"], "mapping": row["mapping_state"], "evidence_id": row["cleaned_output_atom_id"]})
    if len(grader_hashes) != 4 or len(set(grader_hashes.values())) != 4:
        raise ValueError("FOUR_EXISTING_GRADERS_REQUIRED")
    prior_r1 = {r["record_id"]: r for r in json.loads(paths["r1_observations"].read_text())}
    mapping = legacy.fixed_terms()
    observations, samples, by_sample = [], [], defaultdict(list)
    mapping_loss = Counter()
    for rn, row in sorted(raw.items()):
        sample = str(row[0])
        old_id = sample_old.get(sample)
        known = original_by_id.get(old_id)
        group = known["group_id"] if known else "zenodo:UNRESOLVED_ANONYMOUS_LOTS"
        lexical, fields = set(), {}
        for col, field in DESCRIPTION_COLUMNS.items():
            mapped, unmatched = legacy.parse_terms(row[col])
            lexical.update(mapped)
            fragments = [legacy.normalize(p) for p in re.split(r"[,;\n.]", str(row[col] or "")) if legacy.normalize(p)]
            decisions = []
            for phrase in fragments:
                reason = "FROZEN_EXACT_LEXICAL_MAPPING" if phrase in mapping else diagnostic_unmapped_reason(phrase)
                mapping_loss[reason] += 1
                decisions.append({"original_normalized_phrase": phrase, "concept": mapping.get(phrase), "reason": reason})
            fields[field] = {"source_column": col + 1, "source_text": row[col], "readable": isinstance(row[col], str) and bool(row[col].strip()), "mapped_concepts": mapped, "unmapped_phrases": unmatched, "mapping_decisions": decisions}
        measurements = {name: legacy.ordinal(row[col], name) for col, name in ORDINAL_COLUMNS.items()}
        previous = prior_r1["zenodo:r1:panel-row:" + str(rn)]
        if sorted(lexical) != previous["targets"] or any(measurements[k]["value"] != previous["attribute_measurements"][k]["value"] or measurements[k]["status"] != previous["attribute_measurements"][k]["status"] for k in measurements):
            raise ValueError("FROZEN_R1_MAPPING_OR_ORDINAL_RESULT_CHANGED")
        unit = {"observation_unit_id": "zenodo:20840464:All Panelists:row:" + str(rn), "source_row": rn,
                "sample_id": sample, "group_id": group, "grader_hash": grader_hashes[str(row[1])],
                "source_coffee_name": row[2], "source_roast_grind_literal": row[3],
                "old_record_id": old_id, "old_split": recovery_by_id[old_id]["split"] if old_id else "QUARANTINED_UNKNOWN_LOT_OVERLAP",
                "history_status": "PREVIOUSLY_PARSED_R1_HISTORICAL_DEVELOPMENT_NOT_FRESH_CONFIRMATION",
                "strict_D0_concepts": sorted(d0_concepts[rn]), "strict_D0_evidence": d0_evidence[rn],
                "legacy_R1_fixed_lexical_concepts": sorted(lexical), "description_fields": fields,
                "ordinal_intensity_measurements": measurements, "ordinal_intensity_masks": {k: v["value"] is not None for k, v in measurements.items()},
                "quality_columns_excluded": [c + 1 for c in QUALITY_COLUMNS], "source_C0": None, "source_C1": None,
                "context_effect_mask": False, "observation_role": "SOURCE_PARSE_ONLY_NOT_YET_TRAINING_INPUT"}
        observations.append(unit)
        by_sample[sample].append(unit)
    for sample, units in sorted(by_sample.items(), key=lambda item: int(item[0])):
        names = {legacy.normalize(u["source_coffee_name"]) for u in units if u["source_coffee_name"]}
        if len(names) > 1:
            raise ValueError("SOURCE_SAMPLE_HAS_MULTIPLE_COFFEE_NAMES")
        old_id = sample_old.get(sample)
        if bool(names) != bool(old_id):
            raise ValueError("NAMED_SAMPLE_OLD_D0_JOIN_NOT_COMPLETE")
        if old_id:
            observed = sorted(sorted(u["strict_D0_concepts"]) for u in units if u["strict_D0_concepts"])
            if observed != sorted(recovery_by_id[old_id]["panelist_mention_sets"]):
                raise ValueError("D0_PANEL_MAPPING_RECONSTRUCTION_CHANGED")
        ordered = sorted(units, key=lambda u: hashlib.sha256((r4.ORDER_SEED + "|" + u["grader_hash"]).encode()).hexdigest())
        samples.append({"sample_id": sample, "group_id": units[0]["group_id"], "old_record_id": old_id,
                        "old_split": units[0]["old_split"], "traceable_coffee_name": bool(names),
                        "raw_grader_rows": len(units), "ordered_observation_unit_ids": [u["observation_unit_id"] for u in ordered],
                        "three_disjoint_observation_roles_possible": len(units) >= 3,
                        "split_disposition": "HISTORICAL_DEVELOPMENT" if old_id else "UNRESOLVED_POSSIBLE_PRIOR_COFFEE_OVERLAP_NOT_NEW_CONFIRMATION"})
    old_aux = json.loads(paths["r4_auxiliary_episodes"].read_text())
    named = [s for s in samples if s["traceable_coffee_name"]]
    eligible = [s for s in named if s["three_disjoint_observation_roles_possible"]]
    old_dev = [s for s in eligible if s["old_split"] == "DEVELOPMENT"]
    numeric_masks = {name: dict(Counter(u["ordinal_intensity_measurements"][name]["status"] for u in observations)) for name in ORDINAL_COLUMNS.values()}
    funnel = {
        "source_sample_ids": len(samples), "raw_grader_observation_rows": len(observations), "source_grader_people": len(grader_hashes),
        "duplicate_sample_grader_rows": 0, "individual_sheet_mirror_rows_not_added": len(observations),
        "named_samples_linked_to_existing_D0": len(named), "named_coffee_dependency_groups": len({s["group_id"] for s in named}),
        "named_observation_rows": sum(s["raw_grader_rows"] for s in named),
        "anonymous_samples": len(samples) - len(named), "anonymous_observation_rows": sum(s["raw_grader_rows"] for s in samples if not s["traceable_coffee_name"]),
        "anonymous_three_grader_samples": sum(s["three_disjoint_observation_roles_possible"] for s in samples if not s["traceable_coffee_name"]),
        "source_rows_per_sample_distribution": dict(sorted(Counter(s["raw_grader_rows"] for s in samples).items())),
        "R5_raw_three_grader_named_samples": len(eligible), "R5_raw_three_grader_coffee_groups": len({s["group_id"] for s in eligible}),
        "R5_old_DEV_three_grader_samples": len(old_dev), "R5_old_DEV_three_grader_groups": len({s["group_id"] for s in old_dev}),
        "R4_eligible_mapped_three_grader_DEV_samples": len(old_aux), "R4_eligible_coffee_groups": len({e["group_id"] for e in old_aux}),
        "R4_identifiable_filtered_T_samples": sum(bool(e["relevance"]) for e in old_aux), "R4_identifiable_filtered_T_groups": len({e["group_id"] for e in old_aux if e["relevance"]}),
        "R4_empty_filtered_T_samples_retained": sum(not e["relevance"] for e in old_aux),
        "recoverable_old_DEV_samples_from_raw_unit_role_assignment": len(old_dev) - len(old_aux),
        "new_independent_traceable_coffee_groups": 0, "fresh_confirmation_groups": 0,
        "ordinal_masks": numeric_masks, "all_three_ordinals_observed_rows": sum(all(u["ordinal_intensity_masks"].values()) for u in observations),
        "mapping_loss_phrase_occurrences": dict(mapping_loss),
        "mapping_difference_rows_D0_vs_R1": sum(u["strict_D0_concepts"] != u["legacy_R1_fixed_lexical_concepts"] for u in observations),
        "mapping_difference_rows_named_D0_vs_R1": sum(u["old_record_id"] is not None and u["strict_D0_concepts"] != u["legacy_R1_fixed_lexical_concepts"] for u in observations),
        "fine_vocabulary_D0": len({c for u in observations for c in u["strict_D0_concepts"] if c.startswith("sensory.")}),
        "fine_vocabulary_R1": len({c for u in observations for c in u["legacy_R1_fixed_lexical_concepts"] if c.startswith("sensory.")}),
        "exclusion_reasons": {
            "196_to_112": "84 anonymous samples have no source coffee name, all lack roast/grind metadata and have only1-2 grader rows; possible overlap with old coffees unresolved; missing C1 itself is not the exclusion criterion",
            "112_to_95_old_DEV": "17 previously viewed historical records held outside the original DEV slice; not lost source observations",
            "95_old_DEV_to_61_R4": "34 failed old requirement of3 nonempty mapped grader sets: 16 actually have fewer than3 source grader rows, 18 have>=3 source rows but fewer than3 mapped reports",
            "61_records_to_59_groups": "Two extra sample IDs are same normalized coffee names and share original D0 group",
            "61_to_50_R4_identifiable": "11 retained cases had no fine T after old reference formation and A-exact exclusion; R5 full independent T will retain legitimate A/T concept overlap",
            "full196_to95_raw_three_grader": "101 samples have fewer than3 actual grader observations; no role splitting or rotating can create a third independent observation",
        },
    }
    return {"version": VERSION, "parse_only": True, "source_sha256": r4.SOURCE_SHA,
            "input_sha256": {k: r4.sha(p) for k, p in paths.items()}, "mapping_snapshot_sha256": r4.digest(mapping),
            "rights": {"source_url": "https://zenodo.org/records/20840464", "machine_license": "CC-BY-4.0", "author_notice": "CC-BY-NC-4.0; Non-commercial research only", "attribution": metadata["creators"], "raw_and_weights_public_release": False},
            "observation_units": observations, "samples": samples, "funnel": funnel}


def build_examples(parsed, frozen_contract):
    """Produce source-defined full reference only after root's task freeze."""
    contract_path = Path(frozen_contract)
    contract = json.loads(contract_path.read_text())
    if contract.get("data_supervision") != proposal() or not contract.get("registered_utc"):
        raise ValueError("ROOT_DATA_SUPERVISION_PROTOCOL_MUST_BE_FROZEN_FIRST")
    if contract.get("source_parse_sha256") != contract_parse_digest(parsed):
        raise ValueError("SOURCE_PARSE_NOT_BOUND_TO_FROZEN_CONTRACT")
    choice = contract.get("mapping_choice")
    columns = {"STRICT_D0_GOVERNED_PLUS_ORIGINAL_EXPLICIT_BROAD": "strict_D0_concepts", "FROZEN_R1_EXACT_LEXICAL_PARSER": "legacy_R1_fixed_lexical_concepts"}
    if choice != proposal()["mapping_choice"]:
        raise ValueError("ONE_EXISTING_MAPPING_MUST_BE_PREDECLARED")
    by_id = {u["observation_unit_id"]: u for u in parsed["observation_units"]}
    if len(by_id) != len(parsed["observation_units"]):
        raise ValueError("SOURCE_OBSERVATION_UNIT_IDS_MUST_BE_UNIQUE")
    examples = []
    for sample in parsed["samples"]:
        if not sample["traceable_coffee_name"] or not sample["three_disjoint_observation_roles_possible"]:
            continue
        ordered = [by_id[i] for i in sample["ordered_observation_unit_ids"]]
        if len(ordered) < 3 or len({u["observation_unit_id"] for u in ordered}) != len(ordered):
            raise ValueError("A_B_T_REQUIRE_DISJOINT_ORIGINAL_OBSERVATION_UNITS")
        a, b, reference = ordered[0], ordered[1], ordered[2:]
        a_terms, b_terms = a[columns[choice]], b[columns[choice]]
        targets = Counter(c for unit in reference for c in set(unit[columns[choice]]) if c.startswith("sensory."))
        numeric = {}
        for k in ORDINAL_COLUMNS.values():
            values = [u["ordinal_intensity_measurements"][k]["value"] for u in reference]
            masks = [u["ordinal_intensity_masks"][k] for u in reference]
            if any((value is not None) != mask or (mask and value not in range(5)) for value, mask in zip(values, masks, strict=True)):
                raise ValueError("SOURCE_ORDINAL_VALUE_AND_MASK_DISAGREE")
            counts = [sum(mask and value == level for value, mask in zip(values, masks, strict=True)) for level in range(5)]
            n = sum(masks)
            numeric[k] = {"values": values, "masks": masks, "target_observation_unit_ids": [u["observation_unit_id"] for u in reference],
                          "category_counts": counts, "observed_reference_graders": n,
                          "distribution": [count / n for count in counts] if n else None,
                          "cumulative_thresholds": [0, 1, 2, 3], "cumulative_probabilities": [sum(counts[:i+1]) / n for i in range(4)] if n else None,
                          "interpretation": "Empirical independently held grader ordinal response distribution; not population probability, psychological distance, interval mean or production question input"}
        examples.append({"record_id": sample["old_record_id"], "sample_id": sample["sample_id"], "group_id": sample["group_id"], "source_family": "zenodo",
                         "A": a_terms, "B": b_terms, "relevance_full": dict(sorted(targets.items())), "relevance_unexpressed": {k: v for k, v in sorted(targets.items()) if k not in set(a_terms)},
                         "A_observation_unit_id": a["observation_unit_id"], "B_observation_unit_id": b["observation_unit_id"], "T_observation_unit_ids": [u["observation_unit_id"] for u in reference],
                         "A_ordinal_measurements": a["ordinal_intensity_measurements"], "B_ordinal_measurements": b["ordinal_intensity_measurements"], "T_ordinal": numeric,
                         "old_split": sample["old_split"], "split_disposition": "HISTORICAL_DEVELOPMENT", "mapping_choice": choice,
                         "information_origin": "CROSS_GRADER_CORROBORATION", "rating_blinding": "UNVERIFIED", "source_C0": None, "source_C1": None, "context_effect_mask": False})
    return examples


make_examples = build_examples


def contract_parse_digest(parsed):
    """Root R5 uses r1.digest's ASCII-escaped canonical JSON, unlike R4 UTF-8."""
    return hashlib.sha256(json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def reference_agreement(parsed):
    """Describe actual within-sample cross-grader differences, never a ceiling."""
    import alignment_metrics_r3 as metric

    by_id = {r["observation_unit_id"]: r for r in parsed["observation_units"]}
    rows = []
    for sample in parsed["samples"]:
        if not sample["traceable_coffee_name"]:
            continue
        units = [by_id[i] for i in sample["ordered_observation_unit_ids"]]
        for left, right in itertools.combinations(units, 2):
            lf = {c for c in left["strict_D0_concepts"] if c.startswith("sensory.")}
            rf = {c for c in right["strict_D0_concepts"] if c.startswith("sensory.")}
            # Empty mapped reports are not verified sensory absence.
            denominator = len(lf) + len(rf)
            known = bool(lf) and bool(rf)
            exact = 2 * len(lf & rf) / denominator if known else None
            parent = 2 * metric.maximum_matching(sorted(lf), sorted(rf), min(len(lf), len(rf))) / denominator if known else None
            ordinal = {}
            for name in ORDINAL_COLUMNS.values():
                a = left["ordinal_intensity_measurements"][name]["value"]
                b = right["ordinal_intensity_measurements"][name]["value"]
                mask = a is not None and b is not None
                ordinal[name] = {"both_observed": mask, "left_rank": a, "right_rank": b,
                                 "same_category": float(a == b) if mask else None,
                                 "signed_source_rank_step_difference": a - b if mask else None,
                                 "threshold_disagreement": sum((a <= k) != (b <= k) for k in range(4)) / 4 if mask else None}
            rows.append({"sample_id": sample["sample_id"], "group_id": sample["group_id"], "old_split": sample["old_split"],
                         "left_observation_unit_id": left["observation_unit_id"], "right_observation_unit_id": right["observation_unit_id"],
                         "left_grader_hash": left["grader_hash"], "right_grader_hash": right["grader_hash"],
                         "left_fine": sorted(lf), "right_fine": sorted(rf), "both_mapped_fine_nonempty": known,
                         "symmetric_exact_match_fraction": exact, "symmetric_registered_parent_match_fraction": parent, "ordinal": ordinal})

    def group_macro(values, key):
        by_group_sample = defaultdict(lambda: defaultdict(list))
        for row in values:
            value = row[key]
            if value is not None:
                by_group_sample[row["group_id"]][row["sample_id"]].append(value)
        group_values = [sum(sum(v) / len(v) for v in samples.values()) / len(samples) for samples in by_group_sample.values()]
        return sum(group_values) / len(group_values) if group_values else None

    cohorts = {}
    for split in ["DEVELOPMENT", "HISTORICAL_REGRESSION"]:
        selected = [r for r in rows if r["old_split"] == split]
        full_samples = [s for s in parsed["samples"] if s["traceable_coffee_name"] and s["old_split"] == split]
        numeric = {}
        for field in ORDINAL_COLUMNS.values():
            values = [{"group_id": r["group_id"], "sample_id": r["sample_id"], **r["ordinal"][field]} for r in selected]
            numeric[field] = {"observed_pairs": sum(r["both_observed"] for r in values),
                              "missing_pairs": sum(not r["both_observed"] for r in values),
                              "observed_pair_coffee_groups": len({r["group_id"] for r in values if r["both_observed"]}),
                              "same_category_fraction_coffee_macro": group_macro(values, "same_category"),
                              "ordinal_threshold_disagreement_coffee_macro": group_macro(values, "threshold_disagreement"),
                              "signed_rank_step_difference_histogram": dict(sorted(Counter(r["signed_source_rank_step_difference"] for r in values if r["both_observed"]).items()))}
        cohorts[split] = {"actual_within_sample_cross_grader_pairs": len(selected), "source_samples": len({r["sample_id"] for r in selected}),
                          "coffee_dependency_groups": len({r["group_id"] for r in selected}),
                          "all_named_source_samples": len(full_samples), "all_named_coffee_dependency_groups": len({s["group_id"] for s in full_samples}),
                          "source_samples_without_two_grader_pair": sum(s["raw_grader_rows"] < 2 for s in full_samples),
                          "both_fine_mapped_pairs": sum(r["both_mapped_fine_nonempty"] for r in selected),
                          "both_fine_mapped_source_samples": len({r["sample_id"] for r in selected if r["both_mapped_fine_nonempty"]}),
                          "both_fine_mapped_coffee_groups": len({r["group_id"] for r in selected if r["both_mapped_fine_nonempty"]}),
                          "missing_fine_pair_comparisons": sum(not r["both_mapped_fine_nonempty"] for r in selected),
                          "symmetric_exact_match_coffee_macro": group_macro(selected, "symmetric_exact_match_fraction"),
                          "symmetric_fixed_parent_match_coffee_macro": group_macro(selected, "symmetric_registered_parent_match_fraction"), "ordinal": numeric}
    summary = {"version": VERSION + ".reference-disagreement", "cohorts": cohorts,
               "status": "SOURCE_NATIVE_CROSS_GRADER_VARIABILITY_NOT_MODEL_EVALUATION_OR_ACCURACY_CEILING",
               "descriptor_metric": "Symmetric2*M/(left+right positive fine count); exact equality1, registered same-parent partial0.25; both mapped reports must be nonempty; independent reports may legitimately disagree",
               "ordinal_metric": "Exact ordinal category agreement and average four-threshold disagreement; native rank-step histogram is a code diagnostic, not physical intensity or psychological distance",
               "weighting": "Equal cross-grader pair mean within sample, equal sample mean within coffee-name group, equal group mean; pair counts are not independent coffee trials",
               "method_limits": ["Shared sample and session; same4 graders across coffees; rating blinding unverified", "Differences combine grader expression, sensory response and incomplete governed mapping; no true-negative interpretation", "No repeated sample x grader rows: same-person stability NOT_EVALUATED; individual-sheet mirrors are not repeats", "Old historical17 remain separate, not new confirmation or primary training"],
               "source_parse_sha256": r4.digest(parsed), "pair_trace_owner_relative_path": "revisions/r5/source_reference_disagreement_pairs.private.json"}
    return rows, summary


def run_reference_agreement(owner):
    private = Path(owner) / "revisions/r5"
    parsed = json.loads((private / "zenodo_source_parse.private.json").read_text())
    rows, summary = reference_agreement(parsed)
    for name, value in [("source_reference_disagreement_pairs.private.json", rows), ("source_reference_disagreement_summary.private.json", summary)]:
        path = private / name
        if path.exists():
            if json.loads(path.read_text()) != json.loads(json.dumps(value)):
                raise ValueError("PRESERVE_PRIOR_REFERENCE_DISAGREEMENT_AUDIT")
        else:
            r4._save_new(path, value)
    return summary


def run_inventory(owner):
    private = Path(owner) / "revisions/r5"
    parsed = parse_source(owner)
    summary = {k: v for k, v in parsed.items() if k not in {"observation_units", "samples"}}
    summary.update(source_parse_sha256=r4.digest(parsed), proposal=proposal(), source_parse_owner_relative_path="revisions/r5/zenodo_source_parse.private.json", created_utc=datetime.now(timezone.utc).isoformat())
    for name, value in [("zenodo_source_parse.private.json", parsed), ("zenodo_conversion_funnel.private.json", summary)]:
        path = private / name
        if path.exists():
            old = json.loads(path.read_text())
            if name.endswith("funnel.private.json"):
                value["created_utc"] = old["created_utc"]
            if value != old:
                raise ValueError("PRESERVE_EXISTING_R5_SOURCE_PARSE")
        else:
            r4._save_new(path, value)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run_inventory(args.owner_dir), sort_keys=True, ensure_ascii=False, indent=2))
