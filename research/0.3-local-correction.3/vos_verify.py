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
from vos_safety import (STATEMENT_KINDS, ROLES, scope_check, linked_sources, assertion_sources, scrutiny,
                        review_statement, preserve_review_node, render_value, render_review_node, validate_project,
                        attribution_review, quote_correspondence)

from vos_support import support_reviews, render_support_request

VERSION = "0.3.0-design.2-local-correction.3"
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
    if not isinstance(kind, str) or (item.get("statement_role") is not None and not isinstance(item["statement_role"], str)):
        return result(item, "INVALID_INPUT", [flag("KIND_OR_STATEMENT_ROLE_NOT_TEXT")], "CORRECT_INPUT")
    if kind in STATEMENT_KINDS:
        return review_statement(item)
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
            and route.get("prior_control_ref"))))
    if route.get("itemized_explanation_complete") is True:
        flags.append(flag("EXPLANATION_COMPLETENESS_INPUT_NOT_REVERIFIED"))
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
            "deadline_assessment": "SUPPLIED_CLOCK_ONLY_NOT_LEGAL_DEADLINE_CERTIFICATION",
            "explanation_sufficiency": "NOT_DETERMINED",
            "input_explanation_complete": route.get("itemized_explanation_complete"),
            "victim_concession_required": False}

ROUTE_REF_FIELDS = ("prior_control_ref", "duty_ref", "nonperformance_ref", "act_source_ref",
                    "clock_basis_ref", "applicable_rule_ref", "receipt_ref", "explanation_ref")

def route_scope(project, route):
    return scope_check(project, route, linked_sources(
        route, project.get("sources", {}), ROUTE_REF_FIELDS, ("source_refs",)))


def build_support_packet(project):
    validate_project(project)
    ledger, gaps, qualified, quarantined = [], [], [], []
    sources = project.get("sources", {})
    for fact in project.get("facts", []):
        entry = copy.deepcopy(fact)
        ref = fact.get("source_ref")
        linked = assertion_sources(fact, sources)
        entry["source_link_present"] = bool(isinstance(ref, str) and isinstance(sources.get(ref), dict))
        entry["scope_review"] = scope_check(project, fact, linked)
        entry["evidence_scrutiny"] = scrutiny(fact, linked)
        entry["attribution_review"] = attribution_review(fact)
        entry["statement_role"] = entry["attribution_review"]["effective_role"]
        entry["source_correspondence"] = quote_correspondence(fact, sources.get(ref))
        if entry["attribution_review"]["conflict"]:
            gaps.append(flag("FACT_ATTRIBUTION_CONFLICT", fact_id=fact.get("id")))
        elif entry["statement_role"] not in ROLES:
            gaps.append(flag("FACT_STATEMENT_ROLE_INVALID", fact_id=fact.get("id")))
        if not entry["source_correspondence"]["eligible_as_source_quote_only"]:
            gaps.append(flag("FACT_SOURCE_CORRESPONDENCE_PENDING", fact_id=fact.get("id")))
        ledger.append(entry)
        if entry["scope_review"]["status"] != "IN_SCOPE":
            gaps.append(flag("FACT_SCOPE_QUARANTINED", fact_id=fact.get("id"), reasons=entry["scope_review"]["reasons"]))
            quarantined.append(entry)
        if not entry["source_link_present"]:
            gaps.append(flag("FACT_SOURCE_UNLINKED", fact_id=fact.get("id")))
        else:
            source_class = sources[ref].get("source_class")
            entry["source_class"] = source_class or "UNKNOWN"
            if source_class == "AI_GENERATED_ANALYSIS":
                gaps.append(flag("AI_ANALYSIS_NOT_INDEPENDENT_PROOF", fact_id=fact.get("id")))
            elif (fact.get("epistemic_status") == "SOURCE_STATED"
                  and source_class in {"PRIMARY_OFFICIAL_RECORD", "RESEARCH_PRIMARY_TEXT"}
                  and entry["scope_review"]["status"] == "IN_SCOPE"
                  and entry["statement_role"] in {"UNCLASSIFIED", "RECORD_STATEMENT"}
                  and entry["source_correspondence"]["eligible_as_source_quote_only"]):
                qualified.append(entry)
            else:
                gaps.append(flag("FACT_EPISTEMIC_REVIEW_PENDING", fact_id=fact.get("id")))
    for entry in ledger:
        entry["in_primary_paragraph"] = entry in qualified
    nodes, node_results = project.get("review_nodes", {}), {}
    for role in ("lawyer", "medical_expert"):
        node = nodes.get(role, {})
        node_results[role], complete = preserve_review_node(node)
        if not complete:
            gaps.append(flag("REVIEW_NODE_PENDING", role=role))
        if node.get("disagreement") not in (None, "", {}, []):
            gaps.append(flag("EXPERT_DISAGREEMENT_RETAINED", role=role,
                             preserved_in=["review_nodes", "draft_text"]))
    # Future named expert nodes must not disappear merely because they are not one of the defaults.
    for role, node in nodes.items():
        if role not in node_results:
            node_results[role], _ = preserve_review_node(node)
            gaps.append(flag("ADDITIONAL_REVIEW_NODE_RETAINED", role=role))
    paragraphs = ["피해자 지원 검토 초안 — 실제 법원 제출 전 대리인·전문가 확인",
                  "입증 대상: " + project.get("question", "질문 미특정")]
    if project.get("synthetic") is True:
        paragraphs.insert(0, "합성 입력에 대한 시험 출력 — 실제 사건 사실이나 제출 문서가 아닙니다.")
    paragraphs.append("사건·절차 식별자(입력값): " + str(project.get("case_id")) + " / "
                      + str(project.get("track_id", project.get("procedure_id"))))
    if qualified:
        paragraphs.append("같은 사건·절차의 제공 원문 직접인용(문자열 대조만 수행; 진실성·해석·독립 인증은 별도):")
    for f in qualified:
        paragraphs.append("- " + f.get("text", "") + " [" + f["source_ref"] + "; 원자료 인증은 별도]"
                          + (" [불리한 사실 포함]" if f.get("adverse") else ""))
        if f["evidence_scrutiny"]["gaps"]:
            paragraphs.append("위 기재의 원자료 접근·근거 점검 미완료: " + render_value(f["evidence_scrutiny"]))
    unqualified = [f for f in ledger if f not in qualified and f not in quarantined]
    if unqualified:
        paragraphs.append("미확인·가설·출처 보완 대상(확정 사실로 사용하지 않음):")
        labels = {"OPPONENT_CLAIM": "상대방 주장, 피해자 인정 아님", "VICTIM_REBUTTAL": "피해자 반박",
                  "EPISTEMIC_CAVEAT": "필요한 유보, 권리 포기 아님", "PROPOSED_CONCESSION": "양보 제안, 채택·동의 미확인",
                  "ATTRIBUTION_CONFLICT_REVIEW_REQUIRED": "발화자·문장 역할 충돌, 인정·사실로 승격하지 않음"}
        for f in unqualified:
            paragraphs.append("- " + f.get("text", "") + " [" + (f.get("source_ref") or "출처 미연결")
                              + "; " + f.get("epistemic_status", "UNKNOWN") + "; "
                              + labels.get(f["statement_role"], f["statement_role"]) + "; 입력 주장·원문 대응 미확인]"
                              + (" [불리한 사실 포함; 입력 기록으로 보존]" if f.get("adverse") and f.get("source_class") in {"PRIMARY_OFFICIAL_RECORD", "RESEARCH_PRIMARY_TEXT"} else ""))
    if quarantined:
        paragraphs.append("사건·절차 범위 및 출처 보완 대상: 아래 내용은 현재 사건의 사실·상대 주장·신청 근거로 편입하지 않음.")
        for f in quarantined:
            paragraphs.append("[범위 보류 " + str(f.get("id")) + "] " + f.get("text", "")
                              + " / " + render_value(f["scope_review"]))
    route_register = []
    for route in project.get("routes", []):
        scope = route_scope(project, route)
        route_review = scrutiny(route, linked_sources(route, sources, ROUTE_REF_FIELDS, ("source_refs",)))
        route_register.append({"input_record": copy.deepcopy(route), "scope_review": scope,
                               "evidence_scrutiny": route_review,
                               "operative_request": scope["status"] == "IN_SCOPE"})
        if scope["status"] != "IN_SCOPE":
            gaps.append(flag("ROUTE_SCOPE_QUARANTINED", route_id=route.get("id"), reasons=scope["reasons"]))
            paragraphs.append("[범위 보류 요청 " + str(route.get("id")) + "] 현재 사건의 실행 요청으로 편입하지 않음.\n"
                              + render_value(route) + "\n" + render_value(scope))
            continue
        paragraphs.extend(["검증 요청: " + route.get("question", "질문 미특정"),
                           "자료 통제 역할(입력값): " + (route.get("controller") or "미특정 — 확인 필요"),
                           "필요한 원자료: " + ", ".join(route.get("records_needed", [])),
                           "요청 취지: 위 자료의 제출·검색 범위·보존 및 미제공 사유에 대한 항목별 설명과 가능한 대체 검증 경로를 검토해 주시기 바랍니다.",
                           "통제자 설명·대체 원인·이해관계·정정협조 점검: " + render_value(route_review)])
    statement_reviews = []
    for item_index, item in enumerate(project.get("items", [])):
        if not isinstance(item, dict) or item.get("kind") not in STATEMENT_KINDS:
            continue
        review = verify(item)
        linked = assertion_sources(item, sources)
        review["input_item_index"] = item_index
        review["scope_review"] = scope_check(project, item, linked)
        review["evidence_scrutiny"] = scrutiny(item, linked)
        statement_reviews.append(review)
        label = "상대방 주장·피해자 반박·유보 구분 검토" if review["scope_review"]["status"] == "IN_SCOPE" else "범위 보류 진술, 현 사건 근거로 편입하지 않음"
        paragraphs.append(label + " [" + str(item.get("id")) + "]\n" + review["original_text"]
                          + "\n구분 결과(검토 후보): " + render_value(review["segments"])
                          + "\n양측 주장 공통의 근거·접근·설명 점검: " + render_value(review["evidence_scrutiny"]))
    for role, review in node_results.items():
        review["scope_review"] = scope_check(project, review["input_record"], assertion_sources(review["input_record"], sources))
        if review["scope_review"]["status"] != "IN_SCOPE":
            gaps.append(flag("EXPERT_SCOPE_REVIEW_PENDING", role=role))
        if review["input_record"]:
            paragraphs.append("전문 검토 기록 [" + role + "] — 입력 원문·이견·출처·버전·검토 ID를 보존; 진위 미인증·자동 합의 없음.\n"
                              + render_review_node(review["input_record"]) + "\n사건·절차 적용 상태: " + render_value(review["scope_review"]))
    for remedy in project.get("requested_remedies", []):
        paragraphs.append("구제 요청 후보(관할·요건은 대리인 확인): " + remedy)
    review_notes = ["자료 미확보를 피해자의 입증 실패·동의·권리 포기로 자동 전환하지 않습니다. 상대방·기관의 주장도 원자료 접근, 판단 근거, 통제·보존·검색·미제공 설명과 대체 검증 경로를 대조합니다.",
                       "자료 미확보는 곧바로 사실 부존재·자동 면책이나 위법·인과성 확정을 뜻하지 않습니다. 필요한 유보는 검증·자료제출·전문 검토 요청과 함께 유지합니다.",
                       "설계상 설명책임 점검은 법적 입증책임의 판정이 아닙니다. 적용 법령·판례와 구체적 사실은 대리인이 검토합니다.",
                       "의학적 가설·인과성·대체 원인은 전문가 검토 대상으로 유지하며, 기존 처분과 불리한 자료도 함께 대조합니다.",
                       "공리 충돌 해석·설계 승인과 최종 R3 판단은 인간에게 유보합니다."]
    access_reviews = support_reviews(project)
    for access_review in access_reviews:
        request = render_support_request(access_review)
        if request:
            paragraphs.append(request)
    paragraphs.append("원자료의 보존·제출·설명과 독립 검증 기회를 확보해 미해결 질문을 심리해 주시기 바랍니다.")
    return {"draft_text": "\n\n".join(paragraphs), "review_notes": review_notes,
            "access_reviews": access_reviews, "generated_blanket_concessions": [],
            "fact_ledger": ledger, "review_nodes": node_results,
            "quarantined_facts": quarantined, "route_register": route_register,
            "statement_reviews": statement_reviews,
            "flags": gaps, "automatic_deletion": False, "legal_privilege_claimed": False,
            "victim_concession_required": False, "filing_status": "GENERATED_DRAFT_ONLY"}

def analyze(project, now):
    validate_project(project)
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
    checked_results = []
    for item in project.get("items", []):
        review = verify(item)
        if isinstance(item, dict):
            linked = assertion_sources(item, refs)
            review["scope_review"] = scope_check(project, item, linked)
            review["evidence_scrutiny"] = scrutiny(item, linked)
            review["use_in_current_case"] = "REVIEW_CANDIDATE_ONLY" if review["scope_review"]["status"] == "IN_SCOPE" else "HOLD_FOR_SCOPE_REVIEW"
        checked_results.append(review)
    route_results = []
    for original, checked in zip(project.get("routes", []), checked_routes):
        reviewed = review_route(checked, now)
        reviewed["scope_review"] = route_scope(project, original)
        reviewed["input_record"] = copy.deepcopy(original)
        reviewed["evidence_scrutiny"] = scrutiny(original, linked_sources(original, refs, ROUTE_REF_FIELDS, ("source_refs",)))
        if reviewed["scope_review"]["status"] != "IN_SCOPE":
            reviewed["review_triggered"] = False
            reviewed["transition_review_candidate"] = None
            reviewed["process_status"] = "SCOPE_REVIEW_REQUIRED"
            reviewed["accountability_review"] = "HOLD_FOR_SCOPE_REVIEW"
            reviewed["next_action"] = "TECHNICAL_REVIEW_OF_SCOPE_AND_EXISTING_RECORDS"
            reviewed["flags"].append(flag("ROUTE_SCOPE_QUARANTINED", reasons=reviewed["scope_review"]["reasons"]))
        route_results.append(reviewed)
    packet = build_support_packet(project)
    return {"schema": "ADONIS-VOS-0.3-LOCAL-REVIEW/1.2-CANDIDATE", "version": VERSION,
            "data_class": "SYNTHETIC" if project.get("synthetic") is True else "PRIVATE_INPUT_NOT_FOR_PUBLICATION",
            "results": checked_results,
            "routes": route_results,
            "support_packet": packet, "input_gaps": input_gaps,
            "procedural_warnings": [w for r in packet["access_reviews"] for w in r["warnings"]],
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
    packet = report.get("support_packet", {})
    for fact in packet.get("fact_ledger", []):
        if fact.get("in_primary_paragraph") and fact.get("scope_review", {}).get("status") != "IN_SCOPE":
            failures.append("OUT_OF_SCOPE_PRIMARY_FACT")
        if fact.get("in_primary_paragraph") and (fact.get("attribution_review", {}).get("conflict")
                or fact.get("statement_role") not in {"UNCLASSIFIED", "RECORD_STATEMENT"}):
            failures.append("ATTRIBUTION_CONFLICT_PRIMARY_FACT")
        if fact.get("in_primary_paragraph") and not fact.get("source_correspondence", {}).get("eligible_as_source_quote_only"):
            failures.append("UNSUPPORTED_SOURCE_QUOTE_PROMOTION")
    for route in packet.get("route_register", []):
        if route.get("operative_request") and route.get("scope_review", {}).get("status") != "IN_SCOPE":
            failures.append("OUT_OF_SCOPE_OPERATIVE_ROUTE")
    for statement in packet.get("statement_reviews", []):
        index = statement.get("input_item_index")
        results = report.get("results", [])
        if not isinstance(index, int) or not 0 <= index < len(results) or statement.get("scope_review") != results[index].get("scope_review"):
            failures.append("STATEMENT_SCOPE_OUTPUT_DISAGREEMENT")
    for review in packet.get("review_nodes", {}).values():
        raw = review.get("input_record", {})
        if review.get("disagreement") != raw.get("disagreement"):
            failures.append("EXPERT_DISSENT_STRUCTURED_LOSS")
        if raw and render_review_node(raw) not in packet.get("draft_text", ""):
            failures.append("EXPERT_REVIEW_DRAFT_LOSS")
    if packet.get("victim_concession_required") is not False:
        failures.append("AUTOMATIC_VICTIM_CONCESSION")
    for access in packet.get("access_reviews", []):
        if (access.get("victim_concession_required") is not False
                or access.get("clinical_record_absence_reduces_victim_credibility") is not False
                or access.get("claimant_restatement_required") is not False):
            failures.append("VICTIM_BURDEN_SHIFT_IN_SUPPORT_REVIEW")
        if (access.get("recognized_relief_reassessment_requested") is not False
                or access.get("coordination_or_criminal_cartel_established") is not False
                or access.get("automatic_r26_transition") is not False
                or access.get("sanction_decided") is not False):
            failures.append("UNAUTHORIZED_JUDICIAL_OR_CRIMINAL_FINDING")
        if access.get("benefit_reversal_review", {}).get("repayment_or_confiscation_executed") is not False:
            failures.append("UNAUTHORIZED_BENEFIT_EXECUTION")
        if access.get("warnings") and access.get("scope_review", {}).get("status") != "IN_SCOPE":
            failures.append("CROSS_CASE_WARNING")
    if packet.get("generated_blanket_concessions"):
        failures.append("GENERATED_BLANKET_CONCESSION")
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

