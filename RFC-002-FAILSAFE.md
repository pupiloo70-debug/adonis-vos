# RFC-002: Adonis VOS Load Control and Fail-Safe Research Gate

**Date:** 2026-11-14 KST  
**Status:** Draft research specification; standalone synthetic prototype; not released  
**Target:** A-R3 research track. No changes to AX-01–AX-09 or G1–G9.  
**Authority:** No Operational Enforcement Authority. `external_enforcement: false`; `total_score: null`.

This RFC proposes a bounded intake gate. Overload or an execution failure must not imply that an evidence question is closed or verified. A documented external procedural status remains separate from the research result.

## 1. Reference-only intake

Accept UTF-8 JSON bytes up to **65,536 bytes (64 KiB), inclusive**, measured before decoding or parsing. A future stream adapter must enforce this bound while reading; the prototype receives an already allocated Buffer. Check the outer and nested fields against [the schema](research/2026-11-14-rfc-002-failsafe/vos-gate-input.schema.json) and reject duplicate document IDs. The prototype accepts at most 50 references with synthetic IDs. It never reads source files or accepts embedded documents. Reject unvalidated bytes without copying their case ID or procedural status into an output record.

Each reference carries an ID, its access state and a SHA-256 digest when known. `AVAILABLE` requires a digest matching the trusted local fixture registry; use `null` where a non-available item has no known digest. Do not invent a digest to satisfy the schema. The prototype's four access labels are a local subset; a future adapter must preserve richer canonical evidence states and test any label mapping. A digest match identifies bytes relative to a trusted reference. It does not establish authorship, document truth, or substantive verification. No input-provided `hash_signature` is accepted as authentication or as a cache key.

## 2. Bounded processing and reuse

- Use a bounded FIFO waiting queue and limit concurrent workers. Admission beyond capacity returns `QUEUE_CAPACITY_EXCEEDED`, `NOT_QUEUED` and `retry_required: true`. The prototype returns a receipt to the caller but does not durably store jobs or retry them. A future adapter must persist and reconcile accepted jobs and rejected admission receipts before claiming no loss or reliable resumption.
- Reuse only results eligible for **human review**, using a server-computed digest over the normalized payload and trusted context: core, schema, rules, access and evidence revisions, plus the synthetic scenario and review flags. Recheck available fixture digests before reuse. Bound the process-local cache; do not cache failures. Before multiuser use, explicitly partition by verified access scope and test access revocation and revision changes. Concurrent duplicate coalescing is not implemented.
- Keep the worker separate from request processing; enforce an execution timeout and wait for the worker to terminate before recycling capacity. **500 ms** is a configurable prototype value that includes startup; it is not a measured service target or a limit on queue waiting time. There is no real Python child process in this prototype. A future bridge must stop descendants and validate cross-module state transitions.

## 3. Fail-safe result

| Condition | Prototype result |
| --- | --- |
| Byte limit or manifest limit | Reject before worker execution |
| Malformed schema, missing/mismatched trusted digest | Reject or mark the evidence check open |
| Worker timeout, exception or incompatible output state | `GATE_EXECUTION_UNVERIFIED` |
| Queue full | `GATE_EXECUTION_UNVERIFIED` with explicit `NOT_QUEUED` admission outcome |
| Valid synthetic completion | `READY_FOR_HUMAN_VERIFICATION` |

Each failure returns a controlled reason code, retains known review flags in trusted context, and keeps automatic certification and external enforcement disabled. A parsed and validated external `CLOSED` may be recorded as a procedural fact and cannot set gate status. `human_verification_required` indicates a review requirement, not a claim that evidence is ready or review has occurred. Avoid advancing a case or resetting unresolved questions after an intake or worker failure.

## 4. Regression and adoption boundary

Run the [standalone research suite](research/2026-11-14-rfc-002-failsafe/) with:

```sh
node --test research/2026-11-14-rfc-002-failsafe/gate.test.mjs
```

The fixture worker simulates core/bridge outcomes. Before any integration proposal, reproduce the existing CentralCore, correction.3 Python and bridge, correction.4 guard, v1/v2 integration and A-R3 virtual suites from pinned sources. Require all applicable suites to pass; a skipped, stale or unexecuted suite is not a pass. The public A-R3 manifest records **11/11 virtual tests** and a separate **12/12 core smoke test**. A later local suite of 14 cases is a separate research result. This package adds five scenario groups; it does not replace or rerun those integration suites.

Public baseline: [Adonis VOS main at affb4f5](https://github.com/pupiloo70-debug/adonis-vos/tree/affb4f547c56f604a765837da9c2060577dc873f). The baseline has no `research:ar3` npm command. This RFC adds no npm script, production route or CI requirement. The repository package identifies its existing license status as `UNLICENSED`; this proposal does not add a license or an SPDX license grant. Record research approval and operational adoption separately.
