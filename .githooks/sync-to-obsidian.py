#!/usr/bin/env python3
"""
TIL -> Obsidian 동기화 스크립트

■ 사용법:
  python sync-to-obsidian.py                 # 전체 동기화 (pull 후)
  python sync-to-obsidian.py --diff          # 변경분만 동기화 (커밋 후)
  python sync-to-obsidian.py --dry-run       # 판정만 하고 아무것도 쓰지 않음
  python sync-to-obsidian.py --verbose       # 생성·갱신한 노트 이름도 출력

■ 역할 분담:
  이 스크립트는 파일 탐색·git diff·파일 쓰기만 담당한다.
  노트 생성과 Wiki 문서와의 필드 단위 병합 판정은 vaultkit.tilsync가,
  새 노트의 MOC 등록은 vaultkit.register가 한다
  (~/.dotfiles/vault, spec: docs/superpowers/specs/2026-09-26-vault-policy-design.md 5절).
  vaultkit을 import하지 못하면 경고만 출력하고 동기화를 건너뛴다.

■ 병합 원칙 (노트별, Wiki/.til-sync-state.json 기준):
  - title·source·본문·topics·tags는 TIL 값, related_notes·created는 Wiki 값을 유지한다.
  - Wiki 본문이 마지막 동기화 이후 수정됐으면 본문은 두고 frontmatter만 병합하고
    "이관 필요"로 보고한다.
  - Wiki에서 지운 노트(state: synced, Wiki 파일 없음)는 retired로 기록하고
    다시 만들지 않는다.
  - Wiki 전용 노트와 이름이 겹치거나(대소문자만 다른 경우 포함) TIL 여러 폴더에 같은 이름이
    있으면 쓰지 않고 충돌로 보고한다.
  - 기존 Wiki 파일을 덮기 전에 <백업 루트>/til-sync-<시각>/에 복사하고, 쓰기는 같은 폴더
    임시 파일 + os.replace로 원자적으로 한다(백업 루트: VAULTKIT_BACKUP_DIR 또는
    ~/.local/state/vaultkit/backups).
  - 파일 삭제는 절대 하지 않는다 (Wiki는 TIL 외 개인 노트도 있는 공유 폴더).
  - 상태 파일이 없으면(이관 전) --dry-run만 허용한다.

■ Hook 구성:
  post-commit → --diff 모드 (내가 커밋할 때, 변경분만)
  post-merge  → 전체 모드 (pull 받을 때, 전체 동기화)

■ 환경변수 (테스트용 덮어쓰기):
  TIL_PATH, OBSIDIAN_PATH(Wiki 폴더), VAULTKIT_PATH(기본 ~/.dotfiles/vault),
  VAULTKIT_POLICY(vault-policy.json 경로), SYNC_STATE_PATH(기본 OBSIDIAN_PATH/.til-sync-state.json),
  VAULTKIT_BACKUP_DIR(백업 루트, 기본 ~/.local/state/vaultkit/backups)
"""

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

# ============================================================
# 설정
# ============================================================

TIL_PATH = Path(os.environ.get("TIL_PATH") or Path(__file__).resolve().parent.parent)
OBSIDIAN_PATH = Path(
    os.environ.get("OBSIDIAN_PATH")
    or Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Note/Wiki"
)
VAULTKIT_PATH = Path(os.environ.get("VAULTKIT_PATH") or Path.home() / ".dotfiles/vault")
VAULTKIT_POLICY = os.environ.get("VAULTKIT_POLICY")
SYNC_STATE_PATH = Path(os.environ.get("SYNC_STATE_PATH") or OBSIDIAN_PATH / ".til-sync-state.json")
TAG_MAPPING_PATH = TIL_PATH / "tag-mapping.json"

# 제외할 파일/폴더
EXCLUDE_FILES = {"README.md", "CLAUDE.md", "GEMINI.md", "AGENTS.md"}
EXCLUDE_DIRS = {".git", ".github", ".githooks", ".claude", "scripts", ".reviews"}

ACTIONS = ("create", "update", "frontmatter-only", "unchanged", "conflict", "retire", "skip-retired")
WRITE_ACTIONS = {"create", "update", "frontmatter-only"}


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


# ============================================================
# 탐색
# ============================================================

def _is_note(path: Path) -> bool:
    """TIL_PATH/<폴더>/<이름>.md 형식의 동기화 대상인지."""
    try:
        rel = path.relative_to(TIL_PATH)
    except ValueError:
        return False
    return (
        len(rel.parts) == 2
        and path.suffix == ".md"
        and rel.parts[0] not in EXCLUDE_DIRS
        and path.name not in EXCLUDE_FILES
    )


def scan_til() -> dict[str, list[Path]]:
    """TIL 전체 노트 {NFC stem: [경로...]} (같은 stem이 여러 폴더에 있으면 여러 개)."""
    index: dict[str, list[Path]] = defaultdict(list)
    for folder in sorted(TIL_PATH.iterdir()):
        if not folder.is_dir() or folder.name in EXCLUDE_DIRS:
            continue
        for md in sorted(folder.glob("*.md")):
            if _is_note(md):
                index[_nfc(md.stem)].append(md)
    return dict(index)


def scan_wiki() -> dict[str, Path]:
    """Wiki 루트의 노트 {NFC stem: 실제 경로} (디스크 파일명은 NFD일 수 있다)."""
    return {_nfc(p.stem): p for p in OBSIDIAN_PATH.glob("*.md")}


def get_changed_md_files() -> list[Path]:
    """HEAD 커밋에서 추가·변경된 .md 파일 (삭제된 파일은 제외)."""
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD"],
        capture_output=True,
        text=True,
        cwd=TIL_PATH,
    )
    changed = []
    for line in result.stdout.split("\0"):
        if line.endswith(".md"):
            path = TIL_PATH / line
            if path.exists() and _is_note(path):
                changed.append(path)
    return changed


def load_tag_mapping() -> dict[str, list[str]]:
    if TAG_MAPPING_PATH.exists():
        raw = json.loads(TAG_MAPPING_PATH.read_text(encoding="utf-8"))
        return {_nfc(k): v for k, v in raw.items()}
    return {}


def state_ready() -> bool:
    """v2 상태 파일이 있는지. 없거나 구버전(v1: {stem: hash})이면 이관 전으로 본다."""
    try:
        data = json.loads(SYNC_STATE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False
    except (OSError, json.JSONDecodeError):
        return True  # 손상은 load_state가 오류로 보고한다
    return not (isinstance(data, dict) and "version" not in data)


# ============================================================
# 쓰기
# ============================================================

def write_note(path: Path, text: str) -> None:
    """같은 폴더 임시 파일에 쓴 뒤 ``os.replace``로 교체한다(중간에 실패해도 원본 유지).

    생성된 줄 끝을 그대로 쓴다. 쓰기 금지된 기존 파일은 덮지 않는다.
    실패하면 예외를 올린다(호출자가 state 미갱신).
    """
    exists = path.exists()
    if exists and not os.access(path, os.W_OK):
        raise PermissionError(f"쓰기 금지된 파일: {path}")
    if exists:
        mode = path.stat().st_mode & 0o7777
    else:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    # 임시 이름에 원래 이름을 넣지 않는다: 이름 한도(255)에 가까운 노트에 접두·접미사가
    # 붙으면 ENAMETOOLONG으로 쓰기 실패한다
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".til-sync-", suffix=".tmp")
    try:
        try:
            fh = os.fdopen(fd, "w", encoding="utf-8", newline="")
        except BaseException:
            os.close(fd)
            raise
        with fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)  # path는 디스크 이름(NFD일 수 있음) 그대로
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


class Backup:
    """덮어쓸 기존 Wiki 파일을 <루트>/til-sync-<시각>/에 복사한다(첫 복사 때 디렉터리 생성)."""

    def __init__(self, new_backup_dir, root: Path) -> None:
        self._new_backup_dir = new_backup_dir
        self._root = root
        self.dir: Path | None = None

    def save(self, path: Path) -> None:
        if not path.exists():
            return
        if self.dir is None:
            self.dir = self._new_backup_dir(self._root, prefix="til-sync-")
            print(f"💾 백업 위치: {self.dir}", flush=True)
        shutil.copy2(path, self.dir / path.name)


# ============================================================
# 동기화
# ============================================================

def sync(mode: str, dry_run: bool, verbose: bool) -> None:
    try:
        sys.path.insert(0, str(VAULTKIT_PATH))
        from vaultkit import tilsync
        from vaultkit.apply import backup_root, new_backup_dir
        from vaultkit.policy import load_policy
        from vaultkit.register import register_note
    except Exception as exc:  # ImportError 외 import 중 오류도 hook을 깨뜨리지 않는다
        print("⚠️ vaultkit 없음 — 동기화 건너뜀")
        print(f"  {type(exc).__name__}: {exc}")
        return

    ready = state_ready()
    if not ready and not dry_run:
        print("⚠️ state 없음 — 이관(Task 8) 전에는 --dry-run만 허용")
        return

    try:
        policy = load_policy(Path(VAULTKIT_POLICY) if VAULTKIT_POLICY else None)
        state = tilsync.load_state(SYNC_STATE_PATH)
        mapping = load_tag_mapping()
    except Exception as exc:  # PolicyError, ValueError(손상된 state), JSON 오류
        print(f"⚠️ 동기화 건너뜀: {exc}")
        return
    notes_state: dict = state["notes"]

    label = mode + (", dry-run" if dry_run else "")
    print(f"🔄 TIL → Obsidian 동기화 ({label})")
    if not ready:
        print("  (state 없음 — 판정만 표시)")

    til_index = scan_til()
    wiki_index = scan_wiki() if OBSIDIAN_PATH.is_dir() else {}
    # APFS는 대소문자를 구분하지 않아, 대소문자만 다른 새 이름으로 만들면 기존 파일을 덮는다
    wiki_folded = {stem.casefold(): path for stem, path in wiki_index.items()}
    backup = Backup(new_backup_dir, backup_root())
    if mode == "diff":
        targets = {_nfc(p.stem) for p in get_changed_md_files()}
    else:
        targets = set(til_index)

    today = date.today().isoformat()
    results: dict[str, list[str]] = {a: [] for a in ACTIONS}
    migrate: list[tuple[str, str]] = []
    conflicts: list[tuple[str, str]] = []
    unclassified: list[str] = []
    failures: list[tuple[str, str]] = []
    register_skipped: list[str] = []

    for stem in sorted(targets):
        paths = til_index.get(stem, [])
        if len(paths) > 1:
            folders = ", ".join(p.parent.name for p in paths)
            results["conflict"].append(stem)
            conflicts.append((stem, f"TIL 여러 폴더에 같은 이름({folders}) → 동기화하지 않음"))
            continue
        if not paths:
            continue
        src = paths[0]
        wiki_path = wiki_index.get(stem)
        try:
            gen = tilsync.build_note(src, src.parent.name, policy, mapping)
            existing = wiki_path.read_text(encoding="utf-8") if wiki_path else None
            decision = tilsync.merge(gen, existing, notes_state.get(stem), today, policy=policy)
        except Exception as exc:
            failures.append((stem, f"처리 실패: {exc}"))
            continue

        if decision.action == "create" and stem.casefold() in wiki_folded:
            other = wiki_folded[stem.casefold()]
            results["conflict"].append(stem)
            conflicts.append((stem, f"대소문자만 다른 Wiki 노트({_nfc(other.name)})가 있음 → 쓰지 않음"))
            continue

        dest = wiki_path or OBSIDIAN_PATH / src.name
        if decision.text is not None and decision.action in WRITE_ACTIONS and not dry_run:
            try:
                backup.save(dest)
                write_note(dest, decision.text)
            except OSError as exc:
                failures.append((stem, f"쓰기 실패: {exc}"))
                continue
        results[decision.action].append(stem)
        # 쓰기 실패한 노트는 실패 목록에만 남도록, 쓰기 뒤에 분류한다
        if decision.action == "conflict":
            conflicts.append((stem, decision.message))
        elif decision.action == "frontmatter-only":
            migrate.append((stem, decision.message))

        if decision.entry is not None and not dry_run:
            notes_state[stem] = decision.entry

        if decision.action == "create":
            if dry_run:
                register_skipped.append(stem)
            else:
                try:
                    reg = register_note(dest, policy)
                except Exception as exc:
                    failures.append((stem, f"MOC 등록 실패: {exc}"))
                else:
                    if reg.status == "unclassified":
                        unclassified.append(stem)

    til_deleted: list[str] = []
    if mode == "full":
        til_deleted = sorted(
            s for s, e in notes_state.items()
            if isinstance(e, dict) and e.get("status") == "synced" and s not in til_index
        )

    if not dry_run:
        try:
            tilsync.save_state(SYNC_STATE_PATH, state)
        except OSError as exc:
            failures.append((SYNC_STATE_PATH.name, f"state 저장 실패: {exc}"))

    # ---------------- 보고 ----------------
    for action in ACTIONS:
        print(f"  {action}: {len(results[action])}")
    if verbose:
        for action in ("create", "update"):
            for stem in results[action]:
                print(f"  📄 {action} {stem}")
    if register_skipped:
        print(f"  (dry-run: create {len(register_skipped)}건의 MOC 등록 판정은 생략 — 파일 미생성)")

    def _list(header: str, items: list[tuple[str, str]]) -> None:
        if items:
            print(f"{header} ({len(items)})")
            for stem, message in items:
                print(f"  - {stem}: {message}")

    _list("⚠️ 이관 필요(Wiki 본문 수정됨)", migrate)
    _list("⚠️ 충돌", conflicts)
    _list("📋 MOC 미분류", [(s, "MOC 절을 찾지 못함 → 수동 등록 필요") for s in unclassified])
    _list("⚠️ TIL에서 삭제됨", [(s, "state에 synced, TIL 원본 없음 → Wiki에서 수동 정리") for s in til_deleted])
    _list("❌ 실패", failures)
    if backup.dir is not None:
        print(f"💾 백업: {backup.dir}")


# ============================================================
# 메인
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="TIL -> Obsidian 동기화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python sync-to-obsidian.py                    # 전체 동기화
  python sync-to-obsidian.py --diff             # 변경분만 동기화
  python sync-to-obsidian.py --dry-run --verbose
        """,
    )
    parser.add_argument("--diff", action="store_true", help="HEAD 커밋에서 변경된 파일만 동기화 (post-commit용)")
    parser.add_argument("--dry-run", action="store_true", help="판정만 하고 파일·상태를 쓰지 않음")
    parser.add_argument("--verbose", action="store_true", help="생성·갱신한 노트 이름 출력")
    args = parser.parse_args()

    sync("diff" if args.diff else "full", args.dry_run, args.verbose)


if __name__ == "__main__":
    main()
