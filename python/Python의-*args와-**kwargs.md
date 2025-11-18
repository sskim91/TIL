# Python의 *args와 **kwargs 완전 정복

Python에서 가변 인자를 받는 `*args`와 `**kwargs`에 대해 알아봅니다.

## 결론부터 말하면

- `*args`: **위치 인자**(positional arguments)를 **튜플**로 받음
- `**kwargs`: **키워드 인자**(keyword arguments)를 **딕셔너리**로 받음
- 함수가 임의의 개수의 인자를 유연하게 받을 수 있게 해줌

## 1. **kwargs (Keyword Arguments)

### 기본 사용법

```python
def print_info(**kwargs):
    print(type(kwargs))  # <class 'dict'>
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name="홍길동", age=30, city="서울")
# 출력:
# name: 홍길동
# age: 30
# city: 서울
```

### 실제 활용 예시: 옵션 전달

```python
def invoke(self, message: str, **kwargs) -> dict:
    """유연하게 추가 옵션을 받는 함수"""
    response = self.agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        **kwargs  # 받은 키워드 인자를 그대로 전달
    )
    return response

# 사용 예시
invoke("안녕하세요")  # 기본 옵션만
invoke("안녕하세요", temperature=0.7)  # 온도 설정
invoke("안녕하세요", temperature=0.7, max_tokens=100)  # 여러 옵션
```

### **kwargs를 풀어서 전달하기

```python
def create_user(name, age, city):
    print(f"{name}, {age}세, {city} 거주")

user_data = {
    "name": "김철수",
    "age": 25,
    "city": "부산"
}

# **를 사용해 딕셔너리를 키워드 인자로 풀어서 전달
create_user(**user_data)
# 출력: 김철수, 25세, 부산 거주

# 위와 동일
create_user(name="김철수", age=25, city="부산")
```

## 2. *args (Positional Arguments)

### 기본 사용법

```python
def sum_all(*args):
    print(type(args))  # <class 'tuple'>
    return sum(args)

result = sum_all(1, 2, 3, 4, 5)
print(result)  # 15
```

### 실제 활용 예시: 가변 개수 인자

```python
def make_sentence(*words):
    return " ".join(words)

print(make_sentence("안녕하세요"))
# 출력: 안녕하세요

print(make_sentence("오늘", "날씨가", "좋네요"))
# 출력: 오늘 날씨가 좋네요
```

### *args를 풀어서 전달하기

```python
def multiply(a, b, c):
    return a * b * c

numbers = [2, 3, 4]

# *를 사용해 리스트를 위치 인자로 풀어서 전달
result = multiply(*numbers)
print(result)  # 24

# 위와 동일
result = multiply(2, 3, 4)
```

## 3. *args와 **kwargs 함께 사용하기

### 올바른 순서

```python
def complex_function(a, b, *args, **kwargs):
    print(f"일반 인자: a={a}, b={b}")
    print(f"추가 위치 인자: {args}")
    print(f"키워드 인자: {kwargs}")

complex_function(1, 2, 3, 4, 5, name="홍길동", age=30)
# 출력:
# 일반 인자: a=1, b=2
# 추가 위치 인자: (3, 4, 5)
# 키워드 인자: {'name': '홍길동', 'age': 30}
```

### 인자 순서 규칙

```python
# ✅ 올바른 순서
def func(pos1, pos2, *args, key1=None, **kwargs):
    pass

# ❌ 잘못된 순서 - SyntaxError
def func(**kwargs, *args):  # kwargs가 args보다 먼저 올 수 없음
    pass
```

**순서 규칙:**
1. 일반 위치 인자
2. `*args`
3. 키워드 전용 인자
4. `**kwargs`

## 4. 실무 활용 패턴

### 패턴 1: 함수 래핑 (Wrapper)

```python
def debug_wrapper(func):
    """함수 호출을 디버깅하는 래퍼"""
    def wrapper(*args, **kwargs):
        print(f"함수 호출: {func.__name__}")
        print(f"위치 인자: {args}")
        print(f"키워드 인자: {kwargs}")
        result = func(*args, **kwargs)  # 원본 함수에 전달
        print(f"반환값: {result}")
        return result
    return wrapper

@debug_wrapper
def add(a, b):
    return a + b

add(3, 5)
# 출력:
# 함수 호출: add
# 위치 인자: (3, 5)
# 키워드 인자: {}
# 반환값: 8
```

### 패턴 2: 옵션 병합

```python
def api_call(endpoint, **kwargs):
    """기본 옵션과 사용자 옵션을 병합"""
    default_options = {
        "timeout": 30,
        "retries": 3,
        "verify_ssl": True
    }

    # 사용자 옵션이 기본값을 덮어씀
    options = {**default_options, **kwargs}

    print(f"API 호출: {endpoint}")
    print(f"옵션: {options}")

api_call("/users", timeout=60, api_key="secret123")
# 출력:
# API 호출: /users
# 옵션: {'timeout': 60, 'retries': 3, 'verify_ssl': True, 'api_key': 'secret123'}
```

### 패턴 3: 필수/선택 인자 조합

```python
def create_account(username, email, *groups, **metadata):
    """
    사용자 계정 생성

    Args:
        username: 필수 - 사용자명
        email: 필수 - 이메일
        *groups: 선택 - 소속 그룹들
        **metadata: 선택 - 추가 메타데이터
    """
    print(f"사용자: {username}")
    print(f"이메일: {email}")
    print(f"그룹: {groups}")
    print(f"메타데이터: {metadata}")

create_account(
    "hong123",
    "hong@example.com",
    "developers",
    "admins",
    department="IT",
    location="Seoul"
)
# 출력:
# 사용자: hong123
# 이메일: hong@example.com
# 그룹: ('developers', 'admins')
# 메타데이터: {'department': 'IT', 'location': 'Seoul'}
```

## 5. 헷갈리는 포인트

### 이름은 중요하지 않음

```python
# 관례적으로 args, kwargs를 사용하지만
def func1(*args, **kwargs):
    pass

# 다른 이름도 가능 (하지만 비추천)
def func2(*numbers, **options):
    pass

# 중요한 건 *, ** 기호!
```

### 언패킹(Unpacking) vs 패킹(Packing)

```python
# 패킹(Packing): 여러 인자를 하나로 모음
def func(*args):
    print(args)  # 튜플로 패킹됨

func(1, 2, 3)  # (1, 2, 3)

# 언패킹(Unpacking): 하나를 여러 인자로 풀어냄
numbers = [1, 2, 3]
print(*numbers)  # 1 2 3 (풀어서 전달)
```

### 딕셔너리 병합 시 주의사항

```python
dict1 = {"a": 1, "b": 2}
dict2 = {"b": 3, "c": 4}

# 뒤쪽 딕셔너리 값이 우선
merged = {**dict1, **dict2}
print(merged)  # {'a': 1, 'b': 3, 'c': 4}

# 순서를 바꾸면 결과가 달라짐
merged = {**dict2, **dict1}
print(merged)  # {'b': 2, 'c': 4, 'a': 1}
```

## 6. 타입 힌팅

Python 3.5+ 에서는 타입 힌트를 추가할 수 있습니다:

```python
from typing import Any

def process_data(*args: int, **kwargs: str) -> dict[str, Any]:
    """
    타입 힌트 예시

    Args:
        *args: 정수 값들
        **kwargs: 문자열 값들
    """
    return {
        "numbers": args,
        "options": kwargs
    }

# 사용
result = process_data(1, 2, 3, name="test", mode="debug")
```

## 7. 실전 예시: 유연한 로거

```python
class Logger:
    def log(self, level: str, message: str, **context):
        """
        유연한 로깅 시스템

        Args:
            level: 로그 레벨 (INFO, ERROR 등)
            message: 로그 메시지
            **context: 추가 컨텍스트 정보
        """
        log_entry = {
            "level": level,
            "message": message,
            "timestamp": "2025-01-10 12:00:00"
        }

        # context 정보를 병합
        if context:
            log_entry["context"] = context

        print(log_entry)

logger = Logger()

# 기본 로깅
logger.log("INFO", "서버 시작")

# 추가 정보와 함께
logger.log("ERROR", "DB 연결 실패",
          host="localhost",
          port=5432,
          retry_count=3)
```

## 요약 정리

| 구분 | 문법 | 받는 형태 | 용도 | 예시 |
|------|------|----------|------|------|
| **`*args`** | `def f(*args)` | 튜플 | 가변 위치 인자 | `f(1, 2, 3)` |
| **`**kwargs`** | `def f(**kwargs)` | 딕셔너리 | 가변 키워드 인자 | `f(a=1, b=2)` |
| **언패킹 `*`** | `f(*list)` | - | 시퀀스를 인자로 풀기 | `f(*[1,2,3])` |
| **언패킹 `**`** | `f(**dict)` | - | 딕셔너리를 키워드 인자로 풀기 | `f(**{"a":1})` |

**핵심 포인트:**
- `*`는 위치 인자, `**`는 키워드 인자
- 패킹(모으기)과 언패킹(풀기) 모두 가능
- 함수 시그니처에서 올바른 순서 지키기
- 유연한 API 설계에 필수적인 패턴

## 참고 자료

- [Python Documentation - More on Defining Functions](https://docs.python.org/3/tutorial/controlflow.html#more-on-defining-functions)
- [PEP 3102 - Keyword-Only Arguments](https://www.python.org/dev/peps/pep-3102/)
- [Real Python - *args and **kwargs](https://realpython.com/python-kwargs-and-args/)

