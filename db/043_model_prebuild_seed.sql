\set ON_ERROR_STOP on

BEGIN;

INSERT INTO evidence.source_family (
    source_family_key, family_name, family_type, canonical_origin_key,
    counts_as_independent, mirror_of_source_family_key,
    independence_basis, admitted, introduced_round
)
VALUES
    ('family.iswaldi-rataconsumers-2026', 'Iswaldi Indonesian RATA consumers', 'CONSUMER_STUDY', 'origin.doi.10.1590/1981-6723.1062025', TRUE, NULL, 'Independent Indonesian ordinary-consumer sensory study and article aggregate.', TRUE, '3H'),
    ('family.vezzulli-trainedpanel-2022', 'Vezzulli extraction-method trained panel', 'COFFEE_SENSORY', 'origin.doi.10.3390/foods11060807', TRUE, NULL, 'Independent Italian trained-panel sensory study; chemistry supplement is excluded.', TRUE, '3H'),
    ('family.bollen-robusta-qgraders-2024', 'Bollen Robusta Q-grader profiles', 'COFFEE_SENSORY', 'origin.doi.10.3389/fsufs.2024.1382976', TRUE, NULL, 'Independent DRC Robusta source with one versioned Figshare workbook.', TRUE, '3H'),
    ('family.gorman-milk-consumers-2021', 'Gorman milk-coffee consumers', 'CONSUMER_STUDY', 'origin.doi.10.3390/beverages7040080', TRUE, NULL, 'Independent Canadian consumer milk-coffee CATA and hedonic study.', TRUE, '3H'),
    ('family.nguyen-pbma-thai-2026', 'Nguyen Thai PBMA coffee panels', 'CONSUMER_STUDY', 'origin.doi.10.3390/foods15152583', TRUE, NULL, 'Independent Thai trained-panel and consumer PBMA-coffee study.', TRUE, '3H'),
    ('family.condelli-consumer-cata-2022', 'Condelli espresso consumer CATA', 'CONSUMER_STUDY', 'origin.doi.10.1111/1750-3841.16323', TRUE, NULL, 'Independent Italian consumer study used only for generic constructs and aggregate relations.', TRUE, '3H'),
    ('family.heo-coldbrew-consumers-2019', 'Heo cold-brew consumer CATA', 'CONSUMER_STUDY', 'origin.doi.10.3390/foods8080344', TRUE, NULL, 'Independent Korean ordinary-consumer study; only its reduced observed term set is retained.', TRUE, '3H'),
    ('family.coffee-cuality-experts-2026', 'Guinard expert quality-method study', 'OTHER_RESEARCH', 'origin.doi.10.3390/foods15040678', TRUE, NULL, 'Independent expert study; generic architecture is separate from trademarked forms and identity.', TRUE, '3H');

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
    ('scielo.iswaldi-2026', 'family.iswaldi-rataconsumers-2026', 'Chemical, antioxidant, and sensory profiles of Indonesian single-origin Arabica coffee with different roast levels and brewing methods', 'Ihsan Iswaldi et al.', 2026, 'https://doi.org/10.1590/1981-6723.1062025', 'SciELO / Brazilian Journal of Food Technology', 'Volume 29 e2025106 version of record, Epub 2026-03-23', DATE '2026-08-25', 'COFFEE_SENSORY_AGGREGATE', 'Indonesia', 'English article; source-local consumer protocol', '50 naive consumers', 'RATA 0-7 plus hedonic 1-7', 'V60 and cold brew', 'Source light, medium and dark categories', 'Black only', 'CC BY 4.0', TRUE, TRUE, TRUE, TRUE, 'CLEARED', 'REVIEWED', 'PUBLIC_AGGREGATE_ONLY', 'PUBLIC_AGGREGATE', '["file.iswaldi.table3-derived"]'::JSONB, 72, 14, 'Ordinary-user sensory outcome and context evidence', ARRAY['membership.acidity-character.citrus'], ARRAY['roast-spice-smoke'], 'Article Table 3; db/data/round3h/batch1/iswaldi_2026_table3_sensory_aggregates.tsv', 'Aggregate means only; one published SD value is retained verbatim as .182; no citrus term is inferred from acidity.', 'Article, PDF and derived TSV are one origin.', TRUE),
    ('pmc.vezzulli-2022', 'family.vezzulli-trainedpanel-2022', 'Metabolomics Combined with Sensory Analysis Reveals the Impact of Different Extraction Methods on Coffee Beverages', 'Fosca Vezzulli et al.', 2022, 'https://doi.org/10.3390/foods11060807', 'Europe PMC / Foods', 'PMC8953325 full-text XML released 2022-03-26', DATE '2026-08-25', 'COFFEE_SENSORY_AGGREGATE', 'Italy', 'English', 'Six trained panelists', 'Trained descriptive panel medians', 'Moka, Neapolitan pot, espresso and filter', 'Common commercial roast, source label unspecified', 'Black only', 'CC BY 4.0', TRUE, TRUE, TRUE, TRUE, 'CLEARED', 'REVIEWED', 'PUBLIC_AGGREGATE_ONLY', 'PUBLIC_AGGREGATE', '["file.vezzulli.table2-derived"]'::JSONB, 160, 11, 'Reference-panel extraction-method evidence', ARRAY['membership.cocoa-nut-caramel.cocoa','membership.cocoa-nut-caramel.caramel','membership.cocoa-nut-caramel.honey','membership.sweet-associated.honey','membership.floral-tea.floral'], ARRAY['roast-spice-smoke'], 'Article Table 2; db/data/round3h/batch1/vezzulli_2022_table2_sensory_medians.tsv', 'Medians on a source scale; chemistry workbook and third-party form definitions are excluded.', 'One article and one panel origin.', TRUE),
    ('figshare.bollen-2024', 'family.bollen-robusta-qgraders-2024', 'Sensory profiles of Robusta coffee genetic resources from the Democratic Republic of the Congo', 'Robrecht Bollen et al.', 2024, 'https://doi.org/10.3389/fsufs.2024.1382976.s002', 'Frontiers Figshare', 'Item 25735122 version 1 published 2024-05-02T04:25:40Z', DATE '2026-08-25', 'COFFEE_SENSORY_DATASET', 'Democratic Republic of the Congo', 'English', 'Three licensed Q-graders', 'Fine Robusta cupping aggregate profile', 'Immersion cupping', 'Source-reported medium roast', 'Black only', 'CC BY 4.0', TRUE, TRUE, TRUE, TRUE, 'CLEARED', 'REVIEWED', 'NO_PERSONAL_DATA', 'PUBLIC_AGGREGATE', '["file.bollen.sensory-derived"]'::JSONB, 95, 36, 'Reference-panel sample profiles and grouping keys', ARRAY['membership.cocoa-nut-caramel.cocoa','membership.floral-tea.floral'], ARRAY['roast-spice-smoke'], 'Figshare Sensory_scores A1:AJ96; sanitized TSV', 'Broad descriptor classes and one missing Nutty/Cocoa value; protocol materials and wheel designs are not republished.', 'One versioned workbook and article origin.', TRUE),
    ('mdpi.gorman-2021', 'family.gorman-milk-consumers-2021', 'Consumer Perception of Milk and Plant-Based Alternatives Added to Coffee', 'Mackenzie Gorman et al.', 2021, 'https://doi.org/10.3390/beverages7040080', 'Beverages', 'Volume 7 issue 4 article 80 version of record published 2021-12-20', DATE '2026-08-25', 'CONSUMER_SENSORY_AGGREGATE', 'Canada', 'English', '116 ordinary coffee consumers', 'CATA plus 9-point hedonic response', 'Batch-brew coffee with addition', 'Not reported', 'Dairy, soy, almond and oat additions', 'CC BY 4.0', TRUE, TRUE, TRUE, TRUE, 'CLEARED', 'REVIEWED', 'PUBLIC_AGGREGATE_ONLY', 'PUBLIC_AGGREGATE', '["file.gorman.liking-derived","file.gorman.cata-derived"]'::JSONB, 74, 14, 'Actual milk-coffee consumer outcomes and instrument evidence', ARRAY['membership.cocoa-nut-caramel.caramel','membership.floral-tea.floral','membership.roast-spice-smoke.smoke'], ARRAY['acidity-character','roast-spice-smoke','texture-body-drying'], 'Article Tables 3-4 and CATA analysis; two derived TSVs', 'Canadian convenience population; roast and origin unreported; participant rows are confidential/request-only.', 'One consumer study origin.', TRUE),
    ('mdpi.nguyen-2026', 'family.nguyen-pbma-thai-2026', 'Characterizing Sensory Drivers of Acceptance Purchase Intent and Emotional Responses to Plant-Based Milk Alternatives in Chilled Sweetened Coffee Among Thai Consumers', 'Anh Luu Hoang Nguyen et al.', 2026, 'https://doi.org/10.3390/foods15152583', 'Foods', 'Volume 15 issue 15 article 2583 version of record published 2026-07-23', DATE '2026-08-25', 'COFFEE_SENSORY_AGGREGATE', 'Thailand', 'English article; Thai consumer population', 'Nine trained panelists and 100 ordinary consumers', 'Descriptive intensity, hedonic and purchase intent', 'Espresso with plant-based milk alternatives', 'Source-reported medium roast bases', 'Five plant-alternative milk conditions', 'CC BY 4.0', TRUE, TRUE, TRUE, TRUE, 'CLEARED', 'REVIEWED', 'PUBLIC_AGGREGATE_ONLY', 'PUBLIC_AGGREGATE', '["file.nguyen.sensory-derived","file.nguyen.consumer-derived"]'::JSONB, 280, 16, 'Actual PBMA sensory and consumer outcome evidence', ARRAY['membership.cocoa-nut-caramel.caramel'], ARRAY['roast-spice-smoke','texture-body-drying'], 'Article Tables 3-4; two derived TSVs', 'Chilled sweetened matrix and Thai population are inseparable context; no participant rows are public.', 'One study origin with two panel types.', TRUE),
    ('pmc.condelli-2022', 'family.condelli-consumer-cata-2022', 'Drivers of coffee liking', 'Condelli et al.', 2022, 'https://doi.org/10.1111/1750-3841.16323', 'Europe PMC / Journal of Food Science', 'Version of record; PMC9826037', DATE '2026-08-25', 'QUESTION_INSTRUMENT_AGGREGATE', 'Italy', 'English article', '77 ordinary coffee consumers', '18-term consumer CATA plus generalized liking', 'Espresso', 'Source common roast protocol', 'Black only', 'CC BY 4.0', TRUE, TRUE, TRUE, TRUE, 'CLEARED', 'REVIEWED', 'PUBLIC_AGGREGATE_ONLY', 'PUBLIC_AGGREGATE', '["file.condelli.constructs-derived"]'::JSONB, 18, 10, 'Generic construct and relationship evidence only', ARRAY['membership.acidity-character.citrus'], ARRAY['acidity-character','roast-spice-smoke','texture-body-drying'], 'db/data/round3h/batch5/instrument_constructs.tsv rows construct.condelli.*', 'No participant rows; supplement is not redistributed.', 'One consumer study origin.', TRUE),
    ('pmc.heo-2019', 'family.heo-coldbrew-consumers-2019', 'Cold Brew Coffee Consumer Acceptability and Characterization Using the Check-All-That-Apply Method', 'Heo et al.', 2019, 'https://doi.org/10.3390/foods8080344', 'Europe PMC / Foods', 'Volume 8 issue 8 article 344; PMC6723667', DATE '2026-08-25', 'QUESTION_INSTRUMENT_AGGREGATE', 'Korea', 'English back-translation of Korean protocol', '120 naive consumers', 'CATA plus liking and intensity', 'Cold brew and coffee-maker conditions', 'Source city/medium labels where reported', 'Black only', 'CC BY 4.0', TRUE, TRUE, TRUE, TRUE, 'CLEARED', 'REVIEWED', 'PUBLIC_AGGREGATE_ONLY', 'PUBLIC_AGGREGATE', '["file.heo.constructs-derived"]'::JSONB, 17, 10, 'Reduced observed consumer construct evidence', ARRAY['membership.cocoa-nut-caramel.dark-chocolate','membership.fruit.citrus'], ARRAY['acidity-character','roast-spice-smoke','texture-body-drying'], 'db/data/round3h/batch5/instrument_constructs.tsv rows construct.heo.*', 'Full antecedent-derived 108-term list and participant rows are excluded.', 'One Korean consumer study origin.', TRUE),
    ('pmc.coffee-cuality-2026', 'family.coffee-cuality-experts-2026', 'Validation of the Coffee Cuality Method for the Expert Assessment of Coffee Sensory Quality', 'Guinard et al.', 2026, 'https://doi.org/10.3390/foods15040678', 'Europe PMC / Foods', 'Volume 15 issue 4 article 678; PMC12938992', DATE '2026-08-25', 'QUESTION_INSTRUMENT_AGGREGATE', 'United States', 'English', '56 certified Q-graders or industry sensory experts', 'Quality score, JAR adequacy, CATA presence and open response', 'Expert-preferred methods', 'Source Agtron and category labels', 'Black only', 'CC BY 4.0 article; trademark excluded', TRUE, TRUE, TRUE, TRUE, 'CLEARED', 'REVIEWED', 'PUBLIC_AGGREGATE_ONLY', 'PUBLIC_AGGREGATE', '["file.coffee-cuality.constructs-derived"]'::JSONB, 8, 10, 'Generic question architecture and expert construct evidence', ARRAY['membership.fruit.berry'], ARRAY['acidity-character','roast-spice-smoke','texture-body-drying'], 'db/data/round3h/batch5/instrument_constructs.tsv rows construct.cuality.*', 'Trademarked name, logos, trade dress, scorecards and branded forms are excluded.', 'One expert study origin.', TRUE);

INSERT INTO evidence.relationship_source_snapshot (
    snapshot_key, source_key, source_family_key, exact_version,
    acquired_at, immutable_locator, snapshot_sha256,
    source_record_count, admitted
)
VALUES
    ('snapshot.scielo-iswaldi-2026.vor', 'scielo.iswaldi-2026', 'family.iswaldi-rataconsumers-2026', 'BJFT 29 e2025106 version of record', TIMESTAMPTZ '2026-08-25 12:00:00+00', 'http://www.scielo.br/scielo.php?script=sci_pdf&pid=S1981-67232026000100207&tlng=en', '3eb3c6dba45e93c9f3799b6e372330137bcf452cfb5c6001477b2ebc7560b9f8', 72, TRUE),
    ('snapshot.pmc8953325.xml', 'pmc.vezzulli-2022', 'family.vezzulli-trainedpanel-2022', 'PMC8953325 released full-text XML', TIMESTAMPTZ '2026-08-25 12:00:00+00', 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8953325/fullTextXML', '1120133f98712a44d4af364a578f90bc348d31b51de948381fa1b835b5b26c75', 160, TRUE),
    ('snapshot.figshare-25735122.v1', 'figshare.bollen-2024', 'family.bollen-robusta-qgraders-2024', 'Figshare item 25735122 version 1', TIMESTAMPTZ '2026-08-25 12:00:00+00', 'https://ndownloader.figshare.com/files/46039437', '4ca2bff21183d2615e244f68b330ba23282f56e6d012c7be762f04baa19abb0a', 95, TRUE),
    ('snapshot.mdpi-beverages-07-00080.vor', 'mdpi.gorman-2021', 'family.gorman-milk-consumers-2021', 'Beverages 7 80 version of record', TIMESTAMPTZ '2026-08-25 12:00:00+00', 'https://mdpi-res.com/d_attachment/beverages/beverages-07-00080/article_deploy/beverages-07-00080.pdf', 'af49a8410e1cc0b34236f20b39c7174c2c1a495908af9393a5ca1f9bce6493c6', 74, TRUE),
    ('snapshot.mdpi-foods-15-02583.vor', 'mdpi.nguyen-2026', 'family.nguyen-pbma-thai-2026', 'Foods 15 2583 version of record', TIMESTAMPTZ '2026-08-25 12:00:00+00', 'https://mdpi-res.com/d_attachment/foods/foods-15-02583/article_deploy/foods-15-02583.pdf', 'c66dcbe9f6bae0eb0e3dd77cf85a44c5bf97f30519267e5be121c57cfbf8b08f', 280, TRUE),
    ('snapshot.pmc9826037.vor', 'pmc.condelli-2022', 'family.condelli-consumer-cata-2022', 'Version of record metadata acquired 2026-08-25', TIMESTAMPTZ '2026-08-25 12:00:00+00', 'https://doi.org/10.1111/1750-3841.16323', '782b4a65207e61eddff18f8205d632494d72770f73c9dbd6a8ab37af92bdd9d9', 18, TRUE),
    ('snapshot.pmc6723667.vor', 'pmc.heo-2019', 'family.heo-coldbrew-consumers-2019', 'Version of record metadata acquired 2026-08-25', TIMESTAMPTZ '2026-08-25 12:00:00+00', 'https://doi.org/10.3390/foods8080344', 'f8b135fa53a866c1d4d1f9c6889de21fcf6ba645966e125178757d78b0843231', 17, TRUE),
    ('snapshot.pmc12938992.vor', 'pmc.coffee-cuality-2026', 'family.coffee-cuality-experts-2026', 'Version of record metadata acquired 2026-08-25', TIMESTAMPTZ '2026-08-25 12:00:00+00', 'https://doi.org/10.3390/foods15040678', '54e05e1a2159063a5b93365dd748f28a56f92ad68fea7c800bb09e7f350cafab', 8, TRUE);

INSERT INTO evidence.relationship_source_file (
    file_key, snapshot_key, source_key, source_family_key, filename,
    file_role, locator, license, file_size_bytes, declared_sha256,
    verified_sha256, row_count, field_count, hash_verified,
    contains_participant_identifiers, public_export_decision, local_path
)
VALUES
    ('file.iswaldi.table3-derived', 'snapshot.scielo-iswaldi-2026.vor', 'scielo.iswaldi-2026', 'family.iswaldi-rataconsumers-2026', 'iswaldi_2026_table3_sensory_aggregates.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch1/iswaldi_2026_table3_sensory_aggregates.tsv', 'CC BY 4.0', 12668, '9b1771dccfed02da3cc4235633445eecd4800256f5f61e0c3288d5b48235bc53', '9b1771dccfed02da3cc4235633445eecd4800256f5f61e0c3288d5b48235bc53', 72, 14, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch1/iswaldi_2026_table3_sensory_aggregates.tsv'),
    ('file.vezzulli.table2-derived', 'snapshot.pmc8953325.xml', 'pmc.vezzulli-2022', 'family.vezzulli-trainedpanel-2022', 'vezzulli_2022_table2_sensory_medians.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch1/vezzulli_2022_table2_sensory_medians.tsv', 'CC BY 4.0', 28153, '1ae24e67eb77ddcf7c85e6fc085a504e022d22df3642211d21d81ee23040066b', '1ae24e67eb77ddcf7c85e6fc085a504e022d22df3642211d21d81ee23040066b', 160, 11, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch1/vezzulli_2022_table2_sensory_medians.tsv'),
    ('file.bollen.sensory-derived', 'snapshot.figshare-25735122.v1', 'figshare.bollen-2024', 'family.bollen-robusta-qgraders-2024', 'bollen_2024_sensory_scores.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch1/bollen_2024_sensory_scores.tsv', 'CC BY 4.0', 24359, 'af06701d39891c3af2d92d1a493461d33aa8995db1c6a2d39d7239178af20073', 'af06701d39891c3af2d92d1a493461d33aa8995db1c6a2d39d7239178af20073', 95, 36, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch1/bollen_2024_sensory_scores.tsv'),
    ('file.gorman.liking-derived', 'snapshot.mdpi-beverages-07-00080.vor', 'mdpi.gorman-2021', 'family.gorman-milk-consumers-2021', 'gorman_2021_liking_aggregates.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch2/gorman_2021_liking_aggregates.tsv', 'CC BY 4.0', 8322, '78934fa0876598d9dee480407cba93743e6554106fce7071b27d7116301771d1', '78934fa0876598d9dee480407cba93743e6554106fce7071b27d7116301771d1', 48, 14, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch2/gorman_2021_liking_aggregates.tsv'),
    ('file.gorman.cata-derived', 'snapshot.mdpi-beverages-07-00080.vor', 'mdpi.gorman-2021', 'family.gorman-milk-consumers-2021', 'gorman_2021_cata_terms.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch2/gorman_2021_cata_terms.tsv', 'CC BY 4.0', 3293, '23e94c22aa23755120eaa9e73bc3210adce1a0d7e1eaf3932a7ba401bb59923a', '23e94c22aa23755120eaa9e73bc3210adce1a0d7e1eaf3932a7ba401bb59923a', 26, 10, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch2/gorman_2021_cata_terms.tsv'),
    ('file.nguyen.sensory-derived', 'snapshot.mdpi-foods-15-02583.vor', 'mdpi.nguyen-2026', 'family.nguyen-pbma-thai-2026', 'nguyen_2026_table3_sensory_intensities.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch2/nguyen_2026_table3_sensory_intensities.tsv', 'CC BY 4.0', 62187, '10630ff70297d0dbab22ecc164dd863b6bafbef66980a6287c68d6cbb8eda574', '10630ff70297d0dbab22ecc164dd863b6bafbef66980a6287c68d6cbb8eda574', 260, 16, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch2/nguyen_2026_table3_sensory_intensities.tsv'),
    ('file.nguyen.consumer-derived', 'snapshot.mdpi-foods-15-02583.vor', 'mdpi.nguyen-2026', 'family.nguyen-pbma-thai-2026', 'nguyen_2026_table4_consumer_outcomes.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch2/nguyen_2026_table4_consumer_outcomes.tsv', 'CC BY 4.0', 5131, '5d9b8891930629b9304eda3cd5d65018559c84344f40a765ee6d012afc231cc2', '5d9b8891930629b9304eda3cd5d65018559c84344f40a765ee6d012afc231cc2', 20, 15, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch2/nguyen_2026_table4_consumer_outcomes.tsv'),
    ('file.condelli.constructs-derived', 'snapshot.pmc9826037.vor', 'pmc.condelli-2022', 'family.condelli-consumer-cata-2022', 'instrument_constructs.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch5/instrument_constructs.tsv#construct.condelli', 'CC BY 4.0', 10329, '3a196e6581f5717e88d6e59980b2d584f28f113a8b889a1493ae184268477f9b', '3a196e6581f5717e88d6e59980b2d584f28f113a8b889a1493ae184268477f9b', 18, 10, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch5/instrument_constructs.tsv'),
    ('file.heo.constructs-derived', 'snapshot.pmc6723667.vor', 'pmc.heo-2019', 'family.heo-coldbrew-consumers-2019', 'instrument_constructs.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch5/instrument_constructs.tsv#construct.heo', 'CC BY 4.0', 10329, '3a196e6581f5717e88d6e59980b2d584f28f113a8b889a1493ae184268477f9b', '3a196e6581f5717e88d6e59980b2d584f28f113a8b889a1493ae184268477f9b', 17, 10, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch5/instrument_constructs.tsv'),
    ('file.coffee-cuality.constructs-derived', 'snapshot.pmc12938992.vor', 'pmc.coffee-cuality-2026', 'family.coffee-cuality-experts-2026', 'instrument_constructs.tsv', 'DERIVED_AGGREGATE', 'db/data/round3h/batch5/instrument_constructs.tsv#construct.cuality', 'CC BY 4.0 article; trademark excluded', 10329, '3a196e6581f5717e88d6e59980b2d584f28f113a8b889a1493ae184268477f9b', '3a196e6581f5717e88d6e59980b2d584f28f113a8b889a1493ae184268477f9b', 8, 10, TRUE, FALSE, 'PUBLIC_AGGREGATE', 'db/data/round3h/batch5/instrument_constructs.tsv');

INSERT INTO evidence.model_prebuild_source_profile (
    source_key, source_family_key, source_role, sensory_method_family,
    preparation_families, roast_schemes, milk_modes, participant_type,
    languages, counts_as_sensory_outcome, counts_as_ordinary_user,
    counts_as_reference_panel, counts_as_milk_sensory, chemistry_only,
    preparation_only, survey_without_sensory_variables,
    source_local_observation_row_count, source_local_sample_count,
    participant_or_panel_count, empirical_coverage_cell_count,
    crossed_preparation_roast_cell_count, annotation_complete,
    rights_review_complete, limitation
)
VALUES
    ('scielo.iswaldi-2026', 'family.iswaldi-rataconsumers-2026', 'SENSORY_OUTCOME', 'RATA_HEDONIC', ARRAY['v60','cold_brew'], ARRAY['light','medium','dark'], ARRAY['black'], 'ORDINARY_USER', ARRAY['en'], TRUE, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, 72, 12, 50, 12, 12, TRUE, TRUE, 'Aggregate RATA and liking remain separate source scales.'),
    ('pmc.vezzulli-2022', 'family.vezzulli-trainedpanel-2022', 'SENSORY_OUTCOME', 'TRAINED_DESCRIPTIVE', ARRAY['moka','neapolitan_pot','espresso','filter'], ARRAY['source_unknown'], ARRAY['black'], 'TRAINED_PANEL', ARRAY['en'], TRUE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, 160, 8, 6, 8, 0, TRUE, TRUE, 'Source roast is not portable and is excluded from crossed-roast counts.'),
    ('figshare.bollen-2024', 'family.bollen-robusta-qgraders-2024', 'SENSORY_OUTCOME', 'Q_GRADER_CUPPING', ARRAY['immersion_cupping'], ARRAY['medium_source_reported'], ARRAY['black'], 'EXPERT_PANEL', ARRAY['en'], TRUE, FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, 95, 95, 3, 95, 95, TRUE, TRUE, 'Profiles are sample aggregates under one source protocol.'),
    ('mdpi.gorman-2021', 'family.gorman-milk-consumers-2021', 'SENSORY_OUTCOME', 'CATA_HEDONIC', ARRAY['batch_brew'], ARRAY['source_unknown'], ARRAY['dairy','soy','almond','oat'], 'ORDINARY_USER', ARRAY['en'], TRUE, TRUE, FALSE, TRUE, FALSE, FALSE, FALSE, 48, 4, 116, 4, 0, TRUE, TRUE, 'Roast is unreported; CATA and hedonic outcomes are not pooled.'),
    ('mdpi.nguyen-2026', 'family.nguyen-pbma-thai-2026', 'SENSORY_OUTCOME', 'TRAINED_DESCRIPTIVE', ARRAY['espresso'], ARRAY['medium_source_reported'], ARRAY['almond','pistachio','macadamia','white_sesame','riceberry'], 'ORDINARY_USER', ARRAY['en','th'], TRUE, TRUE, TRUE, TRUE, FALSE, FALSE, FALSE, 280, 10, 109, 10, 10, TRUE, TRUE, 'Trained and consumer panels remain separate feature surfaces.'),
    ('pmc.condelli-2022', 'family.condelli-consumer-cata-2022', 'QUESTION_INSTRUMENT', 'INSTRUMENT_ONLY', ARRAY['espresso'], ARRAY['source_common_roast'], ARRAY['black'], 'NOT_APPLICABLE', ARRAY['en'], FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, 0, 0, 0, 0, 0, TRUE, TRUE, 'Only generic constructs and aggregate relationships are imported.'),
    ('pmc.heo-2019', 'family.heo-coldbrew-consumers-2019', 'QUESTION_INSTRUMENT', 'INSTRUMENT_ONLY', ARRAY['cold_brew','coffee_maker'], ARRAY['city_or_medium_source_labels'], ARRAY['black'], 'NOT_APPLICABLE', ARRAY['en'], FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, 0, 0, 0, 0, 0, TRUE, TRUE, 'Only the reduced observed construct set is imported.'),
    ('pmc.coffee-cuality-2026', 'family.coffee-cuality-experts-2026', 'QUESTION_INSTRUMENT', 'INSTRUMENT_ONLY', ARRAY['expert_preferred'], ARRAY['source_agtron_and_categories'], ARRAY['black'], 'NOT_APPLICABLE', ARRAY['en'], FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, 0, 0, 0, 0, 0, TRUE, TRUE, 'Generic architecture only; branded scorecard and trademark identity are excluded.');

INSERT INTO evidence.model_prebuild_feature_definition (
    feature_key, semantics, source_method, data_type, unit,
    missingness_semantics, available_source_families,
    harmonization_status, model_use_status, limitation
)
VALUES
    ('feature.source-family', 'Independent canonical origin identifier.', 'All partitions', 'CATEGORY', 'source family key', ARRAY['NOT_APPLICABLE'], ARRAY['all-governed'], 'SEMANTICALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Identity is compatible; outcome semantics are not implied.'),
    ('feature.coffee-identity', 'Source-local coffee lot genotype product or condition identity.', 'Source metadata', 'TEXT', 'source-local identifier', ARRAY['NOT_REPORTED','SOURCE_UNKNOWN'], ARRAY['sensory-outcome'], 'SEMANTICALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Identifiers cannot be compared as the same coffee across sources without review.'),
    ('feature.participant-type', 'Ordinary user trained panel expert panel or not applicable.', 'Study metadata', 'CATEGORY', 'participant class', ARRAY['NOT_APPLICABLE','NOT_REPORTED'], ARRAY['sensory-outcome','instrument'], 'SEMANTICALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Participant classes remain coarse.'),
    ('feature.preparation', 'Source-local preparation family and reported details.', 'Study context', 'CATEGORY', 'source-local label', ARRAY['NOT_REPORTED','SOURCE_UNKNOWN'], ARRAY['sensory-outcome'], 'SEMANTICALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Labels are retained without silent standardization.'),
    ('feature.roast', 'Source-local roast category scheme or measurement.', 'Study context', 'CATEGORY', 'source-local label or scheme', ARRAY['NOT_REPORTED','SOURCE_UNKNOWN'], ARRAY['sensory-outcome'], 'PARTIALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Medium City and Agtron are never silently equated.'),
    ('feature.milk-mode', 'Black dairy or plant-alternative matrix context.', 'Study context', 'CATEGORY', 'milk mode', ARRAY['NOT_APPLICABLE','NOT_REPORTED'], ARRAY['sensory-outcome'], 'SEMANTICALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Plant alternatives remain named source conditions.'),
    ('feature.language', 'Source and response language where reported.', 'Source metadata', 'CATEGORY', 'BCP 47 code', ARRAY['NOT_REPORTED','SOURCE_UNKNOWN'], ARRAY['all-governed'], 'SEMANTICALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Language code is not bilingual equivalence.'),
    ('feature.missingness-code', 'Declared reason a value is absent.', 'Federated contract', 'CATEGORY', 'missingness category', ARRAY['NOT_APPLICABLE'], ARRAY['all-governed'], 'SEMANTICALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Codes must not be collapsed without an explicit future protocol.'),
    ('feature.descriptor-presence', 'Source-local presence or observed selection of a descriptor.', 'CATA or source class', 'BOOLEAN', 'selected or present', ARRAY['NOT_REPORTED','NOT_MEASURED','STRUCTURALLY_MISSING'], ARRAY['cata','q-grader'], 'PARTIALLY_COMPATIBLE', 'PREBUILD_ONLY', 'CATA selection and Q-grader frequency remain different fields.'),
    ('feature.descriptor-intensity', 'Source-local numeric descriptor intensity.', 'RATA or descriptive panel', 'NUMERIC', 'source scale', ARRAY['NOT_REPORTED','NOT_MEASURED','REPORTED_UNRESOLVED'], ARRAY['rata','trained-panel'], 'NOT_COMPATIBLE', 'PREBUILD_ONLY', '0-7 RATA, 0-9 medians and 0-15 descriptive means are not pooled.'),
    ('feature.cata-selection', 'Check-all-that-apply binary selection or aggregate frequency.', 'CATA', 'BOOLEAN', 'source selection semantics', ARRAY['NOT_REPORTED','NOT_MEASURED'], ARRAY['consumer-cata'], 'SOURCE_LOCAL_ONLY', 'PREBUILD_ONLY', 'Aggregate associations do not reconstruct participant rows.'),
    ('feature.rata-rating', 'Rate-all-that-apply intensity response.', 'RATA', 'NUMERIC', 'source 0-7 scale', ARRAY['NOT_REPORTED','NOT_MEASURED'], ARRAY['iswaldi','liberica'], 'SOURCE_LOCAL_ONLY', 'PREBUILD_ONLY', 'RATA is not CATA presence or trained intensity.'),
    ('feature.basic-taste', 'Source-defined acidity bitterness sweetness or ratio measure.', 'Mixed sensory methods', 'NUMERIC', 'source scale', ARRAY['NOT_REPORTED','NOT_MEASURED','SOURCE_UNKNOWN'], ARRAY['sensory-outcome'], 'PARTIALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Salt/Acid ratio and acidity intensity are incompatible.'),
    ('feature.body', 'Source-defined mouthfeel body fullness or related construct.', 'Mixed sensory methods', 'NUMERIC', 'source scale', ARRAY['NOT_REPORTED','NOT_MEASURED'], ARRAY['sensory-outcome'], 'PARTIALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Body, fullness and mouthfeel are retained separately.'),
    ('feature.astringency', 'Source-defined astringency or drying construct.', 'Mixed sensory methods', 'NUMERIC', 'source scale or selection', ARRAY['NOT_REPORTED','NOT_MEASURED'], ARRAY['sensory-outcome','instrument'], 'PARTIALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Selection and intensity are not pooled.'),
    ('feature.liking', 'Source-local hedonic liking measure.', 'Hedonic test', 'NUMERIC', 'source scale', ARRAY['NOT_REPORTED','NOT_MEASURED'], ARRAY['consumer-outcome'], 'NOT_COMPATIBLE', 'PREBUILD_ONLY', '1-7 and 1-9 scales remain source-local.'),
    ('feature.purchase-intent', 'Source-local purchase-intent response or aggregate.', 'Consumer response', 'NUMERIC', 'source proportion or scale', ARRAY['NOT_REPORTED','NOT_MEASURED'], ARRAY['nguyen'], 'SOURCE_LOCAL_ONLY', 'PREBUILD_ONLY', 'Top-two-box aggregate is not a participant response row.'),
    ('feature.industry-expression', 'Observed product or tasting-note expression.', 'Contemporary corpus', 'TEXT', 'normalized expression', ARRAY['NOT_REPORTED','STRUCTURALLY_MISSING'], ARRAY['firstbloom'], 'PARTIALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Round 3H adds no lawful contemporary families.'),
    ('feature.association-membership', 'Governed non-probabilistic association-range membership state.', 'Evidence review', 'CATEGORY', 'lifecycle status', ARRAY['REPORTED_UNRESOLVED','NOT_APPLICABLE'], ARRAY['relationship-evidence'], 'PARTIALLY_COMPATIBLE', 'PREBUILD_ONLY', 'Membership is not a probability or model weight.'),
    ('feature.question-response', 'Future response to a governed question target.', 'Question research', 'CATEGORY', 'not collected', ARRAY['STRUCTURALLY_MISSING','NOT_APPLICABLE'], ARRAY['question-evidence'], 'NOT_COMPATIBLE', 'PREBUILD_ONLY', 'No real response, validation, or information-gain data exist.');

INSERT INTO evidence.model_prebuild_source_partition (
    partition_key, source_family_key, dataset_snapshot_key,
    source_registry_path, coffee_identity_availability, participant_type,
    sensory_method, context_fields, descriptor_fields, language_fields,
    sample_count, row_count, feature_keys, rights_boundary, grouping_keys,
    future_training_surface_status, compatible_join_group
)
VALUES
    ('partition.baseline.cotter', 'family.legacy-cotter-consumers', 'snapshot.dryad-cotter.v4', 'audit.empirical_coverage_cell + existing Dryad registry', 'AVAILABLE', 'ORDINARY_USER', 'CATA_JAR_HEDONIC', ARRAY['preparation','roast','milk_mode'], ARRAY['cata','jar','liking'], ARRAY['language'], 1, 3186, ARRAY['feature.source-family','feature.coffee-identity','feature.participant-type','feature.preparation','feature.roast','feature.milk-mode','feature.language','feature.cata-selection','feature.basic-taste','feature.liking','feature.missingness-code'], 'Existing source-specific rights record governs export.', ARRAY['source_family','coffee_identity','participant'], 'ELIGIBLE_AFTER_FUTURE_PROTOCOL', 'group.cotter-source-local'),
    ('partition.baseline.yeager', 'family.legacy-yeager-chemistry', 'snapshot.dryad-yeager.v5', 'audit.empirical_coverage_cell + existing Dryad registry', 'PARTIAL', 'NOT_APPLICABLE', 'CHEMISTRY_ONLY', ARRAY['preparation','roast','milk_mode'], ARRAY['chemistry_only'], ARRAY['language'], 0, 1631, ARRAY['feature.source-family','feature.coffee-identity','feature.preparation','feature.roast','feature.milk-mode','feature.language','feature.missingness-code'], 'Chemistry-only partition is ineligible as sensory outcome.', ARRAY['source_family','coffee_identity'], 'INELIGIBLE', 'group.yeager-chemistry-only'),
    ('partition.baseline.liberica', 'family.liberica-ratapanel-2025', 'snapshot.mendeley-liberica.v1', 'evidence.relationship_source_file', 'AVAILABLE', 'TRAINED_PANEL', 'RATA', ARRAY['preparation','roast','milk_mode'], ARRAY['rata'], ARRAY['language'], 9, 9, ARRAY['feature.source-family','feature.coffee-identity','feature.participant-type','feature.preparation','feature.roast','feature.milk-mode','feature.language','feature.rata-rating','feature.descriptor-intensity','feature.missingness-code'], 'Only public aggregate is exportable; raw panel identifiers remain external.', ARRAY['source_family','coffee_identity','roast','preparation'], 'ELIGIBLE_AFTER_FUTURE_PROTOCOL', 'group.liberica-source-local'),
    ('partition.baseline.firstbloom', 'family.firstbloom-historical', 'snapshot.firstbloom-governed', 'corpus.corpus_snapshot_source', 'PARTIAL', 'NOT_APPLICABLE', 'INDUSTRY_LANGUAGE', ARRAY['source','document'], ARRAY['lexical_expression'], ARRAY['language'], 0, 1777, ARRAY['feature.source-family','feature.language','feature.industry-expression','feature.missingness-code'], 'Historical governed corpus remains separate from new contemporary-family targets.', ARRAY['source_family','document'], 'ELIGIBLE_AFTER_FUTURE_PROTOCOL', 'group.firstbloom-language'),
    ('partition.round3h.iswaldi', 'family.iswaldi-rataconsumers-2026', 'snapshot.scielo-iswaldi-2026.vor', 'db/data/round3h/batch1/iswaldi_2026_table3_sensory_aggregates.tsv', 'AVAILABLE', 'ORDINARY_USER', 'RATA_HEDONIC', ARRAY['coffee_origin','preparation','roast','milk_mode'], ARRAY['rata','liking'], ARRAY['language'], 12, 72, ARRAY['feature.source-family','feature.coffee-identity','feature.participant-type','feature.preparation','feature.roast','feature.milk-mode','feature.language','feature.rata-rating','feature.descriptor-intensity','feature.basic-taste','feature.body','feature.liking','feature.missingness-code'], 'CC BY aggregate only.', ARRAY['source_family','coffee_identity','roast','preparation'], 'ELIGIBLE_AFTER_FUTURE_PROTOCOL', 'group.iswaldi-source-local'),
    ('partition.round3h.vezzulli', 'family.vezzulli-trainedpanel-2022', 'snapshot.pmc8953325.xml', 'db/data/round3h/batch1/vezzulli_2022_table2_sensory_medians.tsv', 'AVAILABLE', 'TRAINED_PANEL', 'TRAINED_DESCRIPTIVE', ARRAY['coffee_species','preparation','roast'], ARRAY['descriptor_intensity'], ARRAY['language'], 8, 160, ARRAY['feature.source-family','feature.coffee-identity','feature.participant-type','feature.preparation','feature.roast','feature.milk-mode','feature.language','feature.descriptor-intensity','feature.basic-taste','feature.body','feature.astringency','feature.missingness-code'], 'CC BY article aggregates; chemistry and third-party form materials excluded.', ARRAY['source_family','coffee_identity','preparation'], 'ELIGIBLE_AFTER_FUTURE_PROTOCOL', 'group.vezzulli-source-local'),
    ('partition.round3h.bollen', 'family.bollen-robusta-qgraders-2024', 'snapshot.figshare-25735122.v1', 'db/data/round3h/batch1/bollen_2024_sensory_scores.tsv', 'AVAILABLE', 'EXPERT_PANEL', 'Q_GRADER_CUPPING', ARRAY['genotype','harvest','roast','preparation'], ARRAY['scores','descriptor_frequencies'], ARRAY['language'], 95, 95, ARRAY['feature.source-family','feature.coffee-identity','feature.participant-type','feature.preparation','feature.roast','feature.milk-mode','feature.language','feature.descriptor-presence','feature.descriptor-intensity','feature.basic-taste','feature.body','feature.missingness-code'], 'CC BY sanitized aggregate; raw workbook metadata and third-party protocol materials excluded.', ARRAY['source_family','genotype','harvest'], 'ELIGIBLE_AFTER_FUTURE_PROTOCOL', 'group.bollen-source-local'),
    ('partition.round3h.gorman', 'family.gorman-milk-consumers-2021', 'snapshot.mdpi-beverages-07-00080.vor', 'db/data/round3h/batch2/gorman_2021_liking_aggregates.tsv + gorman_2021_cata_terms.tsv', 'NOT_REPORTED', 'ORDINARY_USER', 'CATA_HEDONIC', ARRAY['milk_mode','preparation','roast'], ARRAY['cata','liking'], ARRAY['language'], 4, 74, ARRAY['feature.source-family','feature.participant-type','feature.preparation','feature.roast','feature.milk-mode','feature.language','feature.cata-selection','feature.descriptor-presence','feature.liking','feature.missingness-code'], 'CC BY aggregate; request-only participant rows excluded.', ARRAY['source_family','milk_mode','participant_group'], 'ELIGIBLE_AFTER_FUTURE_PROTOCOL', 'group.gorman-source-local'),
    ('partition.round3h.nguyen', 'family.nguyen-pbma-thai-2026', 'snapshot.mdpi-foods-15-02583.vor', 'db/data/round3h/batch2/nguyen_2026_table3_sensory_intensities.tsv + nguyen_2026_table4_consumer_outcomes.tsv', 'AVAILABLE', 'ORDINARY_USER', 'TRAINED_DESCRIPTIVE_AND_HEDONIC', ARRAY['coffee_base','milk_mode','preparation','roast','serving_mode'], ARRAY['descriptor_intensity','liking','purchase_intent'], ARRAY['language'], 10, 280, ARRAY['feature.source-family','feature.coffee-identity','feature.participant-type','feature.preparation','feature.roast','feature.milk-mode','feature.language','feature.descriptor-intensity','feature.basic-taste','feature.body','feature.astringency','feature.liking','feature.purchase-intent','feature.missingness-code'], 'CC BY aggregate; panel types and outcomes remain separated.', ARRAY['source_family','coffee_identity','milk_mode','panel_type'], 'ELIGIBLE_AFTER_FUTURE_PROTOCOL', 'group.nguyen-source-local'),
    ('partition.round3h.condelli', 'family.condelli-consumer-cata-2022', 'snapshot.pmc9826037.vor', 'db/data/round3h/batch5/instrument_constructs.tsv#construct.condelli', 'NOT_APPLICABLE', 'NOT_APPLICABLE', 'INSTRUMENT_ONLY', ARRAY['question_construct'], ARRAY['consumer_terms'], ARRAY['language'], 0, 18, ARRAY['feature.source-family','feature.language','feature.association-membership','feature.question-response','feature.missingness-code'], 'Generic CC BY constructs only; no participant rows or supplement copy.', ARRAY['source_family','construct'], 'METADATA_ONLY', 'group.condelli-instrument'),
    ('partition.round3h.heo', 'family.heo-coldbrew-consumers-2019', 'snapshot.pmc6723667.vor', 'db/data/round3h/batch5/instrument_constructs.tsv#construct.heo', 'NOT_APPLICABLE', 'NOT_APPLICABLE', 'INSTRUMENT_ONLY', ARRAY['question_construct'], ARRAY['observed_reduced_terms'], ARRAY['language'], 0, 17, ARRAY['feature.source-family','feature.language','feature.association-membership','feature.question-response','feature.missingness-code'], 'Reduced observed CC BY constructs; full antecedent-derived list excluded.', ARRAY['source_family','construct'], 'METADATA_ONLY', 'group.heo-instrument'),
    ('partition.round3h.coffee-cuality', 'family.coffee-cuality-experts-2026', 'snapshot.pmc12938992.vor', 'db/data/round3h/batch5/instrument_constructs.tsv#construct.cuality', 'NOT_APPLICABLE', 'NOT_APPLICABLE', 'INSTRUMENT_ONLY', ARRAY['question_construct'], ARRAY['generic_measure_architecture'], ARRAY['language'], 0, 8, ARRAY['feature.source-family','feature.language','feature.association-membership','feature.question-response','feature.missingness-code'], 'Generic CC BY architecture only; trademarked forms and identity excluded.', ARRAY['source_family','construct'], 'METADATA_ONLY', 'group.coffee-cuality-instrument');

INSERT INTO evidence.model_prebuild_partition_feature (
    partition_key, feature_key, availability_status, source_field_locator,
    missingness_semantics, harmonization_status, pooling_allowed
)
SELECT
    partition.partition_key,
    listed.feature_key,
    'AVAILABLE',
    partition.source_registry_path,
    'NOT_REPORTED',
    feature.harmonization_status,
    feature.harmonization_status = 'SEMANTICALLY_COMPATIBLE'
FROM evidence.model_prebuild_source_partition AS partition
CROSS JOIN LATERAL unnest(partition.feature_keys) AS listed(feature_key)
JOIN evidence.model_prebuild_feature_definition AS feature
  ON feature.feature_key = listed.feature_key;

INSERT INTO evidence.model_prebuild_split_candidate (
    split_candidate_key, partition_key, grouping_dimensions,
    prohibited_cross_split_keys, split_status, leakage_risk_status,
    limitation
)
SELECT
    replace(partition_key, 'partition.', 'split.'),
    partition_key,
    grouping_keys,
    grouping_keys,
    'CANDIDATE_NOT_EXECUTED',
    CASE future_training_surface_status
        WHEN 'INELIGIBLE' THEN 'PARTIAL_CONTROL'
        ELSE 'CONTROL_DEFINED'
    END,
    'Candidate grouping contract only; no split, model, ranking, or policy was executed.'
FROM evidence.model_prebuild_source_partition;

INSERT INTO audit.model_prebuild_context_cell (
    context_cell_key, source_family_key, coffee_identity,
    preparation_family, roast_source_label, milk_mode, sensory_method,
    participant_type, language_code, evidence_status, zero_filled,
    crossed_preparation_roast_eligible, source_row_locator, limitation
)
SELECT
    format('context.round3h.iswaldi.%s.%s.%s', origin, roast, preparation),
    'family.iswaldi-rataconsumers-2026', origin, preparation, roast,
    'BLACK', 'RATA_HEDONIC', 'ORDINARY_USER', 'en',
    'OBSERVED_SOURCE_LOCAL_EVIDENCE', FALSE, TRUE,
    format('Iswaldi 2026 Table 3: %s / %s / %s', origin, roast, preparation),
    'Aggregate consumer cell; RATA and liking scales remain source-local.'
FROM unnest(ARRAY['gayo','brazil']) AS origin
CROSS JOIN unnest(ARRAY['light','medium','dark']) AS roast
CROSS JOIN unnest(ARRAY['v60','cold-brew']) AS preparation;

INSERT INTO audit.model_prebuild_context_cell (
    context_cell_key, source_family_key, coffee_identity,
    preparation_family, roast_source_label, milk_mode, sensory_method,
    participant_type, language_code, evidence_status, zero_filled,
    crossed_preparation_roast_eligible, source_row_locator, limitation
)
SELECT
    format('context.round3h.vezzulli.%s.%s', species, preparation),
    'family.vezzulli-trainedpanel-2022', species, preparation,
    'SOURCE_UNKNOWN', 'BLACK', 'TRAINED_DESCRIPTIVE', 'TRAINED_PANEL',
    'en', 'OBSERVED_SOURCE_LOCAL_EVIDENCE', FALSE, FALSE,
    format('Vezzulli 2022 Table 2: %s / %s', species, preparation),
    'Source roast is unreported and this cell is excluded from crossed-roast counts.'
FROM unnest(ARRAY['arabica','canephora']) AS species
CROSS JOIN unnest(ARRAY['moka','neapolitan-pot','espresso','filter']) AS preparation;

CREATE TEMP TABLE round3h_bollen_stage (
    genotype TEXT, harvest TEXT, genetic_class TEXT,
    cluster_lula TEXT, cluster_wild TEXT, cluster_congolese_subgroup_a TEXT,
    fragrance_aroma TEXT, flavor TEXT, aftertaste TEXT, salt_acid TEXT,
    bitter_sweet TEXT, mouthfeel TEXT, balance TEXT, overall TEXT,
    uniformity TEXT, clean_cup TEXT, mean_total_score TEXT,
    sd_total_score TEXT, spread_total_score TEXT, total_rounded TEXT,
    green_vegetative TEXT, other_descriptor_class TEXT, roasted TEXT,
    spices TEXT, nutty_cocoa TEXT, sweet TEXT, floral TEXT, fruity TEXT,
    sour_fermented TEXT, planting_year TEXT, tree_age TEXT, inera_info TEXT,
    clones TEXT, weight_in_g TEXT, weight_out_g TEXT, weight_loss_ratio TEXT
) ON COMMIT DROP;

\copy round3h_bollen_stage FROM 'db/data/round3h/batch1/bollen_2024_sensory_scores.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO audit.model_prebuild_context_cell (
    context_cell_key, source_family_key, coffee_identity,
    preparation_family, roast_source_label, milk_mode, sensory_method,
    participant_type, language_code, evidence_status, zero_filled,
    crossed_preparation_roast_eligible, source_row_locator, limitation
)
SELECT
    format('context.round3h.bollen.%s.%s', lower(genotype), lower(harvest)),
    'family.bollen-robusta-qgraders-2024', genotype || '/' || harvest,
    'immersion-cupping', 'medium_source_reported', 'BLACK',
    'Q_GRADER_CUPPING', 'EXPERT_PANEL', 'en',
    'OBSERVED_SOURCE_LOCAL_EVIDENCE', FALSE, TRUE,
    format('Bollen 2024 Sensory_scores: %s / %s', genotype, harvest),
    'Aggregate Q-grader profile; genotype-harvest grouping must remain intact.'
FROM round3h_bollen_stage;

INSERT INTO audit.model_prebuild_context_cell (
    context_cell_key, source_family_key, coffee_identity,
    preparation_family, roast_source_label, milk_mode, sensory_method,
    participant_type, language_code, evidence_status, zero_filled,
    crossed_preparation_roast_eligible, source_row_locator, limitation
)
SELECT
    format('context.round3h.gorman.%s', milk),
    'family.gorman-milk-consumers-2021', 'consumer-coffee-' || milk,
    'batch-brew', 'SOURCE_UNKNOWN',
    CASE milk WHEN 'dairy' THEN 'DAIRY' ELSE 'PLANT_ALTERNATIVE' END,
    'CATA_HEDONIC', 'ORDINARY_USER', 'en',
    'OBSERVED_SOURCE_LOCAL_EVIDENCE', FALSE, FALSE,
    format('Gorman 2021 aggregate: %s coffee', milk),
    'Milk matrix is observed; coffee origin and roast are unreported.'
FROM unnest(ARRAY['dairy','soy','almond','oat']) AS milk;

INSERT INTO audit.model_prebuild_context_cell (
    context_cell_key, source_family_key, coffee_identity,
    preparation_family, roast_source_label, milk_mode, sensory_method,
    participant_type, language_code, evidence_status, zero_filled,
    crossed_preparation_roast_eligible, source_row_locator, limitation
)
SELECT
    format('context.round3h.nguyen.%s.%s', coffee_base, milk),
    'family.nguyen-pbma-thai-2026', coffee_base || '/' || milk,
    'espresso-with-pbma', 'medium_source_reported',
    'PLANT_ALTERNATIVE', 'TRAINED_DESCRIPTIVE_AND_HEDONIC',
    'ORDINARY_USER', 'th', 'OBSERVED_SOURCE_LOCAL_EVIDENCE', FALSE, TRUE,
    format('Nguyen 2026 Tables 3-4: %s / %s', coffee_base, milk),
    'Chilled sweetened matrix, panel types, and source scales remain inseparable context.'
FROM unnest(ARRAY['arabica','arabica_robusta_70_30']) AS coffee_base
CROSS JOIN unnest(ARRAY['riceberry','almond','pistachio','macadamia','white_sesame']) AS milk;

CREATE TEMP TABLE round3h_claim_stage (
    evidence_claim_key TEXT, target_entity_type TEXT, target_entity_key TEXT,
    source_family_key TEXT, source_key TEXT, snapshot_key TEXT,
    evidence_basis TEXT, evidence_direction TEXT, evidence_scope TEXT,
    evidence_locator TEXT, method TEXT, configuration_json TEXT,
    support_count INTEGER, document_count INTEGER, source_diversity INTEGER,
    review_status TEXT, limitation TEXT
) ON COMMIT DROP;

\copy round3h_claim_stage FROM 'db/data/round3h/batch5/relationship_evidence_claims.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', QUOTE E'\x01')

INSERT INTO evidence.relationship_evidence_claim (
    evidence_claim_key, target_entity_type, target_entity_key,
    source_family_key, source_key, snapshot_key, evidence_basis,
    evidence_direction, evidence_scope, evidence_locator, method,
    configuration, support_count, document_count, source_diversity,
    review_status, limitation, contradictory_evidence_retained
)
SELECT
    evidence_claim_key, target_entity_type, target_entity_key,
    source_family_key, source_key, snapshot_key, evidence_basis,
    evidence_direction, evidence_scope, evidence_locator, method,
    configuration_json::JSONB, support_count, document_count,
    source_diversity, review_status, limitation, TRUE
FROM round3h_claim_stage;

CREATE TEMP TABLE round3h_promotion_stage (
    promotion_key TEXT, membership_key TEXT, disposition TEXT,
    prior_lifecycle TEXT, new_lifecycle TEXT,
    supporting_source_families TEXT, supporting_claim_keys TEXT,
    decision_reason TEXT, remaining_uncertainty TEXT, review_protocol TEXT
) ON COMMIT DROP;

\copy round3h_promotion_stage FROM 'db/data/round3h/batch5/membership_promotions.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO kb.relationship_review_decision (
    review_key, association_range_membership_id, disposition,
    prior_lifecycle, new_lifecycle, supporting_source_families,
    challenging_source_families, decision_reason, remaining_uncertainty,
    review_protocol, reviewed_round
)
SELECT
    promotion.promotion_key, membership.association_range_membership_id,
    promotion.disposition, promotion.prior_lifecycle,
    promotion.new_lifecycle,
    regexp_split_to_array(promotion.supporting_source_families, ';'),
    ARRAY[]::TEXT[], promotion.decision_reason,
    promotion.remaining_uncertainty, promotion.review_protocol, '3H'
FROM round3h_promotion_stage AS promotion
JOIN corpus.association_range_membership AS membership
  ON membership.membership_key = promotion.membership_key;

UPDATE corpus.association_range_membership AS membership
SET lifecycle_status = promotion.new_lifecycle,
    evidence_basis = 'PEER_REVIEWED_SENSORY_EVIDENCE',
    evidence_key = promotion.promotion_key,
    provenance_path = 'db/data/round3h/batch5/membership_promotions.tsv -> reviewed Round 3H relationship claims'
FROM round3h_promotion_stage AS promotion
WHERE membership.membership_key = promotion.membership_key;

CREATE TEMP TABLE round3h_question_stage (
    question_evidence_key TEXT, question_range_target_key TEXT,
    supporting_source_families TEXT, independent_origin_count INTEGER,
    decision TEXT, research_basis TEXT, user_validation_status TEXT,
    information_gain_status TEXT, limitation TEXT
) ON COMMIT DROP;

\copy round3h_question_stage FROM 'db/data/round3h/batch5/question_research_evidence.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO calibration.model_prebuild_question_evidence (
    question_evidence_key, question_range_target_id,
    supporting_source_families, independent_origin_count,
    research_decision, research_basis, user_validation_status,
    information_gain_status, limitation
)
SELECT
    staged.question_evidence_key, target.question_range_target_id,
    regexp_split_to_array(staged.supporting_source_families, ';'),
    staged.independent_origin_count, staged.decision,
    staged.research_basis, staged.user_validation_status,
    staged.information_gain_status, staged.limitation
FROM round3h_question_stage AS staged
JOIN calibration.question_range_target AS target
  ON target.question_range_target_key = staged.question_range_target_key;

INSERT INTO calibration.question_target_review_decision (
    review_key, question_range_target_id, disposition,
    supporting_source_families, challenging_source_families,
    decision_reason, remaining_uncertainty, review_protocol,
    reviewed_round
)
SELECT
    replace(staged.question_evidence_key, 'question-evidence.', 'question-review.'),
    target.question_range_target_id, staged.decision,
    regexp_split_to_array(staged.supporting_source_families, ';'),
    ARRAY[]::TEXT[], staged.research_basis, staged.limitation,
    'ROUND3H_INDEPENDENT_RESEARCH_SUPPORT_V1', '3H'
FROM round3h_question_stage AS staged
JOIN calibration.question_range_target AS target
  ON target.question_range_target_key = staged.question_range_target_key;

INSERT INTO audit.model_prebuild_range_evidence_summary (
    range_key, source_local_supporting_membership_count,
    cross_source_supporting_membership_count,
    supporting_source_families, challenging_source_families,
    range_lifecycle_changed, limitation
)
VALUES
    ('acidity-character', 1, 0, ARRAY['family.condelli-consumer-cata-2022'], ARRAY['family.iswaldi-rataconsumers-2026','family.bollen-robusta-qgraders-2024'], FALSE, 'One exact citrus membership path; acidity and citrus remain distinct.'),
    ('cocoa-nut-caramel', 4, 2, ARRAY['family.vezzulli-trainedpanel-2022','family.bollen-robusta-qgraders-2024','family.gorman-milk-consumers-2021','family.nguyen-pbma-thai-2026','family.heo-coldbrew-consumers-2019'], ARRAY[]::TEXT[], FALSE, 'Member promotions do not promote or validate the full association range.'),
    ('floral-tea', 1, 1, ARRAY['family.vezzulli-trainedpanel-2022','family.bollen-robusta-qgraders-2024','family.gorman-milk-consumers-2021'], ARRAY['family.coffee-cuality-experts-2026'], FALSE, 'Floral support does not establish tea or full-range equivalence.'),
    ('fruit', 2, 0, ARRAY['family.heo-coldbrew-consumers-2019','family.coffee-cuality-experts-2026'], ARRAY['family.vezzulli-trainedpanel-2022','family.bollen-robusta-qgraders-2024'], FALSE, 'Berry and citrus remain separate reviewed source-local paths.'),
    ('roast-spice-smoke', 1, 1, ARRAY['family.liberica-ratapanel-2025','family.gorman-milk-consumers-2021'], ARRAY['family.iswaldi-rataconsumers-2026','family.vezzulli-trainedpanel-2022','family.bollen-robusta-qgraders-2024'], FALSE, 'Smoky support does not collapse roast, burnt, spice, ash, or smoke.'),
    ('sweet-associated', 1, 0, ARRAY['family.vezzulli-trainedpanel-2022'], ARRAY['family.nguyen-pbma-thai-2026'], FALSE, 'Honey and basic sweetness remain distinct source constructs.'),
    ('texture-body-drying', 0, 0, ARRAY['family.iswaldi-rataconsumers-2026','family.nguyen-pbma-thai-2026'], ARRAY['family.gorman-milk-consumers-2021','family.condelli-consumer-cata-2022'], FALSE, 'Independent constructs exist, but no membership reached the promotion threshold.');

CREATE TEMP TABLE round3h_contemporary_language_stage (
    candidate_key TEXT, canonical_origin TEXT, stable_url TEXT,
    rights_or_access TEXT, observation_status TEXT, decision TEXT,
    countable_family_gain INTEGER, countable_document_gain INTEGER,
    public_export_decision TEXT, limitation TEXT
) ON COMMIT DROP;

\copy round3h_contemporary_language_stage FROM 'db/data/round3h/batch3/contemporary_language_decisions.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO corpus.model_prebuild_language_source_decision (
    decision_key, candidate_key, language_plane, rights_status,
    observation_status, source_authored, machine_translated,
    artificial_variant, countable_family_gain, countable_document_gain,
    countable_expression_gain, decision, limitation
)
SELECT
    replace(candidate_key, 'candidate.', 'language.round3h.contemporary.'),
    candidate_key, 'CONTEMPORARY', rights_or_access, observation_status,
    FALSE, FALSE, FALSE, countable_family_gain, countable_document_gain,
    0, decision || ': ' || public_export_decision, limitation
FROM round3h_contemporary_language_stage;

CREATE TEMP TABLE round3h_zh_language_stage (
    candidate_key TEXT, canonical_origin TEXT, stable_url TEXT,
    rights_or_access TEXT, source_authored_zh_status TEXT,
    coffee_sensory_yield_status TEXT, decision TEXT,
    countable_family_gain INTEGER, countable_sensory_expression_gain INTEGER,
    public_export_decision TEXT, limitation TEXT
) ON COMMIT DROP;

\copy round3h_zh_language_stage FROM 'db/data/round3h/batch4/zh_hans_language_decisions.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO corpus.model_prebuild_language_source_decision (
    decision_key, candidate_key, language_plane, rights_status,
    observation_status, source_authored, machine_translated,
    artificial_variant, countable_family_gain, countable_document_gain,
    countable_expression_gain, decision, limitation
)
SELECT
    replace(candidate_key, 'candidate.', 'language.round3h.zh-hans.'),
    candidate_key, 'ZH_HANS', rights_or_access,
    source_authored_zh_status || '; ' || coffee_sensory_yield_status,
    FALSE, FALSE, FALSE, countable_family_gain, 0,
    countable_sensory_expression_gain,
    decision || ': ' || public_export_decision, limitation
FROM round3h_zh_language_stage;

INSERT INTO audit.model_prebuild_leakage_risk (
    leakage_risk_key, risk_type, affected_partitions, detection_rule,
    control_status, control_key, audit_pass, limitation
)
VALUES
    ('leakage.round3h.same-coffee', 'SAME_COFFEE', ARRAY['partition.baseline.cotter','partition.round3h.iswaldi','partition.round3h.bollen','partition.round3h.nguyen'], 'Group all rows sharing a source-local coffee identity before any future split.', 'CONTROL_DEFINED', 'grouping_keys:coffee_identity', TRUE, 'Cross-source identity resolution remains intentionally unresolved.'),
    ('leakage.round3h.same-participant', 'SAME_PARTICIPANT', ARRAY['partition.baseline.cotter','partition.round3h.gorman','partition.round3h.nguyen'], 'Participant identifiers or participant groups must not cross future split boundaries.', 'CONTROL_DEFINED', 'grouping_keys:participant', TRUE, 'Aggregate-only sources cannot reconstruct participant-level splits.'),
    ('leakage.round3h.duplicate-product-page', 'DUPLICATE_PRODUCT_PAGE', ARRAY['partition.baseline.firstbloom'], 'Canonical document and stable page identity must be deduplicated before any future split.', 'CONTROL_DEFINED', 'grouping_keys:document', TRUE, 'Round 3H admitted no new contemporary product-page corpus.'),
    ('leakage.round3h.mirrored-source', 'MIRRORED_SOURCE', ARRAY['partition.baseline.firstbloom','partition.round3h.bollen'], 'Canonical origin and mirror-of fields determine one independent family before partitioning.', 'CONTROL_DEFINED', 'source_family:canonical_origin_key', TRUE, 'Mirrors never increment independent-family counts.'),
    ('leakage.round3h.derived-raw-overlap', 'DERIVED_RAW_OVERLAP', ARRAY['partition.round3h.iswaldi','partition.round3h.vezzulli','partition.round3h.bollen','partition.round3h.gorman','partition.round3h.nguyen'], 'Snapshot and file hash lineage groups raw and derived representations together.', 'CONTROL_DEFINED', 'snapshot_key+declared_sha256', TRUE, 'Only rights-cleared aggregate derivatives are committed.'),
    ('leakage.round3h.translation-variant', 'TRANSLATION_VARIANT', ARRAY['partition.baseline.firstbloom'], 'Source-authored identity and language provenance must group translations before a future split.', 'CONTROL_DEFINED', 'grouping_keys:source_family+document', TRUE, 'Machine-translated variants are prohibited from observed-language counts.'),
    ('leakage.round3h.context-derivative', 'CONTEXT_DERIVATIVE', ARRAY['partition.round3h.iswaldi','partition.round3h.bollen','partition.round3h.nguyen'], 'Roast and preparation derivatives sharing coffee identity remain in one future grouping.', 'CONTROL_DEFINED', 'grouping_keys:coffee_identity+roast+preparation', TRUE, 'The registry defines controls only; no train or test split was executed.');

INSERT INTO audit.model_prebuild_batch_result (
    batch_key, targeted_gap, new_source_family_count, new_coverage_count,
    meaningful_coverage_gain, consecutive_no_gain_number, stop_status,
    evidence_path
)
VALUES
    ('batch.round3h.1', 'Sensory outcomes, preparations, roasts, and reference panels', 3, 115, TRUE, 0, 'CONTINUE', 'db/data/round3h/batch1/coverage_after_batch1.tsv'),
    ('batch.round3h.2', 'Actual milk-coffee sensory outcomes and ordinary users', 2, 14, TRUE, 0, 'CONTINUE', 'db/data/round3h/batch2/coverage_after_batch2.tsv'),
    ('batch.round3h.3', 'Contemporary source-authored tasting language', 0, 0, FALSE, 1, 'CONTINUE', 'db/data/round3h/batch3/batch3_result.json'),
    ('batch.round3h.4', 'Source-authored Simplified-Chinese sensory expressions', 0, 0, FALSE, 2, 'STOP_TWO_CONSECUTIVE_NO_GAIN', 'db/data/round3h/batch4/batch4_result.json'),
    ('batch.round3h.5', 'Independent relationship and question-instrument evidence', 3, 76, TRUE, 0, 'STOP_MINIMUM_REACHED', 'db/data/round3h/batch5/batch5_result.json');

INSERT INTO audit.model_prebuild_execution_guard (
    guard_key, ranking_model_run_count, adaptive_policy_run_count,
    deep_learning_run_count, embedding_run_count, pgvector_required,
    real_human_collection_performed, real_observation_count,
    product_frontend_modified, canonical_concept_change_count
)
VALUES ('guard.round3h.prebuild-only', 0, 0, 0, 0, FALSE, FALSE, 0, FALSE, 0);

INSERT INTO audit.model_prebuild_checkpoint (
    checkpoint_key, source_sha, expected_state_commit_sha,
    expected_state_file, expected_state_frozen_before_import,
    threshold_revision_count, canonical_concept_count_before,
    active_sensory_attribute_count_before,
    baseline_empirical_coverage_cell_count, acquisition_stop_status
)
VALUES (
    'checkpoint.round3h.model-prebuild',
    'aa6a18ca5f4c289d5fa588e1996c7fa219f99eca',
    'a2d85ecc1e03a96f129342f4ee4ed9755d7c4a75',
    'db/data/round3h/model_prebuild_expected_state.tsv', TRUE, 0,
    130, 92, 52, 'STOP_TWO_CONSECUTIVE_TARGETED_NO_GAIN_BATCHES'
);

INSERT INTO audit.model_prebuild_data_access_request (
    request_key, source_doi, corresponding_author_route,
    desired_file_structure, requested_reuse_terms,
    prepared_request_text_path, request_ready, request_sent
)
VALUES
    ('request.round3h.foods-2022-2440', '10.3390/foods11162440', 'Corresponding-author route in the published Foods article', 'De-identified participant-by-sample sensory and consumer-response table with codebook', 'Explicit commercial machine-use, derivative-use, and public aggregate redistribution permission', 'docs/research/coffee-sensory-kb-v0-round3h/requests/foods-2022-2440.md', TRUE, FALSE),
    ('request.round3h.jfs-15326', '10.1111/jfs.15326', 'Corresponding-author route in the published Journal of Food Science article', 'De-identified participant-by-sample sensory response table with preparation and roast context plus codebook', 'Explicit commercial machine-use, derivative-use, and public aggregate redistribution permission', 'docs/research/coffee-sensory-kb-v0-round3h/requests/jfs-15326.md', TRUE, FALSE);

INSERT INTO audit.model_prebuild_constraint_registry (
    constraint_key, scope, rule, enforcement_layer, negative_test
)
VALUES
    ('constraint.round3h.source-family-required', 'source registry', 'Every admitted source and partition must resolve to one governed source family.', 'POSTGRESQL_CONSTRAINT', 'reject_dataset_without_source_family'),
    ('constraint.round3h.file-hash-match', 'file provenance', 'Declared and verified SHA-256 values must match before admission.', 'POSTGRESQL_CONSTRAINT', 'reject_file_with_mismatched_hash'),
    ('constraint.round3h.rights-known-export', 'rights', 'Rights-unknown raw material cannot be marked for public export.', 'POSTGRESQL_CONSTRAINT', 'reject_rights_unknown_raw_export'),
    ('constraint.round3h.mirror-independence', 'source counting', 'Two mirrors of one canonical origin cannot both count as independent.', 'POSTGRESQL_TRIGGER', 'reject_two_mirrors_as_independent'),
    ('constraint.round3h.chemistry-not-sensory', 'sensory evidence', 'Chemistry-only sources cannot count as sensory outcomes.', 'POSTGRESQL_CONSTRAINT', 'reject_chemistry_only_as_sensory'),
    ('constraint.round3h.preparation-not-milk', 'milk evidence', 'Preparation-only metadata cannot count as milk sensory evidence.', 'POSTGRESQL_CONSTRAINT', 'reject_preparation_only_as_milk'),
    ('constraint.round3h.dictionary-not-validation', 'language evidence', 'Dictionaries and standards cannot count as observed sensory-language validation.', 'AUDIT_QUERY', 'detect_dictionary_as_sensory_language'),
    ('constraint.round3h.survey-needs-sensory', 'sensory evidence', 'Surveys without sensory variables cannot count as sensory sources.', 'POSTGRESQL_CONSTRAINT', 'reject_survey_without_sensory_variables'),
    ('constraint.round3h.context-observed-only', 'context coverage', 'Inferred cells cannot count as observed empirical coverage.', 'POSTGRESQL_CONSTRAINT', 'reject_inferred_context_as_observed'),
    ('constraint.round3h.no-zero-fill', 'context coverage', 'Unobserved context cells cannot be zero-filled.', 'POSTGRESQL_CONSTRAINT', 'reject_zero_filled_context'),
    ('constraint.round3h.no-artificial-lexical-gain', 'language corpus', 'Artificial lexical variants cannot increase expression coverage.', 'POSTGRESQL_CONSTRAINT', 'reject_artificial_lexical_variant'),
    ('constraint.round3h.no-machine-translation-gain', 'zh-Hans corpus', 'Machine-translated Chinese cannot count as observed source-authored language.', 'POSTGRESQL_CONSTRAINT', 'reject_machine_translated_chinese'),
    ('constraint.round3h.no-rata-cata-pooling', 'harmonization', 'Incompatible RATA and CATA values cannot be silently pooled.', 'POSTGRESQL_CONSTRAINT', 'reject_incompatible_rata_cata_pooling'),
    ('constraint.round3h.missingness-declared', 'harmonization', 'Missingness categories cannot be collapsed without declaration.', 'POSTGRESQL_CONSTRAINT', 'reject_missingness_collapse'),
    ('constraint.round3h.no-incompatible-join', 'federated partitions', 'Source-local partitions cannot silently join to incompatible features.', 'POSTGRESQL_CONSTRAINT', 'reject_incompatible_source_join'),
    ('constraint.round3h.same-coffee-split', 'leakage', 'The same source-local coffee identity cannot cross future split candidates.', 'CI_GATE', 'detect_same_coffee_split_leakage'),
    ('constraint.round3h.relationship-independent-evidence', 'relationship promotion', 'Promotion requires a reviewed decision and independent admitted evidence.', 'POSTGRESQL_TRIGGER', 'reject_relationship_promotion_without_evidence'),
    ('constraint.round3h.canonical-freeze', 'ontology', 'Canonical concepts cannot be created to increase Round 3H coverage.', 'POSTGRESQL_TRIGGER', 'reject_canonical_concept_for_coverage'),
    ('constraint.round3h.no-model-run', 'analysis boundary', 'Prebuild data cannot be used to create a model run.', 'POSTGRESQL_TRIGGER', 'reject_model_run_from_prebuild'),
    ('constraint.round3h.no-embedding', 'analysis boundary', 'Embedding generation is outside Round 3H.', 'POSTGRESQL_TRIGGER', 'reject_embedding_generation'),
    ('constraint.round3h.threshold-revision-record', 'expected state', 'A threshold cannot be reduced without a complete decision record.', 'POSTGRESQL_CONSTRAINT', 'reject_unrecorded_threshold_reduction'),
    ('constraint.round3h.readiness-hard-gates', 'readiness', 'Readiness cannot be true while a mandatory hard gate fails.', 'POSTGRESQL_TRIGGER', 'reject_true_readiness_with_failed_gate'),
    ('constraint.round3h.question-not-user-validated', 'question research', 'Research support cannot be relabeled as user validation.', 'POSTGRESQL_CONSTRAINT', 'reject_question_user_validation_claim'),
    ('constraint.round3h.question-no-information-gain', 'question research', 'Information gain remains not estimable without response observations.', 'POSTGRESQL_CONSTRAINT', 'reject_question_information_gain_claim');

INSERT INTO audit.model_prebuild_readiness_assertion (
    assertion_key, model_prebuild_data_ready, readiness_state,
    asserted_at, evidence_path
)
VALUES (
    'assertion.round3h.final', FALSE, 'COMPLETE_WITH_DATA_COVERAGE_GAP',
    TIMESTAMPTZ '2026-08-25 12:00:00+00',
    'audit.run_model_prebuild_readiness_gate()'
);

INSERT INTO audit.round3e_artifact_hash (artifact_key, sha256)
VALUES (
    'round3h.model-prebuild-manifest',
    'ea895bc0a9a8f9ee2edf567d86ee42bb6acf9570aa9dc8d3dd73f63cd5368569'
);

COMMIT;
