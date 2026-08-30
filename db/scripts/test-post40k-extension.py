#!/usr/bin/env python3
"""Validate the isolated 40k-to-50k CoE continuation receipt."""

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
PUBLIC = ROOT / "db" / "data" / "post40k-extension-staging"
ACQUISITION = ROOT / "db" / "scripts" / "acquire-post40k-extension.py"
RESTRICTED = Path("/private/tmp/coffee-flavor-round3m-post40k")
EXPECTED_START = "archive-page=100;detail-index=3;url=https://farmdirectory.cupofexcellence.org/listing/2-la-lucuma-peru-2023/"


def rows(name: str) -> list[dict[str, str]]:
    with (PUBLIC / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Post40kExtension(unittest.TestCase):
    def test_checkpoint_and_staging_isolation(self) -> None:
        manifest = json.loads((PUBLIC / "POST40K_EXTENSION_MANIFEST.json").read_text())
        sidecar = rows("POST40K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv")
        self.assertTrue(manifest["run"])
        self.assertEqual(manifest["cursor_start"], EXPECTED_START)
        self.assertTrue(manifest["exact_cursor_validated"])
        self.assertTrue(manifest["extension_isolated_from_frozen_snapshot"])
        self.assertTrue(manifest["checkpoint_50000_reached"])
        self.assertGreaterEqual(manifest["total_candidate_count"], 50000)
        self.assertEqual(sum(row["counts_as_assertion"] == "true" for row in sidecar), manifest["net_new_deinflated_assertion_count"])
        self.assertEqual({row["frozen_snapshot_member"] for row in sidecar}, {"false"})
        self.assertEqual(manifest["model_eligible_assertion_count"], 0)
        self.assertEqual(manifest["human_reviewed_assertion_count"], 0)
        self.assertFalse(manifest["schema_changed"])
        self.assertEqual(manifest["new_migration_count"], 0)

    def test_public_boundary_and_shortfall_reporting(self) -> None:
        with (PUBLIC / "POST40K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv").open(encoding="utf-8", newline="") as handle:
            fields = set(csv.DictReader(handle, delimiter="\t").fieldnames or [])
        self.assertFalse(fields & {"raw_field_text", "atomic_source_text", "source_native_form", "publisher"})
        manifest = json.loads((PUBLIC / "POST40K_EXTENSION_MANIFEST.json").read_text())
        self.assertEqual(manifest["new_non_coe_assertion_count"], 0)
        self.assertIn("shortfall", " ".join(manifest).casefold())
        routes = rows("POST40K_SOURCE_ROUTE_DISCOVERY.tsv")
        self.assertEqual(routes[0]["discovery_lane"], "COE_CONTINUATION")

    def test_checksums_and_offline_replay(self) -> None:
        listed = {
            name: value
            for value, name in (line.split("  ", 1) for line in (PUBLIC / "SHA256SUMS").read_text().splitlines())
        }
        self.assertTrue(all(digest(PUBLIC / name) == value for name, value in listed.items()))
        self.assertTrue(RESTRICTED.is_dir())
        before = digest(PUBLIC / "SHA256SUMS")
        subprocess.run([sys.executable, "-B", str(ACQUISITION), "--restricted-root", str(RESTRICTED), "--offline"], cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertEqual(digest(PUBLIC / "SHA256SUMS"), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
