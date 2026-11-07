# Adonis VOS 0.2 중앙코어 + guard v0.2 실제 연결

2026-11-07 · 추가형 합성 연구 통합 v1

이번 파일은 설계 제안만이 아닙니다. 한 번의 Node 호출에서 실제 0.2 `CentralCore.register → assign → runLocal`, 기존 correction.3 Python 실행기, 기존 guard v0.2를 차례로 실행하고, 자료·판정 주체·사건 범위를 점검한 하나의 현재 보고서를 만듭니다. 강제집행 권한을 이 연구 실행의 전제조건으로 삼지 않습니다.

## 달라진 점

- `runIntegratedCore()`가 세 실행 결과를 연결합니다. 현재 보고서는 `report`입니다. 원래 0.2 작업 상태와 부분 제공·미제공 상태는 그대로 남고, 각 Python 단계에는 별도 실제 실행 영수증이 붙습니다.
- correction.3과 guard에는 같은 명시적 합성 프로젝트를 보냅니다. 별도의 그림자 프로젝트로 자료를 바꾸지 않습니다. 요청↔경로, 경로↔검토 연결을 입력에서 명시해야 합니다.
- 사건·절차·사람·자료·질문을 섞어 경고를 만들지 않습니다. 상대방의 요청과 실제 판단기관의 결정을 구분합니다. 일부 자료가 잘못되어도 독립적으로 성립하는 근거와 경고는 유지합니다. 추가 격리의 의존관계까지 다시 점검합니다.
- 기존 correction.3의 경고·초안은 `audit_only`에만 보존합니다. 이를 새로 점검된 현재 초안으로 다시 내보내지 않습니다. 현재 경고와 근거 연결은 guard 결과에 명시적 경로 연결을 적용해 생성합니다.
- 기관·자료 통제자의 제출·설명책임, 독립 검증 요청과 판단방법 점검을 행동 제안으로 연결합니다. 피해자만의 양보나 주장 포기를 자동 요구하지 않습니다. 이견·불리한 자료·원문·기존 구제 요청도 삭제하지 않습니다.
- Python 실패·시간 초과·잘못된 JSON·출력 계약 오류는 성공으로 포장하지 않습니다. 0.2 성공 영수증은 보존하며 전체 상태는 `PARTIAL_STAGE_FAILURE`입니다. guard가 독립적으로 정상 실행한 유효 자료는 계속 볼 수 있습니다.

## 실행

Node 18 이상과 `python3`가 필요합니다. 외부 패키지를 설치하지 않습니다. 저장소 루트에서:

```sh
python3 -B research/0.2-core-guard-integration.v1/verify-baseline.py
node --test research/0.2-core-guard-integration.v1/integration.test.mjs
node research/0.2-core-guard-integration.v1/run-example.mjs
```

마지막 명령은 동봉한 합성 예제를 실제로 실행하고 JSON을 표준출력에 표시합니다. 기존 파일을 덮어쓰지 않습니다. 기본 `npm test`나 기존 CLI는 바꾸지 않았으므로 새 통합 기능은 위 명령 또는 `runIntegratedCore()`를 선택해 실행합니다.

## 입출력 계약

입력은 `legacy_project`, `project`, `mapping`, `now`입니다. 두 프로젝트 모두 `synthetic: true`여야 합니다. 기존 0.2 스키마와 correction.3 스키마를 그대로 사용하되, 통합용 프로젝트·경로에 `subject_id`, 경로에 `question_id`, 관찰·출처에 명시적 주체·행위·자료·질문 정보가 필요합니다. 자동 추론이나 묵시적 이전은 없습니다.

`mapping.request_routes`는 모든 요청과 경로를 일대일로 연결합니다. `mapping.review_routes`는 `{review_id, route_id, question_id}`로 검토를 연결합니다. 유효한 경로에 연결되지 않은 검토는 현재 경고에서 격리하고 원문은 보존합니다. 누락 질문은 다른 질문의 대체값이 아닙니다.

- `report`: 현재 통합 보고서. 유효한 관찰·경고, 격리 사유, 조치 제안, 원래 0.2 자료 제공 상태.
- `receipts`: 실제 0.2, correction.3, guard 실행 상태와 입력·출력 해시.
- `legacy_snapshot`: 변경하지 않은 0.2 코어 작업 상태.
- `audit_only`: 두 기존 구성요소의 원래 출력. 현재 경고나 제출 초안의 권위가 아닙니다.
- `original_input`: 입력 복사본. `review_nodes_original`, `facts_original`, `items_original`은 보존 자료이며 자동 채택·검증된 사실이 아닙니다.

전체 상태가 `LOCAL_INTEGRATION_SUCCEEDED`여도 증거의 진실성이나 법적·의학적 결론이 승인되었다는 뜻은 아닙니다. `LOCAL_INTEGRATION_WITH_QUARANTINE`은 실행은 되었으나 격리 항목이 있음을 뜻합니다. 원래 guard의 `ISOLATED_SYNTHETIC_RESEARCH_NOT_INTEGRATED` 표시는 보존된 구성요소 자체의 역사적 표기이며, 새 실행의 실제 연결 여부는 상위 `local_core_integration`과 세 단계 영수증에서 확인합니다.

## 변하지 않은 경계

기준 공개 커밋은 `aa77d9f5922e53e22156492360e66a5da0bbfb24`입니다. `src/`, 기존 correction.3, guard v0.2, 공리·규칙·상태 파일을 수정하지 않았습니다. AX-01~AX-09, CIVIC-TRACE 0.4.5, 0.4.6 승인 유보, 인간 R3 권한, `total_score=null`은 그대로입니다. 새 통합 실행 상태는 기존 승인 상태를 덮어쓰지 않습니다.

실제 사건·개인 자료는 입력하지 않았습니다. 외부 AI/API 연결, 전송, 제재, 환수, 게시·배포는 수행하지 않습니다. 현재 단계는 로컬 합성 연구 통합이며, 운영 기본값 전환·실제 사건 검증·승인 완료를 뜻하지 않습니다. 문구의 일치와 형식 점검은 원자료 진위나 주체가 실제로 해당 행위를 했다는 사실을 인증하지 않습니다.

관찰 목록 등의 구조가 correction.3의 원래 제한을 어기면 그 단계는 실패할 수 있습니다. 이를 guard의 부분 격리 성공과 혼동하지 않습니다. 검토별 격리와 원문 보존은 계속 가능하며 전체 성공으로 표시하지 않습니다. 관찰의 질문 연결 이후 의존관계 재검사는 제한된 입력 크기 안의 반복 점검입니다. 임의의 대형 적대적 입력에 대한 자원 안전성을 주장하지 않습니다.

검증 수치와 실행 로그는 `verification/` 및 `execution-record.json`을 확인하십시오. 별도 검토는 같은 작업환경에서 수행한 독립 코드·반례 검토이며 독립 기관 인증이 아닙니다.
