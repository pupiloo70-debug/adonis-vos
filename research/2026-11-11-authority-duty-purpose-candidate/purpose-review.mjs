// Adonis VOS 0.3 purpose-function research overlay. Synthetic-only.
// Not a finding of causation, misconduct, fraud, or statutory burden shift.
import { evaluate as authorityDutyEvaluate } from './authority-duty.mjs';
export const VERSION = 'vos03-purpose-review/0.3.0-research.1';
const copy = x => structuredClone(x);
const validRef = x => typeof x === 'string' && x.trim().length > 0;
const unique = a => [...new Set(a)];
const statuses = ['REPORTED','SOURCE_LINKED','INDEPENDENTLY_VERIFIED','UNVERIFIED'];
function evidenceStatus(value) { return statuses.includes(value) ? value : 'UNVERIFIED'; }
function question(q) { return typeof q === 'string' && q.trim() ? q.trim() : null; }
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
    const realized = evidenceStatus(r?.victim_realized_status);
    const provided = r?.victim_realized === true && realized === 'INDEPENDENTLY_VERIFIED';
    const benefitConcern = r?.provider_received_benefit === true && provider !== 'UNVERIFIED' && !provided;
    return {index:i, support_claim:declared, provider_benefit:provider, victim_realized:realized,
      evidence_refs:Array.isArray(r?.source_refs)?unique(r.source_refs.filter(validRef)):[],
      status:benefitConcern?'BENEFIT_RETURN_REVIEW_OPEN':provided?'REALIZED_BENEFIT_REPORTED_AND_VERIFIED':'BENEFIT_OUTCOME_UNVERIFIED',
      automatic_corruption_finding:false, direct_victim_compensation_awarded:false};
  });
  const tasks = [];
  if(materialGap) tasks.push('PRESERVE_UNRESOLVED_MATERIAL_QUESTION');
  if(gapPriority) tasks.push('REQUEST_CONTROLLER_SEARCH_PRESERVATION_EXPLANATION_AND_ALTERNATE_ACCESS');
  if(!controllerVerified && controlReported) tasks.push('VERIFY_REPORTED_CONTROL_AND_SOURCE_WITHOUT_TREATING_REPORT_AS_CERTIFICATION');
  if(gapPriority && !dueBasis) tasks.push('IDENTIFY_APPLICABLE_DUTY_AND_EXCEPTIONS_BEFORE_RESPONSIBILITY_FINDING');
  if(gapPriority && !requested) tasks.push('LINK_OR_PREPARE_SOURCE_SPECIFIC_REQUEST_WITHOUT_REPEAT_VICTIM_PROOF');
  if(benefitEntries.some(x=>x.status==='BENEFIT_RETURN_REVIEW_OPEN')) tasks.push('AUDIT_SUPPORT_BENEFIT_FLOW_CONFLICTS_AND_REALIZED_VICTIM_OUTCOMES');
  if(differences.some(x=>x.human_review_required)) tasks.push('REVIEW_MATERIAL_SEMANTIC_DIFFERENCE_WITHOUT_AUTOMATIC_DELETION');
  return {
    version:VERSION, status:'SYNTHETIC_RESEARCH_CANDIDATE',
    inherited_authority_duty:authority,
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
