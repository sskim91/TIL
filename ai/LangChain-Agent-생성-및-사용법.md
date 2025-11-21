# LangChain Agent 생성 및 사용법

LangChain v1.0의 create_agent를 사용한 AI Agent 구축 완전 가이드

## 결론부터 말하면

**LangChain Agent는 LLM에 도구(tools)를 연결하고, 구조화된 응답을 받으며, 대화 기록을 관리하는 시스템**입니다.

```python
# Before: 단순 LLM 호출
response = model.invoke("날씨 알려줘")
# → "죄송합니다. 실시간 날씨 정보에 접근할 수 없습니다."

# After: Agent with Tools
agent = create_agent(
    model=model,
    tools=[get_weather],  # LLM이 실제 날씨 API 호출 가능
    response_format=WeatherResponse,  # 구조화된 응답
    checkpointer=memory  # 대화 기록 유지
)
response = agent.invoke({"messages": [{"role": "user", "content": "날씨 알려줘"}]})
# → WeatherResponse(temperature=25, condition="맑음")
```

## 1. Agent란 무엇인가?

### 기본 개념

**Agent = LLM + Tools + Memory + Structured Output**

```mermaid
graph TB
    User[사용자 질문] --> Agent[LangChain Agent]

    subgraph Agent Components
        LLM[Large Language Model]
        Tools[도구 모음]
        Memory[대화 기록]
        Format[응답 형식]
    end

    Agent --> LLM
    LLM --> Decision{도구 필요?}

    Decision -->|Yes| Tools
    Tools --> LLM

    Decision -->|No| Format
    LLM --> Format

    Format --> Memory
    Memory --> Response[구조화된 응답]
    Response --> User

    style Agent stroke:#2196F3,stroke-width:3px
    style Tools fill:#4CAF50,color:#fff
    style Memory fill:#FF9800,color:#fff
    style Format fill:#9C27B0,color:#fff
```

### Agent vs 단순 LLM 비교

| 특징 | 단순 LLM | LangChain Agent |
|------|---------|----------------|
| **외부 데이터** | ❌ 없음 | ✅ Tools로 실시간 데이터 접근 |
| **응답 형식** | 자유 텍스트 | 구조화된 데이터 (dataclass) |
| **대화 기록** | 직접 관리 필요 | Checkpointer가 자동 관리 |
| **사용자별 처리** | 불가능 | Context로 런타임 정보 주입 |
| **복잡한 작업** | 한계 있음 | 다단계 도구 사용 가능 |

## 2. 전체 예제 코드

```python
from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver


# 1. 시스템 프롬프트 정의
SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.

You have access to two tools:

- get_weather_for_location: use this to get the weather for a specific location
- get_user_location: use this to get the user's location

If a user asks you for the weather, make sure you know the location. If you can tell from the question that they mean wherever they are, use the get_user_location tool to find their location."""

# 2. Context 스키마 정의
@dataclass
class Context:
    """Custom runtime context schema."""
    user_id: str

# 3. 도구(Tools) 정의
@tool
def get_weather_for_location(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """Retrieve user information based on user ID."""
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"

# 4. 모델 설정
model = init_chat_model(
    "anthropic:claude-sonnet-4-5",
    temperature=0
)

# 5. 응답 형식 정의
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    # A punny response (always required)
    punny_response: str
    # Any interesting information about the weather if available
    weather_conditions: str | None = None

# 6. 메모리 설정
checkpointer = InMemorySaver()

# 7. Agent 생성
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)

# 8. Agent 실행
config = {"configurable": {"thread_id": "1"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])
# ResponseFormat(
#     punny_response="Florida is still having a 'sun-derful' day!...",
#     weather_conditions="It's always sunny in Florida!"
# )

# 9. 대화 이어서 진행
response = agent.invoke(
    {"messages": [{"role": "user", "content": "thank you!"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])
# ResponseFormat(
#     punny_response="You're 'thund-erfully' welcome!...",
#     weather_conditions=None
# )
```

## 3. 단계별 상세 설명

### 3.1 시스템 프롬프트 (SYSTEM_PROMPT)

```python
SYSTEM_PROMPT = """You are an expert weather forecaster, who speaks in puns.

You have access to two tools:

- get_weather_for_location: use this to get the weather for a specific location
- get_user_location: use this to get the user's location

If a user asks you for the weather, make sure you know the location..."""
```

**역할:**
- Agent의 페르소나 정의 ("말장난하는 날씨 전문가")
- 사용 가능한 도구 설명
- 도구 사용 시나리오 안내

**Java 비유:**
```java
// Spring Boot의 @Component 설명과 유사
@Component
public class WeatherAgent {
    /**
     * 역할: 날씨 전문가
     * 도구: WeatherAPI, LocationService
     * 규칙: 위치를 먼저 확인할 것
     */
}
```

### 3.2 Context 스키마

```python
@dataclass
class Context:
    """Custom runtime context schema."""
    user_id: str
```

**역할:** 도구 실행 시 런타임 정보 전달

**실행 흐름:**

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Tool

    User->>Agent: invoke(message, context=Context(user_id=1))
    Agent->>Agent: LLM이 도구 호출 결정
    Agent->>Tool: get_user_location(runtime)
    Note over Tool: runtime.context.user_id = 1
    Tool->>Tool: user_id == 1 확인
    Tool-->>Agent: Florida 반환
    Agent-->>User: 응답 반환
```

**실전 활용:**

```python
@dataclass
class Context:
    user_id: str
    session_id: str
    subscription_tier: str  # "free", "pro", "enterprise"
    language: str           # "ko", "en", "ja"

@tool
def search_database(query: str, runtime: ToolRuntime[Context]) -> str:
    """구독 등급에 따라 다른 검색 결과 제공"""
    tier = runtime.context.subscription_tier
    lang = runtime.context.language

    # 등급별 제한
    limit = {"free": 10, "pro": 100, "enterprise": None}[tier]

    # 언어별 번역
    results = db.search(query, limit=limit, lang=lang)
    return results
```

### 3.3 도구 (Tools) 정의

#### 기본 도구 (Context 없음)

```python
@tool
def get_weather_for_location(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"
```

- `@tool` 데코레이터로 LLM이 호출 가능한 도구로 등록
- 함수의 docstring이 도구 설명으로 사용됨
- 인자와 반환 타입을 명시해야 함

#### Context 사용 도구

```python
@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """Retrieve user information based on user ID."""
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "SF"
```

- `ToolRuntime[Context]`로 런타임 컨텍스트 접근
- `runtime.context.user_id`로 사용자 정보 획득

**도구가 호출되는 과정:**

```mermaid
graph LR
    A[사용자: 날씨 알려줘] --> B[LLM 분석]
    B --> C{위치 정보 있음?}

    C -->|No| D[get_user_location 호출]
    D --> E[user_id로 위치 조회]
    E --> F[Florida 반환]

    C -->|Yes| G[get_weather_for_location 호출]
    F --> G
    G --> H[날씨 정보 반환]

    H --> I[LLM이 응답 생성]
    I --> J[구조화된 응답 반환]

    style D stroke:#2196F3,stroke-width:3px
    style G stroke:#2196F3,stroke-width:3px
```

**실전 도구 예시:**

```python
@tool
def get_current_time(timezone: str) -> str:
    """특정 타임존의 현재 시간을 반환"""
    from datetime import datetime
    import pytz

    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S")

@tool
def search_web(query: str, runtime: ToolRuntime[Context]) -> str:
    """웹 검색 수행 (사용자 언어 고려)"""
    lang = runtime.context.language

    # Google Search API 호출
    results = google_search(query, lang=lang)
    return results[:5]  # 상위 5개 결과만

@tool
def send_email(to: str, subject: str, body: str, runtime: ToolRuntime[Context]) -> str:
    """이메일 발송 (사용자 권한 확인)"""
    user_id = runtime.context.user_id

    # 권한 확인
    if not has_email_permission(user_id):
        return "이메일 발송 권한이 없습니다."

    # 이메일 발송
    send_email_via_smtp(to, subject, body)
    return f"이메일 발송 완료: {to}"
```

### 3.4 모델 설정

```python
model = init_chat_model(
    "anthropic:claude-sonnet-4-5",
    temperature=0
)
```

**파라미터:**
- `"anthropic:claude-sonnet-4-5"`: 모델 지정 (provider:model_name)
- `temperature=0`: 일관된 응답 (0 = 결정론적, 1 = 창의적)

**지원 모델:**

```python
# OpenAI
model = init_chat_model("openai:gpt-4o", temperature=0.7)

# Anthropic
model = init_chat_model("anthropic:claude-sonnet-4-5", temperature=0)

# Google
model = init_chat_model("google-genai:gemini-2.0-flash-exp", temperature=0.5)

# Ollama (로컬)
model = init_chat_model("ollama:llama3", temperature=0.8)
```

**Temperature 값:**

| 값 | 용도 | 예시 |
|----|------|------|
| 0.0 | 정확한 답변, 일관성 | 고객 지원, 데이터 분석 |
| 0.3-0.5 | 균형 잡힌 응답 | 일반 대화, 요약 |
| 0.7-0.9 | 창의적 응답 | 글쓰기, 브레인스토밍 |
| 1.0+ | 매우 창의적 | 스토리 생성, 예술 |

### 3.5 응답 형식 (Response Format)

```python
@dataclass
class ResponseFormat:
    """Response schema for the agent."""
    punny_response: str  # 필수 필드
    weather_conditions: str | None = None  # 선택적 필드
```

**역할:** LLM의 자유 텍스트 응답을 구조화된 데이터로 변환

**Before (응답 형식 없음):**

```python
response = agent.invoke(...)
# 반환값: "Florida is sunny! It's 75 degrees and perfect beach weather!"

# 문제: 어떻게 "75"를 추출하지? 어떻게 "sunny"를 파싱하지?
temperature = extract_temperature(response)  # 복잡한 정규식 필요
```

**After (응답 형식 사용):**

```python
@dataclass
class ResponseFormat:
    punny_response: str
    weather_conditions: str | None = None

response = agent.invoke(...)['structured_response']
# ResponseFormat(
#     punny_response="Florida is having a sun-derful day!",
#     weather_conditions="It's always sunny in Florida!"
# )

# 바로 사용 가능!
print(response.weather_conditions)  # "It's always sunny in Florida!"
if response.weather_conditions:
    display_weather_widget(response.weather_conditions)
```

**실전 응답 형식 예시:**

```python
from typing import Literal

@dataclass
class CustomerSupportResponse:
    """고객 지원 응답 형식"""
    # 문의 분류
    category: Literal["technical", "billing", "shipping", "general"]

    # 긴급도
    urgency: Literal["low", "medium", "high", "critical"]

    # 고객에게 보낼 응답
    response_text: str

    # 권장 조치 사항
    suggested_actions: list[str]

    # 사람 개입 필요 여부
    requires_human: bool

    # 예상 해결 시간 (시간 단위)
    estimated_resolution_hours: int | None = None

# 사용
agent = create_agent(
    model=model,
    tools=[search_kb, check_order_status, refund_policy],
    response_format=CustomerSupportResponse
)

response = agent.invoke(...)['structured_response']

# 자동 라우팅
if response.requires_human or response.urgency == "critical":
    assign_to_human_agent(response)
    send_slack_notification(f"긴급: {response.category}")
else:
    send_automated_response(response.response_text)
    create_ticket(
        category=response.category,
        actions=response.suggested_actions,
        eta=response.estimated_resolution_hours
    )
```

**Java DTO와 비교:**

```java
// Java의 DTO와 동일한 역할
public class WeatherResponse {
    private String punnyResponse;    // 필수
    private String weatherConditions; // 선택

    // Lombok 사용
    @Data
    @Builder
    public class WeatherResponse {
        @NonNull
        private String punnyResponse;

        @Nullable
        private String weatherConditions;
    }
}
```

### 3.6 메모리 (Checkpointer)

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
```

**역할:** 대화 기록(메시지, 상태)을 저장하고 불러오기

**Checkpointer 종류:**

```python
# 1. InMemorySaver - 메모리에 저장 (휘발성)
# 용도: 개발/테스트, 프로토타입
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()

# 2. SqliteSaver - SQLite에 저장 (영구)
# 용도: 소규모 프로덕션, 로컬 앱
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("chat_history.db")

# 3. PostgresSaver - PostgreSQL에 저장 (영구)
# 용도: 대규모 프로덕션
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/chatdb"
)

# 4. RedisSaver - Redis에 저장 (빠른 접근)
# 용도: 고성능 실시간 챗봇
from langgraph.checkpoint.redis import RedisSaver
checkpointer = RedisSaver.from_conn_string("redis://localhost:6379/0")
```

**대화 저장 방식:**

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Checkpointer
    participant LLM

    Note over User,LLM: 첫 번째 메시지
    User->>Agent: 날씨 알려줘 (thread_id=1)
    Agent->>Checkpointer: load(thread_id=1)
    Checkpointer-->>Agent: [] 빈 히스토리

    Agent->>LLM: [user: 날씨 알려줘]
    LLM-->>Agent: Florida는 맑습니다

    Agent->>Checkpointer: save(thread_id=1, messages)
    Note over Checkpointer: [user: 날씨 알려줘<br/>assistant: Florida는 맑습니다]

    Note over User,LLM: 두 번째 메시지
    User->>Agent: 고마워 (thread_id=1)
    Agent->>Checkpointer: load(thread_id=1)
    Checkpointer-->>Agent: [이전 대화 2개]

    Agent->>LLM: [user: 날씨 알려줘<br/>assistant: 맑습니다<br/>user: 고마워]
    LLM-->>Agent: 천만에요! 좋은 하루 되세요

    Agent->>Checkpointer: save(thread_id=1, messages)
    Note over Checkpointer: 4개 메시지 저장
```

**실전 활용:**

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 영구 저장소
checkpointer = SqliteSaver.from_conn_string("chat_history.db")

agent = create_agent(
    model=model,
    tools=tools,
    checkpointer=checkpointer
)

# 사용자별 대화 관리
def chat_with_user(user_id: str, message: str):
    # 사용자마다 별도의 thread_id
    config = {"configurable": {"thread_id": f"user_{user_id}"}}

    response = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        context=Context(user_id=user_id)
    )

    return response['structured_response']

# User A와 대화
chat_with_user("alice", "날씨 알려줘")
# → thread_id: user_alice, 대화 시작

chat_with_user("alice", "고마워")
# → thread_id: user_alice, 이전 대화 기억

# User B와 대화 (완전히 별도)
chat_with_user("bob", "안녕")
# → thread_id: user_bob, 새로운 대화

# 나중에 Alice가 다시 접속해도 대화 이어짐
chat_with_user("alice", "어제 날씨 얘기 했었는데...")
# → thread_id: user_alice, 이전 대화 모두 로드됨
```

**대화 기록 조회:**

```python
# 특정 thread의 전체 대화 기록 조회
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("chat_history.db")

# 대화 기록 가져오기
thread_id = "user_alice"
config = {"configurable": {"thread_id": thread_id}}

# 저장된 상태 확인
state = checkpointer.get(config)
if state:
    for message in state['messages']:
        print(f"{message['role']}: {message['content']}")
```

### 3.7 Agent 생성

```python
agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)
```

**파라미터 정리:**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `model` | ChatModel | ✅ | LLM 모델 |
| `system_prompt` | str | ✅ | Agent의 역할과 지침 |
| `tools` | list[Tool] | ✅ | 사용 가능한 도구 목록 |
| `context_schema` | Type | ❌ | 런타임 컨텍스트 스키마 |
| `response_format` | Type | ❌ | 응답 형식 지정 |
| `checkpointer` | Checkpointer | ❌ | 대화 저장소 |

**Java Spring Boot와 비교:**

```java
// Spring Boot의 빈 설정과 유사
@Configuration
public class AgentConfig {

    @Bean
    public Agent weatherAgent(
        ChatModel model,              // model
        @Value("${prompt}") String systemPrompt,  // system_prompt
        List<Tool> tools,             // tools
        Checkpointer checkpointer     // checkpointer
    ) {
        return Agent.builder()
            .model(model)
            .systemPrompt(systemPrompt)
            .tools(tools)
            .contextSchema(Context.class)
            .responseFormat(ResponseFormat.class)
            .checkpointer(checkpointer)
            .build();
    }
}
```

### 3.8 Agent 실행

```python
config = {"configurable": {"thread_id": "1"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather outside?"}]},
    config=config,
    context=Context(user_id="1")
)
```

**파라미터 설명:**

1. **messages**: 대화 메시지 목록
   ```python
   {
       "messages": [
           {"role": "user", "content": "what is the weather outside?"}
       ]
   }
   ```

2. **config**: 설정 (thread_id로 대화 구분)
   ```python
   {"configurable": {"thread_id": "1"}}
   ```

3. **context**: 런타임 컨텍스트 (도구에 전달)
   ```python
   Context(user_id="1")
   ```

**응답 구조:**

```python
response = {
    'messages': [
        {'role': 'user', 'content': 'what is the weather outside?'},
        {'role': 'assistant', 'content': '...'},
        # 도구 호출 메시지들...
    ],
    'structured_response': ResponseFormat(
        punny_response="Florida is having a 'sun-derful' day!...",
        weather_conditions="It's always sunny in Florida!"
    )
}

# 구조화된 응답만 사용
result = response['structured_response']
print(result.punny_response)
print(result.weather_conditions)
```

### 3.9 대화 이어가기

```python
# 같은 thread_id 사용
response = agent.invoke(
    {"messages": [{"role": "user", "content": "thank you!"}]},
    config=config,  # 같은 thread_id="1"
    context=Context(user_id="1")
)

print(response['structured_response'])
# ResponseFormat(
#     punny_response="You're 'thund-erfully' welcome!...",
#     weather_conditions=None  # 이번엔 날씨 정보 없음
# )
```

**대화 흐름:**

```mermaid
graph TB
    subgraph "첫 번째 메시지"
        M1[User: 날씨 질문]
        M2[Agent: get_user_location 호출]
        M3[Tool: Florida 반환]
        M4[Agent: get_weather_for_location 호출]
        M5[Tool: 날씨 정보 반환]
        M6[Agent: 응답 생성]
    end

    subgraph "두 번째 메시지 같은 thread_id"
        M7[User: 감사 인사]
        M8[Agent: 이전 대화 로드]
        M9[Agent: 도구 불필요 판단]
        M10[Agent: 감사 응답 생성]
    end

    M1 --> M2 --> M3 --> M4 --> M5 --> M6
    M6 -.저장.-> M7
    M7 --> M8 --> M9 --> M10

    style M8 fill:#FF9800,color:#fff
```

## 4. Agent 실행 과정 상세 분석

### 4.1 Agent 내부 동작

```mermaid
sequenceDiagram
    participant U as User
    participant A as Agent
    participant C as Checkpointer
    participant L as LLM
    participant T as Tools

    U->>A: invoke(message, config, context)

    Note over A: Step 1: 대화 기록 로드
    A->>C: load(thread_id)
    C-->>A: 이전 메시지들

    Note over A: Step 2: LLM에 전달
    A->>L: [시스템 프롬프트 + 대화 기록 + 새 메시지]
    L-->>A: get_user_location 호출 필요

    Note over A: Step 3: 도구 실행
    A->>T: get_user_location(runtime.context)
    Note over T: context.user_id = 1
    T-->>A: Florida 반환

    Note over A: Step 4: 도구 결과를 LLM에 전달
    A->>L: [대화 + 도구 결과]
    L-->>A: get_weather_for_location 호출 필요

    A->>T: get_weather_for_location(Florida)
    T-->>A: 날씨 정보 반환

    Note over A: Step 5: 최종 응답 생성
    A->>L: [전체 대화 + 모든 도구 결과]
    L-->>A: 자유 텍스트 응답

    Note over A: Step 6: 응답 구조화
    A->>A: ResponseFormat으로 변환

    Note over A: Step 7: 대화 저장
    A->>C: save(thread_id, 모든 메시지)

    A-->>U: structured_response 반환
```

### 4.2 실제 메시지 흐름

```python
# Agent가 내부적으로 관리하는 메시지 목록

messages = [
    # 1. 시스템 프롬프트
    {
        "role": "system",
        "content": "You are an expert weather forecaster, who speaks in puns..."
    },

    # 2. 사용자 메시지
    {
        "role": "user",
        "content": "what is the weather outside?"
    },

    # 3. Agent의 도구 호출 결정
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "get_user_location",
                    "arguments": "{}"
                }
            }
        ]
    },

    # 4. 도구 실행 결과
    {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": "Florida"
    },

    # 5. Agent의 두 번째 도구 호출
    {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "call_2",
                "type": "function",
                "function": {
                    "name": "get_weather_for_location",
                    "arguments": '{"city": "Florida"}'
                }
            }
        ]
    },

    # 6. 두 번째 도구 실행 결과
    {
        "role": "tool",
        "tool_call_id": "call_2",
        "content": "It's always sunny in Florida!"
    },

    # 7. 최종 응답
    {
        "role": "assistant",
        "content": {
            "punny_response": "Florida is having a 'sun-derful' day!...",
            "weather_conditions": "It's always sunny in Florida!"
        }
    }
]
```

## 5. 실전 활용 예제

### 5.1 고객 지원 챗봇

```python
from dataclasses import dataclass
from typing import Literal
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.sqlite import SqliteSaver

# Context 정의
@dataclass
class CustomerContext:
    user_id: str
    session_id: str
    subscription_tier: Literal["free", "pro", "enterprise"]
    language: str

# 응답 형식
@dataclass
class SupportResponse:
    category: Literal["technical", "billing", "shipping", "general"]
    urgency: Literal["low", "medium", "high", "critical"]
    response_text: str
    suggested_actions: list[str]
    requires_human: bool
    estimated_resolution_hours: int | None = None

# 도구 정의
@tool
def search_knowledge_base(query: str, runtime: ToolRuntime[CustomerContext]) -> str:
    """지식 베이스에서 답변 검색"""
    lang = runtime.context.language
    # DB 검색 로직
    return f"검색 결과: {query} (언어: {lang})"

@tool
def check_order_status(order_id: str, runtime: ToolRuntime[CustomerContext]) -> str:
    """주문 상태 확인"""
    user_id = runtime.context.user_id
    # 주문 조회 로직
    return f"주문 #{order_id} 상태: 배송 중 (사용자: {user_id})"

@tool
def get_refund_policy(runtime: ToolRuntime[CustomerContext]) -> str:
    """환불 정책 조회 (등급별)"""
    tier = runtime.context.subscription_tier
    policies = {
        "free": "14일 이내 전액 환불",
        "pro": "30일 이내 전액 환불",
        "enterprise": "협의 가능"
    }
    return policies[tier]

# Agent 생성
model = init_chat_model("anthropic:claude-sonnet-4-5", temperature=0)
checkpointer = SqliteSaver.from_conn_string("support_chats.db")

SYSTEM_PROMPT = """당신은 전문 고객 지원 상담원입니다.

고객의 문의를 분류하고, 적절한 도구를 사용하여 답변하세요.
긴급한 문제는 즉시 사람 상담원에게 연결해야 합니다.

사용 가능한 도구:
- search_knowledge_base: 지식 베이스 검색
- check_order_status: 주문 상태 확인
- get_refund_policy: 환불 정책 조회
"""

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[search_knowledge_base, check_order_status, get_refund_policy],
    context_schema=CustomerContext,
    response_format=SupportResponse,
    checkpointer=checkpointer
)

# 사용 예시
def handle_customer_inquiry(user_id: str, message: str, tier: str, lang: str):
    config = {"configurable": {"thread_id": f"customer_{user_id}"}}
    context = CustomerContext(
        user_id=user_id,
        session_id=f"session_{user_id}_{int(time.time())}",
        subscription_tier=tier,
        language=lang
    )

    response = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        context=context
    )

    result = response['structured_response']

    # 자동 라우팅
    if result.requires_human or result.urgency == "critical":
        assign_to_human_agent(user_id, result)
        send_notification(f"긴급 문의: {result.category}")
    else:
        send_automated_response(user_id, result.response_text)

    return result

# 사용
result = handle_customer_inquiry(
    user_id="user123",
    message="주문 #12345가 언제 도착하나요?",
    tier="pro",
    lang="ko"
)

print(result.category)  # "shipping"
print(result.urgency)   # "medium"
print(result.response_text)
```

### 5.2 데이터 분석 어시스턴트

```python
from dataclasses import dataclass
from typing import Literal
import pandas as pd

@dataclass
class AnalysisContext:
    user_id: str
    allowed_tables: list[str]  # 접근 가능한 테이블
    max_rows: int              # 최대 조회 행 수

@dataclass
class AnalysisResponse:
    query_used: str            # 실행한 SQL 쿼리
    summary: str               # 분석 요약
    visualization_type: Literal["bar", "line", "pie", "table", "none"]
    data: dict | None = None   # 시각화 데이터
    insights: list[str] = None # 인사이트 목록

@tool
def query_database(sql: str, runtime: ToolRuntime[AnalysisContext]) -> str:
    """SQL 쿼리 실행"""
    allowed_tables = runtime.context.allowed_tables
    max_rows = runtime.context.max_rows

    # 테이블 접근 권한 확인
    # SQL 실행 및 결과 반환
    df = pd.read_sql(sql, connection, params={"limit": max_rows})
    return df.to_json()

@tool
def calculate_statistics(column: str, operation: str, runtime: ToolRuntime[AnalysisContext]) -> str:
    """통계 계산"""
    # 평균, 합계, 최대, 최소 등 계산
    return f"{operation}({column}) = 결과"

# Agent 생성
SYSTEM_PROMPT = """당신은 데이터 분석 전문가입니다.

사용자의 질문을 분석하여 적절한 SQL 쿼리를 생성하고,
결과를 해석하여 인사이트를 제공하세요.

사용 가능한 도구:
- query_database: SQL 쿼리 실행
- calculate_statistics: 통계 계산
"""

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[query_database, calculate_statistics],
    context_schema=AnalysisContext,
    response_format=AnalysisResponse,
    checkpointer=checkpointer
)

# 사용
def analyze_data(user_id: str, question: str):
    context = AnalysisContext(
        user_id=user_id,
        allowed_tables=["sales", "customers", "products"],
        max_rows=1000
    )

    config = {"configurable": {"thread_id": f"analysis_{user_id}"}}

    response = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
        context=context
    )

    return response['structured_response']

# 사용 예시
result = analyze_data(
    user_id="analyst001",
    question="지난 달 매출이 가장 높은 상위 10개 제품은?"
)

print(result.query_used)  # "SELECT product_name, SUM(sales) ..."
print(result.summary)     # "지난 달 매출 상위 10개 제품 분석 결과..."
print(result.visualization_type)  # "bar"
print(result.insights)    # ["Product A가 전체 매출의 30% 차지", ...]
```

### 5.3 코드 리뷰 어시스턴트

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class CodeReviewContext:
    repository: str
    branch: str
    reviewer_id: str
    language: Literal["python", "java", "javascript", "typescript"]

@dataclass
class CodeReviewResponse:
    severity: Literal["info", "warning", "error", "critical"]
    issues: list[dict]  # [{"line": 10, "issue": "...", "suggestion": "..."}]
    security_concerns: list[str]
    performance_tips: list[str]
    code_quality_score: int  # 0-100
    approval_status: Literal["approved", "needs_changes", "rejected"]

@tool
def analyze_code_quality(code: str, runtime: ToolRuntime[CodeReviewContext]) -> str:
    """코드 품질 분석"""
    lang = runtime.context.language
    # Pylint, ESLint 등 실행
    return "분석 결과..."

@tool
def check_security_vulnerabilities(code: str, runtime: ToolRuntime[CodeReviewContext]) -> str:
    """보안 취약점 검사"""
    # Bandit, SonarQube 등 실행
    return "보안 검사 결과..."

@tool
def suggest_improvements(code: str, runtime: ToolRuntime[CodeReviewContext]) -> str:
    """개선 제안"""
    # 리팩토링 제안
    return "개선 제안..."

# Agent 생성 및 사용
agent = create_agent(
    model=model,
    system_prompt="당신은 시니어 코드 리뷰어입니다...",
    tools=[analyze_code_quality, check_security_vulnerabilities, suggest_improvements],
    context_schema=CodeReviewContext,
    response_format=CodeReviewResponse,
    checkpointer=checkpointer
)

def review_code(repo: str, branch: str, code: str, language: str):
    context = CodeReviewContext(
        repository=repo,
        branch=branch,
        reviewer_id="bot",
        language=language
    )

    response = agent.invoke(
        {"messages": [{"role": "user", "content": f"다음 코드를 리뷰해주세요:\n\n{code}"}]},
        config={"configurable": {"thread_id": f"review_{repo}_{branch}"}},
        context=context
    )

    return response['structured_response']
```

## 6. 고급 기능

### 6.1 스트리밍 응답

```python
# 실시간 응답 스트리밍
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "긴 설명이 필요한 질문"}]},
    config=config,
    context=context
):
    if 'structured_response' in chunk:
        print(chunk['structured_response'].punny_response, end='', flush=True)
```

### 6.2 비동기 실행

```python
import asyncio

async def chat_async(message: str):
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config,
        context=context
    )
    return response['structured_response']

# 사용
result = asyncio.run(chat_async("날씨 알려줘"))
```

### 6.3 다중 도구 체인

```python
@tool
def step1_fetch_data(query: str) -> str:
    """1단계: 데이터 가져오기"""
    return "데이터..."

@tool
def step2_process_data(data: str) -> str:
    """2단계: 데이터 처리"""
    return "처리된 데이터..."

@tool
def step3_generate_report(processed_data: str) -> str:
    """3단계: 보고서 생성"""
    return "보고서..."

# Agent가 자동으로 step1 → step2 → step3 순서로 실행
agent = create_agent(
    model=model,
    tools=[step1_fetch_data, step2_process_data, step3_generate_report],
    ...
)
```

## 7. 디버깅 및 모니터링

### 7.1 로깅 활성화

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# LangChain 로그 확인
logger = logging.getLogger("langchain")
logger.setLevel(logging.DEBUG)
```

### 7.2 콜백으로 모니터링

```python
from langchain.callbacks import StdOutCallbackHandler

response = agent.invoke(
    {"messages": [...]},
    config={
        "configurable": {"thread_id": "1"},
        "callbacks": [StdOutCallbackHandler()]  # 실행 과정 출력
    },
    context=context
)
```

### 7.3 메시지 히스토리 확인

```python
# 전체 메시지 확인
all_messages = response['messages']
for msg in all_messages:
    print(f"{msg['role']}: {msg.get('content', msg.get('tool_calls', ''))}")
```

## 8. 베스트 프랙티스

### ✅ Do's

1. **명확한 시스템 프롬프트 작성**
   ```python
   SYSTEM_PROMPT = """
   역할: 당신은 [역할 설명]입니다.

   목표: [목표 설명]

   사용 가능한 도구:
   - tool1: [언제 사용하는지]
   - tool2: [언제 사용하는지]

   제약사항:
   - [제약 1]
   - [제약 2]
   """
   ```

2. **도구 함수에 상세한 docstring**
   ```python
   @tool
   def get_weather(city: str) -> str:
       """
       특정 도시의 현재 날씨 정보를 반환합니다.

       Args:
           city: 도시 이름 (예: "Seoul", "New York")

       Returns:
           날씨 정보 문자열
       """
   ```

3. **응답 형식에 명확한 필드명 사용**
   ```python
   @dataclass
   class Response:
       user_friendly_message: str  # 사용자에게 보여줄 메시지
       technical_details: str | None  # 기술적 세부사항
   ```

4. **프로덕션에서는 영구 저장소 사용**
   ```python
   # ❌ InMemorySaver (개발용)
   # ✅ SqliteSaver, PostgresSaver (프로덕션)
   checkpointer = SqliteSaver.from_conn_string("prod.db")
   ```

### ❌ Don'ts

1. **너무 많은 도구 한 번에 제공**
   ```python
   # ❌ 나쁜 예: 도구 20개
   agent = create_agent(tools=[tool1, tool2, ..., tool20])

   # ✅ 좋은 예: 관련 도구만 5-7개
   agent = create_agent(tools=[related_tool1, related_tool2, ...])
   ```

2. **Context에 민감한 정보 직접 포함**
   ```python
   # ❌ 나쁜 예
   @dataclass
   class Context:
       password: str  # 절대 안 됨!

   # ✅ 좋은 예
   @dataclass
   class Context:
       user_id: str  # ID만 전달, 실제 데이터는 도구에서 조회
   ```

3. **Temperature를 너무 높게 설정**
   ```python
   # ❌ 도구 호출 시 일관성 없음
   model = init_chat_model("...", temperature=1.0)

   # ✅ 도구 호출은 temperature 낮게
   model = init_chat_model("...", temperature=0-0.3)
   ```

## 9. 트러블슈팅

### 문제 1: 도구가 호출되지 않음

**증상:** Agent가 도구를 사용하지 않고 "모르겠습니다" 응답

**해결:**
```python
# 시스템 프롬프트에 도구 사용 명시
SYSTEM_PROMPT = """
...
중요: 사용자가 날씨를 물어보면 반드시 get_weather_for_location 도구를 사용하세요.
추측하지 말고 도구로 확인하세요.
"""
```

### 문제 2: Context가 도구에 전달되지 않음

**증상:** `runtime.context.user_id` 접근 시 에러

**해결:**
```python
# 1. 도구 함수 시그니처 확인
@tool
def my_tool(runtime: ToolRuntime[Context]) -> str:  # ✅ ToolRuntime 사용
    user_id = runtime.context.user_id

# 2. invoke 시 context 전달 확인
agent.invoke(..., context=Context(user_id="1"))  # ✅ context 전달
```

### 문제 3: 응답이 구조화되지 않음

**증상:** `response['structured_response']` KeyError

**해결:**
```python
# response_format을 ToolStrategy로 감싸기
from langchain.agents.structured_output import ToolStrategy

agent = create_agent(
    ...
    response_format=ToolStrategy(ResponseFormat)  # ✅ ToolStrategy 사용
)
```

### 문제 4: 대화 기록이 저장되지 않음

**증상:** 이전 대화를 기억하지 못함

**해결:**
```python
# 1. checkpointer 확인
checkpointer = InMemorySaver()  # ✅ 생성 확인

# 2. agent에 연결 확인
agent = create_agent(..., checkpointer=checkpointer)  # ✅

# 3. 같은 thread_id 사용 확인
config = {"configurable": {"thread_id": "same_id"}}  # ✅ 동일한 ID
```

## Java 개발자를 위한 비교

| LangChain 개념 | Java/Spring 유사 개념 | 설명 |
|---------------|---------------------|------|
| `Agent` | `@Service` Bean | 비즈니스 로직 처리 컴포넌트 |
| `Tool` | `@Component` 메서드 | 재사용 가능한 기능 단위 |
| `Context` | `@Autowired` 의존성 | 런타임 정보 주입 |
| `ResponseFormat` | DTO (Data Transfer Object) | 응답 데이터 구조 |
| `Checkpointer` | `HttpSession`, Redis | 상태 저장소 |
| `thread_id` | Session ID | 대화/세션 식별자 |
| `@tool` 데코레이터 | `@Component` 애노테이션 | 컴포넌트 등록 |

```java
// Java Spring Boot 유사 코드
@Service
public class WeatherAgent {

    @Autowired
    private WeatherService weatherService;  // = Tool

    @Autowired
    private LocationService locationService;  // = Tool

    @Autowired
    private HttpSession session;  // = Checkpointer

    public WeatherResponse getWeather(
        String message,
        UserContext context  // = Context
    ) {
        // 세션에서 이전 대화 로드
        List<Message> history = (List<Message>) session.getAttribute("messages");

        // LLM 호출 (생략)

        // 도구 호출
        String location = locationService.getUserLocation(context.getUserId());
        String weather = weatherService.getWeather(location);

        // 응답 생성
        WeatherResponse response = new WeatherResponse(
            "It's sunny!",
            weather
        );

        // 세션에 저장
        session.setAttribute("messages", updatedHistory);

        return response;
    }
}

@Data
public class WeatherResponse {  // = ResponseFormat
    private String punnyResponse;
    private String weatherConditions;
}
```

## 출처

- [LangChain Documentation - Quickstart](https://docs.langchain.com/oss/python/langchain/quickstart)
- [LangChain API Reference - create_agent](https://python.langchain.com/api_reference/langchain/agents/langchain.agents.create_agent.html)
- [LangGraph Checkpointer Documentation](https://langchain-ai.github.io/langgraph/reference/checkpoints/)
