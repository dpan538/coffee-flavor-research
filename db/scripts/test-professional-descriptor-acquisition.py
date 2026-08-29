#!/usr/bin/env python3
"""Targeted adapter and public-boundary tests for Batch 2 acquisition."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).with_name("acquire-professional-descriptors-batch2.py")
SPEC = importlib.util.spec_from_file_location("professional_descriptor_batch2", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load acquisition adapter")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    native, provisional, status, method, confidence_basis = MODULE.normalize("  Berries. ")
    check(native == "Berries", "native normalization drift")
    check(provisional == "berry", "approved alias drift")
    check(status == "AUTO_APPROVED_ALIAS", "alias status drift")
    check(method == "DOCUMENTED_ORTHOGRAPHIC_ALIAS", "alias method drift")
    check(confidence_basis.startswith("0.990000|"), "alias confidence drift")

    check(MODULE.split_atomic("jasmine, peach; cocoa") == ("jasmine", "peach", "cocoa"), "atomic split drift")
    check(MODULE.descriptor_class("silky mouthfeel") == "BROAD_SENSORY", "broad class drift")
    check(MODULE.descriptor_class("jasmine") == "STRICT_FLAVOR", "strict class drift")

    source = {
        "family": "family.test",
        "publisher": "Test professional panel",
        "route": "route.test",
        "schema": "schema.test",
        "language": "en",
        "rights": "UNKNOWN",
        "rights_basis": "TEST_ONLY",
        "evidence_tier": "UNRESOLVED",
        "collection_tier": "SILVER",
    }
    atoms = MODULE.make_atoms(
        source=source,
        artifact_sha256="a" * 64,
        source_url="https://example.test/lot/1/",
        source_locator="html:field=notes",
        effective_record_id="effective.test.1",
        coffee_identity_id="coffee.test.1",
        edition_or_release="test",
        edition_year="2026",
        preparation_service="CUPPING",
        roast_evidence="UNREPORTED",
        source_field_label="Cupping notes",
        raw_field_text="jasmine, jasmine; silky mouthfeel",
        publication_layer="GENERIC_ORGANIZER_SENSORY_FIELD",
        provenance_state="OFFICIAL_FIELD_ORIGIN_UNRESOLVED",
    )
    assertion_losses, record_losses = MODULE.apply_deinflation(atoms)
    check((assertion_losses, record_losses) == (1, 0), "observation de-inflation drift")
    check(sum(atom.counts_as_assertion for atom in atoms) == 2, "de-inflated assertion count drift")
    safe = list(MODULE.safe_rows(atoms))
    check("atomic_source_text" not in safe[0] and "raw_field_text" not in safe[0], "source text leaked into public row")
    check(safe[0]["source_text_storage_state"].endswith("HASH_ONLY_PUBLIC"), "public storage boundary drift")

    overlap_atoms = MODULE.make_atoms(
        source=source,
        artifact_sha256="b" * 64,
        source_url=next(iter(MODULE.BASELINE_PUBLICATION_OVERLAP_URLS)),
        source_locator="html:field=notes",
        effective_record_id="effective.test.overlap",
        coffee_identity_id="coffee.test.overlap",
        edition_or_release="test",
        edition_year="2009",
        preparation_service="CUPPING",
        roast_evidence="UNREPORTED",
        source_field_label="Overall",
        raw_field_text="jasmine, peach",
        publication_layer="GENERIC_ORGANIZER_SENSORY_FIELD",
        provenance_state="OFFICIAL_FIELD_ORIGIN_UNRESOLVED",
    )
    MODULE.apply_deinflation(overlap_atoms)
    check(MODULE.suppress_baseline_publication_overlap(overlap_atoms, overlap_atoms[0].source_url) == 2, "cross-batch overlap loss drift")
    check(not any(atom.counts_as_assertion for atom in overlap_atoms), "overlap remained countable")

    html = """
    <div class="item-attr">Year</div><div class="item-property">2024</div>
    <div>Score from International Judges</div>
    <td><strong>Top Jury Descriptions:</strong>
    Aroma: jasmine, peach Acidity: citric Mouthfeel: silky</td>
    """
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "detail.html"
        path.write_text(html, encoding="utf-8")
        parsed = MODULE.parse_coe_detail(path, "https://farmdirectory.cupofexcellence.org/listing/test-2024/")
    check(parsed and all(atom.evidence_tier == "P2" for atom in parsed), "explicit jury adapter tier drift")
    check(all(atom.collection_tier == "GOLD" for atom in parsed), "explicit jury collection tier drift")

    print("PROFESSIONAL_DESCRIPTOR_ACQUISITION_ADAPTER_PASS=true")


if __name__ == "__main__":
    main()
