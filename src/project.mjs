import { evaluate } from './engine.mjs';

export const VERSION = '0.2.0-draft';
export const MAX_BYTES = 2 * 1024 * 1024;
const STATES = ['NOT_SEARCHED','ACCESS_RESTRICTED','SUBMISSION_REFUSED','LOST','DESTROYED','NONEXISTENCE_REPORTED','UNKNOWN','AVAILABLE'];
const ACTIONS = {
  VERIFICATION_REQUEST_BLOCKED:'VICTIM_VERIFICATION_VOICE_RESTRICTION_WARNING',
  ASYMMETRY_OMITTED:'EVIDENCE_ASYMMETRY_OMITTED',
  LOSS_AS_VICTIM_FAILURE:'VERIFICATION_LOSS_RECAST_AS_VICTIM_FAILURE',
  UNSUPPORTED_STIGMA:'UNSUPPORTED_STIGMATIZATION_REVIEW',
  AUTHORITY_AS_PROOF:'AUTHORITY_SUBSTITUTED_FOR_VERIFICATION'
};
const fail = s => { throw new Error(s); };
const obj = x => x && typeof x==='object' && !Array.isArray(x);
const text = x => typeof x==='string' && x.trim().length>0;
function list(x, name) { if(!Array.isArray(x)) fail('INVALID_LIST:'+name); return x; }
function index(xs, name) {
  const m=new Map();
  for(const x of list(xs,name)) {
    if(!obj(x)||!text(x.id)||m.has(x.id)) fail('INVALID_OR_DUPLICATE_ID:'+name);
    m.set(x.id,x);
  }
  return m;
}
function refs(xs, m, name) {
  if(!Array.isArray(xs)||new Set(xs).size!==xs.length||xs.some(x=>!text(x)||!m.has(x))) fail('INVALID_REFERENCE:'+name);
}
export function validateProject(p) {
  if(!obj(p)||p.schema!=='ADONIS-VOS-PROJECT/0.2'||!text(p.id)||!obj(p.answers)) fail('INVALID_PROJECT');
  const sources=index(p.sources,'sources'), requests=index(p.requests,'requests');
  index(p.supplies,'supplies');index(p.observations,'observations');
  for(const s of sources.values()) {
    if(!STATES.includes(s.state)||!['REGISTERED','READ','CONTENT_REVIEWED'].includes(s.review)) fail('INVALID_SOURCE');
    if(s.state!=='AVAILABLE'&&s.review!=='REGISTERED') fail('INACCESSIBLE_SOURCE_REVIEW');
    if(s.review!=='REGISTERED'&&!text(s.review_note)) fail('MISSING_REVIEW_NOTE');
  }
  const fields=['record_access','record_loss','procedure_delay','criteria_change','reason_gap','access_inequality','preservation_risk'];
  for(const [field,a] of Object.entries(p.answers)) { if(!fields.includes(field)||!obj(a))fail('INVALID_ANSWER'); refs(a.refs,sources,'answers'); }
  evaluate(p.answers);
  for(const r of requests.values()) {
    if(!text(r.question)||!text(r.controller)||!Array.isArray(r.items)||!r.items.length||r.items.some(x=>!text(x))||new Set(r.items).size!==r.items.length) fail('INVALID_REQUEST');
    refs(r.source_refs,sources,'request');
  }
  for(const s of p.supplies) {
    if(!requests.has(s.request_id)||!requests.get(s.request_id).items.includes(s.item_id)||!sources.has(s.source_id))fail('SUPPLY_SCOPE_MISMATCH');
    if(!['FULL','PARTIAL','SUBSTITUTE','UNKNOWN'].includes(s.coverage))fail('INVALID_COVERAGE');
  }
  for(const o of p.observations) {
    if(!Object.hasOwn(ACTIONS,o.action)||!text(o.request_excerpt)||!text(o.response_excerpt)||!text(o.review_note)||!['REPORTED','REVIEWED','WITHDRAWN'].includes(o.review)) fail('INVALID_OBSERVATION');
    if(!o.source_refs?.length)fail('MISSING_OBSERVATION_EVIDENCE');
    refs(o.source_refs,sources,'observation');
  }
  return p;
}
export function importProject(raw) {
  if(typeof raw!=='string'||Buffer.byteLength(raw,'utf8')>MAX_BYTES)fail('IMPORT_SIZE_OR_TYPE');
  return validateProject(JSON.parse(raw));
}
export function exportProject(p) { validateProject(p);return JSON.stringify(p,null,2)+'\n'; }
export function analyzeProject(input) {
  const p=validateProject(input), sources=new Map(p.sources.map(s=>[s.id,s]));
  const rows=p.requests.flatMap(r=>r.items.map(item=>{
    const supplied=p.supplies.filter(s=>s.request_id===r.id&&s.item_id===item);
    // Provision does not prove that the question has been answered.
    return {request_id:r.id,item_id:item,controller_reported:r.controller,
      provision_status:!supplied.length?'NOT_PROVIDED':supplied.some(s=>s.coverage==='FULL')?'FULL_REPORTED':supplied.some(s=>s.coverage==='PARTIAL')?'PARTIAL_REPORTED':'SCOPE_REVIEW_REQUIRED',
      supply_refs:supplied.map(s=>s.id),source_states:supplied.map(s=>sources.get(s.source_id).state),
      resolution:'UNRESOLVED_REQUIRES_CONTENT_REVIEW',question:r.question,
      next_task:!supplied.length?'AI_PREPARE_CONTROLLER_EXPLANATION_REQUEST':'AI_COMPARE_CONTENT_AND_REMAINING_QUESTIONS'};
  }));
  const ethics=p.observations.map(o=>({observation_id:o.id,tag:ACTIONS[o.action],
    status:o.review==='WITHDRAWN'?'WITHDRAWN':o.review==='REVIEWED'&&o.source_refs.every(id=>sources.get(id).review==='CONTENT_REVIEWED')?'EVIDENCE_LINKED_REVIEW':'REVIEW_PENDING',
    review_note:o.review_note,source_refs:[...o.source_refs],
    correction_status:o.review==='WITHDRAWN'?'NOT_REQUIRED':'DRAFT_REVIEW_REQUIRED',
    adjudication:'NO_AUTOMATIC_FINAL_FINDING'}));
  return {schema:'ADONIS-VOS-REPORT/0.2',project_id:p.id,version:VERSION,
    score:null,total_score:null,core:evaluate(p.answers),rows,ethics,
    action_drafts:rows.map(r=>({request_id:r.request_id,item_id:r.item_id,controller_reported:r.controller_reported,
      assigned_role:'ADONIS_AI_TECHNICAL_SUPPORT',action:r.next_task,status:'DRAFTED',delivery:'NOT_SENT'})),
    inference:{medical_causality:'NOT_ADJUDICATED',legal_liability:'NOT_ADJUDICATED'},
    original_project:structuredClone(p)};
}
