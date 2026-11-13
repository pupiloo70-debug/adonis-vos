import test from 'node:test';
import assert from 'node:assert/strict';
const {evaluatePurpose}=await import('./'+(process.env.MODULE || 'purpose-review.mjs'));
const lot='SYN-LOT-001';
const base={synthetic:true,case_id:'SYN-A',actor_id:'CTRL',question_id:'Q1',now:'2026-11-13T00:00:00Z'};
const period={lot_id:lot,period_start:'2018-01-01',period_end:'2019-01-31'};
const release={record_type:'LOT_RELEASE_RECORD',case_id:'SYN-A',lot_id:lot,event_date:'2018-09-04',source_ref:'SYN-COPY',contemporaneous_origin_ref:'SYN-ORIGINAL'};
const run=(records=[],later_improvements=[])=>evaluatePurpose({...base,historical_lot_review:{...period,records,later_improvements}});
const gap='HISTORICAL_SOURCE_GAP_OPEN';
for(const type of ['LATER_TEST_METHOD','LATER_STANDARD','CURRENT_SAFETY_REPORT','ADMINISTRATIVE_REFORM']) test(type+' cannot close earlier lot review',()=>{
 const z=run([],[{type,source_ref:'SYN-NEW',claimed_status:'SAFE'}]),h=z.historical_lot_review;
 assert.equal(h.later_improvements.length,1);
 assert.ok(Object.values(h.historical_checks).every(x=>x.status===gap));
 assert.equal(h.historical_verification_closed,false);
 assert.equal(h.present_safety_certified,false);
 assert.equal(h.historic_misconduct_determined,false);
 assert.equal(h.causation_determined,false);
 assert.equal(z.total_score,null);
});
for(const mutation of [{lot_id:'SYN-OTHER'},{case_id:'SYN-B'},{event_date:'2025-01-01'},{contemporaneous_origin_ref:''},{event_date:'2018-02-31'},{record_type:'CURRENT_SAFETY_REPORT'}]) test('mismatched or untraceable record '+JSON.stringify(mutation),()=>{
 assert.equal(run([{...release,...mutation}]).historical_lot_review.historical_checks.RELEASE.status,gap);
});
test('later copy with historical origin can inform release only',()=>{
 const z=run([{...release,copy_date:'2025-01-01'}]),h=z.historical_lot_review;
 assert.equal(h.historical_checks.RELEASE.status,'HISTORICAL_SOURCE_LINKED_REVIEW_PENDING');
 assert.equal(h.historical_checks.APPROVAL.status,gap);
 assert.equal(h.historical_checks.DISTRIBUTION.status,gap);
 assert.equal(h.historical_verification_closed,false);
 assert.ok(z.review_tasks.includes('REVIEW_CONTEMPORANEOUS_LOT_APPROVAL_RELEASE_AND_DISTRIBUTION'));
});
