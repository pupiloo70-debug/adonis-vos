"""Independent-audit counterexamples: recursive provenance and attribution."""
import copy
import unittest
import vos_verify as v
from test_safety_refinement import project, NOW


def other_source(p):
    p["sources"]["X"] = {**p["sources"]["S1"], "case_id": "SYNTH-B", "track_id": "CIVIL"}


class RecursiveProvenance(unittest.TestCase):
    def test_nested_fact_citation_source_held(self):
        p = project(); other_source(p)
        p["facts"][0]["evidence"] = {"citation": {"source_ref": "X"}}
        f = v.analyze(p, NOW)["support_packet"]["fact_ledger"][0]
        self.assertFalse(f["in_primary_paragraph"])
        self.assertEqual(f["scope_review"]["status"], "QUARANTINED_FOR_SCOPE_REVIEW")

    def test_previous_dissent_source_held_without_erasure(self):
        p = project(); other_source(p)
        p["review_nodes"]["lawyer"]["disagreement"]["previous_version"]["source_ref"] = "X"
        packet = v.build_support_packet(p)
        self.assertEqual(packet["review_nodes"]["lawyer"]["scope_review"]["status"], "QUARANTINED_FOR_SCOPE_REVIEW")
        self.assertIn("이전 이견", packet["draft_text"])

    def test_route_nested_evidence_source_held(self):
        p = project(); other_source(p)
        p["routes"][0]["evidence"] = {"source_ref": "X"}
        r = v.run_consistency_loop(p, NOW)
        self.assertFalse(r["support_packet"]["route_register"][0]["operative_request"])
        self.assertFalse(r["routes"][0]["review_triggered"])

    def test_transitive_source_dependency_held(self):
        p = project(); other_source(p); p["sources"]["S1"]["source_ref"] = "X"
        r = v.run_consistency_loop(p, NOW)
        self.assertFalse(r["support_packet"]["fact_ledger"][0]["in_primary_paragraph"])
        self.assertFalse(r["support_packet"]["route_register"][0]["operative_request"])
        self.assertEqual(r["support_packet"]["review_nodes"]["lawyer"]["scope_review"]["checked_source_refs"], ["S1", "X"])

    def test_inline_scopes_at_arbitrary_depth_checked(self):
        for field in ("facts", "items", "routes"):
            with self.subTest(field=field):
                p = project()
                p[field][0]["evidence"] = {"revisions": [{"citation": {"case_id": "SYNTH-B", "track_id": "CIVIL", "primary_text": "OTHER_CASE_ONLY"}}]}
                r = v.run_consistency_loop(p, NOW)
                target = r["support_packet"]["fact_ledger"][0] if field == "facts" else r["results" if field == "items" else "routes"][0]
                self.assertEqual(target["scope_review"]["status"], "QUARANTINED_FOR_SCOPE_REVIEW")

    def test_inline_partial_scope_never_inherited(self):
        p = project(); p["facts"][0]["evidence"] = {"case_id": "SYNTH-A"}
        self.assertFalse(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])

    def test_malformed_nested_source_refs_are_held(self):
        for evidence in ({"source_ref": 0}, {"source_refs": "X"}, {"source_refs": {}}, {"reviewed_sources": "X"}, {"source_ref": ["X"]}, {"source_ref": None}, {"source_ref": ""}):
            with self.subTest(evidence=evidence):
                p = project(); p["facts"][0]["evidence"] = evidence
                f = v.build_support_packet(p)["fact_ledger"][0]
                self.assertFalse(f["in_primary_paragraph"])
                self.assertEqual(f["scope_review"]["status"], "QUARANTINED_FOR_SCOPE_REVIEW")

    def test_unknown_ref_field_not_silently_ignored(self):
        p = project(); p["facts"][0]["evidence"] = {"citation_ref": "UNSUPPORTED-REF"}
        f = v.build_support_packet(p)["fact_ledger"][0]
        self.assertFalse(f["in_primary_paragraph"])
        self.assertTrue(any("UNRECOGNIZED_REFERENCE_FIELD" in x for x in f["scope_review"]["reasons"]))

    def test_missing_transitive_ref_held(self):
        p = project(); p["sources"]["S1"]["evidence"] = {"source_ref": "MISSING"}
        self.assertFalse(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])

    def test_cyclic_source_dependencies_fail_closed(self):
        p = project(); p["sources"]["X"] = copy.deepcopy(p["sources"]["S1"])
        p["sources"]["S1"]["source_ref"] = "X"; p["sources"]["X"]["source_ref"] = "S1"
        f = v.build_support_packet(p)["fact_ledger"][0]
        self.assertFalse(f["in_primary_paragraph"])
        self.assertTrue(any("SOURCE_DEPENDENCY_CYCLE" in x for x in f["scope_review"]["reasons"]))

    def test_valid_acyclic_chain_preserved_and_input_unchanged(self):
        p = project(); p["sources"]["X"] = copy.deepcopy(p["sources"]["S1"])
        p["sources"]["S1"]["evidence"] = {"citations": [{"source_ref": "X"}]}
        original = copy.deepcopy(p); r = v.run_consistency_loop(p, NOW)
        self.assertTrue(r["support_packet"]["fact_ledger"][0]["in_primary_paragraph"])
        self.assertEqual(p, original)
        self.assertEqual(v.invariants(r), [])

    def test_depth_limit_holds_not_accepts(self):
        p = project(); child = {}; p["facts"][0]["evidence"] = child
        for _ in range(70):
            child["nested"] = {}; child = child["nested"]
        f = v.build_support_packet(p)["fact_ledger"][0]
        self.assertFalse(f["in_primary_paragraph"])
        self.assertTrue(any("SCOPE_TRAVERSAL_LIMIT" in x for x in f["scope_review"]["reasons"]))


class AttributionAndCorrespondence(unittest.TestCase):
    def test_opponent_record_statement_conflict_not_promoted(self):
        for speaker in ("OPPONENT", "defendant", "피고", "상대방", "기관"):
            with self.subTest(speaker=speaker):
                p = project(); p["facts"][0].update(speaker=speaker, statement_role="RECORD_STATEMENT")
                f = v.build_support_packet(p)["fact_ledger"][0]
                self.assertFalse(f["in_primary_paragraph"])
                self.assertTrue(f["attribution_review"]["conflict"])

    def test_unknown_speaker_not_assumed_record_author(self):
        p = project(); p["facts"][0]["speaker"] = "Unidentified speaker"
        self.assertFalse(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])

    def test_victim_assertion_also_not_promoted_to_record_fact(self):
        p = project(); p["facts"][0]["speaker"] = "VICTIM"
        self.assertFalse(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])

    def test_missing_source_text_not_primary_quote(self):
        p = project(); p["sources"]["S1"].pop("text")
        f = v.build_support_packet(p)["fact_ledger"][0]
        self.assertFalse(f["in_primary_paragraph"])
        self.assertFalse(f["source_correspondence"]["source_text_present"])

    def test_unrelated_source_text_not_support_for_input_claim(self):
        p = project(); p["sources"]["S1"]["text"] = "The sky is blue."
        p["facts"][0]["text"] = "백신 인과관계와 기관 범죄가 확정되었다."
        packet = v.build_support_packet(p)
        self.assertFalse(packet["fact_ledger"][0]["in_primary_paragraph"])
        self.assertIn("입력 주장·원문 대응 미확인", packet["draft_text"])

    def test_quote_without_locator_not_primary(self):
        p = project(); p["sources"]["S1"].pop("locator")
        self.assertFalse(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])

    def test_primary_text_field_is_consistent_in_quote_and_scrutiny(self):
        p = project(); p["sources"]["S1"]["primary_text"] = p["sources"]["S1"].pop("text")
        f = v.build_support_packet(p)["fact_ledger"][0]
        self.assertTrue(f["in_primary_paragraph"])
        self.assertTrue(f["evidence_scrutiny"]["underlying_text_supplied"])
        self.assertNotIn("UNDERLYING_SOURCE_TEXT_NOT_SUPPLIED", f["evidence_scrutiny"]["gaps"])

    def test_invalid_primary_text_not_treated_as_supplied_text(self):
        p = project(); p["sources"]["S1"].pop("text"); p["items"][0]["evidence"] = {"primary_text": ["not text"]}
        r = v.analyze(p, NOW)
        self.assertFalse(r["results"][0]["evidence_scrutiny"]["underlying_text_supplied"])

    def test_same_text_without_explicit_quote_is_input_assertion(self):
        p = project(); p["facts"][0].pop("quoted_text")
        self.assertFalse(v.build_support_packet(p)["fact_ledger"][0]["in_primary_paragraph"])

    def test_opponent_global_role_does_not_mask_own_second_sentence(self):
        r = v.verify({"kind": "plaintiff_draft", "statement_role": "OPPONENT_CLAIM",
                      "claim": '피고는 "원고의 입증 실패"라고 주장한다. 청구를 포기한다.'})
        self.assertEqual(r["status"], "CONTEXT_REVIEW_REQUIRED")

    def test_unrelated_opponent_mention_does_not_hide_own_concession(self):
        r = v.verify({"kind": "plaintiff_draft", "claim": "피고 주장과 무관하게 청구를 포기한다."})
        self.assertEqual(r["status"], "CONCESSION_RISK")

    def test_explicit_waiver_negation_not_concession(self):
        for text in ("청구를 포기하는 것은 아니다.", "청구를 포기할 의사가 없다."):
            with self.subTest(text=text):
                r = v.verify({"kind": "plaintiff_draft", "claim": text})
                self.assertEqual(r["status"], "REBUTTAL_CONTEXT_REVIEW")

    def test_mutated_primary_correspondence_or_attribution_detected(self):
        r = v.run_consistency_loop(project(), NOW)
        f = r["support_packet"]["fact_ledger"][0]
        f["source_correspondence"]["eligible_as_source_quote_only"] = False
        f["attribution_review"]["conflict"] = True
        self.assertIn("UNSUPPORTED_SOURCE_QUOTE_PROMOTION", v.invariants(r))
        self.assertIn("ATTRIBUTION_CONFLICT_PRIMARY_FACT", v.invariants(r))


if __name__ == "__main__":
    unittest.main()
