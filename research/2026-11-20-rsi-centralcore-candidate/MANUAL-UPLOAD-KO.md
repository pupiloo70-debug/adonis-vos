# Adonis VOS 0.3 후속 연구 수동 업로드

2026-11-20 기준 GitHub 직접 브랜치 생성 요청이 `403 Resource not accessible by integration`으로 거부되어 **어떠한 GitHub 파일도 이번 작업에서 수정하지 않았음**.

## 수동 업로드 순서

1. 저장소 `pupiloo70-debug/adonis-vos`의 최신 `main`에서 `research/2026-11-20-rights-preserving-rsi` 브랜치를 새로 생성한다.
2. `research/2026-11-20-rsi-centralcore-candidate/` 폴더를 만들고 **`rsi-gate.mjs`, `rsi-gate.test.mjs`, `README-KO.md`** 세 파일을 올린다.
3. `WORKFLOW-TEMPLATE.yml`은 같은 폴더에 *참고 설계*로 보관한다. **`.github/workflows/`로 아직 복사하지 않는다.** 실행 자동화는 본 저장소 테스트 재현 완료 후 재검토한다.
4. GitHub Codespaces 또는 Actions와 같이 실제 저장소 파일이 있는 환경에서 `node --test research/2026-11-20-rsi-centralcore-candidate/rsi-gate.test.mjs` 및 `npm test`를 재실행한다.
5. 기존 correction.3 Python 132, Bridge 14, correction.4 guard 68, v1/v2 통합 전건은 별도 실행하고 이전 성적을 신규 시험으로 집계하지 않는다.
6. 실행·해시·브리지 연결·실패를 확인하기 전 `main` 병합과 `default_path_connected=true` 변경을 하지 않는다.

GitHub 업로드용 파일은 공개 합성 입력만 사용하며, LP728 비공개 자료·유족 대화·실사건 정보가 없다.

이 후보의 목적은 **중앙코어를 실제 호출하는 선택형 연구 경로 및 자기개선 검토 제안**이며, 스스로 패치 적용·병합·운영 배포를 하지 않는다.
