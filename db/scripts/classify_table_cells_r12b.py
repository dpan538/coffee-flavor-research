"""Independent finite-rule cell-content reference, version 1.

No legacy imports, captions, original labels, or fitted parameters. Shared role
IDs are a declared semantic specification, not new ontology or ground truth.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
import re
import unicodedata

VERSION = 'r12b-cell-structure-1'
LABELS = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'unclassified']
NATIVE = {'acidity', 'sourness', 'body', 'bitterness', 'sweetness', 'aroma',
          'fragrance', 'flavor', 'flavour', 'aftertaste', 'balance', 'uniformity',
          'astringency', 'overall', 'quality', 'clean cup'}
NON_SAMPLE = {'descriptor', 'descriptors', 'attribute', 'attributes', 'sample',
              'samples', 'mean', 'sd', 'se', 'sem', 'p', 'p value', 'f value',
              'definition', 'reference', 'compound', 'compounds', 'cas', 'ri',
              'minimum', 'maximum', 'loading', 'correlation', 'coefficient',
              'r', 'r2', 'pc1', 'pc2', 'model', 'threshold', 'concentration',
              'odor', 'odour', 'description', 'formula', 'unit'}
CHEMICALS = {'caffeine', 'furfural', 'guaiacol', 'hexanal', 'linalool',
             'acetaldehyde', 'acetone', 'ethanol', 'acetic acid', 'vanillin',
             'phenol', 'limonene', 'eugenol', 'methional', 'hexanol'}


def words(value):
    text = unicodedata.normalize('NFKC', str(value)).casefold()
    return tuple(re.findall(r'[^\W_]+', text, flags=re.UNICODE))


def vocabulary(registry):
    result = {}
    for cid, item in registry.items():
        if item['role'] in {'NAMED_DESCRIPTOR', 'PROFILE_DIRECTION'}:
            # Parse the published identifier grammar; do not infer child terms.
            surface = cid.rsplit('.', 1)[-1].replace('_', ' ')
            result[words(surface)] = (cid, item['role'])
    return result


def number(value):
    text = unicodedata.normalize('NFKC', str(value)).strip().replace('−', '-')
    # Complete numeric cells, with an optional uncertainty or significance suffix.
    match = re.fullmatch(r'([+-]?(?:\d+(?:[.,]\d+)?|\.\d+))(?:\s*[±]\s*\d+(?:[.,]\d+)?)?\s*(%)?\s*(?:[a-f*]+)?', text)
    if not match:
        return None
    try:
        return float(Decimal(match[1].replace(',', '.'))), bool(match[2])
    except InvalidOperation:
        return None


def cell(value, lexicon):
    text = str(value).strip()
    key = words(text)
    numeric = number(text)
    if numeric is not None:
        return {'type': 'NUMERIC', 'value': numeric[0], 'percent': numeric[1]}
    if text.casefold() in {'x', '+', 'yes', 'present', 'significant', '✓'}:
        return {'type': 'PRESENCE'}
    if key in lexicon:
        cid, role = lexicon[key]
        return {'type': 'NAMED' if role == 'NAMED_DESCRIPTOR' else 'DIMENSION', 'id': cid}
    if ' '.join(key) in NATIVE:
        return {'type': 'DIMENSION'}
    pieces = [part.strip() for part in re.split(r'[,;\n•]+', text) if part.strip()]
    if len(pieces) >= 2 and all(words(part) in lexicon for part in pieces):
        return {'type': 'DESCRIPTOR_LIST', 'members': [lexicon[words(part)] for part in pieces]}
    if (re.fullmatch(r'\d{2,7}-\d{2}-\d', text) or text.casefold() in CHEMICALS or
            re.search(r'\b\d+[,-]\d*.*(?:pyrazine|furan|phenol|pentan|hexan|butan)', text, re.I)):
        return {'type': 'COMPOUND'}
    if not key:
        return {'type': 'EMPTY'}
    if len(key) >= 12 or (len(key) >= 7 and any(mark in text for mark in '.:')):
        return {'type': 'EXPLANATORY_PROSE'}
    if ' '.join(key) in NON_SAMPLE:
        return {'type': 'NON_SAMPLE'}
    # This is only a syntactic identifier hypothesis, not verified coffee identity.
    return {'type': 'IDENTIFIER_HYPOTHESIS'}


def classify(rows, registry):
    lexicon = vocabulary(registry)
    width = max((len(row) for row in rows), default=0)
    grid = [list(row) + [''] * (width - len(row)) for row in rows]
    types = [[cell(value, lexicon) for value in row] for row in grid]
    supports = {label: set() for label in LABELS[:-1]}
    pair_evidence = []
    all_keys = {' '.join(words(value)) for row in grid for value in row}
    frequency_metadata = bool(all_keys & {'frequency', 'frequencies', 'count', 'counts', 'percentage', 'percent', 'citations'})
    ambiguities = set()
    for r, row in enumerate(types):
        for c, item in enumerate(row):
            if item['type'] == 'DESCRIPTOR_LIST':
                sample_cells = [(r, j) for j, other in enumerate(row) if other['type'] == 'IDENTIFIER_HYPOTHESIS']
                if sample_cells:
                    for cid, role in item['members']:
                        shape = 'T3' if role == 'NAMED_DESCRIPTOR' else 'T4'
                        supports[shape].add((r, c, cid))
                    pair_evidence.append({'value_cell': [r, c], 'sample_axis_cells': sample_cells, 'kind': 'LIST'})
            if item['type'] not in {'NUMERIC', 'PRESENCE'}:
                continue
            # Inspect both complete axes, rather than choosing a header location.
            row_descriptors = [(r, j, v) for j, v in enumerate(row) if v['type'] in {'NAMED', 'DIMENSION'}]
            column_descriptors = [(i, c, types[i][c]) for i in range(len(types)) if types[i][c]['type'] in {'NAMED', 'DIMENSION'}]
            row_samples = [(r, j) for j, v in enumerate(row) if v['type'] == 'IDENTIFIER_HYPOTHESIS']
            column_samples = [(i, c) for i in range(len(types)) if types[i][c]['type'] == 'IDENTIFIER_HYPOTHESIS']
            alternatives = [(row_descriptors, column_samples), (column_descriptors, row_samples)]
            for descriptors, samples in alternatives:
                if not descriptors or not samples:
                    continue
                for dr, dc, descriptor in descriptors:
                    shape = ('T4' if descriptor['type'] == 'DIMENSION' else 'T3' if item['type'] == 'PRESENCE' else
                             'T2' if item.get('percent') or frequency_metadata else 'T1')
                    supports[shape].add((r, c, descriptor.get('id', 'native')))
                    pair_evidence.append({'value_cell': [r, c], 'descriptor_cell': [dr, dc],
                                          'sample_axis_cells': samples, 'kind': shape})
                    if shape == 'T1':
                        ambiguities.add('NUMERIC_INTENSITY_VS_UNLABELLED_FREQUENCY_NOT_IDENTIFIABLE_FROM_CELL_ALONE')
    for r, row in enumerate(types):
        descriptors = [c for c, value in enumerate(row) if value['type'] in {'NAMED', 'DIMENSION', 'DESCRIPTOR_LIST'}]
        if descriptors and any(value['type'] == 'EXPLANATORY_PROSE' for value in row):
            supports['T5'].update((r, c, 'reference') for c in descriptors)
        if descriptors and any(value['type'] == 'COMPOUND' for value in row):
            supports['T6'].update((r, c, 'chemical') for c in descriptors)
    counts = {label: len(points) for label, points in supports.items() if points}
    chosen = min(counts, key=lambda label: (-counts[label], label)) if counts else 'unclassified'
    return {'label': chosen, 'labels': sorted(counts), 'supporting_cell_counts': counts,
            'cell_type_counts': dict(Counter(value['type'] for row in types for value in row)),
            'pairs': pair_evidence, 'ambiguities': sorted(ambiguities),
            'identity_warning': 'IDENTIFIER_HYPOTHESIS is not a validated coffee-sample identity; counterfactual groups need separate extraction and adjudication.'}


def confusion(pairs):
    matrix = [[0 for _ in LABELS] for _ in LABELS]
    for original, reference in pairs:
        matrix[LABELS.index(original)][LABELS.index(reference)] += 1
    n = len(pairs)
    row_totals = [sum(row) for row in matrix]
    col_totals = [sum(row[j] for row in matrix) for j in range(len(LABELS))]
    observed = sum(matrix[i][i] for i in range(len(LABELS))) / n if n else None
    expected = sum(a * b for a, b in zip(row_totals, col_totals)) / n**2 if n else None
    kappa = (observed - expected) / (1 - expected) if n and expected != 1 else None
    return {'labels': LABELS, 'matrix': matrix, 'n': n, 'original_marginals': row_totals,
            'reference_marginals': col_totals, 'observed_agreement': observed, 'kappa': kappa}
