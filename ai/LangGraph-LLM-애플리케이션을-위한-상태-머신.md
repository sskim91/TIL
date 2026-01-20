# LangGraph - LLM 애플리케이션을 위한 상태 머신

LangChain으로 Agent를 만들었는데, "만약 A면 B로, 아니면 C로" 같은 분기가 필요하다면?

## 결론부터 말하면

**LangGraph는 LLM 애플리케이션을 "그래프"로 설계하는 프레임워크** 다. LangChain이 "선형 체인"에 최적화되어 있다면, LangGraph는 **조건부 분기, 루프, 상태 관리** 가 필요한 복잡한 워크플로우를 위해 탄생했다.

```mermaid
flowchart LR
    subgraph LangChain["LangChain (선형)"]
        A1[입력] --> A2[처리1] --> A3[처리2] --> A4[출력]
    end

    subgraph LangGraph["LangGraph (그래프)"]
        B1[입력] --> B2{조건}
        B2 -->|Yes| B3[처리A]
        B2 -->|No| B4[처리B]
        B3 --> B5{재시도?}
        B5 -->|Yes| B3
        B5 -->|No| B6[출력]
        B4 --> B6
    end

```

| 구분 | LangChain | LangGraph |
|------|-----------|-----------|
| 구조 | 선형 체인 | 방향 그래프 (DAG) |
| 분기 | 제한적 | 조건부 엣지로 자유롭게 |
| 루프 | 불가능 | 노드 간 순환 가능 |
| 상태 | 암묵적 | **명시적** State 객체 |
| 중단/재개 | 어려움 | Checkpoint로 쉽게 |
| Human-in-the-loop | 별도 구현 | `interrupt()` 내장 |

## 1. 왜 LangGraph가 필요한가?

### 1.1 LangChain의 한계

LangChain으로 간단한 챗봇을 만드는 건 쉽다. 하지만 실제 프로덕션 환경에서는 이런 요구사항이 생긴다:

> "문서를 검색했는데 관련 없는 결과가 나오면, 쿼리를 다시 작성해서 재검색해줘."
>
> "생성된 답변이 hallucination이면 다시 생성하고, 3번 실패하면 포기해."
>
> "위험한 작업이면 사용자 승인을 받고 진행해."

이걸 LangChain만으로 구현하려면? 복잡한 `if-else` 로직과 상태 관리 코드가 뒤엉킨다.

```python
# LangChain으로 재시도 로직 구현 (복잡함)
def rag_with_retry(question):
    documents = retrieve(question)

    if not is_relevant(documents):
        # 쿼리 재작성
        new_question = transform_query(question)
        documents = retrieve(new_question)

        if not is_relevant(documents):
            # 웹 검색 폴백
            documents = web_search(question)

    answer = generate(question, documents)

    if is_hallucination(answer):
        # 재생성
        answer = generate(question, documents)

        if is_hallucination(answer):
            return "답변을 생성할 수 없습니다."

    return answer
```

문제점:
- **상태 관리가 암묵적** : `documents`, `answer` 등이 함수 내부에 흩어져 있음
- **재사용이 어려움** : 로직이 하나의 함수에 묶여 있음
- **디버깅이 힘듦** : 어느 단계에서 실패했는지 추적하기 어려움
- **중단/재개 불가** : 중간에 멈추고 나중에 이어서 실행할 수 없음

### 1.2 LangGraph의 해결책

LangGraph는 이 문제를 **그래프** 로 해결한다. 각 단계를 **노드(Node)** 로, 전환 규칙을 **엣지(Edge)** 로 정의한다.

```mermaid
flowchart TD
    START((시작)) --> retrieve[문서 검색]
    retrieve --> grade{관련성 평가}

    grade -->|관련 있음| generate[답변 생성]
    grade -->|관련 없음| transform[쿼리 재작성]

    transform --> retrieve

    generate --> check{hallucination?}
    check -->|Yes| generate
    check -->|No| END((종료))

    style START fill:#1565C0,color:#fff
    style END fill:#2E7D32,color:#fff
    style grade fill:#E65100,color:#fff
    style check fill:#E65100,color:#fff
```

같은 로직을 LangGraph로 구현하면:

```python
from langgraph.graph import StateGraph, START, END

# 1. State 정의 - 모든 상태가 명시적
class RAGState(TypedDict):
    question: str
    documents: list[str]
    generation: str
    retry_count: int

# 2. 노드 정의 - 각 단계가 독립적인 함수
def retrieve(state: RAGState) -> dict:
    docs = vector_store.search(state["question"])
    return {"documents": docs}

def grade_documents(state: RAGState) -> dict:
    # 문서 평가 로직
    return {"documents": relevant_docs}

def generate(state: RAGState) -> dict:
    answer = llm.generate(state["question"], state["documents"])
    return {"generation": answer, "retry_count": state["retry_count"] + 1}

def transform_query(state: RAGState) -> dict:
    new_query = llm.rewrite(state["question"])
    return {"question": new_query}

# 3. 조건부 엣지 - 분기 로직이 명확하게 분리
def should_generate(state: RAGState) -> str:
    if has_relevant_documents(state["documents"]):
        return "generate"
    return "transform_query"

def check_hallucination(state: RAGState) -> str:
    if is_hallucination(state["generation"]):
        if state["retry_count"] < 3:
            return "generate"  # 재시도
        return "give_up"
    return "end"

# 4. 그래프 조립
workflow = StateGraph(RAGState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade")
workflow.add_conditional_edges("grade", should_generate, {
    "generate": "generate",
    "transform_query": "transform_query"
})
workflow.add_edge("transform_query", "retrieve")  # 루프!
workflow.add_conditional_edges("generate", check_hallucination, {
    "generate": "generate",  # 재시도 루프!
    "end": END,
    "give_up": END
})

app = workflow.compile()
```

**개선점:**

| Before (LangChain) | After (LangGraph) |
|-------------------|-------------------|
| 상태가 함수 내부에 흩어짐 | `RAGState`에 모든 상태 명시 |
| 분기 로직이 `if-else`로 복잡 | `add_conditional_edges`로 명확 |
| 루프 구현이 재귀/while로 복잡 | 엣지로 자연스럽게 표현 |
| 디버깅 어려움 | 각 노드별 상태 추적 가능 |

## 2. LangGraph 핵심 개념

### 2.1 State - 애플리케이션의 "현재 상태"

State는 그래프 전체에서 공유되는 데이터 구조다. 각 노드는 State를 받아서 처리하고, 변경된 부분만 반환한다.

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class ConversationState(TypedDict):
    # 메시지 리스트 (add_messages는 새 메시지를 누적)
    messages: Annotated[list, add_messages]
    # 현재 단계
    current_step: str
    # 재시도 횟수
    retry_count: int
```

**핵심 포인트:** `Annotated`와 `add_messages`

```python
# add_messages를 사용하면 기존 메시지에 새 메시지가 추가됨
messages: Annotated[list, add_messages]

# 노드에서 반환할 때:
return {"messages": [new_message]}  # 기존 리스트에 append됨

# add_messages 없으면:
return {"messages": [new_message]}  # 기존 리스트가 대체됨!
```

### 2.2 Node - 작업의 단위

노드는 State를 받아 처리하는 함수다. **반환값은 State의 일부분만 있으면 된다** (해당 부분만 업데이트).

```python
def process_input(state: ConversationState) -> dict:
    """입력 처리 노드"""
    last_message = state["messages"][-1].content
    processed = preprocess(last_message)

    # messages만 업데이트 (current_step, retry_count는 그대로)
    return {
        "messages": [AIMessage(content=processed)]
    }
```

**노드 등록:**

```python
from langgraph.graph import StateGraph

builder = StateGraph(ConversationState)

# 함수를 노드로 등록
builder.add_node("process", process_input)
builder.add_node("respond", generate_response)
builder.add_node("validate", validate_response)
```

### 2.3 Edge - 노드 간 전환 규칙

엣지는 "어느 노드 다음에 어느 노드가 실행되는가"를 정의한다.

```python
from langgraph.graph import START, END

# 단순 엣지: A 다음에 항상 B
builder.add_edge("process", "respond")

# 시작점과 종료점
builder.add_edge(START, "process")
builder.add_edge("validate", END)
```

**조건부 엣지** 가 LangGraph의 핵심이다:

```python
def route_by_intent(state: ConversationState) -> str:
    """사용자 의도에 따라 다른 노드로 분기"""
    last_message = state["messages"][-1].content

    if "날씨" in last_message:
        return "weather_node"
    elif "예약" in last_message:
        return "booking_node"
    else:
        return "general_node"

# 조건부 엣지 등록
builder.add_conditional_edges(
    "process",           # 출발 노드
    route_by_intent,     # 라우팅 함수
    {                    # 반환값 → 노드 매핑
        "weather_node": "weather",
        "booking_node": "booking",
        "general_node": "general"
    }
)
```

```mermaid
flowchart LR
    process[입력 처리] --> route{route_by_intent}
    route -->|"날씨"| weather[날씨 노드]
    route -->|"예약"| booking[예약 노드]
    route -->|"기타"| general[일반 노드]

    style route fill:#E65100,color:#fff
```

### 2.4 Graph - 전체 워크플로우

모든 노드와 엣지를 조립하면 그래프가 완성된다.

```python
from langgraph.graph import StateGraph, START, END

# 1. 그래프 빌더 생성
builder = StateGraph(ConversationState)

# 2. 노드 추가
builder.add_node("classify", classify_intent)
builder.add_node("weather", handle_weather)
builder.add_node("booking", handle_booking)
builder.add_node("general", handle_general)

# 3. 엣지 추가
builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route_by_intent)
builder.add_edge("weather", END)
builder.add_edge("booking", END)
builder.add_edge("general", END)

# 4. 컴파일
graph = builder.compile()

# 5. 실행
result = graph.invoke({
    "messages": [HumanMessage(content="오늘 날씨 어때?")],
    "current_step": "",
    "retry_count": 0
})
```

## 3. 실전 예제: Self-RAG 워크플로우

문서 검색 → 관련성 평가 → 답변 생성 → Hallucination 체크까지 수행하는 Self-RAG를 구현해보자.

```mermaid
flowchart TD
    START((START)) --> retrieve[문서 검색]
    retrieve --> grade[관련성 평가]

    grade --> decide{관련 문서 있음?}
    decide -->|Yes| generate[답변 생성]
    decide -->|No| transform[쿼리 재작성]

    transform --> retrieve

    generate --> check{Hallucination?}
    check -->|Yes, 재시도| generate
    check -->|Yes, 포기| web[웹 검색]
    check -->|No| END((END))

    web --> generate

    style START fill:#1565C0,color:#fff
    style END fill:#2E7D32,color:#fff
    style decide fill:#E65100,color:#fff
    style check fill:#E65100,color:#fff
```

```python
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# === 1. State 정의 ===
class RAGState(TypedDict):
    question: str
    documents: list[str]
    generation: str
    retry_count: int
    web_search_used: bool


# === 2. 노드 정의 ===
def retrieve(state: RAGState) -> dict:
    """벡터 DB에서 문서 검색"""
    question = state["question"]
    docs = vector_store.similarity_search(question, k=4)
    return {"documents": [doc.page_content for doc in docs]}


def grade_documents(state: RAGState) -> dict:
    """문서 관련성 평가"""
    question = state["question"]
    documents = state["documents"]

    relevant_docs = []
    for doc in documents:
        score = relevance_grader.invoke({
            "question": question,
            "document": doc
        })
        if score.binary_score == "yes":
            relevant_docs.append(doc)

    return {"documents": relevant_docs}


def generate(state: RAGState) -> dict:
    """답변 생성"""
    question = state["question"]
    documents = state["documents"]

    generation = rag_chain.invoke({
        "context": "\n\n".join(documents),
        "question": question
    })

    return {
        "generation": generation,
        "retry_count": state["retry_count"] + 1
    }


def transform_query(state: RAGState) -> dict:
    """쿼리 재작성"""
    question = state["question"]
    better_question = query_rewriter.invoke({"question": question})
    return {"question": better_question}


def web_search(state: RAGState) -> dict:
    """웹 검색 폴백"""
    question = state["question"]
    docs = tavily_search.invoke({"query": question})
    return {
        "documents": [d["content"] for d in docs],
        "web_search_used": True
    }


# === 3. 라우팅 함수 ===
def decide_to_generate(state: RAGState) -> Literal["generate", "transform"]:
    """관련 문서가 있으면 생성, 없으면 쿼리 재작성"""
    if state["documents"]:
        return "generate"
    return "transform"


def check_hallucination(state: RAGState) -> Literal["end", "retry", "web_search"]:
    """Hallucination 체크"""
    generation = state["generation"]
    documents = state["documents"]

    # Hallucination 체크
    score = hallucination_grader.invoke({
        "documents": documents,
        "generation": generation
    })

    if score.binary_score == "yes":  # Hallucination 감지
        if state["retry_count"] < 3:
            return "retry"
        return "web_search"  # 3번 실패 시 웹 검색

    return "end"


# === 4. 그래프 조립 ===
workflow = StateGraph(RAGState)

# 노드 등록
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform", transform_query)
workflow.add_node("web_search", web_search)

# 엣지 정의
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade")

workflow.add_conditional_edges(
    "grade",
    decide_to_generate,
    {
        "generate": "generate",
        "transform": "transform"
    }
)

workflow.add_edge("transform", "retrieve")  # 쿼리 재작성 후 재검색

workflow.add_conditional_edges(
    "generate",
    check_hallucination,
    {
        "end": END,
        "retry": "generate",      # 재시도 루프
        "web_search": "web_search"
    }
)

workflow.add_edge("web_search", "generate")  # 웹 검색 후 재생성

# 컴파일
app = workflow.compile()


# === 5. 실행 ===
result = app.invoke({
    "question": "LangGraph의 핵심 개념은 무엇인가요?",
    "documents": [],
    "generation": "",
    "retry_count": 0,
    "web_search_used": False
})

print(result["generation"])
```

## 4. Checkpointing - 상태 저장과 복구

LangGraph의 강력한 기능 중 하나가 **Checkpointing** 이다. 각 노드 실행 후 상태를 저장하여 나중에 복구할 수 있다.

### 4.1 Checkpointer 설정

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver

# 개발/테스트용 (메모리)
memory = InMemorySaver()

# 프로덕션용 (SQLite)
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# 프로덕션용 (PostgreSQL)
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/mydb"
)

# 그래프에 적용
app = workflow.compile(checkpointer=memory)
```

### 4.2 Thread ID로 대화 관리

```python
# 사용자별 대화 분리
config = {"configurable": {"thread_id": "user_123"}}

# 첫 번째 질문
result1 = app.invoke(
    {"question": "LangGraph란?", ...},
    config=config
)

# 두 번째 질문 - 이전 대화 컨텍스트 유지
result2 = app.invoke(
    {"question": "더 자세히 설명해줘", ...},
    config=config  # 같은 thread_id
)
```

### 4.3 특정 Checkpoint에서 재개

```python
# 특정 checkpoint로 복구
config = {
    "configurable": {
        "thread_id": "user_123",
        "checkpoint_id": "abc-123-def"  # 특정 시점
    }
}

result = app.invoke(state, config=config)
```

## 5. Human-in-the-Loop - 사람 개입

위험한 작업 전에 사용자 승인을 받거나, 중간 결과를 검토받을 때 사용한다.

```python
from langgraph.types import interrupt, Command

class ApprovalState(TypedDict):
    action: str
    approved: bool | None
    result: str


def propose_action(state: ApprovalState) -> dict:
    """실행할 작업 제안"""
    return {"action": "모든 파일 삭제", "result": "대기 중"}


def get_approval(state: ApprovalState) -> dict:
    """사용자 승인 대기"""
    # interrupt()가 호출되면 그래프 실행이 중단됨
    response = interrupt({
        "question": f"'{state['action']}'을(를) 실행할까요?",
        "options": ["yes", "no"]
    })
    return {"approved": response == "yes"}


def execute_action(state: ApprovalState) -> dict:
    """승인된 작업 실행"""
    if state["approved"]:
        # 실제 작업 수행
        return {"result": "작업 완료!"}
    return {"result": "작업 취소됨"}


# 그래프 구성
builder = StateGraph(ApprovalState)
builder.add_node("propose", propose_action)
builder.add_node("approval", get_approval)
builder.add_node("execute", execute_action)

builder.add_edge(START, "propose")
builder.add_edge("propose", "approval")
builder.add_edge("approval", "execute")
builder.add_edge("execute", END)

# Checkpointer 필수!
memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "approval_flow_1"}}

# 실행 - approval 노드에서 중단됨
for chunk in graph.stream(
    {"action": "", "approved": None, "result": ""},
    config
):
    print(chunk)
    # {'propose': {'action': '모든 파일 삭제', 'result': '대기 중'}}
    # (approval에서 interrupt로 중단)

# 사용자 입력 후 재개
from langgraph.types import Command

# yes를 선택한 경우
graph.invoke(Command(resume="yes"), config=config)
# {'execute': {'result': '작업 완료!'}}
```

```mermaid
sequenceDiagram
    participant User
    participant Graph
    participant Checkpointer

    User->>Graph: invoke(initial_state)
    Graph->>Graph: propose_action 실행
    Graph->>Graph: get_approval 진입
    Graph->>Checkpointer: interrupt 발생, 상태 저장
    Graph-->>User: 중단 (승인 요청)

    Note over User: 사용자가 검토 후 결정

    User->>Graph: invoke(Command(resume="yes"))
    Graph->>Checkpointer: 저장된 상태 로드
    Graph->>Graph: execute_action 실행
    Graph-->>User: 결과 반환
```

## 6. Streaming - 실시간 결과

LangGraph는 두 가지 스트리밍 모드를 지원한다.

### 6.1 노드별 스트리밍

```python
# 각 노드 완료 시마다 결과 반환
for chunk in app.stream(initial_state, config):
    for node_name, node_output in chunk.items():
        print(f"[{node_name}] {node_output}")

# 출력:
# [retrieve] {'documents': [...]}
# [grade] {'documents': [...]}
# [generate] {'generation': '...'}
```

### 6.2 토큰별 스트리밍

```python
# LLM 토큰 단위로 스트리밍
async for event in app.astream_events(initial_state, config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        print(event["data"]["chunk"].content, end="", flush=True)
```

## 7. LangChain Agent와 LangGraph 언제 뭘 써야 할까?

| 상황 | 추천 | 이유 |
|------|------|------|
| 단순 Q&A 챗봇 | LangChain Agent | 선형 흐름으로 충분 |
| 도구 호출 Agent | LangChain Agent | `create_agent`로 쉽게 구현 |
| 조건부 분기 필요 | **LangGraph** | `add_conditional_edges` |
| 재시도/루프 필요 | **LangGraph** | 노드 순환 가능 |
| Human-in-the-loop | **LangGraph** | `interrupt()` 내장 |
| 복잡한 워크플로우 | **LangGraph** | 그래프로 명확하게 표현 |
| 상태 저장/복구 | **LangGraph** | Checkpointing |
| 멀티 에이전트 | **LangGraph** | 각 에이전트를 노드로 |

**실제로 LangChain의 `create_agent` 내부도 LangGraph로 구현되어 있다.** 간단한 경우 `create_agent`를 쓰고, 커스텀 워크플로우가 필요하면 LangGraph로 직접 구현하면 된다.

## 8. 정리

LangGraph는 **LLM 애플리케이션을 상태 머신** 으로 설계하는 프레임워크다.

**핵심 개념:**
- **State** : 그래프 전체에서 공유되는 상태 객체
- **Node** : State를 받아 처리하는 함수
- **Edge** : 노드 간 전환 규칙 (조건부 분기 포함)
- **Graph** : 노드와 엣지로 구성된 워크플로우

**LangChain과의 차이:**
- LangChain = 선형 체인에 최적화
- LangGraph = 조건부 분기, 루프, 상태 관리가 필요한 복잡한 워크플로우

**언제 사용하나:**
- 단순 체인 → LangChain
- 조건 분기, 루프, Human-in-the-loop → LangGraph

---

## 출처

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) - 공식 문서
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangChain Documentation](https://docs.langchain.com/)
