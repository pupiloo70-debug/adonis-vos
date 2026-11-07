# Separate code audit of the synthetic repair candidate

Audit date: 2026-11-07. Scope: local synthetic code and test behavior only. This is not independent authentication of real sources, legal/medical review, R3 approval or actual repository integration verification.

The separate reviewer reported the following against the exact final guard SHA-256:

`1af214770c2068c97d5969a3321489699e26c5f6e75937372733fdf28cf1a56a`

- 68/68 supplied unit tests passed in a separate rerun, including the unchanged original 25 tests and their 1,000 deterministic malformed mutations.
- 2,000 additional random dependency graphs matched an independent dependency-closure oracle.
- A 4,000-node cycle was held while all nine unrelated baseline observations and five baseline warnings remained.
- 3,000 additional malformed mutations (seed 10891) produced 72 controlled `ValueError` rejections, no uncontrolled exceptions and no input mutations.
- Swapping event IDs on simultaneous contradictory remediation events no longer changes the status to access-completed or revoked: the result remains ambiguous/review-open.
- The code hash was stable before and after the audit. The new regression test file hash was `70c5fe9daed9f2e561c5a41fc5334ca5a59a3bce57947e96e91ef83e7ee91e55`.

The reviewer first identified further nested-scope, remedy-source, simultaneous-time and reporting issues, which were corrected before this final rerun. No reproduced defect from those audit probes remained in this exact snapshot. This is bounded evidence, not a proof that no other defects exist.

The 68 unit tests and original independent-probe script are included and reproducible. The reviewer's additional exploratory graph/fuzz harness and raw logs are not included in this bundle; those counts above are a recorded review report, not an extra 5,000 unit tests or self-executed receipt entries. No legacy correction.3, Node or bridge suite is counted as rerun.
