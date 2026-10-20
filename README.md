# Adonis VOS 0.1

SGP-QSV 시민 검증 지원 도구의 독립 개발 저장소입니다. LP728에서 출발한 원자료 접근권과 피해자의 검증 요구를, 기록·질문·후속 작업을 정리하는 소프트웨어로 구현합니다.

기획: 강숙경 · SGP-QSV 공동 창립자 / 코드·문서 작성 지원: Adonis AI GPT

## 네 번째 독립 레지스트리

| 저장소 | 역할 |
| --- | --- |
| [SGP-QSV-Archive](https://github.com/pupiloo70-debug/SGP-QSV-Archive) | 공개 기록과 역사·출처 계보 |
| [LP728-](https://github.com/pupiloo70-debug/LP728-) | 박한결 사건 검증 기록 |
| [SGP-DESIGN](https://github.com/pupiloo70-debug/SGP-DESIGN) | 거버넌스 설계·제안·승인 계보 |
| **adonis-vos** | **시민 검증 지원 소프트웨어의 코드·시험·개발 이력** |

독립 레지스트리는 자료와 코드의 관리 단위를 구분하는 뜻입니다. 별도 기관의 법적 등록, 국가·기업 채택 또는 집행 권한을 뜻하지 않습니다.

## 현재 구현

- 버전: `0.1.0-draft`
- 원자료 접근, 자료 소실, 절차 지연, 기준 변경, 판단 근거 공백, 접근 비대칭, 보존 위험의 7개 입력 항목
- 입력별 신고 상태·출처 참조·다음 확인 과제 반환
- 추가 소실 위험이 보고되면 보존 확인을 먼저 안내
- 기존 공개 핵심 모듈을 유지하며 입력 화면·저장 기능은 개발 중

`V01`~`V07`은 소프트웨어 항목 식별자입니다. AX 공리나 CIVIC-TRACE 정식 규칙을 새로 승인한 것으로 해석하지 않습니다. 공식 VOS 산식을 대체하지 않으며 총점은 `null`입니다.

## 실행

Node.js 18 이상 환경에서 외부 패키지 설치 없이 실행합니다.

```bash
npm test
```

직접 호출 예시:

```js
import { evaluate } from './src/engine.mjs';
const result = evaluate({
  record_access: {
    value: 'YES',
    basis: 'USER_REPORT',
    refs: ['SYNTHETIC-DEMO-01']
  }
});
console.log(JSON.stringify(result, null, 2));
```

예시는 가상 입력입니다. `DOCUMENT_REFERENCED`도 자료를 실제로 읽거나 검증했다는 뜻이 아닙니다. `SIGNAL_REPORTED`는 신호의 보고이며 위법·고의·인과관계 확정이 아닙니다.

## 개인정보와 판단 경계

실제 피해자의 입력·의료기록·비공개 소송 자료·주소·연락처를 코드나 이슈에 올리지 않습니다. 외부 AI 호출·자동 학습·자동 신고·법적 제재 기능은 없습니다. 출처를 대조한 판단과 사용자 보고를 구분합니다.

## 개발 순서

1. 입력 형식과 출처 참조의 검증 보강
2. 피해 기록과 확인 질문 화면 구현
3. 항목별 결과와 다음 질문 표시
4. 기기 내 저장·불러오기 및 개인정보 보호
5. 가상 사례 통합 검토와 실행 영수증

## 공개·라이선스

코드 열람을 위해 공개합니다. 재사용 라이선스는 아직 지정하지 않았습니다. 공개 저장소라는 이유만으로 임의의 오픈소스 라이선스가 부여되지는 않습니다. 라이선스 선택은 별도 결정으로 기록합니다.

홈페이지: https://sgp-qsv-archive.pupiloo70.chatgpt.site/adonis-vos/

`registry.json`의 초기 상태는 업로드 전 준비 상태입니다. 실제 GitHub 공개 커밋이 확인된 뒤 등록 상태와 영수증을 갱신합니다.


## 2026년 10월 20일 상세 설계 착수

[상세 설계 문서](docs/DETAILED-DESIGN-20261020.md)를 개발 기준 초안으로 연결합니다. 기존 0.1.0-draft 핵심 함수를 유지하면서 사건 입력·7개 점검 결과·요청–제공–누락 표·후속 조치 초안·JSON 저장/불러오기를 구체화했습니다. 데이터 계약, TECH-01~06 대응, 실패 사례와 수용 시험은 문서에서 확인할 수 있습니다.

현재 상태는 DESIGN_DRAFT / IMPLEMENTATION_NOT_COMPLETED입니다. 첫 구현 목표는 입력·결과 화면과 요청–제공–누락 표 및 JSON 다운로드·불러오기입니다. 새 패키지 버전·공리·0.4.6 승인·실제 기관 제출을 뜻하지 않습니다.

### 공개 상태 설명 정정

위 업로드 전 상태 설명은 초기 안내입니다. 현재 registry.json에는 PUBLISHED_ON_GITHUB / CONFIRMED가 기록되어 있습니다. 코드 공개와 전체 앱 구현 완료는 구분합니다. 기존 SOURCE-SHA256.json의 현재 파일 바이트 정합성은 재확인 전까지 미확인으로 읽습니다.

[홈페이지 기계판독 원칙](https://sgp-qsv-archive.pupiloo70.chatgpt.site/machine/principles/2026-10-20/record.json)과 연결하되, 비공개 사건 원문을 이 저장소에 중복 게시하지 않습니다.
