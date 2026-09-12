#!/usr/bin/env python3
"""Subset MiSans to the characters the PWA can show (owner's download → apps/pwa/public/fonts).

The app renders only strings from the runtime bundle, the copy modules and the Vue components, so the subset is the
union of every character in those files plus ASCII, CJK punctuation and the digits/units the cards print. Output:
MiSans-{Regular,Medium,Demibold}.woff2 (a few hundred KB each instead of ~5 MB), which the service worker can precache.
Usage: python3 apps/pwa/scripts/subset-fonts.py [~/Downloads/MiSans/woff2]
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / "Downloads" / "MiSans" / "woff2").expanduser()
OUT = ROOT / "apps" / "pwa" / "public" / "fonts"
TEXT_SOURCES = [ROOT / "db" / "data" / "product-vector-v1" / "product-vector-v1.json", *(ROOT / "packages" / "flavor-data" / "src" / "product-vector-v1").glob("*.ts"),
                *(ROOT / "apps" / "pwa" / "src").rglob("*.vue"), *(ROOT / "apps" / "pwa" / "src").rglob("*.ts"), ROOT / "apps" / "pwa" / "index.html"]
BASE = "".join(chr(c) for c in range(0x20, 0x7F)) + "，。、；：？！“”‘’（）《》〈〉【】「」『』—…·│・×→↔↑↓≥≤≈±°%‰′″‑–　©®™"


def main() -> int:
    chars = set(BASE)
    for p in TEXT_SOURCES:
        if p.is_file():
            chars.update(p.read_text(encoding="utf-8", errors="ignore"))
    chars = {c for c in chars if not c.isspace() or c == " "}
    import tempfile
    text_file = Path(tempfile.mkdtemp()) / "subset-chars.txt"  # never inside public/: it would ship with the app
    text_file.write_text("".join(sorted(chars)), encoding="utf-8")
    for weight in ("Regular", "Medium", "Demibold"):
        src = SRC / f"MiSans-{weight}.woff2"
        if not src.is_file():
            print(f"missing {src}"); return 1
        dest = OUT / f"MiSans-{weight}.woff2"
        subprocess.run([sys.executable, "-m", "fontTools.subset", str(src), f"--text-file={text_file}", "--flavor=woff2", "--layout-features=*",
                        "--no-hinting", "--desubroutinize", f"--output-file={dest}"], check=True)
        print(dest.name, dest.stat().st_size, "bytes from", src.stat().st_size)
    print("characters", len(chars))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
