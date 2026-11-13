#!/usr/bin/env python3
"""Only verifies synthetic fixture structure; does NOT run Adonis VOS core/gate."""
import json
from pathlib import Path
p=Path(__file__).with_name('synthetic-gate-cases.json')
data=json.loads(p.read_text(encoding='utf-8'))
assert data['status']=='SPEC_ONLY_NOT_INTEGRATED'
cases=data['cases']
assert len(cases)==9 and len(set(c['id'] for c in cases))==9
for c in cases:
    assert all(isinstance(c[k],str) and c[k] for k in ('id','synthetic_scenario','expected_research_status','reason'))
    assert c['automatic_legal_finding'] is False
print('PASS: 9/9 synthetic fixture structure checks (NOT gate behavior tests)')
