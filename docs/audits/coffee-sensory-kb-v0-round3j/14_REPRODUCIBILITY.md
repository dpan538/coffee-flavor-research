# Reproducibility

`db/scripts/generate-round3j-global-corpus.py` deterministically regenerates
the TSVs, source manifests, hashes, and global manifest from committed inputs.
The verifier checks every generated artifact and admitted source-file hash.
Two clean PostgreSQL 17 rebuilds and a no-diff artifact replay are required
before this receipt can mark reproducibility true.
