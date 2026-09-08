import ast
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import classify_table_cells_r12b as reference
import finalize_r11_artifacts as finalizer

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


if __name__ == '__main__':
    unittest.main()
