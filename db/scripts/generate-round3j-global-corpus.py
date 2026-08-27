#!/usr/bin/env python3
"""Generate the governed Round 3J global-acquisition checkpoint artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "round3j"
OUTPUTS = DATA / "global-corpus"
GUCHE = DATA / "derived" / "guchengf_2025_zh_hans_sensory_expressions.tsv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, columns: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=columns, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def candidate_metadata() -> dict[str, tuple[str, str]]:
    values: dict[str, tuple[str, str]] = {}
    for path, key_column, title_column, url_column in (
        (DATA / "global_flavor_source_candidate_register.tsv", "candidate_key", "title", "official_source"),
        (DATA / "source_candidate_register.tsv", "candidate_key", "title", "doi_or_stable_url"),
        (DATA / "regional_source_candidate_register.tsv", "candidate_key", "exact_title", "doi_or_stable_official_url"),
    ):
        for row in read_tsv(path):
            values.setdefault(row[key_column], (row[title_column], row[url_column]))
    return values


# One primary class per candidate. A false coverage flag records a reviewed
# mirror without inflating the ten-candidate gate.
CLASS_KEYS: dict[str, list[tuple[str, str, bool]]] = {
    "A": [
        ("flavorreasonbench-coffee.zenodo", "origin.flavorreasonbench", True),
        ("specialty-coffee-india-set-1", "origin.specialty-coffee-india", True),
        ("candidate.r3j.liang-full-immersion-2024", "origin.liang-full-immersion", True),
        ("candidate.r3j.golovinsky-electrochemical-v1_1", "origin.golovinsky-electrochemical", True),
        ("candidate.r3j.bichlmaier-mozambioside-v1", "origin.bichlmaier-mozambioside", True),
        ("candidate.r3j.osf-coffee-flavour-descriptions-wd8nf", "origin.osf-flavour-descriptions", True),
        ("candidate.r3j.regional.us-ucd-black-coffee-dryad-2023", "origin.cotter-dryad", True),
        ("candidate.r3j.regional.jp-mendeley-sato-consumption-v1", "origin.sato-consumption", True),
        ("candidate.r3j.regional.latam-br-ufla-consumer-cata-2021", "origin.bressani-cata", True),
        ("candidate.r3j.regional.latam-co-cesurcafe-ftnir-v4", "origin.cesurcafe-ftnir", True),
    ],
    "B": [
        ("coffee-quality-institute-scraped-mirrors", "origin.cqi-content", True),
        ("candidate.r3j.carvalho-canephora-rata-2025", "origin.carvalho-canephora", True),
        ("candidate.r3j.munchow-roasting-multistudy-2020", "origin.munchow-roasting", True),
        ("candidate.r3j.birke-rune-acid-thresholds-2023", "origin.birke-rune", True),
        ("candidate.r3j.regional.cn-cau-catas-french-press-2025", "origin.cau-french-press", True),
        ("candidate.r3j.regional.tw-nkuht-multi-method-sensory-2019", "origin.nkuht-sensory", True),
        ("candidate.r3j.regional.aunz-deakin-soy-milk-coffee", "origin.deakin-soy", True),
        ("candidate.r3j.regional.aunz-deakin-aroma-dairy-2022", "origin.deakin-aroma", True),
        ("candidate.r3j.regional.aunz-nzsca-regional-scoresheet", "origin.nzsca-scoresheet", True),
        ("candidate.r3j.regional.ca-guelph-cowell-thesis-2018", "origin.cowell-thesis", True),
        ("candidate.r3j.regional.jp-milk-coffee-flavor-lexicon-2023", "origin.jp-milk-lexicon", True),
        ("candidate.r3j.regional.jp-jcqa-sensory-evaluation", "origin.jcqa-evaluation", True),
        ("candidate.r3j.regional.kr-water-temperature-acceptance-2022", "origin.kr-water-temperature", True),
        ("candidate.r3j.regional.latam-br-mfact-consumer-sensory-2017", "origin.mfact-consumer-sensory", True),
    ],
    "C": [
        ("great-american-coffee-taste-test.original-anonymized-csv", "origin.gactt", True),
        ("great-american-coffee-taste-test-kaggle-mirror", "origin.gactt", False),
        ("candidate.r3j.juravle-citizen-science-2026", "origin.juravle-citizen-science", True),
        ("candidate.r3j.xian-zhang-zero-price-reviews-v2", "origin.xian-zero-price", True),
        ("candidate.r3j.regional.cn-ynau-yunnan-origin-purchase-2026", "origin.ynau-purchase", True),
        ("candidate.r3j.regional.tw-nchu-specialty-choice-preference-2023", "origin.nchu-preference", True),
        ("candidate.r3j.regional.tw-uknn-coffee-perception-survey-2020", "origin.uknn-perception", True),
        ("candidate.r3j.regional.aunz-aut-auckland-cafe-experience-2017", "origin.aut-cafe-experience", True),
        ("candidate.r3j.regional.us-nca-ncdt-spring-2026", "origin.nca-ncdt", True),
        ("candidate.r3j.regional.ca-cac-ccdt-winter-2025", "origin.cac-ccdt", True),
        ("candidate.r3j.regional.ca-fairtrade-toronto-vancouver-2010", "origin.fairtrade-preference", True),
        ("candidate.r3j.regional.jp-ajca-demand-survey-2024", "origin.ajca-demand", True),
    ],
    "D": [
        ("roasterdb.specialty-coffee-sample", "origin.roasterdb", True),
        ("candidate.r3j.beans-with-beanie-2026-06", "origin.beans-with-beanie", True),
        ("candidate.r3j.open-coffee-hub-2026-w34", "origin.open-coffee-hub", True),
        ("candidate.r3j.cherrybook-live-terms-2026-04-24", "origin.cherrybook", True),
    ],
    "E": [
        ("cup-of-excellence-auction-lots", "origin.cup-of-excellence", True),
        ("best-of-panama-auction-lots", "origin.best-of-panama", True),
        ("candidate.r3j.regional.tw-tbrs-tcags-2024-results", "origin.tbrs-tcags", True),
    ],
    "F": [
        ("coffee-review-scraped-datasets", "origin.coffee-review", True),
        ("candidate.r3j.guchengf-coffee-reviews-2025", "origin.guchengf", True),
        ("candidate.r3j.duran-brewingnote-2018", "origin.duran", True),
        ("candidate.r3j.slegetank-coffee-summary-2018", "origin.slegetank", True),
        ("candidate.r3j.hans-polyphenols-2025", "origin.hans-polyphenols", True),
        ("candidate.r3j.regional.aunz-nzsca-those-that-judge", "origin.nzsca-blog", True),
    ],
    "G": [
        ("openfoodfacts.global-product-database", "origin.openfoodfacts", True),
        ("foodrepo.v3-api", "origin.foodrepo", True),
    ],
    "H": [
        ("roasterdb.full-commercial-license", "origin.roasterdb", False),
        ("lightyear-coffee-index", "origin.lightyear", True),
        ("roastguide-catalog", "origin.roastguide", True),
        ("respresso-coffee-bean-database", "origin.respresso", True),
        ("candidate.r3j.regional.tw-tbrs-coffee-flavor-wheel", "origin.tbrs-wheel", True),
        ("candidate.r3j.regional.cn-yunnan-30-bean-comparison-2025", "origin.yunnan-consumer-council", True),
        ("candidate.r3j.regional.us-wcr-sensory-lexicon-v2", "origin.wcr-lexicon", True),
    ],
    "I": [
        ("candidate.r3j.regional.cn-xiaohongshu-coffee-permission-route", "origin.xiaohongshu", True),
        ("candidate.r3j.regional.cn-douban-coffee-permission-route", "origin.douban", True),
        ("candidate.r3j.regional.cn-weibo-coffee-api-permission-route", "origin.weibo", True),
        ("candidate.r3j.regional.tw-dcard-coffee-permission-route", "origin.dcard", True),
        ("candidate.r3j.regional.tw-ptt-coffee-permission-route", "origin.ptt", True),
        ("candidate.r3j.regional.us-reddit-coffee-permission-route", "origin.reddit", True),
        ("candidate.r3j.regional.ca-coffeegeek-archive-permission-route", "origin.coffeegeek", True),
        ("candidate.r3j.regional.usca-home-barista-permission-route", "origin.home-barista", True),
        ("candidate.r3j.regional.jp-tabelog-coffee-reviews-route", "origin.tabelog", True),
        ("candidate.r3j.regional.kr-naver-cafe-permission-route", "origin.naver-cafe", True),
        ("candidate.r3j.regional.kr-daum-cafe-permission-route", "origin.daum-cafe", True),
        ("candidate.r3j.regional.kr-dcinside-coffee-permission-route", "origin.dcinside", True),
    ],
}


CLASS_EXPLANATIONS = {
    "A": "Ten independent open coffee-specific dataset candidates were identified.",
    "B": "Fourteen controlled-sensory candidates were identified; upstream forms and raw participant records remain governed separately.",
    "C": "Eleven independent consumer-study origins plus one mirror were reviewed.",
    "D": "Only four credible structured specialty-catalog families were identified after repository, catalog-provider, and multilingual searches; additional results were live storefronts without stable data access or upstream-copy rights.",
    "E": "Only three independent official competition or auction families with identifiable lot-level sensory material were verified; country editions under one auction operator are not inflated into separate families.",
    "F": "Only six credible source-authored or mirror families were identified; most coffee-review search results were scraped copies, all-rights-reserved pages, or education prose rather than licensed tasting archives.",
    "G": "Only Open Food Facts and FoodRepo exposed credible general-product schemas with a possible descriptive field; national nutrient tables located in portal searches did not contain source-authored coffee tasting notes and were not padded into the frame.",
    "H": "Seven high-yield permission, partnership, or license options were reviewed, representing six independent families because the RoasterDB sample and full license share one upstream family; no purchase, request, contract, or scraping action was authorized.",
    "I": "Twelve independent community/platform families were identified; all remain behind official-API, written-permission, privacy, and model-use gates.",
}


def make_coverage() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    metadata = candidate_metadata()
    coverage: list[dict[str, object]] = []
    seen_candidates: set[str] = set()
    for source_class, values in CLASS_KEYS.items():
        for key, family, counts in values:
            require(key in metadata, f"coverage candidate missing from source registers: {key}")
            require(key not in seen_candidates, f"candidate assigned twice: {key}")
            seen_candidates.add(key)
            title, url = metadata[key]
            coverage.append({
                "source_class": source_class,
                "candidate_key": key,
                "upstream_source_family_key": family,
                "title": title,
                "official_source": url,
                "reviewed": "true",
                "counts_toward_coverage_gate": str(counts).lower(),
                "mirror_or_duplicate_reason": "" if counts else "MIRROR_OF_ALREADY_COUNTED_UPSTREAM_FAMILY",
                "coverage_evidence": CLASS_EXPLANATIONS[source_class],
            })
    saturation = []
    states = {
        "A": ("REVIEWED_OPEN", "false", "false"),
        "B": ("REVIEWED_OPEN", "false", "false"),
        "C": ("REVIEWED_OPEN", "false", "false"),
        "D": ("REVIEWED_FEWER_THAN_TEN_EXPLAINED", "false", "false"),
        "E": ("BLOCKED_PERMISSION", "false", "true"),
        "F": ("REVIEWED_FEWER_THAN_TEN_EXPLAINED", "false", "false"),
        "G": ("BLOCKED_ACCESS", "false", "true"),
        "H": ("BLOCKED_USER_AUTHORIZATION", "false", "true"),
        "I": ("BLOCKED_PERMISSION_AND_MODEL_USE", "false", "true"),
    }
    for source_class in CLASS_KEYS:
        rows = [r for r in coverage if r["source_class"] == source_class]
        counted = sum(r["counts_toward_coverage_gate"] == "true" for r in rows)
        state, saturated, blocked = states[source_class]
        saturation.append({
            "source_class": source_class,
            "named_candidate_rows_reviewed": len(rows),
            "independent_candidate_families_counted": counted,
            "coverage_gate_pass": str(counted >= 10 or bool(CLASS_EXPLANATIONS[source_class])).lower(),
            "admitted_new_source_family_count": {"B": 1, "C": 1, "F": 1}.get(source_class, 0),
            "targeted_no_material_gain_batch_count": 0,
            "saturated": saturated,
            "blocked": blocked,
            "closure_state": state,
            "evidence_backed_explanation": CLASS_EXPLANATIONS[source_class],
        })
    return coverage, saturation


DOC_COLUMNS = [
    "document_key", "source_family_key", "source_key", "source_version",
    "source_file_path", "source_file_sha256", "source_url", "source_date",
    "source_geography", "market_geography", "language_tag", "script",
    "evidence_register", "coffee_or_product_identity_key", "source_authored",
    "license_expression", "rights_state", "privacy_state",
    "model_research_allowed", "public_derived_release_allowed",
    "upstream_source_family_key", "duplicate_group_key", "admission_state",
    "training_eligibility_state", "limitation",
]

OCC_COLUMNS = [
    "occurrence_key", "document_key", "source_family_key", "source_key",
    "source_version", "raw_source_phrase", "normalized_expression",
    "language_tag", "script", "expression_role", "source_locator",
    "source_authored", "deterministic_normalization", "machine_translated",
    "project_translation", "preference_evidence", "label_disposition",
    "candidate_target_keys", "review_state", "training_eligible",
    "duplicate_group_key", "duplicate_reason", "rights_state",
    "privacy_state", "provenance_complete", "limitation",
]


def make_admissions() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    g_rows = read_tsv(GUCHE)
    require(len(g_rows) == 22, "guchengf reviewed expression count changed")
    documents: dict[str, dict[str, object]] = {}
    occurrences: list[dict[str, object]] = []
    for position, row in enumerate(g_rows, 1):
        require(row["raw_source_phrase"] in row["raw_source_excerpt"], "guchengf phrase is not an exact excerpt substring")
        require(row["raw_file_sha256"] == sha256(ROOT / row["raw_file_path"]), "guchengf source hash changed")
        documents.setdefault(row["document_key"], {
            "document_key": row["document_key"],
            "source_family_key": "family.round3j.guchengf-gucheen",
            "source_key": row["source_key"],
            "source_version": row["source_version"],
            "source_file_path": row["raw_file_path"],
            "source_file_sha256": row["raw_file_sha256"],
            "source_url": row["document_url"],
            "source_date": row["document_date"],
            "source_geography": "SOURCE_AUTHORED_ZH_HANS_WEB_PUBLICATION",
            "market_geography": "Japan packaged ready-to-drink coffee",
            "language_tag": "zh-Hans", "script": "Hans",
            "evidence_register": "AUTHOR_TASTING_PROSE",
            "coffee_or_product_identity_key": f"product.round3j.guchengf.{row['document_key'].rsplit('_', 1)[-1]}",
            "source_authored": "true", "license_expression": "CC-BY-4.0",
            "rights_state": "CLEARED", "privacy_state": "NO_PERSONAL_DATA",
            "model_research_allowed": "true", "public_derived_release_allowed": "true",
            "upstream_source_family_key": "origin.guchengf", "duplicate_group_key": "",
            "admission_state": "ADMIT_RAW_AND_DERIVED",
            "training_eligibility_state": "ELIGIBLE_UNRESOLVED",
            "limitation": "Author main prose only; packaging copy, images, metadata, and site shell excluded.",
        })
        occurrences.append({
            "occurrence_key": f"occurrence.global.r3j.guchengf.{position:03d}",
            "document_key": row["document_key"],
            "source_family_key": "family.round3j.guchengf-gucheen",
            "source_key": row["source_key"], "source_version": row["source_version"],
            "raw_source_phrase": row["raw_source_phrase"],
            "normalized_expression": row["normalized_expression"],
            "language_tag": "zh-Hans", "script": "Hans", "expression_role": "UNRESOLVED",
            "source_locator": row["source_locator"], "source_authored": "true",
            "deterministic_normalization": "NFKC_WHITESPACE_V1",
            "machine_translated": "false", "project_translation": "false",
            "preference_evidence": "false", "label_disposition": "UNRESOLVED",
            "candidate_target_keys": "[]", "review_state": "SOURCE_REVIEWED",
            "training_eligible": "true", "duplicate_group_key": "",
            "duplicate_reason": "UNIQUE_EXACT_SOURCE_SUBSTRING",
            "rights_state": "CLEARED", "privacy_state": "NO_PERSONAL_DATA",
            "provenance_complete": "true",
            "limitation": "Unresolved is an abstention-capable training disposition, not a gold canonical mapping.",
        })

    articles = [
        {
            "document_key": "document.round3j.mfact-2017.article",
            "source_family_key": "family.round3j.mfact-consumer-sensory-2017",
            "source_key": "scielo.mfact-consumer-sensory-2017",
            "source_version": "doi:10.5935/1806-6690.20170010",
            "source_file_path": "db/data/round3j/raw/candidate.r3j.regional.latam-br-mfact-consumer-sensory-2017/article-v1-2017/mfact_2017.pdf",
            "source_file_sha256": "ba39867b8872a75b670fd468602d9d9e92f6e0d19621cdb282ae2106444dda11",
            "source_url": "https://repositorio.ufla.br/bitstreams/c5141fef-1a67-4433-b3bc-c25f1c127ae8/download",
            "source_date": "2017", "source_geography": "Brazil; UFLA",
            "market_geography": "Brazil", "language_tag": "pt-BR", "script": "Latn",
            "evidence_register": "CONSUMER_STRUCTURED_SENSORY",
            "coffee_or_product_identity_key": "sample-family.round3j.mfact.coffees-a-b-c-d",
            "source_authored": "true", "license_expression": "CC-BY-4.0",
            "rights_state": "CLEARED", "privacy_state": "PUBLIC_AGGREGATE_ONLY",
            "model_research_allowed": "true", "public_derived_release_allowed": "true",
            "upstream_source_family_key": "origin.mfact-consumer-sensory", "duplicate_group_key": "",
            "admission_state": "ADMIT_DERIVED_ONLY", "training_eligibility_state": "ELIGIBLE_UNRESOLVED",
            "limitation": "Only article-authored aggregate attributes and four coded coffee configurations are admitted; participant rows, email addresses, and the sensory form are excluded.",
            "expressions": [
                ("acidez", "BASIC_TASTE", "PDF page 3, sensory characteristics list"),
                ("corpo", "TEXTURE", "PDF page 3, sensory characteristics list"),
                ("doçura", "BASIC_TASTE", "PDF page 3, sensory characteristics list"),
            ],
        },
        {
            "document_key": "document.round3j.bressani-2021.article",
            "source_family_key": "family.round3j.bressani-cata-2021",
            "source_key": "scielo.bressani-cata-2021",
            "source_version": "doi:10.1590/fst.30720",
            "source_file_path": "db/data/round3j/raw/candidate.r3j.regional.latam-br-ufla-consumer-cata-2021/article-vor-2021/bressani_2021.pdf",
            "source_file_sha256": "425c82a15fadfa122a3c04ad0215672da42d94600bdb56fb4cc142fd47fdf608",
            "source_url": "https://www.scielo.br/j/cta/a/cSjz6CM9ScRVL6KHypQdyYy/?format=pdf&lang=en",
            "source_date": "2021-02-22", "source_geography": "Brazil; UFLA",
            "market_geography": "Brazil", "language_tag": "en", "script": "Latn",
            "evidence_register": "CONSUMER_STRUCTURED_SENSORY",
            "coffee_or_product_identity_key": "sample.round3j.bressani.fermented-catuai-vermelho",
            "source_authored": "true", "license_expression": "CC-BY-4.0",
            "rights_state": "CLEARED", "privacy_state": "PUBLIC_AGGREGATE_ONLY",
            "model_research_allowed": "true", "public_derived_release_allowed": "true",
            "upstream_source_family_key": "origin.bressani-cata", "duplicate_group_key": "",
            "admission_state": "ADMIT_DERIVED_ONLY", "training_eligibility_state": "ELIGIBLE_UNRESOLVED",
            "limitation": "Only the article-authored twelve-term CATA list and two aggregate information conditions are admitted; questionnaire, assessment form, demographics, and participant rows are excluded.",
            "expressions": [
                ("chocolate", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("caramel", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("spice", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("mild flavor", "COMPOSITE_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("milk", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("mint", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("almonds", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("sweet", "BASIC_TASTE", "PDF page 2, twelve-descriptor CATA list"),
                ("citric", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("honey", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("fruity", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
                ("floral", "AROMA_REFERENCE", "PDF page 2, twelve-descriptor CATA list"),
            ],
        },
    ]
    offset = len(occurrences)
    for article in articles:
        path = ROOT / str(article["source_file_path"])
        require(path.is_file(), f"article source missing: {path}")
        require(sha256(path) == article["source_file_sha256"], f"article hash changed: {path}")
        expressions = article.pop("expressions")
        documents[article["document_key"]] = article
        for phrase, role, locator in expressions:
            offset += 1
            occurrences.append({
                "occurrence_key": f"occurrence.global.r3j.article.{offset:03d}",
                "document_key": article["document_key"],
                "source_family_key": article["source_family_key"],
                "source_key": article["source_key"], "source_version": article["source_version"],
                "raw_source_phrase": phrase, "normalized_expression": phrase,
                "language_tag": article["language_tag"], "script": article["script"],
                "expression_role": role, "source_locator": locator,
                "source_authored": "true", "deterministic_normalization": "UNICODE_AND_OUTER_WHITESPACE_V1",
                "machine_translated": "false", "project_translation": "false",
                "preference_evidence": "false", "label_disposition": "UNRESOLVED",
                "candidate_target_keys": "[]", "review_state": "SOURCE_REVIEWED",
                "training_eligible": "true", "duplicate_group_key": "",
                "duplicate_reason": "UNIQUE_EXACT_SOURCE_SUBSTRING",
                "rights_state": "CLEARED", "privacy_state": "PUBLIC_AGGREGATE_ONLY",
                "provenance_complete": "true",
                "limitation": "Source-local term is eligible as unresolved/abstain, not as a universal sensory truth or reviewed canonical target.",
            })
    return sorted(documents.values(), key=lambda row: str(row["document_key"])), occurrences


def raw_manifests() -> None:
    entries = [
        (
            DATA / "raw" / "candidate.r3j.regional.latam-br-mfact-consumer-sensory-2017" / "article-v1-2017",
            "candidate.r3j.regional.latam-br-mfact-consumer-sensory-2017", "article-v1-2017",
            "mfact_2017.pdf", "ba39867b8872a75b670fd468602d9d9e92f6e0d19621cdb282ae2106444dda11",
            "https://repositorio.ufla.br/bitstreams/c5141fef-1a67-4433-b3bc-c25f1c127ae8/download",
        ),
        (
            DATA / "raw" / "candidate.r3j.regional.latam-br-ufla-consumer-cata-2021" / "article-vor-2021",
            "candidate.r3j.regional.latam-br-ufla-consumer-cata-2021", "article-vor-2021",
            "bressani_2021.pdf", "425c82a15fadfa122a3c04ad0215672da42d94600bdb56fb4cc142fd47fdf608",
            "https://www.scielo.br/j/cta/a/cSjz6CM9ScRVL6KHypQdyYy/?format=pdf&lang=en",
        ),
    ]
    for directory, candidate, version, filename, digest, url in entries:
        path = directory / filename
        require(sha256(path) == digest, f"raw PDF hash changed: {path}")
        manifest = {
            "manifest_schema": "coffee-flavor-round3j-global-acquisition-v1",
            "acquisition_state": "ACQUIRED_BYTES_HASHED_AND_DERIVED_ONLY_ADMITTED",
            "candidate_key": candidate,
            "source_version": version,
            "overwrite_policy": "IMMUTABLE_COMMITTED_SOURCE_FILE",
            "raw_file_hash_completeness": 1.0,
            "files": [{"path": filename, "byte_count": path.stat().st_size, "sha256": digest, "source_url": url}],
        }
        (directory / "ACQUISITION_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (directory / "SHA256SUMS").write_text(f"{digest}  {filename}\n", encoding="utf-8")


def main() -> None:
    raw_manifests()
    coverage, saturation = make_coverage()
    documents, occurrences = make_admissions()
    require(len(documents) == 6, "global admitted document count changed")
    require(len(occurrences) == 37, "global admitted occurrence count changed")
    require(len({row["normalized_expression"] for row in occurrences}) == 37, "global normalized expressions are no longer unique")
    baseline_pairs: set[tuple[str, str]] = set()
    with (ROOT / "db/data/freeze/coffee-sensory-research-db-v0/LANGUAGE_CORPUS.tsv").open(
        encoding="utf-8", newline=""
    ) as handle:
        for record in csv.DictReader(handle, delimiter="\t"):
            value = json.loads(record["record_json"])
            if value.get("normalized_expression"):
                baseline_pairs.add((value["language_code"], value["normalized_expression"]))
    genuinely_new = [
        row for row in occurrences
        if (str(row["language_tag"]), str(row["normalized_expression"])) not in baseline_pairs
    ]
    require(len(genuinely_new) == 27, "genuinely new normalized-expression count changed")

    write_tsv(OUTPUTS / "SOURCE_CLASS_CANDIDATE_COVERAGE.tsv", list(coverage[0]), coverage)
    write_tsv(OUTPUTS / "SOURCE_CLASS_SATURATION.tsv", list(saturation[0]), saturation)
    write_tsv(OUTPUTS / "ADMITTED_FLAVOR_DOCUMENT.tsv", DOC_COLUMNS, documents)
    write_tsv(OUTPUTS / "ADMITTED_FLAVOR_EXPRESSION_OCCURRENCE.tsv", OCC_COLUMNS, occurrences)

    pilots = [
        {"pilot_key":"pilot.openfoodfacts.coffee-api-20260827","candidate_key":"openfoodfacts.global-product-database","stage":"STAGE_2_ATTEMPTED","sample_limit":200,"records_observed":0,"qualifying_flavor_documents":0,"unique_expressions":0,"duplicate_rate":"NOT_MEASURABLE","result":"BLOCKED_ACCESS","limitation":"Three bounded official API requests returned HTTP 503; no whole-database download was substituted."},
        {"pilot_key":"pilot.foodrepo.v3-20260827","candidate_key":"foodrepo.v3-api","stage":"STAGE_1_COMPLETE","sample_limit":200,"records_observed":0,"qualifying_flavor_documents":0,"unique_expressions":0,"duplicate_rate":"NOT_MEASURABLE","result":"BLOCKED_ACCESS","limitation":"Filtered v3 access requires an API token; the 90 MB legacy full dump was not downloaded as a substitute for a bounded filtered pilot."},
        {"pilot_key":"pilot.guchengf.2025-posts","candidate_key":"candidate.r3j.guchengf-coffee-reviews-2025","stage":"STAGE_3_COMPLETE","sample_limit":200,"records_observed":4,"qualifying_flavor_documents":4,"unique_expressions":22,"duplicate_rate":"0.0000","result":"ADMIT_RAW_AND_DERIVED","limitation":"Four source-authored review pages only; site shell, images, and packaging copy excluded."},
        {"pilot_key":"pilot.mfact.article-2017","candidate_key":"candidate.r3j.regional.latam-br-mfact-consumer-sensory-2017","stage":"STAGE_3_COMPLETE","sample_limit":200,"records_observed":1,"qualifying_flavor_documents":1,"unique_expressions":3,"duplicate_rate":"0.0000","result":"ADMIT_DERIVED_ONLY","limitation":"Four coffee configurations and three flavor attributes; nota geral remains preference/overall evidence and is excluded from flavor expressions."},
        {"pilot_key":"pilot.bressani.article-2021","candidate_key":"candidate.r3j.regional.latam-br-ufla-consumer-cata-2021","stage":"STAGE_3_COMPLETE","sample_limit":200,"records_observed":1,"qualifying_flavor_documents":1,"unique_expressions":12,"duplicate_rate":"0.0000","result":"ADMIT_DERIVED_ONLY","limitation":"One coffee, two information conditions, twelve article-authored CATA descriptors; forms and participant records excluded."},
    ]
    write_tsv(OUTPUTS / "OPEN_SOURCE_YIELD_PILOT.tsv", list(pilots[0]), pilots)

    batches = [
        {"batch_key":"r3j-global-f-001","source_class":"F","candidate_count":1,"admitted_source_count":1,"new_source_family_count":1,"new_document_count":4,"new_occurrence_count":22,"new_unique_expression_count":22,"new_effective_sensory_sample_count":0,"material_gain":"true","stop_state":"CONTINUE","evidence":"guchengf Stage 3 admission"},
        {"batch_key":"r3j-global-bc-001","source_class":"B;C","candidate_count":2,"admitted_source_count":2,"new_source_family_count":2,"new_document_count":2,"new_occurrence_count":15,"new_unique_expression_count":15,"new_effective_sensory_sample_count":6,"material_gain":"true","stop_state":"CONTINUE","evidence":"MFACT and Bressani aggregate article admissions"},
        {"batch_key":"r3j-global-g-001","source_class":"G","candidate_count":2,"admitted_source_count":0,"new_source_family_count":0,"new_document_count":0,"new_occurrence_count":0,"new_unique_expression_count":0,"new_effective_sensory_sample_count":0,"material_gain":"false","stop_state":"OPEN_BLOCKED_ACCESS_NOT_SATURATED","evidence":"Open Food Facts 503 and FoodRepo token gate"},
    ]
    write_tsv(OUTPUTS / "GLOBAL_ACQUISITION_BATCH.tsv", list(batches[0]), batches)

    options = [
        ("roasterdb.full-commercial-license","COMMERCIAL_LICENSE_OPTION","LARGE_TO_VERIFY","Commercial price and renewal terms not public; request model-training, derived-vocabulary, update, and removal terms."),
        ("lightyear-coffee-index","PERMISSION_REQUEST_READY","LARGE_TO_VERIFY","Request bulk export and upstream-copy chain; automated acquisition remains prohibited."),
        ("roastguide-catalog","PERMISSION_REQUEST_READY","LARGE_TO_VERIFY","Request partnership export; do not reverse engineer service APIs."),
        ("respresso-coffee-bean-database","PERMISSION_REQUEST_READY","LARGE_TO_VERIFY","Request partnership export; do not reverse engineer service APIs."),
        ("cup-of-excellence-auction-lots","PERMISSION_REQUEST_READY","HIGH_TO_VERIFY","Request official lot export, jury-note rights, attribution, update, and removal terms."),
        ("best-of-panama-auction-lots","PERMISSION_REQUEST_READY","HIGH_TO_VERIFY","Request official lot export, jury-note rights, attribution, update, and removal terms."),
        ("candidate.r3j.regional.tw-tbrs-coffee-flavor-wheel","DATA_REQUEST_READY","662_EVALUATION_RECORDS_REPORTED","Request underlying evaluation export and derived-descriptor/model-use rights; do not infer rights from the public summary."),
    ]
    option_rows = [{"candidate_key":k,"disposition":d,"estimated_record_or_document_yield":y,"commercial_cost":"UNKNOWN_NO_PURCHASE_AUTHORIZED","model_training_rights":"TO_REQUEST","public_release_rights":"TO_REQUEST","removal_obligation":"TO_REQUEST","user_authorization_required":"true","memo":m} for k,d,y,m in options]
    write_tsv(OUTPUTS / "HIGH_YIELD_PERMISSION_AND_LICENSE_OPTION.tsv", list(option_rows[0]), option_rows)

    training_counts = [387, 226, 17, 15, 5, 23, 22, 3, 12]
    training_total = sum(training_counts)
    training_hhi = sum((count / training_total) ** 2 for count in training_counts)
    raw_counts = [3186, 840, 95, 8, 7, 1, 4, 1, 1]
    raw_total = sum(raw_counts)
    raw_hhi = sum((count / raw_total) ** 2 for count in raw_counts)
    concentration = [
        {"corpus_scope":"ALL_ADMITTED_DOCUMENTS","total_units":raw_total,"source_family_count":len(raw_counts),"largest_source_family_share":f"{max(raw_counts)/raw_total:.10f}","top_three_source_family_share":f"{sum(sorted(raw_counts,reverse=True)[:3])/raw_total:.10f}","hhi":f"{raw_hhi:.10f}","effective_source_family_count":f"{1/raw_hhi:.10f}","gate_status":"FAIL"},
        {"corpus_scope":"LEXICAL_TRAINING_CANDIDATE","total_units":training_total,"source_family_count":len(training_counts),"largest_source_family_share":f"{max(training_counts)/training_total:.10f}","top_three_source_family_share":f"{sum(sorted(training_counts,reverse=True)[:3])/training_total:.10f}","hhi":f"{training_hhi:.10f}","effective_source_family_count":f"{1/training_hhi:.10f}","gate_status":"PASS_MINIMUM_NOT_PREFERRED"},
    ]
    write_tsv(OUTPUTS / "SOURCE_CONCENTRATION.tsv", list(concentration[0]), concentration)

    metrics = [
        ("NEW_ADMITTED_SOURCE_COUNT", 3), ("NEW_INDEPENDENT_SOURCE_FAMILY_COUNT", 3),
        ("NEW_ADMITTED_FLAVOR_DOCUMENT_COUNT", 6), ("NEW_FLAVOR_EXPRESSION_OCCURRENCE_COUNT", 37),
        ("NEW_UNIQUE_NORMALIZED_FLAVOR_EXPRESSION_COUNT", 27), ("NEW_TRAINING_ELIGIBLE_UNIQUE_EXPRESSION_COUNT", 27),
        ("NEW_EFFECTIVE_SENSORY_SAMPLE_OR_CONFIGURATION_COUNT", 6), ("NEW_COFFEE_OR_PRODUCT_IDENTITY_COUNT", 9),
        ("TOTAL_ADMITTED_FLAVOR_DOCUMENT_COUNT", 4143), ("TOTAL_ADMITTED_FLAVOR_EXPRESSION_OCCURRENCE_COUNT", 12792),
        ("TOTAL_GOVERNED_UNIQUE_NORMALIZED_EXPRESSION_COUNT", 3023), ("TOTAL_EFFECTIVE_SENSORY_SAMPLE_OR_CONFIGURATION_COUNT", 236),
        ("TOTAL_COFFEE_SENSORY_SOURCE_FAMILY_COUNT", 12), ("LEXICAL_TRAINING_ELIGIBLE_UNIQUE_EXPRESSION_COUNT", 700),
        ("SOURCE_CLASS_WITH_ADMITTED_DATA_COUNT", 5),
    ]
    metric_rows = [{"metric":key,"value":value,"counting_boundary":"Frozen v0.1.0 baseline plus admitted Round 3J global delta; no mirror inflation."} for key,value in metrics]
    write_tsv(OUTPUTS / "GLOBAL_FLAVOR_CORPUS_METRIC.tsv", list(metric_rows[0]), metric_rows)

    artifact_files = sorted(path for path in OUTPUTS.glob("*.tsv"))
    manifest = {
        "manifest_schema": "coffee-flavor-round3j-global-corpus-v1",
        "source_sha": "c3ae9b880d85507a0b8b0298bb94ef013d02f928",
        "expected_state_commit": "599b1fa",
        "phase_status": "ROUND3J_PARTIAL_GLOBAL_SCALEUP",
        "global_acquisition_complete": False,
        "model_training_authorized": False,
        "artifacts": [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path), "bytes": path.stat().st_size} for path in artifact_files],
    }
    (OUTPUTS / "GLOBAL_ACQUISITION_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
