#!/usr/bin/env python3
"""Validate the isolated post-20k extension and optional offline replay."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "db" / "data" / "post20k-extension-staging"
CURRENT = ROOT / "db" / "data" / "current"
ACQUISITION = ROOT / "db" / "scripts" / "acquire-post20k-extension.py"
EXPECTED_CURSOR = (
    "archive-page=12;detail-index=10;url="
    "https://farmdirectory.cupofexcellence.org/listing/"
    "9-liquidambar-honduras-2026-parainema-catracha/"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name: str) -> list[dict[str, str]]:
    with (PUBLIC / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def public_hashes() -> dict[str, str]:
    return {
        path.name: sha256_file(path)
        for path in sorted(PUBLIC.iterdir())
        if path.is_file()
    }


class Post20kExtensionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(
            (PUBLIC / "POST20K_EXTENSION_MANIFEST.json").read_text(encoding="utf-8")
        )
        cls.sidecar = rows("POST20K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv")
        cls.routes = rows("POST20K_SOURCE_ROUTE_DISCOVERY.tsv")
        cls.artifacts = rows("POST20K_PUBLIC_ARTIFACT_RECEIPT.tsv")

    def test_checksums_and_manifest_inventory(self) -> None:
        expected = {}
        for line in (PUBLIC / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            digest, name = line.split("  ", 1)
            expected[name] = digest
        self.assertEqual(set(expected), {
            "POST20K_EXTENSION_MANIFEST.json",
            "POST20K_PUBLIC_ARTIFACT_RECEIPT.tsv",
            "POST20K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv",
            "POST20K_SOURCE_ROUTE_DISCOVERY.tsv",
        })
        for name, digest in expected.items():
            self.assertEqual(sha256_file(PUBLIC / name), digest)
        for item in self.manifest["files"]:
            path = PUBLIC / item["path"]
            self.assertEqual(sha256_file(path), item["sha256"])
            self.assertEqual(path.stat().st_size, item["byte_count"])

    def test_exact_cursor_and_complete_record_stop(self) -> None:
        manifest = self.manifest
        self.assertEqual(manifest["cursor_start"], EXPECTED_CURSOR)
        self.assertTrue(manifest["cursor_end"].startswith("archive-page=75;detail-index=2;"))
        self.assertEqual(
            manifest["hard_stop_rule"],
            "FIRST_COMPLETE_EFFECTIVE_RECORD_BOUNDARY_AT_OR_ABOVE_TOTAL_30000",
        )
        self.assertTrue(manifest["checkpoint_30000_reached"])
        self.assertEqual(manifest["total_candidate_count"], 30010)
        self.assertFalse(manifest["coe_route_exhausted"])
        self.assertFalse(manifest["coe_continuation_blocked"])

    def test_frozen_snapshot_is_immutable_and_excludes_extension(self) -> None:
        snapshot = json.loads(
            (CURRENT / "CANDIDATE_20K_SNAPSHOT_MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(snapshot["immutable"])
        self.assertFalse(snapshot["post20k_extension_included_in_snapshot"])
        self.assertEqual(snapshot["frozen_mechanically_deinflated_assertion_count"], 20003)
        self.assertEqual(self.manifest["frozen_denominator_assertion_count"], 20003)
        self.assertEqual(self.manifest["net_new_deinflated_assertion_count"], 10007)
        self.assertEqual(len(self.sidecar), 10023)
        self.assertTrue(all(row["frozen_snapshot_member"] == "false" for row in self.sidecar))

    def test_public_sidecar_has_no_source_native_text(self) -> None:
        forbidden = {"raw_field_text", "atomic_source_text", "source_native_form"}
        self.assertTrue(self.sidecar)
        self.assertTrue(forbidden.isdisjoint(self.sidecar[0]))
        self.assertTrue(
            all(
                row["source_text_storage_state"]
                == "OWNER_CONTROLLED_RESTRICTED_HASH_ONLY_PUBLIC"
                for row in self.sidecar
            )
        )
        self.assertTrue(
            all(row["source_field_label"].startswith("hash:sha256:") for row in self.sidecar)
        )
        ids = [row["descriptor_assertion_id"] for row in self.sidecar]
        self.assertEqual(len(ids), len(set(ids)))

    def test_counts_review_and_model_states_reconcile(self) -> None:
        assertions = [row for row in self.sidecar if row["counts_as_assertion"] == "true"]
        record_unique = [
            row
            for row in self.sidecar
            if row["counts_as_record_unique_descriptor"] == "true"
        ]
        self.assertEqual(len(assertions), 10007)
        self.assertEqual(len(record_unique), 9528)
        self.assertEqual(
            len({row["effective_record_id"] for row in assertions}),
            self.manifest["net_new_effective_record_count"],
        )
        self.assertTrue(all(row["human_reviewed"] == "false" for row in self.sidecar))
        self.assertTrue(all(row["model_eligible"] == "false" for row in self.sidecar))

    def test_source_family_and_rights_targets_are_truthfully_reported(self) -> None:
        assertion_families = Counter(
            row["source_family_id"]
            for row in self.sidecar
            if row["counts_as_assertion"] == "true"
        )
        non_coe = sum(
            count
            for family, count in assertion_families.items()
            if family != "family.ace_cup_of_excellence"
        )
        self.assertEqual(assertion_families["family.ace_cup_of_excellence"], 9298)
        self.assertEqual(non_coe, 709)
        self.assertEqual(
            {
                family
                for family, count in assertion_families.items()
                if family != "family.ace_cup_of_excellence" and count
            },
            {
                "family.frontiers_cenicafe_lengupa_trained_cuppers",
                "family.frontiers_inera_robusta_q_grader_panel",
            },
        )
        positive = [row for row in self.routes if int(row["deinflated_assertion_count"])]
        self.assertEqual(len([row for row in positive if row["discovery_lane"] == "NON_COE"]), 2)
        self.assertTrue(
            all(
                row["rights_state"] == "AFFIRMATIVE"
                for row in positive
                if row["discovery_lane"] == "NON_COE"
            )
        )
        self.assertEqual(self.manifest["non_coe_discovery_effort_count"], 6)
        self.assertEqual(self.manifest["total_discovery_effort_count"], 7)
        self.assertEqual(self.manifest["non_coe_discovery_effort_rate"], 0.857143)

    def test_artifact_receipts_expose_locators_not_files(self) -> None:
        self.assertEqual(len(self.artifacts), 406)
        self.assertTrue(
            all(
                row["restricted_relative_path"].startswith(
                    "restricted://post20k_extension/"
                )
                for row in self.artifacts
            )
        )

    def test_optional_offline_replay_is_byte_identical(self) -> None:
        restricted_root = os.environ.get("POST20K_RESTRICTED_ROOT")
        if not restricted_root:
            self.skipTest("POST20K_RESTRICTED_ROOT not set; public receipts still verified")
        before = public_hashes()
        subprocess.run(
            [
                sys.executable,
                str(ACQUISITION),
                "--restricted-root",
                restricted_root,
                "--offline",
                "--request-delay",
                "0",
            ],
            cwd=ROOT,
            check=True,
        )
        self.assertEqual(public_hashes(), before)
        print("POST20K_OFFLINE_RERUN_PASS=true")


if __name__ == "__main__":
    unittest.main(verbosity=2)
