import test from 'node:test';
import assert from 'node:assert/strict';
import { runP02Research, P02_BRIDGE_STATUS } from '../src/p02-research-bridge.mjs';

const fixture = () => ({
  schema: 'ADONIS-0.3-CONTEXT/SYNTHETIC-1',
  synthetic: true,
  case_id: 'SYNTHETIC-CASE-01',
  statements: [],
  records: [],
  remedies: []
});

test('P02 must reject real or unmarked input', () => {
  assert.throws(() => runP02Research({ ...fixture(), synthetic: false }), /P02_SYNTHETIC_INPUT_ONLY/);
  assert.throws(() => runP02Research({ ...fixture(), schema: 'OTHER' }), /P02_SYNTHETIC_INPUT_ONLY/);
});

test('P02 bridges the typed dependency candidate without releasing it', () => {
  const result = runP02Research(fixture());
  assert.equal(result.total_score, null);
  assert.equal(result.isolation_report.mode, 'ITEM_LEVEL_TYPED_LINKS_SYNTHETIC_RESEARCH');
  assert.equal(result.isolation_report.source_truth_authenticated, false);
  assert.equal(result.decision_boundaries.auto_causality, false);
  assert.equal(P02_BRIDGE_STATUS.integrated_to_default_core, false);
  assert.equal(P02_BRIDGE_STATUS.released, false);
});

test('P02 isolates missing typed dependencies rather than accepting the record', () => {
  const input = fixture();
  input.records.push({
    id: 'REC-1', controller: 'SYNTHETIC-CONTROLLER', item: 'TEST-ITEM',
    state: 'NOT_PROVIDED', evidence_status: 'CLAIM_ONLY', source_refs: [],
    depends_on_items: [{ collection: 'statements', id: 'MISSING-STATEMENT' }]
  });
  const result = runP02Research(input);
  assert.equal(result.isolation_report.accepted_counts.records, 0);
  assert.ok(result.isolation_report.held.some(x => x.id === 'REC-1'));
});
