import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,writeFileSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {validateProject,importProject,exportProject,analyzeProject,MAX_BYTES} from '../src/project.mjs';
import {CentralCore} from '../src/agents.mjs';
const fixture=()=>JSON.parse(readFileSync(new URL('../examples/synthetic-project.json',import.meta.url),'utf8'));
test('partial A provision leaves B missing and both questions unresolved',()=>{
 const r=analyzeProject(fixture());assert.equal(r.rows[0].provision_status,'PARTIAL_REPORTED');assert.equal(r.rows[1].provision_status,'NOT_PROVIDED');assert.ok(r.rows.every(x=>x.resolution.startsWith('UNRESOLVED')));assert.equal(r.total_score,null);
});
test('reported FULL is not content verification',()=>{let p=fixture();p.supplies[0].coverage='FULL';assert.equal(analyzeProject(p).rows[0].resolution,'UNRESOLVED_REQUIRES_CONTENT_REVIEW');});
test('cannot supply an item outside its request',()=>{let p=fixture();p.supplies[0].item_id='WRONG';assert.throws(()=>validateProject(p),/SUPPLY_SCOPE/);});
test('duplicate source IDs rejected',()=>{let p=fixture();p.sources.push({...p.sources[0]});assert.throws(()=>validateProject(p),/DUPLICATE/);});
test('dangling answer references rejected',()=>{let p=fixture();p.answers.record_access.refs=['MISSING'];assert.throws(()=>validateProject(p),/REFERENCE/);});
test('unknown answer keys rejected rather than discarded',()=>{let p=fixture();p.answers.extra={value:'YES',basis:'USER_REPORT',refs:[]};assert.throws(()=>validateProject(p),/INVALID_ANSWER/);});
test('unreviewed stigma observation cannot become evidence linked',()=>{let p=fixture();p.observations[0].review='REVIEWED';assert.equal(analyzeProject(p).ethics[0].status,'REVIEW_PENDING');});
test('content reviewed basis supports a review record, never guilt',()=>{let p=fixture();p.sources[0].review='CONTENT_REVIEWED';p.sources[0].review_note='synthetic text compared';p.observations[0].review='REVIEWED';let x=analyzeProject(p).ethics[0];assert.equal(x.status,'EVIDENCE_LINKED_REVIEW');assert.equal(x.adjudication,'NO_AUTOMATIC_FINAL_FINDING');});
test('withdrawn observation remains in output with references',()=>{let p=fixture();p.observations[0].review='WITHDRAWN';assert.equal(analyzeProject(p).ethics[0].status,'WITHDRAWN');});
test('observation without evidence rejected',()=>{let p=fixture();p.observations[0].source_refs=[];assert.throws(()=>validateProject(p),/EVIDENCE/);});
test('destroyed source cannot be silently marked read',()=>{let p=fixture();p.sources[0].state='DESTROYED';p.sources[0].review='READ';assert.throws(()=>validateProject(p),/INACCESSIBLE/);});
test('unknown remains distinct from NO',()=>{let p=fixture();p.answers.record_access.value='UNKNOWN';assert.equal(analyzeProject(p).core.items[0].status,'NEEDS_CHECK');});
test('analysis preserves original input and unknown narrative metadata',()=>{let p=fixture();p.belief_narrative={text:'<script>untrusted text</script>'};let before=JSON.stringify(p);assert.deepEqual(importProject(exportProject(p)),p);let r=analyzeProject(p);assert.equal(JSON.stringify(p),before);assert.deepEqual(r.original_project.belief_narrative,p.belief_narrative);assert.ok(r.action_drafts.every(x=>x.delivery==='NOT_SENT'&&x.assigned_role!=='VICTIM'));});
test('unsupported version and oversized import rejected',()=>{let p=fixture();p.schema='FUTURE';assert.throws(()=>importProject(JSON.stringify(p)),/PROJECT/);assert.throws(()=>importProject(' '.repeat(MAX_BYTES+1)),/SIZE/);});
const a={id:'Grok',connection:'INTENT_RECEIVED',layer:'DESIGN',capabilities:['SOURCE_REVIEW']};
const local={id:'local',connection:'LOCAL_ADAPTER_CONFIGURED',layer:'EXECUTION',runtime_ref:'src/project.mjs',capabilities:['LOCAL_RULE_EVALUATION']};
test('named willingness cannot be dispatched as connected agent',()=>{let c=new CentralCore();c.register(a);assert.throws(()=>c.assign({id:'t',agent_id:'Grok',capability:'SOURCE_REVIEW'}),/INTENT_IS_NOT_RUNTIME/);});
test('bounded local assignment is recorded as not executed',()=>{let c=new CentralCore();c.register(local);c.assign({id:'t',agent_id:'local',capability:'LOCAL_RULE_EVALUATION'});assert.equal(c.snapshot().tasks[0].state,'ASSIGNED_NOT_EXECUTED');assert.equal(c.snapshot().external_api_calls,0);});
test('capability mismatch is denied',()=>{let c=new CentralCore();c.register(local);assert.throws(()=>c.assign({id:'t',agent_id:'local',capability:'SOURCE_REVIEW'}),/CAPABILITY/);});
test('resource limits and duplicate task IDs enforced',()=>{let c=new CentralCore({maxAgents:1,maxTasks:1});c.register(local);assert.throws(()=>c.register(a),/LIMIT/);c.assign({id:'t',agent_id:'local',capability:'LOCAL_RULE_EVALUATION'});assert.throws(()=>c.assign({id:'t',agent_id:'local',capability:'LOCAL_RULE_EVALUATION'}),/INVALID_TASK/);assert.throws(()=>c.assign({id:'t2',agent_id:'local',capability:'LOCAL_RULE_EVALUATION'}),/TASK_LIMIT/);});
test('suspension holds queued tasks and denies further assignment',()=>{let c=new CentralCore();c.register(local);c.assign({id:'t',agent_id:'local',capability:'LOCAL_RULE_EVALUATION'});c.suspend('local');assert.equal(c.snapshot().tasks[0].state,'ON_HOLD');assert.throws(()=>c.assign({id:'t2',agent_id:'local',capability:'LOCAL_RULE_EVALUATION'}),/UNAVAILABLE/);});
test('registry cannot promote narrative into execution by assertion',()=>{let c=new CentralCore();assert.throws(()=>c.register({...local,layer:'BELIEF_NARRATIVE'}),/RUNTIME/);assert.throws(()=>c.register({...local,runtime_ref:''}),/RUNTIME/);});
test('snapshot cannot mutate coordinator',()=>{let c=new CentralCore();c.register(local);let s=c.snapshot();s.agents[0].state='SUSPENDED';assert.equal(c.snapshot().agents[0].state,'ACTIVE');});
test('central core actually executes built-in task and emits content hashes',()=>{let c=new CentralCore();c.register(local);c.assign({id:'t',agent_id:'local',capability:'LOCAL_RULE_EVALUATION'});let r=c.runLocal('t',fixture());assert.equal(r.receipt.status,'SUCCEEDED');assert.match(r.receipt.input_sha256,/^[a-f0-9]{64}$/);assert.equal(r.result.total_score,null);assert.equal(c.snapshot().tasks[0].state,'SUCCEEDED');assert.throws(()=>c.runLocal('t',fixture()),/NOT_RUNNABLE/);});
test('invalid local task input records failure rather than success',()=>{let c=new CentralCore();c.register(local);c.assign({id:'t',agent_id:'local',capability:'LOCAL_RULE_EVALUATION'});assert.throws(()=>c.runLocal('t',{}),/PROJECT/);assert.equal(c.snapshot().tasks[0].state,'FAILED');});
test('CLI JSON roundtrip, no overwrite, malformed input failure',()=>{
 const d=mkdtempSync(join(tmpdir(),'vos02-'));try{
 const input=join(d,'in.json'),out=join(d,'out.json');writeFileSync(input,exportProject(fixture()));
 const cli=new URL('../src/cli.mjs',import.meta.url).pathname;
 const run=(...args)=>spawnSync(process.execPath,[cli,...args],{encoding:'utf8'});
 assert.equal(run(input,out).status,0);assert.ok(existsSync(out));assert.equal(JSON.parse(readFileSync(out)).total_score,null);
 const original=readFileSync(out,'utf8');assert.notEqual(run(input,out).status,0);assert.equal(readFileSync(out,'utf8'),original);assert.notEqual(run(input,input).status,0);
 writeFileSync(input,'{broken');assert.notEqual(run(input).status,0);
 } finally{rmSync(d,{recursive:true});}
});
