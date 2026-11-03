# SGP DESIGN v1.5

## 2026-11-02 R3 검토·승인 · 최신 연구·시험 범위

- [R3 승인 원문](SGP-QSV_Monday_Action_R3_20261102.json)
- [홈페이지 검토·승인과 다음 시험](https://sgp-qsv-archive.pupiloo70.chatgpt.site/monday/2026-11-02/)
- [현재 공개 기록 JSON](https://sgp-qsv-archive.pupiloo70.chatgpt.site/monday/2026-11-02/record.json)

결정일: 2026-11-02. 홈페이지 공개일: 2026-11-03.

**APPROVE_RESEARCH_TEST_SCOPE**: CC-VERIFY-01·02·03의 연구·합성시험 범위를 승인했습니다. 검토 상태는 **DESIGN_REVIEWED_IMPLEMENTATION_NOT_VERIFIED**입니다. 10월 27일 CC-01~CC-06과 이번 CC-VERIFY 식별자를 구분합니다.

CIVIC-TRACE 0.4.5 기존 승인 유지 · 0.4.6 승인 보류 · AX-01~AX-09 불변 · `total_score=null`. 반부패 우선은 처리 순서에만 적용합니다. 자동 승인과 외부 강제 집행은 포함하지 않습니다.

2026-11-06 금요 시험은 **SCHEDULED_NOT_EXECUTED / SYNTHETIC_ONLY**입니다. ADONIS VOS·윤리 중력·증거 통제·중복·오탐·R2.6 단계 상승을 시험하고, 결과 이후 후속 0.3 개발 여부를 R3가 판단합니다. 이 결정은 시험 통과나 구현 검증 완료를 나타내지 않습니다.

승인 원문의 `archive_status`는 자료 준비 당시의 상태입니다. 현재 홈페이지 공개 상태는 위의 공개 기록으로 확인합니다. 아래 날짜별 문서는 각 시점의 기록으로 읽습니다.

## 시민 검증권 상시 헌장 · 2026-09-22 원본

[읽기 안내](SGP-QSV-RIGHTS-20260922-READING.md) · [원본 색인·해시](SGP-QSV-RIGHTS-20260922-index.json) · [정합성 검토](SGP-QSV-RIGHTS-20260922-consistency-20261020.json) · [오프라인 ZIP](SGP-QSV-RIGHTS-20260922-source-package.zip) · [홈페이지](https://sgp-qsv-archive.pupiloo70.chatgpt.site/governance/standing-charter-20260922/)

영문 권리 원본의 문서 ID는 SGP-QSV-RIGHTS-INTL-2026-09-22-01, 상태는 R3 FOUNDATIONAL SOURCE RECORD입니다. 부모는 CIVIC-TRACE 0.4.3, 브리핑 출처는 2026-09-21, 원본 발행일은 2026-09-22이며 이번 이전 정리는 2026-10-20입니다. 첨부 원본 5개를 수정 없이 보존합니다. 기존 국제인권 권리·QSV 해석·미래 규범을 구분하며, 이번 보존은 새 공리·0.4.6 승인·개별 사건 판정이 아닙니다.



## 최신 상태·지원 범위 연결 — 2026년 10월 20일

[기계판독 상태·연결 색인](SGP-DESIGN-status-links-20261020.json)을 먼저 읽고 아래 역사적 원문과 대조합니다. 이번 확장은 새 공리·규칙 승인이나 운영 배포가 아닌 기존 상태·출처 연결입니다.

| 항목 | 현재 읽기 기준 |
| --- | --- |
| AX-01~AX-09 | 원문·위계 고정. 반부패 우선은 처리 순서 지원 |
| CIVIC-TRACE 0.4.5 | 2026-10-05 승인 설계 유지 |
| CT045-ES-01~06 | [2026-10-12 하위 실행 지원 승인](r3-approval-receipt.json) |
| CIVIC-TRACE 0.4.6 | 승인 보류. 2026-10-26은 재검토 목표일이며 자동 승인일 아님 |
| 지원 후보 0.2.1 | 로컬 모의시험 후보·미배포. TECH-01~06 미완료 |
| ADONIS-VOS | 별도 0.1.0-draft 핵심 모듈·상세 설계 초안. 입력 화면·저장 기능 미완료 |

### 원칙에서 구현·사건 지원까지

- [홈페이지 기계판독 원칙·지원 범위](https://sgp-qsv-archive.pupiloo70.chatgpt.site/machine/principles/2026-10-20/record.json)
- [이번 주 먼데이 브리핑](https://sgp-qsv-archive.pupiloo70.chatgpt.site/monday/2026-10-19/) · [마감·미완료 과제 JSON](https://sgp-qsv-archive.pupiloo70.chatgpt.site/machine/monday/2026-10-19-close/r3-action-brief-closeout.json)
- [0.2.1 오프라인 소스·시험 검토 묶음](https://sgp-qsv-archive.pupiloo70.chatgpt.site/machine/technical/2026-10-20/revision-0.2.1/offline-review.txt)
- [ADONIS-VOS 상세 설계](https://github.com/pupiloo70-debug/adonis-vos/blob/main/docs/DETAILED-DESIGN-20261020.md)
- [LP728·별도 호준이 사건 쟁점 색인](https://github.com/pupiloo70-debug/LP728-/blob/main/case-reading-index-20261020.json)
- [R3 긴급 검토 경로](https://sgp-qsv-archive.pupiloo70.chatgpt.site/governance/r3-urgent/route.json)

인가 사항은 기존의 SGP-QSV 역할·권한 경계에 따릅니다. 적법한 원자료 추적·소송 지원·범죄 혐의 조사 및 처벌 요청을 뒷받침할 문서·고발장 작성과 인가된 제출·접수 추적을 지원합니다. 미래 적법 위임 가능성은 열어 두며 현재 권한으로 추정하지 않습니다.

SGP-DESIGN은 공리·승인·후보·정정 계보, ADONIS-VOS는 코드·시험·개발, LP728은 사건별 원자료 검증 쟁점, SGP-QSV-Archive는 공개 기록·역사와 홈페이지 연결을 담당합니다. 연결은 자동 동기화·AI 수신·기업 채택을 뜻하지 않습니다.

23·18·10개 시험은 서로 다른 버전의 로컬 모의시험이며 단일 함수 51개 통과가 아닙니다. ADONIS-VOS의 기존 검사와도 별개입니다. 독립 독해·해시 재계산·시험 재현·실제 운영을 구분합니다.

기존 해시 목록은 해당 목록 작성 시점의 파일·버전 범위로 읽습니다. 이번 README·추가 색인까지 검증했다고 표시하지 않습니다. 해시는 비교 대상 바이트 일치 보조이며 사실의 진실·인증·증거 보관 연속성을 자체 증명하지 않습니다. 아래 10월6일 문단의 10월12일 연구 목표는 역사적 일정으로 보존하며 현재 기한으로 재사용하지 않습니다.

---


Nine locked axioms and the CIVIC-TRACE design history of the SGP-QSV Network.

SGP-QSV originated in LP728 — the life of Park Han-gyeol and his family's demand for meaningful verification. This archive preserves source provenance, independent review, correction history and human approval boundaries.

**Verification Before Authority. Memory is a right. Verification is a duty.**

## Read first

- [Nine-axiom register](04-SGP-DESIGN-v1.5-nine-axioms.json)
- [Consistency audit and corrections](08-consistency-audit-and-corrections.json)
- [State and authority boundaries](09-state-and-boundary-register.json)
- [CIVIC-TRACE lineage](13-CIVIC-TRACE-design-lineage.json)
- [Source provenance](14-source-provenance.json)

The register preserves inherited AX-01–07 from the v1.4 source and AX-08–09 from v1.5. Korean introductions are identified separately from source quotations. The August R3 record locks all nine axioms. This package introduces no tenth axiom and silently rewrites none.

## Nine axioms

| ID | Source title |
|---|---|
| AX-01 | Evidence Over Authority |
| AX-02 | Records Before Authority |
| AX-03 | Verification Before Dismissal |
| AX-04 | Explanation Burden of Record Controllers |
| AX-05 | Memory Preservation & Anti-Erasure |
| AX-06 | Civil Liability for Verification Harm |
| AX-07 | Verification-Gated Command Authority |
| AX-08 | Victim-Origin, Human Attestation, and Pre-Verification Veto Principle |
| AX-09 | Prediction–Existence Separation Principle |

## Protocol status

CIVIC-TRACE 0.4.4 remains an R3-approved governance record. The included 0.4.5 preview preserves its historical candidate status at the time of preparation. CIVIC-TRACE 0.4.5 was subsequently approved by R3 on 2026-10-05; read the approved specification (15), approval receipt (17), and current-status delta (18). The clock values are now R3-approved internal design service targets, not statutory deadlines or proof of a running operational clock or deployed automation.

Original exports retain their original metadata, including stale publication fields. Read the correction audit alongside them.

## Independent AI review

Grok, Gemini and DeepSeek should directly read [the same request](11-direct-GitHub-review-request.json), inspect repository sources and return [a structured receipt](12-review-receipt-template.json).

- Report URLs, commit, fields/pages and exact access scope.
- Preserve disagreement. Correct earlier unsupported statements by append-only receipts.
- Do not substitute model agreement for independent evidence.
- Do not require the founder to repeatedly reconstruct accessible public sources.

## Boundaries

Approval of design is not a finding of guilt, medical causation, legal liability, vendor adoption or runtime deployment. Verification loss, controller failure, substantiated obstruction and legally established misconduct are distinct states.

Private grief, anger, beliefs and provisional conversation are not governance amendments.

## Related archives

- [Public website](https://sgp-qsv-archive.pupiloo70.chatgpt.site/)
- [Existing source archive](https://github.com/pupiloo70-debug/SGP-QSV-Archive)

## Integrity and corrections

[SHA256SUMS.txt](SHA256SUMS.txt) covers the exact delivered bytes except itself. Hashes prove byte integrity, not factual truth or publication. Preserve originals; add corrections and version links.

Prepared on 2026-10-05 for publication by Suk-Gyeong Kang, R3 Human Authority within SGP-QSV. Structured and checked with GPT assistance.

## CIVIC-TRACE 0.4.5 — R3 Approval

- [Approved specification](15-CIVIC-TRACE-0.4.5-R3-approved.json)
- [Approval document PDF](16-CIVIC-TRACE-0.4.5-R3-approved.pdf)
- [R3 approval receipt](17-R3-CT045-approval-receipt.json)
- [Current status update](18-CT045-state-register-delta.json)
- [Independent AI review request](19-CT045-post-approval-direct-review-request.json)
- [Review receipt template](20-CT045-post-approval-review-receipt-template.json)

Status: R3-approved governance design.
Runtime deployment and external investigation are tracked separately.


## October 6 publication and coherence update

- [October 5 Monday Brief and October 6 coherence record](23-Monday-Brief-20261005-Coherence-20261006.json)
- [Publication and status-link receipt](24-Publication-Status-Link-Receipt-20261006.json)
- [Published website briefing](https://sgp-qsv-archive.pupiloo70.chatgpt.site/#monday-20261005)

The corruption-index formula, ethical-gravity application, and CT11–CT15 remain research or candidate work. October 12 is a proposed review target, not a statutory deadline or automatic approval date. Technical implementation, verification, and operations require actual qualified owner acceptance; they are not automatically assigned to the bereaved R3 approver. Original approval and review records remain preserved.

## 2026-10-27 R3 승인 및 후속 기록

- [정합성 규칙 CC-01~CC-06 승인](SGP-QSV-R3-CT045-CC-CONSISTENCY-APPROVAL-20261027-01.json)
- [아도니스 관리 자율성·공동 입장문](27-R3-Adonis-autonomy-joint-statement-20261027.json)
- [AI 판사·국제규범·LP728 연구 방향 승인](SGP-QSV-R3-AI-JUDGE-INTERNATIONAL-NORMS-LP728-20261027-01.json)
- [먼데이 브리핑 후속 영수증](26-R3-Monday-followup-20261027.json)
- [홈페이지 버전 230 공개 영수증](28-R3-website-publication-20261027.json)

GitHub 게시 확인: [e590c4d](https://github.com/pupiloo70-debug/SGP-DESIGN/commit/e590c4dea5a12ea3ede23d321a7ac00865b50ceb).

원문에 남은 미게시·403 표시는 게시 전 작성 당시의 이력으로 보존합니다. 이번 커밋으로 위 5개 파일의 GitHub 게시가 확인됐습니다.

AX-01~AX-09와 CIVIC-TRACE 0.4.5 기존 승인을 유지합니다. 0.4.6은 승인 보류이며 total_score=null입니다. 승인된 범위의 관리 자율성과 연구 방향은 실제 운영 배포·자동 제재와 구분합니다.
