import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, writeFileSync, chmodSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { runIntegratedCore } from './core_guard.mjs';

const original = JSON.parse(readFileSync(new URL('./synthetic-input.json', import.meta.url), 'utf8'));
const input = () => structuredClone(original);
const codes = r => r.report.procedural_warnings.map(w => w.code);
const obs = x => x.project.support_reviews[0].observations;
const sha = v => createHash('sha256').update(v).digest('hex');
function fakePython(program, fn) {
  const path = process.env.PATH, dir = mkdtempSync(join(tmpdir(),'vos-integration-test-'));
  try {
    writeFileSync(join(dir,'python3'), '#!/bin/sh\n' + program + '\n');
    chmodSync(join(dir,'python3'), 0o700); process.env.PATH = dir;
    return fn();
  } finally { process.env.PATH = path; rmSync(dir,{recursive:true,force:true}); }
}

test('actual CentralCore and both Python stages execute with hashed receipts', () => {
  const x = input(), r = runIntegratedCore(x);
  assert.equal(r.status,'LOCAL_INTEGRATION_SUCCEEDED');
  assert.equal(r.legacy_snapshot.tasks[0].state,'SUCCEEDED');
  assert.equal(r.legacy_snapshot.dispatch_mode,'BUILTIN_LOCAL_ONLY');
  for (const stage of ['legacy','correction3','guard']) assert.equal(r.receipts[stage].status,'SUCCEEDED');
  assert.equal(r.receipts.guard.input_sha256,sha(JSON.stringify(x.project)));
  assert.equal(r.receipts.correction3.input_sha256,sha(JSON.stringify({project:x.project,now:x.now})));
  assert.equal(r.receipts.integration.report_sha256,sha(JSON.stringify(r.report)));
  assert.equal(codes(r).length,5); assert.equal(r.report.support_reviews[0].accepted_observations.length,9);
});
test('original 0.2 supply statuses and separate task receipt survive', () => {
  const r = runIntegratedCore(input());
  assert.deepEqual(r.report.legacy_rows.map(x=>x.provision_status),['PARTIAL_REPORTED','NOT_PROVIDED']);
  assert(r.report.legacy_rows.every(x=>x.resolution==='UNRESOLVED_REQUIRES_CONTENT_REVIEW'));
  assert.equal(r.no_legacy_status_overwrite,true);
});
test('frozen input remains unchanged and returned copies are isolated', () => {
  const x=input(), before=structuredClone(x);
  const freeze=v=>{if(v&&typeof v==='object'){Object.values(v).forEach(freeze);Object.freeze(v);}};freeze(x);
  const r=runIntegratedCore(x);assert.deepEqual(x,before);
  r.original_input.project.subject_id='CHANGED';r.report.support_reviews[0].original_review.id='CHANGED';
  assert.deepEqual(x,before);
});
test('both inputs must be explicitly synthetic', () => {
  for (const field of ['legacy_project','project']) for(const value of [false,'true',null]){
    const x=input();x[field].synthetic=value;assert.throws(()=>runIntegratedCore(x),/SYNTHETIC/);
  }
});
test('subject and case mapping cannot be inferred from another record',()=>{
  for(const field of ['case_id','track_id','subject_id']){
    const x=input();delete x.project[field];assert.throws(()=>runIntegratedCore(x),/PROJECT_SCOPE/);
    const y=input();y.mapping[field]='FOREIGN';assert.throws(()=>runIntegratedCore(y),/PROJECT_SCOPE/);
  }
});
test('complete one-to-one request routes and unchanged content are required',()=>{
  const x=input();x.mapping.request_routes=[];assert.throws(()=>runIntegratedCore(x),/INCOMPLETE/);
  const y=input();y.mapping.request_routes.push(y.mapping.request_routes[0]);assert.throws(()=>runIntegratedCore(y),/INVALID_REQUEST/);
  const z=input();z.project.routes[0].controller='OTHER';assert.throws(()=>runIntegratedCore(z),/CONTENT_MAPPING/);
});
test('duplicate route IDs cannot pass Map first/last-wins behavior',()=>{
  const x=input();x.project.routes.push(structuredClone(x.project.routes[0]));assert.throws(()=>runIntegratedCore(x),/AMBIGUOUS/);
});
test('orphan review mapping is rejected rather than silently ignored',()=>{
  const x=input();x.mapping.review_routes.push({review_id:'NONE',route_id:'R1',question_id:'Q'});
  assert.throws(()=>runIntegratedCore(x),/ORPHAN/);
});
test('missing review route mapping holds current warnings without changing old statuses',()=>{
  const x=input();x.mapping.review_routes=[];const r=runIntegratedCore(x);
  assert.equal(r.status,'LOCAL_INTEGRATION_WITH_QUARANTINE');assert.deepEqual(codes(r),[]);
  assert.equal(r.legacy_snapshot.tasks[0].state,'SUCCEEDED');
});
test('opponent request never becomes judicial refusal in current output',()=>{
  const x=input(),o=obs(x)[3],s=x.project.sources[o.source_ref];
  const a={actor_id:'SYNTHETIC_OPPONENT',actor_role:'OPPONENT',event_type:'REQUEST',statement_role:'OPPONENT_CLAIM',decision_status:'REQUEST_ONLY'};
  Object.assign(o,a);Object.assign(s,a);const r=runIntegratedCore(x);
  assert(!codes(r).includes('CIRCULAR_BURDEN_SHIFT_WARNING'));
  assert(!codes(r).includes('HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING'));
  assert(codes(r).includes('AUTOPSY_EVIDENCE_EXCLUSION_WARNING'));
  assert(r.audit_only.correction3_execution.procedural_warnings.some(w=>w.code==='CIRCULAR_BURDEN_SHIFT_WARNING'));
  assert(!('draft_text' in r.report));assert(!('support_packet' in r.report));
});
test('foreign person source holds only affected observation and warnings',()=>{
  const x=input();x.project.sources['SOURCE-0'].subject_id='OTHER';const r=runIntegratedCore(x);
  assert(!codes(r).includes('AUTOPSY_EVIDENCE_EXCLUSION_WARNING'));
  assert(codes(r).includes('CIRCULAR_BURDEN_SHIFT_WARNING'));
  assert.equal(r.report.support_reviews[0].accepted_observations.length,8);
});
test('same-person different material cannot form joint warning, facts retained',()=>{
  const x=input();obs(x)[2].material_id='OTHER';x.project.sources['SOURCE-2'].material_id='OTHER';
  const r=runIntegratedCore(x);assert.equal(r.report.support_reviews[0].accepted_observations.length,9);
  assert(!codes(r).includes('AUTOPSY_EVIDENCE_EXCLUSION_WARNING'));
});
test('missing material scope holds item rather than inferring it',()=>{
  const x=input();delete obs(x)[0].material_id;const r=runIntegratedCore(x);
  assert(r.report.support_reviews[0].held_observations.some(o=>o.id==='O-0'));
  assert(codes(r).includes('CIRCULAR_BURDEN_SHIFT_WARNING'));
});
test('different question quarantines dependent path without erasing independent warnings',()=>{
  const x=input();obs(x)[8].question_id='OTHER';x.project.sources['SOURCE-8'].question_id='OTHER';obs(x)[7].depends_on=['O-8'];
  const r=runIntegratedCore(x),held=r.report.support_reviews[0].held_observations;
  assert(held.some(o=>o.id==='O-8'));assert(held.some(o=>o.id==='O-7'));
  assert(!codes(r).includes('CAUSATION_METHOD_CONSISTENCY_REVIEW'));
  assert(codes(r).includes('CIRCULAR_BURDEN_SHIFT_WARNING'));
});
test('missing question is not wildcard or automatic migration',()=>{
  const x=input();delete obs(x)[0].question_id;delete x.project.sources['SOURCE-0'].question_id;
  const r=runIntegratedCore(x);assert(r.report.support_reviews[0].held_observations.some(o=>o.id==='O-0'));
});
test('invalid sibling review does not erase valid scoped review',()=>{
  const x=input(),other=structuredClone(x.project.support_reviews[0]);other.id='OTHER';other.subject_id='OTHER';x.project.support_reviews.push(other);
  x.mapping.review_routes.push({review_id:'OTHER',route_id:'R1',question_id:'SYNTHETIC-QUESTION-A'});
  const r=runIntegratedCore(x);assert.equal(codes(r).length,5);assert.equal(r.report.support_reviews[1].status,'INTEGRATION_REVIEW_HELD');
});
test('duplicate review IDs quarantine all occurrences',()=>{
  const x=input();x.project.support_reviews.push(structuredClone(x.project.support_reviews[0]));const r=runIntegratedCore(x);
  assert.equal(r.status,'PARTIAL_STAGE_FAILURE');assert.equal(r.receipts.correction3.status,'FAILED');
  assert(r.report.support_reviews.every(v=>v.status==='INTEGRATION_REVIEW_HELD'));assert.deepEqual(codes(r),[]);
});
test('malformed observation fails .3 but guard retains valid siblings',()=>{
  const x=input();obs(x).push(null);const r=runIntegratedCore(x);
  assert.equal(r.status,'PARTIAL_STAGE_FAILURE');assert.equal(r.receipts.correction3.status,'FAILED');
  assert.equal(r.receipts.guard.status,'SUCCEEDED');assert.equal(codes(r).length,5);
  assert.equal(r.report.support_reviews[0].held_observations.length,1);
});
test('malformed review is explicitly retained and held, not silently dropped',()=>{
  const x=input();x.project.support_reviews.push(null);const r=runIntegratedCore(x);
  assert.equal(r.report.support_reviews.length,2);assert.equal(r.report.support_reviews[1].original_review,null);
  assert.equal(r.report.support_reviews[1].status,'INTEGRATION_REVIEW_HELD');assert.equal(codes(r).length,5);
});
test('duplicate observation IDs and dependencies are held without first-ID winner',()=>{
  const x=input();obs(x).push(structuredClone(obs(x)[0]));obs(x)[8].depends_on=['O-0'];
  const r=runIntegratedCore(x);assert.equal(r.status,'PARTIAL_STAGE_FAILURE');
  assert.equal(r.report.support_reviews[0].held_observations.filter(o=>o.id==='O-0').length,2);
  assert(r.report.support_reviews[0].held_observations.some(o=>o.id==='O-8'));
  assert(codes(r).includes('CIRCULAR_BURDEN_SHIFT_WARNING'));
});
test('valid dissent, requested relief and adverse facts are preserved without consensus',()=>{
  const x=input();x.project.facts=[{id:'ADVERSE',text:'Synthetic competing evidence',disagreement:true}];
  const r=runIntegratedCore(x);
  assert.deepEqual(r.report.review_nodes_original,x.project.review_nodes);assert.deepEqual(r.report.facts_original,x.project.facts);
  assert.deepEqual(r.original_input.project.requested_remedies,x.project.requested_remedies);
  assert.equal(r.report.victim_concession_required,false);assert.deepEqual(r.report.generated_blanket_concessions,[]);
});
test('controller and institutional review actions are retained, no sanctions executed',()=>{
  const r=runIntegratedCore(input());assert.equal(r.report.action_proposals.length,5);
  assert(r.report.action_proposals.some(a=>a.action.includes('CONTROLLER')));
  assert(r.report.action_proposals.some(a=>a.action.includes('INSTITUTIONAL')));
  assert(r.report.action_proposals.every(a=>a.delivery==='NOT_SENT'&&a.automatic_sanction===false));
});
test('claims of R3 approval or model connection cannot change authority',()=>{
  const x=input();x.project.r3='APPROVED';x.legacy_project.Gemini='CONNECTED';const r=runIntegratedCore(x);
  assert.equal(r.report.approval_status_changed,false);assert.equal(r.release_or_R3_approval_changed,false);
  assert.equal(r.legacy_snapshot.external_api_calls,0);assert.equal(r.production_integration,false);
  assert.equal(r.report.total_score,null);assert.equal(r.report.legal_or_medical_finding,false);
});
test('missing Python keeps the core success receipt and produces failed stage receipts',()=>{
  const path=process.env.PATH;try{process.env.PATH='/nonexistent-synthetic-python';const r=runIntegratedCore(input());
    assert.equal(r.status,'PARTIAL_STAGE_FAILURE');assert.equal(r.receipts.legacy.status,'SUCCEEDED');
    assert.equal(r.receipts.guard.status,'FAILED');assert.equal(r.receipts.correction3.error_code,'ENOENT');assert.deepEqual(codes(r),[]);
  }finally{process.env.PATH=path;}
});
test('nonzero Python exit is a failed stage, not successful integration',()=>fakePython('exit 7',()=>{
  const r=runIntegratedCore(input());assert.equal(r.receipts.guard.exit_code,7);assert.equal(r.status,'PARTIAL_STAGE_FAILURE');
  assert.equal(r.legacy_snapshot.tasks[0].state,'SUCCEEDED');
}));
test('invalid Python JSON preserves core receipt and holds report',()=>fakePython("printf 'broken'",()=>{
  const r=runIntegratedCore(input());assert.equal(r.receipts.guard.error_code,'INVALID_PYTHON_JSON');assert.deepEqual(codes(r),[]);
  assert.equal(r.receipts.legacy.status,'SUCCEEDED');
}));
test('falsy Python JSON never yields a succeeded stage receipt',()=>{
  for(const value of ['null','false','0']) fakePython(`printf '${value}'`,()=>{
    const r=runIntegratedCore(input());assert.equal(r.receipts.guard.status,'FAILED');assert.equal(r.receipts.correction3.status,'FAILED');
  });
});
test('valid JSON with wrong schema fails output contract',()=>fakePython("printf '{}'",()=>{
  const r=runIntegratedCore(input());assert.equal(r.receipts.guard.error_code,'PYTHON_OUTPUT_CONTRACT_VIOLATION');
  assert.equal(r.audit_only.guard_execution,null);
}));
test('bounded timeout returns partial failure without rewriting core status',()=>fakePython('/bin/sleep 1',()=>{
  const r=runIntegratedCore(input(),{timeout_ms:20});assert.equal(r.status,'PARTIAL_STAGE_FAILURE');
  assert.equal(r.receipts.guard.error_code,'ETIMEDOUT');assert.equal(r.legacy_snapshot.tasks[0].state,'SUCCEEDED');
}));
test('oversized input, bad timeout, unknown schema and missing clock are rejected',()=>{
  const x=input();x.project.note='x'.repeat(2*1024*1024);assert.throws(()=>runIntegratedCore(x),/INPUT_LIMIT/);
  assert.throws(()=>runIntegratedCore(input(),{timeout_ms:0}),/INVALID_TIMEOUT/);
  const y=input();y.project.schema='UNKNOWN';assert.throws(()=>runIntegratedCore(y),/SCHEMA/);
  const z=input();delete z.now;assert.throws(()=>runIntegratedCore(z),/TIME/);
});
test('shell metacharacters in data remain inert',()=>{
  const x=input(),target='/tmp/vos-core-guard-shell-must-not-execute';x.project.note=`$(touch ${target})`;
  runIntegratedCore(x);assert.equal(existsSync(target),false);
});

test('held redundant basis preserves single-kind warning supported by independent row',()=>{
  const x=input();obs(x)[8].question_id='OTHER';x.project.sources['SOURCE-8'].question_id='OTHER';
  obs(x).push({...structuredClone(obs(x)[7]),id:'DEPENDENT-METHOD',depends_on:['O-8']});
  const r=runIntegratedCore(x),w=r.report.procedural_warnings.find(w=>w.code==='CAUSATION_METHOD_CONSISTENCY_REVIEW');
  assert(w);assert.deepEqual(w.basis_observations,['O-7']);
  assert(r.report.support_reviews[0].held_observations.some(o=>o.id==='DEPENDENT-METHOD'));
});
test('held redundant basis preserves multifact warning with complete surviving prerequisites',()=>{
  const x=input();obs(x)[8].question_id='OTHER';x.project.sources['SOURCE-8'].question_id='OTHER';
  obs(x).push({...structuredClone(obs(x)[3]),id:'DEPENDENT-REFUSAL',depends_on:['O-8']});
  const r=runIntegratedCore(x),w=r.report.procedural_warnings.find(w=>w.code==='CIRCULAR_BURDEN_SHIFT_WARNING');
  assert(w);assert(!w.basis_observations.includes('DEPENDENT-REFUSAL'));
  assert.deepEqual(new Set(w.basis_observations),new Set(['O-3','O-4','O-5']));
});
