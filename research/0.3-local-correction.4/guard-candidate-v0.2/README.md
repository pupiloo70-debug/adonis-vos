# Adonis VOS 0.3 correction.4: repaired standalone guard candidate

**Status: LOCAL_SYNTHETIC_RESEARCH_CANDIDATE / NOT_INTEGRATED / NOT_DEPLOYED / R3_REVIEW_PENDING**

Date: 2026-11-07. Guard schema: `ADONIS-VOS-CORRECTION4-GUARD-CANDIDATE/0.2`.

This is a separate repair of the supplied standalone candidate. It is not a production correction.4 release, an update to the public correction.3 runtime, a legal/medical finding, or approval to publish or overwrite anything. Every input in the included tests and examples is synthetic. No real person, case or private record was tested.

## What changed

1. Warning prerequisites are grouped by exact case, track, subject, material and question. Different materials cannot silently form an autopsy-exclusion warning. Other multi-fact warnings use the same context rule. The facts remain accepted individually when valid; failure to form a warning is not a finding that the underlying fact is false.
2. Project and review case/track/subject must be explicit nonblank strings. Item and source scope must be explicit and match. Missing project subject holds the review instead of pooling multiple people. A review-level hold explicitly reports that its items were not evaluated. Input data is not changed or deleted.
3. Dependency processing uses an iterative O(V+E) graph algorithm. A valid 1,200-node or 10,000-node chain no longer hits Python recursion limits. Missing or held prerequisites, cycles, and their dependents are quarantined without suppressing independent facts.
4. All occurrences of a duplicate observation ID are held, independent of input order. Dependents cannot use an ambiguous ID. Duplicate remediation-event IDs are handled the same way.
5. Explicit review material/question also scopes remedies. Nested contradictory item, source, actor, remedy-type or review-scope labels are held at the appropriate item/review level. Malformed dependency collections are not recursively copied.
6. Conflicting remediation events at the same instant remain ambiguous, regardless of event ID. Held remediation events also set the unresolved-provenance summary flag.

## Preservation checks

- The unchanged original synthetic baseline still retains all nine observations and all five review-only warnings.
- When only the exclusion's material changes, all nine observations remain accepted, and only the unsupported combined warning disappears.
- A foreign observation does not erase unrelated same-case observations or warnings.
- A bad review does not erase a correctly scoped sibling review.
- Grant, reported access, partial access and revocation remain separate reported states. Prior burdens are preserved; source truth is not authenticated.
- `AX-01` through `AX-09`, CIVIC-TRACE 0.4.5, deferred 0.4.6 approval and `total_score=null` remain unchanged. No automatic guilt, immunity, sanctions or external actions are produced.

## Current verification

Run from this folder:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v test_correction4_guard.py test_correction4_regressions.py
python3 -B independent_probes.py
```

The original `test_correction4_guard.py` is byte-for-byte unchanged: 25 tests, including its 1,000 deterministic malformed mutations (seed 41). The new regression file adds 43 tests, for **68 passing tests**. Mutations and graph sizes are subcases, not additional unit-test counts. See `test-output.txt`, `independent-probe-results.json` and `execution-record.json` for actual runs. Independent audit artifacts are included separately when available.

The historical correction.3 Python 132, bridge 14, and 0.2 Node checks/tests are **not rerun and not counted** in these results. No repository clone, push, PR, merge, deploy, release approval or R3 approval was performed for this repair.

## Explicit schema limits

- This is still a typed-label consistency guard, not a source-authentication or language-understanding system. Matching strings and quoted substrings do not establish truth or prove that an actor did an act.
- Material IDs identify the material/record being assessed, not automatically the document containing the quoted source. Material IDs are required for observations and sources. This is stricter than the older standalone candidate and is not silently compatible with all correction.3 inputs.
- For legacy synthetic fixtures, question ID may be absent on both the observation and source. Absence is a distinct unqualified bucket (`null` in output), never a wildcard for an explicit or nested question. If actual separate questions are unlabeled, the guard cannot infer them. Production use would require a versioned, explicit question model and migration policy.
- Some optional source actor-role, decision-status and remediation-type fields are not present in the original fixture. When present they must agree. Their absence does not authenticate the corresponding assertion.
- Legitimate evidence spanning multiple materials will be retained individually but cannot silently form one warning. An independently reviewed relationship schema would be needed to combine those materials safely.
- Metadata traversal conservatively holds nesting deeper than 24. No resource-exhaustion resistance for arbitrarily large hostile documents is claimed.
- Simultaneous conflicting remediation types are preserved and reported as `SIMULTANEOUS_CONFLICT_REVIEW_OPEN`, not ordered by event ID. A genuinely later timestamp may update the latest reported state, while the earlier conflict remains in timestamp batches. Source authenticity and actual access still are not established.
- This candidate has not been integrated with the actual correction.3 schema, production sources, CI or default runtime. No claim of compatibility, deployment safety or exhaustive correctness is made.

## Manual placement

See `MANUAL-GITHUB-KO.md`. The suggested location is a **new, isolated subfolder**, `research/0.3-local-correction.4/guard-candidate-v0.2/`. That path is a proposed destination, not a verified empty directory or permission to overwrite an existing file. Keep existing correction.3 files and the current research README/review records intact unless you independently decide otherwise.
