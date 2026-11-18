import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {reviewContextIsolated} from './testimony-controller.mjs';
const fixture=()=>JSON.parse(readFileSync(new URL('./synthetic-fixture.json',import.meta.url),'utf8'));

test('CC-04: dissent retains its own text, sources and review IDs',()=>{
 const p=fixture();
 Object.assign(p.statements[0],{summary:'Present',source_refs:['SYN-A'],review_id:'REV-A',review_version:'v1'});
 Object.assign(p.statements[1],{summary:'Not present',source_refs:['SYN-B'],review_id:'REV-B',review_version:'v2'});
 const r=reviewContextIsolated(p), t=r.testimony[0];
 assert.equal(t.requires_human_merge_review,true);
 assert.deepEqual(t.attribution_variants.map(x=>[x.summary,x.source_refs,x.review_id,x.review_version]),[['Present',['SYN-A'],'REV-A','v1'],['Not present',['SYN-B'],'REV-B','v2']]);
 assert.deepEqual(r.duplicates,[]);
 assert.equal(t.truth_status,'NOT_ADJUDICATED');
});
test('CC-04: same text from different reviews is not a repeat; repeated evidence still counts once',()=>{
 const p=fixture();
 Object.assign(p.statements[0],{source_refs:['SYN-A'],review_id:'REV-A',review_version:'v1'});
 Object.assign(p.statements[1],{source_refs:['SYN-B'],review_id:'REV-B',review_version:'v1'});
 p.statements.push({...p.statements[1],id:'S3'});
 const r=reviewContextIsolated(p);
 assert.deepEqual(r.duplicates,[{statement_id:'S3',canonical_statement_id:'S2',not_new_evidence:true}]);
 assert.equal(r.testimony[0].truth_status,'NOT_ADJUDICATED');
 assert.equal(r.total_score,null);
});
test('an evidence-controller document cannot self-certify independent verification',()=>{
 const p=fixture();p.records[0].evidence_status='INDEPENDENTLY_CHECKED';
 const r=reviewContextIsolated(p), rec=r.documentary_gaps[0];
 assert.equal(rec.reported_verification_status,'INDEPENDENTLY_CHECKED');
 assert.equal(rec.verification_status,'DOCUMENT_LINKED');
 assert.equal(rec.controller_explanation,'REQUEST_REVIEW');
 assert.equal(rec.victim_proof_failure,'NOT_INFERRED');
 assert.equal(r.isolation_report.source_truth_authenticated,false);
 assert.equal(r.decision_boundaries.release,'NOT_APPROVED');
});
test('invalid optional review metadata is isolated without losing a valid statement',()=>{
 const p=fixture();p.statements[1].review_id={invalid:true};
 const r=reviewContextIsolated(p);
 assert.deepEqual(r.testimony[0].statement_ids,['S1']);
 assert.ok(r.isolation_report.held.some(x=>x.id==='S2'));
});
