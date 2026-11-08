"""Run the real local integration and regressions without remote writes."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'verification' / 'latest'
OUT.mkdir(parents=True, exist_ok=True)
PREFIX = HERE.relative_to(ROOT).as_posix()
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
jobs = [
    ('baseline-before', ROOT, ['python3', '-B', PREFIX + '/verify-baseline.py']),
    ('core02', ROOT, ['npm', 'test']),
    ('original03', ROOT / 'research/0.3', ['python3', '-B', '-m', 'unittest', 'discover', '-v']),
    ('correction3', ROOT / 'research/0.3-local-correction.3', ['python3', '-B', '-m', 'unittest', 'discover', '-v']),
    ('original-bridge', ROOT / 'research/0.3-local-correction.3', ['node', '--test', 'bridge.test.mjs']),
    ('guard-v02', ROOT / 'research/0.3-local-correction.4/guard-candidate-v0.2',
     ['python3', '-B', '-m', 'unittest', '-v', 'test_correction4_guard.py', 'test_correction4_regressions.py']),
    ('guard-probes', ROOT / 'research/0.3-local-correction.4/guard-candidate-v0.2', ['python3', '-B', 'independent_probes.py']),
    ('original-integration', ROOT, ['node', '--test', 'research/0.2-core-guard-integration.v1/integration.test.mjs']),
    ('original-integration-audit', ROOT, ['node', 'research/0.2-core-guard-integration.v1/verification/independent_integration_audit.mjs']),
    ('candidate-inherited-integration', ROOT, ['node', '--test', PREFIX + '/integration.test.mjs']),
    ('candidate-review-identity', ROOT, ['node', '--test', PREFIX + '/review-identity.test.mjs']),
    ('candidate-independent-identity', ROOT, ['node', '--test', PREFIX + '/verification/independent-identity.test.mjs']),
    ('original-example', ROOT, ['node', 'research/0.2-core-guard-integration.v1/run-example.mjs']),
    ('candidate-example', ROOT, ['node', PREFIX + '/run-example.mjs']),
    ('baseline-after', ROOT, ['python3', '-B', PREFIX + '/verify-baseline.py']),
]
results = []
for name, cwd, command in jobs:
    ran = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=180)
    log = ran.stdout + ran.stderr
    (OUT / (name + '.txt')).write_text(log, encoding='utf-8')
    row = {'suite': name, 'cwd': cwd.relative_to(ROOT).as_posix(), 'command': command,
           'exit_code': ran.returncode, 'log': 'verification/latest/' + name + '.txt'}
    match = re.search(r'(?:Ran |[ℹ#] tests )(\d+)', log)
    if match:
        row['tests'] = int(match[1])
    if name == 'original-integration-audit':
        value = json.loads(ran.stdout)
        row.update({k: value[k] for k in ('tests', 'passed', 'failed')})
    if name.endswith('-example') and ran.returncode == 0:
        value = json.loads(ran.stdout)
        row.update({'status': value['status'], 'warnings': len(value['report']['procedural_warnings']),
                    'accepted_observations': sum(len(r['accepted_observations']) for r in value['report']['support_reviews']),
                    'stage_statuses': {s: value['receipts'][s]['status'] for s in ('legacy', 'correction3', 'guard')}})
        if name == 'candidate-example':
            (OUT / 'synthetic-output.json').write_text(ran.stdout, encoding='utf-8')
    results.append(row)
    print(name, 'PASS' if ran.returncode == 0 else 'FAIL', flush=True)
record = {'checked_at': datetime.now(timezone.utc).isoformat(),
          'source_commit': '42122a759b1bdf9d9c4d692988ea7320cd983a72',
          'candidate_source_sha256': hashlib.sha256((HERE / 'core_guard.mjs').read_bytes()).hexdigest(),
          'all_passed': all(r['exit_code'] == 0 for r in results),
          'node': subprocess.check_output(['node', '--version'], text=True).strip(),
          'python': subprocess.check_output(['python3', '--version'], text=True).strip(),
          'results': results}
(OUT / 'execution-record.json').write_text(json.dumps(record, indent=2) + '\n')
raise SystemExit(not record['all_passed'])
