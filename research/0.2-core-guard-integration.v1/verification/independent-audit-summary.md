# Independent core → correction.3 → guard integration audit

Date: 2026-11-07. Scope: local synthetic-only opt-in integration in `research/0.2-core-guard-integration.v1/`. This audit did not edit baseline implementation, publish, upload, push, deploy, approve R3, authenticate a source, or test private real-case data.

## Final result

**35 independent integration probes passed, 0 failed.** No unresolved defect was found within the tested scope. This is not exhaustive correctness or production approval.

The auditor created its own enriched synthetic fixture rather than reusing the implementation author's example. The tests invoke the actual exported integration function, actual `CentralCore` lifecycle, actual correction.3 Python entry, and actual guard Python entry. Temporary local Python shims test malformed child output only; no external service is used.

Final tested `core_guard.mjs` SHA-256: `165bad3cf211da1b2c8e39bba355b07c8c6f542fa80bf32b1b6c30ebe60e8537`. Other tested source hashes are recorded in `tested-source-sha256.json`.

## Findings corrected during the audit

1. **Integration-only quarantine did not propagate through dependencies.** A foreign-question observation was held, but an accepted observation depending on it could still generate a warning. Reproduced with direct and transitive dependencies. Fixed by applying dependency closure after route-question filtering. The valid independent branch remains accepted.
2. **Falsy child JSON was treated as success.** A parsed `null` guard response bypassed a truthiness-gated contract check. Fixed by unconditional contract validation; the guard now fails with a preserved successful core receipt.
3. **A held redundant basis erased an independently supported warning.** When the guard's native warning had two same-kind basis observations, holding one at integration level suppressed the warning even though the other independent basis survived. Fixed by rebuilding basis/source references from surviving rows and checking all originally required kinds. Independently tested single-kind and three-kind warnings.
4. **Malformed review output could throw after core success.** A valid top-level guard envelope with `reviews: [{}]` could pass the shallow contract and fail inside report assembly. Fixed by validating the required per-review result shape. The final shim probe produces a controlled failed guard receipt, no current warning, and retains the successful actual core receipt.

## Coverage

- Separate core, correction.3, guard and integration receipts, including input/output hash correspondence and zero external API calls.
- One shared enriched `project` sent to both Python stages; an additional shadow `guard_project` cannot substitute its contents.
- Exact, complete request/route mapping and explicit review/route/question binding.
- Case, track, subject, material and question conflicts; nested scope conflicts; missing questions; independent sibling preservation.
- Opposing requests cannot become judicial refusals. Obsolete correction.3 support warnings remain only in `audit_only`; the current report has no copied support packet or draft text.
- Source-held and integration-held dependency propagation, including transitive dependencies and retained independent/redundant supporting evidence.
- Duplicate and malformed observations cause honest partial-stage failure where correction.3 rejects them, while the guard can retain independent valid observations.
- Dissent, adverse input facts, original observations and prior versions are retained without input mutation or automatic validation.
- Institutional and controller accountability proposals remain available; no victim-only concession is required.
- Grant-only, partial access, revocation, simultaneous conflicting remedies and foreign-question remediation remain distinct open/reported states.
- No legal/medical finding, score, automatic sanction, external action, canonical rule change, approval change, or production deployment.

## Baseline integrity

`verify_baseline.py` independently recalculated Git blob SHA-1 for every locally materialized public file against `public-tree.json`. **All 85 public files match, 0 mismatches.** New integration files are listed separately. The public tree SHA is `8d44b808bf0147b64d15229fea9ca0bf1e9eafab`, supplied for public base commit `aa77d9f5922e53e22156492360e66a5da0bbfb24`. This does not claim the entire public repository was materialized.

The separately recorded baseline suite counts are not included in this independent count. `independent-results.json` lists each of the 35 probes. Any later change to the tested integration source requires another run.

## Reproduce

After placing this package in the repository, run from `research/0.2-core-guard-integration.v1/verification/`:

```sh
node independent_integration_audit.mjs
python3 -B ../verify-baseline.py
```

The audit prints replay results without changing the delivered `independent-results.json`. To keep a separate replay log, redirect standard output to a new file outside this package. Temporary test directories are removed after each injected-output probe. The baseline command uses the packaged SHA-256 manifest; the original Git blob comparison described above records the independent audit performed before packaging.

## Limits

This remains a typed-label consistency check. Matching scopes, quotations and actor labels do not authenticate source truth, demonstrate semantic correctness, establish causality or liability, or authorize enforcement. Real-case schema migration, default runtime wiring, source authentication, external-model connections, deployment, and R3 approval were not performed. No claim is made about arbitrary hostile host/runtime modification or exhaustive malformed inputs.
