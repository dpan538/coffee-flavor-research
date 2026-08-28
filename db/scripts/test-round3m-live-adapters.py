#!/usr/bin/env python3
"""Offline semantic and receipt tests for the Round 3M live adapters."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "db" / "adapters"))

from round3k.contract import SOURCE_PROFILES  # noqa: E402
from round3m.generate_public_safe import (  # noqa: E402
    ASSERTION_COLUMNS,
    EFFECTIVE_RECORD_COLUMNS,
    SOURCE_ARTIFACT_COLUMNS,
    generate,
    public_review_candidates,
)
from round3m.live import (  # noqa: E402
    assert_no_inferred_service_or_roast,
    coassertion_events,
    deinflate_assertions,
    effective_record_count,
    extract_candidates,
    independent_source_family_count,
)
from round3m.model import (  # noqa: E402
    AdapterViolation,
    CountDisposition,
    DescriptorClass,
    EffectiveRecordKey,
    EvidenceTier,
    PublicationLayer,
    RightsState,
    SourceField,
    SourceRecord,
)
from round3m.restricted import (  # noqa: E402
    EXPECTED_CAPTURE_MANIFEST_SHA256,
    EXPECTED_CAPTURE_ROOT_LOCATOR,
    load_bounded_captures,
    load_capture_manifest,
)
from round3m.signatures import (  # noqa: E402
    COE_COLOMBIA_FREQUENCY,
    COE_GENERIC_SENSORY,
    COE_HONDURAS_TOP_JURY,
    SIGNATURES,
    WCC_COMPLETED_SCORESHEET,
)


ROUND3M_RESTRICTED_ROOT: Path | None = None
ROUND3L_RESTRICTED_ROOT: Path | None = None
SHA256 = re.compile(r"[0-9a-f]{64}")


def load_review_artifact_builder():
    path = REPO_ROOT / "db" / "scripts" / "build-round3m-review-artifacts.py"
    spec = importlib.util.spec_from_file_location(
        "round3m_review_artifact_builder", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Round 3M review artifact builder: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REVIEW_ARTIFACT_BUILDER = load_review_artifact_builder()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or ()), list(reader)


def make_record(
    signature_id: str,
    fields: tuple[SourceField, ...],
    *,
    entry: str = "lot-1",
    service: str = "service-1",
    rights: RightsState = RightsState.PENDING,
    source_sha: str = "a" * 64,
    judge_filled: bool = False,
    completion_locator: str = "",
    roast_code: str | None = None,
    preparation_code: str | None = None,
) -> SourceRecord:
    signature = SIGNATURES[signature_id]
    return SourceRecord(
        schema_signature_id=signature_id,
        source_artifact_id=f"artifact:{entry}:{service}",
        source_route_id=signature.source_route_id,
        independent_source_family_id=(
            "family.wcc" if signature_id == WCC_COMPLETED_SCORESHEET else "family.coe"
        ),
        source_url="https://example.invalid/governed-fixture",
        source_file_sha256=source_sha,
        source_retrieved_at="2026-08-28T04:30:00Z",
        effective_record=EffectiveRecordKey(
            "series", "edition", "category", "round", entry, service
        ),
        fields=fields,
        rights_state=rights,
        publication_host="example.invalid",
        publication_instance_id=f"publication:{entry}",
        completed_filled_authoritative_scoresheet=judge_filled,
        authoritative_completion_evidence_locator=completion_locator,
        roast_code=roast_code,
        preparation_family_code=preparation_code,
    )


class LiveAdapterSemanticTests(unittest.TestCase):
    def test_honduras_top_jury_is_p2_and_layers_stay_separate(self) -> None:
        record = make_record(
            COE_HONDURAS_TOP_JURY,
            (
                SourceField("Score from International Judges", "88.00", "score"),
                SourceField(
                    "Top Jury Descriptions",
                    "Aroma / Flavor: cedar, peach Acidity: crisp Other Features: silky",
                    "primary",
                ),
                SourceField("Aroma / Flavor", "cedar, cocoa", "secondary"),
                SourceField("Producer cup profile", "fig, body", "producer"),
            ),
        )
        candidates = extract_candidates(record)
        self.assertEqual(public_review_candidates(record), candidates)
        primary = [
            item
            for item in candidates
            if item.publication_layer == PublicationLayer.PRIMARY_JURY_DESCRIPTION
        ]
        secondary = [
            item
            for item in candidates
            if item.publication_layer == PublicationLayer.SECONDARY_SENSORY_TABLE
        ]
        producer = [
            item
            for item in candidates
            if item.publication_layer == PublicationLayer.PRODUCER_OR_FARM_PROFILE
        ]
        self.assertEqual(len(primary), 4)
        self.assertTrue(all(item.evidence_tier == EvidenceTier.P2 for item in primary))
        self.assertTrue(
            all(item.count_disposition == CountDisposition.SECONDARY_REVIEW_ONLY for item in secondary)
        )
        self.assertEqual(len(secondary), 2)
        self.assertTrue(all(item.evidence_tier == EvidenceTier.P3 for item in producer))
        self.assertEqual(len(deinflate_assertions(candidates).assertion_level), 6)
        self.assertTrue(all(not item.model_eligible for item in candidates))

    def test_secondary_layer_stays_review_only_through_review_artifact_build(self) -> None:
        live_path = (
            REPO_ROOT
            / "db"
            / "adapters"
            / "round3m"
            / "generated"
            / "PUBLIC_SAFE_LIVE_ASSERTIONS.tsv"
        )
        columns, committed_rows = read_tsv(live_path)
        template = committed_rows[0]
        shared_hash = template["atomic_source_text_sha256"]
        primary = {
            **template,
            "descriptor_assertion_id": "round3m.synthetic.zzz-primary",
            "publication_layer": "PRIMARY_JURY_DESCRIPTION",
            "source_selector_or_locator": "synthetic:#primary",
            "source_page_or_record_locator": "synthetic:record#primary",
            "atomic_source_text_sha256": shared_hash,
            "count_disposition": "ADMITTED",
            "within_record_repeat_group": "",
            "cross_observation_repeat_group": "",
        }
        secondary = {
            **template,
            "descriptor_assertion_id": "round3m.synthetic.aaa-secondary",
            "publication_layer": "SECONDARY_SENSORY_TABLE",
            "source_selector_or_locator": "synthetic:#secondary",
            "source_page_or_record_locator": "synthetic:record#secondary",
            "atomic_source_text_sha256": shared_hash,
            "count_disposition": "SECONDARY_REVIEW_ONLY",
            "within_record_repeat_group": "",
            "cross_observation_repeat_group": "",
        }

        converted = REVIEW_ARTIFACT_BUILDER.build_live_rows((secondary, primary))
        duplicate_by_id = {
            row["descriptor_assertion_id"]: row for row in converted["duplicates"]
        }
        self.assertEqual(
            duplicate_by_id[primary["descriptor_assertion_id"]][
                "deduplication_disposition"
            ],
            "CANONICAL",
        )
        self.assertEqual(
            duplicate_by_id[primary["descriptor_assertion_id"]][
                "counts_as_record_unique_descriptor"
            ],
            "true",
        )
        self.assertEqual(
            duplicate_by_id[secondary["descriptor_assertion_id"]][
                "deduplication_disposition"
            ],
            "UNRESOLVED",
        )
        self.assertEqual(
            duplicate_by_id[secondary["descriptor_assertion_id"]][
                "counts_as_assertion"
            ],
            "false",
        )
        publication_by_id = {
            row["descriptor_assertion_id"]: row
            for row in converted["publication_layers"]
        }
        self.assertEqual(
            publication_by_id[secondary["descriptor_assertion_id"]]["relation_type"],
            "SECONDARY_REVIEW_ONLY",
        )

        mismatched = {**secondary, "count_disposition": "ADMITTED"}
        with tempfile.TemporaryDirectory(
            prefix="round3m-secondary-contract-"
        ) as temporary:
            mismatch_path = Path(temporary) / "live.tsv"
            with mismatch_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=columns,
                    delimiter="\t",
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerow(mismatched)
            with self.assertRaisesRegex(
                REVIEW_ARTIFACT_BUILDER.ContractError,
                "secondary publication layer and review-only disposition must match",
            ):
                REVIEW_ARTIFACT_BUILDER.read_live_assertions(mismatch_path)

    def test_honduras_requires_score_pairing_for_p2(self) -> None:
        record = make_record(
            COE_HONDURAS_TOP_JURY,
            (SourceField("Top Jury Descriptions", "Aroma / Flavor: cedar", "jury"),),
        )
        self.assertEqual(extract_candidates(record), ())

    def test_frequency_is_one_candidate_per_term_not_per_frequency(self) -> None:
        record = make_record(
            COE_COLOMBIA_FREQUENCY,
            (
                SourceField(
                    "Aroma/Flavor",
                    "Aroma: cedar (13), peach (8). Flavor: cocoa (6). Mouthfeel: silky (11)",
                    "coded",
                ),
                SourceField("Acidity", "bright (9), crisp (7)", "acidity"),
                SourceField("Score", "87.18", "score"),
            ),
            rights=RightsState.UNKNOWN,
        )
        candidates = extract_candidates(record)
        self.assertEqual(len(candidates), 6)
        self.assertGreater(sum(item.frequency_value or 0 for item in candidates), 6)
        self.assertTrue(all(item.evidence_tier == EvidenceTier.UNRESOLVED for item in candidates))
        self.assertTrue(
            all("P1_CANDIDATE" in item.evidence_origin_type for item in candidates)
        )
        self.assertTrue(all(not item.judge_observation_id for item in candidates))

    def test_generic_field_unresolved_and_producer_p3_separate(self) -> None:
        record = make_record(
            COE_GENERIC_SENSORY,
            (
                SourceField("Aroma / Flavor", "cedar, peach", "generic"),
                SourceField("Acidity", "bright", "acidity"),
                SourceField("Producer cup profile", "fig, body", "producer"),
                SourceField("Score", "90.00", "score"),
                SourceField("Rank", "1", "rank"),
            ),
            rights=RightsState.UNKNOWN,
        )
        candidates = extract_candidates(record)
        generic = [
            item
            for item in candidates
            if item.publication_layer
            == PublicationLayer.GENERIC_ORGANIZER_SENSORY_FIELD
        ]
        producer = [
            item
            for item in candidates
            if item.publication_layer == PublicationLayer.PRODUCER_OR_FARM_PROFILE
        ]
        self.assertEqual(len(generic), 3)
        self.assertEqual(len(producer), 2)
        self.assertTrue(all(item.evidence_tier == EvidenceTier.UNRESOLVED for item in generic))
        self.assertTrue(all(item.evidence_tier == EvidenceTier.P3 for item in producer))

    def test_ranking_score_and_blank_form_all_yield_zero(self) -> None:
        cases = (
            make_record(
                COE_HONDURAS_TOP_JURY,
                (SourceField("Score from International Judges", "88", "score"),),
            ),
            make_record(
                COE_COLOMBIA_FREQUENCY,
                (SourceField("Rank", "1", "rank"), SourceField("Score", "88", "score")),
            ),
            make_record(
                COE_GENERIC_SENSORY,
                (SourceField("Rank", "1", "rank"), SourceField("Score", "88", "score")),
            ),
            make_record(
                WCC_COMPLETED_SCORESHEET,
                (
                    SourceField("Judge", "", "judge"),
                    SourceField("Competitor Name", "", "competitor"),
                    SourceField("Judge comments", "", "comments"),
                    SourceField("Taste Score", "", "score"),
                ),
            ),
        )
        self.assertTrue(all(extract_candidates(record) == () for record in cases))

    def test_wcc_filled_text_without_authoritative_completion_yields_zero(self) -> None:
        unverified = make_record(
            WCC_COMPLETED_SCORESHEET,
            (SourceField("Judge comments", "cedar, peach", "comments", "judge-1"),),
        )
        self.assertEqual(extract_candidates(unverified), ())
        missing_receipt = make_record(
            WCC_COMPLETED_SCORESHEET,
            (SourceField("Judge comments", "cedar", "comments", "judge-1"),),
            judge_filled=True,
        )
        with self.assertRaisesRegex(AdapterViolation, "MISSING_COMPLETION_EVIDENCE"):
            extract_candidates(missing_receipt)
        structural_contract = make_record(
            WCC_COMPLETED_SCORESHEET,
            (SourceField("Judge comments", "cedar", "comments", "judge-1"),),
            judge_filled=True,
            completion_locator="fixture:authoritative-completion-receipt",
        )
        result = extract_candidates(structural_contract)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].evidence_tier, EvidenceTier.P1)

    def test_repeat_levels_and_effective_record_boundaries(self) -> None:
        repeated = make_record(
            COE_GENERIC_SENSORY,
            (
                SourceField("Other", "body, body", "generic"),
                SourceField("Producer cup profile", "body", "producer"),
            ),
        )
        result = deinflate_assertions(extract_candidates(repeated))
        self.assertEqual(len(result.extracted_candidates), 3)
        self.assertEqual(len(result.assertion_level), 2)
        self.assertEqual(len(result.record_unique), 1)
        self.assertEqual(
            Counter(item.reason for item in result.suppressed),
            Counter(
                {
                    "EXACT_WITHIN_OBSERVATION_REPEAT": 1,
                    "CROSS_OBSERVATION_SAME_EFFECTIVE_RECORD": 1,
                }
            ),
        )

        other_record = make_record(
            COE_GENERIC_SENSORY,
            (SourceField("Other", "body", "generic"),),
            entry="lot-2",
        )
        combined = deinflate_assertions(
            (*extract_candidates(repeated), *extract_candidates(other_record))
        )
        self.assertEqual(len(combined.record_unique), 2)

        repeated_publication = make_record(
            COE_GENERIC_SENSORY,
            (SourceField("Other", "body", "publication-2"),),
        )
        other_service = make_record(
            COE_GENERIC_SENSORY,
            (SourceField("Other", "body", "service-2"),),
            service="service-2",
        )
        self.assertEqual(effective_record_count((repeated, repeated_publication)), 1)
        self.assertEqual(effective_record_count((repeated, other_service)), 2)

    def test_judges_do_not_create_records_and_pairs_do_not_cross_records(self) -> None:
        first = make_record(
            WCC_COMPLETED_SCORESHEET,
            (
                SourceField("Judge comments", "cedar", "j1", "judge-1"),
                SourceField("Judge comments", "peach", "j2", "judge-2"),
            ),
            entry="lot-1",
            judge_filled=True,
            completion_locator="fixture:completion",
        )
        second = make_record(
            WCC_COMPLETED_SCORESHEET,
            (SourceField("Judge comments", "cocoa", "j3", "judge-3"),),
            entry="lot-2",
            judge_filled=True,
            completion_locator="fixture:completion",
        )
        self.assertEqual(effective_record_count((first, second)), 2)
        candidates = (*extract_candidates(first), *extract_candidates(second))
        events = coassertion_events(deinflate_assertions(candidates).record_unique)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].effective_record_id, first.effective_record.effective_record_id)

    def test_no_roast_preparation_or_translation_inference(self) -> None:
        record = make_record(
            COE_GENERIC_SENSORY,
            (SourceField("Aroma / Flavor", "dark roast, espresso, filter", "generic"),),
            rights=RightsState.UNKNOWN,
            roast_code=None,
            preparation_code=None,
        )
        candidates = extract_candidates(record)
        assert_no_inferred_service_or_roast(record, candidates)
        self.assertTrue(all(item.roast_code is None for item in candidates))
        self.assertTrue(all(item.preparation_family_code is None for item in candidates))
        self.assertTrue(
            all(item.source_native_lexical_form == item.atomic_source_text for item in candidates)
        )

    def test_route_schema_and_independent_family_are_not_conflated(self) -> None:
        coe_records = tuple(
            make_record(signature_id, (), entry=f"lot-{index}")
            for index, signature_id in enumerate(
                (COE_HONDURAS_TOP_JURY, COE_COLOMBIA_FREQUENCY, COE_GENERIC_SENSORY),
                start=1,
            )
        )
        self.assertEqual(len({record.source_route_id for record in coe_records}), 3)
        self.assertEqual(independent_source_family_count(coe_records), 1)
        wcc_record = make_record(WCC_COMPLETED_SCORESHEET, (), entry="wcc-entry")
        self.assertEqual(independent_source_family_count((*coe_records, wcc_record)), 2)

        mismatched = SourceRecord(
            **{
                **coe_records[0].__dict__,
                "source_route_id": SIGNATURES[COE_GENERIC_SENSORY].source_route_id,
            }
        )
        with self.assertRaisesRegex(AdapterViolation, "ROUTE_SIGNATURE_MISMATCH"):
            extract_candidates(mismatched)

    def test_pending_unknown_and_even_singular_affirmative_are_not_eligible(self) -> None:
        for state in (RightsState.PENDING, RightsState.UNKNOWN, RightsState.AFFIRMATIVE):
            record = make_record(
                COE_GENERIC_SENSORY,
                (SourceField("Aroma / Flavor", "cedar", "generic"),),
                rights=state,
            )
            self.assertTrue(all(not item.model_eligible for item in extract_candidates(record)))


class LiveFixtureReceiptTests(unittest.TestCase):
    def test_signature_tsv_matches_registry_and_is_directly_importable(self) -> None:
        path = REPO_ROOT / "db" / "data" / "round3m" / "SOURCE_ROUTE_SCHEMA_SIGNATURE.tsv"
        columns, rows = read_tsv(path)
        self.assertEqual(
            columns,
            [
                "schema_signature_id",
                "source_route_id",
                "schema_version",
                "host",
                "route_pattern",
                "edition_or_period",
                "field_labels_json",
                "selectors_json",
                "publication_layer_rules_json",
                "field_origin_assumptions_json",
                "known_ambiguity",
                "positive_fixture_locator",
                "negative_fixture_locator",
                "adapter_version",
                "live_positive_fixture_present",
                "validation_status",
            ],
        )
        self.assertEqual({row["schema_signature_id"] for row in rows}, set(SIGNATURES))
        fixture_document = json.loads(
            (
                REPO_ROOT
                / "db"
                / "adapters"
                / "round3m"
                / "fixtures"
                / "live_fixture_receipts.json"
            ).read_text(encoding="utf-8")
        )
        fixture_locators = {
            "fixture://round3m/" + str(item["fixture_id"])
            for item in fixture_document["fixtures"]
        }
        for row in rows:
            signature = SIGNATURES[row["schema_signature_id"]]
            self.assertEqual(row["source_route_id"], signature.source_route_id)
            self.assertEqual(row["schema_version"], signature.schema_version)
            self.assertGreater(int(row["schema_version"]), 0)
            self.assertEqual(row["host"], signature.host)
            self.assertEqual(row["route_pattern"], signature.route_pattern)
            self.assertEqual(row["edition_or_period"], signature.edition_or_period)
            self.assertEqual(json.loads(row["field_labels_json"]), list(signature.field_labels))
            self.assertEqual(json.loads(row["selectors_json"]), dict(signature.selectors))
            self.assertEqual(
                json.loads(row["publication_layer_rules_json"]),
                dict(signature.publication_layer_rules),
            )
            self.assertEqual(
                json.loads(row["field_origin_assumptions_json"]),
                dict(signature.field_origin_assumptions),
            )
            self.assertEqual(row["known_ambiguity"], signature.known_ambiguity)
            self.assertEqual(
                row["positive_fixture_locator"], signature.positive_fixture_locator
            )
            self.assertEqual(
                row["negative_fixture_locator"], signature.negative_fixture_locator
            )
            self.assertEqual(row["adapter_version"], "round3m.live-adapters.v1")
            self.assertEqual(
                row["live_positive_fixture_present"],
                str(signature.live_positive_fixture_present).lower(),
            )
            self.assertEqual(row["validation_status"], signature.validation_status)
            if signature.positive_fixture_locator:
                self.assertIn(signature.positive_fixture_locator, fixture_locators)
            self.assertIn(signature.negative_fixture_locator, fixture_locators)

    def test_each_adapter_has_real_receipts_and_wcc_exception_is_explicit(self) -> None:
        path = (
            REPO_ROOT
            / "db"
            / "adapters"
            / "round3m"
            / "fixtures"
            / "live_fixture_receipts.json"
        )
        document = json.loads(path.read_text(encoding="utf-8"))
        fixtures = document["fixtures"]
        by_signature: dict[str, list[dict[str, object]]] = {}
        for fixture in fixtures:
            by_signature.setdefault(str(fixture["schema_signature_id"]), []).append(fixture)
            self.assertTrue(str(fixture["source_locator"]).startswith("https://"))
            self.assertRegex(str(fixture["governed_route_snapshot_sha256"]), SHA256)
            self.assertIn("expected_rights_state", fixture)
            self.assertIn("retrieved_at", fixture)
        for signature_id in (
            COE_HONDURAS_TOP_JURY,
            COE_COLOMBIA_FREQUENCY,
            COE_GENERIC_SENSORY,
        ):
            self.assertTrue(
                any("POSITIVE" in str(item["fixture_role"]) for item in by_signature[signature_id])
            )
            self.assertTrue(
                any(item["fixture_role"] == "LIVE_NEGATIVE" for item in by_signature[signature_id])
            )
        wcc = by_signature[WCC_COMPLETED_SCORESHEET]
        self.assertTrue(all(item["fixture_role"] == "LIVE_NEGATIVE" for item in wcc))
        self.assertFalse(SIGNATURES[WCC_COMPLETED_SCORESHEET].live_positive_fixture_present)

    def test_round3l_governed_route_hashes_when_available(self) -> None:
        if ROUND3L_RESTRICTED_ROOT is None:
            self.skipTest("Round 3L restricted root not supplied")
        fixture_path = (
            REPO_ROOT
            / "db"
            / "adapters"
            / "round3m"
            / "fixtures"
            / "live_fixture_receipts.json"
        )
        fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))["fixtures"]
        checked: set[Path] = set()
        for fixture in fixtures:
            locator = str(fixture["governed_route_snapshot_locator"])
            relative = locator.removeprefix("restricted://round3l/")
            path = ROUND3L_RESTRICTED_ROOT / relative
            if path in checked:
                continue
            self.assertTrue(path.is_file(), str(path))
            self.assertEqual(sha256(path), fixture["governed_route_snapshot_sha256"])
            checked.add(path)

    def test_restricted_bounded_captures_and_public_export(self) -> None:
        if ROUND3M_RESTRICTED_ROOT is None:
            self.skipTest("Round 3M restricted root not supplied")
        self.assertFalse(ROUND3M_RESTRICTED_ROOT.is_relative_to(REPO_ROOT))
        manifest = load_capture_manifest(ROUND3M_RESTRICTED_ROOT)
        self.assertEqual(manifest.sha256, EXPECTED_CAPTURE_MANIFEST_SHA256)
        self.assertEqual(manifest.root_locator, EXPECTED_CAPTURE_ROOT_LOCATOR)
        self.assertEqual(len(manifest.artifacts), 4)
        records, receipts = load_bounded_captures(ROUND3M_RESTRICTED_ROOT)
        self.assertEqual(len(records), 8)
        self.assertEqual(len(receipts), 3)
        counts: Counter[str] = Counter()
        classes: Counter[str] = Counter()
        for record in records:
            for item in extract_candidates(record):
                if item.descriptor_class == DescriptorClass.NON_DESCRIPTOR:
                    continue
                counts[item.evidence_tier.value] += 1
                classes[item.descriptor_class.value] += 1
        self.assertEqual(counts, Counter({"P2": 73, "UNRESOLVED": 67}))
        self.assertEqual(classes, Counter({"STRICT_FLAVOR": 86, "BROAD_SENSORY": 54}))

        export = (
            REPO_ROOT
            / "db"
            / "adapters"
            / "round3m"
            / "generated"
            / "PUBLIC_SAFE_LIVE_ASSERTIONS.tsv"
        )
        columns, rows = read_tsv(export)
        self.assertEqual(columns, list(ASSERTION_COLUMNS))
        self.assertEqual(len(rows), 140)
        self.assertNotIn("raw_field_text", columns)
        self.assertNotIn("atomic_source_text", columns)
        self.assertTrue(all(row["model_eligible"] == "false" for row in rows))
        self.assertTrue(all(row["review_state"] == "PROVISIONAL_MACHINE_CLASSIFIED" for row in rows))
        self.assertTrue(all(row["review_actor_type"] == "AUTOMATED_PARSER" for row in rows))
        self.assertEqual(Counter(row["rights_state"] for row in rows), Counter({"PENDING": 73, "UNKNOWN": 67}))
        self.assertEqual(
            Counter(row["evidence_tier"] for row in rows),
            Counter({"P2": 73, "UNRESOLVED": 67}),
        )
        repeat_groups = {row["cross_observation_repeat_group"] for row in rows} - {""}
        within_repeat_groups = {row["within_record_repeat_group"] for row in rows} - {""}
        self.assertEqual(len(repeat_groups), 2)
        self.assertEqual(len(within_repeat_groups), 1)

        artifact_columns, artifacts = read_tsv(
            REPO_ROOT
            / "db"
            / "adapters"
            / "round3m"
            / "generated"
            / "PUBLIC_SAFE_SOURCE_ARTIFACTS.tsv"
        )
        record_columns, effective_records = read_tsv(
            REPO_ROOT
            / "db"
            / "adapters"
            / "round3m"
            / "generated"
            / "PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv"
        )
        self.assertEqual(artifact_columns, list(SOURCE_ARTIFACT_COLUMNS))
        self.assertEqual(record_columns, list(EFFECTIVE_RECORD_COLUMNS))
        self.assertEqual(len(artifacts), 8)
        self.assertEqual(len(effective_records), 8)
        artifacts_by_id = {row["source_artifact_id"]: row for row in artifacts}
        records_by_id = {
            row["round3m_effective_record_id"]: row for row in effective_records
        }
        self.assertEqual(set(artifacts_by_id), {row["source_artifact_id"] for row in rows})
        self.assertEqual(set(records_by_id), {row["effective_record_id"] for row in rows})
        for row in rows:
            artifact = artifacts_by_id[row["source_artifact_id"]]
            bridge = records_by_id[row["effective_record_id"]]
            self.assertEqual(artifact["source_file_sha256"], bridge["source_file_sha256"])
            self.assertIn(artifact["source_file_sha256"], row["source_file_sha256_scope"])
            self.assertEqual(bridge["source_artifact_id"], row["source_artifact_id"])
            self.assertEqual(bridge["source_route_id"], row["source_route_id"])
            self.assertEqual(bridge["preparation_inferred_from_descriptor"], "false")
            self.assertEqual(bridge["synthetic_generated"], "false")
            self.assertEqual(bridge["identity_resolution_state"], "SOURCE_NATIVE_PROVISIONAL")
            self.assertRegex(bridge["record_identity_sha256"], SHA256)
        self.assertTrue(
            all(row["storage_state"] == "HASH_AND_LOCATOR_ONLY" for row in artifacts)
        )
        self.assertTrue(
            all(row["governed_locator"].startswith(manifest.root_locator + "/") for row in artifacts)
        )

    def test_restricted_manifest_and_artifacts_fail_closed_when_tampered(self) -> None:
        if ROUND3M_RESTRICTED_ROOT is None:
            self.skipTest("Round 3M restricted root not supplied")
        with tempfile.TemporaryDirectory(prefix="round3m-manifest-tamper-") as temporary:
            copied_root = Path(temporary) / "restricted-checkpoint"
            shutil.copytree(ROUND3M_RESTRICTED_ROOT, copied_root)
            manifest_path = copied_root / "CAPTURE_MANIFEST.json"
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
            document["root"] = "restricted://untrusted/substitute"
            manifest_path.write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "manifest hash differs"):
                load_bounded_captures(copied_root)

        with tempfile.TemporaryDirectory(prefix="round3m-artifact-tamper-") as temporary:
            copied_root = Path(temporary) / "restricted-checkpoint"
            shutil.copytree(ROUND3M_RESTRICTED_ROOT, copied_root)
            capture_path = (
                copied_root
                / "web_index_field_capture"
                / "coe_peru_2025_generic.json"
            )
            capture_path.write_bytes(capture_path.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "manifest artifact hash mismatch"):
                load_bounded_captures(copied_root)

    def test_generator_is_deterministic_when_capture_is_available(self) -> None:
        if ROUND3M_RESTRICTED_ROOT is None:
            self.skipTest("Round 3M restricted root not supplied")
        committed = REPO_ROOT / "db" / "adapters" / "round3m" / "generated"
        with tempfile.TemporaryDirectory(prefix="round3m-live-adapter-") as temporary:
            generated = Path(temporary)
            metrics = generate(ROUND3M_RESTRICTED_ROOT, generated)
            self.assertEqual(metrics["segmented_atomic_candidate_count"], 140)
            self.assertEqual(metrics["public_review_candidate_count"], 140)
            self.assertEqual(metrics["secondary_review_only_candidate_count"], 0)
            self.assertEqual(metrics["assertion_level_deinflated_count"], 139)
            self.assertEqual(metrics["record_level_unique_count"], 137)
            self.assertEqual(metrics["within_observation_repeat_count"], 1)
            self.assertEqual(metrics["cross_observation_repeat_count"], 2)
            self.assertEqual(
                metrics["p1_p2_within_effective_record_coassertion_count"], 508
            )
            self.assertEqual(
                metrics["restricted_capture_manifest_sha256"],
                EXPECTED_CAPTURE_MANIFEST_SHA256,
            )
            self.assertEqual(
                metrics["restricted_capture_root_locator"],
                EXPECTED_CAPTURE_ROOT_LOCATOR,
            )
            for filename in (
                "PUBLIC_SAFE_LIVE_ASSERTIONS.tsv",
                "PUBLIC_SAFE_CAPTURE_RECEIPTS.tsv",
                "PUBLIC_SAFE_SOURCE_ARTIFACTS.tsv",
                "PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv",
                "LIVE_ADAPTER_METRICS.json",
            ):
                self.assertEqual(
                    (generated / filename).read_bytes(),
                    (committed / filename).read_bytes(),
                    filename,
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--round3m-restricted-root", type=Path)
    parser.add_argument("--round3l-restricted-root", type=Path)
    return parser.parse_args()


def main() -> int:
    global ROUND3M_RESTRICTED_ROOT, ROUND3L_RESTRICTED_ROOT
    args = parse_args()
    round3m = args.round3m_restricted_root or (
        Path(os.environ["ROUND3M_RESTRICTED_ROOT"])
        if "ROUND3M_RESTRICTED_ROOT" in os.environ
        else None
    )
    round3l = args.round3l_restricted_root or (
        Path(os.environ["ROUND3L_RESTRICTED_ROOT"])
        if "ROUND3L_RESTRICTED_ROOT" in os.environ
        else None
    )
    ROUND3M_RESTRICTED_ROOT = round3m.resolve() if round3m is not None else None
    ROUND3L_RESTRICTED_ROOT = round3l.resolve() if round3l is not None else None
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    print("ROUND3M_LIVE_ADAPTERS_PASS")
    print(f"GENERIC_SOURCE_PROFILE_COUNT={len(SOURCE_PROFILES)}")
    print("LIVE_SOURCE_ADAPTER_COUNT=4")
    print("LIVE_SOURCE_ADAPTER_VALIDATED_COUNT=3")
    print("COE_EXPLICIT_JURY_ADAPTER_PASS=true")
    print("COE_FREQUENCY_CODED_ADAPTER_PASS=true")
    print("COE_GENERIC_FIELD_ADAPTER_PASS=true")
    print("MEXICO_2023_LIVE_FIXTURE_PASS=false")
    print("MEXICO_2023_STATUS=SOURCE_DRIFT_DETAIL_BODY_UNAVAILABLE")
    print("COMPLETED_WCC_SCORESHEET_ADAPTER_PASS=false")
    print("WCC_ZERO_YIELD_NEGATIVE_PASS=true")
    print("LIVE_PROVISIONAL_ASSERTION_COUNT=140")
    print("LIVE_ASSERTION_LEVEL_DEINFLATED_COUNT=139")
    print("LIVE_RECORD_LEVEL_UNIQUE_COUNT=137")
    print("LIVE_WITHIN_OBSERVATION_REPEAT_LOSS_COUNT=1")
    print("LIVE_CROSS_OBSERVATION_REPEAT_LOSS_COUNT=2")
    print("LIVE_P1_P2_WITHIN_RECORD_COASSERTION_COUNT=508")
    print("LIVE_EFFECTIVE_RECORD_COUNT=8")
    print("LIVE_P2_PROVISIONAL_COUNT=73")
    print("LIVE_UNRESOLVED_PROVISIONAL_COUNT=67")
    print("LIVE_MODEL_ELIGIBLE_COUNT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
