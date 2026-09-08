"""R12 software-only checks; no human ground truth or product metrics."""
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import audit_pipeline_recall_r12 as audit


class RecallDiagnostics(unittest.TestCase):
    def test_t3_list_gap_and_no_shadowing(self):
        cases = audit.synthetic_checks()['cases']
        self.assertEqual(cases['explicit_sample_descriptor_list']['typed_rows'], 0)
        self.assertEqual(cases['binary_presence']['shapes'], {'T3': 4})
        self.assertEqual(cases['numeric_named']['shapes'], {'T1': 4})
        self.assertEqual(cases['same_numeric_table_filename_caption']['typed_rows'], 0)

    def test_no_network(self):
        with audit.no_network(), socket.socket() as sock:
            with self.assertRaisesRegex(RuntimeError, 'R12_NETWORK_DISABLED'):
                sock.connect(('127.0.0.1', 1))

    def test_missing_cache_is_not_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            body, reason = audit.cache_body({'requested_url': 'test', 'sha256': 'no'}, Path(directory))
        self.assertIsNone(body)
        self.assertEqual(reason, 'CACHE_MISSING_NOT_ZERO_TABLES')

    def test_observer_preserves_empty_and_captures_it(self):
        observer = audit.Observer()
        with observer.observe('synthetic'):
            result = audit.supplements.tabular_members('unsupported.docx', b'not a document')
        self.assertEqual(result, [])
        self.assertTrue(any('EMPTY_RETURN_OBSERVED' in key for key in observer.events))

    def test_observer_preserves_exception(self):
        observer = audit.Observer()
        with observer.observe('synthetic'):
            with self.assertRaises(Exception):
                audit.extract.parse_xml(b'<broken')
        self.assertTrue(any('EXCEPTION_OBSERVED' in key for key in observer.events))

    def test_funnel_every_candidate_and_no_fabricated_recall(self):
        funnel = audit.read(audit.R12 / 'funnel_counts.json')
        recall = audit.read(audit.R12 / 'recall_report.json')
        self.assertEqual(len(funnel['candidates']), 248)
        self.assertEqual(len({x['candidate_id'] for x in funnel['candidates']}), 248)
        self.assertTrue(all(x['terminal_reason'] for x in funnel['candidates']))
        self.assertTrue(funnel['summary']['frozen_primary_ids_equal'])
        self.assertTrue(funnel['summary']['frozen_primary_content_equal'])
        self.assertIsNone(recall['overall_recall'])
        self.assertFalse(recall['formal_control_run_executed'])
        self.assertEqual(recall['fit_count'], 0)


if __name__ == '__main__':
    unittest.main()
