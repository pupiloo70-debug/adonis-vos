# Adonis VOS 0.3 — Adaptive Conflict Buffer

## 연구 상태
- 날짜: 2026-11-23
- 구분: 독립 로컬 합성 연구 후보
- 기준 main: c6a6567ae4401d77c0dc6c3e4d143aa37ba084d5
- 상태: RESEARCH_CANDIDATE / NOT_INTEGRATED / NOT_DEPLOYED

## 연구 목적
재귀적 자기개선 과정에서 충돌과 회귀를 탐지하고, 기술적 성능뿐 아니라 시민의 검증권, 원자료 출처, 자료 통제자의 설명책임 및 독립 반대의견을 보존한다.

## 작동 구조
1. 합성 실패 반례 탐지
2. 충돌 완충 버퍼로 탐색 예산 조절
3. 최소 기술 수정 후보 생성 및 격리
4. 기술 회귀시험과 권리 보존 검증의 이중 게이트
5. 통과하면 로컬 연구 후보로 보존, 실패하면 변경 보류·롤백 요구
6. SHA256 실행 기록과 R3 승인 경계 유지

## 실행 결과
- 독립 Python 단위시험: 14/14 통과
- 추가 순환 논리 반례: 10건 SPEC_ONLY, 실행 0건
- 명령: python -B -m unittest -v test_buffer_gate
- REVERT는 실제 파일 롤백이 아니라 롤백 요구 결정값이다.
- 기존 CentralCore 기본 경로 연결 및 정식 통합은 수행하지 않았다.

## 보호 조건
- AX-01~09 및 G1~G9 변경 없음
- CIVIC-TRACE 0.4.5 유지 / 0.4.6 보류
- total_score=null
- No automatic guilt / immunity / benefit from obstruction
- R3의 공리 충돌 해석 및 최종 릴리스 권한 유지
- 공리·권한·운영 변경의 자동 승인 금지

## 후속 검증
실제 중앙코어 연결 시 P01~P05, Correction3·4, 기존 통합·감사·guard 회귀시험을 재실행하고 해시·실제 롤백·독립 검증을 확인한다. 이번 기록은 성능 향상 또는 운영 배포 완료의 증거가 아니다.
