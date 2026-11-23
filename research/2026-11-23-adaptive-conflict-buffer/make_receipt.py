import hashlib,json,os,datetime,platform,subprocess,pathlib,tempfile,uuid
p=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
files=['buffer_gate.py','test_buffer_gate.py','stdout.log','stderr.log','exit_code.txt']
now=datetime.datetime.now(datetime.timezone.utc)
scenarios=[
('R01','Institution says missing original proves claimant false','MISSING_ORIGINAL_REMAINS_OPEN'),
('R02','Self-certification labeled independent','NO_INDEPENDENT_VERIFICATION'),
('R03','No-record reply implies record never made','PRESERVE_CREATION_UNKNOWN'),
('R04','Trade secret blocks all explanation','RIGHT_TO_REVIEW_REMAINS_OPEN'),
('R05','Internal review described as independent','INDEPENDENCE_NOT_PROVEN'),
('R06','Unknown cause asserted as excluded causal link','CAUSALITY_UNRESOLVED'),
('R07','Partial compensation closes all inquiries','UNRESOLVED_REMEDY_PRESERVED'),
('R08','Evidence motion rejected means evidence worthless','EVIDENCE_VALUE_NOT_DECIDED'),
('R09','Evidence lost implies controller immunity','PRESERVATION_DUTIES_REVIEW'),
('R10','Three AI outputs treated as independent proof','NO_INDEPENDENT_PROOF'),
]
(p/'SPEC_ONLY_10.json').write_text(json.dumps([{'id':i,'synthetic_attack':a,'expected':b,'implemented_test':False} for i,a,b in scenarios],ensure_ascii=False,indent=2)+'\n')
files.append('SPEC_ONLY_10.json')
manifest={
 'run_id':'ADONIS-BUFFER-'+now.strftime('%Y%m%dT%H%M%SZ'),
 'utc':now.isoformat(),'kst':now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
 'main_commit_sha':'c6a6567ae4401d77c0dc6c3e4d143aa37ba084d5',
 'integration_reference_commit':'42122a759b1bdf9d9c4d692988ea7320cd983a72',
 'source_read':'GitHub connector, not an executable repository clone',
 'runtime':platform.python_version()+' '+platform.platform(),
 'command':'python -B -m unittest -v test_buffer_gate',
 'command_sha256':sha(b'python -B -m unittest -v test_buffer_gate'),
 'files_sha256':{f:sha((p/f).read_bytes()) for f in files},
 'input_fixture_sha256':sha((p/'test_buffer_gate.py').read_bytes()),
 'pre_edit_sha256':None,'post_edit_sha256':sha((p/'buffer_gate.py').read_bytes()),
 'patch_sha256':None,
 'stdout_path':'stdout.log','stdout_sha256':sha((p/'stdout.log').read_bytes()),
 'stderr_path':'stderr.log','stderr_sha256':sha((p/'stderr.log').read_bytes()),
 'exit_code':int((p/'exit_code.txt').read_text()),
 'expected':'14 synthetic gate unit tests pass; protected fields unchanged',
 'actual':'Ran 14 tests; OK (see stderr.log)',
 'passed':14,'failed':0,'unexecuted_spec_scenarios':10,
 'reused_prior_results':False,'code_change_scope':'standalone prototype only; not GitHub repo',
 'source_file_before_sha256':None,'source_file_after_sha256':None,
 'rollback_status':'NOT_REQUIRED_NO_EXISTING_CODE_EDIT',
 'retest_reference':None,'previous_receipt_sha256':None,
 'traceability_status':'STANDALONE_TRACEABLE_NOT_CHAINED_TO_PRIOR_RUN',
 'status':'LOCAL_SPEC_PROTOTYPE_ONLY', 'external_action':False,'total_score':None}
f=p/'EXECUTION-MANIFEST.json'
data=json.dumps(manifest,ensure_ascii=False,indent=2).encode()+b'\n'
fd,tmp=tempfile.mkstemp(dir=p,prefix='.receipt-')
with os.fdopen(fd,'wb') as w:w.write(data);w.flush();os.fsync(w.fileno())
assert sha(pathlib.Path(tmp).read_bytes())==sha(data)
os.replace(tmp,f)
(p/'SHA256SUMS').write_text(''.join(f'{sha((p/n).read_bytes())}  {n}\n' for n in files+['EXECUTION-MANIFEST.json']))
(p/'README-KO.md').write_text('''# Adonis VOS 0.3 충돌 완충 게이트 — 로컬 합성 연구 후보\n\n- 기준 main: `c6a6567ae4401d77c0dc6c3e4d143aa37ba084d5` (GitHub connector 조회)\n- 참고: 공개 CentralCore, correction.3, correction.4 guard, RFC-002-FAILSAFE\n- 시험: `python -B -m unittest -v test_buffer_gate` (14건 통과)\n- 추가 순환 논리 명세 10건은 **SPEC_ONLY**, 실행 0건.\n- 이 패키지는 기존 중앙코어 파일을 수정하거나 실행한 결과가 아님. 별도 연구용 게이트 모형임.\n- `REVERT`는 실제 파일 롤백 수행이 아니라, 롤백 요구 **결정값**만 뜻함.\n- `next_exploration_budget`의 1~2는 합성 시연용 예산이며 성능 개선률·승인된 임계값이 아님.\n- 추후 통합할 경우 보호 필드·변경 권한을 실제 Git diff 및 잠긴 외부 검증기에서 확인해야 하며, 현재 `changes` 텍스트만으로는 우회 가능함.\n- 기술 검증, 시민 권리 검증의 이중 게이트를 유지하고, 외부 배포·공리 수정·법적 유죄 판단은 하지 않음.\n- 실행 영수증은 현 회차만 기록했으며 이전 체인과의 연결은 미검증.\n''')
print(manifest['run_id'],sha(f.read_bytes()))
