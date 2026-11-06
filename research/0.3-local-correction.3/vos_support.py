"""Source-linked, case-scoped victim-support review. No adjudication or dispatch.

Observation kinds are supplied human labels. Exact quote matching establishes
text correspondence only, never that the label is a correct reading of it.
"""
import copy
from vos_safety import scope_check, assertion_sources

KINDS = {
    'AUTOPSY_RECORD_PRESENT', 'CLINICAL_RECORD_ABSENT',
    'AUTOPSY_EXCLUDED_FOR_NO_CLINICAL_RECORD', 'INDEPENDENT_REVIEW_REFUSED',
    'ESSENTIAL_RECORD_NOT_PRODUCED', 'GAP_RELIED_ON_AGAINST_CLAIMANT',
    'INSTITUTIONAL_BENEFIT_RETAINED', 'CAUSATION_REASONING_UNEXPLAINED',
    'SUSCEPTIBILITY_NOT_ASSESSED', 'RECOGNIZED_RELIEF_EXISTS',
}
SOURCE_CLASSES = {'PRIMARY_OFFICIAL_RECORD', 'CONTEMPORANEOUS_RECORD',
                  'CLAIMANT_TESTIMONY', 'EXPERT_OPINION', 'RESEARCH_PRIMARY_TEXT'}
MAX_REVIEWS, MAX_OBSERVATIONS = 20, 100


def validate_support_reviews(project):
    reviews = project.get('support_reviews', [])
    if not isinstance(reviews, list) or len(reviews) > MAX_REVIEWS:
        raise ValueError('support_reviews must be an array of at most 20 entries')
    ids = set()
    for review in reviews:
        if not isinstance(review, dict) or not isinstance(review.get('id'), str) or not review['id'].strip() or review['id'] in ids:
            raise ValueError('Invalid or duplicate support review ID')
        ids.add(review['id'])
        if review.get('purpose') != 'VICTIM_SUPPORT':
            raise ValueError('Only explicit VICTIM_SUPPORT review is supported')
        for field in ('controller', 'decision_body'):
            if field in review and (not isinstance(review[field], str) or not review[field].strip()):
                raise ValueError(field + ' must be nonempty text')
        observations = review.get('observations', [])
        if not isinstance(observations, list) or len(observations) > MAX_OBSERVATIONS:
            raise ValueError('observations must be an array of at most 100 entries')
        oids = set()
        for o in observations:
            if not isinstance(o, dict) or o.get('kind') not in KINDS:
                raise ValueError('Unknown support observation kind')
            if not isinstance(o.get('id'), str) or not o['id'].strip() or o['id'] in oids:
                raise ValueError('Invalid or duplicate observation ID')
            oids.add(o['id'])
            for field in ('source_ref', 'quoted_text'):
                if not isinstance(o.get(field), str) or not o[field].strip():
                    raise ValueError(field + ' must be nonempty text')


def review_access(project, review):
    scope = scope_check(project, review, assertion_sources(review, project.get('sources', {})))
    accepted, pending = [], []
    for observation in review.get('observations', []):
        source = project.get('sources', {}).get(observation['source_ref'], {})
        o_scope = scope_check(project, observation, assertion_sources(observation, project.get('sources', {})))
        source_text = source.get('primary_text', source.get('text'))
        matched = (isinstance(source_text, str) and observation['quoted_text'] in source_text
                   and isinstance(source.get('locator'), str) and bool(source['locator'].strip()))
        eligible = (matched and source.get('source_class') in SOURCE_CLASSES
                    and scope['status'] == o_scope['status'] == 'IN_SCOPE')
        row = {'input_record': copy.deepcopy(observation), 'scope_review': o_scope,
               'quote_matches_supplied_text': matched, 'source_class': source.get('source_class', 'UNKNOWN'),
               'observation_label_verified_semantically': False,
               'truth_or_independence_authenticated': False,
               'eligible_for_warning_review': eligible}
        (accepted if eligible else pending).append(row)
    kinds = {o['input_record']['kind'] for o in accepted}
    warnings = []
    def add(code, label, required):
        support = [x for x in accepted if x['input_record']['kind'] in required]
        warnings.append({'code': code, 'label_ko': label,
                         'basis_observations': [x['input_record']['id'] for x in support],
                         'source_refs': sorted({x['input_record']['source_ref'] for x in support}),
                         'status': 'SOURCE_LINKED_WARNING_FOR_REVIEW',
                         'epistemic_basis': 'SUPPLIED_LABELS_AND_QUOTES_NOT_INDEPENDENT_FACT_FINDING',
                         'legal_or_medical_finding': False})
    autopsy = {'AUTOPSY_RECORD_PRESENT', 'AUTOPSY_EXCLUDED_FOR_NO_CLINICAL_RECORD'}
    circular = {'ESSENTIAL_RECORD_NOT_PRODUCED', 'INDEPENDENT_REVIEW_REFUSED',
                'GAP_RELIED_ON_AGAINST_CLAIMANT'}
    pattern = circular | {'INSTITUTIONAL_BENEFIT_RETAINED'}
    if autopsy <= kinds:
        add('AUTOPSY_EVIDENCE_EXCLUSION_WARNING', '부검자료 배제·진료기록 편중 검증 경고', autopsy)
    if circular <= kinds:
        add('CIRCULAR_BURDEN_SHIFT_WARNING', '검증 차단 뒤 입증 부족 전가 경고', circular)
    if pattern <= kinds and review.get('decision_body') and review.get('controller'):
        add('HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING',
            '피해 암장·사법 카르텔 구조 의심 경고 — 개별 행위·연결관계 독립 조사 필요', pattern)
    if 'CAUSATION_REASONING_UNEXPLAINED' in kinds:
        add('CAUSATION_METHOD_CONSISTENCY_REVIEW', '인과성 판단 방법·근거의 일관성 검토', {'CAUSATION_REASONING_UNEXPLAINED'})
    if 'SUSCEPTIBILITY_NOT_ASSESSED' in kinds:
        add('INDIVIDUAL_SUSCEPTIBILITY_REVIEW_OPEN', '생전 증상·개별 감수성의 최초 전문 검토 요구', {'SUSCEPTIBILITY_NOT_ASSESSED'})
    controller = review.get('controller')
    requirements = []
    if warnings:
        requirements = [
            '원자료 생성·보유·검색·이관·폐기 이력과 적용 당시 규정의 항목별 설명',
            '부검 소견·생전 증상·개별 감수성과 기존 판단 근거의 독립 전문 검토',
            '증거신청 배제 이유, 가능한 대체 검증 경로와 검증 손실의 설명',
            '자료 미제공·검증 차단의 공백을 원고 불이익으로 사용하는 주장에 대한 시정',
        ]
    benefit_review = 'INSTITUTIONAL_BENEFIT_RETAINED' in kinds and bool(warnings)
    return {
        'id': review['id'], 'case_id': review.get('case_id'),
        'track_id': review.get('track_id', review.get('procedure_id')),
        'scope_review': scope, 'input_record': copy.deepcopy(review),
        'status': 'SCOPE_REVIEW_REQUIRED' if scope['status'] != 'IN_SCOPE' else
                  'WARNING_REVIEW_OPEN' if warnings else 'SOURCE_OR_METHOD_REVIEW_OPEN',
        'observations': accepted + pending, 'warnings': warnings,
        'controller': controller, 'decision_body': review.get('decision_body'),
        'controller_identification_pending': not bool(controller),
        'institutional_response_requirements': requirements,
        'recognized_relief_preserved': 'RECOGNIZED_RELIEF_EXISTS' in kinds,
        'recognized_relief_reassessment_requested': False,
        'clinical_record_absence_reduces_victim_credibility': False,
        'autopsy_is_automatically_causation_proof': False,
        'claimant_restatement_required': False,
        'victim_concession_required': False,
        'institutional_concession_candidates': [
            '미제공 자료의 공백을 원고의 입증 실패·권리 포기로 전환하는 주장 철회·시정 요구',
            '원자료 통제로 유지된 절차상 이익의 시정과 독립 검증 기회 회복 요구',
        ] if warnings else [],
        'benefit_reversal_review': {
            'status': 'COUNSEL_REVIEW_REQUIRED' if benefit_review else 'NO_SOURCE_LINKED_BENEFIT_TRIGGER',
            'beneficiary_input': controller, 'amount': None,
            'basis_observations': [o['input_record']['id'] for o in accepted if o['input_record']['kind'] == 'INSTITUTIONAL_BENEFIT_RETAINED'],
            'source_refs': sorted({o['input_record']['source_ref'] for o in accepted if o['input_record']['kind'] == 'INSTITUTIONAL_BENEFIT_RETAINED'}),
            'request': '입증상 이익·지연 이익과 유족의 추가 비용을 추적하고 불리추정·입증부담 조정·비용 구제·반환 등 적용 가능한 수단을 대리인이 검토',
            'unjust_enrichment_legally_established': False,
            'repayment_or_confiscation_executed': False,
        },
        'coordination_or_criminal_cartel_established': False,
        'automatic_r26_transition': False, 'automatic_state_change': False,
        'sanction_decided': False, 'external_action_performed': False,
        'human_interpretation_required': True, 'total_score': None,
        'source_semantics_and_applicability_review_pending': True,
        'review_work_assigned_to': 'AI_AND_QUALIFIED_REVIEW_NODES_NOT_BEREAVED_REPETITION',
    }


def support_reviews(project):
    validate_support_reviews(project)
    return [review_access(project, r) for r in project.get('support_reviews', [])]


def render_support_request(review):
    if not review['warnings']:
        return ''
    refs = sorted({s for w in review['warnings'] for s in w['source_refs']})
    return '\n'.join([
        '원고의 검증권·구제 요청 [' + review['id'] + ']',
        '부검자료와 생전 증상에 대한 개별 평가, 자료 통제자의 항목별 설명 및 독립 전문 검토를 요청한다.',
        '진료기록 미확보나 기관이 제공하지 않은 원자료의 공백을 원고의 진술 부족·입증 실패로 전환해서는 안 된다.',
        '자료 미제공으로 유지된 절차상 이익을 시정하고, 검증 기회와 관련 구제 수단을 확보해 달라.',
        '연결 근거: ' + ', '.join(refs),
    ])
