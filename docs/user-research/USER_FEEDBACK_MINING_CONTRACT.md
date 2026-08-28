# User-feedback mining contract

## Purpose

Feedback and consumer language are valuable only when their evidence role,
rights, privacy, and interpretation stay explicit. This contract separates
external consumer text, interview/usability material, and product interaction
events.

## 1. External consumer review text

### Permitted analyses after rights and purpose review

- lexical and phrase variation;
- term frequency and phrase normalization candidates;
- preparation and roast mentions as reported fields;
- familiarity proxies and vague-versus-specific language;
- sentiment or expectation context;
- disagreement with package notes;
- ambiguity and confusion patterns; and
- potential question wording.

### Prohibited uses

- promotion to professional P1/P2 evidence;
- assertion of objective flavor truth;
- automatic canonical ontology promotion;
- roast inference from tasting language;
- treating a review row as an expert or competition coffee record; and
- direct model training without source rights, purpose, privacy, and model-use
  review.

Positive interpretation: consumer reviews can reveal how people understand and
communicate coffee. They do not establish one correct professional label.

## 2. Interview and usability feedback

Permitted analyses after consent:

- qualitative coding and thematic synthesis;
- task breakdown and comprehension barriers;
- interaction burden and drop-off reasons;
- trust, uncertainty, and candidate interpretation;
- accessibility and language needs; and
- evidence for product prioritization.

Planned prompts or facilitator expectations are not findings. A theme requires
traceability to session artifacts and contradictory evidence.

## 3. Product interaction events

Permitted analyses after consent/privacy activation:

- completion rate and question count;
- answer latency and drop-off;
- context-prior override;
- candidate exposure and acceptance;
- primary versus secondary selection;
- none-of-these / abstention and confidence;
- question information gain; and
- pairwise behavioral preference.

These events may later support behavioral ranking evidence. They do not become
professional flavor labels and do not prove the coffee objectively tastes like
the selected candidate.

## Cross-input controls

| Control                      | External reviews             | Interviews/usability               | Product events                        |
| ---------------------------- | ---------------------------- | ---------------------------------- | ------------------------------------- |
| Source rights review         | required                     | not applicable; consent governs    | not applicable; consent governs       |
| Consent                      | source terms/privacy review  | explicit research consent          | explicit analytics/research consent   |
| Direct identifiers           | avoid                        | do not require                     | do not require                        |
| Professional label promotion | prohibited                   | prohibited                         | prohibited                            |
| Behavioral relevance use     | not inferred                 | possible with explicit task design | possible after consent and evaluation |
| Public raw-text release      | only if rights allow         | separate quotation/release consent | no raw event release by default       |
| Model use                    | separate rights/purpose gate | separate model-use consent         | separate model-use consent            |

## Operational state

`EXTERNAL_CONSUMER_MINING_STATUS=NOT_STARTED`

`INTERVIEW_MINING_STATUS=NOT_STARTED`

`PRODUCT_EVENT_MINING_STATUS=NOT_STARTED`

No live collection or mining is authorized by this document.
