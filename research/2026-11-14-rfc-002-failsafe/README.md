# RFC-002 합성 검증 코드

영문 명세: [RFC-002-FAILSAFE.md](../../RFC-002-FAILSAFE.md)

Node.js에서 별도 실행하는 연구 후보입니다. 실제 CentralCore·Python 브리지·개인정보·외부 집행은 포함하지 않습니다. 입력 검사는 내장 검사로 실행하며 JSON Schema 파일은 입력 계약을 문서화합니다. 결과는 `EXECUTION-MANIFEST.json`과 `test-output.txt`에 있습니다.
