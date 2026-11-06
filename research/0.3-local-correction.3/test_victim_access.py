"""Synthetic harm-prevention and negative-control regressions; no real cases."""
import copy
import json
from pathlib import Path
import unittest
from vos_verify import analyze, invariants, run_consistency_loop

NOW = '2026-11-06T12:00:00+09:00'
CASE, TRACK = 'SYNTHETIC-AUTOPSY-A', 'SYNTHETIC-ADMIN-A'
OBS = [
    ('AUTOPSY_RECORD_PRESENT', 'Synthetic autopsy material is recorded.'),
    ('CLINICAL_RECORD_ABSENT', 'Synthetic sudden death has no prior clinical diagnosis.'),
    ('AUTOPSY_EXCLUDED_FOR_NO_CLINICAL_RECORD', 'Synthetic refusal requires a clinical record instead of autopsy evidence.'),
    ('INDEPENDENT_REVIEW_REFUSED', 'Synthetic independent review request was refused.'),
    ('ESSENTIAL_RECORD_NOT_PRODUCED', 'Synthetic controller has not produced the requested original material.'),
    ('GAP_RELIED_ON_AGAINST_CLAIMANT', 'Synthetic decision relies on the resulting proof gap against the claimant.'),
    ('INSTITUTIONAL_BENEFIT_RETAINED', 'Synthetic institution retains the procedural benefit of the untested conclusion.'),
    ('CAUSATION_REASONING_UNEXPLAINED', 'Synthetic decision does not state its case-specific assessment method.'),
    ('SUSCEPTIBILITY_NOT_ASSESSED', 'Synthetic prior symptoms and individual susceptibility were not assessed.'),
]

def fixture(kinds=None, *, source_class='PRIMARY_OFFICIAL_RECORD'):
    chosen = [x for x in OBS if kinds is None or x[0] in kinds]
    project = {'schema':'ADONIS-VOS-0.3-INPUT/1.0', 'case_id':CASE, 'track_id':TRACK,
               'synthetic':True, 'question':'Synthetic autopsy access and independent assessment',
               'sources':{}, 'facts':[], 'routes':[], 'items':[], 'review_nodes':{},
               'requested_remedies':['Synthetic independent review and restoration of verification opportunity'],
               'support_reviews':[]}
    review = {'id':'ACCESS-A', 'purpose':'VICTIM_SUPPORT', 'case_id':CASE, 'track_id':TRACK,
              'controller':'SYNTHETIC_CONTROLLER', 'decision_body':'SYNTHETIC_COURT', 'observations':[]}
    for i,(kind, quote) in enumerate(chosen):
        ref='SOURCE-'+str(i)
        project['sources'][ref] = {'source_class':source_class, 'primary_text':quote,
                                  'locator':'synthetic paragraph '+str(i), 'case_id':CASE, 'track_id':TRACK}
        review['observations'].append({'id':'O-'+str(i), 'kind':kind,'quoted_text':quote,
                                       'source_ref':ref,'case_id':CASE,'track_id':TRACK})
    project['support_reviews']=[review]
    return project

def reviewed(p):
    return analyze(p, NOW)['support_packet']['access_reviews'][0]

def codes(r):return {x['code'] for x in r['warnings']}

class VictimAccessTests(unittest.TestCase):
    def test_autopsy_only_death_has_access_warning_and_no_credibility_downgrade(self):
        r=reviewed(fixture());self.assertIn('AUTOPSY_EVIDENCE_EXCLUSION_WARNING', codes(r))
        self.assertFalse(r['clinical_record_absence_reduces_victim_credibility'])
        self.assertFalse(r['claimant_restatement_required'])
    def test_absent_clinical_record_alone_does_not_accuse_court(self):
        r=reviewed(fixture({'AUTOPSY_RECORD_PRESENT','CLINICAL_RECORD_ABSENT'}))
        self.assertFalse(r['warnings']);self.assertFalse(r['clinical_record_absence_reduces_victim_credibility'])
    def test_circular_gap_is_traceable_to_each_observation(self):
        r=reviewed(fixture());w=next(w for w in r['warnings']if w['code']=='CIRCULAR_BURDEN_SHIFT_WARNING')
        self.assertEqual(len(w['basis_observations']),3);self.assertEqual(len(w['source_refs']),3)
    def test_cartel_warning_is_strong_but_not_collusion_or_crime_finding(self):
        r=reviewed(fixture());self.assertIn('HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING',codes(r))
        self.assertIn('사법 카르텔', ' '.join(x['label_ko']for x in r['warnings']))
        self.assertFalse(r['coordination_or_criminal_cartel_established']);self.assertFalse(r['sanction_decided'])
    def test_missing_controller_keeps_identification_work_with_ai_and_holds_cartel_label(self):
        p=fixture();del p['support_reviews'][0]['controller'];r=reviewed(p)
        self.assertTrue(r['controller_identification_pending'])
        self.assertNotIn('HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING',codes(r))
        self.assertFalse(r['claimant_restatement_required'])
    def test_denial_alone_is_not_cartel_warning(self):
        r=reviewed(fixture({'INDEPENDENT_REVIEW_REFUSED'}));self.assertFalse(r['warnings'])
    def test_benefit_without_court_does_not_receive_judicial_cartel_label(self):
        p=fixture();del p['support_reviews'][0]['decision_body'];self.assertNotIn('HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING',codes(reviewed(p)))
    def test_no_material_production_gap_no_circular_warning(self):
        p=fixture({k for k,_ in OBS if k!='ESSENTIAL_RECORD_NOT_PRODUCED'});self.assertNotIn('CIRCULAR_BURDEN_SHIFT_WARNING',codes(reviewed(p)))
    def test_no_benefit_source_does_not_assert_benefit_reversal(self):
        p=fixture({k for k,_ in OBS if k!='INSTITUTIONAL_BENEFIT_RETAINED'});r=reviewed(p)
        self.assertNotIn('HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING',codes(r))
        self.assertEqual(r['benefit_reversal_review']['status'],'NO_SOURCE_LINKED_BENEFIT_TRIGGER')
    def test_claimant_testimony_can_raise_review_without_official_permission(self):
        r=reviewed(fixture(source_class='CLAIMANT_TESTIMONY'));self.assertIn('CIRCULAR_BURDEN_SHIFT_WARNING',codes(r))
        self.assertTrue(all(not o['truth_or_independence_authenticated']for o in r['observations']))
    def test_ai_agreement_cannot_supply_primary_pattern_evidence(self):
        r=reviewed(fixture(source_class='AI_GENERATED_ANALYSIS'));self.assertFalse(r['warnings']);self.assertTrue(r['observations'])
    def test_missing_source_is_preserved_and_not_negative_evidence_against_victim(self):
        p=fixture();p['sources']={};r=reviewed(p);self.assertFalse(r['warnings'])
        self.assertEqual(len(r['observations']),len(OBS));self.assertFalse(r['claimant_restatement_required'])
    def test_misquote_cannot_trigger_circular_warning(self):
        p=fixture();p['support_reviews'][0]['observations'][4]['quoted_text']='not in supplied text'
        self.assertNotIn('CIRCULAR_BURDEN_SHIFT_WARNING',codes(reviewed(p)))
    def test_no_locator_prevents_source_linked_trigger(self):
        p=fixture();p['sources']['SOURCE-4'].pop('locator');self.assertNotIn('CIRCULAR_BURDEN_SHIFT_WARNING',codes(reviewed(p)))
    def test_cross_case_autopsy_source_is_quarantined_not_borrowed(self):
        p=fixture();p['sources']['SOURCE-0']['case_id']='SYNTHETIC-OTHER-CHILD';r=reviewed(p)
        self.assertEqual(r['status'],'SCOPE_REVIEW_REQUIRED');self.assertFalse(r['warnings'])
    def test_cross_procedure_and_nested_conflicts_do_not_leak_warnings(self):
        p=fixture();p['support_reviews'][0]['observations'][0]['track_id']='SYNTHETIC-CIVIL';self.assertFalse(reviewed(p)['warnings'])
        p=fixture();p['sources']['SOURCE-0']['nested']={'case_id':'OTHER','track_id':TRACK};self.assertFalse(reviewed(p)['warnings'])
    def test_recognized_relief_is_not_reopened_by_method_review(self):
        p=fixture();ref='GRANTED';q='Synthetic recognized relief remains protected.'
        p['sources'][ref]={'source_class':'PRIMARY_OFFICIAL_RECORD','primary_text':q,'locator':'grant paragraph','case_id':CASE,'track_id':TRACK}
        p['support_reviews'][0]['observations'].append({'id':'GRANT-OBS','kind':'RECOGNIZED_RELIEF_EXISTS','source_ref':ref,'quoted_text':q,'case_id':CASE,'track_id':TRACK})
        r=reviewed(p);self.assertTrue(r['recognized_relief_preserved']);self.assertFalse(r['recognized_relief_reassessment_requested'])
    def test_institution_gets_response_and_concession_requests_not_victim(self):
        r=reviewed(fixture());self.assertTrue(r['institutional_response_requirements']);self.assertTrue(r['institutional_concession_candidates'])
        self.assertFalse(r['victim_concession_required'])
    def test_benefit_reversal_is_counsel_remedy_review_not_automatic_seizure(self):
        r=reviewed(fixture());b=r['benefit_reversal_review'];self.assertEqual(b['status'],'COUNSEL_REVIEW_REQUIRED')
        self.assertIsNone(b['amount']);self.assertFalse(b['unjust_enrichment_legally_established']);self.assertFalse(b['repayment_or_confiscation_executed'])
    def test_generated_draft_stops_adding_blanket_concession_but_keeps_review_notes(self):
        p=analyze(fixture(),NOW)['support_packet'];self.assertTrue(p['review_notes'])
        self.assertNotIn('자료 미확보는 곧바로 사실 부존재',p['draft_text']);self.assertIn('원고의 검증권·구제 요청',p['draft_text'])
        self.assertEqual(p['generated_blanket_concessions'],[])
    def test_supplied_material_limit_is_preserved_not_automatically_deleted(self):
        p=fixture();quote='현재 자료만으로 인과관계가 확정된 것은 아니다. 독립 검경이 필요하다.'
        p['items']=[{'id':'CAVEAT','kind':'plaintiff_draft','claim':quote,'case_id':CASE,'track_id':TRACK,'statement_role':'EPISTEMIC_CAVEAT'}]
        out=analyze(p,NOW);self.assertIn(quote,out['support_packet']['draft_text']);self.assertFalse(out['support_packet']['automatic_deletion'])
    def test_unknown_label_duplicate_ids_and_wrong_purpose_rejected(self):
        for change in ['kind','duplicate','purpose']:
            p=fixture();r=p['support_reviews'][0]
            if change=='kind':r['observations'][0]['kind']='CRIME_CONFIRMED'
            elif change=='duplicate':r['observations'].append(copy.deepcopy(r['observations'][0]))
            else:r['purpose']='REOPEN_RECOGNIZED_VICTIM_RELIEF'
            with self.subTest(change=change),self.assertRaises(ValueError):analyze(p,NOW)
    def test_clinical_and_source_records_are_not_mutated(self):
        p=fixture();before=copy.deepcopy(p);run_consistency_loop(p,NOW);self.assertEqual(p,before)
    def test_no_automatic_state_approval_or_score_change(self):
        r=run_consistency_loop(fixture(),NOW);self.assertEqual(invariants(r),[])
        self.assertIsNone(r['total_score']);self.assertFalse(r['approval_status_changed']);self.assertEqual(r['deployment_status'],'NOT_DEPLOYED')
    def test_invariant_detects_tampered_guilt_and_relief_and_repayment(self):
        r=analyze(fixture(),NOW)
        for field in ['coordination_or_criminal_cartel_established','recognized_relief_reassessment_requested']:
            changed=copy.deepcopy(r);changed['support_packet']['access_reviews'][0][field]=True
            self.assertIn('UNAUTHORIZED_JUDICIAL_OR_CRIMINAL_FINDING',invariants(changed))
        r['support_packet']['access_reviews'][0]['benefit_reversal_review']['repayment_or_confiscation_executed']=True
        self.assertIn('UNAUTHORIZED_BENEFIT_EXECUTION',invariants(r))

if __name__=='__main__':unittest.main()
