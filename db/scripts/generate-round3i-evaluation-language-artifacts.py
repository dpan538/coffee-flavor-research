#!/usr/bin/env python3
"""Generate governed Round 3I evaluation-language artifacts.

This batch re-surfaces three already governed sensory datasets as language
documents. It emits only structured, source-local observations: no article
prose, proprietary definitions, scale conversion, pooling, translation, or
artificial language variants.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "db/data/round3i/evaluation"

COTTER_CSV = (
    ROOT
    / "db/data/round3b/raw/cotter_2020_black_coffee/cotter_dataset.csv"
)
COTTER_README = (
    ROOT / "db/data/round3b/raw/cotter_2020_black_coffee/README.txt"
)
ROUND3B_SOURCE_MANIFEST = ROOT / "db/data/round3b/raw/SOURCE_MANIFEST.json"
BOLLEN_TSV = ROOT / "db/data/round3h/batch1/bollen_2024_sensory_scores.tsv"
VEZZULLI_TSV = (
    ROOT / "db/data/round3h/batch1/vezzulli_2022_table2_sensory_medians.tsv"
)
ROUND3H_BATCH1_MANIFEST = (
    ROOT / "db/data/round3h/batch1/batch1_source_manifest.json"
)
BASELINE_EXPRESSIONS = ROOT / "db/data/round2b/pilot_expressions.tsv"

PINNED_INPUT_SHA256 = {
    COTTER_CSV: (
        "931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114"
    ),
    COTTER_README: (
        "f6d8f508bad2824a27be8785c841e8df4c75751b58726820f9e3dd226fe3fb5e"
    ),
    ROUND3B_SOURCE_MANIFEST: (
        "0a77f686c26d989fefac330d0cabe5f7b8b8c10863dc7e64012bb4abf604f2db"
    ),
    BOLLEN_TSV: (
        "af06701d39891c3af2d92d1a493461d33aa8995db1c6a2d39d7239178af20073"
    ),
    VEZZULLI_TSV: (
        "1ae24e67eb77ddcf7c85e6fc085a504e022d22df3642211d21d81ee23040066b"
    ),
    ROUND3H_BATCH1_MANIFEST: (
        "f89dfe2aac6f49010b21667f28dbc01f9d7710e96c056a40176cf3f761c4fcda"
    ),
    BASELINE_EXPRESSIONS: (
        "4848c64e38a70eba3d51dd3ab7d965d6d02544d6e5b28619dd4e209f0c2f2c23"
    ),
}

EXPECTED_DOCUMENT_COUNTS = {
    "dryad.cotter-v4": 3186,
    "figshare.bollen-2024": 95,
    "pmc.vezzulli-2022": 8,
}
EXPECTED_OCCURRENCE_COUNTS = {
    "dryad.cotter-v4": 10763,
    "figshare.bollen-2024": 530,
    "pmc.vezzulli-2022": 151,
}
EXPECTED_SOURCE_FAMILY_COUNT = 3
EXPECTED_DOCUMENT_COUNT = 3289
EXPECTED_EXPRESSION_COUNT = 37
EXPECTED_ROUND2B_OVERLAP_COUNT = 14
EXPECTED_GOVERNED_BASELINE_OVERLAP_COUNT = 19
EXPECTED_UNIQUE_EXPRESSION_GAIN = 18
EXPECTED_OCCURRENCE_COUNT = 11444
EXPECTED_BASELINE_EXPRESSION_ROWS = 1716
EXPECTED_BASELINE_NORMALIZED_IDENTITIES = 1713

# These identities were admitted after the Round 2B pilot inventory and are
# already present in the governed 1,777-expression Round 3H baseline.  Keep
# them explicit so this offline generator cannot overstate incremental gain by
# comparing only with the older Round 2B file.
POST_ROUND2B_GOVERNED_BASELINE = {
    "astringent",
    "bitter",
    "burnt",
    "rubber",
    "sour",
}

FAMILY_FIELDS = [
    "language_source_family_key",
    "family_name",
    "canonical_origin_key",
    "counts_as_independent",
    "mirror_of_language_source_family_key",
    "counts_as_new_contemporary_family",
    "counts_as_zh_hans_family",
    "historical_baseline",
    "source_authored",
    "admitted",
    "independence_basis",
    "introduced_round",
]
SOURCE_FIELDS = [
    "language_source_key",
    "language_source_family_key",
    "title",
    "authors_or_owner",
    "publication_year",
    "doi_or_stable_url",
    "repository",
    "exact_version",
    "access_date",
    "license_expression",
    "license_url",
    "raw_text_internal_use",
    "raw_text_public_redistribution",
    "derived_expression_internal_use",
    "derived_expression_public_release",
    "derived_counts_internal_use",
    "derived_counts_public_release",
    "model_research_use",
    "rights_basis",
    "rights_review_complete",
    "privacy_decision",
    "privacy_review_complete",
    "source_file_manifest",
    "source_file_hash_complete",
    "language_codes",
    "geography",
    "data_type",
    "evidence_role",
    "limitations",
    "annotation_complete",
    "admitted",
]
DOCUMENT_FIELDS = [
    "language_document_key",
    "language_source_key",
    "language_source_family_key",
    "source_revision",
    "source_date",
    "source_row_locator",
    "language_code",
    "document_type",
    "source_content_sha256",
    "content",
    "raw_text_public_export_allowed",
    "counts_as_new_contemporary_document",
    "counts_as_zh_hans_document",
    "source_authored",
    "machine_translated",
    "artificial_variant",
    "privacy_state",
    "public_export_state",
    "frozen_snapshot",
]
EXPRESSION_FIELDS = [
    "language_expression_key",
    "language_code",
    "representative_source_phrase",
    "normalized_expression",
    "expression_role",
    "source_authored",
    "machine_translated",
    "artificial_variant",
    "review_state",
    "counts_toward_governed_total",
    "counts_as_zh_hans_sensory_expression",
    "public_export_allowed",
    "limitation",
]
OCCURRENCE_FIELDS = [
    "language_occurrence_key",
    "language_document_key",
    "language_expression_key",
    "raw_source_phrase",
    "source_locator",
    "observed_value",
]

COTTER_TERM_SPECS = {
    "Tea.floral": ("tea/floral", "Tea.floral", "COMPOSITE_REFERENCE"),
    "Fruit": ("fruit", "Fruit", "AROMA_REFERENCE"),
    "Citrus": ("citrus", "Citrus", "AROMA_REFERENCE"),
    "Green.veg": (
        "green/vegetative",
        "Green.veg",
        "COMPOSITE_REFERENCE",
    ),
    "Paper.wood": ("paper/wood", "Paper.wood", "COMPOSITE_REFERENCE"),
    "Burnt": ("burnt", "Burnt", "AROMA_REFERENCE"),
    "Cereal": ("cereal", "Cereal", "AROMA_REFERENCE"),
    "Nutty": ("nutty", "Nutty", "AROMA_REFERENCE"),
    "Dark.chocolate": (
        "dark chocolate",
        "Dark.chocolate",
        "AROMA_REFERENCE",
    ),
    "Caramel": ("caramel", "Caramel", "AROMA_REFERENCE"),
    "Bitter": ("bitter", "Bitter", "BASIC_TASTE"),
    "Astringent": ("astringent", "Astringent", "TEXTURE"),
    "Roasted": ("roasted", "Roasted", "AROMA_REFERENCE"),
    "Sour": ("sour", "Sour", "BASIC_TASTE"),
    "Thick.viscous": (
        "thick/viscous",
        "Thick.viscous",
        "COMPOSITE_REFERENCE",
    ),
    "Sweet": ("sweet", "Sweet", "BASIC_TASTE"),
    "Rubber": ("rubber", "Rubber", "AROMA_REFERENCE"),
}

BOLLEN_TERM_SPECS = {
    "green_vegetative": (
        "green/vegetative",
        "Green/Vegetative",
        "COMPOSITE_REFERENCE",
    ),
    "roasted": ("roasted", "Roasted", "AROMA_REFERENCE"),
    "spices": ("spices", "Spices", "AROMA_REFERENCE"),
    "nutty_cocoa": ("nutty/cocoa", "Nutty/Cocoa", "COMPOSITE_REFERENCE"),
    "sweet": ("sweet", "Sweet", "BASIC_TASTE"),
    "floral": ("floral", "Floral", "AROMA_REFERENCE"),
    "fruity": ("fruity", "Fruity", "AROMA_REFERENCE"),
    "sour_fermented": (
        "sour/fermented",
        "Sour/Fermented",
        "COMPOSITE_REFERENCE",
    ),
}

VEZZULLI_TERM_SPECS = {
    "Aroma intensity": ("aroma intensity", "QUALIFIER"),
    "Body": ("body", "TEXTURE"),
    "Acidity": ("acidity", "BASIC_TASTE"),
    "Bitter": ("bitter", "BASIC_TASTE"),
    "Astringency": ("astringency", "TEXTURE"),
    "Honey": ("honey", "AROMA_REFERENCE"),
    "Floral and fruity": ("floral and fruity", "COMPOSITE_REFERENCE"),
    "Dry vegetal": ("dry vegetal", "AROMA_REFERENCE"),
    "Vegetal": ("vegetal", "AROMA_REFERENCE"),
    "Stone fruit": ("stone fruit", "AROMA_REFERENCE"),
    "Nuts and dry fruits": (
        "nuts and dry fruits",
        "COMPOSITE_REFERENCE",
    ),
    "Cereals": ("cereals", "AROMA_REFERENCE"),
    "Caramel": ("caramel", "AROMA_REFERENCE"),
    "Cocoa": ("cocoa", "AROMA_REFERENCE"),
    "Pastry": ("pastry", "AROMA_REFERENCE"),
    "Roasted": ("roasted", "AROMA_REFERENCE"),
    "Burnt": ("burnt", "AROMA_REFERENCE"),
    "Positive aromas": ("positive aromas", "SENSORY_ATTRIBUTE"),
    "Aroma persistence": ("aroma persistence", "QUALIFIER"),
}


class GenerationError(RuntimeError):
    """Raised when a pinned input or generated invariant differs."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GenerationError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def write_tsv(
    path: Path,
    rows: Iterable[dict[str, Any]],
    fields: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def read_delimited(path: Path, delimiter: str) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def verify_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    for path, expected_sha256 in PINNED_INPUT_SHA256.items():
        require(path.is_file(), f"missing pinned input: {path.relative_to(ROOT)}")
        actual_sha256 = sha256_path(path)
        require(
            actual_sha256 == expected_sha256,
            "pinned input SHA-256 differs: "
            + str(path.relative_to(ROOT))
            + f" expected {expected_sha256}, found {actual_sha256}",
        )

    round3b_manifest = json.loads(
        ROUND3B_SOURCE_MANIFEST.read_text(encoding="utf-8")
    )
    cotter_sources = [
        source
        for source in round3b_manifest["sources"]
        if source["source_key"] == "dryad_cotter_black_coffee"
    ]
    require(len(cotter_sources) == 1, "Cotter source manifest entry changed")
    cotter_source = cotter_sources[0]
    require(
        cotter_source["dryad_version_number"] == 4,
        "Cotter Dryad version is not 4",
    )
    require(
        cotter_source["license"] == "CC0-1.0",
        "Cotter license expression changed",
    )
    cotter_files = {item["path"]: item for item in cotter_source["files"]}
    require(
        cotter_files["cotter_2020_black_coffee/cotter_dataset.csv"]["sha256"]
        == PINNED_INPUT_SHA256[COTTER_CSV],
        "Cotter manifest CSV hash changed",
    )
    require(
        cotter_files["cotter_2020_black_coffee/cotter_dataset.csv"][
            "row_count"
        ]
        == 3186,
        "Cotter manifest row count changed",
    )
    require(
        cotter_files["cotter_2020_black_coffee/README.txt"]["sha256"]
        == PINNED_INPUT_SHA256[COTTER_README],
        "Cotter manifest README hash changed",
    )

    batch1_manifest = json.loads(
        ROUND3H_BATCH1_MANIFEST.read_text(encoding="utf-8")
    )
    batch1_sources = {
        source["source_key"]: source for source in batch1_manifest["sources"]
    }
    require(
        set(batch1_sources)
        == {
            "scielo.iswaldi-2026",
            "pmc.vezzulli-2022",
            "figshare.bollen-2024",
        },
        "Round 3H batch-1 source inventory changed",
    )
    bollen = batch1_sources["figshare.bollen-2024"]
    require(
        bollen["license"] == "CC BY 4.0"
        and bollen["derived_file"]["sha256"]
        == PINNED_INPUT_SHA256[BOLLEN_TSV]
        and bollen["derived_file"]["rows"] == 95
        and bollen["official_file"]["sha256"]
        == "4ca2bff21183d2615e244f68b330ba23282f56e6d012c7be762f04baa19abb0a",
        "Bollen manifest contract changed",
    )
    vezzulli = batch1_sources["pmc.vezzulli-2022"]
    require(
        vezzulli["license"] == "CC BY 4.0"
        and vezzulli["derived_file"]["sha256"]
        == PINNED_INPUT_SHA256[VEZZULLI_TSV]
        and vezzulli["derived_file"]["rows"] == 160
        and vezzulli["official_file"]["sha256"]
        == "1120133f98712a44d4af364a578f90bc348d31b51de948381fa1b835b5b26c75",
        "Vezzulli manifest contract changed",
    )
    return cotter_source, batch1_sources


def source_families() -> list[dict[str, Any]]:
    rows = [
        {
            "language_source_family_key": "family.baseline.cotter-consumers",
            "family_name": "Cotter consumer black-coffee evaluations",
            "canonical_origin_key": "doi.10.25338/b8993h",
            "counts_as_independent": True,
            "mirror_of_language_source_family_key": "",
            "counts_as_new_contemporary_family": True,
            "counts_as_zh_hans_family": False,
            "historical_baseline": False,
            "source_authored": True,
            "admitted": True,
            "independence_basis": (
                "Independent UC Davis consumer study deposited as a versioned "
                "Dryad dataset; mirrors do not count separately."
            ),
            "introduced_round": "3I",
        },
        {
            "language_source_family_key": (
                "family.bollen-robusta-qgraders-2024"
            ),
            "family_name": "Bollen Robusta Q-grader profiles",
            "canonical_origin_key": "doi.10.3389/fsufs.2024.1382976",
            "counts_as_independent": True,
            "mirror_of_language_source_family_key": "",
            "counts_as_new_contemporary_family": True,
            "counts_as_zh_hans_family": False,
            "historical_baseline": False,
            "source_authored": True,
            "admitted": True,
            "independence_basis": (
                "Independent Frontiers article and Figshare workbook origin; "
                "the sanitized TSV is a representation of that one origin."
            ),
            "introduced_round": "3I",
        },
        {
            "language_source_family_key": (
                "family.vezzulli-trainedpanel-2022"
            ),
            "family_name": "Vezzulli trained-panel extraction profiles",
            "canonical_origin_key": "doi.10.3390/foods11060807",
            "counts_as_independent": True,
            "mirror_of_language_source_family_key": "",
            "counts_as_new_contemporary_family": True,
            "counts_as_zh_hans_family": False,
            "historical_baseline": False,
            "source_authored": True,
            "admitted": True,
            "independence_basis": (
                "Independent Foods article and trained-panel origin; Europe "
                "PMC and the derived Table 2 TSV do not count separately."
            ),
            "introduced_round": "3I",
        },
    ]
    return sorted(rows, key=lambda row: row["language_source_family_key"])


def language_sources(
    cotter_manifest: dict[str, Any],
    batch1_sources: dict[str, Any],
) -> list[dict[str, Any]]:
    cotter_files = {
        item["path"]: item for item in cotter_manifest["files"]
    }
    bollen = batch1_sources["figshare.bollen-2024"]
    vezzulli = batch1_sources["pmc.vezzulli-2022"]
    all_rights_allow = {
        "raw_text_internal_use": "ALLOW",
        "raw_text_public_redistribution": "ALLOW",
        "derived_expression_internal_use": "ALLOW",
        "derived_expression_public_release": "ALLOW",
        "derived_counts_internal_use": "ALLOW",
        "derived_counts_public_release": "ALLOW",
        "model_research_use": "ALLOW",
    }
    rows = [
        {
            "language_source_key": "dryad.cotter-v4",
            "language_source_family_key": (
                "family.baseline.cotter-consumers"
            ),
            "title": "Consumer preference data for black coffee",
            "authors_or_owner": (
                "Andrew Cotter; William D. Ristenpart; Jean-Xavier Guinard"
            ),
            "publication_year": 2023,
            "doi_or_stable_url": "https://doi.org/10.25338/B8993H",
            "repository": "Dryad",
            "exact_version": (
                "Dryad dataset version 4, published 2023-01-16"
            ),
            "access_date": "2026-08-26",
            "license_expression": "CC0-1.0",
            "license_url": (
                "https://creativecommons.org/publicdomain/zero/1.0/"
            ),
            **all_rights_allow,
            "rights_basis": (
                "Dryad version 4 and the frozen README state CC0 1.0; CC0 "
                "permits copying, redistribution, derivatives, and model "
                "research. Scholarly citation is retained."
            ),
            "rights_review_complete": True,
            "privacy_decision": (
                "Raw rows contain pseudonymous numeric Judge values. Public "
                "language documents omit Judge, Cluster, session, position, "
                "purchase-intent, and other evaluator-linkage fields."
            ),
            "privacy_review_complete": True,
            "source_file_manifest": canonical_json(
                [
                    {
                        "bytes": cotter_files[
                            "cotter_2020_black_coffee/cotter_dataset.csv"
                        ]["bytes"],
                        "canonical_url": cotter_files[
                            "cotter_2020_black_coffee/cotter_dataset.csv"
                        ]["canonical_download_url"],
                        "path": (
                            "db/data/round3b/raw/"
                            "cotter_2020_black_coffee/cotter_dataset.csv"
                        ),
                        "role": "governed_source_input",
                        "rows": 3186,
                        "sha256": PINNED_INPUT_SHA256[COTTER_CSV],
                    },
                    {
                        "bytes": cotter_files[
                            "cotter_2020_black_coffee/README.txt"
                        ]["bytes"],
                        "canonical_url": cotter_files[
                            "cotter_2020_black_coffee/README.txt"
                        ]["canonical_download_url"],
                        "path": (
                            "db/data/round3b/raw/"
                            "cotter_2020_black_coffee/README.txt"
                        ),
                        "role": "license_and_data_dictionary",
                        "sha256": PINNED_INPUT_SHA256[COTTER_README],
                    },
                ]
            ),
            "source_file_hash_complete": True,
            "language_codes": canonical_json(["en"]),
            "geography": "Davis, California, United States",
            "data_type": "COFFEE_CONSUMER_EVALUATION_DATASET",
            "evidence_role": (
                "Individual consumer evaluation rows with 17 binary CATA "
                "attributes and source-local ratings."
            ),
            "limitations": (
                "One washed Honduras coffee and one batch-filter preparation; "
                "CATA and rating scales remain source-local and unpooled."
            ),
            "annotation_complete": True,
            "admitted": True,
        },
        {
            "language_source_key": "figshare.bollen-2024",
            "language_source_family_key": (
                "family.bollen-robusta-qgraders-2024"
            ),
            "title": (
                "Sensory profiles of Robusta coffee genetic resources from "
                "the Democratic Republic of the Congo"
            ),
            "authors_or_owner": "Robrecht Bollen et al.",
            "publication_year": 2024,
            "doi_or_stable_url": (
                "https://doi.org/10.3389/fsufs.2024.1382976.s002"
            ),
            "repository": "Frontiers Figshare",
            "exact_version": (
                "Figshare item 25735122 version 1, published "
                "2024-05-02T04:25:40Z"
            ),
            "access_date": "2026-08-26",
            "license_expression": "CC BY 4.0",
            "license_url": (
                "https://creativecommons.org/licenses/by/4.0/"
            ),
            **all_rights_allow,
            "rights_basis": (
                "The versioned Frontiers Figshare supplement is CC BY 4.0; "
                "reuse and derivatives are allowed with attribution."
            ),
            "rights_review_complete": True,
            "privacy_decision": (
                "The sanitized profile TSV contains genotype, harvest, and "
                "aggregate sample values but no participant identifiers."
            ),
            "privacy_review_complete": True,
            "source_file_manifest": canonical_json(
                [
                    {
                        "bytes": bollen["official_file"]["bytes"],
                        "canonical_url": bollen["official_file"]["locator"],
                        "role": "official_source_workbook",
                        "sha256": bollen["official_file"]["sha256"],
                    },
                    {
                        "bytes": BOLLEN_TSV.stat().st_size,
                        "path": (
                            "db/data/round3h/batch1/"
                            "bollen_2024_sensory_scores.tsv"
                        ),
                        "role": "sanitized_governed_input",
                        "rows": 95,
                        "sha256": PINNED_INPUT_SHA256[BOLLEN_TSV],
                    },
                ]
            ),
            "source_file_hash_complete": True,
            "language_codes": canonical_json(["en"]),
            "geography": "Democratic Republic of the Congo",
            "data_type": "COFFEE_TRAINED_PANEL_PROFILE_DATASET",
            "evidence_role": (
                "Three-Q-grader sample profiles for 95 genotype-harvest "
                "records and eight interpretable descriptor classes."
            ),
            "limitations": (
                "Broad source descriptor classes and source-local score/count "
                "scales; one Nutty/Cocoa cell is not reported. Third-party "
                "wheel definitions are excluded."
            ),
            "annotation_complete": True,
            "admitted": True,
        },
        {
            "language_source_key": "pmc.vezzulli-2022",
            "language_source_family_key": (
                "family.vezzulli-trainedpanel-2022"
            ),
            "title": (
                "Metabolomics Combined with Sensory Analysis Reveals the "
                "Impact of Different Extraction Methods on Coffee Beverages "
                "from Coffea arabica and Coffea canephora var. Robusta"
            ),
            "authors_or_owner": "Fosca Vezzulli et al.",
            "publication_year": 2022,
            "doi_or_stable_url": (
                "https://doi.org/10.3390/foods11060807"
            ),
            "repository": "Europe PMC / Foods",
            "exact_version": (
                "PMC8953325 full-text XML released 2022-03-26; article "
                "Table 2"
            ),
            "access_date": "2026-08-26",
            "license_expression": "CC BY 4.0",
            "license_url": (
                "https://creativecommons.org/licenses/by/4.0/"
            ),
            **all_rights_allow,
            "rights_basis": (
                "The Foods version of record and Europe PMC full text are "
                "CC BY 4.0; attributed reuse of Table 2 aggregates and "
                "derived expressions is allowed."
            ),
            "rights_review_complete": True,
            "privacy_decision": (
                "Only published eight-cell panel medians are emitted; no "
                "individual panelist rows or identifiers are available."
            ),
            "privacy_review_complete": True,
            "source_file_manifest": canonical_json(
                [
                    {
                        "bytes": vezzulli["official_file"]["bytes"],
                        "canonical_url": vezzulli["official_file"]["locator"],
                        "role": "official_full_text_xml",
                        "sha256": vezzulli["official_file"]["sha256"],
                    },
                    {
                        "bytes": VEZZULLI_TSV.stat().st_size,
                        "path": (
                            "db/data/round3h/batch1/"
                            "vezzulli_2022_table2_sensory_medians.tsv"
                        ),
                        "role": "table2_governed_input",
                        "rows": 160,
                        "sha256": PINNED_INPUT_SHA256[VEZZULLI_TSV],
                    },
                ]
            ),
            "source_file_hash_complete": True,
            "language_codes": canonical_json(["en"]),
            "geography": "Italy",
            "data_type": "COFFEE_TRAINED_PANEL_PROFILE_DATASET",
            "evidence_role": (
                "Eight species-by-extraction trained-panel profiles using "
                "19 flavor, aroma, taste, and texture descriptors."
            ),
            "limitations": (
                "Published medians from six panelists; source-local scale "
                "only. Color, chemistry, prose, and third-party form "
                "definitions are excluded."
            ),
            "annotation_complete": True,
            "admitted": True,
        },
    ]
    return sorted(rows, key=lambda row: row["language_source_key"])


def is_positive_source_value(value: str) -> bool:
    if value == "NOT_REPORTED":
        return False
    try:
        return Decimal(value) > 0
    except InvalidOperation as error:
        raise GenerationError(f"non-numeric source value: {value!r}") from error


def expression_key(normalized_expression: str) -> str:
    return (
        "expression.round3i.en.sha256_"
        + sha256_text(normalized_expression)
    )


def occurrence_key(
    document_key: str,
    language_expression_key: str,
    source_locator: str,
) -> str:
    identity = (
        document_key
        + "\x00"
        + language_expression_key
        + "\x00"
        + source_locator
    )
    return "occurrence.round3i.sha256_" + sha256_text(identity)


def add_expression(
    expressions: dict[str, dict[str, Any]],
    baseline_normalized: set[str],
    normalized_expression: str,
    representative_source_phrase: str,
    expression_role: str,
) -> str:
    key = expression_key(normalized_expression)
    existing = expressions.get(normalized_expression)
    if existing is not None:
        require(
            existing["expression_role"] == expression_role,
            "expression role differs across source-local occurrences: "
            + normalized_expression,
        )
        return key
    expressions[normalized_expression] = {
        "language_expression_key": key,
        "language_code": "en",
        "representative_source_phrase": representative_source_phrase,
        "normalized_expression": normalized_expression,
        "expression_role": expression_role,
        "source_authored": True,
        "machine_translated": False,
        "artificial_variant": False,
        "review_state": "SOURCE_REVIEWED",
        "counts_toward_governed_total": (
            normalized_expression not in baseline_normalized
        ),
        "counts_as_zh_hans_sensory_expression": False,
        "public_export_allowed": True,
        "limitation": (
            "Observed source label only; meanings and numeric scales remain "
            "source-local and are not pooled across families."
        ),
    }
    return key


def document_row(
    *,
    key: str,
    source_key: str,
    family_key: str,
    revision: str,
    source_date: str,
    locator: str,
    document_type: str,
    content: dict[str, Any],
    privacy_state: str,
) -> dict[str, Any]:
    encoded_content = canonical_json(content)
    return {
        "language_document_key": key,
        "language_source_key": source_key,
        "language_source_family_key": family_key,
        "source_revision": revision,
        "source_date": source_date,
        "source_row_locator": locator,
        "language_code": "en",
        "document_type": document_type,
        "source_content_sha256": sha256_text(encoded_content),
        "content": encoded_content,
        "raw_text_public_export_allowed": False,
        "counts_as_new_contemporary_document": True,
        "counts_as_zh_hans_document": False,
        "source_authored": True,
        "machine_translated": False,
        "artificial_variant": False,
        "privacy_state": privacy_state,
        "public_export_state": "PUBLIC_DERIVED_ONLY",
        "frozen_snapshot": True,
    }


def occurrence_row(
    *,
    document_key: str,
    expression: str,
    raw_phrase: str,
    locator: str,
    observed_value: dict[str, Any],
) -> dict[str, Any]:
    key = expression_key(expression)
    return {
        "language_occurrence_key": occurrence_key(
            document_key,
            key,
            locator,
        ),
        "language_document_key": document_key,
        "language_expression_key": key,
        "raw_source_phrase": raw_phrase,
        "source_locator": locator,
        "observed_value": canonical_json(observed_value),
    }


def build_cotter(
    baseline_normalized: set[str],
    expressions: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = read_delimited(COTTER_CSV, ",")
    require(len(rows) == 3186, f"Cotter row count is {len(rows)}")
    require(
        len(rows[0]) == 48,
        f"Cotter field count is {len(rows[0])}",
    )
    require(
        set(COTTER_TERM_SPECS).issubset(rows[0]),
        "Cotter CATA columns changed",
    )
    require(
        len({row["Judge"] for row in rows}) == 118,
        "Cotter pseudonymous judge count changed",
    )

    documents: list[dict[str, Any]] = []
    occurrences: list[dict[str, Any]] = []
    for position, row in enumerate(rows, start=1):
        for column in COTTER_TERM_SPECS:
            require(
                row[column] in {"0", "1"},
                f"Cotter CATA value changed at row {position}: {column}",
            )
        selected_columns = [
            column
            for column in COTTER_TERM_SPECS
            if row[column] == "1"
        ]
        require(
            bool(selected_columns),
            f"Cotter row {position} has no selected CATA expression",
        )
        selected_phrases = [
            COTTER_TERM_SPECS[column][1] for column in selected_columns
        ]
        content = {
            "brew_code": row["Brew"],
            "selected_cata_source_labels": selected_phrases,
            "source_local_condition": {
                "percent_extraction_condition": row["PE.x"],
                "tds_condition": row["TDS.x"],
                "temperature_condition": row["Temp.x"],
            },
            "source_local_ratings": {
                "Acidity": row["Acidity"],
                "Flavor.intensity": row["Flavor.intensity"],
                "Liking": row["Liking"],
                "Mouthfeel": row["Mouthfeel"],
            },
            "source_local_scale_notice": (
                "CATA selections and rating values are retained in source "
                "semantics and are not comparable to other source scales."
            ),
        }
        encoded = canonical_json(content).casefold()
        for prohibited in (
            '"judge"',
            '"cluster"',
            '"session number"',
            '"position"',
            '"purchase.intent"',
        ):
            require(
                prohibited not in encoded,
                "Cotter public document contains evaluator-linkage data",
            )
        doc_key = f"document.cotter-v4.row-{position:04d}"
        documents.append(
            document_row(
                key=doc_key,
                source_key="dryad.cotter-v4",
                family_key="family.baseline.cotter-consumers",
                revision="Dryad dataset version 4",
                source_date="2023-01-16",
                locator=f"cotter_dataset.csv:data_row:{position:04d}",
                document_type="CONSUMER_EVALUATION",
                content=content,
                privacy_state="DEIDENTIFIED_SOURCE_ROW",
            )
        )
        for column in selected_columns:
            normalized, raw_phrase, role = COTTER_TERM_SPECS[column]
            add_expression(
                expressions,
                baseline_normalized,
                normalized,
                raw_phrase,
                role,
            )
            locator = f"cata_column:{column}"
            occurrences.append(
                occurrence_row(
                    document_key=doc_key,
                    expression=normalized,
                    raw_phrase=raw_phrase,
                    locator=locator,
                    observed_value={
                        "measurement_type": "CATA_SELECTION",
                        "selected": True,
                        "source_value": "1",
                    },
                )
            )
    return documents, occurrences


def build_bollen(
    baseline_normalized: set[str],
    expressions: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = read_delimited(BOLLEN_TSV, "\t")
    require(len(rows) == 95, f"Bollen row count is {len(rows)}")
    require(
        len(rows[0]) == 36,
        f"Bollen field count is {len(rows[0])}",
    )
    require(
        len({(row["genotype"], row["harvest"]) for row in rows}) == 95,
        "Bollen genotype-harvest identities changed",
    )
    require(
        set(BOLLEN_TERM_SPECS).issubset(rows[0]),
        "Bollen descriptor-class columns changed",
    )

    score_columns = [
        "fragrance_aroma",
        "flavor",
        "aftertaste",
        "salt_acid",
        "bitter_sweet",
        "mouthfeel",
        "balance",
        "overall",
        "uniformity",
        "clean_cup",
        "mean_total_score",
        "sd_total_score",
        "spread_total_score",
        "total_rounded",
    ]
    documents: list[dict[str, Any]] = []
    occurrences: list[dict[str, Any]] = []
    for position, row in enumerate(rows, start=1):
        descriptor_counts: dict[str, Any] = {}
        positive_columns: list[str] = []
        for column, (_, raw_phrase, _) in BOLLEN_TERM_SPECS.items():
            value = row[column]
            descriptor_counts[raw_phrase] = (
                None if value == "NOT_REPORTED" else value
            )
            if is_positive_source_value(value):
                positive_columns.append(column)
        require(
            bool(positive_columns),
            f"Bollen row {position} has no positive descriptor class",
        )
        content = {
            "descriptor_class_counts": descriptor_counts,
            "genetic_class": row["genetic_class"],
            "genotype": row["genotype"],
            "harvest": row["harvest"],
            "source_local_panel_scores": {
                column: row[column] for column in score_columns
            },
            "source_local_scale_notice": (
                "Panel scores and descriptor-class counts retain source "
                "units; no cross-source normalization or pooling is applied."
            ),
        }
        doc_key = f"document.bollen-2024.profile-{position:03d}"
        documents.append(
            document_row(
                key=doc_key,
                source_key="figshare.bollen-2024",
                family_key="family.bollen-robusta-qgraders-2024",
                revision="Frontiers Figshare item 25735122 version 1",
                source_date="2024-05-02",
                locator=(
                    "bollen_2024_sensory_scores.tsv:data_row:"
                    + f"{position:03d}"
                ),
                document_type="TRAINED_PANEL_PROFILE",
                content=content,
                privacy_state="NO_PERSONAL_DATA",
            )
        )
        for column in positive_columns:
            normalized, raw_phrase, role = BOLLEN_TERM_SPECS[column]
            add_expression(
                expressions,
                baseline_normalized,
                normalized,
                raw_phrase,
                role,
            )
            locator = f"descriptor_class_column:{column}"
            occurrences.append(
                occurrence_row(
                    document_key=doc_key,
                    expression=normalized,
                    raw_phrase=raw_phrase,
                    locator=locator,
                    observed_value={
                        "measurement_type": (
                            "SOURCE_DESCRIPTOR_CLASS_COUNT"
                        ),
                        "source_unit": "source-reported count",
                        "source_value": row[column],
                    },
                )
            )
    return documents, occurrences


def build_vezzulli(
    baseline_normalized: set[str],
    expressions: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = read_delimited(VEZZULLI_TSV, "\t")
    require(len(rows) == 160, f"Vezzulli row count is {len(rows)}")
    require(
        len(rows[0]) == 11,
        f"Vezzulli field count is {len(rows[0])}",
    )
    descriptor_inventory = {row["source_descriptor"] for row in rows}
    require(
        descriptor_inventory
        == set(VEZZULLI_TERM_SPECS) | {"Color intensity"},
        "Vezzulli Table 2 descriptor inventory changed",
    )
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["coffee_species"], row["preparation"])].append(row)
    require(len(grouped) == 8, f"Vezzulli profile count is {len(grouped)}")
    require(
        all(len(group_rows) == 20 for group_rows in grouped.values()),
        "Vezzulli profiles no longer contain 20 Table 2 rows",
    )

    documents: list[dict[str, Any]] = []
    occurrences: list[dict[str, Any]] = []
    for species, preparation in sorted(grouped):
        group_rows = grouped[(species, preparation)]
        by_descriptor = {
            row["source_descriptor"]: row for row in group_rows
        }
        source_local_medians = {
            descriptor: by_descriptor[descriptor]["raw_value"]
            for descriptor in VEZZULLI_TERM_SPECS
        }
        content = {
            "coffee_species": species,
            "preparation": preparation,
            "source_local_medians": source_local_medians,
            "source_local_scale_notice": (
                "Published Table 2 medians retain the source-defined panel "
                "scale; no cross-source normalization or pooling is applied."
            ),
        }
        doc_key = (
            "document.vezzulli-2022."
            + species
            + "-"
            + preparation.replace("_", "-")
        )
        documents.append(
            document_row(
                key=doc_key,
                source_key="pmc.vezzulli-2022",
                family_key="family.vezzulli-trainedpanel-2022",
                revision="PMC8953325 Table 2",
                source_date="2022-03-26",
                locator=f"table2:{species}:{preparation}",
                document_type="TRAINED_PANEL_PROFILE",
                content=content,
                privacy_state="NO_PERSONAL_DATA",
            )
        )
        for descriptor, (normalized, role) in VEZZULLI_TERM_SPECS.items():
            source_row = by_descriptor[descriptor]
            value = source_row["raw_value"]
            if not is_positive_source_value(value):
                continue
            add_expression(
                expressions,
                baseline_normalized,
                normalized,
                descriptor,
                role,
            )
            locator = "table2_row:" + source_row["source_row_key"]
            occurrences.append(
                occurrence_row(
                    document_key=doc_key,
                    expression=normalized,
                    raw_phrase=descriptor,
                    locator=locator,
                    observed_value={
                        "measurement_type": "SOURCE_PANEL_MEDIAN",
                        "source_unit": (
                            "source panel median on source-defined scale"
                        ),
                        "source_value": value,
                    },
                )
            )
    return documents, occurrences


def round2b_expression_inventory() -> set[str]:
    rows = read_delimited(BASELINE_EXPRESSIONS, "\t")
    require(
        len(rows) == EXPECTED_BASELINE_EXPRESSION_ROWS,
        f"Round 2B expression row count is {len(rows)}",
    )
    require(
        {row["language_tag_code"] for row in rows} == {"en"},
        "Round 2B baseline language inventory changed",
    )
    normalized = {row["normalized_text"] for row in rows}
    require(
        len(normalized) == EXPECTED_BASELINE_NORMALIZED_IDENTITIES,
        "Round 2B normalized-expression identity count changed",
    )
    return normalized


def governed_expression_inventory() -> set[str]:
    return round2b_expression_inventory() | POST_ROUND2B_GOVERNED_BASELINE


def verify_generated(
    families: list[dict[str, Any]],
    sources: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    expressions: list[dict[str, Any]],
    occurrences: list[dict[str, Any]],
) -> None:
    require(
        len(families) == EXPECTED_SOURCE_FAMILY_COUNT,
        f"source family count is {len(families)}",
    )
    require(len(sources) == 3, f"source count is {len(sources)}")
    require(
        len(documents) == EXPECTED_DOCUMENT_COUNT,
        f"document count is {len(documents)}",
    )
    require(
        len(expressions) == EXPECTED_EXPRESSION_COUNT,
        f"expression count is {len(expressions)}",
    )
    require(
        sum(
            bool(row["counts_toward_governed_total"])
            for row in expressions
        )
        == EXPECTED_UNIQUE_EXPRESSION_GAIN,
        "new governed-expression gain differs",
    )
    require(
        sum(
            not bool(row["counts_toward_governed_total"])
            for row in expressions
        )
        == EXPECTED_GOVERNED_BASELINE_OVERLAP_COUNT,
        "baseline expression overlap differs",
    )
    require(
        len(occurrences) == EXPECTED_OCCURRENCE_COUNT,
        f"occurrence count is {len(occurrences)}",
    )

    family_keys = {
        row["language_source_family_key"] for row in families
    }
    source_keys = {row["language_source_key"] for row in sources}
    document_keys = {
        row["language_document_key"] for row in documents
    }
    expression_keys = {
        row["language_expression_key"] for row in expressions
    }
    occurrence_keys = {
        row["language_occurrence_key"] for row in occurrences
    }
    require(len(family_keys) == len(families), "duplicate family key")
    require(len(source_keys) == len(sources), "duplicate source key")
    require(len(document_keys) == len(documents), "duplicate document key")
    require(
        len(expression_keys) == len(expressions),
        "duplicate expression key",
    )
    require(
        len(occurrence_keys) == len(occurrences),
        "duplicate occurrence key",
    )
    require(
        all(
            row["language_source_family_key"] in family_keys
            for row in sources
        ),
        "source has unresolved family",
    )
    require(
        all(
            row["language_source_key"] in source_keys
            and row["language_source_family_key"] in family_keys
            for row in documents
        ),
        "document has unresolved source or family",
    )
    require(
        all(
            row["language_document_key"] in document_keys
            and row["language_expression_key"] in expression_keys
            for row in occurrences
        ),
        "occurrence has unresolved document or expression",
    )
    require(
        all(
            not row["raw_text_public_export_allowed"]
            and row["public_export_state"] == "PUBLIC_DERIVED_ONLY"
            and row["source_authored"]
            and not row["machine_translated"]
            and not row["artificial_variant"]
            for row in documents
        ),
        "document observation/export boundary changed",
    )

    document_counts = Counter(
        row["language_source_key"] for row in documents
    )
    occurrence_source_by_document = {
        row["language_document_key"]: row["language_source_key"]
        for row in documents
    }
    occurrence_counts = Counter(
        occurrence_source_by_document[row["language_document_key"]]
        for row in occurrences
    )
    require(
        dict(document_counts) == EXPECTED_DOCUMENT_COUNTS,
        f"per-source document counts differ: {dict(document_counts)}",
    )
    require(
        dict(occurrence_counts) == EXPECTED_OCCURRENCE_COUNTS,
        f"per-source occurrence counts differ: {dict(occurrence_counts)}",
    )
    per_document_occurrences = Counter(
        row["language_document_key"] for row in occurrences
    )
    require(
        set(per_document_occurrences) == document_keys,
        "a countable document lacks an observed sensory expression",
    )
    require(
        all(
            row["raw_source_phrase"].strip()
            and not row["raw_source_phrase"].endswith(".")
            for row in occurrences
        ),
        "raw prose or empty phrase entered occurrence inventory",
    )


def main() -> int:
    cotter_manifest, batch1_sources = verify_inputs()
    baseline_normalized = governed_expression_inventory()
    families = source_families()
    sources = language_sources(cotter_manifest, batch1_sources)
    expressions_by_normalized: dict[str, dict[str, Any]] = {}

    documents: list[dict[str, Any]] = []
    occurrences: list[dict[str, Any]] = []
    for builder in (build_cotter, build_bollen, build_vezzulli):
        source_documents, source_occurrences = builder(
            baseline_normalized,
            expressions_by_normalized,
        )
        documents.extend(source_documents)
        occurrences.extend(source_occurrences)

    families.sort(key=lambda row: row["language_source_family_key"])
    sources.sort(key=lambda row: row["language_source_key"])
    documents.sort(key=lambda row: row["language_document_key"])
    expressions = sorted(
        expressions_by_normalized.values(),
        key=lambda row: row["language_expression_key"],
    )
    occurrences.sort(key=lambda row: row["language_occurrence_key"])
    verify_generated(
        families,
        sources,
        documents,
        expressions,
        occurrences,
    )

    artifacts = {
        "language_source_families.tsv": (families, FAMILY_FIELDS),
        "language_sources.tsv": (sources, SOURCE_FIELDS),
        "language_documents.tsv": (documents, DOCUMENT_FIELDS),
        "language_expressions.tsv": (expressions, EXPRESSION_FIELDS),
        "language_expression_occurrences.tsv": (
            occurrences,
            OCCURRENCE_FIELDS,
        ),
    }
    for filename, (rows, fields) in artifacts.items():
        write_tsv(OUTPUT_ROOT / filename, rows, fields)

    artifact_hashes = {
        f"db/data/round3i/evaluation/{filename}": sha256_path(
            OUTPUT_ROOT / filename
        )
        for filename in sorted(artifacts)
    }
    input_hashes = {
        str(path.relative_to(ROOT)): expected
        for path, expected in sorted(
            PINNED_INPUT_SHA256.items(),
            key=lambda item: str(item[0]),
        )
    }
    result = {
        "artifact_hashes": artifact_hashes,
        "batch_key": "round3i.batch1.evaluation-language",
        "governed_baseline_expression_overlap_count": (
            EXPECTED_GOVERNED_BASELINE_OVERLAP_COUNT
        ),
        "round2b_expression_overlap_count": EXPECTED_ROUND2B_OVERLAP_COUNT,
        "contains_article_prose": False,
        "contains_machine_translation": False,
        "contains_proprietary_definitions": False,
        "documents_added": EXPECTED_DOCUMENT_COUNT,
        "documents_by_source": EXPECTED_DOCUMENT_COUNTS,
        "generated_on": "2026-08-26",
        "input_hashes": input_hashes,
        "marginal_coverage_gain": "HIGH",
        "named_sources_reviewed": 3,
        "occurrences_added": EXPECTED_OCCURRENCE_COUNT,
        "occurrences_by_source": EXPECTED_OCCURRENCE_COUNTS,
        "pooled_source_local_scales": False,
        "readiness_state_after": (
            "FAMILY_AND_DOCUMENT_GATES_PASS_UNIQUE_EXPRESSION_GAP_REMAINS"
        ),
        "rights_blocked_count": 0,
        "source_families_added": EXPECTED_SOURCE_FAMILY_COUNT,
        "sources_admitted": 3,
        "targeted_gap": (
            "Rights-cleared contemporary coffee evaluation-language "
            "families and documents"
        ),
        "unique_expression_inventory_count": EXPECTED_EXPRESSION_COUNT,
        "unique_expressions_added": EXPECTED_UNIQUE_EXPRESSION_GAIN,
        "zh_hans_expressions_added": 0,
    }
    write_json(OUTPUT_ROOT / "batch_result.json", result)
    print(canonical_json(result))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as error:
        print(
            f"Round 3I evaluation-language generation failed: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)
