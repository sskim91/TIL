# LangGraph Memory - 기억을 관리하는 두 가지 방법

"지난번에 내가 좋아한다고 했던 음식이 뭐였지?" - 챗봇이 이런 질문에 답하려면 어떻게 해야 할까?

## 결론부터 말하면

LangGraph는 **두 가지 메모리 시스템** 을 제공한다:

1. **Short-term Memory (단기 기억)**: Checkpointer를 통한 **Thread 내** 상태 유지
2. **Long-term Memory (장기 기억)**: Store를 통한 **Thread 간** 데이터 공유

```mermaid
flowchart TB
    subgraph ShortTerm["Short-term Memory (Checkpointer)"]
        direction LR
        T1["Thread A<br>대화 1"] --> T1C["Checkpoint 1<br>Checkpoint 2<br>Checkpoint 3"]
        T2["Thread B<br>대화 2"] --> T2C["Checkpoint 1<br>Checkpoint 2"]
    end

    subgraph LongTerm["Long-term Memory (Store)"]
        direction LR
        S["Store"]
        S --> N1["user_123<br>preferences"]
        S --> N2["user_123<br>facts"]
        S --> N3["shared<br>knowledge"]
    end

    T1C -.->|"같은 사용자"| N1
    T2C -.->|"같은 사용자"| N1

    style T1 fill:#1565C0,color:#fff
    style T2 fill:#1565C0,color:#fff
    style S fill:#2E7D32,color:#fff
```

| 구분 | Short-term (Checkpointer) | Long-term (Store) |
|------|---------------------------|-------------------|
| 범위 | Thread 내 | Thread 간 (Cross-thread) |
| 용도 | 대화 히스토리, 실행 상태 | 사용자 선호도, 학습된 사실 |
| 수명 | Thread 종료까지 | 명시적 삭제까지 영구 |
| 접근 | `thread_id` | `namespace` + `key` |

## 1. Short-term Memory: 대화의 맥락을 기억하다

### 1.1 문제: 메시지를 기억하지 못하는 챗봇

LLM은 기본적으로 **무상태(stateless)** 다. 각 요청은 독립적으로 처리된다.

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI()

# 첫 번째 질문
response1 = llm.invoke("내 이름은 철수야")
print(response1.content)  # "안녕하세요, 철수님!"

# 두 번째 질문
response2 = llm.invoke("내 이름이 뭐라고 했지?")
print(response2.content)  # "죄송합니다, 이름을 알려주시지 않으셨네요." ❌
```

LLM은 이전 대화를 전혀 기억하지 못한다. 이를 해결하려면 **메시지 히스토리를 관리** 해야 한다.

### 1.2 해결: Checkpointer로 대화 상태 저장

LangGraph의 Checkpointer는 각 노드 실행 후 상태를 자동 저장한다. `add_messages` reducer와 함께 사용하면 대화 히스토리가 자동으로 누적된다.

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


class State(TypedDict):
    messages: Annotated[list, add_messages]  # 메시지 자동 누적


llm = ChatOpenAI()


def chatbot(state: State) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


# 그래프 빌드
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)

# Checkpointer 연결
memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)

# 대화 시작 (Thread ID로 대화 분리)
config = {"configurable": {"thread_id": "user_철수"}}

# 첫 번째 메시지
result1 = graph.invoke(
    {"messages": [HumanMessage(content="내 이름은 철수야")]},
    config
)
print(result1["messages"][-1].content)
# "안녕하세요, 철수님! 만나서 반갑습니다."

# 두 번째 메시지 - 이전 대화 기억!
result2 = graph.invoke(
    {"messages": [HumanMessage(content="내 이름이 뭐라고 했지?")]},
    config
)
print(result2["messages"][-1].content)
# "철수라고 하셨습니다!" ✅
```

### 1.3 Short-term Memory의 특징

```mermaid
flowchart LR
    subgraph Thread1["Thread: user_철수"]
        M1["안녕, 나는 철수"] --> M2["철수님 반가워요"]
        M2 --> M3["내 이름이 뭐야?"] --> M4["철수님이시죠!"]
    end

    subgraph Thread2["Thread: user_영희"]
        N1["내 이름이 뭐야?"] --> N2["아직 모릅니다"]
    end

    style M4 fill:#2E7D32,color:#fff
    style N2 fill:#E65100,color:#fff
```

| 특징 | 설명 |
|------|------|
| **Thread 격리** | 각 Thread는 독립적인 메모리 공간 |
| **자동 저장** | 노드 실행마다 Checkpoint 생성 |
| **히스토리 누적** | `add_messages`로 메시지 자동 추가 |
| **Time Travel** | 과거 Checkpoint로 되돌리기 가능 |

### 1.4 한계: Thread를 넘어서는 기억

Short-term Memory는 **같은 Thread 내** 에서만 유효하다.

```python
# Thread A에서 저장한 정보
config_a = {"configurable": {"thread_id": "thread_A"}}
graph.invoke({"messages": [HumanMessage(content="나는 피자를 좋아해")]}, config_a)

# Thread B에서는 모른다
config_b = {"configurable": {"thread_id": "thread_B"}}
result = graph.invoke(
    {"messages": [HumanMessage(content="내가 좋아하는 음식이 뭐야?")]},
    config_b
)
# "아직 알려주지 않으셨네요" ❌
```

사용자가 **새로운 대화를 시작** 하거나 **다른 기기에서 접속** 하면, 이전 대화의 맥락이 사라진다. 이런 문제를 해결하려면 **Long-term Memory** 가 필요하다.

## 2. Long-term Memory: 영구적인 기억 저장소

### 2.1 Store란?

**Store** 는 Thread와 독립적으로 데이터를 저장하는 **키-값 저장소** 다. Namespace로 데이터를 구조화하고, 여러 Thread에서 공유할 수 있다.

```mermaid
flowchart TB
    subgraph Store["Store"]
        subgraph NS1["namespace: ('users', 'user_123')"]
            K1["preferences<br>피자 좋아함, 커피 싫어함"]
            K2["facts<br>서울 거주, 개발자"]
        end

        subgraph NS2["namespace: ('users', 'user_456')"]
            K3["preferences<br>파스타 좋아함"]
        end

        subgraph NS3["namespace: ('shared',)"]
            K4["knowledge<br>공용 지식베이스"]
        end
    end

    T1["Thread A"] -->|read/write| NS1
    T2["Thread B"] -->|read/write| NS1
    T3["Thread C"] -->|read| NS3

    style Store fill:#f5f5f5
    style K1 fill:#1565C0,color:#fff
    style K2 fill:#1565C0,color:#fff
```

### 2.2 기본 사용법

```python
from langgraph.store.memory import InMemoryStore

# Store 생성
store = InMemoryStore()

# 데이터 저장
store.put(
    namespace=("users", "user_123"),  # 계층적 네임스페이스
    key="preferences",                 # 고유 키
    value={"food": "피자", "drink": "콜라"}
)

# 데이터 조회
item = store.get(namespace=("users", "user_123"), key="preferences")
print(item.value)  # {"food": "피자", "drink": "콜라"}

# 네임스페이스 내 모든 항목 검색
items = store.search(namespace=("users", "user_123"))
for item in items:
    print(f"{item.key}: {item.value}")
```

### 2.3 Item 구조

Store에 저장되는 각 항목은 `Item` 객체다.

```python
class Item:
    namespace: tuple[str, ...]  # 계층적 네임스페이스
    key: str                     # 고유 식별자
    value: dict                  # 저장된 데이터
    created_at: datetime         # 생성 시각
    updated_at: datetime         # 수정 시각
```

| 필드 | 설명 | 예시 |
|------|------|------|
| `namespace` | 데이터 분류 경로 | `("users", "user_123")` |
| `key` | 항목 식별자 | `"preferences"` |
| `value` | 실제 데이터 (dict) | `{"food": "피자"}` |
| `created_at` | 생성 시각 | `2024-01-15T10:00:00` |
| `updated_at` | 마지막 수정 시각 | `2024-01-15T14:30:00` |

### 2.4 Store 메서드

```python
# 저장 (존재하면 덮어쓰기)
store.put(namespace, key, value)

# 조회 (없으면 None)
item = store.get(namespace, key)

# 검색 (namespace 내 모든 항목)
items = store.search(namespace)

# 삭제
store.delete(namespace, key)
```

## 3. 그래프에서 Store 사용하기

### 3.1 Store 연결

Store를 그래프에 연결하면 노드에서 직접 접근할 수 있다.

```python
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_store

# Store와 Checkpointer 생성
store = InMemoryStore()
checkpointer = InMemorySaver()

# 그래프 컴파일 시 store 연결
graph = builder.compile(
    checkpointer=checkpointer,
    store=store
)
```

### 3.2 노드에서 Store 접근

노드 함수에서 `get_store()`로 Store에 접근한다.

```python
from langgraph.config import get_store, get_configurable


def memory_node(state: State) -> dict:
    # Store 가져오기
    store = get_store()

    # 현재 사용자 ID (config에서 가져오기)
    configurable = get_configurable()
    user_id = configurable.get("user_id", "anonymous")

    # 사용자 선호도 조회
    namespace = ("users", user_id)
    preferences = store.get(namespace, "preferences")

    if preferences:
        # 기존 선호도 사용
        return {"context": f"사용자 선호: {preferences.value}"}
    else:
        # 선호도 없음
        return {"context": "사용자 정보 없음"}
```

### 3.3 실전 예제: 사용자 선호도 학습 챗봇

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.config import get_store, get_configurable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import json


class State(TypedDict):
    messages: Annotated[list, add_messages]


llm = ChatOpenAI()


def extract_preferences(state: State) -> dict:
    """대화에서 사용자 선호도를 추출하여 Store에 저장"""
    store = get_store()
    configurable = get_configurable()
    user_id = configurable.get("user_id", "anonymous")

    # LLM으로 선호도 추출 (간단한 예시)
    last_message = state["messages"][-1].content

    # 실제로는 LLM을 사용해 더 정교하게 추출
    preferences_to_extract = []
    if "좋아" in last_message:
        # 간단한 패턴 매칭 (실제로는 LLM 사용)
        if "피자" in last_message:
            preferences_to_extract.append(("food", "피자"))
        if "커피" in last_message:
            preferences_to_extract.append(("drink", "커피"))

    if preferences_to_extract:
        # 기존 선호도 가져오기
        namespace = ("users", user_id)
        existing = store.get(namespace, "preferences")
        current_prefs = existing.value if existing else {}

        # 새 선호도 추가
        for key, value in preferences_to_extract:
            current_prefs[key] = value

        # Store에 저장
        store.put(namespace, "preferences", current_prefs)

    return {}  # 상태 변경 없음


def chatbot_with_memory(state: State) -> dict:
    """사용자 선호도를 활용한 응답 생성"""
    store = get_store()
    configurable = get_configurable()
    user_id = configurable.get("user_id", "anonymous")

    # 사용자 선호도 조회
    namespace = ("users", user_id)
    preferences = store.get(namespace, "preferences")

    # 시스템 메시지에 선호도 포함
    system_content = "당신은 친절한 AI 어시스턴트입니다."
    if preferences:
        pref_str = ", ".join(f"{k}: {v}" for k, v in preferences.value.items())
        system_content += f"\n\n사용자 선호도: {pref_str}"

    messages = [SystemMessage(content=system_content)] + state["messages"]
    response = llm.invoke(messages)

    return {"messages": [response]}


# 그래프 빌드
builder = StateGraph(State)
builder.add_node("extract", extract_preferences)
builder.add_node("chat", chatbot_with_memory)
builder.add_edge(START, "extract")
builder.add_edge("extract", "chat")
builder.add_edge("chat", END)

# Store와 Checkpointer 연결
store = InMemoryStore()
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer, store=store)
```

**사용 예시:**

```python
# 사용자 설정 (user_id를 config에 포함)
config = {
    "configurable": {
        "thread_id": "conversation_1",
        "user_id": "user_123"
    }
}

# 첫 번째 대화: 선호도 학습
result1 = graph.invoke(
    {"messages": [HumanMessage(content="나는 피자를 정말 좋아해")]},
    config
)
print(result1["messages"][-1].content)
# "피자를 좋아하시는군요! 어떤 종류의 피자를 좋아하세요?"

# Store 확인
item = store.get(("users", "user_123"), "preferences")
print(item.value)  # {"food": "피자"}

# 새로운 대화 (다른 Thread)
config2 = {
    "configurable": {
        "thread_id": "conversation_2",  # 새 Thread
        "user_id": "user_123"            # 같은 사용자
    }
}

# 이전 대화는 모르지만, 선호도는 기억!
result2 = graph.invoke(
    {"messages": [HumanMessage(content="오늘 뭐 먹을까?")]},
    config2
)
print(result2["messages"][-1].content)
# "피자를 좋아하신다고 하셨는데, 오늘 피자 어떠세요?" ✅
```

```mermaid
flowchart TB
    subgraph Conv1["Thread: conversation_1"]
        M1["피자 좋아해"] --> EXTRACT1["extract_preferences"]
        EXTRACT1 -->|저장| STORE
        EXTRACT1 --> CHAT1["chatbot_with_memory"]
    end

    subgraph Conv2["Thread: conversation_2 (새 대화)"]
        M2["오늘 뭐 먹을까?"] --> EXTRACT2["extract_preferences"]
        EXTRACT2 --> CHAT2["chatbot_with_memory"]
        STORE -->|조회| CHAT2
    end

    STORE["Store<br>food: 피자"]

    style STORE fill:#2E7D32,color:#fff
    style CHAT2 fill:#1565C0,color:#fff
```

## 4. Namespace 설계 패턴

### 4.1 계층적 구조

Namespace는 튜플로 계층 구조를 표현한다.

```python
# 사용자별 데이터
("users", "user_123", "preferences")
("users", "user_123", "history")
("users", "user_456", "preferences")

# 조직별 공유 데이터
("orgs", "acme_corp", "knowledge")
("orgs", "acme_corp", "policies")

# 전역 데이터
("global", "faq")
("global", "system_prompts")
```

### 4.2 설계 가이드

```mermaid
flowchart TB
    ROOT["Store"]

    subgraph UserScoped["사용자 범위"]
        U1["('users', user_id)"]
        U1 --> U1P["preferences"]
        U1 --> U1F["facts"]
        U1 --> U1H["interaction_history"]
    end

    subgraph OrgScoped["조직 범위"]
        O1["('orgs', org_id)"]
        O1 --> O1K["knowledge_base"]
        O1 --> O1P["policies"]
    end

    subgraph Global["전역 범위"]
        G1["('global',)"]
        G1 --> G1F["faq"]
        G1 --> G1S["system_config"]
    end

    ROOT --> UserScoped
    ROOT --> OrgScoped
    ROOT --> Global

    style U1 fill:#1565C0,color:#fff
    style O1 fill:#E65100,color:#fff
    style G1 fill:#2E7D32,color:#fff
```

| 범위 | Namespace 패턴 | 용도 |
|------|---------------|------|
| 사용자 | `("users", user_id)` | 개인 선호도, 히스토리 |
| 조직 | `("orgs", org_id)` | 팀 공유 지식 |
| 전역 | `("global",)` | 시스템 설정, FAQ |

### 4.3 검색과 필터링

```python
# 특정 네임스페이스의 모든 항목
user_data = store.search(namespace=("users", "user_123"))

# prefix로 하위 항목 모두 검색
all_users = store.search(namespace_prefix=("users",))

# 필터 조건 (Store 구현에 따라 다름)
recent_items = store.search(
    namespace=("users", "user_123"),
    filter={"updated_after": "2024-01-01"}
)
```

## 5. 프로덕션 Store 옵션

### 5.1 제공되는 Store 구현

| Store | 패키지 | 용도 |
|-------|--------|------|
| `InMemoryStore` | `langgraph` | 개발/테스트 |
| `PostgresStore` | `langgraph-checkpoint-postgres` | 프로덕션 |

### 5.2 PostgresStore 사용

```python
from langgraph.store.postgres import PostgresStore

DB_URI = "postgres://user:pass@localhost:5432/mydb"

with PostgresStore.from_conn_string(DB_URI) as store:
    # 최초 실행 시 테이블 생성
    store.setup()

    # 사용
    store.put(("users", "user_123"), "preferences", {"food": "피자"})
    item = store.get(("users", "user_123"), "preferences")
```

### 5.3 비동기 Store

```python
from langgraph.store.postgres.aio import AsyncPostgresStore

async with AsyncPostgresStore.from_conn_string(DB_URI) as store:
    await store.setup()

    await store.aput(namespace, key, value)
    item = await store.aget(namespace, key)
    items = [i async for i in store.asearch(namespace)]
```

## 6. Short-term vs Long-term: 언제 무엇을 사용할까?

### 6.1 선택 가이드

```mermaid
flowchart TD
    Q1{{"데이터 범위?"}}

    Q1 -->|"현재 대화만"| SHORT["Short-term<br>(Checkpointer)"]
    Q1 -->|"여러 대화에 걸쳐"| Q2{{"데이터 유형?"}}

    Q2 -->|"메시지 히스토리"| SHORT
    Q2 -->|"사용자 프로필/선호도"| LONG["Long-term<br>(Store)"]
    Q2 -->|"학습된 사실"| LONG

    SHORT --> EX1["예: 현재 대화 맥락<br>실행 상태"]
    LONG --> EX2["예: 좋아하는 음식<br>이름, 직업"]

    style SHORT fill:#1565C0,color:#fff
    style LONG fill:#2E7D32,color:#fff
```

### 6.2 사용 사례별 정리

| 사용 사례 | 메모리 유형 | 이유 |
|----------|------------|------|
| 멀티 턴 대화 | Short-term | Thread 내 메시지 히스토리 |
| 사용자 선호도 | Long-term | Thread 간 유지 필요 |
| 실행 중 상태 | Short-term | Checkpoint로 자동 관리 |
| 학습된 사실 | Long-term | 영구 저장 필요 |
| 공유 지식베이스 | Long-term | 여러 사용자가 접근 |

### 6.3 조합 사용

실제 애플리케이션에서는 **두 메모리를 함께 사용** 한다.

```python
# 그래프에 둘 다 연결
graph = builder.compile(
    checkpointer=PostgresSaver.from_conn_string(DB_URI),  # Short-term
    store=PostgresStore.from_conn_string(DB_URI)          # Long-term
)

config = {
    "configurable": {
        "thread_id": "conv_123",   # Short-term 식별자
        "user_id": "user_456"      # Long-term 접근용
    }
}
```

## 7. 정리

LangGraph의 메모리 시스템은 **두 가지 계층** 으로 구성된다:

**Short-term Memory (Checkpointer):**

| 특징 | 설명 |
|------|------|
| 범위 | Thread 내 |
| 저장 내용 | 메시지 히스토리, 실행 상태 |
| 접근 방식 | `thread_id` |
| 수명 | Thread 종료까지 |

**Long-term Memory (Store):**

| 특징 | 설명 |
|------|------|
| 범위 | Thread 간 (Cross-thread) |
| 저장 내용 | 사용자 선호도, 학습된 사실 |
| 접근 방식 | `namespace` + `key` |
| 수명 | 명시적 삭제까지 영구 |

**핵심 API:**

```python
# Short-term: Checkpointer
graph = builder.compile(checkpointer=InMemorySaver())
graph.invoke(input, {"configurable": {"thread_id": "..."}})

# Long-term: Store
store = InMemoryStore()
store.put(namespace, key, value)
store.get(namespace, key)
store.search(namespace)
```

---

## 출처

- [LangGraph Documentation - Memory](https://langchain-ai.github.io/langgraph/concepts/memory/) - 공식 문서
- [LangGraph Documentation - Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [LangGraph Store Package](https://github.com/langchain-ai/langgraph/tree/main/libs/store)
