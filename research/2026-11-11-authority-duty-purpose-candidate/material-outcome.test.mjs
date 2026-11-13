import test from 'node:test';
import assert from 'node:assert/strict';
const {evaluatePurpose}=await import('./'+(process.env.MODULE || 'purpose-review.mjs'));
const base={synthetic:true,case_id:'SYN-A',actor_id:'CTRL',question_id:'Q1',now:'2026-11-13T00:00:00Z'};
const row={effect_kind:'PAYMENT_RECEIVED',beneficiary_id:'V1',outcome_id:'O1',source_refs:['SYN-REF'],victim_realized:true,victim_realized_status:'INDEPENDENTLY_VERIFIED',provider_received_benefit:true,provider_benefit_status:'SOURCE_LINKED',
 outcome_evidence:{kind:'VICTIM_OUTCOME',source_type:'PAYMENT_RECEIPT',delivery_status:'REALIZED',effect_kind:'PAYMENT_RECEIVED',beneficiary_id:'V1',outcome_id:'O1',case_id:'SYN-A',question_id:'Q1',ref:'SYN-REF'}};
const run=(...records)=>evaluatePurpose({...base,support_benefits:{records}});
const activityKinds=['POLICY_PROPOSAL_OR_ANNOUNCEMENT','SPEAKING_OPPORTUNITY','MEDIA_COVERAGE','PUBLIC_EVENT','STATEMENT_SHARING'];
for (const kind of activityKinds) test(kind+' is recorded separately even when tagged independently verified',()=>{
 const o=run({...row,effect_kind:kind,outcome_evidence:{...row.outcome_evidence,effect_kind:kind,source_type:kind}});
 assert.equal(o.benefit_return.entries[0].status,'ACTIVITY_ONLY_NOT_REALIZED_BENEFIT');
 assert.equal(o.benefit_return.entries[0].realized_benefit_confirmed,false);
 assert.equal(o.benefit_return.entries[0].victim_realized,'UNVERIFIED');
 assert.ok(o.review_tasks.includes('AUDIT_SUPPORT_BENEFIT_FLOW_CONFLICTS_AND_REALIZED_VICTIM_OUTCOMES'));
});
for (const [label,evidence] of [
 ['funding instead of receipt',{source_type:'PROVIDER_FUNDING_RECEIPT'}],
 ['press coverage disguised as payment',{source_type:'MEDIA_COVERAGE'}],
 ['promised payment',{delivery_status:'PROMISED'}],
 ['wrong beneficiary',{beneficiary_id:'V2'}],
 ['wrong case',{case_id:'SYN-B'}],
 ['wrong question',{question_id:'Q2'}],
 ['wrong outcome',{outcome_id:'O2'}],
 ['unlinked source',{ref:'SYN-OTHER'}]
]) test(label+' stays unverified',()=>{
 const o=run({...row,outcome_evidence:{...row.outcome_evidence,...evidence}});
 assert.equal(o.benefit_return.entries[0].victim_realized,'UNVERIFIED');
 assert.equal(o.benefit_return.entries[0].outcome_binding_checked,false);
});
test('legacy source without a corresponding outcome is preserved for review',()=>{
 const o=run({...row,outcome_evidence:undefined});const r=o.benefit_return.entries[0];
 assert.equal(r.victim_realized_input,'INDEPENDENTLY_VERIFIED');
 assert.deepEqual(r.evidence_refs,['SYN-REF']);
 assert.equal(r.status,'BENEFIT_RETURN_REVIEW_OPEN');
});
test('linked material result is pending verification; media does not count or erase it',()=>{
 const o=run(row,{...row,effect_kind:'MEDIA_COVERAGE'});
 assert.deepEqual(o.benefit_return.entries.map(x=>x.status),['MATERIAL_OUTCOME_EVIDENCE_LINKED_REVIEW_PENDING','ACTIVITY_ONLY_NOT_REALIZED_BENEFIT']);
 assert.equal(o.benefit_return.entries[0].victim_realized,'SOURCE_LINKED');
 assert.equal(o.benefit_return.entries[0].realized_benefit_confirmed,false);
 assert.ok(o.review_tasks.includes('CHECK_OUTCOME_SOURCE_ORIGINAL_AND_INDEPENDENT_REVIEW'));
 assert.equal(o.source_truth_authenticated,false);assert.equal(o.total_score,null);assert.equal(o.release_approved,false);
 assert.equal(o.external_action_performed,false);assert.equal(o.production_deployed,false);
});
for (const [effect_kind,source_type] of [
 ['RECORD_ACCESS_USED','RECORD_ACCESS_LOG'],
 ['INDEPENDENT_REVIEW_COMPLETED','COMPLETED_REVIEW_RECORD'],
 ['REMEDY_IMPLEMENTED','REMEDY_EXECUTION_RECORD']
]) test(effect_kind+' with matching evidence is linked but not certified',()=>{
 const o=run({...row,effect_kind,outcome_evidence:{...row.outcome_evidence,effect_kind,source_type}});
 assert.equal(o.benefit_return.entries[0].status,'MATERIAL_OUTCOME_EVIDENCE_LINKED_REVIEW_PENDING');
 assert.equal(o.benefit_return.entries[0].realized_benefit_confirmed,false);
});
