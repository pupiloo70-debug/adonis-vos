import { readFileSync } from 'node:fs';
import { runResearchBridge } from './bridge.mjs';

const data = JSON.parse(readFileSync(new URL('./examples-autopsy-access.json', import.meta.url), 'utf8'));
const out = runResearchBridge(data);
if (out.status !== 'LOCAL_RESEARCH_CONNECTION_SUCCEEDED') {
  throw Error('EXAMPLE_CONNECTION_FAILED');
}

// Replay prints a new receipt without overwriting the published reference evidence.
console.log(JSON.stringify({
  script_revision: 'READ_ONLY_REPLAY_20261106_01',
  status: out.status,
  version: out.research_receipt.adapter_version,
  warnings: out.research_execution.procedural_warnings.map(x => x.code),
  legacy_receipt: out.legacy_execution.receipt,
  research_receipt: out.research_receipt,
  production_integration: out.production_integration,
  total_score: out.research_execution.total_score
}, null, 2));
