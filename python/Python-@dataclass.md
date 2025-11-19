# Python @dataclass

Python 3.7+에서 도입된 `@dataclass` 데코레이터에 대해 알아봅니다.

## 결론부터 말하면

`@dataclass`는 **데이터를 저장하는 클래스를 간편하게 만들어주는 데코레이터**로, 반복적인 보일러플레이트 코드를 자동으로 생성해줍니다.

```python
from dataclasses import dataclass

# ✅ dataclass 사용 (5줄)
@dataclass
class Person:
    name: str
    age: int
    email: str

# ❌ 일반 클래스 (15줄+)
class PersonOld:
    def __init__(self, name: str, age: int, email: str):
        self.name = name
        self.age = age
        self.email = email

    def __repr__(self):
        return f"PersonOld(name={self.name!r}, age={self.age!r}, email={self.email!r})"

    def __eq__(self, other):
        if not isinstance(other, PersonOld):
            return NotImplemented
        return (self.name, self.age, self.email) == (other.name, other.age, other.email)
```

## 1. 기본 사용법

### 간단한 데이터 클래스

```python
from dataclasses import dataclass

@dataclass
class User:
    username: str
    email: str
    age: int

# 인스턴스 생성
user = User("hongildong", "hong@example.com", 30)

print(user)
# User(username='hongildong', email='hong@example.com', age=30)

print(user.username)  # "hongildong"
print(user.age)       # 30
```

### 자동 생성되는 메서드

`@dataclass`는 다음 메서드들을 자동으로 생성합니다:

- `__init__`: 생성자
- `__repr__`: 문자열 표현
- `__eq__`: 동등 비교

```python
@dataclass
class Point:
    x: int
    y: int

p1 = Point(1, 2)
p2 = Point(1, 2)
p3 = Point(3, 4)

# __repr__ 자동 생성
print(p1)  # Point(x=1, y=2)

# __eq__ 자동 생성
print(p1 == p2)  # True
print(p1 == p3)  # False
```

## 2. 기본값 설정

### 일반 기본값

```python
@dataclass
class Product:
    name: str
    price: float
    stock: int = 0          # 기본값
    category: str = "기타"   # 기본값

p1 = Product("노트북", 1200000)
print(p1)
# Product(name='노트북', price=1200000, stock=0, category='기타')

p2 = Product("마우스", 35000, stock=150, category="주변기기")
print(p2)
# Product(name='마우스', price=35000, stock=150, category='주변기기')
```

### 주의: 기본값 순서

```python
# ❌ 오류 발생
@dataclass
class Wrong:
    name: str = "default"
    age: int  # 기본값 없는 필드가 뒤에 오면 안 됨!
# TypeError!

# ✅ 올바른 순서
@dataclass
class Correct:
    age: int                   # 기본값 없는 필드가 먼저
    name: str = "default"      # 기본값 있는 필드가 나중
```

## 3. 가변 기본값 (field 사용)

### 문제 상황

```python
# ❌ 위험! 가변 객체를 기본값으로 사용하면 안 됨
@dataclass
class Team:
    name: str
    members: list = []  # ValueError 발생!
# ValueError: mutable default <class 'list'> for field members is not allowed
```

### 해결: field(default_factory)

```python
from dataclasses import dataclass, field

@dataclass
class Team:
    name: str
    members: list = field(default_factory=list)  # 매번 새 리스트 생성

team1 = Team("개발팀")
team2 = Team("디자인팀")

team1.members.append("홍길동")
team2.members.append("김철수")

print(team1.members)  # ["홍길동"]
print(team2.members)  # ["김철수"] - 독립적!
```

### 다양한 default_factory

```python
from dataclasses import dataclass, field
from typing import Dict, Set
from datetime import datetime

@dataclass
class UserProfile:
    username: str
    tags: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    roles: set = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)

profile = UserProfile("hong")
print(profile.tags)        # []
print(profile.metadata)    # {}
print(profile.roles)       # set()
print(profile.created_at)  # 현재 시간
```

## 4. dataclass 옵션

### 주요 파라미터

```python
@dataclass(
    init=True,        # __init__ 생성 (기본: True)
    repr=True,        # __repr__ 생성 (기본: True)
    eq=True,          # __eq__ 생성 (기본: True)
    order=False,      # __lt__, __le__, __gt__, __ge__ 생성 (기본: False)
    frozen=False,     # 불변 객체로 만들기 (기본: False)
    unsafe_hash=False # __hash__ 생성 (기본: False)
)
class Example:
    value: int
```

### frozen=True (불변 객체)

```python
@dataclass(frozen=True)
class Point:
    x: int
    y: int

p = Point(1, 2)

# ❌ 값 변경 불가
try:
    p.x = 10
except Exception as e:
    print(e)  # FrozenInstanceError: cannot assign to field 'x'

# ✅ dictionary 키로 사용 가능
points = {Point(1, 2): "origin", Point(3, 4): "other"}
print(points[Point(1, 2)])  # "origin"
```

### order=True (정렬 가능)

```python
@dataclass(order=True)
class Student:
    name: str
    score: int

students = [
    Student("홍길동", 85),
    Student("김철수", 92),
    Student("이영희", 78)
]

# 필드 순서대로 비교 (name -> score)
sorted_students = sorted(students)
for s in sorted_students:
    print(s)
# Student(name='김철수', score=92)
# Student(name='이영희', score=78)
# Student(name='홍길동', score=85)
```

## 5. field 옵션

### repr=False (민감한 정보 숨기기)

```python
from dataclasses import dataclass, field

@dataclass
class User:
    username: str
    email: str
    password: str = field(repr=False)  # __repr__에서 숨김

user = User("hong", "hong@example.com", "secret123")
print(user)
# User(username='hong', email='hong@example.com')
# password는 출력 안 됨!
```

### init=False (초기화 후 설정)

```python
@dataclass
class Rectangle:
    width: float
    height: float
    area: float = field(init=False)  # __init__에 포함 안 함

    def __post_init__(self):
        self.area = self.width * self.height

rect = Rectangle(10, 5)
# Rectangle(width=10, height=5) 형태로만 생성 가능
print(rect.area)  # 50.0
```

### compare=False (비교에서 제외)

```python
@dataclass
class User:
    user_id: int
    username: str
    last_login: str = field(compare=False)  # 비교 시 무시

user1 = User(1, "hong", "2025-01-01")
user2 = User(1, "hong", "2025-01-15")

print(user1 == user2)  # True (last_login은 비교 안 함)
```

## 6. __post_init__ (초기화 후 처리)

### 계산된 필드

```python
@dataclass
class Circle:
    radius: float
    area: float = field(init=False)
    circumference: float = field(init=False)

    def __post_init__(self):
        self.area = 3.14159 * self.radius ** 2
        self.circumference = 2 * 3.14159 * self.radius

circle = Circle(5)
print(f"반지름: {circle.radius}")        # 반지름: 5
print(f"넓이: {circle.area:.2f}")        # 넓이: 78.54
print(f"둘레: {circle.circumference:.2f}")  # 둘레: 31.42
```

### 값 검증

```python
@dataclass
class User:
    username: str
    age: int

    def __post_init__(self):
        if self.age < 0:
            raise ValueError("나이는 0보다 작을 수 없습니다")
        if len(self.username) < 3:
            raise ValueError("사용자명은 최소 3자 이상이어야 합니다")

# ✅ 정상
user1 = User("hongildong", 30)

# ❌ 오류 발생
try:
    user2 = User("ho", 30)
except ValueError as e:
    print(e)  # 사용자명은 최소 3자 이상이어야 합니다

try:
    user3 = User("hong", -5)
except ValueError as e:
    print(e)  # 나이는 0보다 작을 수 없습니다
```

### 타입 변환

```python
@dataclass
class Product:
    name: str
    price: float

    def __post_init__(self):
        # 문자열로 들어온 price를 float로 변환
        if isinstance(self.price, str):
            self.price = float(self.price)

p = Product("노트북", "1200000")
print(p.price)        # 1200000.0 (float로 변환됨)
print(type(p.price))  # <class 'float'>
```

## 7. 상속

### 기본 상속

```python
@dataclass
class Person:
    name: str
    age: int

@dataclass
class Employee(Person):
    employee_id: int
    department: str

emp = Employee("홍길동", 30, 12345, "개발팀")
print(emp)
# Employee(name='홍길동', age=30, employee_id=12345, department='개발팀')
```

### 필드 순서 주의

```python
# ❌ 오류 발생
@dataclass
class Parent:
    name: str
    age: int = 0  # 기본값 있음

@dataclass
class Child(Parent):
    student_id: int  # 기본값 없는 필드가 뒤에 오면 안 됨!
# TypeError!

# ✅ 올바른 방법
@dataclass
class ChildCorrect(Parent):
    student_id: int
    grade: str = "A"  # 기본값 있는 필드는 뒤에
```

## 8. asdict와 astuple

### 딕셔너리로 변환

```python
from dataclasses import dataclass, asdict

@dataclass
class User:
    username: str
    email: str
    age: int

user = User("hong", "hong@example.com", 30)

# 딕셔너리로 변환
user_dict = asdict(user)
print(user_dict)
# {'username': 'hong', 'email': 'hong@example.com', 'age': 30}

# JSON 직렬화에 유용
import json
json_str = json.dumps(user_dict)
print(json_str)
# {"username": "hong", "email": "hong@example.com", "age": 30}
```

### 튜플로 변환

```python
from dataclasses import astuple

user = User("hong", "hong@example.com", 30)

# 튜플로 변환
user_tuple = astuple(user)
print(user_tuple)
# ('hong', 'hong@example.com', 30)

# 언패킹
username, email, age = astuple(user)
print(username)  # hong
print(email)     # hong@example.com
print(age)       # 30
```

## 9. 실전 예시

### API 응답 모델

```python
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime

@dataclass
class Comment:
    id: int
    author: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Post:
    id: int
    title: str
    content: str
    author: str
    tags: List[str] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    views: int = 0
    created_at: datetime = field(default_factory=datetime.now)

# 사용
post = Post(
    id=1,
    title="Python dataclass 완전 정복",
    content="dataclass는 데이터 클래스를 쉽게 만들어줍니다.",
    author="홍길동",
    tags=["python", "tutorial"]
)

post.comments.append(Comment(1, "김철수", "좋은 글 감사합니다!"))
post.views += 1

print(post)

# JSON으로 변환
post_dict = asdict(post)
```

### 설정 관리

```python
from dataclasses import dataclass, field
import os

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: str = field(default="", repr=False)  # 비밀번호 숨김
    database: str = "mydb"

    @classmethod
    def from_env(cls):
        """환경 변수에서 설정 로드"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            username=os.getenv("DB_USERNAME", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_DATABASE", "mydb")
        )

    def get_connection_string(self):
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class AppConfig:
    debug: bool = False
    port: int = 8000
    secret_key: str = field(repr=False)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

# 사용
config = AppConfig(
    debug=True,
    port=8080,
    secret_key="my-secret-key",
    database=DatabaseConfig.from_env()
)

print(config)
# AppConfig(debug=True, port=8080, database=DatabaseConfig(...))
# secret_key는 출력 안 됨
```

### 이벤트 로깅

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class LogEntry:
    message: str
    level: LogLevel = LogLevel.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        ctx = ", ".join(f"{k}={v}" for k, v in self.context.items())
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {self.level.value}: {self.message} | {ctx}"

# 사용
log = LogEntry(
    message="User login successful",
    level=LogLevel.INFO,
    context={"user_id": 123, "ip": "192.168.1.1"}
)
print(log)
# [2025-01-13 14:30:45] INFO: User login successful | user_id=123, ip=192.168.1.1
```

### DTO (Data Transfer Object)

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CreateUserRequest:
    """사용자 생성 요청 DTO"""
    username: str
    email: str
    password: str = field(repr=False)
    age: Optional[int] = None

    def __post_init__(self):
        # 유효성 검증
        if not self.username or len(self.username) < 3:
            raise ValueError("사용자명은 3자 이상이어야 합니다")
        if "@" not in self.email:
            raise ValueError("올바른 이메일 형식이 아닙니다")
        if len(self.password) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다")
        if self.age is not None and self.age < 0:
            raise ValueError("나이는 0 이상이어야 합니다")

@dataclass
class UserResponse:
    """사용자 응답 DTO"""
    id: int
    username: str
    email: str
    age: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    # password는 응답에 포함하지 않음

# 사용
request = CreateUserRequest(
    username="hongildong",
    email="hong@example.com",
    password="secret123456",
    age=30
)

# 서비스 계층에서 처리 후
response = UserResponse(
    id=1,
    username=request.username,
    email=request.email,
    age=request.age
)

print(response)
# UserResponse(id=1, username='hongildong', email='hong@example.com', age=30, created_at=...)
```

## 10. dataclass vs NamedTuple vs 일반 클래스

### 비교표

| 특징 | 일반 클래스 | dataclass | NamedTuple |
|------|------------|-----------|------------|
| **간결함** | ❌ 보일러플레이트 많음 | ✅ 간결 | ✅ 매우 간결 |
| **가변성** | ✅ 가변 | ✅ 가변 (frozen=False) | ❌ 불변 |
| **메서드 추가** | ✅ 자유롭게 | ✅ 자유롭게 | ✅ 가능 |
| **상속** | ✅ 자유롭게 | ✅ 가능 | ⚠️ 제한적 |
| **기본값** | ✅ 설정 가능 | ✅ 설정 가능 | ✅ 설정 가능 |
| **타입 힌트** | ⚠️ 수동 | ✅ 필수 | ✅ 필수 |
| **dict 키 사용** | ❌ (기본) | ⚠️ frozen=True 필요 | ✅ 기본 지원 |

### 코드 비교

```python
from dataclasses import dataclass
from typing import NamedTuple

# 1. 일반 클래스 (가장 유연)
class PersonClass:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def __repr__(self):
        return f"PersonClass(name={self.name!r}, age={self.age!r})"

    def __eq__(self, other):
        if not isinstance(other, PersonClass):
            return NotImplemented
        return (self.name, self.age) == (other.name, other.age)

    def greet(self):
        return f"안녕하세요, {self.name}입니다"

# 2. dataclass (중간)
@dataclass
class PersonDataclass:
    name: str
    age: int

    def greet(self):
        return f"안녕하세요, {self.name}입니다"

# 3. NamedTuple (불변)
class PersonTuple(NamedTuple):
    name: str
    age: int

    def greet(self):
        return f"안녕하세요, {self.name}입니다"
```

### 언제 무엇을 쓸까?

```python
# ✅ 불변 데이터 + 간단한 구조 → NamedTuple
class Point(NamedTuple):
    x: int
    y: int

# ✅ 데이터 중심 + 간결함 필요 → dataclass
@dataclass
class User:
    username: str
    email: str
    age: int

# ✅ 복잡한 로직 + 많은 메서드 → 일반 클래스
class UserService:
    def __init__(self, db_connection):
        self.db = db_connection

    def authenticate(self, username, password):
        # 복잡한 인증 로직
        pass

    def get_user(self, user_id):
        # DB 조회 로직
        pass
```

## 11. 주의사항

### 1. 타입 힌트 필수

```python
# ❌ 타입 힌트 없으면 dataclass 필드로 인식 안 됨
@dataclass
class Wrong:
    name = "default"  # 클래스 변수로 인식됨 (dataclass 필드 아님!)

# ✅ 타입 힌트 필수
@dataclass
class Correct:
    name: str = "default"  # dataclass 필드
```

### 2. 가변 기본값 금지

```python
# ❌ 절대 안 됨
@dataclass
class Wrong:
    items: list = []  # ValueError!

# ✅ field(default_factory) 사용
@dataclass
class Correct:
    items: list = field(default_factory=list)
```

### 3. slots 사용 (Python 3.10+)

```python
# 메모리 최적화
@dataclass(slots=True)
class Point:
    x: int
    y: int

# 장점:
# - 더 적은 메모리 사용
# - 속성 접근 속도 향상
# 단점:
# - __dict__가 없어서 동적 속성 추가 불가
```

### 4. kw_only (Python 3.10+)

```python
# 키워드 전용 인수로 강제
@dataclass(kw_only=True)
class Config:
    host: str
    port: int

# ❌ 위치 인수 불가
# config = Config("localhost", 8080)  # TypeError!

# ✅ 키워드 인수만 가능
config = Config(host="localhost", port=8080)
```

## 12. 고급 활용

### 중첩된 dataclass

```python
@dataclass
class Address:
    street: str
    city: str
    zipcode: str

@dataclass
class Person:
    name: str
    age: int
    address: Address

person = Person(
    name="홍길동",
    age=30,
    address=Address("강남대로 123", "서울", "06000")
)

print(person)
# Person(name='홍길동', age=30, address=Address(street='강남대로 123', city='서울', zipcode='06000'))

# asdict로 중첩 변환
from dataclasses import asdict
print(asdict(person))
# {'name': '홍길동', 'age': 30, 'address': {'street': '강남대로 123', 'city': '서울', 'zipcode': '06000'}}
```

### 팩토리 메서드 패턴

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class User:
    id: int
    username: str
    email: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """딕셔너리에서 User 생성"""
        return cls(
            id=data['id'],
            username=data['username'],
            email=data['email']
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'User':
        """JSON 문자열에서 User 생성"""
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)

# 사용
user_data = {"id": 1, "username": "hong", "email": "hong@example.com"}
user = User.from_dict(user_data)

json_str = '{"id": 2, "username": "kim", "email": "kim@example.com"}'
user2 = User.from_json(json_str)
```

## 요약

### dataclass란?

데이터를 저장하는 클래스를 **간편하게 만들어주는 데코레이터**로, 보일러플레이트 코드를 자동 생성합니다.

### 핵심 기능

```python
from dataclasses import dataclass, field

@dataclass(frozen=True, order=True)
class Person:
    name: str
    age: int = 0
    tags: list = field(default_factory=list, repr=False)

    def __post_init__(self):
        if self.age < 0:
            raise ValueError("나이는 0 이상이어야 합니다")
```

### 자동 생성되는 것들

- `__init__`: 생성자
- `__repr__`: 문자열 표현
- `__eq__`: 동등 비교
- `__hash__`: 해시 (frozen=True 일 때)
- `__lt__`, `__le__`, `__gt__`, `__ge__`: 순서 비교 (order=True 일 때)

### 주요 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `init` | `__init__` 생성 | True |
| `repr` | `__repr__` 생성 | True |
| `eq` | `__eq__` 생성 | True |
| `order` | 비교 메서드 생성 | False |
| `frozen` | 불변 객체 | False |
| `slots` | `__slots__` 사용 (3.10+) | False |
| `kw_only` | 키워드 전용 인수 (3.10+) | False |

### 언제 사용?

**✅ 사용하기 좋은 경우:**
- 데이터를 저장하는 간단한 클래스
- 설정 객체, 모델, DTO (Data Transfer Object)
- API 응답/요청 모델
- 보일러플레이트 코드 줄이기

**❌ 사용하지 않는 것이 좋은 경우:**
- 복잡한 비즈니스 로직이 많은 클래스
- 많은 메서드와 상태 관리가 필요한 경우
- 상속 구조가 복잡한 경우

### 빠른 참조

```python
from dataclasses import dataclass, field

@dataclass
class Example:
    # 필수 필드
    required_field: str

    # 기본값
    optional_field: int = 0

    # 가변 기본값
    items: list = field(default_factory=list)

    # __repr__에서 숨김
    secret: str = field(repr=False)

    # 초기화에서 제외
    computed: float = field(init=False)

    # 비교에서 제외
    metadata: dict = field(default_factory=dict, compare=False)

    def __post_init__(self):
        # 초기화 후 처리
        self.computed = self.required_field * self.optional_field
```

## 참고 자료

- [PEP 557 - Data Classes](https://www.python.org/dev/peps/pep-0557/)
- [Python 공식 문서 - dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [Real Python - Python Data Classes](https://realpython.com/python-data-classes/)
