#!/usr/bin/env python3
"""Round 3 — ingest the owner-reviewed CoffeeReview Kaggle scrape as a source family.

WHAT THIS IS
    coffee_reviews_parsed.csv: 8,387 reviews, 2000-2025, one review per URL, with
    the Blind Assessment text that carries the named descriptors. Measured
    before writing this: 6,396 reviews carry >= 2 registry descriptors and all
    56 registry words appear, including all 36 that no question axis reaches.

RIGHTS
    Scraped editorial content. Approved by the owner for this project's
    internal research after manual review (R3-D2, owner_decisions_round3.json).
    Encoded as rights=AFFIRMATIVE_WITH_CONDITIONS with an explicit basis token
    so every downstream filter can tell it from a CC-licensed family. Not a
    tier-wide policy: this file, reviewed by the owner, nothing else.

WHY THE TEXT IS PRE-EXTRACTED
    B2.split_atomic splits a field on commas and semicolons; it expects a
    descriptor list, not prose. A Blind Assessment is prose: "Crisply sweet,
    cocoa-toned. Lemon blossom, roasted cacao nib, date, rice candy, white
    peppercorn in aroma and cup. Savory-tart structure; delicate, silky
    mouthfeel." Splitting the whole paragraph yields fragments like "Crisply
    sweet" and "Savory-tart structure". CoffeeReview's house style puts the
    descriptor list in one sentence ending "in aroma and cup", so that sentence
    is extracted and only it is handed to make_atoms. Reviews without that
    sentence are counted, not guessed at.

WHERE THINGS GO
    Public (git):     db/data/coffeereview-round3-staging/   hashes, ids, pointers
    Restricted root:  $COFFEE_FLAVOR_RESTRICTED_ROOT/coffee-flavor-round3-coffeereview/
                      source-native text, never committed
    The restricted root must not be inside any git tree and must not be under
    /tmp. Both are checked at startup. The second check exists because every
    earlier restricted root lived under /private/tmp and macOS deleted them all
    (F18).

Reuses B2 (acquire-professional-descriptors-batch2.py) for make_atoms,
normalize, apply_deinflation, safe_rows and restricted_rows, so this family is
shaped exactly like the others. No model, no admission, fit count 0.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "db" / "data" / "coffeereview-round3-staging"
B2_PATH = ROOT / "db" / "scripts" / "acquire-professional-descriptors-batch2.py"

DEFAULT_RESTRICTED_ROOT = Path.home() / "Desktop" / "Coffee_Flavor_Restricted"
FAMILY_DIR = "coffee-flavor-round3-coffeereview"
SOURCE_REL = Path("sources") / "coffeereview_kaggle" / "coffee_reviews_parsed.csv"

SOURCE = {
    "url": "https://www.kaggle.com/datasets/schmoyote/coffee-reviews-dataset",
    "filename": "coffee_reviews_parsed.csv",
    "family": "family.coffeereview_kaggle_parsed",
    "route": "route.coffeereview.kaggle-parsed-2000-2025.blind-assessment",
    "schema": "schema.coffeereview.parsed-review-csv.v1",
    "publisher": "Coffee Review (coffeereview.com); Kaggle scrape (schmoyote)",
    "language": "en",
    "rights": "AFFIRMATIVE_WITH_CONDITIONS",
    "rights_basis": "OWNER_MANUAL_REVIEW_APPROVAL_R3_D2_SCRAPED_EDITORIAL_INTERNAL_RESEARCH_ONLY",
    # P2 / SILVER: a professional panel, but a single organisation's editorial
    # cupping rather than a certified Q-grader protocol. Owner may raise.
    "evidence_tier": "P2",
    "collection_tier": "SILVER",
}

# The descriptor list sentence. CoffeeReview house style, stable since 2000.
LIST_SENTENCE = re.compile(
    r"(?:^|\.\s*)([^.]+?)\s+in\s+(?:the\s+)?(?:aroma\s+and\s+(?:the\s+)?cup|aroma|cup)\b",
    re.I,
)
ESPRESSO = re.compile(r"^\s*evaluated as espresso", re.I)
YEAR = re.compile(r"\b(19|20)\d{2}\b")


def load_b2():
    # B2 imports pdfplumber at module level for its PDF parsers (India, Isla,
    # generic cupping PDF). This script uses only B2's text path -- make_atoms,
    # normalize, stable_id, apply_deinflation, safe_rows, restricted_rows -- so
    # the package is stubbed rather than installed. The project declares no
    # requirements file to record it in, and the stub raises a clear error if
    # anything reaches for a PDF parser through this module.
    if "pdfplumber" not in sys.modules:
        try:
            import pdfplumber  # noqa: F401  (use the real one when present)
        except ModuleNotFoundError:
            import types
            stub = types.ModuleType("pdfplumber")
            def _missing(name):
                raise RuntimeError(
                    f"pdfplumber.{name}: pdfplumber is stubbed by acquire-coffeereview-round3; "
                    "PDF parsers are not used on this path")
            stub.__getattr__ = _missing
            sys.modules["pdfplumber"] = stub
    spec = importlib.util.spec_from_file_location("b2", B2_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["b2"] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inside_git_tree(path: Path) -> bool:
    try:
        out = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
        return out.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def require_restricted_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    tmp_roots = {Path("/tmp").resolve(), Path("/private/tmp").resolve()}
    if any(resolved == t or resolved.is_relative_to(t) for t in tmp_roots):
        raise SystemExit(f"restricted root must not be under /tmp (F18): {resolved}")
    if resolved.is_relative_to(ROOT.resolve()):
        raise SystemExit(f"restricted root must not be inside the repository: {resolved}")
    if resolved.exists() and inside_git_tree(resolved):
        raise SystemExit(f"restricted root must not be inside any git tree: {resolved}")
    return resolved


def extract_descriptor_list(blind: str) -> str | None:
    m = LIST_SENTENCE.search(blind)
    if not m:
        return None
    text = m.group(1).strip()
    # drop a leading "Evaluated as espresso." style preface that survived the split
    text = re.sub(r"^(evaluated as [a-z ]+\.\s*)", "", text, flags=re.I)
    return text or None


def parse_coffeereview(b2, source: dict[str, str], path: Path) -> tuple[list[list[Any]], dict[str, int]]:
    artifact_hash = sha256_file(path)
    result: list[list[Any]] = []
    stats = {"rows": 0, "blind_assessment_empty": 0, "no_list_sentence": 0,
             "espresso": 0, "records_with_atoms": 0}
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        for row_number, row in enumerate(csv.DictReader(fh), 2):
            stats["rows"] += 1
            url = (row.get("URL") or "").strip()
            blind = (row.get("Blind Assessment") or "").strip()
            if not url or not blind:
                stats["blind_assessment_empty"] += 1
                continue
            listed = extract_descriptor_list(blind)
            if not listed:
                stats["no_list_sentence"] += 1
                continue
            prep = "ESPRESSO" if ESPRESSO.search(blind) else "CUPPING"
            if prep == "ESPRESSO":
                stats["espresso"] += 1
            date = (row.get("Review Date") or "").strip()
            year_match = YEAR.search(date)
            year = year_match.group(0) if year_match else "UNREPORTED"
            roast_level = (row.get("Roast Level") or "").strip()
            agtron = (row.get("Agtron") or "").strip()
            roast = "; ".join(p for p in (roast_level, f"Agtron {agtron}" if agtron else "") if p) or "UNREPORTED"
            effective = b2.stable_id("effective-b2", source["route"], url, "BLIND_ASSESSMENT")
            coffee = b2.stable_id("coffee-b2", source["route"], url)
            record_atoms = b2.make_atoms(
                source=source,
                artifact_sha256=artifact_hash,
                source_url=url,
                source_locator=f"csv:{path.name}#row={row_number};url={url};field=Blind Assessment;sentence=aroma-and-cup",
                effective_record_id=effective,
                coffee_identity_id=coffee,
                edition_or_release=date or "UNREPORTED",
                edition_year=year,
                preparation_service=prep,
                roast_evidence=roast,
                source_field_label="Blind Assessment (aroma-and-cup descriptor list)",
                raw_field_text=listed,
                publication_layer="PANEL_PUBLISHED_BLIND_ASSESSMENT",
                provenance_state="OWNER_REVIEWED_KAGGLE_SCRAPE_OF_PUBLISHED_REVIEW",
                judge_observation_id="",
            )
            if record_atoms:
                stats["records_with_atoms"] += 1
                result.append(record_atoms)
    return result, stats


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else ["descriptor_assertion_id"])
    with path.open("w", encoding="utf-8", newline="") as fh:
        # lineterminator="\n" as every other family writes: csv.DictWriter defaults to
        # \r\n, git then normalises the blob to LF, and the manifest hash computed on
        # the CRLF working copy no longer matches the committed file (ROUND3-OP9).
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restricted-root", type=Path,
                        default=Path(os.environ.get("COFFEE_FLAVOR_RESTRICTED_ROOT", str(DEFAULT_RESTRICTED_ROOT))))
    parser.add_argument("--public-dir", type=Path, default=PUBLIC)
    args = parser.parse_args()

    restricted_root = require_restricted_root(args.restricted_root)
    source_path = restricted_root / SOURCE_REL
    if not source_path.is_file():
        raise SystemExit(f"source file missing under restricted root: {source_path}")
    family_dir = restricted_root / FAMILY_DIR
    family_dir.mkdir(parents=True, exist_ok=True)
    args.public_dir.mkdir(parents=True, exist_ok=True)

    b2 = load_b2()
    started = time.time()
    records, stats = parse_coffeereview(b2, SOURCE, source_path)
    atoms = [a for rec in records for a in rec]
    raw_count = len(atoms)
    assertion_losses, record_losses = b2.apply_deinflation(atoms)
    deinflated = sum(1 for a in atoms if a.counts_as_assertion)

    safe_rows: list[dict[str, Any]] = []
    for atom, safe in zip(atoms, b2.safe_rows(atoms)):
        item = dict(safe)
        item.pop("publisher", None)  # precedent: post40k publishes an id, not the name
        item["publisher_id"] = b2.stable_id("publisher", atom.source_family)
        item["extension_batch_id"] = "coffeereview-round3-kaggle-parsed-20260911"
        item["source_field_label"] = "hash:sha256:" + hashlib.sha256(atom.source_field_label.encode()).hexdigest()
        item["parser_version"] = "round3.coffeereview-blind-assessment-parser.v1"
        item["adapter_version"] = "b2.public-safe-adapter"
        # Schema parity with the CoE staging sidecars, which descriptor-pipeline.py
        # and generate-batch6-semantic-corpus.py read. This family is not a CoE
        # archive continuation, so the values are explicit, not blank.
        item["acquisition_cursor"] = atom.source_locator.split(";url=")[0]  # csv:<file>#row=N
        item["frozen_snapshot_version"] = "NA_NOT_A_COE_CONTINUATION"
        item["frozen_snapshot_member"] = False
        safe_rows.append(item)
    restricted_rows = list(b2.restricted_rows(atoms))

    restricted_ledger = family_dir / "COFFEEREVIEW_ASSERTIONS_RESTRICTED.tsv"
    write_tsv(restricted_ledger, restricted_rows)
    sidecar = args.public_dir / "COFFEEREVIEW_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv"
    write_tsv(sidecar, safe_rows)

    classes: dict[str, int] = {}
    for a in atoms:
        if a.counts_as_assertion:
            classes[a.descriptor_class] = classes.get(a.descriptor_class, 0) + 1

    manifest = {
        "contract_version": "coffeereview-round3-manifest.v1",
        "extension_batch_id": "coffeereview-round3-kaggle-parsed-20260911",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - started, 1),
        "source": {k: v for k, v in SOURCE.items()},
        "owner_decision": "round3/owner_decisions_round3.json#R3-D2",
        "source_file_sha256": sha256_file(source_path),
        "restricted_root_environment_variable": "COFFEE_FLAVOR_RESTRICTED_ROOT",
        "restricted_family_dir": FAMILY_DIR,
        "extraction": stats,
        "raw_atom_count": raw_count,
        "deinflation": {"assertion_losses": assertion_losses, "record_losses": record_losses},
        "deinflated_assertion_count": deinflated,
        "effective_record_count": len({a.effective_record_id for a in atoms if a.counts_as_assertion}),
        "coffee_identity_count": len({a.coffee_identity_id for a in atoms if a.counts_as_assertion}),
        "descriptor_class_counts": classes,
        "restricted_assertion_ledger_sha256": sha256_file(restricted_ledger),
        "public_files": [{"path": sidecar.name, "sha256": sha256_file(sidecar), "data_row_count": len(safe_rows)}],
        "guards": {"source_native_text_in_public_output": False, "model_eligible_assertion_count": 0,
                   "records_admitted": 0, "fit_count": 0, "schema_changed": False},
    }
    (args.public_dir / "COFFEEREVIEW_ROUND3_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("extraction", "raw_atom_count", "deinflated_assertion_count",
                                               "effective_record_count", "descriptor_class_counts")},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
