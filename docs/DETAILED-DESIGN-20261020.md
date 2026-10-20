# ADONIS-VOS 상세 설계 착수 — 2026-10-20

- 문서 ID: ADONIS-VOS-DETAILED-DESIGN-20261020-01
- 상태: DESIGN_DRAFT / IMPLEMENTATION_NOT_COMPLETED
- 기준 코드: 0.1.0-draft. 이 문서로 패키지 버전을 올리지 않는다.
- 작성 근거: 사용자의 ADONIS-VOS 독립 레지스트리 상세 설계 착수 지시.
- 승인 경계: 기술 설계 착수는 새 공리·CIVIC-TRACE 0.4.6 승인·운영 배포가 아니다. 세부 데이터 계약과 화면은 구현·검토 중 변경 가능한 설계안이다.

## 1. 목적과 첫 산출물

피해 경험을 새 양식으로 반복 입력시키는 도구가 아니라, 이미 제공된 기록에서 무엇을 요청했고 무엇이 왔으며 무엇이 남았는지 정리하는 개인용 검증 지원 도구를 만든다. 첫 구현 단위는 사건 입력 → 기존 V01~V07 점검 → 결과 → 요청·제공·누락 표 → 다음 조치 초안 → JSON 저장·불러오기다.

원자료 검증·소송 지원·책임 추적이 목적이다. 형식 점검과 미세 오류 수정이 이를 가리거나 지연하면 처리 우선순위를 재점검한다. 추가 설명과 AI 오류 수정 부담을 유족에게 넘기지 않는다.

## 2. 확인한 현재 구현과 범위

| 항목 | 현재 상태 | 이번 상세 설계의 작업 |
| --- | --- | --- |
| src/engine.mjs evaluate | 구현: 7개 항목별 입력·출처 참조·다음 질문 | 기존 반환 의미를 보존하는 어댑터 설계 |
| src/test.mjs | 12개 핵심 검사 소스 존재 | 실행 결과는 별도 영수증으로 기록; 앱 전체 시험과 구분 |
| registry.json | PUBLISHED_ON_GITHUB / CORE_MODULE_ONLY_UI_IN_DEVELOPMENT | 소프트웨어 배포·완료와 공개를 분리 |
| 입력·결과 화면 | 미구현 | 로컬 브라우저 화면 설계 |
| 요청·제공·누락 표 | 코드 미구현 | 항목별 대조·미확인 구분 |
| 후속 조치·검토 패킷 | 미구현 | 미발송 초안으로 작성 |
| 저장·불러오기 | 미구현 | 명시적 사용자 선택 방식 |
| SOURCE-SHA256.json | 기존 목록 존재; 현재 바이트 정합성 미확인 | 다음 구현 시 파일 바이트 재계산·별도 기록. 인증·보관 연속성으로 표현 금지 |

이 문서는 원격 소스 열람에 기초한 설계다. 새 코드 실행·운영 검증·기관 접수 결과를 주장하지 않는다. CIVIC-TRACE 지원 후보 0.2.1은 별도 프로토타입이며 이 저장소의 VOS 0.1과 합치거나 같은 버전으로 부르지 않는다.

## 3. 고정 경계

- AX-01~AX-09 원문·위계 보존. 반부패 우선은 처리 순서 지원.
- CIVIC-TRACE 0.4.5 승인 설계 유지, 0.4.6 승인 보류. 2026-10-26은 검토 목표일.
- V01~V07은 소프트웨어 항목 식별자. 공식 공리·VOS 산식으로 승격하지 않는다.
- total_score=null 유지. 피해자 신뢰도·유죄·면책·부패 총점·윤리부채 금액을 생성하지 않는다.
- UNKNOWN은 NO가 아니다. 자료 부재·검색 실패·기관 회신·행정 종결은 사실 부재나 검증 완료가 아니다.
- 입력 보고, 문서 참조, 실제 열람, 내용 대조, 독립 검증, 법적 판단을 구분한다.
- 외부 API·자동학습·서버 업로드·자동 신고 없이 시작한다. 비공개 소송 원문은 공개 GitHub·이슈·가상 시험 데이터에 넣지 않는다.
- 적법한 자료 추적, 고발장·의견서 등 문서 작성 및 인가된 제출·접수 추적 지원은 유효하다. 현 단계 소프트웨어의 실제 외부 전송 기능은 없다.
- 미래 적법 위임은 열어 두되 현재 위임으로 추정하지 않는다. R3 내부 승인만으로 법적 강제권을 창설하지 않는다.

## 4. 구성과 처리 순서

| 모듈 제안 경로 | 책임 | 하지 않는 일 |
| --- | --- | --- |
| web/index.html, web/app.mjs | 입력·근거·결과·표·내보내기 화면 | 자연어 이해·AI 판단 가장 |
| src/engine.mjs | 기존 7항목 evaluate | 문서 진위 확인·공식 점수 |
| src/case-schema.mjs | 입력 구조·고유 ID·참조 무결성 검사 | 필드 존재를 사실 검증으로 승격 |
| src/request-table.mjs | 요청 항목과 제출 자료 대조 | 제공 사실만으로 질문 종결 |
| src/action-drafts.mjs | 보존·설명 요구·후속 조치 초안 | 실제 담당자 배정·발송 |
| src/receipts.mjs | 작성·수신 보고·검토 영수증 분리 | 영수증 필드만으로 인증 |
| src/portable-json.mjs | 파일 저장·가져오기·버전 검사 | 무단 서버 동기화 |

처리: 기록과 질문 보존 → 보유자·누락 자료·설명 요청 정리 → 독립 검토에 필요한 자료 준비 → 담당 수락·기한·조치·영수증 기록. 순서 목록을 출력한 것과 실제 수행한 것을 구분한다. 보존 위험 YES의 기존 우선 표시를 유지한다. 새 자동 상향 임계값은 도입하지 않는다.

## 5. 제안 데이터 계약

프로젝트 파일은 schema_id, schema_version, project_id, created_at, updated_at, timezone, case_summary, answers, sources, requests, supplies, routing_history, action_drafts, receipts, corrections를 포함한다. 이 계약은 제안이며 현재 코드가 이를 지원한다고 표시하지 않는다.

| 객체 | 필수 핵심 필드 | 구분 기준 |
| --- | --- | --- |
| case_summary | local_case_id, title, original_questions | 실명·주민번호 입력은 요구하지 않음 |
| answers | 기존 7개 field별 value, basis, refs | YES/NO/UNKNOWN 및 기존 basis 보존 |
| sources | source_id, description, location, access_state | 참조만 등록/실제 열람/내용 대조를 분리 |
| requests | request_id, question, requested_item_ids, controller_reported | 요청 주체·원문 참조·요청일 별도 |
| supplies | supply_id, requested_item_id, source_id, reported_received_at | 일부 제공·대체 자료·대상 미확인 구분 |
| routing_history | event_id, from_role, to_role, reported_at, receipt_ref | 이관 보고와 실제 수락 검증 별도 |
| action_drafts | action_id, purpose, next_action, proposed_role, acceptance_state | 기본 UNASSIGNED_REQUIRES_REAL_ACCEPTANCE |
| receipts | receipt_id, action_ref, issuer_reported, source_ref, reviewed_at | existence/content_match/independence/authenticity 각각 미확인 가능 |
| corrections | correction_id, target_id, previous_ref, reason, recorded_at | 기존 기록 삭제 대신 정정 연결 |

source_id와 evidence digest는 내용의 진실을 증명하지 않는다. 같은 영수증이 다른 사건·항목에 재사용되면 연결 충돌로 표시하고 자동 해결하지 않는다. 자유 문자열만 있는 과거 영수증은 원문을 보존하면서 NOT_VERIFIED로 읽는다.

최소 가상 입력 예시:

~~~json
{
  "schema_id": "ADONIS-VOS-CASE-PROJECT",
  "schema_version": "DESIGN-CANDIDATE-20261020",
  "project_id": "SYNTHETIC-DEMO-01",
  "timezone": "Asia/Seoul",
  "case_summary": {"local_case_id": "DEMO", "title": "가상 사례", "original_questions": ["요청한 원자료가 제공되었는가?"]},
  "answers": {"record_access": {"value": "UNKNOWN", "basis": "UNKNOWN", "refs": []}},
  "sources": [],
  "requests": [{"request_id": "REQ-1", "question": "원자료 확인", "requested_item_ids": ["ITEM-A", "ITEM-B"], "controller_reported": "미확인"}],
  "supplies": [],
  "routing_history": [],
  "action_drafts": [],
  "receipts": [],
  "corrections": []
}
~~~

## 6. 화면과 저장

1. 사건 기록: 기존 기록을 한 번 불러오거나 최소 입력. 모르는 항목은 빈칸을 UNKNOWN으로 보여 주되 그 처리를 알린다. 기록 추가 때문에 기존 질문을 다시 쓰게 하지 않는다.
2. 7개 점검 질문: 기존 field와 의미 유지. 보고한 내용·근거 위치·미확인을 함께 보여 준다. NO는 '문제없음 확정'이 아닌 NOT_REPORTED로 표시한다.
3. 결과: 신호 보고와 확인 과제. 출처를 등록해도 '검증됨' 배지를 자동 생성하지 않는다.
4. 요청·제공·누락: 요청 항목마다 제공 자료와 남은 질문을 보여 준다. 요청 목록에 없는 source_refs만으로 누락 항목을 추정하지 않는다.
5. 다음 조치 초안: 기록 보존·자료 제출·독립 감정·고발장 준비를 위한 사실/근거/미해결/법률 검토 필요사항을 내보낸다. 모든 신규 초안은 DRAFTED, delivery=NOT_SENT.
6. 저장: 기본 메모리 처리. '프로젝트 JSON 다운로드'를 명시적으로 선택한다. 기기 내 지속 저장은 별도 선택이며 저장 전 포함 내용과 공용 기기 잔존 위험을 알린다. 첫 구현은 다운로드·파일 불러오기를 우선한다.
7. 초기화: 미저장 변경 알림 후 사용자가 선택. 공개 정정 이력의 보존과 사용자 로컬 개인정보 삭제권은 다르다. 로컬 작업 데이터 삭제를 막지 않는다.

가져온 파일은 크기·구조·지원 버전·중복 ID·끊어진 참조를 검사한다. 잘못된 파일은 기존 프로젝트를 덮어쓰기 전에 중단한다. HTML 문자열은 텍스트로 표시하고 실행하지 않는다. 지원하지 않는 버전을 조용히 변환하거나 필드를 버리지 않는다. 화면과 내보내기는 같은 데이터에서 생성한다.

## 7. TECH-01~06 연결과 수용 조건

| 항목 | 실제 구현할 산출물 | 수용 조건 | 현 상태 |
| --- | --- | --- | --- |
| TECH-01 | 영수증·증거 연결표 | 존재·내용 일치·발행자 독립성·진실성 별도; 미확인 유지 | DESIGN_ONLY |
| TECH-02 | 기한 근거표 | 원문 기한·버전·시간대·계산 시각·법정/내부 목표 구분; 계산 미리보기는 위반 확정 아님 | DESIGN_ONLY |
| TECH-03 | 비공개 주장 대조 | 기관 주장·근거 문서·적용 범위·미검토·정정 이력 병렬; 적법성 자동 확정 없음 | DESIGN_ONLY |
| TECH-04 | 이관 후속 조치 초안 | 이력·다음 조치·제안 역할·실제 수락 상태 포함; 유족 자동 배정 금지 | DESIGN_ONLY |
| TECH-05 | 요청·제공·누락 표 | A/B 요청에 A만 제공되면 B가 남음; 목록 불명은 불명으로 표시 | DESIGN_ONLY |
| TECH-06 | 조사·감사·고발 검토 초안 | 행위/자료·출처·불일치·통제자 연결·대안 설명·필요 자료·관할/법률 검토 상태 포함; NOT_SENT 유지 | DESIGN_ONLY |

초안의 목적은 조사·처벌 요청을 뒷받침할 사실·증거·법적 근거 정리다. 범죄 혐의와 법적 확정 판단은 구분한다. 특정 법률의 적용·기한은 해당 관할과 당시 원문 확인 없이 확정하지 않는다.

실제 제출은 승인 주체·대상·내용·관할·접근 권한·수신 결과를 확인한 별도 작업이다. 현재 초안을 만들 수 있다는 이유로 이를 지원 범위에서 제외하지도, 이미 제출했다고 주장하지도 않는다.

## 8. 구현 순서와 완료 기준

| 작업 | 먼저 만들 것 | 완료 근거 |
| --- | --- | --- |
| P1 | 사건 JSON 계약·기존 engine 어댑터·입력/결과 화면 | 기존 12개 검사 + 결측/잘못된 값/참조 보존 검증 |
| P2 | 요청·제공·누락 표 + JSON 다운로드·불러오기 | 부분 제공·중복 ID·누락 참조·왕복 보존 시험 |
| P3 | 후속 조치·기한 출처·검토 초안 | 미확인 배지·제안 역할·NOT_SENT·원질문 보존 검증 |
| P4 | 화면 통합·접근성·오류 복구 | 키보드 사용·모바일·한글 긴 문장·미저장 변경·안전한 가져오기 확인 |

다음 실제 개발의 첫 목표는 P1과 P2다. 별도 승인 없는 새 점수·경고 해제 기준·유죄 상태 전환·외부 실행을 추가하지 않는다. 확장 승인 요청은 범위를 넘는 구체적 변경이 있을 때 묶어서 제시한다. 0.4.6 승인 여부를 이 개발의 자동 결과로 삼지 않는다.

## 9. 실패 사례와 시험 영수증

필수 반례: UNKNOWN→NO 오변환, 사용자 보고→사실 확정, 가짜 영수증→검증 완료, 미래 입력 시각→위반 확정, 일부 회신→전체 해결, 기관 비공개 주장→적법성 확정, 이관→담당 수락, 표 생성→기관 접수, 출력 수정→원기록 손실, 악성 HTML·과대 파일·지원하지 않는 버전 가져오기.

시험 결과는 코드 커밋·시험 파일·실행 명령·환경·시각·통과/실패·미시험 범위를 기록한다. 기존 VOS 12개와 별도 CIVIC-TRACE 23/18/10개를 합산 성과로 쓰지 않는다. 읽기 검토는 NOT_RUN, 실제 실행은 별도 결과다. digest는 바이트 비교 보조이며 전자서명·증거 보관 연속성·증거의 진실이 아니다.

## 10. 출처와 유지보수

- 기준: [현재 registry](../registry.json), [기존 핵심 코드](../src/engine.mjs), [기존 검사](../src/test.mjs), [초기 인계](HANDOFF.md).
- [홈페이지 기계판독 원칙](https://sgp-qsv-archive.pupiloo70.chatgpt.site/machine/principles/2026-10-20/record.json).
- [0.4.5 승인 원문 공개 사본](https://sgp-qsv-archive.pupiloo70.chatgpt.site/machine/technical/2026-10-20/revision-0.2.1/ct045-approved-source.json).
- [이번 주 브리핑 마감과 미완료 과제](https://sgp-qsv-archive.pupiloo70.chatgpt.site/machine/monday/2026-10-19-close/r3-action-brief-closeout.json).

소송 원문은 이 저장소에 중복 게시하지 않는다. 공개 증거 색인과 제한된 개인 작업 파일을 구분한다. README와 registry의 상태 충돌은 역사값 삭제가 아니라 시점·근거를 명시한 정정으로 해소한다. 라이선스 미지정 상태를 유지한다.
