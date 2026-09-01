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
