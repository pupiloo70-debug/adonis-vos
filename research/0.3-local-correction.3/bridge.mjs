// Explicit research adapter. The 0.2 CentralCore implementation is unchanged.
// Its native task and the subsequent local Python step have separate receipts.
import { CentralCore } from '../../src/agents.mjs';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ENTRY = fileURLToPath(new URL('./bridge_entry.py', import.meta.url));
const MAX_BYTES = 2 * 1024 * 1024;
const VERSION = '0.3.0-design.2-local-correction.3';
const sha = x => createHash('sha256').update(x).digest('hex');
const fail = reason => { throw Error(reason); };
const text = x => typeof x === 'string' && x.trim().length > 0;
const object = x => x && typeof x === 'object' && !Array.isArray(x);

function checkMapping(legacy, project, mapping) {
  if (!object(project) || project.synthetic !== true) fail('SYNTHETIC_RESEARCH_ONLY');
  if (!text(project.case_id) || !text(project.track_id) ||
      (project.procedure_id != null && project.procedure_id !== project.track_id)) fail('EXPLICIT_CASE_AND_TRACK_REQUIRED');
  if (!object(mapping) || mapping.legacy_project_id !== legacy.id ||
      mapping.case_id !== project.case_id || mapping.track_id !== project.track_id ||
      mapping.authorization !== 'EXPLICIT_SYNTHETIC_MAPPING') fail('MAPPING_IDENTITY_CONFLICT');
  if (!Array.isArray(mapping.request_routes)) fail('EXPLICIT_REQUEST_ROUTE_MAP_REQUIRED');
  const requests = new Map(legacy.requests.map(x => [x.id, x]));
  const routes = new Map((project.routes ?? []).map(x => [x.id, x]));
  const usedRequests = new Set(), usedRoutes = new Set();
  for (const pair of mapping.request_routes) {
    if (!object(pair) || !requests.has(pair.request_id) || !routes.has(pair.route_id) ||
        usedRequests.has(pair.request_id) || usedRoutes.has(pair.route_id)) fail('INVALID_REQUEST_ROUTE_MAPPING');
    usedRequests.add(pair.request_id); usedRoutes.add(pair.route_id);
    const route = routes.get(pair.route_id), request = requests.get(pair.request_id);
    if (route.case_id !== project.case_id || route.track_id !== project.track_id ||
        route.controller !== request.controller || route.question !== request.question ||
        JSON.stringify(route.records_needed) !== JSON.stringify(request.items)) fail('REQUEST_CONTENT_MAPPING_CONFLICT');
  }
  if (usedRequests.size !== requests.size || usedRoutes.size !== routes.size) fail('INCOMPLETE_REQUEST_ROUTE_MAP');
  // No state, R3 assertion, factual finding, source class or legal clock is inferred.
}

export function runResearchBridge({legacy_project, project, mapping, now}, {timeout_ms = 10000} = {}) {
  if (!text(now) || !/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(now) || Number.isNaN(Date.parse(now))) fail('EXPLICIT_TIME_REQUIRED');
  if (!Number.isSafeInteger(timeout_ms) || timeout_ms < 1 || timeout_ms > 15000) fail('INVALID_TIMEOUT');
  const serialized = JSON.stringify({legacy_project, project, mapping, now});
  if (Buffer.byteLength(serialized) > MAX_BYTES) fail('BRIDGE_INPUT_LIMIT');
  if (!object(legacy_project) || legacy_project.schema !== 'ADONIS-VOS-PROJECT/0.2') fail('LEGACY_SCHEMA_REQUIRED');
  const original = structuredClone(legacy_project), supplied = structuredClone(project);
  checkMapping(original, supplied, mapping);
  const core = new CentralCore();
  core.register({id:'V02-LOCAL-RESEARCH-INPUT', connection:'LOCAL_ADAPTER_CONFIGURED',
    layer:'EXECUTION', capabilities:['LOCAL_RULE_EVALUATION'], runtime_ref:'src/project.mjs'});
  core.assign({id:'V02-LOCAL-RESEARCH-TASK', agent_id:'V02-LOCAL-RESEARCH-INPUT', capability:'LOCAL_RULE_EVALUATION'});
  const base = core.runLocal('V02-LOCAL-RESEARCH-TASK', original);
  const bytes = JSON.stringify({project:supplied, now});
  const child = spawnSync('python3', ['-B', ENTRY], {
    input:bytes, encoding:'utf8', timeout:timeout_ms, maxBuffer:4 * MAX_BYTES,
    env:{PATH:process.env.PATH, LANG:'C.UTF-8', LC_ALL:'C.UTF-8',
         PYTHONNOUSERSITE:'1', PYTHONPATH:'', PYTHONDONTWRITEBYTECODE:'1'},
    shell:false,
  });
  const receipt = {adapter_version:VERSION, mode:'LOCAL_SYNTHETIC_RESEARCH_ADAPTER',
    input_sha256:sha(bytes), stdout_sha256:sha(child.stdout ?? ''),
    stderr_sha256:sha(child.stderr ?? ''), exit_code:child.status,
    signal:child.signal, status:'FAILED', production_integration:false,
    deployment_status:'NOT_DEPLOYED', external_api_calls:0,
    automatic_approval:false, source_authentication:false, total_score:null};
  if (child.error || child.status !== 0) {
    return {status:'PYTHON_RESEARCH_STEP_FAILED', legacy_execution:base,
      legacy_snapshot:core.snapshot(), research_execution:null, research_receipt:receipt,
      error_code:child.error?.code ?? 'PYTHON_STEP_REJECTED',
      mapping:structuredClone(mapping), no_legacy_status_overwrite:true};
  }
  let result;
  try { result = JSON.parse(child.stdout); } catch { fail('INVALID_PYTHON_OUTPUT'); }
  if (result.version !== VERSION || result.total_score !== null || result.approval_status_changed !== false ||
      result.deployment_status !== 'NOT_DEPLOYED' || result.external_action_performed !== false ||
      result.consistency_loop?.status === 'STOP_INVARIANT_FAILURE') fail('RESEARCH_OUTPUT_CONTRACT_VIOLATION');
  receipt.status = 'SUCCEEDED';
  return {status:'LOCAL_RESEARCH_CONNECTION_SUCCEEDED', legacy_execution:base,
    legacy_snapshot:core.snapshot(), research_execution:result,
    research_receipt:receipt, mapping:structuredClone(mapping),
    no_legacy_status_overwrite:true, production_integration:false};
}
