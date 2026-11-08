import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {runIntegratedCore} from '../core_guard.mjs';

const template = JSON.parse(readFileSync(new URL('../synthetic-input.json', import.meta.url)));
const python = execFileSync('which', ['python3'], {encoding:'utf8'}).trim();
function fixture() {
  const x = structuredClone(template);
  const a = x.project.support_reviews[0];
  for (const [id, keep] of [['B',8],['C',7]]) {
    const r = structuredClone(a); r.id=id;
    r.observations = [r.observations[keep]];
    r.observations[0].id = `${id}-observation`;
    x.project.support_reviews.push(r);
    x.mapping.review_routes.push({...x.mapping.review_routes[0],review_id:id});
  }
  return x;
}
// Every fault test runs the real subprocess first, then mutates its output.
// The production adapter receives no test hook, monkeypatch or fake evaluator.
function inject(code, x=fixture(), target='guard_entry.py') {
  const dir=mkdtempSync(join(tmpdir(),'independent-review-'));
  const old=process.env.PATH;
  writeFileSync(join(dir,'python3'), `#!${python}\nimport sys, subprocess, json, os\np=subprocess.run([${JSON.stringify(python)}]+sys.argv[1:],input=sys.stdin.buffer.read(),capture_output=True)\nsys.stderr.buffer.write(p.stderr)\nif p.returncode: sys.exit(p.returncode)\nif os.path.basename(sys.argv[-1]) != ${JSON.stringify(target)}:\n sys.stdout.buffer.write(p.stdout)\n sys.exit(0)\nv=json.loads(p.stdout)\n${code}\nprint(json.dumps(v))\n`, {mode:0o700});
  try { process.env.PATH=dir+':'+old; return runIntegratedCore(x); }
  finally { process.env.PATH=old; rmSync(dir,{recursive:true,force:true}); }
}
const warnings = r => r.report.support_reviews.map(s=>s.warnings.map(w=>w.code));
const baseline = runIntegratedCore(fixture());
const expected = warnings(baseline);
function stages(r) {
  assert.equal(r.legacy_snapshot.tasks[0].state,'SUCCEEDED');
  assert.equal(r.receipts.legacy.status,'SUCCEEDED');
  assert.equal(r.receipts.correction3.status,'SUCCEEDED');
  assert.equal(r.receipts.guard.status,'SUCCEEDED');
}
function heldA(r, reason) {
  stages(r);
  assert.equal(r.report.support_reviews[0].status,'INTEGRATION_REVIEW_HELD');
  assert.equal(r.report.support_reviews[0].warnings.length,0);
  assert(r.report.support_reviews[0].held_reason.includes(reason));
  assert.deepEqual(warnings(r).slice(1),expected.slice(1));
  assert.equal(r.report.guard_review_binding.matched_count,2);
}
test('independent baseline: actual core, correction3 and guard with distinct sibling warnings',()=>{
  stages(baseline); assert.deepEqual(expected.map(x=>x.length),[5,1,1]);
  assert.equal(baseline.status,'LOCAL_INTEGRATION_SUCCEEDED');
});
for (const order of [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]]) {
  test(`independent permutation ${order.join('')}: attribution and actions remain stable`,()=>{
    const r=inject(`v['reviews']=[v['reviews'][i] for i in ${JSON.stringify(order)}]`);
    stages(r); assert.deepEqual(warnings(r),expected);
    assert.deepEqual(r.report.action_proposals,baseline.report.action_proposals);
    assert.deepEqual(r.report.support_reviews.map(s=>s.guard_output_index),[0,1,2].map(i=>order.indexOf(i)));
  });
}
test('independent duplicate expected ID quarantines every occurrence, not first/last wins',()=>{
  const r=inject("v['reviews'].append(v['reviews'][0])");
  heldA(r,'GUARD_REVIEW_ID_DUPLICATE');
  assert.equal(r.report.guard_review_binding.quarantined_outputs.length,2);
});
test('independent missing expected ID preserves two valid siblings',()=>heldA(inject("v['reviews']=v['reviews'][1:]"),'GUARD_REVIEW_ID_MISSING'));
test('independent unknown extra cannot issue proposals or suppress valid siblings',()=>{
  const r=inject("import copy\ne=copy.deepcopy(v['reviews'][0]); e['id']='EXTRA'; v['reviews'].insert(0,e)");
  stages(r); assert.deepEqual(warnings(r),expected);assert.deepEqual(r.report.action_proposals,baseline.report.action_proposals);
  assert.equal(r.report.guard_review_binding.quarantined_outputs[0].reasons[0],'GUARD_REVIEW_ID_UNEXPECTED');
});
for (const value of ['None','{}','[]','0',"{'id': '   '}"]) test(`independent malformed extra ${value} isolated`,()=>{
  const r=inject(`v['reviews'].insert(0,${value})`);stages(r);assert.deepEqual(warnings(r),expected);
  assert.equal(r.report.guard_review_binding.quarantined_outputs.length,1);
});
test('independent exact matching does not trim IDs or guess absent identity',()=>{
  heldA(inject("v['reviews'][0]['id']=' ACCESS-A '"),'GUARD_REVIEW_ID_MISSING');
});
test('independent matching ID with another review payload is held',()=>{
  heldA(inject("import copy\nr=copy.deepcopy(v['reviews'][1]); r['id']='ACCESS-A'; v['reviews'][0]=r"),'GUARD_REVIEW_INPUT_PAYLOAD_CONFLICT');
});
for (const field of ['case_id','track_id','subject_id','source_ref']) test(`independent matching ID with foreign ${field} is held`,()=>{
  heldA(inject(`v['reviews'][0]['accepted_observations'][0][${JSON.stringify(field)}]='FOREIGN'`),'GUARD_REVIEW_INPUT_PAYLOAD_CONFLICT');
});
test('independent warning basis cannot reference absent observations',()=>{
  heldA(inject("v['reviews'][0]['warnings'][0]['basis_observations']=['MISSING']"),'GUARD_REVIEW_INPUT_PAYLOAD_CONFLICT');
});
test('independent malformed warning row cannot suppress valid siblings',()=>{
  heldA(inject("v['reviews'][0]['warnings'][0]=None"),'GUARD_REVIEW_CONTRACT_VIOLATION');
});
test('independent malformed held-state remediation must not crash or suppress siblings',()=>{
  const r=inject("v['reviews'][0]['status']='REVIEW_SCOPE_HELD'\nv['reviews'][0]['held_reason']=['SCOPE']\nv['reviews'][0]['accepted_observations']=[]; v['reviews'][0]['warnings']=[]\nv['reviews'][0]['remediation']['question_material_states']={}");
  heldA(r,'GUARD_REVIEW_CONTRACT_VIOLATION');
});
test('independent invalid JSON guard fails closed while real core and correction3 survive',()=>{
  const r=inject("print('invalid-json'); sys.exit(0)");
  assert.equal(r.status,'PARTIAL_STAGE_FAILURE');assert.equal(r.receipts.guard.error_code,'INVALID_PYTHON_JSON');
  assert.equal(r.receipts.correction3.status,'SUCCEEDED');assert.equal(r.legacy_snapshot.tasks[0].state,'SUCCEEDED');
  assert.equal(r.report.action_proposals.length,0);
});
test('independent nonzero guard exit preserves core receipt and holds all reviews',()=>{
  const r=inject('sys.exit(19)');assert.equal(r.status,'PARTIAL_STAGE_FAILURE');assert.equal(r.receipts.guard.exit_code,19);
  assert.equal(r.receipts.correction3.status,'SUCCEEDED');assert.equal(r.legacy_snapshot.tasks[0].state,'SUCCEEDED');
  assert(r.report.support_reviews.every(s=>s.status==='INTEGRATION_REVIEW_HELD'));
});
test('independent correction3 failure still runs real guard and preserves review warnings',()=>{
  const r=inject('sys.exit(19)',fixture(),'bridge_entry.py');
  assert.equal(r.status,'PARTIAL_STAGE_FAILURE');assert.equal(r.receipts.correction3.exit_code,19);
  assert.equal(r.receipts.guard.status,'SUCCEEDED');assert.deepEqual(warnings(r),expected);
});
test('independent null held-state remediation row is quarantined, not dereferenced',()=>{
  const r=inject("v['reviews'][0]['status']='REVIEW_SCOPE_HELD'\nv['reviews'][0]['held_reason']=['SCOPE']\nv['reviews'][0]['accepted_observations']=[]; v['reviews'][0]['warnings']=[]\nv['reviews'][0]['remediation']['question_material_states']=[None]");
  heldA(r,'GUARD_REVIEW_CONTRACT_VIOLATION');
});
test('independent malformed optional held_reason cannot crash an existing mapping hold',()=>{
  const x=fixture();x.mapping.review_routes=x.mapping.review_routes.filter(r=>r.review_id!=='ACCESS-A');
  const r=inject("v['reviews'][0]['held_reason']=1",x);
  heldA(r,'GUARD_REVIEW_CONTRACT_VIOLATION');
});
test('independent valid scope-held result still preserves valid sibling reviews',()=>{
  const r=inject("v['reviews'][0]['status']='REVIEW_SCOPE_HELD'\nv['reviews'][0]['held_reason']=['SCOPE']\nv['reviews'][0]['accepted_observations']=[]; v['reviews'][0]['warnings']=[]\nv['reviews'][0]['remediation']={}");
  stages(r);assert.equal(r.report.support_reviews[0].status,'INTEGRATION_REVIEW_HELD');
  assert(r.report.support_reviews[0].held_reason.includes('SCOPE'));
  assert.deepEqual(warnings(r).slice(1),expected.slice(1));
});
