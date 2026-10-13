import unittest, sys, json
from pathlib import Path
sys.path.append('evaluation/multi_project/scripts')
from scorer import match_prediction_to_gold, global_match_requirements, canonicalize

class ScorerAdversarialAuditTests(unittest.TestCase):
    def setUp(self):
        self.gold_base = {
            'REF-01': {'statement': 'Drivers should be able to register and log in securely.', 'summary': 'Driver login', 'canonical': 'AUTHENTICATION'},
            'REF-02': {'statement': 'Drivers should be able to reserve an available charging slot before arriving.', 'summary': 'Reserve slot', 'canonical': 'BOOKING'},
            'REF-03': {'statement': 'The system shall maintain an immutable audit log of all transactions.', 'summary': 'Audit log', 'canonical': 'DATA'}
        }

    def test_case_01_unrelated_statement_same_id(self):
        pred = {'id': 'REF-01', 'source_excerpt': 'Drone delivery quadcopters must automatically calibrate wind resistance sensors.', 'summary': 'Drone calibration'}
        gid, status = match_prediction_to_gold(pred, self.gold_base)
        self.assertEqual(status, 'UNMATCHED')
        self.assertIsNone(gid)

    def test_case_02_reordered_renumbered_ids(self):
        pred = {'id': 'NEW-ID-999', 'source_excerpt': 'Drivers should be able to reserve an available charging slot before arriving.', 'summary': 'Reserve charging slot'}
        gid, status = match_prediction_to_gold(pred, self.gold_base)
        self.assertEqual(status, 'UNIQUE_MATCH')
        self.assertEqual(gid, 'REF-02')

    def test_case_03_generic_substring_shared_by_multiple_gold(self):
        gold = {
            'G-A': {'statement': 'The system shall provide notifications to users upon completion.', 'summary': 'Notification A'},
            'G-B': {'statement': 'The system shall provide notifications to operators upon fault.', 'summary': 'Notification B'}
        }
        pred = {'id': 'P-1', 'source_excerpt': 'The system shall provide notifications to all registered stakeholders.', 'summary': 'Notification'}
        gid, status = match_prediction_to_gold(pred, gold)
        self.assertIn(status, ['AMBIGUOUS_MATCH', 'UNMATCHED'])

    def test_case_04_duplicate_predictions_same_gold(self):
        gold = {'G-1': {'statement': 'Customers should be able to pay for orders securely using net banking.', 'summary': 'Net banking', 'canonical': 'PAYMENT'}}
        pred1 = {'id': 'P-1', 'source_excerpt': 'Customers should be able to pay for orders securely using net banking.', 'summary': 'Pay'}
        pred2 = {'id': 'P-2', 'source_excerpt': 'Customers should be able to pay for orders securely using net banking.', 'summary': 'Pay copy'}
        g1, s1 = match_prediction_to_gold(pred1, gold)
        g2, s2 = match_prediction_to_gold(pred2, gold)
        self.assertEqual(s1, 'UNIQUE_MATCH')
        self.assertEqual(s2, 'UNIQUE_MATCH')
        self.assertEqual(g1, g2)

    def test_case_05_similar_gold_distinct_meanings(self):
        gold = {
            'G-START': {'statement': 'Drivers should receive notifications when a charging session starts.', 'summary': 'Start alert'},
            'G-STOP': {'statement': 'Drivers should receive notifications when a charging session completes.', 'summary': 'Complete alert'}
        }
        pred_start = {'id': 'P-1', 'source_excerpt': 'Drivers should receive notifications when a charging session starts.', 'summary': 'Start alert'}
        gid, status = match_prediction_to_gold(pred_start, gold)
        self.assertEqual(status, 'UNIQUE_MATCH')
        self.assertEqual(gid, 'G-START')

    def test_case_06_matching_wording_wrong_module(self):
        gold = {'G-AUTH': {'statement': 'Patients should be able to register and log in securely.', 'summary': 'Login', 'canonical': 'AUTHENTICATION'}}
        pred = {'id': 'P-1', 'source_excerpt': 'Patients should be able to register and log in securely.', 'summary': 'Login'}
        gid, status = match_prediction_to_gold(pred, gold)
        self.assertEqual(status, 'UNIQUE_MATCH')
        pred_module = canonicalize('PAYMENT')
        gold_module = canonicalize(gold[gid]['canonical'])
        self.assertNotEqual(pred_module, gold_module)

    def test_case_07_gold_with_no_prediction(self):
        gold = {
            'G-1': {'statement': 'Patients should be able to register and log in securely.', 'summary': 'Login'},
            'G-2': {'statement': 'Patients should be able to order prescription refills directly.', 'summary': 'Refill'}
        }
        pred_list = [{'id': 'P-1', 'source_excerpt': 'Patients should be able to register and log in securely.', 'summary': 'Login'}]
        res = global_match_requirements(pred_list, gold)
        self.assertIn('G-2', res['unmatched_gold'])

    def test_case_08_one_unmatched_prediction(self):
        pred = {'id': 'P-X', 'source_excerpt': 'Completely novel telemetry requirement for quantum flux capacitors.', 'summary': 'Novel req'}
        gid, status = match_prediction_to_gold(pred, self.gold_base)
        self.assertEqual(status, 'UNMATCHED')

    def test_case_09_duplicate_gold_statements(self):
        duplicate_gold = {
            'G-DUP1': {'statement': 'System must support multi-factor authentication.', 'summary': 'MFA'},
            'G-DUP2': {'statement': 'System must support multi-factor authentication.', 'summary': 'MFA copy'}
        }
        pred = {'id': 'P-1', 'source_excerpt': 'System must support multi-factor authentication.', 'summary': 'MFA'}
        gid, status = match_prediction_to_gold(pred, duplicate_gold)
        self.assertEqual(status, 'AMBIGUOUS_MATCH')

    def test_case_10_empty_or_missing_source_excerpts(self):
        pred_empty = {'id': 'P-EMPTY', 'source_excerpt': '', 'description': '', 'summary': ''}
        gid, status = match_prediction_to_gold(pred_empty, self.gold_base)
        self.assertEqual(status, 'UNMATCHED')
        self.assertIsNone(gid)

    # --- REGRESSION SUITE: 6 SPECIFIED VERIFICATION TESTS ---

    def test_regression_01_partial_before_exact_precedence(self):
        """1. Partial prediction listed before an exact prediction for same gold requirement:
              Exact prediction MUST get the assignment, partial match must NOT steal it."""
        gold = {'G-AUDIT': {'statement': 'System shall maintain immutable audit logs of all security actions for seven years.', 'summary': 'Audit log full', 'canonical': 'DATA'}}
        pred_partial = {'id': 'P-01', 'source_excerpt': 'maintain immutable audit logs of all security actions for seven years and keep them safe', 'summary': 'Audit partial'}
        pred_exact = {'id': 'P-02', 'source_excerpt': 'System shall maintain immutable audit logs of all security actions for seven years.', 'summary': 'Audit exact'}
        
        # P-01 is passed FIRST in list
        res = global_match_requirements([pred_partial, pred_exact], gold)
        pairs = res['matched_pairs']
        self.assertEqual(len(pairs), 1, "Only 1 match should be awarded for 1 gold requirement")
        self.assertEqual(pairs[0]['pred_id'], 'P-02', "Exact match P-02 must take precedence over earlier partial match P-01")
        self.assertEqual(pairs[0]['match_type'], 'EXACT')

    def test_regression_02_order_invariance_on_reversal(self):
        """2. Reversing prediction order produces 100% identical evaluation results."""
        preds = [
            {'id': 'P-01', 'source_excerpt': 'Drivers should be able to register and log in securely.', 'summary': 'Login'},
            {'id': 'P-02', 'source_excerpt': 'Drivers should be able to reserve an available charging slot before arriving.', 'summary': 'Reserve slot'},
            {'id': 'P-03', 'source_excerpt': 'System shall display battery health status during charging session.', 'summary': 'Battery health'}
        ]
        gold = {
            'G-01': {'statement': 'Drivers should be able to register and log in securely.', 'summary': 'Login'},
            'G-02': {'statement': 'Drivers should be able to reserve an available charging slot before arriving.', 'summary': 'Reserve slot'}
        }
        res_fwd = global_match_requirements(preds, gold)
        res_rev = global_match_requirements(list(reversed(preds)), gold)
        
        fwd_pairs = sorted([(m['pred_id'], m['gold_id']) for m in res_fwd['matched_pairs']])
        rev_pairs = sorted([(m['pred_id'], m['gold_id']) for m in res_rev['matched_pairs']])
        self.assertEqual(fwd_pairs, rev_pairs, "Reversing prediction order must yield identical matches")
        self.assertEqual(res_fwd['unmatched_predictions'], res_rev['unmatched_predictions'])

    def test_regression_03_context_embedding_not_matched(self):
        """3. A prediction that mentions another requirement in background context is not incorrectly matched."""
        gold = {'G-SESS': {'statement': 'The system shall terminate user sessions after 15 minutes of inactivity.', 'summary': 'Session timeout', 'canonical': 'SECURITY'}}
        pred_warning = {
            'id': 'P-WARN',
            'source_excerpt': 'The system shall display a warning popup 2 minutes before the system shall terminate user sessions after 15 minutes of inactivity.',
            'summary': 'Session warning popup'
        }
        # In single-item evaluation:
        gid, status = match_prediction_to_gold(pred_warning, gold)
        self.assertEqual(status, 'UNMATCHED', "Context-embedded requirement must not be falsely matched to gold timeout")
        # In global matching:
        res = global_match_requirements([pred_warning], gold)
        self.assertEqual(len(res['matched_pairs']), 0)
        self.assertIn('P-WARN', res['unmatched_predictions'])

    def test_regression_04_similar_gold_different_meanings(self):
        """4. Two similar gold requirements with different meanings: generic statement flagged ambiguous."""
        gold = {
            'G-ADMIN-MFA': {'statement': 'System shall enforce multi-factor authentication for administrative accounts.', 'summary': 'Admin MFA', 'canonical': 'SECURITY'},
            'G-PAY-MFA': {'statement': 'System shall enforce multi-factor authentication for high-value financial transfers.', 'summary': 'Transfer MFA', 'canonical': 'PAYMENT'}
        }
        pred_generic = {'id': 'P-GEN', 'source_excerpt': 'System shall enforce multi-factor authentication.', 'summary': 'Generic MFA'}
        gid, status = match_prediction_to_gold(pred_generic, gold)
        self.assertIn(status, ['AMBIGUOUS_MATCH', 'UNMATCHED'])
        self.assertIsNone(gid, "Generic requirement must not arbitrarily bind to either specific gold item")

    def test_regression_05_duplicate_predictions_for_same_gold(self):
        """5. Duplicate predictions targeting the same gold requirement: handled globally with duplicate tracking."""
        gold = {'G-PAY': {'statement': 'Customers should be able to pay for orders securely using net banking.', 'summary': 'Net banking', 'canonical': 'PAYMENT'}}
        pred_a = {'id': 'P-01', 'source_excerpt': 'Customers should be able to pay for orders securely using net banking.', 'summary': 'Pay A'}
        pred_b = {'id': 'P-02', 'source_excerpt': 'Customers should be able to pay for orders securely using net banking.', 'summary': 'Pay B'}
        res = global_match_requirements([pred_a, pred_b], gold)
        self.assertEqual(len(res['matched_pairs']), 1, "Exactly one match should be awarded")
        self.assertEqual(len(res['duplicate_gold_matches']), 1, "Second prediction must be flagged in duplicate_gold_matches")

    def test_regression_06_ev_charging_58_exact_matches_intact(self):
        """6. All 58 current EV exact matches remain intact."""
        base_dir = Path('evaluation/multi_project')
        ev_pipe = json.loads((base_dir / 'runs/ev_charging_run_1c57d2e2/pipeline_output.json').read_text(encoding='utf-8'))
        ev_gold = json.loads((base_dir / 'benchmark/ev_charging/gold_reference.json').read_text(encoding='utf-8'))
        res = global_match_requirements(ev_pipe['requirements'], ev_gold['requirement_details'])
        self.assertEqual(len(res['matched_pairs']), 58, "All 58 EV requirements must match")
        self.assertEqual(len(res['unmatched_predictions']), 0, "Zero unmatched predictions in EV")
        self.assertTrue(all(m['match_type'] == 'EXACT' for m in res['matched_pairs']), "All 58 matches must be EXACT")

    def test_regression_07_multiple_competing_exact_candidates(self):
        """7. Multiple competing exact candidates: single prediction matching multiple gold statements marked ambiguous."""
        gold_competing = {
            'G-01': {'statement': 'System shall log all access requests.', 'summary': 'Log access 1', 'canonical': 'DATA'},
            'G-02': {'statement': 'System shall log all access requests.', 'summary': 'Log access 2', 'canonical': 'DATA'}
        }
        pred_single = {'id': 'P-01', 'source_excerpt': 'System shall log all access requests.', 'summary': 'Log access'}
        res = global_match_requirements([pred_single], gold_competing)
        self.assertIn('P-01', res['ambiguous_predictions'], "Prediction matching multiple exact gold items must be flagged ambiguous")
        self.assertEqual(len(res['matched_pairs']), 0, "No arbitrary assignment awarded when multiple exact targets compete")

    def test_regression_08_tied_partial_matches_resolution(self):
        """8. Tied partial matches for single gold requirement: assigns exactly one, tracks duplicate without double-counting."""
        gold_single = {'G-01': {'statement': 'The system shall process card payments securely through encrypted channels.', 'summary': 'Card payments', 'canonical': 'PAYMENT'}}
        pred_tie1 = {'id': 'P-A', 'source_excerpt': 'The system shall process card payments securely through encrypted channels now.', 'summary': 'Tie 1'}
        pred_tie2 = {'id': 'P-B', 'source_excerpt': 'The system shall process card payments securely through encrypted channels too.', 'summary': 'Tie 2'}
        res = global_match_requirements([pred_tie1, pred_tie2], gold_single)
        self.assertEqual(len(res['matched_pairs']), 1, "Exactly one match should be awarded for tied partial matches")
        self.assertEqual(len(res['duplicate_gold_matches']), 1, "Second tied prediction must be logged in duplicate_gold_matches")
        self.assertEqual(res['matched_pairs'][0]['pred_id'], 'P-A', "Deterministic tie-breaking picks first by sorted ID")

    def test_regression_09_ambiguous_and_unknown_module_canonicalization(self):
        """9. Ambiguous and unknown module canonicalization: empty/None mapped to UNASSIGNED, unknown strings uppercased."""
        self.assertEqual(canonicalize(''), 'UNASSIGNED')
        self.assertEqual(canonicalize(None), 'UNASSIGNED')
        self.assertEqual(canonicalize('Unknown Custom Subsystem'), 'UNKNOWN CUSTOM SUBSYSTEM')
        self.assertEqual(canonicalize('Payment Management'), 'PAYMENT')

if __name__ == '__main__':
    unittest.main(verbosity=2)

