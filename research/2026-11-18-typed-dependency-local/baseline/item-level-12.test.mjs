// 2026-11-17 all cases SYNTHETIC_ONLY; tests new isolated wrapper not in historical code.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as mod from './testimony-controller.mjs';
const fixture=()=>JSON.parse(readFileSync(new URL('./synthetic-fixture.json',import.meta.url),'utf8'));
function evaluate(f){assert.equal(typeof mod.reviewContextIsolated,'function','ITEM_LEVEL_ISOLATION_UNIMPLEMENTED');const p=fixture();f?.(p);return mod.reviewContextIsolated(p)};
const held=(r,id)=>r.isolation_report.held.some(x=>x.id===id);

test('NEW01 P02: foreign-case statement isolated, independent testimony preserved',()=>{
 const r=evaluate(p=>{p.statements[1].case_id='SYN-CASE-OTHER'});
 assert.equal(r.testimony.length,1); assert.ok(held(r,'S2'));assert.equal(r.documentary_gaps.length,1);
});
test('NEW02 P01/P02: invalid speaker basis held, documentary task still proceeds',()=>{
 const r=evaluate(p=>p.statements[1].basis='AUTHORITY_PROVES_FACT');
 assert.ok(held(r,'S2'));assert.equal(r.testimony.length,1);assert.equal(r.documentary_gaps[0].controller_explanation,'REQUEST_REVIEW');
});
test('NEW03 G: invalid record claim held, valid alternate record independently retained',()=>{
 const r=evaluate(p=>{p.records.push({...p.records[0],id:'REC-VALID',state:'NOT_PROVIDED'});p.records[0].state='ABSENCE_PROVES_FALSE'});
 assert.ok(held(r,'REC1'));assert.equal(r.documentary_gaps.length,1);assert.equal(r.documentary_gaps[0].victim_proof_failure,'NOT_INFERRED');
});
test('NEW04 P04: out-of-scope record held without erasing valid record',()=>{
 const r=evaluate(p=>{p.records[0].case_id='SYN-CASE-B';p.records.push({...p.records[0],id:'REC2',case_id:'SYN-CASE-A'})});
 assert.ok(held(r,'REC1'));assert.equal(r.documentary_gaps.length,1);
});
test('NEW05 P04: foreign remedy cannot claim source access completed',()=>{
 const r=evaluate(p=>p.remedies[0].case_id='SYN-CASE-B');
 assert.ok(held(r,'R1'));assert.equal(r.substantive_remedy.overall,'UNRESOLVED');
});
test('NEW06 P02: all duplicate statement IDs held; distinct statement survives',()=>{
 const r=evaluate(p=>{p.statements[1].id=p.statements[0].id;p.statements.push({...p.statements[0],id:'S3',claim_key:'CLAIM-3'})});
 assert.equal(r.isolation_report.held.filter(x=>x.id==='S1').length,2);assert.equal(r.testimony.length,1);
});
test('NEW07 P02: all duplicate record IDs held while independent record retained',()=>{
 const r=evaluate(p=>{p.records.push({...p.records[0]});p.records.push({...p.records[0],id:'REC3'})});
 assert.equal(r.isolation_report.held.filter(x=>x.id==='REC1').length,2);assert.equal(r.documentary_gaps.length,1);
});
test('NEW08 P02: held parent taints dependent, unrelated sibling survives',()=>{
 const r=evaluate(p=>{p.statements[1].case_id='SYN-OTHER';p.statements.push({...p.statements[0],id:'S3',claim_key:'K3',depends_on:['S2']});p.statements.push({...p.statements[0],id:'S4',claim_key:'K4'})});
 assert.ok(held(r,'S2'));assert.ok(held(r,'S3'));assert.equal(r.testimony.length,2);
});
test('NEW09 P02: cycle and its dependents held; valid sibling unaffected',()=>{
 const r=evaluate(p=>{p.statements.push({...p.statements[0],id:'S3',claim_key:'K3',depends_on:['S4']});p.statements.push({...p.statements[0],id:'S4',claim_key:'K4',depends_on:['S3']});p.statements.push({...p.statements[0],id:'S5',claim_key:'K5',depends_on:['S3']})});
 assert.ok(held(r,'S3'));assert.ok(held(r,'S4'));assert.ok(held(r,'S5'));assert.equal(r.testimony.length,1);
});
test('NEW10 P03: self-declared verified remedies cannot imply independently authenticated proof',()=>{
 const r=evaluate(p=>p.remedies=['monetary','source_access','independent_review','explanation','correction'].map((type,i)=>({id:'R'+i,type,status:'INDEPENDENTLY_VERIFIED',source_refs:['UNAUTHENTICATED-STRING-'+i]})));
 assert.equal(r.substantive_remedy.overall,'UNRESOLVED');assert.ok(Object.values(r.substantive_remedy.components_verified).every(x=>x===false));
 assert.equal(r.isolation_report.source_truth_authenticated,false);
});
test('NEW11 PRIVACY: raw statement quarantined without echoing raw text',()=>{
 const r=evaluate(p=>p.statements[1].raw_text='SYNTHETIC_PRIVATE_SENTINEL_DO_NOT_COPY');
 assert.ok(held(r,'S2'));assert.ok(!JSON.stringify(r).includes('SYNTHETIC_PRIVATE_SENTINEL_DO_NOT_COPY'));
});
test('NEW12 GOVERNANCE: valid work kept and no autonomous guilt, immunity, release or numerical score',()=>{
 const r=evaluate(p=>{p.statements[1].basis='BROKEN';p.records[0].state='REPORTED_DESTROYED'});
 assert.equal(r.documentary_gaps[0].controller_explanation,'REQUEST_REVIEW');
 assert.equal(r.total_score,null);assert.equal(r.decision_boundaries.auto_guilt,false);assert.equal(r.decision_boundaries.auto_immunity,false);
 assert.equal(r.decision_boundaries.release,'NOT_APPROVED');assert.equal(r.decision_boundaries.dispatch,'NOT_SENT');
});

test('NEW13 malformed collection rejected with named error',()=>{const p=fixture();p.records={not:'array'};assert.throws(()=>{if(typeof mod.reviewContextIsolated!=='function')throw Error('ITEM_LEVEL_ISOLATION_UNIMPLEMENTED');mod.reviewContextIsolated(p)},/INVALID_RECORDS/);});
