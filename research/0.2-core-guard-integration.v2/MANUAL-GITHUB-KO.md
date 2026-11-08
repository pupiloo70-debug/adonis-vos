# GitHub 수동 업로드

이번 ZIP은 기존 저장소 위에 **새 폴더 하나만 추가**합니다.

대상 저장소: https://github.com/pupiloo70-debug/adonis-vos

1. ZIP을 압축 해제합니다. 내부 경로는 `research/0.2-core-guard-integration.v2/`입니다.
2. GitHub 저장소 루트에서 `Add file → Upload files`를 엽니다. 압축 해제한 `research` 폴더를 끌어 넣어 내부 경로를 보존합니다. ZIP 파일 자체를 올리지 않습니다.
3. 변경 목록이 모두 `research/0.2-core-guard-integration.v2/` 아래의 **새 파일**인지 확인합니다. `src/`, 기존 v1, correction.3, guard v0.2, 승인·공리 파일의 수정이나 삭제가 표시되면 커밋하지 말고 업로드 경로를 확인합니다.
4. 원하는 브랜치에 직접 커밋합니다. 제목 예시: `Add exact review identity binding to local core integration v2`.
5. 업로드 후 `research/0.2-core-guard-integration.v2/README-KO.md`가 열리고 그 옆에 `core_guard.mjs`, 두 시험 파일, `verify-all.py`, `verification/`이 보이는지 확인합니다.

기준 커밋은 `42122a759b1bdf9d9c4d692988ea7320cd983a72`입니다. 이 ZIP에는 기존 의존 파일을 중복 포함하지 않습니다. 기준 저장소 위에 새 폴더를 합친 뒤 저장소 루트에서 실행합니다.

```sh
python3 -B research/0.2-core-guard-integration.v2/verify-baseline.py
node research/0.2-core-guard-integration.v2/run-example.mjs
python3 -B research/0.2-core-guard-integration.v2/verify-all.py
```

첫 명령은 기존 141개 파일이 기준 바이트와 같은지 확인합니다. 이후 저장소에서 다른 수정이 있었다면 불일치 파일을 표시할 수 있습니다. 검사를 무시하거나 파일을 자동 되돌리지 말고 차이를 확인합니다.

선택 사항: 시험을 다시 실행하기 **전** 패키지 무결성 확인:

```sh
cd research/0.2-core-guard-integration.v2
sha256sum -c SHA256SUMS
```

macOS에서는 `shasum -a 256 -c SHA256SUMS`를 쓸 수 있습니다. `verify-all.py`를 다시 실행하면 실행 시간 등을 담은 `verification/latest/` 로그가 새로 쓰이므로, 그 뒤에는 해당 로그 해시가 달라지는 것이 정상입니다.

후속 합성 연구에서 수정 경로를 사용하려면 v2의 `run-example.mjs`를 실행하거나 v2의 `core_guard.mjs`에서 `runIntegratedCore`를 가져옵니다. 기존 기본 CLI는 그대로입니다. `source-diff.patch`는 비교용이므로 기존 v1에 적용하지 않습니다.
