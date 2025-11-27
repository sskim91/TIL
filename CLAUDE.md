# CLAUDE.md

이 저장소에서 Claude Code가 작업할 때 따라야 할 가이드라인입니다.

---

## 1. 절대 규칙

**사용자가 명시적으로 요청하지 않는 한 다음 행동을 하지 마라:**

| 금지 행동 | 이유 |
|-----------|------|
| `python scripts/generate_readme.py` 실행 | README.md는 GitHub Actions가 자동 생성 |
| `git add`, `git commit`, `git push` 실행 | 사용자가 직접 커밋 시점을 결정 |
| `README.md` 수정 | 자동 생성 파일이므로 수동 편집 금지 |

---

## 2. 저장소 개요

**TIL (Today I Learned)** 저장소. 주로 Python, Java, Spring, 보안 관련 기술 문서를 담고 있다.

**핵심 특징:**
- 모든 설명은 **한국어**, 코드/기술 용어는 **영어**
- 주요 독자는 **Java 개발자** → Python 개념 설명 시 Java 비교 포함
- README.md는 GitHub Actions가 자동 생성

```
TIL/
├── python/          # Python 학습 노트
├── java/            # Java 학습 노트
├── spring/          # Spring Framework 학습 노트
├── security/        # 보안 관련 학습 노트
├── ai/              # AI/ML 관련 학습 노트
├── computer-science/ # CS 기초 개념
├── nodejs/          # Node.js 학습 노트
├── scripts/         # 자동화 스크립트
└── .github/workflows/
```

---

## 3. 문서 작성 철학 (가장 중요)

### 3.1 "왜(Why)"를 반드시 설명하라

**이것이 TIL 문서의 핵심이다.** 기술 문서가 "무엇(What)"과 "어떻게(How)"만 설명하면 금방 잊혀진다.

| 질문 | 설명 |
|------|------|
| **왜 이 기술이 필요한가?** | 이 기술이 없으면 어떤 문제가 생기는지 |
| **왜 이렇게 설계되었는가?** | 다른 방법 대신 이 방법을 선택한 이유 |
| **왜 이런 결과가 나오는가?** | 내부 동작 원리 |

```markdown
❌ Bad: 정의만 나열
"DI는 의존성을 외부에서 주입하는 패턴입니다."
"Node.js는 싱글스레드 기반 이벤트 루프입니다."

✅ Good: "왜?"로 시작
"만약 프레임워크 없이 웹 서버를 만든다면? 우리가 직접 해야 할 일들이 산더미처럼 쌓인다..."
"만약 정말 싱글스레드라면, 파일 4개를 동시에 읽는 게 어떻게 가능할까?"
```

### 3.2 스토리텔링으로 풀어가라 (CRITICAL)

**기술 나열이 아니라 이야기를 들려줘라.** 독자가 자연스럽게 따라오게 만들어야 한다.

#### 스토리텔링 패턴

| 패턴 | 설명 | 예시 |
|------|------|------|
| **문제 → 의문 → 해답** | 문제 상황을 먼저 보여주고, 의문을 제기한 후, 해답 제시 | "싱글스레드인데 어떻게 동시에? → libuv가 있기 때문" |
| **만약 ~라면?** | 가정을 통해 문제를 체감하게 함 | "만약 Spring 없이 웹 서버를 만든다면?" |
| **이상한 점 발견** | 당연하게 알던 것에 의문 제기 | "근데 이상하다. 싱글스레드라면서 왜 4개가 동시에?" |
| **역사적 맥락** | 기술이 왜 등장했는지 배경 설명 | "2005년까지 개발자들은 공짜 점심을 즐겼다..." |

#### 연결어 사용

자연스러운 흐름을 위해 연결어를 적극 사용하라:

```markdown
✅ Good: 자연스러운 흐름
"하지만 여기서 문제가 생겼다."
"왜일까?"
"그렇다면 이건 어떻게 설명할 수 있을까?"
"이제 답이 보인다."
"그래서 libuv가 등장한 것이다."

❌ Bad: 단편적 나열
"libuv는 Thread Pool을 가진다."
"Thread Pool은 기본 4개이다."
"파일 I/O는 Thread Pool을 사용한다."
```

#### 문단 단위로 설명

한 줄씩 끊지 말고, 문단으로 풀어서 설명하라:

```markdown
❌ Bad: 한 줄씩 끊김
- libuv는 비동기 I/O 라이브러리다.
- Thread Pool을 가진다.
- 기본 4개다.

✅ Good: 문단으로 풀어서
libuv는 Node.js의 비동기 I/O를 담당하는 C 라이브러리다. Ryan Dahl이 Node.js를 만들 때
직접 개발했다. 왜 필요했을까? JavaScript 자체에는 파일을 읽거나 네트워크 통신을 하는
기능이 없다. 브라우저에서는 브라우저가 이런 기능을 제공하지만, 서버에서는 Node.js가
직접 제공해야 한다. 그 역할을 libuv가 한다.
```

#### Good Example: 스토리텔링 전체 흐름

```markdown
## 1. 왜 "싱글스레드"라는 오해가 생겼을까?

### 1.1 개발자가 보는 세계

Node.js로 코드를 작성할 때, 우리는 멀티스레드를 전혀 의식하지 않는다.
`new Thread()`도 없고, `synchronized`도 없다. 그냥 JavaScript를 쓸 뿐이다.

이렇게 개발자 입장에서는 모든 것이 단일 스레드로 보인다.
그래서 "Node.js는 싱글스레드"라고 생각하기 쉽다.

### 1.2 그런데 이상한 점이 있다

만약 정말 싱글스레드라면, 이 코드는 어떻게 동작해야 할까?

[코드 예시]

싱글스레드라면 순차적으로 읽어야 한다. 각 파일이 10ms 걸린다면 총 40ms가 걸려야 정상이다.

**하지만 실제 출력은?**

[출력 결과]

거의 동시에 완료된다! 어떻게 싱글스레드에서 이게 가능할까?

### 1.3 비밀은 libuv에 있다

[해답 설명]
```

---

## 4. 문서 구조

### 4.1 필수 구조

```markdown
# 제목 (예: Python의 XXX, Node.js가 싱글스레드라는 미신)

한 줄 설명 (호기심 유발)

## 결론부터 말하면

[핵심 요약 2-3문장]
[다이어그램 또는 Before/After 코드 비교]

## 1. 왜 이런 개념이 필요한가? / 왜 이런 오해가 생겼나?
### 문제 상황 또는 배경

## 2. 핵심 개념 설명
### 스토리텔링으로 풀어서

## 3. 실제 사례 / 코드 예시

## 4. 정리

---

## 출처

- [출처 제목](URL)
```

### 4.2 "결론부터 말하면" 섹션 (MANDATORY)

**이 섹션이 가장 중요하다.** 독자가 1분 안에 핵심을 파악할 수 있어야 한다.

```markdown
## 결론부터 말하면

**Node.js는 싱글스레드가 아니다.** "JavaScript 실행"만 단일 스레드일 뿐,
내부적으로는 멀티스레드를 적극 활용한다.

[mermaid 다이어그램]

| 구분 | 스레드 | 처리 방식 |
|------|--------|----------|
| JavaScript 실행 | **단일** | V8 엔진 |
| 파일 I/O | **멀티** | libuv Thread Pool |
```

### 4.3 파일명 규칙

**파일명은 반드시 첫 번째 제목과 동일하게 작성**

| 제목 | 파일명 |
|------|--------|
| `# Python의 f-string` | `Python의-f-string.md` |
| `# Node.js가 싱글스레드라는 미신` | `Node.js가-싱글스레드라는-미신.md` |

- 특수문자 제거, 공백을 하이픈(-)으로 변환
- 첫 줄은 반드시 `# `로 시작

---

## 5. 시각화 가이드

### 5.1 ASCII 박스 금지, 테이블 또는 mermaid 사용

**ASCII 박스(`┌──┐`, `───▶`, `│`, `├──┤`)를 사용하지 마라.**

한글과 영문의 폭이 달라서 정렬이 깨지고, 렌더링 환경마다 다르게 보인다.

```markdown
❌ Bad: ASCII 박스 (정렬 깨짐)
┌─────────────────────────────────────────┐
│  Upstream: 데이터를 보내는 방향          │  ← 한글/영문 폭 차이로 어긋남
└─────────────────────────────────────────┘

✅ Good: 테이블 (정렬 보장)
| 용어 | 의미 |
|------|------|
| Upstream | 데이터를 보내는 방향 |

✅ Good: mermaid (시각적으로 표현)
```

**변환 가이드:**

| 기존 ASCII | 변환 대상 |
|------------|----------|
| 박스형 정보 나열 | **테이블** |
| 흐름도, 화살표 | **mermaid flowchart** |
| 구조도, 계층 | **mermaid flowchart + subgraph** |
| 시퀀스, 순서 | **mermaid sequenceDiagram** |
| 단순 목록 | **불릿 포인트** 또는 **테이블** |

### 5.2 mermaid 다이어그램 타입

| 상황 | 다이어그램 타입 |
|------|-----------------|
| 워크플로우, 프로세스 | `graph` / `flowchart` |
| 시간 순서 상호작용 | `sequenceDiagram` |
| 클래스 구조, 아키텍처 | `classDiagram` |
| DB 스키마, 엔티티 관계 | `erDiagram` |
| 역사/타임라인 | `timeline` |
| 네트워크 패킷 구조 | `packet-beta` |

**시각화가 유용한 경우:**
- Before/After 비교
- 단계별 프로세스 (1→2→3→4)
- 시스템 아키텍처
- 상태 전이

### 5.3 mermaid 스타일 규칙

**글씨가 반드시 보여야 한다.**

```markdown
❌ Bad: style Node fill:#e1f5ff          (밝은 배경에 자동 흰색 글씨 → 안 보임)
❌ Bad: style Node fill:#333,color:#666  (어두운 배경에 어두운 글씨 → 안 보임)

✅ Good: style Node stroke:#2196F3,stroke-width:3px  (테두리만 강조)
✅ Good: style Node fill:#1565C0,color:#fff          (어두운 배경 + 흰 글씨)
✅ Good: style Node fill:#E3F2FD,color:#000          (밝은 배경 + 검은 글씨)
```

---

## 6. 스타일 가이드

### 6.1 언어

- **설명**: 한국어
- **코드/기술 용어**: 영어 (DI, IoC, Bean, Scope 등)

### 6.2 Bold 처리 규칙 (IMPORTANT)

**Bold는 핵심 강조에 사용한다. 단, 특수문자와 함께 쓸 때 주의하라.**

`**` 바로 앞/뒤에 괄호`)`, 따옴표`"` 등 특수문자가 붙으면 일부 마크다운 파서에서 bold가 적용되지 않는다.

```markdown
❌ Bad: 괄호가 bold 안에
**Concurrency(동시성)**와 **Parallelism(병렬성)**은

✅ Good: 괄호를 bold 밖으로
**Concurrency**(동시성)와 **Parallelism**(병렬성)은
```

```markdown
❌ Bad: 따옴표가 bold 안에
**"인용문"**이다

✅ Good: 따옴표를 bold 밖으로
"**인용문**"이다
```

```markdown
❌ Bad: 콜론 뒤 내용까지 bold
**Step 1: 설명 (보충)**

✅ Good: 핵심만 bold
**Step 1:** 설명 (보충)
```

### 6.3 비교 표현

**테이블:**
```markdown
| 특징 | Python | Java |
|------|--------|------|
| 타입 | 동적 | 정적 |
```

**코드 비교:**
```markdown
# Python
def example():
    pass

# Java
public void example() { }
```

**Do's and Don'ts:**
```markdown
✅ 이렇게 하라
❌ 이렇게 하지 마라
```

### 6.4 수식 표현

**수학 수식은 LaTeX 문법으로 작성한다.**

```markdown
❌ Bad: 일반 텍스트로 수식 작성
S = 1 / ((1 - P) + P/N)

✅ Good: LaTeX 인라인 수식
$S = \frac{1}{(1-P) + \frac{P}{N}}$

✅ Good: LaTeX 블록 수식
$$
S = \frac{1}{(1-P) + \frac{P}{N}}
$$
```

**LaTeX 사용 시점:**
- 분수, 제곱, 루트 등 복잡한 수식
- 그리스 문자 ($\alpha$, $\beta$, $\infty$ 등)
- 수학적 정리나 공식

### 6.5 출처 표기

문서 맨 마지막에 `## 출처` 섹션 추가. 공식 문서를 가장 위에 배치.

```markdown
## 출처

- [Spring Framework Documentation](https://docs.spring.io/...) - 공식 문서
- [블로그 제목](https://blog.example.com/article)
```

---

## 7. 카테고리별 특성

### Python
Java 개발자가 Python으로 전환하는 관점에서 작성:
- Type hints, typing 모듈
- OOP 개념 (@dataclass, @abstractmethod, self)
- Python 특화 기능 (f-string, *args/**kwargs, with)

### Java
- 버전별 새 기능 (Java 21, 25 등)
- 모던 Java 패턴

### Spring
- Spring Framework 핵심 개념 (IoC, DI, AOP)
- Spring Boot 설정과 패턴
- 실무 활용 예제

### Node.js
- 비동기 I/O, Event Loop
- libuv, Thread Pool
- Worker Threads, Cluster

### Computer Science
- 동시성, 병렬성
- 동기/비동기, 블로킹/논블로킹
- 알고리즘, 자료구조

### Security
- 보안 개념 (MITM, PII 등)
- 실무 보안 구현

---

## 8. 자동화

### README 자동 생성

```mermaid
graph LR
    A[TIL 문서 push] --> B[GitHub Actions 트리거]
    B --> C[generate_readme.py 실행]
    C --> D[README.md 자동 커밋]

    style B fill:#1565C0,color:#fff
```

- **트리거**: `main` 브랜치에 `*.md` 파일 변경 시
- **동작**: 모든 TIL 문서 스캔 → 카테고리별 인덱스 생성
- **주의**: push 후 30-60초 대기, 다음 작업 전 `git pull` 필수

### 새 카테고리 추가

폴더만 만들면 자동으로 카테고리가 생성된다:

```bash
mkdir -p new-category
# 문서 작성 후 push하면 README에 자동 반영
```

---

## 9. 요약: 좋은 TIL 문서 체크리스트

### 필수 (MUST)

- [ ] **"왜"를 설명했는가?** (가장 중요!)
- [ ] **스토리텔링으로 풀어갔는가?** (문제→의문→해답)
- [ ] "결론부터 말하면" 섹션이 있는가?
- [ ] 파일명이 제목과 일치하는가?

### 권장 (SHOULD)

- [ ] Before/After 비교가 있는가?
- [ ] 복잡한 개념은 mermaid로 시각화했는가?
- [ ] ASCII 박스 대신 테이블/mermaid를 사용했는가?
- [ ] 출처를 명시했는가?

### 스타일 (CHECK)

- [ ] Bold 처리 시 괄호/따옴표가 밖에 있는가?
- [ ] 수식은 LaTeX로 작성했는가?
- [ ] 문단 단위로 설명했는가? (한 줄씩 끊지 않음)
