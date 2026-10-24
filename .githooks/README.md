# TIL → Obsidian 동기화

이 checkout에서 훅을 켜려면 한 번 실행한다. 다른 컴퓨터에서도 checkout별로 필요하다.

```sh
git config --local core.hooksPath .githooks
```

`post-commit`은 HEAD 변경분을, `post-merge`는 전체 노트를 동기화한다. merge/fast-forward가 없는 `git pull`(이미 최신)이나 rebase는 이 훅 실행을 보장하지 않는다. 그때는 수동 동기화를 실행한다.

```sh
python3 .githooks/sync-to-obsidian.py --dry-run --verbose
python3 .githooks/sync-to-obsidian.py --verbose
# 특정 문서 복구: --note를 반복할 수 있다.
python3 .githooks/sync-to-obsidian.py --note Kubernetes-Architecture --verbose
```

macOS의 `~/.dotfiles/vault/vaultkit`과 기존 v2 상태 파일이 필요하다. TIL 저장소와 dotfiles 양쪽의 동기화 코드를 함께 최신화해야 한다.

## 이미지

- 본문의 인라인 Markdown 이미지 `![설명](./assets/topic/figure.svg)`를 복사한다. SVG, PNG, JPEG, GIF, WebP, AVIF, BMP를 지원한다. 공백 경로는 `<...>` 또는 URL 인코딩을 쓴다.
- `.obsidian/app.json`의 `attachmentFolderPath`를 사용하며, 설정이 없으면 `Attachments/images`다. TIL 원본의 링크는 유지하고 Wiki 사본에만 첨부 파일의 상대 경로를 기록한다. alt text와 제목은 유지한다.
- 파일명에는 TIL 상대 경로와 내용 해시가 들어간다. 동일한 그림은 재사용하고, 갱신본은 새 이름으로 복사한다. 이전 첨부 파일은 자동 삭제하지 않는다. 기존 대상 파일의 내용이 다르면 덮지 않고 실패로 보고한다.
- 이미지 파일만 바뀐 커밋도 `--diff`에서 전체 노트를 재검사한다. 수동으로 수정한 Wiki 본문은 기존 병합 보호 규칙을 따른다.
- 이미지가 누락되거나 TIL/vault 밖을 가리키면 해당 노트와 상태 갱신을 건너뛰고 오류를 보고한다. 외부 URL은 그대로 유지하며 다운로드하지 않는다. 코드 블록과 인라인 코드 안의 예제는 변환하지 않는다.
- 참조형 이미지(`![alt][id]`), HTML `<img>`, Obsidian 자체 임베드는 이 변환의 대상이 아니다.
- `--dry-run`은 이미지·노트·상태·백업을 쓰지 않는다. 이미지 동기화 시 기존 상태 파일과 변경할 Wiki 문서를 `~/.local/state/vaultkit/backups/til-sync-<시각>/`에 백업한다.
