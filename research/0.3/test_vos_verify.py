import unittest
from vos_verify import verify
class Regression(unittest.TestCase):
 def test_fake_case_no_original(self):
  r=verify({'kind':'case_law','id':'C01','claim':'대법원 2099두99999','evidence':{'court':'대법원','case_number':'2099두99999','decision_date':'2099-01-01'}})
  self.assertEqual((r['status'],r['action']),('UNVERIFIED','BLOCK_CITATION_OR_REVISE_CLAIM'))
 def test_quote_mismatch(self):
  r=verify({'kind':'case_law','quoted_text':'인용된 문구','evidence':{'court':'법원','case_number':'1','decision_date':'2020','primary_text':'다른 문구','coverage':'FULL_DOCUMENT'}})
  self.assertEqual(r['status'],'MISQUOTED')
 def test_paper_scope(self):
  r=verify({'kind':'paper','claim_scope':{'intervention':'A백신'},'evidence':{'title':'논문','authors':'연구자','year':2024,'primary_text':'원문','population':'성인','intervention':'B백신','outcome':'발열'}})
  self.assertEqual(r['status'],'MISAPPLIED_EVIDENCE')
 def test_concession(self):
  r=verify({'kind':'plaintiff_draft','purpose':'evidence_request','claim':'이것만으로 인과관계가 입증되는 것은 아니다.'})
  self.assertEqual(r['status'],'REQUIRED_LIMIT_REVIEW')
 def test_asymmetry(self):
  r=verify({'kind':'plaintiff_draft','claim':'자료 제출 요청','evidence_control':'institution'})
  self.assertIn('EVIDENCE_ASYMMETRY_NOT_ADDRESSED',[x['code'] for x in r['flags']])
 def test_no_false_verified(self):
  r=verify({'kind':'case_law','evidence':{'court':'법원','case_number':'1','decision_date':'2020','primary_text':'판결문'}})
  self.assertNotEqual(r['status'],'VERIFIED')
if __name__=='__main__':unittest.main()
