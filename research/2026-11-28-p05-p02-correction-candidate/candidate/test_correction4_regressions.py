"""Synthetic-only repair regressions. Not production or real-case validation."""
from copy import deepcopy
from itertools import permutations
import unittest

from correction4_guard import evaluate
from test_correction4_guard import fixture, run, codes
import test_correction4_guard as original_tests

AUTOPSY = 'AUTOPSY_EVIDENCE_EXCLUSION_WARNING'
CIRCULAR = 'CIRCULAR_BURDEN_SHIFT_WARNING'
PATTERN = 'HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING'
METHOD = 'CAUSATION_METHOD_CONSISTENCY_REVIEW'
SUSCEPTIBILITY = 'INDIVIDUAL_SUSCEPTIBILITY_REVIEW_OPEN'


def observations(p):
    return p['support_reviews'][0]['observations']


def set_linked(p, index, key, value):
    row = observations(p)[index]
    row[key] = value
    p['sources'][row['source_ref']][key] = value


def chain(size, cycle=False):
    p = fixture()
    prototype = observations(p)[7]
    rows = [dict(prototype, id=f'CHAIN-{i}',
                 depends_on=[f'CHAIN-{i + 1}'] if i < size - 1 else [])
            for i in range(size)]
    if cycle:
        rows[-1]['depends_on'] = ['CHAIN-0']
    p['support_reviews'][0]['observations'] = rows
    return p


class RepairRegressionTests(unittest.TestCase):
    def test_separate_autopsy_materials_do_not_combine_but_facts_survive(self):
        p = fixture()
        set_linked(p, 2, 'material_id', 'SYNTHETIC-OTHER-MATERIAL')
        result = run(p)
        self.assertNotIn(AUTOPSY, {w['code'] for w in result['warnings']})
        self.assertEqual(len(result['accepted_observations']), 9)
        self.assertEqual(result['held_observations'], [])
        self.assertEqual(len(result['warnings']), 4)

    def test_distinct_materials_cannot_complete_circular_or_pattern_warning(self):
        for index in (3, 4, 5):
            with self.subTest(index=index):
                p = fixture()
                set_linked(p, index, 'material_id', 'SYNTHETIC-DIFFERENT-RECORD')
                self.assertNotIn(CIRCULAR, codes(p))
                self.assertNotIn(PATTERN, codes(p))
                self.assertIn(AUTOPSY, codes(p))
                self.assertEqual(len(run(p)['accepted_observations']), 9)

    def test_wrong_benefit_material_only_suppresses_pattern_warning(self):
        p = fixture()
        set_linked(p, 6, 'material_id', 'SYNTHETIC-OTHER-BENEFIT')
        self.assertNotIn(PATTERN, codes(p))
        self.assertIn(CIRCULAR, codes(p))
        self.assertEqual(len(run(p)['accepted_observations']), 9)

    def test_explicit_different_questions_do_not_combine(self):
        p = fixture()
        set_linked(p, 0, 'question_id', 'SYNTHETIC-Q1')
        set_linked(p, 2, 'question_id', 'SYNTHETIC-Q2')
        self.assertNotIn(AUTOPSY, codes(p))
        self.assertEqual(len(run(p)['accepted_observations']), 9)

    def test_missing_question_is_not_wildcard(self):
        p = fixture()
        set_linked(p, 0, 'question_id', 'SYNTHETIC-Q1')
        self.assertNotIn(AUTOPSY, codes(p))
        set_linked(p, 2, 'question_id', 'SYNTHETIC-Q1')
        self.assertIn(AUTOPSY, codes(p))

    def test_two_complete_contexts_produce_two_separate_warnings(self):
        p = fixture()
        for i in (0, 2):
            duplicate = deepcopy(observations(p)[i])
            duplicate.update(id=f'COPY-{i}', source_ref=f'COPY-SOURCE-{i}',
                             material_id='SYNTHETIC-AUTOPSY-2')
            p['sources'][duplicate['source_ref']] = dict(
                p['sources'][f'SOURCE-{i}'], material_id='SYNTHETIC-AUTOPSY-2')
            observations(p).append(duplicate)
        relevant = [w for w in run(p)['warnings'] if w['code'] == AUTOPSY]
        self.assertEqual(len(relevant), 2)
        self.assertEqual({w['context']['material_id'] for w in relevant},
                         {'SYNTHETIC-AUTOPSY', 'SYNTHETIC-AUTOPSY-2'})
        self.assertTrue(all(len(w['basis_observations']) == 2 for w in relevant))

    def test_missing_project_subject_does_not_allow_cross_person_warning(self):
        p = fixture()
        del p['subject_id']
        set_linked(p, 3, 'subject_id', 'SYNTHETIC-PERSON-B')
        before = deepcopy(p)
        result = run(p)
        self.assertEqual(result['status'], 'REVIEW_SCOPE_HELD')
        self.assertIn('PROJECT_SUBJECT_ID_UNSPECIFIED', result['held_reason'])
        self.assertEqual(result['warnings'], [])
        self.assertTrue(result['items_not_evaluated_due_to_review_scope'])
        self.assertEqual(p, before)

    def test_project_scope_fields_must_be_nonempty_strings(self):
        for key in ('case_id', 'track_id', 'subject_id'):
            for value in (None, '', ' ', [], {}, 0, False):
                with self.subTest(key=key, value=value):
                    p = fixture()
                    p[key] = value
                    self.assertEqual(run(p)['status'], 'REVIEW_SCOPE_HELD')
                    self.assertEqual(codes(p), set())
            p = fixture()
            del p[key]
            self.assertEqual(run(p)['status'], 'REVIEW_SCOPE_HELD')

    def test_missing_review_scope_is_not_inferred_from_project(self):
        for key in ('case_id', 'track_id', 'subject_id'):
            with self.subTest(key=key):
                p = fixture()
                del p['support_reviews'][0][key]
                self.assertEqual(codes(p), set())
                self.assertEqual(run(p)['status'], 'REVIEW_SCOPE_HELD')

    def test_missing_item_or_source_scope_is_quarantined_locally(self):
        for area in ('observation', 'source'):
            for key in ('case_id', 'track_id', 'subject_id', 'material_id'):
                with self.subTest(area=area, key=key):
                    p = fixture()
                    obj = observations(p)[0] if area == 'observation' else p['sources']['SOURCE-0']
                    del obj[key]
                    result = run(p)
                    self.assertNotIn(AUTOPSY, codes(p))
                    self.assertIn(CIRCULAR, codes(p))
                    self.assertEqual(len(result['held_observations']), 1)

    def test_question_source_must_match_and_be_well_typed(self):
        for value in ('SYNTHETIC-Q1', [], None, ' '):
            p = fixture()
            p['sources']['SOURCE-0']['question_id'] = value
            self.assertNotIn(AUTOPSY, codes(p))
            self.assertEqual(len(run(p)['held_observations']), 1)

    def test_cross_person_item_does_not_erase_other_independent_warnings(self):
        p = fixture()
        set_linked(p, 3, 'subject_id', 'SYNTHETIC-PERSON-B')
        self.assertEqual(codes(p), {AUTOPSY, METHOD, SUSCEPTIBILITY})
        self.assertEqual(len(run(p)['held_observations']), 1)
        self.assertEqual(len(run(p)['accepted_observations']), 8)

    def test_nested_foreign_material_or_question_cannot_bypass_context(self):
        for field in ('material_id', 'question_id'):
            p = fixture()
            if field == 'question_id':
                set_linked(p, 0, field, 'SYNTHETIC-Q1')
                set_linked(p, 2, field, 'SYNTHETIC-Q1')
            p['sources']['SOURCE-0']['metadata'] = {field: 'SYNTHETIC-FOREIGN'}
            self.assertNotIn(AUTOPSY, codes(p))
            self.assertIn(CIRCULAR, codes(p))

    def test_explicit_review_material_does_not_borrow_other_material(self):
        p = fixture()
        p['support_reviews'][0]['material_id'] = 'SYNTHETIC-AUTOPSY'
        self.assertEqual(codes(p), {AUTOPSY})
        self.assertEqual(len(run(p)['accepted_observations']), 2)

    def test_1200_valid_dependency_chain_is_retained(self):
        result = run(chain(1200))
        self.assertEqual(len(result['accepted_observations']), 1200)
        self.assertEqual(result['held_observations'], [])
        self.assertEqual({w['code'] for w in result['warnings']}, {METHOD})

    def test_10000_valid_chain_is_nonrecursive(self):
        result = run(chain(10000))
        self.assertEqual(len(result['accepted_observations']), 10000)
        self.assertEqual(result['held_observations'], [])

    def test_long_cycle_and_its_dependents_held_independent_fact_retained(self):
        p = chain(1200, cycle=True)
        independent = deepcopy(fixture()['support_reviews'][0]['observations'][8])
        observations(p).append(independent)
        dependent = dict(observations(p)[0], id='DEPENDENT', depends_on=['CHAIN-0'])
        observations(p).append(dependent)
        result = run(p)
        self.assertEqual([row['id'] for row in result['accepted_observations']], ['O8'])
        self.assertEqual(len(result['held_observations']), 1201)
        self.assertTrue(all('DEPENDENCY_CYCLE' in row['reason'] for row in result['held_observations']))
        self.assertEqual(codes(p), {SUSCEPTIBILITY})

    def test_diamond_graph_and_repeated_edges_do_not_look_like_cycle(self):
        p = chain(4)
        rows = observations(p)
        rows[0]['depends_on'] = ['CHAIN-1', 'CHAIN-2', 'CHAIN-2']
        rows[1]['depends_on'] = ['CHAIN-3']
        rows[2]['depends_on'] = ['CHAIN-3']
        result = run(p)
        self.assertEqual(len(result['accepted_observations']), 4)
        self.assertEqual(result['held_observations'], [])

    def test_unavailable_end_of_long_chain_propagates_without_recursion(self):
        p = chain(1200)
        observations(p)[-1]['depends_on'] = ['MISSING']
        result = run(p)
        self.assertEqual(len(result['held_observations']), 1200)
        self.assertEqual(result['accepted_observations'], [])
        self.assertTrue(all('DEPENDENCY_UNAVAILABLE' in row['reason'] for row in result['held_observations']))

    def test_deep_malformed_dependencies_do_not_trigger_deepcopy_recursion(self):
        p = fixture()
        nested = []
        for _ in range(1500):
            nested = [nested]
        observations(p)[7]['depends_on'] = nested
        result = run(p)
        held = next(row for row in result['held_observations'] if row['id'] == 'O7')
        self.assertIn('INVALID_DEPENDENCY_FORMAT', held['reason'])
        self.assertIsNone(held['depends_on'])
        self.assertIn(AUTOPSY, codes(p))

    def test_duplicate_ids_hold_all_occurrences_regardless_of_order(self):
        p = fixture()
        original = observations(p)[0]
        duplicate = deepcopy(observations(p)[2])
        duplicate['id'] = original['id']
        for pair in permutations([original, duplicate]):
            candidate = deepcopy(p)
            candidate['support_reviews'][0]['observations'] = list(pair) + deepcopy(observations(p)[1:])
            result = run(candidate)
            self.assertNotIn('O0', {row['id'] for row in result['accepted_observations']})
            self.assertEqual(len([row for row in result['held_observations'] if row['id'] == 'O0']), 2)
            self.assertNotIn(AUTOPSY, codes(candidate))
            self.assertIn(CIRCULAR, codes(candidate))

    def test_duplicate_ids_do_not_supply_dependency_to_an_independent_row(self):
        p = fixture()
        duplicate = deepcopy(observations(p)[0])
        observations(p).append(duplicate)
        observations(p)[8]['depends_on'] = ['O0']
        result = run(p)
        self.assertEqual({row['id'] for row in result['held_observations']}, {'O0', 'O8'})
        self.assertNotIn(SUSCEPTIBILITY, codes(p))
        self.assertIn(CIRCULAR, codes(p))

    def test_invalid_duplicate_also_quarantines_other_occurrence(self):
        p = fixture()
        duplicate = dict(observations(p)[0], kind='UNKNOWN')
        observations(p).append(duplicate)
        self.assertNotIn(AUTOPSY, codes(p))
        self.assertEqual(len([row for row in run(p)['held_observations'] if row['id'] == 'O0']), 2)

    def test_duplicate_remediation_events_cannot_select_first_state(self):
        p = fixture()
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'REVIEW_GRANTED')
        events = p['support_reviews'][0]['remediation_events']
        events.append(dict(events[0], type='ACCESS_PERFORMED'))
        for ordered in (events, list(reversed(events))):
            p['support_reviews'][0]['remediation_events'] = ordered
            result = run(p)['remediation']
            self.assertEqual(result['question_material_states'], [])
            self.assertEqual(len(result['held_events']), 2)

    def test_duplicate_remedy_does_not_erase_other_valid_event(self):
        p = fixture()
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'REVIEW_GRANTED')
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E2', 'ACCESS_PARTIAL')
        events = p['support_reviews'][0]['remediation_events']
        events.append(deepcopy(events[0]))
        result = run(p)['remediation']
        self.assertEqual(result['question_material_states'][0]['event_history'], ['SYNTHETIC-E2'])
        self.assertEqual(result['question_material_states'][0]['status'], 'PARTIAL_ACCESS_REPORTED_REMAINDER_OPEN')
        self.assertTrue(result['prior_burdens_preserved'])

    def test_remedy_source_and_event_require_explicit_scope(self):
        for area in ('event', 'source'):
            for field in ('case_id', 'track_id', 'subject_id'):
                p = fixture()
                original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'REVIEW_GRANTED')
                obj = (p['support_reviews'][0]['remediation_events'][0] if area == 'event'
                       else p['sources']['REMEDY-SYNTHETIC-E1'])
                del obj[field]
                self.assertEqual(run(p)['remediation']['question_material_states'], [])
                self.assertEqual(len(codes(p)), 5)

    def test_conflicting_source_actor_role_or_decision_status_held(self):
        for field, value in (('actor_role', 'OPPONENT'), ('decision_status', 'REQUEST_ONLY')):
            p = fixture()
            p['sources']['SOURCE-3'][field] = value
            self.assertNotIn(CIRCULAR, codes(p))
            self.assertIn(AUTOPSY, codes(p))
            self.assertTrue(any('ATTRIBUTION_CONFLICT_' + field.upper() in row['reason']
                                for row in run(p)['held_observations']))

    def test_nested_actor_conflict_cannot_override_direct_actor(self):
        p = fixture()
        p['sources']['SOURCE-3']['metadata'] = {'actor_id': 'SYNTHETIC-OTHER-COURT'}
        self.assertNotIn(CIRCULAR, codes(p))
        self.assertIn(AUTOPSY, codes(p))

    def test_nonproduction_source_actor_cannot_be_renamed_to_another_controller(self):
        p = fixture()
        p['support_reviews'][0]['controller'] = 'SYNTHETIC-OTHER-CONTROLLER'
        self.assertNotIn(CIRCULAR, codes(p))
        self.assertNotIn(PATTERN, codes(p))
        self.assertIn(AUTOPSY, codes(p))

    def test_explicit_review_scope_applies_to_remedy_events(self):
        for key, value in (('material_id', 'SYNTHETIC-AUTOPSY'),
                           ('question_id', 'SYNTHETIC-OTHER-QUESTION')):
            p = fixture()
            original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'REVIEW_GRANTED')
            p['support_reviews'][0][key] = value
            result = run(p)['remediation']
            self.assertEqual(result['question_material_states'], [])
            self.assertIn('EVENT_REVIEW_' + key.upper() + '_UNLINKED',
                          result['held_events'][0]['reason'])

    def test_whitespace_remedy_identifiers_are_invalid_even_when_linked(self):
        for key in ('question_id', 'material_id', 'subject_id'):
            p = fixture()
            original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'REVIEW_GRANTED')
            event = p['support_reviews'][0]['remediation_events'][0]
            event[key] = p['sources'][event['source_ref']][key] = ' '
            self.assertEqual(run(p)['remediation']['question_material_states'], [])
            self.assertEqual(len(run(p)['remediation']['held_events']), 1)

    def test_nested_question_cannot_invent_missing_item_question(self):
        p = fixture()
        observations(p)[0]['metadata'] = {'question_id': 'SYNTHETIC-Q1'}
        p['sources']['SOURCE-0']['metadata'] = {'question_id': 'SYNTHETIC-Q2'}
        self.assertNotIn(AUTOPSY, codes(p))
        self.assertEqual(len(run(p)['held_observations']), 1)
        self.assertIn(CIRCULAR, codes(p))

    def test_nested_opponent_request_in_observation_cannot_be_court_refusal(self):
        p = fixture()
        observations(p)[3]['metadata'] = {'actor_id': 'SYNTHETIC-OPPONENT',
                                         'event_type': 'REQUEST',
                                         'statement_role': 'OPPONENT_CLAIM'}
        self.assertNotIn(CIRCULAR, codes(p))
        self.assertNotIn(PATTERN, codes(p))
        self.assertIn(AUTOPSY, codes(p))
        self.assertEqual(len(run(p)['held_observations']), 1)

    def test_explicit_source_remedy_type_cannot_turn_grant_into_access(self):
        for field in ('type', 'event_type'):
            for nested in (False, True):
                for area in ('event', 'source'):
                    if area == 'event' and field == 'type' and not nested:
                        continue
                    p = fixture()
                    original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'ACCESS_PERFORMED')
                    event = p['support_reviews'][0]['remediation_events'][0]
                    obj = event if area == 'event' else p['sources'][event['source_ref']]
                    if nested:
                        obj['metadata'] = {field: 'REVIEW_GRANTED'}
                    else:
                        obj[field] = 'REVIEW_GRANTED'
                    result = run(p)['remediation']
                    self.assertEqual(result['question_material_states'], [])
                    self.assertEqual(len(result['held_events']), 1)
                    self.assertEqual(len(codes(p)), 5)

    def test_matching_explicit_source_remedy_type_remains_accepted(self):
        p = fixture()
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'ACCESS_PARTIAL')
        p['sources']['REMEDY-SYNTHETIC-E1'].update(type='ACCESS_PARTIAL', event_type='ACCESS_PARTIAL')
        result = run(p)['remediation']
        self.assertEqual(result['held_events'], [])
        self.assertEqual(result['question_material_states'][0]['status'],
                         'PARTIAL_ACCESS_REPORTED_REMAINDER_OPEN')

    def test_nested_review_scope_conflict_does_not_erase_sibling_review(self):
        p = fixture()
        sibling = deepcopy(p['support_reviews'][0])
        sibling['id'] = 'SYNTHETIC-SIBLING'
        p['support_reviews'].append(sibling)
        p['support_reviews'][0]['metadata'] = {'subject_id': 'SYNTHETIC-OTHER-PERSON'}
        reports = evaluate(p)['reviews']
        self.assertEqual(reports[0]['status'], 'REVIEW_SCOPE_HELD')
        self.assertEqual(reports[0]['warnings'], [])
        self.assertEqual(len(reports[1]['warnings']), 5)
        self.assertEqual(len(reports[1]['accepted_observations']), 9)

    def test_simultaneous_conflicting_remedies_are_not_ordered_by_id(self):
        for first, second in (('ACCESS_REVOKED', 'ACCESS_PERFORMED'),
                              ('ACCESS_PERFORMED', 'ACCESS_REVOKED')):
            p = fixture()
            original_tests.GuardTests().add_event(p, 'SYNTHETIC-A', first)
            original_tests.GuardTests().add_event(p, 'SYNTHETIC-Z', second)
            result = run(p)['remediation']
            state = result['question_material_states'][0]
            self.assertEqual(state['status'], 'SIMULTANEOUS_CONFLICT_REVIEW_OPEN')
            self.assertTrue(state['latest_event_order_ambiguous'])
            self.assertEqual(state['event_history'], ['SYNTHETIC-A', 'SYNTHETIC-Z'])
            self.assertTrue(state['event_batches'][0]['conflicting_types'])
            self.assertFalse(state['event_batches'][0]['order_within_timestamp_established'])
            self.assertEqual(result['held_events'], [])

    def test_genuine_later_timestamp_resolves_latest_reported_state_only(self):
        p = fixture()
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'ACCESS_REVOKED')
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E2', 'ACCESS_PERFORMED')
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E3', 'ACCESS_PARTIAL',
                                             '2026-11-02T12:00:00+09:00')
        result = run(p)['remediation']
        state = result['question_material_states'][0]
        self.assertEqual(state['status'], 'PARTIAL_ACCESS_REPORTED_REMAINDER_OPEN')
        self.assertFalse(state['latest_event_order_ambiguous'])
        self.assertTrue(state['event_batches'][0]['conflicting_types'])
        self.assertEqual(len(state['event_history']), 3)
        self.assertFalse(result['access_truth_independently_authenticated'])
        self.assertTrue(result['prior_burdens_preserved'])

    def test_same_instant_with_different_timezones_is_conflicting(self):
        p = fixture()
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'ACCESS_REVOKED',
                                             '2026-11-01T12:00:00+09:00')
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E2', 'ACCESS_PERFORMED',
                                             '2026-11-01T03:00:00+00:00')
        state = run(p)['remediation']['question_material_states'][0]
        self.assertEqual(state['status'], 'SIMULTANEOUS_CONFLICT_REVIEW_OPEN')
        self.assertEqual(len(state['event_batches']), 1)

    def test_same_type_simultaneous_events_are_preserved_without_false_conflict(self):
        p = fixture()
        for eid in ('SYNTHETIC-E1', 'SYNTHETIC-E2'):
            original_tests.GuardTests().add_event(p, eid, 'ACCESS_PARTIAL')
        state = run(p)['remediation']['question_material_states'][0]
        self.assertEqual(state['status'], 'PARTIAL_ACCESS_REPORTED_REMAINDER_OPEN')
        self.assertFalse(state['latest_event_order_ambiguous'])
        self.assertEqual(len(state['event_history']), 2)
        self.assertFalse(state['event_batches'][0]['order_within_timestamp_established'])

    def test_held_remedy_sets_unresolved_provenance_summary(self):
        p = fixture()
        original_tests.GuardTests().add_event(p, 'SYNTHETIC-E1', 'ACCESS_PERFORMED')
        p['sources']['REMEDY-SYNTHETIC-E1']['event_type'] = 'REVIEW_GRANTED'
        result = run(p)
        self.assertEqual(result['held_observations'], [])
        self.assertEqual(len(result['remediation']['held_events']), 1)
        self.assertTrue(result['unresolved_source_and_provenance_questions'])

    def test_labels_and_research_results_never_change_approval_or_findings(self):
        result = evaluate(fixture())
        self.assertFalse(result['release_or_R3_approval_changed'])
        self.assertFalse(result['legal_or_medical_finding'])
        self.assertFalse(result['external_execution'])
        self.assertTrue(result['axioms_AX01_to_AX09_unchanged'])
        self.assertTrue(result['civic_trace_045_maintained'])
        self.assertTrue(result['civic_trace_046_approval_deferred'])
        self.assertIsNone(result['total_score'])
        for row in result['reviews'][0]['accepted_observations']:
            self.assertFalse(row['source_truth_authenticated'])
            self.assertFalse(row['label_semantically_verified'])

    def test_warning_provenance_basis_is_context_homogeneous(self):
        result = run(fixture())
        rows = {row['id']: row for row in result['accepted_observations']}
        for warning in result['warnings']:
            for oid in warning['basis_observations']:
                for key, value in warning['context'].items():
                    self.assertEqual(rows[oid][key], value)
                self.assertIn(rows[oid]['source_ref'], warning['source_refs'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
