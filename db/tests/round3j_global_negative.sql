\set ON_ERROR_STOP on

DO $round3j_global_negative$
DECLARE
    rejected BOOLEAN := FALSE;
BEGIN
    BEGIN
        INSERT INTO audit.round3j_global_flavor_occurrence (
            occurrence_key, document_key, source_family_key, source_key,
            source_version, raw_source_phrase, normalized_expression,
            language_tag, script, expression_role, source_locator,
            source_authored, deterministic_normalization, machine_translated,
            project_translation, preference_evidence, label_disposition,
            candidate_target_keys, review_state, training_eligible,
            duplicate_reason, rights_state, privacy_state,
            provenance_complete, limitation
        )
        SELECT
            'occurrence.global.r3j.invalid.translation', document_key,
            source_family_key, source_key, source_version, 'invented',
            'invented', language_tag, script, 'UNRESOLVED', 'invalid',
            FALSE, 'LLM_PARAPHRASE', TRUE, TRUE, TRUE, 'UNRESOLVED',
            '["forced-concept"]', 'UNREVIEWED', TRUE, 'NONE',
            'PUBLIC_WEBPAGE_ONLY', privacy_state, FALSE, 'must fail'
        FROM audit.round3j_global_flavor_document LIMIT 1;
    EXCEPTION WHEN check_violation THEN
        rejected := TRUE;
    END;
    IF NOT rejected THEN
        RAISE EXCEPTION 'generated/unreviewed/forced-label occurrence was accepted';
    END IF;

    IF (SELECT count(*) FROM audit.round3j_global_flavor_document) <> 6
       OR (SELECT count(*) FROM audit.round3j_global_flavor_occurrence) <> 37
       OR EXISTS (
           SELECT 1 FROM audit.round3j_global_flavor_occurrence
           WHERE machine_translated OR project_translation
              OR preference_evidence OR NOT source_authored
              OR label_disposition <> 'UNRESOLVED'
              OR candidate_target_keys <> '[]'
              OR NOT provenance_complete
       )
       OR EXISTS (
           SELECT 1 FROM audit.round3j_global_source_class_result
           WHERE saturated
       ) THEN
        RAISE EXCEPTION 'Round 3J global negative invariant failed';
    END IF;
END
$round3j_global_negative$;

SELECT 'ROUND3J_GLOBAL_NEGATIVE_PASS=true' AS result;
