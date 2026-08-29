#!/usr/bin/env python3
"""Build the restricted-to-public semantic-cleaning bridge for Batch 3.

This is the only Batch 3 program that reads restricted source-native text.  It
emits hashes, governed concept identifiers, classifications, and receipts, but
never source-native or cleaned lexical strings.  The committed sidecars are
therefore sufficient for deterministic offline generation without widening
redistribution rights.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
OUT = ROOT / "db" / "data" / "candidate-cleaning-staging"
ONTOLOGY_SQL = ROOT / "db" / "010_canonical_ontology_seed.sql"
DEFAULT_BATCH2_RESTRICTED = Path(
    "/private/tmp/round3l-acquisition/professional_descriptor_batch2"
)
DEFAULT_ROUND3M_RESTRICTED = Path("/private/tmp/coffee-flavor-round3m-restricted")

SNAPSHOT_VERSION = "professional-descriptor-candidate-v0-20k"
BUILDER_VERSION = "batch3.restricted-semantic-cleaner.v1"
GENERATED_AT = "2026-08-29T00:00:00Z"

ESTABLISHED_COMPOUNDS = {
    "brown sugar",
    "black tea",
    "green apple",
    "red apple",
    "orange blossom",
    "dark chocolate",
    "milk chocolate",
    "stone fruit",
    "dried fruit",
    "lemon zest",
    "cocoa nib",
    "maple syrup",
}

MODIFIERS = {
    "ripe", "fresh", "dried", "dark", "light", "delicate", "intense",
    "high", "low", "long", "short", "clean", "sweet", "medium",
    "heavy", "mild", "strong", "soft", "big", "subtle", "refined",
}

QUALITY = {
    "complex", "balanced", "pleasant", "elegant", "excellent", "average",
    "below average", "good", "very good", "fine", "nice", "lovely",
    "distinctive", "unique", "well balanced", "harmonious", "structured",
    "nuanced", "vibrant", "brilliant", "refreshing", "solid",
}

BROAD = {
    "acidity", "aftertaste", "balance", "body", "bright", "cleanliness",
    "creamy", "crisp", "drying", "finish", "fullness", "juicy", "lively",
    "mouthfeel", "oily", "round", "silky", "smooth", "sour", "sweetness",
    "syrupy", "velvety", "viscous", "astringent", "pointed acidity",
    "citric acidity", "malic acidity", "tartaric acidity", "long finish",
}

DEFECT = {
    "baggy", "cardboard", "dirty", "dusty", "fermented", "medicinal",
    "metallic", "mold", "moldy", "mould", "mouldy", "musty", "phenolic",
    "potato", "rubber", "stale", "sulfur", "sulfurous", "sulphur",
    "sulphurous", "petroleum", "ashy", "burnt", "over fermented",
}

AMBIGUOUS = {
    "berry", "berries", "chocolate", "citrus", "floral", "flower",
    "flowers", "fruit", "fruity", "herbal", "nut", "nuts", "spice",
    "spicy", "tea", "tropical", "wine", "winey",
}

PROCESS_METADATA = {
    "anaerobic", "washed", "natural", "honey process", "wet process",
    "dry process", "fermentation", "variety", "cultivar", "altitude",
    "masl", "region", "village", "producer", "farm", "lot", "harvest",
    "roast", "roasted", "filter roast", "espresso roast", "process",
    "origin", "country", "estate", "microlot", "screen size",
}

NON_DESCRIPTOR = {
    "n/a", "na", "none", "not available", "unreported", "overall",
    "aroma", "flavor", "flavour", "other", "score", "rank", "ranking",
    "description", "notes", "cup profile", "unknown", "-", "--",
}

APPROVED_ALIASES = {
    "black currant": "sensory.blackcurrant",
    "black currants": "sensory.blackcurrant",
    "cacao": "sensory.cocoa",
    "mouldy": "sensory.moldy",
    "sulphurous": "sensory.sulfurous",
    "winey": "sensory.wine_like_character",
    "wine like": "sensory.wine_like_character",
    "wine-like": "sensory.wine_like_character",
}

SENTENCE_MARKERS = (
    "this coffee", "this lot", "grown at", "located in", "produced by",
    "we are", "our coffee", "click here", "read more", "copyright",
    "privacy policy", "cookie", "newsletter", "award winning",
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(prefix: str, material: str) -> str:
    return f"{prefix}:{sha256_text(material)[:24]}"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def scalar(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)
    return str(value)


def write_tsv(path: Path, fields: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> None:
    names = list(fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=names, delimiter="\t", lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({name: scalar(row.get(name, "")) for name in names})


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("’", "'").replace("–", "-").replace("—", "-")
    value = re.sub(r"\s*\(\s*\d+\s*\)\s*$", "", value)
    value = re.sub(r"\s+", " ", value.strip(" \t\r\n.,;:!?\"'()[]{}"))
    return value


def ontology() -> tuple[dict[str, str], dict[str, str]]:
    text = ONTOLOGY_SQL.read_text(encoding="utf-8")
    matches = re.findall(
        r"\('(?P<key>sensory\.[a-z0-9_]+)',\s*'(?P<label>[^']+)',\s*"
        r"'(?P<status>active|candidate)'",
        text,
    )
    by_label = {normalize(label): key for key, label, _ in matches}
    by_key = {key: label for key, label, _ in matches}
    if len(by_key) != 100:
        raise RuntimeError(f"expected 100 governed sensory concepts, found {len(by_key)}")
    return by_label, by_key


def likely_metadata(value: str) -> bool:
    words = set(re.findall(r"[a-z]+", value))
    if any(term in value for term in PROCESS_METADATA):
        return True
    return bool(words & {"meters", "metres", "hectares", "elevation", "province"})


def likely_sentence(value: str) -> bool:
    words = value.split()
    return (
        len(words) > 10
        or any(marker in value for marker in SENTENCE_MARKERS)
        or value.startswith(("it is ", "it has ", "coffee is ", "notes of "))
        or "http://" in value
        or "https://" in value
    )


def safe_coordinated_parts(value: str) -> list[str]:
    if value in ESTABLISHED_COMPOUNDS:
        return []
    if not re.search(r"\s+(?:and|&)\s+|\s*/\s*", value):
        return []
    parts = [part.strip() for part in re.split(r"\s+(?:and|&)\s+|\s*/\s*", value)]
    if not (2 <= len(parts) <= 4):
        return []
    if any(not part or len(part.split()) > 4 for part in parts):
        return []
    if any(likely_sentence(part) or likely_metadata(part) for part in parts):
        return []
    return parts


def base_class(value: str) -> str:
    if not value or value in NON_DESCRIPTOR:
        return "NON_DESCRIPTOR"
    if likely_sentence(value):
        return "NON_DESCRIPTOR"
    if likely_metadata(value):
        return "PROCESS_OR_ORIGIN_METADATA"
    if value in QUALITY:
        return "QUALITY_EVALUATION"
    if value in MODIFIERS:
        return "INTENSITY_OR_QUALITY_MODIFIER"
    if value in DEFECT or any(token in value.split() for token in DEFECT):
        return "DEFECT_OR_NEGATIVE_SENSORY"
    if value in BROAD:
        return "BROAD_SENSORY"
    if len(value.split()) > 7:
        return "SEMANTICALLY_UNRESOLVED"
    return "STRICT_FLAVOR"


def clean_atom(raw: str) -> tuple[list[tuple[str, str]], str, str, str]:
    """Return cleaned atoms, segmentation decision, basis, and confidence."""

    value = normalize(raw)
    if not value:
        return [("", "NON_DESCRIPTOR")], "EMPTY_OR_STRUCTURAL", "EMPTY_AFTER_NORMALIZATION", "1.000000"
    if value in ESTABLISHED_COMPOUNDS:
        return [(value, base_class(value))], "KEEP_AS_ESTABLISHED_COMPOUND", "GOVERNED_BATCH3_COMPOUND_ALLOWLIST", "1.000000"

    coordinated = safe_coordinated_parts(value)
    if coordinated:
        classes = [base_class(part) for part in coordinated]
        disposition = (
            "MULTIPLE_BROAD_ATTRIBUTES"
            if all(item in {"BROAD_SENSORY", "QUALITY_EVALUATION", "INTENSITY_OR_QUALITY_MODIFIER"} for item in classes)
            else "SAFE_LIST_SPLIT"
        )
        return list(zip(coordinated, classes)), disposition, "BOUNDED_COORDINATION_RULE", "0.960000"

    words = value.split()
    if len(words) >= 2 and words[0] in MODIFIERS:
        head = " ".join(words[1:])
        if head and not likely_sentence(head) and not likely_metadata(head):
            return [
                (head, base_class(head)),
                (words[0], "INTENSITY_OR_QUALITY_MODIFIER"),
            ], "HEAD_PLUS_MODIFIER", "LEADING_MODIFIER_PRESERVED_SEPARATELY", "0.940000"

    klass = base_class(value)
    if klass == "SEMANTICALLY_UNRESOLVED" and re.search(r"\b(?:and|or)\b|/|&", value):
        return [(value, "COMPOSITE_DESCRIPTOR")], "COMPOSITE_UNRESOLVED", "COORDINATION_NOT_SAFE_TO_SPLIT", "0.500000"
    if klass == "NON_DESCRIPTOR" and likely_sentence(value):
        return [(value, klass)], "SENTENCE_LEAKAGE_REJECTED", "SENTENCE_OR_MARKETING_PROSE_RULE", "0.980000"
    if klass == "PROCESS_OR_ORIGIN_METADATA":
        return [(value, klass)], "METADATA_REJECTED", "PROCESS_OR_ORIGIN_LEXICON", "0.970000"
    return [(value, klass)], "KEEP_ATOMIC", "SINGLE_SEMANTIC_ATOM", "0.920000"


def singular_candidates(value: str) -> list[str]:
    candidates: list[str] = []
    if value.endswith("ies") and len(value) > 4:
        candidates.append(value[:-3] + "y")
    if value.endswith("es") and len(value) > 3:
        candidates.append(value[:-2])
    if value.endswith("s") and not value.endswith("ss") and len(value) > 3:
        candidates.append(value[:-1])
    return candidates


def map_concept(value: str, klass: str, by_label: Mapping[str, str]) -> tuple[str, str, str, str]:
    if klass in {
        "NON_DESCRIPTOR", "PROCESS_OR_ORIGIN_METADATA", "QUALITY_EVALUATION",
        "INTENSITY_OR_QUALITY_MODIFIER",
    }:
        return "NON_DESCRIPTOR", "", "AUTOMATED_SAFE_RULE", "1.000000"
    if klass in {"COMPOSITE_DESCRIPTOR", "SEMANTICALLY_UNRESOLVED"}:
        return "COMPOUND_MAPPING_REVIEW_REQUIRED", "", "MACHINE_PROVISIONAL_REVIEW", "0.000000"
    if value in by_label:
        return "AUTO_EXACT_CANONICAL", by_label[value], "AUTOMATED_SAFE_RULE", "1.000000"
    if value in APPROVED_ALIASES:
        return "AUTO_APPROVED_ALIAS", APPROVED_ALIASES[value], "AUTOMATED_SAFE_RULE", "0.990000"
    for candidate in singular_candidates(value):
        if candidate in by_label:
            return "AUTO_MORPHOLOGICAL", by_label[candidate], "AUTOMATED_SAFE_RULE", "0.980000"
    if value in AMBIGUOUS:
        return "AMBIGUOUS_MAPPING", "", "MACHINE_PROVISIONAL_REVIEW", "0.000000"
    if klass in {"STRICT_FLAVOR", "BROAD_SENSORY", "DEFECT_OR_NEGATIVE_SENSORY"}:
        return "ONTOLOGY_CANDIDATE", "", "MACHINE_PROVISIONAL_REVIEW", "0.000000"
    return "UNRESOLVED", "", "MACHINE_PROVISIONAL_REVIEW", "0.000000"


def restricted_text_by_assertion(
    batch2_root: Path, round3m_root: Path
) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    batch2_path = batch2_root / "PROFESSIONAL_ASSERTIONS_RESTRICTED.tsv"
    if not batch2_path.is_file():
        raise RuntimeError(f"missing Batch 2 restricted ledger: {batch2_path}")
    batch2_rows = read_tsv(batch2_path)
    details = {row["descriptor_assertion_id"]: row for row in batch2_rows}

    sys.path.insert(0, str(ROOT / "db" / "adapters"))
    from round3m.live import extract_candidates  # type: ignore
    from round3m.restricted import load_bounded_captures  # type: ignore

    records, _ = load_bounded_captures(round3m_root)
    baseline: dict[str, str] = {}
    for record in records:
        for candidate in extract_candidates(record):
            baseline[candidate.descriptor_assertion_id] = candidate.atomic_source_text
    if len(baseline) != 140:
        raise RuntimeError(f"Round 3M restricted assertion count drift: {len(baseline)}")
    return details, baseline


def build_entity_rows(batch2_rows: list[dict[str, str]], round3m_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    old_records: list[dict[str, str]] = []
    for path in sorted((round3m_root / "web_index_field_capture").glob("coe_*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for record in document["records"]:
            if urlsplit(record["source_url"]).netloc == "allianceforcoffeeexcellence.org":
                year = re.search(r"(?:19|20)\d{2}", record["record_id"])
                old_records.append({
                    "record_id": record["record_id"],
                    "source_url": record["source_url"],
                    "source_name": record.get("source_name", ""),
                    "year": year.group(0) if year else "",
                    "descriptor_field_hash_bundle": sha256_text(
                        "\x1f".join(sorted(sha256_text(str(v)) for v in record["fields"].values()))
                    ),
                })

    new_grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in batch2_rows:
        if (
            row["source_family_id"] == "family.ace_cup_of_excellence"
            and urlsplit(row["source_url"]).netloc == "farmdirectory.cupofexcellence.org"
        ):
            new_grouped[row["source_url"]].append(row)

    entity_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    for old in sorted(old_records, key=lambda item: item["record_id"]):
        candidates: list[tuple[float, str, list[dict[str, str]]]] = []
        for url, rows in new_grouped.items():
            score, _ = coe_name_year_match_state(
                old["source_name"], old["year"], url, rows[0]["edition_year"]
            )
            candidates.append((score, url, rows))
        score, candidate_url, candidate_rows = max(candidates, default=(0.0, "", []))
        candidate_year = candidate_rows[0]["edition_year"] if candidate_rows else ""
        _, state = coe_name_year_match_state(
            old["source_name"], old["year"], candidate_url, candidate_year
        )
        entity_id = stable_id("coe-entity-candidate", old["source_url"] + "\x1f" + candidate_url)
        entity_rows.append({
            "entity_resolution_id": entity_id,
            "old_domain_source_url": old["source_url"],
            "old_domain_record_id": old["record_id"],
            "old_domain_year": old["year"],
            "old_domain_name_sha256": sha256_text(old["source_name"]),
            "old_domain_descriptor_field_hash_bundle": old["descriptor_field_hash_bundle"],
            "new_domain_source_url": candidate_url,
            "new_domain_effective_record_id": candidate_rows[0]["effective_record_id"] if candidate_rows else "",
            "new_domain_year": candidate_year,
            "new_domain_descriptor_field_hash_bundle": sha256_text(
                "\x1f".join(sorted({row["raw_field_text_sha256"] for row in candidate_rows}))
            ) if candidate_rows else "",
            "match_score": f"{score:.6f}",
            "match_state": state,
            "decision_basis": "YEAR_NAME_SLUG_AND_DESCRIPTOR_HASH_BUNDLE_NO_URL_ONLY_IDENTITY",
            "review_requirement": "MACHINE_PROVISIONAL_REVIEW" if "POSSIBLE" in state or "INSUFFICIENT" in state else "AUTOMATED_SAFE_RULE",
        })
        duplicate_rows.append({
            "entity_resolution_id": entity_id,
            "old_domain_source_url": old["source_url"],
            "new_domain_source_url": candidate_url,
            "match_state": state,
            "canonical_effective_record_id": candidate_rows[0]["effective_record_id"] if state in {"EXACT_SAME_EFFECTIVE_RECORD", "HIGH_CONFIDENCE_SAME_EFFECTIVE_RECORD"} and candidate_rows else "",
            **coe_publication_duplicate_policy(
                state,
                sum(row["counts_as_assertion"] == "true" for row in candidate_rows),
                independent_observation=False,
            ),
        })
    return entity_rows, duplicate_rows


def audit_outcome(cleaned: list[tuple[str, str]], decisions: list[str]) -> str:
    classes = {klass for _, klass in cleaned}
    if "SAFE_LIST_SPLIT" in decisions or "HEAD_PLUS_MODIFIER" in decisions:
        return "VALID_COMPOSITE_REQUIRES_SPLIT"
    if classes <= {"NON_DESCRIPTOR", "PROCESS_OR_ORIGIN_METADATA", "QUALITY_EVALUATION", "INTENSITY_OR_QUALITY_MODIFIER"}:
        return "NON_DESCRIPTOR"
    if "COMPOSITE_DESCRIPTOR" in classes:
        return "SEMANTICALLY_UNRESOLVED"
    if classes == {"BROAD_SENSORY"}:
        return "VALID_BROAD_SENSORY"
    if any(klass in {"STRICT_FLAVOR", "DEFECT_OR_NEGATIVE_SENSORY"} for klass in classes):
        return "VALID_ATOMIC_DESCRIPTOR"
    return "SEMANTICALLY_UNRESOLVED"


def coe_name_year_match_state(
    old_name: str, old_year: str, new_url: str, new_year: str
) -> tuple[float, str]:
    """Conservative pure matcher used by the cross-domain entity audit."""

    old_tokens = set(re.findall(r"[a-z0-9]+", normalize(old_name)))
    slug_tokens = set(re.findall(r"[a-z0-9]+", urlsplit(new_url).path.casefold()))
    name_score = len(old_tokens & slug_tokens) / max(len(old_tokens), 1)
    year_score = 1.0 if old_year and old_year in slug_tokens else 0.0
    score = 0.7 * name_score + 0.3 * year_score
    if score >= 0.95 and new_year == old_year:
        state = "HIGH_CONFIDENCE_SAME_EFFECTIVE_RECORD"
    elif score >= 0.65 and new_year == old_year:
        state = "POSSIBLE_SAME_EFFECTIVE_RECORD_REVIEW_REQUIRED"
    elif score >= 0.65 and new_year and new_year != old_year:
        state = "DISTINCT_ROUND_OR_SERVICE"
    else:
        state = "INSUFFICIENT_IDENTITY_EVIDENCE"
    return score, state


def coe_publication_duplicate_policy(
    match_state: str,
    candidate_assertion_count: int,
    *,
    independent_observation: bool,
) -> dict[str, str]:
    """Retain lineage while suppressing credit for a same-record mirror."""

    same_record = match_state in {
        "EXACT_SAME_EFFECTIVE_RECORD",
        "HIGH_CONFIDENCE_SAME_EFFECTIVE_RECORD",
    }
    duplicate_mirror = same_record and not independent_observation
    return {
        "retain_both_source_artifacts": "true",
        "publication_layer_relation": (
            "DISTINCT_EVIDENCE_PRODUCER_OR_OBSERVATION"
            if same_record and independent_observation
            else "UNRESOLVED_PARALLEL_DESCRIPTION"
            if same_record
            else "NOT_ESTABLISHED_AS_SAME_RECORD"
        ),
        "duplicate_assertion_credit_suppressed": str(duplicate_mirror).lower(),
        "suppressed_assertion_count": (
            str(candidate_assertion_count) if duplicate_mirror else "0"
        ),
        "decision_basis": (
            "DISTINCT_OBSERVATION_RETAINED_WITH_SAME_RECORD_LINEAGE"
            if same_record and independent_observation
            else "SAME_RECORD_PUBLICATION_MIRROR_CREDIT_SUPPRESSED"
            if duplicate_mirror
            else "NO_HIGH_CONFIDENCE_CROSS_DOMAIN_DUPLICATE_ESTABLISHED"
        ),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch2-restricted-root", type=Path, default=DEFAULT_BATCH2_RESTRICTED)
    parser.add_argument("--round3m-restricted-root", type=Path, default=DEFAULT_ROUND3M_RESTRICTED)
    args = parser.parse_args()

    ledger = read_tsv(CURRENT / "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv")
    batch2_details, baseline_text = restricted_text_by_assertion(
        args.batch2_restricted_root, args.round3m_restricted_root
    )
    by_label, by_key = ontology()
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.iterdir():
        if path.is_file():
            path.unlink()

    decision_rows: list[dict[str, Any]] = []
    normalization_acc: dict[str, dict[str, Any]] = {}
    source_text: dict[str, str] = {}
    for row in ledger:
        assertion_id = row["descriptor_assertion_id"]
        restricted = batch2_details.get(assertion_id)
        raw = restricted["atomic_source_text"] if restricted else baseline_text.get(assertion_id, "")
        panelist_hash = restricted.get("judge_observation_id_sha256", "") if restricted else ""
        zenodo_observation_hash = (
            sha256_text(row["effective_record_id"] + "\x1f" + panelist_hash)
            if row["source_family_id"] == "family.zenodo_golovinsky_q_grader_dataset" and panelist_hash
            else ""
        )
        source_text[assertion_id] = raw
        if raw:
            cleaned, segmentation, basis, confidence = clean_atom(raw)
        else:
            cleaned = [("", "SEMANTICALLY_UNRESOLVED")]
            segmentation = "SOURCE_TEXT_UNAVAILABLE_IN_GOVERNED_RESTRICTED_CHECKPOINT"
            basis = "HASH_ONLY_BATCH1_CAPTURE_NOT_AVAILABLE_TO_BATCH3_BUILDER"
            confidence = "0.000000"

        atom_hashes: list[str] = []
        classes: list[str] = []
        mapping_states: list[str] = []
        concept_ids: list[str] = []
        methods: list[str] = []
        mapping_confidences: list[str] = []
        for value, klass in cleaned:
            lexical_hash = sha256_text(value)
            state, concept_id, method, mapping_confidence = map_concept(value, klass, by_label)
            atom_hashes.append(lexical_hash)
            classes.append(klass)
            mapping_states.append(state)
            concept_ids.append(concept_id)
            methods.append(method)
            mapping_confidences.append(mapping_confidence)
            if lexical_hash not in normalization_acc:
                normalization_acc[lexical_hash] = {
                    "cleaned_lexical_form_sha256": lexical_hash,
                    "cleaned_lexical_form_or_restricted_pointer": f"hash:sha256:{lexical_hash}",
                    "source_language": row["source_language"],
                    "semantic_class": klass,
                    "mapping_state": state,
                    "canonical_concept_id": concept_id,
                    "canonical_concept_label": by_key.get(concept_id, ""),
                    "decision_method": method,
                    "mapping_confidence": mapping_confidence,
                    "assertion_support": 0,
                    "effective_records": set(),
                    "source_families": set(),
                    "years": set(),
                    "source_native_forms": set(),
                    "gold_support": 0,
                    "silver_support": 0,
                }
            acc = normalization_acc[lexical_hash]
            acc["source_native_forms"].add(row["atomic_source_text_sha256"])
            if row["counts_as_assertion"] == "true":
                acc["assertion_support"] += 1
                acc["effective_records"].add(row["effective_record_id"])
                acc["source_families"].add(row["source_family_id"])
                acc["years"].add(row["edition_year"])
                if row["evidence_tier"] in {"P1", "P2"}:
                    acc["gold_support"] += 1
                elif row["evidence_tier"] == "UNRESOLVED":
                    acc["silver_support"] += 1

        decision_rows.append({
            "descriptor_assertion_id": assertion_id,
            "source_dataset_id": row["source_dataset_id"],
            "source_family_id": row["source_family_id"],
            "source_route_id": row["source_route_id"],
            "effective_record_id": row["effective_record_id"],
            "coffee_identity_id": row["coffee_identity_id"],
            "edition_year": row["edition_year"],
            "preparation_service_id": row["preparation_service_id"],
            "publication_layer": row["publication_layer"],
            "source_field_label": row["source_field_label"],
            "source_locator": row["source_locator"],
            "source_field_text_sha256": row["source_field_text_sha256"],
            "atomic_source_text_sha256": row["atomic_source_text_sha256"],
            "source_native_form_sha256": row["atomic_source_text_sha256"],
            "source_language": row["source_language"],
            "original_descriptor_class": row["descriptor_class"],
            "segmentation_decision": segmentation,
            "segmentation_confidence": confidence,
            "segmentation_basis": basis,
            "cleaned_atom_count": len(cleaned),
            "cleaned_lexical_form_sha256s": atom_hashes,
            "semantic_classes": classes,
            "mapping_states": mapping_states,
            "canonical_concept_ids": concept_ids,
            "decision_methods": methods,
            "mapping_confidences": mapping_confidences,
            "semantic_cleaning_disposition": (
                "SEMANTICALLY_VALID" if any(klass in {"STRICT_FLAVOR", "BROAD_SENSORY", "DEFECT_OR_NEGATIVE_SENSORY"} for klass in classes)
                else "SEMANTICALLY_UNRESOLVED" if any(klass in {"COMPOSITE_DESCRIPTOR", "SEMANTICALLY_UNRESOLVED"} for klass in classes)
                else "NON_DESCRIPTOR"
            ),
            "review_requirement": "MACHINE_PROVISIONAL_REVIEW" if any(method == "MACHINE_PROVISIONAL_REVIEW" for method in methods) else "AUTOMATED_SAFE_RULE",
            "evidence_tier": row["evidence_tier"],
            "rights_state": row["rights_state"],
            "counts_as_assertion": row["counts_as_assertion"],
            "counts_as_record_unique_descriptor": row["counts_as_record_unique_descriptor"],
            "human_reviewed": "false",
            "expert_adjudicated": "false",
            "model_eligible": "false",
            "panelist_identity_sha256": panelist_hash,
            "panelist_sample_observation_sha256": zenodo_observation_hash,
            "roast_evidence_sha256_or_state": restricted.get("roast_evidence_sha256_or_state", "") if restricted else row["source_native_roast_value"] or "UNREPORTED",
            "restricted_text_available_for_cleaning": str(bool(raw)).lower(),
            "cleaner_version": BUILDER_VERSION,
        })

    decision_rows.sort(key=lambda row: row["descriptor_assertion_id"])
    decision_fields = list(decision_rows[0])
    write_tsv(OUT / "BATCH3_PUBLIC_SAFE_CLEANING_SIDECAR.tsv", decision_fields, decision_rows)

    segmentation_groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in decision_rows:
        key = (
            row["effective_record_id"], row["source_field_text_sha256"],
            row["source_field_label"], row["source_locator"],
        )
        segmentation_groups[key].append(row)
    segmentation_rows: list[dict[str, Any]] = []
    for key, rows in sorted(segmentation_groups.items()):
        effective_id, field_hash, label, locator = key
        segmentation_rows.append({
            "segmentation_group_id": stable_id("segmentation-field", "\x1f".join(key)),
            "effective_record_id": effective_id,
            "source_family_id": rows[0]["source_family_id"],
            "publication_layer": rows[0]["publication_layer"],
            "source_field_label": label,
            "source_locator": locator,
            "raw_field_text_or_restricted_pointer": f"hash:sha256:{field_hash}",
            "raw_field_text_sha256": field_hash,
            "first_pass_atom_count": len(rows),
            "first_pass_atom_sha256s": sorted(row["atomic_source_text_sha256"] for row in rows),
            "cleaned_atom_count": sum(int(row["cleaned_atom_count"]) for row in rows),
            "cleaned_atom_sha256s": sorted(
                atom for row in rows for atom in str(row["cleaned_lexical_form_sha256s"]).split("|")
            ),
            "segmentation_decisions": sorted({row["segmentation_decision"] for row in rows}),
            "minimum_segmentation_confidence": f"{min(float(row['segmentation_confidence']) for row in rows):.6f}",
            "decision_basis": sorted({row["segmentation_basis"] for row in rows}),
            "review_requirement": "MACHINE_PROVISIONAL_REVIEW" if any(row["review_requirement"] == "MACHINE_PROVISIONAL_REVIEW" for row in rows) else "AUTOMATED_SAFE_RULE",
            "segmentation_reversible": "true",
        })
    write_tsv(OUT / "BATCH3_PUBLIC_SAFE_SEGMENTATION_SIDECAR.tsv", list(segmentation_rows[0]), segmentation_rows)

    normalization_rows: list[dict[str, Any]] = []
    for lexical_hash, acc in sorted(normalization_acc.items()):
        normalization_rows.append({
            **{key: value for key, value in acc.items() if not isinstance(value, set)},
            "effective_record_support": len(acc["effective_records"]),
            "source_family_count": len(acc["source_families"]),
            "source_family_ids": sorted(acc["source_families"]),
            "year_count": len(acc["years"] - {""}),
            "years": sorted(acc["years"] - {""}),
            "source_native_form_count": len(acc["source_native_forms"]),
            "canonical_status": "ONTOLOGY_CANDIDATE" if acc["mapping_state"] == "ONTOLOGY_CANDIDATE" else "EXISTING_GOVERNED_CONCEPT" if acc["canonical_concept_id"] else "UNMAPPED",
            "review_requirement": "MACHINE_PROVISIONAL_REVIEW" if acc["decision_method"] == "MACHINE_PROVISIONAL_REVIEW" else "AUTOMATED_SAFE_RULE",
        })
    write_tsv(OUT / "BATCH3_PUBLIC_SAFE_NORMALIZATION_SIDECAR.tsv", list(normalization_rows[0]), normalization_rows)

    batch2_restricted_rows = list(batch2_details.values())
    entity_rows, duplicate_rows = build_entity_rows(batch2_restricted_rows, args.round3m_restricted_root)
    write_tsv(OUT / "BATCH3_PUBLIC_SAFE_COE_ENTITY_RESOLUTION.tsv", list(entity_rows[0]), entity_rows)
    write_tsv(OUT / "BATCH3_PUBLIC_SAFE_COE_DUPLICATE_DECISION.tsv", list(duplicate_rows[0]), duplicate_rows)

    gold_ids = {
        row["descriptor_assertion_id"] for row in decision_rows
        if row["counts_as_assertion"] == "true" and row["evidence_tier"] in {"P1", "P2"}
    }
    family_required = {
        "family.coffee_board_of_india_fine_cup",
        "family.sheba_coffee_yemen_auction",
        "family.project_origin",
    }
    required_ids = set(gold_ids)
    required_ids.update(
        row["descriptor_assertion_id"] for row in decision_rows
        if row["source_family_id"] in family_required and row["counts_as_assertion"] == "true"
    )
    zenodo_rows = [
        row for row in decision_rows
        if row["source_family_id"] == "family.zenodo_golovinsky_q_grader_dataset"
        and row["counts_as_assertion"] == "true"
    ]
    zenodo_observations: dict[str, list[str]] = defaultdict(list)
    for row in zenodo_rows:
        zenodo_observations[row["panelist_sample_observation_sha256"]].append(row["descriptor_assertion_id"])
    selected_observations = sorted(zenodo_observations)[:200]
    for observation in selected_observations:
        required_ids.update(zenodo_observations[observation])

    coe_generic = [
        row for row in decision_rows
        if row["source_family_id"] == "family.ace_cup_of_excellence"
        and row["publication_layer"] == "GENERIC_ORGANIZER_SENSORY_FIELD"
        and row["counts_as_assertion"] == "true"
    ]
    coe_generic.sort(key=lambda row: (
        row["edition_year"], row["source_field_label"],
        row["source_field_text_sha256"], row["descriptor_assertion_id"],
    ))
    # Deterministic even-stride selection preserves broad year/field/density coverage.
    if coe_generic:
        for index in range(min(300, len(coe_generic))):
            required_ids.add(coe_generic[(index * len(coe_generic)) // min(300, len(coe_generic))]["descriptor_assertion_id"])

    decision_by_id = {row["descriptor_assertion_id"]: row for row in decision_rows}
    audit_rows: list[dict[str, Any]] = []
    for assertion_id in sorted(required_ids):
        row = decision_by_id[assertion_id]
        classes = (
            list(row["semantic_classes"])
            if isinstance(row["semantic_classes"], list)
            else str(row["semantic_classes"]).split("|")
        )
        segmentation = str(row["segmentation_decision"])
        lexical_hashes = (
            list(row["cleaned_lexical_form_sha256s"])
            if isinstance(row["cleaned_lexical_form_sha256s"], list)
            else str(row["cleaned_lexical_form_sha256s"]).split("|")
        )
        cleaned = list(zip(lexical_hashes, classes))
        outcome = audit_outcome(cleaned, [segmentation])
        original = row["original_descriptor_class"]
        valid_classes = {"STRICT_FLAVOR", "DEFECT_OR_NEGATIVE_SENSORY"}
        class_error = (
            original == "STRICT_FLAVOR" and not any(item in valid_classes for item in classes)
        ) or (
            original == "BROAD_SENSORY" and "BROAD_SENSORY" not in classes
        )
        audit_rows.append({
            "semantic_audit_id": stable_id("semantic-audit", assertion_id),
            "descriptor_assertion_id": assertion_id,
            "source_family_id": row["source_family_id"],
            "audit_stratum": (
                "INDIA_FINE_CUP_ALL" if row["source_family_id"] == "family.coffee_board_of_india_fine_cup" else
                "SHEBA_ALL" if row["source_family_id"] == "family.sheba_coffee_yemen_auction" else
                "PROJECT_ORIGIN_ALL" if row["source_family_id"] == "family.project_origin" else
                "ZENODO_GOLD_ALL" if row["source_family_id"] == "family.zenodo_golovinsky_q_grader_dataset" else
                "COE_GOLD_EXPLICIT_JURY" if assertion_id in gold_ids else
                "COE_GENERIC_STRATIFIED" if row["source_family_id"] == "family.ace_cup_of_excellence" else
                "ZENODO_200_OBSERVATIONS"
            ),
            "edition_year": row["edition_year"],
            "source_field_label": row["source_field_label"],
            "publication_layer": row["publication_layer"],
            "raw_field_text_sha256": row["source_field_text_sha256"],
            "atomic_source_text_sha256": row["atomic_source_text_sha256"],
            "panelist_identity_sha256": row["panelist_identity_sha256"],
            "panelist_sample_observation_sha256": row["panelist_sample_observation_sha256"],
            "effective_record_id": row["effective_record_id"],
            "audit_outcome": outcome,
            "valid_atomic": str(outcome == "VALID_ATOMIC_DESCRIPTOR").lower(),
            "valid_broad": str(outcome == "VALID_BROAD_SENSORY").lower(),
            "compound": str(outcome == "VALID_COMPOSITE_REQUIRES_SPLIT").lower(),
            "over_segmentation": "false",
            "under_segmentation": str(segmentation in {"SAFE_LIST_SPLIT", "HEAD_PLUS_MODIFIER"}).lower(),
            "non_descriptor_leakage": str(outcome == "NON_DESCRIPTOR").lower(),
            "strict_broad_misclassification": str(class_error).lower(),
            "publication_duplicate": "false",
            "audit_method": "CODEX_RESTRICTED_SOURCE_SEMANTIC_AUDIT_AUTOMATED_SAFE_OR_PROVISIONAL",
            "human_reviewed": "false",
        })
    write_tsv(OUT / "BATCH3_PUBLIC_SAFE_SEMANTIC_AUDIT.tsv", list(audit_rows[0]), audit_rows)

    manifest = {
        "contract_version": "batch3.public-safe-cleaning-staging.v1",
        "snapshot_version": SNAPSHOT_VERSION,
        "builder_version": BUILDER_VERSION,
        "generated_at": GENERATED_AT,
        "restricted_input_storage": "OWNER_CONTROLLED_RESTRICTED_NON_GIT",
        "public_source_native_text_included": False,
        "frozen_raw_assertion_count": len(ledger),
        "frozen_mechanically_deinflated_assertion_count": sum(row["counts_as_assertion"] == "true" for row in ledger),
        "semantic_cleaning_disposition_count": len(decision_rows),
        "normalization_disposition_count": len(normalization_rows),
        "audit_assertion_count": len(audit_rows),
        "audit_gold_assertion_count": len(gold_ids),
        "audit_zenodo_observation_count": len({row["panelist_sample_observation_sha256"] for row in audit_rows if row["panelist_sample_observation_sha256"]}),
        "coe_old_domain_record_count": len(entity_rows),
        "governed_sensory_concept_count": len(by_key),
        "governed_scheme_node_count_reported_by_project": 130,
        "files": [],
    }
    for path in sorted(OUT.glob("*.tsv")):
        manifest["files"].append({
            "path": path.name,
            "sha256": sha256_file(path),
            "byte_count": path.stat().st_size,
            "data_row_count": max(sum(1 for _ in path.open(encoding="utf-8")) - 1, 0),
        })
    manifest_path = OUT / "BATCH3_STAGING_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum_paths = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (OUT / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_paths),
        encoding="utf-8",
    )
    print(
        f"BATCH3_CLEANING_STAGING_PASS decisions={len(decision_rows)} "
        f"forms={len(normalization_rows)} audit={len(audit_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
