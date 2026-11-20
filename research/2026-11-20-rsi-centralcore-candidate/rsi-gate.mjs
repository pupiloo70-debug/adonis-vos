/** Research-only rights-preserving self-improvement gate. No default-path or remote actions. */
import { createHash } from 'node:crypto';
import { CentralCore } from '../../src/agents.mjs';

export const STATUS = Object.freeze({ design: 'RESEARCH_CANDIDATE', default_path_connected: false,
  production_released: false, policy_release_046: false, r3_final_authority: true,
  total_score: null, automated_adjudication: false });
export const sha256 = x => createHash('sha256').update(typeof x === 'string' ? x : JSON.stringify(x)).digest('hex');
const object = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const ALLOWED = new Set(['REQUEST','NOT_PROVIDED','PROVIDED','CONTROLLER_EXPLANATION','FORMAL_CLOSURE',
  'REMEDY_REPORTED','REMEDY_CONFIRMED','INDEPENDENT_DISSENT','CORRECTION_REPORTED',
  'AUTHORITY_OVERRIDE','TECH_SINGULARITY_CLAIM','MISSING_REPORT']);
const MAX_BYTES = 256 * 1024;

function checkInput(input) {
  if (!object(input) || input.synthetic !== true || input.schema !== 'ADONIS-RSI/SYNTHETIC-1') throw Error('SYNTHETIC_ONLY');
  if (Buffer.byteLength(JSON.stringify(input)) > MAX_BYTES) throw Error('PAYLOAD_LIMIT');
  if (!object(input.project) || !input.project.id?.startsWith('SYNTHETIC-')) throw Error('SYNTHETIC_PROJECT_REQUIRED');
  if (!Array.isArray(input.events) || input.events.length > 128 || !Array.isArray(input.sources) || input.sources.length > 128) throw Error('BOUNDED_INPUT_REQUIRED');
  const sources = new Set();
  for (const s of input.sources) {
    if (!object(s) || typeof s.id !== 'string' || sources.has(s.id) || !['CLAIM_ONLY','RECORD_LINKED','INDEPENDENTLY_REVIEWED'].includes(s.status)) throw Error('INVALID_SOURCE');
    sources.add(s.id);
  }
  const ids = new Set();
  for (const event of input.events) {
    if (!object(event) || typeof event.id !== 'string' || ids.has(event.id) || !ALLOWED.has(event.type) ||
        typeof event.question_id !== 'string' || !Array.isArray(event.source_refs) ||
        event.source_refs.some(r => !sources.has(r))) throw Error('INVALID_EVENT');
    ids.add(event.id);
  }
}

export function runSyntheticRSICycle(input) {
  // Fail closed on untrusted input, while preserving independent evidence in the caller's custody.
  checkInput(input);
  const inputHash = sha256(input);
  const core = new CentralCore({maxAgents: 1, maxTasks: 1});
  core.register({id:'ADONIS-LOCAL',layer:'EXECUTION',connection:'LOCAL_ADAPTER_CONFIGURED',
    runtime_ref:'src/project.mjs',capabilities:['LOCAL_RULE_EVALUATION']});
  core.assign({id:'SYNTHETIC-RSI-CORE',agent_id:'ADONIS-LOCAL',capability:'LOCAL_RULE_EVALUATION'});
  let executed;
  try { executed = core.runLocal('SYNTHETIC-RSI-CORE', input.project); }
  catch (err) { return {status:'GATE_EXECUTION_UNVERIFIED',reason:'CENTRALCORE_FAILURE',
    input_sha256:inputHash,output_sha256:null,total_score:null,default_path_connected:false,
    receipts:{centralcore:null},proposals:[],unverified:[String(err.message)]}; }
  if (executed.receipt.status !== 'SUCCEEDED' || executed.receipt.input_sha256 !== sha256(input.project) ||
      executed.receipt.output_sha256 !== sha256(executed.result) || executed.result.total_score !== null) {
    return {status:'GATE_EXECUTION_UNVERIFIED',reason:'RECEIPT_OR_CONTRACT_MISMATCH',
      input_sha256:inputHash,output_sha256:null,total_score:null,default_path_connected:false,
      receipts:{centralcore:executed.receipt},proposals:[],unverified:['CENTRALCORE_RECEIPT']};
  }
  const byQuestion = new Map();
  for (const e of input.events) {
    if (!byQuestion.has(e.question_id)) byQuestion.set(e.question_id,[]);
    byQuestion.get(e.question_id).push(e);
  }
  const findings = [];
  const proposals = [];
  for (const [question_id, events] of byQuestion) {
    const types = new Set(events.map(e => e.type));
    const reasons = [];
    if (types.has('NOT_PROVIDED') && (types.has('FORMAL_CLOSURE') || types.has('MISSING_REPORT'))) reasons.push('CIRCULAR_JUSTIFICATION_REVIEW');
    if (types.has('FORMAL_CLOSURE') && !types.has('REMEDY_CONFIRMED')) reasons.push('FORMAL_CLOSURE_NOT_SUBSTANTIVE_REMEDY');
    if (types.has('REMEDY_REPORTED') && !types.has('REMEDY_CONFIRMED')) reasons.push('BENEFIT_SOURCE_UNVERIFIED');
    if (types.has('AUTHORITY_OVERRIDE')) reasons.push('AUTHORITY_OVERRIDE_REJECTED');
    if (types.has('TECH_SINGULARITY_CLAIM')) reasons.push('ETHICAL_PRIORITY_NOT_TECH_CERTIFICATION');
    if (types.has('INDEPENDENT_DISSENT')) reasons.push('INDEPENDENT_DISSENT_PRESERVED');
    if (types.has('CORRECTION_REPORTED')) reasons.push('CORRECTION_REQUIRES_VERIFICATION');
    if (types.has('PROVIDED') && !events.some(e => e.type==='PROVIDED' && e.source_refs.some(ref =>
        input.sources.some(s => s.id===ref && s.status==='INDEPENDENTLY_REVIEWED')))) reasons.push('SUPPLY_NOT_INDEPENDENT_VERIFICATION');
    if (types.has('REQUEST') && !types.has('PROVIDED')) reasons.push('CONTROLLER_EXPLANATION_PENDING');
    const refs = [...new Set(events.flatMap(e=>e.source_refs))];
    findings.push({question_id,status:'REVIEW_OPEN',reasons,source_refs:refs,
      independent_dissent_ids:events.filter(e=>e.type==='INDEPENDENT_DISSENT').map(e=>e.id)});
    for (const reason of reasons) proposals.push({question_id,reason,status:'PROPOSED_NOT_ADOPTED',
      responsible_role:'TECHNICAL_REVIEW_UNASSIGNED',r3_approval_required_for_policy_change:true});
  }
  const body = {schema:'ADONIS-RSI-REPORT/0.1',mode:'SYNTHETIC_RESEARCH_ONLY',
    status:'RESEARCH_REVIEW_OPEN',default_path_connected:false,production_released:false,
    total_score:null,axioms:'AX-01..09_UNCHANGED',civic_trace:'0.4.5_ONLY',civic_trace_046:'R3_RELEASE_NOT_APPROVED',
    no_legal_or_medical_adjudication:true,findings,proposals,
    core:{receipt:executed.receipt,version:executed.result.version,output_sha256:sha256(executed.result)},
    input_sha256:inputHash};
  return {...body,output_sha256:sha256(body)};
}

/** Compare a proposed research revision against the previous result.
 * Value regression and technical regression are independent hard vetoes, never summed.
 * This only returns a recommendation, never modifies source code or approval state.
 */
export function compareResearchRevision(previous, proposed, {technical_tests_passed=false}={}) {
  const problems = [];
  for (const [label, value] of [['previous',previous],['proposed',proposed]]) {
    if (!object(value) || value.schema !== 'ADONIS-RSI-REPORT/0.1' ||
        value.total_score !== null || value.default_path_connected !== false ||
        value.no_legal_or_medical_adjudication !== true ||
        value.civic_trace_046 !== 'R3_RELEASE_NOT_APPROVED') problems.push(`${label.toUpperCase()}_CONTRACT_INVALID`);
  }
  if (problems.length) return {status:'ADOPTION_HELD',reasons:problems,requires_r3_review:true};
  const oldMap = new Map(previous.findings.map(f=>[f.question_id,f]));
  const newMap = new Map(proposed.findings.map(f=>[f.question_id,f]));
  for (const [id, before] of oldMap) {
    const after = newMap.get(id);
    if (!after) {problems.push('QUESTION_DROPPED:'+id);continue;}
    for (const dissent of before.independent_dissent_ids) {
      if (!after.independent_dissent_ids.includes(dissent)) problems.push('DISSENT_DROPPED:'+id+':'+dissent);
    }
    for (const ref of before.source_refs) {
      if (!after.source_refs.includes(ref)) problems.push('SOURCE_DROPPED:'+id+':'+ref);
    }
  }
  if (!technical_tests_passed) problems.push('TECHNICAL_TESTS_UNVERIFIED');
  return {status:problems.length?'ADOPTION_HELD':'RESEARCH_REVIEW_READY',reasons:problems,
    requires_r3_review:true,auto_merge:false,auto_release:false,total_score:null};
}
