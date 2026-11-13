# R3 승인 후 상태 및 안전한 수동 작업

- 승인 권한: R3의 대화 내 명시적 설계 승인(2026-11-13). GitHub 게시 행위는 별도 수동 수행.
- `design_status=APPROVED_AND_INTEGRATING`
- `default_path_connected=false` (실제 기본 호출 경로 미연결)
- `virtual_test_passed=11/11` (Node 연구 후보 호출, Python 브리지 연결 증명 아님)
- `patch_local_regression=88/88` (기존 82 포함; 독립 88개의 신규 사례 아님)
- `full_python_bridge_status=NOT_VERIFIED_THIS_RUN`
- `production_released=false`
- R3 최종 권한·AX-01~09·CIVIC-TRACE 0.4.5 유지·0.4.6 보류·`total_score=null`.

## GitHub 수동 적용 순서

1. **기존 README/DECISION 파일을 덮어쓰기 전에** 본 상태 문서를 새 연구 폴더에 추가할 수 있다. 기존 A-R3 제안 파일과 상충하는 부분은 승인 상태 변경(설계 수준에 한정)으로 명시한다.
2. `suggested-authority-duty.patch` 및 `suggested-fixture-clarification.patch`는 승인된 로컬 코드 후보이며 **원본 GitHub 경로에 바로 적용하지 말고** 새 연구 브랜치에서 `git apply --check` 후 `git apply`하고 전 시험을 재실행한다. 두 패치의 헤더는 과거 로컬 절대 경로를 포함하므로 GitHub 저장소 상대 경로로 정규화한 후 사용한다.
3. `virtual-integration/`는 설명 가능한 연구 시험 예제이며 repo 메인 `src/` 또는 `package.json`에 연결하는 단계가 아니다. 저장소의 연구 브랜치에 배치하기 전 상대 경로를 새 디렉터리에 맞게 조정한다.
4. CentralCore 24, correction.3 132+14, guard 68, integration v1/v2 전체 재실행 후 기본 경로 연결 여부를 다시 결정한다.
5. 운영 배포·외부 발송·법적 의학적 자동 판정 금지.

## 재현

압축 해제한 최상위 폴더에서 `sh run-verified-tests.sh`. 테스트들은 공개 합성자료만 사용한다.
