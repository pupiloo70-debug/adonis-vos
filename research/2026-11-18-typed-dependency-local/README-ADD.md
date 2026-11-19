# P02 typed dependency bridge — 연구용 연결

이 패키지는 공개된 `research/2026-11-18-typed-dependency-local/candidate/testimony-controller.mjs`의 `reviewContextLinked`를 명시적으로 호출하는 경량 연결입니다.

- 위치: `src/p02-research-bridge.mjs` 및 `tests/p02-research-bridge.test.mjs`
- 기본 중앙코어(`src/project.mjs`, `src/engine.mjs`, `src/cli.mjs`)에는 연결하지 않습니다.
- 합성 입력만 허용합니다. 실제 사건·비공개 자료를 사용하지 않습니다.
- 실행: 저장소 루트에서 `node --test tests/p02-research-bridge.test.mjs`
- 기존 기본 시험: `npm test`
- 두 명령은 GitHub 등록 후 실제 재실행하여 결과를 확인해야 합니다. 현재 패키지 자체에 시험 통과를 보증하는 실행 영수증은 없습니다.
- 상태: `RESEARCH_ONLY`, `NOT_INTEGRATED_TO_DEFAULT_CORE`, `NOT_RELEASED`.
