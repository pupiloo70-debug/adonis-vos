// Standalone synthetic research candidate. Not imported by the central core.
// Input assertions are caller-supplied; this module does not authenticate sources.
export const VERSION = 'authority-duty-review/0.1.0-candidate';
const copy = x => structuredClone(x);
const time = x => typeof x === 'string' && /(?:Z|[+-]\d{2}:\d{2})$/.test(x) ? Date.parse(x) : NaN;
const supported = x => typeof x?.source_ref === 'string' && x.source_ref.trim().length > 0;
export function evaluate(input) {
  if (input?.synthetic !== true) throw Error('SYNTHETIC_ONLY');
  if (![input.case_id,input.actor_id,input.question_id].every(x => typeof x === 'string' && x.trim())) throw Error('IDENTITY_REQUIRED');
  const now = time(input.now);
  if (!Number.isFinite(now)) throw Error('EXPLICIT_VALID_TIME_REQUIRED');
  const accepted = [], held = [], ids = new Map(), fingerprints = new Set();
  const rows = input.events ?? [];
  for (const e of rows) if (typeof e?.id === 'string') ids.set(e.id,(ids.get(e.id) ?? 0)+1);
  for (const e of rows) {
    const reasons = [];
    if (!e || !e.id || ids.get(e.id) !== 1) reasons.push('AMBIGUOUS_EVENT_ID');
    if (!supported(e)) reasons.push('SOURCE_REFERENCE_REQUIRED');
    if (['case_id','actor_id','question_id'].some(k => e?.[k] !== input[k])) reasons.push('EVENT_SCOPE_CONFLICT');
    if (!Number.isFinite(time(e?.at)) || time(e.at) > now) reasons.push('EVENT_TIME_INVALID');
    if (!['REQUEST_RECEIVED','FORMAL_REPLY','PARTIAL_ACCESS','CORE_ACCESS_VERIFIED','REFUSAL','ALTERNATIVE_OFFERED','ALTERNATIVE_VERIFIED'].includes(e?.type)) reasons.push('EVENT_TYPE_UNSUPPORTED');
    if (reasons.length) { held.push({event:copy(e),reasons}); continue; }
    const fingerprint = JSON.stringify([e.source_ref,e.type,e.at,e.case_id,e.actor_id,e.question_id]);
    if (fingerprints.has(fingerprint)) { held.push({event:copy(e),reasons:['DUPLICATE_EVENT_PROVENANCE']}); continue; }
    fingerprints.add(fingerprint); accepted.push(copy(e));
  }
  accepted.sort((a,b)=>time(a.at)-time(b.at)||a.id.localeCompare(b.id));
  const has = type => accepted.some(e=>e.type===type);
  const authority = copy(input.authority ?? {status:'UNKNOWN'});
  if (authority.expires_at != null) {
    const expires = time(authority.expires_at);
    authority.status = !Number.isFinite(expires) ? 'UNKNOWN' : expires <= now ? 'EXPIRED' : authority.status;
  }
  const duty = input.duty ?? {};
  const basisVerified = duty.basis_status === 'VERIFIED' && supported({source_ref:duty.basis_ref});
  const deadline = time(duty.deadline_at);
  const deadlineVerified = duty.deadline_status === 'VERIFIED' && supported({source_ref:duty.deadline_ref}) && Number.isFinite(deadline);
  const extension = time(duty.extension_until);
  const extensionVerified = duty.extension_status === 'VERIFIED' && supported({source_ref:duty.extension_ref}) && Number.isFinite(extension);
  const effectiveDeadline = deadlineVerified ? (extensionVerified ? Math.max(deadline,extension) : deadline) : null;
  const overdue = has('REQUEST_RECEIVED') && effectiveDeadline !== null && effectiveDeadline < now;
  const latestRequest = accepted.filter(e=>e.type==='REQUEST_RECEIVED').at(-1);
  const latestResponse = accepted.filter(e=>e.type!=='REQUEST_RECEIVED' && (!latestRequest || time(e.at)>=time(latestRequest.at))).at(-1);
  // No total-case closure, guilt finding, legal burden shift or authority revocation.
  let fulfillment = 'UNKNOWN';
  if (latestResponse?.type==='CORE_ACCESS_VERIFIED' || latestResponse?.type==='ALTERNATIVE_VERIFIED') fulfillment='VERIFIED_FOR_THIS_QUESTION';
  else if (latestResponse?.type==='PARTIAL_ACCESS') fulfillment='PARTIAL_ACCESS_WITH_OPEN_SCOPE';
  else if (latestResponse?.type==='ALTERNATIVE_OFFERED') fulfillment='ALTERNATIVE_OFFERED_EFFECTIVENESS_UNVERIFIED';
  else if (latestResponse?.type==='FORMAL_REPLY') fulfillment='FORMAL_REPLY_ONLY';
  else if (latestResponse?.type==='REFUSAL') fulfillment='REFUSAL_RECORDED';
  else if (overdue) fulfillment='NO_RESPONSE_AFTER_VERIFIED_DEADLINE';
  else if (has('REQUEST_RECEIVED')) fulfillment='REQUEST_RECEIVED_RESPONSE_UNVERIFIED';
  const needsExplanation = fulfillment !== 'VERIFIED_FOR_THIS_QUESTION';
  const observedNonfulfillment = has('REQUEST_RECEIVED') && needsExplanation && (overdue || ['FORMAL_REPLY_ONLY','REFUSAL_RECORDED','PARTIAL_ACCESS_WITH_OPEN_SCOPE'].includes(fulfillment));
  const explanation = needsExplanation ? {
    status:'DRAFT_NOT_SENT', assignee:'SUPPORT_AI_AND_VERIFIED_RECORD_CONTROLLER',
    tasks:['Review already linked sources first','Identify missing scope and controller explanation','Check applicable independent review pathways'],
    victim_repeat_submission_required:false
  } : null;
  const action = input.action ?? {kind:'RESEARCH_SUPPORT'};
  const explicitImproperRequest = action.explicit_revenge === true || action.fabricate_evidence === true;
  let disposition = 'SUPPORT_CONTINUES';
  if (explicitImproperRequest) disposition='REQUESTED_IMPROPER_ACTION_REJECTED_SUPPORT_CONTINUES';
  else if (action.kind==='EXTERNAL_ENFORCEMENT') {
    const gates = action.gates ?? {};
    const validAuthority = authority.status==='VALID' && authority.verified===true && Array.isArray(authority.scope) && authority.scope.includes(action.permission) && typeof action.permission==='string';
    const gatesPassed = ['current_evidence_reviewed','necessity_reviewed','proportionality_reviewed','notice_or_exception_basis_reviewed','independent_review_route_checked','appeal_route_checked','stop_and_recovery_checked'].every(k=>gates[k]===true);
    disposition = validAuthority && gatesPassed ? 'READY_FOR_AUTHORIZED_HUMAN_REVIEW_NOT_EXECUTED' : 'EXTERNAL_ACTION_HELD_SUPPORT_CONTINUES';
  } else if (action.kind!=='RESEARCH_SUPPORT') disposition='UNKNOWN_ACTION_HELD_SUPPORT_CONTINUES';
  return {
    version:VERSION, status:'SYNTHETIC_RESEARCH_CANDIDATE',
    authority_status:authority, duty_basis_status:basisVerified?'VERIFIED_AS_INPUT':'UNVERIFIED',
    duty_fulfillment_status:fulfillment, effective_deadline:effectiveDeadline,
    omission_review:observedNonfulfillment?(basisVerified?'DUTY_FULFILLMENT_REVIEW_CANDIDATE':'EXPLANATION_GAP_DUTY_BASIS_OPEN'):'NO_ADDITIONAL_OMISSION_CLASSIFICATION',
    accepted_events:accepted, held_events:held,
    observed_adverse_response_count:accepted.filter(e=>['FORMAL_REPLY','REFUSAL'].includes(e.type)).length,
    repetition_threshold:null, repetition_does_not_establish_intent:true,
    explanation_task:explanation, action_disposition:disposition,
    residual_questions:copy(input.residual_questions ?? []), past_burden:copy(input.past_burden ?? []),
    allowed_support:['RESEARCH','SOURCE_COMPARISON','LAWFUL_REQUEST_DRAFTING','INDEPENDENT_REVIEW_PATHWAY_RESEARCH'],
    total_score:null, ethical_gravity_numeric:null, intent:'UNKNOWN',
    source_truth_verified:false, external_action_performed:false, automatic_sanction:false,
    legal_burden_shifted:false, r26_transition:false, authority_revoked:false,
    rule_approval_changed:false, production_deployed:false
  };
}
