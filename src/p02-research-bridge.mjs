/**
 * Adonis VOS P02 research-only bridge.
 * Explicit opt-in; not imported by the 0.2 production CLI or engine.
 * Inputs must be synthetic and explicitly marked. No private case data.
 */
import { reviewContextLinked } from '../research/2026-11-18-typed-dependency-local/candidate/testimony-controller.mjs';

export const P02_BRIDGE_STATUS = Object.freeze({
  mode: 'RESEARCH_ONLY',
  integrated_to_default_core: false,
  released: false,
  source_authentication: false,
  legal_or_medical_adjudication: false
});

export function runP02Research(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input) ||
      input.synthetic !== true || input.schema !== 'ADONIS-0.3-CONTEXT/SYNTHETIC-1') {
    throw new Error('P02_SYNTHETIC_INPUT_ONLY');
  }
  return reviewContextLinked(input);
}
