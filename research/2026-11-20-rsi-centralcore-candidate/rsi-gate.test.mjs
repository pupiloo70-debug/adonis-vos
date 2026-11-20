import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runSyntheticRSICycle, STATUS, sha256 } from './rsi-gate.mjs';
const project = JSON.parse(readFileSync(new URL('../../examples/synthetic-project.json',import.meta.url),'utf8'));
const sample = (events=[],sources=[])=>({schema:'ADONIS-RSI/SYNTHETIC-1',synthetic:true,project:structuredClone(project),events,sources});
const e=(id,type,q='Q1',source_refs=[])=>({id,type,question_id:q,source_refs});
test('uses real CentralCore and records matching receipts',()=>{
  const out=runSyntheticRSICycle(sample([e('a','REQUEST')]));
  assert.equal(out.core.receipt.status,'SUCCEEDED');assert.equal(out.total_score,null);
  assert.equal(out.core.receipt.input_sha256,sha256(project));
});
test('rejects private and unmarked inputs',()=>{
  assert.throws(()=>runSyntheticRSICycle({...sample(),synthetic:false}),/SYNTHETIC_ONLY/);
  assert.throws(()=>runSyntheticRSICycle({...sample(),schema:'OTHER'}),/SYNTHETIC_ONLY/);
});
test('detects circular justification, preserves explanation duty',()=>{
  const r=runSyntheticRSICycle(sample([e('a','NOT_PROVIDED'),e('b','FORMAL_CLOSURE')]));
  assert.ok(r.findings[0].reasons.includes('CIRCULAR_JUSTIFICATION_REVIEW'));
  assert.ok(r.findings[0].reasons.includes('FORMAL_CLOSURE_NOT_SUBSTANTIVE_REMEDY'));
});
test('reported benefit is not confirmed remedy',()=>{
  const r=runSyntheticRSICycle(sample([e('a','REMEDY_REPORTED')]));
  assert.ok(r.findings[0].reasons.includes('BENEFIT_SOURCE_UNVERIFIED'));
});
test('independent dissent survives consensus or authority override',()=>{
  const r=runSyntheticRSICycle(sample([e('a','INDEPENDENT_DISSENT'),e('b','AUTHORITY_OVERRIDE')]));
  assert.deepEqual(r.findings[0].independent_dissent_ids,['a']);
  assert.ok(r.findings[0].reasons.includes('AUTHORITY_OVERRIDE_REJECTED'));
});
test('unreviewed provision is not a verified answer',()=>{
  const r=runSyntheticRSICycle(sample([e('a','PROVIDED','Q1',['S'])],[{id:'S',status:'CLAIM_ONLY'}]));
  assert.ok(r.findings[0].reasons.includes('SUPPLY_NOT_INDEPENDENT_VERIFICATION'));
});
test('correction is pending independent verification',()=>{
  const r=runSyntheticRSICycle(sample([e('a','CORRECTION_REPORTED')]));
  assert.ok(r.findings[0].reasons.includes('CORRECTION_REQUIRES_VERIFICATION'));
});
test('ethical declaration cannot certify ASI',()=>{
  const r=runSyntheticRSICycle(sample([e('a','TECH_SINGULARITY_CLAIM')]));
  assert.ok(r.findings[0].reasons.includes('ETHICAL_PRIORITY_NOT_TECH_CERTIFICATION'));
});
test('does not silently merge questions or events',()=>{
  const r=runSyntheticRSICycle(sample([e('a','REQUEST','Q1'),e('b','REMEDY_REPORTED','Q2')]));
  assert.equal(r.findings.length,2); assert.ok(r.findings[0].reasons.includes('CONTROLLER_EXPLANATION_PENDING'));
});
test('duplicate event ID and absent evidence reference rejected',()=>{
  assert.throws(()=>runSyntheticRSICycle(sample([e('a','REQUEST'),e('a','REQUEST')])),/INVALID_EVENT/);
  assert.throws(()=>runSyntheticRSICycle(sample([e('b','REQUEST','Q1',['MISSING'])])),/INVALID_EVENT/);
});
test('does not mutate input',()=>{
  const input=sample([e('a','REQUEST')]);const before=JSON.stringify(input);
  runSyntheticRSICycle(input);assert.equal(JSON.stringify(input),before);
});
test('boundaries remain invariant',()=>{
  const r=runSyntheticRSICycle(sample());
  assert.equal(STATUS.default_path_connected,false);assert.equal(STATUS.total_score,null);
  assert.equal(r.civic_trace_046,'R3_RELEASE_NOT_APPROVED');
  assert.equal(r.no_legal_or_medical_adjudication,true);
  assert.ok(r.proposals.every(p=>p.status==='PROPOSED_NOT_ADOPTED'));
});

import { compareResearchRevision } from './rsi-gate.mjs';
test('recursive revision vetoes removed dissent despite faster code',()=>{
  const before=runSyntheticRSICycle(sample([e('a','INDEPENDENT_DISSENT','Q1',['S'])],[{id:'S',status:'RECORD_LINKED'}]));
  const after=structuredClone(before);after.findings[0].independent_dissent_ids=[];
  const result=compareResearchRevision(before,after,{technical_tests_passed:true});
  assert.equal(result.status,'ADOPTION_HELD'); assert.ok(result.reasons.some(x=>x.startsWith('DISSENT_DROPPED')));
});
test('recursive revision vetoes dropped source and unverified tests',()=>{
  const before=runSyntheticRSICycle(sample([e('a','REQUEST','Q1',['S'])],[{id:'S',status:'RECORD_LINKED'}]));
  const after=structuredClone(before);after.findings[0].source_refs=[];
  const result=compareResearchRevision(before,after);
  assert.ok(result.reasons.some(x=>x.startsWith('SOURCE_DROPPED')));
  assert.ok(result.reasons.includes('TECHNICAL_TESTS_UNVERIFIED'));
});
test('successful research comparison still requires human review',()=>{
  const before=runSyntheticRSICycle(sample([e('a','REQUEST')]));
  const result=compareResearchRevision(before,structuredClone(before),{technical_tests_passed:true});
  assert.equal(result.status,'RESEARCH_REVIEW_READY');assert.equal(result.requires_r3_review,true);
  assert.equal(result.auto_merge,false);assert.equal(result.auto_release,false);
});
