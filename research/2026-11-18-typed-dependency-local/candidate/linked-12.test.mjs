// 2026-11-18: PUBLIC SYNTHETIC INPUT ONLY, cross-collection P02/P03 dependency boundary.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as mod from './testimony-controller.mjs';
const create=()=>JSON.parse(readFileSync(new URL('./synthetic-fixture.json',import.meta.url),'utf8'));
function run(change){if(typeof mod.reviewContextLinked!=='function')throw Error('LINKED_SCOPE_REVIEW_UNIMPLEMENTED');const x=create();change?.(x);return mod.reviewContextLinked(x)}
const inHeld=(r,collection,id)=>r.isolation_report.held.some(x=>x.collection===collection&&x.id===id);
const item=(id)=>({id,claim_key:id,summary:'합성 공개 원자료 미확보',speaker_role:'SYNTHETIC_OBSERVER',basis:'DIRECT',event_time:'2026-01-01',report_time:'2026-01-02'});
const record=(id)=>({id,controller:'SYNTHETIC_ARCHIVE',item:'SYNTHETIC_RECORD',state:'NOT_PROVIDED',evidence_status:'DOCUMENT_LINKED',source_refs:['SYN-REF']});
const remedy=(id)=>({id,type:'independent_review',status:'INDEPENDENTLY_VERIFIED',source_refs:['SELF-ASSERTED-REF']});

test('LINK01 P02 held record blocks dependent testimony but preserves unrelated S1',()=>{
 const r=run(x=>{x.records[0].case_id='SYN-OTHER';x.statements[1].depends_on_items=[{collection:'records',id:'REC1'}]});
 assert.ok(inHeld(r,'records','REC1'));assert.ok(inHeld(r,'statements','S2'));
 assert.equal(r.testimony[0].occurrences,1);assert.equal(r.substantive_remedy.overall,'UNRESOLVED');
});
test('LINK02 P02 a held statement blocks dependent record, not sibling record',()=>{
 const r=run(x=>{x.statements[1].case_id='SYN-OTHER';x.records[0].depends_on_items=[{collection:'statements',id:'S2'}];x.records.push(record('REC2'))});
 assert.ok(inHeld(r,'records','REC1'));assert.deepEqual(r.documentary_gaps.map(x=>x.record_id),['REC2']);
});
test('LINK03 P02 transitive typed dependencies quarantine downstream remedy',()=>{
 const r=run(x=>{x.statements[1].basis='INVALID';x.records[0].depends_on_items=[{collection:'statements',id:'S2'}];x.remedies.push({...remedy('R2'),depends_on_items:[{collection:'records',id:'REC1'}]})});
 assert.ok(inHeld(r,'records','REC1'));assert.ok(inHeld(r,'remedies','R2'));
});
test('LINK04 P02 cross-category dependency cycle quarantined without full abort',()=>{
 const r=run(x=>{x.records[0].depends_on_items=[{collection:'statements',id:'S2'}];x.statements[1].depends_on_items=[{collection:'records',id:'REC1'}]});
 assert.ok(inHeld(r,'records','REC1'));assert.ok(inHeld(r,'statements','S2'));assert.equal(r.testimony[0].occurrences,1);
});
test('LINK05 P02 unrelated valid statements remain even when all records depend on invalid source',()=>{
 const r=run(x=>{x.statements[1].basis='BAD';x.records[0].depends_on_items=[{collection:'statements',id:'S2'}]});
 assert.equal(r.testimony.length,1);assert.equal(r.documentary_gaps.length,0);
 assert.equal(r.isolation_report.independent_valid_work_preserved,true);
});
test('LINK06 P03 a bare string source reference is never independent evidence authentication',()=>{
 const r=run(x=>{x.statements[0].source_refs=['SYN-UNAUTHENTICATED'];x.records[0].state='REPORTED_MISSING'});
 assert.equal(r.isolation_report.source_truth_authenticated,false);assert.equal(r.documentary_gaps[0].victim_proof_failure,'NOT_INFERRED');
});
test('LINK07 P04 scope mismatch for record blocks linked remedy only, not original statement',()=>{
 const r=run(x=>{x.records[0].subject_id='SYN-FOREIGN-SUBJECT';x.remedies[0].depends_on_items=[{collection:'records',id:'REC1'}]});
 assert.ok(inHeld(r,'records','REC1'));assert.ok(inHeld(r,'remedies','R1'));assert.equal(r.testimony.length,1);
});
test('LINK08 P05 an accepted independent_review label still does not close the case',()=>{
 const r=run(x=>{x.remedies.push({...remedy('R2'),depends_on_items:[{collection:'records',id:'REC1'}]})});
 assert.equal(r.substantive_remedy.overall,'UNRESOLVED');assert.equal(r.isolation_report.source_truth_authenticated,false);
});
test('LINK09 G-pattern data absence must not imply victim proof failure',()=>{
 const r=run(x=>{x.records[0].state='REPORTED_DESTROYED';x.records[0].evidence_status='CLAIM_ONLY';x.records[0].source_refs=[]});
 assert.equal(r.documentary_gaps[0].victim_proof_failure,'NOT_INFERRED');assert.equal(r.documentary_gaps[0].guilt,'NOT_ADJUDICATED');
});
test('LINK10 G-pattern multiple AI source IDs do not prove source authenticity',()=>{
 const r=run(x=>{x.records[0].source_refs=['MODEL-A','MODEL-B','MODEL-C'];x.records[0].evidence_status='DOCUMENT_LINKED'});
 assert.equal(r.isolation_report.source_truth_authenticated,false);assert.equal(r.total_score,null);
});
test('LINK11 governance boundary preserved under cross-scope partial failure',()=>{
 const r=run(x=>{x.statements[1].depends_on_items=[{collection:'records',id:'NOT_THERE'}]});
 assert.ok(inHeld(r,'statements','S2'));assert.equal(r.decision_boundaries.auto_adverse_inference,false);
 assert.equal(r.decision_boundaries.auto_guilt,false);assert.equal(r.decision_boundaries.dispatch,'NOT_SENT');assert.equal(r.decision_boundaries.release,'NOT_APPROVED');
});
test('LINK12 malformed typed links quarantine one item only; no global approval',()=>{
 const r=run(x=>{x.statements[1].depends_on_items=[{collection:'agents',id:'X'}]});
 assert.ok(inHeld(r,'statements','S2'));assert.equal(r.testimony[0].occurrences,1);assert.equal(r.total_score,null);
});
