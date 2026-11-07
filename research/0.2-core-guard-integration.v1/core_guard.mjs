// Opt-in integration. Imported public core, correction.3 and guard stay unchanged.
import { CentralCore } from '../../src/agents.mjs';
import { validateProject } from '../../src/project.mjs';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const VERSION = '0.2-core-guard-integration/1.0.0-synthetic';
const ENTRY = fileURLToPath(new URL('./guard_entry.py', import.meta.url));
const RESEARCH_ENTRY = fileURLToPath(new URL('../0.3-local-correction.3/bridge_entry.py', import.meta.url));
const LIMIT = 2 * 1024 * 1024;
const sha = value => createHash('sha256').update(value).digest('hex');
const obj = x => x !== null && typeof x === 'object' && !Array.isArray(x);
const text = x => typeof x === 'string' && x.trim().length > 0;
const fail = code => { throw new Error(code); };
const clone = x => structuredClone(x);
const CONTEXT = ['case_id', 'track_id', 'subject_id'];

// One serialized JSON input is shared by both Python stages. Nothing migrates
// labels, actors, material IDs, evidence states, decisions or approvals.
function snapshot(input) {
  let encoded;
  try { encoded = JSON.stringify(input); } catch { fail('JSON_INPUT_REQUIRED'); }
  if (typeof encoded !== 'string' || Buffer.byteLength(encoded) > LIMIT) fail('INTEGRATION_INPUT_LIMIT');
  const x = JSON.parse(encoded);
  if (!obj(x) || !obj(x.project) || !obj(x.legacy_project) || !obj(x.mapping)) fail('INVALID_ENVELOPE');
  if (x.project.synthetic !== true || x.legacy_project.synthetic !== true) fail('EXPLICIT_SYNTHETIC_INPUTS_REQUIRED');
  validateProject(x.legacy_project);
  if (x.project.schema !== 'ADONIS-VOS-0.3-INPUT/1.0') fail('RESEARCH_SCHEMA_REQUIRED');
  if (CONTEXT.some(k => !text(x.project[k]) || x.mapping[k] !== x.project[k])) fail('PROJECT_SCOPE_MAPPING_REQUIRED');
  if (!Array.isArray(x.project.support_reviews) || !Array.isArray(x.project.routes) || !obj(x.project.sources)) fail('INVALID_RESEARCH_COLLECTION');
  if (!Array.isArray(x.mapping.review_routes)) fail('EXPLICIT_REVIEW_ROUTE_MAP_REQUIRED');
  for (const pair of x.mapping.review_routes) {
    if (!obj(pair) || !text(pair.review_id) || !text(pair.route_id) || !text(pair.question_id) ||
        !x.project.support_reviews.some(r => obj(r) && r.id === pair.review_id)) fail('INVALID_OR_ORPHAN_REVIEW_MAPPING');
  }
  for (const collection of [x.project.routes, x.legacy_project.requests]) {
    if (collection.some(r => !obj(r) || !text(r.id)) || new Set(collection.map(r => r.id)).size !== collection.length) fail('AMBIGUOUS_ROUTE_OR_REQUEST');
  }
  if (!text(x.now) || !/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(x.now) || Number.isNaN(Date.parse(x.now))) fail('EXPLICIT_TIME_REQUIRED');
  if (x.mapping.authorization !== 'EXPLICIT_SYNTHETIC_MAPPING' || x.mapping.legacy_project_id !== x.legacy_project.id) fail('MAPPING_IDENTITY_CONFLICT');
  if (x.project.procedure_id != null && x.project.procedure_id !== x.project.track_id) fail('EXPLICIT_CASE_AND_TRACK_REQUIRED');
  if (!Array.isArray(x.mapping.request_routes)) fail('EXPLICIT_REQUEST_ROUTE_MAP_REQUIRED');
  const seenRequests = new Set(), seenRoutes = new Set();
  for (const pair of x.mapping.request_routes) {
    const request = x.legacy_project.requests.find(r => r.id === pair?.request_id);
    const route = x.project.routes.find(r => r.id === pair?.route_id);
    if (!obj(pair) || !request || !route || seenRequests.has(request.id) || seenRoutes.has(route.id)) fail('INVALID_REQUEST_ROUTE_MAPPING');
    if (CONTEXT.some(k => route[k] !== x.project[k]) || route.controller !== request.controller || route.question !== request.question ||
        JSON.stringify(route.records_needed) !== JSON.stringify(request.items)) fail('REQUEST_CONTENT_MAPPING_CONFLICT');
    seenRequests.add(request.id); seenRoutes.add(route.id);
  }
  if (seenRequests.size !== x.legacy_project.requests.length || seenRoutes.size !== x.project.routes.length) fail('INCOMPLETE_REQUEST_ROUTE_MAP');
  return {x, encoded};
}

function reviewBindings(x) {
  const reviews = x.project.support_reviews;
  return reviews.map((review, index) => {
    const reasons = [];
    if (!obj(review) || !text(review.id)) reasons.push('INVALID_REVIEW_ID');
    if (obj(review) && reviews.filter(r => obj(r) && r.id === review.id).length !== 1) reasons.push('DUPLICATE_REVIEW_ID');
    const pairs = x.mapping.review_routes.filter(p => obj(p) && p.review_id === review?.id);
    if (pairs.length !== 1) reasons.push('MISSING_OR_AMBIGUOUS_REVIEW_ROUTE_MAP');
    const pair = pairs[0];
    const route = x.project.routes.find(r => r.id === pair?.route_id);
    if (!route) reasons.push('UNLINKED_REVIEW_ROUTE');
    if (route && obj(review)) {
      if (CONTEXT.some(k => review[k] !== x.project[k] || route[k] !== x.project[k])) reasons.push('REVIEW_ROUTE_SCOPE_CONFLICT');
      if (review.controller !== route.controller) reasons.push('REVIEW_ROUTE_CONTROLLER_CONFLICT');
      if (!text(route.question_id) || pair.question_id !== route.question_id) reasons.push('EXPLICIT_ROUTE_QUESTION_REQUIRED');
    }
    return {input_index:index, review_id:obj(review) ? review.id ?? null : null,
      route_id:route?.id ?? null, question_id:route?.question_id ?? null,
      status:reasons.length ? 'MAPPING_HELD' : 'BOUND', reasons};
  });
}

function guardContract(result) {
  return obj(result) && result.schema === 'ADONIS-VOS-CORRECTION4-GUARD-CANDIDATE/0.2' &&
    Array.isArray(result.reviews) && result.release_or_R3_approval_changed === false &&
    result.civic_trace_045_maintained === true && result.civic_trace_046_approval_deferred === true &&
    result.axioms_AX01_to_AX09_unchanged === true && result.legal_or_medical_finding === false &&
    result.external_execution === false && result.total_score === null && result.reviews.every(r =>
      obj(r) && ['REVIEW_SCOPE_HELD','WARNING_REVIEW_OPEN','SOURCE_OR_PROVENANCE_REVIEW_OPEN'].includes(r.status) &&
      Array.isArray(r.warnings) && Array.isArray(r.accepted_observations) && Array.isArray(r.held_observations) &&
      r.accepted_observations.every(o => obj(o) && text(o.id) && Array.isArray(o.depends_on) && o.depends_on.every(text)) &&
      r.warnings.every(w => obj(w) && Object.hasOwn(ACTIONS, w.code) && obj(w.context) &&
        Array.isArray(w.basis_observations) && w.basis_observations.every(text) && Array.isArray(w.source_refs) &&
        w.source_refs.every(text) && w.not_a_legal_or_medical_finding === true) &&
      obj(r.remediation) && (r.status === 'REVIEW_SCOPE_HELD' ? Array.isArray(r.held_reason) :
        Array.isArray(r.remediation.question_material_states) && r.remediation.question_material_states.every(obj) &&
        Array.isArray(r.remediation.held_events)));
}

function pythonStep(payload, entry, stage, contract, timeout_ms) {
  const input = JSON.stringify(payload);
  const child = spawnSync('python3', ['-B', entry], {input, encoding:'utf8', timeout:timeout_ms,
    maxBuffer:4 * LIMIT, shell:false,
    env:{PATH:process.env.PATH, LANG:'C.UTF-8', LC_ALL:'C.UTF-8',
      PYTHONNOUSERSITE:'1', PYTHONPATH:'', PYTHONDONTWRITEBYTECODE:'1'}});
  const receipt = {stage, input_sha256:sha(input),
    stdout_sha256:sha(child.stdout ?? ''), stderr_sha256:sha(child.stderr ?? ''),
    exit_code:child.status, signal:child.signal, status:'FAILED', error_code:null};
  let result = null;
  if (child.error || child.status !== 0) receipt.error_code = child.error?.code ?? 'PYTHON_STEP_REJECTED';
  else {
    try { result = JSON.parse(child.stdout); } catch { receipt.error_code = 'INVALID_PYTHON_JSON'; }
    if (!receipt.error_code && !contract(result)) receipt.error_code = 'PYTHON_OUTPUT_CONTRACT_VIOLATION';
    if (!receipt.error_code) receipt.status = 'SUCCEEDED';
  }
  return {result:receipt.status === 'SUCCEEDED' ? result : null, receipt};
}

const ACTIONS = {
  AUTOPSY_EVIDENCE_EXCLUSION_WARNING:'REQUEST_AUTOPSY_EVIDENCE_ASSESSMENT_AND_EXCLUSION_REASONS',
  CIRCULAR_BURDEN_SHIFT_WARNING:'REQUEST_CONTROLLER_PRODUCTION_AND_INDEPENDENT_REVIEW',
  HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING:'REQUEST_SOURCE_LINKED_INSTITUTIONAL_AND_DECISION_PROCESS_REVIEW',
  CAUSATION_METHOD_CONSISTENCY_REVIEW:'REQUEST_CASE_SPECIFIC_CAUSATION_METHOD_EXPLANATION',
  INDIVIDUAL_SUSCEPTIBILITY_REVIEW_OPEN:'REQUEST_INDEPENDENT_INDIVIDUAL_SUSCEPTIBILITY_ASSESSMENT',
};

function combine(x, base, guard, bindings) {
  const inputReviews = x.project.support_reviews;
  // Guard skips nonobjects; correlate its native result only against objects.
  let cursor = 0;
  const reviews = inputReviews.map((raw, index) => {
    const native = obj(raw) && guard.result ? guard.result.reviews[cursor++] : null;
    const binding = bindings[index];
    const held = !native || binding.status !== 'BOUND' || native.status === 'REVIEW_SCOPE_HELD';
    const accepted = held ? [] : native.accepted_observations;
    // Question must match the explicitly mapped route. Missing is not wildcard.
    let eligible = accepted.filter(o => o.question_id === binding.question_id);
    const extraHeld = accepted.filter(o => o.question_id !== binding.question_id).map(o => ({...o, reason:['OBSERVATION_ROUTE_QUESTION_UNLINKED']}));
    let ids = new Set(eligible.map(o => o.id));
    // New mapping holds also propagate to dependencies. They do not erase independent facts.
    while (true) {
      const dependent = eligible.filter(o => o.depends_on.some(id => !ids.has(id)));
      if (!dependent.length) break;
      const bad = new Set(dependent.map(o => o.id));
      extraHeld.push(...dependent.map(o => ({...o, reason:['INTEGRATION_DEPENDENCY_UNAVAILABLE']})));
      eligible = eligible.filter(o => !bad.has(o.id));
      ids = new Set(eligible.map(o => o.id));
    }
    const warnings = held ? [] : native.warnings.flatMap(w => {
      if (w.context.question_id !== binding.question_id) return [];
      const basis = accepted.filter(o => w.basis_observations.includes(o.id));
      const requiredKinds = new Set(basis.map(o => o.kind));
      const surviving = basis.filter(o => ids.has(o.id));
      const survivingKinds = new Set(surviving.map(o => o.kind));
      // The unchanged guard already defines exactly which kinds form this
      // warning. Recheck those same kinds after new mapping/dependency holds.
      // A held redundant basis must not erase a surviving independent basis.
      if (!requiredKinds.size || [...requiredKinds].some(k => !survivingKinds.has(k))) return [];
      return [{...w, basis_observations:surviving.map(o => o.id),
        source_refs:[...new Set(surviving.map(o => o.source_ref))].sort()}];
    });
    const remediation = held ? null : clone(native.remediation);
    if (remediation) {
      const foreign = remediation.question_material_states.filter(s => s.question_id !== binding.question_id);
      remediation.question_material_states = remediation.question_material_states.filter(s => s.question_id === binding.question_id);
      remediation.unbound_question_states = foreign;
      remediation.unresolved_route_binding = foreign.length > 0;
    }
    return {input_index:index, id:binding.review_id, binding, status:held ? 'INTEGRATION_REVIEW_HELD' :
      (native.held_observations.length || native.remediation.held_events.length || extraHeld.length || remediation.unresolved_route_binding ? 'PARTIAL_REVIEW_WITH_QUARANTINE' : native.status),
      warnings, accepted_observations:eligible,
      held_observations:held ? [] : [...native.held_observations, ...extraHeld],
      items_not_evaluated_for_integrated_use:held,
      held_reason:held ? [...binding.reasons, ...(native?.held_reason ?? []), ...(!native ? ['GUARD_RESULT_UNAVAILABLE'] : [])] : [],
      remediation, original_review:clone(raw)};
  });
  const warnings = reviews.flatMap(r => r.warnings.map(w => ({...w, review_id:r.id, route_id:r.binding.route_id})));
  const actions = warnings.map(w => ({action:ACTIONS[w.code], review_id:w.review_id, route_id:w.route_id,
    context:clone(w.context), basis_observations:[...w.basis_observations], source_refs:[...w.source_refs],
    status:'LOCAL_REVIEW_PROPOSAL', delivery:'NOT_SENT', automatic_sanction:false,
    victim_concession_required:false}));
  return {schema:'ADONIS-VOS-CORE-GUARD-REPORT/1.0',
    warning_authority:'GUARD_V02_PLUS_EXPLICIT_ROUTE_BINDING',
    legacy_rows:clone(base.legacy_execution.result.rows),
    legacy_ethics:clone(base.legacy_execution.result.ethics),
    legacy_action_drafts:clone(base.legacy_execution.result.action_drafts),
    support_reviews:reviews, procedural_warnings:warnings, action_proposals:actions,
    correction3_routes:base.research_execution ? clone(base.research_execution.routes) : null,
    review_nodes_original:clone(x.project.review_nodes ?? {}),
    facts_original:clone(x.project.facts ?? []), items_original:clone(x.project.items ?? []),
    preservation_notice:'Original facts, dissent, adverse evidence and held items remain available, not automatically validated or discarded.',
    victim_concession_required:false, generated_blanket_concessions:[],
    clinical_record_absence_reduces_victim_credibility:false,
    total_score:null, legal_or_medical_finding:false, external_action_performed:false,
    canonical_rules_changed:false, approval_status_changed:false, deployment_status:'NOT_DEPLOYED'};
}

export function runIntegratedCore(input, {timeout_ms = 10000} = {}) {
  if (!Number.isSafeInteger(timeout_ms) || timeout_ms < 1 || timeout_ms > 15000) fail('INVALID_TIMEOUT');
  const {x, encoded} = snapshot(input), bindings = reviewBindings(x);
  // Real 0.2 task lifecycle. Python stages have separate receipts and never
  // overwrite native SUCCEEDED/FAILED task status or expand its capabilities.
  const core = new CentralCore();
  core.register({id:'V02-CORE-GUARD-INPUT', connection:'LOCAL_ADAPTER_CONFIGURED',
    layer:'EXECUTION', capabilities:['LOCAL_RULE_EVALUATION'], runtime_ref:'src/project.mjs'});
  core.assign({id:'V02-CORE-GUARD-TASK', agent_id:'V02-CORE-GUARD-INPUT', capability:'LOCAL_RULE_EVALUATION'});
  const legacy = core.runLocal('V02-CORE-GUARD-TASK', x.legacy_project);
  const research = pythonStep({project:x.project, now:x.now}, RESEARCH_ENTRY, 'UNCHANGED_CORRECTION3', r =>
    obj(r) && r.version === '0.3.0-design.2-local-correction.3' && r.total_score === null &&
    r.canonical_rules_changed === false && r.approval_status_changed === false &&
    r.deployment_status === 'NOT_DEPLOYED' && r.external_action_performed === false &&
    r.source_verified_externally === false && Array.isArray(r.routes) &&
    ['STABLE_WITH_OPEN_ITEMS', 'STABLE_LOCAL_CHECK_ONLY'].includes(r.consistency_loop?.status), timeout_ms);
  const base = {legacy_execution:legacy, legacy_snapshot:core.snapshot(),
    research_execution:research.result, research_receipt:research.receipt};
  const guard = pythonStep(x.project, ENTRY, 'UNCHANGED_GUARD_V02', r => guardContract(r) && r.reviews.length === x.project.support_reviews.filter(obj).length, timeout_ms);
  const report = combine(x, base, guard, bindings);
  const stageFailure = base.research_receipt.status !== 'SUCCEEDED' || guard.receipt.status !== 'SUCCEEDED';
  const quarantine = report.support_reviews.some(r => r.status === 'INTEGRATION_REVIEW_HELD' || r.status === 'PARTIAL_REVIEW_WITH_QUARANTINE');
  return {status:stageFailure ? 'PARTIAL_STAGE_FAILURE' : quarantine ? 'LOCAL_INTEGRATION_WITH_QUARANTINE' : 'LOCAL_INTEGRATION_SUCCEEDED',
    integration_version:VERSION, report,
    legacy_execution:base.legacy_execution, legacy_snapshot:base.legacy_snapshot,
    receipts:{legacy:base.legacy_execution.receipt, correction3:base.research_receipt, guard:guard.receipt,
      integration:{input_sha256:sha(encoded), report_sha256:sha(JSON.stringify(report)),
        mode:'LOCAL_SYNTHETIC_CORE_GUARD_INTEGRATION', external_api_calls:0}},
    audit_only:{correction3_execution:base.research_execution, guard_execution:guard.result,
      notice:'Unmodified component output, not the integrated warning or draft authority. Historical correction.3 warnings and draft text are not reissued.'},
    original_input:clone(x), no_legacy_status_overwrite:true,
    local_core_integration:true, production_integration:false,
    release_or_R3_approval_changed:false, total_score:null};
}
