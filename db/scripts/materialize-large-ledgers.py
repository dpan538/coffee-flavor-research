#!/usr/bin/env python3
"""The two source-assertion ledgers are larger than GitHub's 100 MiB file limit. They used to live in Git LFS; every CI
run that needed them downloaded about 211 MB, and once the account's monthly LFS bandwidth was used up the database
jobs could not check the repository out at all (owner, 2026-09-20: "I do not want to depend on LFS every time").

They are now stored in plain git as xz archives (about 5 MB each) in db/data/large-ledger-archives/ — a directory of
their own, because db/data/current has an exact file inventory that a contract checks — and this script writes the
ledgers back to db/data/current byte for byte:

    python3 db/scripts/materialize-large-ledgers.py            write the ledgers that are missing or differ, verify all
    python3 db/scripts/materialize-large-ledgers.py --check    verify only; non-zero exit if a ledger is missing or differs
    python3 db/scripts/materialize-large-ledgers.py --pack     rebuild the archives from the ledgers on disk (after a
                                                               ledger legitimately changed) and rewrite the manifest

The manifest (LARGE_LEDGER_ARCHIVES.tsv) pins the SHA-256 and size of every ledger, so a ledger is exactly what it was
under LFS: the readers, the hash contracts and the replay see the same bytes. The ledgers themselves are git-ignored.
Python's standard library only (lzma), so it runs in the bare postgres container as well.
"""
from __future__ import annotations

import csv
import hashlib
import lzma
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "db/data/large-ledger-archives/LARGE_LEDGER_ARCHIVES.tsv"
FIELDS = ["ledger_path", "archive_path", "ledger_sha256", "ledger_bytes"]
CHUNK = 1 << 20


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def entries() -> list[dict[str, str]]:
    with MANIFEST.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def intact(entry: dict[str, str]) -> bool:
    ledger = ROOT / entry["ledger_path"]
    return (
        ledger.is_file()
        and ledger.stat().st_size == int(entry["ledger_bytes"])
        and sha256(ledger) == entry["ledger_sha256"]
    )


def unpack(entry: dict[str, str]) -> None:
    ledger = ROOT / entry["ledger_path"]
    partial = ledger.with_suffix(ledger.suffix + ".partial")
    with lzma.open(ROOT / entry["archive_path"], "rb") as source, partial.open("wb") as target:
        for block in iter(lambda: source.read(CHUNK), b""):
            target.write(block)
    partial.replace(ledger)


def pack() -> None:
    rows = []
    for entry in entries():
        ledger, archive = ROOT / entry["ledger_path"], ROOT / entry["archive_path"]
        # one thread and a fixed preset: the same ledger always gives the same archive
        with ledger.open("rb") as source, lzma.open(archive, "wb", preset=9 | lzma.PRESET_EXTREME) as target:
            for block in iter(lambda: source.read(CHUNK), b""):
                target.write(block)
        rows.append({**entry, "ledger_sha256": sha256(ledger), "ledger_bytes": str(ledger.stat().st_size)})
        print(f"LARGE_LEDGER_PACKED={entry['archive_path']} bytes={archive.stat().st_size}")
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "--pack":
        pack()
    failures = 0
    for entry in entries():
        if not intact(entry):
            if mode == "--check":
                print(f"LARGE_LEDGER_MISSING_OR_DIFFERENT={entry['ledger_path']}")
                failures += 1
                continue
            unpack(entry)
            if not intact(entry):
                print(f"LARGE_LEDGER_ARCHIVE_DOES_NOT_REPRODUCE={entry['ledger_path']}")
                failures += 1
                continue
            print(f"LARGE_LEDGER_WRITTEN={entry['ledger_path']}")
        print(f"LARGE_LEDGER_VERIFIED={entry['ledger_path']} sha256={entry['ledger_sha256']}")
    if failures:
        raise SystemExit(1)
    print("LARGE_LEDGERS_PASS=true")


if __name__ == "__main__":
    main()
