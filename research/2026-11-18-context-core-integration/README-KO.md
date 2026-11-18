# Adonis VOS 0.3 P02 · 기존 중앙 코어 연결 후보

2026-11-18. 기존 CentralCore → correction.3 → guard v2 실행에 수리된 P02 맥락 검토를 연결했다. 단순 설계안이 아니라 실제 합성 입력으로 실행한 추가형 어댑터다.

## 실제 바뀐 것
- `context_core.mjs`의 `runContextCore()`가 기존 v2 `runIntegratedCore()`와 P02 `reviewContextIsolated()`를 함께 호출한다.
- 사건·절차·대상 및 항목별 검토 ID 대응을 요구한다. 다른 사건, 누락·중복·잘못된 연결은 거부한다.
- 최종 반환값은 기존 코어 출력과 P02의 진술·이견·출처·보류 사유를 그대로 보존한다. 자료 통제자의 설명 요청을 남기며, 자료 부족을 피해자의 입증 실패로 변환하지 않는다.
- 부분 실패를 전체 성공으로 표시하지 않는다. P02 항목 격리는 나머지 유효 작업을 보존한다.
- 입력의 독립검증 자기표시는 참조 연결 수준으로 낮추고 원래 표시는 별도로 남긴다.

## 사용
저장소 기준 커밋 `6e8afd5c8aa3023e48b85cc171f80d6be7828ade`에 이 `research/2026-11-18-context-core-integration/` 폴더를 추가한다. 기존 파일을 덮어쓰지 않는다. Node 18 이상과 python3가 필요하며 외부 패키지는 없다.

```sh
node research/2026-11-18-context-core-integration/run-example.mjs
node --test research/2026-11-18-context-core-integration/integration.test.mjs
node --test research/2026-11-18-context-core-integration/p02/*.test.mjs
```

## 재시험 결과
- 새 실제 연결 시험 9/9
- 수리된 P02 기존 시험 45/45
- 기존 v2 통합 및 검토 ID 시험 61/61
- 기존 0.2 엔진 검사 및 Node 시험 24/24
- correction.3 Python 132/132
- 기존 Node→Python 브리지 14/14
- guard Python 68/68
각 집합은 범위가 겹치므로 합산하지 않는다. 실제 명령과 로그는 `execution-record.json`, `logs/` 참조.

## 계보
P02 기반 후보와 2026-11-17 후속 패치를 재사용했다. 조합된 P02 소스 SHA-256은 기존 검토 기록의 `432530134339183646647d79846513bcd12f59678d1d5d5d5f82a4c7dc67cb58`과 일치한다. P02 소스 자체는 이번에 변경하지 않았다.

## 남은 연결 단계
이 어댑터는 명시적으로 호출하면 실행된다. 기본 CLI·홈페이지·실제 대화 생성 경로에는 아직 연결하지 않았으며 외부 모델 API를 호출하지 않는다. 실제 사건과 사적 대화는 입력하거나 저장하지 않았다. 입력·출처의 내용 진위는 해시로 인증하지 않는다. 기본 경로 전환은 별도 인수 검토 대상이다. 기존 AX, CIVIC-TRACE 0.4.5 유지·0.4.6 보류, R3 승인, total_score=null을 바꾸지 않는다. 공개 저장소와 운영 배포는 변경하지 않았다.
