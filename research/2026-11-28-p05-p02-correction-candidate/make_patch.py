from pathlib import Path
import shutil, difflib, json
from run_receipts import atomic,record,sha,stamps,root,manifest,main,base
b=root/'baseline';c=root/'candidate';p=b/'correction4_guard.py';q=c/p.name
assert sha(p)=='1af214770c2068c97d5969a3321489699e26c5f6e75937372733fdf28cf1a56a'
s=p.read_text();out=s
old='''        if err:
            held.append({'id': eid, 'reason': sorted(set(err))})
        else:
            accepted.append({'id': eid, 'type': event['type'], 'question_id': event['question_id'],
                             'subject_id': event['subject_id'], 'material_id': event['material_id'],
                             'occurred_at': date, 'source_ref': event['source_ref'], '_sort': dt})'''
new='''        # A reported timestamp is not an independently authenticated event time.
        # If the linked source supplies an explicit time/attribution, it must
        # agree. Legacy sources lacking these fields remain report-only.
        time_binding = 'REPORTED_TIME_NOT_SOURCE_BOUND'
        if isinstance(source, dict):
            if 'occurred_at' in source:
                try:
                    source_dt = datetime.fromisoformat(source['occurred_at'])
                    if source_dt.tzinfo is None or source_dt.utcoffset() is None:
                        raise ValueError('naive source datetime')
                    if dt is None or dt != source_dt:
                        err.append('REMEDY_SOURCE_TIME_CONFLICT')
                    else:
                        time_binding = 'SOURCE_TIME_MATCHED_NOT_AUTHENTICATED'
                except (TypeError, ValueError, OverflowError):
                    err.append('INVALID_REMEDY_SOURCE_TIME')
            for key in ('actor_id', 'actor_role', 'statement_role'):
                if key in source and (not _identifier(source[key]) or source[key] != event.get(key)):
                    err.append('REMEDY_SOURCE_' + key.upper() + '_CONFLICT')
        if err:
            held.append({'id': eid, 'reason': sorted(set(err)),
                         'source_ref': event.get('source_ref'), 'occurred_at': date})
        else:
            accepted.append({'id': eid, 'type': event['type'], 'question_id': event['question_id'],
                             'subject_id': event['subject_id'], 'material_id': event['material_id'],
                             'occurred_at': date, 'source_ref': event['source_ref'], '_sort': dt,
                             'time_binding': time_binding})'''
assert out.count(old)==1;out=out.replace(old,new)
old="                'order_within_timestamp_established': len(batch) == 1,"
new="                'order_within_timestamp_established': len(batch) == 1,\n                'time_binding_by_event': {item['id']: item['time_binding'] for item in batch},"
assert out.count(old)==1;out=out.replace(old,new)
old='''    for review in review_list:
        if not isinstance(review, dict):
            continue
        review_target ='''
new='''    review_ids = Counter(r['id'] for r in review_list
                         if isinstance(r, dict) and _identifier(r.get('id')))
    for review_index, review in enumerate(review_list):
        if not isinstance(review, dict):
            reports.append({'id': None, 'review_index': review_index,
                            'status': 'REVIEW_SCOPE_HELD', 'held_reason': ['REVIEW_NOT_OBJECT'],
                            'warnings': [], 'accepted_observations': [], 'held_observations': [],
                            'remediation': {}, 'items_not_evaluated_due_to_review_scope': True})
            continue
        review_target ='''
assert out.count(old)==1;out=out.replace(old,new)
old='''        reasons = _scope_conflicts(review_metadata, review_target)
        for key in SCOPE_KEYS:'''
new='''        reasons = _scope_conflicts(review_metadata, review_target)
        rid = review.get('id')
        if not _identifier(rid) or review_ids[rid] > 1:
            reasons.append('INVALID_OR_DUPLICATE_REVIEW_ID')
        for key in SCOPE_KEYS:'''
assert out.count(old)==1;out=out.replace(old,new)
old="reports.append({'id': review.get('id'), 'status': 'REVIEW_SCOPE_HELD',"
new="reports.append({'id': review.get('id'), 'review_index': review_index, 'status': 'REVIEW_SCOPE_HELD',"
assert out.count(old)==1;out=out.replace(old,new)
start=stamps();prior=sha(manifest)
try:
 for f in b.glob('*.py'):
  if f.name!=p.name:atomic(c/f.name,f.read_bytes())
 atomic(q,out.encode());patch=root/'guard.patch';atomic(patch,''.join(difflib.unified_diff(s.splitlines(True),out.splitlines(True),fromfile='a/correction4_guard.py',tofile='b/correction4_guard.py')).encode())
 assert sha(p)=='1af214770c2068c97d5969a3321489699e26c5f6e75937372733fdf28cf1a56a'
 receipt={'run_id':'VOS-20261128-PATCH','started':start,'ended':stamps(),'main_commit':main,'baseline_commit':base,'command':['python','-B','make_patch.py'],'related_file_paths':['baseline/correction4_guard.py','candidate/correction4_guard.py','guard.patch'],'fixture_sha256':sha(root/'fixtures.json'),'pre_file_sha256':sha(p),'post_file_sha256':sha(q),'patch_sha256':sha(patch),'stdout':None,'stderr':None,'exit_code':0,'expected':'local candidate only; baseline preserved','actual':'candidate written and byte verified, pending retest','previous_manifest_sha256':prior,'traceability':'VERIFIED_LOCAL_BYTES','rollback':False,'rollback_reason':'NO_IN_PLACE_BASELINE_MODIFICATION','retest_pending':'logs/guard-after.receipt.json'}
 path=root/'logs'/'patch.receipt.json';record(path,receipt);m=json.loads(manifest.read_text());m['patch_receipt']={'path':str(path.relative_to(root)),'sha256':sha(path)};record(manifest,m)
except Exception:
 if q.exists():atomic(q,p.read_bytes())
 assert not q.exists() or sha(q)==sha(p)
 raise
