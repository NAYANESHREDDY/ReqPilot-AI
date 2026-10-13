import unittest
import sys
from pathlib import Path
sys.path.append('evaluation/multi_project/scripts')
from scorer import match_prediction_to_gold, canonicalize

class TestScorerRobustness(unittest.TestCase):
    def setUp(self):
        self.gold_details = {
            'REF-01': {
                'statement': 'Drivers should be able to register and log in securely.',
                'summary': 'Driver registration and login',
                'canonical': 'AUTHENTICATION'
            },
            'REF-02': {
                'statement': 'Drivers should be able to reserve an available charging slot before arriving.',
                'summary': 'Reserve charging slot',
                'canonical': 'BOOKING'
            },
            'REF-03': {
                'statement': 'The system shall maintain an immutable audit log of all security transactions.',
                'summary': 'Audit log retention',
                'canonical': 'DATA'
            }
        }

    def test_reordered_and_shifted_ids(self):
        # Even if ID is renumbered to FR-999, it must match REF-02 by content
        pred_shifted = {
            'id': 'FR-999',
            'source_excerpt': 'Drivers should be able to reserve an available charging slot before arriving.',
            'summary': 'Slot reservation'
        }
        gid, status = match_prediction_to_gold(pred_shifted, self.gold_details)
        self.assertEqual(status, 'UNIQUE_MATCH')
        self.assertEqual(gid, 'REF-02')

    def test_unrelated_statements_never_match(self):
        # A completely unrelated statement must be UNMATCHED, never matching by position
        pred_unrelated = {
            'id': 'FR-001', # Same ID as REF-01 positionally, but completely unrelated content
            'source_excerpt': 'Drone delivery quadcopters must automatically calibrate wind resistance sensors.',
            'summary': 'Drone sensor calibration'
        }
        gid, status = match_prediction_to_gold(pred_unrelated, self.gold_details)
        self.assertEqual(status, 'UNMATCHED')
        self.assertIsNone(gid)

    def test_ambiguous_matches_excluded(self):
        # When a statement matches multiple gold targets equally, it must be flagged AMBIGUOUS_MATCH
        ambiguous_gold = {
            'REF-A': {'statement': 'User notification alert service.', 'summary': 'User notification alert service.'},
            'REF-B': {'statement': 'User notification alert service for urgent warnings.', 'summary': 'User notification alert service.'}
        }
        pred_ambiguous = {
            'id': 'FR-050',
            'source_excerpt': 'User notification alert service.',
            'summary': 'User notification alert service.'
        }
        gid, status = match_prediction_to_gold(pred_ambiguous, ambiguous_gold)
        self.assertEqual(status, 'AMBIGUOUS_MATCH')
        self.assertIsNone(gid)

if __name__ == '__main__':
    unittest.main()
