#!/usr/bin/env python3
"""Build an explicitly licensed, readable, grouped record-recovery subset."""

from __future__ import annotations
import argparse, csv, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-model-20260905"
ZENODO = "family.zenodo_golovinsky_q_grader_dataset"
EXPECTED = {
    "zenodo-panelists.xlsx": "85df699ea18f5849ef3104100a20570d5df13e7d6cc7ce53e20c3df8a5219150",
    "inera-sensory.xlsx": "4ca2bff21183d2615e244f68b330ba23282f56e6d012c7be762f04baa19abb0a",
}


def sha(x):
    return hashlib.sha256(x).hexdigest()


def read(name):
    return list(
        csv.DictReader((ROOT / "db/data/current" / name).open(), delimiter="\t")
    )


def write(path, x):
    path.write_text(json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def prepare(owner):
    if (owner / "records.json").exists():
        raise RuntimeError(
            "Refusing to overwrite frozen core records; use the recorded core commit in an isolated reproduction directory"
        )
    source = owner / "sources"
    for name, digest in EXPECTED.items():
        assert sha((source / name).read_bytes()) == digest, (
            "Readable artifact identity mismatch: " + name
        )
    meta = json.loads((source / "zenodo-metadata.json").read_text())
    # Depositor description imposes NC despite a broader machine license field.
    # Enforce the restrictive intersection; never infer commercial permission.
    assert meta["metadata"]["license"]["id"] == "cc-by-4.0"
    assert "Non-commercial research only" in meta["metadata"]["description"]
    assert "Attribution Non Commercial 4.0" in meta["metadata"]["description"]
    fm = json.loads((source / "figshare-metadata.json").read_text())
    assert fm["license"]["name"] == "CC BY 4.0"
    assert any(
        f["id"] == 46039437
        and f["computed_md5"]
        == hashlib.md5((source / "inera-sensory.xlsx").read_bytes()).hexdigest()
        for f in fm["files"]
    )
    rights = [
        r
        for r in read("PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv")
        if r["purpose"] == "NONCOMMERCIAL_MODEL_RESEARCH"
    ]
    admitted_right = [r for r in rights if r["source_family_id"] == ZENODO]
    assert (
        len(admitted_right) == 1
        and admitted_right[0]["purpose_rights_status"] == "AFFIRMATIVE_WITH_CONDITIONS"
    )
    wb = openpyxl.load_workbook(
        source / "zenodo-panelists.xlsx", read_only=True, data_only=True
    )
    cells = list(wb["All Panelists"].values)
    ledger = {
        r["descriptor_assertion_id"]: r
        for r in read("CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv")
        if r["source_family_id"] == ZENODO
    }
    checked = {}
    names = defaultdict(set)
    roasts = defaultdict(set)
    for aid, r in ledger.items():
        match = re.fullmatch(
            r"sheet:All Panelists#row=(\d+);column=(\d+)", r["source_locator"]
        )
        assert match
        row = cells[int(match[1]) - 1]
        value = row[int(match[2]) - 1]
        assert (
            sha(str(value).encode()) == r["raw_field_text_sha256"]
        ), "Source cell differs from governed record"
        checked[aid] = r
        names[r["coffee_identity_id"]].add(
            re.sub(r"\s+", " ", str(row[2]).strip().casefold())
        )
        roasts[r["coffee_identity_id"]].add(str(row[3] or "").strip())
    assert all(len(n) == 1 for n in names.values())
    records = {}
    excluded = Counter()
    permitted = {
        "EXISTING_CANONICAL_EXACT",
        "EXISTING_CANONICAL_ALIAS",
        "EXISTING_CANONICAL_MORPHOLOGICAL_VARIANT",
    }
    for atom in read("CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv"):
        if atom["source_family_id"] != ZENODO:
            continue
        if atom["descriptor_assertion_id"] not in checked:
            excluded["UNREADABLE_ASSERTION"] += 1
            continue
        if atom["semantic_class"] != "STRICT_FLAVOR":
            excluded["NOT_STRICT_FLAVOR"] += 1
            continue
        if (
            atom["mapping_state"] not in permitted
            or atom["normalization_authority"] != "MACHINE_GOVERNED_HIGH_CONFIDENCE"
        ):
            excluded["NOT_EXACT_EQUIVALENT_MAPPING"] += 1
            continue
        target = atom["canonical_concept_id"]
        if not target or "|" in target:
            excluded["AMBIGUOUS_TARGET"] += 1
            continue
        # A self-component is identity metadata, not a compound. Exact whole
        # concepts such as dark_chocolate retain their explicit modifier;
        # MODIFIER_OF_EXISTING_CONCEPT rows have already been excluded above.
        components = {x for x in atom["component_concept_ids"].split("|") if x}
        if components - {target}:
            excluded["COMPOUND_NOT_EQUIVALENT"] += 1
            continue
        # Admission follows this artifact's satisfied conditions, never another source's same concept.
        assert atom["source_artifact_id"] == admitted_right[0]["source_artifact_id"]
        assert (
            atom["rights_noncommercial_model_research"] == "AFFIRMATIVE_WITH_CONDITIONS"
        )
        c = atom["coffee_identity_id"]
        rid = atom["effective_record_id"]
        name = next(iter(names[c]))
        group = "coffee-group:" + sha((ZENODO + "|" + name).encode())[:24]
        record = records.setdefault(
            rid,
            dict(
                record_id=rid,
                coffee_id=c,
                group_id=group,
                source_family=ZENODO,
                c0=None,
                c1=None,
                targets=[],
                evidence_ids=[],
                source_roast_status="MISSING_OR_UNMAPPED",
                label_type="INCOMPLETE_POSITIVE_DESCRIPTORS",
            ),
        )
        record["targets"].append(target)
        record["evidence_ids"].append(atom["cleaned_output_atom_id"])
    literal = {}
    for r in records.values():
        r["targets"] = sorted(set(r["targets"]))
        r["evidence_ids"] = sorted(set(r["evidence_ids"]))
        values = roasts[r["coffee_id"]]
        r["source_roast_terms"] = sorted(values)
        r["source_roast_status"] = (
            "SOURCE_NATIVE_TERMS_RETAINED_NO_AUTOMATIC_PRODUCT_C1_MAPPING"
        )
    records = sorted(records.values(), key=lambda r: r["record_id"])
    # Split by source identities BEFORE vocabulary counts, graph estimation, episodes or fitting.
    groups = sorted(
        {r["group_id"] for r in records},
        key=lambda g: sha(("20260905|split|" + g).encode()),
    )
    a = int(0.70 * len(groups))
    b = int(0.85 * len(groups))
    split = {
        g: ("TRAIN" if i < a else "DEV" if i < b else "TEST")
        for i, g in enumerate(groups)
    }
    for r in records:
        r["split"] = split[r["group_id"]]
    iw = openpyxl.load_workbook(
        source / "inera-sensory.xlsx", read_only=True, data_only=True
    )
    ir = list(iw["Sensory_scores"].values)[1:]
    full = sum(all(isinstance(x, (int, float)) for x in r[20:29]) for r in ir)
    source_rights = Counter(
        (r["source_family_id"], r["purpose_rights_status"]) for r in rights
    )
    manifest = {
        "experiment_id": "backend-flavor-record-recovery-20260905",
        "task": "RECORD_RECOVERY_PROXY",
        "authorization": "Explicit owner backend-model instruction 2026-09-05; noncommercial local comparative research only; no deployment or weight release",
        "admitted_source": {
            "family": ZENODO,
            "title": meta["metadata"]["title"],
            "creators": [x["name"] for x in meta["metadata"]["creators"]],
            "url": "https://zenodo.org/records/20840464",
            "version": "1.1",
            "license": "CC BY-NC 4.0",
            "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
            "source_sha256": EXPECTED["zenodo-panelists.xlsx"],
            "metadata_sha256": sha((source / "zenodo-metadata.json").read_bytes()),
            "conditions_checked": {
                "attribution_in_manifest": True,
                "noncommercial_local_research_only": True,
                "raw_data_not_redistributed": True,
                "model_weights_not_released": True,
                "changes_disclosed": "Exact/alias/morphological governed descriptors deduplicated within coffee; modifiers/compounds excluded; identity grouping; masked record-recovery episodes",
                "separate_source_permission_propagation": False,
            },
        },
        "source_classes": {
            "complete_structured_frequency_observations": {
                "source": "https://doi.org/10.3389/fsufs.2024.1382976.s002",
                "license": "CC BY 4.0",
                "artifact_sha256": EXPECTED["inera-sensory.xlsx"],
                "record_count": len(ir),
                "complete_nine_attribute_record_count": full,
                "genotype_groups": len({r[0] for r in ir}),
                "explicit_missing_cell_count": sum(
                    x is None for r in ir for x in r[20:29]
                ),
                "disposition": "Available for a source-category head; not recoded to fine sensory labels. Nutty/Cocoa is a combined source category, not independent cocoa or dark chocolate truth.",
            },
            "positive_only_records": {
                "source": ZENODO,
                "readable_source_assertion_count": len(checked),
                "retained_record_count": len(records),
                "retained_unique_descriptor_count": sum(
                    len(r["targets"]) for r in records
                ),
            },
            "complete_c0_c1_records": {
                "count": 0,
                "reason": "No reviewed source C0 family in this subset; source C1 literal matches are partial only",
            },
            "incomplete_context_auxiliary_records": {
                "count": len(records),
                "c0_present": 0,
                "literal_c1_present": sum(r["c1"] is not None for r in records),
                "use": "Context-independent answer/descriptor recovery; missing source context is masked, never a production input branch",
            },
        },
        "source_exclusions": [
            {
                "family": f,
                "rights_state": s,
                "artifact_count": n,
                "reason": "No affirmative model-use permission with satisfied conditions",
            }
            for (f, s), n in sorted(source_rights.items())
            if not s.startswith("AFFIRMATIVE")
        ],
        "other_audited_source": {
            "url": "https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2026.1809471/full",
            "record_count": 21,
            "disposition": "Coded panel-consensus observations retained as source evidence; not pooled into this first source-specific experiment or used as fabricated complete negatives",
        },
        "filter_exclusions": dict(excluded),
        "independent_group_count": len(groups),
        "split_counts": dict(Counter(r["split"] for r in records)),
        "split_group_counts": dict(Counter(split.values())),
        "split_membership": [
            {
                "record_id": r["record_id"],
                "group_id": r["group_id"],
                "split": r["split"],
            }
            for r in records
        ],
        "split_seed": 20260905,
        "group_policy": "Same sample ID, all panelists and exact normalized coffee-name duplicates kept together. Two duplicate-name sample IDs collapse conservatively. No panelist ID is a model feature.",
        "pre_split_statistics_estimated": False,
        "c1_mapping": {
            "mapping": literal,
            "basis": "Literal package/source label equality only; not calibrated seven-bin Agtron mapping; all other roast strings remain source-missing for features",
        },
        "label_limit": "Observed descriptor recovery only; absent words are unlabelled, not sensory negatives. Scores/quality fields and questionnaire answers are not labels.",
        "license_metadata_discrepancy": {
            "machine_field": "CC BY 4.0",
            "depositor_description_and_record_copyright": "CC BY-NC 4.0; noncommercial research only",
            "enforced_scope": "Restrictive intersection: attribution and noncommercial local research; no commercial training, deployment or weight release inferred",
        },
        "lineage_hashes": {
            n: sha((ROOT / "db/data/current" / n).read_bytes())
            for n in [
                "CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv",
                "CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv",
                "PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv",
            ]
        },
    }
    OUT.mkdir(exist_ok=True)
    write(OUT / "dataset_manifest.json", manifest)
    write(owner / "records.json", records)
    (owner / "records.json").chmod(0o600)
    print(
        json.dumps(
            {
                "records": len(records),
                "groups": len(groups),
                "multi_descriptor_records": sum(len(r["targets"]) > 1 for r in records),
                "splits": manifest["split_counts"],
                "literal_c1_records": manifest["source_classes"][
                    "incomplete_context_auxiliary_records"
                ]["literal_c1_present"],
            }
        )
    )
    return records


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--owner-root", type=Path, required=True)
    a = p.parse_args()
    prepare(a.owner_root)
