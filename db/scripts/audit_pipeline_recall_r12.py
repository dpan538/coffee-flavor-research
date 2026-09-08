#!/usr/bin/env python3
"""Cache-only R12 diagnostic replay. No acquisition, fitting or model metrics.

The legacy modules are imported unmodified. sys.settrace makes their exceptions,
empty returns and executed fallback sites observable without changing decisions.
Historical retrieval gaps remain unknown. This is NOT the human control trial.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from contextlib import contextmanager
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import zipfile

import extract_candidates_r11 as extract
import stratify_extraction_r11 as stratify
import recover_supplements_r11 as supplements
import finalize_r11_artifacts as finalizer

ROOT = Path(__file__).resolve().parents[2]
REVISIONS = ROOT / 'db/data/backend-sequential-model-v2/revisions'
R11 = REVISIONS / 'r11'
R12 = REVISIONS / 'r12'
BASELINE = '7323a32e964a137dcd49886bbe024db2a773dd92'
MODULES = ['extract_candidates_r11.py', 'stratify_extraction_r11.py',
           'recover_supplements_r11.py', 'acquire_targeted_r11.py',
           'finalize_r11_artifacts.py', 'acquire_license_verified_r10.py']


def read(path):
    return json.loads(path.read_text())


def sha(body):
    return hashlib.sha256(body).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


@contextmanager
def no_network():
    old = socket.socket.connect
    def reject(*args, **kwargs):
        raise RuntimeError('R12_NETWORK_DISABLED_NO_ACQUISITION')
    socket.socket.connect = reject
    try:
        yield
    finally:
        socket.socket.connect = old


class Observer:
    """Report empty control-flow outcomes, not invented empirical failure counts."""
    def __init__(self):
        self.files = {str(ROOT / 'db/scripts' / name): name for name in MODULES}
        self.events = Counter()
        self.lines = Counter()
        self.mapping = Counter()
        self.rules = Counter()
        self.forms = set()
        self.context = 'NOT_SET'
        self.context_events = Counter()

    def trace(self, frame, event, arg):
        if frame.f_code.co_filename not in self.files:
            return None
        file = self.files[frame.f_code.co_filename]
        line = frame.f_lineno
        function = frame.f_code.co_name
        if event == 'line':
            self.lines[(file, line)] += 1
        kind = None
        if event == 'exception':
            kind = 'EXCEPTION_OBSERVED:' + arg[0].__name__
        elif event == 'return':
            if arg is None or isinstance(arg, (list, dict, tuple, str)) and not arg:
                kind = 'EMPTY_RETURN_OBSERVED'
            if function == 'resolve_surface' and isinstance(arg, dict):
                self.mapping[arg.get('mapping_status', 'MISSING_STATUS')] += 1
                self.forms.add(extract.norm(frame.f_locals['surface']))
                if arg.get('rule_id'):
                    self.rules[arg['rule_id']] += 1
        if kind:
            code = f'{file}:{line}:{function}:{kind}'
            self.events[code] += 1
            self.context_events[(self.context, code)] += 1
        return self.trace

    @contextmanager
    def observe(self, context):
        previous = sys.gettrace()
        previous_context = self.context
        self.context = context
        sys.settrace(self.trace)
        try:
            yield
        finally:
            sys.settrace(previous)
            self.context = previous_context


def cache_body(receipt, cache):
    if not receipt or not receipt.get('requested_url'):
        return None, 'HISTORICAL_RETRIEVAL_TELEMETRY_MISSING'
    path = cache / (sha(receipt['requested_url'].encode()) + '.body')
    if not path.exists():
        return None, 'CACHE_MISSING_NOT_ZERO_TABLES'
    body = path.read_bytes()
    if sha(body) != receipt['sha256']:
        raise ValueError('CACHE_CHECKSUM_MISMATCH:' + str(path))
    return body, 'CHECKSUM_VERIFIED'


def parse_baseline(body, receipt):
    if receipt['content_type'] in {'text/xml', 'application/xml'} or body.lstrip().startswith(b'<?xml'):
        return extract.parse_xml(body)
    if receipt['content_type'] == 'text/html':
        return extract.parse_html(body)
    raise ValueError('UNSUPPORTED_BASELINE_PRIMARY_CONTENT_TYPE:' + receipt['content_type'])


def classify(candidate, outcome, table, plain, direct, rules):
    rows = stratify.ontology_records(candidate, outcome, table, direct, rules)
    rows.extend(stratify.sample_axis_records(candidate, outcome, table, plain, direct, rules))
    return list({row['record_id']: row for row in rows}.values())


def replay(candidates, outcomes, cache, observer):
    direct, rules = stratify.load_direct_registry()
    traces, all_rows = [], {}
    for candidate in candidates:
        cid = candidate['candidate_id']
        outcome = outcomes[cid]
        receipt = outcome.get('retrieval')
        historical_reason = outcome.get('failure_reason')
        fetch_failed = (historical_reason or '').startswith('FULL_TEXT_RETRIEVAL_FAILED')
        trace = {
            'candidate_id': cid, 'query_ids': candidate['query_ids'],
            'query_hit': True,
            'oa_location_resolved': True if receipt else None,
            'oa_metadata': {'source_record_id': candidate['source_record_id'],
                            'license_source_url': candidate.get('license_source_url'),
                            'note': 'OA discovery metadata is not proof of a working full-text location.'},
            'fetch_attempted': True if receipt else None,
            'fetch_succeeded': True if receipt else False if fetch_failed else None,
            'historical_retrieval': receipt,
            'historical_reason': historical_reason,
            'historical_failure_detail': outcome.get('failure_detail'),
            'alternative_location_attempted': None,
            'document_parsed': None, 'tables_detected_before_classification': None,
            'tables': [], 'mapping_applied': False, 'gate_evaluated': False,
            'typed_rows': 0, 'admitted': False,
        }
        body, cache_status = cache_body(receipt, cache)
        trace['cache_status'] = cache_status
        trace['terminal_reason'] = historical_reason or cache_status
        if body is not None:
            with observer.observe(cid):
                try:
                    tables, metadata = parse_baseline(body, receipt)
                    trace['document_parsed'] = True
                    trace['tables_detected_before_classification'] = len(tables)
                except Exception as error:
                    trace['document_parsed'] = False
                    trace['terminal_reason'] = 'PARSE_OR_DISPATCH_FAILED:' + type(error).__name__
                    trace['parse_error'] = str(error)[:400]
                    traces.append(trace)
                    continue
                # Detect before frozen rights gate; never re-resolve rights or admit rejected sources.
                for index, table in enumerate(tables):
                    entry = {'table_id': table['table_id'], 'table_index': index,
                             'row_count': len(table['rows']), 'shapes': [],
                             'mapping_calls': 0, 'mapping_rule_matches': 0}
                    if not outcome.get('source_verified_license'):
                        entry['terminal_reason'] = 'SKIPPED_FROZEN_LICENSE_GATE'
                    else:
                        before = sum(observer.mapping.values())
                        mapped_before = observer.mapping['MAPPED']
                        trace['gate_evaluated'] = True
                        try:
                            with observer.observe(f'{cid}/table:{index}:{table["table_id"]}'):
                                produced = classify(candidate, outcome, table, metadata['plain_text'], direct, rules)
                            entry['shapes'] = sorted({row['shape_id'] for row in produced})
                            entry['typed_rows'] = len(produced)
                            entry['terminal_reason'] = 'TYPED' if produced else 'UNCLASSIFIED_EXPLICIT_EMPTY'
                            all_rows.update({row['record_id']: row for row in produced})
                            trace['typed_rows'] += len(produced)
                        except Exception as error:
                            entry['terminal_reason'] = 'CLASSIFICATION_EXCEPTION:' + type(error).__name__
                        entry['mapping_calls'] = sum(observer.mapping.values()) - before
                        entry['mapping_rule_matches'] = observer.mapping['MAPPED'] - mapped_before
                    trace['tables'].append(entry)
                trace['mapping_applied'] = any(t['mapping_calls'] for t in trace['tables'])
                trace['admitted'] = trace['typed_rows'] > 0
                trace['terminal_reason'] = ('TYPED_RECORDS_RECOVERED' if trace['admitted'] else
                    'SKIPPED_FROZEN_LICENSE_GATE' if not outcome.get('source_verified_license') else
                    'NO_TABLES_DETECTED' if not tables else 'TABLES_PRESENT_NONE_CLASSIFIED')
        traces.append(trace)
    return traces, list(all_rows.values())


def magic(body):
    if body.startswith(b'PK'):
        return 'ZIP_CONTAINER'
    if body.startswith(b'%PDF'):
        return 'PDF'
    if body.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        return 'OLE_COMPOUND'
    if body.startswith(b'\xff\xd8'):
        return 'JPEG'
    if body.startswith(b'GIF8'):
        return 'GIF'
    if body.startswith(b'\x89PNG'):
        return 'PNG'
    head = body.lstrip()[:200].lower()
    if b'<html' in head or b'<!doctype html' in head:
        return 'HTML'
    if head.startswith(b'<?xml'):
        return 'XML_DECLARATION'
    return 'UNDETERMINED_NO_MIME_GUESS'


SUPPORTED = {'.xlsx', '.csv', '.tsv', '.txt', '.xml', '.nxml', '.html', '.htm'}


def audit_supplements(cache, observer):
    result = []
    for outcome in read(R11 / 'supplement_recovery.json')['candidate_outcomes']:
        receipt = outcome.get('retrieval')
        body, status = cache_body(receipt, cache)
        row = {'candidate_id': outcome['candidate_id'], 'endpoint': outcome['endpoint'],
               'endpoint_extension': Path(outcome['endpoint']).suffix,
               'retrieval': receipt, 'cache_status': status, 'members': [],
               'legacy_status': outcome['status'], 'historical_failure_detail': outcome.get('detail')}
        if body is not None:
            row.update(bytes=len(body), magic=magic(body), is_zip=zipfile.is_zipfile(BytesIO(body)))
            if row['is_zip']:
                with zipfile.ZipFile(BytesIO(body)) as archive:
                    for info in archive.infolist():
                        if info.is_dir():
                            continue
                        suffix = Path(info.filename).suffix.lower()
                        member = {'name': info.filename, 'extension': suffix,
                                  'bytes': info.file_size, 'content_type': None,
                                  'mime_note': 'ZIP member has no HTTP Content-Type.',
                                  'parser_exists': suffix in SUPPORTED,
                                  'tables_detected': None}
                        if info.file_size > supplements.MEMBER_LIMIT:
                            member['reason'] = 'MEMBER_SIZE_LIMIT_RESPECTED'
                        else:
                            with observer.observe('supplement:' + outcome['candidate_id']):
                                try:
                                    data = archive.read(info)
                                    member.update(sha256=sha(data), magic=magic(data))
                                    if suffix == '.zip' and zipfile.is_zipfile(BytesIO(data)):
                                        with zipfile.ZipFile(BytesIO(data)) as nested:
                                            member['nested_members_inventory_only'] = [
                                                {'name': item.filename, 'bytes': item.file_size,
                                                 'extension': Path(item.filename).suffix.lower(),
                                                 'legacy_parser_dispatch_reached': False}
                                                for item in nested.infolist() if not item.is_dir()]
                                    if suffix in SUPPORTED:
                                        tables = supplements.tabular_members(info.filename, data)
                                        member['tables_detected'] = len(tables)
                                        member['reason'] = 'PARSED_TABLES' if tables else 'PARSER_RETURNED_EMPTY'
                                    else:
                                        member['reason'] = 'UNSUPPORTED_MEMBER_TYPE_NOT_EMPIRICAL_ZERO'
                                except Exception as error:
                                    member['reason'] = 'MEMBER_PARSE_EXCEPTION:' + type(error).__name__
                        row['members'].append(member)
            else:
                row['reason'] = 'NON_ZIP_RESPONSE_NOT_PARSED_AS_TABLE'
        result.append(row)
    return result


def synthetic_checks():
    """Software counterexamples only, deliberately excluded from corpus counts."""
    direct, rules = stratify.load_direct_registry()
    candidate = {'candidate_id': 'SYNTHETIC', 'doi': 'synthetic:test',
                 'title': 'Coffee sensory analysis', 'source_system': 'SYNTHETIC', 'source_record_id': 'TEST'}
    outcome = {'retrieval': {'final_url': 'synthetic:test', 'sha256': 'SYNTHETIC'},
               'source_verified_license': 'SYNTHETIC_NOT_CORPUS'}
    def run(rows, caption='Sensory descriptors', label='Table 1'):
        table = {'table_id': 'test', 'label': label, 'caption': caption, 'rows': rows}
        return stratify.sample_axis_records(candidate, outcome, table, 'Coffee trained panel of 8 assessors.', direct, rules)
    numeric = [['Sample', 'Lemon', 'Honey'], ['Lot Alpha', '2', '3'], ['Lot Beta', '3', '4']]
    binary = [['Descriptor', 'Lot Alpha', 'Lot Beta'], ['Lemon', 'present', 'yes'], ['Honey', 'yes', 'present']]
    listed = [['Sample', 'Significant sensory descriptors'], ['Lot Alpha', 'lemon, honey'], ['Lot Beta', 'lemon, honey']]
    tests = {
        'numeric_named': run(numeric), 'binary_presence': run(binary),
        'explicit_sample_descriptor_list': run(listed),
        'same_numeric_table_filename_caption': run(numeric, 'Supplement1.xlsx#Sheet1', 'Supplement1.xlsx#Sheet1'),
    }
    return {'synthetic_only': True, 'counts_not_corpus_or_recall': True,
            'cases': {key: {'typed_rows': len(rows), 'shapes': dict(Counter(x['shape_id'] for x in rows))}
                      for key, rows in tests.items()},
            'conclusion': 'T3 binary cells are implemented before T1; explicit sample descriptor lists are not. Filename-only captions can suppress otherwise identical numeric tables.'}


def static_sweep(observer):
    sites = []
    for name in MODULES:
        path = ROOT / 'db/scripts' / name
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            kind = None
            if isinstance(node, ast.ExceptHandler):
                kind = 'EXCEPTION_HANDLER'
            elif isinstance(node, ast.Return):
                kind = 'RETURN_REQUIRES_EMPTY_VISIBILITY'
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'get':
                kind = 'DEFAULT_LOOKUP_SCHEMA_RISK'
            elif isinstance(node, ast.Continue):
                kind = 'CONTINUE_REQUIRES_SKIP_VISIBILITY'
            if kind:
                executed = observer.lines[(name, node.lineno)]
                observed = {k: v for k, v in observer.events.items() if k.startswith(f'{name}:{node.lineno}:')}
                handler_disposition = None
                if isinstance(node, ast.ExceptHandler):
                    strings = ' '.join(n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str))
                    handler_disposition = ('RAISE_OR_RETRY' if any(isinstance(n, ast.Raise) for n in ast.walk(node)) else
                        'EXISTING_TYPED_FAILURE_RECORD' if re.search(r'FAILED|ERROR|failure_reason|error|INVALID', strings) else
                        'SILENT_FALLBACK_BASELINE_REQUIRES_OBSERVER')
                sites.append({'file': str(path.relative_to(ROOT)), 'line': node.lineno, 'kind': kind,
                              'source': ast.get_source_segment(source, node)[:240],
                              'legacy_handler_disposition': handler_disposition,
                              'executed_line_count': executed, 'observed_events': observed,
                              'disposition': 'OBSERVED_TYPED_RUNTIME_EVENT' if observed else
                              'EXECUTED_SITE_REQUIRES_MANUAL_CLASSIFICATION' if executed else
                              'NOT_EXECUTED_LEGACY_SITE_REMAINS_UNVERIFIED'})
    return {'scope': MODULES, 'sites': sites,
            'site_kind_counts': dict(Counter(x['kind'] for x in sites)),
            'exception_handler_dispositions': dict(Counter(x['legacy_handler_disposition'] for x in sites if x['legacy_handler_disposition'])),
            'runtime_typed_events': dict(sorted(observer.events.items())),
            'disposition_counts': dict(Counter(x['disposition'] for x in sites)),
            'complete_remediation': False,
            'limitations': 'Conservative AST inventory includes intentional normal returns and defaults; it is not a count of bugs. Cached replay logs exceptions and empty returns without changing baseline. Unexecuted retrieval handlers and implicit schema fallbacks are not claimed repaired; a separate instrumented implementation remains necessary before future acquisition.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--primary-cache', type=Path, default=Path('/private/tmp/coffee-flavor-r11-fulltext-cache'))
    parser.add_argument('--supplement-cache', type=Path, default=Path('/private/tmp/coffee-flavor-r11-supplement-cache'))
    args = parser.parse_args()
    candidates = read(REVISIONS / 'r10/acquisition_manifest.json')['discovery_candidates']
    raw = read(R11 / 'extraction_report.json')
    outcomes = {x['candidate_id']: x for x in raw['candidate_outcomes']}
    assert len(outcomes) == len(candidates) == len({c['candidate_id'] for c in candidates}) == 248
    protected = {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in R11.glob('*.json')}
    private_corpus_hash = sha(finalizer.PRIVATE_R10.read_bytes()) if finalizer.PRIVATE_R10.exists() else None
    for name in MODULES:
        path = ROOT / 'db/scripts' / name
        relative = str(path.relative_to(ROOT))
        baseline = subprocess.check_output(['git', 'show', BASELINE + ':' + relative], cwd=ROOT)
        assert baseline == path.read_bytes(), 'LEGACY_SOURCE_CHANGED:' + name
        protected[relative] = sha(baseline)
    control_path = R12 / 'control_set.json'
    committed = subprocess.check_output(['git', 'show', 'HEAD:' + str(control_path.relative_to(ROOT))], cwd=ROOT)
    assert committed == control_path.read_bytes(), 'CONTROL_FIXTURE_MUST_BE_COMMITTED_FIRST'
    controls = read(control_path)
    if controls['positive_controls'] or controls['negative_controls']:
        raise ValueError('Human controls require a separately reviewed, group-aligned formal run; this entrypoint is cache diagnostic only.')
    observer = Observer()
    with no_network():
        traces, rows = replay(candidates, outcomes, args.primary_cache, observer)
        primary_mapping = dict(observer.mapping)
        primary_rules = dict(observer.rules)
        primary_forms = len(observer.forms)
        supplement_rows = audit_supplements(args.supplement_cache, observer)
        synthetic = synthetic_checks()
    sweep = static_sweep(observer)
    for relative, expected in protected.items():
        assert sha((ROOT / relative).read_bytes()) == expected, relative
    if private_corpus_hash:
        assert sha(finalizer.PRIVATE_R10.read_bytes()) == private_corpus_hash
    table_rows = [t for c in traces for t in c['tables']]
    frozen_primary = [x for x in read(R11 / 'shape_distribution.json')['records']
                      if x.get('r11_acquisition_stream') == 'R10_248_PRIMARY']
    frozen_ids = {x['record_id'] for x in frozen_primary}
    replay_ids = {x['record_id'] for x in rows}
    frozen_content = {x['record_id']: {k: v for k, v in x.items() if k != 'r11_acquisition_stream'} for x in frozen_primary}
    replay_content = {x['record_id']: x for x in rows}
    # Read-only demonstration: do not execute finalizer.main(), which writes R11.
    recombined, recombined_receipt = finalizer.combined_outputs(
        read(R11 / 'shape_distribution.json'), read(R11 / 'supplement_recovery.json'),
        read(R11 / 'targeted_acquisition.json'))
    original_streams = {x['record_id']: x['r11_acquisition_stream'] for x in read(R11 / 'shape_distribution.json')['records']}
    changed_stream_count = sum(x['r11_acquisition_stream'] != original_streams[x['record_id']] for x in recombined)
    summary = {
        'candidates': len(traces),
        'historical_raw_tables_scanned': sum(x.get('tables_scanned', 0) for x in outcomes.values()),
        'tables_detected_cache_replay': sum(c['tables_detected_before_classification'] or 0 for c in traces),
        'documents_unknown_table_count': sum(c['tables_detected_before_classification'] is None for c in traces),
        'documents_parsed': sum(c['document_parsed'] is True for c in traces),
        'tables_classified': sum(bool(t['shapes']) for t in table_rows),
        'tables_unclassified': sum(not t['shapes'] for t in table_rows),
        'tables_by_shape': dict(Counter(shape for t in table_rows for shape in t['shapes'])),
        'shape_table_count_note': 'Per-shape table counts overlap; one table can yield multiple types.',
        'typed_rows': len(rows), 'rows_by_shape': dict(Counter(x['shape_id'] for x in rows)),
        'candidate_terminal_counts': dict(Counter(c['terminal_reason'] for c in traces)),
        'mapping_call_counts': primary_mapping, 'distinct_normalized_surfaces_presented': primary_forms,
        'rules_fired': primary_rules, 'unique_rules_fired': len(primary_rules),
        'frozen_primary_ids_equal': replay_ids == frozen_ids,
        'frozen_primary_content_equal': replay_content == frozen_content,
        'frozen_primary_id_count': len(frozen_ids),
        'added_ids': len(replay_ids - frozen_ids), 'missing_ids': len(frozen_ids - replay_ids),
    }
    for stage in ['oa_location_resolved', 'fetch_attempted', 'fetch_succeeded', 'document_parsed', 'mapping_applied', 'gate_evaluated', 'admitted']:
        summary[stage] = dict(Counter('UNKNOWN' if c[stage] is None else 'YES' if c[stage] else 'NO' for c in traces))
    retrieval_failures = [c for c in traces if (c['historical_reason'] or '').startswith('FULL_TEXT_RETRIEVAL_FAILED')]
    failure_audits = []
    for c in retrieval_failures:
        detail = c['historical_failure_detail'] or ''
        match = re.search(r'HTTP Error (\d{3})', detail)
        status = int(match[1]) if match else None
        failure_audits.append({'candidate_id': c['candidate_id'], 'reason': c['historical_reason'],
            'failure_detail': detail, 'http_status': status, 'http_status_basis': 'HISTORICAL_ERROR_STRING' if status else 'NOT_RECORDED',
            'final_url': None, 'oa_location_existed': None, 'alternative_attempted': None,
            'classification': 'ACCESS_DENIED_RESPECTED' if status in {401, 403, 429} else
                'HTTP_NOT_FOUND_CAUSE_UNRESOLVED' if status == 404 else
                'ENDPOINT_RESOLUTION_EXHAUSTED_ATTEMPT_DETAILS_UNRECORDED' if detail == 'NO_RETRIEVABLE_FULL_TEXT_ENDPOINT' else
                'UNKNOWN_MISSING_ERROR_TELEMETRY'})
    member_rows = [m for r in supplement_rows for m in r['members']]
    common = {'baseline_commit': BASELINE, 'fit_count': 0, 'real_label_model_metric_count': 0,
              'new_candidate_count': 0, 'network_calls_allowed': False,
              'protected_file_hashes_unchanged': protected, 'control_fixture_sha256': sha(committed)}
    common['private_r10_training_corpus_sha256_unchanged'] = private_corpus_hash
    save(R12 / 'funnel_counts.json', common | {
        'summary': summary, 'candidates': traces,
        'runtime_typed_event_counts': dict(sorted(observer.events.items())),
        'event_contexts': [{'context': c, 'event': e, 'count': n} for (c, e), n in sorted(observer.context_events.items())],
        'interpretation': 'Classification replay of checksum-verified historical bodies, not fresh retrieval. Unknown historical stages are explicit. Admitted means legacy typed row, not human-validated coffee supervision; T5/T6 remain ontology only.'})
    save(R12 / 'anomaly_diagnosis.json', common | {
        'supplements': {'endpoints': len(supplement_rows), 'endpoint_audits': supplement_rows,
            'verified_zip_responses': sum(r.get('is_zip', False) for r in supplement_rows),
            'parsed_member_tables': sum(m['tables_detected'] or 0 for m in member_rows),
            'nested_member_extension_counts': dict(Counter(n['extension'] for m in member_rows for n in m.get('nested_members_inventory_only', []))),
            'member_extension_counts': dict(Counter(m['extension'] for m in member_rows)),
            'member_reason_counts': dict(Counter(m['reason'] for m in member_rows)),
            'support': {'.xlsx': 'OPENPYXL', '.xls': 'NOT_IMPLEMENTED', '.csv': 'CSV_READER',
                        '.docx': 'NOT_IMPLEMENTED', '.pdf': 'NOT_IMPLEMENTED', '.zip': 'TOP_LEVEL_ONLY_NO_NESTED_RECURSION'},
            'verdict': 'IMPLEMENTATION_GAPS_CONFIRMED; zero is not evidence of zero source data.'},
        't3': synthetic,
        'mapping': {'call_counts': primary_mapping, 'distinct_surfaces': primary_forms, 'rule_hits': primary_rules,
            'frozen_rule_count': len(stratify.load_direct_registry()[1]),
            'stage_order': 'caption/domain/consumer prefilters -> descriptor_axis/resolve_surface -> cell admission. Ontology resolver has a separate route.',
            'verdict': 'Mapping is reachable but downstream of prefilters; zero new named groups cannot prove a dead resolver.'},
        'retrieval': {'actual_retrieval_failure_count': len(retrieval_failures),
            'historical_failure_reason_counts': dict(Counter(x.get('failure_reason') or 'ADMITTED' for x in outcomes.values())),
            'failures': failure_audits,
            'static_findings': ['User-Agent and Accept headers exist; urllib handles ordinary redirects.',
                'Retries only selected HTTP errors, not general timeout/URLError.',
                'Crossref resolution occurs before using an already found PMC alternative.',
                'OpenAlex alternative attempts swallow exceptions without recording them.',
                'HTML/XML landing content can be accepted without checking full-text identity.',
                'XML declaration takes precedence over HTML MIME; XHTML can reach JATS XML parser.',
                'PDF may be selected although baseline has no PDF table parser.',
                '25 MB read cap has no truncation detection.'],
            'access_policy': 'Do not retry/bypass refusals in R12. Historical missing HTTP telemetry does not establish ACCESS_DENIED_RESPECTED or CLIENT_DEFECT for an individual failure.'},
        'reporting': '47 classified tables included targeted acquisition; compare raw detection and primary classification separately.',
        'finalizer_read_only_idempotence_probe': {
            'no_writes_to_r11': True, 'rows_with_changed_acquisition_stream_on_rerun': changed_stream_count,
            'recombined_receipt': recombined_receipt,
            'finding': 'main reads shape_distribution.json and writes its combined output back to the same file. A subsequent run relabels targeted rows as primary via first-wins setdefault. Historical file left unchanged.'},
        'verdict': 'Confirmed instrument defects invalidate scarcity inference from zeros; their population impact and overall recall remain NOT_EVALUATED.'})
    save(R12 / 'silent_failure_audit.json', common | sweep)
    save(R12 / 'recall_report.json', common | {
        'status': 'BLOCKED_HUMAN_VERIFIED_CONTROLS_REQUIRED',
        'human_verified_positive_count': len(controls['positive_controls']),
        'human_verified_negative_count': len(controls['negative_controls']),
        'positive_required': controls['positive_target'], 'negative_required': controls['negative_target'],
        'per_stage_recall': None, 'overall_recall': None, 'negative_false_positive_rate': None,
        'fixed_bands': controls['fixed_bands'], 'applied_band': 'NOT_EVALUATED',
        'formal_control_run_executed': False,
        'synthetic_software_checks': synthetic,
        'prior_scarcity_claim': 'NOT_VALIDATED_BY_R10_R11_MEASUREMENT_INSTRUMENT',
        'owner_decision': 'UNCHANGED_PENDING_OWNER_DECISION',
        'scale_inference': 'No inverse-recall expansion or bulk-corpus yield is estimated from unrepresentative or missing controls.'})
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
