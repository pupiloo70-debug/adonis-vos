"""Independent read/test-only probes, distinct from the supplied 25 tests."""
from copy import deepcopy
import json
from correction4_guard import evaluate
from test_correction4_guard import fixture

results = []
p=fixture()
obs=p['support_reviews'][0]['observations']
# Individually linked sources, same person, different material for actual exclusion.
obs[2]['material_id']='SYNTHETIC-OTHER-MATERIAL'
p['sources']['SOURCE-2']['material_id']='SYNTHETIC-OTHER-MATERIAL'
r=evaluate(p)['reviews'][0]
results.append({'probe':'cross_material_combination','accepted':len(r['accepted_observations']),
'held':len(r['held_observations']),
'autopsy_exclusion_warning':any(w['code']=='AUTOPSY_EVIDENCE_EXCLUSION_WARNING' for w in r['warnings']),
'warning_basis_materials':[obs[0]['material_id'],obs[2]['material_id']]})

p=fixture()
p.pop('subject_id')
p['support_reviews'][0]['observations'][3]['subject_id']='SYNTHETIC-PERSON-B'
p['sources']['SOURCE-3']['subject_id']='SYNTHETIC-PERSON-B'
r=evaluate(p)['reviews'][0]
results.append({'probe':'missing_project_subject_cross_person','warning_codes':[w['code'] for w in r['warnings']],
'held':r['held_observations']})

p=fixture()
proto=deepcopy(p['support_reviews'][0]['observations'][7])
p['support_reviews'][0]['observations']=[
dict(proto,id='CHAIN-'+str(i),depends_on=['CHAIN-'+str(i+1)] if i<1199 else []) for i in range(1200)]
try:
    evaluate(p)
    results.append({'probe':'long_dependency_chain_1200','exception':None})
except Exception as exc:
    results.append({'probe':'long_dependency_chain_1200','exception':type(exc).__name__,'message':str(exc)})

p=fixture()
p['support_reviews'][0]['observations'][0]['id']='SAME'
extra=deepcopy(p['support_reviews'][0]['observations'][2])
extra['id']='SAME'
p['support_reviews'][0]['observations'].append(extra)
r=evaluate(p)['reviews'][0]
results.append({'probe':'duplicate_observation_ids_first_retained',
'accepted_ids':[o['id'] for o in r['accepted_observations']],
'held':[o for o in r['held_observations'] if o['id']=='SAME']})

print(json.dumps(results,indent=2))

