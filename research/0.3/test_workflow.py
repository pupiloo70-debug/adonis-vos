import copy
import unittest
from vos_verify import verify, review_route, build_support_packet, run_consistency_loop, invariants

NOW = "2026-11-03T12:00:00+09:00"

def paper():
    return {"id":"P-SYNTH","kind":"paper","claim_metadata":{"title":"Synthetic study"},
            "claim_scope":{"population":"A","intervention":"B","outcome":"C"},
            "evidence":{"title":"Synthetic study","authors":["Synthetic Author"],"year":2026,
                        "primary_text":"Synthetic text only.","population":"A","intervention":"B","outcome":"C",
                        "source_ref":"S1","locator":"p1","coverage":"FULL_DOCUMENT"}}

def route():
    return {"id":"R-SYNTH","question":"検証用 synthetic record?","source_refs":["S1"],
            "prior_control_ref":"S1","availability":"NOT_PRODUCED","controller":"Synthetic institution",
            "coordinator":"Technical support role","current_evidence_state":"R2.6-1",
            "opened_at":"2026-10-01T12:00:00+09:00","next_due_at":"2026-11-01T12:00:00+09:00",
            "clock_type":"INTERNAL_TARGET","clock_basis_ref":"DESIGN",
            "historical_first_request_at":"2026-08-01"}

def project():
    return {"synthetic":True,"question":"Synthetic production request","sources":{
            "S1":{"source_class":"PRIMARY_OFFICIAL_RECORD","origin_id":"ORIGIN1"},
            "DESIGN":{"source_class":"PRIMARY_OFFICIAL_RECORD","origin_id":"DESIGN1"}},
            "items":[paper()],"routes":[route()],
            "facts":[{"id":"F1","text":"原자료의 추가 대조가 필요함 — 합성 사실",
                      "source_ref":"S1","epistemic_status":"SOURCE_STATED","adverse":True}]}

class WorkflowCounterexamples(unittest.TestCase):
    def test_absent_case_identity_is_missing_not_conflicting(self):
        r=verify({'kind':'case_law','claim_metadata':{'court':'SYNTHETIC COURT'},'evidence':{}})
        self.assertEqual(r['status'],'UNVERIFIED')

    def test_absent_text_cannot_prove_misquotation(self):
        r=verify({'kind':'case_law','quoted_text':'Synthetic quote','evidence':{'coverage':'FULL_DOCUMENT'}})
        self.assertEqual(r['status'],'UNVERIFIED')

    def test_doi_is_not_full_text(self):
        p=paper(); p["evidence"].pop("primary_text"); p["evidence"]["doi"]="10.SYNTH/example"
        self.assertEqual(verify(p)["status"], "UNVERIFIED")

    def test_statistic_wrong_arithmetic(self):
        p=paper();p["claimed_statistic"]={"numerator":1,"denominator":100,"percent":10}
        self.assertEqual(verify(p)["status"], "STATISTIC_CONFLICT")

    def test_zero_denominator(self):
        p=paper();p["claimed_statistic"]={"numerator":0,"denominator":0,"percent":0}
        self.assertEqual(verify(p)["status"], "STATISTIC_CONFLICT")

    def test_nonfinite_statistic(self):
        p=paper();p["claimed_statistic"]={"numerator":"NaN","denominator":100,"percent":1}
        self.assertEqual(verify(p)["status"], "STATISTIC_CONFLICT")

    def test_causal_risk_not_spontaneous_report_fraction(self):
        p=paper();p["claim_scope"]["causality_level"]="CAUSED";p["evidence"]["causality_level"]="SUSPECTED_REPORT"
        self.assertEqual(verify(p)["status"], "MISAPPLIED_EVIDENCE")

    def test_source_hash_conflict(self):
        p=paper();p["evidence"]["expected_text_sha256"]="0"*64
        self.assertEqual(verify(p)["status"], "SOURCE_INTEGRITY_CONFLICT")

    def test_unicode_quote_whitespace_not_false_misquote(self):
        p=paper();p["quoted_text"]="Synthetic  text\nonly."
        self.assertEqual(verify(p)["status"], "SOURCE_MATCH_CANDIDATE")
        self.assertFalse(verify(p)["source_verified_externally"])

    def test_required_uncertainty_text_not_deleted(self):
        text="현재 자료만으로 확정된 것은 아니다. 독립 검토를 요청한다."
        r=verify({"kind":"plaintiff_draft","claim":text})
        self.assertEqual(r["original_text"], text)
        self.assertFalse(r["automatic_deletion"])

    def test_concession_is_review_prompt_not_automatic_falsification(self):
        r=verify({"kind":"plaintiff_draft","claim":"자료가 없으니 원고의 입증 실패이다."})
        self.assertEqual(r["status"], "CONCESSION_RISK")
        self.assertFalse(r["automatic_deletion"])

    def test_adverse_fact_is_retained(self):
        r=build_support_packet(project())
        self.assertTrue(r["fact_ledger"][0]["adverse"])
        self.assertIn("불리한 사실 포함",r["draft_text"])

    def test_unlinked_fact_not_promoted(self):
        p=project();p["facts"][0]["source_ref"]="MISSING"
        r=build_support_packet(p)
        self.assertIn("FACT_SOURCE_UNLINKED",[f["code"] for f in r["flags"]])
        self.assertIn("출처 보완 대상",r["draft_text"])

    def test_ai_label_cannot_turn_analysis_into_proof(self):
        p=project();p["sources"]["S1"]["source_class"]="AI_GENERATED_ANALYSIS"
        r=build_support_packet(p)
        self.assertIn("AI_ANALYSIS_NOT_INDEPENDENT_PROOF",[f["code"] for f in r["flags"]])
        self.assertNotIn("불리한 사실 포함",r["draft_text"])

    def test_missing_experts_does_not_stop_packet_creation(self):
        r=build_support_packet(project())
        self.assertEqual(set(r["review_nodes"]),{"lawyer","medical_expert"})
        self.assertTrue(r["draft_text"])
        self.assertEqual(r["filing_status"], "GENERATED_DRAFT_ONLY")

    def test_expert_disagreement_not_majority_vote(self):
        p=project();p["review_nodes"]={"medical_expert":{"disagreement":"Alternative diagnosis remains open."}}
        self.assertIn("EXPERT_DISAGREEMENT_RETAINED",[f["code"] for f in build_support_packet(p)["flags"]])

    def test_rule63_is_not_evidence_state3(self):
        r=review_route(route(),NOW)
        self.assertTrue(r["review_triggered"])
        self.assertEqual(r["current_evidence_state"],"R2.6-1")
        self.assertFalse(r["automatic_state_change"])

    def test_missing_controller_not_assigned_to_victim(self):
        p=route();p.pop("controller");p.pop("coordinator")
        r=review_route(p,NOW)
        self.assertIsNone(r["coordinator"])
        self.assertIn("PROCESS_ASSIGNMENT_GAP",[f["code"] for f in r["flags"]])

    def test_transfer_and_closure_do_not_reset_clock(self):
        p=route();p["transfer_at"]="2026-11-02";p["administrative_closed"]=True
        r=review_route(p,NOW)
        self.assertEqual(r["opened_at"],"2026-10-01T12:00:00+09:00")
        self.assertEqual(r["process_status"],"DELAY_REVIEW_TRIGGERED")
        self.assertIn("ADMINISTRATIVE_CLOSURE_NOT_VERIFICATION_RESOLUTION",[f["code"] for f in r["flags"]])

    def test_unverified_deadline_not_missed_finding(self):
        p=route();p["clock_basis_ref"]=None
        r=review_route(p,NOW)
        self.assertEqual(r["process_status"],"REMEDY_OPEN")
        self.assertIn("CLOCK_BASIS_UNVERIFIED",[f["code"] for f in r["flags"]])

    def test_receipt_claim_needs_receipt(self):
        p=route();p["delivery_state"]="RECEIVED_CONFIRMED"
        r=review_route(p,NOW)
        self.assertIn("RECEIPT_MISSING",[f["code"] for f in r["flags"]])
        self.assertEqual(r["delivery_state"],"GENERATED_DRAFT_ONLY")

    def test_act_based_accountability_review_not_sanction(self):
        p=route();p.update(specific_act="Alleged synthetic destruction",act_source_ref="S1")
        r=review_route(p,NOW)
        self.assertEqual(r["accountability_review"],"COUNSEL_ASSESS_DISCIPLINARY_OR_OVERSIGHT_PACKET")
        self.assertFalse(r["sanction_decided"])
        self.assertTrue(r["accountability_gaps"])

    def test_control_failure_candidate_not_state_upgrade(self):
        p=route();p.update(duty_ref="D",nonperformance_ref="N")
        r=review_route(p,NOW)
        self.assertEqual(r["transition_review_candidate"],"R2.6-2_REVIEW_CANDIDATE")
        self.assertEqual(r["current_evidence_state"],"R2.6-1")

    def test_loop_stops_and_keeps_open_items(self):
        r=run_consistency_loop(project(),NOW)
        self.assertEqual(len(r["consistency_loop"]["history"]),2)
        self.assertEqual(r["consistency_loop"]["status"],"STABLE_WITH_OPEN_ITEMS")
        self.assertEqual(r["release_status"],"HOLD_FOR_COUNSEL_AND_EXPERT_REVIEW")
        self.assertIsNone(r["total_score"])
        self.assertFalse(r["external_action_performed"])

    def test_duplicate_id_and_broken_route_provenance(self):
        p=project();p["routes"][0]["id"]="F1";p["routes"][0]["source_refs"]=["MISSING"]
        codes=[f["code"] for f in run_consistency_loop(p,NOW)["input_gaps"]]
        self.assertIn("MISSING_OR_DUPLICATE_ID",codes)
        self.assertIn("ROUTE_SOURCE_UNLINKED",codes)

    def test_asserted_score_cannot_override_lock(self):
        p=project();p.update(total_score=99,deployment_status="DEPLOYED",automatic_approval=True)
        r=run_consistency_loop(p,NOW)
        self.assertIsNone(r["total_score"])
        self.assertEqual(r["deployment_status"],"NOT_DEPLOYED")
        self.assertFalse(r["approval_status_changed"])

    def test_unlinked_clock_source_blocks_deadline_escalation(self):
        p=project();p['routes'][0]['clock_basis_ref']='MISSING'
        r=run_consistency_loop(p,NOW)
        self.assertEqual(r['routes'][0]['process_status'],'REMEDY_OPEN')
        self.assertIn('CLOCK_BASIS_UNVERIFIED',[f['code'] for f in r['routes'][0]['flags']])

    def test_future_regulation_does_not_imply_legal_retroactivity(self):
        p=route();p['applicable_rule_ref']='LATER_RULE';p['material_conflict']=True
        r=review_route(p,NOW)
        self.assertTrue(r['review_triggered'])
        self.assertEqual(r['current_evidence_state'],'R2.6-1')
        self.assertFalse(r['sanction_decided'])

    def test_invariant_mutation_detects_punishment_and_fake_verification(self):
        r=run_consistency_loop(project(),NOW)
        r["routes"][0]["sanction_decided"]=True
        r["results"][0]["source_verified_externally"]=True
        self.assertIn("AUTOMATIC_LIABILITY_OR_SANCTION",invariants(r))
        self.assertIn("UNSUPPORTED_CITATION_CERTAINTY",invariants(r))

    def test_invalid_inputs_are_rejected(self):
        self.assertEqual(verify({"kind":"paper","evidence":[]})["status"],"INVALID_INPUT")
        with self.assertRaises(ValueError):run_consistency_loop({"routes":"bad"},NOW)
        with self.assertRaises(ValueError):run_consistency_loop(project(),NOW,max_iterations=999)

if __name__=="__main__":unittest.main()

