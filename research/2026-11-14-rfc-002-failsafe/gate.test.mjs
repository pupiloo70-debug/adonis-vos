import test from 'node:test';
import assert from 'node:assert/strict';
import {createResearchGate} from './gate.mjs';

const key = 'a'.repeat(64);
const input = {case_id:'SYN-001',external_status:'CLOSED',
  evidence_manifest:[{doc_id:'SYN-DOC-01',sha256:key,access_state:'AVAILABLE'}]};
const bytes = (x=input) => Buffer.from(JSON.stringify(x));
const trusted = {core:'fixture-1',schema:'rfc002-1',rules:'test-1',access:'a1',evidence:'e1',
  scenario:'READY',reviewFlags:['CONTROLLER_EXPLANATION_REVIEW'],availableDigests:new Map([['SYN-DOC-01',key]])};
function held(r,why,parsed=true){
  assert.equal(r.gate_status,'GATE_EXECUTION_UNVERIFIED');
  assert.equal(r.reason,why);
  assert.equal(r.external_status,parsed?'CLOSED':'UNKNOWN');
  assert.equal(r.auto_certification_allowed,false);
  assert.equal(r.external_enforcement,false);
  assert.equal(r.human_verification_required,true);
  assert.equal(r.total_score,null);
}

test('1. overflow: exact 64 KiB accepted; 64 KiB + 1 and 51 evidence entries rejected',async()=>{
  const g=createResearchGate();
  const pad = Buffer.alloc(65536-bytes().length,0x20);
  assert.equal((await g.evaluate(Buffer.concat([bytes(),pad]),trusted)).gate_status,'READY_FOR_HUMAN_VERIFICATION');
  held(await g.evaluate(Buffer.concat([bytes(),pad,Buffer.from(' ')]),trusted),'PAYLOAD_TOO_LARGE',false);
  const evidence_manifest=Array.from({length:51},(_,i)=>({...input.evidence_manifest[0],doc_id:'SYN-D'+i}));
  held(await g.evaluate(bytes({...input,evidence_manifest}),trusted),'EVIDENCE_ITEM_LIMIT',false);
  assert.equal(g.stats().runs,1);
});

test('2. invalid schema/digest: no work on invalid input; revision-bound result cache',async()=>{
  const g=createResearchGate();
  const evidence_manifest=[{...input.evidence_manifest[0],raw_document:'forbidden'}];
  held(await g.evaluate(bytes({...input,evidence_manifest}),trusted),'SCHEMA_VIOLATION',false);
  held(await g.evaluate(bytes(),{...trusted,availableDigests:new Map()}),'SOURCE_DIGEST_UNCONFIRMED');
  assert.equal(g.stats().runs,0);
  assert.equal((await g.evaluate(bytes(),trusted)).cache_hit,false);
  assert.equal((await g.evaluate(bytes(),trusted)).cache_hit,true);
  assert.equal((await g.evaluate(bytes(),{...trusted,access:'a2'})).cache_hit,false);
  held(await g.evaluate(bytes(),{...trusted,availableDigests:new Map()}),'SOURCE_DIGEST_UNCONFIRMED');
  assert.equal(g.stats().runs,2);
});

test('3. timeout: terminate the synthetic worker, preserve reasons, and continue processing',async()=>{
  const g=createResearchGate({timeoutMs:500});
  const r=await g.evaluate(bytes(),{...trusted,scenario:'HANG'});
  held(r,'TIMEOUT');
  assert.deepEqual(r.review_flags,trusted.reviewFlags);
  assert.equal((await g.evaluate(bytes(),trusted)).gate_status,'READY_FOR_HUMAN_VERIFICATION');
});

test('4. module conflict or exception: neither can certify, and formal closure stays separate',async()=>{
  const g=createResearchGate();
  for(const [scenario,reason] of [['THROW','MODULE_EXCEPTION'],['CONFLICT','MODULE_STATE_CONFLICT']]){
    const r=await g.evaluate(bytes(),{...trusted,scenario});
    held(r,reason);
    assert.deepEqual(r.review_flags,trusted.reviewFlags);
  }
  assert.equal(g.stats().cached,0);
});

test('5. bounded FIFO: explicit not-queued outcome, with retry required',async()=>{
  const g=createResearchGate({maxActive:1,maxQueued:2,timeoutMs:500});
  const order=[];
  const a=g.evaluate(bytes(),{...trusted,scenario:'HANG'});
  const b=g.evaluate(bytes({...input,case_id:'SYN-002'}),trusted).then(r=>order.push(r.case_id));
  const c=g.evaluate(bytes({...input,case_id:'SYN-003'}),trusted).then(r=>order.push(r.case_id));
  const overflow=await g.evaluate(bytes({...input,case_id:'SYN-004'}),trusted);
  held(overflow,'QUEUE_CAPACITY_EXCEEDED');
  assert.equal(overflow.request_status,'NOT_QUEUED');
  assert.equal(overflow.retry_required,true);
  assert.deepEqual(overflow.review_flags,trusted.reviewFlags);
  held(await a,'TIMEOUT');
  await Promise.all([b,c]);
  assert.deepEqual(order,['SYN-002','SYN-003']);
  assert.equal((await g.evaluate(bytes({...input,case_id:'SYN-004'}),trusted)).case_id,'SYN-004');
});
