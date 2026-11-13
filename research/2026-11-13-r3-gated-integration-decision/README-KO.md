# Adonis VOS 0.3 · R3 게이트 통합 설계 결정 후보

- 기준일: 2026-11-13 KST
- 기준 저장소: `pupiloo70-debug/adonis-vos`
- 기준 main SHA: `6503dddc2c67c54afacd9ad964720e3e102653a9` (읽기 시점 확인)
- 상태: `EXISTING_0_3_ADAPTERS_PRESENT / A_R3_GATE_PLANNED / A_R3_NOT_CONNECTED_TO_DEFAULT / NOT_RELEASED / R3_APPROVAL_PENDING`
- 파일 성격: **연구 설계 문서와 합성 반례 명세**. 운영 코드·기존 시험·기존 README 변경 없음.

## 기존 0.3 구현·통합 범위 (공개 코드 대조)
- `research/0.3/`에는 Python 0.3 설계 후보와 시험이 구현되어 있다.
- `research/0.3-local-correction.3/bridge.mjs`는 `src/agents.mjs`의 CentralCore와 Python 지원 엔진을 연결하는 **실제 연구 어댑터**이다.
- `research/0.2-core-guard-integration.v1/` 및 `v2/`는 0.2·correction.3·guard의 **선택 실행 통합 코드**다. v2는 정확한 검토 ID 귀속·유효한 형제 검토 보존을 보완한다.
- v2 README에 기존 통합 33/33, 검토 연결 반례 28/28 등 과거 실행 결과가 기록되어 있지만, 이번 금요 전건 재실행과는 구별한다.
- 루트 `package.json`은 `0.2.0-draft`이며 기본 `npm test`는 0.2 경로다. 따라서 **0.3 연구 통합 구현 존재**와 **기본 명령으로 v2/A-R3 게이트가 항상 실행됨**은 별개의 주장이다.
- 새 폴더는 기존 0.3 통합을 대체하거나 미통합이라고 재분류하지 않는다. 새로 제안하는 것은 **A-R3 목적함수 게이트의 기본 경로 연결**뿐이다.

## 목적
기관의 절차적 종결·일부 피해구제 실적을 모든 질문의 실질 검증 완료로 잘못 환산하지 않도록 기본 호출 경로에 A-R3 검증 게이트를 통합하는 방향을 제안한다. '격리 자체가 결함'은 검증할 가설이며 현행 기본 경로의 결함을 새로 실증했다는 뜻이 아니다.

## A-R3 설계 규칙
1. A-R3 게이트 채택 시 모든 기본 호출에서 실행. **신규 A-R3 게이트의 기본 경로 연결은 확인되지 않음**. 기존 0.3 연구 어댑터·v1/v2 연결은 유지.
2. 사건/질문별 증거 출처·통제자·접근 권한·요청/응답 시각·검증 수준을 구분.
3. 증거 불충분, 충돌, 게이트 실행 실패는 자체 VERIFIED 인증을 보류. 외부 법적 종결은 그대로 별도 기록.
4. 행정/사법 절차의 종결, 발표, 일부 인정·지원은 모든 청구·문제의 실질 구제 완료와 같지 않음.
5. 기관의 설명책임 미이행 가능성은 검증 플래그. 위법·인과성·민형사 책임·불리추정 법률 효과 자동 판정 없음.
6. 독립 평가 결과의 식별자와 원본 보존, 정정 상태는 실제 이행 증거를 확인한 뒤에만 갱신.
7. R3가 승인한 명시적 게이트 규칙 이외 새로운 준사법적 자동 통제 금지.

## 순환 논증 반례
자료 미제공 → 검증 불능 → 입증 부족 → 추가 조사 배제 → 최초 자료 미제공 상태 재생산. 이 패턴은 **검토 트리거**이지 기관의 은폐·범죄 사실 판정이 아니다.

## 금요일 재현기록과 한계
2026-11-13 별도 실행 패키지에서 공개 연구 후보 원본 Node 82/82, 새 합성 반례 3/6, 로컬 패치 및 시험입력 수정 후 88/88로 기록됨. 88건에는 기존 82건이 포함되어 이중 합산 금지. `suggested-authority-duty.patch` 및 `suggested-fixture-clarification.patch`는 **GitHub 원본에 미적용, 채택 미승인**.

0.2 CentralCore 전체 24, correction.3 Python 132+bridge 14, correction.4 guard 68, integration v1/v2, v2 Node→Python 연결은 **2026-11-13 금요 회귀시험에서** 재현되지 않아 `UNVERIFIED_THIS_RUN`. 이전 날짜의 v2 통합 실행 결과는 유지한다. 과거 시험 기록을 신규 성과로 계산하지 않는다.

## 선행 조건과 승인 게이트
- 두 패치 독립 검토 → 적용 대상/해시 확인 → 동일 반례 및 기존 회귀 재시험
- 0.2 CentralCore 전체 24건 직접 실행
- correction.3 Python 132 + bridge 14, correction.4 guard 68 직접 실행
- integration v1/v2 전체 시험 및 v2 Node→Python 실제 연결 실행
- 합성 반례를 실제 통합 게이트에 연결해 실패→수정→재시험 증명
- 실패 시 `GATE_EXECUTION_UNVERIFIED`로 종결 인증을 막는지 검증
- R3 최종 확인 전 운영 호출 경로/배포 전환 금지

## 거버넌스
AX-01~09 불변 · CIVIC-TRACE 0.4.5 유지 · 0.4.6 보류 · `total_score=null` · R3 최종 권한 유지.
비공개 LP728 의료·소송기록, 사적 대화 사용 금지. LP728은 실패 유형 설계 맥락일 뿐 합성 시험 입력에 포함하지 않음.

## 파일
- `DECISION-KO.md`: 제안된 승인 문구
- `synthetic-gate-cases.json`: 합성 입력/기대 상태 명세(실제 통합 시험 아님)
- `validate_fixtures.py`: 명세의 구조 검증만 수행
- `MANUAL-UPLOAD-KO.md`: 비파괴 수동 업로드 절차
