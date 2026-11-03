"""Adonis VOS 0.3 reference prototype: supplied text only, no network or dispatch."""
import argparse
import copy
import hashlib
import json
import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

VERSION = "0.3.0-design.2"
R26 = {"R2.6-1", "R2.6-2", "R2.6-3", "R2.6-4"}

def norm(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(text))).strip()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def flag(code, **details):
    return {"code": code, **details}

def result(item, status, flags, action, **extras):
    return {"id": item.get("id"), "status": status, "flags": flags, "action": action,
            "human_approval_required": True, "source_verified_externally": False,
            "total_score": None, **extras}

def verify(item):
    if not isinstance(item, dict):
        return result({}, "INVALID_INPUT", [flag("ITEM_NOT_OBJECT")], "CORRECT_INPUT")
    kind, claim = item.get("kind"), item.get("claim", "")
    if not isinstance(claim, str):
        return result(item, "INVALID_INPUT", [flag("CLAIM_NOT_TEXT")], "CORRECT_INPUT")
    flags = []
    if kind == "plaintiff_draft":
        status = "NO_RULE_HIT"
        phrases = ("입증되는 것은 아니다", "확정된 것은 아니다", "인과관계가 입증되지", "책임이 인정되는 것은 아니다")
        hits = [p for p in phrases if p in claim]
        if hits:
            flags.append(flag("EPISTEMIC_LIMIT_RETAIN", matches=hits))
            status = "REQUIRED_LIMIT_REVIEW"
        hits = [p for p in ("원고의 입증 실패", "청구를 포기", "따라서 기각", "원고에게 모든 책임") if p in claim]
        if hits:
            flags.append(flag("POSSIBLE_UNNECESSARY_CONCESSION", matches=hits))
            status = "CONCESSION_RISK"
        if item.get("evidence_control") == "institution" and not item.get("disclosure_request"):
            flags.append(flag("EVIDENCE_ASYMMETRY_NOT_ADDRESSED"))
        return result(item, status, flags, "GENERATE_SUPPORT_DRAFT_FOR_REVIEW",
                      original_text=claim, automatic_deletion=False)
    if kind not in {"case_law", "paper"}:
        return result(item, "UNVERIFIED", [flag("UNKNOWN_KIND")], "HUMAN_REVIEW")
    evidence = item.get("evidence", {})
    meta, scope = item.get("claim_metadata", {}), item.get("claim_scope", {})
    if not all(isinstance(x, dict) for x in (evidence, meta, scope)):
        return result(item, "INVALID_INPUT", [flag("CLAIM_OR_EVIDENCE_NOT_OBJECT")], "CORRECT_INPUT")
    required = (("court", "case_number", "decision_date", "primary_text") if kind == "case_law"
                else ("title", "authors", "year", "primary_text", "population", "intervention", "outcome"))
    missing = [k for k in required if not evidence.get(k)]
    if missing:
        flags.append(flag("PRIMARY_SOURCE_MISSING", fields=missing))
    text, quote = evidence.get("primary_text", ""), item.get("quoted_text", "")
    if not isinstance(text, str) or not isinstance(quote, str):
        return result(item, "INVALID_INPUT", [flag("SOURCE_OR_QUOTE_NOT_TEXT")], "CORRECT_INPUT")
    identity = (("court", "case_number", "decision_date") if kind == "case_law"
                else ("title", "authors", "year", "doi"))
    for field in identity:
        if field in meta and not evidence.get(field):
            flags.append(flag('IDENTITY_SOURCE_FIELD_MISSING', field=field))
        elif field in meta and norm(meta[field]) != norm(evidence.get(field, "")):
            flags.append(flag("IDENTITY_MISMATCH", field=field, claim=meta[field], source=evidence.get(field)))
    if kind == "paper":
        for field in ("population", "intervention", "outcome", "study_design", "follow_up",
                      "denominator_type", "numerator_type", "measure", "causality_level"):
            if field in scope and not evidence.get(field):
                flags.append(flag('STUDY_SCOPE_FIELD_MISSING', field=field))
            elif field in scope and norm(scope[field]) != norm(evidence.get(field, "")):
                flags.append(flag("SCOPE_MISMATCH", field=field, claim=scope[field], source=evidence.get(field)))
        stats = item.get("claimed_statistic")
        if stats is not None:
            try:
                n, d, rate = [Decimal(str(stats[k])) for k in ("numerator", "denominator", "percent")]
                if not all(x.is_finite() for x in (n,d,rate)) or n < 0 or d <= 0 or n > d or rate < 0 or rate > 100:
                    raise ValueError()
                if abs(n / d * 100 - rate) > Decimal("0.000001"):
                    flags.append(flag("STATISTIC_ARITHMETIC_MISMATCH"))
            except (KeyError, InvalidOperation, ValueError, TypeError):
                flags.append(flag("STATISTIC_INVALID"))
    if quote and text and norm(quote) not in norm(text):
        flags.append(flag("QUOTE_NOT_IN_SUPPLIED_FULLTEXT" if evidence.get("coverage") == "FULL_DOCUMENT"
                          else "QUOTE_NOT_LOCATED_IN_EXCERPT"))
    if evidence.get('expected_text_sha256') and hashlib.sha256(text.encode()).hexdigest() != evidence['expected_text_sha256']:
        flags.append(flag('SOURCE_BYTES_CONFLICT'))
    if item.get('holding_paraphrase'):
        flags.append(flag('HOLDING_SCOPE_REQUIRES_LAWYER'))
    if not evidence.get("source_ref") or not evidence.get("locator"):
        flags.append(flag("SOURCE_PROVENANCE_PENDING"))
    if not meta:
        flags.append(flag("CLAIM_IDENTITY_NOT_STRUCTURED"))
    if kind == "paper" and not scope:
        flags.append(flag("CLAIM_SCOPE_NOT_STRUCTURED"))
    codes = {f["code"] for f in flags}
    if 'SOURCE_BYTES_CONFLICT' in codes:
        status = 'SOURCE_INTEGRITY_CONFLICT'
    elif "IDENTITY_MISMATCH" in codes:
        status = "SOURCE_IDENTITY_CONFLICT"
    elif "SCOPE_MISMATCH" in codes:
        status = "MISAPPLIED_EVIDENCE"
    elif codes & {"STATISTIC_INVALID", "STATISTIC_ARITHMETIC_MISMATCH"}:
        status = "STATISTIC_CONFLICT"
    elif "QUOTE_NOT_IN_SUPPLIED_FULLTEXT" in codes:
        status = "MISQUOTED"
    elif codes & {"PRIMARY_SOURCE_MISSING", "QUOTE_NOT_LOCATED_IN_EXCERPT", 'IDENTITY_SOURCE_FIELD_MISSING', 'STUDY_SCOPE_FIELD_MISSING'}:
        status = "UNVERIFIED"
    else:
        status = "SOURCE_MATCH_CANDIDATE"
    return result(item, status, flags,
                  "HUMAN_SCOPE_AND_AUTHENTICITY_REVIEW" if status == "SOURCE_MATCH_CANDIDATE" else "BLOCK_CITATION_OR_REVISE_CLAIM",
                  comparison_scope="SUPPLIED_TEXT_ONLY", retrieval_status="NOT_IMPLEMENTED", fabrication_confirmed=False)

def parse_time(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.utcoffset() is not None else None
    except (ValueError, TypeError):
        return None

def review_route(route, now):
    flags = []
    current = route.get("current_evidence_state", "UNKNOWN")
    if current not in R26 | {"UNKNOWN"}:
        flags.append(flag("STATE_LABEL_INVALID"))
        current = "UNKNOWN"
    triggered = bool(route.get("question") and route.get("source_refs") and (
        route.get("material_conflict") or (
            route.get("availability") in {"NOT_PRODUCED", "REPORTED_DESTROYED", "UNKNOWN_CUSTODY"}
            and route.get("prior_control_ref") and not route.get("itemized_explanation_complete"))))
    if not route.get("controller"):
        flags.append(flag("CONTROLLER_IDENTIFICATION_PENDING"))
    if not route.get("coordinator"):
        flags.append(flag("PROCESS_ASSIGNMENT_GAP"))
    opened, due, now_dt = parse_time(route.get("opened_at")), parse_time(route.get("next_due_at")), parse_time(now)
    process = "REMEDY_OPEN"
    if not opened or not due:
        flags.append(flag("CLOCK_START_OR_DUE_UNVERIFIED"))
    elif due < opened:
        flags.append(flag("CLOCK_ORDER_CONFLICT"))
    elif not route.get("clock_basis_ref") or route.get("clock_type") not in {"INTERNAL_TARGET", "EXTERNAL_VERIFIED"}:
        flags.append(flag("CLOCK_BASIS_UNVERIFIED"))
    elif not now_dt:
        flags.append(flag('EVALUATION_TIME_UNVERIFIED'))
    elif now_dt > due:
        process = "DELAY_REVIEW_TRIGGERED"
        if route.get("extension_count") == 1 and route.get("extension_expired") is True:
            process = "REMEDY_ESCALATED"
    if route.get("delivery_state") in {"RECEIVED_CONFIRMED", "ASSIGNED_CONFIRMED", "ACTION_CONFIRMED"} and not route.get("receipt_ref"):
        flags.append(flag("RECEIPT_MISSING"))
    if route.get("administrative_closed") and not route.get("verification_resolved"):
        flags.append(flag("ADMINISTRATIVE_CLOSURE_NOT_VERIFICATION_RESOLUTION"))
    transition = ("R2.6-2_REVIEW_CANDIDATE" if current == "R2.6-1" and route.get("controller")
                  and route.get("duty_ref") and route.get("nonperformance_ref") else None)
    accountability = bool(route.get("specific_act") and route.get("act_source_ref") and route.get("controller"))
    return {"id": route.get("id"), "rule_id": "CT-RULE-6.3", "review_triggered": triggered,
            "current_evidence_state": current, "evidence_state_basis": "INPUT_LABEL_NOT_REVERIFIED",
            "transition_review_candidate": transition,
            "automatic_state_change": False, "process_status": process,
            "opened_at": route.get("opened_at"), "historical_first_request_at": route.get("historical_first_request_at"),
            "next_due_at": route.get("next_due_at"), "clock_type": route.get("clock_type"),
            "controller": route.get("controller"), "coordinator": route.get("coordinator"),
            "next_action": "PREPARE_ITEMIZED_PRODUCTION_AND_INDEPENDENT_REVIEW_DRAFT",
            "next_escalation": route.get("next_escalation") or "IDENTIFY_COMPETENT_OVERSIGHT_ROUTE",
            "accountability_review": "COUNSEL_ASSESS_DISCIPLINARY_OR_OVERSIGHT_PACKET" if accountability else "OBTAIN_ACT_SPECIFIC_RECORDS",
            "accountability_gaps": [k for k in ("alternative_explanations", "applicable_rule_ref", "competent_route") if not route.get(k)],
            "sanction_decided": False, "external_action_performed": False, "delivery_state": "GENERATED_DRAFT_ONLY",
            "receipt_ref": None, "input_delivery_state": route.get("delivery_state"), "input_receipt_ref": route.get("receipt_ref"),
            "total_score": None, "flags": flags, "human_review_required": True,
            "deadline_assessment": "SUPPLIED_CLOCK_ONLY_NOT_LEGAL_DEADLINE_CERTIFICATION"}

def build_support_packet(project):
    ledger, gaps, qualified = [], [], []
    sources = project.get("sources", {})
    for fact in project.get("facts", []):
        entry = copy.deepcopy(fact)
        ref = fact.get("source_ref")
        entry["source_link_present"] = bool(ref and ref in sources)
        ledger.append(entry)
        if not entry["source_link_present"]:
            gaps.append(flag("FACT_SOURCE_UNLINKED", fact_id=fact.get("id")))
        else:
            source = sources[ref]
            source_class = source.get('source_class') if isinstance(source, dict) else None
            entry['source_class'] = source_class or 'UNKNOWN'
            if source_class == 'AI_GENERATED_ANALYSIS':
                gaps.append(flag('AI_ANALYSIS_NOT_INDEPENDENT_PROOF', fact_id=fact.get('id')))
            elif fact.get('epistemic_status') == 'SOURCE_STATED' and source_class in {'PRIMARY_OFFICIAL_RECORD', 'RESEARCH_PRIMARY_TEXT'}:
                qualified.append(entry)
            else:
                gaps.append(flag('FACT_EPISTEMIC_REVIEW_PENDING', fact_id=fact.get('id')))
    nodes, node_results = project.get("review_nodes", {}), {}
    for role in ("lawyer", "medical_expert"):
        node = nodes.get(role, {})
        complete = bool(node.get("review_ref") and node.get("scope") and node.get("qualification_ref"))
        node_results[role] = {"status": "REVIEW_RECORDED_PENDING_AUTHENTICITY_CHECK" if complete else "REVIEW_PENDING",
                              "scope": node.get("scope"), "review_ref": node.get("review_ref"),
                              "qualification_ref": node.get("qualification_ref"),
                              "opinion": node.get("opinion"), "independently_authenticated": False}
        if not complete:
            gaps.append(flag("REVIEW_NODE_PENDING", role=role))
        if node.get("disagreement"):
            gaps.append(flag("EXPERT_DISAGREEMENT_RETAINED", role=role))
    paragraphs = ["피해자 지원 검토 초안 — 실제 법원 제출 전 대리인·전문가 확인",
                  "입증 대상: " + project.get("question", "질문 미특정")]
    if project.get('synthetic') is True:
        paragraphs.insert(0, '합성 입력에 대한 시험 출력 — 실제 사건 사실이나 제출 문서가 아닙니다.')
    if project.get("case_id"):
        paragraphs.append("사건 식별자(입력값): " + project["case_id"])
    for f in qualified:
        paragraphs.append("- " + f.get("text","") + " [" + f["source_ref"] + "; 원자료 인증은 별도]"
                          + (" [불리한 사실 포함]" if f.get("adverse") else ""))
    unqualified = [f for f in ledger if f not in qualified]
    if unqualified:
        paragraphs.append("미확인·가설·출처 보완 대상(확정 사실로 사용하지 않음):")
        for f in unqualified:
            paragraphs.append("- " + f.get("text","") + " [" + (f.get("source_ref") or "출처 미연결") + "; "
                              + f.get("epistemic_status","UNKNOWN") + "]")
    for route in project.get("routes", []):
        paragraphs.extend(["검증 요청: " + route.get("question", "질문 미특정"),
                           "자료 통제 역할: " + (route.get("controller") or "미특정 — 확인 필요"),
                           "필요한 원자료: " + ", ".join(route.get("records_needed", [])),
                           "요청 취지: 위 자료의 제출·검색 범위·보존 및 미제공 사유에 대한 항목별 설명과 가능한 대체 검증 경로를 검토해 주시기 바랍니다."])
    for remedy in project.get("requested_remedies", []):
        paragraphs.append("구제 요청 후보(관할·요건은 대리인 확인): " + remedy)
    paragraphs.extend(["자료 미확보는 곧바로 사실 부존재나 위법 확정을 뜻하지 않습니다. 미제공 경위 및 원자료를 확인할 절차와 전문 검토를 요청합니다.",
                       "의학적 가설·인과성·대체 원인은 전문가 검토 대상으로 유지하며, 기존 처분과 불리한 자료도 함께 대조합니다."])
    return {"draft_text": "\n\n".join(paragraphs), "fact_ledger": ledger, "review_nodes": node_results,
            "flags": gaps, "automatic_deletion": False, "legal_privilege_claimed": False,
            "filing_status": "GENERATED_DRAFT_ONLY"}

def analyze(project, now):
    if not isinstance(project, dict):
        raise ValueError("Project must be an object")
    for field in ("items", "routes", "facts", "requested_remedies"):
        if not isinstance(project.get(field, []), list):
            raise ValueError(field + " must be an array")
    if any(not isinstance(x, dict) for k in ("routes","facts") for x in project.get(k, [])):
        raise ValueError("Route and fact entries must be objects")
    if not isinstance(project.get("sources",{}), dict) or not isinstance(project.get("review_nodes",{}), dict):
        raise ValueError("Sources and review_nodes must be objects")
    if any(not isinstance(n, dict) for n in project.get('review_nodes',{}).values()):
        raise ValueError('Each review node must be an object')
    ids = [x.get("id") for k in ("items","routes","facts") for x in project.get(k, []) if isinstance(x,dict)]
    input_gaps = []
    if None in ids or len(ids) != len(set(ids)):
        input_gaps.append(flag("MISSING_OR_DUPLICATE_ID"))
    refs = project.get("sources", {})
    checked_routes = []
    for route in project.get("routes", []):
        checked = copy.deepcopy(route)
        requested_refs = list(route.get("source_refs", [])) + [route.get(k) for k in
                         ("prior_control_ref","duty_ref","nonperformance_ref","act_source_ref","clock_basis_ref","applicable_rule_ref") if route.get(k)]
        if any(ref not in refs for ref in requested_refs):
            input_gaps.append(flag("ROUTE_SOURCE_UNLINKED", route_id=route.get("id")))
        checked['source_refs'] = [ref for ref in route.get('source_refs', []) if ref in refs]
        for field in ('prior_control_ref','duty_ref','nonperformance_ref','act_source_ref','clock_basis_ref','applicable_rule_ref'):
            if checked.get(field) and checked[field] not in refs:
                checked[field] = None
        checked_routes.append(checked)
    return {"schema": "ADONIS-VOS-0.3-LOCAL-REVIEW/1.0", "version": VERSION,
            "data_class": "SYNTHETIC" if project.get("synthetic") is True else "PRIVATE_INPUT_NOT_FOR_PUBLICATION",
            "results": [verify(x) for x in project.get("items", [])],
            "routes": [review_route(r, now) for r in checked_routes],
            "support_packet": build_support_packet(project), "input_gaps": input_gaps,
            "total_score": None, "corruption_index": {"value": None, "formula_status": "NOT_APPROVED_NOT_COMPUTED",
            "use": "REVIEW_PROCESSING_PRIORITY_ONLY", "legal_effect": "NONE"},
            "canonical_rules_changed": False, "approval_status_changed": False,
            "deployment_status": "NOT_DEPLOYED", "external_action_performed": False,
            "source_verified_externally": False, "input_sha256": digest(project)}

def invariants(report):
    failures = []
    if report.get("total_score") is not None or report.get("corruption_index",{}).get("value") is not None:
        failures.append("UNAPPROVED_SCORE")
    if report.get("canonical_rules_changed") is not False or report.get("approval_status_changed") is not False:
        failures.append("UNAUTHORIZED_RULE_OR_APPROVAL_CHANGE")
    if report.get("external_action_performed") is not False or report.get("deployment_status") != "NOT_DEPLOYED":
        failures.append("UNAUTHORIZED_EXECUTION_CLAIM")
    if report.get("source_verified_externally") is not False:
        failures.append("UNSUPPORTED_EXTERNAL_VERIFICATION")
    for r in report.get("results", []):
        if r.get("source_verified_externally") is not False or r.get("status") in {"VERIFIED","FABRICATED_CONFIRMED"}:
            failures.append("UNSUPPORTED_CITATION_CERTAINTY")
    for r in report.get("routes", []):
        if r.get("automatic_state_change") is not False or r.get("sanction_decided") is not False:
            failures.append("AUTOMATIC_LIABILITY_OR_SANCTION")
    return sorted(set(failures))

def run_consistency_loop(project, now, max_iterations=3):
    """Bounded deterministic recheck, not model self-improvement or semantic proof."""
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int) or not 2 <= max_iterations <= 5:
        raise ValueError("max_iterations must be an integer between 2 and 5")
    previous, history = None, []
    for step in range(1, max_iterations + 1):
        report = analyze(project, now)
        failures = invariants(report)
        unresolved = (sum(len(r["flags"]) for r in report["results"])
                      + sum(len(r["flags"]) for r in report["routes"])
                      + len(report["support_packet"]["flags"]) + len(report["input_gaps"]))
        fingerprint = digest(report)
        history.append({"iteration": step, "output_sha256": fingerprint,
                        "invariant_failures": failures, "unresolved_flags": unresolved})
        if failures:
            state = "STOP_INVARIANT_FAILURE"
            break
        if fingerprint == previous:
            state = "STABLE_WITH_OPEN_ITEMS" if unresolved else "STABLE_LOCAL_CHECK_ONLY"
            break
        previous = fingerprint
    else:
        state = "STOP_ITERATION_LIMIT"
    report["consistency_loop"] = {"status": state, "history": history,
                                  "max_iterations": max_iterations, "automatic_rule_revision": False}
    report["release_status"] = "HOLD_FOR_COUNSEL_AND_EXPERT_REVIEW"
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--now", required=True, help="Explicit evaluation time, not a running legal clock")
    parser.add_argument("--output")
    args = parser.parse_args()
    project = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = run_consistency_loop(project, args.now)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with open(args.output, "x", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text, end="")

if __name__ == "__main__":
    main()

