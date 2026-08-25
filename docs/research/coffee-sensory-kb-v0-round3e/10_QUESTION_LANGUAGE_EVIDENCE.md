# Question-language evidence

Round 3E adds nine logical research candidates in English and Simplified
Chinese. Together with the six frozen Round 3C logical questions, the governed
inventory is 15 logical distinctions and 30 language versions. The 18 new
versions are research material, not validated adaptive questions.

| Candidate region      | New logical candidates                           | Highest supported lifecycle                      |
| --------------------- | ------------------------------------------------ | ------------------------------------------------ |
| floral / tea          | floral-versus-tea; tea-style reference           | English `RESEARCH_REVIEWED`; Chinese `CANDIDATE` |
| fruit                 | fruit-region reference                           | English `RESEARCH_REVIEWED`; Chinese `CANDIDATE` |
| cocoa / nut / caramel | cocoa/nut reference; caramelized-sweet reference | English `RESEARCH_REVIEWED`; Chinese `CANDIDATE` |
| roast / spice / smoke | toast/smoke/ash/spice reference                  | English `RESEARCH_REVIEWED`; Chinese `CANDIDATE` |
| sweetness             | taste versus sweet-associated character          | English `RESEARCH_REVIEWED`; Chinese `CANDIDATE` |
| acidity               | bright/juicy/clean/sharp/sour character          | English `RESEARCH_REVIEWED`; Chinese `CANDIDATE` |
| texture               | smooth/creamy/heavy/drying/light character       | English `RESEARCH_REVIEWED`; Chinese `CANDIDATE` |

The exact target distinction, eligible C0/C1 contexts, answer options,
modality, evidence, familiarity assumptions, translation notes, ambiguity,
expected information role and unresolved concerns are retained in
`db/data/round3e/generated/question_candidates.tsv` and the database.

## Design constraints applied

- Candidate-local questions follow a broad answer; they do not rank coffees or
  define a learned question policy.
- Every candidate offers `another ...`, `none of these` and/or `not sure`
  routes where appropriate, limiting forced-choice distortion.
- Named references such as jasmine, Earl Grey, bergamot and cocoa powder carry
  explicit familiarity assumptions.
- `bright`, `clean`, `juicy`, `tea-like` and `jasmine` retain modality and
  polysemy concerns rather than literal one-to-one translation claims.
- Eligible contexts are hypotheses for later comprehension testing, not
  measured context effects.
- `expected_information_role` is qualitative. Information gain is
  `NOT_ESTIMABLE` for every candidate.

No ordinary-user comprehension study occurred. New English candidates advance
only to `RESEARCH_REVIEWED`; new Chinese versions remain `CANDIDATE` pending
independent bilingual sensory review. `QUESTION_USER_VALIDATED_COUNT=0`.
