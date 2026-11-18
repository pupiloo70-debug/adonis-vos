# Adonis VOS 0.3 — 2026-11-18 합성 로컬 연구

상태: **LOCAL_SYNTHETIC_RESEARCH_CANDIDATE / NOT_RELEASED / NOT_INTEGRATED**.

## 오늘 새 문제와 해소 후보
11월 17일 로컬 증언 컨트롤러는 동일 배열 내부 의존성만 격리한다. 다른 배열(records→statements→remedies)에 있는 자료가 보류되더라도 의존 항목이 유지될 수 있으므로 새로운 typed dependency 연결이 필요하다. `reviewContextLinked()`는 기존 코어 변경 없이 명시 호출하는 추가 합성 연구 경로다. 의존성 `{"collection":"records","id":"REC1"}`의 범위를 검사하고, 유효하지 않거나 보류된 선행 항목·순환 항목 및 의존 항목을 격리한다. 독립적 정상 항목은 유지한다. **식별자 연결은 원문 인증이 아니다.**

## 실행 기록 (Node.js v22.16.0)
- 신규 수용시험 12건: 수정 전 0/12 (기능 미구현, 실패는 12개의 개별 결함을 뜻하지 않음), 수정 후 12/12.
- 전날 후보 회귀 41건: 원본 다시 실행 41/41, 수정 후 다시 실행 41/41.
- 전체 결합 53건: 53/53 (위 41+12의 합계; 추가 독립 세트가 아님).
- G1~G9의 순환 논리 등 별도 신규 **명세 12건 작성**, 코드 자동실행 0건. `ADVERSARIAL-SPEC-20261118.json` 참조.

재실행: `cd candidate && node --test testimony-controller.test.mjs adversarial.test.mjs item-level-12.test.mjs linked-12.test.mjs`.

메인 HEAD: `6e8afd5c8aa3023e48b85cc171f80d6be7828ade` (2026-11-15 UTC의 기존 커밋과 동일, 변경 0). 중앙코어 통합 기준: `42122a759b1bdf9d9c4d692988ea7320cd983a72` 이후 33커밋. 실제 공개 `vos_support.py`, `bridge.mjs`, guard, integration 코드를 GitHub 커넥터에서 확인했지만, GitHub 원본 전체 클론을 위한 외부 네트워크 접근이 실패하여 guard68, Python132, Bridge14, CentralCore24, 통합33/감사35 등을 실행한 것으로 주장하지 않는다. 중앙코어 통합 v1의 **역사적 로컬 연결 사실**을 부인하지 않으며, 새 후보와 통합 상태를 구분한다.

## 실효성 및 남은 위험
이 연구는 P02 의존성별 격리와 P03 출처-행위자 연결의 *형식 범위*만 추가로 점검한다. P01 실제 결정 귀속, P04 개인/검체 혼입, P05 후속 열람·부분 시정은 공개 guard/통합과 통합하지 않았다. G1~G9의 공식 번호별 정의는 확인되지 않아 사례를 임의 대응하지 않는다. 유효한 작업은 승인 재요구 없이 기술 연구 내에서 수행하되 규칙 승인·공개·릴리스는 R3 권한이다.

## 추적
`EXECUTION-MANIFEST.json`에 UTC/KST, 실행명령, fixture SHA256, 수정 전후 코드/패치/log SHA256, 통과/실패/미실행, 이전 로그 재사용 여부, 기준 커밋, 전 회차 manifest 연결을 기록한다. 파일 자체 해시는 `SHA256SUMS`에 분리되어 있다. 초기 탐색에서 발생한 사전 import 오류 로그는 덮어써 검증 불가이므로 성공으로 주장하지 않고 매니페스트에 기록했다. 이후 최종 적색시험 12건 실패와 패치 후 녹색시험 12건 통과는 각 별도 로그로 보존됐다.

**불변:** CIVIC-TRACE 0.4.5, 0.4.6 보류, AX-01~09, total_score=null, 자동 유죄/면책/방해 이익·불리추정 금지, R3 최종 승인권. 실사례·비공개 대화/의료/법원자료 사용 0건; GitHub 쓰기·외부 발송·운영 배포 없음.
