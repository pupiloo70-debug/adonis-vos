from pathlib import Path
import json,subprocess,hashlib,sys
new=Path(__file__).resolve().parents[1]
base=new/'evidence/baseline'
env=json.loads((new/'examples-autopsy-access.json').read_text())
p=new/'evidence/comparison-input.json';p.write_text(json.dumps(env['project'],ensure_ascii=False,indent=2)+'\n')
results={}
for name,folder in [('before',base),('after',new)]:
 command=[sys.executable,'-B',str(folder/'vos_verify.py'),str(p),'--now',env['now']]
 c=subprocess.run(command,capture_output=True,text=True,check=True,cwd=folder)
 data=json.loads(c.stdout);out=new/'evidence'/('comparison-'+name+'.json');out.write_text(c.stdout)
 packet=data['support_packet'];warnings={w['code'] for w in data.get('procedural_warnings',[])}
 checks={
 'autopsy_exclusion_review': 'AUTOPSY_EVIDENCE_EXCLUSION_WARNING' in warnings,
 'circular_burden_shift_review': 'CIRCULAR_BURDEN_SHIFT_WARNING' in warnings,
 'source_linked_cartel_pattern_warning': 'HARM_BURIAL_JUDICIAL_CARTEL_PATTERN_WARNING' in warnings,
 'no_generated_blanket_concession_in_submission_draft': '자료 미확보는 곧바로 사실 부존재' not in packet['draft_text'],
 'controller_concession_and_benefit_review': any(r.get('institutional_concession_candidates') and r.get('benefit_reversal_review',{}).get('status')=='COUNSEL_REVIEW_REQUIRED'for r in packet.get('access_reviews',[])),
 }
 results[name]={'version':data['version'],'command':command,'exit_code':c.returncode,'stdout_sha256':hashlib.sha256(c.stdout.encode()).hexdigest(),'checks':checks,'pass_count':sum(checks.values()),'check_count':len(checks),'automatic_approval':data['approval_status_changed'],'total_score':data['total_score']}
record={'scope':'SYNTHETIC_COUNTEREXAMPLE_COMPARISON_NOT_INDEPENDENT_PERFORMANCE_BENCHMARK','input':'comparison-input.json','input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'results':results}
(new/'evidence/before-after-review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{'version':v['version'],'passed':v['pass_count'],'total':v['check_count']}for k,v in results.items()},indent=2))
