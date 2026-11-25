/** Synthetic-only research guard. Not a release or evidence authentication. */
export const P02_MAX_BYTES = 2 * 1024 * 1024;
const reject = code => { throw new Error(code); };
export function normalizeP02SyntheticInput(input) {
  const seen = new WeakSet();
  const pending = [input];
  while (pending.length) {
    const value = pending.pop();
    if (value === null || typeof value === 'string' || typeof value === 'boolean') continue;
    if (typeof value === 'number') {
      if (!Number.isFinite(value)) reject('P02_INVALID_NUMBER');
      continue;
    }
    if (typeof value !== 'object') reject('P02_INVALID_VALUE');
    if (seen.has(value)) reject('P02_CIRCULAR_OR_SHARED_REFERENCE');
    seen.add(value);
    if (!Array.isArray(value) && Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null)
      reject('P02_INHERITED_PROPERTIES_NOT_ALLOWED');
    if (Array.isArray(value) && Object.getPrototypeOf(value) !== Array.prototype)
      reject('P02_INHERITED_PROPERTIES_NOT_ALLOWED');
    if (Object.getOwnPropertySymbols(value).length) reject('P02_SYMBOL_PROPERTY');
    for (const [key, descriptor] of Object.entries(Object.getOwnPropertyDescriptors(value))) {
      if (!('value' in descriptor)) reject('P02_ACCESSOR_PROPERTY');
      if (key === '__proto__' || key === 'constructor' || key === 'prototype') reject('P02_UNSAFE_PROPERTY');
      if (Array.isArray(value) && key === 'length') continue;
      pending.push(descriptor.value);
    }
    if (Array.isArray(value)) {
      for (let index = 0; index < value.length; index++) {
        if (!Object.hasOwn(value, index)) reject('P02_SPARSE_ARRAY');
      }
    }
  }
  const encoded = JSON.stringify(input);
  if (typeof encoded !== 'string' || Buffer.byteLength(encoded, 'utf8') > P02_MAX_BYTES)
    reject('P02_INPUT_SIZE_LIMIT');
  const result = JSON.parse(encoded);
  if (!result || Array.isArray(result) || result.synthetic !== true ||
    result.schema !== 'ADONIS-0.3-CONTEXT/SYNTHETIC-1') reject('P02_SYNTHETIC_INPUT_ONLY');
  return result;
}
