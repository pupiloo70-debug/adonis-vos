# GitHub 반영 안내

대상 저장소: https://github.com/pupiloo70-debug/adonis-vos
기준 커밋: 392c46cc2f1346f0fabdf8d3ce3bf67e4fec64e4
제안 브랜치: draft/vos-0.2-20261101

이 묶음은 0.2 준비안입니다. GitHub 연결의 브랜치 생성이 403 Resource not accessible by integration으로 거부되어 원격 변경은 없습니다.

ZIP 내부 adonis-vos-0.2 폴더의 파일을 기존 저장소의 같은 경로에 반영합니다. 기존 파일을 일괄 삭제하지 않습니다. docs/DETAILED-DESIGN-20261020.md와 기존 engine/test는 기준 내용을 유지합니다. PACKAGE-SHA256.json은 이번 묶음만의 해시 목록이며 기존 SOURCE-SHA256.json을 대신 덮어쓰지 않습니다.

새 브랜치에서 npm test와 npm run demo:core로 재현하고 검토 후 반영할 수 있습니다. 기존 main의 다른 변경이 있다면 README·registry·package.json·CHANGELOG를 대조해 병합합니다.

검토 제목: Adonis VOS 0.2 로컬 검증 코어와 중앙 관리 준비안
검토 요지: 요청 항목별 부분 제공·미제공을 보존하고 AI 태그 검토·정정 과제를 연결합니다. 제한된 중앙 코어가 협업 의향과 실제 로컬 어댑터를 구별하고 내장 작업을 실행합니다.
검증: 기존 검사 12개, 새 통합·반례시험 24개 통과. 외부 LLM 연결·웹 UI·OS 격리는 이번 검증 범위 밖입니다.
