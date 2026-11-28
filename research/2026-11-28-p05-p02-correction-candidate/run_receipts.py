import subprocess,hashlib,json,os,datetime,platform,re,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
main='9bddb55a8f47a14adfa5c0360319602478e9389b';base='42122a759b1bdf9d9c4d692988ea7320cd983a72';prev='5945d89ae4bc2c536e0c7527f65969c0bb69bca71e73e81e84a95f543da9bc0b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 fd,tmp=tempfile.mkstemp(dir=p.parent,prefix='.tmp-')
 try:
  with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  assert Path(tmp).read_bytes()==b;os.replace(tmp,p);assert p.read_bytes()==b
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def record(p,x):atomic(p,(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def stamps():
 now=datetime.datetime.now(datetime.timezone.utc);return {'utc':now.isoformat(),'kst':now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat()}
def hashes(paths):return {str(p.relative_to(root)):sha(p) for p in paths}
manifest=root/'EXECUTION-MANIFEST.json'
if not manifest.exists():
 p=Path('/mnt/data/vos-20261127-daily/EXECUTION-MANIFEST.json');assert sha(p)==prev
 atomic(root/'previous-manifest.json',p.read_bytes())
 record(manifest,{'schema':'ADONIS-LOCAL-RESEARCH-EXECUTION/1.0','run_id':'VOS-20261128-P05-P02','main_commit':main,'baseline_commit':base,'previous_manifest_sha256':prev,'previous_manifest_local_copy':'previous-manifest.json','previous_results_reused_as_new_tests':False,'previous_source_bytes_reused_and_git_blob_verified':True,'source_transfer_reconstruction':'initial encoding transfer mismatch; discarded; final 43-test source exact Git blob match before execution','receipts':[],'scope':'LOCAL_SYNTHETIC_ONLY','default_path_connected':False,'repository_written':False,'total_score':None})
def run(name,cwd,cmd,paths,expected,prior=None,patch=None):
 for p in paths:assert p.is_file()
 start=stamps();inputs=hashes(paths);env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','PYTHONPATH':''};proc=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,timeout=60);end=stamps();out=root/'logs'/f'{name}.stdout.log';err=root/'logs'/f'{name}.stderr.log';atomic(out,proc.stdout);atomic(err,proc.stderr)
 text=(proc.stdout+proc.stderr).decode(errors='replace');m=re.search(r'Ran (\d+) tests?',text);f=re.search(r'FAILED \((.*?)\)',text);n=int(m[1]) if m else (12 if proc.returncode==0 and '12 core checks passed' in text else None);fail=0 if proc.returncode==0 else None
 if f:fail=sum(map(int,re.findall(r'(?:failures|errors)=(\d+)',f[1])))
 summary={'total':n,'passed':n-fail if n is not None and fail is not None else None,'failed':fail,'not_run':0 if n is not None else None}
 old=sha(manifest);receipt={'run_id':'VOS-20261128-'+name,'started':start,'ended':end,'main_commit':main,'baseline_commit':base,'related_file_paths':list(inputs),'fixture_and_source_sha256':inputs,'command':cmd,'cwd':str(cwd.relative_to(root)),'environment':{'python':sys.version,'node':subprocess.check_output(['node','-v'],text=True).strip(),'platform':platform.platform(),'synthetic_only':True},'pre_file_sha256':inputs,'post_file_sha256':hashes(paths),'patch_sha256':sha(patch) if patch else None,'stdout':{'path':str(out.relative_to(root)),'sha256':sha(out)},'stderr':{'path':str(err.relative_to(root)),'sha256':sha(err)},'exit_code':proc.returncode,'expected':expected,'actual':summary,'previous_result_reused':False,'traceability':'VERIFIED_LOCAL_BYTES','rollback':False,'rollback_reason':'NO_IN_PLACE_BASELINE_MODIFICATION','retest_of':prior,'previous_manifest_sha256':old}
 assert receipt['pre_file_sha256']==receipt['post_file_sha256'];r=root/'logs'/f'{name}.receipt.json';record(r,receipt);m=json.loads(manifest.read_text());m['receipts'].append({'path':str(r.relative_to(root)),'sha256':sha(r),'actual':summary,'exit_code':proc.returncode});record(manifest,m);print(name,proc.returncode,summary)
if __name__=='__main__':
 b=root/'baseline';c=root/'candidate';l=root/'legacy-core';fixtures=root/'fixtures.json'
 if sys.argv[1]=='before':
  run('legacy-core-12',l,['node','test.mjs'],list(l.glob('*.mjs')),'12 legacy core checks, not CentralCore 24')
  run('guard-before',b,['python','-B','-m','unittest','-v','test_correction4_guard','test_correction4_regressions','test_new_boundary'],list(b.glob('*.py'))+[fixtures],'68 historical tests plus 14 new attacks/controls; expect gaps in new assertions')
 else:
  run('guard-after',c,['python','-B','-m','unittest','-v','test_correction4_guard','test_correction4_regressions','test_new_boundary'],list(c.glob('*.py'))+[fixtures],'all 82 tests pass; no automatic adjudication',prior='logs/guard-before.receipt.json',patch=root/'guard.patch')
