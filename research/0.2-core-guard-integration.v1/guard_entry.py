"""Bounded, local-only entry to the unchanged public guard v0.2."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       '0.3-local-correction.4' / 'guard-candidate-v0.2'))
from correction4_guard import evaluate

LIMIT = 2 * 1024 * 1024

def main():
    raw = sys.stdin.buffer.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('GUARD_INPUT_LIMIT')
    project = json.loads(raw)
    result = evaluate(project)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))

if __name__ == '__main__':
    main()
