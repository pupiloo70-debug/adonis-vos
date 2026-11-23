"""Standalone synthetic-only conflict buffer research proposal.
No IO, no model weights, no external action, no changes to Adonis VOS core.
"""
from dataclasses import dataclass

LOCKED = ('AX-01~09', 'G1~G9', 'CIVIC-TRACE-0.4.5', 'total_score=null')
GUARDED = {'rules', 'authority', 'release', 'deployment', 'axioms', 'evaluation_gate'}

@dataclass(frozen=True)
class Candidate:
    change_id: str
    changes: tuple
    technical_pass: bool
    rights_pass: bool
    source_provenance_preserved: bool
    dissent_preserved: bool
    controller_duties_preserved: bool
    baseline_hash_verified: bool
    rollback_snapshot_verified: bool
    conflict_count: int = 0
    new_failures: int = 0


def evaluate(c: Candidate):
    """Choose an action for an authorized local candidate, never legal guilt or deployment."""
    if not isinstance(c, Candidate):
        raise TypeError('CANDIDATE_REQUIRED')
    if not c.change_id or any(not isinstance(x, str) for x in c.changes):
        return _out('HOLD', 'INVALID_CANDIDATE', 0)
    if any(x in GUARDED for x in c.changes):
        return _out('HOLD', 'R3_SCOPE_REQUIRED', 0)
    if not c.baseline_hash_verified or not c.rollback_snapshot_verified:
        return _out('HOLD', 'TRACEABILITY_NOT_VERIFIED', 0)
    if not (c.source_provenance_preserved and c.dissent_preserved and c.controller_duties_preserved):
        return _out('REVERT', 'RIGHTS_INVARIANT_FAILED', 0)
    if not (c.technical_pass and c.rights_pass):
        return _out('REVERT', 'DUAL_GATE_FAILED', 0)
    if c.conflict_count < 0 or c.new_failures < 0:
        return _out('HOLD', 'INVALID_CONFLICT_COUNT', 0)
    # Test-only exploration buffer; never an authorization or proof of improvement.
    if c.new_failures > 0 or c.conflict_count >= 3:
        return _out('HOLD', 'CONFLICT_BUFFER_EXCEEDED', 0)
    budget = 2 if c.conflict_count == 0 else 1
    return _out('LOCAL_CANDIDATE_ONLY', 'DUAL_GATE_PASSED', budget)


def _out(action, reason, budget):
    return dict(action=action, reason=reason, next_exploration_budget=budget,
                total_score=None, external_action=False, automatic_guilt=False,
                automatic_immunity=False, benefit_from_obstruction=False,
                rules_changed=False, release_approved=False)
