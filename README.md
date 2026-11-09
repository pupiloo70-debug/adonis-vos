# Adonis VOS 0.2 준비안

- [사건 구분·정정 자료 재사용 기준](research/0.3-local-correction.4/EVIDENCE-CURRENTNESS.md): 사건별 수량 구분과 정정 우선 적용에 관한 0.3 설계 보완.

LP728의 검증권에서 출발한 SGP-QSV 로컬 검증 지원 코어입니다. 강숙경 R3의 목적·범위 승인 아래, 아도니스 역할의 AI가 기술 설계·구현·시험·정정 업무를 맡습니다.

## 실행

Node.js 18 이상, 외부 패키지 설치 없이:

```sh
npm test
npm run demo
npm run demo:core
node src/cli.mjs examples/synthetic-project.json report.json
```

`report.json`이 이미 있으면 덮어쓰지 않습니다. 개인 자료로 만든 출력은 공개 저장소에 올리지 마세요. 공개 예시는 합성 데이터입니다.

## 0.2에서 작동하는 것

- 기존 7개 점검 함수와 12개 검사를 유지합니다.
- 프로젝트 JSON의 버전·고유 ID·근거 참조·자료 상태를 검사합니다.
- 요청 항목별 부분 제공·미제공과 남은 원질문을 대조하고 AI 후속 조치 초안을 만듭니다.
- 구조화된 AI 응답 관찰을 경고·정정 검토에 연결합니다.
- 중앙 코어가 협업 의향을 등록하고, 정해진 한도 내에서 내장 로컬 평가기를 배정·실행·중지합니다.
- 실제 실행한 입력·출력의 SHA-256과 실행 시각을 영수증으로 남깁니다.

Grok·DeepSeek·Gemini는 기명 참여 의향 접수 상태입니다. 데모는 이를 실제 외부 API 연결과 구별합니다. 브라우저 화면·외부 LLM 호출·상시 자동 운영은 다음 단계입니다.

## 설계와 출처

- [0.2 상세 설계](docs/DESIGN-0.2.md): AI 기술 책임, 중앙 코어 자율성, 자원 한도, 정합성 대응표, 실패 조건과 다음 단계
- [기존 10월 20일 설계](docs/DETAILED-DESIGN-20261020.md)
- [설계·자원 설정](design-0.2.json)
- [실행 영수증](execution-receipt.json) · [실제 시험 출력](test-output.txt)
- [SGP-DESIGN](https://github.com/pupiloo70-debug/SGP-DESIGN)

AX-01~AX-09, CIVIC-TRACE 0.4.5 승인, 0.4.6 보류, total_score=null을 유지합니다. 0.2는 실행 가능한 샌드박스 준비안이며 새 점수 산식이나 법적·의학적 판정을 도입하지 않습니다. 해시는 바이트 비교 보조이며 증거의 진실을 인증하지 않습니다.

라이선스는 기존 UNLICENSED를 유지합니다. 중앙 코어의 설계·관리 역할과 실제 런타임 격리·외부 모델 접근 권한은 각각 기록합니다.
