#!/usr/bin/env python3
"""
TIL -> Obsidian 동기화 스크립트

■ 사용법:
  python sync-to-obsidian.py          # 전체 동기화 (처음 설정, pull 후)
  python sync-to-obsidian.py --diff   # 변경분만 동기화 (커밋 후)

■ 동작 방식:
  전체 모드: 모든 .md 파일을 Obsidian에 동기화 (upsert + orphan 정리)
  diff 모드: 마지막 커밋에서 변경된 .md 파일만 동기화 (빠름)

■ Hook 구성:
  post-commit → --diff 모드 (내가 커밋할 때, 변경분만)
  post-merge  → 전체 모드 (pull 받을 때, 전체 동기화)

■ 태그 매핑:
  tag-mapping.json이 있으면 domain/topic 형식 태그를 사용한다.
  매핑에 없는 파일은 기존 방식(디렉토리명)으로 폴백한다.
"""

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path

# ============================================================
# 설정
# ============================================================

TIL_PATH = Path(__file__).parent.parent
OBSIDIAN_PATH = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Note/09.TIL"
TAG_MAPPING_PATH = TIL_PATH / "tag-mapping.json"

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


def get_deleted_md_files() -> list[str]:
    """마지막 커밋에서 삭제된 .md 파일 목록 반환

    --diff-filter=D: 삭제된 파일만 필터링
    """
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "--diff-filter=D", "HEAD"],
        capture_output=True,
        text=True,
        cwd=TIL_PATH,
    )

    deleted = []
    for line in result.stdout.strip().split("\n"):
        if line and line.endswith(".md"):
            # 파일명만 추출 (경로에서 stem)
            filename = Path(line).stem
            deleted.append(filename)
    return deleted


# ============================================================
# 동기화 함수들
# ============================================================

def sync_diff():
    """변경분만 동기화 (post-commit용, 빠름)

    마지막 커밋에서 변경된 .md 파일만 처리한다.
    - 수정/추가된 파일 → Obsidian에 복사
    - 삭제된 파일 → Obsidian에서도 삭제
    """
    OBSIDIAN_PATH.mkdir(parents=True, exist_ok=True)

    # 1. 삭제된 파일 처리
    deleted_files = get_deleted_md_files()
    for filename in deleted_files:
        if filename not in {f.replace(".md", "") for f in EXCLUDE_FILES}:
            dest_path = OBSIDIAN_PATH / f"{filename}.md"
            if dest_path.exists():
                dest_path.unlink()
                print(f"  🗑️  {filename}.md 삭제")

    # 2. 변경된 파일 처리
    changed_files = get_changed_md_files()
    if not changed_files and not deleted_files:
        print("📝 변경된 .md 파일 없음")
        return

    synced_count = 0
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
            dest_path = OBSIDIAN_PATH / f"{filename}.md"
            dest_path.write_text(content, encoding="utf-8")
            synced_count += 1
            print(f"  📄 {filename}.md")
        except Exception as e:
            print(f"  ⚠️  {src_path.name} 처리 실패: {e}")

    print(f"✅ Obsidian 동기화 완료: {synced_count}개 변경, {len(deleted_files)}개 삭제")


def sync_full():
    """전체 동기화 (post-merge용, 처음 설정용)

    모든 .md 파일을 처리한다.
    Upsert 방식: 소스 파일을 기준으로 덮어쓰기하고,
    소스에 없는 orphan 파일만 삭제한다.
    """
    OBSIDIAN_PATH.mkdir(parents=True, exist_ok=True)

    # TIL 소스 파일 순회 → upsert
    synced_files = set()
    synced_count = 0
    for item in TIL_PATH.iterdir():
        if item.is_dir() and item.name not in EXCLUDE_DIRS:
            topic = item.name.capitalize()
            for md_file in item.glob("*.md"):
                if md_file.name not in EXCLUDE_FILES:
                    try:
                        filename, content = process_file(md_file, topic)
                        dest_path = OBSIDIAN_PATH / f"{filename}.md"
                        dest_path.write_text(content, encoding="utf-8")
                        synced_files.add(unicodedata.normalize("NFC", f"{filename}.md"))
                        synced_count += 1
                    except Exception as e:
                        print(f"  ⚠️  {md_file.name} 처리 실패: {e}")

    # Orphan 정리: 소스에 없는 Obsidian 파일만 삭제
    # macOS(APFS/HFS+)는 파일명을 NFD로 저장하지만,
    # Python 문자열(synced_files)은 NFC이므로 비교 전에 정규화 필요

    orphan_count = 0
    for f in OBSIDIAN_PATH.glob("*.md"):
        if unicodedata.normalize("NFC", f.name) not in synced_files:
            try:
                f.unlink()
                orphan_count += 1
                print(f"  🗑️  orphan 삭제: {f.name}")
            except PermissionError as e:
                print(f"  ⚠️  {f.name} 삭제 실패: {e}")

    print(f"✅ Obsidian 동기화 완료: {synced_count}개 문서, {orphan_count}개 orphan 삭제")


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
