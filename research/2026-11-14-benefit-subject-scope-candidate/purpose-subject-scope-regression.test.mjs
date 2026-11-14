// Synthetic-only P04/P02 negative and positive fixtures for current public purpose-review.
import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluatePurpose } from './purpose-review.mjs';
const base = () => ({
  synthetic:true, case_id:'SYN-CASE-A', actor_id:'SYN-CONTROLLER',
  subject_id:'SYN-PERSON-A', question_id:'SYN-QUESTION-1',
  now:'2026-11-14T00:00:00Z', events:[],
  rights_review:{claimant:{access_status:'UNAVAILABLE'},
    controller:{control_status:'SOURCE_LINKED',source_ref:'SYN-CONTROLLER-REF'},
    material_question_open:true, existing_source_refs:['SYN-EXISTING-SOURCE']}
});
const record = (id, subject) => ({
  effect_kind:'PAYMENT_RECEIVED',subject_id:subject, beneficiary_id:subject, outcome_id:id,
  source_refs:['SYN-RECEIPT-'+id],victim_realized:true,
  victim_realized_status:'INDEPENDENTLY_VERIFIED',
  provider_received_benefit:true,provider_benefit_status:'SOURCE_LINKED',
  outcome_evidence:{kind:'VICTIM_OUTCOME',source_type:'PAYMENT_RECEIPT',
    delivery_status:'REALIZED',effect_kind:'PAYMENT_RECEIVED',subject_id:subject,
    beneficiary_id:subject,case_id:'SYN-CASE-A',question_id:'SYN-QUESTION-1',
    outcome_id:id,ref:'SYN-RECEIPT-'+id}
});
const run=(...rows)=>evaluatePurpose({...base(),support_benefits:{records:rows}});
const linked='MATERIAL_OUTCOME_EVIDENCE_LINKED_REVIEW_PENDING';
const held='BENEFIT_SUBJECT_SCOPE_REVIEW_OPEN';
test('P04: another person receipt cannot be assigned to the current person',()=>{
  const o=run(record('B','SYN-PERSON-B'));
  assert.equal(o.benefit_return.entries[0].status,held);
  assert.equal(o.benefit_return.entries[0].outcome_binding_checked,false);
  assert.equal(o.benefit_return.entries[0].realized_benefit_confirmed,false);
});
test('P02: keep correct sibling while holding only the other-person benefit',()=>{
  const o=run(record('A','SYN-PERSON-A'),record('B','SYN-PERSON-B'));
  assert.deepEqual(o.benefit_return.entries.map(x=>x.status),[linked,held]);
  assert.ok(o.review_tasks.includes('REQUEST_CONTROLLER_SEARCH_PRESERVATION_EXPLANATION_AND_ALTERNATE_ACCESS'));
  assert.ok(o.review_tasks.includes('REVIEW_BENEFIT_SUBJECT_LINK_WITHOUT_REASSIGNMENT'));
});
test('P04: absent person scope is unverified rather than borrowed',()=>{
  const a=record('A','SYN-PERSON-A');delete a.subject_id;delete a.outcome_evidence.subject_id;
  const o=run(a);assert.equal(o.benefit_return.entries[0].status,held);
});
test('P04: explicitly same-person linked outcome remains pending, never certified',()=>{
  const o=run(record('A','SYN-PERSON-A'));
  assert.equal(o.benefit_return.entries[0].status,linked);
  assert.equal(o.benefit_return.entries[0].subject_scope_binding,'SUBJECT_BOUND_TO_INPUT');
  assert.equal(o.benefit_return.entries[0].realized_benefit_confirmed,false);
  assert.equal(o.source_truth_authenticated,false);
});
test('scope unspecified legacy input does not automatically authenticate the outcome',()=>{
  const x=base();delete x.subject_id;
  const o=evaluatePurpose({...x,support_benefits:{records:[record('A','SYN-PERSON-A')]}});
  assert.equal(o.benefit_return.entries[0].subject_scope_binding,'SUBJECT_SCOPE_NOT_SUPPLIED');
  assert.equal(o.benefit_return.entries[0].realized_benefit_confirmed,false);
  assert.equal(o.total_score,null);
  assert.equal(o.release_approved,false);
  assert.equal(o.production_deployed,false);
});
