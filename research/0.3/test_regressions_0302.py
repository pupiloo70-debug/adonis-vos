import unittest
from vos_verify import verify

class NewCounterexamples(unittest.TestCase):
    def test_wrong_case_identity_is_blocked(self):
        r = verify({'kind':'case_law','claim_metadata':{'case_number':'SYNTH-002'},'evidence':{'court':'Synthetic Court','case_number':'SYNTH-001','decision_date':'2026-01-01','primary_text':'Synthetic holding only.','coverage':'FULL_DOCUMENT'}})
        self.assertNotEqual(r['status'], 'SOURCE_MATCH_CANDIDATE')

    def test_required_uncertainty_is_preserved(self):
        r = verify({'kind':'plaintiff_draft','purpose':'evidence_request','claim':'현재 자료만으로 인과관계가 입증되는 것은 아니다. 추가 감정이 필요하다.'})
        self.assertNotEqual(r['status'], 'CONCESSION_RISK')

    def test_excerpt_absence_is_not_misquotation(self):
        r = verify({'kind':'case_law','quoted_text':'다른 쪽에 있을 수 있는 문구','evidence':{'court':'Synthetic Court','case_number':'SYNTH-001','decision_date':'2026-01-01','primary_text':'일부 발췌','coverage':'EXCERPT'}})
        self.assertNotEqual(r['status'], 'MISQUOTED')

    def test_event_fraction_is_not_dose_incidence(self):
        r = verify({'kind':'paper','claim_scope':{'denominator_type':'DOSES'},'evidence':{'title':'Synthetic paper','authors':['Synthetic Author'],'year':2026,'primary_text':'Synthetic evidence','population':'A','intervention':'B','outcome':'C','denominator_type':'REPORTED_EVENTS'}})
        self.assertNotEqual(r['status'], 'SOURCE_MATCH_CANDIDATE')

if __name__ == '__main__':
    unittest.main()
