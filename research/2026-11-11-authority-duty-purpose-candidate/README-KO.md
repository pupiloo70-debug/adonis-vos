# Adonis VOS 0.3 · 2026-11-11 합성 연구 정정 후보

상태: `LOCAL_SYNTHETIC_CANDIDATE / NOT_INTEGRATED / NOT_RELEASED`

## 오늘의 신규 발견

대상은 최신 `main`의 독립 후보 `research/2026-11-10-authority-duty-candidate/authority-duty.mjs`이다. 공개 기준 커밋 `ff769045dc7d8f0f6d2a0ed48a192d3ff6116561`의 공개 파일과 이 패키지의 `authority-duty.original.mjs`의 SHA-256이 동일하다 (`0aa43c2a8aa45c40360e32931795fb2adc51c973ea9bf11f69bafcd3929e50ca`).

**결함 ID:** `AUTHORITY_DUTY_SIMULTANEOUS_RESPONSE_ID_SORT_001` (Correction4 P05).

동일 시각에 두 개의 독립 출처로 `CORE_ACCESS_VERIFIED`와 `REFUSAL`이 들어오면 기존 함수는 이벤트 ID의 사전순을 근거로 마지막 응답을 결정한다. 어느 사건·질문·출처·시각도 바뀌지 않은 상태에서 이벤트 ID만 서로 바꾸어도 `REFUSAL_RECORDED` ↔ `VERIFIED_FOR_THIS_QUESTION`으로 결과가 뒤집혔다. 이것은 **실제 기관이 잘못했다는 증거가 아니라 로컬 합성 후보 코드의 상태 귀속 결함**이다.

Correction4의 공개 guard 후보는 동일 시각에 상충하는 종류가 들어오면 `SIMULTANEOUS_CONFLICT_REVIEW_OPEN`으로 처리한다. 독립 authority-duty 연구 후보에는 이 처리 원칙이 누락돼 있었다. 두 후보가 실제 중앙코어에 결합되었다고 가정하지 않는다.

## 최소 변경

`candidate.patch`는 가장 최근 수신 요청 이후의 응답을 보존한 채, 최신 시각에 동시 기록된 **상이한 응답 종류**가 있는지 확인한다. 종류가 충돌하면 `SIMULTANEOUS_RESPONSE_CONFLICT_REVIEW_OPEN`으로 표시하고, 추가 출처·시각순서 대조 과제를 생성한다. 이 상태만으로 의무 불이행 심사나 검증 완료를 확정하지 않는다. 다른 정상 기록, 이전 부담, 미해결 질문 및 허용 연구 지원은 유지한다.

`candidate.patch`는 저장소 루트에서 `git apply --check candidate.patch`로 적용 가능 여부를 확인하고, 별도 연구 브랜치 등에서 `git apply candidate.patch`로 검토할 수 있도록 실제 저장소 경로를 사용한다. **이 연구에서는 GitHub에 적용하지 않았다.**

## 시험 결과

- 공개에 등록된 기존 Node 21개 시험의 완전 동일 소스 재구성 및 SHA-256 확인 → 재실행 **21/21 통과** (Node v22.16.0).
- 신규 합성 반례 8개 추가 후, 원본 소스로 **29개 중 27개 통과·2개 실패**, 정상 원인 재현.
- 동일 29개 입력을 최소 패치에 재시험 → **29/29 통과**. 새 반례 8개만 따지면 수정 전 6/8, 수정 후 8/8.
- 깨끗한 파일 사본에 `git apply --check` / `git apply` 성공, 패치 결과 SHA-256이 시험에 사용한 수정본과 일치.
- 이전 통합 33·독립감사 35·guard 68은 **이번 실행하지 않은 과거 기록**. 동일 시험 재실행 횟수를 독립 사례 수로 합산하지 않는다.

재현: 패키지를 풀고 현재 폴더에서 `node --test authority-duty.test.mjs simultaneous-response.test.mjs`. 수정 전 재현은 `authority-duty.original.mjs`를 사본의 `authority-duty.mjs`로 지정해서 실행한다. `comparison.json`에 변조별 입력·출력을 기록했다. `verification-record.json`에 출처 버전, 실행 명령, 해시, 실패, 잔여 한계를 구분했다.

## 잔여 미검증

이 수정은 **응답들 사이의 같은 시각 충돌**만 다룬다. 수신 요청과 응답이 정확히 같은 시각인 사건의 선후관계, 잘못된 시계·소급 기록, 원자료 진위 및 사건별 법적 기한은 별도 검증 과제다. 동의·허용·자료 제공·실제 검증은 등치할 수 없다. 통제기관의 사실 설명책임을 유족에게 전가하지 않고, 사실 확인→권한·의무 이행→책임 심사→법정 요건 충족 시에만 불리추정 검토 순서를 유지한다.

이 패치는 독립 모듈의 범위만 다루며 **CentralCore/Correction3/Guard/v1 또는 v2 통합 실행을 새로 검증한 것이 아니다.** R3의 미래 적법한 설계·승인 가능성을 제한하지 않는다. AX-01~09 불변, CIVIC-TRACE 0.4.5 유지, 0.4.6 보류, `total_score=null`. No automatic guilt / immunity / benefit from obstruction.
