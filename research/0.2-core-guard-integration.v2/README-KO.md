# Adonis VOS 검토 ID 연결 오류 수정 후보

2026-11-08 · 추가형 합성 연구 통합 v2

기존 v1의 0.2 중앙코어·correction.3·guard v0.2 연결은 실제로 작동합니다. 이번 수정은 그 연결의 **검토 결과 귀속 오류**를 고칩니다. 강제집행 권한을 연구 실행의 전제조건으로 삼지 않습니다.

## 수정 내용

- v1은 guard 출력 배열의 순서로 입력 검토를 연결했습니다. 출력 순서가 바뀌면 다른 검토의 경고가 붙을 수 있었고, 같은 개수의 잘못된 ID도 통과했습니다.
- v2는 입력에 존재하는 정확한 검토 ID가 입력·출력 양쪽에서 각각 하나일 때만 연결합니다. 공백 제거, 문자열 변환, 비슷한 ID 추정, 첫 항목·마지막 항목 우선 선택을 하지 않습니다.
- 누락·중복·예상 밖 ID와 잘못된 검토 출력은 격리합니다. 잘못된 검토 때문에 독립적으로 유효한 형제 검토까지 지우지 않습니다. 원래 입력과 guard 출력은 각각 `original_input`, `audit_only.guard_execution`에 남습니다.
- ID가 맞아도 다른 검토의 관찰·출처·주체·행위·사건·절차·사람 정보를 가져오면 해당 검토 출력을 격리합니다. 경고의 근거와 질문·자료 범위를 재확인하고, 시정 상태의 사건 범위는 원래 사건에 연결된 명시적 이벤트 ID로 확인합니다.
- 잘못된 격리 사유나 시정 상태 형식이 전체 통합 실행을 중단시키던 두 검증 누락도 수정했습니다. 독립 검토에서 재현한 세 충돌 반례가 회귀 시험에 들어 있습니다.

자료 통제자의 제출·설명책임, 판단기관의 판단 과정 점검, 독립 검증 요청은 그대로 유지합니다. 피해자만의 포괄적 양보를 생성하지 않으며, 불리한 자료와 이견을 삭제하지 않습니다.

## 실제 실행 결과

기준 공개 커밋: `42122a759b1bdf9d9c4d692988ea7320cd983a72`.
공개 Git 트리와 기존 141개 파일의 Git blob 해시를 대조했고, 실행 전후 SHA-256 검사에서 모두 변경되지 않았습니다. 기존 `src/`, correction.3, guard v0.2, v1 통합을 그대로 불러옵니다.

- v2에 적용한 기존 통합 시험: 33/33 통과.
- 새 검토 연결 반례: 28/28 통과.
- 별도 독립 검토 반례: 30/30 통과.
- 기존 0.2: 기본 엔진 확인과 Node 시험 24/24 통과.
- 기존 0.3: 40/40, correction.3: 132/132, 원래 브리지: 14/14 통과.
- 기존 guard: 68/68, 기존 v1 통합: 33/33, 기존 v1 독립 점검: 35/35 통과.
- 기존 guard 탐침과 v1/v2 실제 합성 예제도 성공했습니다. v2 예제는 세 실행 영수증이 모두 `SUCCEEDED`, 관찰 9개와 경고 5개입니다.

검증 숫자는 서로 다른 시험 집합별 결과입니다. 중복 범위가 있으므로 독립 사례의 총수나 실제 사건의 정확도로 합산하지 않습니다.

`boundary-comparison.mjs`는 실제 코어와 두 Python 단계를 실행한 다음 시험용 경계에서만 guard 출력 순서를 바꿉니다. 검토 A/B/C의 정상 경고 수 1/5/0이 역순에서 v1은 0/5/1, v2는 1/5/0으로 나옵니다. A 출력 누락 시 v1은 guard 전체 계약 실패로 B 경고도 사라지지만 v2는 A만 보류하고 B의 5개 경고를 유지합니다. 시험 주입 기능을 실제 `runIntegratedCore` API에 추가하지 않았습니다.

## 실행 방법

Node 18 이상, `python3`, 기존 저장소 파일이 필요합니다. 외부 패키지 설치는 없습니다. 동봉한 경계 주입 시험은 macOS·Linux·WSL처럼 `/bin/sh`를 사용할 수 있는 환경에서 실행합니다. 이번 실측 환경은 Node 24.22.1, Python 3.12.14입니다.

저장소 루트에서:

```sh
python3 -B research/0.2-core-guard-integration.v2/verify-baseline.py
node research/0.2-core-guard-integration.v2/run-example.mjs
python3 -B research/0.2-core-guard-integration.v2/verify-all.py
node research/0.2-core-guard-integration.v2/boundary-comparison.mjs
```

`verify-all.py`는 모든 시험을 재실행하고 새 실행 기록을 `verification/latest/`에 씁니다. 네트워크 전송·Git 커밋·업로드를 하지 않습니다. 소스 변경 차이는 `source-diff.patch`에 있으며, 이는 비교용입니다. v1에 패치를 적용하지 않습니다.

## 결과 확인

- `report.guard_review_binding`: 정확한 ID 연결 방식, 입력·출력 개수, 연결 수, 격리된 출력의 위치·ID·사유.
- `report.support_reviews[*].guard_output_index`: 실제로 연결된 guard 출력 위치. 위치는 기록용이며 연결 판단에 쓰지 않습니다.
- 검토의 `held_reason`: 누락·중복·잘못된 형식·입력과 출력 충돌 등의 사유.
- `receipts`: 원래 코어와 Python 실행의 상태 및 입력·출력 해시.

guard의 실행과 상위 출력 계약이 성공해도 개별 검토가 격리될 수 있습니다. 이때 `receipts.guard.status`는 `SUCCEEDED`, 전체 결과는 `LOCAL_INTEGRATION_WITH_QUARANTINE`입니다. 실행 실패·잘못된 JSON·상위 계약 위반은 계속 `PARTIAL_STAGE_FAILURE`입니다. 이 구분이 누락된 검토를 성공으로 표시하지 않으면서 유효한 검토를 보존합니다.

## 적용 범위

v2는 별도 경로로 선택 실행하는 추가형 후보입니다. 업로드만으로 기존 CLI·기본 실행 경로가 v2로 바뀌지 않습니다. 후속 연구 실행에서는 v2의 `runIntegratedCore` 또는 위 실행 명령을 사용합니다.

입력 ID와 출력의 일치는 원자료 진위 인증이 아닙니다. 기존 guard의 출처·인용·행위 검사를 유지하면서 반환값의 귀속을 확인합니다. 유한한 합성 시험과 같은 작업환경의 독립 코드 검토를 수행했으며, 모든 입력의 안전성이나 외부 기관 인증을 주장하지 않습니다.

AX-01~AX-09, CIVIC-TRACE 0.4.5, 0.4.6 승인 유보, 인간 R3 권한, `total_score=null`, 기존 승인 상태는 바뀌지 않았습니다. 공개 저장소 쓰기, 실제 사건 입력, 외부 AI 호출, 제출·제재·배포를 하지 않았습니다.

실행 명령·개수·소스 해시는 `verification/latest/execution-record.json`, 독립 검토는 `verification/independent-audit.md`, 전후 비교는 `verification/boundary-comparison.json`을 확인하십시오.
