# Adonis VOS 2026-11-09 합성 경계 검토 후보

**신규 발견:** v2 검토 ID는 정확히 연결되더라도, guard 경계에서 경고 코드만 다른 코드로 바꾸면 `guardReviewContract` 및 `reviewPayloadMatchesInput`이 모두 수용한다. 이로 인해 제안 조치의 종류가 변경될 가능성이 있다. 이는 실제 기관 행위의 발견이나 source truth 인증이 아니라 합성 결과 변조 반례다.

**재현:** 공개 v2 `synthetic-input.json`과 `verification/latest/synthetic-output.json`을 로드하여 공개 `core_guard.mjs`의 `guardReviewContract`, `reviewPayloadMatchesInput`, `bindGuardReviews` 함수 본문을 V8에서 그대로 평가했다. 정상 1/1 결합, 코드만 변조해도 1/1 결합, 이웃 검토를 붙이면 2/2 결합이라는 결과를 재현했다.

**후보:** `candidate.patch`는 v2의 경고 코드별 최소 전제 관찰 종류를 반환 경계에서 재확인한다. 같은 반례의 부분 패치 재시험은 변조 검토 1건을 `GUARD_REVIEW_INPUT_PAYLOAD_CONFLICT`로 보류하고 정상 이웃 1건을 유지했다. 기존 합성 원본은 계속 결합된다.

**주의:** 이것은 Node/Python 전체 실행이 아니라 실제 GitHub 원문에서 함수 본문을 추출하여 실행한 경계검증이다. v1 통합 33건, 별도 감사 35건, guard 68건, correction.3 132건, v2 검토 ID 28+30건의 과거 기록은 이번에 재실행하지 않았다. 추가한 Node 회귀시험은 실제 저장소 환경에서 미실행이다.

실제 소스에 패치를 적용하기 전 공개 원문과 hunk를 다시 확인하고, `node --test research/0.2-core-guard-integration.v2/review-identity.test.mjs` 및 `python3 -B research/0.2-core-guard-integration.v2/verify-all.py`로 회귀시험을 수행해야 한다. 검증되는 경우라도 연구 후보이며 R3 최종 승인·정식 릴리스는 별개다.

**추가 반례:** 공개 합성 출력의 경고 5개 각각을 나머지 4개 유효 코드로 치환한 20건 모두 현행 검증기로 통과했으며 후보 검증기는 20건을 보류했다. 정상 출력 5개를 가진 원본은 후보에서 통과했다. 이 수치는 V8 경계 함수 검토 결과이며, 전체 Node/Python 시험 수에 합산하지 않는다.

**원격 쓰기:** 별도 연구 브랜치를 생성하려 했으나 GitHub 커넥터에서 `403 Resource not accessible by integration`이 발생하여 원격 저장소에는 아무것도 쓰지 못했다. 이번 산출물은 로컬 패치·기록만이다.
