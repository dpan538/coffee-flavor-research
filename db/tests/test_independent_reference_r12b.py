import ast
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import classify_table_cells_r12b as reference
import finalize_r11_artifacts as finalizer
import measure_pdf_geometry_r12b as geometry

REGISTRY = {'sensory.lemon': {'role': 'NAMED_DESCRIPTOR'},
            'sensory.honey': {'role': 'NAMED_DESCRIPTOR'},
            'attribute.fruity': {'role': 'PROFILE_DIRECTION'}}


class IndependentReferenceTests(unittest.TestCase):
    def test_lists_are_present(self):
        result = reference.classify([['Sample', 'Descriptors'], ['Lot A', 'lemon; honey']], REGISTRY)
        self.assertEqual(result['label'], 'T3')

    def test_no_caption_input(self):
        result = reference.classify([['Sample', 'Lemon', 'Honey'], ['Lot A', '2', '3']], REGISTRY)
        self.assertEqual(result['label'], 'T1')

    def test_native_not_named(self):
        result = reference.classify([['Sample', 'Body'], ['Lot A', '3']], REGISTRY)
        self.assertEqual(result['label'], 'T4')

    def test_transpose(self):
        rows = [['Sample', 'Lemon', 'Honey'], ['Lot A', '2', '3']]
        self.assertEqual(reference.classify(rows, REGISTRY)['label'],
                         reference.classify(list(map(list, zip(*rows))), REGISTRY)['label'])

    def test_negative_numeric_only(self):
        self.assertEqual(reference.classify([['1', '2'], ['3', '4']], REGISTRY)['label'], 'unclassified')

    def test_independence_imports(self):
        tree = ast.parse(Path(reference.__file__).read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        self.assertEqual(set(imports), {'collections', 'decimal', 're', 'unicodedata'})

    def test_kappa(self):
        self.assertEqual(reference.confusion([('T1', 'T1'), ('T3', 'T3')])['kappa'], 1)
        self.assertIsNone(reference.confusion([])['kappa'])

    def test_forward_stream_fix(self):
        row = {'record_id': 'SYNTHETIC', 'r11_acquisition_stream': 'R11_TARGETED'}
        first, _ = finalizer.combined_outputs({'records': [row]}, {}, {'records': [row]})
        second, stats = finalizer.combined_outputs({'records': first}, {}, {'records': [row]})
        self.assertEqual(first, second)
        self.assertEqual(stats['source_record_counts_post_record_dedup']['R10_248_PRIMARY'], 0)
        self.assertEqual(stats['source_record_counts_post_record_dedup']['R11_TARGETED'], 1)

    def test_enumeration_and_missing_measurement_are_explicit(self):
        root = Path(__file__).resolve().parents[1] / 'data/backend-sequential-model-v2/revisions/r12b'
        matrix = json.loads((root / 'tier1_confusion.json').read_text())
        self.assertEqual(matrix['n'], 400)
        self.assertEqual(sum(map(sum, matrix['matrix'])), 400)
        self.assertEqual(matrix['original_unclassified'], 360)
        # Dominant-label projection must not erase the original mixed T1 tables.
        self.assertEqual(matrix['original_per_shape_table_presence']['T1'], 2)
        calibration = json.loads((root / 'tier2_calibration.json').read_text())
        self.assertTrue(calibration['executed_before_target_measurement'])
        self.assertEqual(calibration['library_pin']['PyMuPDF'], '1.27.2.2')
        self.assertEqual(calibration['true_accuracy_identification_interval'], [0,1])

    def test_geometry_pin_and_synthetic_grid(self):
        import fitz
        self.assertEqual(fitz.VersionBind, geometry.PIN)
        with fitz.open() as doc:
            page = doc.new_page()
            for r, row in enumerate([['Sample','Lemon','Honey'],['A1','2','4'],['B1','3','5'],['C1','6','7']]):
                for c, value in enumerate(row):
                    page.insert_text((50+c*100, 70+r*25), value)
            self.assertTrue(geometry.inspect_page(doc, 1)['positive'])

    def test_bootstrap_keeps_document_membership_and_is_deterministic(self):
        rows = [{'candidate_id':'A', 'positive':True}, {'candidate_id':'A', 'positive':False},
                {'candidate_id':'B', 'positive':True}]
        self.assertEqual(geometry.document_bootstrap(rows), geometry.document_bootstrap(rows))
        self.assertEqual(geometry.document_bootstrap(rows), [0.5,1.0])


if __name__ == '__main__':
    unittest.main()
