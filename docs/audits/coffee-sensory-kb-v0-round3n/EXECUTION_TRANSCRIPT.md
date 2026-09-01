# Round 3N execution transcript

## Stage 0 — recovery and baseline verification

```text
COMMAND=git worktree list --porcelain
WORKTREE=/Users/jarlgiovanni/Desktop/Coffee_Flavor_Research
RESULT=identified as ORIGINAL_DIRTY_MAIN_WORKTREE; branch=main; HEAD=1755915d3918013c8bd7c5f744e5ce8a0e972167; not modified

COMMAND=git status --porcelain=v1 --untracked-files=all
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
RESULT=empty output; selected execution worktree clean

COMMAND=git branch --show-current; git rev-parse HEAD; git remote get-url origin
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
RESULT=research/coffee-sensory-data-ml-readiness; 6e2e0a3f3cbc5aa1837d5d35385a92dc3a96c6b5; git@github.com:dpan538/coffee-flavor-research.git

COMMAND=git fetch origin --prune
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
RESULT=tracking refs refreshed without reported divergence

COMMAND=git rev-parse origin/main origin/research/coffee-sensory-data-ml-readiness
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
RESULT=afde62ba0e957de959fd6127fc1e8b900814cbf4; 6e2e0a3f3cbc5aa1837d5d35385a92dc3a96c6b5

COMMAND=git merge-base --is-ancestor origin/main origin/research/coffee-sensory-data-ml-readiness
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
RESULT=pass

COMMAND=git log --all --grep='fix(ci): restore Batch 7 outputs after historical replay'
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
RESULT=6e2e0a3f3cbc5aa1837d5d35385a92dc3a96c6b5

COMMAND=git ls-remote origin refs/heads/main refs/heads/research/coffee-sensory-data-ml-readiness
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=128
RESULT=ssh: Could not resolve hostname github.com: -65563

COMMAND=gh run list --repo dpan538/coffee-flavor-research --branch research/coffee-sensory-data-ml-readiness --limit 20 ...
WORKTREE=/Users/jarlgiovanni/Desktop/Coffee_Flavor_Research
EXIT_STATUS=1
RESULT=error connecting to api.github.com
```

No database, corpus, semantic, rights, model, or frontend artifact was changed
in Stage 0. The first failed run is retained because it was an external
connectivity condition, not evidence of a repository-baseline defect.

## Stage 1 — CI runtime remediation

```text
COMMAND=docker run --rm --detach --name coffee-round3n-profile-pg17 ... postgres:17-bookworm
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=130
RESULT=interrupted after bounded image-retrieval wait with no container id or database created
DIAGNOSIS=external image/network availability; do not retry the complete historical pipeline merely to profile it

COMMAND=bash db/scripts/ci-verify-current-artifacts.sh
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
ELAPSED_SECONDS=113
RESULT=CI_VERIFY_CURRENT_ARTIFACTS_PASS=true; all named public contracts pass; restricted-input cases explicitly skipped by their existing public-safe contracts

COMMAND=bash -n db/scripts/ci-stage-timing.sh db/scripts/ci-verify-current-artifacts.sh db/scripts/ci-verify-current-database.sh db/scripts/ci-verify-restricted-local.sh db/scripts/ci-verify.sh
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
RESULT=PASS

COMMAND=python3 -B db/scripts/test-ci-workflow-contract.py
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
RESULT=CI_TEST_CLASSIFICATION_COUNT=17; MANDATORY_TEST_SKIP_COUNT=0; CI_TEST_CLASSIFICATION_PASS=true

COMMAND=python3 -B db/scripts/test-public-snapshot-contract.py
WORKTREE=/private/tmp/coffee-flavor-round3m
EXIT_STATUS=0
RESULT=PUBLIC_SNAPSHOT_CONTRACT_PASS=true
```

## Recovery amendment — explicit runtimes and bounded remote remediation

```text
COMMAND=python -X dev -B db/scripts/generate-batch6-semantic-corpus.py
PYTHON_VERSION=3.12.13
EXIT_STATUS=0
RESULT=direct Batch 6 generator pass; accepted current artifacts restored after the diagnostic

COMMAND=python -X dev -B db/scripts/test-current-descriptor-data.py
PYTHON_VERSION=3.12.13
EXIT_STATUS=0
RESULT=CURRENT_DESCRIPTOR_DATA_CONTRACT_PASS=true

COMMAND=git commit
EXIT_STATUS=0
RESULT=aaaa615cd33b4bf3b21ff06f48c1a2fea3e334d8 fix(ci): restore explicit Python runtimes and surface generator failures

COMMAND=git push origin research/coffee-sensory-data-ml-readiness
EXIT_STATUS=0
RESULT=normal non-force recovery push 1 of 2

COMMAND=gh run view 33468931133
EXIT_STATUS=0
RESULT=frontend pass; PostgreSQL 17 current contract pass; public artifact fail in direct Batch 6 diagnostic

COMMAND=gh api .../jobs/99734502763/logs
EXIT_STATUS=0
RESULT=PermissionError errno 13 at /private/tmp/coffee-flavor-round3m-post30k/post30k_extension/batch6_semantic_review under setup-python CPython 3.12.14
CLASSIFICATION=PATH_OR_WORKING_DIRECTORY

COMMAND=python -X dev -B db/scripts/generate-batch6-semantic-corpus.py
PYTHON_VERSION=3.12.13
EXIT_STATUS=0
RESULT=platform-neutral tempfile.gettempdir() default passes locally

COMMAND=git commit
EXIT_STATUS=0
RESULT=88cd394f96df0d409ea2b40b30396b314beecdd8 fix(ci): use a platform-neutral Batch 6 review path

COMMAND=git push origin research/coffee-sensory-data-ml-readiness
EXIT_STATUS=0
RESULT=normal non-force recovery push 2 of 2

COMMAND=gh run watch 33470462970 --exit-status
EXIT_STATUS=0
RESULT=frontend 1m21s pass; public artifacts 3m54s pass; PostgreSQL 17 current contract 18m19s pass

COMMAND=gh run watch 33470462938 --exit-status
EXIT_STATUS=0
RESULT=PostgreSQL 17 full two-clean-database historical replay passed in 35m01s

COMMAND=git push --dry-run origin HEAD:refs/heads/main
EXIT_STATUS=0
RESULT=fast-forward from afde62ba0e957de959fd6127fc1e8b900814cbf4 to 88cd394f96df0d409ea2b40b30396b314beecdd8

COMMAND=git push origin HEAD:refs/heads/main
EXIT_STATUS=0
RESULT=remote main fast-forwarded normally; dirty local main checkout not used; no force push
```

No corpus content, semantic mapping, evidence tier, rights decision, database
migration, product rule, model artifact, or frontend behavior changed in either
recovery commit.

## Stages 3–11 — product contract, simulator, acquisition review, and tests

```text
COMMAND=python3.12 -B db/scripts/generate-product-inference-v0.py
EXIT_STATUS=0
RESULT=20 candidates; 8 C0 families; 7 C1 levels; 56 cells; 120 cases; TRAINING_RUN_COUNT=0

COMMAND=python3.12 -B db/scripts/test-product-inference-v0.py
EXIT_STATUS=0
RESULT=PRODUCT_INFERENCE_V0_CONTRACT_PASS=true; PRODUCT_NEGATIVE_TEST_PASS=true; PRODUCT_BYTE_REPRODUCIBILITY_PASS=true; PRODUCT_PUBLIC_SAFE_PASS=true

COMMAND=python3.12 -B db/scripts/run-product-inference-v0.py --case-id answer-update-01
EXIT_STATUS=0
RESULT=developer inspection output includes case, deterministic result, score components, and explanations

COMMAND=python3.12 -B db/scripts/run-corpus-ci.py --public-snapshot
EXIT_STATUS=0
RESULT=PUBLIC_SNAPSHOT_CONTRACT_PASS=true; MANDATORY_PUBLIC_TEST_SKIP_COUNT=0

COMMAND=python3.12 -B db/scripts/test-ci-workflow-contract.py
EXIT_STATUS=0
RESULT=CI_TEST_CLASSIFICATION_COUNT=18; MANDATORY_TEST_SKIP_COUNT=0
```

The bounded acquisition pass selected 30 of 36 previously governed source
candidates and imported zero datasets and zero observations. No network source
was treated as newly verified. Consumer material remained outside professional
candidate scoring. The owner packet contains exactly 100 blank decisions over
all ten required review categories.

## Stage 12 — complete local product checkpoint gate

```text
COMMAND=PYTHON_COMMAND=/opt/homebrew/bin/python3.12 bash db/scripts/ci-verify-current-artifacts.sh
EXIT_STATUS=0
ELAPSED_SECONDS=114
RESULT=CI_VERIFY_CURRENT_ARTIFACTS_PASS=true; product, checksum, public-safe, and workflow contracts pass

COMMAND=docker info
EXIT_STATUS=130
RESULT=Docker Desktop daemon remained unresponsive after a bounded readiness window
INTERPRETATION=no local PostgreSQL 16 result is represented as PostgreSQL 17 parity; remote postgres:17-bookworm current verification passed

COMMAND=npm run format:check
EXIT_STATUS=0
RESULT=all matched files use Prettier code style

COMMAND=npm run check
EXIT_STATUS=0
RESULT=TypeScript pass; local Node 22.21 emits a non-fatal React Router minimum-version warning

COMMAND=npm run test
EXIT_STATUS=0
RESULT=2 files and 9 unit tests passed

COMMAND=npm run build
EXIT_STATUS=0
RESULT=static React Router build and all declared prerender routes passed

COMMAND=npm run test:smoke
EXIT_STATUS=1
RESULT=initial sandboxed preview bind failed with EPERM on 127.0.0.1:4321

COMMAND=npm run test:smoke
EXECUTION=approved local preview-server binding
EXIT_STATUS=0
RESULT=15 Playwright tests passed across mobile, tablet, and desktop projects
```
