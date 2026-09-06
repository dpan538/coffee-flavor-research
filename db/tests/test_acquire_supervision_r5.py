"""Synthetic schema fixtures only; never used as sensory labels or model data."""

import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import acquire_supervision_r5 as s


def csv_file(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def cotter_fixture():
    return {
        "Judge": "1",
        "Brew": "87-1.0-16",
        "Session Number": "1",
        **{k: "0" for k in s.CATA},
        **{k: "3" for k in s.JAR},
        "Liking": "7",
        "Purchase.intent": "3",
    }


def blend_fixture(exp="1", conc="0.07"):
    return {
        "Sample": "1",
        "Exp": exp,
        "CEB": "1",
        "CT": "0",
        "CC": "0",
        "CEA": "0",
        "Conc": conc,
        "Body": "6",
        "Flavour": "5",
        "Acidity": "4",
        "Bitterness": "0",
        "Score": "8",
    }


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_cata_zero_is_ballot_nonselection_not_absolute_absence(self):
        path = self.root / "cotter.csv"
        csv_file(path, [cotter_fixture()])
        rows, summary = s.parse_cotter(path)
        cell = rows[0]["cata"]["Fruit"]
        self.assertEqual(cell["status"], "NOT_SELECTED_WITHIN_THIS_BALLOT")
        self.assertFalse(cell["absolute_sensory_absence"])
        self.assertEqual(summary["source_native_intensity_columns"], 0)
        self.assertFalse(rows[0]["jar"]["Flavor.intensity"]["is_perceived_intensity"])
        self.assertEqual(rows[0]["jar"]["Flavor.intensity"]["middle"], 3)

    def test_cata_missing_and_nonbinary_are_not_false_zeros(self):
        for value in ["", "NA", "2"]:
            row = cotter_fixture()
            row["Fruit"] = value
            path = self.root / "bad.csv"
            csv_file(path, [row])
            with self.assertRaisesRegex(ValueError, "CATA_MISSING_OR_NONBINARY"):
                s.parse_cotter(path)

    def test_cata_duplicate_person_condition_rejected(self):
        path = self.root / "duplicates.csv"
        csv_file(path, [cotter_fixture(), cotter_fixture()])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PARTICIPANT"):
            s.parse_cotter(path)

    def test_blend_cohold_does_not_make_fake_person_or_coffee_identity(self):
        for name in ["DataCD", "DataNAT"]:
            csv_file(
                self.root / f"blendstat_{name}.csv",
                [blend_fixture(), blend_fixture("3", "0.1")],
            )
        rows, summary = s.parse_blendstat(self.root)
        self.assertEqual(len(rows), 4)
        self.assertEqual(summary["conservative_composition_groups"], 1)
        self.assertEqual(summary["unique_process_mix_concentration_conditions"], 4)
        self.assertTrue(all(r["participant_id"] is None for r in rows))
        self.assertTrue(
            all(not r["split_group_is_independent_coffee_material"] for r in rows)
        )
        self.assertEqual(
            rows[0]["minimum_auxiliary_view"],
            {"A": [], "B": {"native.Flavour": 5.0}, "T": {"native.Bitterness": 0.0}},
        )
        self.assertEqual(rows[0]["native_ratings"]["Score"]["task"], "OVERALL_QUALITY")
        self.assertFalse(
            rows[0]["native_ratings"]["Acidity"][
                "eligible_minimal_flavour_to_bitterness_task"
            ]
        )
        self.assertIn("native_mix", rows[0]["forbidden_predictors"])

    def test_blend_duplicate_native_identity_rejected(self):
        csv_file(self.root / "blendstat_DataCD.csv", [blend_fixture(), blend_fixture()])
        with self.assertRaisesRegex(ValueError, "DUPLICATE_BLENDED"):
            s.parse_blendstat(self.root)

    def test_gactt_missing_values_and_unrelated_demographics_never_leak(self):
        row = {
            "Submission ID": "fixture-only",
            "political affiliation": "EXCLUDED_FIXTURE_FIELD",
        }
        for c in "ABCD":
            row.update(
                {
                    f"Coffee {c} - Bitterness": "",
                    f"Coffee {c} - Acidity": "1",
                    f"Coffee {c} - Personal Preference": "5",
                    f"Coffee {c} - Notes": "",
                }
            )
        path = self.root / "survey.csv"
        csv_file(path, [row])
        records, summary = s.parse_great_american(path)
        self.assertEqual(summary["four_sample_observation_slots"], 4)
        self.assertIsNone(records[0]["native_ratings"]["Bitterness"]["value"])
        self.assertFalse(records[0]["training_allowed"])
        self.assertNotIn("EXCLUDED_FIXTURE_FIELD", json.dumps(records))
        self.assertFalse(summary["training_allowed"])

    def test_firstbloom_preserves_aggregate_membership_uncertainty(self):
        csv_file(
            self.root / "firstbloom_product_releases.csv",
            [{"product_release_id": "r1", "product_id": "p1"}],
        )
        row = {
            "id": "obs1",
            "review_text": "fixture only",
            "rating": "4",
            "product_release_id": "r1",
            "body_intensity": "0",
            "acidity_intensity": "3",
            "sweetness_intensity": "",
            "finish_intensity": "1",
        }
        csv_file(
            self.root / "firstbloom_first_bloom_user_product_reviews_202312201402.csv",
            [row],
        )
        csv_file(
            self.root / "firstbloom_product_release_tasting_notes.csv",
            [
                {
                    "product_release_id": "r1",
                    "roaster_tasting_notes": "{a}",
                    "user_review_tasting_notes": "{b}",
                }
            ],
        )
        records, tags, summary = s.parse_firstbloom(self.root)
        self.assertIsNone(records[0]["participant_id"])
        self.assertIsNone(
            records[0]["native_score_observations"]["body_intensity"]["value"]
        )
        self.assertIsNone(records[0]["cata"])
        self.assertNotIn("user_tag_ids_native", records[0])
        self.assertFalse(tags[0]["individual_cata_ballot"])
        self.assertEqual(summary["aggregate_tags_copied_to_individual_reviews"], 0)

    def test_immutable_cache_rejects_different_content(self):
        path = self.root / "artifact.json"
        before = s.save(path, {"real_source": True})
        self.assertEqual(before, s.save(path, {"real_source": True}))
        with self.assertRaisesRegex(ValueError, "PRESERVE_EXISTING"):
            s.save(path, {"real_source": False})

    def test_nested_zip_member_identity_survives_container_change(self):
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as z:
            z.writestr(
                "blank-form.pdf", b"fixture, not a real form or sensory response"
            )
        path = self.root / "outer.zip"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("source-supplement.zip", inner.getvalue())
        result = s.zip_inventory(path)
        self.assertEqual(result[-1]["member"], "source-supplement.zip!blank-form.pdf")
        self.assertEqual(
            result[-1]["sha256"],
            s.digest(b"fixture, not a real form or sensory response"),
        )

    def test_temporary_url_credentials_are_not_provenance(self):
        url = "https://example.org/source.csv?version=1&X-Amz-Credential=x&Signature=y&token=z#fragment"
        self.assertEqual(
            s.safe_source_url(url), "https://example.org/source.csv?version=1"
        )


if __name__ == "__main__":
    unittest.main()
