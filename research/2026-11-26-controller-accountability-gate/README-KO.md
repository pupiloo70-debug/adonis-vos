# CONTROLLER-ACCOUNTABILITY-GATE-01 · 자료 통제자 책임 게이트

2026-11-26 R3 연구 방향 승인에 따른 **합성 데이터 전용 연구 후보**입니다. 승인 범위는 연구 목적과 설계 방향이며 실제 중앙코어 연결, 외부 집행, 제재, 정식 배포 승인을 뜻하지 않습니다.

## 문제와 기능

- 원자료 통제자의 자료 미제공, 독립 검증 제한, 보존 공백, 반복 미답변, 이해충돌 우려를 **자료 통제자 기준**으로 추적합니다.
- 유족에게 원자료 제출 권한이 없다는 사실을 '피해자의 입증 실패'로 자동 환산하지 않습니다.
- 기관의 검증되지 않은 주장에 **시스템의 검증 완료 인증을 부여하지 않습니다**. 이는 기관 전체를 법적으로 제재하거나 위법을 확정하는 행위가 아닙니다.
- 해당 기관에 README-KO.md 법적 의무는 별도 증거와 법률 검토 없이 자동 확정하지 않습니다. 적법한 비공개 사유 및 제3자의 권리를 함께 심사합니다.
- 위법·담합·고의적 은폐 여부는 자동 판정하지 않고, 법률상 불리추정 및 제재 가능성은 대리인·담당기관·법원이 판단할 심사 초안으로만 만듭니다.
- 기계 판정은 모든 경우 `total_score=null`, `automatic_guilt=false`, `automatic_immunity=false`, `automatic_sanction=false`, `automatic_causality=false`, `delivery=NOT_SENT`를 유지합니다.

## 파일 및 실행

- `src/controller-accountability-gate.mjs` — 경량 게이트. `src/p02-input-boundary.mjs`를 재사용합니다.
- `tests/controller-accountability-gate.test.mjs` — 합성 반례 시험.
- 이 README는 `research/2026-11-26-controller-accountability-gate/README-KO.md`에 놓습니다.

```bash
node --test tests/controller-accountability-gate.test.mjs
node --test tests/p02-input-boundary.test.mjs tests/p02-research-bridge.test.mjs
npm test
```

위 명령은 **GitHub 등록 후 동일 저장소 최신 main에서 반드시 재실행**해야 합니다. 개별 연구 시험 통과를 중앙코어 결합 시험 통과로 바꾸지 않습니다.

## 경계와 후속 단계

입력은 실제 사건 데이터가 아닌 합성 사례만 허용하며 기존 P02 2 MiB JSON 경계를 사용합니다. 출처 문자열 자체는 원자료 인증이 아닙니다. 출력은 시민의 검증 요구 및 제도적 검토 지원용이고 법적 결정권이 없습니다. 이후 프로젝트별 원자료·법적 의무·제출 사실의 독립 검증, 충돌 회귀시험, 인간 R3의 단계적 승인 없이는 기본 실행 경로에 연결하거나 배포하지 않습니다.
