#!/usr/bin/env python3
"""
TIL -> Obsidian 동기화 스크립트
- Frontmatter 자동 생성
- Flat 구조로 저장 (폴더 없이 파일만)
- 관련 문서 링크를 Obsidian 형식으로 변환
"""

import re
from pathlib import Path

# 경로 설정
TIL_PATH = Path(__file__).parent.parent
OBSIDIAN_PATH = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Note/09.TIL"

# 제외할 파일/폴더
EXCLUDE_FILES = {"README.md", "CLAUDE.md"}
EXCLUDE_DIRS = {".git", ".github", ".githooks", ".claude", "scripts"}


def extract_title(content: str) -> str:
    """첫 번째 # 제목 추출"""
    match = re.search(r"^# (.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"


def extract_sources(content: str) -> list[str]:
    """## 출처 섹션에서 URL 추출"""
    sources = []
    # ## 출처 섹션 찾기
    match = re.search(r"## 출처\s*\n([\s\S]*?)(?=\n## |\Z)", content)
    if match:
        section = match.group(1)
        # 마크다운 링크에서 URL 추출
        urls = re.findall(r"\[.*?\]\((https?://[^\)]+)\)", section)
        sources.extend(urls)
    return sources


def extract_related_notes(content: str) -> list[str]:
    """## 관련 문서 섹션에서 링크 추출하여 Obsidian 형식으로 변환"""
    notes = []
    # ## 관련 문서 섹션 찾기
    match = re.search(r"## 관련 문서\s*\n([\s\S]*?)(?=\n## |\n---|\Z)", content)
    if match:
        section = match.group(1)
        # 마크다운 링크에서 파일명 추출: [제목](./파일명.md) 또는 [제목](파일명.md)
        links = re.findall(r"\[([^\]]+)\]\(\./?([\w\-]+)\.md\)", section)
        for title, filename in links:
            # Obsidian 링크 형식으로 변환
            notes.append(f"[[{filename}]]")
    return notes


def convert_internal_links(content: str) -> str:
    """문서 내 상대 링크를 Obsidian 형식으로 변환"""
    # [제목](./파일명.md) -> [[파일명|제목]]
    def replace_link(match):
        title = match.group(1)
        filename = match.group(2)
        return f"[[{filename}|{title}]]"

    content = re.sub(r"\[([^\]]+)\]\(\./?([\w\-]+)\.md\)", replace_link, content)
    return content


def generate_frontmatter(title: str, sources: list[str], topic: str, related_notes: list[str]) -> str:
    """Frontmatter YAML 생성"""
    lines = ["---"]

    # title
    lines.append(f'title: "{title}"')

    # source
    if sources:
        if len(sources) == 1:
            lines.append(f"source: {sources[0]}")
        else:
            lines.append("source:")
            for src in sources:
                lines.append(f"  - {src}")

    # topics
    lines.append("topics:")
    lines.append(f"  - {topic}")

    # related_notes
    if related_notes:
        lines.append("related_notes:")
        for note in related_notes:
            lines.append(f'  - "{note}"')

    # tags
    lines.append("tags:")
    lines.append(f"  - {topic.lower()}")
    lines.append(f"  - TIL")

    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def process_file(src_path: Path, topic: str) -> tuple[str, str]:
    """파일 처리: frontmatter 추가 및 링크 변환"""
    content = src_path.read_text(encoding="utf-8")

    # 이미 frontmatter가 있으면 제거 (새로 생성할 것이므로)
    if content.startswith("---"):
        # 두 번째 --- 찾기
        end_match = re.search(r"\n---\n", content[3:])
        if end_match:
            content = content[3 + end_match.end():]

    # 정보 추출
    title = extract_title(content)
    sources = extract_sources(content)
    related_notes = extract_related_notes(content)

    # 내부 링크 변환
    content = convert_internal_links(content)

    # Frontmatter 생성
    frontmatter = generate_frontmatter(title, sources, topic, related_notes)

    # 최종 콘텐츠
    final_content = frontmatter + content

    return src_path.stem, final_content


def sync_to_obsidian():
    """TIL을 Obsidian으로 동기화"""
    # Obsidian 폴더 생성
    OBSIDIAN_PATH.mkdir(parents=True, exist_ok=True)

    # 기존 파일 삭제 (clean sync)
    for f in OBSIDIAN_PATH.glob("*.md"):
        try:
            f.unlink()
        except PermissionError as e:
            print(f"⚠️  {f.name} 삭제 실패: {e}")

    # TIL 폴더 순회
    synced_count = 0
    for item in TIL_PATH.iterdir():
        if item.is_dir() and item.name not in EXCLUDE_DIRS:
            topic = item.name.capitalize()
            # 폴더 내 .md 파일 처리
            for md_file in item.glob("*.md"):
                if md_file.name not in EXCLUDE_FILES:
                    try:
                        filename, content = process_file(md_file, topic)
                        # Obsidian에 저장 (flat)
                        dest_path = OBSIDIAN_PATH / f"{filename}.md"
                        dest_path.write_text(content, encoding="utf-8")
                        synced_count += 1
                    except Exception as e:
                        print(f"⚠️  {md_file.name} 처리 실패: {e}")

    print(f"✅ Obsidian 동기화 완료: {synced_count}개 문서 → 09.TIL")


if __name__ == "__main__":
    sync_to_obsidian()
