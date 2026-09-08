#!/usr/bin/env python3
"""Run frozen cell reference over the sealed R12 table inventory, offline.

Use the bundled Python with lxml. The legacy bridge is called only AFTER the
independent classification, never as an input to it. Missing vision measurement
is recorded as missing, not as a negative or a calibrated accuracy estimate.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
from lxml import etree, html

import classify_table_cells_r12b as reference
import finalize_r11_artifacts as finalizer

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'db/data/backend-sequential-model-v2/revisions'
OUT = REV / 'r12b'
CACHE = Path('/private/tmp/coffee-flavor-r11-fulltext-cache')


def read(path):
    return json.loads(path.read_text())


def sha(body):
    return hashlib.sha256(body).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n')


def body_for(receipt):
    if not receipt:
        return None
    path = CACHE / (sha(receipt['requested_url'].encode()) + '.body')
    if not path.exists():
        return None
    body = path.read_bytes()
    if sha(body) != receipt['sha256']:
        raise ValueError('CACHE_HASH_MISMATCH')
    return body


def tree_for(body, mime):
    parser = (etree.XMLParser(resolve_entities=False, no_network=True, recover=True)
              if 'xml' in mime or body.lstrip().startswith(b'<?xml') else html.HTMLParser(no_network=True))
    return etree.fromstring(body, parser)


def content_grid(table):
    """Independent generic span decoder. No descriptor or caption knowledge."""
    occupied = {}
    trs = table.xpath('.//*[local-name()="tr"]')
    for r, tr in enumerate(trs):
        c = 0
        for node in tr:
            if not isinstance(node.tag, str):
                continue
            if etree.QName(node).localname not in {'td', 'th'}:
                continue
            while (r, c) in occupied:
                c += 1
            value = ' '.join(''.join(node.itertext()).split())
            down = int(node.get('rowspan', '1'))
            across = int(node.get('colspan', '1'))
            if not (1 <= down <= 1000 and 1 <= across <= 1000):
                raise ValueError('INVALID_SPAN')
            for dr in range(down):
                for dc in range(across):
                    occupied[(r + dr, c + dc)] = value
            c += across
    if not occupied:
        return []
    height = max(r for r, c in occupied) + 1
    width = max(c for r, c in occupied) + 1
    return [[occupied.get((r, c), '') for c in range(width)] for r in range(height)]


def select_table(tree, identity, ordinal, expected_count):
    tables = tree.xpath('//*[local-name()="table"]')
    matching = [t for t in tables if t.get('id') == identity or
                any(parent.get('id') == identity for parent in t.iterancestors())]
    if matching:
        return matching[0], len(matching), 'PUBLISHED_ID_FIRST_VARIANT'
    if len(tables) != expected_count:
        raise ValueError('AMBIGUOUS_TABLE_ALIGNMENT:' + identity)
    return tables[ordinal], 1, 'ORDINAL_WITH_EQUAL_DOCUMENT_TABLE_COUNT'


def original_projection(labels, records):
    counts = Counter(r['shape_id'] for r in records)
    return min(labels, key=lambda k: (-counts[k], k)) if labels else 'unclassified'


def group_bridge(candidate, outcome, body, table_id):
    # This module is deliberately not imported by classify_table_cells_r12b.
    import extract_candidates_r11 as legacy_document
    import stratify_extraction_r11 as legacy_groups
    receipt = outcome['retrieval']
    if 'xml' in receipt['content_type'] or body.lstrip().startswith(b'<?xml'):
        tables, metadata = legacy_document.parse_xml(body)
    else:
        tables, metadata = legacy_document.parse_html(body)
    selected = [t for t in tables if t['table_id'] == table_id]
    if len(selected) != 1:
        raise ValueError('LEGACY_BRIDGE_TABLE_ID_NOT_UNIQUE')
    direct, rules = legacy_groups.load_direct_registry()
    result = legacy_groups.sample_axis_records(candidate, outcome, selected[0], metadata['plain_text'], direct, rules)
    named = [r for r in result if r['shape_id'] in {'T1', 'T2', 'T3'}]
    return named


def run():
    if etree.LXML_VERSION != (6,1,1,0) or etree.LIBXML_VERSION != (2,14,6):
        raise RuntimeError('XML_LIBRARY_VERSION_MISMATCH')
    def deny(*args, **kwargs):
        raise RuntimeError('R12B_NETWORK_DISABLED')
    socket.socket.connect = deny
    protected_paths = list((REV / 'r11').glob('*.json')) + list((REV / 'r12').glob('*.json'))
    protected = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in protected_paths}
    classifier_path = ROOT / 'db/scripts/classify_table_cells_r12b.py'
    frozen_classifier = subprocess.check_output(['git', 'show', 'f8e7ba2:db/scripts/classify_table_cells_r12b.py'], cwd=ROOT)
    assert frozen_classifier == classifier_path.read_bytes(), 'FROZEN_REFERENCE_CHANGED'
    combined = read(REV / 'r11/shape_distribution.json')
    corrected, correction = finalizer.combined_outputs(combined, read(REV / 'r11/supplement_recovery.json'), read(REV / 'r11/targeted_acquisition.json'))
    assert {r['record_id']: r for r in corrected} == {r['record_id']: r for r in combined['records']}
    rows_by_table = {}
    for row in corrected:
        if row['r11_acquisition_stream'] == 'R10_248_PRIMARY':
            rows_by_table.setdefault((row['source_doi'], row['table_id']), []).append(row)
    registry = read(REV / 'r9/output_policy_contract.json')['concept_role_registry']
    funnel = read(REV / 'r12/funnel_counts.json')
    outcomes = {r['candidate_id']: r for r in read(REV / 'r11/extraction_report.json')['candidate_outcomes']}
    candidates = {r['candidate_id']: r for r in read(REV / 'r10/acquisition_manifest.json')['discovery_candidates']}
    measurements, groups, disagreements = [], [], []
    for doc in funnel['candidates']:
        if not doc['tables']:
            continue
        receipt = doc['historical_retrieval']
        body = body_for(receipt)
        if body is None:
            raise ValueError('REQUIRED_400_TABLE_BODY_MISSING')
        tree = tree_for(body, receipt['content_type'])
        for old in doc['tables']:
            table_id = old['table_id']
            element, variants, alignment = select_table(tree, table_id, old['table_index'], len(doc['tables']))
            grid = content_grid(element)
            result = reference.classify(grid, registry)
            original_rows = rows_by_table.get((doc['candidate_id'], table_id), [])
            old_label = original_projection(old['shapes'], original_rows)
            wrappers = list(element.iterancestors())
            wrapper = next((x for x in wrappers if etree.QName(x).localname == 'table-wrap'), element)
            caption = ' '.join(wrapper.xpath('./*[local-name()="caption"]//text()'))
            filename_only = bool(re.fullmatch(r'\s*[^\s]+\.(?:xlsx|xls|csv|tsv|docx|pdf)(?:#[^\s]+)?\s*', caption, re.I))
            entry = {'candidate_id': doc['candidate_id'], 'table_id': table_id,
                'source_sha256': receipt['sha256'], 'grid_sha256': sha(json.dumps(grid, ensure_ascii=False).encode()),
                'input_variant_count': variants, 'input_alignment': alignment,
                'original_label': old_label, 'original_label_set': old['shapes'],
                'reference': result, 'filename_only_caption': filename_only,
                'list_presence_detected': any(p['kind'] == 'LIST' for p in result['pairs']),
                'frozen_license_clear': bool(outcomes[doc['candidate_id']].get('source_verified_license'))}
            measurements.append(entry)
            if set(old['shapes']) != set(result['labels']):
                disagreements.append({'candidate_id': doc['candidate_id'], 'table_id': table_id,
                    'original': old['shapes'], 'reference': result['labels'],
                    'third_method': 'OPTIONAL_VISUAL_TABLE_REGION', 'status': 'UNRESOLVED_OPTIONAL_THIRD_METHOD_NOT_EXECUTED'})
            if set(result['labels']) & {'T1', 'T2', 'T3'}:
                group_row = {'candidate_id': doc['candidate_id'], 'table_id': table_id,
                             'reference_labels': result['labels'], 'group_ids': [], 'direct_group_ids': [],
                             'records': [], 'status': 'SKIPPED_FROZEN_LICENSE_GATE'}
                if entry['frozen_license_clear']:
                    named = group_bridge(candidates[doc['candidate_id']], outcomes[doc['candidate_id']], body, table_id)
                    group_row.update(status='EXISTING_EXTRACTOR_NONEMPTY' if named else 'EXISTING_EXTRACTOR_EMPTY_NOT_EVIDENCE_OF_NO_GROUPS',
                        group_ids=sorted({r['coffee_group_id'] for r in named}),
                        direct_group_ids=sorted({r['coffee_group_id'] for r in named if r['mapping_status'] == 'DIRECT'}),
                        records=[{'record_id': r['record_id'], 'group_id': r['coffee_group_id'], 'concept_id': r['concept_id'],
                                  'shape': r['shape_id'], 'mapping_status': r['mapping_status']} for r in named])
                groups.append(group_row)
    assert len(measurements) == 400
    matrix = reference.confusion([(r['original_label'], r['reference']['label']) for r in measurements])
    old_negative = [r for r in measurements if r['original_label'] == 'unclassified']
    newly_typed = [r for r in old_negative if r['reference']['label'] != 'unclassified']
    group_ids = {g for row in groups for g in row['group_ids']}
    baseline_ids = {r['coffee_group_id'] for r in corrected if r['r11_acquisition_stream'] == 'R10_248_PRIMARY' and r['shape_id'] in {'T1','T2','T3'}}
    inventory = []
    taxonomy = read(REV / 'r11/failure_taxonomy.json')['records']
    for row in taxonomy:
        if row['initial_diagnosis_class'] not in {'FULL_TEXT_NO_MACHINE_READABLE_TABLE', 'TABLE_PRESENT_WRONG_STRUCTURE'}:
            continue
        outcome = outcomes[row['candidate_id']]
        receipt = outcome.get('retrieval')
        body = body_for(receipt)
        clear = bool(outcome.get('source_verified_license'))
        inventory.append({'candidate_id': row['candidate_id'], 'original_class': row['initial_diagnosis_class'],
            'held': body is not None, 'frozen_license_clear': clear,
            'content_type': receipt['content_type'] if receipt else None,
            'original_pdf_bytes': bool(body and body.startswith(b'%PDF')),
            'source_sha256': receipt['sha256'] if receipt else None,
            'visual_verdict': None, 'status': 'ELIGIBLE_AWAITING_RENDER_AND_CALIBRATED_VISION' if clear and body else 'OUTSIDE_HELD_LICENSE_CLEAR_SCOPE'})
    common = {'fit_count': 0, 'new_acquisition_count': 0, 'real_label_model_metric_count': 0,
        'classifier_version': reference.VERSION, 'classifier_sha256': sha(frozen_classifier),
        'lxml_version': list(etree.LXML_VERSION), 'orchestrator_python_version':sys.version,
        'render_implementation_sha256':sha((ROOT/'db/scripts/render_held_pdf_pages_r12b.py').read_bytes()),
        'protected_artifacts_sha256': protected, 'r11_forward_source_accounting': correction,
        'not_ground_truth': True}
    render_requests = []
    for item in inventory:
        if item['held'] and item['frozen_license_clear']:
            receipt = outcomes[item['candidate_id']]['retrieval']
            render_requests.append({'candidate_id': item['candidate_id'], 'sha256': receipt['sha256'],
                'path': str(CACHE/(sha(receipt['requested_url'].encode())+'.body'))})
    requested_ids = {r['candidate_id'] for r in render_requests}
    for item in measurements:
        if item['original_label_set'] and item['candidate_id'] not in requested_ids:
            receipt = outcomes[item['candidate_id']]['retrieval']
            render_requests.append({'candidate_id': item['candidate_id'], 'sha256': receipt['sha256'],
                'path': str(CACHE/(sha(receipt['requested_url'].encode())+'.body'))})
            requested_ids.add(item['candidate_id'])
    # System Python provides PyMuPDF; the bundled runtime supplies lxml above.
    rendered = json.loads(subprocess.check_output(
        ['/Library/Frameworks/Python.framework/Versions/3.13/bin/python3',
         str(ROOT/'db/scripts/render_held_pdf_pages_r12b.py')],
        input=json.dumps(render_requests).encode()))
    save('tier1_confusion.json', common | matrix | {'tables': measurements,
        'original_unclassified': len(old_negative), 'reference_types_original_unclassified': len(newly_typed),
        'apparent_original_false_negative_fraction_relative_to_reference': len(newly_typed)/len(old_negative),
        'measurement_error_identification_interval': [0, 1],
        'kappa_accuracy_interpretation': 'Kappa is exact projected agreement on this finite table inventory, not accuracy. Multiple labels are retained; projection is lossy.',
        'original_multilabel_tables': sum(len(r['original_label_set'])>1 for r in measurements),
        'reference_multilabel_tables': sum(len(r['reference']['labels'])>1 for r in measurements),
        'original_per_shape_table_presence': dict(Counter(label for r in measurements for label in r['original_label_set'])),
        'reference_per_shape_table_presence': dict(Counter(label for r in measurements for label in r['reference']['labels'])),
        'original_typed_retained_as_any_type': sum(bool(r['reference']['labels']) for r in measurements if r['original_label_set']),
        'genuine_missed_tables_among_360_identification_interval': [0,len(old_negative)]})
    save('tier1_recovered_groups.json', common | {'tables': groups,
        'existing_extractor_counterfactual_group_count': len(group_ids),
        'baseline_primary_named_group_count': len(baseline_ids), 'additional_group_ids': sorted(group_ids-baseline_ids),
        'valid_supervision_identification_interval': [0,len(group_ids)],
        'total_missed_groups_identification_interval': {'lower': 0, 'upper': None, 'reason': 'Misses shared by both instruments are unidentified.'},
        'defect_classes_among_original_unclassified': {
            'filename_only_caption': sum(r['filename_only_caption'] for r in old_negative),
            'explicit_list_structure_detected': sum(r['list_presence_detected'] for r in old_negative)},
        'limitation': 'The existing extractor includes its old caption and axis gates. Its empty result is not a valid estimate of zero lost groups. No bypass, synthetic caption or admission was applied.'})
    geometry_request = {'common': common, 'output_dir': str(OUT), 'rendered': rendered,
        'inventory': inventory, 'positive_table_ids': [{'candidate_id': r['candidate_id'], 'table_id': r['table_id']} for r in measurements if r['original_label_set']]}
    geometry = json.loads(subprocess.check_output(
        ['/Library/Frameworks/Python.framework/Versions/3.13/bin/python3', str(ROOT/'db/scripts/measure_pdf_geometry_r12b.py')],
        input=json.dumps(geometry_request).encode()))
    tier2_results = read(OUT/'tier2_adjudication.json')
    tier2_disagreements = []
    for item in tier2_results['documents']:
        baseline = next(c for c in funnel['candidates'] if c['candidate_id']==item['candidate_id'])
        if item['positive'] is not None and baseline['tables_detected_before_classification'] is not None:
            old_detected = baseline['tables_detected_before_classification'] > 0
            if item['positive'] != old_detected:
                tier2_disagreements.append({'candidate_id':item['candidate_id'], 'original_any_table_detected':old_detected,
                    'geometry_sensory_numeric_grid':item['positive'], 'status':'UNRESOLVED_DIFFERENT_TARGET_DEFINITIONS_AND_OPTIONAL_THIRD_METHOD',
                    'note':'Any HTML/XML table and a sensory numeric PDF grid are different predicates; disagreement is not automatically an error.'})
    save('disagreement_escalation.json', common | {'tier1_disagreements': disagreements,
        'tier1_disagreement_count': len(disagreements), 'third_method_completed': 0,
        'residual_unresolved_fraction_of_disagreements': 1.0 if disagreements else None,
        'residual_unresolved_fraction_of_all_tables': len(disagreements)/len(measurements),
        'tier2_disagreements': tier2_disagreements, 'tier2_unresolved_disagreement_count':len(tier2_disagreements),
        'reason': 'Third visual adjudication is optional under owner amendment; no forced tie-break or ground truth claim.'})
    reference_positive = [r for r in measurements if r['reference']['labels']]
    retained = sum(bool(r['original_label_set']) for r in reference_positive)
    save('agreement_report.json', common | {'status': 'MACHINE_REFERENCES_MEASURED_WITH_EXPLICIT_LIMITATIONS',
        'tier1_kappa': matrix['kappa'], 'tier2_geometry_calibration':geometry,
        'pipeline_positive_retention_relative_to_tier1': retained/len(reference_positive) if reference_positive else None,
        'pipeline_positive_retention_counts': {'retained':retained,'reference_positive':len(reference_positive)},
        'measurement_uncertainty_band': [0,1],
        'uncertainty_reason': 'Tier 2 page-control s/f bands are reported separately and cannot calibrate Tier 1 or be transported to document-any-positive rates. Reflow controls do not calibrate original PDFs. Genuine accuracy remains unidentified in [0,1]; document count band is propagated conservatively in tier2_adjudication.',
        'newly_typed_table_count': len(newly_typed),
        'existing_extractor_additional_group_count': len(group_ids-baseline_ids),
        'verdict': 'Instrument limitations and inter-method disagreements are measured, but calibrated valid-supervision loss is not identified. Geometry self-calibration is conditional on markup reference pages, not truth. No population extrapolation or training resumption.',
        'owner_decision': 'UNCHANGED_PENDING_OWNER_DECISION'})
    for path, expected in protected.items():
        assert sha((ROOT/path).read_bytes()) == expected, 'SEALED_ARTIFACT_CHANGED'
    print(json.dumps({'tables': len(measurements), 'kappa': matrix['kappa'],
        'newly_typed':len(newly_typed), 'counterfactual_groups':len(group_ids),
        'additional_groups':len(group_ids-baseline_ids), 'disagreements':len(disagreements),
        'tier2_scope':len(inventory)}, indent=2))


if __name__ == '__main__':
    run()
