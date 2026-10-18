export const RULESET = '0.1.0-draft';
export const RULES = [
  ['V01', 'record_access',
    '원자료 접근 제약', '자료 보유자와 제한 사유를 확인하세요.'],
  ['V02', 'record_loss',
    '자료 소실 또는 폐기', '소실 경위와 사본 존재를 확인하세요.'],
  ['V03', 'procedure_delay',
    '절차 지연', '요청일과 답변일을 시간순으로 정리하세요.'],
  ['V04', 'criteria_change',
    '적용 기준 변경', '당시 기준과 적용 기준의 근거를 대조하세요.'],
  ['V05', 'reason_gap',
    '판단 근거의 공백', '결론을 뒷받침하는 원자료를 질문하세요.'],
  ['V06', 'access_inequality',
    '검증 기회의 비대칭', '양측의 자료 접근 차이를 정리하세요.'],
  ['V07', 'preservation_risk',
    '추가 자료 소실 위험', '자료 보유자와 보존 가능성을 먼저 확인하세요.']
];

export function evaluate(answers) {
  const values = ['YES', 'NO', 'UNKNOWN'];
  const bases = ['USER_REPORT', 'DOCUMENT_REFERENCED',
    'CONFLICTING', 'UNKNOWN'];
  if (!answers || typeof answers !== 'object' ||
      Array.isArray(answers)) throw new Error('INVALID_INPUT');
  const items = RULES.map(([id, field, title, action]) => {
    const a = answers[field] ??
      { value: 'UNKNOWN', basis: 'UNKNOWN', refs: [] };
    if (!a || !values.includes(a.value) ||
        !bases.includes(a.basis) || !Array.isArray(a.refs) ||
        a.refs.some(x => typeof x !== 'string')) {
      throw new Error('INVALID_ANSWER:' + field);
    }
    return {
      rule_id: id, input_field: field, title,
      input_value: a.value, basis: a.basis, refs: [...a.refs],
      status: a.value === 'YES' ? 'SIGNAL_REPORTED' :
        a.value === 'NO' ? 'NOT_REPORTED' : 'NEEDS_CHECK',
      priority: a.value === 'YES' && field === 'preservation_risk'
        ? 'PRESERVATION_FIRST' : 'STANDARD_REVIEW',
      next_step: a.value === 'YES' ? action :
        a.value === 'UNKNOWN' ? '모르는 항목과 확인 경로를 남기세요.' :
        '새 자료가 생기면 다시 점검할 수 있습니다.'
    };
  });
  return { ruleset_version: RULESET, mode: 'RULE_BASED',
    total_score: null, items };
}
