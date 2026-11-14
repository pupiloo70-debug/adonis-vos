import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluateVirtual} from './a-r3-virtual.mjs';

const initial = Object.freeze({
  synthetic: true, case_id: 'SYN-LEARN-01', actor_id: 'SYN-CONTROLLER',
  question_id: 'SYN-Q1', formal_procedure_status: 'CLOSED',
  unresolved_questions: ['SYN-GAP'],
  controller_only_source: true, claimant_has_access: false,
  denial_depends_on_same_missing_evidence: true,
  independent_review_available: false
});
const common = r => {
  assert.equal(r.formal_procedure_status, 'CLOSED');
  assert.equal(r.technical_certification, 'HELD');
  assert.deepEqual(r.unresolved_questions, ['SYN-GAP']);
  for (const key of ['claimant_repeat_proof_required','legal_omission_finding','criminal_guilt_finding','medical_causation_finding','automatic_sanction','default_path_connected','production_released']) {
    assert.equal(r[key], false, key);
  }
  assert.equal(r.total_score, null);
};

test('bridge failure must not erase pending controller and circularity reviews', () => {
  const r = evaluateVirtual({...initial, bridge_status: 'FAILED'});
  common(r);
  assert.equal(r.status, 'GATE_EXECUTION_UNVERIFIED');
  assert.deepEqual(r.review_flags, [
    'GATE_EXECUTION_UNVERIFIED', 'CONTROLLER_EXPLANATION_REVIEW',
    'CIRCULAR_JUSTIFICATION_REVIEW'
  ]);
});

test('without bridge failure, controller and circularity flags both remain', () => {
  const r = evaluateVirtual(initial);
  common(r);
  assert.equal(r.status, 'CONTROLLER_EXPLANATION_REVIEW');
  assert.deepEqual(r.review_flags, [
    'CONTROLLER_EXPLANATION_REVIEW', 'CIRCULAR_JUSTIFICATION_REVIEW'
  ]);
});

test('actual access and an independent review path prevent stale flags', () => {
  const r = evaluateVirtual({...initial, claimant_has_access: true, independent_review_available: true});
  common(r);
  assert.equal(r.status, 'EVIDENCE_REVIEW_OPEN');
  assert.deepEqual(r.review_flags, ['EVIDENCE_REVIEW_OPEN']);
});
