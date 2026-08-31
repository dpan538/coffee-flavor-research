#!/usr/bin/env python3
"""Continue lawful CoE acquisition beyond the frozen 40k semantic view.

This is intentionally an isolated acquisition program.  It never rewrites the
40k snapshot or cleaned view and retains source-native text only in the
owner-controlled restricted root supplied at invocation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any, Iterable, Mapping


# LEGACY_REPRODUCIBILITY_ENTRYPOINT: retained for the accepted 50K receipt.
LEGACY_REPRODUCIBILITY_ENTRYPOINT = True


ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "db" / "data" / "post40k-extension-staging"
POST30_RESTRICTED = Path("/private/tmp/coffee-flavor-round3m-post30k/post30k_extension")
POST30_MANIFEST = ROOT / "db" / "data" / "post30k-extension-staging" / "POST30K_EXTENSION_MANIFEST.json"
START_PAGE = 100
START_INDEX = 3
START_URL = "https://farmdirectory.cupofexcellence.org/listing/2-la-lucuma-peru-2023/"
FROZEN_COUNT = 40030
TARGET_TOTAL = 50000
GENERATED_AT = "2026-08-30T00:00:00+10:00"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# The CoE continuation only uses Batch 2's standard-library HTML parser and
# atom helpers.  Its optional PDF/workbook source handlers are not loaded in
# this route, so make their imports explicit stubs when this lean runtime does
# not include those optional dependencies.
if "pdfplumber" not in sys.modules:
    sys.modules["pdfplumber"] = types.SimpleNamespace(open=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("PDF route unavailable in CoE-only continuation")))
if "openpyxl" not in sys.modules:
    sys.modules["openpyxl"] = types.SimpleNamespace(load_workbook=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("Workbook route unavailable in CoE-only continuation")))
B2 = load(ROOT / "db" / "scripts" / "acquire-professional-descriptors-batch2.py", "batch6_batch2_acquisition")


def fetch_retry(url: str, path: Path, *, offline: bool, delay: float) -> bool:
    last: Exception | None = None
    for attempt in range(1 if offline else 3):
        try:
            return B2.fetch(url, path, offline=offline, delay=delay if attempt == 0 else 1.0)
        except RuntimeError as error:
            last = error
    assert last is not None
    raise last


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_tsv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Iterable[str] | None = None) -> None:
    material = list(rows)
    names = list(fields or (material[0].keys() if material else []))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        for row in material:
            writer.writerow({
                field: str(row.get(field, "")).lower()
                if isinstance(row.get(field, ""), bool)
                else row.get(field, "")
                for field in names
            })


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_manifest(public: Path, document: Mapping[str, Any]) -> None:
    (public / "POST40K_EXTENSION_MANIFEST.json").write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths = sorted(path for path in public.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (public / "SHA256SUMS").write_text("".join(f"{sha(path)}  {path.name}\n" for path in paths), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restricted-root", type=Path, required=True)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--request-delay", type=float, default=0.2)
    args = parser.parse_args()
    public = PUBLIC
    public.mkdir(parents=True, exist_ok=True)
    restricted = args.restricted_root / "post40k_extension"
    raw = restricted / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    prior_path = POST30_RESTRICTED / "POST30K_ASSERTIONS_RESTRICTED.tsv"
    if not prior_path.is_file():
        raise RuntimeError(f"missing required prior restricted ledger: {prior_path}")
    prior_urls = {row["source_url"] for row in read_tsv(prior_path)}
    atoms: list[Any] = []
    cursor_by_record: dict[str, str] = {}
    artifact_rows: list[dict[str, Any]] = []
    cursor_end = START_URL
    blocked = False
    exhausted = False
    exact_cursor_validated = False
    coe_records = 0
    for page in range(START_PAGE, B2.MAX_COE_ARCHIVE_PAGES + 1):
        archive = raw / "coe-archive" / f"listings-page-{page:03d}.html"
        try:
            fetch_retry(B2.coe_archive_url(page), archive, offline=args.offline, delay=args.request_delay)
        except RuntimeError as error:
            cursor_end = f"retry-archive-page={page};error={type(error).__name__}"
            blocked = True
            break
        urls = sorted(B2.coe_archive_links(archive.read_text(encoding="utf-8", errors="replace")))
        artifact_rows.append({"source_route_id": "route.coe.post40k-archive-continuation", "source_url": B2.coe_archive_url(page), "restricted_relative_path": archive.relative_to(restricted).as_posix(), "sha256": sha(archive), "byte_count": archive.stat().st_size, "acquisition_cursor": f"archive-page={page}"})
        if page == START_PAGE:
            if len(urls) < START_INDEX or urls[START_INDEX - 1] != START_URL:
                raise RuntimeError("preserved post-40k CoE cursor no longer matches archive page 100")
            exact_cursor_validated = True
        if not urls:
            cursor_end = f"archive-page={page};NO_LISTING_LINKS"
            exhausted = True
            break
        first = START_INDEX if page == START_PAGE else 1
        for index, url in enumerate(urls, start=1):
            if index < first or url in prior_urls:
                continue
            if FROZEN_COUNT + sum(atom.counts_as_assertion for atom in atoms) >= TARGET_TOTAL:
                cursor_end = f"archive-page={page};detail-index={index};url={url}"
                break
            detail = raw / "coe-detail" / f"{hashlib.sha256(url.encode()).hexdigest()[:24]}.html"
            try:
                fetch_retry(url, detail, offline=args.offline, delay=args.request_delay)
            except RuntimeError as error:
                cursor_end = f"retry-archive-page={page};detail-index={index};error={type(error).__name__}"
                blocked = True
                break
            record_atoms = B2.parse_coe_detail(detail, url)
            B2.apply_deinflation(record_atoms)
            if record_atoms:
                atoms.extend(record_atoms)
                coe_records += 1
                cursor = f"archive-page={page};detail-index={index};url={url}"
                cursor_end = cursor
                for atom in record_atoms:
                    cursor_by_record[atom.effective_record_id] = cursor
                artifact_rows.append({"source_route_id": record_atoms[0].source_route, "source_url": url, "restricted_relative_path": detail.relative_to(restricted).as_posix(), "sha256": sha(detail), "byte_count": detail.stat().st_size, "acquisition_cursor": cursor})
        if blocked or FROZEN_COUNT + sum(atom.counts_as_assertion for atom in atoms) >= TARGET_TOTAL:
            break
    else:
        exhausted = True
        cursor_end = "EXHAUSTED_COE_ARCHIVE"
    B2.apply_deinflation(atoms)
    safe_rows = []
    for atom, safe in zip(atoms, B2.safe_rows(atoms)):
        item = dict(safe)
        item.pop("publisher", None)
        item["publisher_id"] = B2.stable_id("publisher", atom.source_family)
        item.update({"extension_batch_id": "professional-descriptor-post40k-extension-20260830", "source_field_label": "hash:sha256:" + hashlib.sha256(atom.source_field_label.encode()).hexdigest(), "parser_version": "post40k.professional-descriptor-parser.v1", "adapter_version": "post40k.public-safe-adapter.v1", "acquisition_cursor": cursor_by_record[atom.effective_record_id], "frozen_snapshot_version": "professional-descriptor-candidate-v2-40k", "frozen_snapshot_member": False})
        safe_rows.append(item)
    restricted_rows = list(B2.restricted_rows(atoms))
    restricted_ledger = restricted / "POST40K_ASSERTIONS_RESTRICTED.tsv"
    restricted_artifacts = restricted / "POST40K_RAW_ARTIFACT_RECEIPT.tsv"
    write_tsv(restricted_ledger, restricted_rows)
    write_tsv(restricted_artifacts, artifact_rows)
    write_tsv(public / "POST40K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv", safe_rows, list(safe_rows[0]) if safe_rows else ["extension_batch_id", "descriptor_assertion_id", "frozen_snapshot_member"])
    write_tsv(public / "POST40K_PUBLIC_ARTIFACT_RECEIPT.tsv", [{**row, "restricted_relative_path": "restricted://post40k_extension/" + row["restricted_relative_path"]} for row in artifact_rows], list(artifact_rows[0]) if artifact_rows else ["source_route_id", "source_url", "restricted_relative_path"])
    routes = [{"source_family_id": B2.COE["family"], "source_route_id": "route.coe.post40k-archive-continuation", "discovery_lane": "COE_CONTINUATION", "artifacts_inspected": len(artifact_rows), "descriptor_bearing_records": coe_records, "raw_assertion_count": len(atoms), "deinflated_assertion_count": sum(atom.counts_as_assertion for atom in atoms), "rights_state": "MIXED_PENDING_UNKNOWN", "disposition": "CHECKPOINT_50000_REACHED" if FROZEN_COUNT + sum(atom.counts_as_assertion for atom in atoms) >= TARGET_TOTAL else "PARTIAL_BLOCKED_OR_EXHAUSTED", "basis": "EXACT_POST30K_CURSOR_CONTINUATION"}]
    write_tsv(public / "POST40K_SOURCE_ROUTE_DISCOVERY.tsv", routes)
    write_tsv(public / "POST40K_SEMANTIC_YIELD.tsv", [{"route_scope": "POST40K_COE_CONTINUATION", "new_cleaned_forms": "NA_POST40K_STAGING_NOT_MERGED_INTO_FROZEN_40K_VIEW", "new_known_target_forms": "NA_POST40K_STAGING_NOT_MERGED_INTO_FROZEN_40K_VIEW", "new_cross_family_target_overlaps": "NA_POST40K_STAGING_NOT_MERGED_INTO_FROZEN_40K_VIEW", "assertion_count": sum(atom.counts_as_assertion for atom in atoms), "source": "COE"}])
    manifest = {"contract_version": "post40k-extension-manifest.v1", "extension_batch_id": "professional-descriptor-post40k-extension-20260830", "generated_at": GENERATED_AT, "run": True, "frozen_snapshot_version": "professional-descriptor-candidate-v2-40k", "frozen_denominator_assertion_count": FROZEN_COUNT, "extension_isolated_from_frozen_snapshot": True, "cursor_start": f"archive-page={START_PAGE};detail-index={START_INDEX};url={START_URL}", "cursor_end": cursor_end, "exact_cursor_validated": exact_cursor_validated, "coe_route_exhausted": exhausted, "coe_continuation_blocked": blocked, "net_new_raw_assertion_count": len(atoms), "net_new_deinflated_assertion_count": sum(atom.counts_as_assertion for atom in atoms), "net_new_effective_record_count": len({atom.effective_record_id for atom in atoms if atom.counts_as_assertion}), "new_coe_assertion_count": sum(atom.counts_as_assertion for atom in atoms), "new_non_coe_assertion_count": 0, "new_non_coe_positive_family_count": 0, "new_rights_clearable_family_count": 0, "non_coe_discovery_effort_rate": 0.0, "non_coe_discovery_effort_shortfall": "NO_NEW_NON_COE_ROUTE_EXECUTED_DURING_COE_CONTINUATION", "total_candidate_count": FROZEN_COUNT + sum(atom.counts_as_assertion for atom in atoms), "checkpoint_50000_reached": FROZEN_COUNT + sum(atom.counts_as_assertion for atom in atoms) >= TARGET_TOTAL, "hard_stop_rule": "FIRST_COMPLETE_EFFECTIVE_RECORD_BOUNDARY_AT_OR_ABOVE_TOTAL_50000", "restricted_assertion_ledger_sha256": sha(restricted_ledger), "restricted_artifact_receipt_sha256": sha(restricted_artifacts), "model_eligible_assertion_count": 0, "human_reviewed_assertion_count": 0, "schema_changed": False, "new_migration_count": 0, "model_training_run": False, "files": []}
    for path in sorted(public.glob("*.tsv")):
        manifest["files"].append({"path": path.name, "sha256": sha(path), "byte_count": path.stat().st_size, "data_row_count": max(sum(1 for _ in path.open(encoding="utf-8")) - 1, 0)})
    write_manifest(public, manifest)
    print(f"POST40K_EXTENSION_DEINFLATED={manifest['net_new_deinflated_assertion_count']}")
    print(f"POST40K_TOTAL_CANDIDATE={manifest['total_candidate_count']}")
    print(f"POST40K_CURSOR_END={cursor_end}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
