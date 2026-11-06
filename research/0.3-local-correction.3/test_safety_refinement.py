"""Synthetic regressions for the local correction, not actual case findings."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import vos_verify as v

NOW = "2026-11-05T01:00:00+00:00"
SCOPE = {"case_id": "SYNTH-A", "track_id": "ADMIN"}


def project():
    return {"synthetic": True, **SCOPE, "question": "합성 원자료 검증",
            "sources": {"S1": {**SCOPE, "source_class": "PRIMARY_OFFICIAL_RECORD", "text": "합성 회신 원문 SYNTHETIC_FACT_MARKER", "locator": "synthetic line 1"}},
            "facts": [{**SCOPE, "id": "F1", "source_ref": "S1", "text": "SYNTHETIC_FACT_MARKER", "quoted_text": "SYNTHETIC_FACT_MARKER",
                       "epistemic_status": "SOURCE_STATED", "statement_role": "RECORD_STATEMENT", "adverse": True}],
            "routes": [{**SCOPE, "id": "R1", "source_refs": ["S1"], "prior_control_ref": "S1",
                        "question": "SYNTHETIC_ROUTE_MARKER", "controller": "SYNTHETIC_CONTROLLER",
                        "availability": "NOT_PRODUCED", "records_needed": ["SYNTHETIC_RECORD"],
                        "current_evidence_state": "R2.6-1", "clock_basis_ref": "S1", "clock_type": "INTERNAL_TARGET",
                        "opened_at": "2026-11-01T01:00:00+00:00", "next_due_at": "2026-11-02T01:00:00+00:00"}],
            "items": [{**SCOPE, "id": "I1", "kind": "opponent_claim", "source_ref": "S1",
                       "claim": "자료가 없으니 원고의 입증 실패이다.", "speaker": "OPPONENT",
                       "evidence_control": "institution", "source_access": "RESTRICTED"}],
            "review_nodes": {role: {**SCOPE, "review_ref": "REVIEW-" + role,
                                    "scope": "합성 검토 범위", "qualification_ref": "QUAL-" + role,
                                    "opinion": "독립 검토 의견 " + role, "reviewed_sources": ["S1"],
                                    "version": "NODE-V2", "correction": "정정 이력 보존",
                                    "disagreement": {"text": "이견 원문 " + role, "source_ref": "S1",
                                                     "version": "DISSENT-V3", "review_id": "DISSENT-ID-" + role,
                                                     "additional_verification": ["추가 검사", "대체 원인"],
                                                     "previous_version": {"text": "이전 이견", "version": "V1"}}}
                             for role in ("lawyer", "medical_expert")},
            "requested_remedies": ["항목별 자료제출·설명 요청"]}


def codes(result):
    return {x["code"] for x in result["flags"]}


class ScopeSafety(unittest.TestCase):
    def test_matching_scope_remains_usable_as_source_stated_only(self):
        report = v.run_consistency_loop(project(), NOW)
        self.assertEqual(v.invariants(report), [])
        self.assertTrue(report["support_packet"]["fact_ledger"][0]["in_primary_paragraph"])
        self.assertTrue(report["support_packet"]["route_register"][0]["operative_request"])
        self.assertFalse(report["source_verified_externally"])

    def test_fact_wrong_case_wrong_track_and_missing_are_held(self):
        for update in ({"case_id": "SYNTH-B"}, {"track_id": "CIVIL"}, {"case_id": None}, {"track_id": ""}):
            with self.subTest(update=update):
                p = project(); p["facts"][0].update(update)
                packet = v.build_support_packet(p)
                self.assertFalse(packet["fact_ledger"][0]["in_primary_paragraph"])
                self.assertEqual(len(packet["quarantined_facts"]), 1)
                self.assertIn("SYNTHETIC_FACT_MARKER", packet["draft_text"])
                self.assertNotIn("- SYNTHETIC_FACT_MARKER [S1; 원자료 인증은 별도]", packet["draft_text"])

    def test_project_scope_missing_never_inferred_from_records(self):
        p = project(); p.pop("case_id")
        packet = v.build_support_packet(p)
        self.assertFalse(packet["fact_ledger"][0]["in_primary_paragraph"])
        self.assertFalse(packet["route_register"][0]["operative_request"])

    def test_source_scope_checked_independently(self):
        for update in ({"case_id": "SYNTH-B"}, {"track_id": "CIVIL"}, {"track_id": None}):
            with self.subTest(update=update):
                p = project(); p["sources"]["S1"].update(update)
                report = v.run_consistency_loop(p, NOW)
                self.assertFalse(report["support_packet"]["fact_ledger"][0]["in_primary_paragraph"])
                self.assertFalse(report["routes"][0]["review_triggered"])
                self.assertIsNone(report["routes"][0]["transition_review_candidate"])

    def test_every_route_reference_is_scoped_in_draft_and_report(self):
        for field in v.ROUTE_REF_FIELDS:
            with self.subTest(field=field):
                p = project(); p["sources"]["X"] = {**p["sources"]["S1"], "case_id": "SYNTH-B"}
                p["routes"][0][field] = "X"
                r = v.run_consistency_loop(p, NOW)
                self.assertEqual(r["routes"][0]["process_status"], "SCOPE_REVIEW_REQUIRED")
                self.assertFalse(r["support_packet"]["route_register"][0]["operative_request"])
                self.assertNotIn("검증 요청: SYNTHETIC_ROUTE_MARKER", r["support_packet"]["draft_text"])

    def test_route_own_scope_mismatch_holds(self):
        p = project(); p["routes"][0]["track_id"] = "CIVIL"
        r = v.run_consistency_loop(p, NOW)
        self.assertFalse(r["routes"][0]["review_triggered"])
        self.assertIn("SYNTHETIC_ROUTE_MARKER", r["support_packet"]["draft_text"])

    def test_nested_evidence_scope_identical_in_draft_and_result(self):
        p = project(); p["sources"]["X"] = {**p["sources"]["S1"], "case_id": "SYNTH-B"}
        p["items"][0]["evidence"] = {"source_ref": "X", "primary_text": "합성 반대 주장"}
        r = v.run_consistency_loop(p, NOW)
        a = r["results"][0]["scope_review"]
        b = r["support_packet"]["statement_reviews"][0]["scope_review"]
        self.assertEqual(a, b)
        self.assertEqual(a["status"], "QUARANTINED_FOR_SCOPE_REVIEW")

    def test_extra_fact_source_refs_are_not_ignored(self):
        p = project(); p["sources"]["X"] = {**p["sources"]["S1"], "track_id": "CIVIL"}
        p["facts"][0]["source_refs"] = ["X"]
        self.assertFalse(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])

    def test_explanation_source_scope_is_not_ignored(self):
        p = project(); p["sources"]["X"] = {**p["sources"]["S1"], "case_id": "SYNTH-B"}
        p["items"][0]["explanation_ref"] = "X"
        self.assertEqual(v.analyze(p, NOW)["results"][0]["use_in_current_case"], "HOLD_FOR_SCOPE_REVIEW")

    def test_procedure_alias_supported_without_guessing_equivalence(self):
        p = project()
        for row in [p, *p["sources"].values(), *p["facts"], *p["routes"], *p["items"]]:
            row["procedure_id"] = row.pop("track_id")
        self.assertTrue(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])
        p["facts"][0]["track_id"] = "CIVIL"
        self.assertFalse(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])

    def test_cross_scope_reuse_input_does_not_self_authorize(self):
        p = project(); p["facts"][0].update(case_id="SYNTH-B", cross_scope_reuse_authorized=True)
        packet = v.build_support_packet(p)
        self.assertFalse(packet["fact_ledger"][0]["in_primary_paragraph"])
        self.assertFalse(packet["fact_ledger"][0]["scope_review"]["cross_scope_reuse_authorized"])


class DissentSafety(unittest.TestCase):
    def test_complete_nested_dissent_json_and_draft_for_both_experts(self):
        p = project(); packet = v.build_support_packet(p)
        for role, node in p["review_nodes"].items():
            self.assertEqual(packet["review_nodes"][role]["disagreement"], node["disagreement"])
            self.assertEqual(packet["review_nodes"][role]["input_record"], node)
            for value in [node["opinion"], node["disagreement"]["text"], node["disagreement"]["review_id"],
                          "DISSENT-V3", "NODE-V2", "정정 이력 보존", "이전 이견", "추가 검사", "대체 원인"]:
                self.assertIn(value, packet["draft_text"])
            self.assertFalse(packet["review_nodes"][role]["independently_authenticated"])

    def test_string_list_and_empty_dissent_preserved_without_mutating(self):
        for dissent in ("짧은 이견", ["첫째", {"text": "둘째"}], {}, [], None):
            with self.subTest(dissent=dissent):
                p = project(); p["review_nodes"]["lawyer"]["disagreement"] = dissent
                before = copy.deepcopy(p)
                out = v.run_consistency_loop(p, NOW)
                self.assertEqual(out["support_packet"]["review_nodes"]["lawyer"]["disagreement"], dissent)
                self.assertEqual(p, before)

    def test_output_dissent_does_not_alias_input(self):
        p = project(); packet = v.build_support_packet(p)
        packet["review_nodes"]["lawyer"]["disagreement"]["text"] = "changed"
        self.assertEqual(p["review_nodes"]["lawyer"]["disagreement"]["text"], "이견 원문 lawyer")

    def test_extra_named_expert_retained(self):
        p = project(); p["review_nodes"]["independent_pathologist"] = copy.deepcopy(p["review_nodes"]["medical_expert"])
        packet = v.build_support_packet(p)
        self.assertIn("independent_pathologist", packet["review_nodes"])
        self.assertIn("independent_pathologist", packet["draft_text"])

    def test_dissent_source_scope_held_without_erasure(self):
        p = project(); p["sources"]["X"] = {**p["sources"]["S1"], "case_id": "SYNTH-B"}
        p["review_nodes"]["lawyer"]["disagreement"]["source_ref"] = "X"
        r = v.build_support_packet(p)
        self.assertEqual(r["review_nodes"]["lawyer"]["scope_review"]["status"], "QUARANTINED_FOR_SCOPE_REVIEW")
        self.assertIn("이견 원문 lawyer", r["draft_text"])


class StatementSafety(unittest.TestCase):
    def test_opponent_quote_not_concession(self):
        r = v.verify({"kind": "plaintiff_draft", "claim": '피고는 "자료가 없으니 원고의 입증 실패"라고 주장한다.'})
        self.assertEqual(r["status"], "OPPONENT_ASSERTION_REVIEW")
        self.assertFalse(r["victim_concession_required"])

    def test_rebuttal_not_concession(self):
        r = v.verify({"kind": "plaintiff_draft", "claim": "자료가 없다는 이유로 원고의 입증 실패라고 볼 수 없다. 원자료 제출을 요청한다."})
        self.assertEqual(r["status"], "REBUTTAL_CONTEXT_REVIEW")

    def test_necessary_caveat_retained(self):
        text = "현재 자료만으로 인과관계가 확정된 것은 아니다. 독립 검토를 요청한다."
        r = v.verify({"kind": "plaintiff_draft", "claim": text})
        self.assertEqual(r["status"], "REQUIRED_LIMIT_REVIEW")
        self.assertEqual(r["original_text"], text)
        self.assertFalse(r["automatic_deletion"])

    def test_real_concession_phrase_remains_review_only(self):
        r = v.verify({"kind": "plaintiff_draft", "claim": "자료가 없으니 원고의 입증 실패이다."})
        self.assertEqual(r["status"], "CONCESSION_RISK")
        self.assertFalse(r["victim_concession_required"])

    def test_opponent_sentence_does_not_hide_later_own_concession(self):
        r = v.verify({"kind": "plaintiff_draft", "claim": '피고는 "원고의 입증 실패"라고 주장한다. 청구를 포기한다.'})
        self.assertEqual(r["status"], "CONCESSION_RISK")
        self.assertEqual(len(r["segments"]), 2)

    def test_same_sentence_mixed_attribution_is_unresolved(self):
        r = v.verify({"kind": "plaintiff_draft", "claim": "피고는 원고의 입증 실패라고 주장하지만 청구를 포기한다."})
        self.assertEqual(r["status"], "CONTEXT_REVIEW_REQUIRED")

    def test_symmetric_source_scrutiny_for_all_speakers(self):
        results = [v.verify({"kind": kind, "claim": "합성 주장", "evidence_control": "institution",
                             "source_access": "RESTRICTED"}) for kind in
                   ("plaintiff_draft", "opponent_claim", "institution_claim", "defendant_draft")]
        for r in results:
            gaps = r["evidence_scrutiny"]["gaps"]
            self.assertIn("UNDERLYING_SOURCE_TEXT_NOT_SUPPLIED", gaps)
            self.assertIn("SOURCE_ACCESS_REVIEW_PENDING", gaps)
            self.assertIn("CONTROLLER_EXPLANATION_REVIEW_PENDING", gaps)
            self.assertFalse(r["evidence_scrutiny"]["legal_burden_shift_determined"])
            self.assertFalse(r["evidence_scrutiny"]["victim_restatement_required"])

    def test_asserted_explanation_complete_is_not_verified(self):
        p = project(); p["items"][0]["itemized_explanation_complete"] = True
        r = v.analyze(p, NOW)["results"][0]["evidence_scrutiny"]
        self.assertEqual(r["explanation_sufficiency"], "NOT_DETERMINED")
        self.assertIn("EXPLANATION_COMPLETENESS_IS_INPUT_CLAIM_NOT_VERIFIED", r["gaps"])

    def test_route_explanation_boolean_cannot_suppress_review(self):
        p = project(); p["routes"][0]["itemized_explanation_complete"] = True
        r = v.run_consistency_loop(p, NOW)
        self.assertTrue(r["routes"][0]["review_triggered"])
        self.assertEqual(r["routes"][0]["explanation_sufficiency"], "NOT_DETERMINED")
        self.assertIn("EXPLANATION_COMPLETENESS_INPUT_NOT_REVERIFIED", codes(r["routes"][0]))
        self.assertIn("CONTROLLER_EXPLANATION_SOURCE_PENDING", r["routes"][0]["evidence_scrutiny"]["gaps"])
        self.assertFalse(r["routes"][0]["automatic_state_change"])

    def test_opponent_fact_and_unknown_role_not_promoted(self):
        for role in ("OPPONENT_CLAIM", "OPPONENT_CLAIM_TYPO", "VICTIM_REBUTTAL", "EPISTEMIC_CAVEAT", "PROPOSED_CONCESSION"):
            with self.subTest(role=role):
                p = project(); p["facts"][0]["statement_role"] = role
                self.assertFalse(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])


class IntegritySafety(unittest.TestCase):
    def test_no_input_mutation_or_authority_promotion(self):
        p = project(); p.update(approval_status_changed=True, total_score=99, deployment_status="DEPLOYED")
        before = copy.deepcopy(p); r = v.run_consistency_loop(p, NOW)
        self.assertEqual(p, before)
        self.assertEqual(v.invariants(r), [])
        self.assertFalse(r["approval_status_changed"])
        self.assertIsNone(r["total_score"])
        self.assertEqual(r["deployment_status"], "NOT_DEPLOYED")

    def test_mutant_scope_disagreement_detected(self):
        r = v.run_consistency_loop(project(), NOW)
        r["support_packet"]["statement_reviews"][0]["scope_review"]["status"] = "QUARANTINED_FOR_SCOPE_REVIEW"
        self.assertIn("STATEMENT_SCOPE_OUTPUT_DISAGREEMENT", v.invariants(r))

    def test_mutant_dissent_json_and_draft_losses_detected(self):
        r = v.run_consistency_loop(project(), NOW)
        r["support_packet"]["review_nodes"]["lawyer"]["disagreement"] = None
        r["support_packet"]["draft_text"] = "dissent removed"
        self.assertIn("EXPERT_DISSENT_STRUCTURED_LOSS", v.invariants(r))
        self.assertIn("EXPERT_REVIEW_DRAFT_LOSS", v.invariants(r))

    def test_mutant_scope_fact_and_route_detected(self):
        r = v.run_consistency_loop(project(), NOW)
        r["support_packet"]["fact_ledger"][0]["scope_review"]["status"] = "QUARANTINED_FOR_SCOPE_REVIEW"
        r["support_packet"]["route_register"][0]["scope_review"]["status"] = "QUARANTINED_FOR_SCOPE_REVIEW"
        self.assertIn("OUT_OF_SCOPE_PRIMARY_FACT", v.invariants(r))
        self.assertIn("OUT_OF_SCOPE_OPERATIVE_ROUTE", v.invariants(r))

    def test_malformed_refs_fail_clearly(self):
        for field, value in (("source_ref", []), ("source_refs", "S1"), ("records_needed", [None])):
            with self.subTest(field=field):
                p = project(); p["routes"][0][field] = value
                with self.assertRaises(ValueError):
                    v.run_consistency_loop(p, NOW)

    def test_malformed_claim_and_kind_are_controlled(self):
        for field, value in (("claim", None), ("claim", 42), ("kind", []), ("statement_role", [])):
            with self.subTest(field=field, value=value):
                p = project(); p["items"][0][field] = value
                self.assertEqual(v.verify(p["items"][0])["status"], "INVALID_INPUT")
                with self.assertRaises(ValueError):
                    v.run_consistency_loop(p, NOW)

    def test_source_class_wrong_shape_is_controlled(self):
        p = project(); p["sources"]["S1"]["source_class"] = []
        with self.assertRaises(ValueError):
            v.run_consistency_loop(p, NOW)

    def test_cli_serialization_retains_dissent_and_exclusive_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); input_path = root / "input.json"; output_path = root / "output.json"
            input_path.write_text(json.dumps(project(), ensure_ascii=False))
            args = [sys.executable, str(Path(v.__file__)), str(input_path), "--now", NOW, "--output", str(output_path)]
            subprocess.run(args, check=True, capture_output=True, timeout=10)
            data = output_path.read_bytes(); report = json.loads(data)
            self.assertIn("이견 원문 lawyer", report["support_packet"]["draft_text"])
            self.assertEqual(v.invariants(report), [])
            second = subprocess.run(args, capture_output=True, timeout=10)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(output_path.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
