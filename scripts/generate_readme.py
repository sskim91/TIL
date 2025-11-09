#!/usr/bin/env python3
"""
TIL README.md 자동 생성 스크립트
모든 마크다운 파일을 스캔하여 목차를 자동으로 생성합니다.
"""

import re
from collections import defaultdict
from pathlib import Path


def extract_title(file_path: Path) -> str:
    """마크다운 파일에서 첫 번째 # 제목을 추출"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()
    except (FileNotFoundError, IOError) as e:
        print(f"Error reading {file_path}: {e}")

    # 제목이 없으면 파일명을 제목으로 사용
    return file_path.stem.replace("-", " ").replace("_", " ").title()


def get_category_from_path(file_path: Path, base_path: Path) -> str:
    """파일 경로에서 카테고리 추출"""
    relative_path = file_path.relative_to(base_path)
    parts = relative_path.parts[:-1]  # 파일명 제외

    if not parts:
        return "기타"

    # 첫 번째 폴더가 카테고리
    category = parts[0]

    # 서브카테고리가 있으면 함께 반환
    if len(parts) > 1:
        return f"{category}/{parts[1]}"

    return category


def generate_readme() -> None:
    """README.md 생성"""
    base_path: Path = Path(__file__).parent.parent

    # README.md와 scripts 폴더의 파일들은 제외
    md_files = [
        f
        for f in base_path.rglob("*.md")
        if f.name != "README.md"
        and "scripts" not in f.parts
        and not f.name.startswith(".")
    ]

    # 카테고리별로 분류
    categories = defaultdict(list)

    for md_file in md_files:
        title = extract_title(md_file)
        category = get_category_from_path(md_file, base_path)
        relative_path = md_file.relative_to(base_path)

        categories[category].append({"title": title, "path": str(relative_path)})

    # README.md 생성
    readme_content = []
    readme_content.append("# TIL (Today I Learned)\n")
    readme_content.append("> 🤖 Learning with AI\n")

    # 통계
    total_count = len(md_files)
    readme_content.append(f"\n## 📊 통계\n")
    readme_content.append(f"- 총 TIL 개수: **{total_count}개**\n")
    readme_content.append(f"- 카테고리 수: **{len(categories)}개**\n")

    # 카테고리별 목차
    if categories:
        readme_content.append("## 📚 카테고리\n")

        # 카테고리 정렬 (알파벳순)
        for category in sorted(categories.keys()):
            entries = categories[category]
            readme_content.append(f"### {category}\n")

            # 제목 알파벳순 정렬
            for entry in sorted(entries, key=lambda x: x["title"].lower()):
                readme_content.append(f"- [{entry['title']}]({entry['path']})\n")

            readme_content.append("\n")

    # 작성 규칙
    readme_content.append("---\n")
    readme_content.append("## 📝 작성 규칙\n\n")
    readme_content.append("- 폴더명은 소문자로 작성합니다\n")
    readme_content.append("- 각 문서는 `# 제목`으로 시작합니다\n")
    readme_content.append("- 카테고리별로 폴더를 구분합니다\n")
    readme_content.append("- README는 자동으로 생성되므로 직접 수정하지 않습니다\n")

    # 파일 저장
    readme_path = base_path / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(readme_content))

    print(f"✅ README.md 생성 완료!")
    print(f"   - 총 {total_count}개의 TIL")
    print(f"   - {len(categories)}개의 카테고리")


if __name__ == "__main__":
    generate_readme()
