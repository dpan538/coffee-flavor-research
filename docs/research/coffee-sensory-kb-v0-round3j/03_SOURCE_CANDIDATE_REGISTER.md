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

## Registered metadata-screen state

- `NAMED_SOURCE_CANDIDATE_COUNT=17`
- `RAW_ACQUISITION_AUTHORIZED_CANDIDATE_COUNT=5`
- `RAW_SOURCE_FILE_ACQUISITION_COUNT=0`
- `SOURCE_IMPORT_COUNT=0`
- `EXPECTED_STATE_THRESHOLD_REVISION_COUNT=0`

The 17 candidates are canonical named origins after mirror and frozen-baseline
reconciliation. FT-NIR v4, Li taste-sensitivity v1, and Yeager's acids
meta-analysis were discovered in the v0.1.0 inventory and therefore remain
existing-corpus eligibility records rather than new candidates. The Carvalho
canephora study appeared in both language and sensory searches but is one
registered candidate.

Raw acquisition is authorized only for Liang/Dryad, Golovinsky/Zenodo,
Bichlmaier/Mendeley, the manually bounded `guchengf` pages, and Xian
Zhang/Mendeley. Authorization is for file, privacy, rights, and schema audit; it
does not imply admission or training eligibility. All other candidates remain
metadata-only, aggregate-evidence-only, pending, rejected, or blocked under the
decision recorded in the TSV.
