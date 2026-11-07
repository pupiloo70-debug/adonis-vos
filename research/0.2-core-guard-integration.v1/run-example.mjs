import { readFileSync } from 'node:fs';
import { runIntegratedCore } from './core_guard.mjs';

// Replays only the bundled synthetic fixture. No automatic file writes or upload.
const input = JSON.parse(readFileSync(new URL('./synthetic-input.json', import.meta.url), 'utf8'));
const result = runIntegratedCore(input);
console.log(JSON.stringify(result, null, 2));
if (result.status !== 'LOCAL_INTEGRATION_SUCCEEDED') process.exitCode = 1;
