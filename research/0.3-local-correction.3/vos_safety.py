"""Local-only review helpers. No legal findings, network, approval or dispatch."""
import copy
import json
import re

STATEMENT_KINDS = {"plaintiff_draft", "opponent_claim", "defendant_draft", "institution_claim"}
ROLES = {"OPPONENT_CLAIM", "VICTIM_REBUTTAL", "EPISTEMIC_CAVEAT", "PROPOSED_CONCESSION", "VICTIM_CLAIM", "UNCLASSIFIED", "RECORD_STATEMENT", "HYPOTHESIS"}
LIMITS = ("입증되는 것은 아니다", "확정된 것은 아니다", "인과관계가 입증되지", "책임이 인정되는 것은 아니다")
CONCESSIONS = ("원고의 입증 실패", "청구를 포기", "따라서 기각", "원고에게 모든 책임")


def scope_values(record):
    """Do not guess procedural equivalence or inherit absent identifiers."""
    case, track, procedure = (record.get(k) for k in ("case_id", "track_id", "procedure_id"))
    conflict = bool(track is not None and procedure is not None and track != procedure)
    values = (case, track if track is not None else procedure)
    valid = all(isinstance(x, str) and x.strip() for x in values)
    return values, valid, conflict


SOURCE_REF_FIELDS = {"source_ref", "explanation_ref", "prior_control_ref", "duty_ref", "nonperformance_ref",
                     "act_source_ref", "clock_basis_ref", "applicable_rule_ref", "receipt_ref"}
SOURCE_REF_ARRAYS = {"source_refs", "reviewed_sources"}
NON_SOURCE_REF_FIELDS = {"review_ref", "qualification_ref"}
SCOPE_FIELDS = {"case_id", "track_id", "procedure_id"}
MAX_SCAN_NODES = 10000
MAX_SCAN_DEPTH = 64


def audit_graph(record, registry, supplied_sources=None):
    """Inspect all nested declarations and referenced source dependencies once.

    Metadata about a review/qualification is preserved without pretending it is
    an evidence ID. Unknown *_ref(s) fields are held, not silently accepted.
    Bounds and cyclic provenance fail closed; input JSON is never modified.
    """
    found, declarations, reasons, scanned = {}, [], [], [0]
    active_sources, visited_sources = set(), set()
    active_objects = set()

    def scan(value, path, depth=0):
        scanned[0] += 1
        if scanned[0] > MAX_SCAN_NODES or depth > MAX_SCAN_DEPTH:
            reasons.append("SCOPE_TRAVERSAL_LIMIT:" + path)
            return
        if not isinstance(value, (dict, list)):
            return
        if id(value) in active_objects:
            reasons.append("CYCLIC_INPUT_OBJECT:" + path)
            return
        active_objects.add(id(value))
        if isinstance(value, dict):
            if SCOPE_FIELDS.intersection(value):
                declarations.append((path, value))
            for key, child in value.items():
                child_path = path + "." + str(key)
                if key in SOURCE_REF_FIELDS or key in SOURCE_REF_ARRAYS:
                    refs = child if key in SOURCE_REF_ARRAYS and isinstance(child, list) else [child]
                    if key in SOURCE_REF_ARRAYS and not isinstance(child, list):
                        reasons.append("SOURCE_REFERENCE_SHAPE_INVALID:" + child_path)
                    for ref in refs:
                        if ref is None or ref == "":
                            reasons.append("SOURCE_REFERENCE_MISSING_OR_EMPTY:" + child_path)
                            continue
                        if not isinstance(ref, str):
                            reasons.append("SOURCE_REFERENCE_SHAPE_INVALID:" + child_path)
                        else:
                            visit_source(ref, child_path, depth + 1)
                elif isinstance(key, str) and (key.endswith("_ref") or key.endswith("_refs")) and key not in NON_SOURCE_REF_FIELDS:
                    reasons.append("UNRECOGNIZED_REFERENCE_FIELD:" + child_path)
                scan(child, child_path, depth + 1)
        else:
            for index, child in enumerate(value):
                scan(child, path + "[" + str(index) + "]", depth + 1)
        active_objects.remove(id(value))

    def visit_source(ref, path, depth):
        if ref in active_sources:
            reasons.append("SOURCE_DEPENDENCY_CYCLE:" + ref)
            return
        if ref in visited_sources:
            return
        source = registry.get(ref)
        if source is None and supplied_sources and ref in supplied_sources:
            source = supplied_sources[ref]
        found[ref] = source
        if not isinstance(source, dict):
            reasons.append("SOURCE_MISSING_OR_INVALID:" + ref)
            visited_sources.add(ref)
            return
        active_sources.add(ref)
        # Root declarations are mandatory even if the source has no scope fields.
        declarations.append(("sources[" + ref + "]", source))
        scan(source, "sources[" + ref + "]", depth)
        active_sources.remove(ref)
        visited_sources.add(ref)

    scan(record, "record")
    for ref in (supplied_sources or {}):
        visit_source(ref, "supplied_sources", 0)
    return found, declarations, reasons


def scope_check(project, record, sources=None):
    expected, valid_project, conflict_project = scope_values(project)
    actual, valid_record, conflict_record = scope_values(record)
    found, declarations, reasons = audit_graph(record, project.get("sources", {}), sources)
    if conflict_project or conflict_record:
        reasons.append("SCOPE_ALIAS_CONFLICT")
    if not valid_project or not valid_record:
        reasons.append("SCOPE_IDENTIFIER_MISSING_OR_INVALID")
    if valid_project and valid_record and actual != expected:
        reasons.append("CASE_OR_PROCEDURE_SCOPE_MISMATCH")
    for path, source in declarations:
        values, valid, conflict = scope_values(source)
        if conflict:
            reasons.append("NESTED_SCOPE_ALIAS_CONFLICT:" + path)
        if not valid:
            reasons.append("NESTED_SCOPE_MISSING_OR_INVALID:" + path)
        elif valid_project and values != expected:
            reasons.append("NESTED_SCOPE_MISMATCH:" + path)
    return {"status": "IN_SCOPE" if not reasons else "QUARANTINED_FOR_SCOPE_REVIEW",
            "project_case_id": expected[0], "project_procedure_id": expected[1],
            "record_case_id": actual[0], "record_procedure_id": actual[1],
            "reasons": sorted(set(reasons)), "checked_source_refs": sorted(found),
            "scope_audit": "RECURSIVE_INLINE_AND_TRANSITIVE_SOURCES",
            "cross_scope_reuse_authorized": False, "interpretation_or_approval_performed": False}


def linked_sources(record, sources, fields=("source_ref",), array_fields=()):
    # Retained API name, now one recursive scanner for every record kind.
    return audit_graph(record, sources)[0]


def assertion_sources(record, sources):
    return audit_graph(record, sources)[0]


def attribution_review(record):
    role = record.get("statement_role", "UNCLASSIFIED")
    speaker = record.get("speaker", "NOT_RECORDED")
    normalized_speaker = speaker.strip().upper() if isinstance(speaker, str) else "INVALID"
    opposed = normalized_speaker in {"OPPONENT", "DEFENDANT", "INSTITUTION", "피고", "상대방", "기관"}
    conflicting = opposed and role not in {"UNCLASSIFIED", "OPPONENT_CLAIM"}
    unknown = normalized_speaker not in {"OPPONENT", "DEFENDANT", "INSTITUTION", "피고", "상대방", "기관",
                                         "VICTIM", "PLAINTIFF", "피해자", "원고", "NOT_RECORDED", "RECORD", "SOURCE"}
    if conflicting:
        effective = "ATTRIBUTION_CONFLICT_REVIEW_REQUIRED"
    elif unknown:
        effective = "UNKNOWN_ATTRIBUTION_REVIEW_REQUIRED"
    elif opposed:
        effective = "OPPONENT_CLAIM"
    elif normalized_speaker in {"VICTIM", "PLAINTIFF", "피해자", "원고"} and role in {"UNCLASSIFIED", "RECORD_STATEMENT"}:
        effective = "VICTIM_CLAIM"
    else:
        effective = role
    return {"input_speaker": speaker, "input_statement_role": role, "effective_role": effective,
            "conflict": conflicting, "speaker_class_unknown": unknown, "attribution_authenticated": False}


def quote_correspondence(fact, source):
    """Exact supplied-text quotation, never truth or semantic support certification."""
    source = source if isinstance(source, dict) else {}
    text = source.get("primary_text", source.get("text"))
    quote = fact.get("quoted_text")
    fact_text = fact.get("text")
    locator = fact.get("source_locator") or source.get("locator")
    present = isinstance(text, str) and bool(text.strip())
    quoted = isinstance(quote, str) and bool(quote.strip())
    direct = present and quoted and quote == fact_text and quote in text and isinstance(locator, str) and bool(locator.strip())
    return {"status": "DIRECT_QUOTE_IN_SUPPLIED_TEXT_ONLY" if direct else "INPUT_ASSERTION_NOT_SOURCE_CONFIRMED",
            "source_text_present": present, "direct_quote_supplied": quoted, "locator": locator,
            "semantic_support_verified": False, "source_authenticity_verified": False,
            "eligible_as_source_quote_only": bool(direct)}


def scrutiny(record, source_records=None):
    """The same questions apply to every speaker; none establish legal burden."""
    sources = source_records or {}
    evidence = record.get("evidence", {})
    if not isinstance(evidence, dict):
        evidence = {}
    supplied_text = any(isinstance(evidence.get(k), str) and bool(evidence[k].strip()) for k in ("primary_text", "text")) or any(
        isinstance(s, dict) and any(isinstance(s.get(k), str) and bool(s[k].strip()) for k in ("primary_text", "text"))
        for s in sources.values())
    gaps = []
    if not supplied_text:
        gaps.append("UNDERLYING_SOURCE_TEXT_NOT_SUPPLIED")
    if not sources and not (evidence.get("source_ref") and evidence.get("locator")):
        gaps.append("ASSERTION_SOURCE_LINK_PENDING")
    if any(not isinstance(s, dict) for s in sources.values()):
        gaps.append("ASSERTION_SOURCE_UNLINKED")
    access = record.get("source_access", "NOT_RECORDED")
    if access != "FULL_TEXT_SUPPLIED":
        gaps.append("SOURCE_ACCESS_REVIEW_PENDING")
    controller = record.get("controller") or record.get("evidence_control")
    if controller:
        gaps.append("CONTROLLER_EXPLANATION_REVIEW_PENDING")
        if record.get("itemized_explanation_complete") is True:
            gaps.append("EXPLANATION_COMPLETENESS_IS_INPUT_CLAIM_NOT_VERIFIED")
        if not record.get("explanation_ref") or not isinstance(sources.get(record.get("explanation_ref")), dict):
            gaps.append("CONTROLLER_EXPLANATION_SOURCE_PENDING")
    if not record.get("alternative_explanations"):
        gaps.append("ALTERNATIVE_EXPLANATIONS_REVIEW_PENDING")
    if controller and not record.get("interests_disclosure"):
        gaps.append("CONTROLLER_INTERESTS_REVIEW_PENDING")
    if not record.get("correction_or_cooperation_record"):
        gaps.append("CORRECTION_OR_COOPERATION_RECORD_PENDING")
    return {"speaker": record.get("speaker", "NOT_RECORDED"),
            "source_access": access, "underlying_text_supplied": supplied_text,
            "source_authenticity": "NOT_INDEPENDENTLY_AUTHENTICATED",
            "claim_truth": "NOT_DETERMINED", "controller": controller,
            "explanation_ref": record.get("explanation_ref"),
            "input_explanation_complete": record.get("itemized_explanation_complete"),
            "explanation_sufficiency": "NOT_DETERMINED",
            "alternative_explanations": copy.deepcopy(record.get("alternative_explanations")),
            "interests_disclosure": copy.deepcopy(record.get("interests_disclosure")),
            "correction_or_cooperation_record": copy.deepcopy(record.get("correction_or_cooperation_record")),
            "gaps": gaps,
            "next_review": ["원자료·인용 위치·판단 근거 대조", "자료 통제자의 보존·검색·미제공 사유 및 대체 검증 경로 검토"],
            "legal_burden_shift_determined": False,
            "victim_concession_required": False,
            "victim_restatement_required": False}


def classify_statement(item):
    """Bounded phrase/context hints, never a semantic or strategy verdict."""
    claim = item.get("claim", "")
    declared = item.get("statement_role")
    attribution = attribution_review(item)
    segments = []
    # Segment-level handling prevents one opponent quote hiding a later own concession.
    for part in re.split(r"(?<=[.!?。])\s+|\n+", claim):
        if not part.strip():
            continue
        limit_hits = [p for p in LIMITS if p in part]
        hits = [p for p in CONCESSIONS if p in part]
        contexts = [part[m.end():m.end()+35].split(",")[0]
                    for phrase in CONCESSIONS for m in re.finditer(re.escape(phrase), part)]
        rebuttal = bool(contexts) and all(re.search(
            r"^(?:(?:하는|한다는|할|했다는)?\s*것(?:은|이)\s*아니다|할\s*의사가\s*없|(?:라고|으로|라|를|을|라는|이라고|한다는|하는|한다|할|하|한다는 이유로|이라고 해서|이다)?\s*(?:볼 수 없|단정할 수 없|받아들일 수 없|동의하지 않|아니다|하지 않|할 수 없))", tail)
            for tail in contexts)
        quoted = bool(re.search(r"(?:피고|상대방|기관)(?:는|은|이|가)?.*(?:라고|이라고|라는 취지로)\s*(?:주장|회신)", part))
        # Conflicting adoption language or unbalanced quotes must remain unresolved.
        mixed = bool(re.search(r"(?:그러나|하지만|그렇지만|동의하|인정하|수용하|포기하겠)", part))
        if mixed:
            quoted = False
        # Explicit opponent provenance is retained as an input claim, not authenticated.
        if attribution["conflict"]:
            role = "MIXED_CONTEXT_REVIEW_REQUIRED"
        elif mixed and hits and item.get("kind") == "plaintiff_draft":
            role = "MIXED_CONTEXT_REVIEW_REQUIRED"
        elif item.get("kind") in {"opponent_claim", "defendant_draft", "institution_claim"}:
            role = "OPPONENT_CLAIM"
        elif hits and rebuttal:
            role = "VICTIM_REBUTTAL_CANDIDATE"
        elif hits and quoted:
            role = "OPPONENT_QUOTATION_CANDIDATE"
        elif hits and declared == "OPPONENT_CLAIM":
            role = "MIXED_CONTEXT_REVIEW_REQUIRED"
        elif hits:
            role = "POSSIBLE_CONCESSION_FOR_REVIEW"
        elif limit_hits:
            role = "EPISTEMIC_CAVEAT"
        else:
            role = declared if declared in ROLES else "UNCLASSIFIED"
        segments.append({"text": part, "role": role, "concession_phrase_matches": hits,
                         "epistemic_limit_matches": limit_hits,
                         "classification_basis": "INPUT_ROLE_AND_BOUNDED_TEXT_HINTS_NOT_SEMANTIC_PROOF"})
    return segments


def review_statement(item):
    segments = classify_statement(item)
    flags = []
    if any(s["epistemic_limit_matches"] for s in segments):
        flags.append({"code": "EPISTEMIC_LIMIT_RETAIN", "matches": [p for s in segments for p in s["epistemic_limit_matches"]]})
    roles = {s["role"] for s in segments}
    if "MIXED_CONTEXT_REVIEW_REQUIRED" in roles:
        status = "CONTEXT_REVIEW_REQUIRED"
        flags.append({"code": "MIXED_ATTRIBUTION_OR_ADOPTION_REVIEW", "review_only": True})
    elif "POSSIBLE_CONCESSION_FOR_REVIEW" in roles:
        status = "CONCESSION_RISK"
        flags.append({"code": "POSSIBLE_UNNECESSARY_CONCESSION", "review_only": True})
    elif roles & {"OPPONENT_CLAIM", "OPPONENT_QUOTATION_CANDIDATE"}:
        status = "OPPONENT_ASSERTION_REVIEW"
        flags.append({"code": "OPPONENT_ASSERTION_NOT_VICTIM_ADMISSION"})
    elif "VICTIM_REBUTTAL_CANDIDATE" in roles:
        status = "REBUTTAL_CONTEXT_REVIEW"
        flags.append({"code": "REBUTTAL_NOT_AUTOMATIC_CONCESSION"})
    elif flags:
        status = "REQUIRED_LIMIT_REVIEW"
    else:
        status = "NO_RULE_HIT"
    if item.get("statement_role") is not None and item["statement_role"] not in ROLES:
        flags.append({"code": "STATEMENT_ROLE_INVALID"})
    if item.get("evidence_control") == "institution" and not item.get("disclosure_request"):
        flags.append({"code": "EVIDENCE_ASYMMETRY_NOT_ADDRESSED"})
    return {"id": item.get("id"), "status": status, "flags": flags,
            "action": "GENERATE_SUPPORT_DRAFT_FOR_REVIEW", "human_approval_required": True,
            "source_verified_externally": False, "total_score": None,
            "original_text": item.get("claim", ""), "automatic_deletion": False,
            "segments": segments, "evidence_scrutiny": scrutiny(item),
            "attribution_review": attribution_review(item),
            "victim_concession_required": False, "semantic_review_required": True}


def preserve_review_node(node):
    # Retain every input field, including future dissent revisions and source arrays.
    complete = bool(node.get("review_ref") and node.get("scope") and node.get("qualification_ref"))
    out = {"status": "REVIEW_RECORDED_PENDING_AUTHENTICITY_CHECK" if complete else "REVIEW_PENDING",
           "scope": copy.deepcopy(node.get("scope")), "review_ref": node.get("review_ref"),
           "qualification_ref": node.get("qualification_ref"), "opinion": copy.deepcopy(node.get("opinion")),
           "disagreement": copy.deepcopy(node.get("disagreement")),
           "input_record": copy.deepcopy(node), "independently_authenticated": False,
           "automatic_resolution": False}
    return out, complete


def render_value(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def render_review_node(record):
    labels = {"opinion": "검토 의견", "disagreement": "이견 원문과 상세 기록",
              "scope": "전문 검토 범위", "review_ref": "일반 검토 기록 참조",
              "review_id": "검토 ID", "version": "검토 버전", "qualification_ref": "자격 참조",
              "reviewed_sources": "실제 읽은 출처(입력값)", "response": "회신", "correction": "정정 기록"}
    return "\n".join(labels.get(k, k) + ": " + render_value(v) for k, v in record.items())


def validate_project(project):
    if not isinstance(project, dict):
        raise ValueError("Project must be an object")
    for field in ("items", "routes", "facts", "requested_remedies"):
        if not isinstance(project.get(field, []), list):
            raise ValueError(field + " must be an array")
    for field in ("sources", "review_nodes"):
        if not isinstance(project.get(field, {}), dict):
            raise ValueError(field + " must be an object")
        if any(not isinstance(x, dict) for x in project.get(field, {}).values()):
            raise ValueError(field + " values must be objects")
    for source in project.get("sources", {}).values():
        if source.get("source_class") is not None and not isinstance(source["source_class"], str):
            raise ValueError("source_class must be text")
    for item in project.get("items", []):
        if isinstance(item, dict):
            for key in ("kind", "claim", "statement_role"):
                if key in item and not isinstance(item[key], str):
                    raise ValueError(key + " must be text")
    if not all(isinstance(x, str) for x in project.get("requested_remedies", [])):
        raise ValueError("requested_remedies must contain text")
    if not isinstance(project.get("question", ""), str):
        raise ValueError("question must be text")
    for field in ("routes", "facts"):
        if any(not isinstance(x, dict) for x in project.get(field, [])):
            raise ValueError(field + " entries must be objects")
    for record in [x for field in ("items", "routes", "facts") for x in project.get(field, []) if isinstance(x, dict)]:
        for key in ("id", "source_ref", "explanation_ref", "prior_control_ref", "duty_ref", "nonperformance_ref", "act_source_ref", "clock_basis_ref", "applicable_rule_ref", "receipt_ref"):
            if record.get(key) is not None and not isinstance(record[key], str):
                raise ValueError(key + " must be text when supplied")
        for key in ("text", "question", "controller", "coordinator", "epistemic_status", "statement_role", "speaker", "availability", "current_evidence_state", "clock_type", "delivery_state"):
            if record.get(key) is not None and not isinstance(record[key], str):
                raise ValueError(key + " must be text when supplied")
        for key in ("source_refs", "records_needed"):
            if key in record and (not isinstance(record[key], list) or not all(isinstance(x, str) for x in record[key])):
                raise ValueError(key + " must be an array of text")
