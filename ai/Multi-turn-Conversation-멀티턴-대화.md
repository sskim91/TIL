# Multi-turn Conversation (멀티턴 대화)

LLM에서 Multi-turn이란 무엇인지 알아봅니다.

## 정의

**Multi-turn**: LLM과의 여러 번의 왕복 대화 (대화 맥락을 유지하며 이어지는 대화)

## Single-turn vs Multi-turn

### Single-turn (단일 턴)

한 번의 질문 → 한 번의 답변으로 끝

```
User: "Python에서 리스트를 정렬하는 방법은?"
AI: "list.sort() 또는 sorted(list)를 사용하세요."
[대화 종료]
```

**특징:**
- 독립적인 질문-답변
- 이전 대화 기억 안함
- 단순하고 빠름

### Multi-turn (멀티 턴)

여러 번의 질문과 답변이 이어짐

```
User: "Python에서 리스트를 정렬하는 방법은?"
AI: "list.sort() 또는 sorted(list)를 사용하세요."

User: "둘의 차이는 뭐야?"  ← 이전 대화를 기억
AI: "sort()는 원본을 변경하고, sorted()는 새 리스트를 반환합니다."

User: "역순으로 하려면?"  ← 여전히 맥락 유지
AI: "reverse=True 파라미터를 추가하세요."
```

**특징:**
- 연속된 대화
- 이전 맥락 기억
- 자연스러운 대화 가능

## 비교표

| 구분 | Single-turn | Multi-turn |
|------|------------|-----------|
| **대화 횟수** | 1회 질문-답변 | 여러 번 왕복 |
| **맥락 유지** | ❌ 없음 | ✅ 이전 대화 기억 |
| **구현 복잡도** | 낮음 | 높음 (히스토리 관리) |
| **비용** | 낮음 | 높음 (전체 대화 전송) |
| **사용 예시** | 검색, 번역, 분류 | 챗봇, 상담, 튜터링 |

## LangChain 구현 예시

### 기본 패턴

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

# LLM 초기화
llm = ChatOpenAI(model="gpt-4", temperature=0)

# 대화 히스토리 저장
messages = []

# Turn 1
messages.append(HumanMessage(content="Python이 뭐야?"))
response = llm.invoke(messages)
messages.append(response)
print(response.content)

# Turn 2 - 이전 대화 맥락 유지
messages.append(HumanMessage(content="어디에 쓰여?"))  # "Python"을 기억
response = llm.invoke(messages)
messages.append(response)
print(response.content)

# Turn 3
messages.append(HumanMessage(content="배우기 어려워?"))
response = llm.invoke(messages)
messages.append(response)
print(response.content)
```

### ConversationChain 사용

```python
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

# 메모리 설정 (대화 히스토리 자동 관리)
memory = ConversationBufferMemory()

# 대화 체인 생성
conversation = ConversationChain(
    llm=ChatOpenAI(model="gpt-4"),
    memory=memory,
    verbose=True  # 대화 히스토리 출력
)

# 대화 진행 (자동으로 맥락 유지)
conversation.predict(input="Python이 뭐야?")
conversation.predict(input="어디에 쓰여?")  # Python을 기억
conversation.predict(input="배우기 어려워?")  # 여전히 Python 얘기

# 대화 히스토리 확인
print(memory.load_memory_variables({}))
```

### 메모리 관리 전략

LangChain은 다양한 메모리 관리 전략을 제공합니다:

#### 1. ConversationBufferMemory

전체 대화를 그대로 저장:

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
```

- ✅ 모든 대화 내용 보존
- ❌ 메모리 많이 사용
- **사용 시기**: 짧은 대화, 모든 맥락이 중요한 경우

#### 2. ConversationBufferWindowMemory

최근 N개 턴만 유지:

```python
from langchain.memory import ConversationBufferWindowMemory

# 최근 5턴만 저장
memory = ConversationBufferWindowMemory(k=5)
```

- ✅ 메모리 사용량 제한
- ❌ 오래된 대화 손실
- **사용 시기**: 최근 맥락만 중요한 경우

#### 3. ConversationSummaryMemory

대화를 요약해서 저장:

```python
from langchain.memory import ConversationSummaryMemory
from langchain_openai import ChatOpenAI

memory = ConversationSummaryMemory(
    llm=ChatOpenAI(model="gpt-4")
)
```

- ✅ 긴 대화도 압축 가능
- ❌ 요약 과정에서 정보 손실
- ❌ 요약에 추가 비용 발생
- **사용 시기**: 매우 긴 대화, 핵심만 필요한 경우

#### 4. ConversationSummaryBufferMemory

요약 + 최근 대화 조합:

```python
from langchain.memory import ConversationSummaryBufferMemory

# 토큰 제한 내에서 최근 대화 유지, 나머지는 요약
memory = ConversationSummaryBufferMemory(
    llm=ChatOpenAI(model="gpt-4"),
    max_token_limit=2000
)
```

- ✅ 최근 대화는 상세히, 오래된 것은 요약
- ✅ 균형잡힌 접근
- **사용 시기**: 긴 대화에서 최근 맥락이 중요한 경우

#### 5. ConversationTokenBufferMemory

토큰 수로 관리:

```python
from langchain.memory import ConversationTokenBufferMemory

# 최대 2000 토큰까지만 저장
memory = ConversationTokenBufferMemory(
    llm=ChatOpenAI(model="gpt-4"),
    max_token_limit=2000
)
```

- ✅ 토큰 제한 정확히 관리
- **사용 시기**: 토큰 비용 제어가 중요한 경우

#### 6. ConversationKGMemory

지식 그래프로 관리:

```python
from langchain.memory import ConversationKGMemory

memory = ConversationKGMemory(
    llm=ChatOpenAI(model="gpt-4")
)
```

- ✅ 엔티티 간 관계 추적
- ❌ 설정 복잡
- **사용 시기**: 복잡한 관계 정보가 중요한 경우

#### 7. VectorStoreRetrieverMemory

벡터 DB로 검색:

```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

vectorstore = Chroma(embedding_function=OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

memory = VectorStoreRetrieverMemory(retriever=retriever)
```

- ✅ 의미적으로 관련된 과거 대화 검색
- ✅ 매우 긴 대화 히스토리 가능
- **사용 시기**: 특정 주제 관련 과거 대화 참조가 필요한 경우

### 메모리 선택 가이드

| Memory 타입 | 대화 길이 | 비용 | 복잡도 | 추천 상황 |
|------------|----------|------|--------|---------|
| BufferMemory | 짧음 | 낮음 | 낮음 | 단순 챗봇 |
| BufferWindowMemory | 중간 | 낮음 | 낮음 | 일반 상담 |
| SummaryMemory | 긺 | 높음 | 중간 | 긴 상담 세션 |
| SummaryBufferMemory | 긺 | 중간 | 중간 | 균형잡힌 접근 |
| TokenBufferMemory | 중간 | 중간 | 중간 | 비용 제어 |
| KGMemory | 긺 | 높음 | 높음 | 복잡한 관계 |
| VectorStoreMemory | 매우 긺 | 높음 | 높음 | 의미 검색 필요 |

**더 자세한 내용은 [LangChain Memory 공식 문서](https://python.langchain.com/docs/modules/memory/types/) 참조**

## 실제 활용 사례

### Multi-turn이 필요한 경우

**1. 고객 상담 챗봇**
```
User: "환불하고 싶어요"
Bot: "네, 주문번호를 알려주세요"
User: "1234입니다"  ← "환불" 맥락 유지
Bot: "1234 주문 확인했습니다. 환불 사유는?"
User: "사이즈가 안 맞아요"
Bot: "알겠습니다. 환불 처리하겠습니다"
```

**2. 코딩 튜터**
```
User: "for 문 사용법 알려줘"
AI: [for 문 설명]
User: "예제 보여줘"  ← for 문 맥락 유지
AI: [for 문 예제]
User: "range는 뭐야?"  ← 여전히 for 문 맥락
AI: [range 설명]
```

**3. 개인 비서**
```
User: "내일 일정 알려줘"
AI: [내일 일정 출력]
User: "오후 3시에 회의 추가해줘"  ← "내일" 기억
AI: "내일 오후 3시 회의 추가했습니다"
User: "그 전에 점심 약속도 넣어줘"  ← "내일" 여전히 유지
AI: "내일 점심 약속 추가했습니다"
```

### Single-turn으로 충분한 경우

- 검색 엔진 (독립적인 검색)
- 번역 서비스 (문장별 번역)
- 텍스트 분류 (감성 분석 등)
- 문서 요약 (한 번에 요약)

## Multi-turn의 도전 과제

### 1. 토큰 제한

대화가 길어지면 토큰 한계 도달:

```python
# 문제: 100턴 대화 → 수만 토큰
messages = [...]  # 100개 메시지

# 해결책 1: 최근 N턴만 유지
messages = messages[-10:]

# 해결책 2: 요약
summary = summarize_conversation(messages[:-5])
messages = [summary] + messages[-5:]
```

### 2. 비용

매 요청마다 전체 대화 히스토리 전송:

```
Turn 1: 100 토큰
Turn 2: 100 + 150 = 250 토큰
Turn 3: 250 + 200 = 450 토큰
...
Turn 10: 수천 토큰 (비용 증가)
```

**해결책:**
- 요약 사용
- 중요한 부분만 유지
- 세션 타임아웃 설정

### 3. 맥락 추적

LLM이 먼 과거 대화를 잊어버릴 수 있음:

```
Turn 1: "내 이름은 홍길동이야"
...
Turn 50: "내 이름이 뭐였지?"
AI: [잊어버릴 수 있음]
```

**해결책:**
- 중요 정보는 시스템 프롬프트에 저장
- 메타데이터 별도 관리

## 구현 팁

### 1. 세션 관리

```python
# 사용자별 대화 히스토리 분리
user_sessions = {}

def get_or_create_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "messages": [],
            "created_at": datetime.now()
        }
    return user_sessions[user_id]
```

### 2. 타임아웃 설정

```python
# 30분 이상 대화 없으면 초기화
SESSION_TIMEOUT = 1800  # 30분

def is_session_expired(session):
    elapsed = (datetime.now() - session["last_activity"]).seconds
    return elapsed > SESSION_TIMEOUT
```

### 3. 컨텍스트 윈도우 관리

```python
MAX_MESSAGES = 20  # 최대 20개 메시지만 유지

def add_message(session, message):
    session["messages"].append(message)

    # 오래된 메시지 제거
    if len(session["messages"]) > MAX_MESSAGES:
        session["messages"] = session["messages"][-MAX_MESSAGES:]
```


## 요약

### Multi-turn이란?

여러 번의 왕복 대화를 통해 **맥락을 유지**하며 자연스러운 대화를 하는 방식

### 핵심 차이

| 항목 | 내용 |
|------|------|
| **Single-turn** | 독립적인 1회 질문-답변 |
| **Multi-turn** | 맥락 유지하며 연속 대화 |

### LangChain 구현

```python
# 기본: 메시지 히스토리 직접 관리
messages = []
messages.append(HumanMessage(content="질문"))
response = llm.invoke(messages)

# 편리: ConversationChain 사용
conversation = ConversationChain(
    llm=llm,
    memory=ConversationBufferMemory()
)
conversation.predict(input="질문")
```

### 주의사항

- ⚠️ 토큰 제한 (긴 대화)
- ⚠️ 비용 증가 (전체 히스토리 전송)
- ⚠️ 메모리 관리 필요

## 참고 자료

### LangChain 문서

- [ConversationBufferMemory API](https://python.langchain.com/api_reference/langchain/memory/langchain.memory.buffer.ConversationBufferMemory.html)
- [LangChain Memory (v0.1)](https://python.langchain.com/v0.1/docs/modules/memory/types/buffer/)
- [LangGraph Short-term Memory](https://docs.langchain.com/oss/python/langchain/short-term-memory) (최신 권장 방식)

### LLM Provider 문서

- [OpenAI - Chat Completions](https://platform.openai.com/docs/guides/chat-completions)
- [Anthropic - Claude Conversations](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)

### 튜토리얼

- [Pinecone - LangChain Conversational Memory](https://www.pinecone.io/learn/series/langchain/langchain-conversational-memory/)
- [Analytics Vidhya - LangChain Memory Guide](https://www.analyticsvidhya.com/blog/2024/11/langchain-memory/)
