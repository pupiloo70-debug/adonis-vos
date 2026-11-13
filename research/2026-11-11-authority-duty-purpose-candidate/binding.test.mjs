import test from 'node:test';
import assert from 'node:assert/strict';
const {evaluatePurpose}=await import('./'+(process.env.MODULE || 'purpose-review.mjs'));
const receipt={ref:'SYN-OUTCOME',kind:'VICTIM_OUTCOME',source_type:'PAYMENT_RECEIPT',delivery_status:'REALIZED',effect_kind:'PAYMENT_RECEIVED',beneficiary_id:'V1',case_id:'SYN-A',question_id:'Q1',outcome_id:'O1'};
const scenarios=[
 ['provider funding alone',null,false],
 ['different case',{...receipt,case_id:'SYN-B'},false],
 ['different question',{...receipt,question_id:'Q2'},false],
 ['different outcome',{...receipt,outcome_id:'O2'},false],
 ['correct binding',receipt,true],
];
for(const [name,outcome_evidence,ok] of scenarios)test(name,()=>{
 const input={synthetic:true,case_id:'SYN-A',actor_id:'CTRL',question_id:'Q1',now:'2026-11-13T00:00:00Z',support_benefits:{records:[{outcome_id:'O1',effect_kind:'PAYMENT_RECEIVED',beneficiary_id:'V1',outcome_evidence,provider_received_benefit:true,provider_benefit_status:'SOURCE_LINKED',victim_realized:true,victim_realized_status:'INDEPENDENTLY_VERIFIED',source_refs:['SYN-PROVIDER-FUNDING',...(outcome_evidence?[outcome_evidence.ref]:[])]}]}};
 const o=evaluatePurpose(input),r=o.benefit_return.entries[0];
 console.log(JSON.stringify({name,input:input.support_benefits.records[0],status:r.status,review:o.review_tasks}));
 assert.equal(r.status,ok?'MATERIAL_OUTCOME_EVIDENCE_LINKED_REVIEW_PENDING':'BENEFIT_RETURN_REVIEW_OPEN');
 assert.equal(o.total_score,null);assert.equal(o.source_truth_authenticated,false);assert.equal(o.release_approved,false);
});
