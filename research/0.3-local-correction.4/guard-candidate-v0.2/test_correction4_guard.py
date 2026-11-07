"""Synthetic-only candidate acceptance tests, distinct from published correction.3 suite."""
import copy
import unittest
from correction4_guard import evaluate, DECISION_KINDS

KINDS = [
  'AUTOPSY_RECORD_PRESENT','CLINICAL_RECORD_ABSENT',
  'AUTOPSY_EXCLUDED_FOR_NO_CLINICAL_RECORD','INDEPENDENT_REVIEW_REFUSED',
  'ESSENTIAL_RECORD_NOT_PRODUCED','GAP_RELIED_ON_AGAINST_CLAIMANT',
  'INSTITUTIONAL_BENEFIT_RETAINED','CAUSATION_REASONING_UNEXPLAINED',
  'SUSCEPTIBILITY_NOT_ASSESSED',
]
CASE='SYNTHETIC-CASE-X'
TRACK='SYNTHETIC-TRACK-A'
SUBJECT='SYNTHETIC-PERSON-A'


def fixture():
  p={'synthetic': True, 'case_id': CASE, 'track_id': TRACK, 'subject_id': SUBJECT,
     'sources': {}, 'support_reviews': []}
  r={'id': 'R1', 'case_id': CASE, 'track_id': TRACK, 'subject_id':SUBJECT,
     'purpose': 'VICTIM_SUPPORT','controller': 'SYNTHETIC_CONTROLLER',
     'decision_body': 'SYNTHETIC_COURT', 'observations':[], 'remediation_events': []}
  for i, kind in enumerate(KINDS):
    ref=f'SOURCE-{i}'
    quote=f'Entirely fictional source sentence number {i}.'
    if kind in DECISION_KINDS:
      actor, role, action, stmt = 'SYNTHETIC_COURT','DECISION_BODY','DECISION','DECISION_RECORD'
    elif kind == 'ESSENTIAL_RECORD_NOT_PRODUCED':
      actor, role, action, stmt = 'SYNTHETIC_CONTROLLER','CONTROLLER','NONPRODUCTION','CONTROLLER_RECORD'
    elif kind == 'INSTITUTIONAL_BENEFIT_RETAINED':
      actor, role, action, stmt = 'SYNTHETIC_WITNESS','WITNESS','ASSESSMENT','WITNESS_REPORT'
    else:
      actor, role, action, stmt = 'SYNTHETIC_WITNESS','WITNESS','SOURCE_REPORT','WITNESS_REPORT'
    material='SYNTHETIC-AUTOPSY' if i in (0,2) else 'SYNTHETIC-GENERAL'
    p['sources'][ref]={'primary_text':quote,'locator':f'fictional paragraph {i}',
             'source_class':'PRIMARY_OFFICIAL_RECORD','case_id':CASE,'track_id':TRACK,
             'subject_id':SUBJECT,'material_id':material,'actor_id':actor,
             'event_type':action,'statement_role':stmt}
    row={'id':f'O{i}', 'kind':kind,'quoted_text':quote,'source_ref':ref,
         'case_id':CASE,'track_id':TRACK,'subject_id':SUBJECT,'material_id':material,
         'actor_id':actor,'actor_role':role,'event_type':action,'statement_role':stmt}
    if kind in DECISION_KINDS:
      row['decision_status']=DECISION_KINDS[kind]
    r['observations'].append(row)
  p['support_reviews'].append(r)
  return p


def run(p):return evaluate(p)['reviews'][0]
def codes(p):return {w['code'] for w in run(p)['warnings']}

class GuardTests(unittest.TestCase):
  def test_baseline_five_warnings_are_review_only(self):
    p=fixture(); before=copy.deepcopy(p)
    out=evaluate(p);r=out['reviews'][0]
    self.assertEqual(len(r['warnings']),5)
    self.assertEqual(len(r['accepted_observations']),9)
    self.assertEqual(len(r['held_observations']),0)
    self.assertFalse(out['legal_or_medical_finding'])
    self.assertIsNone(out['total_score'])
    self.assertEqual(before,p)

  def test_P01_opponent_request_not_court_refusal(self):
    p=fixture();o=p['support_reviews'][0]['observations'][3]; s=p['sources']['SOURCE-3']
    o.update(actor_id='SYNTHETIC_OPPONENT',actor_role='OPPONENT',event_type='REQUEST',statement_role='OPPONENT_CLAIM',decision_status='REQUEST_ONLY')
    s.update(actor_id='SYNTHETIC_OPPONENT',event_type='REQUEST',statement_role='OPPONENT_CLAIM')
    self.assertNotIn('CIRCULAR_BURDEN_SHIFT_WARNING',codes(p))
    self.assertTrue(any(x['id']=='O3' for x in run(p)['held_observations']))

  def test_P01_label_and_source_event_conflict(self):
    p=fixture();p['sources']['SOURCE-3']['event_type']='REQUEST'
    self.assertNotIn('CIRCULAR_BURDEN_SHIFT_WARNING',codes(p))

  def test_P02_one_foreign_observation_does_not_erase_independent_warnings(self):
    p=fixture(); q=copy.deepcopy(p['support_reviews'][0]['observations'][0]);
    q.update(id='FOREIGN', case_id='OTHER-CASE',source_ref='FOREIGN-SOURCE')
    p['sources']['FOREIGN-SOURCE']=dict(p['sources']['SOURCE-0'],case_id='OTHER-CASE')
    p['support_reviews'][0]['observations'].append(q)
    self.assertEqual(len(codes(p)),5)
    self.assertTrue(any(x['id']=='FOREIGN' for x in run(p)['held_observations']))

  def test_P02_conflicted_core_evidence_only_blocks_dependent_warning(self):
    p=fixture();p['sources']['SOURCE-0']['case_id']='OTHER-CASE'
    self.assertNotIn('AUTOPSY_EVIDENCE_EXCLUSION_WARNING',codes(p))
    self.assertIn('CIRCULAR_BURDEN_SHIFT_WARNING',codes(p))

  def test_P03_arbitrary_renamed_court_does_not_reassign_judicial_warning(self):
    p=fixture();p['support_reviews'][0]['decision_body']='UNLINKED-OTHER-BODY'
    self.assertNotIn('HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING',codes(p))
    self.assertTrue(any('DECISION_BODY_UNLINKED' in x['reason'] for x in run(p)['held_observations']))

  def test_P04_different_person_same_case_autopsy_is_held(self):
    p=fixture();p['sources']['SOURCE-0']['subject_id']='SYNTHETIC-PERSON-B'
    self.assertNotIn('AUTOPSY_EVIDENCE_EXCLUSION_WARNING',codes(p))
    self.assertIn('CIRCULAR_BURDEN_SHIFT_WARNING',codes(p))

  def test_P04_material_id_mismatch_even_if_person_matches(self):
    p=fixture();p['sources']['SOURCE-0']['material_id']='SYNTHETIC-AUTOPSY-OTHER'
    self.assertNotIn('AUTOPSY_EVIDENCE_EXCLUSION_WARNING',codes(p))

  def test_nested_cross_case_hidden_in_source(self):
    p=fixture();p['sources']['SOURCE-0']['metadata']={'case_id':'OTHER-CASE'}
    self.assertNotIn('AUTOPSY_EVIDENCE_EXCLUSION_WARNING',codes(p))

  def test_P02_direct_dependency_held_if_parent_source_invalid(self):
    p=fixture();p['sources']['SOURCE-4']['locator']=''
    p['support_reviews'][0]['observations'][8]['depends_on']=['O4']
    r=run(p); ids={v['id'] for v in r['held_observations']}
    self.assertTrue({'O4','O8'} <= ids)
    self.assertNotIn('INDIVIDUAL_SUSCEPTIBILITY_REVIEW_OPEN', codes(p))

  def test_dependency_cycle_held_no_hang(self):
    p=fixture();p['support_reviews'][0]['observations'][7]['depends_on']=['O8'];p['support_reviews'][0]['observations'][8]['depends_on']=['O7']
    r=run(p);self.assertTrue(any('DEPENDENCY_CYCLE' in x['reason'] for x in r['held_observations']))

  def test_P04_missing_observation_subject_cannot_be_borrowed(self):
    p=fixture();p['support_reviews'][0]['observations'][0].pop('subject_id')
    self.assertNotIn('AUTOPSY_EVIDENCE_EXCLUSION_WARNING',codes(p))

  def test_P04_missing_source_subject_cannot_be_borrowed(self):
    p=fixture();p['sources']['SOURCE-0'].pop('subject_id')
    self.assertNotIn('AUTOPSY_EVIDENCE_EXCLUSION_WARNING',codes(p))

  def test_P05_grant_only_not_access_completed(self):
    p=fixture();self.add_event(p,'E1','REVIEW_GRANTED')
    state=run(p)['remediation']['question_material_states'][0]
    self.assertEqual(state['status'],'GRANT_ONLY_ACCESS_NOT_ESTABLISHED')
    self.assertTrue(run(p)['remediation']['prior_burdens_preserved'])

  def test_P05_grant_followed_by_reported_partial_access_not_full(self):
    p=fixture();self.add_event(p,'E1','REVIEW_GRANTED', '2026-11-01T11:00:00+09:00')
    self.add_event(p,'E2','ACCESS_PARTIAL','2026-11-02T12:00:00+09:00')
    x=run(p)['remediation']['question_material_states'][0]
    self.assertEqual(x['status'],'PARTIAL_ACCESS_REPORTED_REMAINDER_OPEN')
    self.assertEqual(x['event_history'],['E1','E2'])
    self.assertIsNone(run(p)['remediation']['previous_cost_amount'])

  def test_P05_new_reported_access_still_requires_authentication(self):
    p=fixture();self.add_event(p,'E1','ACCESS_PERFORMED')
    self.assertEqual(run(p)['remediation']['question_material_states'][0]['status'],
                     'ACCESS_REPORTED_AUTHENTICATION_PENDING')

  def test_P05_foreign_subject_remedy_event_held(self):
    p=fixture();self.add_event(p,'E1','REVIEW_GRANTED')
    p['sources']['REMEDY-E1']['subject_id']='SYNTHETIC-PERSON-B'
    self.assertEqual(run(p)['remediation']['question_material_states'],[])
    self.assertEqual(len(run(p)['remediation']['held_events']),1)

  def test_missing_locator_cannot_lead_to_judicial_pattern(self):
    p=fixture();p['sources']['SOURCE-3'].pop('locator')
    self.assertNotIn('HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING',codes(p))

  def test_unhashable_malformed_input_is_held_not_crash(self):
    p=fixture();p['support_reviews'][0]['observations'][0]['source_ref']=['not','a','ref']
    r=run(p)
    self.assertTrue(any(x['id']=='O0' for x in r['held_observations']))
    self.assertNotIn('AUTOPSY_EVIDENCE_EXCLUSION_WARNING',codes(p))

  def test_unhashable_observation_kind_is_held_not_crash(self):
    p=fixture();p['support_reviews'][0]['observations'][0]['kind']=['AUTOPSY_RECORD_PRESENT']
    self.assertTrue(any(x['id']=='O0' for x in run(p)['held_observations']))

  def test_malformed_dependency_collection_held(self):
    p=fixture();p['support_reviews'][0]['observations'][7]['depends_on']=None
    self.assertTrue(any('INVALID_DEPENDENCY_FORMAT' in x['reason'] for x in run(p)['held_observations']))

  def test_malformed_observation_and_remediation_lists_fail_closed(self):
    p=fixture();p['support_reviews'][0]['observations']=None
    self.assertFalse(run(p)['warnings'])
    p=fixture();p['support_reviews'][0]['remediation_events']=None
    self.assertEqual(len(run(p)['remediation']['held_events']),1)

  def test_remedy_nonstring_question_id_held(self):
    p=fixture();self.add_event(p,'E1','REVIEW_GRANTED')
    p['support_reviews'][0]['remediation_events'][0]['question_id']=[]
    self.assertFalse(run(p)['remediation']['question_material_states'])

  def test_real_case_rejected_no_private_input(self):
    p=fixture();p['synthetic']=False
    with self.assertRaisesRegex(ValueError,'SYNTHETIC_ONLY'):evaluate(p)

  def test_deterministic_malformed_input_fuzz_1000(self):
    import random
    rng=random.Random(41)
    bad=[None,[],{},0,1.5,False,'','UNKNOWN']
    for i in range(1000):
      p=fixture()
      area=rng.choice(['observation','source','review','event'])
      if area=='observation':
        obj=p['support_reviews'][0]['observations'][rng.randrange(9)]
        field=rng.choice(['id','kind','source_ref','quoted_text','subject_id','case_id','material_id','actor_id','event_type','depends_on'])
      elif area=='source':
        obj=p['sources']['SOURCE-'+str(rng.randrange(9))]
        field=rng.choice(['source_class','primary_text','locator','subject_id','case_id','actor_id','event_type','metadata'])
      elif area=='review':
        obj=p['support_reviews'][0]
        field=rng.choice(['id','purpose','controller','decision_body','case_id','track_id','subject_id','observations','remediation_events'])
      else:
        self.add_event(p,'E1','REVIEW_GRANTED')
        obj=p['support_reviews'][0]['remediation_events'][0]
        field=rng.choice(['id','type','source_ref','quoted_text','subject_id','case_id','material_id','question_id','occurred_at'])
      obj[field]=rng.choice(bad)
      try:
        evaluate(p)
      except ValueError:
        pass  # Controlled input rejection is valid.
      except Exception as exc:
        self.fail(f'Uncontrolled exception at fuzz input {i}: {area}.{field}: {exc}')

  def add_event(self,p,eid,kind,date='2026-11-01T12:00:00+09:00'):
    ref='REMEDY-'+eid;quote=f'Synthetic remedy event {eid}.'
    p['sources'][ref]={'source_class':'CONTEMPORANEOUS_RECORD','primary_text':quote,
       'locator':'synthetic remedy record','case_id':CASE,'track_id':TRACK,
       'subject_id':SUBJECT,'material_id':'MAT-7','question_id':'Q-7'}
    p['support_reviews'][0]['remediation_events'].append({'id':eid,'type':kind,
       'source_ref':ref,'quoted_text':quote,'case_id':CASE,'track_id':TRACK,
       'subject_id':SUBJECT,'material_id':'MAT-7','question_id':'Q-7','occurred_at':date})

if __name__=='__main__':unittest.main(verbosity=2)
