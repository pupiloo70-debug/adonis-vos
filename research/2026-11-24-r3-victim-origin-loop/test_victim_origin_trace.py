import unittest, json
from pathlib import Path
from victim_origin_trace import review
DATA=json.loads((Path(__file__).parent/'SYNTHETIC-ATTACKS-12.json').read_text())
class Attacks(unittest.TestCase):
    pass
for row in DATA:
    def check(self,r=row):
        obj=review(r['input']); self.assertEqual(obj['accepted'][0]['counsel_response'],r['expected']['response']);self.assertEqual(obj['accepted'][0]['unresolved'],r['expected']['unresolved']);self.assertIsNone(obj['total_score']);self.assertFalse(obj['automatic_guilt']);self.assertFalse(obj['automatic_immunity'])
    setattr(Attacks,'test_'+row['id'],check)
class GuardTests(unittest.TestCase):
    def test_scope_isolation(self):
        x=DATA[0]['input'].copy();x['issues']=list(x['issues'])+[dict(x['issues'][0],id='different',subject_id='B')]
        out=review(x);self.assertEqual(len(out['accepted']),1);self.assertEqual(out['held'][0]['reason'],'SCOPE_CONFLICT')
    def test_synthetic_only(self):
        with self.assertRaises(ValueError):review({'synthetic':False})
    def test_false_string_rejected(self):
        x=json.loads(json.dumps(DATA[0]['input']));x['issues'][0]['raw_evidence_verified']='false';self.assertEqual(review(x)['held'][0]['reason'],'VERIFICATION_FLAG_INVALID')
    def test_duplicate_is_held(self):
        x=json.loads(json.dumps(DATA[0]['input']));x['issues'].append(x['issues'][0]);self.assertEqual(len(review(x)['held']),1)
if __name__=='__main__':unittest.main()
