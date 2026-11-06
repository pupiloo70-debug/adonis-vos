import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { runResearchBridge } from './bridge.mjs';
const original = JSON.parse(readFileSync(new URL('./examples-autopsy-access.json',import.meta.url),'utf8'));
const input = () => structuredClone(original);

test('actual v02 core -> bounded Python research execution emits separate receipts and warning',()=>{
  const out=runResearchBridge(input());
  assert.equal(out.status,'LOCAL_RESEARCH_CONNECTION_SUCCEEDED');
  assert.equal(out.legacy_execution.receipt.status,'SUCCEEDED');
  assert.equal(out.research_receipt.exit_code,0);
  assert.equal(out.research_receipt.status,'SUCCEEDED');
  assert.equal(out.research_execution.version,'0.3.0-design.2-local-correction.3');
  assert(out.research_execution.procedural_warnings.some(w=>w.code==='CIRCULAR_BURDEN_SHIFT_WARNING'));
  const h=createHash('sha256').update(JSON.stringify({project:original.project,now:original.now})).digest('hex');
  assert.equal(out.research_receipt.input_sha256,h);
});
test('missing clinical diagnosis does not reduce credibility or erase the autopsy',()=>{
  const r=runResearchBridge(input()).research_execution.support_packet.access_reviews[0];
  assert.equal(r.clinical_record_absence_reduces_victim_credibility,false);
  assert(r.warnings.some(w=>w.code==='AUTOPSY_EVIDENCE_EXCLUSION_WARNING'));
});
test('legacy partial and missing provision remain unresolved, not silently migrated',()=>{
  const r=runResearchBridge(input());
  assert.deepEqual(r.legacy_execution.result.rows.map(x=>x.provision_status),['PARTIAL_REPORTED','NOT_PROVIDED']);
  assert(r.legacy_execution.result.rows.every(x=>x.resolution==='UNRESOLVED_REQUIRES_CONTENT_REVIEW'));
  assert.equal(r.research_execution.routes[0].evidence_state_basis,'INPUT_LABEL_NOT_REVERIFIED');
});
test('R3 labels and named external-model willingness are not runtime consent',()=>{
  const p=input();p.legacy_project.r3={approval:'APPROVED',Gemini:'CONNECTED'};
  const r=runResearchBridge(p);
  assert.deepEqual(r.legacy_execution.result.original_project.r3,p.legacy_project.r3);
  assert.equal(r.research_execution.approval_status_changed,false);
  assert.equal(r.legacy_snapshot.external_api_calls,0);
  assert.equal(r.research_receipt.external_api_calls,0);
});
test('wrong case or procedure mapping is rejected before dispatch',()=>{
  for(const field of ['case_id','track_id']){
    const p=input();p.mapping[field]='OTHER';assert.throws(()=>runResearchBridge(p),/MAPPING_IDENTITY_CONFLICT/);
  }
});
test('cross-case original evidence is held without becoming a current-case warning',()=>{
  const p=input();p.project.sources['SOURCE-0'].case_id='OTHER-CHILD';
  const r=runResearchBridge(p).research_execution.support_packet.access_reviews[0];
  assert.equal(r.status,'SCOPE_REVIEW_REQUIRED');assert.deepEqual(r.warnings,[]);
});
test('private input is not accepted by the synthetic research adapter',()=>{
  const p=input();p.project.synthetic=false;assert.throws(()=>runResearchBridge(p),/SYNTHETIC_RESEARCH_ONLY/);
});
test('input R3 string cannot waive synthetic-only gate',()=>{
  const p=input();p.project.synthetic='true';p.project.r3='APPROVED';assert.throws(()=>runResearchBridge(p),/SYNTHETIC_RESEARCH_ONLY/);
});
test('invalid Python review records produce a failed research receipt, not a success claim',()=>{
  const p=input();p.project.support_reviews[0].purpose='IMPOSE_SANCTION';
  const r=runResearchBridge(p);
  assert.equal(r.status,'PYTHON_RESEARCH_STEP_FAILED');assert.equal(r.research_receipt.status,'FAILED');
  assert.equal(r.research_execution,null);assert.equal(r.legacy_execution.receipt.status,'SUCCEEDED');
  assert.equal(r.no_legacy_status_overwrite,true);
});
test('request maps are explicit, complete, one-to-one and content preserving',()=>{
  const p=input();p.mapping.request_routes=[];assert.throws(()=>runResearchBridge(p),/INCOMPLETE_REQUEST_ROUTE_MAP/);
  const q=input();q.project.routes[0].controller='OTHER';assert.throws(()=>runResearchBridge(q),/REQUEST_CONTENT_MAPPING_CONFLICT/);
});
test('research execution does not mutate either version input',()=>{
  const p=input(),before=structuredClone(p);runResearchBridge(p);assert.deepEqual(p,before);
});
test('no score, sanction, repayment, approval or production integration is asserted',()=>{
  const r=runResearchBridge(input()),a=r.research_execution.support_packet.access_reviews[0];
  assert.equal(r.production_integration,false);assert.equal(r.research_receipt.total_score,null);
  assert.equal(a.benefit_reversal_review.repayment_or_confiscation_executed,false);
  assert.equal(a.coordination_or_criminal_cartel_established,false);
  assert.equal(r.research_execution.deployment_status,'NOT_DEPLOYED');
});
test('shell-like data is inert and not interpolated into subprocess command',()=>{
  const p=input();p.project.note='$(touch /tmp/vos-untrusted-input-must-not-execute)';
  runResearchBridge(p);assert.equal(existsSync('/tmp/vos-untrusted-input-must-not-execute'),false);
});
test('invalid clock, unsupported version and excessive input fail closed',()=>{
  const p=input();p.now='not-a-time';assert.throws(()=>runResearchBridge(p),/EXPLICIT_TIME_REQUIRED/);
  const q=input();q.legacy_project.schema='ADONIS-VOS-PROJECT/9.9';assert.throws(()=>runResearchBridge(q),/LEGACY_SCHEMA_REQUIRED/);
  const r=input();r.project.note='x'.repeat(2*1024*1024);assert.throws(()=>runResearchBridge(r),/BRIDGE_INPUT_LIMIT/);
});
