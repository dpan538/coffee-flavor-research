#!/usr/bin/env python3
"""Manifest-driven professional descriptor acquisition and checkpoint runner.

Commands are intentionally explicit: discover, probe, acquire, resume, clean,
semantic, validate, and checkpoint. Source-native text is accepted only below
the configured restricted root; committed products are hash/ID/citation-only.
No command trains or evaluates a model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import itertools
import json
import math
import os
import re
import subprocess
import sys
import time
import types
import unicodedata
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "db" / "config" / "source-routes" / "batch7-routes.json"
STATE = ROOT / "db" / "data" / "acquisition-state"
CURRENT = ROOT / "db" / "data" / "current"
POST40 = ROOT / "db" / "data" / "post40k-extension-staging"
POST50 = ROOT / "db" / "data" / "post50k-extension-staging"
JATS_DIR = ROOT / "db" / "adapters" / "professional_sources"
if str(JATS_DIR) not in sys.path:
    sys.path.insert(0, str(JATS_DIR))
import jats  # type: ignore  # noqa: E402


BASELINE_SHA = "afde62ba0e957de959fd6127fc1e8b900814cbf4"
SNAPSHOT_50K = "professional-descriptor-candidate-v3-50k"
CLEANED_50K = "professional-descriptor-cleaned-v2-50k"
CLEANER_VERSION = "batch4.semantic-cleaner.v2"
BENCHMARK_VERSION = "batch7.cross-form-benchmark.v2"
GENERATED_AT = "2026-08-31T00:00:00+10:00"
FROZEN_40K_COUNT = 40030
FROZEN_50K_COUNT = 50034
TARGET_60K = 60000
COE_START_PAGE = 142
COE_START_INDEX = 2
COE_START_URL = "https://farmdirectory.cupofexcellence.org/listing/abiyot-ethiopia-2022/"
VALID_SOURCE = {
    "VALID_STRICT_FLAVOR",
    "VALID_BROAD_SENSORY",
    "VALID_DEFECT_OR_NEGATIVE_SENSORY",
    "VALID_COMPOUND_SPLIT",
    "VALID_COMPOUND_PRESERVED",
}
MODEL_SUFFIXES = {".pt", ".pth", ".onnx", ".safetensors", ".ckpt", ".h5", ".keras", ".pkl", ".joblib"}
RAW_FIELDS = {"raw_field_text", "atomic_source_text", "source_native_form", "judge_observation_id"}


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(prefix: str, material: str) -> str:
    return f"{prefix}:{sha_text(material)[:24]}"


def scalar(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (set, list, tuple)):
        return "|".join(str(item) for item in sorted(value))
    return str(value)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def fields(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t").fieldnames or [])


def write_tsv(path: Path, names: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(names)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: scalar(row.get(name, "")) for name in columns})


def write_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def data_rows(path: Path) -> int | str:
    if path.suffix != ".tsv":
        return "NA_NOT_TABULAR"
    return max(sum(1 for _ in path.open(encoding="utf-8")) - 1, 0)


def write_sums(root: Path) -> None:
    paths = sorted(path for path in root.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (root / "SHA256SUMS").write_text("".join(f"{sha_file(path)}  {path.name}\n" for path in paths), encoding="utf-8")


def config() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def route_map() -> dict[str, dict[str, Any]]:
    return {route["route_id"]: route for route in config()["routes"]}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_batch6():
    return load_module(ROOT / "db" / "scripts" / "generate-batch6-semantic-corpus.py", "batch7_batch6_generator")


def load_batch2():
    if "pdfplumber" not in sys.modules:
        sys.modules["pdfplumber"] = types.SimpleNamespace(open=lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("PDF adapter unavailable")))
    if "openpyxl" not in sys.modules:
        sys.modules["openpyxl"] = types.SimpleNamespace(load_workbook=lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("Workbook adapter unavailable")))
    return load_module(ROOT / "db" / "scripts" / "acquire-professional-descriptors-batch2.py", "batch7_batch2_acquisition")


def normalize_term(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().strip()
    value = re.sub(r"\s*\([^)]*(?:-[aft]|id|crc|bcc|cvl|ccs|car|rar|sar|aar|sta|bta|cfl|rfl|ata|sat|bat|ffl|ast|vis|bdy)[^)]*\)\s*$", "", value)
    value = re.sub(r"^[oft]\.", "", value)
    value = re.sub(r"[^\w/ -]+", " ", value)
    return " ".join(value.split())


def restricted_batch(root: Path) -> Path:
    return root / "batch7_acquisition"


def raw_path_for(root: Path, route_id: str, url: str) -> Path:
    suffix = ".xml" if "fullTextXML" in url else ".html"
    return restricted_batch(root) / "raw" / route_id.replace("/", "_") / f"{sha_text(url)[:24]}{suffix}"


def fetch(url: str, destination: Path, *, offline: bool, delay: float) -> tuple[int, str]:
    if offline:
        if not destination.is_file():
            raise RuntimeError(f"offline artifact missing: {destination}")
        return 200, "OFFLINE_CACHED_ARTIFACT"
    destination.parent.mkdir(parents=True, exist_ok=True)
    time.sleep(max(delay, 0.0))
    request = urllib.request.Request(url, headers={"User-Agent": config()["rate_limit_policy"]["user_agent"]})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read()
        destination.write_bytes(payload)
        return int(response.status), response.headers.get_content_type()


def probe_results() -> list[dict[str, str]]:
    path = STATE / "SOURCE_ROUTE_PROBE_RESULT.tsv"
    return read_tsv(path) if path.is_file() else []


def command_discover(_args: argparse.Namespace) -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    adapters = [
        {
            "adapter_id": "adapter.epmc.jats-trained-panel-v1",
            "adapter_version": "batch7.epmc-jats.v1",
            "source_class": "TRAINED_PANEL_RESEARCH",
            "input_schema": "JATS_XML",
            "output_contract": "SEMANTIC_REFERENCE_RELATIONS_AND_OPTIONAL_AGGREGATE_OBSERVATIONS",
            "public_restricted_boundary": "SOURCE_TEXT_RESTRICTED_PUBLIC_HASHES_ONLY",
            "idempotent_offline_replay": "true",
        },
        {
            "adapter_id": "adapter.web.metadata-probe-v1",
            "adapter_version": "batch7.web-metadata-probe.v1",
            "source_class": "STANDARD_DATASET_COMPETITION_OR_CATALOGUE",
            "input_schema": "HTML_OR_REPOSITORY_LANDING_PAGE",
            "output_contract": "ROUTE_ACCESS_AND_YIELD_RECEIPT_ONLY",
            "public_restricted_boundary": "CONTENT_RESTRICTED_PUBLIC_HASHES_ONLY",
            "idempotent_offline_replay": "true",
        },
        {
            "adapter_id": "adapter.coe.structured-official-sensory-fields-v2",
            "adapter_version": "batch7.coe-continuation.v2",
            "source_class": "COE_ANCHOR_CONTINUATION",
            "input_schema": "COE_ARCHIVE_AND_STRUCTURED_DETAIL_HTML",
            "output_contract": "SOURCE_ASSERTIONS_AND_CURSOR_RECEIPTS",
            "public_restricted_boundary": "SOURCE_TEXT_RESTRICTED_PUBLIC_HASHES_ONLY",
            "idempotent_offline_replay": "true",
        },
    ]
    write_tsv(STATE / "SOURCE_ADAPTER_REGISTRY.tsv", list(adapters[0]), adapters)
    family_acc: dict[str, dict[str, Any]] = {}
    schema_acc: dict[str, dict[str, Any]] = {}
    for route in config()["routes"]:
        family = family_acc.setdefault(route["source_family_id"], {
            "source_family_id": route["source_family_id"],
            "source_classes": set(),
            "languages": set(),
            "route_count": 0,
            "identity_policy": "MANIFEST_DECLARED_STABLE_SOURCE_FAMILY",
            "model_eligible": "false",
        })
        family["source_classes"].add(route["source_class"])
        family["languages"].update(route["languages"])
        family["route_count"] += 1
        schema_acc.setdefault(route["route_schema_id"], {
            "route_schema_id": route["route_schema_id"],
            "adapter_id": route["adapter_id"],
            "source_class": route["source_class"],
            "schema_contract": "ROUTE_MANIFEST_PLUS_ADAPTER_VERSIONED_OUTPUT_CONTRACT",
            "schema_drift_state": "NO_DRIFT_OBSERVED",
            "public_restricted_boundary": "PUBLIC_HASH_ID_CITATION_RESTRICTED_SOURCE_NATIVE_TEXT",
        })
    families = sorted(family_acc.values(), key=lambda row: row["source_family_id"])
    schemas = sorted(schema_acc.values(), key=lambda row: row["route_schema_id"])
    write_tsv(STATE / "SOURCE_FAMILY_REGISTRY.tsv", list(families[0]), families)
    write_tsv(STATE / "ROUTE_SCHEMA_REGISTRY.tsv", list(schemas[0]), schemas)
    observed = {row["source_route_id"]: row for row in probe_results()}
    post50_manifest = json.loads((POST50 / "POST50K_EXTENSION_MANIFEST.json").read_text()) if (POST50 / "POST50K_EXTENSION_MANIFEST.json").is_file() else {}
    registry = []
    transitions = []
    for route in config()["routes"]:
        state = "DISCOVERED"
        artifact_cursor = route["citation_locator"]
        if route["route_id"] in observed:
            state = observed[route["route_id"]]["new_state"]
            artifact_cursor = observed[route["route_id"]]["artifact_cursor"]
        if route["source_class"] == "COE_ANCHOR_CONTINUATION":
            state = "EXHAUSTED" if post50_manifest.get("coe_route_exhausted") else (
                "ACQUISITION_PAUSED" if post50_manifest.get("run") else "DISCOVERED"
            )
            artifact_cursor = post50_manifest.get("cursor_end", route["citation_locator"])
        registry.append({
            "source_route_id": route["route_id"],
            "source_family_id": route["source_family_id"],
            "source_class": route["source_class"],
            "languages": route["languages"],
            "source_url": route["url"],
            "adapter_id": route["adapter_id"],
            "route_schema_id": route["route_schema_id"],
            "current_state": state,
            "rights_state": route["rights_state"],
            "robots_access_decision": route["robots_access_decision"],
            "semantic_reference": route["semantic_reference"],
            "row_level_observations": route["row_level_observations"],
            "artifact_cursor": artifact_cursor,
            "retry_state": "NO_PENDING_RETRY",
            "failure_taxonomy": "NONE" if state not in {"BLOCKED_ACCESS", "PARSER_FAILED", "SCHEMA_DRIFT"} else state,
        })
        transitions.append({
            "transition_id": stable_id("route-transition", route["route_id"] + "\x1fDISCOVERED"),
            "timestamp": GENERATED_AT,
            "source_route_id": route["route_id"],
            "previous_state": "",
            "new_state": "DISCOVERED",
            "reason": "ROUTE_DECLARED_IN_BATCH7_MANIFEST",
            "artifact_cursor": route["citation_locator"],
            "commit_sha": BASELINE_SHA,
            "operator_type": "CODEX_OWNER_AUTHORIZED_AUTOMATION",
        })
        if state != "DISCOVERED":
            transitions.append({
                "transition_id": stable_id("route-transition", route["route_id"] + "\x1f" + state + "\x1f" + artifact_cursor),
                "timestamp": "2026-08-31T01:00:00+10:00",
                "source_route_id": route["route_id"],
                "previous_state": "DISCOVERED",
                "new_state": state,
                "reason": observed.get(route["route_id"], {}).get("reason", "ACQUISITION_CHECKPOINT_STATE"),
                "artifact_cursor": artifact_cursor,
                "commit_sha": BASELINE_SHA,
                "operator_type": "CODEX_OWNER_AUTHORIZED_AUTOMATION",
            })
    write_tsv(STATE / "SOURCE_ROUTE_REGISTRY.tsv", list(registry[0]), registry)
    write_tsv(STATE / "SOURCE_ROUTE_STATE_TRANSITION.tsv", list(transitions[0]), transitions)
    cursors = [{
        "cursor_id": "cursor.coe.post50k",
        "source_route_id": "route.coe.post50k-archive-continuation",
        "cursor_contract": "ARCHIVE_PAGE_DETAIL_INDEX_CANONICAL_URL",
        "cursor_start": f"archive-page={COE_START_PAGE};detail-index={COE_START_INDEX};url={COE_START_URL}",
        "cursor_current": post50_manifest.get("cursor_end", f"archive-page={COE_START_PAGE};detail-index={COE_START_INDEX};url={COE_START_URL}"),
        "checkpoint_target": TARGET_60K,
        "stop_rule": "FIRST_COMPLETE_EFFECTIVE_RECORD_BOUNDARY_AT_OR_ABOVE_60000",
        "resume_validated": post50_manifest.get("exact_cursor_validated", False),
        "terminal_state": "EXHAUSTED" if post50_manifest.get("coe_route_exhausted") else "ACQUISITION_PAUSED",
    }]
    write_tsv(STATE / "ACQUISITION_CURSOR_REGISTRY.tsv", list(cursors[0]), cursors)
    write_sums(STATE)
    print(f"SOURCE_ROUTE_REGISTRY_COUNT={len(registry)}")
    print(f"SOURCE_ADAPTER_REGISTRY_COUNT={len(adapters)}")
    print(f"SOURCE_FAMILY_REGISTRY_COUNT={len(families)}")
    print(f"ROUTE_SCHEMA_REGISTRY_COUNT={len(schemas)}")
    return 0


def command_probe(args: argparse.Namespace) -> int:
    routes = [route for route in config()["routes"] if route["source_class"] != "COE_ANCHOR_CONTINUATION"]
    results = []
    for route in routes:
        destination = raw_path_for(args.restricted_root, route["route_id"], route["url"])
        accessed = False
        status = ""
        content_type = ""
        failure = "NONE"
        reason = ""
        try:
            status_code, content_type = fetch(route["url"], destination, offline=args.offline, delay=args.request_delay)
            status = str(status_code)
            accessed = True
        except urllib.error.HTTPError as error:
            status = str(error.code)
            failure = "HTTP_ERROR"
            reason = f"HTTP_{error.code}"
        except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
            failure = "NETWORK_ERROR" if not isinstance(error, RuntimeError) else "ACCESS_DENIED"
            reason = type(error).__name__
        duplicate = route["route_id"] == "route.zenodo.20840464.q-grader-dataset"
        descriptor_bearing = accessed and bool(route["semantic_reference"] or route["row_level_observations"])
        new_state = "DUPLICATE_SATURATED" if duplicate and accessed else (
            "PROBE_POSITIVE" if descriptor_bearing else ("PROBE_ZERO_YIELD" if accessed else "BLOCKED_ACCESS")
        )
        if not reason:
            reason = {
                "DUPLICATE_SATURATED": "EXISTING_GOVERNED_SOURCE_FAMILY_NO_DUPLICATE_IMPORT",
                "PROBE_POSITIVE": "ACCESSIBLE_DESCRIPTOR_OR_SEMANTIC_REFERENCE_ROUTE",
                "PROBE_ZERO_YIELD": "ACCESSIBLE_ROUTE_WITH_NO_ADMITTED_DESCRIPTOR_SURFACE",
                "BLOCKED_ACCESS": "ROUTE_COULD_NOT_BE_ACCESSED",
            }[new_state]
        results.append({
            "source_route_id": route["route_id"],
            "source_family_id": route["source_family_id"],
            "source_class": route["source_class"],
            "languages": route["languages"],
            "attempted": "true",
            "accessed": str(accessed).lower(),
            "http_status": status,
            "content_type": content_type,
            "descriptor_bearing": str(descriptor_bearing).lower(),
            "row_level": str(accessed and route["row_level_observations"]).lower(),
            "semantic_reference_only": str(accessed and route["semantic_reference"] and not route["row_level_observations"]).lower(),
            "zero_yield": str(new_state == "PROBE_ZERO_YIELD").lower(),
            "blocked": str(new_state == "BLOCKED_ACCESS").lower(),
            "rights_state": route["rights_state"],
            "continuation_state": "ACQUISITION_ACTIVE" if route["route_id"] == "route.epmc.pmc8774372.brewed-black-coffee" else (
                "DUPLICATE_SATURATED" if duplicate else "SEMANTIC_MINING_COMPLETE_OR_METADATA_ONLY"
            ),
            "new_state": new_state,
            "reason": reason,
            "artifact_cursor": route["citation_locator"],
            "restricted_artifact_pointer": f"restricted://batch7_acquisition/{destination.relative_to(restricted_batch(args.restricted_root)).as_posix()}" if destination.is_file() else "",
            "artifact_sha256": sha_file(destination) if destination.is_file() else "",
            "artifact_byte_count": destination.stat().st_size if destination.is_file() else 0,
            "failure_taxonomy": failure,
        })
    write_tsv(STATE / "SOURCE_ROUTE_PROBE_RESULT.tsv", list(results[0]), results)
    write_tsv(STATE / "NON_COE_ROUTE_ATTEMPT.tsv", list(results[0]), results)
    command_discover(args)
    positive = sum(row["descriptor_bearing"] == "true" for row in results)
    print(f"NON_COE_DISCOVERY_ROUTE_ATTEMPT_COUNT={len(results)}")
    print(f"NON_COE_DISCOVERY_POSITIVE_ROUTE_COUNT={positive}")
    return 0


S2_SOURCES = {
    "PMC8774372": "route.epmc.pmc8774372.brewed-black-coffee",
    "PMC13163763": "route.epmc.pmc13163763.cafe-latte-lexicon",
    "PMC6776322": "route.epmc.pmc6776322.retronasal-aroma",
    "PMC11675256": "route.epmc.pmc11675256.storage-temperature-lexicon",
    "PMC13279845": "route.epmc.pmc13279845.espresso-lexicon",
}
S2_SOURCE_METADATA = {
    "PMC8774372": {
        "publisher": "Foods",
        "title": "Sensory Drivers of Consumer Acceptance, Purchase Intent and Emotions toward Brewed Black Coffee",
        "version_or_date": "2022",
    },
    "PMC13163763": {
        "publisher": "Foods",
        "title": "Effects of Cognitive Style and Evaluation Context on Hedonic and Sensory Perception of Café Latte: A Comparison of Sensory Booth, Real-Life, and Mixed Reality Environments",
        "version_or_date": "2026",
    },
    "PMC6776322": {
        "publisher": "PLoS ONE",
        "title": "Impact of bitter tastant sub-qualities on retronasal coffee aroma perception",
        "version_or_date": "2019",
    },
    "PMC11675256": {
        "publisher": "Foods",
        "title": "Effect of Temperature and Storage on Coffee’s Volatile Compound Profile and Sensory Characteristics",
        "version_or_date": "2024",
    },
    "PMC13279845": {
        "publisher": "Journal of Food Science",
        "title": "Between Bitterness and Sweetness: How Decaffeination and Sweeteners Shape the Sensory Experience of Espresso Coffee",
        "version_or_date": "2026",
    },
}


def semantic_reference_source_rows(relation_rows: list[Mapping[str, str]]) -> list[dict[str, Any]]:
    routes = route_map()
    by_source: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for relation in relation_rows:
        by_source[relation["semantic_reference_source_id"]].append(relation)
    source_rows: list[dict[str, Any]] = [{
        "semantic_reference_source_id": "semantic-reference.existing-governed-ontology-v1",
        "publisher": "Coffee Flavor Atlas project",
        "title": "Existing governed ontology and approved alias rules",
        "version_or_date": CLEANER_VERSION,
        "language": "en",
        "term_or_term_hash": "NA_GOVERNED_MAPPING_RULE_REFERENCE",
        "definition_or_restricted_pointer": "restricted://governed-ontology-and-approved-alias-rules",
        "relation_supported": "EXACT_EQUIVALENT|APPROVED_ALIAS_OF|MORPHOLOGICAL_VARIANT_OF",
        "evidence_level": "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS",
        "rights_status": "PROJECT_GOVERNED_CONTENT",
        "citation_or_locator": "db/scripts/build-batch4-cleaning-staging.py",
        "artifact_hash": sha_file(ROOT / "db" / "scripts" / "build-batch4-cleaning-staging.py"),
        "relation_count": 0,
    }]
    for pmcid, route_id in S2_SOURCES.items():
        source_id = f"semantic-reference.{pmcid.casefold()}"
        relations = by_source[source_id]
        if not relations:
            raise RuntimeError(f"committed S2 relation seed lacks source: {source_id}")
        metadata = S2_SOURCE_METADATA[pmcid]
        source_rows.append({
            "semantic_reference_source_id": source_id,
            **metadata,
            "language": "en",
            "term_or_term_hash": "HASHES_IN_S2_REFERENCE_RELATION_SEED",
            "definition_or_restricted_pointer": f"restricted://batch7_acquisition/raw/{route_id}",
            "relation_supported": "EXPLICIT_DEFINITION_MATCH|EXPLICIT_BROADER_NARROWER",
            "evidence_level": "S2_EXPLICIT_PROFESSIONAL_REFERENCE",
            "rights_status": "CC_BY_4_0_ATTRIBUTION_REQUIRED",
            "citation_or_locator": routes[route_id]["citation_locator"],
            "artifact_hash": relations[0]["source_artifact_sha256"],
            "relation_count": len(relations),
        })
    return source_rows


def acquire_semantic_references(args: argparse.Namespace) -> tuple[int, int]:
    routes = route_map()
    relation_rows = []
    for pmcid, route_id in S2_SOURCES.items():
        route = routes[route_id]
        artifact = raw_path_for(args.restricted_root, route_id, route["url"])
        if not artifact.is_file():
            fetch(route["url"], artifact, offline=args.offline, delay=args.request_delay)
        metadata = jats.article_metadata(artifact)
        if "creative commons attribution" not in metadata["license"].casefold() and "creativecommons.org/licenses/by/4.0" not in metadata["license"].casefold():
            raise RuntimeError(f"S2 source is not verified CC BY 4.0: {pmcid}")
        expected = S2_SOURCE_METADATA[pmcid]
        if any(metadata[key] != expected[target] for key, target in (("journal", "publisher"), ("title", "title"), ("year", "version_or_date"))):
            raise RuntimeError(f"S2 citation metadata drift: {pmcid}")
        extracted = jats.source_relations(artifact, pmcid)
        source_id = f"semantic-reference.{pmcid.casefold()}"
        for item in extracted:
            term_hash = sha_text(item["term"])
            normalized_hash = sha_text(normalize_term(item["term"]))
            object_hash = sha_text(item["definition_or_category"])
            relation_id = stable_id("semantic-relation", "\x1f".join((source_id, item["relation_type"], term_hash, object_hash)))
            relation_rows.append({
                "semantic_relation_id": relation_id,
                "semantic_reference_source_id": source_id,
                "relation_type": item["relation_type"],
                "relation_layer": "CONCEPT_HIERARCHY" if item["relation_type"] == "EXPLICIT_BROADER_NARROWER" else "LEXICAL_DEFINITION",
                "subject_node_id": f"semantic-reference-term:{normalized_hash[:24]}",
                "object_node_id": f"semantic-reference-definition:{object_hash[:24]}",
                "source_term_sha256": term_hash,
                "normalized_term_sha256": normalized_hash,
                "definition_or_category_sha256": object_hash,
                "source_locator_or_restricted_pointer": item["source_locator"],
                "source_artifact_sha256": sha_file(artifact),
                "support_role": "EXPLICIT_PROFESSIONAL_REFERENCE",
                "evidence_authority": "S2_EXPLICIT_PROFESSIONAL_REFERENCE",
                "rights_state": "CC_BY_4_0_ATTRIBUTION_REQUIRED",
                "raw_definition_published": "false",
            })
    relation_rows.sort(key=lambda row: row["semantic_relation_id"])
    source_rows = semantic_reference_source_rows(relation_rows)
    if len(source_rows) - 1 < 5 or len(relation_rows) < 100:
        raise RuntimeError(f"S2 target shortfall after admitted extraction: sources={len(source_rows) - 1} relations={len(relation_rows)}")
    write_tsv(STATE / "S2_REFERENCE_RELATION_SEED.tsv", list(relation_rows[0]), relation_rows)
    write_tsv(CURRENT / "SEMANTIC_REFERENCE_SOURCE.tsv", list(source_rows[0]), source_rows)
    target_count = len({row["normalized_term_sha256"] for row in relation_rows})
    write_json(STATE / "S2_REFERENCE_MINING_RECEIPT.json", {
        "contract_version": "batch7.s2-reference-mining.v1",
        "evidence_authority": "S2_EXPLICIT_PROFESSIONAL_REFERENCE",
        "reference_source_count": len(source_rows) - 1,
        "unique_relation_count": len({row["semantic_relation_id"] for row in relation_rows}),
        "target_concept_coverage_count": target_count,
        "raw_definition_published": False,
        "source_xml_committed": False,
        "rights_states": ["CC_BY_4_0_ATTRIBUTION_REQUIRED"],
        "model_run": False,
    })
    write_sums(STATE)
    return len(source_rows) - 1, len(relation_rows)


def descriptor_class(attribute: str) -> str:
    lowered = attribute.casefold()
    if any(token in lowered for token in ("balance", "impact", "longevity", "fullness", "astringent")):
        return "BROAD_SENSORY"
    if any(token in lowered for token in ("burnt", "acrid", "ashy", "rubber", "creosote", "musty", "sour taste", "bitter taste")):
        return "DEFECT_OR_NEGATIVE_SENSORY"
    return "STRICT_FLAVOR"


def acquire_non_coe_observations(args: argparse.Namespace) -> int:
    route = route_map()["route.epmc.pmc8774372.brewed-black-coffee"]
    artifact = raw_path_for(args.restricted_root, route["route_id"], route["url"])
    if not artifact.is_file():
        fetch(route["url"], artifact, offline=args.offline, delay=args.request_delay)
    observations = jats.brewed_black_coffee_observations(artifact)
    if not observations:
        raise RuntimeError("positive non-CoE observation route yielded no assertions")
    restricted_rows = []
    public_rows = []
    for observation in observations:
        material = "\x1f".join((route["source_family_id"], observation["sample"], observation["attribute"]))
        assertion_id = stable_id("assertion-b7", material)
        effective_id = stable_id("effective-b7", route["source_family_id"] + "\x1f" + observation["sample"])
        coffee_id = stable_id("coffee-b7", route["source_family_id"] + "\x1f" + observation["sample"])
        atomic_hash = sha_text(observation["attribute"])
        roast_hash = sha_text(observation["roast_class"])
        restricted = {
            "descriptor_assertion_id": assertion_id,
            "source_family_id": route["source_family_id"],
            "publisher": "Foods / MDPI",
            "source_route_id": route["route_id"],
            "route_schema": route["route_schema_id"],
            "source_url": route["url"],
            "source_artifact_sha256": sha_file(artifact),
            "source_locator": observation["source_locator"],
            "effective_record_id": effective_id,
            "coffee_identity_id": coffee_id,
            "edition_or_release": "PMC8774372 version of record",
            "edition_year": "2022",
            "source_language": "en",
            "preparation_service": "UNREPORTED_SOURCE_METHOD_NOT_IN_ASSERTION_TABLE",
            "roast_evidence_sha256_or_state": roast_hash,
            "source_field_label": "Table 4 trained-panel aggregate intensity",
            "raw_field_text_sha256": atomic_hash,
            "atomic_source_text_sha256": atomic_hash,
            "source_native_form_sha256": atomic_hash,
            "descriptor_class": descriptor_class(observation["attribute"]),
            "evidence_tier": "P2",
            "collection_tier": "GOLD",
            "provenance_state": "PEER_REVIEWED_TRAINED_PANEL_AGGREGATE",
            "rights_state": "AFFIRMATIVE",
            "rights_basis": "CC_BY_4_0_ATTRIBUTION_REQUIRED",
            "publication_layer": "TRAINED_PANEL_AGGREGATE_TABLE",
            "judge_observation_id_sha256": "",
            "provisional_normalized_form_id": stable_id("provisional-form", normalize_term(observation["attribute"])),
            "provisional_normalized_form_sha256": sha_text(normalize_term(observation["attribute"])),
            "mapping_status": "AUTO_ORTHOGRAPHIC",
            "mapping_method": "NFKC_CASE_SPACE_PUNCTUATION",
            "mapping_confidence": "0.990000",
            "mapping_basis": "CASE_SPACING_AND_PUNCTUATION_NORMALIZATION",
            "review_requirement": "AUTO_PROVISIONALLY_MAPPED",
            "human_reviewed": "false",
            "model_eligible": "false",
            "counts_as_assertion": "true",
            "counts_as_record_unique_descriptor": "true",
            "source_text_storage_state": "OWNER_CONTROLLED_RESTRICTED_HASH_ONLY_PUBLIC",
            "raw_field_text": observation["attribute"],
            "atomic_source_text": observation["attribute"],
            "source_native_form": observation["attribute"],
            "provisional_normalized_form": normalize_term(observation["attribute"]),
            "judge_observation_id": "",
            "roast_evidence": observation["roast_class"],
            "reported_intensity": observation["intensity"],
        }
        restricted_rows.append(restricted)
        public_rows.append({key: value for key, value in restricted.items() if key not in RAW_FIELDS | {"reported_intensity", "publisher"}} | {
            "publisher_id": stable_id("publisher", "Foods / MDPI"),
            "extension_batch_id": "professional-descriptor-post50k-extension-20260831",
            "parser_version": "batch7.epmc-jats.v1",
            "adapter_version": "batch7.non-coe-trained-panel.v1",
            "acquisition_cursor": observation["source_locator"],
            "frozen_snapshot_version": SNAPSHOT_50K,
            "frozen_snapshot_member": "false",
        })
    restricted_dir = restricted_batch(args.restricted_root) / "post50k_extension"
    restricted_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(restricted_dir / "NON_COE_ASSERTIONS_RESTRICTED.tsv", list(restricted_rows[0]), restricted_rows)
    POST50.mkdir(parents=True, exist_ok=True)
    write_tsv(POST50 / "NON_COE_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv", list(public_rows[0]), public_rows)
    write_json(POST50 / "NON_COE_ACQUISITION_RECEIPT.json", {
        "contract_version": "batch7.non-coe-acquisition.v1",
        "discovery_status": "NON_COE_DISCOVERY_RUN_POSITIVE",
        "route_attempt_count": len(probe_results()),
        "source_class_count": len({row["source_class"] for row in probe_results()}),
        "language_count": len({language for row in probe_results() for language in row["languages"].split("|") if language}),
        "positive_observation_family_count": 1,
        "rights_clearable_family_count": 1,
        "deinflated_source_assertion_count": len(restricted_rows),
        "effective_record_count": len({row["effective_record_id"] for row in restricted_rows}),
        "target_assertion_count": 1500,
        "assertion_shortfall_count": max(1500 - len(restricted_rows), 0),
        "raw_source_text_published": False,
        "model_eligible_assertion_count": 0,
    })
    write_sums(POST50)
    return len(restricted_rows)


def command_acquire(args: argparse.Namespace) -> int:
    source_count, relation_count = acquire_semantic_references(args)
    non_coe_count = acquire_non_coe_observations(args)
    print(f"S2_REFERENCE_SOURCE_COUNT={source_count}")
    print(f"S2_UNIQUE_RELATION_COUNT={relation_count}")
    print(f"NEW_NON_COE_DEINFLATED_ASSERTION_COUNT={non_coe_count}")
    return 0


def find_restricted_ledger(root: Path, name: str, segment: str) -> Path:
    candidates = [root / name, root / segment / name]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError(f"restricted ledger not found under {root}: {name}")


def b2_fetch_retry(b2: Any, url: str, path: Path, *, offline: bool, delay: float) -> bool:
    last: Exception | None = None
    for attempt in range(1 if offline else 3):
        try:
            return b2.fetch(url, path, offline=offline, delay=delay if attempt == 0 else 1.0)
        except RuntimeError as error:
            last = error
    assert last is not None
    raise last


def resume_coe(args: argparse.Namespace) -> dict[str, Any]:
    b2 = load_batch2()
    prior_path = find_restricted_ledger(args.prior_post40_root, "POST40K_ASSERTIONS_RESTRICTED.tsv", "post40k_extension")
    prior_urls = {row["source_url"] for row in read_tsv(prior_path)}
    non_coe_path = restricted_batch(args.restricted_root) / "post50k_extension" / "NON_COE_ASSERTIONS_RESTRICTED.tsv"
    if not non_coe_path.is_file():
        raise RuntimeError("non-CoE acquisition must run before CoE continuation")
    non_coe_rows = [row for row in read_tsv(non_coe_path) if row["counts_as_assertion"] == "true"]
    restricted_dir = restricted_batch(args.restricted_root) / "post50k_extension"
    raw = restricted_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    atoms: list[Any] = []
    cursor_by_record: dict[str, str] = {}
    artifact_rows: list[dict[str, Any]] = []
    cursor_end = f"archive-page={COE_START_PAGE};detail-index={COE_START_INDEX};url={COE_START_URL}"
    exact_cursor_validated = False
    blocked = False
    exhausted = False
    reached = False
    coe_records = 0
    for page in range(COE_START_PAGE, b2.MAX_COE_ARCHIVE_PAGES + 1):
        archive = raw / "coe-archive" / f"listings-page-{page:03d}.html"
        try:
            b2_fetch_retry(b2, b2.coe_archive_url(page), archive, offline=args.offline, delay=args.request_delay)
        except RuntimeError as error:
            cursor_end = f"retry-archive-page={page};error={type(error).__name__}"
            blocked = True
            break
        urls = sorted(b2.coe_archive_links(archive.read_text(encoding="utf-8", errors="replace")))
        artifact_rows.append({
            "source_route_id": "route.coe.post50k-archive-continuation",
            "source_url": b2.coe_archive_url(page),
            "restricted_relative_path": archive.relative_to(restricted_dir).as_posix(),
            "sha256": sha_file(archive),
            "byte_count": archive.stat().st_size,
            "acquisition_cursor": f"archive-page={page}",
        })
        if page == COE_START_PAGE:
            if len(urls) < COE_START_INDEX or urls[COE_START_INDEX - 1] != COE_START_URL:
                raise RuntimeError("preserved post-50K CoE cursor no longer matches archive page 142")
            exact_cursor_validated = True
        if not urls:
            exhausted = True
            cursor_end = f"archive-page={page};NO_LISTING_LINKS"
            break
        first = COE_START_INDEX if page == COE_START_PAGE else 1
        for index, url in enumerate(urls, start=1):
            if index < first or url in prior_urls:
                continue
            current_total = FROZEN_50K_COUNT + len(non_coe_rows) + sum(atom.counts_as_assertion for atom in atoms)
            if current_total >= TARGET_60K:
                cursor_end = f"archive-page={page};detail-index={index};url={url}"
                reached = True
                break
            detail = raw / "coe-detail" / f"{sha_text(url)[:24]}.html"
            try:
                b2_fetch_retry(b2, url, detail, offline=args.offline, delay=args.request_delay)
            except RuntimeError as error:
                cursor_end = f"retry-archive-page={page};detail-index={index};error={type(error).__name__}"
                blocked = True
                break
            record_atoms = b2.parse_coe_detail(detail, url)
            b2.apply_deinflation(record_atoms)
            cursor = f"archive-page={page};detail-index={index};url={url}"
            cursor_end = cursor
            if record_atoms:
                atoms.extend(record_atoms)
                coe_records += 1
                for atom in record_atoms:
                    cursor_by_record[atom.effective_record_id] = cursor
                artifact_rows.append({
                    "source_route_id": record_atoms[0].source_route,
                    "source_url": url,
                    "restricted_relative_path": detail.relative_to(restricted_dir).as_posix(),
                    "sha256": sha_file(detail),
                    "byte_count": detail.stat().st_size,
                    "acquisition_cursor": cursor,
                })
        if blocked or reached:
            break
    else:
        exhausted = True
        cursor_end = "EXHAUSTED_COE_ARCHIVE"
    b2.apply_deinflation(atoms)
    coe_deinflated = sum(atom.counts_as_assertion for atom in atoms)
    total = FROZEN_50K_COUNT + len(non_coe_rows) + coe_deinflated
    reached = reached or total >= TARGET_60K
    safe_rows = []
    for atom, safe in zip(atoms, b2.safe_rows(atoms)):
        item = dict(safe)
        item.pop("publisher", None)
        item["publisher_id"] = b2.stable_id("publisher", atom.source_family)
        item.update({
            "extension_batch_id": "professional-descriptor-post50k-extension-20260831",
            "source_field_label": "hash:sha256:" + sha_text(atom.source_field_label),
            "parser_version": "batch7.professional-descriptor-parser.v1",
            "adapter_version": "batch7.manifest-driven-coe-adapter.v1",
            "acquisition_cursor": cursor_by_record[atom.effective_record_id],
            "frozen_snapshot_version": SNAPSHOT_50K,
            "frozen_snapshot_member": False,
        })
        safe_rows.append(item)
    restricted_rows = list(b2.restricted_rows(atoms))
    write_tsv(restricted_dir / "POST50K_COE_ASSERTIONS_RESTRICTED.tsv", list(restricted_rows[0]) if restricted_rows else ["descriptor_assertion_id"], restricted_rows)
    write_tsv(restricted_dir / "POST50K_RAW_ARTIFACT_RECEIPT.tsv", list(artifact_rows[0]) if artifact_rows else ["source_route_id"], artifact_rows)
    POST50.mkdir(parents=True, exist_ok=True)
    write_tsv(POST50 / "POST50K_COE_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv", list(safe_rows[0]) if safe_rows else ["descriptor_assertion_id"], safe_rows)
    public_artifacts = [{**row, "restricted_relative_path": "restricted://batch7_acquisition/post50k_extension/" + row["restricted_relative_path"]} for row in artifact_rows]
    write_tsv(POST50 / "POST50K_PUBLIC_ARTIFACT_RECEIPT.tsv", list(public_artifacts[0]) if public_artifacts else ["source_route_id"], public_artifacts)
    attempts = probe_results()
    route_rows = [{
        "source_route_id": row["source_route_id"],
        "source_family_id": row["source_family_id"],
        "source_class": row["source_class"],
        "attempted": row["attempted"],
        "accessed": row["accessed"],
        "descriptor_bearing": row["descriptor_bearing"],
        "row_level": row["row_level"],
        "semantic_reference_only": row["semantic_reference_only"],
        "zero_yield": row["zero_yield"],
        "blocked": row["blocked"],
        "rights_state": row["rights_state"],
        "continuation_state": row["continuation_state"],
        "deinflated_assertion_count": len(non_coe_rows) if row["source_route_id"] == "route.epmc.pmc8774372.brewed-black-coffee" else 0,
    } for row in attempts]
    route_rows.append({
        "source_route_id": "route.coe.post50k-archive-continuation",
        "source_family_id": "family.ace_cup_of_excellence",
        "source_class": "COE_ANCHOR_CONTINUATION",
        "attempted": "true",
        "accessed": str(bool(artifact_rows)).lower(),
        "descriptor_bearing": str(coe_deinflated > 0).lower(),
        "row_level": "true",
        "semantic_reference_only": "false",
        "zero_yield": str(coe_deinflated == 0).lower(),
        "blocked": str(blocked).lower(),
        "rights_state": "MIXED_PENDING_UNKNOWN",
        "continuation_state": "EXHAUSTED" if exhausted else "ACQUISITION_PAUSED",
        "deinflated_assertion_count": coe_deinflated,
    })
    write_tsv(POST50 / "POST50K_SOURCE_ROUTE_DISCOVERY.tsv", list(route_rows[0]), route_rows)
    manifest = {
        "contract_version": "post50k-extension-manifest.v1",
        "extension_batch_id": "professional-descriptor-post50k-extension-20260831",
        "generated_at": GENERATED_AT,
        "run": True,
        "frozen_snapshot_version": SNAPSHOT_50K,
        "frozen_denominator_assertion_count": FROZEN_50K_COUNT,
        "extension_isolated_from_frozen_snapshot": True,
        "non_coe_attempts_completed_before_coe_continuation": len(attempts) >= 10,
        "non_coe_route_attempt_count": len(attempts),
        "non_coe_source_class_count": len({row["source_class"] for row in attempts}),
        "non_coe_language_count": len({language for row in attempts for language in row["languages"].split("|") if language}),
        "non_coe_discovery_status": "NON_COE_DISCOVERY_RUN_POSITIVE" if non_coe_rows else "NON_COE_DISCOVERY_RUN_ZERO_YIELD",
        "cursor_start": f"archive-page={COE_START_PAGE};detail-index={COE_START_INDEX};url={COE_START_URL}",
        "cursor_end": cursor_end,
        "exact_cursor_validated": exact_cursor_validated,
        "coe_route_exhausted": exhausted,
        "coe_continuation_blocked": blocked,
        "post50k_net_new_deinflated_assertion_count": len(non_coe_rows) + coe_deinflated,
        "post50k_net_new_effective_record_count": len({row["effective_record_id"] for row in non_coe_rows}) + len({atom.effective_record_id for atom in atoms if atom.counts_as_assertion}),
        "post50k_new_coe_assertion_count": coe_deinflated,
        "post50k_new_non_coe_assertion_count": len(non_coe_rows),
        "new_positive_non_coe_observation_family_count": 1 if non_coe_rows else 0,
        "new_rights_clearable_non_coe_family_count": 1 if non_coe_rows else 0,
        "total_acquired_candidate_source_assertion_count": total,
        "candidate_60k_checkpoint_reached": reached,
        "hard_stop_rule": "FIRST_COMPLETE_EFFECTIVE_RECORD_BOUNDARY_AT_OR_ABOVE_60000",
        "restricted_coe_assertion_ledger_sha256": sha_file(restricted_dir / "POST50K_COE_ASSERTIONS_RESTRICTED.tsv"),
        "restricted_non_coe_assertion_ledger_sha256": sha_file(non_coe_path),
        "restricted_artifact_receipt_sha256": sha_file(restricted_dir / "POST50K_RAW_ARTIFACT_RECEIPT.tsv"),
        "model_eligible_assertion_count": 0,
        "human_reviewed_assertion_count": 0,
        "schema_changed": False,
        "new_migration_count": 0,
        "model_training_run": False,
        "files": [],
    }
    for path in sorted(POST50.iterdir()):
        if path.is_file() and path.name not in {"POST50K_EXTENSION_MANIFEST.json", "SHA256SUMS"}:
            manifest["files"].append({"path": path.name, "sha256": sha_file(path), "byte_count": path.stat().st_size, "data_row_count": data_rows(path)})
    write_json(POST50 / "POST50K_EXTENSION_MANIFEST.json", manifest)
    write_sums(POST50)
    command_discover(args)
    return manifest


def command_resume(args: argparse.Namespace) -> int:
    if len(probe_results()) < 10:
        raise RuntimeError("at least ten non-CoE route attempts are required before CoE resume")
    manifest = resume_coe(args)
    print(f"POST50K_NET_NEW_DEINFLATED_ASSERTION_COUNT={manifest['post50k_net_new_deinflated_assertion_count']}")
    print(f"TOTAL_ACQUIRED_CANDIDATE_SOURCE_ASSERTION_COUNT={manifest['total_acquired_candidate_source_assertion_count']}")
    print(f"CANDIDATE_60K_CHECKPOINT_REACHED={str(manifest['candidate_60k_checkpoint_reached']).lower()}")
    print(f"COE_CONTINUATION_CURSOR_END={manifest['cursor_end']}")
    return 0


def post40_source(batch6: Any, row: Mapping[str, str]) -> dict[str, str]:
    # Batch 2's historical identity material did not include the acquisition
    # segment, so distinct later CoE records can collide with assertions in
    # the frozen 40K denominator. The 50K canonical surface uses a stable,
    # segment-scoped identity while retaining the historical ID in its
    # restricted pointer. This changes no semantic-cleaner rule.
    assertion_id = stable_id(
        "assertion-b7-post40",
        "\x1f".join(
            (
                row["descriptor_assertion_id"],
                row["source_artifact_sha256"],
                row["source_locator"],
            )
        ),
    )
    return {
        "corpus_segment": "POST40K_EXTENSION",
        "descriptor_assertion_id": assertion_id,
        "source_family_id": row["source_family_id"],
        "publisher_id": stable_id("publisher", row["publisher"]),
        "source_route_id": row["source_route_id"],
        "source_artifact_id": stable_id("source-artifact", row["source_artifact_sha256"]),
        "source_artifact_sha256": row["source_artifact_sha256"],
        "source_locator": row["source_locator"],
        "effective_record_id": row["effective_record_id"],
        "coffee_identity_id": row["coffee_identity_id"],
        "year_id": f"year.{row['edition_year']}" if row["edition_year"] else "year.unreported",
        "preparation_service_id": row["preparation_service"],
        "source_language": row["source_language"],
        "source_field_label_sha256": sha_text(row["source_field_label"]),
        "raw_field_text_sha256": row["raw_field_text_sha256"],
        "atomic_source_text_sha256": row["atomic_source_text_sha256"],
        "source_native_form_id": f"source-form:{row['source_native_form_sha256'][:24]}",
        "restricted_source_pointer": f"restricted://post40k_extension/assertions/{row['descriptor_assertion_id']}",
        "original_descriptor_class": row["descriptor_class"],
        "evidence_tier": row["evidence_tier"],
        "collection_tier": row["collection_tier"],
        "provenance_state": row["provenance_state"],
        "rights_state": row["rights_state"],
        "rights_basis": row["rights_basis"],
        "publication_layer": row["publication_layer"],
        "judge_observation_id_sha256": row["judge_observation_id_sha256"],
        "duplicate_group_id": "",
        "mirror_group_id": "",
        "counts_as_record_unique_descriptor": row["counts_as_record_unique_descriptor"],
    }


def build_cleaned_50k(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    cached_source = CURRENT / "CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv"
    cached_atoms = CURRENT / "CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv"
    try:
        restricted_path = find_restricted_ledger(args.prior_post40_root, "POST40K_ASSERTIONS_RESTRICTED.tsv", "post40k_extension")
    except RuntimeError:
        if cached_source.is_file() and cached_atoms.is_file():
            decisions = read_tsv(cached_source)
            atoms = read_tsv(cached_atoms)
            if len(decisions) != FROZEN_50K_COUNT:
                raise RuntimeError("cached 50K source denominator drift")
            return decisions, atoms
        raise
    batch6 = load_batch6()
    decisions: list[dict[str, Any]] = [dict(row) for row in read_tsv(CURRENT / "CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv")]
    atoms: list[dict[str, Any]] = [dict(row) for row in read_tsv(CURRENT / "CLEANED_40K_OUTPUT_ATOM_LEDGER.tsv")]
    raw_rows = [row for row in read_tsv(restricted_path) if row["counts_as_assertion"] == "true"]
    if len(decisions) != FROZEN_40K_COUNT or len(raw_rows) != 10004:
        raise RuntimeError(f"50K input denominator drift: 40k={len(decisions)} post40k={len(raw_rows)}")
    for raw in raw_rows:
        source = post40_source(batch6, raw)
        decision, new_atoms = batch6.clean_source(source, raw["atomic_source_text"])
        decisions.append(decision)
        atoms.extend(new_atoms)
    decisions.sort(key=lambda row: row["descriptor_assertion_id"])
    atoms.sort(key=lambda row: row["cleaned_output_atom_id"])
    decisions = [{key: scalar(value) for key, value in row.items()} for row in decisions]
    atoms = [{key: scalar(value) for key, value in row.items()} for row in atoms]
    if len(decisions) != FROZEN_50K_COUNT or len({row["descriptor_assertion_id"] for row in decisions}) != FROZEN_50K_COUNT:
        raise RuntimeError("combined 50K source assertion identity reconciliation failed")
    if len(atoms) != sum(int(row["cleaned_output_atom_count"]) for row in decisions):
        raise RuntimeError("combined 50K source/output atom reconciliation failed")
    write_tsv(cached_source, fields(CURRENT / "CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv"), decisions)
    write_tsv(cached_atoms, fields(CURRENT / "CLEANED_40K_OUTPUT_ATOM_LEDGER.tsv"), atoms)
    manifest_content = "\n".join("\t".join((row["descriptor_assertion_id"], row["source_artifact_sha256"], row["effective_record_id"], row["atomic_source_text_sha256"])) for row in decisions)
    snapshot = {
        "contract_version": "candidate-50k-snapshot-manifest.v1",
        "snapshot_version": SNAPSHOT_50K,
        "snapshot_role": "IMMUTABLE_ACQUISITION_CHECKPOINT_NOT_TRAINING_CORPUS",
        "immutable": True,
        "candidate_40k_snapshot_sha256": sha_file(CURRENT / "CANDIDATE_40K_SNAPSHOT_MANIFEST.json"),
        "post40k_extension_manifest_sha256": sha_file(POST40 / "POST40K_EXTENSION_MANIFEST.json"),
        "snapshot_content_sha256": sha_text(manifest_content),
        "source_assertion_count": len(decisions),
        "effective_record_count": len({row["effective_record_id"] for row in decisions}),
        "source_family_count": len({row["source_family_id"] for row in decisions}),
        "source_ledger": cached_source.name,
        "source_ledger_sha256": sha_file(cached_source),
        "post40k_identity_namespace": "assertion-b7-post40",
        "post40k_identity_basis": "HISTORICAL_ASSERTION_ID+SOURCE_ARTIFACT_SHA256+SOURCE_LOCATOR",
        "cleaner_changed": False,
        "exact_coe_continuation_cursor": json.loads((POST40 / "POST40K_EXTENSION_MANIFEST.json").read_text())["cursor_end"],
        "restricted_ledger_root_hash": json.loads((POST40 / "POST40K_EXTENSION_MANIFEST.json").read_text())["restricted_assertion_ledger_sha256"],
        "cleaner_contract_version": CLEANER_VERSION,
        "training_corpus_frozen": False,
        "model_eligible_corpus_frozen": False,
        "model_eligible_assertion_count": 0,
        "schema_changed": False,
        "new_migration_count": 0,
    }
    write_json(CURRENT / "CANDIDATE_50K_SNAPSHOT_MANIFEST.json", snapshot)
    valid_count = sum(row["source_assertion_disposition"] in VALID_SOURCE for row in decisions)
    valid_atoms = [row for row in atoms if row["counts_as_cleaned_descriptor_output"] == "true"]
    cleaned_manifest = {
        "contract_version": "cleaned-50k-manifest.v1",
        "cleaned_view_version": CLEANED_50K,
        "cleaner_version": CLEANER_VERSION,
        "source_assertion_count": len(decisions),
        "valid_source_assertion_count": valid_count,
        "non_descriptor_source_assertion_count": sum(row["source_assertion_disposition"] == "NON_DESCRIPTOR" for row in decisions),
        "unresolved_source_assertion_count": sum(row["source_assertion_disposition"] == "UNRESOLVED" for row in decisions),
        "output_atom_count": len(atoms),
        "valid_output_atom_count": len(valid_atoms),
        "record_unique_output_atom_count": len({(row["effective_record_id"], batch6.target_id(row)) for row in valid_atoms if row["counts_as_record_unique_descriptor"] == "true"}),
        "source_assertion_reconciliation_pass": sum(int(row["cleaned_output_atom_count"]) for row in decisions) == len(atoms),
        "candidate_50k_snapshot_sha256": sha_file(CURRENT / "CANDIDATE_50K_SNAPSHOT_MANIFEST.json"),
        "source_ledger_sha256": sha_file(cached_source),
        "output_atom_ledger_sha256": sha_file(cached_atoms),
        "model_run": False,
    }
    write_json(CURRENT / "CLEANED_50K_MANIFEST.json", cleaned_manifest)
    return [dict(row) for row in decisions], [dict(row) for row in atoms]


def command_clean(args: argparse.Namespace) -> int:
    decisions, atoms = build_cleaned_50k(args)
    manifest = json.loads((CURRENT / "CLEANED_50K_MANIFEST.json").read_text())
    print(f"CANDIDATE_50K_SOURCE_ASSERTION_COUNT={len(decisions)}")
    print(f"CLEANED_50K_OUTPUT_ATOM_COUNT={len(atoms)}")
    print(f"CLEANED_50K_VALID_SOURCE_ASSERTION_COUNT={manifest['valid_source_assertion_count']}")
    return 0


def atom_authority(atom: Mapping[str, str]) -> str:
    state = atom["mapping_state"]
    if state == "EXISTING_CANONICAL_MORPHOLOGICAL_VARIANT":
        return "S0_DETERMINISTIC_ORTHOGRAPHIC"
    if state in {"EXISTING_CANONICAL_EXACT", "EXISTING_CANONICAL_ALIAS"}:
        return "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS"
    return "S3_MULTI_SOURCE_MACHINE_CANDIDATE"


def publication_group(source: Mapping[str, str]) -> str:
    return source.get("duplicate_group_id") or source.get("mirror_group_id") or source["effective_record_id"]


def percentile(values: list[int], quantile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[max(math.ceil(quantile * len(ordered)) - 1, 0)]


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, item: str) -> str:
        self.parent.setdefault(item, item)
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[b] = a


def benchmark_v2(batch6: Any, decisions: list[Mapping[str, str]], atoms: list[Mapping[str, str]]) -> dict[str, Any]:
    source_by_id = {row["descriptor_assertion_id"]: row for row in decisions}
    valid = [row for row in atoms if row["counts_as_cleaned_descriptor_output"] == "true"]
    by_target: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for atom in valid:
        by_target[batch6.target_id(atom)].append(atom)
    case_rows = []
    group_rows = []
    audits = []
    for target, target_atoms in sorted(by_target.items()):
        by_form: dict[str, list[Mapping[str, str]]] = defaultdict(list)
        for atom in target_atoms:
            by_form[atom["cleaned_lexical_form_sha256"]].append(atom)
        eligible = []
        for form_hash, form_atoms in by_form.items():
            groups = {atom["coffee_identity_id"] or atom["effective_record_id"] for atom in form_atoms}
            if len(groups) >= 3:
                eligible.append((form_hash, form_atoms, len(groups)))
        eligible.sort(key=lambda item: (-item[2], item[0]))
        for fold_sequence, (held_form, test_atoms, test_group_count) in enumerate(eligible[:5], start=1):
            authority = atom_authority(test_atoms[0])
            primary = authority in {"S0_DETERMINISTIC_ORTHOGRAPHIC", "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS"} and bool(test_atoms[0]["canonical_concept_id"])
            review = authority == "S3_MULTI_SOURCE_MACHINE_CANDIDATE"
            if not primary and not review:
                continue
            test_groups = {atom["coffee_identity_id"] or atom["effective_record_id"] for atom in test_atoms}
            test_publications = {publication_group(source_by_id[atom["descriptor_assertion_id"]]) for atom in test_atoms}
            train_atoms = [
                atom for form, rows in by_form.items() if form != held_form
                for atom in rows
                if (atom["coffee_identity_id"] or atom["effective_record_id"]) not in test_groups
                and publication_group(source_by_id[atom["descriptor_assertion_id"]]) not in test_publications
            ]
            if not train_atoms:
                continue
            train_forms = {atom["cleaned_lexical_form_sha256"] for atom in train_atoms}
            if not train_forms:
                continue
            tier = "PRIMARY_GOVERNED" if primary else "REVIEW_REQUIRED_S3"
            case_id = stable_id("cross-form-fold", "\x1f".join((BENCHMARK_VERSION, target, held_form)))
            rows_for_case = []
            for split, selected in (("TRAIN", train_atoms), ("TEST", test_atoms)):
                for atom in selected:
                    source = source_by_id[atom["descriptor_assertion_id"]]
                    rows_for_case.append({
                        "benchmark_version": BENCHMARK_VERSION,
                        "benchmark_case_id": case_id,
                        "benchmark_tier": tier,
                        "surface": "UNSEEN_FORM_KNOWN_TARGET",
                        "fold_sequence": fold_sequence,
                        "split": split,
                        "cleaned_output_atom_id": atom["cleaned_output_atom_id"],
                        "cleaned_form_hash": atom["cleaned_lexical_form_sha256"],
                        "held_out_form_hash": held_form,
                        "target_concept_or_cluster_id": target,
                        "coffee_sample_group_id": atom["coffee_identity_id"] or atom["effective_record_id"],
                        "duplicate_publication_group_id": publication_group(source),
                        "source_family_id": atom["source_family_id"],
                        "year_id": atom["year_id"],
                        "relation_authority": authority,
                        "target_present_in_training": "true",
                        "held_out_form_absent_from_training": "true",
                        "sample_group_absent_from_training": "true" if split == "TEST" else "NA_TRAIN_ROW",
                        "duplicate_publication_group_absent_from_training": "true" if split == "TEST" else "NA_TRAIN_ROW",
                        "expected_response": "MAP_TO_KNOWN_TARGET",
                        "human_reviewer_decision": "",
                    })
            case_rows.extend(rows_for_case)
            train_groups = {row["coffee_sample_group_id"] for row in rows_for_case if row["split"] == "TRAIN"}
            test_groups_written = {row["coffee_sample_group_id"] for row in rows_for_case if row["split"] == "TEST"}
            train_pubs = {row["duplicate_publication_group_id"] for row in rows_for_case if row["split"] == "TRAIN"}
            test_pubs = {row["duplicate_publication_group_id"] for row in rows_for_case if row["split"] == "TEST"}
            train_form_values = {row["cleaned_form_hash"] for row in rows_for_case if row["split"] == "TRAIN"}
            test_form_values = {row["cleaned_form_hash"] for row in rows_for_case if row["split"] == "TEST"}
            group_rows.append({
                "benchmark_case_id": case_id,
                "benchmark_tier": tier,
                "target_concept_or_cluster_id": target,
                "held_out_form_hash": held_form,
                "eligible_form_count": len(eligible),
                "eligible_held_out_fold_count": min(len(eligible), 5),
                "training_form_count": len(train_forms),
                "train_group_count": len(train_groups),
                "test_form_group_support": len(test_groups_written),
                "source_family_support": len({row["source_family_id"] for row in rows_for_case}),
                "year_support": len({row["year_id"] for row in rows_for_case}),
                "relation_authority": authority,
                "minimum_test_group_threshold": 3,
                "form_holdout_feasible": "true",
                "sample_group_feasible": "true",
            })
            audits.append({
                "benchmark_case_id": case_id,
                "held_out_form_train_overlap_count": len(train_form_values & test_form_values),
                "coffee_sample_group_overlap_count": len(train_groups & test_groups_written),
                "duplicate_publication_group_overlap_count": len(train_pubs & test_pubs),
                "target_present_in_training": "true" if train_atoms else "false",
                "known_target_condition_pass": str(bool(train_atoms) and not (train_form_values & test_form_values) and not (train_groups & test_groups_written) and not (train_pubs & test_pubs)).lower(),
            })
    if not case_rows:
        raise RuntimeError("benchmark V2 produced no eligible folds")
    write_tsv(CURRENT / "CROSS_FORM_BENCHMARK_CANDIDATE.tsv", list(case_rows[0]), case_rows)
    write_tsv(CURRENT / "CROSS_FORM_BENCHMARK_GROUP.tsv", list(group_rows[0]), group_rows)
    write_tsv(CURRENT / "CROSS_FORM_BENCHMARK_LEAKAGE_AUDIT.tsv", list(audits[0]), audits)
    uf = UnionFind()
    for atom in valid:
        uf.union("coffee:" + (atom["coffee_identity_id"] or atom["effective_record_id"]), "form:" + atom["cleaned_lexical_form_sha256"])
    component_sizes = Counter(uf.find(node) for node in uf.parent)
    sizes = list(component_sizes.values())
    primary_cases = {row["benchmark_case_id"] for row in case_rows if row["benchmark_tier"] == "PRIMARY_GOVERNED"}
    review_cases = {row["benchmark_case_id"] for row in case_rows if row["benchmark_tier"] == "REVIEW_REQUIRED_S3"}
    primary_targets = {row["target_concept_or_cluster_id"] for row in case_rows if row["benchmark_tier"] == "PRIMARY_GOVERNED"}
    review_targets = {row["target_concept_or_cluster_id"] for row in case_rows if row["benchmark_tier"] == "REVIEW_REQUIRED_S3"}
    target_families: dict[str, set[str]] = defaultdict(set)
    for atom in valid:
        target_families[batch6.target_id(atom)].add(atom["source_family_id"])
    summary = {
        "contract_version": BENCHMARK_VERSION,
        "model_run": False,
        "minimum_held_out_form_test_group_count": 3,
        "preferred_held_out_form_test_group_count": 5,
        "primary_governed_target_count": len(primary_targets),
        "primary_governed_fold_count": len(primary_cases),
        "primary_governed_train_output_count": sum(row["benchmark_tier"] == "PRIMARY_GOVERNED" and row["split"] == "TRAIN" for row in case_rows),
        "primary_governed_test_output_count": sum(row["benchmark_tier"] == "PRIMARY_GOVERNED" and row["split"] == "TEST" for row in case_rows),
        "review_required_target_count": len(review_targets),
        "review_required_fold_count": len(review_cases),
        "review_required_test_output_count": sum(row["benchmark_tier"] == "REVIEW_REQUIRED_S3" and row["split"] == "TEST" for row in case_rows),
        "median_held_out_form_test_group_count": percentile([int(row["test_form_group_support"]) for row in group_rows], 0.5),
        "held_out_family_shared_target_count": sum(len(families) >= 2 for families in target_families.values()),
        "open_set_unseen_target_count": len({batch6.target_id(atom) for atom in valid if not atom["canonical_concept_id"]}),
        "global_component_count": len(sizes),
        "largest_global_component_share": round(max(sizes, default=0) / max(sum(sizes), 1), 6),
        "p50_component_size": percentile(sizes, 0.50),
        "p95_component_size": percentile(sizes, 0.95),
        "p99_component_size": percentile(sizes, 0.99),
        "leak_count": sum(int(row["held_out_form_train_overlap_count"]) + int(row["coffee_sample_group_overlap_count"]) + int(row["duplicate_publication_group_overlap_count"]) for row in audits),
        "target_known_condition_pass": all(row["known_target_condition_pass"] == "true" for row in audits),
        "relation_authority_pass": all(row["relation_authority"] in {"S0_DETERMINISTIC_ORTHOGRAPHIC", "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS", "S3_MULTI_SOURCE_MACHINE_CANDIDATE"} for row in group_rows),
    }
    write_json(CURRENT / "CROSS_FORM_BENCHMARK_SPLIT_MANIFEST.json", summary)
    human_source = [row for row in case_rows if row["split"] == "TEST"][:500]
    human = [{
        "human_benchmark_item_id": stable_id("human-cross-form-v2", row["benchmark_case_id"] + "\x1f" + row["cleaned_output_atom_id"]),
        "item_sequence": index,
        "benchmark_version": BENCHMARK_VERSION,
        "benchmark_case_id": row["benchmark_case_id"],
        "benchmark_tier": row["benchmark_tier"],
        "public_case_pointer": row["cleaned_output_atom_id"],
        "restricted_context_pointer": f"restricted://batch7_semantic_review/human/{index}",
        "reviewer_id": "",
        "reviewer_decision": "",
        "reviewed_at": "",
        "review_note": "",
    } for index, row in enumerate(human_source, start=1)]
    write_tsv(CURRENT / "HUMAN_CROSS_FORM_BENCHMARK_TEMPLATE.tsv", list(human[0]), human)
    return summary


def build_relation_support(batch6: Any, decisions: list[Mapping[str, str]], atoms: list[Mapping[str, str]], edges: list[Mapping[str, Any]], s2: list[Mapping[str, str]]) -> list[dict[str, Any]]:
    source_by_id = {row["descriptor_assertion_id"]: row for row in decisions}
    edge_by_key = {(row["subject_node_id"], row["relation_type"], row["object_node_id"]): row for row in edges}
    rows: list[dict[str, Any]] = []

    def add(key: tuple[str, str, str], atom: Mapping[str, str], role: str) -> None:
        edge = edge_by_key.get(key)
        if not edge:
            return
        source = source_by_id[atom["descriptor_assertion_id"]]
        rows.append({
            "semantic_relation_id": edge["semantic_relation_id"],
            "relation_type": key[1],
            "relation_layer": edge["relation_layer"],
            "supporting_output_atom_id": atom["cleaned_output_atom_id"],
            "supporting_source_assertion_id": atom["descriptor_assertion_id"],
            "effective_record_id": atom["effective_record_id"],
            "coffee_or_sample_identity_id": atom["coffee_identity_id"],
            "source_family_id": atom["source_family_id"],
            "source_artifact_sha256": source["source_artifact_sha256"],
            "source_locator_or_restricted_pointer": source["restricted_source_pointer"],
            "support_role": role,
            "evidence_authority": edge["semantic_evidence_authority"],
            "rights_state": atom["rights_state"],
            "publication_layer": atom["publication_layer"],
        })

    valid = [atom for atom in atoms if atom["counts_as_cleaned_descriptor_output"] == "true"]
    for atom in valid:
        form = f"semantic-form:{atom['cleaned_lexical_form_sha256'][:24]}"
        concept = batch6.node_id(atom)
        state = atom["mapping_state"]
        relation = {
            "EXISTING_CANONICAL_EXACT": "EXACT_EQUIVALENT",
            "EXISTING_CANONICAL_ALIAS": "APPROVED_ALIAS_OF",
            "EXISTING_CANONICAL_MORPHOLOGICAL_VARIANT": "MORPHOLOGICAL_VARIANT_OF",
            "EXISTING_CANONICAL_CHILD_OR_SPECIFIC_FORM": "INSTANCE_OR_SPECIFIC_FORM_OF",
        }.get(state)
        if relation:
            add((form, relation, concept), atom, "LEXICAL_MAPPING_SUPPORT")
            if relation != "INSTANCE_OR_SPECIFIC_FORM_OF":
                add((concept, relation, form), atom, "LEXICAL_MAPPING_SUPPORT_REVERSE")
        for modifier in batch6.split_pipe(atom["modifier_form_sha256s"]):
            add((f"semantic-form:{modifier[:24]}", "MODIFIES", form), atom, "MODIFIER_PARSE_SUPPORT")
        for component in batch6.split_pipe(atom["component_concept_ids"]):
            add((f"semantic-concept:{component}", "COMPONENT_OF", form), atom, "COMPOUND_PARSE_SUPPORT")
        if atom["preparation_service_id"]:
            add((concept, "OBSERVED_UNDER_PREPARATION", f"semantic-context:preparation:{sha_text(atom['preparation_service_id'])[:24]}"), atom, "OBSERVATIONAL_CONTEXT_SUPPORT")
    by_record: dict[str, dict[str, Mapping[str, str]]] = defaultdict(dict)
    for atom in valid:
        by_record[atom["effective_record_id"]][batch6.node_id(atom)] = atom
    for record_atoms in by_record.values():
        nodes = sorted(record_atoms)
        for index, left in enumerate(nodes):
            for right in nodes[index + 1:]:
                add((left, "COASSERTED_WITH", right), record_atoms[left], "SAME_EFFECTIVE_RECORD_OBSERVATION")
    for relation in s2:
        rows.append({
            "semantic_relation_id": relation["semantic_relation_id"],
            "relation_type": relation["relation_type"],
            "relation_layer": relation["relation_layer"],
            "supporting_output_atom_id": "NA_SEMANTIC_REFERENCE_NOT_OBSERVATION",
            "supporting_source_assertion_id": "NA_SEMANTIC_REFERENCE_NOT_OBSERVATION",
            "effective_record_id": "NA_SEMANTIC_REFERENCE_NOT_OBSERVATION",
            "coffee_or_sample_identity_id": "NA_SEMANTIC_REFERENCE_NOT_OBSERVATION",
            "source_family_id": relation["semantic_reference_source_id"],
            "source_artifact_sha256": relation["source_artifact_sha256"],
            "source_locator_or_restricted_pointer": relation["source_locator_or_restricted_pointer"],
            "support_role": relation["support_role"],
            "evidence_authority": relation["evidence_authority"],
            "rights_state": relation["rights_state"],
            "publication_layer": "PROFESSIONAL_SEMANTIC_REFERENCE",
        })
    rows.sort(key=lambda row: (row["semantic_relation_id"], row["supporting_source_assertion_id"], row["supporting_output_atom_id"]))
    aggregated: list[dict[str, Any]] = []
    for relation_id, relation_rows in itertools.groupby(
        rows, key=lambda row: row["semantic_relation_id"]
    ):
        occurrences = list(relation_rows)
        representative = dict(occurrences[0])
        representative.update({
            "support_occurrence_count": len(occurrences),
            "unique_supporting_source_assertion_count": len({row["supporting_source_assertion_id"] for row in occurrences}),
            "unique_effective_record_count": len({row["effective_record_id"] for row in occurrences}),
            "unique_source_family_count": len({row["source_family_id"] for row in occurrences}),
            "support_row_encoding": "ONE_RELATION_ROW_WITH_EXPLICIT_OCCURRENCE_COUNTS",
        })
        if representative["semantic_relation_id"] != relation_id:
            raise RuntimeError("semantic relation support aggregation drift")
        aggregated.append(representative)
    return aggregated


def command_semantic(args: argparse.Namespace) -> int:
    if not (STATE / "S2_REFERENCE_RELATION_SEED.tsv").is_file():
        acquire_semantic_references(args)
    decisions, atoms = build_cleaned_50k(args)
    batch6 = load_batch6()
    clusters = batch6.concept_clusters(atoms)
    form_nodes, concept_nodes, edge_rows, evidence_rows, candidates, rejections = batch6.semantic_graph(atoms, clusters)
    s2 = read_tsv(STATE / "S2_REFERENCE_RELATION_SEED.tsv")
    source_rows = semantic_reference_source_rows(s2)
    write_tsv(CURRENT / "SEMANTIC_REFERENCE_SOURCE.tsv", list(source_rows[0]), source_rows)
    known_nodes = {row["semantic_concept_node_id"] for row in concept_nodes}
    for relation in s2:
        for node_id, node_kind in ((relation["subject_node_id"], "SEMANTIC_REFERENCE_TERM"), (relation["object_node_id"], "SEMANTIC_REFERENCE_DEFINITION_OR_CATEGORY")):
            if node_id not in known_nodes:
                concept_nodes.append({
                    "semantic_concept_node_id": node_id,
                    "concept_or_cluster_id": node_id.split(":", 1)[-1],
                    "node_kind": node_kind,
                    "canonical_ontology_auto_promotion": "false",
                })
                known_nodes.add(node_id)
        edge_rows.append({
            "semantic_relation_id": relation["semantic_relation_id"],
            "relation_layer": relation["relation_layer"],
            "subject_node_id": relation["subject_node_id"],
            "relation_type": relation["relation_type"],
            "object_node_id": relation["object_node_id"],
            "semantic_evidence_authority": "S2_EXPLICIT_PROFESSIONAL_REFERENCE",
            "governance_state": "GOVERNED_REFERENCE_RELATION",
            "source_basis": relation["semantic_reference_source_id"],
            "source_assertion_support": 0,
            "effective_record_support": 0,
            "source_family_support": 0,
            "human_reviewed": "false",
            "sensory_expert_adjudicated": "false",
        })
        evidence_rows.append({
            "semantic_relation_evidence_id": stable_id("semantic-evidence", relation["semantic_relation_id"] + "\x1f" + relation["semantic_reference_source_id"]),
            "semantic_relation_id": relation["semantic_relation_id"],
            "source_id": relation["semantic_reference_source_id"],
            "source_locator_or_restricted_pointer": relation["source_locator_or_restricted_pointer"],
            "term_or_context_hash": relation["source_term_sha256"],
            "relation_supported": relation["relation_type"],
            "evidence_authority": relation["evidence_authority"],
            "rights_status": relation["rights_state"],
            "raw_definition_published": "false",
        })
    edge_rows.sort(key=lambda row: row["semantic_relation_id"])
    concept_nodes.sort(key=lambda row: row["semantic_concept_node_id"])
    support = build_relation_support(batch6, decisions, atoms, edge_rows, s2)
    write_tsv(CURRENT / "ONTOLOGY_CONSOLIDATION_V2.tsv", list(clusters[0]), clusters)
    write_tsv(CURRENT / "SEMANTIC_FORM_NODE.tsv", list(form_nodes[0]), form_nodes)
    write_tsv(CURRENT / "SEMANTIC_CONCEPT_NODE.tsv", list(concept_nodes[0]), concept_nodes)
    write_tsv(CURRENT / "SEMANTIC_RELATION_EDGE.tsv", list(edge_rows[0]), edge_rows)
    write_tsv(CURRENT / "SEMANTIC_RELATION_EVIDENCE.tsv", list(evidence_rows[0]), evidence_rows)
    candidate_by_id = {row["semantic_relation_candidate_id"]: row for row in candidates}
    write_tsv(CURRENT / "SEMANTIC_RELATION_CANDIDATE.tsv", list(candidate_by_id.values())[0].keys() if candidate_by_id else ["semantic_relation_candidate_id"], sorted(candidate_by_id.values(), key=lambda row: row["semantic_relation_candidate_id"]))
    write_tsv(CURRENT / "SEMANTIC_RELATION_REJECTION.tsv", list(rejections[0]) if rejections else ["semantic_relation_rejection_id"], rejections)
    write_tsv(CURRENT / "SEMANTIC_RELATION_SUPPORT.tsv", list(support[0]), support)
    benchmark = benchmark_v2(batch6, decisions, atoms)
    governed = {row["semantic_relation_id"] for row in edge_rows if row["governance_state"] in {"GOVERNED", "GOVERNED_REFERENCE_RELATION"}}
    review = {row["semantic_relation_id"] for row in edge_rows if row["governance_state"] == "REVIEW_REQUIRED"}
    observational = {row["semantic_relation_id"] for row in edge_rows if row["relation_layer"] in {"OBSERVATIONAL", "CONTEXT"}}
    s3_unique = {row["semantic_relation_id"] for row in edge_rows if row["semantic_evidence_authority"] == "S3_MULTI_SOURCE_MACHINE_CANDIDATE"}
    support_occurrences = sum(int(row["support_occurrence_count"]) for row in support)
    s3_occurrences = sum(
        int(row["support_occurrence_count"])
        for row in support
        if row["evidence_authority"] == "S3_MULTI_SOURCE_MACHINE_CANDIDATE"
    )
    summary_rows = [
        {"metric": "UNIQUE_GOVERNED_SEMANTIC_RELATION_COUNT", "value": len(governed)},
        {"metric": "UNIQUE_REVIEW_REQUIRED_SEMANTIC_RELATION_COUNT", "value": len(review)},
        {"metric": "OBSERVATIONAL_CONTEXT_RELATION_COUNT", "value": len(observational)},
        {"metric": "S2_UNIQUE_RELATION_COUNT", "value": len(s2)},
        {"metric": "S3_UNIQUE_RELATION_COUNT", "value": len(s3_unique)},
        {"metric": "S3_SUPPORT_OCCURRENCE_COUNT", "value": s3_occurrences},
        {"metric": "RELATION_SUPPORT_OCCURRENCE_COUNT", "value": support_occurrences},
        {"metric": "RELATION_LEVEL_SUPPORT_ROW_COUNT", "value": len(support)},
    ]
    write_tsv(CURRENT / "SEMANTIC_RELATION_SUMMARY.tsv", ["metric", "value"], summary_rows)
    edge_by_id = {row["semantic_relation_id"]: row for row in edge_rows}
    review_candidates = []
    for relation in s2:
        review_candidates.append({
            "semantic_relation_id": relation["semantic_relation_id"],
            "relation_type": relation["relation_type"],
            "relation_authority": relation["evidence_authority"],
            "support_occurrence_count": 1,
            "source_locator_or_restricted_pointer": relation["source_locator_or_restricted_pointer"],
            "priority_reason": "S2_SUPPORTED_CANDIDATE_RELATION",
        })
    for edge in sorted((row for row in edge_rows if row["governance_state"] == "REVIEW_REQUIRED"), key=lambda row: (-int(row["source_assertion_support"]), row["semantic_relation_id"])):
        review_candidates.append({
            "semantic_relation_id": edge["semantic_relation_id"],
            "relation_type": edge["relation_type"],
            "relation_authority": edge["semantic_evidence_authority"],
            "support_occurrence_count": edge["source_assertion_support"],
            "source_locator_or_restricted_pointer": f"restricted://batch7_semantic_review/{edge['semantic_relation_id']}",
            "priority_reason": "HIGH_SUPPORT_S3_OR_MODIFIER_COMPOUND_BOUNDARY",
        })
    owner = []
    for index, item in enumerate(review_candidates[:100], start=1):
        owner.append({
            "review_item_id": stable_id("semantic-owner-review", item["semantic_relation_id"]),
            "review_rank": index,
            **item,
            "suggested_action": "REVIEW_RELATION_AND_BOUNDARY",
            "project_owner_decision": "",
            "decision_reason": "",
            "reviewer_id": "",
            "reviewed_at": "",
        })
    write_tsv(CURRENT / "SEMANTIC_RELATION_OWNER_REVIEW_PACKET.tsv", list(owner[0]), owner)
    imports = [{
        "review_item_id": row["review_item_id"],
        "semantic_relation_id": row["semantic_relation_id"],
        "allowed_decisions": "ACCEPT|REJECT|DEFER|REQUEST_EXPERT_REVIEW",
        "project_owner_decision": "",
        "decision_reason": "",
        "reviewer_id": "",
        "reviewed_at": "",
    } for row in owner]
    write_tsv(CURRENT / "SEMANTIC_RELATION_OWNER_REVIEW_IMPORT_TEMPLATE.tsv", list(imports[0]), imports)
    write_json(CURRENT / "BATCH7_SEMANTIC_MANIFEST.json", {
        "contract_version": "batch7.semantic-layer.v1",
        "source_assertion_count": len(decisions),
        "cleaned_output_atom_count": len(atoms),
        "semantic_relation_count": len(edge_rows),
        "relation_support_occurrence_count": support_occurrences,
        "relation_level_support_row_count": len(support),
        "s2_reference_source_count": 5,
        "s2_unique_relation_count": len(s2),
        "s2_target_concept_coverage_count": len({row["normalized_term_sha256"] for row in s2}),
        "unique_governed_relation_count": len(governed),
        "unique_review_required_relation_count": len(review),
        "observational_context_relation_count": len(observational),
        "s3_unique_relation_count": len(s3_unique),
        "s3_support_occurrence_count": s3_occurrences,
        "owner_review_relation_cluster_count": len(owner),
        "owner_review_decision_count": 0,
        "human_benchmark_packet_count": data_rows(CURRENT / "HUMAN_CROSS_FORM_BENCHMARK_TEMPLATE.tsv"),
        "human_benchmark_completed_count": 0,
        "benchmark": benchmark,
        "model_run": False,
        "schema_changed": False,
    })
    print(f"S2_UNIQUE_RELATION_COUNT={len(s2)}")
    print(f"RELATION_LEVEL_SUPPORT_ROW_COUNT={len(support)}")
    print(f"PRIMARY_GOVERNED_FOLD_COUNT={benchmark['primary_governed_fold_count']}")
    return 0


def current_file_receipts() -> list[dict[str, Any]]:
    excluded = {"CURRENT_DATA_MANIFEST.json", "SHA256SUMS"}
    return [
        {
            "path": path.name,
            "sha256": sha_file(path),
            "byte_count": path.stat().st_size,
            "data_row_count": data_rows(path),
        }
        for path in sorted(CURRENT.iterdir())
        if path.is_file() and path.name not in excluded
    ]


def command_checkpoint(args: argparse.Namespace) -> int:
    required = [
        "CANDIDATE_50K_SNAPSHOT_MANIFEST.json",
        "CLEANED_50K_MANIFEST.json",
        "CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv",
        "CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv",
        "BATCH7_SEMANTIC_MANIFEST.json",
        "SEMANTIC_RELATION_SUPPORT.tsv",
        "CROSS_FORM_BENCHMARK_SPLIT_MANIFEST.json",
    ]
    missing = [name for name in required if not (CURRENT / name).is_file()]
    if missing:
        raise RuntimeError(f"Batch 7 checkpoint inputs missing: {missing}")
    command_discover(args)
    manifest_path = CURRENT / "CURRENT_DATA_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot = json.loads((CURRENT / "CANDIDATE_50K_SNAPSHOT_MANIFEST.json").read_text(encoding="utf-8"))
    cleaned = json.loads((CURRENT / "CLEANED_50K_MANIFEST.json").read_text(encoding="utf-8"))
    semantic = json.loads((CURRENT / "BATCH7_SEMANTIC_MANIFEST.json").read_text(encoding="utf-8"))
    benchmark = json.loads((CURRENT / "CROSS_FORM_BENCHMARK_SPLIT_MANIFEST.json").read_text(encoding="utf-8"))
    post50 = (
        json.loads((POST50 / "POST50K_EXTENSION_MANIFEST.json").read_text(encoding="utf-8"))
        if (POST50 / "POST50K_EXTENSION_MANIFEST.json").is_file()
        else None
    )
    phase = (
        "BATCH7_50K_AND_60K_ACQUISITION_CHECKPOINT_REACHED"
        if post50 and post50.get("candidate_60k_checkpoint_reached")
        else "BATCH7_50K_CLEANED_SEMANTIC_ENGINEERING_PASS"
    )
    manifest.update({
        "active_research_branch": "research/coffee-sensory-data-ml-readiness",
        "baseline_main_sha": BASELINE_SHA,
        "phase_status": phase,
        "canonical_current_source_assertion_ledger": "CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv",
        "canonical_current_cleaned_output_ledger": "CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv",
        "candidate_50k_snapshot": snapshot,
        "cleaned_50k_view": cleaned,
        "batch7_semantic_layer": semantic,
        "batch7_cross_form_benchmark": benchmark,
        "post50k_extension": post50 or {
            "run": False,
            "status": "NA_POST50K_EXTENSION_NOT_YET_RUN",
        },
        "manifest_driven_pipeline_entrypoint": "db/scripts/descriptor-pipeline.py",
        "artifact_retention_policy": "docs/research/CORPUS_ARTIFACT_RETENTION_POLICY.md",
        "training_corpus_frozen": False,
        "model_eligible_assertion_count": 0,
        "model_training_run": False,
        "model_weight_file_count": 0,
        "schema_changed": False,
        "new_migration_count": 0,
        "files": [],
    })
    manifest["files"] = current_file_receipts()
    write_json(manifest_path, manifest)
    write_sums(CURRENT)
    if POST50.is_dir():
        write_sums(POST50)
    print(f"PHASE_STATUS={phase}")
    print(f"CANDIDATE_50K_SNAPSHOT_SHA256={sha_file(CURRENT / 'CANDIDATE_50K_SNAPSHOT_MANIFEST.json')}")
    print(f"CURRENT_SHA256SUMS={sha_file(CURRENT / 'SHA256SUMS')}")
    return 0


def command_validate(_args: argparse.Namespace) -> int:
    subprocess.run(
        [sys.executable, "-B", str(ROOT / "db" / "scripts" / "test-batch7-pipeline.py")],
        cwd=ROOT,
        check=True,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--restricted-root",
        type=Path,
        default=Path(
            os.environ.get(
                "COFFEE_FLAVOR_RESTRICTED_ROOT",
                ROOT / ".restricted-input-unavailable",
            )
        ),
        help="owner-controlled Batch 7 acquisition root",
    )
    parser.add_argument(
        "--prior-post40-root",
        type=Path,
        default=Path(
            os.environ.get(
                "POST40K_RESTRICTED_ROOT",
                ROOT / ".restricted-input-unavailable",
            )
        ),
        help="owner-controlled post-40K restricted replay root",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="require already cached restricted artifacts",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=0.25,
        help="minimum delay between network requests",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    dispatch = {
        "discover": command_discover,
        "probe": command_probe,
        "acquire": command_acquire,
        "resume": command_resume,
        "clean": command_clean,
        "semantic": command_semantic,
        "validate": command_validate,
        "checkpoint": command_checkpoint,
    }
    for name in dispatch:
        subcommands.add_parser(name)
    args = parser.parse_args()
    return dispatch[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
