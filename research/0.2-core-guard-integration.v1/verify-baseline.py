"""Verify pinned imported dependencies and unchanged canonical/test files."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
lock = json.loads((HERE / 'BASELINE-SHA256.json').read_text())
failures = []
for row in lock['files']:
    path = ROOT / row['path']
    if not path.is_file():
        failures.append({'path': row['path'], 'reason': 'MISSING'})
    elif hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
        failures.append({'path': row['path'], 'reason': 'CHANGED'})
print(json.dumps({'commit': lock['commit'], 'checked': len(lock['files']),
                  'unchanged': not failures, 'failures': failures}, indent=2))
raise SystemExit(bool(failures))
