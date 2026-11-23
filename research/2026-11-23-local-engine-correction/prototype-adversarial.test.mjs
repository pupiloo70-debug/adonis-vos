import test from 'node:test';
import assert from 'node:assert/strict';
import { evaluate } from '../src/engine.mjs';

const answer = (value, basis='USER_REPORT', refs=[]) => ({value,basis,refs});

test('A11 inherited record_access must not become case evidence', () => {
  const input = Object.create({record_access:answer('YES','DOCUMENT_REFERENCED',['SYNTHETIC-REF'])});
  const r=evaluate(input);
  assert.equal(r.items[0].status,'NEEDS_CHECK');
  assert.deepEqual(r.items[0].refs,[]);
  assert.equal(r.total_score,null);
});
test('A12 inherited preservation_risk must not escalate priority', () => {
  const input=Object.create({preservation_risk:answer('YES')});
  const r=evaluate(input);
  assert.equal(r.items[6].status,'NEEDS_CHECK');
  assert.equal(r.items[6].priority,'STANDARD_REVIEW');
});
test('A13 explicit own NO remains NO even against inherited YES', () => {
  const input=Object.assign(Object.create({record_access:answer('YES')}),{record_access:answer('NO')});
  assert.equal(evaluate(input).items[0].status,'NOT_REPORTED');
});
test('A14 independent own YES still produces reported signal, never a score', () => {
  const r=evaluate({reason_gap:answer('YES','USER_REPORT')});
  assert.equal(r.items[4].status,'SIGNAL_REPORTED');
  assert.equal(r.items[4].basis,'USER_REPORT');
  assert.equal(r.total_score,null);
});
