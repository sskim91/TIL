# Python TypedDict vs dataclass vs Pydantic 완전 비교

Python에서 데이터 구조를 정의하는 세 가지 방법의 차이점과 실전 활용 가이드

## 결론부터 말하면

**같은 데이터 구조를 세 가지 방법으로 정의할 수 있습니다:**

```python
# ========== 1. TypedDict - 딕셔너리 + 타입 힌트 ==========
from typing import TypedDict

class User(TypedDict):
    id: int
    name: str

user: User = {"id": 1, "name": "홍길동"}  # 런타임은 일반 dict
print(type(user))  # <class 'dict'>
print(user["name"])  # 딕셔너리 접근


# ========== 2. dataclass - 간단한 클래스 ==========
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str

user = User(id=1, name="홍길동")  # 클래스 객체
print(type(user))  # <class '__main__.User'>
print(user.name)  # 속성 접근


# ========== 3. Pydantic - 런타임 검증 ==========
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

user = User(id=1, name="홍길동")  # 런타임 검증 + 자동 변환
user = User(id="123", name="홍길동")  # ✅ "123" → 123 (자동 변환!)
```

**핵심 차이:**

| 특징 | TypedDict | dataclass | Pydantic |
|------|-----------|-----------|----------|
| **런타임 타입** | `dict` | 클래스 | 클래스 |
| **접근** | `user["name"]` | `user.name` | `user.name` |
| **런타임 검증** | ❌ | ❌ | ✅ |
| **성능** | 가장 빠름 (1x) | 보통 (5x) | 느림 (50x) |
| **사용 케이스** | LangChain State, API 응답 | 내부 데이터 모델 | API 요청 검증 |

**선택 기준:**
- **성능/JSON 직렬화 중요** → `TypedDict`
- **속성 접근/가독성 중요** → `dataclass`
- **외부 입력 검증 필요** → `Pydantic`

## 1. TypedDict - 딕셔너리 타입 정의

### 기본 사용법

```python
from typing import TypedDict

class User(TypedDict):
    id: int
    name: str
    email: str

# ✅ 실제로는 그냥 dict!
user: User = {
    "id": 1,
    "name": "홍길동",
    "email": "hong@example.com"
}

print(type(user))  # <class 'dict'>
print(user["name"])  # 딕셔너리처럼 접근
```

### 주요 특징

```python
from typing import TypedDict, NotRequired

# 선택적 필드
class User(TypedDict):
    id: int
    name: str
    email: NotRequired[str]  # 선택적 필드 (Python 3.11+)

# 또는
class User(TypedDict, total=False):
    email: str  # 선택적 필드

# 사용
user1: User = {"id": 1, "name": "홍길동"}  # ✅ email 없어도 OK
user2: User = {"id": 1, "name": "홍길동", "email": "hong@example.com"}  # ✅ OK
```

### 장점

```python
# 1. 이미 dict라서 변환 불필요
import json

user: User = {"id": 1, "name": "홍길동"}
json.dumps(user)  # ✅ 바로 직렬화 가능!

# 2. 메모리 효율적
import sys
print(sys.getsizeof(user))  # 약 232 bytes (일반 dict와 동일)

# 3. 성능 최고 (런타임 오버헤드 없음)
for i in range(1000000):
    user = {"id": i, "name": f"user_{i}"}  # 가장 빠름
```

### 단점

```python
# ❌ 타입 오류를 런타임에 잡지 못함
user: User = {"id": "not_int", "name": 123}  # 실행됨! (mypy만 경고)

# ❌ 속성으로 접근 불가
user: User = {"id": 1, "name": "홍길동"}
print(user.name)  # ❌ AttributeError! (dict는 속성 접근 불가)
print(user["name"])  # ✅ OK

# ❌ IDE 자동완성 약함
user["  # IDE가 키 자동완성 제공 못할 수 있음
```

## 2. dataclass - 간단한 클래스

### 기본 사용법

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

# ✅ 클래스 인스턴스
user = User(id=1, name="홍길동", email="hong@example.com")

print(type(user))  # <class '__main__.User'>
print(user.name)   # 속성으로 접근
print(user["name"])  # ❌ TypeError! (dict가 아님)
```

### 주요 특징

```python
from dataclasses import dataclass, field, asdict

@dataclass
class User:
    id: int
    name: str
    email: str = "default@example.com"  # 기본값
    tags: list = field(default_factory=list)  # 가변 기본값

# 불변 객체
@dataclass(frozen=True)
class Point:
    x: int
    y: int

point = Point(x=10, y=20)
point.x = 30  # ❌ FrozenInstanceError! (수정 불가)
```

### 장점

```python
# 1. 속성 접근 (.name)
user = User(id=1, name="홍길동", email="hong@example.com")
print(user.name)  # ✅ 가독성 좋음
print(user.email)

# 2. __repr__ 자동 생성
print(user)  # User(id=1, name='홍길동', email='hong@example.com')

# 3. __eq__ 자동 생성
user1 = User(id=1, name="홍길동", email="hong@example.com")
user2 = User(id=1, name="홍길동", email="hong@example.com")
print(user1 == user2)  # ✅ True

# 4. IDE 자동완성 강력
user.  # IDE가 모든 속성 자동완성!
```

### 단점

```python
# ❌ JSON 직렬화 시 변환 필요
import json
from dataclasses import asdict

user = User(id=1, name="홍길동", email="hong@example.com")
json.dumps(user)  # ❌ TypeError!
json.dumps(asdict(user))  # ✅ OK (변환 필요)

# ❌ 타입 오류를 런타임에 잡지 못함
user = User(id="not_int", name=123, email="hong@example.com")
# ✅ 실행됨! (타입 검증 없음)
```

## 3. Pydantic - 데이터 검증

### 기본 사용법

```python
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    id: int
    name: str
    email: EmailStr  # 이메일 형식 검증!
    age: int = Field(gt=0, lt=150)  # 범위 검증

# ✅ 정상 생성
user = User(id=1, name="홍길동", email="hong@example.com", age=30)

# ❌ 런타임 ValidationError 발생!
try:
    user = User(id="not_int", name="홍길동", email="invalid", age=200)
except ValidationError as e:
    print(e)
    # id는 int여야 함!
    # email 형식이 잘못됨!
    # age는 150 미만이어야 함!
```

### 주요 특징

```python
from pydantic import BaseModel, validator

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int

    # 커스텀 검증
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('이름은 비어있을 수 없습니다')
        return v

    @validator('age')
    def age_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('나이는 0 이상이어야 합니다')
        return v
```

### 장점

```python
# 1. 런타임 타입 검증!
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str

try:
    user = User(id="not_int", name="홍길동")
except ValidationError as e:
    print(e)  # ✅ 런타임에 타입 에러 잡음!

# 2. 자동 타입 변환
user = User(id="123", name="홍길동")  # 문자열 "123"
print(user.id)  # 123 (int로 자동 변환!)
print(type(user.id))  # <class 'int'>

# 3. JSON 직렬화/역직렬화 내장
user = User(id=1, name="홍길동")
json_str = user.model_dump_json()  # JSON 문자열
print(json_str)  # '{"id":1,"name":"홍길동"}'

user_dict = user.model_dump()  # dict
print(user_dict)  # {'id': 1, 'name': '홍길동'}

# 4. 복잡한 검증
from pydantic import EmailStr, HttpUrl

class User(BaseModel):
    email: EmailStr  # 이메일 형식 자동 검증
    website: HttpUrl  # URL 형식 자동 검증
    age: int = Field(ge=0, le=150)  # 범위 검증
```

### 단점

```python
# ❌ 성능 오버헤드 (검증 비용)
import time

# TypedDict
start = time.time()
for i in range(100000):
    user = {"id": i, "name": f"user_{i}"}
print(f"TypedDict: {time.time() - start:.2f}초")  # 약 0.05초

# Pydantic
start = time.time()
for i in range(100000):
    user = User(id=i, name=f"user_{i}")
print(f"Pydantic: {time.time() - start:.2f}초")  # 약 2.5초 (50배 느림!)

# ❌ 메모리 사용량 큼
import sys
user_dict = {"id": 1, "name": "홍길동"}
user_pydantic = User(id=1, name="홍길동")

print(sys.getsizeof(user_dict))  # 232 bytes
print(sys.getsizeof(user_pydantic))  # 약 500+ bytes
```

## 4. 핵심 차이 비교

### 비교표

| 특징 | TypedDict | dataclass | Pydantic |
|------|-----------|-----------|----------|
| **런타임 타입** | `dict` | 클래스 객체 | 클래스 객체 |
| **접근 방법** | `user["name"]` | `user.name` | `user.name` |
| **타입 검증** | ❌ (타입 체커만) | ❌ | ✅ 런타임 검증 |
| **데이터 변환** | ❌ | ❌ | ✅ 자동 변환 |
| **직렬화** | 불필요 (이미 dict) | `asdict()` 필요 | `.model_dump()` 내장 |
| **메모리** | 가벼움 (~230B) | 보통 (~300B) | 무거움 (~500B+) |
| **성능** | 빠름 (1x) | 보통 (5x) | 느림 (50x) |
| **JSON 호환** | ✅ 바로 가능 | 변환 필요 | ✅ 바로 가능 |
| **IDE 자동완성** | 약함 | 강력 | 강력 |
| **불변성** | ❌ | `frozen=True` | `frozen=True` |
| **검증 로직** | ❌ | ❌ | ✅ 강력 |

### 언제 타입 체크가 일어나는가?

| 단계 | TypedDict | dataclass | Pydantic |
|------|-----------|-----------|----------|
| **코딩 시** | IDE 경고 | IDE 경고 | IDE 경고 |
| **mypy 실행** | ✅ 체크 | ✅ 체크 | ✅ 체크 |
| **런타임** | ❌ 체크 안함 | ❌ 체크 안함 | ✅ 체크함! |

## 5. 실전 비교 예시

### 타입 검증 비교

```python
from typing import TypedDict
from dataclasses import dataclass
from pydantic import BaseModel, ValidationError

# ========== TypedDict ==========
class UserDict(TypedDict):
    id: int
    name: str

user_dict: UserDict = {"id": "not_int", "name": 123}
print(user_dict)  # ✅ 실행됨! (검증 없음)


# ========== dataclass ==========
@dataclass
class UserDataclass:
    id: int
    name: str

user_dc = UserDataclass(id="not_int", name=123)
print(user_dc)  # ✅ 실행됨! (검증 없음)


# ========== Pydantic ==========
class UserPydantic(BaseModel):
    id: int
    name: str

try:
    user_pd = UserPydantic(id="not_int", name=123)
except ValidationError as e:
    print(e)  # ❌ ValidationError! (런타임 검증)
```

### JSON 직렬화 비교

```python
import json
from typing import TypedDict
from dataclasses import dataclass, asdict
from pydantic import BaseModel

# ========== TypedDict - 가장 간단 ==========
class UserDict(TypedDict):
    id: int
    name: str

user_dict: UserDict = {"id": 1, "name": "홍길동"}
json_str = json.dumps(user_dict)  # ✅ 바로 가능!
print(json_str)  # {"id": 1, "name": "홍길동"}


# ========== dataclass - 변환 필요 ==========
@dataclass
class UserDataclass:
    id: int
    name: str

user_dc = UserDataclass(id=1, name="홍길동")
json.dumps(user_dc)  # ❌ TypeError!
json_str = json.dumps(asdict(user_dc))  # ✅ 변환 후 가능
print(json_str)  # {"id": 1, "name": "홍길동"}


# ========== Pydantic - 내장 메서드 ==========
class UserPydantic(BaseModel):
    id: int
    name: str

user_pd = UserPydantic(id=1, name="홍길동")
json_str = user_pd.model_dump_json()  # ✅ 내장 메서드
print(json_str)  # {"id":1,"name":"홍길동"}
```

### 자동 타입 변환 비교

```python
# ========== TypedDict - 변환 없음 ==========
user_dict: UserDict = {"id": "123", "name": "홍길동"}
print(type(user_dict["id"]))  # <class 'str'> (문자열 그대로)


# ========== dataclass - 변환 없음 ==========
user_dc = UserDataclass(id="123", name="홍길동")
print(type(user_dc.id))  # <class 'str'> (문자열 그대로)


# ========== Pydantic - 자동 변환! ==========
user_pd = UserPydantic(id="123", name="홍길동")
print(type(user_pd.id))  # <class 'int'> (자동 변환!)
print(user_pd.id)  # 123
```

## 6. LangChain 마이그레이션 사례

### 왜 TypedDict만 지원하는가?

LangChain 1.0부터 State는 **TypedDict만 지원**합니다.

**이유:**
1. State는 내부적으로 dict 형태로 전달됨
2. 성능 최적화 (변환/검증 오버헤드 없음)
3. JSON 직렬화 간편

### Before (Pydantic 또는 dataclass)

```python
from pydantic import BaseModel

class AgentState(BaseModel):
    messages: list[str]
    next_step: str | None = None
    user_id: str
    context: dict = {}

# 사용
state = AgentState(
    messages=["안녕하세요"],
    next_step="process",
    user_id="user123",
    context={"session": "abc"}
)

# LangGraph에 전달 시 변환 필요
graph.invoke(state.model_dump())  # dict로 변환
```

### After (TypedDict)

```python
from typing import TypedDict, NotRequired

class AgentState(TypedDict):
    messages: list[str]
    next_step: NotRequired[str]  # 선택적 필드
    user_id: str
    context: NotRequired[dict]

# 사용
state: AgentState = {
    "messages": ["안녕하세요"],
    "next_step": "process",
    "user_id": "user123",
    "context": {"session": "abc"}
}

# LangGraph에 바로 전달
graph.invoke(state)  # ✅ 변환 불필요!
```

### 성능 비교

```python
import time
from langgraph.graph import StateGraph

# ========== Pydantic 사용 시 ==========
start = time.time()
for i in range(10000):
    state = AgentStatePydantic(messages=[f"msg_{i}"], user_id=f"user_{i}")
    graph.invoke(state.model_dump())  # 변환 + 검증
print(f"Pydantic: {time.time() - start:.2f}초")  # 약 3초


# ========== TypedDict 사용 시 ==========
start = time.time()
for i in range(10000):
    state: AgentStateDict = {"messages": [f"msg_{i}"], "user_id": f"user_{i}"}
    graph.invoke(state)  # 변환 없음
print(f"TypedDict: {time.time() - start:.2f}초")  # 약 0.1초 (30배 빠름!)
```

### 마이그레이션 체크리스트

```python
# ❌ Before
from pydantic import BaseModel

class State(BaseModel):
    field1: str
    field2: int | None = None


# ✅ After
from typing import TypedDict, NotRequired

class State(TypedDict):
    field1: str
    field2: NotRequired[int]


# 변환 규칙:
# 1. BaseModel → TypedDict
# 2. field: Type | None = None → field: NotRequired[Type]
# 3. 기본값 제거 (TypedDict는 기본값 지원 안함)
# 4. .model_dump() → 제거 (이미 dict)
```

## 7. 선택 가이드

### 의사결정 플로우차트

```
데이터 구조를 정의해야 한다면?
    │
    ├─ 런타임 검증이 필수? ──────────────→ Pydantic
    │   (외부 입력, API 요청)
    │
    ├─ 속성 접근 선호? ─────────────────→ dataclass
    │   (코드 가독성, IDE 자동완성)
    │
    ├─ dict 형태로 전달? ───────────────→ TypedDict
    │   (LangChain State, API 응답)
    │
    ├─ 성능이 최우선? ─────────────────→ TypedDict
    │   (대량 데이터 처리)
    │
    └─ JSON 직렬화 빈번? ───────────────→ TypedDict
        (REST API, 메시지 큐)
```

### 구체적인 사용 사례

#### ✅ TypedDict를 쓰세요

```python
# 1. LangChain/LangGraph State
from typing import TypedDict
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    messages: list[str]
    next_step: str

graph = StateGraph(AgentState)


# 2. API 응답 구조
class APIResponse(TypedDict):
    status: int
    data: dict
    message: str

def api_handler() -> APIResponse:
    return {
        "status": 200,
        "data": {"user": "홍길동"},
        "message": "Success"
    }


# 3. 설정 파일 구조
class Config(TypedDict):
    db_url: str
    api_key: str
    timeout: int

config: Config = {
    "db_url": "postgresql://...",
    "api_key": "secret",
    "timeout": 30
}
```

#### ✅ dataclass를 쓰세요

```python
# 1. 간단한 데이터 클래스
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

point = Point(x=10, y=20)
print(point.x)  # 속성 접근


# 2. 불변 객체
@dataclass(frozen=True)
class Coordinate:
    lat: float
    lon: float

coord = Coordinate(lat=37.5, lon=127.0)
# coord.lat = 38.0  # ❌ FrozenInstanceError!


# 3. 내부 데이터 모델
@dataclass
class UserProfile:
    user_id: str
    name: str
    age: int
    tags: list = field(default_factory=list)
```

#### ✅ Pydantic을 쓰세요

```python
# 1. API 요청 검증
from pydantic import BaseModel, EmailStr, Field

class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    age: int = Field(gt=0, lt=150)
    password: str = Field(min_length=8)

@app.post("/users")
def create_user(user: UserCreateRequest):
    # ✅ 자동으로 검증됨!
    return {"message": "User created"}


# 2. 환경 변수 검증
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()  # ✅ 환경 변수 자동 로드 + 검증


# 3. 복잡한 데이터 변환
from pydantic import validator

class UserData(BaseModel):
    name: str
    email: str
    age: int

    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('유효한 이메일이 아닙니다')
        return v.lower()  # 소문자로 변환
```

### 비교 요약

| 사용 사례 | TypedDict | dataclass | Pydantic |
|----------|-----------|-----------|----------|
| **LangChain State** | ✅ 필수 | ❌ | ❌ |
| **API 응답** | ✅ 최적 | ⚠️ 변환 필요 | ✅ 좋음 |
| **API 요청 검증** | ❌ | ❌ | ✅ 최적 |
| **내부 데이터 모델** | ⚠️ | ✅ 최적 | ⚠️ 과함 |
| **설정 파일** | ✅ 좋음 | ✅ 좋음 | ✅ 최적 |
| **대량 데이터 처리** | ✅ 최적 | ⚠️ | ❌ 느림 |
| **불변 객체** | ❌ | ✅ frozen | ✅ frozen |
| **JSON 직렬화** | ✅ 최적 | ⚠️ 변환 필요 | ✅ 내장 |

## 8. Java와의 비교

### TypedDict ≈ Map with Type Hints

```python
# ========== Python TypedDict ==========
from typing import TypedDict

class User(TypedDict):
    id: int
    name: str

user: User = {"id": 1, "name": "홍길동"}


# ========== Java Map ==========
// 타입 안전성 없음
Map<String, Object> user = new HashMap<>();
user.put("id", 1);
user.put("name", "홍길동");

// 또는 Record (Java 14+)
public record User(int id, String name) {}
User user = new User(1, "홍길동");
```

### dataclass ≈ Java Record / Lombok @Data

```python
# ========== Python dataclass ==========
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str

user = User(id=1, name="홍길동")


# ========== Java Record (Java 14+) ==========
public record User(int id, String name) {}
User user = new User(1, "홍길동");


# ========== Java Lombok @Data ==========
@Data
public class User {
    private int id;
    private String name;
}
User user = new User();
user.setId(1);
user.setName("홍길동");
```

### Pydantic ≈ Bean Validation (JSR 380)

```python
# ========== Python Pydantic ==========
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int = Field(gt=0, lt=150)

user = User(id=1, name="홍길동", email="hong@example.com", age=30)
# ✅ 자동 검증


# ========== Java Bean Validation ==========
import javax.validation.constraints.*;

public class User {
    @NotNull
    private Integer id;

    @NotBlank
    private String name;

    @Email
    private String email;

    @Min(0) @Max(150)
    private Integer age;
}

// 검증 실행
ValidatorFactory factory = Validation.buildDefaultValidatorFactory();
Validator validator = factory.getValidator();
Set<ConstraintViolation<User>> violations = validator.validate(user);
```

### 런타임 검증 비교

| 언어 | 타입 체크 시점 | 런타임 검증 |
|------|---------------|-------------|
| **Java** | 컴파일 타임 | Bean Validation |
| **Python TypedDict** | mypy 실행 시 | ❌ |
| **Python dataclass** | mypy 실행 시 | ❌ |
| **Python Pydantic** | 런타임 | ✅ |

## 실무 팁

### 1. 성능 순위

```
TypedDict (가장 빠름) > dataclass (보통) > Pydantic (느림)
     1x                    5x                50x
```

### 2. 메모리 순위

```
TypedDict (가장 적음) > dataclass (보통) > Pydantic (많음)
   ~230 bytes            ~300 bytes        ~500+ bytes
```

### 3. 검증 순위

```
Pydantic (런타임 검증) > dataclass/TypedDict (mypy만)
```

### 4. 최종 권장

```python
# ✅ 일반적인 경우
from typing import TypedDict  # 가벼움, 빠름, JSON 직렬화 쉬움

# ✅ 속성 접근 선호
from dataclasses import dataclass  # 가독성, IDE 지원

# ✅ 외부 입력 검증
from pydantic import BaseModel  # 안전, 자동 변환

# ⚠️ LangChain 1.0+
from typing import TypedDict  # 필수! (Pydantic/dataclass 지원 안됨)
```

### 5. 학습 순서

1. **TypedDict** - 가장 간단, 기본 타입 힌트
2. **dataclass** - 클래스 편의성 이해
3. **Pydantic** - 검증이 필요한 경우만

---

## 참고 자료

- [Python TypedDict 공식 문서](https://docs.python.org/3/library/typing.html#typing.TypedDict)
- [dataclass 공식 문서](https://docs.python.org/3/library/dataclasses.html)
- [Pydantic 공식 문서](https://docs.pydantic.dev/)
- [LangChain 1.0 마이그레이션 가이드](https://docs.langchain.com/oss/python/migrate/langchain-v1#state-type-restrictions)
