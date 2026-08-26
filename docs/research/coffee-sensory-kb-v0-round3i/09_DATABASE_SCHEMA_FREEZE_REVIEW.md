# Database schema freeze review

## Review decision

Round 3I keeps migrations `000` through `044` immutable and adds a forward-only
language and release layer in migrations `045` through `048`. The design is
suitable for a freeze candidate because it gives observed language its own
source-local identity, preserves the federated sensory structures, declares a
single set of future prebuild read surfaces, and requires an exact-main
attestation before `FROZEN` can be recorded.

This is a schema-design review, not a substitute for executing the migrations.
`SCHEMA_INTEGRITY_PASS=true` may be asserted only after a clean PostgreSQL 17
rebuild, the Round 3I negative suite, the research-database freeze gate, and the
two-rebuild reproducibility check all pass on the same candidate.

## Structural review

| Review dimension          | Governing structure                                                                                                                                                                                                                                     | Decision                           |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| Primary-key coverage      | Every new family, source, document, candidate, review, expression, occurrence, batch, release, artifact, surface, member, revision, and attestation relation has an explicit primary key.                                                               | Accepted                           |
| Foreign-key integrity     | The chain is family -> source -> document -> occurrence -> expression. Review decisions reference a hash-bound candidate; release artifacts, surfaces, members, and attestations reference one release version. Deletes and key changes are restricted. | Accepted                           |
| Candidate keys            | Independent canonical origins, source-row locators, normalized `(language_code, expression)`, occurrence locators, candidate hashes, review passes, artifact types/paths, and surface roles/object names are unique within their governed scope.        | Accepted                           |
| Source/version provenance | Sources require a title, owner, stable URL, repository, exact version, access date, license basis, non-empty limitations, and a non-empty file manifest whose entries have a locator and valid SHA-256.                                                 | Accepted                           |
| Lifecycle integrity       | Language rows use explicit candidate/admitted/rejected/quarantined/deprecated states; admitted booleans and lifecycle states must agree. Releases use `DRAFT`, `FREEZE_CANDIDATE`, `FROZEN`, or `SUPERSEDED`.                                           | Accepted                           |
| Countability              | A countable document must be admitted, source-authored, sensory-verified, frozen, non-translated, and non-artificial. Countable expressions exclude preparation and roast roles and require observed admitted evidence.                                 | Accepted                           |
| Review provenance         | Firstbloom candidates retain hash inventories rather than candidate text. `DUAL_CODEX_REVIEWED` expressions require two admitting decisions from different reviewer keys over the same candidate inventory. Neither decision is labeled human review.   | Accepted                           |
| Rights and privacy        | Seven separate raw/derived/model-use decisions are stored per language source. Triggers prevent raw retention or public export beyond the source decision; documents carry privacy and public-export states.                                            | Accepted                           |
| Frozen membership         | Release members store a hash of the governed row. Membership completeness recomputes all member hashes before attestation; attested members and release payloads cannot be changed in place.                                                            | Accepted, subject to rebuild proof |

## Ontology, relationship, and analysis boundaries

The migration set does not insert, split, merge, retype, or deactivate a
canonical concept. The required invariants remain 130 concepts and 92 active
sensory attributes. Round 3I also does not alter the 20 feature definitions or
12 source partitions.

The Cotter acidity--citrus addition is one reviewed `SUPPORTS` claim. It updates
the independent-origin breadth summary for the acidity-character range but
does not update either the membership lifecycle or the range lifecycle. The
frozen totals are therefore still six source-local-supported memberships, four
cross-source-supported memberships, and six ranges with source-local evidence;
the preferred breadth metric alone rises from three to four ranges with
cross-source evidence. Contradictory claim directions remain in the underlying
claim registry even when a narrower current view excludes them from future
prebuild consumption.

The Round 3H model-run and embedding guards remain in force. Feature
missingness, harmonization status, pooling permission, partition grouping keys,
and seven declared leakage risks remain explicit. Round 3I creates no split,
model, embedding, pgvector dependency, adaptive policy, or human-observation
table content.

## Release and immutability contract

`coffee-sensory-research-db-v0.1.0` must first exist as a
`FREEZE_CANDIDATE`. Candidate state requires a complete release-member set, 11
verified artifact hashes, and exactly eight approved current surfaces. The
release may become `FROZEN` only through a post-promotion attestation containing:

- an external PostgreSQL 17 reproducibility attestation for two clean rebuilds
  whose 11 committed artifact hashes match;
- the exact SHA on `refs/heads/main`;
- an annotated tag whose target is that same main SHA;
- a tag-object SHA distinct from the target commit SHA; and
- the matching release name and manifest hash.

After attestation, triggers protect the release row, artifact and surface
registries, member rows, language members, and approved view definitions.
Historical migrations are retained; supersession is by a new release and a new
forward migration, never by editing v0.1.0 in place.

## Required executable proof

The final schema-integrity receipt must demonstrate all of the following on one
exact candidate:

1. the migration plan validates the immutable `000`--`044` baseline before
   applying `045`--`048`;
2. `audit.run_model_prebuild_readiness_gate()` has no failed hard gate;
3. `audit.run_research_database_freeze_gate()` exposes required, observed,
   passed, severity, evidence-path, and limitation fields;
4. the Round 3I negative suite rejects all 35 enumerated
   gaming, rights, hash, lifecycle, and surface mutations;
5. all 11 artifact hashes (10 inventories plus the manifest) match across two
   clean PostgreSQL 17 rebuilds; and
6. the feature candidate and promoted main SHA both pass frontend and PostgreSQL
   CI before the exact-main attestation is written.

Until those executable conditions are recorded in the audit package, the
schema decision is `FREEZE_CANDIDATE`, not `FROZEN`.
