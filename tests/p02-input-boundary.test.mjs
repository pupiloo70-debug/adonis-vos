import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeP02SyntheticInput as normalize, P02_MAX_BYTES } from '../src/p02-input-boundary.mjs';
const valid = () => ({ schema: 'ADONIS-0.3-CONTEXT/SYNTHETIC-1', synthetic: true,
  case_id: 'SYNTHETIC', statements: [], records: [], remedies: [] });
test('valid synthetic object round trips and is detached', () => {
  const input = valid(); const output = normalize(input);
  assert.deepEqual(output, input); assert.notEqual(output, input);
});
test('reject non-synthetic', () => assert.throws(() => normalize({...valid(), synthetic:false}), /SYNTHETIC_INPUT_ONLY/));
test('reject >2 MiB', () => assert.throws(() => normalize({...valid(), padding:'x'.repeat(P02_MAX_BYTES)}), /INPUT_SIZE_LIMIT/));
test('reject inherited record property', () => {
  const input = valid(); input.records = [Object.assign(Object.create({ evidence_status:'CLAIM_ONLY' }), {id:'A'})];
  assert.throws(() => normalize(input), /INHERITED_PROPERTIES/);
});
test('reject inherited typed dependency reference', () => {
  const input = valid(); input.records = [{ id:'R', depends_on_items:[Object.assign(Object.create({collection:'statements'}), {id:'S'})] }];
  assert.throws(() => normalize(input), /INHERITED_PROPERTIES/);
});
test('reject accessors without reading them', () => {
  const input = valid(); Object.defineProperty(input, 'trap', {enumerable:true, get(){throw Error('read')}});
  assert.throws(() => normalize(input), /ACCESSOR_PROPERTY/);
});
test('reject cyclic and shared references', () => {
  const a = valid(); a.loop=a; assert.throws(() => normalize(a), /CIRCULAR_OR_SHARED/);
  const b=valid(); b.statements=[{}]; b.records=[b.statements[0]];
  assert.throws(() => normalize(b), /CIRCULAR_OR_SHARED/);
});
test('reject sparse arrays and unsafe keys', () => {
  const a=valid(); a.records=new Array(1); assert.throws(() => normalize(a), /SPARSE_ARRAY/);
  const b=valid(); Object.defineProperty(b,'__proto__',{value:'x',enumerable:true});
  assert.throws(() => normalize(b), /UNSAFE_PROPERTY/);
});
