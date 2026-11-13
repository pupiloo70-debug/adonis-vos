# 모바일 GitHub 수동 등록 · 기존 0.3 통합 보존

대상: https://github.com/pupiloo70-debug/adonis-vos/tree/main/research
검토 기준 main SHA: `6503dddc2c67c54afacd9ad964720e3e102653a9` (2026-11-13 확인). 업로드 직전 새 커밋 여부 확인.

## 기존 편집창에서 아직 Commit하지 않았다면

`README-KO.md` 입력 화면에서 **Cancel changes**를 눌러 이전 초안을 저장하지 않는다. 폴더는 README를 커밋하기 전에는 GitHub에 생기지 않는다. 새 ZIP을 풀고 수정된 `README-KO.md`로 다시 등록한다.

## 수동 등록

1. `research/`의 **Add file → Create new file**에서 `2026-11-13-r3-gated-integration-decision/README-KO.md` 경로를 지정한다.
2. 새 ZIP의 같은 이름 파일 내용을 복사해 붙여넣고 Commit changes.
3. 생성된 폴더에서 Add file → Upload files로 `DECISION-KO.md`, `MANUAL-UPLOAD-KO.md`, `synthetic-gate-cases.json`, `validate_fixtures.py` 4개를 등록한다.
4. 업로드 대상은 총 5개. ZIP 안의 홈페이지 게시문, 검증 로그, SHA 목록은 GitHub 파일 5개에 포함하지 않는다.
5. `src/`, `tests/`, 루트 `README.md`, `package.json`, 기존 0.3/v1/v2 파일은 수정하지 않는다.
6. 커밋 문구: `research: preserve 0.3 adapters and propose R3 default gate`.

이 문서 등록 자체는 A-R3 기능의 실제 통합, 패치 채택, 신규 회귀시험 완료 또는 운영 배포가 아니다.
