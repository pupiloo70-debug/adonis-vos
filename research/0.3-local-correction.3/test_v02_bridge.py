"""Synthetic LOCAL_TEST_ONLY boundary smoke tests, NOT a production adapter.

The Python test harness calls the unchanged Node coordinator, then constructs a
deliberately narrow fixture. No R3 consent, procedural identity, evidence state,
source authenticity, or legal clock mapping is specified by this fixture.
Production integration and migration remain unimplemented.
"""
import copy
import json
from pathlib import Path
import subprocess
import unittest

from vos_verify import invariants, run_consistency_loop

ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-11-05T00:00:00+00:00"
NODE_RUN = r"""
import fs from 'node:fs';
import { CentralCore } from './src/agents.mjs';
const p = JSON.parse(fs.readFileSync(0, 'utf8'));
const core = new CentralCore();
core.register({id:'SYNTHETIC-LOCAL', connection:'LOCAL_ADAPTER_CONFIGURED',
  layer:'EXECUTION', capabilities:['LOCAL_RULE_EVALUATION'], runtime_ref:'src/project.mjs'});
core.assign({id:'SYNTHETIC-TASK', agent_id:'SYNTHETIC-LOCAL', capability:'LOCAL_RULE_EVALUATION'});
const execution = core.runLocal('SYNTHETIC-TASK', p);
console.log(JSON.stringify({execution, snapshot:core.snapshot()}));
"""


def run_node(project):
    completed = subprocess.run(
        ['node', '--input-type=module', '-e', NODE_RUN], cwd=ROOT,
        input=json.dumps(project), text=True, capture_output=True, timeout=15,
        check=True)
    return json.loads(completed.stdout)


def synthetic_fixture(report, *, case_id=None):
    """Local experiment only: request questions are copied, not adjudicated.

    project.id/request.id are NOT court case/procedure identifiers. R3 and all
    other legacy metadata are retained in the envelope, never treated as consent.
    Source state/review is preserved but never promoted to 0.3 evidence quality.
    """
    if report.get('schema') != 'ADONIS-VOS-REPORT/0.2':
        raise ValueError('Only the explicit 0.2 report fixture is supported')
    original = report['original_project']
    fixture = {
        'schema': 'ADONIS-VOS-0.3-INPUT/1.0', 'synthetic': True,
        'question': 'Synthetic request preservation boundary check',
        'sources': {s['id']: {'source_class': 'UNKNOWN',
                              'legacy_v02_source': copy.deepcopy(s)}
                    for s in original['sources']},
        'items': [], 'facts': [], 'routes': [],
    }
    if case_id is not None:
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError('Explicit synthetic case identifier required')
        fixture['case_id'] = case_id
    for number, request in enumerate(original['requests']):
        fixture['routes'].append({
            'id': f'SYNTHETIC-BRIDGE-ROUTE-{number}',
            'question': request['question'],
            'controller': request['controller'],
            'source_refs': copy.deepcopy(request['source_refs']),
            'records_needed': copy.deepcopy(request['items']),
            # No automatic translation of provision status to custody/evidence.
            'availability': 'UNKNOWN', 'current_evidence_state': 'UNKNOWN',
        })
    return {
        'test_only': True, 'production_migration': 'NOT_IMPLEMENTED',
        'r3_consent_mapping': 'UNSPECIFIED_NOT_AUTHORIZATION',
        'legacy_v02_report': copy.deepcopy(report), 'v03_input': fixture,
        'identity_map': {'legacy_project_id': original['id'],
                         'explicit_case_id': case_id,
                         'procedure_id': None},
    }


class SyntheticBoundarySmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = json.loads((ROOT / 'examples/synthetic-project.json').read_text())
        cls.project['r3'] = {'synthetic_assertion': 'APPROVED'}
        cls.node = run_node(cls.project)
        cls.legacy = cls.node['execution']['result']

    def test_real_v02_core_runs_only_builtin_node_adapter(self):
        self.assertEqual(self.node['execution']['receipt']['status'], 'SUCCEEDED')
        self.assertEqual(self.node['snapshot']['dispatch_mode'], 'BUILTIN_LOCAL_ONLY')
        self.assertEqual(self.node['snapshot']['external_api_calls'], 0)
        self.assertEqual(self.legacy['original_project'], self.project)

    def test_partial_and_absent_supply_remain_unresolved_in_envelope(self):
        bridge = synthetic_fixture(self.legacy)
        rows = bridge['legacy_v02_report']['rows']
        self.assertEqual([r['provision_status'] for r in rows],
                         ['PARTIAL_REPORTED', 'NOT_PROVIDED'])
        self.assertTrue(all(r['resolution'] == 'UNRESOLVED_REQUIRES_CONTENT_REVIEW'
                            for r in rows))
        self.assertEqual(bridge['v03_input']['routes'][0]['records_needed'], ['A', 'B'])

    def test_project_and_request_ids_are_not_case_or_procedure_ids(self):
        bridge = synthetic_fixture(self.legacy)
        self.assertNotIn('case_id', bridge['v03_input'])
        self.assertIsNone(bridge['identity_map']['procedure_id'])
        explicit = synthetic_fixture(self.legacy, case_id='SYNTHETIC-CASE-SEPARATE')
        self.assertNotEqual(explicit['v03_input']['case_id'], self.project['id'])
        self.assertNotEqual(explicit['v03_input']['routes'][0]['id'],
                            self.project['requests'][0]['id'])

    def test_r3_assertion_is_retained_but_not_mapped_to_consent(self):
        bridge = synthetic_fixture(self.legacy)
        self.assertEqual(bridge['legacy_v02_report']['original_project']['r3'],
                         self.project['r3'])
        self.assertEqual(bridge['r3_consent_mapping'], 'UNSPECIFIED_NOT_AUTHORIZATION')
        self.assertNotIn('r3', bridge['v03_input'])
        self.assertNotIn('consent', bridge['v03_input'])

    def test_no_source_review_or_evidence_state_promotion(self):
        fixture = synthetic_fixture(self.legacy)['v03_input']
        self.assertEqual(fixture['sources']['SRC-1']['source_class'], 'UNKNOWN')
        self.assertEqual(fixture['sources']['SRC-1']['legacy_v02_source'],
                         self.project['sources'][0])
        report = run_consistency_loop(fixture, NOW)
        route = report['routes'][0]
        self.assertEqual(route['current_evidence_state'], 'UNKNOWN')
        self.assertFalse(route['automatic_state_change'])
        self.assertIsNone(route['transition_review_candidate'])
        self.assertFalse(report['source_verified_externally'])

    def test_v02_core_rejects_python_adapter_dispatch(self):
        script = NODE_RUN.replace("runtime_ref:'src/project.mjs'",
                                  "runtime_ref:'research/0.3/vos_verify.py'")
        completed = subprocess.run(
            ['node', '--input-type=module', '-e', script], cwd=ROOT,
            input=json.dumps(self.project), text=True, capture_output=True, timeout=15)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn('LOCAL_ADAPTER_NOT_SUPPORTED', completed.stderr)

    def test_python_result_retains_no_dispatch_or_approval_claims(self):
        bridge = synthetic_fixture(self.legacy)
        report = run_consistency_loop(bridge['v03_input'], NOW)
        self.assertEqual(invariants(report), [])
        self.assertIsNone(report['total_score'])
        self.assertFalse(report['approval_status_changed'])
        self.assertFalse(report['external_action_performed'])
        self.assertEqual(report['deployment_status'], 'NOT_DEPLOYED')
        self.assertEqual(report['support_packet']['filing_status'], 'GENERATED_DRAFT_ONLY')
        self.assertEqual(bridge['production_migration'], 'NOT_IMPLEMENTED')

    def test_wrong_version_and_input_mutation_are_not_silent(self):
        with self.assertRaises(ValueError):
            synthetic_fixture({'schema': 'ADONIS-VOS-REPORT/9.9'})
        with self.assertRaises(ValueError):
            synthetic_fixture(self.legacy, case_id='')
        bridge = synthetic_fixture(self.legacy)
        bridge['v03_input']['sources']['SRC-1']['legacy_v02_source']['state'] = 'DESTROYED'
        self.assertEqual(self.legacy['original_project']['sources'][0]['state'], 'AVAILABLE')


if __name__ == '__main__':
    unittest.main()
