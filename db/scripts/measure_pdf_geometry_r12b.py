#!/usr/bin/env python3
"""Pinned PDF word-geometry reference. No caption/header matching or fitting.

Calibration is written before target documents are measured. Semantic grid
detection is a proxy, not confirmation of coffee sample identities.
"""
from collections import Counter
from contextlib import redirect_stdout
import hashlib
import json
from pathlib import Path
import random
import re
import sys
import fitz

VERSION = 'r12b-pdf-word-geometry-1'
PIN = '1.27.2.2'
SENSORY = frozenset('acidity aroma body bitterness sweetness aftertaste balance astringency floral fruity lemon honey citrus chocolate caramel nutty roasted sourness vanilla berry'.split())
CONFIG = {'vertical_strategy': 'text', 'horizontal_strategy': 'text',
          'min_words_vertical': 3, 'min_words_horizontal': 1}


def inspect_page(document, page_number):
    page = document[page_number-1]
    finder = page.find_tables(**CONFIG)
    grids = []
    for table in finder.tables:
        cells = table.extract()
        numeric = sum(bool(re.search(r'(?<!\w)[+-]?\d+(?:[.,]\d+)?', value or '')) for row in cells for value in row)
        terms = sorted({token.strip('.,;:()[]').lower() for row in cells for value in row for token in (value or '').split()} & SENSORY)
        positive = table.row_count >= 3 and table.col_count >= 2 and numeric >= 4 and len(terms) >= 2
        grids.append({'bbox': list(table.bbox), 'rows': table.row_count, 'columns': table.col_count,
            'numeric_cell_count': numeric, 'sensory_terms': terms, 'positive': positive})
    return {'page_number': page_number, 'word_count': len(page.get_text('words')),
            'grids': grids, 'positive': any(g['positive'] for g in grids)}


def document_bootstrap(rows):
    if not rows:
        return None
    by_document = {}
    for row in rows:
        by_document.setdefault(row['candidate_id'], []).append(int(row['positive']))
    keys = sorted(by_document)
    rng = random.Random(120208)
    fractions = []
    for _ in range(2000):
        values = [value for key in rng.choices(keys, k=len(keys)) for value in by_document[key]]
        fractions.append(sum(values)/len(values))
    fractions.sort()
    return [fractions[49], fractions[1949]]


def run(request):
    if fitz.VersionBind != PIN:
        raise RuntimeError('PDF_LIBRARY_VERSION_MISMATCH')
    output = Path(request['output_dir'])
    rendered = {row['candidate_id']: row for row in request['rendered'] if row.get('status') == 'RENDERED_NOT_VISUALLY_ADJUDICATED'}
    cache = {}
    def measured(cid, page):
        key = (cid, page)
        if key not in cache:
            source = rendered[cid]
            path = Path(source['pdf_path'])
            if hashlib.sha256(path.read_bytes()).hexdigest() != source['pdf_sha256']:
                raise ValueError('RENDERED_PDF_CHECKSUM_MISMATCH')
            with fitz.open(path) as pdf:
                cache[key] = {'candidate_id': cid, 'modality': source['source_modality'], **inspect_page(pdf, page)}
        return cache[key]
    control_documents = {x['candidate_id'] for x in request['positive_table_ids']}
    positives, unmatched = set(), []
    for item in request['positive_table_ids']:
        source = rendered.get(item['candidate_id'])
        pages = [a['page'] for a in source['anchors'] if a['id'] == item['table_id']] if source else []
        if pages:
            positives.update((item['candidate_id'], p) for p in range(min(pages), max(pages)+1))
        else:
            unmatched.append(item)
    negative_pool, strict_negative_pool = [], []
    for cid in sorted(control_documents & rendered.keys()):
        source = rendered[cid]
        table_pages = set()
        for identity in source['all_table_anchor_ids']:
            pages = [a['page'] for a in source['anchors'] if a['id'] == identity]
            if pages:
                table_pages.update(range(min(pages), max(pages)+1))
        for page in source['pages']:
            if page['page_number'] not in table_pages and page.get('negative_section_marker_strict_v1'):
                strict_negative_pool.append((cid, page['page_number']))
            if page['page_number'] not in table_pages and page.get('negative_section_marker'):
                negative_pool.append((cid, page['page_number']))
    negatives = sorted(set(negative_pool)-positives)[:len(positives)]
    positive_rows = [measured(cid,p) for cid,p in sorted(positives)]
    negative_rows = [measured(cid,p) for cid,p in negatives]
    strict_negative_rows = [measured(cid,p) for cid,p in sorted(set(strict_negative_pool)-positives)[:len(positives)]]
    sensitivity = sum(r['positive'] for r in positive_rows)/len(positive_rows) if positive_rows else None
    false_positive = sum(r['positive'] for r in negative_rows)/len(negative_rows) if negative_rows else None
    s_band, f_band = document_bootstrap(positive_rows), document_bootstrap(negative_rows)
    calibration = request['common'] | {'version': VERSION, 'library_pin': {'PyMuPDF': PIN, 'MuPDF': fitz.VersionFitz},
        'python_version': sys.version, 'implementation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'config': CONFIG, 'sensory_cell_terms': sorted(SENSORY),
        'status': 'CALIBRATION_MEASURED_WITH_COVERAGE_LIMITATIONS' if unmatched or len(negatives)!=len(positives) else 'CALIBRATION_MEASURED',
        'positive_pages': positive_rows, 'negative_pages': negative_rows,
        'original_table_controls_requested': len(request['positive_table_ids']), 'unmatched_table_controls': unmatched,
        'positive_page_count': len(positives), 'negative_page_count': len(negatives),
        'strict_v1_negative_calibration': {'page_count':len(strict_negative_rows),
            'false_positive_rate':sum(r['positive'] for r in strict_negative_rows)/len(strict_negative_rows) if strict_negative_rows else None,
            'document_bootstrap_band':document_bootstrap(strict_negative_rows)},
        'negative_selection_amendment': 'After the first 33-page shortage was observed, section identification was corrected once to accept numbered section headings and standalone Methods. Geometry rules unchanged; original strict result retained. No pages were selected by their detector outcomes.',
        'equal_negative_requirement_met': len(positives)==len(negatives) and bool(positives),
        'sensitivity_relative_to_source_anchor_controls': sensitivity, 'false_positive_rate_relative_to_markup_negatives': false_positive,
        'document_cluster_bootstrap_s_band': s_band, 'document_cluster_bootstrap_f_band': f_band,
        'bootstrap_scope': '2000 fixed-seed document resamples, preserving all within-document page outcomes. These bands are conditional on markup controls, not ground-truth accuracy.',
        'native_pdf_calibration': 'NOT_ESTABLISHED_BY_REFLOWED_MARKUP_CONTROLS',
        'true_accuracy_identification_interval': [0,1],
        'negative_selection': 'Same source documents, reference/method section marker and no rendered source-table anchors. Missing graphics make these machine negatives imperfect.',
        'executed_before_target_measurement': True}
    (output/'tier2_calibration.json').write_text(json.dumps(calibration,indent=2,sort_keys=True)+'\n')
    # Deliberately after calibration receipt; shared calibration pages remain
    # labelled as overlap and are not independent held-out evaluation.
    results = []
    for item in request['inventory']:
        row = dict(item)
        if item['candidate_id'] not in rendered or not item['frozen_license_clear']:
            row.update(status='NOT_MEASURED_OUTSIDE_RENDERED_LICENSE_CLEAR_SCOPE', positive=None)
        else:
            source = rendered[item['candidate_id']]
            pages = [measured(item['candidate_id'], p['page_number']) for p in source['pages']]
            row.update(status='GEOMETRY_MEASURED_NOT_GROUND_TRUTH', positive=any(p['positive'] for p in pages),
                page_measurements=pages, calibration_document_overlap=item['candidate_id'] in control_documents,
                modality=source['source_modality'])
        results.append(row)
    valid = [r for r in results if r['positive'] is not None]
    positives_count = sum(r['positive'] for r in valid)
    # Calibration is page-level, outcomes are document-level. Applying s/f
    # directly to document counts would silently assume independent page errors.
    adjudication = request['common'] | {'version': VERSION, 'documents': results,
        'scope_counts':dict(Counter(r['original_class'] for r in results)),
        'rendering_audit':request['rendered'],
        'rendering_failure_count':sum(r.get('status')!='RENDERED_NOT_VISUALLY_ADJUDICATED' for r in request['rendered']),
        'measured_documents': len(valid), 'positive_document_count_relative_to_geometry': positives_count,
        'true_positive_document_identification_interval': [0,len(valid)],
        'held_license_clear_scope_identification_interval': [0,sum(r['held'] and r['frozen_license_clear'] for r in results)],
        'uncertainty_propagation': {'page_s_band': s_band, 'page_f_band': f_band,
            'document_band': [0,len(valid)],
            'reason': 'Page sensitivity/FPR cannot be transported to document-any-positive outcomes without a page-dependence model; original PDF domain is also uncalibrated. No invented model is fitted.'},
        'rendered_documents': list(rendered.values()),
        'verdict_caveat': 'Grid positives are not confirmed coffee supervision. The measured calibration false-positive rate is recorded above; it and incomplete equal-sized negative controls weaken target findings. Reflow and missing graphics prevent transfer to original PDFs.'}
    (output/'tier2_adjudication.json').write_text(json.dumps(adjudication,indent=2,sort_keys=True)+'\n')
    return {'calibration_s': sensitivity, 'calibration_f': false_positive,
        's_band': s_band, 'f_band': f_band, 'positive_pages': len(positives), 'negative_pages': len(negatives),
        'unmatched_controls': len(unmatched), 'target_documents': len(valid), 'target_positive': positives_count}


if __name__ == '__main__':
    fitz.set_messages(stream=sys.stderr)
    with redirect_stdout(sys.stderr):
        result = run(json.load(sys.stdin))
    print(json.dumps(result))
