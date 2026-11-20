# Adonis VOS 0.3 · 시민 권리 보존형 재귀적 연구 어댑터

상태: `RESEARCH_CANDIDATE / SYNTHETIC_ONLY / NOT_DEFAULT_CONNECTED / NOT_RELEASED`.

이 후보는 기존 `src/agents.mjs`의 `CentralCore`를 **실제로 호출**한 다음, 공개 합성 이벤트에 한해 시민 검증권 관련 반례와 수정 제안을 생성합니다. 이전 0.3 Python/correction.3/guard/v2를 모두 기본 경로에 연결했다고 주장하지 않습니다. 코어와 프로젝트 원문 파일은 변경하지 않습니다.

## 목적함수 경계

- 시민의 생존권, 증거 접근권, 설명책임, 독립 이의제기와 실제 구제를 **점수화하지 않고 검토 우선순위로 사용**합니다.
- 검증 불능과 형식 종결은 자동 인증되지 않습니다.
- 피해자에게 자료 통제자의 검색·설명책임을 이전하지 않습니다.
- 독립적인 반대 견해를 보존하며, 다중 AI 합의를 독립적 증거로 간주하지 않습니다.
- 오류를 발견하면 *수정 후보*만 생성하며, 자기 코드 변경·재승인·자동 배포·외부 전송을 수행하지 않습니다.
- 자체 기술 책임(코드·무결성·보안·실행)은 별도의 실행 기록과 시험으로 확인해야 합니다.

## 재현

```bash
node --test research/2026-11-20-rsi-centralcore-candidate/rsi-gate.test.mjs
```

동일 저장소의 `src/agents.mjs`, `src/project.mjs`, `src/engine.mjs`, `examples/synthetic-project.json`이 필요합니다. 합성 입력 스키마는 `ADONIS-RSI/SYNTHETIC-1`, `synthetic:true` 입니다. 최대 JSON 256 KiB·이벤트/출처 128개이며 제한 초과 입력은 거부합니다.

본 후보는 안전한 **연구용 의사결정 보조**이며 법적·의학적 인과성, 위법, 유죄 또는 AGI·ASI를 자동 판정하지 않습니다. `total_score=null`, AX-01~09 불변, CIVIC-TRACE 0.4.5 유지, 0.4.6 `R3_RELEASE_NOT_APPROVED`, R3 인간 승인권 유지.

## 아직 미구현·미검증

독립적인 Python 132·Bridge 14·guard 68·v1/v2 전체 통합 회귀, 인증된 신원/해시 영수증 체인, 안전한 장기 저장, 외부 기관의 법적 의무 확인, 자동 반복 실행 스케줄은 이 코드를 게시하는 것만으로 완료되지 않습니다. 운영 기본 경로 연결 `false`입니다.

## 2026-11-20 로컬 예비 시험 한계

최초 예비 실행의 15/15 통과는 공개 `CentralCore`의 호출 계약을 모사한 로컬 테스트 사본으로 확인한 결과다. 실제 GitHub 전체 원본 소스의 통합시험은 이번 실행에서 미검증이며 그 숫자와 합산하지 않는다. 최종 적용 판단은 실제 저장소 전체 환경 재시험이 필요하다.

`WORKFLOW-TEMPLATE.yml`은 복사 전에는 비활성 상태다. 실제 워크플로 등록 후에도 contents:read만 사용하고 코드를 수정/커밋하지 않는다. 장기 재귀 개선 연구는 기존 ChatGPT 예약 점검이 별도로 수행하며, 실행되지 않은 것을 성공으로 보고하지 않는다.
