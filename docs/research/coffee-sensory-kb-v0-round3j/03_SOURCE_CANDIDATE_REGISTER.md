# Round 3J source-candidate register

The authoritative machine-readable register is
`db/data/round3j/source_candidate_register.tsv`. It was created before any
Round 3J raw source acquisition or import and initially contains only its
schema. Named candidates are appended before their raw files are downloaded.

## Required decision fields

Each row records the candidate key, acquisition batch, targeted training gap,
exact title, authors or owner, year, DOI or stable official URL, repository,
expected contribution, license or terms, rights state, access state,
preliminary decision, independence basis, estimated effective units, explicit
raw-acquisition authorization, registration date, and controlling limitation.

`raw_acquisition_authorized=true` means only that a specifically identified
file may be acquired for review. It does not imply admission, public export, or
training eligibility. An admitted source must later receive complete source,
family, version, file-hash, license, rights, privacy, public-export, and
model-research-use annotations.

## Initial state

- `NAMED_SOURCE_CANDIDATE_COUNT=0`
- `RAW_SOURCE_FILE_ACQUISITION_COUNT=0`
- `SOURCE_IMPORT_COUNT=0`
- `EXPECTED_STATE_THRESHOLD_REVISION_COUNT=0`

This empty initial state is intentional: generic searches do not count as
candidates, and no source may be backfilled into the register after its raw
acquisition.
