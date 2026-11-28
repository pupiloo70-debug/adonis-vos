import sys, json, copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'baseline'))
from test_correction4_guard import fixture, GuardTests
root=Path(__file__).parent
cases=[]
def base():
 p=fixture(); g=GuardTests();g.add_event(p,'E1','ACCESS_REVOKED','2026-11-01T12:00:00+09:00');g.add_event(p,'E2','ACCESS_PERFORMED','2026-11-02T12:00:00+09:00');return p

def add(id,p,expected):cases.append({'id':id,'project':p,'expected':expected})
for ident,field,value in [('P05_source_earlier_time','occurred_at','2026-10-31T12:00:00+09:00'),('P05_source_later_time','occurred_at','2026-11-03T12:00:00+09:00'),('P05_source_naive_time','occurred_at','2026-11-02T12:00:00'),('P05_source_malformed_time','occurred_at',{'date':'2026-11-02'}),('P03_source_actor_missing_on_event','actor_id','SYNTHETIC-CONTROLLER'),('P01_source_role_missing_on_event','statement_role','CONTROLLER_RECORD')]:
 p=base();p['sources']['REMEDY-E2'][field]=value;add(ident,p,'HOLD_E2')
for ident,field,ev,src in [('P03_remedy_actor_mismatch','actor_id','SYNTHETIC-OPPONENT','SYNTHETIC-CONTROLLER'),('P01_remedy_statement_mismatch','statement_role','DECISION_RECORD','OPPONENT_CLAIM'),('P01_remedy_actor_role_mismatch','actor_role','DECISION_BODY','WITNESS')]:
 p=base();p['support_reviews'][0]['remediation_events'][1][field]=ev;p['sources']['REMEDY-E2'][field]=src;add(ident,p,'HOLD_E2')
p=base();p['support_reviews'].insert(0,None);add('P02_malformed_review_not_silent',p,'HOLD_MALFORMED')
p=base();r=copy.deepcopy(p['support_reviews'][0]);ind=copy.deepcopy(r);ind['id']='R2';p['support_reviews']+=[r,ind];add('P02_duplicate_review_no_first_winner',p,'HOLD_DUPLICATE')
p=base();p['sources']['REMEDY-E2']['occurred_at']='2026-11-02T03:00:00Z';add('CONTROL_equivalent_utc_offset',p,'ACCEPT_BOUND')
p=base();add('CONTROL_legacy_no_explicit_time',p,'ACCEPT_LEGACY_UNBOUND')
p=base();p['sources']['REMEDY-E2']['subject_id']='SYNTHETIC-PERSON-B';add('CONTROL_P04_foreign_subject',p,'HOLD_E2')
(root/'fixtures.json').write_text(json.dumps(cases,indent=2)+'\n')
