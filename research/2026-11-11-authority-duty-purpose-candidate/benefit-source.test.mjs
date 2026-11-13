import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluatePurpose} from './purpose-review.mjs';
const run = source_refs => evaluatePurpose({synthetic:true,case_id:'SYN',actor_id:'CTRL',question_id:'Q',now:'2026-11-12T00:00:00Z',support_benefits:{records:[{effect_kind:"PAYMENT_RECEIVED",beneficiary_id:"V1",outcome_id:"O1",outcome_evidence:{source_type:"PAYMENT_RECEIPT",delivery_status:"REALIZED",effect_kind:"PAYMENT_RECEIVED",beneficiary_id:"V1",ref:"SYN-RECEIPT",kind:"VICTIM_OUTCOME",case_id:"SYN",question_id:"Q",outcome_id:"O1"},victim_realized:true,victim_realized_status:'INDEPENDENTLY_VERIFIED',provider_received_benefit:true,provider_benefit_status:'SOURCE_LINKED',source_refs}]}});
for(const refs of [undefined,[],[' ']]) test('missing source '+JSON.stringify(refs),()=>{
 const o=run(refs); const r=o.benefit_return.entries[0];
 console.log(JSON.stringify({refs,r,tasks:o.review_tasks,score:o.total_score}));
 assert.equal(r.status,'BENEFIT_RETURN_REVIEW_OPEN');assert.equal(r.victim_realized,'UNVERIFIED');
 assert.equal(o.total_score,null);assert.equal(o.release_approved,false);
});
test('linked synthetic control stays pending review',()=>assert.equal(run(['SYN-RECEIPT']).benefit_return.entries[0].status,'MATERIAL_OUTCOME_EVIDENCE_LINKED_REVIEW_PENDING'));
