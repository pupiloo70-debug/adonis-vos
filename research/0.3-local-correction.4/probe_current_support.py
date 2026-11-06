"""Read-only synthetic probes of correction.3, not a correction.4 implementation.

Run from the repository root:
    python3 -B research/0.3-correction.4-proposal-20261106/probe_current_support.py

The output distinguishes current behavior from proposed acceptance criteria.
A proposed-criterion miss is NOT a failure of correction.3's published tests.
No real case data, networking, file writes, approvals, or external actions.
"""
import copy
import importlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[1] / "0.3-local-correction.3"
sys.path.insert(0, str(BASE))
v = importlib.import_module("vos_verify")
f = importlib.import_module("test_victim_access")


def observe(project):
    before = copy.deepcopy(project)
    review = v.analyze(project, f.NOW)["support_packet"]["access_reviews"][0]
    return {
        "status": review["status"],
        "warning_codes": sorted(w["code"] for w in review["warnings"]),
        "eligible_observations": sum(o["eligible_for_warning_review"] for o in review["observations"]),
        "decision_body_input": review["decision_body"],
        "input_unchanged": before == project,
    }


def main():
    rows = []
    baseline = observe(f.fixture())
    baseline_codes = set(baseline["warning_codes"])
    rows.append({
        "id": "B00", "kind": "BASELINE_CONTROL", "observed": baseline,
        "check_satisfied": len(baseline_codes) == 5 and baseline["input_unchanged"],
    })

    p = f.fixture()
    quote = "피고는 독립 감정 신청을 불채택해 달라고 요청했다. 법원의 결정은 아직 없다."
    p["sources"]["SOURCE-3"].update(
        primary_text=quote, source_class="CONTEMPORANEOUS_RECORD",
        speaker="OPPONENT", statement_role="OPPONENT_CLAIM")
    p["support_reviews"][0]["observations"][3].update(
        quoted_text=quote, speaker="OPPONENT", statement_role="OPPONENT_CLAIM",
        decision_status="REQUEST_ONLY")
    observed = observe(p)
    rows.append({
        "id": "P01", "kind": "ATTRIBUTION_AND_EVENT_TYPE_GAP",
        "mutation": "An observation remains mislabeled as a refusal although its quote and speaker say opponent request only.",
        "proposed_requirement": "Hold the refusal-dependent warning until actor, speech act, and decision type are reconciled.",
        "observed": observed,
        "proposed_criterion_satisfied": "CIRCULAR_BURDEN_SHIFT_WARNING" not in observed["warning_codes"],
        "limit": "Current module explicitly relies on supplied human labels; this does not show automatic natural-language misreading.",
    })

    p = f.fixture()
    quote = "다른 사건에서 별도 구제가 인정됐다는 합성 기록"
    p["sources"]["OTHER"] = {
        "primary_text": quote, "source_class": "PRIMARY_OFFICIAL_RECORD",
        "locator": "other paragraph", "case_id": "OTHER-CASE", "track_id": f.TRACK,
    }
    p["support_reviews"][0]["observations"].append({
        "id": "UNRELATED-OBS", "kind": "RECOGNIZED_RELIEF_EXISTS",
        "source_ref": "OTHER", "quoted_text": quote,
        "case_id": "OTHER-CASE", "track_id": f.TRACK,
    })
    observed = observe(p)
    rows.append({
        "id": "P02", "kind": "REVIEW_WIDE_QUARANTINE_TRADEOFF",
        "proposed_requirement": "Quarantine the foreign observation and its dependants while retaining independently supported in-scope baseline warnings.",
        "observed": observed,
        "proposed_criterion_satisfied": baseline_codes <= set(observed["warning_codes"]),
        "limit": "Correction.3 deliberately quarantines the whole review; changing this requires dependency-aware checks and revised acceptance tests.",
    })

    p = f.fixture()
    p["support_reviews"][0]["decision_body"] = "UNLINKED-OTHER-COURT"
    observed = observe(p)
    rows.append({
        "id": "P03", "kind": "ACTOR_TO_ACT_BINDING_GAP",
        "proposed_requirement": "Do not attach the judicial-pattern warning to an arbitrary named body without a reviewed actor-action-source relationship.",
        "observed": observed,
        "proposed_criterion_satisfied": "HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING" not in observed["warning_codes"],
        "limit": "The output is already marked a review warning, not an authenticated finding of misconduct.",
    })

    p = f.fixture()
    p["subject_id"] = "CHILD-A"
    p["support_reviews"][0]["subject_id"] = "CHILD-A"
    for observation in p["support_reviews"][0]["observations"]:
        observation["subject_id"] = "CHILD-A"
    for source in p["sources"].values():
        source["subject_id"] = "CHILD-A"
    p["sources"]["SOURCE-0"]["subject_id"] = "CHILD-B"
    observed = observe(p)
    rows.append({
        "id": "P04", "kind": "SAME_PROCEEDING_DIFFERENT_PERSON_GAP",
        "proposed_requirement": "Hold the other person's autopsy source without suppressing unrelated valid observations for the target person.",
        "observed": observed,
        "proposed_criterion_satisfied": "AUTOPSY_EVIDENCE_EXCLUSION_WARNING" not in observed["warning_codes"],
        "limit": "subject_id is a proposed field and is not an implemented correction.3 scope dimension.",
    })

    p = f.fixture()
    p["support_reviews"][0]["observations"][3]["kind"] = "INDEPENDENT_REVIEW_GRANTED"
    try:
        observed = observe(p)
        lifecycle_supported = True
    except ValueError as error:
        observed = {"controlled_rejection": str(error)}
        lifecycle_supported = False
    rows.append({
        "id": "P05", "kind": "UNIMPLEMENTED_LIFECYCLE_EXTENSION",
        "proposed_requirement": "Represent a later grant and actual access separately without erasing the earlier restriction and costs.",
        "observed": observed,
        "extension_supported": lifecycle_supported,
        "limit": "Rejecting an unknown kind is correct under the current closed schema; this probe identifies an extension, not an uncontrolled crash.",
    })

    output = {
        "schema": "ADONIS-VOS-CORRECTION4-DESIGN-PROBES/1.0",
        "reference_date": "2026-11-06",
        "base_version": v.VERSION,
        "data": "SYNTHETIC_ONLY",
        "implementation_changed": False,
        "published_test_suite_modified": False,
        "summary": {
            "baseline_controls": 1,
            "baseline_controls_satisfied": int(rows[0]["check_satisfied"]),
            "additional_design_probes": 5,
            "current_proposed_criteria_evaluated": 4,
            "current_proposed_criteria_satisfied": sum(r["proposed_criterion_satisfied"] for r in rows if "proposed_criterion_satisfied" in r),
            "lifecycle_extension_supported": lifecycle_supported,
        },
        "results": rows,
        "not_a_real_case_or_independent_institutional_audit": True,
        "total_score": None,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
