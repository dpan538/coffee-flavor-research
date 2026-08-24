\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0 -- independently curated canonical seed
--
-- This forward-only seed deliberately does not reproduce a WCR, SCA, ISO, or
-- publication vocabulary.  The 92 active sensory concepts plus eight retained
-- candidates are an independently selected cross-source project inventory.  Descriptions,
-- categories, lexical mappings, and canonical hierarchy are project-authored;
-- no source definitions, references, intensities, scores, or hierarchy are
-- copied.  External support rows record only admission/scope evidence.
--
-- Stable contract after this migration (including the Round 1 smoke rows):
--   active sensory_attribute concepts                          92
--   candidate sensory_attribute concepts                        8
--   project categories                                         20
--   project candidate qualifiers                                6
--   composite_reference / process_entity / affective_term     1 / 2 / 1
--   active schemes                                               2
--   project-scheme nodes/mappings                              130 / 130
--   project-scheme edges                 106 (98 active + 8 candidate)
--   WCR public-page partial nodes/mappings/edges               24 / 15 / 0
--
-- The WCR partial mapping is intentionally incomplete.  Twelve mappings assert
-- reviewed equivalent scope (Sour, Bitter, Salty, Apple, Grape, Coconut,
-- Pineapple, Peapod, Phenolic, Petroleum, Almond, Jasmine).  Three mappings
-- assert association only (Acetic acid, Fermented, Papery).  Butyric acid,
-- Isovaleric acid, Fresh, Musty/Earthy, Musty/Dusty, Moldy/Damp, Brown Spice,
-- Vanillin, and Floral remain source-local and unmapped.

BEGIN;

-- Rights are evaluated at a fixed date.  Production export is enabled only
-- for the independently authored project source.  Open-access research remains
-- evidence metadata in V0 and is not exported as source content.
INSERT INTO evidence.license_policy (
    license_policy_key,
    access_class_code,
    rights_status_code,
    redistributable,
    derivative_work_allowed,
    commercial_use_allowed,
    machine_use_allowed,
    production_export_allowed,
    checked_on,
    notes
)
VALUES
    (
        'license.project_canonical_ontology.cc_by_4_0.v1',
        'public', 'verified', TRUE, TRUE, TRUE, TRUE, TRUE,
        DATE '2026-08-24',
        'Project-authored ontology content under the repository documented CC BY 4.0 content layer; no external definitions or source hierarchy are included.'
    ),
    (
        'license.peer_reviewed.cc_by_4_0.evidence_only.v1',
        'public', 'verified', TRUE, TRUE, TRUE, TRUE, FALSE,
        DATE '2026-08-24',
        'Verified CC BY 4.0 article; V0 stores bibliographic metadata and independently summarized support only, so source-content production export stays disabled.'
    ),
    (
        'license.chambers_2016.cc_by_nc_4_0.metadata_only.v1',
        'metadata_only', 'verified', TRUE, TRUE, FALSE, TRUE, FALSE,
        DATE '2026-08-24',
        'CC BY-NC 4.0 article; commercial production export is not authorized. No definition, reference, intensity, or full vocabulary is copied.'
    ),
    (
        'license.williams_2023.cc_by_nc_4_0.metadata_only.v1',
        'metadata_only', 'verified', TRUE, TRUE, FALSE, TRUE, FALSE,
        DATE '2026-08-24',
        'CC BY-NC open-access article; commercial production export is not authorized. The published character wheel and its full term inventory are not copied.'
    ),
    (
        'license.carvalho_2025.cc_by_nc_nd_4_0.metadata_only.v1',
        'metadata_only', 'verified', TRUE, FALSE, FALSE, FALSE, FALSE,
        DATE '2026-08-24',
        'CC BY-NC-ND 4.0 article; adapted content and commercial export are not authorized. Only bibliographic metadata and non-copied evidence links are stored.'
    ),
    (
        'license.wiley_article.rights_unconfirmed.metadata_only.v1',
        'metadata_only', 'unknown', FALSE, FALSE, FALSE, FALSE, FALSE,
        DATE '2026-08-24',
        'Article metadata and reported-use locator only; the applicable reuse licence was not verified from the publisher page, so all reuse gates remain closed.'
    ),
    (
        'license.wcr_lexicon.personal_use.metadata_only.v1',
        'metadata_only', 'verified', FALSE, FALSE, FALSE, FALSE, FALSE,
        DATE '2026-08-24',
        'WCR permits free download and printing for personal use. V0 retains only bibliographic metadata and the 24 labels explicitly enumerated on the public landing page.'
    ),
    (
        'license.sca_cva.all_rights_reserved.metadata_only.v1',
        'metadata_only', 'verified', FALSE, FALSE, FALSE, FALSE, FALSE,
        DATE '2026-08-24',
        'SCA page and CVA materials are metadata-only in V0; forms, glossaries, definitions, and proprietary text are not imported.'
    ),
    (
        'license.iso.no_reproduction_or_machine_use.metadata_only.v1',
        'metadata_only', 'verified', FALSE, FALSE, FALSE, FALSE, FALSE,
        DATE '2026-08-24',
        'ISO copyright terms require permission for reproduction and prohibit machine or AI use outside stated exceptions. Only bibliographic metadata is retained.'
    );

INSERT INTO evidence.source (
    source_key,
    title,
    creator,
    publisher,
    citation,
    doi,
    source_url,
    external_metadata
)
VALUES
    (
        'source.project.coffee_sensory_kb_v0_round2a',
        'Coffee Sensory Knowledge Base V0 Round 2A Canonical Ontology',
        'Coffee Flavor Atlas project',
        'Coffee Flavor Atlas project',
        'Coffee Flavor Atlas project. Coffee Sensory Knowledge Base V0 Round 2A Canonical Ontology. 2026-08-24.',
        NULL,
        NULL,
        '{"authorship":"project","content_license":"CC-BY-4.0","external_definitions_copied":false,"source_hierarchies_copied":false}'::JSONB
    ),
    (
        'source.chambers_2016_living_lexicon',
        'Development of a living lexicon for descriptive sensory analysis of brewed coffee',
        'Edgar Chambers IV; Karolina Sanchez; Uyen X. T. Phan; Rhonda Miller; Gail V. Civille; Brizio Di Donfrancesco',
        'Journal of Sensory Studies',
        'Chambers IV, E., Sanchez, K., Phan, U. X. T., Miller, R., Civille, G. V., and Di Donfrancesco, B. (2016). Journal of Sensory Studies 31(6), 465-480.',
        '10.1111/joss.12237',
        'https://onlinelibrary.wiley.com/doi/10.1111/joss.12237',
        '{"source_class":"peer_reviewed","license_identifier":"CC-BY-NC-4.0","use":"admission_and_scope_basis_only"}'::JSONB
    ),
    (
        'source.carvalho_2025_canephora_rata',
        'Development of a flavour wheel for Coffea canephora using rate-all-that-apply',
        'Fabiana M. Carvalho; Enrique A. Alves; Mateus M. Artencio; Alvaro L. L. Cassago; Lucas L. Pereira et al.',
        'Scientific Reports',
        'Carvalho, F. M., Alves, E. A., Artencio, M. M., et al. (2025). Scientific Reports 15, 16643.',
        '10.1038/s41598-025-99921-w',
        'https://www.nature.com/articles/s41598-025-99921-w',
        '{"source_class":"peer_reviewed","license_identifier":"CC-BY-NC-ND-4.0","use":"reported_usage_and_scope_basis_only","source_hierarchy_imported":false}'::JSONB
    ),
    (
        'source.ledezma_2025_geisha_rata',
        'Sensory Perception and Physicochemical Characteristics of Geisha Coffee From Different Production Zones in Panama',
        'D. B. Ledezma; C. Sartori; E. Tomasino',
        'Food Science & Nutrition',
        'Ledezma, D. B., Sartori, C., and Tomasino, E. (2025). Food Science & Nutrition 13(12), e71278.',
        '10.1002/fsn3.71278',
        'https://onlinelibrary.wiley.com/doi/10.1002/fsn3.71278',
        '{"source_class":"peer_reviewed","rights_claim":"unverified","use":"reported_usage_only"}'::JSONB
    ),
    (
        'source.seninde_2020_sensory_review',
        'Coffee Flavor: A Review',
        'D. R. Seninde; E. Chambers IV',
        'Beverages',
        'Seninde, D. R., and Chambers IV, E. (2020). Coffee Flavor: A Review. Beverages 6(3), 44.',
        '10.3390/beverages6030044',
        'https://doi.org/10.3390/beverages6030044',
        '{"source_class":"peer_reviewed_review","license_identifier":"CC-BY-4.0","use":"cross_source_scope_basis"}'::JSONB
    ),
    (
        'source.zhang_2019_wet_processing',
        'Influence of Various Processing Parameters on the Microbial Community Dynamics, Metabolomic Profiles, and Cup Quality During Wet Coffee Processing',
        'Sophia Jiyuan Zhang et al.',
        'Frontiers in Microbiology',
        'Zhang, S. J., De Bruyn, F., Pothakos, V., et al. (2019). Frontiers in Microbiology 10, 2621.',
        '10.3389/fmicb.2019.02621',
        'https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2019.02621/full',
        '{"source_class":"peer_reviewed","license_identifier":"CC-BY-4.0","use":"empirical_scope_basis"}'::JSONB
    ),
    (
        'source.munchow_2020_roast_sensory',
        'Roasting Conditions and Coffee Flavor: A Multi-Study Empirical Investigation',
        'Morten Muenchow; Jesper Alstrup; Ida Steen; Davide Giacalone',
        'Beverages',
        'Muenchow, M., Alstrup, J., Steen, I., and Giacalone, D. (2020). Roasting Conditions and Coffee Flavor: A Multi-Study Empirical Investigation. Beverages 6(2), 29.',
        '10.3390/beverages6020029',
        'https://www.mdpi.com/2306-5710/6/2/29',
        '{"source_class":"peer_reviewed","license_identifier":"CC-BY-4.0","use":"roast_and_brown_note_scope_basis"}'::JSONB
    ),
    (
        'source.batali_2022_brew_temperature',
        'Sensory Analysis of Full Immersion Coffee: Cold Brew Is More Floral, and Less Bitter, Sour, and Rubbery Than Hot Brew',
        'Mackenzie E. Batali; Lik Xian Lim; Jiexin Liang; Sara E. Yeager; Ashley N. Thompson; Juliet Han; William D. Ristenpart; Jean-Xavier Guinard',
        'Foods',
        'Batali, M. E., Lim, L. X., Liang, J., et al. (2022). Sensory Analysis of Full Immersion Coffee: Cold Brew Is More Floral, and Less Bitter, Sour, and Rubbery Than Hot Brew. Foods 11(16), 2440.',
        '10.3390/foods11162440',
        'https://www.mdpi.com/2304-8158/11/16/2440',
        '{"source_class":"peer_reviewed","license_identifier":"CC-BY-4.0","use":"taste_mouthfeel_and_aroma_scope_basis"}'::JSONB
    ),
    (
        'source.bollen_2024_canephora_profiles',
        'Sensory profiles of Robusta coffee (Coffea canephora) genetic resources from the Democratic Republic of the Congo',
        'R. Bollen et al.',
        'Frontiers in Sustainable Food Systems',
        'Bollen, R., et al. (2024). Sensory profiles of Robusta coffee (Coffea canephora) genetic resources from the Democratic Republic of the Congo. Frontiers in Sustainable Food Systems 8, 1382976.',
        '10.3389/fsufs.2024.1382976',
        'https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2024.1382976/full',
        '{"source_class":"peer_reviewed","license_identifier":"CC-BY-4.0","use":"reported_usage_only","third_party_taxonomy_not_imported":true}'::JSONB
    ),
    (
        'source.williams_2023_acidity_mouthfeel',
        'Coffee is more than flavor, the creation of a coffee character wheel',
        'Simon D. Williams; Danilo de Andrade; Lei Liu',
        'Journal of Sensory Studies',
        'Williams, S. D., de Andrade, D., and Liu, L. (2023). Journal of Sensory Studies 38(6), e12886.',
        '10.1111/joss.12886',
        'https://onlinelibrary.wiley.com/doi/10.1111/joss.12886',
        '{"source_class":"peer_reviewed","license_identifier":"CC-BY-NC-4.0","use":"mouthfeel_scope_basis_only"}'::JSONB
    ),
    (
        'source.wcr_sensory_lexicon_2_0',
        'World Coffee Research Sensory Lexicon 2.0',
        'World Coffee Research',
        'World Coffee Research',
        'World Coffee Research. Sensory Lexicon 2.0. Published October 2017.',
        NULL,
        'https://worldcoffeeresearch.org/resources/sensory-lexicon',
        '{"source_class":"authoritative_lexicon_metadata","rights_scope":"personal_use","full_vocabulary_imported":false,"definitions_imported":false}'::JSONB
    ),
    (
        'source.sca_coffee_value_assessment',
        'Coffee Value Assessment',
        'Specialty Coffee Association',
        'Specialty Coffee Association',
        'Specialty Coffee Association. Coffee Value Assessment framework and standards metadata.',
        NULL,
        'https://sca.coffee/value-assessment',
        '{"source_class":"authoritative_method_metadata","forms_imported":false,"glossary_imported":false}'::JSONB
    ),
    (
        'source.iso_18794_2025',
        'ISO 18794:2025 Coffee - Sensory analysis - Vocabulary',
        'International Organization for Standardization',
        'International Organization for Standardization',
        'ISO 18794:2025, Coffee - Sensory analysis - Vocabulary, Edition 2.',
        NULL,
        'https://www.iso.org/standard/87695.html',
        '{"source_class":"authoritative_standard_metadata","reference_number":"ISO 18794:2025","edition":2,"standard_content_imported":false}'::JSONB
    );

INSERT INTO evidence.source_version (
    source_version_key,
    source_id,
    license_policy_id,
    version_label,
    published_on,
    retrieved_on,
    version_locator,
    external_metadata
)
SELECT
    seed.source_version_key,
    source.source_id,
    policy.license_policy_id,
    seed.version_label,
    seed.published_on,
    DATE '2026-08-24',
    seed.version_locator,
    seed.external_metadata
FROM (
    VALUES
        ('source_version.project.coffee_sensory_kb_v0.2026-08-24', 'source.project.coffee_sensory_kb_v0_round2a', 'license.project_canonical_ontology.cc_by_4_0.v1', 'Round 2A 2026-08-24', DATE '2026-08-24', 'db/010_canonical_ontology_seed.sql', '{"authorship":"project"}'::JSONB),
        ('source_version.chambers_2016_living_lexicon.vor', 'source.chambers_2016_living_lexicon', 'license.chambers_2016.cc_by_nc_4_0.metadata_only.v1', 'Version of record', DATE '2016-12-01', 'https://doi.org/10.1111/joss.12237', '{"publication_identifier":"31(6):465-480"}'::JSONB),
        ('source_version.carvalho_2025_canephora_rata.vor', 'source.carvalho_2025_canephora_rata', 'license.carvalho_2025.cc_by_nc_nd_4_0.metadata_only.v1', 'Version of record', DATE '2025-05-13', 'https://doi.org/10.1038/s41598-025-99921-w', '{"article_number":"16643"}'::JSONB),
        ('source_version.ledezma_2025_geisha_rata.vor', 'source.ledezma_2025_geisha_rata', 'license.wiley_article.rights_unconfirmed.metadata_only.v1', 'Version of record', DATE '2025-11-25', 'https://doi.org/10.1002/fsn3.71278', '{"article_number":"e71278","rights_claim":"unverified"}'::JSONB),
        ('source_version.seninde_2020_sensory_review.vor', 'source.seninde_2020_sensory_review', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'Version of record', DATE '2020-07-08', 'https://doi.org/10.3390/beverages6030044', '{"article_number":"44"}'::JSONB),
        ('source_version.zhang_2019_wet_processing.vor', 'source.zhang_2019_wet_processing', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'Version of record', DATE '2019-11-13', 'https://doi.org/10.3389/fmicb.2019.02621', '{"article_number":"2621"}'::JSONB),
        ('source_version.munchow_2020_roast_sensory.vor', 'source.munchow_2020_roast_sensory', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'Version of record', DATE '2020-05-08', 'https://doi.org/10.3390/beverages6020029', '{"article_number":"29"}'::JSONB),
        ('source_version.batali_2022_brew_temperature.vor', 'source.batali_2022_brew_temperature', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'Version of record', DATE '2022-08-13', 'https://doi.org/10.3390/foods11162440', '{"article_number":"2440"}'::JSONB),
        ('source_version.bollen_2024_canephora_profiles.vor', 'source.bollen_2024_canephora_profiles', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'Version of record', DATE '2024-05-02', 'https://doi.org/10.3389/fsufs.2024.1382976', '{"article_number":"1382976"}'::JSONB),
        ('source_version.williams_2023_acidity_mouthfeel.vor', 'source.williams_2023_acidity_mouthfeel', 'license.williams_2023.cc_by_nc_4_0.metadata_only.v1', 'Version of record', DATE '2023-10-24', 'https://doi.org/10.1111/joss.12886', '{"article_number":"e12886","license_identifier":"CC-BY-NC-4.0","full_character_wheel_imported":false}'::JSONB),
        ('source_version.wcr_sensory_lexicon_2_0.public_page', 'source.wcr_sensory_lexicon_2_0', 'license.wcr_lexicon.personal_use.metadata_only.v1', '2.0 (October 2017)', NULL::DATE, 'https://worldcoffeeresearch.org/resources/sensory-lexicon', '{"published_month":"2017-10","partial_public_labels":24}'::JSONB),
        ('source_version.sca_cva.web_2026-08-24', 'source.sca_coffee_value_assessment', 'license.sca_cva.all_rights_reserved.metadata_only.v1', 'Web page retrieved 2026-08-24', NULL::DATE, 'https://sca.coffee/value-assessment', '{"standards_metadata":["SCA-102","SCA-103","SCA-104","SCA-105"]}'::JSONB),
        ('source_version.iso_18794_2025.edition_2', 'source.iso_18794_2025', 'license.iso.no_reproduction_or_machine_use.metadata_only.v1', 'ISO 18794:2025 Edition 2', DATE '2025-11-26', 'https://www.iso.org/standard/87695.html', '{"edition":2,"publication_month":"2025-11"}'::JSONB)
) AS seed(
    source_version_key,
    source_key,
    license_policy_key,
    version_label,
    published_on,
    version_locator,
    external_metadata
)
JOIN evidence.source AS source
  ON source.source_key = seed.source_key
JOIN evidence.license_policy AS policy
  ON policy.license_policy_key = seed.license_policy_key;

-- Reclassify the Round 1 project support explicitly.  No curated concept is
-- left with the migration-only legacy_unspecified role.
UPDATE evidence.concept_support AS support
SET concept_support_role_code = 'project_authorship'
FROM evidence.source_version AS source_version
WHERE source_version.source_version_id = support.source_version_id
  AND source_version.source_version_key =
      'source_version.project_smoke_seed.2026-08-24'
  AND support.concept_support_role_code = 'legacy_unspecified';

-- The support_source_version_key column below documents the admission route
-- considered during curation; it is not stored on kb.concept.  Only the later
-- filtered support matrix creates evidence assertions.  Group membership is
-- likewise project curation, not a source hierarchy.
WITH sensory_seed(
    concept_key,
    label,
    lifecycle_status_code,
    provenance_scope_code,
    support_source_version_key
) AS (
    VALUES
        ('sensory.sweet', 'sweet', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.sour', 'sour', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.bitter', 'bitter', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.salty', 'salty', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.astringent', 'astringent', 'active', 'external', 'source_version.williams_2023_acidity_mouthfeel.vor'),
        ('sensory.drying', 'drying', 'active', 'external', 'source_version.williams_2023_acidity_mouthfeel.vor'),
        ('sensory.fullness', 'fullness', 'active', 'external', 'source_version.williams_2023_acidity_mouthfeel.vor'),
        ('sensory.smooth_mouthfeel', 'smooth mouthfeel', 'active', 'external', 'source_version.williams_2023_acidity_mouthfeel.vor'),
        ('sensory.oily_mouthfeel', 'oily mouthfeel', 'active', 'external', 'source_version.williams_2023_acidity_mouthfeel.vor'),
        ('sensory.creamy_mouthfeel', 'creamy mouthfeel', 'active', 'external', 'source_version.williams_2023_acidity_mouthfeel.vor'),
        ('sensory.syrupy_mouthfeel', 'syrupy mouthfeel', 'active', 'external', 'source_version.williams_2023_acidity_mouthfeel.vor'),
        ('sensory.mouth_coating', 'mouth coating', 'active', 'external', 'source_version.williams_2023_acidity_mouthfeel.vor'),
        ('sensory.metallic', 'metallic', 'active', 'external', 'source_version.williams_2023_acidity_mouthfeel.vor'),
        ('sensory.lemon', 'lemon', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.lime', 'lime', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.orange', 'orange', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.grapefruit', 'grapefruit', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.pink_grapefruit', 'pink grapefruit', 'candidate', 'project_authored', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.bergamot', 'bergamot', 'active', 'external', 'source_version.ledezma_2025_geisha_rata.vor'),
        ('sensory.apple', 'apple', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.pear', 'pear', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.peach', 'peach', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.plum', 'plum', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.cherry', 'cherry', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.pomegranate', 'pomegranate', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.strawberry', 'strawberry', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.raspberry', 'raspberry', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.blueberry', 'blueberry', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.blackberry', 'blackberry', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.blackcurrant', 'blackcurrant', 'candidate', 'project_authored', 'source_version.project.coffee_sensory_kb_v0.2026-08-24'),
        ('sensory.grape', 'grape', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.banana', 'banana', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.pineapple', 'pineapple', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.mango', 'mango', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.coconut', 'coconut', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.raisin', 'raisin', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.prune', 'prune', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.jasmine', 'jasmine', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.rose', 'rose', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.orange_blossom', 'orange blossom', 'candidate', 'project_authored', 'source_version.project.coffee_sensory_kb_v0.2026-08-24'),
        ('sensory.chamomile', 'chamomile', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.fresh_grass', 'fresh grass', 'active', 'external', 'source_version.seninde_2020_sensory_review.vor'),
        ('sensory.hay', 'hay', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.green_vegetal', 'green vegetal', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.pea_pod', 'pea pod', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.bell_pepper', 'bell pepper', 'active', 'external', 'source_version.seninde_2020_sensory_review.vor'),
        ('sensory.mint', 'mint', 'candidate', 'project_authored', 'source_version.project.coffee_sensory_kb_v0.2026-08-24'),
        ('sensory.eucalyptus', 'eucalyptus', 'candidate', 'project_authored', 'source_version.project.coffee_sensory_kb_v0.2026-08-24'),
        ('sensory.lemongrass', 'lemongrass', 'candidate', 'project_authored', 'source_version.project.coffee_sensory_kb_v0.2026-08-24'),
        ('sensory.black_tea', 'black tea', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.green_tea', 'green tea', 'candidate', 'project_authored', 'source_version.project.coffee_sensory_kb_v0.2026-08-24'),
        ('sensory.almond', 'almond', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.hazelnut', 'hazelnut', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.peanut', 'peanut', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.walnut', 'walnut', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.cinnamon', 'cinnamon', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.clove', 'clove', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.nutmeg', 'nutmeg', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.black_pepper', 'black pepper', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.cardamom', 'cardamom', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.ginger', 'ginger', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.anise', 'anise', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.honey', 'honey', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.brown_sugar', 'brown sugar', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.molasses', 'molasses', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.caramel', 'caramel', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.vanilla', 'vanilla', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.butter', 'butter', 'active', 'external', 'source_version.ledezma_2025_geisha_rata.vor'),
        ('sensory.cocoa', 'cocoa', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.dark_chocolate', 'dark chocolate', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.malt', 'malt', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.cereal_grain', 'cereal grain', 'active', 'external', 'source_version.munchow_2020_roast_sensory.vor'),
        ('sensory.baked_bread', 'baked bread', 'active', 'external', 'source_version.munchow_2020_roast_sensory.vor'),
        ('sensory.toast', 'toast', 'active', 'external', 'source_version.munchow_2020_roast_sensory.vor'),
        ('sensory.roasted_nut', 'roasted nut', 'active', 'external', 'source_version.munchow_2020_roast_sensory.vor'),
        ('sensory.roasted_character', 'roasted character', 'active', 'external', 'source_version.munchow_2020_roast_sensory.vor'),
        ('sensory.smoky', 'smoky', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.burnt', 'burnt', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.ash', 'ash', 'active', 'external', 'source_version.munchow_2020_roast_sensory.vor'),
        ('sensory.tobacco', 'tobacco', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.earthy', 'earthy', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.damp_soil', 'damp soil', 'active', 'external', 'source_version.seninde_2020_sensory_review.vor'),
        ('sensory.mushroom', 'mushroom', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.woody', 'woody', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.cedar', 'cedar', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor'),
        ('sensory.paper', 'paper', 'active', 'external', 'source_version.seninde_2020_sensory_review.vor'),
        ('sensory.cardboard', 'cardboard', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.leather', 'leather', 'candidate', 'project_authored', 'source_version.project.coffee_sensory_kb_v0.2026-08-24'),
        ('sensory.dusty', 'dusty', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.musty', 'musty', 'active', 'external', 'source_version.ledezma_2025_geisha_rata.vor'),
        ('sensory.moldy', 'moldy', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.rubber', 'rubber', 'active', 'external', 'source_version.batali_2022_brew_temperature.vor'),
        ('sensory.petroleum', 'petroleum', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.phenolic', 'phenolic', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.sulfurous', 'sulfurous', 'active', 'external', 'source_version.seninde_2020_sensory_review.vor'),
        ('sensory.fermented_character', 'fermented', 'active', 'external', 'source_version.zhang_2019_wet_processing.vor'),
        ('sensory.wine_like_character', 'wine-like character', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.acetic_vinegar', 'acetic vinegar', 'active', 'external', 'source_version.zhang_2019_wet_processing.vor'),
        ('sensory.alcoholic', 'alcoholic', 'active', 'external', 'source_version.chambers_2016_living_lexicon.vor'),
        ('sensory.stale', 'stale', 'active', 'external', 'source_version.carvalho_2025_canephora_rata.vor')
)
INSERT INTO kb.concept (
    concept_key,
    concept_type_code,
    lifecycle_status_code,
    provenance_scope_code,
    replacement_concept_id,
    description,
    editorial_note
)
SELECT
    seed.concept_key,
    'sensory_attribute',
    seed.lifecycle_status_code,
    seed.provenance_scope_code,
    NULL,
    CASE
        WHEN seed.concept_key = 'sensory.pink_grapefruit' THEN
            'A project-defined sensory-language specialization for perceptions explicitly described as pink grapefruit.'
        ELSE
            'A project-defined sensory identity for coffee perceptions described as ' || seed.label || '.'
    END,
    CASE
        WHEN seed.concept_key = 'sensory.pink_grapefruit' THEN
            'Candidate specialization retained distinctly from grapefruit; no coffee-specific formal or peer-reviewed support for this narrower identity was verified by 2026-08-24.'
        WHEN seed.lifecycle_status_code = 'candidate' THEN
            'Candidate retained for explicit curation review; exact coffee-specific reported usage was not verified in the cited Bollen article text or a checked supplementary dataset by 2026-08-24.'
        ELSE
            'Admission reflects reviewed external evidence and independent project curation; the concept carries no intrinsic intensity, desirability, prevalence, cause, or exclusive category.'
    END
FROM sensory_seed AS seed
ON CONFLICT (concept_key) DO UPDATE
SET
    concept_type_code = EXCLUDED.concept_type_code,
    lifecycle_status_code = EXCLUDED.lifecycle_status_code,
    provenance_scope_code = EXCLUDED.provenance_scope_code,
    replacement_concept_id = EXCLUDED.replacement_concept_id,
    description = EXCLUDED.description,
    editorial_note = EXCLUDED.editorial_note;

INSERT INTO kb.concept (
    concept_key,
    concept_type_code,
    lifecycle_status_code,
    provenance_scope_code,
    replacement_concept_id,
    description,
    editorial_note
)
VALUES
    ('category.taste_oral', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for basic-taste and oral-sensation concepts.', 'Project-authored organization; not copied from a source wheel or standard.'),
    ('category.fruit', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for fruit-reference sensory concepts.', 'Project-authored organization; concepts may have other parents.'),
    ('category.citrus', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for citrus-reference sensory concepts.', 'Project-authored organization; not a reproduction of an external hierarchy.'),
    ('category.orchard_fruit', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for orchard-fruit reference concepts.', 'Project-authored organization; botanical taxonomy is not asserted.'),
    ('category.berry', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for berry-reference sensory concepts.', 'Project-authored organization; botanical taxonomy is not asserted.'),
    ('category.tropical_fruit', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for tropical-fruit reference concepts.', 'Project-authored organization; regional universality is not asserted.'),
    ('category.dried_fruit', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for dried-fruit reference concepts.', 'Project-authored organization; process causality is not asserted.'),
    ('category.floral', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for floral-reference sensory concepts.', 'Project-authored organization; not copied from a source wheel.'),
    ('category.green_herbal', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for green and herbal sensory references.', 'Project-authored organization; desirability is context dependent.'),
    ('category.tea', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for tea-reference sensory concepts.', 'Project-authored organization; composite beverage identity is not implied.'),
    ('category.nut_seed', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for nut and seed reference concepts.', 'Project-authored organization; allergen content is not asserted.'),
    ('category.spice', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for spice-reference sensory concepts.', 'Project-authored organization; not copied from a source hierarchy.'),
    ('category.sweet_brown', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for sweet and cooked-brown references.', 'Project-authored organization; sweetness intensity is not assigned.'),
    ('category.cocoa_chocolate', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for cocoa and chocolate references.', 'Project-authored organization; ingredient presence is not asserted.'),
    ('category.grain_baked', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for grain and baked references.', 'Project-authored organization; processing cause is not asserted.'),
    ('category.roast', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for roast-associated sensory concepts.', 'Project-authored organization; roast level is a separate empirical context.'),
    ('category.earth_wood', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for earth and wood reference concepts.', 'Project-authored organization; value judgment is not encoded.'),
    ('category.paper_storage', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for paper and storage-associated perceptions.', 'Project-authored organization; storage causality is not asserted.'),
    ('category.fermentation', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for fermentation-associated perceptions.', 'Sensory character remains distinct from a fermentation process entity.'),
    ('category.chemical', 'category', 'active', 'project_authored', NULL, 'A non-exclusive project grouping for chemical-reference sensory concepts.', 'Project-authored organization; chemical identity or concentration is not asserted.')
ON CONFLICT (concept_key) DO UPDATE
SET
    concept_type_code = EXCLUDED.concept_type_code,
    lifecycle_status_code = EXCLUDED.lifecycle_status_code,
    provenance_scope_code = EXCLUDED.provenance_scope_code,
    replacement_concept_id = EXCLUDED.replacement_concept_id,
    description = EXCLUDED.description,
    editorial_note = EXCLUDED.editorial_note;

INSERT INTO kb.concept (
    concept_key,
    concept_type_code,
    lifecycle_status_code,
    provenance_scope_code,
    replacement_concept_id,
    description,
    editorial_note
)
VALUES
    (
        'qualifier.jammy', 'qualifier', 'candidate', 'project_authored', NULL,
        'A candidate contextual modifier for wording described as jammy.',
        'No fixed sweetness, fruit intensity, texture, or desirability is assigned; contextual review is required.'
    ),
    (
        'process.anaerobic_fermentation', 'process_entity', 'candidate', 'project_authored', NULL,
        'A candidate process identity for coffee processing described as anaerobic fermentation.',
        'Process naming does not assert oxygen measurements, protocol equivalence, or a resulting sensory character.'
    );

-- Preserve and clarify the already seeded non-sensory fixtures.
UPDATE kb.concept
SET
    description = 'A project process identity for fermentation metadata.',
    editorial_note = 'A process record does not assert that a sample has fermented sensory character.'
WHERE concept_key = 'process.fermentation';

UPDATE kb.concept
SET
    description = 'A project composite reference for the beverage conventionally named Earl Grey.',
    editorial_note = 'The composite is neither a synonym nor a lexicalization of bergamot or black tea.'
WHERE concept_key = 'composite.earl_grey';

-- One project-authorship support row covers every independently written
-- concept scope, including externally admitted concepts whose wording is ours.
INSERT INTO evidence.concept_support (
    concept_support_key,
    concept_id,
    source_version_id,
    dataset_id,
    locator,
    notes,
    concept_support_role_code
)
SELECT
    'support.concept.' || concept.concept_key || '.project_round2a',
    concept.concept_id,
    source_version.source_version_id,
    NULL,
    'db/010_canonical_ontology_seed.sql#canonical-concepts',
    'Independently authored project scope; no external definition, intensity, reference, or hierarchy was copied.',
    'project_authorship'
FROM kb.concept AS concept
CROSS JOIN evidence.source_version AS source_version
WHERE source_version.source_version_key =
      'source_version.project.coffee_sensory_kb_v0.2026-08-24';

-- External concept-support matrix.  Each of the 92 active sensory concepts has
-- a routed peer-reviewed support row.  Pink grapefruit uses Chambers only as a
-- broader grapefruit scope basis.  The other seven sensory candidates have no
-- external exact-term support claim; all eight candidate identities remain
-- explicitly project-authored.
-- Primary routed row counts: Chambers 53 (52 active plus pink scope), Williams 9,
-- Carvalho 12, Ledezma 3, Seninde 5, Zhang 2, Muenchow 6, Batali 1, Bollen 2.
-- The two corroborating rows below bring external support to 95 rows total:
-- Chambers 54 and WCR 1, with every other routed count unchanged.  These are
-- evidence links, not imported source content.
WITH routed_concept AS (
    SELECT
        concept.concept_id,
        concept.concept_key,
        CASE
            WHEN concept.concept_key IN (
                'sensory.astringent',
                'sensory.drying',
                'sensory.fullness',
                'sensory.smooth_mouthfeel',
                'sensory.oily_mouthfeel',
                'sensory.creamy_mouthfeel',
                'sensory.syrupy_mouthfeel',
                'sensory.mouth_coating',
                'sensory.metallic'
            ) THEN 'source_version.williams_2023_acidity_mouthfeel.vor'
            WHEN concept.concept_key IN (
                'sensory.plum',
                'sensory.banana',
                'sensory.mango',
                'sensory.green_vegetal',
                'sensory.walnut',
                'sensory.cardamom',
                'sensory.ginger',
                'sensory.caramel',
                'sensory.cocoa',
                'sensory.mushroom',
                'sensory.cedar',
                'sensory.stale'
            ) THEN 'source_version.carvalho_2025_canephora_rata.vor'
            WHEN concept.concept_key IN (
                'sensory.bergamot',
                'sensory.butter',
                'sensory.musty'
            ) THEN 'source_version.ledezma_2025_geisha_rata.vor'
            WHEN concept.concept_key IN (
                'sensory.earthy',
                'sensory.wine_like_character'
            ) THEN 'source_version.bollen_2024_canephora_profiles.vor'
            WHEN concept.concept_key IN (
                'sensory.fresh_grass',
                'sensory.bell_pepper',
                'sensory.damp_soil',
                'sensory.paper',
                'sensory.sulfurous'
            ) THEN 'source_version.seninde_2020_sensory_review.vor'
            WHEN concept.concept_key IN (
                'sensory.cereal_grain',
                'sensory.baked_bread',
                'sensory.toast',
                'sensory.roasted_nut',
                'sensory.roasted_character',
                'sensory.ash'
            ) THEN 'source_version.munchow_2020_roast_sensory.vor'
            WHEN concept.concept_key = 'sensory.rubber'
                THEN 'source_version.batali_2022_brew_temperature.vor'
            WHEN concept.concept_key IN (
                'sensory.fermented_character',
                'sensory.acetic_vinegar'
            ) THEN 'source_version.zhang_2019_wet_processing.vor'
            ELSE 'source_version.chambers_2016_living_lexicon.vor'
        END AS source_version_key
    FROM kb.concept AS concept
    WHERE concept.concept_type_code = 'sensory_attribute'
      AND concept.concept_key <> 'sensory.pink_grapefruit'
      AND concept.lifecycle_status_code = 'active'

    UNION ALL

    SELECT
        concept.concept_id,
        concept.concept_key,
        'source_version.chambers_2016_living_lexicon.vor'
    FROM kb.concept AS concept
    WHERE concept.concept_key = 'sensory.pink_grapefruit'
)
INSERT INTO evidence.concept_support (
    concept_support_key,
    concept_id,
    source_version_id,
    dataset_id,
    locator,
    notes,
    concept_support_role_code
)
SELECT
    'support.concept.' || routed.concept_key || '.external_round2a',
    routed.concept_id,
    source_version.source_version_id,
    NULL,
    CASE source_version.source_version_key
        WHEN 'source_version.chambers_2016_living_lexicon.vor'
            THEN 'doi:10.1111/joss.12237; attribute-development and validation results'
        WHEN 'source_version.carvalho_2025_canephora_rata.vor'
            THEN 'doi:10.1038/s41598-025-99921-w; RATA results and discussion'
        WHEN 'source_version.ledezma_2025_geisha_rata.vor'
            THEN 'doi:10.1002/fsn3.71278; Table 2 and sensory results'
        WHEN 'source_version.seninde_2020_sensory_review.vor'
            THEN 'doi:10.3390/beverages6030044; sensory evidence review'
        WHEN 'source_version.zhang_2019_wet_processing.vor'
            THEN 'doi:10.3389/fmicb.2019.02621; wet-processing and fermentation context only'
        WHEN 'source_version.munchow_2020_roast_sensory.vor'
            THEN 'doi:10.3390/beverages6020029; multi-study roast and sensory results'
        WHEN 'source_version.batali_2022_brew_temperature.vor'
            THEN 'doi:10.3390/foods11162440; trained-panel sensory results'
        WHEN 'source_version.bollen_2024_canephora_profiles.vor'
            THEN 'doi:10.3389/fsufs.2024.1382976; article text reporting winey usage and discussing earthy sensory character'
        WHEN 'source_version.williams_2023_acidity_mouthfeel.vor'
            THEN 'doi:10.1111/joss.12886; mouthfeel evidence synthesis and panels'
    END,
    CASE
        WHEN routed.concept_key = 'sensory.pink_grapefruit' THEN
            'Supports the broader grapefruit scope only; it does not establish the narrower pink-grapefruit candidate identity.'
        WHEN source_version.source_version_key =
             'source_version.zhang_2019_wet_processing.vor' THEN
            'Processing and fermentation context used only for independent boundary review; this row does not claim that the paper reports either canonical sensory term.'
        ELSE
            'Evidence used for admission or boundary review; no source definition, hierarchy, reference, intensity, or score is imported.'
    END,
    CASE
        WHEN routed.concept_key = 'sensory.pink_grapefruit' THEN
            'scope_basis'
        WHEN source_version.source_version_key =
             'source_version.chambers_2016_living_lexicon.vor' THEN
            'lexicon_inclusion'
        WHEN routed.concept_key = 'sensory.wine_like_character' THEN
            'scope_basis'
        WHEN source_version.source_version_key =
             'source_version.zhang_2019_wet_processing.vor' THEN
            'scope_basis'
        WHEN source_version.source_version_key IN (
            'source_version.carvalho_2025_canephora_rata.vor',
            'source_version.ledezma_2025_geisha_rata.vor',
            'source_version.batali_2022_brew_temperature.vor',
            'source_version.bollen_2024_canephora_profiles.vor'
        ) THEN 'reported_usage'
        ELSE 'scope_basis'
    END
FROM routed_concept AS routed
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = routed.source_version_key;

-- Independent cross-source admission remains explicit for the two concepts
-- whose Zhang rows are processing-context scope bases, not reported sensory
-- usages.  Chambers includes fermented character as a lexicon entry.  WCR's
-- public page lists Acetic acid, which is retained only as a scope basis for
-- the separately project-authored acetic-vinegar identity; equivalence is not
-- asserted here or in the source-scheme crosswalk.
INSERT INTO evidence.concept_support (
    concept_support_key,
    concept_id,
    source_version_id,
    dataset_id,
    locator,
    notes,
    concept_support_role_code
)
SELECT
    seed.concept_support_key,
    concept.concept_id,
    source_version.source_version_id,
    NULL,
    seed.locator,
    seed.notes,
    seed.concept_support_role_code
FROM (
    VALUES
        (
            'support.concept.sensory.fermented_character.chambers_round2a',
            'sensory.fermented_character',
            'source_version.chambers_2016_living_lexicon.vor',
            'doi:10.1111/joss.12237; lexicon inclusion only',
            'Corroborates admission of fermented sensory character without importing the source definition, references, intensity, or hierarchy.',
            'lexicon_inclusion'
        ),
        (
            'support.concept.sensory.acetic_vinegar.wcr_scope_round2a',
            'sensory.acetic_vinegar',
            'source_version.wcr_sensory_lexicon_2_0.public_page',
            'public landing page label: Acetic acid',
            'Broader source-local terminology considered during independent scope review; exact equivalence and source-content reuse are not asserted.',
            'scope_basis'
        )
) AS seed(
    concept_support_key,
    concept_key,
    source_version_key,
    locator,
    notes,
    concept_support_role_code
)
JOIN kb.concept AS concept
  ON concept.concept_key = seed.concept_key
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = seed.source_version_key;

-- Add one English preferred expression only where Round 1 did not already
-- provide one.  Generated labels are simple project display forms derived from
-- stable keys; they are not source labels.
WITH unlabeled_concept AS (
    SELECT
        concept.concept_id,
        concept.concept_key,
        CASE
            WHEN concept.concept_type_code = 'category' THEN
                'category_' || split_part(concept.concept_key, '.', 2)
            ELSE split_part(concept.concept_key, '.', 2)
        END AS expression_local_key,
        replace(split_part(concept.concept_key, '.', 2), '_', ' ')
            || CASE
                WHEN concept.concept_type_code = 'category' THEN ' category'
                ELSE ''
            END AS label
    FROM kb.concept AS concept
    WHERE NOT EXISTS (
        SELECT 1
        FROM kb.lexicalization AS lexicalization
        JOIN ref.mapping_type AS mapping_type
          ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
        WHERE lexicalization.concept_id = concept.concept_id
          AND lexicalization.lifecycle_status_code = 'active'
          AND mapping_type.is_preferred
    )
)
INSERT INTO kb.lexical_expression (
    expression_key,
    language_tag_code,
    expression_text,
    lifecycle_status_code
)
SELECT
    'expression.en.' || unlabeled.expression_local_key,
    'en',
    unlabeled.label,
    'active'
FROM unlabeled_concept AS unlabeled;

WITH unlabeled_concept AS (
    SELECT
        concept.concept_id,
        concept.concept_key,
        CASE
            WHEN concept.concept_type_code = 'category' THEN
                'category_' || split_part(concept.concept_key, '.', 2)
            ELSE split_part(concept.concept_key, '.', 2)
        END AS expression_local_key
    FROM kb.concept AS concept
    WHERE NOT EXISTS (
        SELECT 1
        FROM kb.lexicalization AS lexicalization
        JOIN ref.mapping_type AS mapping_type
          ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
        WHERE lexicalization.concept_id = concept.concept_id
          AND lexicalization.lifecycle_status_code = 'active'
          AND mapping_type.is_preferred
    )
)
INSERT INTO kb.lexicalization (
    lexicalization_key,
    expression_id,
    concept_id,
    mapping_type_code,
    lifecycle_status_code,
    provenance_scope_code,
    valid_from,
    valid_until
)
SELECT
    'lexicalization.en.' || unlabeled.expression_local_key || '.preferred',
    expression.expression_id,
    unlabeled.concept_id,
    'preferred_label',
    'active',
    'project_authored',
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL
FROM unlabeled_concept AS unlabeled
JOIN kb.lexical_expression AS expression
  ON expression.expression_key =
     'expression.en.' || unlabeled.expression_local_key;

-- Preferred English mappings are independently authored project decisions,
-- even when the concept identity has external admission evidence.  Existing
-- variants and the winey polysemy fixture were already project-authored in
-- Round 1 and remain so; source-scheme mappings are governed separately.
UPDATE kb.lexicalization AS lexicalization
SET provenance_scope_code = 'project_authored'
FROM ref.mapping_type AS mapping_type
WHERE mapping_type.mapping_type_code = lexicalization.mapping_type_code
  AND mapping_type.is_preferred;

INSERT INTO evidence.lexicalization_support (
    lexicalization_support_key,
    lexicalization_id,
    source_version_id,
    dataset_id,
    locator,
    notes
)
SELECT
    'support.' || lexicalization.lexicalization_key || '.project_round2a',
    lexicalization.lexicalization_id,
    source_version.source_version_id,
    NULL,
    'db/010_canonical_ontology_seed.sql#lexicalizations',
    'Project-curated English lexical mapping; no external definition is copied.'
FROM kb.lexicalization AS lexicalization
CROSS JOIN evidence.source_version AS source_version
WHERE source_version.source_version_key =
      'source_version.project.coffee_sensory_kb_v0.2026-08-24';

-- Forward lifecycle corrections preserve the smoke assertions for audit while
-- removing them from the current canonical graph.
UPDATE kb.concept_relation
SET
    lifecycle_status_code = 'deprecated',
    valid_until = TIMESTAMPTZ '2026-08-24 00:00:01+00'
WHERE relation_key IN (
    'relation.grapefruit.broader_than.pink_grapefruit',
    'relation.bergamot.sensory_neighbour.jasmine'
);

-- Project-authored direct hierarchy.  It is intentionally polyhierarchical:
-- metallic belongs directly to both taste/oral and chemical, and green tea to
-- both green/herbal and tea.  No transitive-closure rows are stored.
WITH direct_edge(parent_key, child_key) AS (
    VALUES
        ('category.fruit', 'category.citrus'),
        ('category.fruit', 'category.orchard_fruit'),
        ('category.fruit', 'category.berry'),
        ('category.fruit', 'category.tropical_fruit'),
        ('category.fruit', 'category.dried_fruit'),
        ('category.taste_oral', 'sensory.sweet'),
        ('category.taste_oral', 'sensory.sour'),
        ('category.taste_oral', 'sensory.bitter'),
        ('category.taste_oral', 'sensory.salty'),
        ('category.taste_oral', 'sensory.astringent'),
        ('category.taste_oral', 'sensory.drying'),
        ('category.taste_oral', 'sensory.fullness'),
        ('category.taste_oral', 'sensory.smooth_mouthfeel'),
        ('category.taste_oral', 'sensory.oily_mouthfeel'),
        ('category.taste_oral', 'sensory.creamy_mouthfeel'),
        ('category.taste_oral', 'sensory.syrupy_mouthfeel'),
        ('category.taste_oral', 'sensory.mouth_coating'),
        ('category.taste_oral', 'sensory.metallic'),
        ('category.fruit', 'sensory.grape'),
        ('category.citrus', 'sensory.lemon'),
        ('category.citrus', 'sensory.lime'),
        ('category.citrus', 'sensory.orange'),
        ('category.citrus', 'sensory.grapefruit'),
        ('category.citrus', 'sensory.bergamot'),
        ('category.orchard_fruit', 'sensory.apple'),
        ('category.orchard_fruit', 'sensory.pear'),
        ('category.orchard_fruit', 'sensory.peach'),
        ('category.orchard_fruit', 'sensory.plum'),
        ('category.orchard_fruit', 'sensory.cherry'),
        ('category.orchard_fruit', 'sensory.pomegranate'),
        ('category.berry', 'sensory.strawberry'),
        ('category.berry', 'sensory.raspberry'),
        ('category.berry', 'sensory.blueberry'),
        ('category.berry', 'sensory.blackberry'),
        ('category.berry', 'sensory.blackcurrant'),
        ('category.tropical_fruit', 'sensory.banana'),
        ('category.tropical_fruit', 'sensory.pineapple'),
        ('category.tropical_fruit', 'sensory.mango'),
        ('category.tropical_fruit', 'sensory.coconut'),
        ('category.dried_fruit', 'sensory.raisin'),
        ('category.dried_fruit', 'sensory.prune'),
        ('category.floral', 'sensory.jasmine'),
        ('category.floral', 'sensory.rose'),
        ('category.floral', 'sensory.orange_blossom'),
        ('category.floral', 'sensory.chamomile'),
        ('category.green_herbal', 'sensory.fresh_grass'),
        ('category.green_herbal', 'sensory.hay'),
        ('category.green_herbal', 'sensory.green_vegetal'),
        ('category.green_herbal', 'sensory.pea_pod'),
        ('category.green_herbal', 'sensory.bell_pepper'),
        ('category.green_herbal', 'sensory.mint'),
        ('category.green_herbal', 'sensory.eucalyptus'),
        ('category.green_herbal', 'sensory.lemongrass'),
        ('category.green_herbal', 'sensory.green_tea'),
        ('category.tea', 'sensory.black_tea'),
        ('category.tea', 'sensory.green_tea'),
        ('category.nut_seed', 'sensory.almond'),
        ('category.nut_seed', 'sensory.hazelnut'),
        ('category.nut_seed', 'sensory.peanut'),
        ('category.nut_seed', 'sensory.walnut'),
        ('category.spice', 'sensory.cinnamon'),
        ('category.spice', 'sensory.clove'),
        ('category.spice', 'sensory.nutmeg'),
        ('category.spice', 'sensory.black_pepper'),
        ('category.spice', 'sensory.cardamom'),
        ('category.spice', 'sensory.ginger'),
        ('category.spice', 'sensory.anise'),
        ('category.sweet_brown', 'sensory.honey'),
        ('category.sweet_brown', 'sensory.brown_sugar'),
        ('category.sweet_brown', 'sensory.molasses'),
        ('category.sweet_brown', 'sensory.caramel'),
        ('category.sweet_brown', 'sensory.vanilla'),
        ('category.sweet_brown', 'sensory.butter'),
        ('category.cocoa_chocolate', 'sensory.cocoa'),
        ('category.cocoa_chocolate', 'sensory.dark_chocolate'),
        ('category.grain_baked', 'sensory.malt'),
        ('category.grain_baked', 'sensory.cereal_grain'),
        ('category.grain_baked', 'sensory.baked_bread'),
        ('category.grain_baked', 'sensory.toast'),
        ('category.roast', 'sensory.roasted_nut'),
        ('category.roast', 'sensory.roasted_character'),
        ('category.roast', 'sensory.smoky'),
        ('category.roast', 'sensory.burnt'),
        ('category.roast', 'sensory.ash'),
        ('category.roast', 'sensory.tobacco'),
        ('category.earth_wood', 'sensory.earthy'),
        ('category.earth_wood', 'sensory.damp_soil'),
        ('category.earth_wood', 'sensory.mushroom'),
        ('category.earth_wood', 'sensory.woody'),
        ('category.earth_wood', 'sensory.cedar'),
        ('category.earth_wood', 'sensory.leather'),
        ('category.earth_wood', 'sensory.dusty'),
        ('category.earth_wood', 'sensory.musty'),
        ('category.earth_wood', 'sensory.moldy'),
        ('category.paper_storage', 'sensory.paper'),
        ('category.paper_storage', 'sensory.cardboard'),
        ('category.paper_storage', 'sensory.stale'),
        ('category.chemical', 'sensory.rubber'),
        ('category.chemical', 'sensory.petroleum'),
        ('category.chemical', 'sensory.phenolic'),
        ('category.chemical', 'sensory.sulfurous'),
        ('category.chemical', 'sensory.metallic'),
        ('category.fermentation', 'sensory.fermented_character'),
        ('category.fermentation', 'sensory.wine_like_character'),
        ('category.fermentation', 'sensory.acetic_vinegar'),
        ('category.fermentation', 'sensory.alcoholic')
)
INSERT INTO kb.concept_relation (
    relation_key,
    relation_type_code,
    subject_concept_id,
    object_concept_id,
    lifecycle_status_code,
    provenance_scope_code,
    valid_from,
    valid_until
)
SELECT
    'relation.project.' || replace(edge.parent_key, '.', '_')
        || '.broader_than.' || replace(edge.child_key, '.', '_'),
    'broader_than',
    parent.concept_id,
    child.concept_id,
    child.lifecycle_status_code,
    'project_authored',
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL
FROM direct_edge AS edge
JOIN kb.concept AS parent
  ON parent.concept_key = edge.parent_key
JOIN kb.concept AS child
  ON child.concept_key = edge.child_key
WHERE NOT EXISTS (
    SELECT 1
    FROM kb.concept_relation AS existing
    WHERE existing.relation_type_code = 'broader_than'
      AND existing.subject_concept_id = parent.concept_id
      AND existing.object_concept_id = child.concept_id
);

INSERT INTO evidence.relation_support (
    relation_support_key,
    concept_relation_id,
    source_version_id,
    dataset_id,
    locator,
    notes
)
SELECT
    'support.' || relation.relation_key || '.project_round2a',
    relation.concept_relation_id,
    source_version.source_version_id,
    NULL,
    'db/010_canonical_ontology_seed.sql#project-direct-hierarchy',
    'Project-authored direct relation; no source hierarchy, universal placement, or transitive-closure row is asserted.'
FROM kb.concept_relation AS relation
CROSS JOIN evidence.source_version AS source_version
WHERE source_version.source_version_key =
      'source_version.project.coffee_sensory_kb_v0.2026-08-24';

INSERT INTO kb.concept_dimension_link (
    link_key,
    concept_id,
    sensory_dimension_id,
    lifecycle_status_code,
    provenance_scope_code,
    link_semantics
)
SELECT
    seed.link_key,
    concept.concept_id,
    dimension.sensory_dimension_id,
    'active',
    'project_authored',
    seed.link_semantics
FROM (
    VALUES
        ('dimension_link.sensory_sweet.taste_sweetness', 'sensory.sweet', 'taste.sweetness', 'The concept may be used to describe observations measured on a protocol-specific sweetness construct; no value is assigned.'),
        ('dimension_link.sensory_sour.taste_sourness_acidity', 'sensory.sour', 'taste.sourness_acidity', 'The concept may be used to describe observations measured on a protocol-specific sourness/acidity construct; no value is assigned.'),
        ('dimension_link.sensory_bitter.taste_bitterness', 'sensory.bitter', 'taste.bitterness', 'The concept may be used to describe observations measured on a protocol-specific bitterness construct; no value is assigned.'),
        ('dimension_link.sensory_salty.taste_saltiness', 'sensory.salty', 'taste.saltiness', 'The concept may be used to describe observations measured on a protocol-specific saltiness construct; no value is assigned.'),
        ('dimension_link.sensory_fullness.tactile_body_fullness', 'sensory.fullness', 'tactile.body_fullness', 'The concept may be used to describe observations measured on a protocol-specific body/fullness construct; no value is assigned.'),
        ('dimension_link.sensory_drying.tactile_drying_astringency', 'sensory.drying', 'tactile.drying_astringency', 'The concept may be used to describe observations measured on a protocol-specific drying/astringency construct; no value is assigned.')
) AS seed(link_key, concept_key, dimension_key, link_semantics)
JOIN kb.concept AS concept
  ON concept.concept_key = seed.concept_key
JOIN kb.sensory_dimension AS dimension
  ON dimension.dimension_key = seed.dimension_key;

INSERT INTO evidence.concept_dimension_link_support (
    concept_dimension_link_support_key,
    concept_dimension_link_id,
    source_version_id,
    dataset_id,
    locator,
    notes
)
SELECT
    'support.' || link.link_key || '.project_round2a',
    link.concept_dimension_link_id,
    source_version.source_version_id,
    NULL,
    'db/010_canonical_ontology_seed.sql#dimension-links',
    'Project-authored nonnumeric association; no intrinsic concept score or empirical measurement is asserted.'
FROM kb.concept_dimension_link AS link
CROSS JOIN evidence.source_version AS source_version
WHERE source_version.source_version_key =
      'source_version.project.coffee_sensory_kb_v0.2026-08-24';

-- Project projection: every canonical concept receives one project-local node
-- and one reviewed equivalent-scope mapping.  Candidate concepts remain
-- candidate nodes/mappings, so complete storage does not publish them as
-- current canonical terms.  This is the only seeded scheme with hierarchy.
INSERT INTO evidence.concept_scheme (
    concept_scheme_key,
    source_version_id,
    lifecycle_status_code,
    name,
    description,
    valid_from,
    valid_until,
    metadata
)
SELECT
    'scheme.project.coffee_sensory_kb_v0.2026-08-24',
    source_version.source_version_id,
    'active',
    'Coffee Sensory Knowledge Base V0 project projection',
    'Complete project-authored projection of the canonical concepts and direct hierarchy as curated on 2026-08-24.',
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL,
    '{"completeness":"complete","authorship":"project","production_export_allowed":true,"copied_source_hierarchy":false}'::JSONB
FROM evidence.source_version AS source_version
WHERE source_version.source_version_key =
      'source_version.project.coffee_sensory_kb_v0.2026-08-24';

INSERT INTO evidence.concept_scheme_node (
    concept_scheme_node_key,
    concept_scheme_id,
    source_node_key,
    source_label,
    lifecycle_status_code,
    valid_from,
    valid_until,
    notes,
    metadata
)
SELECT
    'scheme_node.project_v0.' || replace(concept.concept_key, '.', '_'),
    scheme.concept_scheme_id,
    concept.concept_key,
    expression.expression_text,
    concept.lifecycle_status_code,
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL,
    'Project-local node; its label, scope, and placement are independently curated.',
    jsonb_build_object(
        'canonical_concept_key', concept.concept_key,
        'concept_type_code', concept.concept_type_code,
        'project_authored', TRUE
    )
FROM kb.concept AS concept
JOIN kb.lexicalization AS lexicalization
  ON lexicalization.concept_id = concept.concept_id
 AND lexicalization.lifecycle_status_code = 'active'
JOIN ref.mapping_type AS mapping_type
  ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
 AND mapping_type.is_preferred
JOIN kb.lexical_expression AS expression
  ON expression.expression_id = lexicalization.expression_id
 AND expression.lifecycle_status_code = 'active'
 AND expression.language_tag_code = 'en'
CROSS JOIN evidence.concept_scheme AS scheme
WHERE scheme.concept_scheme_key =
      'scheme.project.coffee_sensory_kb_v0.2026-08-24';

INSERT INTO evidence.concept_scheme_mapping (
    concept_scheme_mapping_key,
    concept_scheme_id,
    concept_scheme_node_id,
    concept_id,
    scheme_concept_mapping_role_code,
    lifecycle_status_code,
    valid_from,
    valid_until,
    notes
)
SELECT
    'scheme_mapping.project_v0.' || replace(concept.concept_key, '.', '_'),
    scheme.concept_scheme_id,
    node.concept_scheme_node_id,
    concept.concept_id,
    'equivalent_scope',
    concept.lifecycle_status_code,
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL,
    'Identity projection into the project-authored scheme; it does not create a lexical synonym or an external-source claim.'
FROM kb.concept AS concept
CROSS JOIN evidence.concept_scheme AS scheme
JOIN evidence.concept_scheme_node AS node
  ON node.concept_scheme_id = scheme.concept_scheme_id
 AND node.source_node_key = concept.concept_key
WHERE scheme.concept_scheme_key =
      'scheme.project.coffee_sensory_kb_v0.2026-08-24';

INSERT INTO evidence.concept_scheme_edge (
    concept_scheme_edge_key,
    concept_scheme_id,
    parent_node_id,
    child_node_id,
    lifecycle_status_code,
    valid_from,
    valid_until,
    notes
)
SELECT
    'scheme_edge.project_v0.' || replace(relation.relation_key, '.', '_'),
    scheme.concept_scheme_id,
    parent_node.concept_scheme_node_id,
    child_node.concept_scheme_node_id,
    relation.lifecycle_status_code,
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL,
    'Project-authored direct projection; no source hierarchy or transitive-closure edge is asserted.'
FROM kb.concept_relation AS relation
JOIN kb.concept AS parent
  ON parent.concept_id = relation.subject_concept_id
JOIN kb.concept AS child
  ON child.concept_id = relation.object_concept_id
CROSS JOIN evidence.concept_scheme AS scheme
JOIN evidence.concept_scheme_node AS parent_node
  ON parent_node.concept_scheme_id = scheme.concept_scheme_id
 AND parent_node.source_node_key = parent.concept_key
JOIN evidence.concept_scheme_node AS child_node
  ON child_node.concept_scheme_id = scheme.concept_scheme_id
 AND child_node.source_node_key = child.concept_key
WHERE scheme.concept_scheme_key =
      'scheme.project.coffee_sensory_kb_v0.2026-08-24'
  AND relation.relation_type_code = 'broader_than'
  AND relation.lifecycle_status_code IN ('active', 'candidate');

-- Rights-limited WCR public-page projection.  These are exactly the 24 labels
-- enumerated on the public WCR 2.0 landing page, stored flat and without
-- definitions, references, intensities, source hierarchy, or inferred terms.
INSERT INTO evidence.concept_scheme (
    concept_scheme_key,
    source_version_id,
    lifecycle_status_code,
    name,
    description,
    valid_from,
    valid_until,
    metadata
)
SELECT
    'scheme.wcr.sensory_lexicon_2_0.public_24_partial',
    source_version.source_version_id,
    'active',
    'WCR Sensory Lexicon 2.0 public-page labels (partial)',
    'Rights-gated partial source-local projection limited to 24 labels explicitly listed on the public WCR landing page; intentionally flat and incomplete.',
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL,
    '{"completeness":"partial","public_page_label_count":24,"definitions_imported":false,"references_imported":false,"intensities_imported":false,"hierarchy_imported":false,"production_export_allowed":false}'::JSONB
FROM evidence.source_version AS source_version
WHERE source_version.source_version_key =
      'source_version.wcr_sensory_lexicon_2_0.public_page';

INSERT INTO evidence.concept_scheme_node (
    concept_scheme_node_key,
    concept_scheme_id,
    source_node_key,
    source_label,
    lifecycle_status_code,
    valid_from,
    valid_until,
    notes,
    metadata
)
SELECT
    'scheme_node.wcr2.' || seed.local_key,
    scheme.concept_scheme_id,
    'wcr2.public_page.' || seed.local_key,
    seed.source_label,
    'active',
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL,
    'Public-page source label retained as rights-gated metadata; no definition, reference, intensity, or hierarchy is stored.',
    jsonb_build_object(
        'public_page_enumerated', TRUE,
        'mapping_review_status',
        CASE WHEN seed.is_mapped THEN 'reviewed_mapping' ELSE 'unmapped' END
    )
FROM (
    VALUES
        ('sour', 'Sour', TRUE),
        ('bitter', 'Bitter', TRUE),
        ('salty', 'Salty', TRUE),
        ('apple', 'Apple', TRUE),
        ('grape', 'Grape', TRUE),
        ('coconut', 'Coconut', TRUE),
        ('pineapple', 'Pineapple', TRUE),
        ('acetic_acid', 'Acetic acid', TRUE),
        ('butyric_acid', 'Butyric acid', FALSE),
        ('isovaleric_acid', 'Isovaleric acid', FALSE),
        ('fermented', 'Fermented', TRUE),
        ('peapod', 'Peapod', TRUE),
        ('fresh', 'Fresh', FALSE),
        ('papery', 'Papery', TRUE),
        ('musty_earthy', 'Musty/Earthy', FALSE),
        ('musty_dusty', 'Musty/Dusty', FALSE),
        ('moldy_damp', 'Moldy/Damp', FALSE),
        ('phenolic', 'Phenolic', TRUE),
        ('petroleum', 'Petroleum', TRUE),
        ('brown_spice', 'Brown Spice', FALSE),
        ('almond', 'Almond', TRUE),
        ('vanillin', 'Vanillin', FALSE),
        ('floral', 'Floral', FALSE),
        ('jasmine', 'Jasmine', TRUE)
) AS seed(local_key, source_label, is_mapped)
CROSS JOIN evidence.concept_scheme AS scheme
WHERE scheme.concept_scheme_key =
      'scheme.wcr.sensory_lexicon_2_0.public_24_partial';

-- Reviewed WCR crosswalk: 12 equivalent-scope mappings and three explicit
-- associations.  The other nine source nodes remain intentionally unmapped.
INSERT INTO evidence.concept_scheme_mapping (
    concept_scheme_mapping_key,
    concept_scheme_id,
    concept_scheme_node_id,
    concept_id,
    scheme_concept_mapping_role_code,
    lifecycle_status_code,
    valid_from,
    valid_until,
    notes
)
SELECT
    'scheme_mapping.wcr2.' || seed.local_key || '.'
        || replace(seed.concept_key, '.', '_'),
    scheme.concept_scheme_id,
    node.concept_scheme_node_id,
    concept.concept_id,
    seed.mapping_role_code,
    'active',
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL,
    CASE seed.mapping_role_code
        WHEN 'equivalent_scope' THEN
            'Reviewed as equivalent in scope for this source version; no canonical lexicalization or source hierarchy is created.'
        ELSE
            'Reviewed association only; equivalence, broader scope, and narrower scope are explicitly not asserted.'
    END
FROM (
    VALUES
        ('sour', 'sensory.sour', 'equivalent_scope'),
        ('bitter', 'sensory.bitter', 'equivalent_scope'),
        ('salty', 'sensory.salty', 'equivalent_scope'),
        ('apple', 'sensory.apple', 'equivalent_scope'),
        ('grape', 'sensory.grape', 'equivalent_scope'),
        ('coconut', 'sensory.coconut', 'equivalent_scope'),
        ('pineapple', 'sensory.pineapple', 'equivalent_scope'),
        ('peapod', 'sensory.pea_pod', 'equivalent_scope'),
        ('phenolic', 'sensory.phenolic', 'equivalent_scope'),
        ('petroleum', 'sensory.petroleum', 'equivalent_scope'),
        ('almond', 'sensory.almond', 'equivalent_scope'),
        ('jasmine', 'sensory.jasmine', 'equivalent_scope'),
        ('acetic_acid', 'sensory.acetic_vinegar', 'associated_with_concept'),
        ('fermented', 'sensory.fermented_character', 'associated_with_concept'),
        ('papery', 'sensory.paper', 'associated_with_concept')
) AS seed(local_key, concept_key, mapping_role_code)
CROSS JOIN evidence.concept_scheme AS scheme
JOIN evidence.concept_scheme_node AS node
  ON node.concept_scheme_id = scheme.concept_scheme_id
 AND node.source_node_key = 'wcr2.public_page.' || seed.local_key
JOIN kb.concept AS concept
  ON concept.concept_key = seed.concept_key
WHERE scheme.concept_scheme_key =
      'scheme.wcr.sensory_lexicon_2_0.public_24_partial';

-- Explicitly excluded from canonical rows rather than padded into the target:
-- WCR amplitude, overall impact, blended, and longevity are meta/amplitude
-- constructs requiring a separate governance decision.  The nine WCR nodes
-- above marked unmapped remain source-local because their boundaries are too
-- broad, compound, or unsupported for a safe V0 crosswalk.

-- Frozen seed audit.  These checks fail the transaction rather than allowing a
-- partial ontology or accidental vocabulary reproduction to become canonical.
DO $round2a_seed_contract$
DECLARE
    observed BIGINT;
BEGIN
    SELECT count(*) INTO observed
    FROM kb.concept
    WHERE concept_type_code = 'sensory_attribute'
      AND lifecycle_status_code = 'active';
    IF observed <> 92 THEN
        RAISE EXCEPTION 'round2a seed expected 92 active sensory attributes, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM kb.concept
    WHERE concept_type_code = 'sensory_attribute'
      AND lifecycle_status_code = 'candidate';
    IF observed <> 8 THEN
        RAISE EXCEPTION 'round2a seed expected eight candidate sensory attributes, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM kb.concept
    WHERE concept_type_code = 'category';
    IF observed <> 20 THEN
        RAISE EXCEPTION 'round2a seed expected 20 project categories, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM kb.concept
    WHERE concept_type_code = 'qualifier'
      AND lifecycle_status_code = 'candidate';
    IF observed <> 6 THEN
        RAISE EXCEPTION 'round2a seed expected six candidate qualifiers, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_support
    WHERE concept_support_role_code = 'legacy_unspecified';
    IF observed <> 0 THEN
        RAISE EXCEPTION 'round2a seed expected no legacy-unspecified concept support, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM kb.concept AS concept
    WHERE concept.concept_type_code = 'sensory_attribute'
      AND concept.lifecycle_status_code = 'active'
      AND EXISTS (
          SELECT 1
          FROM evidence.concept_support AS support
          JOIN evidence.source_version AS source_version
            ON source_version.source_version_id = support.source_version_id
          WHERE support.concept_id = concept.concept_id
            AND support.concept_support_role_code IN (
                'lexicon_inclusion',
                'reported_usage',
                'scope_basis'
            )
            AND source_version.source_version_key <>
                'source_version.project.coffee_sensory_kb_v0.2026-08-24'
      );
    IF observed <> 92 THEN
        RAISE EXCEPTION 'round2a seed expected external controlled-role support for all 92 active sensory attributes, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme
    WHERE lifecycle_status_code = 'active';
    IF observed <> 2 THEN
        RAISE EXCEPTION 'round2a seed expected exactly two active schemes, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_node AS node
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = node.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.project.coffee_sensory_kb_v0.2026-08-24';
    IF observed <> 130 THEN
        RAISE EXCEPTION 'round2a project scheme expected 130 nodes, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_mapping AS mapping
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = mapping.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.project.coffee_sensory_kb_v0.2026-08-24';
    IF observed <> 130 THEN
        RAISE EXCEPTION 'round2a project scheme expected 130 mappings, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_edge AS edge
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = edge.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.project.coffee_sensory_kb_v0.2026-08-24';
    IF observed <> 106 THEN
        RAISE EXCEPTION 'round2a project scheme expected 106 direct edges, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_edge AS edge
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = edge.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.project.coffee_sensory_kb_v0.2026-08-24'
      AND edge.lifecycle_status_code = 'active';
    IF observed <> 98 THEN
        RAISE EXCEPTION 'round2a project scheme expected 98 active direct edges, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_edge AS edge
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = edge.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.project.coffee_sensory_kb_v0.2026-08-24'
      AND edge.lifecycle_status_code = 'candidate';
    IF observed <> 8 THEN
        RAISE EXCEPTION 'round2a project scheme expected eight candidate direct edges, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_node AS node
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = node.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.wcr.sensory_lexicon_2_0.public_24_partial';
    IF observed <> 24 THEN
        RAISE EXCEPTION 'round2a WCR partial expected 24 nodes, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_mapping AS mapping
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = mapping.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.wcr.sensory_lexicon_2_0.public_24_partial';
    IF observed <> 15 THEN
        RAISE EXCEPTION 'round2a WCR partial expected 15 mappings, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_mapping AS mapping
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = mapping.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
      AND mapping.scheme_concept_mapping_role_code = 'equivalent_scope';
    IF observed <> 12 THEN
        RAISE EXCEPTION 'round2a WCR partial expected 12 equivalent-scope mappings, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_mapping AS mapping
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = mapping.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
      AND mapping.scheme_concept_mapping_role_code = 'associated_with_concept';
    IF observed <> 3 THEN
        RAISE EXCEPTION 'round2a WCR partial expected three association-only mappings, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM evidence.concept_scheme_edge AS edge
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = edge.concept_scheme_id
    WHERE scheme.concept_scheme_key =
          'scheme.wcr.sensory_lexicon_2_0.public_24_partial';
    IF observed <> 0 THEN
        RAISE EXCEPTION 'round2a WCR partial expected zero hierarchy edges, found %', observed;
    END IF;

    SELECT count(*) INTO observed
    FROM kb.concept_dimension_link
    WHERE lifecycle_status_code = 'active';
    IF observed <> 6 THEN
        RAISE EXCEPTION 'round2a seed expected six nonnumeric dimension links, found %', observed;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM kb.lexicalization AS lexicalization
        JOIN ref.mapping_type AS mapping_type
          ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
        WHERE lexicalization.lifecycle_status_code = 'active'
          AND mapping_type.is_preferred
          AND lexicalization.provenance_scope_code <> 'project_authored'
    ) THEN
        RAISE EXCEPTION 'round2a preferred English lexical mappings must be project-authored';
    END IF;

    -- Exact rights matrix for every non-project source version present after
    -- this migration.  The comparison both rejects an unlisted external
    -- version and detects any missing expected version or permissive flag
    -- drift, including production export on otherwise open-access evidence.
    IF EXISTS (
        WITH expected_rights(
            source_version_key,
            license_policy_key,
            access_class_code,
            rights_status_code,
            redistributable,
            derivative_work_allowed,
            commercial_use_allowed,
            machine_use_allowed,
            production_export_allowed
        ) AS (
            VALUES
                ('source_version.chambers_2016_living_lexicon.vor', 'license.chambers_2016.cc_by_nc_4_0.metadata_only.v1', 'metadata_only', 'verified', TRUE, TRUE, FALSE, TRUE, FALSE),
                ('source_version.carvalho_2025_canephora_rata.vor', 'license.carvalho_2025.cc_by_nc_nd_4_0.metadata_only.v1', 'metadata_only', 'verified', TRUE, FALSE, FALSE, FALSE, FALSE),
                ('source_version.ledezma_2025_geisha_rata.vor', 'license.wiley_article.rights_unconfirmed.metadata_only.v1', 'metadata_only', 'unknown', FALSE, FALSE, FALSE, FALSE, FALSE),
                ('source_version.seninde_2020_sensory_review.vor', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'public', 'verified', TRUE, TRUE, TRUE, TRUE, FALSE),
                ('source_version.zhang_2019_wet_processing.vor', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'public', 'verified', TRUE, TRUE, TRUE, TRUE, FALSE),
                ('source_version.munchow_2020_roast_sensory.vor', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'public', 'verified', TRUE, TRUE, TRUE, TRUE, FALSE),
                ('source_version.batali_2022_brew_temperature.vor', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'public', 'verified', TRUE, TRUE, TRUE, TRUE, FALSE),
                ('source_version.bollen_2024_canephora_profiles.vor', 'license.peer_reviewed.cc_by_4_0.evidence_only.v1', 'public', 'verified', TRUE, TRUE, TRUE, TRUE, FALSE),
                ('source_version.williams_2023_acidity_mouthfeel.vor', 'license.williams_2023.cc_by_nc_4_0.metadata_only.v1', 'metadata_only', 'verified', TRUE, TRUE, FALSE, TRUE, FALSE),
                ('source_version.wcr_sensory_lexicon_2_0.public_page', 'license.wcr_lexicon.personal_use.metadata_only.v1', 'metadata_only', 'verified', FALSE, FALSE, FALSE, FALSE, FALSE),
                ('source_version.sca_cva.web_2026-08-24', 'license.sca_cva.all_rights_reserved.metadata_only.v1', 'metadata_only', 'verified', FALSE, FALSE, FALSE, FALSE, FALSE),
                ('source_version.iso_18794_2025.edition_2', 'license.iso.no_reproduction_or_machine_use.metadata_only.v1', 'metadata_only', 'verified', FALSE, FALSE, FALSE, FALSE, FALSE)
        ), actual_external AS (
            SELECT
                source_version.source_version_key,
                policy.license_policy_key,
                policy.access_class_code,
                policy.rights_status_code,
                policy.redistributable,
                policy.derivative_work_allowed,
                policy.commercial_use_allowed,
                policy.machine_use_allowed,
                policy.production_export_allowed
            FROM evidence.source_version AS source_version
            JOIN evidence.source AS source
              ON source.source_id = source_version.source_id
            JOIN evidence.license_policy AS policy
              ON policy.license_policy_id = source_version.license_policy_id
            WHERE source.source_key NOT IN (
                'source.project_smoke_seed',
                'source.synthetic_restricted_fixture',
                'source.project.coffee_sensory_kb_v0_round2a'
            )
        )
        SELECT 1
        FROM actual_external AS actual
        LEFT JOIN expected_rights AS expected
          ON expected.source_version_key = actual.source_version_key
        WHERE expected.source_version_key IS NULL
           OR ROW(
                actual.license_policy_key,
                actual.access_class_code,
                actual.rights_status_code,
                actual.redistributable,
                actual.derivative_work_allowed,
                actual.commercial_use_allowed,
                actual.machine_use_allowed,
                actual.production_export_allowed
              ) IS DISTINCT FROM ROW(
                expected.license_policy_key,
                expected.access_class_code,
                expected.rights_status_code,
                expected.redistributable,
                expected.derivative_work_allowed,
                expected.commercial_use_allowed,
                expected.machine_use_allowed,
                expected.production_export_allowed
              )

        UNION ALL

        SELECT 1
        FROM expected_rights AS expected
        LEFT JOIN actual_external AS actual
          ON actual.source_version_key = expected.source_version_key
        WHERE actual.source_version_key IS NULL
    ) THEN
        RAISE EXCEPTION 'round2a external source-version rights matrix is incomplete or has permissive flag drift';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM evidence.license_policy AS policy
        JOIN evidence.source_version AS source_version
          ON source_version.license_policy_id = policy.license_policy_id
        WHERE source_version.source_version_key IN (
            'source_version.chambers_2016_living_lexicon.vor',
            'source_version.carvalho_2025_canephora_rata.vor',
            'source_version.ledezma_2025_geisha_rata.vor',
            'source_version.seninde_2020_sensory_review.vor',
            'source_version.zhang_2019_wet_processing.vor',
            'source_version.munchow_2020_roast_sensory.vor',
            'source_version.batali_2022_brew_temperature.vor',
            'source_version.bollen_2024_canephora_profiles.vor',
            'source_version.williams_2023_acidity_mouthfeel.vor',
            'source_version.wcr_sensory_lexicon_2_0.public_page',
            'source_version.sca_cva.web_2026-08-24',
            'source_version.iso_18794_2025.edition_2'
        )
          AND policy.production_export_allowed
    ) THEN
        RAISE EXCEPTION 'round2a external rights policy unexpectedly permits production export';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        WHERE concept.concept_key = 'sensory.pink_grapefruit'
          AND concept.lifecycle_status_code = 'candidate'
    ) OR EXISTS (
        SELECT 1
        FROM kb.concept_relation AS relation
        WHERE relation.relation_key IN (
            'relation.grapefruit.broader_than.pink_grapefruit',
            'relation.bergamot.sensory_neighbour.jasmine'
        )
          AND relation.lifecycle_status_code = 'active'
    ) THEN
        RAISE EXCEPTION 'round2a forward lifecycle corrections are incomplete';
    END IF;
END
$round2a_seed_contract$;

COMMIT;
