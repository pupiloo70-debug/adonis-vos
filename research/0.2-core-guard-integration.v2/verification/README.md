# Adonis VOS 0.3 — Verification Records

## 1. Purpose

This directory preserves synthetic test evidence for the Adonis VOS 0.2 CentralCore, correction.3, and Guard integration v2.

Status: RESEARCH_CANDIDATE / NOT_RELEASED

## 2. Verification Structure

- latest/: Execution logs, synthetic outputs, and test records
- boundary-comparison.json: Original and candidate behavior comparison
- independent-audit.md: Independent review record
- independent-identity.test.mjs: Review identity regression tests

## 3. Verification Principles

1. Match review results by exact review ID, not array position.
2. Quarantine invalid or duplicated identities.
3. Preserve independently valid results.
4. Preserve original input and evidence provenance.
5. Distinguish PASS, FAIL, PARTIAL, and UNVERIFIED.
6. Never convert missing evidence into automatic guilt or immunity.
7. Preserve dissent, correction rights, and unresolved questions.

## 4. Approval Boundaries

- AX-01 through AX-09: UNCHANGED
- CIVIC-TRACE 0.4.5: MAINTAINED
- CIVIC-TRACE 0.4.6: DEFERRED
- total_score: null
- R3 final release authority: RESERVED

No automatic deployment, legal judgment, external enforcement, or release authorization.

## 5. Evidence Status

This README is a directory guide only.

Execution records and test outputs must be verified against their original files and hashes.

Uploading files does not constitute independent test reproduction or production integration.

No Constitutional Change.
