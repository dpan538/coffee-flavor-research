# Association method comparison

No method below was run in Round 3F. The table evaluates transferability to the
current source-concentrated corpus without using embeddings or LLM similarity.
Mutual information has a long history as a lexical association statistic
([Church and Hanks, 1990](https://aclanthology.org/J90-1003/)); overlapping
community methods explicitly allow nodes in multiple groups
([Palla et al., 2005](https://doi.org/10.1038/nature03607)). These methods do not
turn textual association into sensory truth.

| Method                          | Research question                                       | Input                              | Minimum support policy                                    | Output                             | Interpretation                       | Failure mode                                       | Current transferability                       |
| ------------------------------- | ------------------------------------------------------- | ---------------------------------- | --------------------------------------------------------- | ---------------------------------- | ------------------------------------ | -------------------------------------------------- | --------------------------------------------- |
| source-defined grouping         | what grouping did one source explicitly define?         | source nodes/groups                | one formal grouping with version/rights                   | membership record                  | source-local structure               | copied taxonomy or lost rights scope               | usable as `SOURCE_LOCAL`; none added          |
| raw co-occurrence               | which expressions share governed documents?             | preserved occurrences/documents    | pair count >=3; document count >=3                        | count                              | observed joint presence              | frequent marginals dominate                        | available; not rerun                          |
| document frequency              | is an expression recurrent enough to analyze?           | normalized expression occurrences  | occurrence >=3; documents >=3                             | document count/rate                | support filter                       | says nothing about association partner             | usable only as gate                           |
| Jaccard                         | how large is pair intersection relative to union?       | document sets                      | both marginals >=5; pair documents >=3                    | intersection/union                 | normalized overlap                   | rare pairs unstable; ignores count intensity       | candidate after support filter                |
| conditional co-occurrence       | how often does B appear given A?                        | pair and marginal document counts  | conditioning marginal >=5; pair >=3                       | directional rate                   | asymmetric corpus relation           | small denominator; order matters                   | candidate after support filter                |
| PMI / PPMI                      | is joint presence above independence expectation?       | pair/marginal counts and corpus N  | both marginals >=5; pair >=3; PPMI keeps positive values  | log association                    | lexical association under snapshot   | inflates rare pairs; PPMI hides negative values    | candidate with minimum-frequency protection   |
| source-diversity weighting      | is association distributed beyond one publisher/source? | pair counts by evidence family     | >=2 independent families for cross-source claim           | method-specific adjusted statistic | robustness to source concentration   | arbitrary weights can hide provenance              | audit only until weighting rationale reviewed |
| overlapping community detection | do supported edges form overlapping graph regions?      | thresholded method-specific graph  | all retained edges meet support; no isolated one-off node | overlapping node sets              | graph organization                   | parameter sensitivity; community != sensory family | insufficient for project-level ranges now     |
| fuzzy membership                | does a reviewed method assign partial membership?       | declared features/method           | reviewed features, support and calibration                | method-local membership value      | algorithm-specific graded allocation | looks like probability; scale not portable         | defer; no universal field                     |
| graph-neighbour analysis        | what is one hop from an anchor?                         | typed/source-local graph           | admitted edges only                                       | neighbour list                     | local exploration                    | silently mixes edge semantics                      | usable only with edge-type filter             |
| source holdout stability        | does a range survive withholding one evidence family?   | at least 3 independent families    | >=3 families; repeat every holdout                        | retention/change report            | cross-source robustness              | impossible with one/two families                   | insufficient now                              |
| bootstrap stability             | does a corpus-derived grouping survive resampling?      | documents sampled with replacement | support gates first; >=200 resamples proposed             | membership retention distribution  | sampling stability, not truth        | source dependence preserved; threshold arbitrary   | future only; threshold requires review        |

## Conservative current policy

For corpus-derived candidate ranges: minimum occurrence count 3, document count
3, pair-document count 3, marginal document count 5, and at least two distinct
publishers/evidence units. Cross-source support additionally needs two
independent evidence families. Expressions below occurrence or document count 3
remain long-tail and do not create ranges. These are conservative engineering
guards based on a 215-document, single-commercial-corpus snapshot, not claims of
scientific significance.

Stability is required before any corpus-derived range can progress beyond
`CANDIDATE`. Current evidence is too source-concentrated for a project-level
community-detection result: `INSUFFICIENT_FOR_RANGE`.
