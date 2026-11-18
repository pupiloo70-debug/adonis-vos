// Additional synthetic adversarial cases. These tests are not the existing 16 tests.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {reviewContext} from './testimony-controller.mjs';
const base=()=>JSON.parse(readFileSync(new URL('./synthetic-fixture.json',import.meta.url),'utf8'));
const apply=f=>{const a=base();f(a);return reviewContext(a)};
test('RT01 P01: different speakers under same claim require merge review and preserved attribution',()=>{
 const r=apply(x=>x.statements[1].speaker_role='SYNTHETIC_AGENCY');
 assert.equal(r.testimony[0].requires_human_merge_review,true);
 assert.deepEqual(r.testimony[0].attribution_variants.map(v=>v.speaker_role),['SYNTHETIC_CLAIMANT','SYNTHETIC_AGENCY']);
});
test('RT02 P01: same claim changes DIRECT to HEARSAY; avoid silent evidence elevation',()=>{
 const r=apply(x=>x.statements[1].basis='HEARSAY');
 assert.equal(r.testimony[0].requires_human_merge_review,true);
 assert.deepEqual(r.testimony[0].attribution_variants.map(v=>v.basis),['DIRECT','HEARSAY']);
});
test('RT03 P01: conflicting event timestamps cannot silently merge',()=>{
 const r=apply(x=>x.statements[1].event_time='2026-02-01');
 assert.equal(r.testimony[0].requires_human_merge_review,true);
 assert.deepEqual(r.testimony[0].attribution_variants.map(v=>v.event_time),['2026-01-01','2026-02-01']);
});
test('RT04 testimony chronology: report_time alone may differ without increasing proof or flagging conflict',()=>{
 const r=reviewContext(base());
 assert.equal(r.testimony[0].requires_human_merge_review,false);
 assert.deepEqual(r.testimony[0].attribution_variants.map(v=>v.report_time),['2026-01-02','2026-01-03']);
 assert.equal(r.total_score,null);
});
test('RT05 P03 provenance: referenced synthetic statement source must not be silently dropped',()=>{
 const r=apply(x=>{x.statements[0].source_refs=['SYN-DOC-A'];x.statements[1].source_refs=['SYN-DOC-B'];});
 assert.deepEqual(r.testimony[0].attribution_variants.map(v=>v.source_refs),[['SYN-DOC-A'],['SYN-DOC-B']]);
 assert.equal(r.testimony.length,1);
});
test('RT06 P04: explicitly foreign-case statement is rejected instead of absorbed',()=>{
 assert.throws(()=>apply(x=>x.statements[1].case_id='SYN-CASE-B'),/STATEMENT_CASE_MISMATCH/);
});
test('RT07 G-review: institutional record-not-provided stays an explanation issue, not victim failure',()=>{
 const r=apply(x=>{x.records[0].state='NOT_PROVIDED';x.records[0].evidence_status='CLAIM_ONLY';x.records[0].source_refs=[];});
 const g=r.documentary_gaps[0];assert.equal(g.controller_explanation,'REQUEST_REVIEW');assert.equal(g.victim_proof_failure,'NOT_INFERRED');assert.equal(g.guilt,'NOT_ADJUDICATED');
});
test('RT08 G-review: self-reported lack is not automatically independently investigated',()=>{
 const r=apply(x=>{x.records[0].state='REPORTED_DESTROYED';x.records[0].evidence_status='CLAIM_ONLY';x.records[0].source_refs=[];});
 assert.equal(r.documentary_gaps[0].investigation_review,'NOT_AUTOMATIC');
});
test('RT09 A-R3: one verified payment is not proof of total substantive remedy',()=>{
 const r=reviewContext(base());assert.equal(r.substantive_remedy.overall,'UNRESOLVED');assert.equal(r.substantive_remedy.money_alone_never_closes,true);
});
test('RT10 governance: 5 verified components still require human review; no auto legal findings',()=>{
 const r=apply(x=>x.remedies=['monetary','source_access','independent_review','explanation','correction'].map((type,i)=>({id:'M'+i,type,status:'INDEPENDENTLY_VERIFIED',source_refs:['SYN-'+i]})));
 assert.equal(r.substantive_remedy.overall,'COMPONENTS_VERIFIED_REQUIRES_HUMAN_REVIEW');
 assert.deepEqual([r.decision_boundaries.auto_guilt,r.decision_boundaries.auto_immunity,r.decision_boundaries.auto_causality,r.decision_boundaries.auto_adverse_inference],[false,false,false,false]);
});
test('RT11 privacy: injected raw transcript cannot become training source',()=>{
 assert.throws(()=>apply(x=>x.statements[1].private_conversation='SYNTHETIC_NOT_A_REAL_CHAT'),/RAW_PRIVATE_TEXT_NOT_ACCEPTED/);
});
test('RT12 repetition: fifty duplicate phrasings do not inflate ethical-gravity numeric score',()=>{
 const r=apply(x=>x.statements=Array.from({length:50},(_,i)=>({...x.statements[0],id:'SYN-'+i,summary:i%2===0?'합성 원자료 미제공':'합성 자료 미확보'})));
 assert.equal(r.testimony.length,1);assert.equal(r.ethical_gravity.score,null);assert.equal(r.testimony[0].requires_human_merge_review,true);
});
