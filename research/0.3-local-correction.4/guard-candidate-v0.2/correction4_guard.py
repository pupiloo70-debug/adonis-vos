"""Adonis VOS 0.3 correction.4 **isolated research candidate**.

Synthetic-only, fail-closed attribution and item-level scope guard.
Not integrated with correction.3 / the 0.2 runtime; not a legal or medical classifier.
Supplied labels, source descriptions and quotes are not independently authenticated.
"""
from __future__ import annotations
from collections import Counter, defaultdict, deque
from datetime import datetime
from itertools import groupby
from typing import Any

KINDS = {
    'AUTOPSY_RECORD_PRESENT', 'CLINICAL_RECORD_ABSENT',
    'AUTOPSY_EXCLUDED_FOR_NO_CLINICAL_RECORD', 'INDEPENDENT_REVIEW_REFUSED',
    'ESSENTIAL_RECORD_NOT_PRODUCED', 'GAP_RELIED_ON_AGAINST_CLAIMANT',
    'INSTITUTIONAL_BENEFIT_RETAINED', 'CAUSATION_REASONING_UNEXPLAINED',
    'SUSCEPTIBILITY_NOT_ASSESSED', 'RECOGNIZED_RELIEF_EXISTS',
}
SOURCE_CLASSES = {'PRIMARY_OFFICIAL_RECORD', 'CONTEMPORANEOUS_RECORD',
                  'CLAIMANT_TESTIMONY', 'EXPERT_OPINION', 'RESEARCH_PRIMARY_TEXT'}
DECISION_KINDS = {
    'AUTOPSY_EXCLUDED_FOR_NO_CLINICAL_RECORD': 'EXCLUDED',
    'INDEPENDENT_REVIEW_REFUSED': 'REFUSED',
    'GAP_RELIED_ON_AGAINST_CLAIMANT': 'PROOF_GAP_APPLIED',
}
WARNING_RULES = {
    'AUTOPSY_EVIDENCE_EXCLUSION_WARNING': {'AUTOPSY_RECORD_PRESENT', 'AUTOPSY_EXCLUDED_FOR_NO_CLINICAL_RECORD'},
    'CIRCULAR_BURDEN_SHIFT_WARNING': {'ESSENTIAL_RECORD_NOT_PRODUCED', 'INDEPENDENT_REVIEW_REFUSED', 'GAP_RELIED_ON_AGAINST_CLAIMANT'},
    'HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING': {'ESSENTIAL_RECORD_NOT_PRODUCED', 'INDEPENDENT_REVIEW_REFUSED', 'GAP_RELIED_ON_AGAINST_CLAIMANT', 'INSTITUTIONAL_BENEFIT_RETAINED'},
    'CAUSATION_METHOD_CONSISTENCY_REVIEW': {'CAUSATION_REASONING_UNEXPLAINED'},
    'INDIVIDUAL_SUSCEPTIBILITY_REVIEW_OPEN': {'SUSCEPTIBILITY_NOT_ASSESSED'},
}
REMEDY_TYPES = {'REVIEW_GRANTED', 'ACCESS_PERFORMED', 'ACCESS_PARTIAL', 'ACCESS_REVOKED'}
SCOPE_KEYS = ('case_id', 'track_id', 'subject_id')
WARNING_CONTEXT_KEYS = SCOPE_KEYS + ('material_id', 'question_id')


def _identifier(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _scope_conflicts(record: Any, target: dict, depth=0) -> list[str]:
    """Conservatively detect conflicting nested scope claims (no semantic NLP)."""
    if depth > 24:
        return ['SCOPE_NESTING_LIMIT']
    reasons = []
    if isinstance(record, dict):
        for k in target:
            if k in record and k in target and record[k] != target[k]:
                reasons.append('SCOPE_MISMATCH_' + k.upper())
        for k, v in record.items():
            if isinstance(v, (dict, list)):
                reasons += _scope_conflicts(v, target, depth + 1)
    elif isinstance(record, list):
        for v in record:
            if isinstance(v, (dict, list)):
                reasons += _scope_conflicts(v, target, depth + 1)
    return sorted(set(reasons))


def _source_link(source: Any, quote: Any, target: dict) -> list[str]:
    issues = []
    if not isinstance(source, dict) or not source:
        return ['SOURCE_MISSING']
    issues += _scope_conflicts(source, target)
    for key in SCOPE_KEYS:
        if not _identifier(source.get(key)) or source.get(key) != target.get(key):
            issues.append('SOURCE_' + key.upper() + '_NOT_BOUND')
    if not isinstance(source.get('source_class'), str) or source['source_class'] not in SOURCE_CLASSES:
        issues.append('SOURCE_CLASS_NOT_ADMISSIBLE_FOR_REVIEW')
    primary = source.get('primary_text', source.get('text'))
    if not isinstance(primary, str) or not isinstance(quote, str) or not quote.strip() or quote not in primary:
        issues.append('QUOTE_NOT_LINKED')
    if not isinstance(source.get('locator'), str) or not source['locator'].strip():
        issues.append('LOCATOR_MISSING')
    return sorted(set(issues))


def _attribution_issues(obs: dict, source: dict, review: dict) -> list[str]:
    """P01/P03: typed provenance binds acts to actors; no claim of semantic authentication."""
    kind = obs['kind']
    issues = []
    for k in ('actor_id', 'event_type', 'statement_role'):
        if not _identifier(obs.get(k)):
            issues.append('OBS_MISSING_' + k.upper())
        if not _identifier(source.get(k)):
            issues.append('SOURCE_MISSING_' + k.upper())
        if obs.get(k) != source.get(k):
            issues.append('ATTRIBUTION_CONFLICT_' + k.upper())
    if not _identifier(obs.get('actor_role')):
        issues.append('OBS_MISSING_ACTOR_ROLE')
    # Older synthetic fixtures omit these optional source labels. When present,
    # they must agree; their absence is never represented as authentication.
    for key in ('actor_role', 'decision_status'):
        if key in source and source[key] != obs.get(key):
            issues.append('ATTRIBUTION_CONFLICT_' + key.upper())
    actor_context = {key: obs[key] for key in ('actor_id', 'event_type', 'statement_role',
                                             'actor_role', 'decision_status') if key in obs}
    issues += _scope_conflicts(source, actor_context)
    issues += _scope_conflicts(obs, actor_context)
    if kind in DECISION_KINDS:
        if obs.get('event_type') != 'DECISION':
            issues.append('DECISION_MISLABELED_NONDECISION')
        if obs.get('actor_role') != 'DECISION_BODY':
            issues.append('DECISION_ROLE_MISMATCH')
        if obs.get('actor_id') != review.get('decision_body'):
            issues.append('DECISION_BODY_UNLINKED')
        if obs.get('decision_status') != DECISION_KINDS[kind]:
            issues.append('DECISION_STATUS_CONFLICT')
        if obs.get('statement_role') != 'DECISION_RECORD':
            issues.append('NOT_DECISION_STATEMENT')
    if kind == 'ESSENTIAL_RECORD_NOT_PRODUCED':
        if obs.get('event_type') != 'NONPRODUCTION' or obs.get('actor_id') != review.get('controller'):
            issues.append('CONTROLLER_ACT_UNLINKED')
        if obs.get('actor_role') != 'CONTROLLER':
            issues.append('CONTROLLER_ROLE_MISMATCH')
    if kind == 'INSTITUTIONAL_BENEFIT_RETAINED' and obs.get('event_type') != 'ASSESSMENT':
        issues.append('BENEFIT_ASSESSMENT_EVENT_MISMATCH')
    return sorted(set(issues))


def _dependency_review(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Linear iterative graph processing: no Python recursion, no first-ID winner.

    Missing/held prerequisites propagate only to their dependents. Kahn's
    algorithm then isolates cycles and their dependents, retaining all other DAGs.
    """
    by_id = {row['id']: row for row in rows}
    reverse = defaultdict(set)
    reasons = {}
    for row in rows:
        for dependency in set(row['depends_on']):
            reverse[dependency].add(row['id'])
            if dependency not in by_id:
                reasons[row['id']] = 'DEPENDENCY_UNAVAILABLE'
    pending = deque(reasons)
    while pending:
        bad = pending.popleft()
        for dependent in reverse[bad]:
            if dependent not in reasons:
                reasons[dependent] = 'DEPENDENCY_UNAVAILABLE'
                pending.append(dependent)
    remaining = {key for key in by_id if key not in reasons}
    indegree = {key: len(set(by_id[key]['depends_on'])) for key in remaining}
    ready = deque(key for key in by_id if key in remaining and indegree[key] == 0)
    proven = set()
    while ready:
        node = ready.popleft()
        proven.add(node)
        for dependent in reverse[node]:
            if dependent in remaining:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    ready.append(dependent)
    for key in remaining - proven:
        reasons[key] = 'DEPENDENCY_CYCLE'
    return ([row for row in rows if row['id'] not in reasons],
            [{**row, 'reason': [reasons[row['id']]]} for row in rows if row['id'] in reasons])


def _item_review(project: dict, review: dict) -> tuple[list[dict], list[dict]]:
    sources = project.get('sources', {})
    target = {k: project[k] for k in SCOPE_KEYS if k in project}
    accepted, held = [], []
    observation_list = review.get('observations', [])
    if not isinstance(observation_list, list):
        return [], [{'id': None, 'reason': ['OBSERVATIONS_NOT_ARRAY']}]
    counts = Counter(obs['id'] for obs in observation_list
                     if isinstance(obs, dict) and _identifier(obs.get('id')))
    for obs in observation_list:
        reasons = []
        if not isinstance(obs, dict):
            held.append({'id': None, 'reason': ['OBSERVATION_NOT_OBJECT']})
            continue
        oid = obs.get('id')
        if not _identifier(oid) or counts[oid] > 1:
            reasons.append('INVALID_OR_DUPLICATE_OBSERVATION_ID')
        if not isinstance(obs.get('kind'), str) or obs['kind'] not in KINDS:
            reasons.append('UNKNOWN_OBSERVATION_KIND')
        for key in SCOPE_KEYS:
            if not _identifier(obs.get(key)) or obs.get(key) != target.get(key):
                reasons.append('OBS_' + key.upper() + '_NOT_BOUND_TO_PROJECT')
        # Material is mandatory for this research schema. A question can be
        # absent, but never borrowed from another row to complete a warning.
        if not _identifier(obs.get('material_id')):
            reasons.append('OBS_MATERIAL_ID_REQUIRED')
        if 'question_id' in obs and not _identifier(obs['question_id']):
            reasons.append('OBS_QUESTION_ID_INVALID')
        # None is an explicit absent-question bucket, not permission to take a
        # question label from nested metadata. Conflicting nested labels hold
        # only this item instead of silently changing its warning context.
        item_target = {**target, 'material_id': obs.get('material_id'),
                       'question_id': obs.get('question_id')}
        for key in ('material_id', 'question_id'):
            if key in review and obs.get(key) != review[key]:
                reasons.append('OBS_REVIEW_' + key.upper() + '_UNLINKED')
        reasons += _scope_conflicts(obs, item_target)
        ref = obs.get('source_ref')
        if not _identifier(ref):
            reasons.append('SOURCE_REF_INVALID')
        source = sources.get(ref) if isinstance(sources, dict) and isinstance(ref, str) else None
        reasons += _source_link(source, obs.get('quoted_text'), item_target)
        if isinstance(source, dict):
            for key in ('material_id', 'question_id'):
                if source.get(key) != obs.get(key):
                    reasons.append('SOURCE_OBSERVATION_' + key.upper() + '_CONFLICT')
            if not _identifier(source.get('material_id')):
                reasons.append('SOURCE_MATERIAL_ID_REQUIRED')
            if 'question_id' in source and not _identifier(source['question_id']):
                reasons.append('SOURCE_QUESTION_ID_INVALID')
            if isinstance(obs.get('kind'), str) and obs['kind'] in KINDS:
                reasons += _attribution_issues(obs, source, review)
        deps = obs.get('depends_on', [])
        valid_deps = isinstance(deps, list) and all(_identifier(d) for d in deps)
        if not valid_deps:
            reasons.append('INVALID_DEPENDENCY_FORMAT')
        row = {'id': oid, 'kind': obs.get('kind'), 'source_ref': ref,
               'depends_on': list(deps) if valid_deps else None,
               'source_class': source.get('source_class') if isinstance(source, dict) else None,
               **{key: obs.get(key) for key in WARNING_CONTEXT_KEYS},
               'actor_id': obs.get('actor_id'), 'actor_role': obs.get('actor_role'),
               'event_type': obs.get('event_type'),
               'label_semantically_verified': False,
               'source_truth_authenticated': False}
        if reasons:
            held.append({**row, 'reason': sorted(set(reasons))})
        else:
            accepted.append(row)
    accepted, dependent_held = _dependency_review(accepted)
    return accepted, held + dependent_held


def _warnings(accepted: list[dict], review: dict) -> list[dict]:
    """No evidence combination across case, track, person, material or question.

    An omitted question is an explicit unqualified bucket, not a wildcard.
    Retained observations need not jointly satisfy a warning's prerequisites.
    """
    groups = defaultdict(list)
    for row in accepted:
        groups[tuple(row[key] for key in WARNING_CONTEXT_KEYS)].append(row)
    warnings = []
    for context, rows in groups.items():
        kinds = {row['kind'] for row in rows}
        for code, required in WARNING_RULES.items():
            if not required <= kinds:
                continue
            if code == 'HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING' and not (
                    _identifier(review.get('controller')) and _identifier(review.get('decision_body'))):
                continue
            basis = [row for row in rows if row['kind'] in required]
            warnings.append({'code': code,
                             'context': dict(zip(WARNING_CONTEXT_KEYS, context)),
                             'basis_observations': [x['id'] for x in basis],
                             'source_refs': sorted({x['source_ref'] for x in basis}),
                             'status': 'SOURCE_LINKED_WARNING_FOR_HUMAN_REVIEW',
                             'asserted_actor_or_event_not_independently_authenticated': True,
                             'not_a_legal_or_medical_finding': True})
    return warnings


def _remedies(project: dict, review: dict) -> dict:
    target = {k: project[k] for k in SCOPE_KEYS if k in project}
    sources = project.get('sources', {})
    accepted, held = [], []
    event_list = review.get('remediation_events', [])
    if not isinstance(event_list, list):
        return {'question_material_states': [], 'held_events': [{'id': None, 'reason': ['REMEDIATION_EVENTS_NOT_ARRAY']}],
                'prior_burdens_preserved': True, 'access_truth_independently_authenticated': False,
                'previous_cost_amount': None}
    counts = Counter(event['id'] for event in event_list
                     if isinstance(event, dict) and _identifier(event.get('id')))
    for event in event_list:
        if not isinstance(event, dict):
            held.append({'id': None, 'reason': ['EVENT_NOT_OBJECT']})
            continue
        err = _scope_conflicts(event, target)
        eid = event.get('id')
        if not _identifier(eid) or counts[eid] > 1:
            err.append('INVALID_OR_DUPLICATE_EVENT_ID')
        if not isinstance(event.get('type'), str) or event['type'] not in REMEDY_TYPES:
            err.append('UNKNOWN_REMEDIATION_EVENT')
        if any(not _identifier(event.get(k)) for k in ('question_id', 'subject_id', 'material_id')):
            err.append('QUESTION_SUBJECT_MATERIAL_REQUIRED')
        for key in SCOPE_KEYS:
            if not _identifier(event.get(key)) or event.get(key) != target.get(key):
                err.append('EVENT_' + key.upper() + '_NOT_BOUND')
        for key in ('material_id', 'question_id'):
            if key in review and event.get(key) != review[key]:
                err.append('EVENT_REVIEW_' + key.upper() + '_UNLINKED')
        ref = event.get('source_ref')
        source = sources.get(ref) if isinstance(sources, dict) and isinstance(ref, str) else None
        event_target = {**target, **{key: event[key] for key in ('material_id', 'question_id')
                                   if _identifier(event.get(key))}}
        err += _scope_conflicts(event, event_target)
        err += _source_link(source, event.get('quoted_text'), event_target)
        remedy_type_target = {'type': event.get('type'), 'event_type': event.get('type')}
        err += _scope_conflicts(event, remedy_type_target)
        err += _scope_conflicts(source, remedy_type_target)
        if isinstance(source, dict):
            for k in ('subject_id', 'material_id', 'question_id'):
                if source.get(k) != event.get(k):
                    err.append('REMEDY_SOURCE_' + k.upper() + '_UNLINKED')
        date = event.get('occurred_at')
        try:
            dt = datetime.fromisoformat(date)
            if dt.tzinfo is None:
                raise ValueError('naive datetime')
        except (TypeError, ValueError):
            err.append('INVALID_EVENT_TIME')
            dt = None
        if err:
            held.append({'id': eid, 'reason': sorted(set(err))})
        else:
            accepted.append({'id': eid, 'type': event['type'], 'question_id': event['question_id'],
                             'subject_id': event['subject_id'], 'material_id': event['material_id'],
                             'occurred_at': date, 'source_ref': event['source_ref'], '_sort': dt})
    by_context = defaultdict(list)
    for item in sorted(accepted, key=lambda x: (x['_sort'], x['id'])):
        key = (item['question_id'], item['subject_id'], item['material_id'])
        by_context[key].append(item)
    statuses = {
        'REVIEW_GRANTED': 'GRANT_ONLY_ACCESS_NOT_ESTABLISHED',
        'ACCESS_PERFORMED': 'ACCESS_REPORTED_AUTHENTICATION_PENDING',
        'ACCESS_PARTIAL': 'PARTIAL_ACCESS_REPORTED_REMAINDER_OPEN',
        'ACCESS_REVOKED': 'ACCESS_REVOKED_REVIEW_OPEN',
    }
    states = []
    for key, items in by_context.items():
        rec = {'question_id': key[0], 'subject_id': key[1],
               'material_id': key[2], 'event_history': [], 'event_batches': []}
        for instant, simultaneous in groupby(items, key=lambda x: x['_sort']):
            batch = list(simultaneous)
            types = {item['type'] for item in batch}
            conflict = len(types) > 1
            rec['status'] = ('SIMULTANEOUS_CONFLICT_REVIEW_OPEN' if conflict
                             else statuses[next(iter(types))])
            rec['latest_event_order_ambiguous'] = conflict
            rec['event_history'].extend(item['id'] for item in batch)
            rec['event_batches'].append({
                'occurred_at': instant.isoformat(),
                'event_ids': [item['id'] for item in batch],
                'reported_types': sorted(types),
                'conflicting_types': conflict,
                'order_within_timestamp_established': len(batch) == 1,
            })
        states.append(rec)
    return {'question_material_states': states, 'held_events': held,
            'prior_burdens_preserved': True, 'access_truth_independently_authenticated': False,
            'previous_cost_amount': None}


def evaluate(project: dict) -> dict:
    """P01..P05 candidate. No mutations, judicial findings, dispatch, or approval."""
    if not isinstance(project, dict) or project.get('synthetic') is not True:
        raise ValueError('CANDIDATE_SYNTHETIC_ONLY')
    target = {k: project[k] for k in SCOPE_KEYS if k in project}
    reports = []
    review_list = project.get('support_reviews', [])
    if not isinstance(review_list, list):
        raise ValueError('SUPPORT_REVIEWS_NOT_ARRAY')
    for review in review_list:
        if not isinstance(review, dict):
            continue
        review_target = {**target, 'material_id': review.get('material_id'),
                         'question_id': review.get('question_id')}
        # Review metadata describes the review. Child items have their own
        # quarantine path and must not turn one bad item into a review-wide hold.
        review_metadata = {key: value for key, value in review.items()
                           if key not in ('observations', 'remediation_events')}
        reasons = _scope_conflicts(review_metadata, review_target)
        for key in SCOPE_KEYS:
            if not _identifier(project.get(key)):
                reasons.append('PROJECT_' + key.upper() + '_UNSPECIFIED')
            if not _identifier(review.get(key)) or review.get(key) != project.get(key):
                reasons.append('REVIEW_' + key.upper() + '_NOT_BOUND_TO_PROJECT')
        for key in ('material_id', 'question_id'):
            if key in review and not _identifier(review[key]):
                reasons.append('REVIEW_' + key.upper() + '_INVALID')
        if review.get('purpose') != 'VICTIM_SUPPORT':
            reasons.append('PURPOSE_NOT_AUTHORIZED')
        if reasons:
            reports.append({'id': review.get('id'), 'status': 'REVIEW_SCOPE_HELD',
                            'held_reason': sorted(set(reasons)), 'warnings': [],
                            'accepted_observations': [],
                            'held_observations': [], 'remediation': {},
                            'items_not_evaluated_due_to_review_scope': True})
            continue
        accepted, held = _item_review(project, review)
        warnings = _warnings(accepted, review)
        remediation = _remedies(project, review)
        reports.append({'id': review.get('id'),
                        'status': 'WARNING_REVIEW_OPEN' if warnings else 'SOURCE_OR_PROVENANCE_REVIEW_OPEN',
                        'warnings': warnings, 'accepted_observations': accepted,
                        'held_observations': held, 'remediation': remediation,
                        'unresolved_source_and_provenance_questions': bool(held or remediation['held_events']),
                        'clinical_record_absence_reduces_victim_credibility': False,
                        'recognized_relief_reassessment_requested': False,
                        'benefit_reversal_executed': False,
                        'specific_actor_criminal_or_disciplinary_guilt_established': False})
    return {'schema': 'ADONIS-VOS-CORRECTION4-GUARD-CANDIDATE/0.2',
            'scope': 'ISOLATED_SYNTHETIC_RESEARCH_NOT_INTEGRATED',
            'reviews': reports,
            'release_or_R3_approval_changed': False,
            'civic_trace_045_maintained': True, 'civic_trace_046_approval_deferred': True,
            'axioms_AX01_to_AX09_unchanged': True,
            'legal_or_medical_finding': False, 'external_execution': False,
            'total_score': None}
