# Data-role and label contract

“Can support model training” means only that the stratum may be considered after
task-specific rights, review, purpose, privacy, and split gates. It is not a
current authorization.

| Data stratum                                        | Can ground professional label                            | Can support vocabulary                     | Can support UX                       | Can support ranking relevance                                 | Can support model training                                |
| --------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------ | ------------------------------------ | ------------------------------------------------------------- | --------------------------------------------------------- |
| Reviewed P1/P2 professional evidence                | Yes, within qualified review scope                       | Yes                                        | Indirectly                           | Yes, for professional compatibility                           | Potentially, only with model-use rights                   |
| Unreviewed or unresolved professional-source fields | No                                                       | Yes, as provisional source-native language | Indirectly                           | No gate credit                                                | No until provenance/review/rights pass                    |
| P3 competitor/producer evidence                     | No, unless separately promoted through evidence contract | Yes                                        | Yes, for package/industry comparison | Auxiliary only                                                | Potentially as auxiliary data with rights                 |
| P4 commercial/roaster language                      | No                                                       | Yes                                        | Yes                                  | Auxiliary or package-relevance role                           | Potentially as auxiliary data with rights                 |
| P5 consumer language                                | No                                                       | Yes                                        | Yes                                  | Potential behavioral/familiarity role, not professional truth | Only with source rights and purpose review                |
| First-party interview data                          | No                                                       | Yes                                        | Yes                                  | Qualitative relevance only unless task defines labels         | Only with explicit consent and governed transformation    |
| First-party interaction data                        | No                                                       | Indirectly                                 | Yes                                  | Yes, as behavioral relevance after consent                    | Only with explicit model-use consent and leakage controls |
| Synthetic/test fixtures                             | No                                                       | Test vocabulary only                       | Workflow testing only                | No empirical relevance                                        | No; never empirical model data                            |

## Label precedence

1. A professional normalization target requires reviewed P1/P2 strict evidence,
   bounded source provenance, and qualified review.
2. Consumer or first-party choices may create behavioral relevance labels only
   for a declared ranking/comprehension task.
3. Industry and commercial language can discover variants or compare
   expectations; it is not silently promoted to professional truth.
4. A row may have multiple roles, but each use requires a recorded purpose and
   cannot widen rights.
5. Synthetic fixtures remain inside rollback/disposable tests and are excluded
   from empirical counts.

## Auxiliary features are not labels

C0/C1 context, lexical similarity, source reputation, publication rank, score,
roaster wording, and co-assertion frequency may become features only when their
semantics and rights allow. None proves a canonical target by itself. Explicit
sensory answers should be able to override context priors in the product task.

## Promotion and review

Automatic ontology or evidence-tier promotion is prohibited. A model candidate
must remain provisional until an authorized review path accepts it. Human review
requires qualification, admission, and row-level decision evidence; a reviewer
code, actor type, or opaque hash alone is insufficient.
