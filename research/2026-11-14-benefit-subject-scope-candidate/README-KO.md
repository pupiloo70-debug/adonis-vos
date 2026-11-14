# Adonis VOS 0.3 · 2026-11-14 신규 P04 수혜자 범위 정정 후보

상태: **LOCAL_SYNTHETIC_CANDIDATE / GITHUB_NOT_WRITTEN / NOT_RELEASED**

## 신규 발견
2026-11-14 확인한 공개 `main`(`01d8fe089e15025b6ddfeabdd893265c87d1446f`)의 `purpose-review.mjs`에서 지원 실적의 `r.beneficiary_id`와 `outcome.beneficiary_id`가 서로 같아도 **현재 평가 대상 `input.subject_id`와 같은 사람인지 확인하지 않는 문제**를 확인했다. 합성 사례에서 `SYN-PERSON-A` 사건의 `SYN-PERSON-B` 수령 자료가 `MATERIAL_OUTCOME_EVIDENCE_LINKED_REVIEW_PENDING`으로 표시된다. 최종 실제 수령 인증 상태(false)까지 올라간 것은 아니지만, 출처 연결 대기 분류가 잘못된 대상에게 귀속되었다.

이는 코드의 **합성 입력 분류 결함**이며 실제 기관의 기망·법적 책임·백신 피해에 대한 판단이 아니다.

## 검토한 공개 코드와 현재 기준
- 최신 `main`: `01d8fe089e15025b6ddfeabdd893265c87d1446f` (커밋 2026-11-13 19:20:49 UTC)
- `purpose-review.mjs` Git blob: `eb37ee2075829ce46f9be998aceae616d9d66290`
- `authority-duty.mjs` Git blob: `fa12749f7e68c62474a235ce1aefa1c9e9398f6a`
- 공개 `purpose-review.test.mjs` Git blob: `bd4785afd5570549a240383652e3a51325550c5e`
- 공개 `material-outcome.test.mjs` Git blob: `006053f96917f326cc7ddd8f6fdfbaed07a30423`
- correction.3 `bridge.mjs`: `a54dff90be1d621cd405d813c98bc67dc854de1b` (42122a7 기준 대비 동일)
- correction.4 `correction4_guard.py`: `cd165d4267c1f3958e3103ce2876756fe387c91f` (42122a7 기준 대비 동일)
- 통합 v1 `core_guard.mjs`: `32e24c3f13b4871b04ae281cbf9db9610b392e2b` (42122a7 기준 대비 동일)

## 실제 실행 결과 (Node.js v22.16.0)
1. 공개 테스트 원본 15개 + 2026-11-13 공개 material-outcome 테스트 18개 + **신규 합성 P04/P02 반례 5개** = 38개.
2. 공개 원본 코드: **33 PASS / 5 FAIL**, exit code 1. 기존 공개 시험 33개는 전부 통과했고 **이번 신규 반례 5개만 실패**했다.
3. 최소 패치의 `git apply --check` exit code 0, `git apply` exit code 0.
4. 깨끗한 복제본에 패치 적용 후 같은 명령: **38 PASS / 0 FAIL**, exit code 0.
5. 공개 `authority-duty.mjs` 및 공개 테스트 원본 바이트의 Git blob SHA를 지역 복제본에서 재계산·대조했다. 공개 `purpose-review.mjs`도 10012바이트로 SHA 대조 완료.
6. 본 패치는 **독립 목적함수 연구 후보**에 한정. 중앙코어 통합 33/별도 감사 35/guard68은 선행 과거 기록이며 **이번 재실행 아님**. correction.3 Python·guard 전체 및 v1/v2 Node→Python 전체는 **이번 실행에서 미검증**.

## 최소 정정 내용
- 합성 입력에 현재 `subject_id`가 명시된 경우, 지원 기록과 출처 레코드 양측의 `subject_id`가 모두 현재 대상과 같아야 링크 대기로 인정한다.
- 불일치·누락이면 **해당 수혜 기록만** `BENEFIT_SUBJECT_SCOPE_REVIEW_OPEN`으로 남긴다. 독립적인 유효 수혜 기록과 자료 통제자 설명 업무를 보존한다.
- 입력에 `subject_id`가 없는 레거시 문서는 기존 호환 출력을 유지하되 `SUBJECT_SCOPE_NOT_SUPPLIED`로 별도 표시하며, 실수령 확정은 하지 않는다.

## 수동 재현 (공개 저장소의 새 연구용 복제본에서만)
원 공개 `main`이 위 커밋과 **정확히 동일**한지 먼저 확인한다. 새 main이면 패치를 무조건 적용하지 말고 원문·충돌을 검토한다.

```bash
# 저장소 루트에서
 git apply --check research/2026-11-14-benefit-subject-scope-candidate/candidate.patch
 git apply research/2026-11-14-benefit-subject-scope-candidate/candidate.patch
 cp research/2026-11-14-benefit-subject-scope-candidate/purpose-subject-scope-regression.test.mjs research/2026-11-11-authority-duty-purpose-candidate/
 cd research/2026-11-11-authority-duty-purpose-candidate
 node --test purpose-review.test.mjs material-outcome.test.mjs purpose-subject-scope-regression.test.mjs
```

이 패키지는 GitHub에 자동 업로드하지 않았고 어느 파일도 운영 배포하지 않았다.

## 추가로 발견된 공개 상태 불일치 (미수정)
`research/2026-11-13-r3-gated-integration-decision/`에서 `STATUS-AND-IMPORT-KO.md` 및 `EXECUTION-MANIFEST.json`은 설계 `APPROVED_AND_INTEGRATING`을 표시하지만 `README-KO.md`, `DECISION-KO.md`에는 이전 `R3_APPROVAL_PENDING` 문구가 남아 있다. 공개 기록의 버전별 승인 범위를 구분하여 정정할 필요가 있다. 이는 **A-R3 기본 경로 연결 증명이나 운영 출시가 아니다**. `default_path_connected=false`는 유지.

## 보존 경계
R3 최종 해석권·승인권 유지, AX-01~09 불변, CIVIC-TRACE 0.4.5 유지, 0.4.6 보류, `total_score=null`. 원자료 확인 → 권한·의무 → 이행 → 책임 → 법률 요건 충족 시에만 불리추정 검토. No automatic guilt/immunity/benefit from obstruction. 실제 사건·비공개 자료·사적 대화 미사용, 모든 테스트 식별자는 SYN으로 시작하는 가상 데이터다.
