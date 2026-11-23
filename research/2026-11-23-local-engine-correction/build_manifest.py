from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib,json,os,platform,subprocess,tempfile,re
R=Path('/mnt/data/adonis-research-20261123')
sha=lambda b:hashlib.sha256(b).hexdigest()
def filehash(p):return sha((R/p).read_bytes())
now=datetime.now(timezone.utc)
kst=timezone(timedelta(hours=9))
def fmt(dt):return dt.isoformat(timespec='seconds')
run_id='ADONIS-0.3-20261123-ENGINE-PROVENANCE-LOCAL-01'
main='c6a6567ae4401d77c0dc6c3e4d143aa37ba084d5';baseline='42122a759b1bdf9d9c4d692988ea7320cd983a72'
commands=[
 ('PRE_CORE12','node src/test.mjs',12,0,0,0,'BEFORE_PATCH'),
 ('PRE_PROBE4','node --test tests/prototype-adversarial.test.mjs',2,2,0,1,'EXPECTED_RED'),
 ('POST_CORE12','node src/test.mjs',12,0,0,0,'AFTER_PATCH'),
 ('POST_PROBE4','node --test tests/prototype-adversarial.test.mjs',4,0,0,0,'AFTER_PATCH'),
]
tests=[]
for id,cmd,passed,failed,skipped,code,phase in commands:
 out=f'logs/{id}.stdout.log';err=f'logs/{id}.stderr.log'
 dt=datetime.fromtimestamp((R/out).stat().st_mtime,timezone.utc)
 tests.append({'test_id':run_id+'/'+id, 'phase':phase,'executed_utc':fmt(dt),'executed_KST':fmt(dt.astimezone(kst)),
 'command':cmd,'command_sha256':sha(cmd.encode('utf-8')),'working_dir':str(R),'exit_code':code,
 'stdout_path':out,'stdout_sha256':filehash(out),'stderr_path':err,'stderr_sha256':filehash(err),
 'expected':{'pass':4 if id.endswith('PROBE4') else 12,'fail':0},'actual':{'passed':passed,'failed':failed,'skipped':skipped,'unexecuted':0},
 'prior_results_reused':False,'classification':'EXPECTED_RED_PRE_PATCH' if phase=='EXPECTED_RED' else 'EXECUTED_PASS',
 'original_code_sha256':filehash('baseline/engine.mjs'),'changed_code_sha256':filehash('src/engine.mjs') if phase=='AFTER_PATCH' else None,
 'retest_reference':run_id+'/POST_PROBE4' if id=='PRE_PROBE4' else None})
manifest={'schema':'SGP-QSV-EXECUTION-MANIFEST/2026-11-14','run_id':run_id,
 'generated_utc':fmt(now),'generated_KST':fmt(now.astimezone(kst)),
 'previous_record_sha256':None, 'previous_record_reference':'research/2026-11-18-typed-dependency-local/EXECUTION-MANIFEST.json',
 'hash_chain_status':'UNLINKED_PREVIOUS_MANIFEST_BYTES_NOT_PRESENT_LOCAL; DO_NOT_CLAIM_CONTINUOUS_CHAIN',
 'main_commit_SHA':main,'baseline_commit_SHA':baseline,'prior_checked_main_SHA':'6e8afd5c8aa3023e48b85cc171f80d6be7828ade',
 'main_comparison':{'vs_integration_baseline':'+48 commits (connector compare)','vs_older_20261118_local_run':'+15 commits (connector compare)','latest_main_commit_date_utc':'2026-11-19T03:26:37Z'},
 'source_provenance':{'method':'GitHub connector fetch_file; content reconstructed exactly and verified as original Git blob hash; SHA-1 blob does not equal SHA-256',
 'paths':{'src/engine.mjs':{'git_blob_sha1':'43ad65aa1227fef66fd6e3ed7a939e32c7e0d089','raw_original_sha256':filehash('baseline/engine.mjs')},
 'src/test.mjs':{'git_blob_sha1':'1c9fbaf0bc24cf2718405cb1a82e082493aee9bc','raw_original_sha256':filehash('baseline/test.mjs')}},
 'repo_full_clone_available':False,'full_main_test_executed':False},
 'synthetic_fixture':'synthetic-adversarial-20261123.json','synthetic_fixture_sha256':filehash('synthetic-adversarial-20261123.json'),
 'adversarial_test_source':'tests/prototype-adversarial.test.mjs','adversarial_test_source_sha256':filehash('tests/prototype-adversarial.test.mjs'),
 'environment':{'node':subprocess.run(['node','--version'],capture_output=True,text=True).stdout.strip(),'python':platform.python_version(),'os':platform.platform(), 'dependencies':'node builtins; no external packages'},
 'fix':{'scope':'LOCAL_RESEARCH_ONLY; NOT_COMMITTED_NOT_DEPLOYED','source_file':'src/engine.mjs','original_sha256':filehash('baseline/engine.mjs'),'modified_sha256':filehash('src/engine.mjs'),
 'patch_file':'minimal-local.patch','patch_sha256':filehash('minimal-local.patch'),'issue':'Prototype inherited answer properties become reported evidence signals without an own source field',
 'minimal_change':'Require Object.hasOwn before reading each rule answer; preserve old null fallback',
 'before':'2 adversarial test failures / 2 passes','after':'4 adversarial test passes / 0 failures; original 12 checks continue passing',
 'rollback':{'required':False,'status':'NOT_PERFORMED; ORIGINAL SNAPSHOT SHA256 VERIFIED', 'original_snapshot':'baseline/engine.mjs','reason':'Patch accepted only as local research proposal; no unsafe traceability detected'},
 'retest_receipt_ref':run_id+'/POST_PROBE4'},
 'test_entries':tests,
 'adversarial_research':{'ten_governance_scenarios':'SPEC_ONLY (A01-A10), execution 0','additional_engine_attacks':'A11-A12 EXECUTED fail-before pass-after','existing_positive_controls':'A13-A14 EXECUTED pass-before and after',
 'G1_G9_official_definition': 'UNVERIFIED; no numbered mapping assigned'},
 'legacy_run_status':{'0.2_CentralCore_24':'UNVERIFIED_THIS_RUN','Python_132':'UNVERIFIED_THIS_RUN','Bridge_14':'UNVERIFIED_THIS_RUN','correction3':'UNVERIFIED_THIS_RUN','correction4_guard_68':'UNVERIFIED_THIS_RUN','integration_v1_33':'UNVERIFIED_THIS_RUN','independent_audit_35':'UNVERIFIED_THIS_RUN', 'legacy_0.1_engine_checks_12':'EXECUTED_PASS'},
 'rsi_candidate_20261120':'NOT_FOUND_IN_CURRENT_MAIN_TREE; existence in other branches not excluded',
 'policy_unchanged':{'CIVIC_TRACE':'0.4.5 retained; 0.4.6 deferred','AX_01_09':'UNCHANGED','total_score':None,'no_automatic_guilt_or_immunity':True,'no_benefit_from_obstruction':True,'R3_final_release_authority':True},
 'external_transmission':False,'github_write':False,'release':False,'production_deploy':False,'private_case_data_used':False,
 'source_limits':'Only verified exact 0.1 engine/test files recreated in runtime; not a full repository regression nor legal/medical evidence proof'}
p=R/'EXECUTION-MANIFEST.json'
b=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
tmp=R/'EXECUTION-MANIFEST.json.tmp'
tmp.write_bytes(b)
assert json.loads(tmp.read_text())==manifest
os.replace(tmp,p)
assert p.read_bytes()==b
# checksum file of all user deliverables; manifest self hash is outside the manifest.
checks=[x for x in sorted(R.rglob('*')) if x.is_file() and x.name not in ('SHA256SUMS','build_manifest.py')]
(R/'SHA256SUMS').write_text(''.join(f'{sha(x.read_bytes())}  {x.relative_to(R)}\n' for x in checks))
print('manifest_SHA256='+sha(b));print('total_receipts='+str(len(tests)));print('run_id='+run_id)
