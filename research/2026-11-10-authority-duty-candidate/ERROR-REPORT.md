# 오류 보고와 보완 범위
작성일: 2026-11-10

## A. 기존 경고 코드 결함: 해결로 과대 보고하지 않음
발견 ID: BINDING-WARNING-CODE-PREREQUISITE-001.
기존 코어가 변조를 차단한 것이 아니라 candidate.patch가 제한된 V8 경계 재시험에서 20건을 보류했다. 기존 기록의 full_Node_Python_replay=0을 유지한다.
기준 커밋 ff9d961ced23462666d88e1103edd78ac2384ebe의 과거 결과를 현재 main의 완전 검증으로 재사용하지 않는다.
기존 수정 후보의 규칙 목록 복제에는 버전 연결·변경 감지 시험이 남아 있고, 한 경고 오류로 검토 전체를 보류하는 범위도 별도 검토 대상이다.
이번 패키지는 이 패치를 적용하지 않았다. 원문: https://github.com/pupiloo70-debug/adonis-vos/blob/d8ef4f72f02a971a598d81444cd9426cfe3cce9d/research/2026-11-09-warning-code-boundary-candidate/verification-record.json

## B. 이번 독립 후보에서 재현한 시간순서 결함
입력: 동일한 합성 질문의 과거 CORE_ACCESS_VERIFIED 이후 REQUEST_RECEIVED가 새로 발생하고, 입력된 유효 기한은 지났으나 후속 답변은 없다.
수정 전: 과거 열람을 최신 이행으로 사용해 VERIFIED_FOR_THIS_QUESTION을 반환했다.
요구 결과: 새 요청 이후의 답변만 현재 이행 평가에 사용하고 과거 열람·누적 부담·잔여 질문은 보존한다.
수정: 최신 요청 시각 이후의 응답만 현재 이행 상태로 선택한다.
재현 명령: node --test authority-duty.test.mjs
동일한 21개 합성시험에서 수정 전 20 통과·1 실패, 수정 후 21 통과. 로그와 소스 해시는 execution-record.json 참조.
이 오류는 이번 독립 후보의 오류이며 기존 공개 중앙코어에서 재현된 결함이라고 주장하지 않는다.

## C. 제안 문구와 실제 능력의 경계
영구 보존·완전 잠금·비선형 EGW·임계값·독립 시민위원회의 강제권은 구현·승인·법적 권한 확보 사실이 아니다.
대체 수단 제공 사실과 그 실효성은 별도다. 감정의 강도를 복수 의도의 증거로 쓰지 않는다.
노드의 경고는 통제자의 설명과 근거 대조를 촉진해야 하며, 피해자의 지원을 자동 중단하거나 기관에 자동 면책을 주지 않는다.
