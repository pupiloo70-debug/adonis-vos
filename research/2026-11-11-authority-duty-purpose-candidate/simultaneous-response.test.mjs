import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluate } from './authority-duty.mjs';

const event = (id, type, at, more = {}) => ({
  id, type, at, case_id: 'SYN-TIME', actor_id: 'CONTROLLER-X',
  question_id: 'Q-ONE', source_ref: `SRC-${type}-${id}`, ...more
});
const request = event('REQ', 'REQUEST_RECEIVED', '2026-11-08T00:00:00Z');
const responseTime = '2026-11-09T06:00:00Z';
function base(events = []) {
  return {
    synthetic: true, case_id: 'SYN-TIME', actor_id: 'CONTROLLER-X',
    question_id: 'Q-ONE', now: '2026-11-10T00:00:00Z',
    authority: { status:'UNKNOWN' },
    duty: { basis_status:'UNKNOWN', deadline_status:'UNKNOWN' },
    events: [request, ...events],
    residual_questions: ['verification outcome contested'],
    past_burden: [{ type:'prior unresolved request', amount:null }]
  };
}
const pair = (verifiedID, refusalID) => [
  event(verifiedID, 'CORE_ACCESS_VERIFIED', responseTime, { source_ref:'SRC-ACCESS' }),
  event(refusalID, 'REFUSAL', responseTime, { source_ref:'SRC-REFUSAL' })
];

test('simultaneous conflicting source-linked responses are not silently resolved by event ID ordering', () => {
  const r = evaluate(base(pair('E2','E3')));
  assert.equal(r.duty_fulfillment_status, 'SIMULTANEOUS_RESPONSE_CONFLICT_REVIEW_OPEN');
  assert.equal(r.omission_review, 'NO_ADDITIONAL_OMISSION_CLASSIFICATION');
  assert(r.explanation_task);
  assert.equal(r.accepted_events.length, 3);
  assert.equal(r.held_events.length, 0);
});
test('renaming event IDs must not change the fulfillment result for the same evidence types, times and sources', () => {
  const first = evaluate(base(pair('E2','E3')));
  const second = evaluate(base(pair('E3','E2')));
  assert.equal(first.duty_fulfillment_status, second.duty_fulfillment_status);
  assert.equal(second.duty_fulfillment_status, 'SIMULTANEOUS_RESPONSE_CONFLICT_REVIEW_OPEN');
});
test('single unambiguous verified response still closes only this question status', () => {
  const r = evaluate(base([event('V1', 'CORE_ACCESS_VERIFIED',responseTime)]));
  assert.equal(r.duty_fulfillment_status,'VERIFIED_FOR_THIS_QUESTION');
  assert.equal(r.source_truth_verified,false);
  assert.equal(r.past_burden.length,1);
  assert.equal(r.residual_questions.length,1);
});
test('independent same-kind responses at a common timestamp are not mistaken for contradictory types', () => {
  const r = evaluate(base([
    event('F1','FORMAL_REPLY',responseTime),
    event('F2','FORMAL_REPLY',responseTime)
  ]));
  assert.equal(r.duty_fulfillment_status,'FORMAL_REPLY_ONLY');
  assert.equal(r.accepted_events.length,3);
});
test('later dated unambiguous verification can update previously conflicted responses', () => {
  const r = evaluate(base([
    ...pair('E2','E3'),
    event('V4','ALTERNATIVE_VERIFIED','2026-11-09T08:00:00Z')
  ]));
  assert.equal(r.duty_fulfillment_status,'VERIFIED_FOR_THIS_QUESTION');
  assert.equal(r.accepted_events.length,4);
});
test('cross-case response is held and unrelated valid evidence continues', () => {
  const r = evaluate(base([
    event('F1','FORMAL_REPLY',responseTime),
    event('R2','REFUSAL',responseTime,{case_id:'OTHER-CASE'})
  ]));
  assert.equal(r.duty_fulfillment_status,'FORMAL_REPLY_ONLY');
  assert.equal(r.held_events.length,1);
});
test('conflicting response does not cause automatic guilt, enforcement or scoring', () => {
  const r = evaluate(base(pair('E2','E3')));
  assert.equal(r.total_score,null);
  assert.equal(r.legal_burden_shifted,false);
  assert.equal(r.external_action_performed,false);
  assert.equal(r.automatic_sanction,false);
  assert.equal(r.action_disposition,'SUPPORT_CONTINUES');
});
test('prohibited request is held locally while source-review support remains available', () => {
  const x = base(pair('E2','E3'));
  x.action = { kind:'EXTERNAL_ENFORCEMENT', fabricate_evidence:true };
  const r = evaluate(x);
  assert.equal(r.action_disposition,'REQUESTED_IMPROPER_ACTION_REJECTED_SUPPORT_CONTINUES');
  assert(r.allowed_support.includes('SOURCE_COMPARISON'));
});
