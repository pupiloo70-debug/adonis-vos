// Adonis VOS 0.3 purpose-function research overlay. Synthetic-only.
// Not a finding of causation, misconduct, fraud, or statutory burden shift.
import { evaluate as authorityDutyEvaluate } from './authority-duty.mjs';
export const VERSION = 'vos03-purpose-review/0.3.0-research.3';
const copy = x => structuredClone(x);
const validRef = x => typeof x === 'string' && x.trim().length > 0;
const unique = a => [...new Set(a)];
const activityKinds = new Set([
  'POLICY_PROPOSAL_OR_ANNOUNCEMENT','SPEAKING_OPPORTUNITY','MEDIA_COVERAGE',
  'PUBLIC_EVENT','STATEMENT_SHARING'
]);
const effectEvidenceTypes = new Map([
  ['PAYMENT_RECEIVED','PAYMENT_RECEIPT'],
  ['SERVICE_DELIVERED','SERVICE_DELIVERY_RECORD'],
  ['RECORD_ACCESS_USED','RECORD_ACCESS_LOG'],
  ['INDEPENDENT_REVIEW_COMPLETED','COMPLETED_REVIEW_RECORD'],
  ['REMEDY_IMPLEMENTED','REMEDY_EXECUTION_RECORD']
]);
const statuses = ['REPORTED','SOURCE_LINKED','INDEPENDENTLY_VERIFIED','UNVERIFIED'];
function evidenceStatus(value) { return statuses.includes(value) ? value : 'UNVERIFIED'; }
function question(q) { return typeof q === 'string' && q.trim() ? q.trim() : null; }
const historicalKinds = new Map([
  ['APPROVAL','LOT_APPROVAL_RECORD'],
  ['RELEASE','LOT_RELEASE_RECORD'],
  ['DISTRIBUTION','LOT_DISTRIBUTION_RECORD']
]);
const dateOnly = x => typeof x === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(x)
  && Number.isFinite(Date.parse(x)) && new Date(x).toISOString().slice(0,10) === x;
function reviewHistoricalLot(input) {
  const h=input.historical_lot_review;
  if (!h) return null;
  const improvements=Array.isArray(h.later_improvements)?copy(h.later_improvements):[];
  const records=Array.isArray(h.records)?h.records:[];
  const scopeOk=validRef(h.lot_id) && dateOnly(h.period_start) && dateOnly(h.period_end)
    && h.period_start <= h.period_end;
  const checks=Object.fromEntries([...historicalKinds].map(([key,kind])=>{
    const refs=records.filter(r=>scopeOk && r?.record_type===kind
      && r.case_id===input.case_id && r.lot_id===h.lot_id
      && dateOnly(r.event_date) && r.event_date>=h.period_start && r.event_date<=h.period_end
      && validRef(r.contemporaneous_origin_ref) && validRef(r.source_ref));
    return [key,{status:refs.length?'HISTORICAL_SOURCE_LINKED_REVIEW_PENDING':'HISTORICAL_SOURCE_GAP_OPEN',
      matched_records:copy(refs)}];
  }));
  return {lot_id:h.lot_id ?? null,period_start:h.period_start ?? null,period_end:h.period_end ?? null,
    later_improvements:improvements, historical_checks:checks, supplied_records:copy(records),
    historical_verification_closed:false, later_improvement_implies_historical_compliance:false,
    present_safety_certified:false, historic_misconduct_determined:false, causation_determined:false};
}
export function evaluatePurpose(input) {
  if (input?.synthetic !== true) throw new Error('SYNTHETIC_ONLY');
  const authority = authorityDutyEvaluate(input);
  const rights = input.rights_review ?? {};
  const victim = rights.claimant ?? {};
  const controller = rights.controller ?? {};
  const claimantAccess = victim.access_status ?? 'UNKNOWN';
  const controllerControl = controller.control_status ?? 'UNKNOWN';
  const controllerSource = validRef(controller.source_ref);
  const controllerVerified = controllerControl === 'INDEPENDENTLY_VERIFIED' && controllerSource;
  const claimantUnable = ['UNAVAILABLE','RESTRICTED','NONE','UNKNOWN'].includes(claimantAccess);
  const controlReported = ['REPORTED','SOURCE_LINKED','INDEPENDENTLY_VERIFIED'].includes(controllerControl);
  const materialGap = rights.material_question_open === true;
  const dueBasis = rights.duty_basis_status === 'INDEPENDENTLY_VERIFIED' && validRef(rights.duty_basis_ref);
  const requested = rights.request_status === 'SOURCE_LINKED' && validRef(rights.request_source_ref);
  const gapPriority = materialGap && claimantUnable && controlReported;
  const burden = gapPriority ? 'CONTROLLER_EXPLANATION_FIRST' : materialGap ? 'SOURCE_AND_ACCESS_MAPPING_OPEN' : 'NO_OPEN_MATERIAL_QUESTION_REPORTED';

  // A minor wording difference never invalidates a source-linked substantive claim.
  const differences = (rights.language_differences ?? []).map((d,i)=>{
    const semanticEffect = d?.material_change === true;
    return {index:i, kind:semanticEffect?'MATERIAL_MEANING_REVIEW':'NON_MATERIAL_VARIATION',
      original_statement:typeof d?.original_statement === 'string'?d.original_statement:null,
      competing_statement:typeof d?.competing_statement === 'string'?d.competing_statement:null,
      human_review_required:semanticEffect, automatic_claim_deletion:false};
  });
  const existing = Array.isArray(rights.existing_source_refs) ? unique(rights.existing_source_refs.filter(validRef)) : [];
  const repeats = (rights.additional_requests ?? []).map((req,i)=>({
    index:i, source_ref:validRef(req?.source_ref)?req.source_ref:null,
    result: validRef(req?.source_ref) && existing.includes(req.source_ref)
       ? 'REUSE_EXISTING_SOURCE_NO_REPEAT_BURDEN'
       : req?.controlled_by === 'CONTROLLER' && claimantUnable
         ? 'ASSIGN_CONTROLLER_EXPLANATION_TASK'
         : 'NECESSITY_AND_ACCESS_REVIEW',
    automatic_negative_claimant_inference:false
  }));

  const b = input.support_benefits ?? {};
  const benefits = Array.isArray(b.records)? b.records : [];
  const benefitEntries = benefits.map((r,i)=>{
    const declared = evidenceStatus(r?.support_claim_status);
    const provider = evidenceStatus(r?.provider_benefit_status);
    const refs = Array.isArray(r?.source_refs)?unique(r.source_refs.filter(validRef)):[];
    const declaredRealized = evidenceStatus(r?.victim_realized_status);
    const outcome = r?.outcome_evidence;
    const effectKind = r?.effect_kind ?? null;
    const activityOnly = activityKinds.has(effectKind) || activityKinds.has(outcome?.source_type);
    const expectedSourceType = effectEvidenceTypes.get(effectKind);
    const matchedOutcome = !activityOnly && expectedSourceType !== undefined
      && outcome?.kind === 'VICTIM_OUTCOME' && outcome.source_type === expectedSourceType
      && outcome.effect_kind === effectKind && outcome.delivery_status === 'REALIZED'
      && validRef(outcome.ref) && refs.includes(outcome.ref)
      && outcome.case_id === input.case_id && outcome.question_id === input.question_id
      && validRef(r?.outcome_id) && outcome.outcome_id === r.outcome_id
      && validRef(r?.beneficiary_id) && outcome.beneficiary_id === r.beneficiary_id;
    const candidateLinked = r?.victim_realized === true && matchedOutcome;
    const realized = candidateLinked ? 'SOURCE_LINKED'
      : declaredRealized === 'REPORTED' ? 'REPORTED' : 'UNVERIFIED';
    const benefitConcern = r?.provider_received_benefit === true && provider !== 'UNVERIFIED'
      && !candidateLinked;
    return {index:i, support_claim:declared, provider_benefit:provider, victim_realized:realized,
      victim_realized_input:declaredRealized, victim_realized_claimed:r?.victim_realized === true,
      effect_kind:effectKind, outcome_id:r?.outcome_id ?? null, beneficiary_id:r?.beneficiary_id ?? null,
      evidence_refs:refs, outcome_evidence:copy(outcome ?? null), outcome_binding_checked:matchedOutcome,
      realized_benefit_confirmed:false, actual_benefit_review_open:!activityOnly || benefitConcern,
      status:activityOnly?'ACTIVITY_ONLY_NOT_REALIZED_BENEFIT'
        :candidateLinked?'MATERIAL_OUTCOME_EVIDENCE_LINKED_REVIEW_PENDING'
        :benefitConcern?'BENEFIT_RETURN_REVIEW_OPEN':'BENEFIT_OUTCOME_UNVERIFIED',
      automatic_corruption_finding:false, direct_victim_compensation_awarded:false};
  });
  const historicalLot = reviewHistoricalLot(input);
  const tasks = [];
  if(historicalLot) tasks.push('REVIEW_CONTEMPORANEOUS_LOT_APPROVAL_RELEASE_AND_DISTRIBUTION');
  if(materialGap) tasks.push('PRESERVE_UNRESOLVED_MATERIAL_QUESTION');
  if(gapPriority) tasks.push('REQUEST_CONTROLLER_SEARCH_PRESERVATION_EXPLANATION_AND_ALTERNATE_ACCESS');
  if(!controllerVerified && controlReported) tasks.push('VERIFY_REPORTED_CONTROL_AND_SOURCE_WITHOUT_TREATING_REPORT_AS_CERTIFICATION');
  if(gapPriority && !dueBasis) tasks.push('IDENTIFY_APPLICABLE_DUTY_AND_EXCEPTIONS_BEFORE_RESPONSIBILITY_FINDING');
  if(gapPriority && !requested) tasks.push('LINK_OR_PREPARE_SOURCE_SPECIFIC_REQUEST_WITHOUT_REPEAT_VICTIM_PROOF');
  if(benefitEntries.some(x=>x.actual_benefit_review_open)) tasks.push('AUDIT_SUPPORT_BENEFIT_FLOW_CONFLICTS_AND_REALIZED_VICTIM_OUTCOMES');
  if(benefitEntries.some(x=>x.outcome_binding_checked)) tasks.push('CHECK_OUTCOME_SOURCE_ORIGINAL_AND_INDEPENDENT_REVIEW');
  if(differences.some(x=>x.human_review_required)) tasks.push('REVIEW_MATERIAL_SEMANTIC_DIFFERENCE_WITHOUT_AUTOMATIC_DELETION');
  return {
    version:VERSION, status:'SYNTHETIC_RESEARCH_CANDIDATE',
    inherited_authority_duty:authority,
    historical_lot_review:historicalLot,
    rights_review:{burden_routing:burden, evidence_access_gap_review:gapPriority?'PRIORITY_REVIEW_OPEN':'NOT_AUTOMATICALLY_ESTABLISHED',
      controller_reported_not_authenticated:controlReported&&!controllerVerified,
      claimant_credibility_penalty:null, automatic_burden_shift:false,
      legal_duty_verified_for_review:dueBasis, legality_or_misconduct_determined:false,
      meaning_differences:differences, repeated_requests:repeats,
      source_references:existing, unresolved_question:question(rights.unresolved_question)},
    benefit_return:{entries:benefitEntries, automatic_corruption_conclusion:false,
      support_success_auto_inferred:false, actual_victim_benefit_requires_evidence:true},
    review_tasks:unique(tasks), verification_order:['SOURCE_FACTS','AUTHORITY_AND_DUTY','FULFILLMENT_AND_EXCEPTIONS','RESPONSIBILITY_REVIEW','STATUTORY_INFERENCE_ONLY_IF_ELIGIBLE'],
    ax_status:'UNCHANGED', civic_trace_045:'MAINTAINED', civic_trace_046:'DEFERRED',
    total_score:null, future_r3_authority_prejudged:false,
    external_action_performed:false, production_deployed:false, release_approved:false,
    source_truth_authenticated:false
  };
}
