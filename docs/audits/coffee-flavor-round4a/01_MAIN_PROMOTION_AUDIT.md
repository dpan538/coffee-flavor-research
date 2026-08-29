# Main promotion audit

The pre-promotion receipt hash is
`e79518b193bb37382a029cdc1840c2fcac72a3abc2ed7c2a0bf4b8e661a0b445`.
The source SHA, expected remote-main SHA, merge base, 29/0 ahead/behind relation,
clean source worktree, and successful source CI run were checked before any
write. The old main backup ref was pushed first.

Remote main was fast-forwarded exactly to the source SHA. Exact-main CI passed,
then the annotated `v0.2.0` research-baseline tag was created. No merge commit,
squash, rebase, force push, migration rewrite, main development, or historical
branch deletion occurred.
