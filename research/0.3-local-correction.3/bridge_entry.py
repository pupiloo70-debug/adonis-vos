"""Bounded stdin entry point for the explicitly synthetic Node research bridge."""
import json
import sys
from vos_verify import run_consistency_loop, invariants

LIMIT = 2 * 1024 * 1024

def main():
    raw = sys.stdin.buffer.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('BRIDGE_INPUT_LIMIT')
    envelope = json.loads(raw)
    project = envelope['project']
    if project.get('synthetic') is not True:
        raise ValueError('SYNTHETIC_RESEARCH_ONLY')
    if not isinstance(envelope.get('now'), str):
        raise ValueError('EXPLICIT_TIME_REQUIRED')
    result = run_consistency_loop(project, envelope['now'])
    if invariants(result):
        raise ValueError('INVARIANT_FAILURE')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == '__main__':
    main()
