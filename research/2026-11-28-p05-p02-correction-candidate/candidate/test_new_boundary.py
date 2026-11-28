import unittest,json,copy
from pathlib import Path
from correction4_guard import evaluate
CASES=json.loads((Path(__file__).parent.parent/'fixtures.json').read_text())
class NewBoundary(unittest.TestCase):pass

def test(case):
 def check(self):
  p=case['project'];before=copy.deepcopy(p);out=evaluate(p);self.assertEqual(p,before);self.assertIsNone(out['total_score']);self.assertFalse(out['legal_or_medical_finding']);self.assertFalse(out['release_or_R3_approval_changed']);self.assertFalse(out['external_execution']);rs=out['reviews'];want=case['expected']
  if want=='HOLD_MALFORMED':
   self.assertEqual(len(rs),2);self.assertEqual(rs[0]['status'],'REVIEW_SCOPE_HELD');self.assertIn('REVIEW_NOT_OBJECT',rs[0]['held_reason']);self.assertEqual(len(rs[1]['warnings']),5);return
  if want=='HOLD_DUPLICATE':
   self.assertEqual(len(rs),3);self.assertTrue(all(r['status']=='REVIEW_SCOPE_HELD' and 'INVALID_OR_DUPLICATE_REVIEW_ID' in r['held_reason'] for r in rs[:2]));self.assertEqual(len(rs[2]['warnings']),5);return
  r=rs[0];self.assertEqual(len(r['warnings']),5);rem=r['remediation'];self.assertTrue(rem['prior_burdens_preserved']);self.assertFalse(rem['access_truth_independently_authenticated']);state=rem['question_material_states'][0]
  if want=='HOLD_E2':
   self.assertEqual(state['status'],'ACCESS_REVOKED_REVIEW_OPEN');self.assertEqual(state['event_history'],['E1']);self.assertIn('E2',[e['id'] for e in rem['held_events']]);self.assertTrue(r['unresolved_source_and_provenance_questions']);return
  self.assertEqual(state['status'],'ACCESS_REPORTED_AUTHENTICATION_PENDING');self.assertEqual(state['event_history'],['E1','E2']);self.assertEqual(rem['held_events'],[])
  self.assertEqual(state['event_batches'][-1]['time_binding_by_event']['E2'],'SOURCE_TIME_MATCHED_NOT_AUTHENTICATED' if want=='ACCEPT_BOUND' else 'REPORTED_TIME_NOT_SOURCE_BOUND')
 return check
for c in CASES:setattr(NewBoundary,'test_'+c['id'],test(c))
