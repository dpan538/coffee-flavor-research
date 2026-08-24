\set ON_ERROR_STOP on

-- Round 3A deterministic context seed. Descriptions and taxonomic choices are
-- independently authored project interpretations. External sources support
-- scope and empirical relevance; protected definitions are not reproduced.

BEGIN;

INSERT INTO ref.context_value_status VALUES
    ('known', 'Known and normalized', 'A reported or measured value has a reviewed project-normalized representation.', TRUE, FALSE),
    ('reported_unresolved', 'Reported but unresolved', 'The source supplied a label, but no safe project-normalized mapping is asserted.', FALSE, TRUE),
    ('unknown', 'User does not know', 'The context was asked and the observer explicitly did not know.', FALSE, FALSE),
    ('not_reported', 'Not reported', 'The source did not report this context; no inference is permitted.', FALSE, FALSE),
    ('not_applicable', 'Not applicable', 'The contextual variable does not apply to this observation.', FALSE, FALSE);

INSERT INTO ref.context_assertion_role VALUES
    ('project_authored', 'Project authored', 'An independently authored Round 3A modeling or taxonomy assertion.'),
    ('empirical_observation', 'Empirical observation', 'A source or dataset directly reports the contextual variable or comparison.'),
    ('source_reported', 'Source reported', 'A source reports the term or grouping without the project adopting it as universal truth.'),
    ('interpretive', 'Interpretive', 'A conservative project interpretation of identified evidence.'),
    ('corroboration', 'Corroboration', 'An independent source supports an already defined project context boundary.'),
    ('lexical_mapping', 'Lexical mapping', 'A reviewed mapping between a context expression and a project or source-scheme identity.');

INSERT INTO ref.preparation_concept_type VALUES
    ('family', 'Preparation family', 'A broad low-burden C0 organizational choice; it is not a universal sensory axis.'),
    ('method', 'Preparation method', 'An extraction method or method-level preparation identity.'),
    ('beverage_style', 'Beverage style', 'A served beverage identity that may add water, milk, gas, or another post-extraction operation.');

INSERT INTO ref.context_relation_type VALUES
    ('broader_than', 'Broader than', 'The subject is a broader project preparation grouping than the object.', TRUE, FALSE),
    ('related_to', 'Related to', 'A symmetric, non-equivalence contextual association requiring explicit provenance.', FALSE, TRUE);

INSERT INTO ref.context_mapping_certainty VALUES
    ('exact_project_label', 'Exact project label', 'The expression is the independently authored preferred project label for the target identity.', FALSE),
    ('approximate', 'Approximate', 'The mapping is useful but source boundaries are not guaranteed to match the target boundaries.', FALSE),
    ('ambiguous_candidate', 'Ambiguous candidate', 'The expression has multiple defensible senses and remains explicitly polysemous.', TRUE);

INSERT INTO ref.roast_scheme_kind VALUES
    ('project_user_scale', 'Project user scale', 'A low-burden project interaction scale with ordinal labels but no invented color cutoffs.', TRUE),
    ('source_ordinal', 'Source ordinal scheme', 'A source- or convention-specific ordered category set retained independently.', TRUE),
    ('industry_terminology', 'Industry terminology', 'An unordered terminology set whose labels must not be treated as a universal darkness scale.', FALSE);

INSERT INTO ref.roast_measurement_basis VALUES
    ('whole_bean', 'Whole bean', 'Measurement is made on roasted whole beans.'),
    ('ground', 'Ground coffee', 'Measurement is made after grinding under the declared method.'),
    ('brewed_beverage', 'Brewed beverage', 'Measurement is made on the brewed liquid rather than the roasted material.');

INSERT INTO ref.addition_presence VALUES
    ('present', 'Present', 'One or more explicit beverage-addition rows are expected.', TRUE),
    ('absent', 'Absent', 'The source explicitly states or the protocol establishes that no addition was present.', FALSE),
    ('unknown', 'Unknown', 'The observer does not know whether an addition was present.', FALSE),
    ('not_reported', 'Not reported', 'The source does not report beverage additions.', FALSE),
    ('not_applicable', 'Not applicable', 'Addition context does not apply to this record.', FALSE);

INSERT INTO evidence.license_policy (
    license_policy_key, access_class_code, rights_status_code,
    redistributable, derivative_work_allowed, commercial_use_allowed,
    machine_use_allowed, production_export_allowed, checked_on, notes
)
VALUES
    (
        'license.project_context.cc_by_4_0.v1', 'public', 'verified',
        TRUE, TRUE, TRUE, TRUE, TRUE, DATE '2026-08-25',
        'Independently authored Round 3A prose and context taxonomy are licensed CC BY 4.0 under the repository licence-scope policy.'
    ),
    (
        'license.context_publication_metadata_only.unknown.v1', 'metadata_only', 'unknown',
        FALSE, FALSE, FALSE, FALSE, FALSE, DATE '2026-08-25',
        'Bibliographic metadata and independent project interpretation only. No protected article, standard, table, or definition is exported.'
    ),
    (
        'license.dryad_cc0_context_data.v1', 'public', 'verified',
        TRUE, TRUE, TRUE, TRUE, TRUE, DATE '2026-08-25',
        'Dryad states that published datasets are released under CC0; attribution and the dataset DOI remain recorded. Source-article rights are separate.'
    );

INSERT INTO evidence.source (
    source_key, title, creator, publisher, citation, doi, source_url,
    external_metadata
)
VALUES
    (
        'source.project.coffee_sensory_kb_v0_round3a_context',
        'Coffee Sensory KB V0 Round 3A Context Taxonomy and Research Synthesis',
        'Coffee Flavor Atlas project', 'Coffee Flavor Atlas project',
        'Coffee Flavor Atlas project. Coffee Sensory KB V0 Round 3A Context Taxonomy and Research Synthesis. 2026.',
        NULL, NULL,
        '{"authorship":"project","external_definitions_copied":false,"numeric_roast_cutoffs_invented":false}'::JSONB
    ),
    (
        'source.gloess_2013_nine_extraction_methods',
        'Comparison of nine common coffee extraction methods: instrumental and sensory analysis',
        'Gloess et al.', 'European Food Research and Technology',
        'Gloess AN et al. Comparison of nine common coffee extraction methods: instrumental and sensory analysis. Eur Food Res Technol. 2013;236:607-627.',
        '10.1007/s00217-013-1917-x', 'https://doi.org/10.1007/s00217-013-1917-x', '{}'::JSONB
    ),
    (
        'source.sanchez_chambers_2015_preparation',
        'How Does Product Preparation Affect Sensory Properties? An Example with Coffee',
        'Sanchez and Chambers', 'Journal of Sensory Studies',
        'Sanchez K, Chambers E. How Does Product Preparation Affect Sensory Properties? An Example with Coffee. J Sens Stud. 2015.',
        '10.1111/joss.12184', 'https://doi.org/10.1111/joss.12184', '{}'::JSONB
    ),
    (
        'source.batali_2020_brew_temperature',
        'Brew temperature, at fixed brew strength and extraction, has little impact on the sensory profile of drip brew coffee',
        'Batali et al.', 'Scientific Reports',
        'Batali ME et al. Brew temperature, at fixed brew strength and extraction, has little impact on the sensory profile of drip brew coffee. Sci Rep. 2020;10:16450.',
        '10.1038/s41598-020-73341-4', 'https://doi.org/10.1038/s41598-020-73341-4', '{}'::JSONB
    ),
    (
        'source.guinard_2023_brewing_control_chart',
        'The new Coffee Brewing Control Chart',
        'Cotter et al.', 'Journal of Food Science',
        'Cotter AR et al. Consumer-driven derivation of a new Coffee Brewing Control Chart. J Food Sci. 2023.',
        '10.1111/1750-3841.16531', 'https://doi.org/10.1111/1750-3841.16531', '{}'::JSONB
    ),
    (
        'source.frost_2019_basket_geometry',
        'Effect of Basket Geometry on the Sensory Quality and Consumer Acceptance of Drip Brewed Coffee',
        'Frost et al.', 'Journal of Food Science',
        'Frost SC et al. Effect of Basket Geometry on the Sensory Quality and Consumer Acceptance of Drip Brewed Coffee. J Food Sci. 2019.',
        '10.1111/1750-3841.14696', 'https://doi.org/10.1111/1750-3841.14696', '{}'::JSONB
    ),
    (
        'source.cordoba_2021_cold_hot_brew',
        'Specialty and regular coffee bean quality for cold and hot brewing: Evaluation of sensory and physicochemical characteristics',
        'Cordoba et al.', 'LWT',
        'Cordoba N et al. Specialty and regular coffee bean quality for cold and hot brewing: Evaluation of sensory and physicochemical characteristics. LWT. 2021.',
        '10.1016/j.lwt.2021.111363', 'https://doi.org/10.1016/j.lwt.2021.111363', '{}'::JSONB
    ),
    (
        'source.liang_2024_immersion_context',
        'Sensory analysis of full immersion coffee brewed at hot, room, and cold temperatures over time',
        'Liang et al.', 'Scientific Reports',
        'Liang J et al. Sensory analysis of full immersion coffee brewed at hot, room, and cold temperatures over time. Sci Rep. 2024;14.',
        '10.1038/s41598-024-69867-6', 'https://doi.org/10.1038/s41598-024-69867-6', '{}'::JSONB
    ),
    (
        'source.cordova_2025_roast_milk',
        'Effects of Roasting Level and Milk Addition on In Vivo Aroma Release and Perception of Coffee',
        'Cordova et al.', 'Journal of Agricultural and Food Chemistry',
        'Cordova N et al. Effects of Roasting Level and Milk Addition on In Vivo Aroma Release and Perception of Coffee. J Agric Food Chem. 2025.',
        '10.1021/acs.jafc.4c12852', 'https://doi.org/10.1021/acs.jafc.4c12852', '{}'::JSONB
    ),
    (
        'source.itobe_2015_milk_aroma',
        'Influence of Milk on Aroma Release and Aroma Perception during Consumption of Coffee Beverages',
        'Itobe, Nishimura, and Kumazawa', 'Food Science and Technology Research',
        'Itobe T, Nishimura O, Kumazawa K. Influence of Milk on Aroma Release and Aroma Perception during Consumption of Coffee Beverages. Food Sci Technol Res. 2015;21:607-614.',
        '10.3136/fstr.21.607', 'https://doi.org/10.3136/fstr.21.607', '{}'::JSONB
    ),
    (
        'source.yeager_2022_roast_brew_color',
        'Roast level and brew temperature significantly affect the color of brewed coffee',
        'Yeager et al.', 'Journal of Food Science',
        'Yeager SE et al. Roast level and brew temperature significantly affect the color of brewed coffee. J Food Sci. 2022.',
        '10.1111/1750-3841.16089', 'https://doi.org/10.1111/1750-3841.16089', '{}'::JSONB
    ),
    (
        'source.frost_2020_strength_yield_roast',
        'Effects of brew strength, brew yield, and roast on the sensory quality of drip brewed coffee',
        'Frost, Ristenpart, and Guinard', 'Journal of Food Science',
        'Frost SC, Ristenpart WD, Guinard JX. Effects of brew strength, brew yield, and roast on the sensory quality of drip brewed coffee. J Food Sci. 2020.',
        '10.1111/1750-3841.15326', 'https://doi.org/10.1111/1750-3841.15326', '{}'::JSONB
    ),
    (
        'source.sca_roast_color_standards_2026',
        'SCA Coffee Product Standards and Roast Color Research',
        'Specialty Coffee Association', 'Specialty Coffee Association',
        'Specialty Coffee Association. Coffee Product Standards and roast-color research pages. Retrieved 2026-08-25.',
        NULL, 'https://sca.coffee/research/coffee-standards/',
        '{"member_material_not_copied":true,"standard_boundaries_not_reproduced":true}'::JSONB
    ),
    (
        'source.dryad_liang_2024_context_data',
        'Data from: Sensory analysis of full immersion coffee brewed at hot, room, and cold temperatures over time',
        'Liang et al.', 'Dryad',
        'Liang J et al. Data from: Sensory analysis of full immersion coffee brewed at hot, room, and cold temperatures over time. Dryad.',
        '10.5061/dryad.v15dv423h', 'https://doi.org/10.5061/dryad.v15dv423h', '{"license":"CC0"}'::JSONB
    ),
    (
        'source.dryad_cotter_2020_black_coffee',
        'Data from: Consumer preferences for black coffee are spread over a wide range of brew strengths and extraction yields',
        'Cotter et al.', 'Dryad',
        'Cotter AR et al. Consumer preferences for black coffee dataset. Dryad.',
        '10.25338/B8993H', 'https://doi.org/10.25338/B8993H', '{"license":"CC0"}'::JSONB
    ),
    (
        'source.dryad_cotter_2023_acids_meta_analysis',
        'Data from: Acids in brewed coffees: Chemical composition and sensory threshold',
        'Cotter et al.', 'Dryad',
        'Cotter AR et al. Acids in brewed coffees meta-analysis dataset. Dryad.',
        '10.25338/B8C91C', 'https://doi.org/10.25338/B8C91C', '{"license":"CC0"}'::JSONB
    );

INSERT INTO evidence.source_version (
    source_version_key, source_id, license_policy_id, version_label,
    published_on, retrieved_on, version_locator, external_metadata
)
SELECT
    version.source_version_key,
    source.source_id,
    policy.license_policy_id,
    version.version_label,
    version.published_on,
    DATE '2026-08-25',
    version.version_locator,
    version.external_metadata
FROM (VALUES
    ('source_version.project.context_v0.2026-08-25', 'source.project.coffee_sensory_kb_v0_round3a_context', 'license.project_context.cc_by_4_0.v1', 'Round 3A 2026-08-25', DATE '2026-08-25', 'db/020_context_taxonomy_seed.sql', '{"authorship":"project"}'::JSONB),
    ('source_version.gloess_2013.vor', 'source.gloess_2013_nine_extraction_methods', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2013-03-01', 'https://doi.org/10.1007/s00217-013-1917-x', '{}'::JSONB),
    ('source_version.sanchez_chambers_2015.vor', 'source.sanchez_chambers_2015_preparation', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2015-01-01', 'https://doi.org/10.1111/joss.12184', '{}'::JSONB),
    ('source_version.batali_2020.vor', 'source.batali_2020_brew_temperature', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2020-10-05', 'https://doi.org/10.1038/s41598-020-73341-4', '{}'::JSONB),
    ('source_version.guinard_2023.vor', 'source.guinard_2023_brewing_control_chart', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2023-01-01', 'https://doi.org/10.1111/1750-3841.16531', '{}'::JSONB),
    ('source_version.frost_2019.vor', 'source.frost_2019_basket_geometry', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2019-01-01', 'https://doi.org/10.1111/1750-3841.14696', '{}'::JSONB),
    ('source_version.cordoba_2021.vor', 'source.cordoba_2021_cold_hot_brew', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2021-01-01', 'https://doi.org/10.1016/j.lwt.2021.111363', '{}'::JSONB),
    ('source_version.liang_2024.vor', 'source.liang_2024_immersion_context', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2024-08-08', 'https://doi.org/10.1038/s41598-024-69867-6', '{}'::JSONB),
    ('source_version.cordova_2025.vor', 'source.cordova_2025_roast_milk', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2025-01-01', 'https://doi.org/10.1021/acs.jafc.4c12852', '{}'::JSONB),
    ('source_version.itobe_2015.vor', 'source.itobe_2015_milk_aroma', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2015-09-10', 'https://doi.org/10.3136/fstr.21.607', '{}'::JSONB),
    ('source_version.yeager_2022.vor', 'source.yeager_2022_roast_brew_color', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2022-01-01', 'https://doi.org/10.1111/1750-3841.16089', '{}'::JSONB),
    ('source_version.frost_2020.vor', 'source.frost_2020_strength_yield_roast', 'license.context_publication_metadata_only.unknown.v1', 'Version of record metadata', DATE '2020-01-01', 'https://doi.org/10.1111/1750-3841.15326', '{}'::JSONB),
    ('source_version.sca_roast_color.2026-08-25', 'source.sca_roast_color_standards_2026', 'license.context_publication_metadata_only.unknown.v1', 'Web metadata retrieved 2026-08-25', NULL, 'https://sca.coffee/research/coffee-standards/', '{"protected_standard_content_copied":false}'::JSONB),
    ('source_version.dryad_liang_2024.v1', 'source.dryad_liang_2024_context_data', 'license.dryad_cc0_context_data.v1', 'Dryad dataset version retrieved 2026-08-25', NULL, 'https://doi.org/10.5061/dryad.v15dv423h', '{"license":"CC0"}'::JSONB),
    ('source_version.dryad_cotter_2020.v1', 'source.dryad_cotter_2020_black_coffee', 'license.dryad_cc0_context_data.v1', 'Dryad dataset version retrieved 2026-08-25', NULL, 'https://doi.org/10.25338/B8993H', '{"license":"CC0"}'::JSONB),
    ('source_version.dryad_cotter_2023.v1', 'source.dryad_cotter_2023_acids_meta_analysis', 'license.dryad_cc0_context_data.v1', 'Dryad dataset version retrieved 2026-08-25', NULL, 'https://doi.org/10.25338/B8C91C', '{"license":"CC0"}'::JSONB)
) AS version(
    source_version_key, source_key, license_policy_key, version_label,
    published_on, version_locator, external_metadata
)
JOIN evidence.source AS source ON source.source_key = version.source_key
JOIN evidence.license_policy AS policy
  ON policy.license_policy_key = version.license_policy_key;

INSERT INTO evidence.dataset (
    dataset_key, source_version_id, name, description, external_metadata
)
SELECT
    dataset.dataset_key,
    source_version.source_version_id,
    dataset.name,
    dataset.description,
    dataset.external_metadata
FROM (VALUES
    (
        'dataset.liang_2024_full_immersion_context',
        'source_version.dryad_liang_2024.v1',
        'Full-immersion temperature, time, and roast sensory dataset',
        'Rights-cleared experimental context data spanning two roast treatments, three brewing temperatures, and five extraction times. Candidate for later contextual model benchmarking; not imported in Round 3A.',
        '{"license":"CC0","roast_treatments":2,"brew_temperature_treatments":3,"brew_time_treatments":5,"production_export_allowed":true}'::JSONB
    ),
    (
        'dataset.cotter_2020_black_coffee_context',
        'source_version.dryad_cotter_2020.v1',
        'Black-coffee brew strength and extraction consumer dataset',
        'Rights-cleared black-coffee data covering 27 controlled brew conditions and 118 consumers. Preparation is fixed rather than diverse; useful for strength/extraction calibration, not method taxonomy truth.',
        '{"license":"CC0","consumers":118,"brew_conditions":27,"reported_tastings":3186,"preparation_scope":"controlled drip black coffee","production_export_allowed":true}'::JSONB
    ),
    (
        'dataset.cotter_2023_acids_meta_analysis',
        'source_version.dryad_cotter_2023.v1',
        'Brewed-coffee acids meta-analysis dataset',
        'Rights-cleared chemistry meta-analysis with extraction and source roast labels. Useful for testing source-scheme preservation; it is not a consumer sensory ranking dataset.',
        '{"license":"CC0","reported_datapoints":7509,"reported_source_papers":121,"source_roast_labels_subjective":true,"production_export_allowed":true}'::JSONB
    )
) AS dataset(dataset_key, source_version_key, name, description, external_metadata)
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = dataset.source_version_key;

INSERT INTO context.preparation_concept (
    preparation_concept_key, preparation_concept_type_code,
    lifecycle_status_code, preferred_label, description,
    c0_top_level, c0_second_level
)
VALUES
    ('preparation.family.filter_percolation', 'family', 'active', 'Filter / percolation', 'Water passes through a coffee bed and filter; manual and batch forms remain distinguishable below this low-burden family.', TRUE, FALSE),
    ('preparation.family.immersion', 'family', 'active', 'Immersion', 'Coffee and water remain in contact before separation; time, agitation, filtration, and recipe remain protocol metadata.', TRUE, FALSE),
    ('preparation.family.hybrid', 'family', 'active', 'Hybrid / manual pressure', 'Methods combining more than one extraction or separation mechanism; membership is explicitly polyhierarchical where needed.', TRUE, FALSE),
    ('preparation.family.espresso_pressure', 'family', 'active', 'Espresso / short pressure', 'Concentrated pressure-brewed coffee and its short-volume styles; this family does not include moka by equivalence.', TRUE, FALSE),
    ('preparation.family.diluted_espresso', 'family', 'active', 'Espresso + water', 'A served beverage made by combining espresso-family coffee with additional water.', TRUE, FALSE),
    ('preparation.family.stovetop_boiled', 'family', 'active', 'Stovetop / boiled', 'Stovetop pressure-percolation and unfiltered boiled preparations grouped for low-burden interaction while retained as distinct methods.', TRUE, FALSE),
    ('preparation.family.cold_extraction', 'family', 'active', 'Cold extraction', 'Coffee extracted principally with cool or ambient water over an extended process; chilled hot-brewed coffee is not automatically included.', TRUE, FALSE),
    ('preparation.family.espresso_milk', 'family', 'active', 'Espresso + milk', 'Espresso-family beverages served with dairy or plant-based milk; recipe and milk identity remain contextual variables.', TRUE, FALSE),
    ('preparation.method.manual_filter', 'method', 'active', 'Manual filter', 'A broad manual percolation method retained when the exact brewer is unknown or unnecessary for the V1 interaction.', FALSE, FALSE),
    ('preparation.method.batch_filter', 'method', 'active', 'Batch filter', 'Machine-assisted filter coffee prepared as a batch rather than as an individual manual pour.', FALSE, FALSE),
    ('preparation.method.pour_over_cone', 'method', 'active', 'Pour-over cone', 'Manual filter brewing using a conical or comparable open dripper; exact geometry can remain optional metadata.', FALSE, FALSE),
    ('preparation.method.chemex', 'method', 'active', 'Chemex-style filter', 'Manual filter preparation using the Chemex brewer family, retained as a subtype rather than a universal sensory profile.', FALSE, FALSE),
    ('preparation.method.french_press', 'method', 'active', 'French press', 'Full-immersion preparation separated with a plunger screen.', FALSE, FALSE),
    ('preparation.method.generic_immersion', 'method', 'active', 'Other immersion', 'An immersion preparation whose more specific device is unavailable or outside the small V1 taxonomy.', FALSE, FALSE),
    ('preparation.method.aeropress', 'method', 'active', 'AeroPress', 'A recipe-sensitive hybrid method represented under both immersion and manual-pressure organization; no single sensory profile is asserted.', FALSE, FALSE),
    ('preparation.method.siphon', 'method', 'active', 'Siphon / vacuum', 'A vacuum-assisted preparation with immersion and filtration phases, retained under the hybrid family.', FALSE, FALSE),
    ('preparation.method.espresso_standard', 'method', 'active', 'Espresso', 'A standard espresso-style concentrated pressure extraction; machine settings and recipe remain separate metadata.', FALSE, TRUE),
    ('preparation.beverage.ristretto', 'beverage_style', 'active', 'Ristretto', 'A short espresso-family beverage identity; no universal volume or extraction cutoff is asserted.', FALSE, TRUE),
    ('preparation.beverage.lungo', 'beverage_style', 'active', 'Lungo', 'A longer espresso-family beverage identity; no universal volume or extraction cutoff is asserted.', FALSE, TRUE),
    ('preparation.beverage.americano', 'beverage_style', 'active', 'Americano', 'A diluted-espresso beverage label retained independently from long black because naming and preparation conventions vary.', FALSE, TRUE),
    ('preparation.beverage.long_black', 'beverage_style', 'active', 'Long black', 'A diluted-espresso beverage label related to, but not merged with, Americano.', FALSE, TRUE),
    ('preparation.method.moka', 'method', 'active', 'Moka', 'Stovetop pressure-driven percolation retained independently from espresso.', FALSE, FALSE),
    ('preparation.method.cezve', 'method', 'active', 'Cezve / Turkish-style', 'An unfiltered boiled preparation retained independently from moka.', FALSE, FALSE),
    ('preparation.method.cold_brew_immersion', 'method', 'active', 'Cold-brew immersion', 'Extended cool or ambient immersion extraction; time, temperature, concentration, and dilution remain metadata.', FALSE, TRUE),
    ('preparation.method.cold_drip', 'method', 'active', 'Cold drip', 'Cold percolation in which water passes gradually through the coffee bed.', FALSE, TRUE),
    ('preparation.beverage.nitro_cold_brew', 'beverage_style', 'active', 'Nitro cold brew', 'Cold-brew coffee served with nitrogenation; gas service is a beverage operation rather than a new extraction mechanism.', FALSE, TRUE),
    ('preparation.beverage.flat_white', 'beverage_style', 'active', 'Flat white', 'An espresso-and-textured-milk identity retained separately because recipe, milk amount, and foam conventions can differ.', FALSE, TRUE),
    ('preparation.beverage.latte', 'beverage_style', 'active', 'Latte', 'An espresso-and-milk identity retained separately from flat white; no universal recipe ratio is asserted.', FALSE, TRUE),
    ('preparation.beverage.cappuccino', 'beverage_style', 'active', 'Cappuccino', 'An espresso-and-textured-milk identity whose foam and ratio remain recipe metadata.', FALSE, TRUE),
    ('preparation.beverage.cortado', 'beverage_style', 'active', 'Cortado', 'An espresso-and-milk identity retained as a distinct consumer-visible context.', FALSE, TRUE),
    ('preparation.beverage.piccolo', 'beverage_style', 'active', 'Piccolo', 'A small espresso-and-milk identity retained as a distinct consumer-visible context.', FALSE, TRUE),
    ('preparation.beverage.macchiato', 'beverage_style', 'active', 'Macchiato', 'An espresso-and-milk identity whose regional recipe variation is retained as a limitation.', FALSE, TRUE);

INSERT INTO context.preparation_concept_support (
    preparation_concept_support_key, preparation_concept_id,
    source_version_id, context_assertion_role_code, evidence_locator, notes
)
SELECT
    'support.' || replace(concept.preparation_concept_key, 'preparation.', 'preparation.'),
    concept.preparation_concept_id,
    source_version.source_version_id,
    'project_authored',
    'docs/research/coffee-sensory-kb-v0-round3a/02_PREPARATION_TAXONOMY.md',
    'Independent Round 3A definition; no external definition was copied.'
FROM context.preparation_concept AS concept
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = 'source_version.project.context_v0.2026-08-25';

INSERT INTO context.preparation_concept_support (
    preparation_concept_support_key, preparation_concept_id,
    source_version_id, context_assertion_role_code, evidence_locator, notes
)
SELECT
    support.support_key,
    concept.preparation_concept_id,
    source_version.source_version_id,
    support.assertion_role,
    support.locator,
    support.notes
FROM (VALUES
    ('support.preparation.filter.gloess', 'preparation.family.filter_percolation', 'source_version.gloess_2013.vor', 'empirical_observation', 'Methods and sensory comparison', 'Supports preparation method as an empirical condition, not a fixed flavor profile.'),
    ('support.preparation.immersion.gloess', 'preparation.family.immersion', 'source_version.gloess_2013.vor', 'empirical_observation', 'Methods and sensory comparison', 'Supports method separation; protocol details remain necessary.'),
    ('support.preparation.espresso.gloess', 'preparation.family.espresso_pressure', 'source_version.gloess_2013.vor', 'empirical_observation', 'Methods and sensory comparison', 'Supports pressure-preparation distinction.'),
    ('support.preparation.moka.gloess', 'preparation.method.moka', 'source_version.gloess_2013.vor', 'empirical_observation', 'Compared extraction methods', 'Moka remains independent from espresso in the project taxonomy.'),
    ('support.preparation.geometry.frost', 'preparation.method.manual_filter', 'source_version.frost_2019.vor', 'empirical_observation', 'Basket geometry experiment', 'Supports optional brewer/geometry metadata without requiring it in the first C0 choice.'),
    ('support.preparation.cold.cordoba', 'preparation.family.cold_extraction', 'source_version.cordoba_2021.vor', 'empirical_observation', 'Cold-versus-hot brewing comparison', 'Supports preserving cold extraction separately from hot preparation.'),
    ('support.preparation.cold.liang', 'preparation.method.cold_brew_immersion', 'source_version.liang_2024.vor', 'empirical_observation', 'Full-immersion temperature and time experiment', 'Supports joint time/temperature/roast context rather than a method label alone.'),
    ('support.preparation.milk.cordova', 'preparation.family.espresso_milk', 'source_version.cordova_2025.vor', 'empirical_observation', 'Milk and roast interaction study', 'Supports a distinct milk-coffee context mode.'),
    ('support.preparation.milk.itobe', 'preparation.family.espresso_milk', 'source_version.itobe_2015.vor', 'corroboration', 'Black-coffee versus milk-coffee aroma comparison', 'Corroborates aroma/perception changes with milk addition.')
) AS support(support_key, concept_key, source_version_key, assertion_role, locator, notes)
JOIN context.preparation_concept AS concept
  ON concept.preparation_concept_key = support.concept_key
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = support.source_version_key;

INSERT INTO context.preparation_relation (
    preparation_relation_key, subject_preparation_concept_id,
    context_relation_type_code, object_preparation_concept_id,
    source_version_id, context_assertion_role_code, evidence_locator,
    lifecycle_status_code
)
SELECT
    relation.relation_key,
    subject.preparation_concept_id,
    relation.relation_type,
    object.preparation_concept_id,
    source_version.source_version_id,
    relation.assertion_role,
    'docs/research/coffee-sensory-kb-v0-round3a/02_PREPARATION_TAXONOMY.md',
    'active'
FROM (VALUES
    ('relation.filter.manual_filter', 'preparation.family.filter_percolation', 'broader_than', 'preparation.method.manual_filter', 'project_authored'),
    ('relation.filter.batch_filter', 'preparation.family.filter_percolation', 'broader_than', 'preparation.method.batch_filter', 'project_authored'),
    ('relation.manual_filter.pour_over', 'preparation.method.manual_filter', 'broader_than', 'preparation.method.pour_over_cone', 'project_authored'),
    ('relation.manual_filter.chemex', 'preparation.method.manual_filter', 'broader_than', 'preparation.method.chemex', 'project_authored'),
    ('relation.immersion.french_press', 'preparation.family.immersion', 'broader_than', 'preparation.method.french_press', 'project_authored'),
    ('relation.immersion.generic', 'preparation.family.immersion', 'broader_than', 'preparation.method.generic_immersion', 'project_authored'),
    ('relation.immersion.aeropress', 'preparation.family.immersion', 'broader_than', 'preparation.method.aeropress', 'interpretive'),
    ('relation.hybrid.aeropress', 'preparation.family.hybrid', 'broader_than', 'preparation.method.aeropress', 'interpretive'),
    ('relation.hybrid.siphon', 'preparation.family.hybrid', 'broader_than', 'preparation.method.siphon', 'interpretive'),
    ('relation.espresso.standard', 'preparation.family.espresso_pressure', 'broader_than', 'preparation.method.espresso_standard', 'project_authored'),
    ('relation.espresso.ristretto', 'preparation.family.espresso_pressure', 'broader_than', 'preparation.beverage.ristretto', 'project_authored'),
    ('relation.espresso.lungo', 'preparation.family.espresso_pressure', 'broader_than', 'preparation.beverage.lungo', 'project_authored'),
    ('relation.diluted.americano', 'preparation.family.diluted_espresso', 'broader_than', 'preparation.beverage.americano', 'project_authored'),
    ('relation.diluted.long_black', 'preparation.family.diluted_espresso', 'broader_than', 'preparation.beverage.long_black', 'project_authored'),
    ('relation.americano.long_black', 'preparation.beverage.americano', 'related_to', 'preparation.beverage.long_black', 'interpretive'),
    ('relation.stovetop.moka', 'preparation.family.stovetop_boiled', 'broader_than', 'preparation.method.moka', 'project_authored'),
    ('relation.stovetop.cezve', 'preparation.family.stovetop_boiled', 'broader_than', 'preparation.method.cezve', 'project_authored'),
    ('relation.cold.immersion', 'preparation.family.cold_extraction', 'broader_than', 'preparation.method.cold_brew_immersion', 'project_authored'),
    ('relation.cold.drip', 'preparation.family.cold_extraction', 'broader_than', 'preparation.method.cold_drip', 'project_authored'),
    ('relation.cold.nitro', 'preparation.method.cold_brew_immersion', 'broader_than', 'preparation.beverage.nitro_cold_brew', 'project_authored'),
    ('relation.milk.flat_white', 'preparation.family.espresso_milk', 'broader_than', 'preparation.beverage.flat_white', 'project_authored'),
    ('relation.milk.latte', 'preparation.family.espresso_milk', 'broader_than', 'preparation.beverage.latte', 'project_authored'),
    ('relation.milk.cappuccino', 'preparation.family.espresso_milk', 'broader_than', 'preparation.beverage.cappuccino', 'project_authored'),
    ('relation.milk.cortado', 'preparation.family.espresso_milk', 'broader_than', 'preparation.beverage.cortado', 'project_authored'),
    ('relation.milk.piccolo', 'preparation.family.espresso_milk', 'broader_than', 'preparation.beverage.piccolo', 'project_authored'),
    ('relation.milk.macchiato', 'preparation.family.espresso_milk', 'broader_than', 'preparation.beverage.macchiato', 'project_authored')
) AS relation(relation_key, subject_key, relation_type, object_key, assertion_role)
JOIN context.preparation_concept AS subject
  ON subject.preparation_concept_key = relation.subject_key
JOIN context.preparation_concept AS object
  ON object.preparation_concept_key = relation.object_key
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = 'source_version.project.context_v0.2026-08-25';

INSERT INTO context.preparation_expression (
    preparation_expression_key, language_tag_code, expression_text,
    normalized_text, lifecycle_status_code
)
SELECT
    'preparation_expression.' || replace(replace(concept.preparation_concept_key, 'preparation.', ''), '.', '_'),
    'en', concept.preferred_label, lower(concept.preferred_label), 'active'
FROM context.preparation_concept AS concept;

INSERT INTO context.preparation_expression (
    preparation_expression_key, language_tag_code, expression_text,
    normalized_text, lifecycle_status_code
)
VALUES
    ('preparation_expression.unresolved.drip_coffee', 'en', 'drip coffee', 'drip coffee', 'candidate'),
    ('preparation_expression.unresolved.iced_coffee', 'en', 'iced coffee', 'iced coffee', 'candidate');

INSERT INTO context.preparation_expression_mapping (
    preparation_expression_mapping_key, preparation_expression_id,
    preparation_concept_id, context_mapping_certainty_code,
    source_version_id, context_assertion_role_code, evidence_locator,
    lifecycle_status_code
)
SELECT
    'preparation_mapping.' || replace(replace(concept.preparation_concept_key, 'preparation.', ''), '.', '_'),
    expression.preparation_expression_id,
    concept.preparation_concept_id,
    'exact_project_label',
    source_version.source_version_id,
    'lexical_mapping',
    'db/020_context_taxonomy_seed.sql',
    'active'
FROM context.preparation_concept AS concept
JOIN context.preparation_expression AS expression
  ON expression.preparation_expression_key =
     'preparation_expression.' || replace(replace(concept.preparation_concept_key, 'preparation.', ''), '.', '_')
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = 'source_version.project.context_v0.2026-08-25';

INSERT INTO context.roast_scheme (
    roast_scheme_key, roast_scheme_kind_code, lifecycle_status_code,
    source_version_id, name, description, is_project_normalized_target
)
SELECT
    scheme.scheme_key, scheme.scheme_kind, scheme.lifecycle_status,
    source_version.source_version_id, scheme.name, scheme.description,
    scheme.is_target
FROM (VALUES
    ('roast.scheme.project_v0_five_level', 'project_user_scale', 'active', 'Project V0 five-level roast context', 'A coarse user-facing ordinal context with five independently authored labels and no numerical color cutoffs.', TRUE),
    ('roast.scheme.common_three_level', 'source_ordinal', 'active', 'Common three-level source labels', 'A source-label projection for light, medium, and dark. Boundaries vary, so mappings to the project scale remain approximate.', FALSE),
    ('roast.scheme.traditional_trade_labels', 'industry_terminology', 'candidate', 'Traditional and regional roast terminology', 'Unordered source vocabulary retained without assuming that City, Vienna, French, Italian, or Nordic labels have universal color boundaries.', FALSE),
    ('roast.scheme.brew_intent_labels', 'industry_terminology', 'candidate', 'Brew-intent roast terminology', 'Filter roast, espresso roast, and omniroast are retained as intended-use or style labels rather than darkness categories.', FALSE)
) AS scheme(scheme_key, scheme_kind, lifecycle_status, name, description, is_target)
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = 'source_version.project.context_v0.2026-08-25';

INSERT INTO context.roast_category (
    roast_category_key, roast_scheme_id, source_category_code,
    preferred_label, ordinal_position, lifecycle_status_code, description
)
SELECT
    category.category_key,
    scheme.roast_scheme_id,
    category.category_code,
    category.label,
    category.ordinal_position,
    category.lifecycle_status,
    category.description
FROM (VALUES
    ('roast.project.very_light', 'roast.scheme.project_v0_five_level', 'very_light', 'Very light', 1::SMALLINT, 'active', 'Lightest project interaction bin; a relative label with no universal color cutoff.'),
    ('roast.project.light', 'roast.scheme.project_v0_five_level', 'light', 'Light', 2::SMALLINT, 'active', 'Light project interaction bin; a relative label with no universal color cutoff.'),
    ('roast.project.medium', 'roast.scheme.project_v0_five_level', 'medium', 'Medium', 3::SMALLINT, 'active', 'Middle project interaction bin; a relative label with no universal color cutoff.'),
    ('roast.project.dark', 'roast.scheme.project_v0_five_level', 'dark', 'Dark', 4::SMALLINT, 'active', 'Dark project interaction bin; a relative label with no universal color cutoff.'),
    ('roast.project.very_dark', 'roast.scheme.project_v0_five_level', 'very_dark', 'Very dark', 5::SMALLINT, 'active', 'Darkest project interaction bin; a relative label with no universal color cutoff.'),
    ('roast.common.light', 'roast.scheme.common_three_level', 'light', 'Light roast', 1::SMALLINT, 'active', 'Source-style light label retained independently because category boundaries vary.'),
    ('roast.common.medium', 'roast.scheme.common_three_level', 'medium', 'Medium roast', 2::SMALLINT, 'active', 'Source-style medium label retained independently because category boundaries vary.'),
    ('roast.common.dark', 'roast.scheme.common_three_level', 'dark', 'Dark roast', 3::SMALLINT, 'active', 'Source-style dark label retained independently because category boundaries vary.'),
    ('roast.trade.city', 'roast.scheme.traditional_trade_labels', 'city', 'City roast', NULL::SMALLINT, 'candidate', 'Traditional trade label retained without an asserted universal position.'),
    ('roast.trade.full_city', 'roast.scheme.traditional_trade_labels', 'full_city', 'Full City roast', NULL::SMALLINT, 'candidate', 'Traditional trade label retained without an asserted universal position.'),
    ('roast.trade.vienna', 'roast.scheme.traditional_trade_labels', 'vienna', 'Vienna roast', NULL::SMALLINT, 'candidate', 'Traditional trade label retained without an asserted universal position.'),
    ('roast.trade.french', 'roast.scheme.traditional_trade_labels', 'french', 'French roast', NULL::SMALLINT, 'candidate', 'Traditional trade label retained without an asserted universal position.'),
    ('roast.trade.italian', 'roast.scheme.traditional_trade_labels', 'italian', 'Italian roast', NULL::SMALLINT, 'candidate', 'Traditional trade label retained without an asserted universal position.'),
    ('roast.trade.nordic', 'roast.scheme.traditional_trade_labels', 'nordic', 'Nordic roast', NULL::SMALLINT, 'candidate', 'Regional or stylistic label retained without treating it as a measured degree.'),
    ('roast.intent.filter', 'roast.scheme.brew_intent_labels', 'filter_roast', 'Filter roast', NULL::SMALLINT, 'candidate', 'Intended-use label; it does not by itself identify roast color.'),
    ('roast.intent.espresso', 'roast.scheme.brew_intent_labels', 'espresso_roast', 'Espresso roast', NULL::SMALLINT, 'candidate', 'Intended-use label; it does not by itself identify roast color.'),
    ('roast.intent.omni', 'roast.scheme.brew_intent_labels', 'omniroast', 'Omniroast', NULL::SMALLINT, 'candidate', 'Intended-use label; it does not by itself identify roast color.')
) AS category(category_key, scheme_key, category_code, label, ordinal_position, lifecycle_status, description)
JOIN context.roast_scheme AS scheme ON scheme.roast_scheme_key = category.scheme_key;

INSERT INTO context.roast_category_mapping (
    roast_category_mapping_key, source_roast_category_id,
    normalized_roast_category_id, context_mapping_certainty_code,
    source_version_id, context_assertion_role_code, evidence_locator,
    lifecycle_status_code
)
SELECT
    mapping.mapping_key,
    source_category.roast_category_id,
    target_category.roast_category_id,
    'approximate',
    source_version.source_version_id,
    'interpretive',
    'docs/research/coffee-sensory-kb-v0-round3a/06_ROAST_TAXONOMY.md',
    'active'
FROM (VALUES
    ('roast_mapping.common_light.project_light', 'roast.common.light', 'roast.project.light'),
    ('roast_mapping.common_medium.project_medium', 'roast.common.medium', 'roast.project.medium'),
    ('roast_mapping.common_dark.project_dark', 'roast.common.dark', 'roast.project.dark')
) AS mapping(mapping_key, source_key, target_key)
JOIN context.roast_category AS source_category
  ON source_category.roast_category_key = mapping.source_key
JOIN context.roast_category AS target_category
  ON target_category.roast_category_key = mapping.target_key
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = 'source_version.project.context_v0.2026-08-25';

INSERT INTO context.roast_expression (
    roast_expression_key, language_tag_code, expression_text,
    normalized_text, lifecycle_status_code
)
VALUES
    ('roast_expression.project.very_light', 'en', 'very light', 'very light', 'active'),
    ('roast_expression.project.light', 'en', 'light', 'light', 'active'),
    ('roast_expression.project.medium', 'en', 'medium', 'medium', 'active'),
    ('roast_expression.project.dark', 'en', 'dark', 'dark', 'active'),
    ('roast_expression.project.very_dark', 'en', 'very dark', 'very dark', 'active'),
    ('roast_expression.unresolved.extremely_light', 'en', 'extremely light', 'extremely light', 'candidate'),
    ('roast_expression.unresolved.medium_light', 'en', 'medium-light', 'medium-light', 'candidate'),
    ('roast_expression.unresolved.medium_dark', 'en', 'medium-dark', 'medium-dark', 'candidate'),
    ('roast_expression.unresolved.extremely_dark', 'en', 'extremely dark', 'extremely dark', 'candidate'),
    ('roast_expression.unresolved.city', 'en', 'City roast', 'city roast', 'candidate'),
    ('roast_expression.unresolved.full_city', 'en', 'Full City roast', 'full city roast', 'candidate'),
    ('roast_expression.unresolved.vienna', 'en', 'Vienna roast', 'vienna roast', 'candidate'),
    ('roast_expression.unresolved.french', 'en', 'French roast', 'french roast', 'candidate'),
    ('roast_expression.unresolved.italian', 'en', 'Italian roast', 'italian roast', 'candidate'),
    ('roast_expression.unresolved.nordic', 'en', 'Nordic roast', 'nordic roast', 'candidate'),
    ('roast_expression.unresolved.filter', 'en', 'filter roast', 'filter roast', 'candidate'),
    ('roast_expression.unresolved.espresso', 'en', 'espresso roast', 'espresso roast', 'candidate'),
    ('roast_expression.unresolved.omni', 'en', 'omniroast', 'omniroast', 'candidate');

INSERT INTO context.roast_expression_mapping (
    roast_expression_mapping_key, roast_expression_id, roast_category_id,
    context_mapping_certainty_code, source_version_id,
    context_assertion_role_code, evidence_locator, lifecycle_status_code
)
SELECT
    mapping.mapping_key,
    expression.roast_expression_id,
    category.roast_category_id,
    'exact_project_label',
    source_version.source_version_id,
    'lexical_mapping',
    'db/020_context_taxonomy_seed.sql',
    'active'
FROM (VALUES
    ('roast_expression_mapping.project.very_light', 'roast_expression.project.very_light', 'roast.project.very_light'),
    ('roast_expression_mapping.project.light', 'roast_expression.project.light', 'roast.project.light'),
    ('roast_expression_mapping.project.medium', 'roast_expression.project.medium', 'roast.project.medium'),
    ('roast_expression_mapping.project.dark', 'roast_expression.project.dark', 'roast.project.dark'),
    ('roast_expression_mapping.project.very_dark', 'roast_expression.project.very_dark', 'roast.project.very_dark')
) AS mapping(mapping_key, expression_key, category_key)
JOIN context.roast_expression AS expression
  ON expression.roast_expression_key = mapping.expression_key
JOIN context.roast_category AS category
  ON category.roast_category_key = mapping.category_key
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = 'source_version.project.context_v0.2026-08-25';

INSERT INTO context.roast_measurement_method (
    roast_measurement_method_key, source_version_id,
    roast_measurement_basis_code, name, unit, minimum_value,
    maximum_value, higher_value_is_lighter, description,
    lifecycle_status_code
)
SELECT
    method.method_key,
    source_version.source_version_id,
    method.basis,
    method.name,
    method.unit,
    method.minimum_value,
    method.maximum_value,
    TRUE,
    method.description,
    'active'
FROM (VALUES
    ('roast_measurement.agtron_gourmet.whole_bean', 'whole_bean', 'Agtron Gourmet whole-bean reading', 'Agtron Gourmet reading', 0::NUMERIC, 150::NUMERIC, 'Instrument reading recorded on whole beans. It is never converted to a sensory score or category without a versioned mapping.'),
    ('roast_measurement.agtron_gourmet.ground', 'ground', 'Agtron Gourmet ground-coffee reading', 'Agtron Gourmet reading', 0::NUMERIC, 150::NUMERIC, 'Instrument reading recorded after grinding. Whole-bean and ground values remain different measurement contexts.'),
    ('roast_measurement.cielab_lstar.whole_bean', 'whole_bean', 'CIELAB L* whole-bean value', 'CIELAB L*', 0::NUMERIC, 100::NUMERIC, 'Lightness component recorded on whole beans under a declared color-measurement protocol.'),
    ('roast_measurement.cielab_lstar.ground', 'ground', 'CIELAB L* ground-coffee value', 'CIELAB L*', 0::NUMERIC, 100::NUMERIC, 'Lightness component recorded on ground coffee under a declared color-measurement protocol.')
) AS method(method_key, basis, name, unit, minimum_value, maximum_value, description)
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = 'source_version.sca_roast_color.2026-08-25';

INSERT INTO context.beverage_addition_type (
    beverage_addition_type_key, parent_beverage_addition_type_id,
    preferred_label, description, is_strong_flavour_interference,
    lifecycle_status_code
)
VALUES
    ('addition.milk_or_alternative', NULL, 'Milk or milk alternative', 'Broad milk-context parent; exact product, proportion, temperature, and texture remain observation metadata.', FALSE, 'active'),
    ('addition.sweetener', NULL, 'Sweetener', 'Sugar or another sweetener, represented as a beverage-context ingredient rather than sensory evidence about the coffee.', TRUE, 'active'),
    ('addition.flavored_syrup', NULL, 'Flavored syrup', 'A flavored syrup with strong potential to obscure or introduce sensory references.', TRUE, 'active'),
    ('addition.chocolate', NULL, 'Chocolate / cocoa addition', 'Chocolate or cocoa added as an ingredient; it cannot support a canonical cocoa sensory assertion about the coffee.', TRUE, 'active'),
    ('addition.cream', NULL, 'Cream', 'Dairy or plant-based cream represented as beverage context.', FALSE, 'active'),
    ('addition.spice', NULL, 'Spice', 'An added spice or spice mixture with strong flavor interference.', TRUE, 'active'),
    ('addition.tonic', NULL, 'Tonic', 'Tonic water represented as a beverage ingredient, not a coffee sensory attribute.', TRUE, 'active'),
    ('addition.fruit_or_juice', NULL, 'Fruit or juice', 'Fruit or juice added to the beverage; ingredient flavor must not become evidence of bean sensory character.', TRUE, 'active'),
    ('addition.alcohol', NULL, 'Alcohol', 'Alcoholic ingredient represented as context and excluded from the default V1 coffee-reference mode.', TRUE, 'active'),
    ('addition.ice_cream', NULL, 'Ice cream', 'Ice cream represented as a strong composite addition outside the default V1 context.', TRUE, 'active'),
    ('addition.other', NULL, 'Other addition', 'Extensible fallback for an explicitly reported addition not yet represented.', TRUE, 'active');

INSERT INTO context.beverage_addition_type (
    beverage_addition_type_key, parent_beverage_addition_type_id,
    preferred_label, description, is_strong_flavour_interference,
    lifecycle_status_code
)
SELECT
    addition.addition_key,
    parent.beverage_addition_type_id,
    addition.label,
    addition.description,
    FALSE,
    'active'
FROM (VALUES
    ('addition.cow_milk', 'Cow milk', 'Dairy milk; fat, protein, quantity, and heating remain protocol metadata.'),
    ('addition.plant_milk', 'Plant-based milk', 'Plant-based milk parent retained for extensible subtype representation.')
) AS addition(addition_key, label, description)
JOIN context.beverage_addition_type AS parent
  ON parent.beverage_addition_type_key = 'addition.milk_or_alternative';

INSERT INTO context.beverage_addition_type (
    beverage_addition_type_key, parent_beverage_addition_type_id,
    preferred_label, description, is_strong_flavour_interference,
    lifecycle_status_code
)
SELECT
    addition.addition_key,
    parent.beverage_addition_type_id,
    addition.label,
    addition.description,
    FALSE,
    'candidate'
FROM (VALUES
    ('addition.oat_milk', 'Oat milk', 'Oat-based milk context; formulation differences remain unmodeled.'),
    ('addition.soy_milk', 'Soy milk', 'Soy-based milk context; formulation differences remain unmodeled.'),
    ('addition.almond_milk', 'Almond milk', 'Almond-based milk context; formulation differences remain unmodeled.'),
    ('addition.coconut_milk', 'Coconut milk', 'Coconut-based milk context; formulation differences remain unmodeled.'),
    ('addition.other_plant_milk', 'Other plant-based milk', 'Extensible plant-based milk fallback without inferring formulation.')
) AS addition(addition_key, label, description)
JOIN context.beverage_addition_type AS parent
  ON parent.beverage_addition_type_key = 'addition.plant_milk';

COMMIT;
