# Adonis VOS 0.3 — 2026-11-23 로컬 재귀 검증 보고

**상태:** LOCAL_RESEARCH_PATCH / NOT_COMMITTED / NOT_RELEASED / NOT_DEPLOYED

공개 GitHub `pupiloo70-debug/adonis-vos`의 `main` `c6a6567ae4401d77c0dc6c3e4d143aa37ba084d5`(커밋시각 2026-11-19T03:26:37Z)을 GitHub 커넥터로 확인했다. 2026-11-07 통합 기준 `42122a759b1bdf9d9c4d692988ea7320cd983a72`보다 48커밋 앞선다. **전체 클론은 네트워크 DNS 제한으로 불가능**했다. 아래 재현은 GitHub 원본 파일 두 개의 정확한 바이트를 복원하여 각 Git blob SHA-1과 비교한 별도 작업 폴더에서 이루어졌다. Git blob SHA-1과 별도의 로컬 SHA-256을 혼동하지 않는다.

## 신규 기술 발견

구현된 0.1 엔진(`src/engine.mjs`, 0.2 저장소에 포함)에 `answers[field]`가 자기 객체에 없는 **프로토타입 상속값**을 입력 답변으로 읽는 경계 오류가 있었다. 합성 입력 `Object.create({record_access:{value:'YES',basis:'DOCUMENT_REFERENCED',refs:['SYNTHETIC-REF']}})`는 원래 답변이 없는데도 `SIGNAL_REPORTED`가 되었다. `preservation_risk` 상속값 역시 보존 우선순위를 잘못 올렸다. 이는 **사실 인증/형사 유죄 결론과는 다른** 입력-출처 혼동이다.

- **최소 수정:** `answers[field]`를 읽기 전에 `Object.hasOwn(answers, field)` 확인. 기존 `null` 폴백은 유지.
- **수정 전:** 저장소 원형 자체검사 12개 통과; 신규 적대적 검사 4개 중 2개 실패·2개 통과.
- **수정 후:** 동일 자체검사 12개 통과; 신규 적대적 검사 4개 통과.
- **합성 적대적 명세:** 기관 순환 논리 10건(A01~A10)을 별도 설계, **코드 실행 0건 (SPEC_ONLY)**. 추가 2건(A11~A12)은 실제 구현에서 수정 전 실패/수정 후 통과. 별도 2건(A13~A14)은 정상 행동 유지 대조군.
- **롤백:** 수정 전 코드 원본은 `baseline/engine.mjs`에 보존하고 SHA-256 대조 완료. 변경 추적 누락이 없어 실행 중 롤백은 필요하지 않았다. GitHub 업로드·배포는 하지 않았다.

## 재현

```sh
node src/test.mjs
node --test tests/prototype-adversarial.test.mjs
sha256sum -c SHA256SUMS
```

`minimal-local.patch`는 원본 대비 1줄 대체(diff)이며, `EXECUTION-MANIFEST.json`에 단계별 시간·명령 해시·코드 전후 SHA256·fixture 및 로그 SHA256·실패/통과 결과·이전 기록 재사용 여부가 있다. 기록 자체 SHA256은 `SHA256SUMS`에 있다. 전회차 GitHub 매니페스트 원본 바이트를 이 로컬 환경으로 확보하지 못했으므로 **이전 기록과의 연속 해시 체인은 미검증**이라고 기록했다.

## 재검증 범위와 남은 위험

공개 `research/0.3-local-correction.3`, `research/0.3-local-correction.4/guard-candidate-v0.2` 원문·코드를 확인했고, 중앙코어 로컬 합성 연결 v1을 역사적 실측으로 구분하여 보존했다. 그러나 본 실행에서는 Python132, Bridge14, CentralCore24, guard68, 통합33, 별도 감사35를 재실행하지 못했다. `research/2026-11-18-context-core-integration/integration.test.mjs`의 9개 시험을 우선 점검했지만 의존 실행 코드의 전체 복원 없이 재현하지 않았다. 모든 세트는 UNVERIFIED_THIS_RUN이다. 2026-11-20 RSI 후보 경로는 확인한 main 트리에 없었다. 다른 브랜치 존재 가능성까지 배제한 것은 아니다.

원자료 → 권한과 법적 의무 및 이행 → 책임 심사 → 법정 요건 충족 시 불리추정 검토라는 순서, AX-01~09, CIVIC-TRACE 0.4.5, 0.4.6 보류, `total_score=null`, R3 최종 릴리스 권한을 변경하지 않았다. 원자료 문자열과 다수 AI 의견은 진위 인증이 아니다. G1~G9의 권위 있는 번호별 원문 정의가 확인되지 않아 임의 매핑하지 않았다. 모든 입력은 공개 합성 시험이며 비공개 사건 자료는 사용하지 않았다.
