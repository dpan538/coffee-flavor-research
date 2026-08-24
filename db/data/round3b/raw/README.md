# Round 3B frozen source files

The files in this directory are exact, rights-reviewed source bytes. The six
imported files were published under CC0-1.0 under the DOI records shown in
`SOURCE_MANIFEST.json`.

Dryad's public metadata API exposed exact version, byte-count, and SHA-256
records but its file endpoint required a bearer token during retrieval on
2026-08-25. The same DOI-identified files were therefore downloaded from the
official Zenodo mirrors. Every downloaded byte count and SHA-256 matches the
Dryad API metadata exactly.

No source file is normalized in place. Derived context records retain source
file and row locators. The inaccessible Liang DOI is recorded as a refused
import; no substitute data or inferred row inventory was created.
