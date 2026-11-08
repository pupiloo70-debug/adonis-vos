import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdtempSync, chmodSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { runIntegratedCore } from './core_guard.mjs';

const original = JSON.parse(readFileSync(new URL('./synthetic-input.json', import.meta.url), 'utf8'));
const python = spawnSync('python3', ['-c','import sys; print(sys.executable)'], {encoding:'utf8'}).stdout.trim();
assert(python);

function fixture() {
  const x = structuredClone(original), raw = x.project.support_reviews[0], pair = x.mapping.review_routes[0];
  x.project.support_reviews = ['REVIEW-A','REVIEW-B','REVIEW-C'].map((id, i) => {
    const row = structuredClone(raw); row.id = id;
    row.observations = (i === 0 ? [row.observations[7]] : i === 1 ? row.observations : []).map(o =>
      ({...o, id:`${id}:${o.id}`, depends_on:(o.depends_on ?? []).map(d => `${id}:${d}`)}));
    return row;
  });
  x.mapping.review_routes = x.project.support_reviews.map(r => ({...pair, review_id:r.id}));
  return x;
}

// Test-only executable shim. Both real Python modules run; only the guard's
// serialized boundary output is changed. No injection API in production code.
function inject(transform, x = fixture()) {
  const previous = process.env.PATH, dir = mkdtempSync(join(tmpdir(),'vos-identity-'));
  try {
    const shim = join(dir,'shim.mjs');
    writeFileSync(shim, `import {readFileSync} from 'node:fs'; import {spawnSync} from 'node:child_process';
      const r=spawnSync(${JSON.stringify(python)},process.argv.slice(2),{input:readFileSync(0),encoding:'utf8',maxBuffer:16*1024*1024});
      if(r.error){process.stderr.write(String(r.error));process.exit(90);}
      process.stderr.write(r.stderr??''); if(r.status!==0){process.stdout.write(r.stdout??'');process.exit(r.status??91);}
      let s=r.stdout;
      if(process.argv.some(a=>a.endsWith('/guard_entry.py'))){const g=JSON.parse(s);(${transform.toString()})(g);s=JSON.stringify(g);}
      process.stdout.write(s);
    `);
    writeFileSync(join(dir,'python3'), `#!/bin/sh\nexec ${JSON.stringify(process.execPath)} ${JSON.stringify(shim)} "$@"\n`);
    chmodSync(join(dir,'python3'),0o700); process.env.PATH=dir;
    return runIntegratedCore(x);
  } finally {process.env.PATH=previous;rmSync(dir,{recursive:true,force:true});}
}
const review = (r,id) => r.report.support_reviews.find(row => row.id === id);
const summary = r => Object.fromEntries(r.report.support_reviews.map(row => [row.id,row.warnings.length]));
const expected = {'REVIEW-A':1,'REVIEW-B':5,'REVIEW-C':0};
const noAuthorityChange = r => {
  assert.equal(r.receipts.legacy.status,'SUCCEEDED');
  assert.equal(r.report.approval_status_changed,false);
  assert.equal(r.report.external_action_performed,false);
  assert.equal(r.report.victim_concession_required,false);
  assert.deepEqual(r.report.generated_blanket_concessions,[]);
  assert.equal(r.total_score,null);
};

test('actual full integration keeps three distinct input review identities',()=>{
  const r=runIntegratedCore(fixture());assert.deepEqual(summary(r),expected);
  assert.equal(r.status,'LOCAL_INTEGRATION_SUCCEEDED');
  assert.equal(r.receipts.correction3.status,'SUCCEEDED');assert.equal(r.receipts.guard.status,'SUCCEEDED');
  assert.equal(r.report.guard_review_binding.matched_count,3);noAuthorityChange(r);
});

for(const order of [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]]) {
  test(`full subprocess boundary permutation ${order.join('')} preserves attribution`,()=>{
    const fn=Function('g',`g.reviews=${JSON.stringify(order)}.map(i=>g.reviews[i]);`);
    const r=inject(fn);assert.deepEqual(summary(r),expected);
    assert.equal(r.status,'LOCAL_INTEGRATION_SUCCEEDED');
    assert.equal(r.report.guard_review_binding.status,'BOUND');noAuthorityChange(r);
    for(const row of r.report.support_reviews) assert.equal(r.audit_only.guard_execution.reviews[row.guard_output_index].id,row.id);
  });
}
test('missing output holds only missing review even when count changes',()=>{
  const r=inject(g=>{g.reviews=g.reviews.filter(r=>r.id!=='REVIEW-A');});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
  assert(review(r,'REVIEW-A').held_reason.includes('GUARD_REVIEW_ID_MISSING'));
  assert.equal(r.status,'LOCAL_INTEGRATION_WITH_QUARANTINE');assert.equal(r.receipts.guard.status,'SUCCEEDED');
});
test('duplicate output quarantines every duplicate and keeps valid sibling warnings',()=>{
  const r=inject(g=>{g.reviews.push(structuredClone(g.reviews[0]));});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
  assert.equal(r.report.guard_review_binding.quarantined_outputs.length,2);
  assert(review(r,'REVIEW-A').held_reason.includes('GUARD_REVIEW_ID_DUPLICATE'));
});
test('malformed duplicate cannot win over a well-formed output with same ID',()=>{
  const r=inject(g=>{g.reviews.push({id:'REVIEW-A',status:'WRONG'});});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
  assert(review(r,'REVIEW-A').held_reason.includes('GUARD_REVIEW_ID_DUPLICATE'));
});
test('unknown replacement is retained only in audit output and missing expected review is held',()=>{
  const r=inject(g=>{g.reviews[0].id='OTHER';});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
  assert.equal(r.report.guard_review_binding.quarantined_outputs[0].id,'OTHER');
  assert.equal(r.audit_only.guard_execution.reviews[0].id,'OTHER');
  assert.equal(r.report.support_reviews.length,3);
});
test('extra unexpected output does not suppress any valid review',()=>{
  const r=inject(g=>{g.reviews.push({...structuredClone(g.reviews[1]),id:'EXTRA'});});
  assert.deepEqual(summary(r),expected);assert.equal(r.status,'LOCAL_INTEGRATION_WITH_QUARANTINE');
  assert.equal(r.report.guard_review_binding.quarantined_outputs.length,1);
});
test('invalid IDs and nonobjects are individually quarantined without global contract failure',()=>{
  const r=inject(g=>{g.reviews.push(null,4,[],{id:''},{id:' '},{id:0},{id:{}},{id:false});});
  assert.deepEqual(summary(r),expected);assert.equal(r.report.guard_review_binding.quarantined_outputs.length,8);
  assert.equal(r.receipts.guard.status,'SUCCEEDED');
});
test('numeric string coercion and trimming never match an expected review',()=>{
  const r=inject(g=>{g.reviews[0].id=' REVIEW-A';g.reviews[1].id='REVIEW-B ';});
  assert.deepEqual(summary(r),{'REVIEW-A':0,'REVIEW-B':0,'REVIEW-C':0});
  assert.equal(r.report.guard_review_binding.quarantined_outputs.length,2);
});
test('malformed review is isolated rather than discarding valid sibling outputs',()=>{
  const r=inject(g=>{g.reviews[0].accepted_observations=null;});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
  assert(review(r,'REVIEW-A').held_reason.includes('GUARD_REVIEW_CONTRACT_VIOLATION'));
});
test('scope-held malformed remediation is isolated without an uncaught exception',()=>{
  const r=inject(g=>{g.reviews[0]={id:'REVIEW-A',status:'REVIEW_SCOPE_HELD',held_reason:[],warnings:[],accepted_observations:[],held_observations:[],remediation:{question_material_states:3}};});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
  assert(review(r,'REVIEW-A').held_reason.includes('GUARD_REVIEW_CONTRACT_VIOLATION'));
});
for(const field of ['case_id','track_id','subject_id']) test(`returned cross-${field} observation cannot attach through a valid review ID`,()=>{
  const fn=Function('g',`g.reviews[0].accepted_observations[0][${JSON.stringify(field)}]='FOREIGN';`);
  const r=inject(fn);assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
  assert(review(r,'REVIEW-A').held_reason.includes('GUARD_REVIEW_INPUT_PAYLOAD_CONFLICT'));
});
test('foreign warning context is held even if accepted observations remain correct',()=>{
  const r=inject(g=>{g.reviews[0].warnings[0].context.case_id='FOREIGN';});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
});
test('swapped IDs with unchanged payloads cannot impersonate another input review',()=>{
  const r=inject(g=>{[g.reviews[0].id,g.reviews[1].id]=[g.reviews[1].id,g.reviews[0].id];});
  assert(review(r,'REVIEW-A').held_reason.includes('GUARD_REVIEW_INPUT_PAYLOAD_CONFLICT'));
  assert(review(r,'REVIEW-B').held_reason.includes('GUARD_REVIEW_INPUT_PAYLOAD_CONFLICT'));
  assert.equal(r.report.procedural_warnings.length,0);
});
test('unknown warning basis cannot be resolved against a sibling review',()=>{
  const r=inject(g=>{g.reviews[0].warnings[0].basis_observations=['REVIEW-B:O-7'];});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
});
test('returned source or actor substitution cannot be accepted by ID alone',()=>{
  const r=inject(g=>{g.reviews[0].accepted_observations[0].actor_id='FOREIGN';});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
});
test('duplicate accepted observation identity is not a first-or-last winner',()=>{
  const r=inject(g=>{g.reviews[0].accepted_observations.push(structuredClone(g.reviews[0].accepted_observations[0]));});
  assert.deepEqual(summary(r),{...expected,'REVIEW-A':0});
});
test('input duplicate identity remains held without suppressing independent review',()=>{
  const x=fixture();x.project.support_reviews.push(structuredClone(x.project.support_reviews[0]));
  const r=runIntegratedCore(x);
  assert.equal(r.status,'PARTIAL_STAGE_FAILURE');assert.equal(r.receipts.correction3.status,'FAILED');
  assert.equal(review(r,'REVIEW-B').warnings.length,5);
  assert(r.report.support_reviews.filter(row=>row.id==='REVIEW-A').every(row=>row.status==='INTEGRATION_REVIEW_HELD'));
});
test('prototype property names are exact Map keys, not accidental matches',()=>{
  const x=fixture();x.project.support_reviews[0].id='__proto__';x.mapping.review_routes[0].review_id='__proto__';
  x.project.support_reviews[1].id='constructor';x.mapping.review_routes[1].review_id='constructor';
  const r=inject(g=>{g.reviews.reverse();},x);
  assert.equal(review(r,'__proto__').warnings.length,1);assert.equal(review(r,'constructor').warnings.length,5);
});
test('all missing reviews is quarantine, not successful complete integration',()=>{
  const r=inject(g=>{g.reviews=[];});
  assert.equal(r.status,'LOCAL_INTEGRATION_WITH_QUARANTINE');
  assert(r.report.support_reviews.every(row=>row.held_reason.includes('GUARD_REVIEW_ID_MISSING')));
  assert.equal(r.report.procedural_warnings.length,0);noAuthorityChange(r);
});
test('wrong envelope still fails the entire guard stage',()=>{
  const r=inject(g=>{g.release_or_R3_approval_changed=true;});
  assert.equal(r.receipts.guard.status,'FAILED');assert.equal(r.status,'PARTIAL_STAGE_FAILURE');
  assert.equal(r.report.procedural_warnings.length,0);assert.equal(r.audit_only.guard_execution,null);
});
