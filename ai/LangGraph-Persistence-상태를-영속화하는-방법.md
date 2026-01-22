# LangGraph Persistence - 상태를 영속화하는 방법

LangGraph로 챗봇을 만들었는데, 서버가 재시작되면 모든 대화 내역이 사라진다면?

## 결론부터 말하면

**Persistence는 그래프의 상태를 저장소에 영속화하는 기능** 이다. 각 노드 실행 후 **Checkpoint** 를 생성하여 저장하고, 필요할 때 복구할 수 있다. 이를 통해 **대화 컨텍스트 유지**, **중단/재개**, **Time Travel** 이 가능해진다.

```mermaid
flowchart LR
    subgraph Execution["그래프 실행"]
        N1[노드 1] --> N2[노드 2] --> N3[노드 3]
    end

    subgraph Storage["Checkpointer"]
        C1[Checkpoint 1]
        C2[Checkpoint 2]
        C3[Checkpoint 3]
    end

    N1 -.->|저장| C1
    N2 -.->|저장| C2
    N3 -.->|저장| C3

    C2 -.->|복구| N2

    style N1 fill:#1565C0,color:#fff
    style N2 fill:#1565C0,color:#fff
    style N3 fill:#1565C0,color:#fff
```

| 구분 | Persistence 없음 | Persistence 있음 |
|------|------------------|------------------|
| 서버 재시작 | 상태 소실 | 상태 복구 가능 |
| 멀티 턴 대화 | 매번 전체 히스토리 전달 필요 | Thread ID로 자동 로드 |
| 중단/재개 | 불가능 | Checkpoint에서 재개 |
| Time Travel | 불가능 | 과거 상태로 되돌리기 가능 |
| Human-in-the-loop | 별도 구현 필요 | `interrupt()` + 자동 저장 |

## 1. 왜 Persistence가 필요한가?

### 1.1 메모리만으로는 부족하다

간단한 챗봇을 만들어보자. 상태를 메모리에만 저장하면 어떻게 될까?

```python
# 메모리 기반 (Persistence 없음)
from langgraph.graph import StateGraph, START, END

class ChatState(TypedDict):
    messages: list

def respond(state: ChatState) -> dict:
    # LLM 호출
    response = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}

builder = StateGraph(ChatState)
builder.add_node("respond", respond)
builder.add_edge(START, "respond")
builder.add_edge("respond", END)

graph = builder.compile()  # checkpointer 없음!

# 첫 번째 대화
result = graph.invoke({"messages": ["안녕하세요"]})
# 결과: {"messages": ["안녕하세요", "안녕하세요! 무엇을 도와드릴까요?"]}

# ❌ 서버 재시작 후...
# 모든 상태가 사라짐! 이전 대화를 기억하지 못함
```

**문제점:**

- **서버 재시작 시 상태 소실**: 프로세스가 종료되면 메모리의 모든 데이터가 사라진다.
- **멀티 사용자 지원 어려움**: 각 사용자의 대화를 어떻게 분리할 것인가?
- **중단/재개 불가능**: Human-in-the-loop 같은 패턴을 구현하기 어렵다.

### 1.2 Checkpointer가 해결한다

LangGraph의 **Checkpointer** 는 각 노드 실행 후 상태를 자동으로 저장한다.

```python
from langgraph.checkpoint.memory import InMemorySaver

# Checkpointer 추가
memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)

# Thread ID로 대화 분리
config = {"configurable": {"thread_id": "user_123"}}

# 첫 번째 대화
result1 = graph.invoke(
    {"messages": ["안녕하세요"]},
    config=config
)

# 두 번째 대화 - 이전 컨텍스트 자동 로드!
result2 = graph.invoke(
    {"messages": ["이전에 뭐라고 했었죠?"]},
    config=config  # 같은 thread_id
)
# ✅ 이전 대화 내역을 기억하고 있음!
```

## 2. Checkpoint의 구조

Checkpoint는 단순한 상태 스냅샷이 아니다. **실행 히스토리와 메타데이터** 를 함께 저장한다.

### 2.1 Checkpoint 구조 분석

```python
checkpoint = {
    # 버전 정보
    "v": 4,

    # 타임스탬프
    "ts": "2024-07-31T20:14:19.804150+00:00",

    # 고유 식별자
    "id": "1ef4f797-8335-6428-8001-8a1503f9b875",

    # 실제 상태 값들
    "channel_values": {
        "messages": [...],      # 메시지 히스토리
        "current_step": "respond",  # 현재 단계
        "retry_count": 0        # 재시도 횟수
    },

    # 각 채널의 버전
    "channel_versions": {
        "__start__": 2,
        "messages": 3,
        "current_step": 3
    },

    # 각 노드가 본 버전
    "versions_seen": {
        "__input__": {},
        "__start__": {"__start__": 1},
        "respond": {"messages": 2}
    }
}
```

```mermaid
flowchart TB
    subgraph Checkpoint["Checkpoint 구조"]
        direction TB
        META["메타데이터<br>v, ts, id"]
        CV["channel_values<br>(실제 상태)"]
        CVER["channel_versions<br>(채널별 버전)"]
        VSEEN["versions_seen<br>(노드별 관찰 버전)"]
    end

    META --> CV
    CV --> CVER
    CVER --> VSEEN

    style META fill:#1565C0,color:#fff
    style CV fill:#2E7D32,color:#fff
```

| 필드 | 설명 | 용도 |
|------|------|------|
| `v` | Checkpoint 스키마 버전 | 호환성 관리 |
| `ts` | 생성 타임스탬프 | 정렬, 디버깅 |
| `id` | 고유 식별자 (UUID) | 특정 Checkpoint 참조 |
| `channel_values` | 실제 상태 값 | 상태 복구 |
| `channel_versions` | 채널별 버전 번호 | 변경 추적 |
| `versions_seen` | 노드가 관찰한 버전 | 동시성 제어 |

### 2.2 왜 이렇게 복잡한 구조인가?

단순히 `{"messages": [...]}` 만 저장하면 안 될까? **동시성과 정확한 재실행** 을 위해서다.

```mermaid
flowchart LR
    subgraph Problem["문제: 동시 실행"]
        A[노드 A] -->|messages 수정| S1[State]
        B[노드 B] -->|messages 수정| S1
    end

    subgraph Solution["해결: 버전 추적"]
        A2[노드 A] -->|v2 기반 수정| S2["State v3"]
        B2[노드 B] -->|v2 기반 수정| S2
    end

    style A fill:#C62828,color:#fff
    style B fill:#C62828,color:#fff
    style A2 fill:#2E7D32,color:#fff
    style B2 fill:#2E7D32,color:#fff
```

`channel_versions`와 `versions_seen`은 **각 노드가 어떤 버전의 상태를 보고 작업했는지** 를 추적한다. 이를 통해:

- 병렬 노드 실행 시 충돌 감지
- 정확한 상태 복구
- Time Travel 시 올바른 시점으로 되돌리기

## 3. Thread와 Checkpoint 관계

### 3.1 Thread란?

**Thread** 는 일련의 Checkpoint를 묶는 논리적 단위다. 하나의 대화 세션, 하나의 작업 흐름을 나타낸다.

```mermaid
flowchart TB
    subgraph Thread1["Thread: user_123"]
        C1_1["Checkpoint 1<br>안녕하세요"]
        C1_2["Checkpoint 2<br>날씨 알려줘"]
        C1_3["Checkpoint 3<br>고마워"]
        C1_1 --> C1_2 --> C1_3
    end

    subgraph Thread2["Thread: user_456"]
        C2_1["Checkpoint 1<br>코드 리뷰해줘"]
        C2_2["Checkpoint 2<br>더 설명해줘"]
        C2_1 --> C2_2
    end

    style C1_3 fill:#2E7D32,color:#fff
    style C2_2 fill:#2E7D32,color:#fff
```

### 3.2 Config 구조

```python
# 기본: Thread ID만 지정
config = {
    "configurable": {
        "thread_id": "user_123"
    }
}

# 고급: 특정 Checkpoint에서 시작
config = {
    "configurable": {
        "thread_id": "user_123",
        "checkpoint_id": "1ef4f797-8335-6428-8001-8a1503f9b875"
    }
}

# Subgraph용: Namespace 지정
config = {
    "configurable": {
        "thread_id": "user_123",
        "checkpoint_ns": "inner_graph"
    }
}
```

| 설정 | 필수 여부 | 설명 |
|------|----------|------|
| `thread_id` | **필수** | 대화/작업 세션 식별자 |
| `checkpoint_id` | 선택 | 특정 Checkpoint에서 재개 |
| `checkpoint_ns` | 선택 | Subgraph 네임스페이스 |

## 4. Checkpointer 종류와 선택

### 4.1 제공되는 Checkpointer

```mermaid
flowchart TB
    BASE["BaseCheckpointSaver<br>(인터페이스)"]

    MEM["InMemorySaver<br>개발/테스트용"]
    SQL["SqliteSaver<br>단일 서버"]
    PG["PostgresSaver<br>프로덕션"]

    BASE --> MEM
    BASE --> SQL
    BASE --> PG

    style BASE fill:#E65100,color:#fff
    style MEM fill:#1565C0,color:#fff
    style SQL fill:#1565C0,color:#fff
    style PG fill:#2E7D32,color:#fff
```

| Checkpointer | 패키지 | 용도 | 특징 |
|--------------|--------|------|------|
| `InMemorySaver` | `langgraph` | 개발/테스트 | 재시작 시 소실 |
| `SqliteSaver` | `langgraph-checkpoint-sqlite` | 단일 서버 | 파일 기반, 간편 |
| `AsyncSqliteSaver` | `langgraph-checkpoint-sqlite` | 단일 서버 (비동기) | 논블로킹 I/O |
| `PostgresSaver` | `langgraph-checkpoint-postgres` | 프로덕션 | 다중 서버, 확장성 |
| `AsyncPostgresSaver` | `langgraph-checkpoint-postgres` | 프로덕션 (비동기) | 고성능 |

### 4.2 각 Checkpointer 사용법

**InMemorySaver (개발용)**

```python
from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)
```

**SqliteSaver (단일 서버)**

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 파일 기반
with SqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    result = graph.invoke(state, config)

# 메모리 기반 (테스트용)
with SqliteSaver.from_conn_string(":memory:") as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
```

**PostgresSaver (프로덕션)**

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgres://user:pass@localhost:5432/mydb"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # 최초 실행 시 테이블 생성
    checkpointer.setup()

    graph = builder.compile(checkpointer=checkpointer)
    result = graph.invoke(state, config)
```

**AsyncPostgresSaver (비동기 프로덕션)**

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
    await checkpointer.setup()

    graph = builder.compile(checkpointer=checkpointer)
    result = await graph.ainvoke(state, config)
```

### 4.3 선택 가이드

```mermaid
flowchart TD
    START((시작)) --> Q1{프로덕션?}

    Q1 -->|No| Q2{파일 저장 필요?}
    Q2 -->|No| MEM["InMemorySaver"]
    Q2 -->|Yes| SQL["SqliteSaver"]

    Q1 -->|Yes| Q3{다중 서버?}
    Q3 -->|No| SQL2["SqliteSaver"]
    Q3 -->|Yes| PG["PostgresSaver"]

    style START fill:#1565C0,color:#fff
    style MEM fill:#E65100,color:#fff
    style SQL fill:#E65100,color:#fff
    style SQL2 fill:#E65100,color:#fff
    style PG fill:#2E7D32,color:#fff
```

## 5. Checkpointer 인터페이스

커스텀 Checkpointer를 만들려면 `BaseCheckpointSaver`를 상속하고 다음 메서드를 구현해야 한다.

### 5.1 필수 메서드

```python
from langgraph.checkpoint.base import BaseCheckpointSaver

class MyCheckpointer(BaseCheckpointSaver):

    def put(self, config, checkpoint, metadata, new_versions):
        """Checkpoint 저장"""
        pass

    def put_writes(self, config, writes, task_id):
        """중간 쓰기 저장 (pending writes)"""
        pass

    def get_tuple(self, config):
        """Checkpoint 조회"""
        pass

    def list(self, config, *, filter=None, before=None, limit=None):
        """Checkpoint 목록 조회"""
        pass

    def delete_thread(self, thread_id):
        """Thread의 모든 Checkpoint 삭제"""
        pass
```

### 5.2 비동기 메서드

비동기 실행(`ainvoke`, `astream`)을 지원하려면 `a` prefix 메서드도 구현해야 한다.

```python
async def aput(self, config, checkpoint, metadata, new_versions):
    """비동기 Checkpoint 저장"""
    pass

async def aget_tuple(self, config):
    """비동기 Checkpoint 조회"""
    pass

async def alist(self, config, *, filter=None, before=None, limit=None):
    """비동기 Checkpoint 목록 조회"""
    pass

async def adelete_thread(self, thread_id):
    """비동기 Thread 삭제"""
    pass
```

## 6. 실전 예제: 멀티 턴 대화 챗봇

Persistence를 활용한 실제 챗봇 구현을 살펴보자.

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI


# 1. State 정의
class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]  # 자동 누적


# 2. 노드 정의
llm = ChatOpenAI(model="gpt-4")

def chat(state: ConversationState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


# 3. 그래프 빌드
builder = StateGraph(ConversationState)
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)


# 4. Checkpointer 적용
DB_URI = "postgres://user:pass@localhost:5432/chatbot"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()
    graph = builder.compile(checkpointer=checkpointer)

    # 사용자 A의 대화
    config_a = {"configurable": {"thread_id": "user_A"}}

    # 첫 번째 메시지
    result1 = graph.invoke(
        {"messages": [HumanMessage(content="안녕! 나는 철수야")]},
        config=config_a
    )
    print(result1["messages"][-1].content)
    # "안녕하세요, 철수님! 만나서 반갑습니다."

    # 두 번째 메시지 - 이전 컨텍스트 유지
    result2 = graph.invoke(
        {"messages": [HumanMessage(content="내 이름이 뭐라고 했지?")]},
        config=config_a
    )
    print(result2["messages"][-1].content)
    # "철수라고 하셨습니다!"  ✅ 이전 대화 기억

    # 사용자 B의 대화 - 완전히 분리된 컨텍스트
    config_b = {"configurable": {"thread_id": "user_B"}}

    result3 = graph.invoke(
        {"messages": [HumanMessage(content="내 이름이 뭐야?")]},
        config=config_b
    )
    print(result3["messages"][-1].content)
    # "아직 이름을 알려주지 않으셨네요."  ✅ 다른 Thread
```

## 7. Checkpoint 조회와 관리

### 7.1 현재 상태 조회

```python
# 현재 상태 가져오기
state = graph.get_state(config)
print(state.values)  # channel_values
print(state.next)    # 다음 실행될 노드
```

### 7.2 Checkpoint 목록 조회

```python
# Thread의 모든 Checkpoint 조회
for checkpoint in checkpointer.list(config):
    print(f"ID: {checkpoint['id']}")
    print(f"Time: {checkpoint['ts']}")
    print(f"Values: {checkpoint['channel_values']}")
    print("---")
```

### 7.3 특정 Checkpoint에서 재개

```python
# Time Travel: 과거 상태에서 다시 시작
config_with_checkpoint = {
    "configurable": {
        "thread_id": "user_A",
        "checkpoint_id": "1ef4f797-8335-6428-8001-8a1503f9b875"
    }
}

result = graph.invoke(
    {"messages": [HumanMessage(content="다른 질문")]},
    config=config_with_checkpoint
)
```

### 7.4 Thread 삭제

```python
# Thread의 모든 Checkpoint 삭제
checkpointer.delete_thread("user_A")
```

## 8. 정리

LangGraph의 **Persistence** 는 그래프 상태를 영속화하여 다음을 가능하게 한다:

**핵심 개념:**

| 개념 | 설명 |
|------|------|
| **Checkpoint** | 노드 실행 후 저장되는 상태 스냅샷 |
| **Thread** | Checkpoint들을 묶는 논리적 단위 (대화 세션) |
| **Checkpointer** | Checkpoint를 저장/조회하는 인터페이스 |

**Checkpointer 선택:**

| 상황 | 추천 |
|------|------|
| 개발/테스트 | `InMemorySaver` |
| 단일 서버, 간단한 프로덕션 | `SqliteSaver` |
| 다중 서버, 확장 필요 | `PostgresSaver` |

**활용 시나리오:**

- **멀티 턴 대화**: Thread ID로 사용자별 대화 컨텍스트 유지
- **중단/재개**: Human-in-the-loop, 긴 작업의 중간 저장
- **Time Travel**: 과거 상태로 되돌리기, 디버깅
- **Durable Execution**: 서버 재시작 후에도 작업 재개

---

## 출처

- [LangGraph Documentation - Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) - 공식 문서
- [LangGraph Checkpoint Package](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint) - GitHub
- [LangGraph Checkpoint SQLite](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-sqlite)
- [LangGraph Checkpoint Postgres](https://github.com/langchain-ai/langgraph/tree/main/libs/checkpoint-postgres)
