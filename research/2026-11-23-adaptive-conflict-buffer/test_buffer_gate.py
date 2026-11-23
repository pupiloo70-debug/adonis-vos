import unittest
from dataclasses import replace
from buffer_gate import Candidate,evaluate

BASE=Candidate('synthetic-001',('local_patch',),True,True,True,True,True,True,True)

class TestBuffer(unittest.TestCase):
    def expect(self,c,action,reason):
        out=evaluate(c)
        self.assertEqual((out['action'],out['reason']),(action,reason))
        self.assertIsNone(out['total_score'])
        for k in ('external_action','automatic_guilt','automatic_immunity','benefit_from_obstruction','rules_changed','release_approved'):
            self.assertIs(out[k],False)
    def test_valid(self): self.expect(BASE,'LOCAL_CANDIDATE_ONLY','DUAL_GATE_PASSED')
    def test_provenance(self): self.expect(replace(BASE,source_provenance_preserved=False),'REVERT','RIGHTS_INVARIANT_FAILED')
    def test_dissent(self): self.expect(replace(BASE,dissent_preserved=False),'REVERT','RIGHTS_INVARIANT_FAILED')
    def test_controller(self): self.expect(replace(BASE,controller_duties_preserved=False),'REVERT','RIGHTS_INVARIANT_FAILED')
    def test_tech_regression(self): self.expect(replace(BASE,technical_pass=False),'REVERT','DUAL_GATE_FAILED')
    def test_rights_regression(self): self.expect(replace(BASE,rights_pass=False),'REVERT','DUAL_GATE_FAILED')
    def test_hash_missing(self): self.expect(replace(BASE,baseline_hash_verified=False),'HOLD','TRACEABILITY_NOT_VERIFIED')
    def test_snapshot_missing(self): self.expect(replace(BASE,rollback_snapshot_verified=False),'HOLD','TRACEABILITY_NOT_VERIFIED')
    def test_authority(self): self.expect(replace(BASE,changes=('authority',)),'HOLD','R3_SCOPE_REQUIRED')
    def test_evaluator(self): self.expect(replace(BASE,changes=('evaluation_gate',)),'HOLD','R3_SCOPE_REQUIRED')
    def test_conflict(self): self.expect(replace(BASE,conflict_count=3),'HOLD','CONFLICT_BUFFER_EXCEEDED')
    def test_new_failures(self): self.expect(replace(BASE,new_failures=1),'HOLD','CONFLICT_BUFFER_EXCEEDED')
    def test_soft_conflict(self):
        out=evaluate(replace(BASE,conflict_count=1))
        self.assertEqual(out['next_exploration_budget'],1)
    def test_no_conflict(self):
        out=evaluate(BASE)
        self.assertEqual(out['next_exploration_budget'],2)
if __name__=='__main__': unittest.main(verbosity=2)
