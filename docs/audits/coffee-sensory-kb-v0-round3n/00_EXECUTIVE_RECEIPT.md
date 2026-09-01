# Round 3N execution receipt

## Stage 0 — recovery and baseline verification

Status: `PASS_SELECTED_EXECUTION_WORKTREE`

This receipt intentionally distinguishes the authorized clean research
worktree from the unrelated, user-owned dirty `main` worktree. No mutating
command was issued in the latter.

```text
EXECUTION_WORKTREE_PATH=/private/tmp/coffee-flavor-round3m
EXECUTION_WORKTREE_MODE=EXISTING_RESEARCH
EXECUTION_WORKTREE_BRANCH=research/coffee-sensory-data-ml-readiness
EXECUTION_WORKTREE_STARTING_SHA=6e2e0a3f3cbc5aa1837d5d35385a92dc3a96c6b5
EXECUTION_WORKTREE_CLEAN=true

ORIGINAL_DIRTY_MAIN_WORKTREE_PATH=/Users/jarlgiovanni/Desktop/Coffee_Flavor_Research
ORIGINAL_DIRTY_MAIN_WORKTREE_DETECTED=true
ORIGINAL_DIRTY_MAIN_WORKTREE_CLEAN=false
ORIGINAL_DIRTY_MAIN_WORKTREE_UNCHANGED=true
ORIGINAL_DIRTY_MAIN_WORKTREE_TOUCHED=false
ORIGINAL_DIRTY_MAIN_WORKTREE_STASHED=false
ORIGINAL_DIRTY_MAIN_WORKTREE_COMMITTED=false
ORIGINAL_DIRTY_MAIN_WORKTREE_RESET=false
ORIGINAL_UNTRACKED_PDF_PRESERVED=true
ALL_WORKTREES_CLEAN=NA_NOT_REQUIRED

ORIGIN_URL=git@github.com:dpan538/coffee-flavor-research.git
REMOTE_RESEARCH_BRANCH=research/coffee-sensory-data-ml-readiness
REMOTE_RESEARCH_SHA=6e2e0a3f3cbc5aa1837d5d35385a92dc3a96c6b5
REMOTE_MAIN_SHA=afde62ba0e957de959fd6127fc1e8b900814cbf4
REMOTE_RESEARCH_SHA_CONFIRMED=true
REMOTE_MAIN_SHA_CONFIRMED=true
REMOTE_MAIN_IS_ANCESTOR_OF_RESEARCH=true

PREVIOUS_REMEDIATION_COMMIT=6e2e0a3f3cbc5aa1837d5d35385a92dc3a96c6b5
PREVIOUS_REMEDIATION_SUBJECT=fix(ci): restore Batch 7 outputs after historical replay
CURRENT_DATABASE_WORKFLOW_TIMEOUT_MINUTES=35
CURRENT_WEB_WORKFLOW_TIMEOUT_MINUTES=25
CURRENT_TIMEOUT_DOMINANT_COMMAND=db/scripts/rebuild-twice.sh
CURRENT_TIMEOUT_EVIDENCE=CI_HEARTBEAT elapsed=1920s followed by context cancellation after prior assertions passed
REMOTE_ACTIONS_STATUS=NOT_YET_AVAILABLE
REMOTE_REF_QUERY_NOTE=git fetch origin completed before a transient GitHub DNS failure; subsequent git ls-remote and gh access failed with hostname resolution errors and are retained in the execution transcript

AUTHORITATIVE_CORE_COUNTS=round3m public manifest: 480 census items; 131 source-route/family keys; 11 independent source families; 140 segmented observations; 139 de-inflated assertions; 137 record-unique observations; 508 P2 pair events; 0 human-confirmed; 0 model-eligible
STAGE0_FILES_INSPECTED=AGENTS.md; PROJECT_STATUS.md; product, architecture, ML, Round3M research and audit receipts; CI scripts; migration/rebuild scripts; Round3M manifests and context receipt
STAGE0_FILES_CHANGED=this receipt and EXECUTION_TRANSCRIPT.md only
STAGE0_TESTS=worktree identity and cleanliness; remote tracking-ref equality; ancestry; prior remediation-commit presence; authoritative manifest reconciliation
STAGE0_RESULT=PASS
STAGE0_UNRESOLVED=Remote Actions and direct remote-ref inspection await restored GitHub DNS/connectivity; no remote result is treated as passing.
```

The current workflow runs public artifact/contract tests first and invokes the
two-empty-database reproducibility replay last. The latter includes all
migrations, artifact loading, SQL validation (including negative and query-plan
contracts), and byte comparisons twice. It is historical replay, not a safe
per-push latency budget.
