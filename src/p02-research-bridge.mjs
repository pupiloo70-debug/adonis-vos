/** P02 research-only opt-in bridge; existing production 0.2 is unchanged. */
import { reviewContextLinked } from '../research/2026-11-18-typed-dependency-local/candidate/testimony-controller.mjs';
import { normalizeP02SyntheticInput } from './p02-input-boundary.mjs';

export const P02_BRIDGE_STATUS = Object.freeze({
  mode: 'RESEARCH_ONLY',
  integrated_to_default_core: false,
  released: false,
  source_authentication: false,
  legal_or_medical_adjudication: false
});

export function runP02Research(input) {
  return reviewContextLinked(normalizeP02SyntheticInput(input));
}

