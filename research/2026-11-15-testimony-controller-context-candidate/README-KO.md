# Adonis VOS 0.3 연구 후보: 증언·자료통제·실질구제 맥락

상태: `RESEARCH_ONLY / NOT_INTEGRATED / NOT_RELEASED`. 공개 합성 입력 전용. 기존 0.2·correction.3·correction.4·통합 v1 소스 변경 없음.

## 기능
- 명시적 `claim_key`를 기준으로 중복 진술을 하나의 맥락으로 합치되 반복 횟수를 입증력·윤리중력 점수로 환산하지 않음.
- 오타/거친 언어는 임의의 의미 변형 없이 요약 필드의 공백/유니코드만 정규화. 원문 자동 저장 차단. 문장의 의미를 바꾸는 교정은 인간 검토 필요.
- 자료가 기관 통제하에 있으면서 미제공·미검색·폐기 등이 문서로 연결된 경우 공개·보존·설명·독립검토 필요성을 분리해 표시. 고의·범죄 자동 판정 금지.
- 금전 보상만으로 해결 완료 처리 불가. 비금전적 구제 요소의 확인 상태 별도 기록.
- `total_score=null`; CIVIC-TRACE 0.4.5 승인 유지, 0.4.6 보류, AX-01~09 불변, R3 승인 권한 유지.

## 범위 제한
비공개 진술이나 실제 의료·소송 자료를 입력하지 마세요. `source_refs`는 사용자가 제공한 합성 식별자이며 서류 진위를 자동 인증하지 않습니다. 인지 가능한 범위의 자료 통제자 설명 요청·조사 필요성 검토는 법적 판단이 아닙니다. 의미적 중복 인식이나 언어모델의 자동 교열·오타 수정은 **구현하지 않았습니다**. 일치하는 claim_key만 중복 인식하고 다른 요약은 사람이 검토해야 합니다. 기간 수치화 공식은 도입하지 않았습니다.

## 실행
GitHub 저장소 루트에 `research/2026-11-15-testimony-controller-context-candidate/`를 그대로 배치한 뒤:
`node --test research/2026-11-15-testimony-controller-context-candidate/testimony-controller.test.mjs`

기존 0.2 회귀시험은 `node src/test.mjs`와 `node --test tests/project.test.mjs`로 별도 실행. 증언 모듈은 현재 통합 호출 경로에 연결되지 않은 연구 후보입니다.
