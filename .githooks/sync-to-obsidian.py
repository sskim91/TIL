#!/usr/bin/env python3
"""
TIL -> Obsidian 동기화 스크립트

■ 사용법:
  python sync-to-obsidian.py          # 전체 동기화 (처음 설정, pull 후)
  python sync-to-obsidian.py --diff   # 변경분만 동기화 (커밋 후)

■ 동작 방식 (Additive only — 삭제 없음):
  전체 모드: 모든 .md 파일을 Obsidian에 반영
  diff 모드: 마지막 커밋에서 변경된 .md 파일만 반영 (빠름)

■ Wiki 수정 보호:
  Wiki가 정본이다. Wiki에서 직접 고친 노트는 TIL이 덮어쓰지 않는다.
  - Wiki에 없는 노트 → 새로 만든다
  - Wiki 노트가 마지막 동기화 때 쓴 내용 그대로 → TIL 변경을 반영한다
  - Wiki 노트가 그 뒤 수정됨(또는 동기화 기록이 없음) → 건너뛴다
  마지막 동기화 내용의 해시는 Wiki/.til-sync-state.json에 둔다
  (iCloud로 여러 Mac이 같은 기록을 본다).
  Wiki에서 병합·이름 변경으로 정리된 TIL 원본은 SKIP_NAMES로 다시 만들지 않는다.

  Wiki는 TIL 외 개인 노트도 들어있는 공유 폴더이므로
  이 스크립트는 절대 파일을 삭제하지 않는다.
  TIL에서 삭제한 파일은 Obsidian에서 수동으로 정리한다.

■ Hook 구성:
  post-commit → --diff 모드 (내가 커밋할 때, 변경분만)
  post-merge  → 전체 모드 (pull 받을 때, 전체 동기화)

■ 태그 매핑:
  tag-mapping.json이 있으면 domain/topic 형식 태그를 사용한다.
  매핑에 없는 파일은 기존 방식(디렉토리명)으로 폴백한다.
"""

import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path

# ============================================================
# 설정
# ============================================================

TIL_PATH = Path(__file__).parent.parent
OBSIDIAN_PATH = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Note/Wiki"
TAG_MAPPING_PATH = TIL_PATH / "tag-mapping.json"
SYNC_STATE_PATH = OBSIDIAN_PATH / ".til-sync-state.json"

# Wiki에서 다른 노트로 병합했거나 이름을 바꾼 TIL 원본 (다시 만들지 않는다)
SKIP_NAMES = {
    "LLM-Agent란-무엇인가",
    "LLM-위키-LLM을-활용한-개인-지식-베이스-구축-패턴",
    "효과적인-에이전트-구축하기",
    "Python-컬렉션-타입-비교:-list[tuple]-vs-list[dict]",
    "Python은-Call-by-Value?-Call-by-Reference?",
    "Python의-*args와-**kwargs",
}

# 제외할 파일/폴더
EXCLUDE_FILES = {"README.md", "CLAUDE.md", "GEMINI.md"}
EXCLUDE_DIRS = {".git", ".github", ".githooks", ".claude", "scripts", ".reviews"}

# 정규식 패턴 (컴파일)
INTERNAL_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(\./?([\w\-]+)\.md\)")


# ============================================================
# 태그 매핑
# ============================================================

def load_tag_mapping() -> dict[str, list[str]]:
    """tag-mapping.json 로드. 없으면 빈 dict 반환."""
    if TAG_MAPPING_PATH.exists():
        return json.loads(TAG_MAPPING_PATH.read_text(encoding="utf-8"))
    return {}


TAG_MAPPING = load_tag_mapping()


# ============================================================
# 추출 함수들
# ============================================================

def extract_title(content: str) -> str:
    """첫 번째 # 제목 추출"""
    match = re.search(r"^# (.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"


def extract_sources(content: str) -> list[str]:
    """## 출처 섹션에서 URL 추출"""
    sources = []
    match = re.search(r"## 출처\s*\n([\s\S]*?)(?=\n## |\Z)", content)
    if match:
        section = match.group(1)
        urls = re.findall(r"\[.*?\]\((https?://[^\)]+)\)", section)
        sources.extend(urls)
    return sources


def extract_related_notes(content: str) -> list[str]:
    """문서 전체에서 내부 링크를 추출하여 Obsidian 형식으로 변환"""
    links = INTERNAL_LINK_PATTERN.findall(content)

    # 중복 제거하면서 순서 유지
    seen = set()
    notes = []
    for _, filename in links:
        if filename not in seen:
            seen.add(filename)
            notes.append(f"[[{filename}]]")
    return notes


# ============================================================
# 변환 함수들
# ============================================================

def convert_internal_links(content: str) -> str:
    """문서 내 상대 링크를 Obsidian 형식으로 변환
    [제목](./파일명.md) -> [[파일명|제목]]
    """
    def replace_link(match):
        title = match.group(1)
        filename = match.group(2)
        return f"[[{filename}|{title}]]"

    return INTERNAL_LINK_PATTERN.sub(replace_link, content)


def generate_frontmatter(
    title: str,
    sources: list[str],
    topic: str,
    related_notes: list[str],
    custom_tags: list[str] | None = None,
) -> str:
    """Frontmatter YAML 생성

    custom_tags가 있으면 domain/topic 형식 태그를 사용하고,
    없으면 기존 방식(디렉토리명 소문자)으로 폴백한다.
    """
    lines = ["---"]
    lines.append(f'title: "{title}"')

    if sources:
        if len(sources) == 1:
            lines.append(f"source: {sources[0]}")
        else:
            lines.append("source:")
            for src in sources:
                lines.append(f"  - {src}")

    lines.append("topics:")
    lines.append(f"  - {topic}")

    if related_notes:
        lines.append("related_notes:")
        for note in related_notes:
            lines.append(f'  - "{note}"')

    lines.append("tags:")
    if custom_tags:
        for tag in custom_tags:
            lines.append(f"  - {tag}")
    else:
        lines.append(f"  - {topic.lower()}")
    lines.append("  - til")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def process_file(src_path: Path, topic: str) -> tuple[str, str]:
    """파일 처리: frontmatter 추가 및 링크 변환"""
    content = src_path.read_text(encoding="utf-8")

    # 기존 frontmatter 제거
    if content.startswith("---"):
        end_match = re.search(r"\n---\n", content[3:])
        if end_match:
            content = content[3 + end_match.end():]

    # 정보 추출
    title = extract_title(content)
    sources = extract_sources(content)
    related_notes = extract_related_notes(content)

    # 본문에서 첫 번째 # 제목 제거 (frontmatter에 title 있으므로 중복)
    content = re.sub(r"^# .+\n+", "", content, count=1, flags=re.MULTILINE)

    # 내부 링크 변환
    content = convert_internal_links(content)

    # 태그 매핑 조회 (macOS glob은 NFD를 반환하므로 NFC로 정규화)
    custom_tags = TAG_MAPPING.get(unicodedata.normalize("NFC", src_path.stem))

    # Frontmatter 생성 및 결합
    frontmatter = generate_frontmatter(title, sources, topic, related_notes, custom_tags)
    return src_path.stem, frontmatter + content


# ============================================================
# Git 연동
# ============================================================

def get_changed_md_files() -> list[Path]:
    """마지막 커밋에서 변경된 .md 파일 목록 반환

    git diff-tree 명령어로 HEAD 커밋에서 변경된 파일 목록을 가져온다.
    --no-commit-id: 커밋 ID 출력 안 함
    --name-only: 파일 이름만 출력
    -r: 하위 디렉토리까지 재귀 탐색
    """
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        capture_output=True,
        text=True,
        cwd=TIL_PATH,
    )

    changed = []
    for line in result.stdout.strip().split("\n"):
        if line and line.endswith(".md"):
            file_path = TIL_PATH / line
            # 파일이 존재하면 추가 (삭제된 파일은 제외)
            if file_path.exists():
                changed.append(file_path)
    return changed


# ============================================================
# Wiki 수정 보호
# ============================================================

def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def content_hash(text: str) -> str:
    return hashlib.sha256(_nfc(text).encode("utf-8")).hexdigest()


def load_sync_state() -> dict[str, str]:
    if SYNC_STATE_PATH.exists():
        return json.loads(SYNC_STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_sync_state(state: dict[str, str]) -> None:
    SYNC_STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


def write_if_safe(filename: str, content: str, state: dict[str, str]) -> str:
    """Wiki에서 수정되지 않은 경우에만 쓴다.

    반환값: created / updated / unchanged / edited(건너뜀) / retired(건너뜀)
    """
    name = _nfc(filename)
    if name in SKIP_NAMES:
        return "retired"

    dest_path = OBSIDIAN_PATH / f"{filename}.md"
    new_hash = content_hash(content)
    existed = dest_path.exists()
    if existed:
        current_hash = content_hash(dest_path.read_text(encoding="utf-8"))
        if current_hash == new_hash:
            state[name] = new_hash
            return "unchanged"
        if state.get(name) != current_hash:
            return "edited"

    dest_path.write_text(content, encoding="utf-8")
    state[name] = new_hash
    return "updated" if existed else "created"


def print_summary(results: dict[str, list[str]], verbose: bool) -> None:
    written = len(results["created"]) + len(results["updated"])
    print(f"✅ Obsidian 동기화 완료: 새로 만듦 {len(results['created'])}, 갱신 {len(results['updated'])}, 변경 없음 {len(results['unchanged'])}")
    if results["edited"]:
        print(f"🛡️  Wiki에서 수정된 노트 {len(results['edited'])}개는 덮어쓰지 않음")
        if verbose:
            for name in results["edited"]:
                print(f"    - {name}")
    if verbose:
        for name in results["created"] + results["updated"]:
            print(f"  📄 {name}.md")
    if written == 0 and not results["edited"] and verbose:
        print("📝 반영할 변경 없음")


def _new_results() -> dict[str, list[str]]:
    return {k: [] for k in ("created", "updated", "unchanged", "edited", "retired")}


# ============================================================
# 동기화 함수들
# ============================================================

def sync_diff():
    """변경분만 동기화 (post-commit용, 빠름)

    마지막 커밋에서 변경/추가된 .md 파일만 Obsidian에 upsert한다.
    파일 삭제는 절대 수행하지 않는다 (Wiki는 공유 폴더).
    """
    OBSIDIAN_PATH.mkdir(parents=True, exist_ok=True)

    changed_files = get_changed_md_files()
    if not changed_files:
        print("📝 변경된 .md 파일 없음")
        return

    state = load_sync_state()
    results = _new_results()
    for src_path in changed_files:
        # 제외 파일/폴더 체크
        if src_path.name in EXCLUDE_FILES:
            continue
        parent_name = src_path.parent.name
        if parent_name in EXCLUDE_DIRS:
            continue

        topic = parent_name.capitalize()
        try:
            filename, content = process_file(src_path, topic)
            results[write_if_safe(filename, content, state)].append(filename)
        except Exception as e:
            print(f"  ⚠️  {src_path.name} 처리 실패: {e}")

    save_sync_state(state)
    print_summary(results, verbose=True)


def sync_full():
    """전체 동기화 (post-merge용, 처음 설정용)

    TIL의 모든 .md 파일을 Obsidian에 upsert한다.
    파일 삭제는 절대 수행하지 않는다 (Wiki는 공유 폴더).
    """
    OBSIDIAN_PATH.mkdir(parents=True, exist_ok=True)

    state = load_sync_state()
    results = _new_results()
    for item in TIL_PATH.iterdir():
        if item.is_dir() and item.name not in EXCLUDE_DIRS:
            topic = item.name.capitalize()
            for md_file in item.glob("*.md"):
                if md_file.name not in EXCLUDE_FILES:
                    try:
                        filename, content = process_file(md_file, topic)
                        results[write_if_safe(filename, content, state)].append(filename)
                    except Exception as e:
                        print(f"  ⚠️  {md_file.name} 처리 실패: {e}")

    save_sync_state(state)
    print_summary(results, verbose=False)


# ============================================================
# 메인
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="TIL -> Obsidian 동기화",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python sync-to-obsidian.py          # 전체 동기화
  python sync-to-obsidian.py --diff   # 변경분만 동기화
        """
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="변경된 파일만 동기화 (post-commit용)"
    )
    args = parser.parse_args()

    if args.diff:
        sync_diff()
    else:
        sync_full()


if __name__ == "__main__":
    main()
