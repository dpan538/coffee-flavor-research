"""Source evidence invariants; fixtures are not empirical confirmation data."""

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import acquire_confirmation_r7 as acquisition


def native_fixture():
    return [
        {
            "condition": condition,
            "participant": person,
            "attribute": field,
            "value": str(value),
        }
        for condition in ("condition_one", "condition_two")
        for person in ("grader_one", "grader_two", "grader_three")
        for field, value in zip(acquisition.FIELDS, (0, 1, 2, 0, 1))
    ]


class ConfirmationSourceTests(unittest.TestCase):
    def test_original_observations_not_cells_or_role_rotations(self):
        parsed = acquisition.parse_exposition_rows(native_fixture())
        self.assertEqual(len(parsed), 6)
        self.assertEqual(len({r["material_id"] for r in parsed}), 1)
        self.assertEqual(len({r["observation_id"] for r in parsed}), 6)
        self.assertTrue(
            all("A" not in r and "B" not in r and "T" not in r for r in parsed)
        )

    def test_numeric_zero_retained_without_negative_or_fine_target(self):
        row = acquisition.parse_exposition_rows(native_fixture())[0]
        self.assertEqual(row["native_recorded_ratings"]["Salty"], 0)
        self.assertTrue(row["observation_masks"]["Salty"])
        self.assertNotIn("negative_concepts", row)
        self.assertNotIn("relevance", row)

    def test_duplicate_raw_cell_cannot_inflate_people_or_groups(self):
        rows = native_fixture()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_SOURCE_OBSERVATION_CELL"):
            acquisition.parse_exposition_rows(rows + [copy.deepcopy(rows[0])])

    def test_missing_measurement_cannot_become_unobserved_zero(self):
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_SOURCE_OBSERVATION"):
            acquisition.parse_exposition_rows(native_fixture()[1:])

    def test_invalid_code_and_unknown_axis_fail(self):
        for value in ("nan", "inf", "-1", "3", "0.5"):
            rows = native_fixture()
            rows[0]["value"] = value
            with self.assertRaisesRegex(ValueError, "EXPOSITION_NATIVE_CODE_REQUIRED"):
                acquisition.parse_exposition_rows(rows)
        rows = native_fixture()
        rows[0]["attribute"] = "Liking"
        with self.assertRaisesRegex(ValueError, "UNREGISTERED_EXPOSITION_ATTRIBUTE"):
            acquisition.parse_exposition_rows(rows)

    def test_public_summary_cannot_leak_answers_or_identifiers(self):
        payload = {
            "source_id": "FIXTURE",
            "source_units": {"observations": 6},
            "status": "TYPED_ONLY",
            "confirmation_groups": 0,
            "records": native_fixture(),
            "participant_id": "PRIVATE",
            "sample_id": "PRIVATE",
            "weights": [1, 2, 3],
        }
        summary = acquisition.public_typed_summary(payload)
        self.assertEqual(
            set(summary), {"source_id", "source_units", "status", "confirmation_groups"}
        )
        self.assertNotIn("PRIVATE", json.dumps(summary))

    def test_source_hash_is_binding(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "source.bin"
            path.write_bytes(b"original")
            expected = hashlib.sha256(b"original").hexdigest()
            self.assertEqual(acquisition.checked_bytes(path, expected), b"original")
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "SOURCE_HASH_CHANGED"):
                acquisition.checked_bytes(path, expected)

    def test_changed_zenodo_workbook_requires_identity_review(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "old.xlsx").write_bytes(b"old workbook")
            current = {
                "id": 20840464,
                "files": [
                    {
                        "key": "panelists_scores_EN.xlsx",
                        "checksum": "md5:" + hashlib.md5(b"old workbook").hexdigest(),
                    }
                ],
            }
            (d / "zenodo-current.json").write_text(json.dumps(current))
            (d / "zenodo-latest.json").write_text(json.dumps({"id": 20840464}))
            (d / "zenodo-versions.json").write_text(json.dumps({"hits": {"total": 2}}))
            self.assertEqual(
                acquisition.zenodo_version_audit(d, d / "old.xlsx")[
                    "new_coffee_groups"
                ],
                0,
            )
            (d / "zenodo-latest.json").write_text(json.dumps({"id": 99999999}))
            with self.assertRaisesRegex(ValueError, "REQUIRES_FRESH_IDENTITY_REVIEW"):
                acquisition.zenodo_version_audit(d, d / "old.xlsx")

    def test_intake_does_not_authorize_model_evaluation(self):
        p = acquisition.protocol()
        self.assertFalse(p["model_evaluation_allowed"])
        self.assertFalse(p["training_allowed"])
        routes = acquisition.source_routes()
        self.assertEqual(len({r["source_id"] for r in routes}), len(routes))
        self.assertTrue(all(r["status"] != "ADMITTED" for r in routes))


if __name__ == "__main__":
    unittest.main()
