#!/usr/bin/env python3
"""Validate the isolated post-30k acquisition checkpoint."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "db" / "data" / "post30k-extension-staging"
ACQUISITION = ROOT / "db" / "scripts" / "acquire-post30k-extension.py"
EXPECTED_START = (
    "archive-page=75;detail-index=2;url=https://farmdirectory.cupofexcellence.org/"
    "listing/2-don-dario-hacienda-san-isidro-labrador-costa-rica-2024-experimental/"
)


def rows(name: str) -> list[dict[str, str]]:
    with (PUBLIC / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Post30kExtensionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((PUBLIC / "POST30K_EXTENSION_MANIFEST.json").read_text())

    def test_exact_cursor_and_complete_record_stop(self) -> None:
        manifest = self.manifest
        self.assertEqual(manifest["cursor_start"], EXPECTED_START)
        self.assertTrue(manifest["exact_cursor_validated"])
        self.assertEqual(manifest["total_candidate_count"], 40030)
        self.assertTrue(manifest["checkpoint_40000_reached"])
        self.assertGreaterEqual(manifest["net_new_deinflated_assertion_count"], 9990)
        self.assertEqual(
            manifest["hard_stop_rule"],
            "FIRST_COMPLETE_EFFECTIVE_RECORD_BOUNDARY_AT_OR_ABOVE_TOTAL_40000",
        )
        sidecar = rows("POST30K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv")
        last_record = sidecar[-1]["effective_record_id"]
        last_record_rows = [row for row in sidecar if row["effective_record_id"] == last_record]
        self.assertTrue(any(row["counts_as_assertion"] == "true" for row in last_record_rows))
        self.assertEqual(
            {row["acquisition_cursor"] for row in last_record_rows},
            {last_record_rows[0]["acquisition_cursor"]},
        )

    def test_new_non_coe_family_and_effort_targets(self) -> None:
        manifest = self.manifest
        self.assertGreaterEqual(manifest["new_non_coe_assertion_count"], 1500)
        self.assertEqual(manifest["new_non_coe_positive_family_count"], 1)
        self.assertEqual(manifest["new_rights_clearable_family_count"], 1)
        self.assertTrue(manifest["new_non_coe_assertion_target_reached"])
        self.assertTrue(manifest["new_non_coe_positive_family_target_reached"])
        self.assertGreaterEqual(manifest["non_coe_discovery_effort_rate"], 0.60)
        discovery = rows("POST30K_SOURCE_ROUTE_DISCOVERY.tsv")
        mdpi = next(
            row for row in discovery
            if row["source_family_id"] == "family.mdpi_certified_q_grader_storage_panel"
        )
        self.assertEqual(mdpi["rights_state"], "AFFIRMATIVE_WITH_CONDITIONS")
        self.assertEqual(mdpi["disposition"], "POSITIVE_RIGHTS_CLEARABLE_ROUTE_EXHAUSTED")

    def test_frozen_snapshot_is_preserved_and_extension_is_isolated(self) -> None:
        snapshot = json.loads((ROOT / "db/data/current/CANDIDATE_30K_SNAPSHOT_MANIFEST.json").read_text())
        self.assertEqual(snapshot["mechanically_deinflated_source_assertion_count"], 30010)
        self.assertFalse(snapshot["post30k_extension_included_in_snapshot"])
        self.assertTrue(self.manifest["extension_isolated_from_frozen_snapshot"])
        self.assertEqual(
            {row["frozen_snapshot_member"] for row in rows("POST30K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv")},
            {"false"},
        )

    def test_public_boundary_and_source_language_preservation(self) -> None:
        path = PUBLIC / "POST30K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv"
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            fieldnames = set(reader.fieldnames or [])
            data = list(reader)
        self.assertFalse(
            fieldnames & {
                "raw_field_text", "atomic_source_text", "source_native_form",
                "provisional_normalized_form", "publisher",
            }
        )
        mdpi = [
            row for row in data
            if row["source_family_id"] == "family.mdpi_certified_q_grader_storage_panel"
        ]
        self.assertTrue(mdpi)
        self.assertEqual({row["source_language"] for row in mdpi}, {"es"})
        self.assertTrue(all(row["source_field_label"].startswith("hash:sha256:") for row in data))

    def test_coe_identity_states_do_not_authorize_merges(self) -> None:
        identity = rows("POST30K_COE_IDENTITY_AUDIT.tsv")
        allowed = {
            "EXACT_SAME_RECORD", "HIGH_CONFIDENCE_SAME_RECORD", "POSSIBLE_SAME_RECORD",
            "DISTINCT_RECORD", "INSUFFICIENT_EVIDENCE", "NO_CANDIDATE",
        }
        self.assertTrue(identity)
        self.assertTrue(all(row["match_state"] in allowed for row in identity))
        self.assertTrue(all(row["identity_merge_authorized"] == "false" for row in identity))

    def test_counts_checksums_and_no_model_states(self) -> None:
        sidecar = rows("POST30K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv")
        self.assertEqual(len(sidecar), self.manifest["net_new_raw_assertion_count"])
        self.assertEqual(
            sum(row["counts_as_assertion"] == "true" for row in sidecar),
            self.manifest["net_new_deinflated_assertion_count"],
        )
        expected = {}
        for line in (PUBLIC / "SHA256SUMS").read_text().splitlines():
            value, name = line.split("  ", 1)
            expected[name] = value
        self.assertTrue(all(digest(PUBLIC / name) == value for name, value in expected.items()))
        self.assertEqual(self.manifest["model_eligible_assertion_count"], 0)
        self.assertEqual(self.manifest["human_reviewed_assertion_count"], 0)
        self.assertFalse(self.manifest["schema_changed"])
        self.assertEqual(self.manifest["new_migration_count"], 0)

    @unittest.skipUnless(os.environ.get("POST30K_RESTRICTED_ROOT"), "POST30K_RESTRICTED_ROOT not set; public receipts still verified")
    def test_optional_offline_replay_is_byte_identical(self) -> None:
        before = digest(PUBLIC / "SHA256SUMS")
        subprocess.run(
            [
                sys.executable,
                "-B",
                str(ACQUISITION),
                "--restricted-root",
                os.environ["POST30K_RESTRICTED_ROOT"],
                "--offline",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(digest(PUBLIC / "SHA256SUMS"), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
