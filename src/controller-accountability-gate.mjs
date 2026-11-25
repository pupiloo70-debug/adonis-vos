/**
 * Controller Accountability Gate 01 — synthetic research only.
 * Detects evidence-control asymmetry; does not adjudicate misconduct or impose penalties.
 * Standalone explicit opt-in. Never auto-dispatches or changes the 0.2 core.
 */
import { normalizeP02SyntheticInput } from './p02-input-boundary.mjs';

export const CONTROLLER_GATE_STATUS = Object.freeze({
  version: 'CAG-01/0.1-research',
  research_only: true,
  default_core_connected: false,
  released: false,
  human_r3_approval_required: true,
  automatic_guilt: false,
  automatic_immunity: false,
  automatic_sanction: false,
  automatic_causality: false
});
const STATES = new Set(['NOT_REQUESTED','REQUESTED','PARTIAL','PROVIDED','REFUSED','REPORTED_MISSING','REPORTED_DESTROYED','UNKNOWN']);
const DUTIES = new Set(['UNASSESSED','ASSERTED','DOCUMENTED','INDEPENDENTLY_REVIEWED','NOT_APPLICABLE']);
const EVIDENCE = new Set(['CLAIM_ONLY','DOCUMENT_LINKED','INDEPENDENTLY_CHECKED']);
const OBSTRUCTION = new Set(['NONE_REPORTED','NON_RESPONSE','ACCESS_RESTRICTION','PRESERVATION_GAP','CONFLICT_OF_INTEREST_CONCERN','AUTHORITY_AS_EVIDENCE']);
const OWN = (obj,key) => Object.hasOwn(obj,key);
const validText = x => typeof x === 'string' && x.trim().length > 0;
const fail = code => { throw new Error(code); };
const exactKeys = (obj, allowed) => Object.keys(obj).every(k => allowed.includes(k));

/** All input is synthetic and normalized by the same 2 MiB P02 boundary guard. */
export function reviewControllerAccountability(raw) {
  const input = normalizeP02SyntheticInput(raw);
  if (input.schema !== 'ADONIS-0.3-CONTEXT/SYNTHETIC-1' || !validText(input.case_id)) fail('CAG_INVALID_CASE');
  if (!Array.isArray(input.controller_items)) fail('CAG_INVALID_ITEMS');
  if (!exactKeys(input,['schema','synthetic','case_id','controller_items'])) fail('CAG_UNEXPECTED_TOP_LEVEL_FIELD');
  const seen = new Set();
  const results = [];
  const actions = [];
  for (const row of input.controller_items) {
    if (!row || Array.isArray(row) || typeof row !== 'object' ||
        !exactKeys(row,['id','case_id','controller_id','requested_material','request_state','duty_status','evidence_status','source_refs','obstruction_type','explanation','independent_access','legitimate_limitations','response_verified'])) fail('CAG_INVALID_ITEM_SHAPE');
    if (!validText(row.id) || seen.has(row.id)) fail('CAG_DUPLICATE_OR_INVALID_ID');
    seen.add(row.id);
    if (OWN(row,'case_id') && row.case_id !== input.case_id) fail('CAG_CROSS_CASE_ITEM');
    if (![row.controller_id,row.requested_material].every(validText) ||
        !STATES.has(row.request_state) || !DUTIES.has(row.duty_status) ||
        !EVIDENCE.has(row.evidence_status) || !OBSTRUCTION.has(row.obstruction_type) ||
        !Array.isArray(row.source_refs) || row.source_refs.some(x=>!validText(x)) ||
        new Set(row.source_refs).size !== row.source_refs.length ||
        !['YES','NO','UNKNOWN'].includes(row.independent_access) ||
        !['YES','NO','UNKNOWN'].includes(row.response_verified) ||
        !['NONE_REPORTED','REPORTED','DOCUMENTED','REVIEWED'].includes(row.legitimate_limitations) ||
        !(row.explanation === null || validText(row.explanation))) fail('CAG_INVALID_ITEM');
    if (row.evidence_status !== 'CLAIM_ONLY' && row.source_refs.length === 0) fail('CAG_MISSING_EVIDENCE_REFERENCE');
    // Source identifiers are not source authentication. Never infer a legal breach from a label.
    const sourceLinked = row.evidence_status !== 'CLAIM_ONLY' && row.source_refs.length > 0;
    const actualGap = ['REQUESTED','PARTIAL','REFUSED','REPORTED_MISSING','REPORTED_DESTROYED','UNKNOWN'].includes(row.request_state) || row.independent_access === 'NO';
    const assertedObstruction = row.obstruction_type !== 'NONE_REPORTED';
    const reviewedDuty = row.duty_status === 'INDEPENDENTLY_REVIEWED';
    const materialUnverified = !sourceLinked || row.response_verified !== 'YES' || row.independent_access !== 'YES';
    const needsReview = actualGap || assertedObstruction || row.legitimate_limitations !== 'NONE_REPORTED';
    const cert = materialUnverified ? 'NOT_CERTIFIED' : 'ITEM_VERIFICATION_ELIGIBLE_FOR_HUMAN_REVIEW';
    const controllerReview = !needsReview ? 'NO_GAP_IDENTIFIED_FROM_INPUT' : !sourceLinked ? 'ALLEGATION_REQUIRES_DOCUMENTS' : 'EVIDENCE_LINKED_EXPLANATION_REVIEW';
    const legalEscalation = actualGap && sourceLinked && reviewedDuty ? 'LEGAL_REMEDY_REVIEW_CANDIDATE' : 'NO_AUTOMATIC_LEGAL_INFERENCE';
    const humanTasks = [];
    if (actualGap) humanTasks.push('REQUEST_ITEMIZED_CONTROLLER_EXPLANATION');
    if (['REPORTED_MISSING','REPORTED_DESTROYED'].includes(row.request_state)) humanTasks.push('REVIEW_EVIDENCE_PRESERVATION');
    if (assertedObstruction) humanTasks.push('REVIEW_REPORTED_VERIFICATION_OBSTRUCTION');
    if (row.legitimate_limitations !== 'NONE_REPORTED') humanTasks.push('REVIEW_LAWFUL_NONDISCLOSURE_GROUNDS');
    if (actualGap && row.independent_access !== 'YES') humanTasks.push('REQUEST_INDEPENDENT_REVIEW_PATH');
    if (legalEscalation === 'LEGAL_REMEDY_REVIEW_CANDIDATE') humanTasks.push('COUNSEL_REVIEW_PROCEDURAL_REMEDIES');
    const item = {
      id:row.id, controller_id:row.controller_id, requested_material:row.requested_material,
      reported_request_state:row.request_state, duty_status:row.duty_status, evidence_status:row.evidence_status,
      source_refs:[...row.source_refs], certification:cert, controller_review:controllerReview,
      legal_escalation:legalEscalation, independent_access:row.independent_access,
      legitimate_limitations:row.legitimate_limitations,
      claimant_proof_failure:'NOT_INFERRED', wrongfulness:'NOT_ADJUDICATED', collusion:'NOT_ESTABLISHED',
      exoneration:'NOT_AUTOMATIC', explanation:row.explanation, human_review_tasks:humanTasks
    };
    results.push(item);
    for(const action of humanTasks) actions.push({item_id:row.id,action,status:'DRAFT_ONLY',delivery:'NOT_SENT',legal_effect:'NONE'});
  }
  return {
    schema:'ADONIS-CONTROLLER-ACCOUNTABILITY-REVIEW/RESEARCH-1', version:CONTROLLER_GATE_STATUS.version,
    case_id:input.case_id, total_score:null, score:null, mode:'SYNTHETIC_RESEARCH_ONLY',
    source_authentication:false, entries:results, action_drafts:actions,
    system_certification:'NOT_GLOBALLY_CERTIFIED',
    decision_boundaries:{ automatic_guilt:false, automatic_immunity:false, automatic_sanction:false,
      automatic_causality:false, adverse_inference:'LEGAL_REVIEW_ONLY', release:'NOT_APPROVED', dispatch:'NOT_SENT', r3_approval_required:true }
  };
}
