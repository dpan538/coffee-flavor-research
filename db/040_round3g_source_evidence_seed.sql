\set ON_ERROR_STOP on

BEGIN;

INSERT INTO evidence.source_family (
    source_family_key, family_name, family_type,
    canonical_origin_key, counts_as_independent,
    independence_basis, admitted
)
VALUES
    (
        'family.liberica-ratapanel-2025',
        'Liberica coffee-bag RATA study', 'COFFEE_SENSORY',
        'origin.doi.10.17632.m3n2gc4dv6.1', TRUE,
        'Independent Universitas Jember study; its workbook and the project-derived aggregate are one source family.',
        TRUE
    ),
    (
        'family.wiktionary-revision-set-20260825',
        'Wiktionary exact-revision lexical review', 'BILINGUAL_LEXICAL',
        'origin.wikimedia.wiktionary.revision-set-20260825', TRUE,
        'English and Chinese Wiktionary editions are kept as separate sources inside one conservative Wikimedia lexical family and are not counted as independent bilingual reviewers.',
        TRUE
    );

INSERT INTO evidence.relationship_source (
    source_key, source_family_key, title, authors_or_owner,
    publication_year, doi_or_stable_url, repository, exact_version,
    access_date, source_type, geography, language, population_or_panel,
    sensory_method, preparation_coverage, roast_coverage, milk_coverage,
    license, commercial_use_allowed, derivative_use_allowed,
    redistribution_allowed, machine_use_allowed, rights_review_status,
    privacy_review_status, privacy_decision, public_export_decision,
    file_list, row_count, field_count, evidence_role,
    supported_relationship_keys, challenged_relationship_keys,
    evidence_locator, limitations, independence_note, admitted
)
VALUES
    (
        'mendeley.liberica-sensory.v1',
        'family.liberica-ratapanel-2025',
        'Liberica Coffee Sensory',
        'Lita Meilina; Rangganis Ulya Auliya; Niken Widya Palupi',
        2025, 'https://doi.org/10.17632/m3n2gc4dv6.1',
        'Mendeley Data', 'Version 1, published 2025-10-11',
        DATE '2026-08-25', 'COFFEE_SENSORY_DATASET',
        'Indonesia; Universitas Jember', 'English and Indonesian headings',
        '25 pseudonymous panelist codes in raw workbook; only aggregate rows are exported',
        'Rate-All-That-Apply plus hedonic testing; Round 3G uses only the RATA summary matrix',
        'Liberica coffee bags with source-defined coffee-leaf infusion configurations',
        'Source-defined L, M and D roast configurations', 'No milk condition documented',
        'CC BY 4.0', TRUE, TRUE, TRUE, TRUE,
        'CLEARED', 'REVIEWED', 'PUBLIC_AGGREGATE_ONLY',
        'MIXED_EXTERNAL_RAW_PUBLIC_DERIVED',
        '["file.liberica.raw-workbook", "file.liberica.rata-summary"]'::JSONB,
        956, 41,
        'Source-local coffee sensory descriptor evidence; not a universal relationship standard',
        ARRAY['membership.roast-spice-smoke.smoke'],
        ARRAY['roast-spice-smoke', 'acidity-character', 'texture-body-drying'],
        'Dataset.xlsx, RATA Test sheet, source summary A158:J168 and descriptor blocks',
        'Specialized coffee-bag formulations, one institution, one protocol, aggregate means only; raw panelist initials are not republished.',
        'The paper, repository workbook and derived TSV share one origin and count once.',
        TRUE
    ),
    (
        'wiktionary.en.revision-set.20260825',
        'family.wiktionary-revision-set-20260825',
        'English Wiktionary exact-revision title set',
        'English Wiktionary contributors', 2026,
        'https://en.wiktionary.org/w/api.php', 'Wikimedia Wiktionary',
        'Revision IDs 92199582, 92085779, 92296005 and 91967689; two missing-title results',
        DATE '2026-08-25', 'LEXICAL_REVISION_METADATA', 'Global', 'English',
        'Community-edited dictionary; no research participants',
        'Exact page-title and revision-metadata attestation only',
        'Not applicable', 'medium-light title included in query', 'Not applicable',
        'CC BY-SA 4.0 / GFDL', TRUE, TRUE, TRUE, TRUE,
        'CLEARED', 'REVIEWED', 'NO_PERSONAL_DATA', 'PUBLIC_METADATA',
        '["file.wiktionary.en-metadata"]'::JSONB, 6, 5,
        'Lexical attestation and missing-title audit below bilingual-review status',
        ARRAY[]::TEXT[], ARRAY[]::TEXT[],
        'db/data/round3g/enwiktionary_revision_metadata.json and exact oldid URLs',
        'Dictionary title presence is not coffee sensory meaning, experiential equivalence or user comprehension.',
        'Kept in one family with Chinese Wiktionary to avoid overstating editorial independence.',
        TRUE
    ),
    (
        'wiktionary.zh.revision-set.20260825',
        'family.wiktionary-revision-set-20260825',
        'Chinese Wiktionary exact-revision title set',
        'Chinese Wiktionary contributors', 2026,
        'https://zh.wiktionary.org/w/api.php', 'Wikimedia Wiktionary',
        'Revision IDs 9162433, 8510635 and 7207074; six missing-title results',
        DATE '2026-08-25', 'LEXICAL_REVISION_METADATA', 'Global',
        'Simplified Chinese query titles',
        'Community-edited dictionary; no research participants',
        'Exact page-title and revision-metadata attestation only',
        'Not applicable', '中浅烘 and 浅中烘 titles included in query', 'Not applicable',
        'CC BY-SA 4.0 / GFDL', TRUE, TRUE, TRUE, TRUE,
        'CLEARED', 'REVIEWED', 'NO_PERSONAL_DATA', 'PUBLIC_METADATA',
        '["file.wiktionary.zh-metadata"]'::JSONB, 9, 5,
        'Lexical attestation and missing-title audit below bilingual-review status',
        ARRAY[]::TEXT[], ARRAY[]::TEXT[],
        'db/data/round3g/zhwiktionary_revision_metadata.json and exact oldid URLs',
        'Title presence, morphology and missing pages do not establish English/Chinese equivalence.',
        'Kept in one family with English Wiktionary and never counted as an independent bilingual reviewer.',
        TRUE
    );

INSERT INTO evidence.source_candidate_register (
    candidate_key, source_key, targeted_range_or_gap, reason_for_search,
    access_result, rights_result, decision, next_action,
    stop_status, reviewed_on
)
VALUES
    ('candidate.mendeley-liberica', 'mendeley.liberica-sensory.v1', 'all seven ranges; especially roast-spice-smoke', 'Named RATA workbook with coffee sensory descriptors and sample configurations.', 'Workbook downloaded and SHA-256 matched repository metadata.', 'CC BY 4.0; raw workbook contains panelist initials so only de-identified aggregate may be exported.', 'ADMIT_AGGREGATE_ONLY', 'Use exact RATA summary rows; keep raw workbook external.', 'STOP_ADMITTED', DATE '2026-08-25'),
    ('candidate.wiktionary-revision-set', 'wiktionary.revision-set.20260825', 'high-risk English/Chinese wording', 'Exact revision metadata can test lexical attestation and missing compounds without claiming equivalence.', 'English and Chinese Action API metadata acquired with a policy-compliant user agent.', 'CC BY-SA 4.0/GFDL; commercial and derivative use permitted with attribution and share-alike.', 'ADMIT_METADATA_ONLY', 'Retain results below bilingual-review status.', 'STOP_ADMITTED', DATE '2026-08-25'),
    ('candidate.mendeley-mozambioside', 'mendeley.mozambioside.v1', 'roast-spice-smoke and bitterness boundary', 'Named coffee bitter-taste paper repository with CC-licensed supplements.', 'Repository inventory accessible; sensory folders contain receptor/NMR experiment files rather than association observations.', 'CC BY 4.0.', 'REJECT_OUT_OF_SCOPE', 'Reserve for a future chemical/receptor evidence round.', 'STOP_OUT_OF_SCOPE', DATE '2026-08-25'),
    ('candidate.zenodo-electrochemical', 'zenodo.electrochemical-coffee.v1', 'acidity, sweetness, bitterness and body', 'Named dataset advertises approximately 196 coffee sensory profiles.', 'Record and files are public.', 'CC BY-NC 4.0 is incompatible with the public baseline export.', 'REJECT_RIGHTS', 'Seek a commercially reusable release; do not import.', 'STOP_RIGHTS', DATE '2026-08-25'),
    ('candidate.wcr-lexicon-v2', 'wcr.sensory-lexicon.v2', 'all seven ranges and bilingual wording', 'Named formal coffee sensory lexicon relevant to descriptors and references.', 'Official page and personal-use download are accessible.', 'Official page limits download and printing to personal-use copies.', 'REJECT_RIGHTS', 'Keep citation-only; copy no vocabulary, definitions, forms, colors or layout.', 'STOP_RIGHTS', DATE '2026-08-25'),
    ('candidate.cc-cedict', 'cc-cedict.release.20260824', 'high-risk Chinese wording', 'Named CC-licensed structured Chinese-English corpus could test literal lexical attestation.', 'Official release page gives a version and entry count but prohibits automated or scripted access.', 'CC BY-SA 4.0 content rights do not override access terms.', 'REJECT_ACCESS_TERMS', 'Do not automate or download.', 'STOP_ACCESS_TERMS', DATE '2026-08-25');

INSERT INTO evidence.relationship_source_snapshot (
    snapshot_key, source_key, source_family_key, exact_version,
    acquired_at, immutable_locator, snapshot_sha256,
    source_record_count, admitted
)
VALUES
    ('snapshot.mendeley-liberica.v1', 'mendeley.liberica-sensory.v1', 'family.liberica-ratapanel-2025', 'Mendeley Data version 1', TIMESTAMPTZ '2026-08-25 00:00:00+00', 'https://doi.org/10.17632/m3n2gc4dv6.1', '299c4ee083b8cc5a67608c1280a75e963e93d64478d2d70755ad299f9e5e8dda', 10, TRUE),
    ('snapshot.wiktionary.en.20260825', 'wiktionary.en.revision-set.20260825', 'family.wiktionary-revision-set-20260825', 'Exact revision metadata queried 2026-08-25', TIMESTAMPTZ '2026-08-25 00:00:00+00', 'db/data/round3g/enwiktionary_revision_metadata.json', 'd3c68aa73dc9f4974abb104ae986017f90560b4befbd40670a4f20daeb72bfa8', 6, TRUE),
    ('snapshot.wiktionary.zh.20260825', 'wiktionary.zh.revision-set.20260825', 'family.wiktionary-revision-set-20260825', 'Exact revision metadata queried 2026-08-25', TIMESTAMPTZ '2026-08-25 00:00:00+00', 'db/data/round3g/zhwiktionary_revision_metadata.json', 'fab81d42e2758bc7d656fa5e41ea305f7d92a8294d1a89c90e771a28dd280ac2', 9, TRUE);

INSERT INTO evidence.relationship_source_file (
    file_key, snapshot_key, source_key, source_family_key, filename,
    file_role, locator, license, file_size_bytes, declared_sha256,
    verified_sha256, row_count, field_count, hash_verified,
    contains_participant_identifiers, public_export_decision, local_path
)
VALUES
    ('file.liberica.raw-workbook', 'snapshot.mendeley-liberica.v1', 'mendeley.liberica-sensory.v1', 'family.liberica-ratapanel-2025', 'Dataset.xlsx', 'RAW_EXTERNAL', 'https://data.mendeley.com/public-files/datasets/m3n2gc4dv6/files/f2aac28f-b5b8-4ae5-8bf1-d3db1f16c435/file_downloaded', 'CC BY 4.0', 834747, '299c4ee083b8cc5a67608c1280a75e963e93d64478d2d70755ad299f9e5e8dda', '299c4ee083b8cc5a67608c1280a75e963e93d64478d2d70755ad299f9e5e8dda', 956, 41, TRUE, TRUE, 'EXTERNAL_ONLY', NULL),
    ('file.liberica.rata-summary', 'snapshot.mendeley-liberica.v1', 'mendeley.liberica-sensory.v1', 'family.liberica-ratapanel-2025', 'liberica_rata_summary_matrix.tsv', 'DERIVED_AGGREGATE', 'db/data/round3g/liberica_rata_summary_matrix.tsv', 'CC BY 4.0', 1549, '05c70310bc9ca64bde3bd3f02da0c029a2043446799e340ad83ecafd2f01babc', '05c70310bc9ca64bde3bd3f02da0c029a2043446799e340ad83ecafd2f01babc', 10, 10, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3g/liberica_rata_summary_matrix.tsv'),
    ('file.wiktionary.en-metadata', 'snapshot.wiktionary.en.20260825', 'wiktionary.en.revision-set.20260825', 'family.wiktionary-revision-set-20260825', 'enwiktionary_revision_metadata.json', 'REVISION_METADATA', 'db/data/round3g/enwiktionary_revision_metadata.json', 'CC BY-SA 4.0 / GFDL', 1206, 'd3c68aa73dc9f4974abb104ae986017f90560b4befbd40670a4f20daeb72bfa8', 'd3c68aa73dc9f4974abb104ae986017f90560b4befbd40670a4f20daeb72bfa8', 6, 5, TRUE, FALSE, 'PUBLIC_METADATA', 'db/data/round3g/enwiktionary_revision_metadata.json'),
    ('file.wiktionary.zh-metadata', 'snapshot.wiktionary.zh.20260825', 'wiktionary.zh.revision-set.20260825', 'family.wiktionary-revision-set-20260825', 'zhwiktionary_revision_metadata.json', 'REVISION_METADATA', 'db/data/round3g/zhwiktionary_revision_metadata.json', 'CC BY-SA 4.0 / GFDL', 1174, 'fab81d42e2758bc7d656fa5e41ea305f7d92a8294d1a89c90e771a28dd280ac2', 'fab81d42e2758bc7d656fa5e41ea305f7d92a8294d1a89c90e771a28dd280ac2', 9, 5, TRUE, FALSE, 'PUBLIC_METADATA', 'db/data/round3g/zhwiktionary_revision_metadata.json');

WITH claim_seed(
    claim_key, target_type, target_key, family_key, source_key,
    snapshot_key, basis, direction, scope, locator, method,
    support_count, document_count, limitation
) AS (
    VALUES
        ('claim.liberica.membership.smoke.supports', 'MEMBERSHIP', 'membership.roast-spice-smoke.smoke', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'COFFEE_SENSORY_STUDY', 'SUPPORTS', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test!A33:K62; aggregate row Smoky Aroma', 'RATA descriptor measured across nine source-defined sample configurations', 9, 9, 'Source-local smoke evidence only; no synonymy with roasty or spice.'),
        ('claim.liberica.range.roast.distinct', 'ASSOCIATION_RANGE', 'roast-spice-smoke', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'COFFEE_SENSORY_STUDY', 'CHALLENGES', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test rows Smoky Aroma and Roasty Flavor', 'Separate RATA variables compared within one protocol', 9, 9, 'The source separates smoky aroma and roasty flavor.'),
        ('claim.liberica.range.fruit.jackfruit', 'ASSOCIATION_RANGE', 'fruit', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'COFFEE_SENSORY_STUDY', 'INSUFFICIENT', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test row Jackfruit Aroma', 'Single descriptor measured across source-defined samples', 9, 9, 'No relationship among current fruit memberships is tested.'),
        ('claim.liberica.range.sweet.direct', 'ASSOCIATION_RANGE', 'sweet-associated', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'COFFEE_SENSORY_STUDY', 'MIXED', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test row Sweet', 'Single descriptor measured across source-defined samples', 9, 9, 'Sweet is measured directly but caramel and honey associations are not tested.'),
        ('claim.liberica.range.acidity.sour-separate', 'ASSOCIATION_RANGE', 'acidity-character', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'COFFEE_SENSORY_STUDY', 'CHALLENGES', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test row Sour', 'Separate RATA variable under the source protocol', 9, 9, 'Sour is operationalized directly; bright, citrus and juicy equivalence is not established.'),
        ('claim.liberica.range.texture.separate', 'ASSOCIATION_RANGE', 'texture-body-drying', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'COFFEE_SENSORY_STUDY', 'CHALLENGES', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test rows Astringent Aftertaste and Body', 'Separate RATA variables compared within one protocol', 9, 9, 'Body and astringent aftertaste are separate variables; current texture memberships are not validated.'),
        ('claim.liberica.range.floral.outside', 'ASSOCIATION_RANGE', 'floral-tea', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'COFFEE_SENSORY_STUDY', 'INSUFFICIENT', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test!A158:J168', 'Declared descriptor inventory review', 10, 9, 'No targeted floral/tea grouping is present; absence is not negative evidence.'),
        ('claim.liberica.range.cocoa.outside', 'ASSOCIATION_RANGE', 'cocoa-nut-caramel', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'COFFEE_SENSORY_STUDY', 'INSUFFICIENT', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test!A158:J168', 'Declared descriptor inventory review', 10, 9, 'No cocoa/nut/caramel grouping is tested; absence is not negative evidence.'),
        ('claim.liberica.question.roast-direction', 'QUESTION_TARGET', 'question-range.roast-direction.roast-spice-smoke', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'QUESTION_WORDING_EVIDENCE', 'INSUFFICIENT', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test rows Smoky Aroma and Roasty Flavor', 'Protocol relevance review', 9, 9, 'Relevant variables exist, but project wording and user comprehension were not tested.'),
        ('claim.liberica.question.roast-smoke', 'QUESTION_TARGET', 'question-range.roast-smoke-reference.roast-spice-smoke', 'family.liberica-ratapanel-2025', 'mendeley.liberica-sensory.v1', 'snapshot.mendeley-liberica.v1', 'QUESTION_WORDING_EVIDENCE', 'INSUFFICIENT', 'SOURCE_LOCAL', 'Dataset.xlsx:RATA Test rows Smoky Aroma and Roasty Flavor', 'Protocol relevance review', 9, 9, 'No user validation or information-gain estimation was performed.'),
        ('claim.wiktionary.membership.jasmine', 'MEMBERSHIP', 'membership.floral-tea.jasmine', 'family.wiktionary-revision-set-20260825', 'wiktionary.en.revision-set.20260825', 'snapshot.wiktionary.en.20260825', 'LEXICAL_ATTESTATION', 'INSUFFICIENT', 'LEXICAL_REVISION', 'English Wiktionary jasmine oldid=91967689', 'Exact-revision title attestation', 1, 1, 'Word attestation does not establish range membership or bilingual equivalence.'),
        ('claim.wiktionary.membership.juicy-acidity', 'MEMBERSHIP', 'membership.acidity-character.juicy', 'family.wiktionary-revision-set-20260825', 'wiktionary.en.revision-set.20260825', 'snapshot.wiktionary.en.20260825', 'LEXICAL_ATTESTATION', 'INSUFFICIENT', 'LEXICAL_REVISION', 'English Wiktionary juicy oldid=92296005', 'Exact-revision title attestation', 1, 1, 'General lexical attestation is below the frozen occurrence/document thresholds.'),
        ('claim.wiktionary.membership.juicy-texture', 'MEMBERSHIP', 'membership.texture-body-drying.juicy', 'family.wiktionary-revision-set-20260825', 'wiktionary.en.revision-set.20260825', 'snapshot.wiktionary.en.20260825', 'LEXICAL_ATTESTATION', 'INSUFFICIENT', 'LEXICAL_REVISION', 'English Wiktionary juicy oldid=92296005', 'Exact-revision title attestation', 1, 1, 'General lexical attestation does not establish coffee texture semantics.'),
        ('claim.wiktionary.membership.tea-like', 'MEMBERSHIP', 'membership.texture-body-drying.tea-like', 'family.wiktionary-revision-set-20260825', 'wiktionary.en.revision-set.20260825', 'snapshot.wiktionary.en.20260825', 'LEXICAL_ATTESTATION', 'INSUFFICIENT', 'LEXICAL_REVISION', 'English Wiktionary query result: tea-like missing at 2026-08-25', 'Exact-revision-set presence/absence audit', 0, 1, 'Missing-page status is not negative evidence.'),
        ('claim.wiktionary.question.bright', 'QUESTION_TARGET', 'question-range.bright-acidity.acidity-character', 'family.wiktionary-revision-set-20260825', 'wiktionary.en.revision-set.20260825', 'snapshot.wiktionary.en.20260825', 'QUESTION_WORDING_EVIDENCE', 'INSUFFICIENT', 'LEXICAL_REVISION', 'English bright oldid=92199582; Chinese 明亮 oldid=9162433', 'Cross-edition title-attestation review without equivalence assertion', 2, 2, 'Two editions in one family are not independent bilingual review.'),
        ('claim.wiktionary.question.floral-tea', 'QUESTION_TARGET', 'question-range.floral-tea-reference.floral-tea', 'family.wiktionary-revision-set-20260825', 'wiktionary.zh.revision-set.20260825', 'snapshot.wiktionary.zh.20260825', 'QUESTION_WORDING_EVIDENCE', 'INSUFFICIENT', 'LEXICAL_REVISION', 'Chinese 茉莉 oldid=8510635; 茉莉花香 missing at 2026-08-25', 'Exact-revision-set title audit', 1, 2, 'Attestation and absence do not establish experiential equivalence.'),
        ('claim.wiktionary.question.tea-style', 'QUESTION_TARGET', 'question-range.tea-style-reference.floral-tea', 'family.wiktionary-revision-set-20260825', 'wiktionary.zh.revision-set.20260825', 'snapshot.wiktionary.zh.20260825', 'QUESTION_WORDING_EVIDENCE', 'INSUFFICIENT', 'LEXICAL_REVISION', 'Chinese 茶感 missing; English tea-like missing at 2026-08-25', 'Exact-revision-set presence/absence audit', 0, 2, 'Missing pages are not negative evidence and no bilingual reviewer exists.'),
        ('claim.wiktionary.question.texture', 'QUESTION_TARGET', 'question-range.texture-character.texture-body-drying', 'family.wiktionary-revision-set-20260825', 'wiktionary.zh.revision-set.20260825', 'snapshot.wiktionary.zh.20260825', 'QUESTION_WORDING_EVIDENCE', 'INSUFFICIENT', 'LEXICAL_REVISION', 'Chinese 多汁感 and 果汁感 missing; English juicy oldid=92296005', 'Cross-edition title-attestation audit', 1, 3, 'Literal morphology and title availability cannot validate juicy as texture.'),
        ('claim.wiktionary.question.family-floral', 'QUESTION_TARGET', 'question-range.family-direction.floral-tea', 'family.wiktionary-revision-set-20260825', 'wiktionary.zh.revision-set.20260825', 'snapshot.wiktionary.zh.20260825', 'QUESTION_WORDING_EVIDENCE', 'INSUFFICIENT', 'LEXICAL_REVISION', 'Chinese 茉莉 oldid=8510635; English jasmine oldid=91967689', 'Cross-edition title-attestation review', 2, 2, 'One conservative family and no user review cannot validate the option.'),
        ('claim.wiktionary.question.roast-medium-light', 'QUESTION_TARGET', 'question-range.roast-direction.roast-spice-smoke', 'family.wiktionary-revision-set-20260825', 'wiktionary.zh.revision-set.20260825', 'snapshot.wiktionary.zh.20260825', 'QUESTION_WORDING_EVIDENCE', 'INSUFFICIENT', 'LEXICAL_REVISION', 'English medium-light; Chinese 中浅烘 and 浅中烘 all missing at 2026-08-25', 'Exact-revision-set presence/absence audit', 0, 3, 'Missing-page status does not resolve ordering or bilingual register risk.')
)
INSERT INTO evidence.relationship_evidence_claim (
    evidence_claim_key, target_entity_type, target_entity_key,
    source_family_key, source_key, snapshot_key, evidence_basis,
    evidence_direction, evidence_scope, evidence_locator, method,
    configuration, support_count, document_count, source_diversity,
    review_status, limitation
)
SELECT
    claim_key, target_type, target_key, family_key, source_key,
    snapshot_key, basis, direction, scope, locator, method,
    jsonb_build_object(
        'minimum_occurrence_count', 3,
        'minimum_document_count', 2,
        'minimum_source_diversity', 1,
        'long_tail_disposition', 'INSUFFICIENT_FOR_RANGE',
        'pooling', 'NONE',
        'value_semantics', 'source-local evidence; not sensory similarity'
    ),
    support_count, document_count, 1, 'REVIEWED', limitation
FROM claim_seed;

WITH review_seed(
    review_key, membership_key, disposition, new_lifecycle,
    supporting, challenging, reason, uncertainty
) AS (
    VALUES
        ('review.membership.floral-tea.floral', 'membership.floral-tea.floral', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'No admitted source tested this anchor relationship.', 'Coffee-protocol and bilingual evidence remain absent.'),
        ('review.membership.floral-tea.jasmine', 'membership.floral-tea.jasmine', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'Exact lexical attestation is insufficient for range membership.', 'Independent bilingual and coffee-sensory grouping review remain absent.'),
        ('review.membership.floral-tea.black-tea', 'membership.floral-tea.black-tea', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'No admitted source tested this relationship.', 'Tea-style wording remains protocol and culture dependent.'),
        ('review.membership.fruit.berry', 'membership.fruit.berry', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'The admitted sensory source measured jackfruit aroma, not berry membership.', 'No compatible berry grouping evidence was acquired.'),
        ('review.membership.fruit.citrus', 'membership.fruit.citrus', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'The admitted sensory source did not test citrus placement.', 'No compatible grouping evidence was acquired.'),
        ('review.membership.cocoa-nut-caramel.cocoa', 'membership.cocoa-nut-caramel.cocoa', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'No admitted source tested this relationship.', 'The sensory workbook had no cocoa grouping.'),
        ('review.membership.cocoa-nut-caramel.dark-chocolate', 'membership.cocoa-nut-caramel.dark-chocolate', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'No admitted source tested this relationship.', 'The sensory workbook had no dark-chocolate grouping.'),
        ('review.membership.cocoa-nut-caramel.caramel', 'membership.cocoa-nut-caramel.caramel', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'Direct sweet ratings do not support caramel grouping.', 'Caramel-to-sweet and caramel-to-cocoa relationships remain untested.'),
        ('review.membership.cocoa-nut-caramel.honey', 'membership.cocoa-nut-caramel.honey', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'Direct sweet ratings do not support honey grouping.', 'Honey remains ambiguous across sensory and consumer-reference uses.'),
        ('review.membership.roast-spice-smoke.smoke', 'membership.roast-spice-smoke.smoke', 'PROMOTE_SOURCE_LOCAL', 'SOURCE_LOCAL_SUPPORTED', 'family.liberica-ratapanel-2025', NULL, 'A versioned coffee RATA study explicitly measured Smoky Aroma across nine sample configurations.', 'Promotion is limited to this membership and source-local lifecycle.'),
        ('review.membership.sweet-associated.caramel', 'membership.sweet-associated.caramel', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'The admitted study measured Sweet but did not associate caramel with it.', 'Consumer wording and coffee-sensory grouping remain untested.'),
        ('review.membership.sweet-associated.honey', 'membership.sweet-associated.honey', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'The admitted study measured Sweet but did not associate honey with it.', 'Consumer wording and coffee-sensory grouping remain untested.'),
        ('review.membership.acidity-character.citrus', 'membership.acidity-character.citrus', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, 'family.liberica-ratapanel-2025', 'The source operationalized Sour separately and supplied no citrus relationship.', 'Compatibility among sour, bright and citrus remains unresolved.'),
        ('review.membership.acidity-character.juicy', 'membership.acidity-character.juicy', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, 'family.liberica-ratapanel-2025', 'Lexical attestation is below threshold and the sensory source did not test juicy.', 'Coffee-specific acidity meaning and bilingual wording require review.'),
        ('review.membership.texture-body-drying.juicy', 'membership.texture-body-drying.juicy', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, 'family.liberica-ratapanel-2025', 'The source separated Body and Astringent Aftertaste and did not test juicy as texture.', 'Coffee-specific tactile meaning remains unresolved.'),
        ('review.membership.texture-body-drying.silky', 'membership.texture-body-drying.silky', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, 'family.liberica-ratapanel-2025', 'The source separated Body and Astringent Aftertaste and did not test silky.', 'No grouping evidence for silky was acquired.'),
        ('review.membership.floral-tea.fragrant-tea', 'membership.floral-tea.fragrant-tea', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'No admitted source tested this text-only candidate.', 'The phrase remains source- and translation-sensitive.'),
        ('review.membership.texture-body-drying.tea-like', 'membership.texture-body-drying.tea-like', 'RETAIN_CANDIDATE', 'CANDIDATE', NULL, NULL, 'The exact Wiktionary title was missing and absence is not negative evidence.', 'Coffee texture semantics and bilingual wording remain unresolved.')
)
INSERT INTO kb.relationship_review_decision (
    review_key, association_range_membership_id, disposition,
    prior_lifecycle, new_lifecycle, supporting_source_families,
    challenging_source_families, decision_reason, remaining_uncertainty,
    review_protocol
)
SELECT
    seed.review_key, membership.association_range_membership_id,
    seed.disposition, 'CANDIDATE', seed.new_lifecycle,
    CASE WHEN seed.supporting IS NULL THEN ARRAY[]::TEXT[]
         ELSE ARRAY[seed.supporting] END,
    CASE WHEN seed.challenging IS NULL THEN ARRAY[]::TEXT[]
         ELSE ARRAY[seed.challenging] END,
    seed.reason, seed.uncertainty, 'ROUND3G_COMPLETE_EVIDENCE_MATRIX_V1'
FROM review_seed AS seed
JOIN corpus.association_range_membership AS membership
  ON membership.membership_key = seed.membership_key;

WITH review_seed(
    review_key, target_key, disposition, supporting, challenging,
    reason, uncertainty
) AS (
    VALUES
        ('review.question.family-floral', 'question-range.family-direction.floral-tea', 'BILINGUAL_REVIEW_REQUIRED', NULL, NULL, 'Cross-edition title attestation does not validate a bilingual question option.', 'Independent bilingual and user evidence are absent.'),
        ('review.question.family-fruit', 'question-range.family-direction.fruit', 'RETAIN_HYPOTHESIS', NULL, NULL, 'No admitted evidence directly tested this target.', 'Ordinary-user comprehension remains unmeasured.'),
        ('review.question.family-cocoa', 'question-range.family-direction.cocoa-nut-caramel', 'RETAIN_HYPOTHESIS', NULL, NULL, 'No admitted evidence directly tested this target.', 'The combined option remains a design hypothesis.'),
        ('review.question.family-roast', 'question-range.family-direction.roast-spice-smoke', 'RETAIN_HYPOTHESIS', NULL, 'family.liberica-ratapanel-2025', 'The source separates smoky aroma and roasty flavor.', 'Ordinary-user interpretation remains unknown.'),
        ('review.question.fruit-direction', 'question-range.fruit-direction.fruit', 'RETAIN_HYPOTHESIS', NULL, NULL, 'Jackfruit measurement does not validate this wording.', 'User comprehension remains untested.'),
        ('review.question.sweet-direction', 'question-range.sweet-direction.sweet-associated', 'RETAIN_HYPOTHESIS', NULL, NULL, 'A direct Sweet rating does not validate caramel/honey wording.', 'Construct alignment remains untested.'),
        ('review.question.roast-direction', 'question-range.roast-direction.roast-spice-smoke', 'RESEARCH_SUPPORT_ADDED', 'family.liberica-ratapanel-2025', 'family.liberica-ratapanel-2025', 'A coffee RATA source adds relevant context while separating roast and smoke.', 'No wording, comprehension or information-gain test exists.'),
        ('review.question.bright-acidity', 'question-range.bright-acidity.acidity-character', 'BILINGUAL_REVIEW_REQUIRED', NULL, 'family.liberica-ratapanel-2025', 'Bright/明亮 title attestation and a separate Sour variable do not establish equivalence.', 'Independent bilingual and ordinary-user review are required.'),
        ('review.question.texture-direction', 'question-range.texture-direction.texture-body-drying', 'RETAIN_HYPOTHESIS', NULL, 'family.liberica-ratapanel-2025', 'The source measures body/astringency separately and does not test the option.', 'Construct compatibility remains unknown.'),
        ('review.question.floral-reference', 'question-range.floral-tea-reference.floral-tea', 'BILINGUAL_REVIEW_REQUIRED', NULL, NULL, '茉莉 and jasmine titles do not establish equivalence or wording validity.', 'Independent bilingual review is required.'),
        ('review.question.tea-style', 'question-range.tea-style-reference.floral-tea', 'BILINGUAL_REVIEW_REQUIRED', NULL, NULL, 'Missing title results are not negative evidence.', 'Register, sensory meaning and comprehension remain unresolved.'),
        ('review.question.fruit-region', 'question-range.fruit-region-reference.fruit', 'RETAIN_HYPOTHESIS', NULL, NULL, 'One jackfruit descriptor does not test project fruit-region options.', 'Coverage and wording remain unvalidated.'),
        ('review.question.cocoa-nut', 'question-range.cocoa-nut-reference.cocoa-nut-caramel', 'RETAIN_HYPOTHESIS', NULL, NULL, 'No admitted source tested this target.', 'Ordinary-user comprehension remains unmeasured.'),
        ('review.question.browned-sweet', 'question-range.browned-sweet-reference.cocoa-nut-caramel', 'RETAIN_HYPOTHESIS', NULL, NULL, 'Direct Sweet ratings do not validate browned-sweet wording.', 'Caramel/honey/cocoa relationships remain untested.'),
        ('review.question.roast-smoke', 'question-range.roast-smoke-reference.roast-spice-smoke', 'RESEARCH_SUPPORT_ADDED', 'family.liberica-ratapanel-2025', 'family.liberica-ratapanel-2025', 'A coffee RATA source adds smoky and roasty variables while keeping them separate.', 'No wording, bilingual or user validation exists.'),
        ('review.question.sweetness-character', 'question-range.sweetness-character.sweet-associated', 'RETAIN_HYPOTHESIS', 'family.liberica-ratapanel-2025', NULL, 'The source measured Sweet, which is context rather than question validation.', 'The answer wording remains untested.'),
        ('review.question.acidity-character', 'question-range.acidity-character.acidity-character', 'RETAIN_HYPOTHESIS', NULL, 'family.liberica-ratapanel-2025', 'The source measured Sour separately and did not test project wording.', 'Construct boundaries remain unresolved.'),
        ('review.question.texture-character', 'question-range.texture-character.texture-body-drying', 'RETAIN_HYPOTHESIS', NULL, 'family.liberica-ratapanel-2025', 'Body/astringency are separate and juicy lexical evidence is insufficient.', 'The target remains unvalidated and information gain is not estimable.')
)
INSERT INTO calibration.question_target_review_decision (
    review_key, question_range_target_id, disposition,
    supporting_source_families, challenging_source_families,
    decision_reason, remaining_uncertainty, review_protocol
)
SELECT
    seed.review_key, target.question_range_target_id, seed.disposition,
    CASE WHEN seed.supporting IS NULL THEN ARRAY[]::TEXT[]
         ELSE ARRAY[seed.supporting] END,
    CASE WHEN seed.challenging IS NULL THEN ARRAY[]::TEXT[]
         ELSE ARRAY[seed.challenging] END,
    seed.reason, seed.uncertainty, 'ROUND3G_QUESTION_TARGET_MATRIX_V1'
FROM review_seed AS seed
JOIN calibration.question_range_target AS target
  ON target.question_range_target_key = seed.target_key;

WITH review_seed(
    review_key, range_key, supporting, challenging, reason, uncertainty
) AS (
    VALUES
        ('review.range.floral-tea', 'floral-tea', NULL, NULL, 'No source-defined floral/tea grouping met promotion criteria.', 'Bilingual and coffee-protocol grouping evidence remain absent.'),
        ('review.range.fruit', 'fruit', 'family.liberica-ratapanel-2025', NULL, 'Jackfruit Aroma is relevant but does not validate the full range.', 'Compatible grouping evidence remains absent.'),
        ('review.range.cocoa-nut-caramel', 'cocoa-nut-caramel', NULL, NULL, 'No admitted source tested the combined range.', 'Component boundaries remain unresolved.'),
        ('review.range.roast-spice-smoke', 'roast-spice-smoke', 'family.liberica-ratapanel-2025', 'family.liberica-ratapanel-2025', 'One membership gained local support while the source separates smoky and roasty.', 'The full range and spice boundary remain unvalidated.'),
        ('review.range.sweet-associated', 'sweet-associated', 'family.liberica-ratapanel-2025', NULL, 'Direct Sweet ratings do not establish caramel/honey grouping.', 'Consumer-reference and intensity semantics remain separate.'),
        ('review.range.acidity-character', 'acidity-character', NULL, 'family.liberica-ratapanel-2025', 'Sour is separate and bright/citrus/juicy equivalence is not validated.', 'Protocol and bilingual compatibility remain unresolved.'),
        ('review.range.texture-body-drying', 'texture-body-drying', NULL, 'family.liberica-ratapanel-2025', 'Body and Astringent Aftertaste are separate variables.', 'Current texture boundaries remain unresolved.')
)
INSERT INTO audit.range_review_decision (
    review_key, association_range_id, disposition, prior_lifecycle,
    new_lifecycle, supporting_source_families, challenging_source_families,
    decision_reason, remaining_uncertainty, review_protocol
)
SELECT
    seed.review_key, range.association_range_id,
    'REVIEWED_RETAIN_CANDIDATE', 'CANDIDATE', 'CANDIDATE',
    CASE WHEN seed.supporting IS NULL THEN ARRAY[]::TEXT[]
         ELSE ARRAY[seed.supporting] END,
    CASE WHEN seed.challenging IS NULL THEN ARRAY[]::TEXT[]
         ELSE ARRAY[seed.challenging] END,
    seed.reason, seed.uncertainty, 'ROUND3G_RANGE_MATRIX_V1'
FROM review_seed AS seed
JOIN corpus.association_range AS range ON range.range_key = seed.range_key;

INSERT INTO audit.data_access_request_update (
    request_key, source_doi, contact_verification, requested_fields,
    desired_license_and_release_rights, prepared_request_text_path,
    request_sent
)
VALUES
    ('request.foods-2022-2440.source-data', '10.3390/foods11162440', 'Corresponding-author route verified against the publisher article record; no message sent.', 'De-identified sample identifier; coffee origin; variety; process; roast; preparation; panel or consumer code; sensory terms; ratings; scale anchors; protocol; missingness codebook.', 'CC BY 4.0 or equivalent commercial redistribution, derivative and machine-use permission for de-identified records.', 'docs/research/coffee-sensory-kb-v0-round3g/14_DATA_ACCESS_REQUEST_UPDATES.md', FALSE),
    ('request.jfs-15326.instrument-data', '10.1111/1750-3841.15326', 'Corresponding-author route verified against the publisher article record; no message sent.', 'De-identified response identifier; exact question and option text; answer codebook; coffee sample identifier; preparation; roast; language; response; missingness and exclusion rules.', 'CC BY 4.0 or equivalent commercial redistribution, derivative and machine-use permission for de-identified records.', 'docs/research/coffee-sensory-kb-v0-round3g/14_DATA_ACCESS_REQUEST_UPDATES.md', FALSE);

INSERT INTO audit.round3g_constraint_registry (
    constraint_key, scope, rule, enforcement_layer, negative_test
)
VALUES
    ('constraint.round3g.source-family-required', 'admitted relationship sources', 'Every admitted source has exactly one source-family key.', 'POSTGRESQL_CONSTRAINT', 'source_with_no_source_family'),
    ('constraint.round3g.source-review-complete', 'admitted relationship sources', 'Every admitted source has an exact version plus cleared rights and privacy reviews.', 'POSTGRESQL_CONSTRAINT', 'source_without_rights_review'),
    ('constraint.round3g.file-hash-match', 'relationship source files', 'Every admitted source file has identical declared and verified SHA-256 values.', 'POSTGRESQL_CONSTRAINT', 'source_file_mismatched_hash'),
    ('constraint.round3g.evidence-provenance', 'relationship evidence claims', 'Every evidence claim has a valid target, source family, source, snapshot and locator.', 'POSTGRESQL_TRIGGER', 'promotion_without_evidence_locator'),
    ('constraint.round3g.cross-source-independence', 'cross-source lifecycle promotion', 'Cross-source support requires two independently countable canonical origins.', 'POSTGRESQL_TRIGGER', 'cross_source_with_one_family'),
    ('constraint.round3g.mirror-not-independent', 'source families', 'A mirror cannot count as independent from its own origin.', 'POSTGRESQL_CONSTRAINT', 'source_independent_from_own_mirror'),
    ('constraint.round3g.derived-copy-not-family', 'source files and families', 'Multiple files and derived copies from one dataset remain one source family.', 'AUDIT_QUERY', 'two_files_counted_as_two_families'),
    ('constraint.round3g.promotion-review', 'membership lifecycle promotion', 'Every promotion requires a matching current review decision.', 'POSTGRESQL_TRIGGER', 'promotion_without_review'),
    ('constraint.round3g.rejection-reason', 'membership and question decisions', 'Every rejection or unresolved disposition retains a decision reason and uncertainty.', 'POSTGRESQL_CONSTRAINT', 'rejection_without_reason'),
    ('constraint.round3g.membership-disposition-complete', '18 inherited memberships', 'All inherited memberships receive exactly one Round 3G disposition.', 'AUDIT_QUERY', 'missing_membership_disposition'),
    ('constraint.round3g.question-disposition-complete', '18 inherited question targets', 'All inherited question targets receive exactly one Round 3G disposition.', 'AUDIT_QUERY', 'missing_question_disposition'),
    ('constraint.round3g.no-calibration-activation', 'association ranges and memberships', 'No Round 3G range or membership may be active for calibration.', 'POSTGRESQL_TRIGGER', 'range_activated_for_calibration'),
    ('constraint.round3g.no-new-range', 'association ranges', 'Round 3G cannot create an additional association range.', 'POSTGRESQL_TRIGGER', 'new_active_range_created'),
    ('constraint.round3g.canonical-freeze', 'canonical concepts', 'Canonical concept count and typing remain frozen at the Round 3F baseline.', 'AUDIT_QUERY', 'canonical_concept_from_expression'),
    ('constraint.round3g.no-model-use', 'model runs', 'Round 3G evidence cannot enter a model or embedding run.', 'POSTGRESQL_TRIGGER', 'round3g_source_used_in_model_run'),
    ('constraint.round3g.privacy-export', 'source files', 'Files containing participant identifiers remain external-only.', 'POSTGRESQL_CONSTRAINT', 'participant_identifier_file_exported'),
    ('constraint.round3g.expected-state-frozen', 'expected-state gate', 'The expected state was frozen before acquisition and has zero threshold revisions.', 'AUDIT_QUERY', 'threshold_changed_after_import_without_decision'),
    ('constraint.round3g.result-truth', 'expected-state classification', 'PASS cannot be asserted while a hard or minimum expected-state metric fails.', 'CI_GATE', 'failed_minimum_reported_as_pass');

INSERT INTO audit.round3g_checkpoint (
    checkpoint_key, source_sha, expected_state_commit_sha,
    expected_state_frozen_before_import, threshold_revision_count,
    canonical_concept_count_before, active_sensory_attribute_count_before,
    association_range_count_before, association_membership_count_before,
    question_target_count_before, new_active_association_range_count,
    automatic_promotion_path_count, real_human_collection_performed,
    real_observation_count, question_user_validated_count,
    question_information_gain_estimated_count, model_or_embedding_run_count,
    product_frontend_modified
)
VALUES (
    'coffee-sensory-kb-v0-round3g',
    'adf615af06ae8cb9ee4d659034157e111476044f',
    'd5a2f895018dcc4dd6b22af4db6a99f8548a3cc3',
    TRUE, 0, 130, 92, 7, 18, 18, 0, 0,
    FALSE, 0, 0, 0, 0, FALSE
);

UPDATE corpus.association_range_membership
SET lifecycle_status = 'SOURCE_LOCAL_SUPPORTED',
    evidence_basis = 'PEER_REVIEWED_SENSORY_EVIDENCE',
    evidence_key = 'claim.liberica.membership.smoke.supports',
    provenance_path = 'mendeley.liberica-sensory.v1 -> snapshot.mendeley-liberica.v1 -> RATA Smoky Aroma -> reviewed source-local membership'
WHERE membership_key = 'membership.roast-spice-smoke.smoke';

COMMIT;
