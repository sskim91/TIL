# Python Typing (타입 힌팅)

> Python의 타입 힌트 시스템과 정적 타입 체킹에 대한 완벽 가이드

## 목차
1. [Python Typing이란?](#python-typing이란)
2. [역사 및 버전별 변화](#역사-및-버전별-변화)
3. [왜 필요한가?](#왜-필요한가)
4. [기본 타입 힌트](#기본-타입-힌트)
5. [컬렉션 타입](#컬렉션-타입)
6. [Optional과 Union](#optional과-union)
7. [제네릭 (Generic)](#제네릭-generic)
8. [Callable (함수 타입)](#callable-함수-타입)
9. [TypedDict](#typeddict)
10. [중요한 특징: 런타임 무시](#중요한-특징-런타임-무시)
11. [타입 체커 도구](#타입-체커-도구)
12. [실전 예제](#실전-예제)
13. [Java와의 비교](#java와의-비교)

---

## Python Typing이란?

**타입 힌트(Type Hints)**는 Python 코드에 타입 정보를 추가하는 기능입니다.

```python
# 타입 힌트 없이
def add(a, b):
    return a + b

# 타입 힌트 사용
def add(a: int, b: int) -> int:
    return a + b
```

**핵심 특징:**
- Python은 **동적 타이핑 언어**이지만, 타입 힌트로 정적 분석 가능
- 타입 힌트는 **런타임에 무시됨** (성능 영향 없음)
- **선택적(Optional)**: 타입 힌트 없어도 코드 실행 가능
- IDE 자동완성, 코드 가독성, 버그 사전 발견에 도움

---

## 역사 및 버전별 변화

### Python 3.5 (2015년) - 타입 힌트 공식 도입
- **PEP 484**: 타입 힌트 공식 표준
- `typing` 모듈 추가

```python
from typing import List, Dict

def process(items: List[int]) -> Dict[str, int]:
    return {"count": len(items)}
```

### Python 3.6 (2016년) - 변수 어노테이션
- **PEP 526**: 변수에도 타입 힌트 가능

```python
# Python 3.6+
name: str = "John"
age: int = 30
scores: List[int] = [90, 85, 88]
```

### Python 3.7 (2018년) - 지연 평가
- **PEP 563**: `from __future__ import annotations`

```python
from __future__ import annotations

class Node:
    def __init__(self, value: int, next: Node | None = None):
        #                              ^^^^^ 순환 참조 해결!
        self.value = value
        self.next = next
```

### Python 3.9 (2020년) - 내장 타입 제네릭
- **PEP 585**: `typing.List` 대신 `list` 사용 가능

```python
# Python 3.9 이전
from typing import List, Dict, Tuple
numbers: List[int] = [1, 2, 3]

# Python 3.9+ (권장!)
numbers: list[int] = [1, 2, 3]
scores: dict[str, int] = {"math": 90}
point: tuple[int, int] = (10, 20)
```

### Python 3.10 (2021년) - Union 타입 연산자
- **PEP 604**: `|` 연산자로 Union 표현

```python
# Python 3.10 이전
from typing import Union, Optional
def process(value: Union[int, str]) -> Optional[str]:
    return None

# Python 3.10+ (더 간단!)
def process(value: int | str) -> str | None:
    return None
```

### Python 3.11 (2022년) - Self 타입
- **PEP 673**: `Self` 타입 추가

```python
from typing import Self

class Builder:
    def set_name(self, name: str) -> Self:  # 자기 자신 반환
        self.name = name
        return self
```

### Python 3.12 (2023년) - 타입 파라미터 문법
- **PEP 695**: 제네릭 문법 개선

```python
# Python 3.12+
def max[T](a: T, b: T) -> T:
    return a if a > b else b

class Stack[T]:
    def __init__(self):
        self.items: list[T] = []
```

---

## 왜 필요한가?

### 1. 동적 타이핑의 문제점

```python
# 타입 힌트 없는 코드
def add(a, b):
    return a + b

result1 = add(1, 2)        # 3 (정수 덧셈)
result2 = add("1", "2")    # "12" (문자열 결합!)
result3 = add(1, "2")      # ❌ TypeError: 런타임에만 발견!
```

**Java에서는?**
```java
// 컴파일 타임에 타입 체크
public int add(int a, int b) {
    return a + b;
}

add(1, "2");  // ❌ 컴파일 에러! 실행 불가
```

### 2. 타입 힌트로 해결

```python
def add(a: int, b: int) -> int:
    return a + b

# IDE가 경고, mypy가 미리 발견!
result = add(1, "2")  # ⚠️ error: Argument 2 has incompatible type "str"
```

### 3. IDE 자동완성 향상

```python
# 타입 힌트 없이
def get_user(user_id):
    return {"name": "John", "age": 30}

user = get_user(1)
user.  # ❓ IDE가 뭘 추천할지 모름

# 타입 힌트 사용
from typing import TypedDict

class User(TypedDict):
    name: str
    age: int

def get_user(user_id: int) -> User:
    return {"name": "John", "age": 30}

user = get_user(1)
user["  # ✅ IDE가 "name", "age" 자동완성!
```

### 4. 코드 가독성 향상

```python
# 타입 힌트 없이 - 뭘 반환하는지 모름
def process_data(data):
    # 100줄의 복잡한 로직...
    return result

# 타입 힌트 - 한눈에 이해 가능!
def process_data(data: dict[str, list[int]]) -> list[tuple[str, float]]:
    # 100줄의 복잡한 로직...
    return result
```

---

## 기본 타입 힌트

### 1. 기본 타입

```python
# 변수 타입 힌트
name: str = "John"
age: int = 30
height: float = 175.5
is_student: bool = True
data: bytes = b"hello"

# 함수 파라미터와 반환값
def greet(name: str) -> str:
    return f"Hello, {name}"

def calculate_age(birth_year: int) -> int:
    return 2024 - birth_year

# 반환값이 없는 경우
def log_message(message: str) -> None:
    print(message)
```

**Java와 비교:**
```python
# Python
def get_user(user_id: int) -> str:
    return "John"

# Java
public String getUser(int userId) {
    return "John";
}
```

### 2. 타입 힌트는 선택적

```python
# 일부만 타입 힌트 사용 가능
def process(a: int, b):  # b는 타입 힌트 없음
    return a + b

# 반환값만 타입 힌트
def calculate(a, b) -> int:
    return a + b
```

---

## 컬렉션 타입

### Python 3.9+ (권장 방식)

```python
# list - 리스트
numbers: list[int] = [1, 2, 3, 4, 5]
names: list[str] = ["John", "Jane", "Bob"]
mixed: list[int | str] = [1, "two", 3]

# dict - 딕셔너리
scores: dict[str, int] = {"math": 90, "english": 85}
user_ages: dict[str, int] = {"John": 30, "Jane": 25}

# tuple - 튜플 (고정 길이)
point: tuple[int, int] = (10, 20)
rgb: tuple[int, int, int] = (255, 0, 0)

# tuple - 가변 길이
numbers: tuple[int, ...] = (1, 2, 3, 4, 5)  # 길이 제한 없음

# set - 집합
unique_ids: set[int] = {1, 2, 3, 4, 5}
tags: set[str] = {"python", "java", "kotlin"}
```

**Java와 비교:**
```python
# Python 3.9+
users: list[str] = ["John", "Jane"]
scores: dict[str, int] = {"math": 90}
point: tuple[int, int] = (10, 20)

# Java
List<String> users = Arrays.asList("John", "Jane");
Map<String, Integer> scores = new HashMap<>();
// Java에는 tuple이 없음 (Pair 클래스 사용)
```

### Python 3.8 이하 (구버전)

```python
from typing import List, Dict, Tuple, Set

numbers: List[int] = [1, 2, 3]
scores: Dict[str, int] = {"math": 90}
point: Tuple[int, int] = (10, 20)
tags: Set[str] = {"python", "java"}
```

### 중첩된 컬렉션

```python
# 리스트의 리스트
matrix: list[list[int]] = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

# 딕셔너리의 리스트
users: list[dict[str, str]] = [
    {"name": "John", "email": "john@example.com"},
    {"name": "Jane", "email": "jane@example.com"}
]

# 복잡한 중첩
data: dict[str, list[tuple[int, str]]] = {
    "results": [(1, "John"), (2, "Jane")]
}
```

---

## Optional과 Union

### Optional (None 가능한 타입)

```python
from typing import Optional

# Optional[T] = T | None
def find_user(user_id: int) -> Optional[str]:
    if user_id == 1:
        return "John"
    return None  # None 반환 가능

# Python 3.10+ (더 간단!)
def find_user(user_id: int) -> str | None:
    if user_id == 1:
        return "John"
    return None
```

**Java와 비교:**
```python
# Python
def find_user(user_id: int) -> str | None:
    return None

# Java (Optional)
public Optional<String> findUser(int userId) {
    return Optional.empty();
}

# Java (Nullable 어노테이션)
@Nullable
public String findUser(int userId) {
    return null;
}
```

### Union (여러 타입 가능)

```python
from typing import Union

# Union[int, str] = int 또는 str
def process_id(user_id: Union[int, str]) -> str:
    if isinstance(user_id, int):
        return f"ID: {user_id}"
    return f"Username: {user_id}"

# Python 3.10+ (더 간단!)
def process_id(user_id: int | str) -> str:
    return str(user_id)

# 여러 타입 가능
def parse_value(value: int | float | str | None) -> str:
    if value is None:
        return "N/A"
    return str(value)
```

### 실전 예제

```python
# 데이터베이스 조회 함수
def get_user_by_id(user_id: int) -> dict[str, str | int] | None:
    """
    사용자 조회
    반환: 사용자 딕셔너리 또는 None (없을 경우)
    """
    # 데이터베이스 조회...
    if found:
        return {"name": "John", "age": 30}
    return None

# 사용
user = get_user_by_id(1)
if user is not None:
    print(user["name"])  # 타입 가드 후 안전하게 사용
```

---

## 제네릭 (Generic)

### 기본 제네릭

```python
from typing import TypeVar, Generic

# 타입 변수 정의
T = TypeVar('T')

class Box(Generic[T]):
    def __init__(self, item: T):
        self.item: T = item

    def get(self) -> T:
        return self.item

    def set(self, item: T) -> None:
        self.item = item

# 사용
int_box: Box[int] = Box(123)
str_box: Box[str] = Box("hello")

print(int_box.get())  # 123 (타입: int)
print(str_box.get())  # "hello" (타입: str)

# ❌ 타입 체커가 경고
int_box.set("wrong")  # error: Argument has incompatible type "str"
```

**Java와 비교:**
```python
# Python
class Box(Generic[T]):
    def __init__(self, item: T):
        self.item = item

    def get(self) -> T:
        return self.item

# Java
public class Box<T> {
    private T item;

    public Box(T item) {
        this.item = item;
    }

    public T get() {
        return item;
    }
}
```

### 제네릭 함수

```python
from typing import TypeVar

T = TypeVar('T')

def first(items: list[T]) -> T | None:
    """리스트의 첫 번째 요소 반환"""
    if items:
        return items[0]
    return None

# 사용
numbers = [1, 2, 3]
result: int | None = first(numbers)  # 타입: int | None

names = ["John", "Jane"]
result: str | None = first(names)  # 타입: str | None
```

### 제약이 있는 제네릭

```python
from typing import TypeVar

# 숫자 타입만 허용
NumType = TypeVar('NumType', int, float)

def add(a: NumType, b: NumType) -> NumType:
    return a + b

add(1, 2)      # ✅ int
add(1.5, 2.5)  # ✅ float
add("1", "2")  # ❌ error: str은 허용 안됨
```

### Python 3.12+ 간소화된 문법

```python
# Python 3.12+
def first[T](items: list[T]) -> T | None:
    if items:
        return items[0]
    return None

class Box[T]:
    def __init__(self, item: T):
        self.item = item
```

---

## Callable (함수 타입)

### 기본 Callable

```python
from typing import Callable

# Callable[[인자타입...], 반환타입]

# (int, int) -> int 형태의 함수
def apply_operation(
    func: Callable[[int, int], int],
    a: int,
    b: int
) -> int:
    return func(a, b)

def add(x: int, y: int) -> int:
    return x + y

def multiply(x: int, y: int) -> int:
    return x * y

# 사용
result1 = apply_operation(add, 5, 3)       # 8
result2 = apply_operation(multiply, 5, 3)  # 15
```

**Java와 비교:**
```python
# Python
def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

# Java (Functional Interface)
public int apply(BiFunction<Integer, Integer, Integer> func, int a, int b) {
    return func.apply(a, b);
}
```

### 인자 없는 Callable

```python
from typing import Callable

# () -> str 형태의 함수
def execute(func: Callable[[], str]) -> str:
    return func()

def get_greeting() -> str:
    return "Hello"

result = execute(get_greeting)  # "Hello"
```

### 실전 예제: 데코레이터

```python
from typing import Callable, TypeVar

T = TypeVar('T')

def log_execution(func: Callable[..., T]) -> Callable[..., T]:
    """함수 실행을 로깅하는 데코레이터"""
    def wrapper(*args, **kwargs) -> T:
        print(f"Executing {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}")
        return result
    return wrapper

@log_execution
def add(a: int, b: int) -> int:
    return a + b

result = add(1, 2)
# 출력:
# Executing add
# Finished add
```

### 콜백 함수

```python
from typing import Callable

def fetch_data(
    url: str,
    on_success: Callable[[dict], None],
    on_error: Callable[[str], None]
) -> None:
    """데이터 조회 후 콜백 실행"""
    try:
        # 데이터 조회...
        data = {"result": "success"}
        on_success(data)
    except Exception as e:
        on_error(str(e))

# 사용
def handle_success(data: dict) -> None:
    print(f"Success: {data}")

def handle_error(error: str) -> None:
    print(f"Error: {error}")

fetch_data("https://api.example.com", handle_success, handle_error)
```

---

## TypedDict

### 기본 TypedDict

```python
from typing import TypedDict

# 딕셔너리 구조 정의
class User(TypedDict):
    id: int
    username: str
    email: str
    age: int

# 사용
def create_user(user: User) -> None:
    print(user["username"])  # IDE가 자동완성!
    # user["unknown"]  # ❌ error: 정의되지 않은 키

user: User = {
    "id": 1,
    "username": "john",
    "email": "john@example.com",
    "age": 30
}

create_user(user)
```

### Optional 필드

```python
from typing import TypedDict, NotRequired

# Python 3.11+
class User(TypedDict):
    id: int
    username: str
    email: str
    age: NotRequired[int]  # 선택적 필드

# Python 3.8-3.10
class User(TypedDict, total=False):
    age: int  # 선택적

class User(TypedDict):
    id: int
    username: str
    email: str
```

### 실전 예제: API 응답

```python
from typing import TypedDict

class APIResponse(TypedDict):
    status: int
    message: str
    data: dict[str, str | int]

class UserResponse(TypedDict):
    id: int
    username: str
    email: str
    created_at: str

def fetch_user(user_id: int) -> APIResponse:
    """사용자 정보 조회 API"""
    return {
        "status": 200,
        "message": "Success",
        "data": {
            "id": 1,
            "username": "john",
            "email": "john@example.com"
        }
    }

# 사용
response = fetch_user(1)
print(response["status"])  # IDE가 자동완성!
```

**Java와 비교:**
```python
# Python TypedDict
class User(TypedDict):
    id: int
    username: str

# Java DTO/Record
public record User(int id, String username) {}
```

---

## 중요한 특징: 런타임 무시

### 타입 힌트는 런타임에 무시됨!

```python
def add(a: int, b: int) -> int:
    return a + b

# ⚠️ 타입 힌트는 런타임에 무시됨!
result = add("Hello", "World")  # ✅ 실행됨! (에러 없음)
print(result)  # "HelloWorld"

# Java였다면?
# public int add(int a, int b) { ... }
# add("Hello", "World");  // ❌ 컴파일 에러! 실행 불가
```

### 타입 체크는 별도 도구 필요

```python
# test.py
def add(a: int, b: int) -> int:
    return a + b

result = add("1", "2")  # 실행은 됨!
```

**타입 체커 실행:**
```bash
# mypy로 타입 체크
$ mypy test.py

# 출력:
# test.py:4: error: Argument 1 to "add" has incompatible type "str"; expected "int"
# test.py:4: error: Argument 2 to "add" has incompatible type "str"; expected "int"
# Found 2 errors in 1 file (checked 1 source file)
```

### 언제 타입 체크가 일어나는가?

| 단계 | Java | Python (타입 힌트) |
|------|------|-------------------|
| **코딩 시** | IDE 경고 | IDE 경고 (타입 체커 활성화 시) |
| **컴파일 시** | 컴파일 에러! | 체크 안함 (컴파일 없음) |
| **타입 체커** | - | mypy/pyright 실행 시 체크 |
| **런타임** | - | 체크 안함 (무시됨!) |

### 런타임 타입 체크가 필요하다면?

```python
# pydantic 사용 (런타임 검증!)
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    username: str
    age: int

try:
    user = User(id="not_int", username="john", age=30)
except ValidationError as e:
    print(e)  # ❌ 런타임에 타입 에러 발생!
    # id: value is not a valid integer
```

---

## 타입 체커 도구

### 1. mypy (가장 유명)

**설치:**
```bash
pip install mypy
```

**사용:**
```bash
# 단일 파일 체크
mypy script.py

# 프로젝트 전체 체크
mypy .

# 엄격 모드
mypy --strict script.py
```

**설정 파일 (mypy.ini):**
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### 2. pyright (Microsoft, VS Code 내장)

**설치:**
```bash
npm install -g pyright
```

**사용:**
```bash
pyright script.py
```

**VS Code 설정:**
```json
{
    "python.analysis.typeCheckingMode": "basic"  // or "strict"
}
```

### 3. pyre (Facebook)

**설치:**
```bash
pip install pyre-check
```

**사용:**
```bash
pyre init
pyre check
```

### IDE 통합

**VS Code:**
- Pylance 확장 설치 (pyright 내장)
- 설정에서 `Type Checking Mode` 활성화

**PyCharm:**
- 기본적으로 타입 힌트 체크 지원
- Settings > Editor > Inspections > Python > Type checker

---

## 실전 예제

### 1. 데이터베이스 모델과 타입 힌트

```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class User:
    id: int
    username: str
    email: str
    created_at: datetime
    age: Optional[int] = None
    is_active: bool = True

def create_user(username: str, email: str) -> User:
    """새 사용자 생성"""
    return User(
        id=1,
        username=username,
        email=email,
        created_at=datetime.now()
    )

def find_user_by_id(user_id: int) -> User | None:
    """ID로 사용자 조회"""
    # 데이터베이스 조회...
    return None

def find_users_by_age(min_age: int, max_age: int) -> list[User]:
    """나이 범위로 사용자 조회"""
    # 데이터베이스 조회...
    return []
```

### 2. API 클라이언트

```python
from typing import TypedDict, Literal
import requests

class APIConfig(TypedDict):
    base_url: str
    api_key: str
    timeout: int

class APIResponse(TypedDict):
    status: Literal["success", "error"]
    data: dict[str, str | int] | None
    message: str

class APIClient:
    def __init__(self, config: APIConfig):
        self.config = config

    def get(self, endpoint: str) -> APIResponse:
        """GET 요청"""
        url = f"{self.config['base_url']}/{endpoint}"
        headers = {"Authorization": f"Bearer {self.config['api_key']}"}

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.config["timeout"]
            )
            return {
                "status": "success",
                "data": response.json(),
                "message": "OK"
            }
        except Exception as e:
            return {
                "status": "error",
                "data": None,
                "message": str(e)
            }

# 사용
config: APIConfig = {
    "base_url": "https://api.example.com",
    "api_key": "secret_key",
    "timeout": 30
}

client = APIClient(config)
response = client.get("users/1")

if response["status"] == "success":
    print(response["data"])
```

### 3. 제네릭 Repository 패턴

```python
from typing import TypeVar, Generic, Protocol
from dataclasses import dataclass

# Entity 프로토콜
class Entity(Protocol):
    id: int

T = TypeVar('T', bound=Entity)

class Repository(Generic[T]):
    """제네릭 Repository"""

    def __init__(self):
        self._storage: dict[int, T] = {}

    def save(self, entity: T) -> T:
        """엔티티 저장"""
        self._storage[entity.id] = entity
        return entity

    def find_by_id(self, entity_id: int) -> T | None:
        """ID로 조회"""
        return self._storage.get(entity_id)

    def find_all(self) -> list[T]:
        """전체 조회"""
        return list(self._storage.values())

    def delete(self, entity_id: int) -> bool:
        """삭제"""
        if entity_id in self._storage:
            del self._storage[entity_id]
            return True
        return False

# 사용
@dataclass
class User:
    id: int
    username: str
    email: str

user_repo: Repository[User] = Repository()

# 저장
user = User(id=1, username="john", email="john@example.com")
user_repo.save(user)

# 조회
found_user = user_repo.find_by_id(1)
all_users = user_repo.find_all()
```

### 4. 함수형 프로그래밍 스타일

```python
from typing import Callable, TypeVar

T = TypeVar('T')
U = TypeVar('U')

def map_list(func: Callable[[T], U], items: list[T]) -> list[U]:
    """함수형 map"""
    return [func(item) for item in items]

def filter_list(predicate: Callable[[T], bool], items: list[T]) -> list[T]:
    """함수형 filter"""
    return [item for item in items if predicate(item)]

def reduce_list(
    func: Callable[[U, T], U],
    items: list[T],
    initial: U
) -> U:
    """함수형 reduce"""
    result = initial
    for item in items:
        result = func(result, item)
    return result

# 사용
numbers = [1, 2, 3, 4, 5]

# map: 각 숫자를 제곱
squared = map_list(lambda x: x ** 2, numbers)  # [1, 4, 9, 16, 25]

# filter: 짝수만 필터링
evens = filter_list(lambda x: x % 2 == 0, numbers)  # [2, 4]

# reduce: 합계 계산
total = reduce_list(lambda acc, x: acc + x, numbers, 0)  # 15
```

---

## Java와의 비교

### 타입 시스템 비교

| 특징 | Java | Python (타입 힌트) |
|------|------|--------------------|
| **타입 체크 시점** | 컴파일 타임 (강제) | 별도 도구 실행 (선택) |
| **런타임 타입 체크** | O | X (무시됨) |
| **타입 추론** | 제한적 (`var`) | 강력함 |
| **제네릭** | O (소거됨) | O (런타임에도 정보 유지) |
| **Null 안전성** | X (NullPointerException) | Optional 사용 |
| **덕 타이핑** | X | O (Protocol) |

### 문법 비교

```python
# ========== 기본 타입 ==========
# Python
def greet(name: str) -> str:
    return f"Hello, {name}"

# Java
public String greet(String name) {
    return "Hello, " + name;
}

# ========== 제네릭 ==========
# Python
class Box(Generic[T]):
    def __init__(self, item: T):
        self.item = item

# Java
public class Box<T> {
    private T item;
    public Box(T item) {
        this.item = item;
    }
}

# ========== 컬렉션 ==========
# Python
users: list[str] = ["John", "Jane"]
scores: dict[str, int] = {"math": 90}

# Java
List<String> users = Arrays.asList("John", "Jane");
Map<String, Integer> scores = new HashMap<>();

# ========== Optional ==========
# Python
def find_user(id: int) -> User | None:
    return None

# Java
public Optional<User> findUser(int id) {
    return Optional.empty();
}

# ========== 함수 타입 ==========
# Python
def apply(func: Callable[[int, int], int]) -> int:
    return func(1, 2)

# Java
public int apply(BiFunction<Integer, Integer, Integer> func) {
    return func.apply(1, 2);
}
```

### 타입 체크 차이

```python
# Python: 런타임에는 타입 무시!
def add(a: int, b: int) -> int:
    return a + b

result = add("1", "2")  # ✅ 실행됨! "12"
# mypy로 실행 전에 체크해야 발견 가능

# Java: 컴파일 시 타입 체크!
public int add(int a, int b) {
    return a + b;
}

add("1", "2");  // ❌ 컴파일 에러! 실행 불가
```

---

## 정리

### 핵심 요점

1. **Python 3.5 (2015)부터 타입 힌트 공식 도입**
2. **런타임에는 무시됨** - 별도 타입 체커(mypy, pyright) 필요
3. **선택적 사용** - 타입 힌트 없어도 코드 실행 가능
4. **Python 3.9+**: `list[int]`, `dict[str, int]` 사용 (권장)
5. **Python 3.10+**: `int | str` 유니온 타입 (권장)
6. **Java와의 차이**: 컴파일 타임 vs 도구 실행 시

### 권장 사항

```python
# ✅ 권장: Python 3.10+ 현대적 문법
def process(value: int | str) -> str | None:
    return str(value) if value else None

users: list[User] = []
config: dict[str, str | int] = {}

# ❌ 비권장: 구식 문법
from typing import Union, Optional, List, Dict

def process(value: Union[int, str]) -> Optional[str]:
    return str(value) if value else None

users: List[User] = []
config: Dict[str, Union[str, int]] = {}
```

### 학습 순서

1. 기본 타입 힌트 (`str`, `int`, `bool`)
2. 컬렉션 (`list[int]`, `dict[str, int]`)
3. Optional/Union (`str | None`, `int | str`)
4. TypedDict (딕셔너리 구조 정의)
5. Generic (고급 - 필요 시)
6. Callable (고급 - 필요 시)

### 타입 체커 설정

```bash
# mypy 설치 및 실행
pip install mypy
mypy your_script.py

# VS Code에서 자동 타입 체크
# settings.json
{
    "python.analysis.typeCheckingMode": "basic"
}
```
