# LangGraph Durable Execution - 실패해도 이어서 실행하기

LLM Agent가 10단계 작업 중 7단계에서 API 에러로 죽었다. 처음부터 다시 실행해야 할까?

## 결론부터 말하면

**Durable Execution은 워크플로우가 실패하거나 중단되어도 마지막 성공 지점에서 재개할 수 있는 기능** 이다. LangGraph는 각 노드 실행 후 **Checkpoint** 를 저장하고, **pending writes** 를 추적하여 정확히 중단된 지점에서 다시 시작할 수 있게 한다.

```mermaid
flowchart LR
    subgraph Before["❌ Durable Execution 없음"]
        A1[Step 1] --> A2[Step 2] --> A3[Step 3] --> A4["Step 4<br>💥 실패"]
        A4 -.->|처음부터 다시| A1
    end

    subgraph After["✅ Durable Execution 있음"]
        B1[Step 1] --> B2[Step 2] --> B3[Step 3] --> B4["Step 4<br>💥 실패"]
        B4 -.->|Step 4부터 재개| B4_2["Step 4<br>✅ 성공"]
        B4_2 --> B5[Step 5]
    end

    style A4 fill:#C62828,color:#fff
    style B4 fill:#C62828,color:#fff
    style B4_2 fill:#2E7D32,color:#fff
```

| 구분 | 일반 실행 | Durable Execution |
|------|----------|-------------------|
| 실패 시 | 처음부터 다시 | 실패 지점에서 재개 |
| 서버 재시작 | 모든 진행 소실 | 저장된 상태에서 재개 |
| 장시간 작업 | 불안정 | 안정적 |
| 비용 | 중복 실행으로 증가 | 최소화 |
| 멱등성 필요 | 모든 노드에 필요 | 실패한 노드만 재실행 |

## 1. 왜 Durable Execution이 필요한가?

### 1.1 실제 프로덕션에서 일어나는 일들

LLM 기반 Agent를 프로덕션에 배포하면 다양한 문제가 발생한다:

```mermaid
flowchart TD
    subgraph Problems["프로덕션 환경의 현실"]
        P1["API Rate Limit<br>(429 Too Many Requests)"]
        P2["네트워크 타임아웃<br>(Connection Timeout)"]
        P3["서버 재배포<br>(Rolling Update)"]
        P4["메모리 부족<br>(OOM Kill)"]
        P5["외부 서비스 장애<br>(Third-party Outage)"]
    end

    P1 --> FAIL["워크플로우 중단"]
    P2 --> FAIL
    P3 --> FAIL
    P4 --> FAIL
    P5 --> FAIL

    style FAIL fill:#C62828,color:#fff
```

예를 들어, 다음과 같은 복잡한 Agent를 생각해보자:

```python
# 문서 분석 Agent - 총 5단계
# 1. 문서 로드 (10초)
# 2. 청크 분할 (5초)
# 3. 임베딩 생성 (30초) - OpenAI API 호출
# 4. 벡터 DB 저장 (10초)
# 5. 요약 생성 (20초) - OpenAI API 호출

# 4단계에서 네트워크 에러 발생!
# 이미 소비한 시간: 45초
# 이미 소비한 OpenAI API 비용: $0.50

# Durable Execution 없이는?
# → 처음부터 다시 실행해야 함
# → 추가 45초 + $0.50 낭비
```

### 1.2 Checkpoint만으로는 부족하다

[Persistence 문서](./LangGraph-Persistence-상태를-영속화하는-방법.md)에서 Checkpoint를 배웠다. 하지만 Checkpoint만으로는 완전한 Durable Execution이 어렵다.

**문제 상황:**

```python
def process_data(state):
    # 1. 외부 API 호출 (성공)
    result1 = expensive_api_call_1()

    # 2. 데이터 변환 (성공)
    transformed = transform(result1)

    # 3. 다른 API 호출 (💥 실패!)
    result2 = expensive_api_call_2(transformed)  # 여기서 에러!

    return {"result": result2}
```

Checkpoint는 **노드 단위** 로 저장된다. 노드 내부에서 실패하면?

- `expensive_api_call_1()`은 이미 실행됨 (비용 발생)
- 노드가 완료되지 않았으므로 Checkpoint 미생성
- 재실행 시 `expensive_api_call_1()`부터 다시 실행 (비용 중복!)

### 1.3 LangGraph의 해결책: Pending Writes

LangGraph는 **pending writes** 메커니즘으로 이 문제를 해결한다.

```mermaid
flowchart TD
    subgraph Node["노드 실행 중"]
        T1["Task 1 실행"] -->|결과 저장| PW1["Pending Write 1"]
        T1 --> T2["Task 2 실행"]
        T2 -->|결과 저장| PW2["Pending Write 2"]
        T2 --> T3["Task 3 실행"]
        T3 -->|💥 실패| ERR["Error"]
    end

    subgraph Resume["재개 시"]
        PW1 -->|이미 저장됨| SKIP1["Task 1 스킵"]
        PW2 -->|이미 저장됨| SKIP2["Task 2 스킵"]
        T3_2["Task 3만 재실행"]
    end

    style ERR fill:#C62828,color:#fff
    style T3_2 fill:#2E7D32,color:#fff
```

| 개념 | 설명 | 저장 시점 |
|------|------|----------|
| **Checkpoint** | 노드 실행 완료 후 전체 상태 | 노드 종료 시 |
| **Pending Writes** | 노드 실행 중 부분 결과 | Task 완료 시 |

## 2. Durable Execution 구현하기

### 2.1 기본 구조: @task 데코레이터

LangGraph는 `@task` 데코레이터로 개별 작업을 정의한다. 각 Task의 결과는 자동으로 저장된다.

```python
from langgraph.func import entrypoint, task
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()

@task()
def fetch_data():
    """외부 API에서 데이터 가져오기 - 비용이 큰 작업"""
    print("Fetching data...")  # 재개 시 출력되지 않음!
    return expensive_api_call()

@task()
def process_data(data):
    """데이터 처리"""
    print("Processing data...")
    return transform(data)

@task()
def save_result(result):
    """결과 저장 - 실패할 수 있는 작업"""
    print("Saving result...")
    return database_save(result)  # 네트워크 에러 가능

@entrypoint(checkpointer=checkpointer)
def workflow(inputs):
    """메인 워크플로우"""
    data = fetch_data().result()      # Task 1
    processed = process_data(data).result()  # Task 2
    final = save_result(processed).result()  # Task 3 (실패 가능)
    return final
```

### 2.2 실패 후 재개 예제

```python
import time
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task

# 실패 시뮬레이션을 위한 변수
attempts = 0

@task()
def slow_task():
    """시간이 오래 걸리는 작업"""
    print("Running slow task...")
    time.sleep(2)  # 2초 소요
    return "Slow task completed"

@task()
def unreliable_task():
    """불안정한 작업 - 첫 번째 시도에서 실패"""
    global attempts
    attempts += 1
    print(f"Attempt {attempts}...")

    if attempts < 2:
        raise ConnectionError("Network error!")  # 첫 시도 실패

    return "Success!"

checkpointer = InMemorySaver()

@entrypoint(checkpointer=checkpointer)
def main(inputs):
    result1 = slow_task().result()       # 2초 소요
    result2 = unreliable_task().result() # 첫 시도에서 실패
    return f"{result1} + {result2}"

config = {"configurable": {"thread_id": "workflow-1"}}

# 첫 번째 실행 - 실패
print("=== First attempt ===")
try:
    main.invoke({"input": "start"}, config=config)
except ConnectionError as e:
    print(f"Failed: {e}")

# 두 번째 실행 - 재개
print("\n=== Resume ===")
result = main.invoke(None, config=config)  # None으로 재개!
print(f"Result: {result}")
```

**출력:**

```
=== First attempt ===
Running slow task...        # 2초 소요
Attempt 1...
Failed: Network error!

=== Resume ===
Attempt 2...                # slow_task는 스킵됨!
Result: Slow task completed + Success!
```

**핵심 포인트:**
- 재개 시 `slow_task()`는 **다시 실행되지 않음** (결과가 이미 저장됨)
- `unreliable_task()`만 다시 실행됨
- `invoke(None, config)`로 재개 (새 입력 없이 이전 상태에서 계속)

### 2.3 RetryPolicy로 자동 재시도

매번 수동으로 재개하는 대신, **RetryPolicy** 로 자동 재시도를 설정할 수 있다.

```python
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from typing_extensions import TypedDict
import random

class State(TypedDict):
    attempts: int
    result: str

def unreliable_api_call(state: State):
    """70% 확률로 실패하는 API"""
    if random.random() < 0.7:
        raise ConnectionError("API temporarily unavailable")
    return {
        "result": "Success!",
        "attempts": state.get("attempts", 0) + 1
    }

def process_result(state: State):
    return {"result": state["result"] + " - Processed"}

# 그래프 빌드
builder = StateGraph(State)

# RetryPolicy 적용
builder.add_node(
    "api_call",
    unreliable_api_call,
    retry=RetryPolicy(
        max_attempts=5,           # 최대 5회 시도
        retry_on=ConnectionError, # 이 에러에서만 재시도
        backoff_factor=2.0,       # 지수 백오프 (1초, 2초, 4초...)
        initial_interval=1.0,     # 첫 재시도 대기 시간
        jitter=True               # 무작위 지연 추가
    )
)
builder.add_node("process", process_result)

builder.add_edge(START, "api_call")
builder.add_edge("api_call", "process")
builder.add_edge("process", END)

graph = builder.compile()

# 실행
try:
    result = graph.invoke({"attempts": 0, "result": ""})
    print(f"Success: {result}")
except Exception as e:
    print(f"Failed after all retries: {e}")
```

### 2.4 RetryPolicy 옵션

```python
from langgraph.types import RetryPolicy

RetryPolicy(
    # 재시도 횟수
    max_attempts=3,           # 최대 시도 횟수 (기본: 3)

    # 재시도 대상 에러
    retry_on=(                # 재시도할 예외 타입들
        ConnectionError,
        TimeoutError,
        RateLimitError
    ),

    # 백오프 설정
    initial_interval=1.0,     # 첫 재시도 대기 (초)
    backoff_factor=2.0,       # 지수 증가 배수 (1초 → 2초 → 4초)
    max_interval=60.0,        # 최대 대기 시간 (초)

    # 지터 (Jitter)
    jitter=True               # 무작위 지연 추가 (thundering herd 방지)
)
```

```mermaid
flowchart LR
    subgraph Backoff["지수 백오프 + Jitter"]
        R1["시도 1<br>실패"] -->|1초 + jitter| R2["시도 2<br>실패"]
        R2 -->|2초 + jitter| R3["시도 3<br>실패"]
        R3 -->|4초 + jitter| R4["시도 4<br>실패"]
        R4 -->|8초 + jitter| R5["시도 5<br>성공!"]
    end

    style R1 fill:#C62828,color:#fff
    style R2 fill:#C62828,color:#fff
    style R3 fill:#C62828,color:#fff
    style R4 fill:#C62828,color:#fff
    style R5 fill:#2E7D32,color:#fff
```

## 3. 실전 예제: 문서 처리 파이프라인

실제 프로덕션에서 사용할 수 있는 Durable한 문서 처리 파이프라인을 구현해보자.

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.types import RetryPolicy
import httpx


class DocumentState(TypedDict):
    document_id: str
    content: str
    chunks: list[str]
    embeddings: list[list[float]]
    summary: str
    status: str


# === 노드 정의 ===

def load_document(state: DocumentState) -> dict:
    """Step 1: 문서 로드"""
    print(f"Loading document: {state['document_id']}")
    content = fetch_document_from_storage(state["document_id"])
    return {"content": content, "status": "loaded"}


def chunk_document(state: DocumentState) -> dict:
    """Step 2: 청크 분할"""
    print("Chunking document...")
    chunks = split_into_chunks(state["content"], chunk_size=1000)
    return {"chunks": chunks, "status": "chunked"}


def generate_embeddings(state: DocumentState) -> dict:
    """Step 3: 임베딩 생성 (비용이 큰 작업)"""
    print(f"Generating embeddings for {len(state['chunks'])} chunks...")
    embeddings = []
    for chunk in state["chunks"]:
        # OpenAI API 호출 - 비용 발생!
        embedding = openai_embed(chunk)
        embeddings.append(embedding)
    return {"embeddings": embeddings, "status": "embedded"}


def store_vectors(state: DocumentState) -> dict:
    """Step 4: 벡터 DB 저장 (네트워크 에러 가능)"""
    print("Storing vectors...")
    vector_db.upsert(
        ids=[f"{state['document_id']}-{i}" for i in range(len(state["chunks"]))],
        embeddings=state["embeddings"],
        documents=state["chunks"]
    )
    return {"status": "stored"}


def generate_summary(state: DocumentState) -> dict:
    """Step 5: 요약 생성"""
    print("Generating summary...")
    summary = llm.summarize(state["content"])
    return {"summary": summary, "status": "completed"}


# === 그래프 빌드 ===

builder = StateGraph(DocumentState)

# 노드 추가 (RetryPolicy 적용)
builder.add_node("load", load_document)
builder.add_node("chunk", chunk_document)
builder.add_node(
    "embed",
    generate_embeddings,
    retry=RetryPolicy(max_attempts=3, retry_on=(httpx.HTTPStatusError,))
)
builder.add_node(
    "store",
    store_vectors,
    retry=RetryPolicy(max_attempts=5, backoff_factor=2.0)
)
builder.add_node(
    "summarize",
    generate_summary,
    retry=RetryPolicy(max_attempts=3)
)

# 엣지 정의
builder.add_edge(START, "load")
builder.add_edge("load", "chunk")
builder.add_edge("chunk", "embed")
builder.add_edge("embed", "store")
builder.add_edge("store", "summarize")
builder.add_edge("summarize", END)

# Checkpointer로 컴파일
DB_URI = "postgres://user:pass@localhost:5432/mydb"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
    graph = builder.compile(checkpointer=checkpointer)

    # === 실행 ===
    config = {"configurable": {"thread_id": f"doc-{document_id}"}}

    try:
        result = graph.invoke(
            {"document_id": "doc-123", "content": "", "chunks": [],
             "embeddings": [], "summary": "", "status": "pending"},
            config=config
        )
        print(f"Completed: {result['status']}")

    except Exception as e:
        print(f"Failed at: {e}")
        print("Run again with same config to resume...")

        # 나중에 재개
        result = graph.invoke(None, config=config)
```

## 4. Durable Execution vs 일반 재시도

| 측면 | 일반 재시도 (try/except) | Durable Execution |
|------|------------------------|-------------------|
| 범위 | 함수 내부 | 전체 워크플로우 |
| 상태 보존 | 없음 | Checkpoint에 저장 |
| 서버 재시작 | 복구 불가 | 복구 가능 |
| 부분 실패 | 처음부터 재실행 | 실패 지점에서 재개 |
| 비용 | 중복 발생 | 최소화 |

```python
# ❌ 일반 재시도 - 부분 실패 시 전체 재실행
def process_with_retry():
    for attempt in range(3):
        try:
            step1_result = expensive_step1()  # 매번 재실행!
            step2_result = expensive_step2()  # 매번 재실행!
            step3_result = step3_that_fails() # 여기서 실패
            return step3_result
        except Exception:
            continue

# ✅ Durable Execution - 실패 지점에서만 재실행
@entrypoint(checkpointer=checkpointer)
def process_durable(inputs):
    step1_result = step1_task().result()  # 결과 저장됨
    step2_result = step2_task().result()  # 결과 저장됨
    step3_result = step3_task().result()  # 실패해도 여기서만 재실행
    return step3_result
```

## 5. 주의사항

### 5.1 멱등성(Idempotency) 고려

Durable Execution은 실패한 Task만 재실행하지만, **외부 부작용** 이 있는 경우 주의해야 한다.

```python
# ⚠️ 주의: 멱등하지 않은 작업
@task()
def send_email(to: str, content: str):
    """이메일 발송 - 재실행 시 중복 발송 위험!"""
    email_service.send(to, content)
    return "sent"

# ✅ 개선: 멱등성 보장
@task()
def send_email_idempotent(to: str, content: str, idempotency_key: str):
    """멱등한 이메일 발송"""
    if email_service.was_sent(idempotency_key):
        return "already_sent"
    email_service.send(to, content, idempotency_key=idempotency_key)
    return "sent"
```

### 5.2 Task 결과 크기 제한

Task 결과는 Checkpoint에 저장되므로, **큰 데이터** 를 반환하면 저장 비용이 증가한다.

```python
# ❌ Bad: 큰 데이터 반환
@task()
def process_large_file():
    data = read_huge_file()  # 1GB 파일
    return data  # 전체 데이터가 Checkpoint에 저장됨!

# ✅ Good: 참조만 반환
@task()
def process_large_file():
    data = read_huge_file()
    file_path = save_to_temp_storage(data)
    return file_path  # 경로만 저장
```

## 6. 정리

**Durable Execution** 은 LangGraph의 핵심 기능으로, 장시간 실행되는 워크플로우를 안정적으로 만든다.

**핵심 개념:**

| 개념 | 설명 |
|------|------|
| **Checkpoint** | 노드 완료 후 전체 상태 저장 |
| **Pending Writes** | 노드 실행 중 Task 결과 저장 |
| **RetryPolicy** | 노드별 자동 재시도 정책 |
| **Resume** | `invoke(None, config)`로 중단점에서 재개 |

**언제 사용하나:**

| 상황 | Durable Execution 필요성 |
|------|-------------------------|
| 장시간 실행 (분~시간) | **필수** |
| 비용이 큰 API 호출 | **필수** |
| 불안정한 외부 서비스 | **권장** |
| 프로덕션 배포 | **권장** |
| 빠른 프로토타이핑 | 선택 |

**RetryPolicy vs Checkpoint:**

- **RetryPolicy**: 일시적 실패에 대한 **자동 재시도**
- **Checkpoint**: 재시작/장기 중단 후 **수동 재개**

---

## 출처

- [LangGraph Documentation - Durable Execution](https://langchain-ai.github.io/langgraph/concepts/durable_execution/) - 공식 문서
- [LangGraph GitHub - README](https://github.com/langchain-ai/langgraph) - Core Benefits
- [LangGraph Functional API](https://langchain-ai.github.io/langgraph/reference/functions/)
