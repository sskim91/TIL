# Python 언패킹

JavaScript의 구조 분해 할당(Destructuring)을 아는가? Python에도 비슷한 기능이 있다. **언패킹(Unpacking)** 이라고 부른다.

## 결론부터 말하면

**Python 언패킹은 시퀀스(리스트, 튜플)의 요소를 여러 변수에 한 번에 할당하는 문법이다.**

```python
# Python 언패킹
a, b, c = [1, 2, 3]

# JavaScript 구조 분해
# const [a, b, c] = [1, 2, 3];
```

| 기능 | Python | JavaScript |
|------|--------|------------|
| 배열/리스트 | `a, b = [1, 2]` | `[a, b] = [1, 2]` |
| 나머지 요소 | `a, *rest = [1,2,3]` | `[a, ...rest] = [1,2,3]` |
| 객체/딕셔너리 | ❌ 직접 불가 | ✅ `{a, b} = obj` |
| 기본값 | ❌ 없음 | ✅ `[a=1] = []` |

---

## 1. 왜 언패킹이 필요한가?

### 1.1 언패킹 없이 코드 작성

```python
# 함수가 여러 값을 반환할 때
result = get_user_info()  # ["John", 30, "john@example.com"]

name = result[0]
age = result[1]
email = result[2]
```

인덱스로 접근하면:
- 코드가 길어진다
- `result[0]`이 뭔지 한눈에 안 보인다
- 실수하기 쉽다

### 1.2 언패킹으로 개선

```python
name, age, email = get_user_info()
```

한 줄로 끝. 변수명으로 의미도 명확하다.

---

## 2. 기본 언패킹

### 2.1 리스트/튜플 언패킹

```python
# 리스트 언패킹
x, y, z = [1, 2, 3]
print(x, y, z)  # 1 2 3

# 튜플 언패킹
a, b = (10, 20)
print(a, b)  # 10 20

# 괄호 생략 가능
c, d = 100, 200
print(c, d)  # 100 200
```

### 2.2 개수가 맞아야 한다

```python
# ❌ ValueError: too many values to unpack
a, b = [1, 2, 3]

# ❌ ValueError: not enough values to unpack
a, b, c = [1, 2]
```

Java로 치면 배열 길이 불일치 예외와 비슷하다.

### 2.3 문자열도 가능

```python
a, b, c = "ABC"
print(a, b, c)  # A B C
```

문자열도 시퀀스이므로 언패킹된다.

---

## 3. 확장 언패킹 (*)

### 3.1 나머지 요소 받기

개수가 맞지 않을 때 `*`로 나머지를 리스트로 받을 수 있다.

```python
first, *rest = [1, 2, 3, 4, 5]
print(first)  # 1
print(rest)   # [2, 3, 4, 5]

*start, last = [1, 2, 3, 4, 5]
print(start)  # [1, 2, 3, 4]
print(last)   # 5

first, *middle, last = [1, 2, 3, 4, 5]
print(first)   # 1
print(middle)  # [2, 3, 4]
print(last)    # 5
```

JavaScript의 `...rest`와 동일한 역할이다.

### 3.2 요소가 부족해도 빈 리스트

```python
first, *rest = [1]
print(first)  # 1
print(rest)   # [] (빈 리스트)

first, *middle, last = [1, 2]
print(first)   # 1
print(middle)  # [] (빈 리스트)
print(last)    # 2
```

### 3.3 * 는 하나만 사용 가능

```python
# ❌ SyntaxError: multiple starred expressions
*a, *b = [1, 2, 3, 4, 5]
```

---

## 4. 무시하기 (_)

필요 없는 값은 `_`로 무시할 수 있다.

```python
# 두 번째 값만 필요할 때
_, important, _ = [1, 2, 3]
print(important)  # 2

# 첫 번째만 필요하고 나머지 무시
first, *_ = [1, 2, 3, 4, 5]
print(first)  # 1

# 마지막만 필요
*_, last = [1, 2, 3, 4, 5]
print(last)  # 5
```

`_`는 "이 값은 사용하지 않겠다"는 관례적 표현이다.

---

## 5. 중첩 언패킹

리스트 안의 리스트도 언패킹할 수 있다.

```python
# 중첩 구조
data = [1, [2, 3], 4]

a, (b, c), d = data
print(a, b, c, d)  # 1 2 3 4

# 더 복잡한 구조
nested = [[1, 2], [3, 4]]
(a, b), (c, d) = nested
print(a, b, c, d)  # 1 2 3 4
```

### 실무 예제: 좌표 처리

```python
points = [(0, 0), (1, 2), (3, 4)]

for x, y in points:
    print(f"x={x}, y={y}")

# x=0, y=0
# x=1, y=2
# x=3, y=4
```

---

## 6. 딕셔너리 언패킹의 한계

**Python은 JavaScript처럼 딕셔너리를 키 이름으로 언패킹할 수 없다.**

```javascript
// ✅ JavaScript - 객체 구조 분해
const { name, age } = { name: "John", age: 30 };
```

```python
# ❌ Python - 문법 오류
{ name, age } = {"name": "John", "age": 30}

# ✅ Python - 직접 접근
data = {"name": "John", "age": 30}
name = data["name"]
age = data["age"]

# ✅ 또는 .values() 사용 (순서 보장 Python 3.7+)
name, age = {"name": "John", "age": 30}.values()
```

### 대안: dataclass나 Pydantic 사용

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

user = User(**{"name": "John", "age": 30})
print(user.name, user.age)  # John 30
```

---

## 7. 실무 패턴

### 7.1 함수 반환값 언패킹

```python
def get_user_info(user_id: int) -> tuple[str, int, str]:
    return "John", 30, "john@example.com"

# 언패킹으로 받기
name, age, email = get_user_info(1)
```

### 7.2 Redis Pipeline 결과 처리 (질문하신 코드)

```python
async def get_tool_info(self, environment: str, tool_name: str) -> list:
    key = _make_key_tool(environment, tool_name)
    async with self._async_redis_client.pipeline() as pipe:
        pipe.json().get(key, "$.endpoint_url")
        pipe.json().get(key, "$.tool_type")
        pipe.json().get(key, "$.need_context")
        pipe.json().get(key, "$.auth_config")
        pipe.json().get(key, "$.tool_config")
        results = await pipe.execute()
    return [r[0] if r else None for r in results]

# 호출 측에서 언패킹
(endpoint_url,
 tool_type,
 context_injection,
 auth,
 tool_config) = await self._context_cache.get_tool_info(
     environment=EXECUTION_CODE_MAP[execution_code],
     tool_name=tool_name
 )
```

**왜 이렇게 할까?**

1. **가독성**: 각 변수가 무엇인지 명확
2. **순서 일치**: 반환 순서와 변수 순서가 일치해야 함
3. **타입 힌트 대안**: 튜플 대신 dataclass를 쓰면 더 안전

### 7.3 enumerate와 함께

```python
items = ["apple", "banana", "cherry"]

for index, item in enumerate(items):
    print(f"{index}: {item}")

# 0: apple
# 1: banana
# 2: cherry
```

### 7.4 dict.items()와 함께

```python
scores = {"math": 90, "english": 85, "science": 92}

for subject, score in scores.items():
    print(f"{subject}: {score}")

# math: 90
# english: 85
# science: 92
```

### 7.5 zip과 함께

```python
names = ["Alice", "Bob", "Charlie"]
ages = [25, 30, 35]

for name, age in zip(names, ages):
    print(f"{name} is {age} years old")

# Alice is 25 years old
# Bob is 30 years old
# Charlie is 35 years old
```

---

## 8. 변수 교환 (Swap)

Python 언패킹의 가장 유명한 활용:

```python
a = 1
b = 2

# 언패킹으로 교환 (임시 변수 불필요)
a, b = b, a

print(a, b)  # 2 1
```

Java에서는 임시 변수가 필요하다:

```java
int a = 1, b = 2;
int temp = a;
a = b;
b = temp;
```

---

## 정리

| 패턴 | 문법 | 설명 |
|------|------|------|
| 기본 | `a, b = [1, 2]` | 순서대로 할당 |
| 나머지 | `a, *rest = [1,2,3]` | 나머지를 리스트로 |
| 무시 | `_, b, _ = [1,2,3]` | 필요 없는 값 무시 |
| 중첩 | `(a, b), c = [[1,2], 3]` | 중첩 구조 분해 |
| 교환 | `a, b = b, a` | 변수 값 교환 |

**JavaScript와의 핵심 차이:**
- Python은 **순서 기반** 언패킹만 지원
- JavaScript는 **키 기반** 구조 분해도 지원 (`{a, b} = obj`)
- Python에서 키 기반이 필요하면 dataclass/Pydantic 사용

---

## 출처

- [Python 공식 문서 - Unpacking](https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences)
- [PEP 3132 - Extended Iterable Unpacking](https://peps.python.org/pep-3132/)
