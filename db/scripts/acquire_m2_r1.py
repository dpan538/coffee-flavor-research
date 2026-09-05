#!/usr/bin/env python3
"""M2 r1 source adapters; private rows, explicit masks, conservative lot grouping.

No download is automatically a rights admission. Cached artifacts are checked
before parsing. Raw observations and derived matrices remain owner-private.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl
from lxml import etree

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / 'db/data/backend-sequential-model-v2/revisions/r1'
OWNER = Path.home() / 'Library/Application Support/Coffee Flavor Research'
OLD = OWNER / 'backend-sequential-model-v2'
PRIOR = OWNER / 'backend-model-20260905'
PRIVATE = OLD / 'revisions/r1'
SPLIT_SEED = 'M2_R1_D1_SPLIT_20260905'
ZENODO_FAMILY = 'family.zenodo_golovinsky_q_grader_dataset'
STATUS = {'OBSERVED', 'TRUE_ZERO', 'NOT_MEASURED', 'NOT_MENTIONED', 'NOT_APPLICABLE', 'UNPARSEABLE'}
SOURCE_DIGESTS = {
    'peru-full.xml': '5abfaf0e897a5f9a2a7825fadcdafaa059ba03ea166963fbaefd64bc233b90fc',
    'peru-attachment.zip': 'f5601020e583172d865ae9c040d3c18781a412fd43351e2c89164c36acc3409e',
    'liking-mono.xml': 'e823fdcd48b93c4e5500de3d75b5c154a7489297e5aab0fb6b3e5e64537fadd5',
    'mono-epmc-supp.zip': '3ed6655b9fd5c9d53e4c4a7967c566d56576bd90100d6589f44be8bd04b2a785',
    'metabolomics47.xml': '8ffc1050f47b78dfaf28f479b8f960e768e566ef7852a21ec496abb437533c95',
    'metabolomics47.zip': '0ed657b2b2a8cbdde5dd50b1cf0dcaab9f89412d33dff9243e23e75b8f1b36bb',
    'cotter-original-cache.csv': '931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114',
    'cotter-original-cache-README.txt': 'f6d8f508bad2824a27be8785c841e8df4c75751b58726820f9e3dd226fe3fb5e',
    'cotter-mirror-rows.csv': '8f3f5a93f88f4669cb02dd9e15175673d23e4f1c4e99308689215414665bad03',
    'cotter-mirror-license.txt': '5ebb130faa15eb8b910a3a328cab96e6ef6ea17dfd3fa38c4f03794901901d0e',
    'cotter-api.json': '65b1b9b12a8e22f5c336a01486e95bfcb3d9ea1f4c5f5f7d42e60fcdf16f58fb',
}


def digest(b):
    return hashlib.sha256(b).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    if PUBLIC not in path.parents:
        path.chmod(0o600)


def split(group):
    h = digest((SPLIT_SEED + '|' + group).encode())
    return 'CONFIRMATION' if int(h[:8], 16) % 5 == 0 else 'DEVELOPMENT'


def normalize(s):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', str(s)).strip().casefold())


def fixed_terms():
    # Existing project vocabulary, never a newly scraped source vocabulary.
    from flavor_backend import BASE_CANDIDATES
    mapping = {x.split('.', 1)[1].replace('_', ' '): x for x in BASE_CANDIDATES}
    for word, target in list(mapping.items()):
        if ' ' not in word:
            mapping[word + 's'] = target
    mapping.update({'berries': 'attribute.fruity', 'fruits': 'attribute.fruity',
                    'fruity': 'attribute.fruity', 'flowers': 'attribute.floral',
                    'floral': 'attribute.floral', 'nuts': 'broad.nutty',
                    'nut': 'broad.nutty', 'nutty': 'broad.nutty',
                    'chocolate': 'broad.chocolate', 'citrus': 'broad.citrus',
                    'spices': 'attribute.spices', 'green vegetative': 'attribute.green_vegetative',
                    'raspberries': 'sensory.raspberry', 'blueberries': 'sensory.blueberry',
                    'blackberries': 'sensory.blackberry', 'strawberries': 'sensory.strawberry',
                    'cherries': 'sensory.cherry', 'peaches': 'sensory.peach',
                    'raisins': 'sensory.raisin', 'prunes': 'sensory.prune'})
    return mapping


SPANISH_EXACT = {
    'manzana': 'sensory.apple', 'naranja': 'sensory.orange', 'limón': 'sensory.lemon',
    'ciruela': 'sensory.plum', 'durazno': 'sensory.peach', 'uva': 'sensory.grape',
    'uvas': 'sensory.grape', 'mango': 'sensory.mango', 'piña': 'sensory.pineapple',
    'cerezas': 'sensory.cherry', 'moras': 'sensory.blackberry',
    'arándanos': 'sensory.blueberry', 'arandanos': 'sensory.blueberry',
    'toronja': 'sensory.grapefruit', 'pasas': 'sensory.raisin',
    'guindones': 'sensory.prune', 'miel': 'sensory.honey', 'caramelo': 'sensory.caramel',
    'melaza': 'sensory.molasses', 'vainilla': 'sensory.vanilla',
    'azúcar morena': 'sensory.brown_sugar', 'almendra': 'sensory.almond',
    'almendras': 'sensory.almond', 'avellanas': 'sensory.hazelnut', 'avellana': 'sensory.hazelnut',
    'maní': 'sensory.peanut', 'malta': 'sensory.malt', 'canela': 'sensory.cinnamon',
    'cedro': 'sensory.cedar', 'madera': 'sensory.woody', 'manzanilla': 'sensory.chamomile',
    'te verde': 'sensory.green_tea', 'té verde': 'sensory.green_tea',
    'te negro': 'sensory.black_tea', 'té negro': 'sensory.black_tea',
    'cocoa': 'sensory.cocoa', 'chocolate': 'broad.chocolate', 'floral': 'attribute.floral',
    'frutas': 'attribute.fruity', 'frutos rojos': 'attribute.fruity',
    'herbal': 'attribute.green_vegetative',
}
# English translations are project-authored exact lexical mappings. Modified,
# compound and context-dependent phrases are retained unmatched, never silently
# converted into exact leaf truth. Spanish 'dulce' is not sweet-aroma evidence.


def parse_terms(raw, language='en'):
    mapping = SPANISH_EXACT if language == 'es' else fixed_terms()
    found, excluded = set(), []
    for phrase in re.split(r'[,;\n.]', str(raw or '')):
        term = normalize(phrase)
        if language == 'es':
            term = re.sub(r'^(?:notas?\s+(?:a\s+|de\s+)?|base\s+(?:de\s+)?|fondo\s+(?:a\s+|de\s+)?)', '', term)
        if not term:
            continue
        if term in mapping:
            found.add(mapping[term])
        else:
            excluded.append(term)
    return sorted(found), excluded


def measurement(value, scale, meaning, status=None, source_value=None):
    state = status or ('TRUE_ZERO' if value == 0 else 'OBSERVED')
    assert state in STATUS
    assert (value is not None) == (state in {'OBSERVED', 'TRUE_ZERO'})
    return {'value': value, 'status': state, 'scale': scale, 'meaning': meaning,
            'source_value': value if source_value is None else source_value}


def ordinal(raw, meaning):
    levels = ['low', 'below middle', 'middle', 'above middle', 'high']
    s = normalize(raw) if raw is not None else ''
    scale = {'type': 'ordinal', 'ordered_levels': levels, 'numeric_encoding': 'rank 0..4; not interval intensity',
             'zero_means_absence': False}
    if s in levels:
        # The lowest ordinal rank is an observed low value, not sensory zero.
        return measurement(levels.index(s), scale, meaning, 'OBSERVED', raw)
    status = 'NOT_MEASURED' if s in {'', '.', '-'} else 'UNPARSEABLE'
    return measurement(None, scale, meaning, status, raw)


def zenodo_views(owner=PRIVATE):
    source = PRIOR / 'sources/zenodo-panelists.xlsx'
    expected = '85df699ea18f5849ef3104100a20570d5df13e7d6cc7ce53e20c3df8a5219150'
    assert digest(source.read_bytes()) == expected
    meta = json.loads((PRIOR / 'sources/zenodo-metadata.json').read_text())
    assert meta['metadata']['license']['id'] == 'cc-by-4.0'
    assert 'Non-commercial research only' in meta['metadata']['description']
    old = json.loads((OLD / 'recovery_records.json').read_text())
    old_groups = {r['group_id']: r['split'] for r in old}
    cells = list(openpyxl.load_workbook(source, read_only=True, data_only=True)['All Panelists'].values)
    names = defaultdict(set)
    for row in cells[2:]:
        if row[2]:
            names[str(row[0])].add(normalize(row[2]))
    assert all(len(v) == 1 for v in names.values())
    observations, grouped = [], defaultdict(list)
    for rn, row in enumerate(cells[2:], 3):
        if row[0] is None or row[1] is None:
            continue
        sid = str(row[0])
        name = next(iter(names.get(sid, set())), None)
        gid = ('coffee-group:' + digest((ZENODO_FAMILY + '|' + name).encode())[:24]
               if name else 'zenodo:UNRESOLVED_ANONYMOUS_LOTS')
        terms, unmatched = set(), []
        for col in [4, 6, 8, 10, 13, 16, 19]:
            t, u = parse_terms(row[col]); terms.update(t); unmatched.extend(u)
        values = {key: ordinal(row[col], meaning) for col, key, meaning in [
            (11, 'native.acidity_intensity', 'source acidity intensity; not acidity quality score'),
            (14, 'taste.sweetness', 'sweetness intensity; separate from sweet-associated aroma'),
            (17, 'taste.bitterness', 'bitterness intensity; separate from quality')
        ]}
        rec = {
            'record_id': 'zenodo:r1:panel-row:' + str(rn), 'source_family': 'zenodo',
            'sample_id': sid, 'group_id': gid, 'evaluation_group': gid,
            'evidence_unit_ids': ['zenodo:20840464:All Panelists:row:' + str(rn)],
            'targets': sorted(terms), 'relevance': {t: 1 for t in terms},
            'attribute_measurements': values, 'unmapped_source_phrases': unmatched,
            'source_C0': None, 'source_C1': None, 'source_native_C1_historical': row[3],
            'role': 'CORE_PROFESSIONAL', 'supervision': 'INCOMPLETE_POSITIVE_DESCRIPTIONS_AND_SEPARATE_ORDINAL_INTENSITIES',
            'split': old_groups.get(gid, 'QUARANTINED_UNKNOWN_LOT_OVERLAP'),
            'lot_identity_status': 'D0_KNOWN_GROUP' if name else 'UNKNOWN_POSSIBLE_D0_OVERLAP',
            'task_masks': {'attribute': True, 'leaf_recovery': bool(terms),
                           'core_d0_comparison': name is not None, 'new_confirmation': False},
            'proxy_status': 'DERIVED_RECORD_PROXY', 'missing_descriptor_status': 'NOT_MENTIONED',
        }
        observations.append(rec); grouped[sid].append(rec)
    aggregate = []
    for sid, records in sorted(grouped.items(), key=lambda x: int(x[0])):
        base = {k: v for k, v in records[0].items() if k != 'attribute_measurements'}
        mentions = Counter(t for r in records for t in r['targets'])
        values = {}
        for key in records[0]['attribute_measurements']:
            original = [r['attribute_measurements'][key] for r in records]
            known = [r['value'] for r in original if r['value'] is not None]
            values[key] = {'panelist_measurements': original, 'n_measured': len(known),
                           'ordinal_distribution': [known.count(k) for k in range(5)],
                           'numeric_summary_type': 'ordinal distribution only; no asserted interval mean'}
        aggregate.append({**base, 'record_id': 'zenodo:r1:sample:' + sid,
                          'targets': sorted(mentions), 'relevance': dict(mentions),
                          'panelist_mention_sets': [r['targets'] for r in records],
                          'attribute_distributions': values,
                          'evidence_unit_ids': [e for r in records for e in r['evidence_unit_ids']],
                          'panelist_observation_count': len(records)})
    save(owner / 'zenodo_attribute_observations.private.json', observations)
    save(owner / 'zenodo_attribute_samples.private.json', aggregate)
    anonymous = [r for r in aggregate if r['lot_identity_status'].startswith('UNKNOWN')]
    save(owner / 'd1_quarantined_records.private.json', anonymous)
    known = [r for r in observations if not r['lot_identity_status'].startswith('UNKNOWN')]
    return {'raw_rows': len(cells) - 2, 'panelist_observations': len(observations),
            'source_sample_ids': len(grouped), 'd0_known_groups': len({r['group_id'] for r in known}),
            'd0_new_attribute_observations': len(known), 'anonymous_source_sample_ids': len(anonymous),
            'anonymous_panelist_observations': sum(r['panelist_observation_count'] for r in anonymous),
            'proven_new_independent_lots': 0, 'strict_D0_D1_comparison_admission': False,
            'reason': 'Anonymous sample IDs are real, but identity overlap with D0 coffee names cannot be excluded.',
            'artifact_sha256': expected}


def peru_records(owner=PRIVATE):
    root = owner / 'sources'
    xml = etree.parse(str(root / 'peru-full.xml'))
    links = xml.xpath('//permissions//@*[contains(.,"creativecommons")]')
    assert any('by/4.0' in v for v in links)
    z = zipfile.ZipFile(root / 'peru-attachment.zip')
    content = z.read('File S1. Sensory Evaluation Results.xlsx')
    w = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    rows = list(w['Descriptors'].values)
    group = 'peru_2026:single_blend_lot'
    records, quality = [], []
    for ppc in range(8):
        for stage in range(5):
            rn = ppc * 10 + 4 + stage
            for ti, temp in enumerate([40, 50, 60]):
                day, score, raw = rows[rn][ti * 3:ti * 3 + 3]
                assert isinstance(raw, str) and isinstance(day, (int, float))
                if stage == 0 and ti > 0:
                    assert raw == rows[rn][2] and score == rows[rn][1]
                    continue  # Day zero was pasted across the three temperatures.
                condition = f'PPC_{chr(65 + ppc)}:' + ('baseline' if stage == 0 else f'{temp}C:day{int(day)}')
                targets, unmatched = parse_terms(raw, 'es')
                evidence = f'peru:FileS1:Descriptors:row{rn+1}:column{ti*3+3}'
                records.append({
                    'record_id': 'peru_2026:' + condition, 'group_id': group,
                    'evaluation_group': group, 'source_family': 'peru_2026',
                    'condition_id': condition, 'targets': targets,
                    'relevance': {t: 1 for t in targets}, 'evidence_unit_ids': [evidence],
                    'raw_source_description': raw, 'source_language': 'es',
                    'unmapped_source_phrases': unmatched, 'panelist_mention_sets': [],
                    'source_C0': 'preparation.family.immersion', 'source_C1': None,
                    'source_native_C1_historical': 'medium_source_native_unmapped' if ppc >= 3 else None,
                    'source_context': {'packaging_product_configuration': chr(65+ppc),
                                       'storage_temperature_c': None if stage == 0 else temp,
                                       'storage_days': day, 'brew_water_c': 95,
                                       'coffee_g': 11.55, 'water_ml': 150,
                                       'independent_packages_per_condition': 3,
                                       'panelist_count': 6, 'narrative_unit': 'published concatenation of graders; not six separable answers'},
                    'quality_score': measurement(score, {'type': 'source cupping quality total'}, 'quality, not intensity'),
                    'role': 'AUX_COFFEE_WEAK_LABEL',
                    'supervision': 'INCOMPLETE_AGGREGATED_PROFESSIONAL_NARRATIVES_UNDER_ACCELERATED_STORAGE',
                    'split': split(group), 'proxy_status': 'DERIVED_RECORD_PROXY',
                    'missing_descriptor_status': 'NOT_MENTIONED', 'recovery_target_available': bool(targets),
                    'task_masks': {'attribute': False, 'leaf_recovery': bool(targets),
                                   'core_evaluation': False, 'new_confirmation': False},
                    'source_scale_note': 'Quality ratings remain separate; no sensory intensity is reconstructed from them.'})
        sheet = list(w.worksheets[ppc+1].values)
        blocks = [i for i, row in enumerate(sheet) if row[0] in ['40 °C', '50 °C', '60 °C']]
        assert len(blocks) == 3
        for ti, start in enumerate(blocks):
            for stage in range(5):
                if ti > 0 and stage == 0:
                    continue
                for judge in range(6):
                    values = {}
                    for row in sheet[start+3:start+14]:
                        if not isinstance(row[1], str):
                            continue
                        raw = row[2 + stage*8 + judge]
                        values[row[1]] = measurement(float(raw), {'type': 'source cupping quality'},
                            'grader mean over three packages; not intensity') if isinstance(raw, (int, float)) else measurement(
                            None, {'type': 'source cupping quality'}, 'quality, not intensity', 'UNPARSEABLE', raw)
                    quality.append({'group_id': group, 'ppc': chr(65+ppc), 'storage_temperature_c': None if stage == 0 else [40,50,60][ti],
                                    'stage': stage, 'judge_local_index': judge+1, 'values': values,
                                    'evidence_unit_id': f'peru:FileS1:{w.worksheets[ppc+1].title}:block{start+1}:stage{stage}:judge{judge+1}'})
    assert len(records) == 104 and len(quality) == 624
    save(owner / 'peru_recovery_records.private.json', records)
    save(owner / 'peru_quality_records.private.json', quality)
    return records, {'raw_descriptor_cells': 120, 'duplicate_baseline_descriptor_cells': 16,
        'unique_condition_narratives': 104, 'grader_mean_quality_observations': 624,
        'independent_coffee_lot_groups': 1, 'independent_collection_studies': 1,
        'fine_grained_recovery_records': sum(r['recovery_target_available'] for r in records),
        'complete_intensity_records': 0, 'source_context_paired_records': 104,
        'production_C0_C1_paired_records': 0, 'confirmation_groups': int(split(group)=='CONFIRMATION'),
        'group_id': group, 'split': split(group), 'role': 'AUX_COFFEE_WEAK_LABEL',
        'author': 'Frank Fernandez-Rosillo; Lenin Quiñones-Huatangari; Jonathan Alberto Campos Trigoso; Eliana Milagros Cabrejos-Barrios; Segundo G. Chavez; César R. Balcázar-Zumaeta',
        'url': 'https://doi.org/10.3390/foods15152756', 'version': '2026-08-05 Version of Record',
        'artifact_url': 'https://mdpi-res.com/d_attachment/foods/foods-15-02756/article_deploy/foods-15-02756-s001.zip',
        'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'attribution_required': True, 'conditions_satisfied': True,
        'modifications': 'Source language retained privately; conservative project-authored exact Spanish mappings; duplicate day-zero narratives removed; cupping quality not used as intensity.',
        'archive_sha256': digest((root/'peru-attachment.zip').read_bytes()), 'xlsx_sha256': digest(content),
        'limitation': 'One blended lot under accelerated storage; packaging/product/roast factors confounded; not fresh-brew core truth.'}


CATA_CONCEPTS = {
    'Sweet': 'taste.sweetness', 'Dark.chocolate': 'sensory.dark_chocolate',
    'Nutty': 'broad.nutty', 'Roasted': 'attribute.roasted', 'Rubber': 'native.rubber',
    'Caramel': 'sensory.caramel', 'Sour': 'taste.sourness', 'Fruit': 'attribute.fruity',
    'Burnt': 'native.burnt', 'Bitter': 'taste.bitterness', 'Astringent': 'mouthfeel.astringent',
    'Tea.floral': 'compound.tea_floral',
}


def cotter_records(owner=PRIVATE):
    root = owner/'sources'
    metadata = json.loads((root/'cotter-api.json').read_text())
    assert metadata['license'] == 'https://spdx.org/licenses/CC0-1.0.html'
    assert 'Apache License' in (root/'cotter-mirror-license.txt').read_text()
    tree = json.loads((root/'cotter-github-tree.json').read_text())
    artifact = root/'cotter-mirror-rows.csv'
    blob_hash = hashlib.sha1(b'blob '+str(artifact.stat().st_size).encode()+b'\0'+artifact.read_bytes()).hexdigest()
    assert any(x['path']=='models/no_aggregation/output_reg/preprocessing/_data_none.csv' and x['sha']==blob_hash for x in tree['tree'])
    rows = list(csv.DictReader(artifact.open()))
    group = 'cotter_2023:honduras_single_coffee'
    result = []
    for i, row in enumerate(rows):
        values = {concept: measurement(int(row[name]), {'type': 'binary CATA', 'min': 0, 'max': 1},
                       '0=not detected on shown CATA ballot; 1=detected; consumer report') for name, concept in CATA_CONCEPTS.items()}
        assert all(m['value'] in (0, 1) for m in values.values())
        result.append({'record_id': 'cotter:author-derived-row:'+str(i), 'group_id': group,
            'evaluation_group': group, 'source_family': 'cotter_2023', 'split': split(group),
            'role': 'AUX_COFFEE_WEAK_LABEL', 'attribute_measurements': values,
            'targets': sorted(c for c,m in values.items() if m['value']==1),
            'relevance': {c: m['value'] for c,m in values.items() if m['value']==1},
            'source_C0': 'preparation.family.filter_percolation', 'source_C1': None,
            'source_native_C1_historical': 'medium_source_native_unmapped',
            'condition_id': None, 'panelist_id': None,
            'evidence_unit_ids': ['cotter:github:'+tree['sha']+':unaggregated:'+str(i+2)],
            'supervision': 'AUTHOR_DERIVED_SELECTED_CATA_COLUMNS_TRAINING_SUBSET',
            'task_masks': {'attribute': True, 'leaf_recovery': False, 'core_evaluation': False,
                           'context_row_link': False, 'new_confirmation': False},
            'missing_descriptor_status': 'NOT_MEASURED_IN_DERIVED_MATRIX',
            'proxy_status': 'DERIVED_RECORD_PROXY',
            'excluded_columns': ['liking','Flavor intensity (adj)','Acidity (adj)','Mouthfeel (adj)']})
    assert len(result) == 2548
    save(owner/'cotter_attribute_observations.private.json', result)
    return result, {'original_api_files_acquired': False, 'original_download_failure': 'HTTP401 API / HTTP403 public file_stream',
        'actual_retained_matrix': 'Author-derived feature-selected unaggregated training subset; original observation identifiers absent',
        'raw_original_rows_acquired': 0, 'author_derived_observation_rows_acquired': len(result),
        'available_complete_CATA_columns': list(CATA_CONCEPTS), 'sensory_cell_count': len(result)*len(CATA_CONCEPTS),
        'independent_coffee_lot_groups': 1, 'independent_collection_studies': 1,
        'source_reported_conditions': 27, 'condition_ids_recoverable': 0,
        'fine_grained_core_training_records': 0, 'broad_attribute_auxiliary_records': len(result),
        'production_C0_C1_paired_records': 0, 'confirmation_groups': int(split(group)=='CONFIRMATION'),
        'group_id': group, 'split': split(group), 'role': 'AUX_COFFEE_WEAK_LABEL',
        'author': 'William Ristenpart; Andrew R. Cotter; Jean-Xavier Guinard',
        'url': 'https://doi.org/10.25338/B8993H', 'version': 'Dryad 2023-01-16; author derivative Git tree '+tree['sha'],
        'license': 'CC0 1.0 original data; Apache-2.0 author derivative repository',
        'license_urls': ['https://spdx.org/licenses/CC0-1.0.html','https://github.com/mhgun/sensory_prediction/blob/'+tree['sha']+'/LICENSE'],
        'mirror_attribution': 'mhgun/sensory_prediction; author repository for AI-driven prediction of consumer liking of coffee from sensory data',
        'artifact_url': 'https://github.com/mhgun/sensory_prediction/blob/'+tree['sha']+'/models/no_aggregation/output_reg/preprocessing/_data_none.csv',
        'artifact_sha256': digest(artifact.read_bytes()), 'conditions_satisfied': True,
        'modifications': 'Retain 12 observed CATA columns; discard liking and transformed JAR preferences from sensory targets; compound Tea.floral stays whole. No reverse-engineering of missing identity or conditions.',
        'limitation': 'One coffee; selected columns and author training subset; no fine-label core truth or context row pairing; original raw checksum unavailable.'}




def cotter_full_records(owner=PRIVATE):
    cached = ROOT/'db/data/round3b/raw/cotter_2020_black_coffee'
    source = cached/'cotter_dataset.csv'
    readme = cached/'README.txt'
    assert digest(source.read_bytes()) == '931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114'
    assert digest(readme.read_bytes()) == 'f6d8f508bad2824a27be8785c841e8df4c75751b58726820f9e3dd226fe3fb5e'
    assert 'CC0 1.0' in readme.read_text(encoding='cp1252')
    for name, raw in [('cotter-original-cache.csv',source.read_bytes()), ('cotter-original-cache-README.txt',readme.read_bytes())]:
        path = owner/'sources'/name
        if path.exists():
            assert path.read_bytes() == raw
        else:
            path.write_bytes(raw); path.chmod(0o600)
    columns = {**CATA_CONCEPTS, 'Citrus':'broad.citrus',
        'Green.veg':'compound.green_vegetative', 'Paper.wood':'compound.paper_wood',
        'Cereal':'native.cereal', 'Thick.viscous':'mouthfeel.thick_viscous'}
    rows = list(csv.DictReader(source.open()))
    assert len(rows) == 3186 and len(columns) == 17
    assert len({r['Judge'] for r in rows}) == 118 and len({r['Brew'] for r in rows}) == 27
    assert len({(r['Judge'],r['Brew']) for r in rows}) == 3186
    group = 'cotter_2023:honduras_single_coffee'
    records = []
    for i, row in enumerate(rows):
        values = {concept:measurement(int(row[name]), {'type':'binary CATA','min':0,'max':1},
            '0=not detected on explicitly shown CATA ballot; 1=detected; consumer observation') for name,concept in columns.items()}
        assert all(m['value'] in (0,1) for m in values.values())
        records.append({'record_id':'cotter:original-row:'+str(i+2),
            'source_family':'cotter_2023', 'group_id':group,'evaluation_group':group,
            'split':split(group), 'role':'AUX_COFFEE_WEAK_LABEL',
            'panelist_id':'cotter:judge:'+row['Judge'], 'condition_id':'cotter:brew:'+row['Brew'],
            'evidence_unit_ids':['cotter:original:'+row['Judge']+':'+row['Brew']],
            'attribute_measurements':values, 'targets':sorted(c for c,m in values.items() if m['value']==1),
            'relevance':{c:1 for c,m in values.items() if m['value']==1},
            'source_C0':'preparation.family.filter_percolation','source_C1':None,
            'source_native_C1_historical':'medium_source_native_unmapped',
            'source_context':{k:row[k] for k in ['Brew','Temp.x','TDS.x','PE.x','Week','Session Number','Position']},
            'supervision':'COMPLETE_ORIGINAL_CONSUMER_CATA_MATRIX',
            'missing_descriptor_status':'NOT_MEASURED_OUTSIDE_SOURCE_BALLOT',
            'excluded_columns':['Liking','Temp','Flavor.intensity','Acidity','Mouthfeel','Purchase.intent','Cluster'],
            'task_masks':{'attribute':True,'attribute_positive_mentions':True,
                'attribute_intensity':False,'attribute_binary_detection':True,
                'leaf_recovery':False,'core_evaluation':False,
                'context_row_link':True,'new_confirmation':False},
            'proxy_status':'DERIVED_RECORD_PROXY'})
    save(owner/'cotter_full_attribute_observations.private.json',records)
    return records, {'status':'REUSED_GOVERNED_ORIGINAL_CACHE_HASH_VERIFIED',
        'raw_original_rows_acquired':3186, 'panelist_count':118, 'condition_count':27,
        'measured_CATA_columns':list(columns),'sensory_cell_count':3186*17,
        'independent_coffee_lot_groups':1, 'incremental_coffee_groups_over_author_derivative':0,
        'new_to_D0_collection_source':True,'newly_downloaded_collection_source_this_block':False,
        'author':'Andrew Cotter; William D. Ristenpart; Jean-Xavier Guinard',
        'url':'https://doi.org/10.25338/B8993H','version':'Dryad v4 2023-01-16; data collected April–June 2019',
        'license':'CC0 1.0','license_url':'https://creativecommons.org/publicdomain/zero/1.0/',
        'conditions_satisfied':True,'cache_provenance':'db/data/round3b/raw/cotter_2020_black_coffee; original hash equals live Dryad v4 file metadata',
        'artifact_sha256':digest(source.read_bytes()),'readme_sha256':digest(readme.read_bytes()),
        'private_artifact':str(owner/'cotter_full_attribute_observations.private.json'),
        'modifications':'Parse original 17 complete CATA columns; retain private judge and condition identity for disjoint evidence; exclude preferences/JAR and lab variables from runtime input; compound categories stay whole.',
        'supersedes_for_new_attribute_experiments':'cotter_attribute_observations.private.json author-derived subset; do not concatenate duplicate views',
        'limitation':'Still one coffee; original independent panelist units are not independent coffee confirmation; C1 remains source-native unmapped.'}

CONDELLI_IDS = [*(f'A{i}' for i in range(1, 10)), 'GC', 'GD', 'PH', 'PV', *(f'R{i}' for i in range(1, 8))]
CONDELLI_CONCEPTS = {
    'Tobacco': 'sensory.tobacco', 'Caramel': 'sensory.caramel',
    'Licorice': 'native.licorice', 'Chocolate': 'broad.chocolate',
    'Nutty': 'broad.nutty', 'Roasted': 'attribute.roasted',
    'Burnt': 'native.burnt', 'Earthy': 'sensory.earthy',
    'Grassy': 'native.grassy', 'Citrus': 'broad.citrus',
    'Bitter': 'taste.bitterness', 'Sweet': 'taste.sweetness',
    'Acidic': 'taste.sourness', 'Astringent': 'mouthfeel.astringent',
}


def condelli_records(owner=PRIVATE):
    # Sample IDs come from source Table S1. Register groups before reading the
    # sensory matrix or evaluating models. Products are not traceable raw lots.
    groups = {sid: 'condelli_2022:coffee_product:' + sid for sid in CONDELLI_IDS}
    registration = {'version': 'm2-r1-condelli-split.v1', 'seed': SPLIT_SEED,
        'created_before_model_results': True,
        'identity_basis': 'Twenty distinct published coffee-product sample IDs; blend constituent lots unknown',
        'groups': {sid: {'group_id': group, 'split': split(group)} for sid, group in groups.items()}}
    preregistered = owner/'condelli_split_preregistered.private.json'
    if preregistered.exists():
        assert json.loads(preregistered.read_text()) == registration
    else:
        save(preregistered, registration)
    root = owner/'sources'
    xml = etree.parse(str(root/'liking-mono.xml'))
    assert any('by/4.0' in x for x in xml.xpath('//permissions//@*[contains(.,"creativecommons")]'))
    archive = zipfile.ZipFile(root/'mono-epmc-supp.zip')
    content = archive.read('JFDS-87-4688-s001.docx')
    doc = etree.fromstring(zipfile.ZipFile(io.BytesIO(content)).read('word/document.xml'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    def table_rows(index):
        return [[''.join(c.xpath('.//w:t/text()', namespaces=ns))
                 for c in row.xpath('./w:tc', namespaces=ns)]
                for row in doc.xpath('//w:tbl', namespaces=ns)[index].xpath('./w:tr', namespaces=ns)]
    identity = {row[0]: row[1:] for row in table_rows(0)[2:]}
    cells = table_rows(7)
    assert cells[1][1:] == CONDELLI_IDS
    assert set(identity) == set(CONDELLI_IDS) and len(cells) == 20
    native = {re.sub(r'\s*\*+$', '', row[0]): [int(v) for v in row[1:]] for row in cells[2:]}
    assert len(native) == 18 and all(len(v) == 20 for v in native.values())
    totals = [sum(v[i] for v in native.values()) for i in range(20)]
    # Source says citation percentage, but no respondent-level denominator is
    # supplied. Column sums ~100 indicate composition, not P(detection|person).
    assert all(95 <= n <= 105 for n in totals)
    scale = {'type': 'source-reported rounded CATA citation percentage', 'min': 0, 'max': 100,
        'reporting_resolution': 1, 'respondent_denominator': None,
        'zero_means_absence': False, 'not_intensity': True,
        'not_respondent_detection_probability': True}
    observations, recovery = [], []
    from flavor_backend import BASE_CANDIDATES
    vocabulary = set(BASE_CANDIDATES) | {c for c in CONDELLI_CONCEPTS.values() if c.startswith(('broad.', 'attribute.', 'taste.', 'mouthfeel.'))}
    for col, sid in enumerate(CONDELLI_IDS):
        attrs = {concept: measurement(native[label][col], scale,
            'Published rounded citation frequency; zero is a reported aggregate zero, not proof of sensory absence',
            'OBSERVED') for label, concept in CONDELLI_CONCEPTS.items()}
        positive = sorted(c for c, value in attrs.items() if value['value'] > 0 and c in vocabulary)
        base = {'record_id': 'condelli:tableS8:' + sid, 'source_family': 'condelli_2022',
            'sample_id': sid, 'group_id': groups[sid], 'evaluation_group': groups[sid],
            'split': split(groups[sid]), 'role': 'AUX_COFFEE_WEAK_LABEL',
            'source_C0': 'preparation.family.espresso_pressure', 'source_C1': None,
            'source_native_C1_historical': '245 degrees Celsius for 15 minutes; same source roast protocol; no calibrated C1',
            'source_identity_metadata': {'continent': identity[sid][0], 'country': identity[sid][1], 'species_or_product': identity[sid][2]},
            'lot_identity_status': 'SOURCE_DEFINED_COFFEE_PRODUCT; RAW_LOT_NOT_REPORTED; BLEND_CONSTITUENTS_UNKNOWN',
            'targets': positive, 'relevance': {c: attrs[c]['value'] for c in positive},
            'attribute_measurements': attrs, 'source_native_all_citation_percentages': {k:v[col] for k,v in native.items()},
            'source_column_percentage_sum': totals[col],
            'evidence_unit_ids': ['condelli:PMC9826037:Supplement:S8:sample:'+sid],
            'supervision': 'POSITIVE_ONLY_SOURCE_REPORTED_ROUNDED_CATA_CITATION_PERCENTAGES',
            'missing_descriptor_status': 'NOT_MEASURED_OUTSIDE_SOURCE_BALLOT',
            'zero_target_status': 'ROUNDED_REPORTED_ZERO_NOT_SENSORY_ABSENCE',
            'excluded_preference_columns': ['Strong', 'Delicate', 'Balanced', 'Long aftertaste', 'Overall liking'],
            'proxy_status': 'DERIVED_RECORD_PROXY',
            'task_masks': {'attribute': False, 'attribute_positive_mentions': True,
                'attribute_intensity': False, 'attribute_binary_detection': False,
                'native_citation_profile': True,
                'leaf_recovery': bool(positive), 'sensory_intensity': False,
                'binary_detection': False, 'core_evaluation': False,
                'new_confirmation': split(groups[sid]) == 'CONFIRMATION'}}
        observations.append(base)
        # Retain canonical positive labels, never use rounded zero as negatives.
        recovery.append({k:v for k,v in base.items() if k not in {'attribute_measurements','source_native_all_citation_percentages'}})
    save(owner/'condelli_native_citation_observations.private.json', observations)
    save(owner/'condelli_recovery_records.private.json', recovery)
    return recovery, {'author': 'Nicola Condelli; Nazarena Cela; Maria Di Cairano; Teresa Scarpa; Luigi Milella; Roberta Ascrizzi; Guido Flamini; Fernanda Galgano',
        'url': 'https://doi.org/10.1111/1750-3841.16323', 'version': '2022 version of record',
        'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'conditions_satisfied': True, 'attribution_required': True,
        'artifact_url': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9826037/supplementaryFiles',
        'artifact_sha256': digest((root/'mono-epmc-supp.zip').read_bytes()), 'docx_sha256': digest(content),
        'source_reported_panelists': 77, 'raw_panelist_records_acquired': 0,
        'source_defined_coffee_product_groups': 20, 'traceable_raw_lots': None,
        'sample_id_groups': registration['groups'], 'independent_collection_studies': 1,
        'admitted_positive_recovery_rows': len(recovery), 'source_native_cells': len(native)*20,
        'retained_sensory_citation_cells': len(CONDELLI_CONCEPTS)*20,
        'intensity_cells': 0, 'true_zero_sensory_cells': 0, 'production_C0_C1_paired_records': 0,
        'role': 'AUX_COFFEE_WEAK_LABEL',
        'confirmation_groups': sum(r['split']=='CONFIRMATION' for r in recovery),
        'modifications': 'Table S1 identity and S8 values transcribed programmatically; strip significance stars from names; canonical positives only; never convert rounded zero to absence; quality/hedonic fields excluded.',
        'limitation': 'Consumer auxiliary; published aggregate percentages only, no independent answer rows; 4 blend constituents unspecified; not 20 traceable independent raw lots; source-native roast unmapped.'}

ROCCHETTI_FIELDS = {
    'OLFACTORY INTENSITY': 'native.olfactory_intensity',
    'BODY': 'mouthfeel.body',
    'ACIDITY': 'native.acidity_intensity',
    'BITTERNESS': 'taste.bitterness',
    'ASTRINGENT': 'mouthfeel.astringency',
    'FLOWERS AND FRESH FRUIT': 'native.flowers_and_fresh_fruit',
    'VEGETABLE': 'native.vegetable',
    'DRIED FRUITS AND NUTS': 'native.dried_fruits_and_nuts',
    'ROASTED': 'native.roasted_composite',
    'SPICY': 'native.spicy',
    'EMPYREUMATIC': 'native.empyreumatic',
    'BIOCHEMICAL': 'native.biochemical',
}


def rocchetti_records(owner=PRIVATE):
    root = owner / 'sources'
    xml = etree.parse(str(root / 'metabolomics47.xml'))
    assert any('creativecommons.org/licenses/by/4.0' in v for v in xml.xpath('//permissions//@*'))
    archive = zipfile.ZipFile(root / 'metabolomics47.zip')
    content = archive.read('11306_2020_1751_MOESM3_ESM.docx')
    doc = zipfile.ZipFile(io.BytesIO(content))
    x = etree.fromstring(doc.read('word/document.xml'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    rows = [[' '.join(c.xpath('.//w:t/text()', namespaces=ns))
             for c in r.xpath('./w:tc', namespaces=ns)]
            for r in x.xpath('//w:tbl/w:tr', namespaces=ns)]
    assert len(rows) == 48 and all(len(r) == 30 for r in rows)
    header = rows[0]
    registration = json.loads((owner / 'rocchetti_split_preregistered.private.json').read_text())
    expected = {'rocchetti_2020:coffee_product:' + r[0]: split('rocchetti_2020:coffee_product:' + r[0]) for r in rows[1:]}
    assert len(expected) == 47 and registration['groups'] == expected
    observations = []
    for row in rows[1:]:
        raw = dict(zip(header, row))
        gid = 'rocchetti_2020:coffee_product:' + row[0]
        attrs = {}
        for label, key in ROCCHETTI_FIELDS.items():
            value = float(raw[label].replace(',', '.'))
            assert 0 <= value <= 9
            body = label == 'BODY'
            scale = {'type': 'source-native 10-position descriptive rating; published panel aggregate',
                'min': 0, 'max': 9, 'anchors': ['ZERO', 'MAX'],
                'anchor_verification': 'Supplement Table 1 embedded assessment: 10 positions; zero-to-maximum, independently read from its embedded PDF',
                'zero_means_absence': not body, 'source_aggregation_method': 'NOT_REPORTED; do not assume arithmetic mean',
                'not_quality_score': True,
                'body_zero_reference': 'source filter-coffee viscosity baseline; not absence of body' if body else None}
            attrs[key] = measurement(value, scale,
                'Source-native quantitative sensory dimension; compound source category retained whole; not a fine descriptor or quality judgement',
                'OBSERVED' if body or value > 0 else 'TRUE_ZERO', raw[label])
            attrs[key]['source_label'] = label
        observations.append({'record_id': 'rocchetti:tableS1:' + row[0],
            'source_family': 'rocchetti_2020', 'sample_id': row[0], 'group_id': gid, 'evaluation_group': gid,
            'split': expected[gid], 'role': 'CORE_PROFESSIONAL', 'source_C0': None, 'source_C1': None,
            'source_native_category_code': row[2], 'source_submission_country': row[1],
            'source_identity_metadata': '2018 International Coffee Tasting product code; country is submission country, not proven bean origin; category-to-brew mapping unavailable',
            'lot_identity_status': 'SOURCE_DEFINED_COFFEE_PRODUCT; RAW_LOT_NOT_REPORTED; BLEND_CONSTITUENTS_UNKNOWN',
            'attribute_measurements': attrs, 'attribute_masks': {k: True for k in attrs},
            'targets': [], 'relevance': {},
            'task_masks': {'attribute': True, 'attribute_intensity': True, 'attribute_positive_mentions': False,
                'attribute_binary_detection': False, 'leaf_recovery': False, 'source_native_attribute_profile': True,
                'new_confirmation': expected[gid] == 'CONFIRMATION', 'production_context_complete': False},
            'evidence_unit_ids': ['rocchetti:PMC7736008:Supplement:TableS1:sample:' + row[0]],
            'proxy_status': 'DERIVED_RECORD_PROXY',
            'supervision': 'COMPLETE_SOURCE_NATIVE_PANEL_AGGREGATE_DESCRIPTIVE_RATINGS',
            'missing_descriptor_status': 'NOT_MEASURED_OUTSIDE_SOURCE_BALLOT',
            'independent_panelist_answers_available': False,
            'source_panel': {'total_experts': 30, 'experience': '>1200 hours evaluating food/beverages including coffee',
                'commissions': 5, 'sample_specific_panelist_count': None, 'native_values_are': 'published panel aggregate'},
            'excluded_fields': [k for k in header[3:] if k not in ROCCHETTI_FIELDS],
            'excluded_input_information': ['award/quality stratum', 'country', 'sample/category IDs', 'chemical measurements']})
    save(owner / 'rocchetti_attribute_observations.private.json', observations)
    return observations, {'author': 'Gabriele Rocchetti; Gian Paolo Braceschi; Luigi Odello; Terenzio Bertuzzi; Marco Trevisan; Luigi Lucini',
        'url': 'https://doi.org/10.1007/s11306-020-01751-6', 'version': '2020 version of record; original collection November 2018',
        'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'attribution_required': True, 'conditions_satisfied': True,
        'form_copyright_note': 'Embedded third-party assessment form bears CSA copyright; inspected for scale only and excluded from public redistribution and model inputs; author-published numerical results are admitted under article CC BY 4.0.',
        'artifact_url': 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7736008/supplementaryFiles',
        'artifact_sha256': digest((root / 'metabolomics47.zip').read_bytes()), 'docx_sha256': digest(content),
        'source_defined_coffee_product_groups': 47, 'traceable_raw_lots': None, 'independent_collection_studies': 1,
        'source_reported_panelists': 30, 'raw_panelist_records_acquired': 0,
        'confirmation_groups': sum(r['split'] == 'CONFIRMATION' for r in observations),
        'admitted_native_attribute_cells': len(observations) * len(ROCCHETTI_FIELDS),
        'source_native_attribute_labels': ROCCHETTI_FIELDS,
        'admitted_fine_recovery_rows': 0, 'production_C0_C1_paired_records': 0,
        'role': 'CORE_PROFESSIONAL', 'fresh_brew_eligibility': 'NOT_FULLY_DOCUMENTED; product-specific preparation and service timing absent', 'source_protocol': 'Trialtest descriptive/qualitative scores separate; original professionally prepared filter/moka/single-dose/espresso products; product-specific brew family not established by letter codes',
        'modifications': 'Programmatic extraction of numeric S1 rows; comma-decimal parsing; select 12 descriptive dimensions; preserve compound categories; explicit zero/missing/masks; quality and chemistry excluded. No assessment-form wording/design in public data.',
        'limitation': '47 source-defined products sampled across award strata, not representative prevalence; no traceable lots or blend components; source-native roast and per-product brewing metadata missing; no fine descriptor labels or independent answers.'}


def acquisition_audit(owner):
    started = datetime(2026, 9, 5, 10, 42, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    block = {'started_utc': started.isoformat(), 'ended_utc': None,
        'start_time_precision': 'minute; approximately 10:42 UTC recorded by coordinating task',
        'last_updated_utc': now.isoformat(), 'elapsed_minutes': round((now-started).total_seconds()/60, 1),
        'status': 'IN_PROGRESS', 'authorized_duration_hours': [3, 4],
        'targeted_data_routes_limit': 12, 'targeted_data_routes_used': 12,
        'policy': 'Continue useful acquisition and validation within existing routes; no additional broad source discovery, author requests, or idle time padding.'}
    specs = [
      ('10.3390/foods15152756', 'ADMITTED_STORAGE_AUXILIARY', ['peru-full.xml','peru-attachment.zip'],
       '104 deduplicated condition narratives from one blended lot; 624 Q-grader quality aggregates isolated. Positive recovery only; accelerated storage is not fresh-core coffee.'),
      ('10.25338/B8993H', 'REUSED_GOVERNED_ORIGINAL_CACHE', ['cotter-api.json','cotter-original-cache.csv','cotter-original-cache-README.txt'],
       '3186 judge-by-brew rows of 17 complete CATA attributes, one coffee. API verified CC0 and original cache hash; not a newly downloaded collection. Author-derived 2548 view retained but not concatenated.'),
      ('10.1111/1750-3841.16323', 'NEW_ACQUISITION_ADMITTED_CONSUMER_AUXILIARY', ['liking-mono.xml','mono-epmc-supp.zip'],
       '20 coffee product IDs; rounded native citation percentages. 17 DEV/3 confirmation. Zero percentages are not sensory absence; quality/intensity loss excluded.'),
      ('10.1016/j.dib.2025.111609', 'NO_ELIGIBLE_SENSORY_MATRIX_ACQUIRED', ['nir.xml','mendeley-nir-files.json'],
       '64 coffees claimed; public Mendeley metadata lists spectra/quality files. Actual quality-file endpoint returned 403. Quality totals cannot supervise sensory intensity; zero admitted rows.'),
      ('10.3389/fsufs.2025.1497350', 'DATA_AVAILABLE_ON_REQUEST_ONLY', ['frontiers-ccc.xml'],
       'Original full XML acquired: 378 analyzed accessions, 10 ordinal quality dimensions plus descriptors; tables are cluster/region summaries, no per-accession matrix. Body/acidity/sweetness are quality assessments, not intensity. No data request sent; zero admitted groups.'),
      ('10.1038/s41598-025-99921-w', 'SUPPLEMENT_ACQUIRED_NO_SENSORY_ROWS', ['carvalho.xml','carvalho-supp.zip','carvalho-dryad-search.json'],
       '67 professional RATA coffees described; public Dryad share returns 404, original supplementary DOCX contains grader demographics and water composition only. No sensory matrix and no admitted rows; article CC BY NC ND does not itself authorize adapted data.'),
      ('10.1111/joss.12886', 'FULL_TEXT_READ_SUPPLEMENT_NOT_RETRIEVABLE', ['williams-crossref.json'],
       '71 professional coffees and 179 follow-on validation samples described. Public original CC BY NC full text read; XLSX HTTP403; browser download emitted an event but no accessible artifact. Mixed original-panel and third-party text must be separated if obtained; zero rows counted.'),
      ('10.1007/s11306-020-01751-6', 'NEW_ACQUISITION_ADMITTED_PROFESSIONAL_ATTRIBUTES', ['metabolomics47.xml','metabolomics47.zip'],
       '47 source-defined coffee products, 12 complete native sensory dimensions. 38 DEV/9 new professional confirmation fixed before models. Quality, chemistry, original form and compound-to-leaf expansion excluded.'),
      ('10.3390/molecules24244515', 'SUPPLEMENT_ACQUIRED_NO_SENSORY_ROWS', ['enose.xml','enose.zip'],
       '184 coffees and six expert panel described; actual supplement contains one PCA plot only. Main table is overall statistics, not per-coffee rows. Original mixed quality/intensity wording also needs caution; zero groups admitted.'),
      ('10.1038/s41598-024-69867-6', 'SUPPLEMENT_ACQUIRED_RAW_REPOSITORY_UNAVAILABLE', ['liang-supp.zip','liang-dryad-api.json','liang-dryad-landing.html'],
       '30 conditions from one blend; supplementary DOCX supplies reference standards, ANOVA and plots only. Published Dryad identifier returns not-viewable/missing-required-elements response. No row reconstruction from figures; cold stored/diluted service applies.'),
      ('10.1038/s41598-020-73341-4', 'SUPPLEMENT_ACQUIRED_MARGINAL_MEANS_ONLY', ['batali2020.xml','batali2020-supp.zip'],
       '27 factorial brewing recipes in Table S1, but sensory Table S5 has nine marginal factor means, not 27 joint sensory profiles. One Honduras coffee may overlap Cotter; no new coffee count. Keep any marginal auxiliary view outside condition/coffee confirmation and exclude delayed-service extrapolation.'),
      ('10.3390/foods11162440', 'SUPPLEMENT_ACQUIRED_NO_SENSORY_ROWS', ['batali.xml','batali2022-supp.zip'],
       'Three coffees by three native roast levels by three brew temperatures; actual zipped supplement contains one PCA biplot. Raw data on request, not requested. No 27-row profile reconstructed; overnight refrigeration and dilution constrain use.'),
    ]
    routes = []
    for doi, status, files, use in specs:
        artifacts = {f: {'sha256': digest((owner/'sources'/f).read_bytes()), 'bytes': (owner/'sources'/f).stat().st_size}
                     for f in files if (owner/'sources'/f).exists()}
        routes.append({'doi': doi, 'source_url': 'https://doi.org/'+doi, 'result': status,
            'actual_cached_artifacts': artifacts, 'model_use_or_obstacle': use})
    return block, routes


def main():
    ap = argparse.ArgumentParser();ap.add_argument('--owner', type=Path, default=PRIVATE)
    args=ap.parse_args();owner=args.owner
    owner.mkdir(parents=True, exist_ok=True)
    for filename, expected_sha in SOURCE_DIGESTS.items():
        assert digest((owner / 'sources' / filename).read_bytes()) == expected_sha, 'Frozen source changed: ' + filename
    # Register deterministic grouping before adapters, any feature fitting, or evaluation.
    policy = {'version':'m2-r1-source-split.v1','seed':SPLIT_SEED,
        'rule':'SHA256(seed|group_id) first 8 hex modulo 5 == 0 => CONFIRMATION; otherwise DEVELOPMENT',
        'fixed_known_groups': {g:split(g) for g in ['peru_2026:single_blend_lot','cotter_2023:honduras_single_coffee']},
        'created_before_model_results':True,
        'anonymous_zenodo':'QUARANTINED_UNKNOWN_LOT_OVERLAP; barred from D0 comparisons and confirmation',
        'small_group_rule':'No forced condition-level confirmation split; all trajectories from a coffee remain together.'}
    existing=owner/'sample_split_preregistered.private.json'
    if existing.exists():assert json.loads(existing.read_text())==policy
    else:save(existing,policy)
    zen=zenodo_views(owner);peru,pm=peru_records(owner);cotter,cm=cotter_records(owner)
    frozen_recovery = owner / 'd1_recovery_records.private.json'
    if frozen_recovery.exists():
        assert json.loads(frozen_recovery.read_text()) == peru, 'Frozen D1 v1 changed; create a distinct version instead'
    else:
        save(frozen_recovery, peru)
    save(owner/'d1_attribute_observations.private.json',cotter)
    cotter_full,fm=cotter_full_records(owner)
    save(owner/'d1_attribute_expanded.private.json',cotter_full)
    condelli,dm=condelli_records(owner)
    rocchetti,rm=rocchetti_records(owner)
    expanded_peru = [{**r, 'task_masks':{**r['task_masks'],
        'attribute_positive_mentions': True, 'attribute_intensity': False,
        'attribute_binary_detection': False}} for r in peru]
    save(owner/'d1_recovery_expanded.private.json',expanded_peru+condelli)
    manifest={'experiment_id':'backend-sequential-model-v2/revisions/r1',
        'purpose':'PERSONAL_NONCOMMERCIAL_COFFEE_RESEARCH','status':'ACQUIRED_AND_PARSED',
        'manifest_version':3, 'd1_v1_frozen_path':str(owner/'d1_recovery_records.private.json'),
        'd1_v2_expanded_path':str(owner/'d1_recovery_expanded.private.json'),
        'split_policy':policy, 'sources':{'zenodo_recovered_views':zen,'peru_2026':pm,'cotter_2023_author_derived_frozen':cm,'cotter_2023_original':fm,'condelli_2022':dm,'rocchetti_2020':rm},
        'actual_increment':{'new_independent_coffee_lot_or_product_groups':69,'new_study_coffee_lot_groups':2,
          'new_source_defined_coffee_product_groups':67,'new_to_D0_independent_collection_studies':4,
          'newly_acquired_collection_studies_this_block':3,'reused_existing_collection_studies':1,
          'new_core_professional_product_groups':47,'fresh_brew_eligibility':'NOT_FULLY_DOCUMENTED','new_complete_native_intensity_records':47,'new_complete_native_intensity_cells':564,'new_known_condition_observations':104,
          'new_fine_recovery_auxiliary_records':len(peru)+len(condelli),'new_complete_CATA_auxiliary_records':len(cotter_full),
          'new_confirmation_groups':dm['confirmation_groups']+rm['confirmation_groups'],'new_production_C0_C1_paired_records':0,
          'quarantined_anonymous_source_sample_ids':zen['anonymous_source_sample_ids']},
        'target_gap':{'independent_group_target':[50,100],'shortfall_to_50':0,
          'explanation':'Two studies each used one coffee lot; two further studies provide 20 consumer and 47 professional source-defined coffee products. Count reaches 69 product/lot groups, not 69 traceable independent raw lots; sensory labels and professional provenance remain role-specific.'},
        'not_evaluated':['REAL_ANSWER_EVALUATION','NEW_CONFIRMATION_RESULTS_AT_ACQUISITION_TIME'],
        'private_artifacts':{p.name:{'path':str(p),'sha256':digest(p.read_bytes())} for p in owner.glob('*private.json') if any(k in p.name for k in ['d1_','attribute_','quality_','peru_recovery','sample_split','condelli_','cotter_full','rocchetti_'])},
        'rights_policy':'Original files, derivatives and weights stay owner-private. Original source license and notices are preserved; no permission is propagated across unrelated sources.',
        'field_status_enum':sorted(STATUS),
        'supervision_mask_contract':{'legacy_attribute_field':'Legacy field refers to complete numeric measurement supervision, never a blanket prohibition on positive broad mentions.',
            'Peru':{'attribute_positive_mentions':True,'attribute_intensity':False,'attribute_binary_detection':False},
            'Condelli':{'attribute_positive_mentions':True,'attribute_intensity':False,'attribute_binary_detection':False},
            'Rocchetti':{'attribute_positive_mentions':False,'attribute_intensity':True,'intensity_type':'SOURCE_NATIVE_10_POSITION_PANEL_AGGREGATE','attribute_binary_detection':False,'leaf_recovery':False},
            'Cotter':{'attribute_positive_mentions':True,'attribute_intensity':False,'attribute_binary_detection':True},
            'Zenodo':{'attribute_positive_mentions':True,'attribute_intensity':True,'intensity_type':'SOURCE_NATIVE_ORDINAL_ONLY','attribute_binary_detection':False},
            'frozen_v1':'Earlier 104-row Peru artifact remains byte-identical; this contract clarifies its legacy attribute=false meaning.'}, 'measurement_warning':'Cupping quality, JAR adequacy, aroma association and basic-taste intensity have separate fields and masks.'}
    manifest['source_work_block'], manifest['acquisition_routes'] = acquisition_audit(owner)
    manifest['confirmation_cohorts'] = {'consumer_condelli': {'groups': 3, 'source_family': 'condelli_2022', 'meaning': 'consumer positive-only recovery; already inspected separately'}, 'professional_rocchetti': {'groups': 9, 'source_family': 'rocchetti_2020', 'meaning': 'new independent product-group confirmation for native attribute heads; not pooled with consumer confirmation'}}
    save(PUBLIC/'sample_expansion_manifest.json',manifest)
    print(json.dumps(manifest['actual_increment'],sort_keys=True))


if __name__=='__main__':main()
