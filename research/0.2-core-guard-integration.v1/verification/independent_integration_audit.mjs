// Independent integration-level probes. All inputs synthetic; no baseline edits.
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdtempSync, chmodSync, rmSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {runIntegratedCore} from '../core_guard.mjs';
const template=JSON.parse(readFileSync(new URL('./audit-fixture.json',import.meta.url),'utf8'));
const fresh=()=>structuredClone(template);
const hash=x=>createHash('sha256').update(x).digest('hex');
const rows=p=>p.project.support_reviews[0].observations;
const warnings=o=>o.report.procedural_warnings.map(w=>w.code);
const accepted=o=>o.report.support_reviews[0].accepted_observations.map(x=>x.id);
const held=o=>o.report.support_reviews[0].held_observations.map(x=>x.id);
const results=[];
function probe(name, fn) {try {fn();results.push({name,status:'PASS'});} catch(e){results.push({name,status:'FAIL',error:e.message,stack:e.stack});}}
const AUTOPSY='AUTOPSY_EVIDENCE_EXCLUSION_WARNING';
const CIRCULAR='CIRCULAR_BURDEN_SHIFT_WARNING';
const CARTEL='HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING';
const METHOD='CAUSATION_METHOD_CONSISTENCY_REVIEW';
const SUSCEPTIBILITY='INDIVIDUAL_SUSCEPTIBILITY_REVIEW_OPEN';
probe('actual core and two Python stages succeed with distinct receipts',()=>{
 const p=fresh(),o=runIntegratedCore(p);
 assert.equal(o.status,'LOCAL_INTEGRATION_SUCCEEDED');
 assert.equal(o.legacy_snapshot.tasks[0].state,'SUCCEEDED');
 for(const s of ['legacy','correction3','guard'])assert.equal(o.receipts[s].status,'SUCCEEDED');
 assert.equal(o.receipts.legacy.input_sha256,hash(JSON.stringify(p.legacy_project)));
 assert.equal(o.receipts.correction3.input_sha256,hash(JSON.stringify({project:p.project,now:p.now})));
 assert.equal(o.receipts.guard.input_sha256,hash(JSON.stringify(p.project)));
 assert.equal(o.receipts.integration.report_sha256,hash(JSON.stringify(o.report)));
 assert.equal(o.legacy_snapshot.external_api_calls,0);
 assert.equal(o.report.support_reviews[0].accepted_observations.length,9);
 assert.equal(warnings(o).length,5);
});
probe('input snapshot, sources, dissent, adverse facts and proposals are retained without mutation',()=>{
 const p=fresh(); p.project.review_nodes={lawyer:{case_id:p.project.case_id,track_id:p.project.track_id,review_ref:'SYNTHETIC-DISSENT',scope:'synthetic',qualification_ref:'UNVERIFIED',opinion:'adverse opinion',reviewed_sources:['SOURCE-0'],version:'3',correction:'previous preserved',disagreement:{text:'SYNTHETIC DISSENT MARKER',previous_version:{text:'earlier dissent',version:'2'}}}};
 p.project.facts=[{id:'F-ADVERSE',case_id:p.project.case_id,track_id:p.project.track_id,source_ref:'SOURCE-0',text:'Synthetic adverse fact',epistemic_status:'UNVERIFIED',statement_role:'OPPONENT_CLAIM',adverse:true}];
 const before=structuredClone(p),o=runIntegratedCore(p);
 assert.deepEqual(p,before);assert.deepEqual(o.original_input,p);
 assert.deepEqual(o.report.review_nodes_original,p.project.review_nodes);assert.deepEqual(o.report.facts_original,p.project.facts);
 assert(o.report.action_proposals.some(x=>x.action.includes('CONTROLLER')));
 assert(o.report.action_proposals.some(x=>x.action.includes('INSTITUTIONAL')));
 assert(o.report.action_proposals.every(x=>x.delivery==='NOT_SENT'&&!x.victim_concession_required));
});
probe('partial provision and missing provision remain distinct unresolved core rows',()=>{
 const o=runIntegratedCore(fresh()); assert.deepEqual(o.report.legacy_rows.map(x=>x.provision_status),['PARTIAL_REPORTED','NOT_PROVIDED']);
 assert(o.report.legacy_rows.every(x=>x.resolution==='UNRESOLVED_REQUIRES_CONTENT_REVIEW'));
});
probe('no score, adjudication, approval, rule change, automatic concession or deployment',()=>{
 const o=runIntegratedCore(fresh());
 assert.equal(o.total_score,null);assert.equal(o.production_integration,false);assert.equal(o.release_or_R3_approval_changed,false);
 assert.equal(o.report.total_score,null);assert.equal(o.report.legal_or_medical_finding,false);
 assert.equal(o.report.canonical_rules_changed,false);assert.equal(o.report.approval_status_changed,false);
 assert.equal(o.report.external_action_performed,false);assert.equal(o.report.victim_concession_required,false);
 assert.equal(o.report.clinical_record_absence_reduces_victim_credibility,false);assert.deepEqual(o.report.generated_blanket_concessions,[]);
 assert.equal(o.report.deployment_status,'NOT_DEPLOYED');
});
probe('foreign-case observation and source are held without suppressing independent warnings',()=>{
 const p=fresh();rows(p)[0].case_id='FOREIGN-CASE';p.project.sources['SOURCE-0'].case_id='FOREIGN-CASE';
 const o=runIntegratedCore(p);assert(held(o).includes('O-0'));assert(!warnings(o).includes(AUTOPSY));assert(warnings(o).includes(CIRCULAR));assert(warnings(o).includes(METHOD));
});
for(const field of ['case_id','track_id','subject_id','material_id','question_id'])probe('source '+field+' mismatch only quarantines its dependent evidence',()=>{
 const p=fresh();p.project.sources['SOURCE-0'][field]='FOREIGN-'+field;
 const o=runIntegratedCore(p);assert(held(o).includes('O-0'));assert(!warnings(o).includes(AUTOPSY));assert(warnings(o).includes(CIRCULAR));
});
probe('matching separate materials retain facts but cannot combine autopsy warning',()=>{
 const p=fresh();rows(p)[2].material_id='OTHER-MATERIAL';p.project.sources['SOURCE-2'].material_id='OTHER-MATERIAL';
 const o=runIntegratedCore(p);assert(accepted(o).includes('O-0'));assert(accepted(o).includes('O-2'));assert(!warnings(o).includes(AUTOPSY));assert(warnings(o).includes(CIRCULAR));
});
probe('opposing request cannot become judicial refusal; stale correction3 warning stays audit-only',()=>{
 const p=fresh(),r=rows(p)[3],s=p.project.sources[r.source_ref];
 for(const x of [r,s])Object.assign(x,{actor_id:'SYNTHETIC_OPPONENT',actor_role:'OPPONENT',event_type:'REQUEST',statement_role:'OPPONENT_CLAIM',decision_status:'REQUEST_ONLY'});
 const o=runIntegratedCore(p);assert(held(o).includes(r.id));assert(!warnings(o).includes(CIRCULAR));assert(!warnings(o).includes(CARTEL));assert(warnings(o).includes(AUTOPSY));
 assert(o.audit_only.correction3_execution.procedural_warnings.some(w=>w.code===CIRCULAR));
 assert.equal(Object.hasOwn(o.report,'support_packet'),false);assert.equal(Object.hasOwn(o.report,'draft_text'),false);assert.equal(Object.hasOwn(o.report,'access_reviews'),false);
 assert(!JSON.stringify(o.report.action_proposals).includes(CIRCULAR));
});
probe('one nested foreign source scope does not erase unrelated valid evidence',()=>{
 const p=fresh();p.project.sources['SOURCE-0'].metadata={subject_id:'OTHER-PERSON'};
 const o=runIntegratedCore(p);assert(held(o).includes('O-0'));assert(warnings(o).includes(CIRCULAR));assert(warnings(o).includes(SUSCEPTIBILITY));
});
probe('cross-question observation is explicitly quarantined, never wildcarded',()=>{
 const p=fresh();rows(p)[8].question_id='FOREIGN-Q';p.project.sources['SOURCE-8'].question_id='FOREIGN-Q';
 const o=runIntegratedCore(p);assert(held(o).includes('O-8'));assert(!accepted(o).includes('O-8'));assert(!warnings(o).includes(SUSCEPTIBILITY));assert(warnings(o).includes(METHOD));
});
probe('post-binding quarantine propagates to dependent observations and their warnings',()=>{
 const p=fresh();rows(p)[7].depends_on=['O-8'];rows(p)[8].question_id='FOREIGN-Q';p.project.sources['SOURCE-8'].question_id='FOREIGN-Q';
 const o=runIntegratedCore(p);assert(held(o).includes('O-8'));assert(held(o).includes('O-7'));assert(!accepted(o).includes('O-7'));assert(!warnings(o).includes(METHOD));assert(warnings(o).includes(AUTOPSY));
});
probe('post-binding quarantine propagates transitively, preserving independent branches',()=>{
 const p=fresh();rows(p)[6].depends_on=['O-7'];rows(p)[7].depends_on=['O-8'];rows(p)[8].question_id='FOREIGN-Q';p.project.sources['SOURCE-8'].question_id='FOREIGN-Q';
 const o=runIntegratedCore(p);assert(['O-6','O-7','O-8'].every(x=>held(o).includes(x)));assert(!warnings(o).includes(CARTEL));assert(!warnings(o).includes(METHOD));assert(warnings(o).includes(CIRCULAR));
});
probe('source-held dependency propagates while unrelated warnings remain',()=>{
 const p=fresh();rows(p)[7].depends_on=['O-8'];p.project.sources['SOURCE-8'].locator='';
 const o=runIntegratedCore(p);assert(held(o).includes('O-7'));assert(held(o).includes('O-8'));assert(!warnings(o).includes(METHOD));assert(warnings(o).includes(CIRCULAR));
});
probe('missing observation question is quarantined even if source also omits it',()=>{
 const p=fresh();delete rows(p)[0].question_id;delete p.project.sources['SOURCE-0'].question_id;
 const o=runIntegratedCore(p);assert(held(o).includes('O-0'));assert(!warnings(o).includes(AUTOPSY));assert(warnings(o).includes(CIRCULAR));
});
for(const field of ['controller','subject_id','question_id'])probe('review-route '+field+' mismatch cannot authorize warnings',()=>{
 const p=fresh();p.project.routes[0][field]='CONFLICT';
 let out;try {out=runIntegratedCore(p);} catch(e){assert.match(e.message,/CONFLICT|MAPPING|SCOPE/);return;}
 assert.equal(warnings(out).length,0);
});
probe('missing and ambiguous review map fail closed',()=>{
 for(const ambiguous of [false,true]){const p=fresh();p.mapping.review_routes=ambiguous?[...p.mapping.review_routes,...p.mapping.review_routes]:[]; const o=runIntegratedCore(p);assert.equal(warnings(o).length,0);assert.equal(o.report.support_reviews[0].status,'INTEGRATION_REVIEW_HELD');}
});
probe('unbound sibling review cannot suppress valid review warnings',()=>{
 const p=fresh(),s=structuredClone(p.project.support_reviews[0]);s.id='BAD-SIBLING';s.subject_id='FOREIGN';p.project.support_reviews.push(s);
 p.mapping.review_routes.push({review_id:s.id,route_id:'R1',question_id:'Q1'});
 const o=runIntegratedCore(p);assert.equal(o.report.support_reviews[1].status,'INTEGRATION_REVIEW_HELD');assert.equal(warnings(o).length,5);
});
probe('duplicate observation IDs hold all ambiguous occurrences, preserving independent evidence even if correction3 fails',()=>{
 const p=fresh();rows(p).push(structuredClone(rows(p)[0]));const o=runIntegratedCore(p);
 assert.equal(o.receipts.correction3.status,'FAILED');assert.equal(o.receipts.guard.status,'SUCCEEDED');assert.equal(o.status,'PARTIAL_STAGE_FAILURE');
 assert(!accepted(o).includes('O-0'));assert.equal(held(o).filter(x=>x==='O-0').length,2);assert(!warnings(o).includes(AUTOPSY));assert(warnings(o).includes(CIRCULAR));
});
probe('malformed observation is held while independent valid items survive',()=>{
 const p=fresh();rows(p).push(null);const o=runIntegratedCore(p);
 assert.equal(o.receipts.correction3.status,'FAILED');assert.equal(o.receipts.guard.status,'SUCCEEDED');assert.equal(warnings(o).length,5);
});
probe('shadow guard payload cannot replace the project sent to either Python stage',()=>{
 const p=fresh();p.guard_project={synthetic:true,support_reviews:[],sources:{}};
 const o=runIntegratedCore(p);assert.equal(warnings(o).length,5);assert.equal(o.receipts.guard.input_sha256,hash(JSON.stringify(p.project)));
});
probe('private inputs and subject-free projects are rejected before integration',()=>{
 for(const f of [p=>p.project.synthetic=false,p=>p.legacy_project.synthetic=false,p=>delete p.project.subject_id]){const p=fresh();f(p);assert.throws(()=>runIntegratedCore(p));}
});
probe('request route mapping remains exact, complete, and one-to-one',()=>{
 for(const f of [p=>p.mapping.request_routes=[],p=>p.project.routes[0].records_needed=['UNMAPPED'],p=>p.mapping.request_routes.push(structuredClone(p.mapping.request_routes[0]))]){const p=fresh();f(p);assert.throws(()=>runIntegratedCore(p));}
});
function addRemedy(p,id,type,time='2026-11-01T10:00:00+00:00',q='Q1',m='GENERAL'){
 const ref='REMEDY-'+id,quote='Synthetic remedy '+id;
 const scope={case_id:p.project.case_id,track_id:p.project.track_id,subject_id:p.project.subject_id,question_id:q,material_id:m};
 p.project.sources[ref]={...scope,primary_text:quote,locator:'synthetic remedy',source_class:'CONTEMPORANEOUS_RECORD'};
 (p.project.support_reviews[0].remediation_events??=[]).push({...scope,id,type,source_ref:ref,quoted_text:quote,occurred_at:time});
}
probe('grant does not become access or erase prior burdens',()=>{
 const p=fresh();addRemedy(p,'E1','REVIEW_GRANTED');const r=runIntegratedCore(p).report.support_reviews[0].remediation;
 assert.equal(r.question_material_states[0].status,'GRANT_ONLY_ACCESS_NOT_ESTABLISHED');assert.equal(r.prior_burdens_preserved,true);
});
probe('partial access, revocation, and simultaneous conflict remain reported open states',()=>{
 for(const [types,status] of [[['ACCESS_PARTIAL'],'PARTIAL_ACCESS_REPORTED_REMAINDER_OPEN'],[['ACCESS_REVOKED'],'ACCESS_REVOKED_REVIEW_OPEN'],[['ACCESS_PERFORMED','ACCESS_REVOKED'],'SIMULTANEOUS_CONFLICT_REVIEW_OPEN']]){
 const p=fresh();types.forEach((t,i)=>addRemedy(p,'E'+i,t));const r=runIntegratedCore(p).report.support_reviews[0].remediation;
 assert.equal(r.question_material_states[0].status,status);assert.equal(r.access_truth_independently_authenticated,false);
 }
});
probe('foreign-question remedy state cannot become a current route remedy',()=>{
 const p=fresh();addRemedy(p,'E1','ACCESS_PERFORMED',undefined,'OTHER-Q');const o=runIntegratedCore(p),r=o.report.support_reviews[0].remediation;
 assert.deepEqual(r.question_material_states,[]);assert.equal(r.unbound_question_states.length,1);assert.equal(r.unresolved_route_binding,true);
});
// Inject controlled child stdout, then restore PATH and remove only this test's temporary directory.
function withGuardOutput(payload, run) {
 const python=spawnSync('python3',['-c','import sys; print(sys.executable)'],{encoding:'utf8'}).stdout.trim();assert(python);
 const dir=mkdtempSync(join(tmpdir(),'vos-audit-output-')),shim=join(dir,'python3'),file=join(dir,'payload.json');
 const path=process.env.PATH;
 try {
  writeFileSync(file,JSON.stringify(payload));
  writeFileSync(shim,`#!/bin/sh
case "$*" in
 *guard_entry.py*) cat ${JSON.stringify(file)} ;;
 *) exec ${JSON.stringify(python)} "$@" ;;
esac
`);
  chmodSync(shim,0o700);
  process.env.PATH=dir+':'+path;
  return run();
 } finally {
  if (path === undefined) delete process.env.PATH; else process.env.PATH=path;
  rmSync(dir,{recursive:true,force:true});
 }
}
probe('invalid guard stdout cannot produce a succeeded guard receipt',()=>{
 const out=withGuardOutput(null,()=>runIntegratedCore(fresh()));
 assert.equal(out.receipts.guard.status,'FAILED');
 assert.equal(out.receipts.guard.exit_code,0);
 assert.equal(out.receipts.guard.error_code,'PYTHON_OUTPUT_CONTRACT_VIOLATION');
 assert.equal(out.status,'PARTIAL_STAGE_FAILURE');assert.equal(warnings(out).length,0);assert.equal(out.receipts.legacy.status,'SUCCEEDED');
});
probe('redundant held method basis does not erase an independent valid method warning',()=>{
 const p=fresh();rows(p)[8].question_id='FOREIGN-Q';p.project.sources['SOURCE-8'].question_id='FOREIGN-Q';
 rows(p).push({...structuredClone(rows(p)[7]),id:'O-METHOD-DEPENDENT',depends_on:['O-8']});
 const o=runIntegratedCore(p);assert(accepted(o).includes('O-7'));assert(held(o).includes('O-METHOD-DEPENDENT'));assert(warnings(o).includes(METHOD));
 const warning=o.report.procedural_warnings.find(w=>w.code===METHOD);assert.deepEqual(warning.basis_observations,['O-7']);
});
probe('redundant held circular basis does not erase valid three-kind warning or accountability action',()=>{
 const p=fresh();rows(p)[8].question_id='FOREIGN-Q';p.project.sources['SOURCE-8'].question_id='FOREIGN-Q';
 rows(p).push({...structuredClone(rows(p)[4]),id:'O-CONTROLLER-DEPENDENT',depends_on:['O-8']});
 const o=runIntegratedCore(p);assert(accepted(o).includes('O-4'));assert(held(o).includes('O-CONTROLLER-DEPENDENT'));assert(warnings(o).includes(CIRCULAR));assert(warnings(o).includes(CARTEL));
 assert(o.report.action_proposals.some(x=>x.action.includes('CONTROLLER')));
});
probe('well-formed envelope but malformed guard review output is a controlled stage failure preserving core',()=>{
 const reference=runIntegratedCore(fresh()).audit_only.guard_execution;reference.reviews=[{}];
 const out=withGuardOutput(reference,()=>runIntegratedCore(fresh()));
 assert.equal(out.receipts.guard.status,'FAILED');
 assert.equal(out.receipts.guard.exit_code,0);
 assert.equal(out.receipts.guard.error_code,'PYTHON_OUTPUT_CONTRACT_VIOLATION');
 assert.equal(out.status,'PARTIAL_STAGE_FAILURE');assert.equal(warnings(out).length,0);assert.equal(out.receipts.legacy.status,'SUCCEEDED');
});
const summary={schema:'INDEPENDENT-SYNTHETIC-INTEGRATION-AUDIT/1',tests:results.length,passed:results.filter(x=>x.status==='PASS').length,failed:results.filter(x=>x.status==='FAIL').length,results};
console.log(JSON.stringify(summary,null,2));process.exitCode=summary.failed?1:0;
