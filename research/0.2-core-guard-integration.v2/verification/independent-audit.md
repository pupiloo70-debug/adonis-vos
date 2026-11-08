# Independent review identity audit

Date: 2026-11-08. Scope: local synthetic v2 integration, not production certification.

Audited core_guard.mjs SHA-256: `7c5740928ef212d0563cf667b695930f305d369bf0c1557a6212916b07e6e0c0`.

## Method

Read the implementation, synthetic fixture and inherited integration tests. This reviewer modified only the independent test and audit files, not the implementation. The independent suite invokes the full exported runIntegratedCore, actual CentralCore and both actual Python programs. A temporary PATH shim runs the real Python program first, then mutates its completed stdout or exit status. There is no production injection hook or substituted evaluator.

Run from repository root:

    node --test research/0.2-core-guard-integration.v2/verification/independent-identity.test.mjs

## Measured result

Final: **30 tests passed, 0 failed, 0 skipped**. Runtime approximately 3.66 seconds. Packaged execution log: [latest/candidate-independent-identity.txt](latest/candidate-independent-identity.txt).

Coverage includes all six permutations of three distinct review outputs, stable action attribution, duplicate expected IDs, missing IDs, unknown extras, malformed extras, exact matching without trimming, cross-review payload substitution, foreign case/track/subject/source, nonexistent warning basis, malformed warning isolation, scope-held remediation shapes, optional held_reason shapes, a valid scope-held result, invalid JSON, nonzero guard exit and correction3 failure with successful guard continuation. Successful fault-isolation cases check that unaffected sibling reviews retain their distinct warnings and actual stage receipts remain successful. Stage-failure cases check the relevant failure receipt and surviving stages.

## Findings discovered and retested

Initial run: 29 tests, 26 passed and 3 failed. Two contract-validation gaps caused three complete-integration crashes:

1. **Malformed scope-held remediation:** A REVIEW_SCOPE_HELD row could carry question_material_states={} or [null], pass the held contract branch, and throw during payload iteration or dereference. This lost valid sibling results rather than quarantining the malformed row.
2. **Malformed optional held_reason:** A normal native row with held_reason=1 passed the contract. When that input review lacked its route mapping, combine attempted to spread the number and threw.

The implementation owner repaired both gaps. The independent regression tests now pass against the hash above. Scope-held malformed-remediation tests clear accepted observations and warnings first, ensuring the malformed remediation itself is rejected. A separate positive test confirms valid scope-held output remains supported. No unresolved defect was reproduced in this finite test set.

## Limits

Exact ID and payload correspondence is not authentication of source truth, verification of legal or medical findings, or independent reimplementation of warning semantics. The suite is finite synthetic coverage, not proof over all malformed JSON or real-world inputs. This audit does not claim to have rerun the owner's separate inherited/adversarial suites. No public repository was changed and no remote push was performed. This is an independent review, not release certification.
