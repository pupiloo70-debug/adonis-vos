// Reproducible full-pipeline before/after comparison, synthetic inputs only.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdtempSync, chmodSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { runIntegratedCore as originalCore } from '../0.2-core-guard-integration.v1/core_guard.mjs';
import { runIntegratedCore as candidateCore } from './core_guard.mjs';
let runIntegratedCore;
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

const scenarios = [
  ['original_order', g=>{}],
  ['reversed_order', g=>{g.reviews.reverse();}],
  ['unexpected_id_same_count', g=>{g.reviews[0].id='UNEXPECTED';}],
  ['duplicate_id_same_count', g=>{g.reviews[0].id='REVIEW-B';}],
  ['missing_review', g=>{g.reviews.shift();}],
  ['extra_unexpected_review', g=>{g.reviews.push({...structuredClone(g.reviews[1]),id:'UNEXPECTED'});}]
];
const results=[];
for (const [name, fn] of scenarios) {
  const row={scenario:name};
  for(const [label, core] of [['v1',originalCore],['v2',candidateCore]]) {
    runIntegratedCore=core; const r=inject(fn);
    row[label]={status:r.status,stage_statuses:Object.fromEntries(['legacy','correction3','guard'].map(s=>[s,r.receipts[s].status])),
      reviews:r.report.support_reviews.map(v=>({id:v.id,warnings:v.warnings.length,status:v.status,held_reason:v.held_reason})),
      binding:r.report.guard_review_binding??null,approval_status_changed:r.report.approval_status_changed,
      total_score:r.report.total_score,victim_concession_required:r.report.victim_concession_required};
  }
  results.push(row);
}
console.log(JSON.stringify({source_commit:'42122a759b1bdf9d9c4d692988ea7320cd983a72',
  scope:'Both implementations invoke actual CentralCore and both actual Python stages before test-only guard stdout mutation.',
  expected_warning_counts:{'REVIEW-A':1,'REVIEW-B':5,'REVIEW-C':0},results},null,2));
