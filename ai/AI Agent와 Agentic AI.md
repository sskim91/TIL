# AI Agent와 Agentic AI

AI Agent의 개념, 역사, 그리고 왜 지금 "Agent 시대"라고 불리는지 완전히 이해하기

## 결론부터 말하면

**AI Agent = 스스로 생각하고(Reasoning) + 행동하며(Acting) + 도구를 사용해(Tool Use) 목표를 달성하는 AI 시스템**

```python
# ❌ 전통적인 LLM (단순 대화)
response = llm.generate("날씨 어때?")
# "죄송하지만, 저는 실시간 정보에 접근할 수 없습니다."

# ✅ AI Agent (도구를 사용해 문제 해결)
agent = Agent(llm, tools=[WeatherAPI(), SearchTool()])
response = agent.run("오늘 서울 날씨 알려주고, 우산 필요한지 판단해줘")
# 1. WeatherAPI 호출 → 서울 날씨 확인
# 2. 강수확률 분석
# 3. "오늘 서울은 비 올 확률 80%입니다. 우산 꼭 챙기세요!"
```

**"Agent 시대"가 온 이유**:
- 2022년 10월: ReAct 논문 - Agent의 이론적 기반 확립
- 2023년 3월: GPT-4 출시 - 강력한 추론 능력
- 2023년 3-4월: AutoGPT, BabyAGI - 자율 Agent 프레임워크 등장
- 2023년 6월: Function Calling 추가 - Agent 실용화 가속
- **LLM은 대화만 하지만, Agent는 실제 일을 할 수 있음**

## 1. AI Agent란 무엇인가?

### 1.1 정의

**AI Agent**: 자율적으로 목표를 달성하기 위해 환경을 인식(Perceive)하고, 추론(Reason)하며, 행동(Act)하는 AI 시스템

```python
class AIAgent:
    """
    AI Agent의 핵심 구조
    """
    def __init__(self, llm, tools):
        self.llm = llm          # 두뇌 (추론)
        self.tools = tools      # 손발 (행동)
        self.memory = []        # 기억

    def run(self, task: str) -> str:
        """
        Agent의 실행 루프
        """
        # 1. Perceive: 작업 이해
        current_state = self._perceive(task)

        # 2. Reason: 계획 수립
        plan = self._reason(current_state)

        # 3. Act: 도구 사용하여 실행
        result = self._act(plan)

        # 4. Learn: 결과를 기억에 저장
        self._learn(result)

        return result
```

### 1.2 전통적인 LLM vs AI Agent

| 특징 | 전통적인 LLM | AI Agent |
|-----|------------|----------|
| **역할** | 텍스트 생성 | 작업 수행 |
| **능력** | 대화, 질문 응답 | 도구 사용, 문제 해결 |
| **자율성** | 수동적 (프롬프트 대기) | 능동적 (목표 달성 추구) |
| **도구 사용** | 불가능 | 가능 (API, DB, 파일 등) |
| **추론** | 1회성 추론 | 반복적 추론 (루프) |
| **메모리** | 대화 컨텍스트만 | 장기 기억 가능 |

```python
# 전통적인 LLM
user: "내일 회의 일정 추가해줘"
llm: "죄송하지만, 저는 캘린더에 접근할 수 없습니다."

# AI Agent
user: "내일 회의 일정 추가해줘"
agent:
  1. CalendarAPI 호출
  2. 내일 날짜 확인
  3. 일정 추가
  4. "내일 오후 2시 회의 일정을 추가했습니다."
```

## 2. Agent 개념의 역사

### 2.1 초기: 강화학습 Agent (1990s~2010s)

```python
# 초기 Agent: 게임 환경에서의 강화학습
class RLAgent:
    """
    강화학습 기반 Agent
    """
    def __init__(self):
        self.q_table = {}  # 상태-행동 가치

    def choose_action(self, state):
        # Epsilon-greedy 전략
        if random.random() < epsilon:
            return random_action()
        else:
            return best_action(state)

    def learn(self, state, action, reward, next_state):
        # Q-learning 업데이트
        self.q_table[state][action] += alpha * (
            reward + gamma * max(self.q_table[next_state]) -
            self.q_table[state][action]
        )
```

**특징**:
- 환경과 상호작용하며 학습
- 보상을 최대화하는 정책 학습
- **한계**: 복잡한 추론이나 언어 이해 불가

### 2.2 전환점: ReAct 논문 (2022년 10월)

**논문**: "ReAct: Synergizing Reasoning and Acting in Language Models"
- 저자: Shunyu Yao et al. (Princeton, Google)
- 핵심 아이디어: **Reasoning (추론) + Acting (행동)을 번갈아가며 수행**

```python
# ReAct 패턴
task = "서울에서 부산까지 기차로 가는데 얼마나 걸려?"

# Step 1: Thought (추론)
thought = "기차 시간표를 검색해야겠다."

# Step 2: Action (행동)
action = Search("서울 부산 KTX 소요시간")

# Step 3: Observation (관찰)
observation = "KTX는 약 2시간 30분 소요"

# Step 4: Thought (추론)
thought = "이제 답변할 수 있다."

# Step 5: Final Answer
answer = "서울에서 부산까지 KTX로 약 2시간 30분 걸립니다."
```

**ReAct의 혁신**:

```
# 기존 방식 (Chain-of-Thought)
Q: 서울 날씨는?
A: [추론만] 서울은 한국의 수도이고... (실제 정보 없음)

# ReAct 방식
Q: 서울 날씨는?
Thought: 날씨 API를 호출해야겠다.
Action: WeatherAPI.get("Seoul")
Observation: 맑음, 15도
Thought: 이제 답변할 수 있다.
Answer: 서울은 현재 맑고 기온은 15도입니다.
```

### 2.3 실용화 시작 (2023년 초~)

**2023년 3월 14일: GPT-4 출시**

OpenAI가 GPT-4를 출시하며 추론 능력이 크게 향상됨

**2023년 3월 말: AutoGPT, BabyAGI 등장**

자율적으로 작업을 분해하고 실행하는 Agent 프레임워크가 등장

**2023년 6월 13일: Function Calling 추가**

OpenAI가 GPT-4에 Function Calling API를 추가 - Agent 구현이 극도로 쉬워짐

```python
# GPT-4 Function Calling
functions = [
    {
        "name": "get_weather",
        "description": "Get current weather in a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }
]

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "서울 날씨는?"}],
    functions=functions
)

# GPT-4가 자동으로 함수 호출 결정
# function_call: {"name": "get_weather", "arguments": '{"location": "Seoul"}'}
```

**AutoGPT/BabyAGI 예시**

자율적으로 작업을 분해하고 실행하는 Agent

```python
# AutoGPT 스타일 (2023년 3월)
user: "Python으로 웹 크롤러 만들어줘"

agent:
  Task 1: 요구사항 분석
  Task 2: 필요한 라이브러리 검색 (requests, BeautifulSoup)
  Task 3: 코드 작성
  Task 4: 테스트 코드 작성
  Task 5: 실행 및 검증
  Task 6: 결과 보고
```

**2023년 하반기: LangGraph, CrewAI 등장**

더 정교한 Agent 제어와 Multi-Agent 협업

### 2.4 타임라인 정리

```
1990s-2010s: 강화학습 Agent (게임, 로봇)
            └─ 제한적 환경, 언어 이해 불가

2017년: Transformer 등장
       └─ 언어 이해 능력 획기적 향상

2020년: GPT-3 출시
       └─ Few-shot learning, Chain-of-Thought

2022년 3월: InstructGPT
            └─ RLHF (인간 피드백 강화학습)

2022년 10월 6일: ReAct 논문 ⭐
                 └─ Agent의 이론적 기반 확립
                 └─ Reasoning + Acting 패턴

2022년 11월: ChatGPT (11월 30일), LangChain
            └─ 대화형 AI 대중화
            └─ LangChain Agent 지원

2023년 3월 14일: GPT-4 출시 ⭐
                └─ 강력한 추론 능력

2023년 3월 28일: BabyAGI ⭐
2023년 3월 30일: AutoGPT ⭐
                 └─ 자율 Agent 프레임워크
                 └─ GitHub 폭발적 성장

2023년 6월 13일: GPT-4 Function Calling ⭐
                 └─ Agent 실용화 가속
                 └─ 도구 사용이 안정화됨

2023년 하반기: LangGraph, CrewAI
               └─ Agent 개발 도구 성숙
               └─ Multi-Agent 시스템

2024년~: Multi-Agent 협업 생태계
        └─ Agent들이 협업하는 시스템
        └─ AutoGen, Microsoft Copilot Agents 등
```

## 3. 왜 지금 "Agent 시대"인가?

### 3.1 기술적 성숙

**1) LLM의 추론 능력 향상**

```python
# GPT-3 (2020)
"2+2는?"
→ "4입니다."

# GPT-4 (2023)
"철수가 사과 2개, 영희가 사과 3개 가지고 있어.
 둘이 나눠먹으려면 몇 개씩 먹어야 해?"
→ "총 5개이므로 2개씩 먹고 1개가 남습니다."
  [복잡한 추론 + 맥락 이해]
```

**2) Function Calling 안정화**

```python
# 이전: 프롬프트 엔지니어링으로 도구 사용 유도
prompt = """
You have access to these tools:
- search(query): Search the web
- calculator(expr): Calculate math

User: What's 123 * 456?
Assistant: Let me use calculator(123 * 456)
"""
# 불안정하고 오류 많음

# 현재: 구조화된 Function Calling
response = llm.chat(
    "What's 123 * 456?",
    tools=[CalculatorTool]
)
# response.tool_calls = [{"name": "calculator", "args": {"expr": "123 * 456"}}]
# 안정적이고 신뢰성 높음
```

**3) 벡터 DB와 RAG 생태계**

```python
# Agent가 방대한 지식에 접근 가능
agent = Agent(
    llm=GPT4,
    tools=[
        VectorSearchTool(chroma_db),  # 회사 문서 검색
        SQLTool(database),             # 데이터베이스 쿼리
        WebSearchTool(google),         # 실시간 정보
    ]
)

# 이제 Agent는 거의 모든 정보에 접근 가능!
```

### 3.2 실용적 가치

**기존 LLM의 한계**:

```python
user: "지난 달 매출 데이터를 분석해서 보고서 만들어줘"

# 전통적인 LLM
llm: "죄송하지만, 데이터베이스에 접근할 수 없습니다."

# 인간이 해야 할 일:
# 1. DB에서 데이터 추출
# 2. 엑셀로 정리
# 3. 분석
# 4. 보고서 작성
# → 2-3시간 소요
```

**Agent의 가치**:

```python
user: "지난 달 매출 데이터를 분석해서 보고서 만들어줘"

# AI Agent
agent.run("지난 달 매출 분석 보고서 생성")

# Agent의 실행:
Step 1: DB에서 지난 달 매출 데이터 쿼리
Step 2: 데이터 분석 (증감률, 추세 등)
Step 3: 차트 생성
Step 4: 보고서 작성 (Markdown/PDF)
Step 5: 이메일 발송

# → 2분 소요 (90배 빠름!)
```

**실제 사용 사례**:

```python
# 1. 고객 지원 Agent
customer_agent = Agent(
    tools=[
        KnowledgeBaseTool,    # FAQ 검색
        OrderStatusTool,      # 주문 조회
        RefundTool,           # 환불 처리
        EmailTool             # 이메일 발송
    ]
)

# 인간 개입 없이 80%의 고객 문의 자동 처리

# 2. 데이터 분석 Agent
analyst_agent = Agent(
    tools=[
        SQLTool,              # 데이터 쿼리
        PythonREPLTool,       # 분석 코드 실행
        VisualizationTool,    # 차트 생성
    ]
)

# "최근 3개월 사용자 증가율 분석" → 자동 실행

# 3. 소프트웨어 개발 Agent
dev_agent = Agent(
    tools=[
        CodeSearchTool,       # 코드베이스 검색
        FileEditTool,         # 파일 수정
        TerminalTool,         # 명령어 실행
        GitTool,              # Git 작업
    ]
)

# "버그 #123 수정" → 코드 분석, 수정, 테스트, PR 생성
```

### 3.3 산업계의 변화

**투자 급증**:
- 2023년: Agent 관련 스타트업에 수십억 달러 투자
- OpenAI, Anthropic, Google: Agent 기능 강화
- Microsoft, Salesforce: Agent 플랫폼 출시

**채용 시장 변화**:

```
2022년 이전:
- ML Engineer
- Data Scientist
- Backend Developer

2023년~현재:
- AI Agent Engineer
- LLM Application Developer
- Prompt Engineer
- Agent Orchestration Engineer

새로운 직군 등장!
```

**기업들의 Agent 도입**:

```python
# Salesforce: AgentForce
# - 영업, 고객 지원, 마케팅 Agent

# Microsoft: Copilot Agents
# - M365 전반에 Agent 통합

# Google: Duet AI Agents
# - Workspace 자동화

# 개발 도구:
# - GitHub Copilot Workspace (코딩 Agent)
# - Cursor (AI 코드 편집기)
# - Devin (자율 소프트웨어 엔지니어)
```

## 4. Agent의 핵심 구성 요소

### 4.1 LLM (두뇌)

```python
from typing import List, Dict

class AgentLLM:
    """
    Agent의 추론 엔진
    """
    def reason(self, task: str, context: Dict) -> str:
        """
        현재 상황을 분석하고 다음 행동 결정
        """
        prompt = f"""
You are an AI agent tasked with: {task}

Current context:
{context}

Think step by step:
1. What information do I have?
2. What information do I need?
3. What action should I take next?
4. Why is this action appropriate?

Your reasoning:
"""
        return self.llm.generate(prompt)

    def select_tool(self, reasoning: str, available_tools: List) -> Dict:
        """
        추론을 바탕으로 사용할 도구 선택
        """
        prompt = f"""
Based on this reasoning:
{reasoning}

Available tools:
{[tool.description for tool in available_tools]}

Which tool should be used and with what parameters?
Return JSON: {{"tool": "name", "params": {{}}}}
"""
        return self.llm.generate(prompt, format="json")
```

### 4.2 Tools (손발)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class Tool(ABC):
    """
    Agent가 사용할 수 있는 도구의 기본 인터페이스
    """
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs) -> Any:
        """도구 실행"""
        pass

    def to_json_schema(self) -> Dict:
        """LLM이 이해할 수 있는 형태로 변환"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }

# 실제 도구 구현 예시
class WeatherTool(Tool):
    """날씨 정보 조회 도구"""
    name = "get_weather"
    description = "Get current weather for a location"

    def run(self, location: str) -> Dict:
        # 실제 Weather API 호출
        response = requests.get(
            f"https://api.weather.com/v1/current",
            params={"location": location}
        )
        return response.json()

class SQLQueryTool(Tool):
    """데이터베이스 쿼리 도구"""
    name = "query_database"
    description = "Execute SQL query on the database"

    def __init__(self, connection_string: str):
        self.db = create_engine(connection_string)

    def run(self, query: str) -> List[Dict]:
        with self.db.connect() as conn:
            result = conn.execute(text(query))
            return [dict(row) for row in result]

class PythonREPLTool(Tool):
    """Python 코드 실행 도구"""
    name = "python_repl"
    description = "Execute Python code and return the result"

    def run(self, code: str) -> str:
        # 샌드박스 환경에서 코드 실행
        local_vars = {}
        exec(code, {}, local_vars)
        return str(local_vars.get('result', ''))

class WebSearchTool(Tool):
    """웹 검색 도구"""
    name = "web_search"
    description = "Search the web for information"

    def run(self, query: str, num_results: int = 5) -> List[Dict]:
        # Google Search API 등 사용
        results = google_search(query, num_results)
        return [
            {"title": r.title, "snippet": r.snippet, "url": r.url}
            for r in results
        ]
```

### 4.3 Memory (기억)

```python
from typing import List, Dict, Optional
from datetime import datetime

class AgentMemory:
    """
    Agent의 기억 시스템
    """
    def __init__(self):
        self.short_term = []   # 현재 작업의 대화 기록
        self.long_term = []    # 장기 기억 (벡터 DB)
        self.working = {}      # 작업 중 임시 데이터

    def add_interaction(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        상호작용 기록 추가
        """
        interaction = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        self.short_term.append(interaction)

    def get_context(self, max_tokens: int = 2000) -> str:
        """
        현재 컨텍스트 가져오기 (토큰 제한 고려)
        """
        # 최근 대화부터 역순으로 추가
        context = []
        token_count = 0

        for interaction in reversed(self.short_term):
            content = interaction["content"]
            tokens = len(content.split()) * 1.3  # 대략적 추정

            if token_count + tokens > max_tokens:
                break

            context.insert(0, f"{interaction['role']}: {content}")
            token_count += tokens

        return "\n".join(context)

    def save_to_long_term(self, key: str, value: Any):
        """
        장기 기억에 저장 (중요한 정보)
        """
        self.long_term.append({
            "key": key,
            "value": value,
            "timestamp": datetime.now()
        })

    def retrieve_from_long_term(self, query: str, top_k: int = 3) -> List:
        """
        장기 기억에서 관련 정보 검색
        """
        # 벡터 유사도 기반 검색
        # 실제로는 Chroma, Pinecone 등 사용
        relevant_memories = vector_search(query, self.long_term, top_k)
        return relevant_memories
```

### 4.4 Planner (계획자)

```python
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Task:
    """작업 단위"""
    id: int
    description: str
    dependencies: List[int]  # 선행 작업 ID
    status: str  # pending, in_progress, completed, failed
    result: Any = None

class AgentPlanner:
    """
    복잡한 작업을 여러 단계로 분해
    """
    def __init__(self, llm):
        self.llm = llm

    def decompose_task(self, goal: str) -> List[Task]:
        """
        목표를 하위 작업들로 분해
        """
        prompt = f"""
Goal: {goal}

Break this goal down into smaller, actionable tasks.
Each task should be:
1. Specific and measurable
2. Independently executable
3. Properly sequenced (considering dependencies)

Return a list of tasks in JSON format:
[
    {{
        "id": 1,
        "description": "task description",
        "dependencies": []
    }},
    ...
]
"""
        response = self.llm.generate(prompt, format="json")
        tasks = json.loads(response)

        return [
            Task(
                id=t["id"],
                description=t["description"],
                dependencies=t["dependencies"],
                status="pending"
            )
            for t in tasks
        ]

    def get_next_task(self, tasks: List[Task]) -> Optional[Task]:
        """
        다음에 실행할 작업 선택
        """
        for task in tasks:
            if task.status != "pending":
                continue

            # 모든 선행 작업이 완료되었는지 확인
            deps_completed = all(
                tasks[dep_id - 1].status == "completed"
                for dep_id in task.dependencies
            )

            if deps_completed:
                return task

        return None

    def update_plan(
        self,
        tasks: List[Task],
        current_task: Task,
        result: Any
    ) -> List[Task]:
        """
        실행 결과에 따라 계획 업데이트
        """
        # 작업 상태 업데이트
        current_task.status = "completed"
        current_task.result = result

        # 결과에 따라 추가 작업 필요한지 판단
        if self._needs_replanning(current_task, result):
            new_tasks = self.decompose_task(
                f"Handle result: {result} for task: {current_task.description}"
            )
            tasks.extend(new_tasks)

        return tasks

    def _needs_replanning(self, task: Task, result: Any) -> bool:
        """
        재계획이 필요한지 판단
        """
        # 예: 에러 발생, 예상과 다른 결과 등
        if isinstance(result, Exception):
            return True
        return False

# 사용 예시
planner = AgentPlanner(llm)

goal = "지난 달 매출 데이터 분석 보고서 작성"
tasks = planner.decompose_task(goal)

# 결과:
# Task 1: DB에서 지난 달 매출 데이터 쿼리
# Task 2: 데이터 정제 및 전처리 (depends on 1)
# Task 3: 매출 추세 분석 (depends on 2)
# Task 4: 차트 생성 (depends on 3)
# Task 5: 보고서 작성 (depends on 3, 4)
```

## 5. Agent 구현 패턴

### 5.1 ReAct Agent (가장 기본)

```python
from typing import List, Dict, Any, Optional
import json

class ReActAgent:
    """
    ReAct (Reasoning + Acting) 패턴 Agent
    """
    def __init__(self, llm, tools: List[Tool], max_iterations: int = 10):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.max_iterations = max_iterations
        self.memory = AgentMemory()

    def run(self, task: str) -> str:
        """
        Agent 실행 루프
        """
        self.memory.add_interaction("user", task)

        for i in range(self.max_iterations):
            # 1. Thought: 현재 상황 분석 및 다음 행동 계획
            thought = self._think()
            print(f"Thought {i+1}: {thought}")

            # 종료 조건 확인
            if self._is_final_answer(thought):
                answer = self._extract_answer(thought)
                return answer

            # 2. Action: 도구 선택 및 실행
            action, action_input = self._decide_action(thought)
            print(f"Action: {action}({action_input})")

            # 3. Observation: 도구 실행 결과 관찰
            observation = self._execute_action(action, action_input)
            print(f"Observation: {observation}\n")

            # 메모리에 저장
            self.memory.add_interaction("assistant", f"Thought: {thought}")
            self.memory.add_interaction("assistant", f"Action: {action}({action_input})")
            self.memory.add_interaction("tool", f"Observation: {observation}")

        return "Maximum iterations reached without finding an answer."

    def _think(self) -> str:
        """
        현재 상황을 분석하고 다음 행동 계획
        """
        context = self.memory.get_context()
        tools_desc = "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in self.tools.items()
        ])

        prompt = f"""
You are an AI agent solving a task step by step.

Available tools:
{tools_desc}

Conversation history:
{context}

Think about:
1. What have I learned so far?
2. What information do I still need?
3. What action should I take next?
4. Or, do I have enough information to provide a final answer?

Your thought (if ready to answer, start with "Final Answer:"):
"""
        return self.llm.generate(prompt)

    def _is_final_answer(self, thought: str) -> bool:
        """
        최종 답변인지 확인
        """
        return thought.strip().startswith("Final Answer:")

    def _extract_answer(self, thought: str) -> str:
        """
        최종 답변 추출
        """
        return thought.split("Final Answer:", 1)[1].strip()

    def _decide_action(self, thought: str) -> tuple[str, Dict]:
        """
        수행할 행동 결정
        """
        tools_schema = [tool.to_json_schema() for tool in self.tools.values()]

        prompt = f"""
Based on this thought:
{thought}

Choose an appropriate tool to use from:
{json.dumps(tools_schema, indent=2)}

Return JSON:
{{
    "tool": "tool_name",
    "input": {{"param1": "value1", ...}}
}}
"""
        response = self.llm.generate(prompt, format="json")
        action_data = json.loads(response)

        return action_data["tool"], action_data["input"]

    def _execute_action(self, action: str, action_input: Dict) -> str:
        """
        도구 실행
        """
        if action not in self.tools:
            return f"Error: Tool '{action}' not found"

        try:
            result = self.tools[action].run(**action_input)
            return str(result)
        except Exception as e:
            return f"Error executing {action}: {str(e)}"

# 실전 예시
weather_tool = WeatherTool()
search_tool = WebSearchTool()

agent = ReActAgent(
    llm=GPT4(),
    tools=[weather_tool, search_tool]
)

response = agent.run(
    "서울 날씨 알려주고, 우산이 필요한지 판단해줘"
)

# 실행 과정:
# Thought 1: 서울의 현재 날씨를 확인해야 한다.
# Action: get_weather({"location": "Seoul"})
# Observation: {"temp": 15, "condition": "Rainy", "precipitation": 80}

# Thought 2: 비가 올 확률이 80%이므로 우산이 필요하다.
# Final Answer: 서울은 현재 15도이고 비가 올 확률이 80%입니다. 우산을 꼭 챙기세요!
```

### 5.2 Plan-and-Execute Agent

```python
class PlanAndExecuteAgent:
    """
    계획 수립 후 순차 실행하는 Agent
    복잡한 작업에 적합
    """
    def __init__(self, llm, tools: List[Tool], planner: AgentPlanner):
        self.llm = llm
        self.tools = {tool.name: tool for tool in tools}
        self.planner = planner
        self.memory = AgentMemory()

    def run(self, goal: str) -> str:
        """
        Agent 실행
        """
        print(f"Goal: {goal}\n")

        # 1. Planning: 작업 분해
        print("=== Planning Phase ===")
        tasks = self.planner.decompose_task(goal)
        for task in tasks:
            print(f"Task {task.id}: {task.description} (deps: {task.dependencies})")
        print()

        # 2. Execution: 순차 실행
        print("=== Execution Phase ===")
        while True:
            next_task = self.planner.get_next_task(tasks)

            if next_task is None:
                # 모든 작업 완료
                break

            print(f"\nExecuting Task {next_task.id}: {next_task.description}")
            next_task.status = "in_progress"

            try:
                # 작업 실행
                result = self._execute_task(next_task, tasks)
                print(f"Result: {result}")

                # 계획 업데이트
                tasks = self.planner.update_plan(tasks, next_task, result)

            except Exception as e:
                print(f"Error: {e}")
                next_task.status = "failed"
                next_task.result = e

                # 재계획 필요 여부 판단
                tasks = self.planner.update_plan(tasks, next_task, e)

        # 3. 최종 결과 정리
        final_result = self._compile_results(tasks)
        return final_result

    def _execute_task(self, task: Task, completed_tasks: List[Task]) -> Any:
        """
        개별 작업 실행
        """
        # 선행 작업의 결과를 컨텍스트로 사용
        context = self._build_context(task, completed_tasks)

        # LLM에게 작업 실행 방법 결정 요청
        tool_call = self._decide_tool_for_task(task, context)

        # 도구 실행
        result = self.tools[tool_call["tool"]].run(**tool_call["params"])

        return result

    def _build_context(self, task: Task, tasks: List[Task]) -> Dict:
        """
        작업 실행을 위한 컨텍스트 구성
        """
        context = {"task": task.description}

        # 선행 작업의 결과 포함
        for dep_id in task.dependencies:
            dep_task = tasks[dep_id - 1]
            if dep_task.status == "completed":
                context[f"dependency_{dep_id}"] = dep_task.result

        return context

    def _decide_tool_for_task(self, task: Task, context: Dict) -> Dict:
        """
        작업에 적합한 도구 선택
        """
        prompt = f"""
Task: {task.description}

Context from previous tasks:
{json.dumps(context, indent=2)}

Available tools:
{[tool.to_json_schema() for tool in self.tools.values()]}

Which tool should be used to complete this task?
Return JSON: {{"tool": "name", "params": {{}}}}
"""
        response = self.llm.generate(prompt, format="json")
        return json.loads(response)

    def _compile_results(self, tasks: List[Task]) -> str:
        """
        모든 작업의 결과를 종합
        """
        completed = [t for t in tasks if t.status == "completed"]
        failed = [t for t in tasks if t.status == "failed"]

        summary = f"Completed {len(completed)}/{len(tasks)} tasks.\n\n"

        if failed:
            summary += "Failed tasks:\n"
            for task in failed:
                summary += f"- Task {task.id}: {task.description}\n"
                summary += f"  Error: {task.result}\n"

        # LLM에게 최종 요약 요청
        prompt = f"""
Original goal: {self.memory.short_term[0]['content']}

Task results:
{json.dumps([{"task": t.description, "result": str(t.result)} for t in completed], indent=2)}

Provide a comprehensive summary of what was accomplished:
"""
        final_summary = self.llm.generate(prompt)

        return final_summary

# 사용 예시
sql_tool = SQLQueryTool("postgresql://...")
python_tool = PythonREPLTool()
chart_tool = VisualizationTool()

agent = PlanAndExecuteAgent(
    llm=GPT4(),
    tools=[sql_tool, python_tool, chart_tool],
    planner=AgentPlanner(GPT4())
)

result = agent.run(
    "지난 분기 매출 데이터를 분석하고 다음 분기 예측을 포함한 보고서 작성"
)

# 실행 과정:
# === Planning Phase ===
# Task 1: DB에서 지난 분기 매출 데이터 쿼리
# Task 2: 데이터 전처리 및 이상치 제거 (depends on 1)
# Task 3: 매출 추세 분석 (depends on 2)
# Task 4: 다음 분기 예측 모델 생성 (depends on 3)
# Task 5: 시각화 차트 생성 (depends on 3, 4)
# Task 6: 보고서 작성 (depends on 5)
#
# === Execution Phase ===
# Executing Task 1: DB에서 지난 분기 매출 데이터 쿼리
# Tool: query_database
# Result: [{"month": "2024-01", "sales": 1000000}, ...]
# ...
```

### 5.3 Multi-Agent System

```python
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class AgentRole(Enum):
    """Agent의 역할"""
    PLANNER = "planner"        # 계획 수립
    RESEARCHER = "researcher"  # 정보 조사
    ANALYST = "analyst"        # 데이터 분석
    CODER = "coder"           # 코드 작성
    REVIEWER = "reviewer"      # 검토
    COORDINATOR = "coordinator" # 조율

@dataclass
class Message:
    """Agent 간 메시지"""
    sender: str
    recipient: str
    content: str
    message_type: str  # request, response, info

class MultiAgentSystem:
    """
    여러 Agent가 협업하는 시스템
    """
    def __init__(self):
        self.agents: Dict[str, SpecializedAgent] = {}
        self.message_queue: List[Message] = []
        self.coordinator = CoordinatorAgent()

    def add_agent(self, name: str, agent: 'SpecializedAgent'):
        """Agent 추가"""
        self.agents[name] = agent

    def run(self, task: str) -> str:
        """
        Multi-Agent 시스템 실행
        """
        # 1. Coordinator가 작업 분배
        assignments = self.coordinator.assign_tasks(task, self.agents)

        # 2. 각 Agent가 작업 수행
        for assignment in assignments:
            agent_name = assignment["agent"]
            subtask = assignment["task"]

            print(f"\n[{agent_name}] Working on: {subtask}")

            # Agent에게 작업 전달
            result = self.agents[agent_name].work(subtask)

            # 결과를 다른 Agent들에게 브로드캐스트
            self._broadcast(agent_name, result)

        # 3. 최종 결과 종합
        final_result = self.coordinator.compile_results(self.message_queue)
        return final_result

    def _broadcast(self, sender: str, content: str):
        """
        메시지를 모든 Agent에게 전달
        """
        message = Message(
            sender=sender,
            recipient="all",
            content=content,
            message_type="info"
        )
        self.message_queue.append(message)

        # 관련 Agent들에게 알림
        for agent in self.agents.values():
            agent.receive_message(message)

class SpecializedAgent:
    """
    특정 역할에 특화된 Agent
    """
    def __init__(self, role: AgentRole, llm, tools: List[Tool]):
        self.role = role
        self.llm = llm
        self.tools = tools
        self.inbox: List[Message] = []

    def work(self, task: str) -> str:
        """
        자신의 전문 분야 작업 수행
        """
        # 받은 메시지에서 관련 정보 수집
        context = self._gather_context(task)

        # 작업 수행
        result = self._execute_specialized_task(task, context)

        return result

    def receive_message(self, message: Message):
        """
        다른 Agent로부터 메시지 수신
        """
        if message.recipient == "all" or message.recipient == self.role.value:
            self.inbox.append(message)

    def _gather_context(self, task: str) -> Dict:
        """
        다른 Agent들의 작업 결과에서 관련 정보 수집
        """
        context = {}
        for message in self.inbox:
            if self._is_relevant(message.content, task):
                context[message.sender] = message.content
        return context

    def _is_relevant(self, content: str, task: str) -> bool:
        """
        메시지가 현재 작업과 관련있는지 판단
        """
        # 간단한 키워드 매칭 (실제로는 LLM 사용)
        task_keywords = set(task.lower().split())
        content_keywords = set(content.lower().split())
        overlap = task_keywords & content_keywords
        return len(overlap) > 2

    def _execute_specialized_task(self, task: str, context: Dict) -> str:
        """
        전문 분야의 작업 실행
        """
        prompt = f"""
You are a {self.role.value} agent.

Your task: {task}

Context from other agents:
{json.dumps(context, indent=2)}

Your specialized tools:
{[tool.name for tool in self.tools]}

Execute your task and provide the result:
"""
        return self.llm.generate(prompt)

# 실제 사용 예시
class CoordinatorAgent:
    """
    다른 Agent들을 조율하는 Agent
    """
    def __init__(self, llm=None):
        self.llm = llm or GPT4()

    def assign_tasks(
        self,
        goal: str,
        agents: Dict[str, SpecializedAgent]
    ) -> List[Dict]:
        """
        목표를 각 Agent에게 할당
        """
        agent_descriptions = {
            name: agent.role.value
            for name, agent in agents.items()
        }

        prompt = f"""
Goal: {goal}

Available agents and their roles:
{json.dumps(agent_descriptions, indent=2)}

Break down the goal into subtasks and assign each to the most appropriate agent.
Return JSON: [
    {{"agent": "agent_name", "task": "subtask description"}},
    ...
]
"""
        response = self.llm.generate(prompt, format="json")
        return json.loads(response)

    def compile_results(self, messages: List[Message]) -> str:
        """
        모든 Agent의 작업 결과를 종합
        """
        results = {}
        for msg in messages:
            if msg.message_type == "info":
                results[msg.sender] = msg.content

        prompt = f"""
Compile these results from different agents into a comprehensive answer:

{json.dumps(results, indent=2)}

Provide a coherent, integrated response:
"""
        return self.llm.generate(prompt)

# Multi-Agent 시스템 구성
system = MultiAgentSystem()

# 각 전문 Agent 추가
system.add_agent(
    "researcher",
    SpecializedAgent(
        role=AgentRole.RESEARCHER,
        llm=GPT4(),
        tools=[WebSearchTool(), WikipediaTool()]
    )
)

system.add_agent(
    "analyst",
    SpecializedAgent(
        role=AgentRole.ANALYST,
        llm=GPT4(),
        tools=[SQLQueryTool(), PythonREPLTool()]
    )
)

system.add_agent(
    "coder",
    SpecializedAgent(
        role=AgentRole.CODER,
        llm=GPT4(),
        tools=[CodeSearchTool(), FileEditTool()]
    )
)

system.add_agent(
    "reviewer",
    SpecializedAgent(
        role=AgentRole.REVIEWER,
        llm=GPT4(),
        tools=[LinterTool(), TestRunnerTool()]
    )
)

# 복잡한 작업 실행
result = system.run(
    "경쟁사 3곳의 최근 제품 출시 동향을 조사하고, "
    "우리 회사 데이터와 비교 분석한 후, "
    "분석 결과를 시각화하는 Python 스크립트를 작성해줘"
)

# 실행 과정:
# [researcher] 경쟁사 제품 출시 동향 조사
# → Web search, 뉴스 기사 수집
#
# [analyst] 우리 회사 데이터 분석
# → DB 쿼리, 통계 분석
#
# [analyst] 경쟁사 vs 우리 회사 비교
# → researcher의 결과와 자사 데이터 비교
#
# [coder] 시각화 스크립트 작성
# → analyst의 분석 결과를 차트로 표현
#
# [reviewer] 코드 검토
# → coder의 스크립트 검증, 개선 제안
```

## 6. 실전 프레임워크

### 6.1 LangChain Agent

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain import hub

# 1. 도구 정의
def search_web(query: str) -> str:
    """웹 검색 도구"""
    # 실제 검색 API 호출
    return f"Search results for: {query}"

def calculate(expression: str) -> str:
    """계산기 도구"""
    try:
        result = eval(expression)
        return str(result)
    except:
        return "Invalid expression"

tools = [
    Tool(
        name="Search",
        func=search_web,
        description="useful for when you need to search the web for information"
    ),
    Tool(
        name="Calculator",
        func=calculate,
        description="useful for when you need to calculate math expressions"
    )
]

# 2. LLM 설정
llm = ChatOpenAI(model="gpt-4", temperature=0)

# 3. Prompt 가져오기
prompt = hub.pull("hwchase17/react")

# 4. Agent 생성
agent = create_react_agent(llm, tools, prompt)

# 5. Executor 생성 (실행 엔진)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=10,
    handle_parsing_errors=True
)

# 6. 실행
response = agent_executor.invoke({
    "input": "What's the weather in Seoul and what's 123 * 456?"
})

print(response["output"])
```

### 6.2 LangGraph Agent (더 정교한 제어)

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage

# 1. State 정의
class AgentState(TypedDict):
    """Agent의 상태"""
    messages: List[HumanMessage | AIMessage]
    next_action: str
    iteration: int

# 2. 노드 함수 정의
def planning_node(state: AgentState) -> AgentState:
    """계획 수립 노드"""
    llm = ChatOpenAI(model="gpt-4")

    # 계획 수립
    response = llm.invoke([
        HumanMessage(content="Analyze the task and create a plan")
    ])

    state["messages"].append(response)
    state["next_action"] = "execute"
    return state

def execution_node(state: AgentState) -> AgentState:
    """실행 노드"""
    # 도구 실행 로직
    last_message = state["messages"][-1]

    # 실행 결과
    result = execute_tools(last_message.content)

    state["messages"].append(AIMessage(content=result))
    state["iteration"] += 1
    state["next_action"] = "review"
    return state

def review_node(state: AgentState) -> AgentState:
    """검토 노드"""
    llm = ChatOpenAI(model="gpt-4")

    # 결과 검토
    review = llm.invoke([
        HumanMessage(content="Review the execution result")
    ])

    state["messages"].append(review)

    # 완료 또는 재시도 결정
    if "completed" in review.content.lower():
        state["next_action"] = "end"
    else:
        state["next_action"] = "planning"

    return state

def router(state: AgentState) -> str:
    """다음 노드 결정"""
    if state["next_action"] == "end" or state["iteration"] >= 10:
        return END
    return state["next_action"]

# 3. 그래프 구성
workflow = StateGraph(AgentState)

# 노드 추가
workflow.add_node("planning", planning_node)
workflow.add_node("execute", execution_node)
workflow.add_node("review", review_node)

# 엣지 정의
workflow.set_entry_point("planning")
workflow.add_conditional_edges("planning", router)
workflow.add_conditional_edges("execute", router)
workflow.add_conditional_edges("review", router)

# 4. 컴파일
app = workflow.compile()

# 5. 실행
initial_state = AgentState(
    messages=[HumanMessage(content="Analyze Q3 sales data")],
    next_action="planning",
    iteration=0
)

result = app.invoke(initial_state)
```

### 6.3 CrewAI (Multi-Agent Framework)

```python
from crewai import Agent, Task, Crew, Process

# 1. Agent 정의
researcher = Agent(
    role="Market Researcher",
    goal="Research competitor products and market trends",
    backstory="""You are an expert market researcher with 10 years of experience.
    You excel at finding and analyzing market data.""",
    verbose=True,
    allow_delegation=False,
    tools=[web_search_tool, scraper_tool]
)

analyst = Agent(
    role="Data Analyst",
    goal="Analyze data and provide insights",
    backstory="""You are a senior data analyst skilled at finding patterns
    and deriving actionable insights from data.""",
    verbose=True,
    allow_delegation=False,
    tools=[python_repl_tool, sql_tool]
)

writer = Agent(
    role="Report Writer",
    goal="Create comprehensive reports",
    backstory="""You are a professional report writer who creates clear,
    insightful reports for executives.""",
    verbose=True,
    allow_delegation=False,
    tools=[document_writer_tool]
)

# 2. Task 정의
research_task = Task(
    description="""Research the top 3 competitors in the smartphone market.
    Gather information about their latest products, pricing, and market share.""",
    agent=researcher,
    expected_output="A detailed report on competitor analysis"
)

analysis_task = Task(
    description="""Analyze the research data and compare it with our company's data.
    Identify strengths, weaknesses, and opportunities.""",
    agent=analyst,
    expected_output="A comprehensive analysis with data visualizations"
)

writing_task = Task(
    description="""Based on the research and analysis, write an executive summary
    and recommendations for our product strategy.""",
    agent=writer,
    expected_output="A polished executive report"
)

# 3. Crew 생성 (팀 구성)
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, writing_task],
    process=Process.sequential,  # 순차 실행
    verbose=True
)

# 4. 실행
result = crew.kickoff()

print(result)
```

## 7. Agent 개발 Best Practices

### 7.1 ✅ Do's

```python
# ✅ 1. 명확한 도구 설명
class GoodTool(Tool):
    name = "get_user_info"
    description = """
    Retrieves user information from the database.

    Parameters:
    - user_id (str): The unique identifier of the user

    Returns:
    - dict: User information including name, email, created_at

    Example:
    get_user_info(user_id="12345")
    """

# ✅ 2. 에러 처리
def safe_tool_execution(tool: Tool, **kwargs):
    try:
        return tool.run(**kwargs)
    except Exception as e:
        return {
            "error": str(e),
            "suggestion": "Please check the parameters and try again"
        }

# ✅ 3. 중간 결과 로깅
class LoggingAgent(ReActAgent):
    def _execute_action(self, action, action_input):
        logger.info(f"Executing: {action} with {action_input}")
        result = super()._execute_action(action, action_input)
        logger.info(f"Result: {result[:100]}...")  # 처음 100자만
        return result

# ✅ 4. 토큰 사용량 모니터링
class TokenAwareAgent:
    def __init__(self, *args, max_tokens=10000):
        super().__init__(*args)
        self.token_count = 0
        self.max_tokens = max_tokens

    def _think(self):
        if self.token_count > self.max_tokens:
            return "Final Answer: Token limit exceeded. Providing partial result."

        response = super()._think()
        self.token_count += estimate_tokens(response)
        return response

# ✅ 5. Agent 테스트
def test_agent():
    # Mock tools for testing
    mock_weather = MockWeatherTool()
    mock_weather.set_response("Seoul", {"temp": 15, "condition": "Sunny"})

    agent = ReActAgent(llm=MockLLM(), tools=[mock_weather])

    result = agent.run("서울 날씨 알려줘")

    assert "15" in result
    assert "Sunny" in result.lower() or "맑" in result
```

### 7.2 ❌ Don'ts

```python
# ❌ 1. 모호한 도구 설명
class BadTool(Tool):
    name = "tool1"
    description = "Does something"  # 너무 모호!

# ❌ 2. 무한 루프 위험
class DangerousAgent:
    def run(self, task):
        while True:  # 종료 조건 없음!
            self._think()
            self._act()

# ❌ 3. 에러 무시
def bad_execution(tool, **kwargs):
    try:
        return tool.run(**kwargs)
    except:
        pass  # 에러 무시 - 디버깅 불가능!

# ❌ 4. 과도한 도구 제공
agent = ReActAgent(
    llm=GPT4(),
    tools=[tool1, tool2, ..., tool50]  # 너무 많음! LLM이 혼란
)

# ✅ 관련 도구만 제공
agent = ReActAgent(
    llm=GPT4(),
    tools=[weather_tool, location_tool]  # 작업과 관련된 것만
)

# ❌ 5. 컨텍스트 무시
def bad_agent_loop():
    for i in range(10):
        # 이전 결과를 무시하고 매번 새로 시작
        result = llm.generate(original_task)
```

### 7.3 성능 최적화

```python
# 1. Tool 결과 캐싱
from functools import lru_cache

class CachedWeatherTool(Tool):
    @lru_cache(maxsize=100)
    def run(self, location: str) -> Dict:
        # 같은 위치 반복 조회 시 캐시 사용
        return self._fetch_weather(location)

# 2. 병렬 도구 실행
import asyncio

class ParallelAgent:
    async def execute_tools_parallel(self, tool_calls: List[Dict]):
        """여러 도구를 동시에 실행"""
        tasks = [
            self._execute_tool_async(call["tool"], call["params"])
            for call in tool_calls
        ]
        results = await asyncio.gather(*tasks)
        return results

# 3. 스트리밍 응답
class StreamingAgent:
    def run_stream(self, task: str):
        """결과를 스트리밍으로 반환"""
        for iteration in self.iterate(task):
            yield iteration.thought
            yield iteration.action
            yield iteration.observation

# 4. 효율적인 메모리 관리
class MemoryEfficientAgent:
    def _get_context(self):
        # 오래된 메시지는 요약하여 저장
        if len(self.memory) > 20:
            old_messages = self.memory[:10]
            summary = self._summarize(old_messages)
            self.memory = [summary] + self.memory[10:]

# 5. Early stopping
class EarlyStoppingAgent:
    def run(self, task: str):
        for i in range(self.max_iterations):
            thought = self._think()

            # 충분한 정보를 얻었으면 조기 종료
            if self._has_sufficient_info(thought):
                return self._extract_answer(thought)

            # 계속 진행
            self._act()
```

## 8. Agent의 한계와 미래

### 8.1 현재의 한계

```python
# 1. 비용 문제
agent.run("complex task")
# → 10-20번의 LLM 호출
# → GPT-4 기준: $0.50 ~ $2.00 per task
# 대규모 서비스에는 부담

# 2. 속도 문제
# 전통적인 API: 100ms
# Agent: 10-30초 (여러 번의 LLM 호출)

# 3. 신뢰성 문제
# Agent가 잘못된 도구를 선택하거나
# 무한 루프에 빠질 수 있음

# 4. 설명 가능성 (Explainability)
# "왜 이 결정을 내렸는가?" 설명 어려움
```

### 8.2 해결 방안 연구

```python
# 1. Distillation: 큰 모델을 작은 모델로
# GPT-4 Agent의 동작을 학습한 작은 모델 사용
distilled_agent = DistilledAgent(
    teacher=GPT4Agent,
    student=SmallModel  # 빠르고 저렴
)

# 2. Hybrid: LLM + 전통적 알고리즘
class HybridAgent:
    def route_task(self, task):
        # 간단한 작업은 규칙 기반으로
        if is_simple(task):
            return rule_based_solve(task)
        # 복잡한 작업만 LLM 사용
        else:
            return llm_based_solve(task)

# 3. Caching & Reusing
# 비슷한 작업의 결과 재사용
class SmartCachingAgent:
    def run(self, task):
        # 유사한 과거 작업 검색
        similar = self.find_similar_tasks(task)
        if similar:
            # 과거 결과를 재사용/수정
            return self.adapt_result(similar.result, task)
```

### 8.3 미래 전망

```
2024년 (현재):
├─ Function Calling 안정화
├─ Multi-Agent 시스템 성숙
└─ 기업 도입 가속화

2025년 예상:
├─ Agent-as-a-Service 플랫폼 등장
├─ 더 저렴하고 빠른 모델
├─ Agent 간 표준 프로토콜
└─ 산업별 특화 Agent

2026년+ 예상:
├─ 완전 자율 Agent (최소 감독)
├─ Agent 마켓플레이스
├─ Agent가 Agent를 생성
└─ 새로운 직업: Agent Manager, Agent Trainer
```

## 9. 실전 프로젝트: 고객 지원 Agent

### 완전한 구현 예시

```python
"""
실전 예제: E-commerce 고객 지원 Agent
기능:
- 주문 조회
- 환불 처리
- 상품 문의 응답
- 이슈 에스컬레이션
"""

from typing import List, Dict, Optional
from datetime import datetime
import sqlite3

# ===== Tools =====

class OrderQueryTool(Tool):
    """주문 조회 도구"""
    name = "query_order"
    description = """
    Query order information by order ID or customer email.
    Returns order details including status, items, and shipping info.
    """

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)

    def run(self, order_id: Optional[str] = None, email: Optional[str] = None) -> Dict:
        cursor = self.conn.cursor()

        if order_id:
            cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        elif email:
            cursor.execute("SELECT * FROM orders WHERE customer_email = ?", (email,))
        else:
            return {"error": "Must provide order_id or email"}

        result = cursor.fetchone()
        if not result:
            return {"error": "Order not found"}

        return {
            "order_id": result[0],
            "customer_email": result[1],
            "status": result[2],
            "items": result[3],
            "total": result[4],
            "created_at": result[5]
        }

class RefundTool(Tool):
    """환불 처리 도구"""
    name = "process_refund"
    description = """
    Process a refund for an order.
    Requires order_id and reason.
    Returns refund confirmation.
    """

    def run(self, order_id: str, reason: str) -> Dict:
        # 실제로는 결제 게이트웨이 API 호출
        refund_id = f"RF{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # DB 업데이트
        # ...

        return {
            "refund_id": refund_id,
            "order_id": order_id,
            "status": "processing",
            "estimated_days": 5
        }

class KnowledgeBaseTool(Tool):
    """FAQ 검색 도구"""
    name = "search_faq"
    description = """
    Search the knowledge base for answers to common questions.
    Returns relevant FAQ entries.
    """

    def __init__(self, vector_db):
        self.vector_db = vector_db

    def run(self, query: str, top_k: int = 3) -> List[Dict]:
        # 벡터 검색
        results = self.vector_db.search(query, top_k)

        return [
            {"question": r.question, "answer": r.answer, "score": r.score}
            for r in results
        ]

class EmailTool(Tool):
    """이메일 발송 도구"""
    name = "send_email"
    description = """
    Send an email to the customer.
    Use this for order confirmations, updates, or escalations.
    """

    def run(self, to: str, subject: str, body: str) -> Dict:
        # 실제 이메일 발송 로직
        # ...

        return {
            "status": "sent",
            "to": to,
            "timestamp": datetime.now().isoformat()
        }

# ===== Agent =====

class CustomerSupportAgent(ReActAgent):
    """
    고객 지원 Agent
    """
    def __init__(
        self,
        llm,
        db_path: str,
        vector_db,
        escalation_threshold: int = 3
    ):
        tools = [
            OrderQueryTool(db_path),
            RefundTool(),
            KnowledgeBaseTool(vector_db),
            EmailTool()
        ]

        super().__init__(llm, tools, max_iterations=10)

        self.escalation_threshold = escalation_threshold
        self.conversation_sentiment = []

    def run(self, customer_message: str, customer_email: str) -> str:
        """
        고객 메시지 처리
        """
        # 감정 분석
        sentiment = self._analyze_sentiment(customer_message)
        self.conversation_sentiment.append(sentiment)

        # 에스컬레이션 필요 여부 확인
        if self._should_escalate():
            return self._escalate_to_human(customer_message, customer_email)

        # 일반 처리
        self.memory.add_interaction("user", customer_message)
        self.memory.add_interaction("system", f"Customer email: {customer_email}")

        response = super().run(customer_message)

        # 응답 품질 확인
        if self._is_satisfactory_response(response):
            return response
        else:
            # 재시도 또는 에스컬레이션
            return self._escalate_to_human(customer_message, customer_email)

    def _analyze_sentiment(self, message: str) -> float:
        """
        메시지의 감정 분석 (-1: 부정, 0: 중립, 1: 긍정)
        """
        prompt = f"""
Analyze the sentiment of this customer message:

"{message}"

Return a score from -1 (very negative) to 1 (very positive).
Return only the number.
"""
        result = self.llm.generate(prompt)
        return float(result.strip())

    def _should_escalate(self) -> bool:
        """
        인간 상담사에게 에스컬레이션 필요 여부
        """
        # 여러 번 부정적 메시지
        if len(self.conversation_sentiment) >= self.escalation_threshold:
            avg_sentiment = sum(self.conversation_sentiment) / len(self.conversation_sentiment)
            if avg_sentiment < -0.5:
                return True

        return False

    def _escalate_to_human(self, message: str, email: str) -> str:
        """
        인간 상담사에게 전달
        """
        # 티켓 생성
        ticket_id = self._create_support_ticket(message, email)

        # 고객에게 안내
        return f"""
죄송합니다. 더 나은 지원을 위해 전문 상담사에게 연결해드리겠습니다.

티켓 번호: {ticket_id}
상담사가 24시간 내에 연락드릴 예정입니다.

긴급한 경우 1588-XXXX로 전화주시기 바랍니다.
"""

    def _create_support_ticket(self, message: str, email: str) -> str:
        """
        지원 티켓 생성
        """
        ticket_id = f"TK{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # DB에 티켓 저장
        # ...

        # 상담사에게 이메일 알림
        EmailTool().run(
            to="support@company.com",
            subject=f"New escalated ticket: {ticket_id}",
            body=f"Customer: {email}\n\nMessage: {message}"
        )

        return ticket_id

    def _is_satisfactory_response(self, response: str) -> bool:
        """
        응답이 만족스러운지 확인
        """
        # 너무 짧거나 애매한 응답 체크
        if len(response) < 50:
            return False

        # "죄송합니다" 같은 표현이 너무 많으면
        apology_count = response.lower().count("죄송") + response.lower().count("sorry")
        if apology_count > 2:
            return False

        return True

# ===== 사용 예시 =====

# Agent 초기화
agent = CustomerSupportAgent(
    llm=GPT4(),
    db_path="orders.db",
    vector_db=chroma_db,
    escalation_threshold=3
)

# 시나리오 1: 주문 조회
response1 = agent.run(
    customer_message="제 주문이 언제 배송되나요? 주문번호는 ORD123456입니다.",
    customer_email="customer@example.com"
)
# Agent 실행:
# Thought: 주문 상태를 확인해야 한다.
# Action: query_order(order_id="ORD123456")
# Observation: {"status": "shipped", "tracking": "TRK789", ...}
# Final Answer: 주문하신 상품은 이미 발송되었습니다. 운송장 번호는 TRK789입니다.

# 시나리오 2: 환불 요청
response2 = agent.run(
    customer_message="상품이 파손되어 왔습니다. 환불 받고 싶습니다.",
    customer_email="customer@example.com"
)
# Agent 실행:
# Thought: 파손 상품이므로 환불 처리가 필요하다.
# Action: query_order(email="customer@example.com")
# Observation: {"order_id": "ORD123456", ...}
# Action: process_refund(order_id="ORD123456", reason="damaged")
# Observation: {"refund_id": "RF20240101120000", "status": "processing"}
# Action: send_email(...)
# Final Answer: 환불이 처리되었습니다. 5영업일 내에 환불이 완료됩니다.

# 시나리오 3: 복잡한 문의 (에스컬레이션)
for i in range(3):
    response = agent.run(
        customer_message="정말 화가 납니다! 이게 무슨 서비스입니까!",
        customer_email="angry@example.com"
    )
# 3번째 부정적 메시지 → 자동 에스컬레이션
# "죄송합니다. 더 나은 지원을 위해 전문 상담사에게 연결해드리겠습니다..."
```

## 10. 요약

### Agent란?

**정의**: 자율적으로 추론(Reasoning)하고 행동(Acting)하며 도구(Tools)를 사용해 목표를 달성하는 AI 시스템

**핵심 구성**:
- LLM (두뇌): 추론 및 의사결정
- Tools (손발): 실제 작업 수행
- Memory (기억): 컨텍스트 유지
- Planner (계획자): 작업 분해

### 역사적 타임라인

```
2022년 10월 6일: ReAct 논문 ⭐
                 └─ Reasoning + Acting 패턴 확립

2023년 3월 14일: GPT-4 출시 ⭐
                └─ 강력한 추론 능력

2023년 3월 28-30일: BabyAGI, AutoGPT ⭐
                   └─ 자율 Agent 프레임워크

2023년 6월 13일: Function Calling ⭐
                └─ Agent 실용화 가속

2023년 하반기~: Multi-Agent 시스템 성숙
```

### 왜 지금 "Agent 시대"?

| 이유 | 설명 |
|-----|------|
| **기술 성숙** | LLM 추론 능력 + Function Calling 안정화 |
| **실용적 가치** | LLM은 대화만, Agent는 실제 일 처리 |
| **비용 효율** | 인간 작업의 자동화 (90% 시간 절감) |
| **산업 도입** | 모든 대기업이 Agent 플랫폼 출시 |

### 주요 패턴

1. **ReAct Agent**: Thought → Action → Observation 반복
2. **Plan-and-Execute**: 계획 수립 후 순차 실행
3. **Multi-Agent**: 전문 Agent들의 협업

### 실무 체크리스트

```
✅ 명확한 도구 설명 작성
✅ 에러 처리 및 로깅
✅ 토큰 사용량 모니터링
✅ 무한 루프 방지 (max_iterations)
✅ 에스컬레이션 로직 (인간 개입)
✅ 성능 최적화 (캐싱, 병렬 실행)
✅ 테스트 코드 작성
```

## 관련 문서

- LLM 데이터 전처리의 중요성
- Python의 @abstractmethod와 추상 클래스
- Python Typing (타입 힌팅)
