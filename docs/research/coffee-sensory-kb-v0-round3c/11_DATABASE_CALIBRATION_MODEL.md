# Database calibration model

A dedicated `calibration` schema is justified because experimental observations, interaction assignments, analyses, and releases have different epistemic roles from canonical ontology, corpus, and context-taxonomy records.

## Entity groups

- governance: `study`, `protocol_version`, `analysis_plan`, `release_snapshot`;
- material: `coffee_lot`, `roast_batch`, `preparation_condition`, `beverage_sample`;
- people and execution: `assessor`, `session`, `randomization_schedule`, `presentation`;
- observations: `sensory_observation`, `descriptor_response`, `dimension_response`;
- interaction: `question`, `question_option`, `question_eligibility`, `question_assignment`, `question_response`, `question_response_selection`;
- evaluation: `candidate_reference_judgment`, `grouped_split`, `analysis_run`, `model_candidate_output`.

Foreign keys bind roast batches to the current governed seven-level C1 categories and preparation conditions to the current eight-family C0 taxonomy. Milk is a condition attribute with a paired-base key, not a flavor label. Sample identity includes study, lot, roast, preparation, replicate, and protocol.

## Epistemic firebreaks

Raw observations have `record_role=raw_observation`; consensus and model outputs use separate tables. Database triggers reject consensus as raw data and model candidates as canonical knowledge. Public participant rows reject direct identifiers. Split membership is grouped and exclusive. Release readiness requires manifest, checksum, license, and rights metadata.

Round 3C seeds only governance, protocol, design, question-bank, and eligibility rows. It inserts no sample observations. Round 3D may seed a physical matrix and conspicuously synthetic engineering fixtures; these are excluded from scientific counts and release-data views.
