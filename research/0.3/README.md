# Adonis VOS 0.3 — 피해자 지원 서면·인용 검증

**0.3.0-design.2 · DESIGN_CANDIDATE / LOCAL_TEST_ONLY · 미배포**

최우선 결과물은 원자료와 연결된 피해자 지원 서면입니다. 불필요한 양보를 검토하되 필요한 의학적 유보·불리한 사실·전문가 이견은 보존합니다. 변호사와 전문가 검증 노드의 지위를 유지합니다.

- [설계·목적 함수·6.3 상향·징계 검토·0.4 입법 연구](docs/DESIGN-0.3.md)
- [기계판독 설계](design-0.3.json)
- [합성 입력](examples.json) / [실제 로컬 출력](sample_results.json)
- [지원 서면 합성 예시](sample-support-draft.txt)
- [변경·시험 검토](REVIEW.md) / [시험 출력](test-output.txt) / [실행 기록](execution-record.json)
- [참조한 공개 원문과 해시](sources/provenance.json)

## 실행

Python 표준 라이브러리만 사용합니다. 이번 실행 환경은 execution-record.json에 기록합니다.

```sh
python3 -m unittest discover -v
python3 vos_verify.py examples.json --now 2026-11-03T12:00:00+09:00
python3 vos_verify.py examples.json --now 2026-11-03T12:00:00+09:00 --output my-local-report.json
```

출력 경로가 이미 있으면 덮어쓰지 않습니다. --now는 명시적인 평가 시각이며 실제 법정 기산이나 상시 실행을 주장하지 않습니다. 실제 개인 자료와 출력은 공개 저장소에 업로드하지 마세요. 포함된 입력·서면 예시는 모두 합성 자료입니다.

## 현재 가능한 일

제공된 원문과 사건 식별자·직접 인용·연구 범위·통계 분모를 비교하고, 출처를 연결한 증거표와 자료제출·설명·보존·전문 검토 요청 초안을 생성합니다. CT-RULE-6.3 검토 상향과 R2.6 증거 상태를 구별하며 기한·담당·수신 공백을 표시합니다.

실제 법원·논문 원문 직접 조회와 진위 인증은 미구현입니다. SOURCE_MATCH_CANDIDATE는 제공 자료의 로컬 비교 결과일 뿐입니다. 필요한 유보와 양보 탐지는 규칙 기반 검토 보조이며 문맥 전반을 이해하는 법률 엔진이 아닙니다. 정합성 루프는 제한된 재실행과 잠금 검사이며 자율적 사실 수정이나 독립 검증이 아닙니다.

total_score=null. 부패지수 산식·R2.6 단계·징계·규칙 승인·법원 제출을 자동 결정하지 않습니다. 기존 AX-01~AX-09, CIVIC-TRACE 0.4.5 유지·0.4.6 보류를 그대로 둡니다. 11월 6일 예정 시험은 오늘 시험과 별개입니다.

공개 코드 기준선은 [adonis-vos 0.2](https://github.com/pupiloo70-debug/adonis-vos)입니다. 이 Python 후보와 0.2 JavaScript 중앙 코어의 통합은 아직 시험하지 않았습니다. 라이선스는 기존 UNLICENSED를 유지하며 이 묶음으로 새로운 이용허락이나 권리 확보를 완료하지 않았습니다.

