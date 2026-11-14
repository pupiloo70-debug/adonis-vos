import {createHash} from 'node:crypto';
import {Worker} from 'node:worker_threads';

const CAP = 65_536;
const sha = x => createHash('sha256').update(x).digest('hex');
const id = x => typeof x === 'string' && /^SYN-[A-Za-z0-9_-]{1,60}$/.test(x);
const digest = x => typeof x === 'string' && /^[a-fA-F0-9]{64}$/.test(x);
const exact = (x, keys) => x !== null && typeof x === 'object' && !Array.isArray(x)
  && Object.keys(x).length === keys.length && keys.every(k => Object.hasOwn(x,k));
const revisions = ['core','schema','rules','access','evidence'];

function check(x) {
  if (!exact(x,['case_id','external_status','evidence_manifest']) || !id(x.case_id)
    || !['OPEN','CLOSED','UNKNOWN'].includes(x.external_status)
    || !Array.isArray(x.evidence_manifest)) return 'SCHEMA_VIOLATION';
  if (x.evidence_manifest.length > 50) return 'EVIDENCE_ITEM_LIMIT';
  const ids = new Set();
  for (const v of x.evidence_manifest) {
    if (!exact(v,['doc_id','sha256','access_state']) || !id(v.doc_id) || ids.has(v.doc_id)
      || !['AVAILABLE','WITHHELD','MISSING_CLAIMED','CORRUPTED'].includes(v.access_state)
      || !(digest(v.sha256) || (v.sha256 === null && v.access_state !== 'AVAILABLE'))) return 'SCHEMA_VIOLATION';
    ids.add(v.doc_id);
  }
  return null;
}

export function createResearchGate({
  workerURL = new URL('./synthetic-worker.mjs',import.meta.url),
  timeoutMs = 500, maxActive = 1, maxQueued = 2, maxCached = 16
} = {}) {
  for (const [key,value,min,max] of [['timeoutMs',timeoutMs,1,60_000],['maxActive',maxActive,1,16],['maxQueued',maxQueued,0,64],['maxCached',maxCached,0,128]]) {
    if (!Number.isInteger(value) || value < min || value > max) throw new RangeError(key);
  }
  const queue = [], cache = new Map();
  let active = 0, runs = 0;
  const base = (x, context) => ({
    case_id:x?.case_id ?? null, external_status:x?.external_status ?? 'UNKNOWN',
    review_flags:[...(context?.reviewFlags ?? [])], human_verification_required:true,
    auto_certification_allowed:false, external_enforcement:false, total_score:null
  });
  const fail = (x,c,reason) => ({...base(x,c), request_status:reason==='QUEUE_CAPACITY_EXCEEDED'?'NOT_QUEUED':'UNVERIFIED',
    gate_status:'GATE_EXECUTION_UNVERIFIED', reason, retry_required:reason==='QUEUE_CAPACITY_EXCEEDED'});
  async function run(x,c,key){
    const existing = cache.get(key);
    if (existing) return {...structuredClone(existing), cache_hit:true};
    runs++;
    try {
      const result = await new Promise((resolve,reject) => {
        const w = new Worker(workerURL,{workerData:{scenario:c.scenario}});
        let done = false;
        const finish = (error,data) => {
          if(done) return;
          done = true;
          clearTimeout(timer);
          w.terminate().then(() => error ? reject(error) : resolve(data), () => reject({code:'WORKER_STOP_FAILED'}));
        };
        const timer = setTimeout(() => finish({code:'TIMEOUT'}), timeoutMs);
        w.once('message', data => finish(null,data));
        w.once('error', () => finish({code:'MODULE_EXCEPTION'}));
        w.once('exit', () => finish({code:'WORKER_EXIT_WITHOUT_RESULT'}));
      });
      if (result?.status !== 'READY_FOR_HUMAN_VERIFICATION') return fail(x,c,'MODULE_STATE_CONFLICT');
      const out = {...base(x,c), request_status:'REVIEW_REQUIRED', gate_status:result.status,cache_hit:false};
      if (maxCached > 0) {
        cache.set(key,structuredClone(out));
        if(cache.size>maxCached) cache.delete(cache.keys().next().value);
      }
      return out;
    } catch(e) {
      return fail(x,c,['TIMEOUT','MODULE_EXCEPTION','WORKER_EXIT_WITHOUT_RESULT','WORKER_STOP_FAILED'].includes(e?.code)?e.code:'INTERNAL_GATE_ERROR');
    }
  }
  function pump(){
    while (active < maxActive && queue.length) {
      const j=queue.shift();
      active++;
      void run(j.x,j.c,j.key).then(j.resolve,()=>j.resolve(fail(j.x,j.c,'INTERNAL_GATE_ERROR')))
        .finally(()=>{active--; pump();});
    }
  }
  async function evaluate(raw, trusted) {
    if(!Buffer.isBuffer(raw)) return fail(null,null,'EXPECTED_BYTES');
    if(raw.byteLength > CAP) return fail(null,null,'PAYLOAD_TOO_LARGE');
    let x;
    try { x=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)); }
    catch { return fail(null,null,'INVALID_JSON_OR_UTF8'); }
    const problem=check(x);
    if(problem) return fail(null,null,problem);
    if(!trusted || !revisions.every(k=>typeof trusted[k]==='string' && /^[A-Za-z0-9_.-]{1,64}$/.test(trusted[k]))
      || !['READY','HANG','THROW','CONFLICT'].includes(trusted.scenario)
      || !Array.isArray(trusted.reviewFlags) || trusted.reviewFlags.length>16
      || !trusted.reviewFlags.every(f=>typeof f==='string' && /^[A-Z_]{1,64}$/.test(f))) return fail(x,null,'TRUSTED_CONTEXT_REQUIRED');
    // Only the local synthetic adapter may supply this context; none of it is accepted from JSON.
    const c={...Object.fromEntries(revisions.map(k=>[k,trusted[k]])),scenario:trusted.scenario,reviewFlags:[...trusted.reviewFlags]};
    if (x.evidence_manifest.some(ref=>ref.access_state==='AVAILABLE' &&
       trusted.availableDigests?.get(ref.doc_id)?.toLowerCase()!==ref.sha256.toLowerCase())) return fail(x,c,'SOURCE_DIGEST_UNCONFIRMED');
    const stable=[x.case_id,x.external_status,x.evidence_manifest.map(v=>[v.doc_id,v.sha256?.toLowerCase()??null,v.access_state]),c];
    const key=sha(JSON.stringify(stable));
    const existing=cache.get(key);
    if(existing) return {...structuredClone(existing),cache_hit:true};
    if(active>=maxActive && queue.length>=maxQueued) return fail(x,c,'QUEUE_CAPACITY_EXCEEDED');
    return new Promise(resolve=>{queue.push({x,c,key,resolve});pump();});
  }
  return {evaluate, stats:()=>({active,queued:queue.length,runs,cached:cache.size})};
}
