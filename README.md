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
