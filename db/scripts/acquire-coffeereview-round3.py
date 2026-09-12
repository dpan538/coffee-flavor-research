#!/usr/bin/env python3
"""Round 3 — ingest the owner-reviewed CoffeeReview Kaggle scrape as a source family.

WHAT THIS IS
    coffee_reviews_parsed.csv: 8,387 reviews, 1997-2025, one review per URL, with
    the Blind Assessment text that carries the named descriptors. Measured
    before writing this: 6,396 reviews carry >= 2 registry descriptors and all
    56 registry words appear, including all 36 that no question axis reaches.

PARSER VERSIONS
    v1 (frozen, 77K checkpoint): the "... in aroma and cup" sentence only.
    6,180 reviews / 27,004 assertions; hit rate collapses before 2012.
    v2 (CR-2, 83K checkpoint): v1 unchanged (same atom ids) plus four extra
    sentence shapes and a bare-list fallback, each under its own pattern id in
    the source locator. 7,300 reviews / 32,996 assertions; +5,992 of which
    3,610 come from 2004-2011. Quality per pattern (registry-word rate, words
    per atom) is measured in round3/cr2_parser_v2_finding.json.

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


# Parser v2 (CR-2). v1 covers the post-2012 house style ("... in aroma and cup");
# before 2012 the same reviews list their descriptors in other sentence shapes.
# Measured on the 8,387 reviews: v1 hit rate 5-25% for 1997-2003, 30-45% for
# 2004-2011, >90% from 2013. Each extra shape is its own pattern id so the atoms
# it yields stay measurable and revocable. v1 atoms keep their locator and ids;
# the v1 sentence is masked before the v2 shapes run so nothing is captured twice.
PARSER_VERSIONS = ("v1", "v2")
COLON_LIST = re.compile(r"\b(?:aroma|cup|nose|flavou?rs?|notes)\s*:\s*([^.;]+)", re.I)
IN_CUP_PREFIX = re.compile(r"(?:^|\.\s*)in\s+the\s+(?:small\s+)?(?:aroma|cup|finish)\s*[,:]?\s*([^.]+)", re.I)
NOTES_OF = re.compile(
    r"\b(?:notes?|hints?|suggestions?|nuances?|flavou?rs?|touch(?:es)?)\s+of\s+"
    r"(.+?)(?=\s+in\s+(?:the\s+)?(?:aroma|cup|finish)\b|\s+(?:that|which|as|while|when)\b|[.;]|$)", re.I)
AROMA_THROUGH = re.compile(
    r"(?:^|\.\s*)([^.;]+?)\s+(?:runs?|carry|carries|carried|persists?|persisting|continues?|threads?)"
    r"\s+(?:through|throughout|from)\s+(?:the\s+)?aroma\b", re.I)
# items that describe structure, the tasting setup, or a clause rather than a descriptor
ITEM_EXCLUDE = re.compile(
    r"\b(?:acidity|acidy|mouthfeel|body|finish(?:es|ing)?|structure|sweetness|balance|aftertaste|roast|"
    r"evaluated|tested|brewed|rating|points?|is|are|was|were|has|have|had|that|which|but|though|"
    r"although|as|by|this|fades?|persists?|turns?|emerges?|dominates?|becomes?|carries|continues?)\b|\d", re.I)
ITEM_PREFIX = re.compile(
    r"^(?:(?:a|an|the|some|more|with|of|and|plus|also|very|slightly|slight|distinct|distinctly|continuing|continued)\s+)+"
    r"|^(?:(?:a\s+)?(?:hints?|notes?|touch(?:es)?|suggestions?|nuances?|whiffs?)\s+of\s+)", re.I)
ITEM_MAX_WORDS = 4
V2_PATTERNS = (
    ("aroma-colon", COLON_LIST),
    ("in-the-cup-prefix", IN_CUP_PREFIX),
    ("notes-of", NOTES_OF),
    ("aroma-through-cup", AROMA_THROUGH),
)


def clean_v2_items(text: str) -> str | None:
    """Keep only descriptor-shaped items of a captured list (v2 shapes only; v1 is frozen)."""
    kept: list[str] = []
    for raw in re.split(r"[,;]", text):
        item = raw.strip(" .,:;\t\n\"'")
        item = re.sub(r"\s*\([^)]*\)", "", item).strip()
        while True:  # "a hint of milk chocolate": article, then hedge, then article again
            stripped = ITEM_PREFIX.sub("", item).strip(" \"'")
            if stripped == item:
                break
            item = stripped
        if not item or len(item.split()) > ITEM_MAX_WORDS or ITEM_EXCLUDE.search(item):
            continue
        kept.append(item)
    return ", ".join(kept) if kept else None


def bare_list_sentence(blind: str) -> str | None:
    """Post-2012 reviews without the v1 sentence list their descriptors as a bare
    sentence of >= 4 short items (the 3-item adjective opener is not a list)."""
    best: tuple[int, str] | None = None
    for sentence in re.split(r"(?<=[.!?])\s+", blind):
        core = sentence.strip().rstrip(".!?").strip()
        items = [item.strip() for item in re.split(r"[,;]", core) if item.strip()]
        if len(items) < 4 or re.search(r"\b(?:in|on|to|for|from|with|of|the|and\s+a)\b|\d", core, re.I):
            continue
        if any(len(item.split()) > ITEM_MAX_WORDS or ITEM_EXCLUDE.search(item) for item in items):
            continue
        if best is None or len(items) > best[0]:
            best = (len(items), core)
    return best[1] if best else None


def extract_descriptor_lists(blind: str, version: str = "v1") -> list[tuple[str, str]]:
    """[(pattern_id, list_text)]; the v1 sentence always comes first under its v1 id."""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    masked = blind
    m = LIST_SENTENCE.search(blind)
    v1 = extract_descriptor_list(blind)
    if v1:
        found.append(("aroma-and-cup", v1))
        seen.add(v1.casefold())
        masked = blind[:m.start()] + ". " + blind[m.end():]
    if version == "v1":
        return found
    for pattern_id, pattern in V2_PATTERNS:
        for hit in pattern.finditer(masked):
            text = clean_v2_items(hit.group(1))
            if not text or text.casefold() in seen:
                continue
            seen.add(text.casefold())
            found.append((pattern_id, text))
    if not v1:
        bare = bare_list_sentence(masked)
        if bare:
            text = clean_v2_items(bare)
            if text and text.casefold() not in seen:
                found.append(("bare-list", text))
    return found


def parse_coffeereview(b2, source: dict[str, str], path: Path, version: str = "v1") -> tuple[list[list[Any]], dict[str, Any]]:
    artifact_hash = sha256_file(path)
    result: list[list[Any]] = []
    stats: dict[str, Any] = {"parser_version": version, "rows": 0, "blind_assessment_empty": 0, "no_list_sentence": 0,
                             "espresso": 0, "records_with_atoms": 0, "pattern_reviews": {}, "pattern_raw_atoms": {}}
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        for row_number, row in enumerate(csv.DictReader(fh), 2):
            stats["rows"] += 1
            url = (row.get("URL") or "").strip()
            blind = (row.get("Blind Assessment") or "").strip()
            if not url or not blind:
                stats["blind_assessment_empty"] += 1
                continue
            extractions = extract_descriptor_lists(blind, version)
            if not extractions:
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
            record_atoms: list[Any] = []
            for pattern_id, listed in extractions:
                pattern_atoms = b2.make_atoms(
                    source=source,
                    artifact_sha256=artifact_hash,
                    source_url=url,
                    source_locator=f"csv:{path.name}#row={row_number};url={url};field=Blind Assessment;sentence={pattern_id}",
                    effective_record_id=effective,
                    coffee_identity_id=coffee,
                    edition_or_release=date or "UNREPORTED",
                    edition_year=year,
                    preparation_service=prep,
                    roast_evidence=roast,
                    source_field_label=f"Blind Assessment ({pattern_id} descriptor list)",
                    raw_field_text=listed,
                    publication_layer="PANEL_PUBLISHED_BLIND_ASSESSMENT",
                    provenance_state="OWNER_REVIEWED_KAGGLE_SCRAPE_OF_PUBLISHED_REVIEW",
                    judge_observation_id="",
                )
                if pattern_atoms:
                    stats["pattern_reviews"][pattern_id] = stats["pattern_reviews"].get(pattern_id, 0) + 1
                    stats["pattern_raw_atoms"][pattern_id] = stats["pattern_raw_atoms"].get(pattern_id, 0) + len(pattern_atoms)
                    record_atoms.extend(pattern_atoms)
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
            # Booleans as "true"/"false", the convention every other writer in
            # this project follows (B2.write_tsv, post40k.write_tsv, pipeline
            # scalar()). Python's default "True"/"False" made the pipeline's
            # counts_as_assertion == "true" filter select 0 rows (ROUND3-OP10).
            w.writerow({k: (str(v).lower() if isinstance(v, bool) else v) for k, v in r.items()})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restricted-root", type=Path,
                        default=Path(os.environ.get("COFFEE_FLAVOR_RESTRICTED_ROOT", str(DEFAULT_RESTRICTED_ROOT))))
    parser.add_argument("--public-dir", type=Path, default=PUBLIC)
    parser.add_argument("--parser", choices=PARSER_VERSIONS, default="v1",
                        help="v1: the frozen 77K extraction; v2: CR-2 sentence shapes (measured before adoption)")
    parser.add_argument("--restricted-out", type=Path, default=None,
                        help="override the restricted family dir (measurement runs); same /tmp and git-tree rules apply")
    args = parser.parse_args()

    restricted_root = require_restricted_root(args.restricted_root)
    source_path = restricted_root / SOURCE_REL
    if not source_path.is_file():
        raise SystemExit(f"source file missing under restricted root: {source_path}")
    family_dir = require_restricted_root(args.restricted_out) if args.restricted_out else restricted_root / FAMILY_DIR
    family_dir.mkdir(parents=True, exist_ok=True)
    args.public_dir.mkdir(parents=True, exist_ok=True)

    b2 = load_b2()
    started = time.time()
    records, stats = parse_coffeereview(b2, SOURCE, source_path, args.parser)
    batch_id = "coffeereview-round3-kaggle-parsed-20260911" if args.parser == "v1" else "coffeereview-round3-kaggle-parsed-v2-20260912"
    atoms = [a for rec in records for a in rec]
    raw_count = len(atoms)
    assertion_losses, record_losses = b2.apply_deinflation(atoms)
    deinflated = sum(1 for a in atoms if a.counts_as_assertion)

    safe_rows: list[dict[str, Any]] = []
    for atom, safe in zip(atoms, b2.safe_rows(atoms)):
        item = dict(safe)
        item.pop("publisher", None)  # precedent: post40k publishes an id, not the name
        item["publisher_id"] = b2.stable_id("publisher", atom.source_family)
        item["extension_batch_id"] = batch_id
        item["source_field_label"] = "hash:sha256:" + hashlib.sha256(atom.source_field_label.encode()).hexdigest()
        item["parser_version"] = f"round3.coffeereview-blind-assessment-parser.{args.parser}"
        item["adapter_version"] = "b2.public-safe-adapter"
        # Schema parity with the CoE staging sidecars, which descriptor-pipeline.py
        # and generate-batch6-semantic-corpus.py read. This family is not a CoE
        # archive continuation, so the values are explicit, not blank.
        item["acquisition_cursor"] = atom.source_locator.split(";url=")[0]  # csv:<file>#row=N
        item["frozen_snapshot_version"] = "NA_NOT_A_COE_CONTINUATION"
        item["frozen_snapshot_member"] = False
        safe_rows.append(item)
    restricted_rows = list(b2.restricted_rows(atoms))

    # v1 names are frozen with the 77K checkpoint; v2 writes beside them so both
    # checkpoints stay reproducible from the same restricted root.
    suffix = "" if args.parser == "v1" else "_V2"
    restricted_ledger = family_dir / f"COFFEEREVIEW_ASSERTIONS_RESTRICTED{suffix}.tsv"
    write_tsv(restricted_ledger, restricted_rows)
    sidecar = args.public_dir / f"COFFEEREVIEW_PUBLIC_SAFE_ASSERTION_SIDECAR{suffix}.tsv"
    write_tsv(sidecar, safe_rows)

    classes: dict[str, int] = {}
    for a in atoms:
        if a.counts_as_assertion:
            classes[a.descriptor_class] = classes.get(a.descriptor_class, 0) + 1

    manifest = {
        "contract_version": "coffeereview-round3-manifest.v1",
        "parser_version": args.parser,
        "extension_batch_id": batch_id,
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
    (args.public_dir / f"COFFEEREVIEW_ROUND3_MANIFEST{suffix}.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("extraction", "raw_atom_count", "deinflated_assertion_count",
                                               "effective_record_count", "descriptor_class_counts")},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
