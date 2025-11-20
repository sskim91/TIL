# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ Important Rules

**DO NOT do the following unless explicitly requested by the user:**

1. **DO NOT run `python scripts/generate_readme.py`** - Do not update README.md
2. **DO NOT run git commands** (`git add`, `git commit`, `git push`) - Wait for user's explicit request
3. **DO NOT modify README.md** - It is auto-generated and should only be updated when the user asks

The user will decide when to update the README and commit changes.

## Repository Overview

This is a **TIL (Today I Learned)** repository containing technical documentation and learning notes, primarily focused on Python, Java, and security topics. All documentation is written in Korean with code examples and comparisons to Java for developers transitioning between languages.

## Repository Structure

```
TIL/
├── python/          # Python 언어 학습 노트
├── java/            # Java 언어 학습 노트
├── security/        # 보안 관련 학습 노트
├── ai/              # AI/ML 관련 학습 노트
├── scripts/         # 자동화 스크립트
│   └── generate_readme.py
└── .github/workflows/
    └── update-readme.yml
```

## Automated README Generation

**CRITICAL**: The `README.md` file is **automatically generated** and should **NEVER be manually edited**.

### How It Works

1. **Trigger**: Any markdown file changes pushed to `main` branch (except README.md itself)
2. **Process**: GitHub Actions runs `python scripts/generate_readme.py`
3. **Output**: Auto-commits updated README.md with category index

**Important**: README.md is auto-generated. Never edit it manually.

### README Generation Logic

The script (`scripts/generate_readme.py`):
- Scans all `*.md` files (excluding README.md and files in `scripts/`)
- Extracts first `# Title` from each markdown file
- Categorizes by directory name (e.g., `python/`, `java/`, `security/`)
- Generates statistics (total TIL count, category count)
- Sorts categories alphabetically, files by title within each category

### When Creating New TIL Documents

**CRITICAL FILE NAMING RULE**:
- **파일명은 반드시 첫 번째 제목과 동일하게 작성**
- 제목에서 특수문자 제거, 공백을 하이픈(-)으로 변환
- Example: `# Python f-string` → `Python-f-string.md`

**Required Format**:
```markdown
# Title Goes Here

> Optional subtitle or description

## Section 1
...
```

**Important**:
- First line MUST start with `# ` (single hash with space)
- **File name MUST match the first heading** (첫 번째 제목과 파일명 일치 필수)
- Title extracted from this first heading
- Category determined by folder location
- README auto-updates on push to main

**File Naming Examples**:
```
# Python Typing (타입 힌팅)
→ Python-Typing-타입-힌팅.md

# MITM (Man-In-The-Middle) 중간자 공격
→ MITM-Man-In-The-Middle-중간자-공격.md

# Python의 @abstractmethod와 추상 클래스
→ Python의-@abstractmethod와-추상-클래스.md
```

## Documentation Writing Standards

### **CRITICAL: Standard Document Structure**

**모든 TIL 문서는 다음 구조를 따라야 합니다:**

```markdown
# Python의 XXX
또는
# Python의 XXX 정리

[한 줄 설명: 무엇에 대한 문서인지]

## 결론부터 말하면

[핵심 내용을 2-3문장으로 요약]
[Before/After 코드 비교로 즉시 가치 제공]

## 1. 첫 번째 주제

### 세부 내용

## 2. 두 번째 주제

### 세부 내용

## Java와의 비교 (해당되는 경우)

## 실전/실무 활용
```

### **결론부터 말하면 섹션 (MANDATORY)**

**이 섹션은 필수이며, 문서의 가장 중요한 부분입니다!**

**목적**:
- 독자가 1분 안에 핵심을 파악할 수 있도록
- "왜 이게 중요한가?"를 즉시 보여줌
- Before/After 비교로 실용적 가치 제공

**Good Examples**:

```markdown
## 결론부터 말하면

`self`는 **인스턴스 자기 자신**을 가리키는 참조입니다. (Java의 `this`와 동일)
```

```markdown
## 결론부터 말하면

f-string은 **가장 빠르고 읽기 쉬운** 문자열 포매팅 방법입니다.

```python
# f-string (권장)
f"이름: {name}, 나이: {age}"

# 다른 방법들 (구식)
"이름: %s, 나이: %d" % (name, age)
"이름: {}, 나이: {}".format(name, age)
```

```markdown
## 결론부터 말하면

- `*args`: **위치 인자**(positional arguments)를 **튜플**로 받음
- `**kwargs`: **키워드 인자**(keyword arguments)를 **딕셔너리**로 받음
- 함수가 임의의 개수의 인자를 유연하게 받을 수 있게 해줌
```

### Structure Details
- **제목**: `# Python의 XXX` 또는 `# Python의 XXX 정리` 형태 권장 (간결하고 겸손한 표현)
- **한 줄 설명**: 문서가 다루는 내용을 간단히 설명
- **결론부터 말하면**: **필수 섹션** - 핵심 내용 + 코드 예시
- **Numbered sections**: `## 1.`, `## 2.` 등으로 순차적 구성
- **Java 비교**: Python 개념 설명 시 포함 (독자는 Java 개발자)
- **실전/실무 예제**: 실제 사용 사례 제공

### Style Guidelines
- Korean for explanations, English for technical terms
- Use emoji sparingly (mainly in README.md, not in TIL documents)
- Include "Java와의 비교" sections for Python concepts
- Provide "실전 예제" or "실무 활용 패턴" for complex topics
- Use tables for comparisons
- Use ✅/❌ for do's and don'ts

### Visualization Guidelines
- **복잡한 개념, 프로세스, 관계도는 mermaid 다이어그램으로 시각화**
- **다이어그램 타입 선택**:
  - `graph` / `flowchart`: 워크플로우, 프로세스, 의사결정 트리
  - `sequenceDiagram`: 시간 순서에 따른 상호작용, API 호출 흐름
  - `classDiagram`: 클래스 구조, 상속 관계, 아키텍처
  - `erDiagram`: 데이터베이스 스키마, 엔티티 관계
- **시각화가 유용한 경우**:
  - Before/After 비교 (기존 방식 vs 새로운 방식)
  - 단계별 프로세스 (1→2→3→4)
  - 시스템 아키텍처 (컴포넌트 간 관계)
  - 상태 전이 (State A → State B)
  - 복잡한 조건 분기
- **원칙**: 코드 블록으로 설명하는 것보다 다이어그램이 더 명확할 때만 사용
- **⚠️ CRITICAL - 가독성 있는 스타일 사용**:
  - mermaid 다이어그램에 스타일을 사용할 수 있지만, **글씨가 명확히 보여야 함**
  - **절대 금지**: 밝은 배경색만 지정 (자동으로 흰색 글씨가 되어 안 보임)
  - **권장 방법**:
    1. **테두리만 색상**: `style NodeName stroke:#2196F3,stroke-width:3px` (배경 투명, 글씨 검정)
    2. **어두운 배경 + 흰색 글씨**: `style NodeName fill:#1976D2,color:#fff`
    3. **밝은 배경 + 검은 글씨**: `style NodeName fill:#E3F2FD,color:#000`
  - ❌ 나쁜 예: `style CF fill:#e1f5ff` (밝은 배경에 자동 흰색 글씨 → 안 보임)
  - ❌ 나쁜 예: `style CF fill:#333,color:#666` (어두운 배경에 어두운 글씨 → 안 보임)
  - ✅ 좋은 예: `style CF stroke:#2196F3,stroke-width:3px` (테두리만 강조)
  - ✅ 좋은 예: `style CF fill:#1565C0,color:#fff` (어두운 파란색 배경 + 흰 글씨)

### Common Patterns Found in Existing Docs

**Type Comparison Tables**:
```markdown
| 특징 | Python | Java |
|------|--------|------|
| ... | ... | ... |
```

**Code Comparison Blocks**:
```markdown
# Python
def example():
    pass

# Java
public void example() {
    // ...
}
```

**Decision Guides**:
```markdown
# ✅ Use case A
# ❌ Avoid case B
```

### Source Attribution Guidelines
- **모든 문서는 출처가 있다면 반드시 명시**
- **출처 섹션 위치**: 문서 맨 마지막에 `## 출처` 또는 `## 참고 자료` 섹션 추가
- **링크 포함 필수**: 출처 URL을 클릭 가능한 형태로 제공
- **출처 형식**:
  ```markdown
  ## 출처

  - [공식 문서 제목](https://example.com/official-docs)
  - [블로그 제목](https://blog.example.com/article)
  - [Stack Overflow 질문](https://stackoverflow.com/questions/...)
  ```
- **공식 문서 우선**: 여러 출처가 있는 경우 공식 문서를 가장 위에 배치
- **작성 날짜 포함 권장**: `(2025-01-15 작성)` 형태로 날짜 명시

**Good Example**:
```markdown
## 출처

- [Spring Boot Reference - JSP Limitations](https://docs.spring.io/spring-boot/reference/web/servlet.html#web.servlet.embedded-container.jsp-limitations) - 공식 문서
- [Google Antigravity 소개 블로그](https://antigravity.google/blog/introducing-google-antigravity) - 공식 블로그 (2025년 발표)
- [Python 공식 문서 - Type Hints](https://docs.python.org/3/library/typing.html)
```

## Working with the Codebase

### Testing README Generation Locally

```bash
# Run the README generator
python scripts/generate_readme.py

# Check the output
git diff README.md
```

### Adding New Categories

Simply create a new directory with markdown files:
```bash
mkdir -p new-category
echo "# New Topic" > new-category/example.md
```

The next push will automatically create the category in README.

### Git Workflow

**IMPORTANT**: This repository uses automated commits via GitHub Actions.

After pushing TIL documents to main:
1. GitHub Actions triggers within seconds
2. Auto-commits "docs: auto-update README.md"
3. **Always `git pull` before making new commits** to avoid conflicts

Example workflow:
```bash
# After creating/editing TIL documents
git add python/new-topic.md
git commit -m "Add Python new topic guide"
git push origin main

# Wait 30-60 seconds for auto-commit

# Pull before next work
git pull origin main
```

## Document Categories and Themes

### Python Documents
Focus on transitioning from Java to Python:
- Type systems (typing, type hints)
- Object-oriented concepts (@dataclass, @abstractmethod, self)
- Python-specific features (f-strings, *args/**kwargs, with statements)
- Data structures and collection types
- Database connectivity patterns

### Java Documents
- New features by version (e.g., Java 25)
- Modern Java syntax and patterns

### Security Documents
- Security concepts (MITM, PII)
- Practical security implementation in Python

## Key Insights for Claude Code

### When Creating New Documents

1. **Follow existing patterns**: Reference `python/typing.md` or `python/collection-types-comparison.md` for structure
2. **Include comparisons**: Java developers are the primary audience
3. **Use Korean**: All explanations in Korean, code/technical terms in English
4. **Add practical examples**: "실전 예제" sections are expected
5. **Don't edit README.md**: It will be overwritten

### When Explaining Code

- Assume reader knows Java but learning Python
- Explain "why" Python does things differently
- Provide memory/performance comparisons when relevant
- Include common pitfalls and best practices

### Document Length

Existing documents range from 500-2000 lines. Comprehensive coverage is valued over brevity.

## GitHub Actions Workflow

The repository uses a single workflow: `.github/workflows/update-readme.yml`

**Triggers on**:
- Push to `main` branch
- Changes to any `*.md` file
- Excludes changes to `README.md` itself

**Permissions**: Requires `contents: write` to auto-commit

**Python Version**: 3.11 (ensure compatibility)
