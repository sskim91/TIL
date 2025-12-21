# Python의 enumerate - 인덱스와 값을 동시에

반복문에서 "지금 몇 번째야?"를 알고 싶을 때, 인덱스 변수를 따로 관리하지 않아도 된다.

## 결론부터 말하면

**`enumerate()`는 iterable을 순회하면서 (인덱스, 값) 튜플을 반환하는 내장 함수다.** 인덱스를 수동으로 관리하는 코드를 없애고, 더 Pythonic하게 만든다.

```python
# Bad: 인덱스 수동 관리
i = 0
for name in names:
    print(f"{i}: {name}")
    i += 1

# Good: enumerate 사용
for i, name in enumerate(names):
    print(f"{i}: {name}")
```

| Java | Python |
|------|--------|
| `for (int i = 0; i < list.size(); i++)` | `for i, item in enumerate(list)` |
| 인덱스로 접근: `list.get(i)` | 값이 바로 제공됨 |

## 1. 왜 enumerate가 필요한가?

### 1.1 흔한 실수: 인덱스 관리

리스트를 순회하면서 "지금 몇 번째 항목인지" 알아야 할 때가 많다.

```python
fruits = ["apple", "banana", "cherry"]

# 방법 1: 인덱스 변수 수동 관리 (실수 유발)
i = 0
for fruit in fruits:
    print(f"{i}: {fruit}")
    i += 1  # 깜빡하면 버그!
```

`i += 1`을 깜빡하거나 조건문 안에서 continue할 때 증가시키지 않으면 버그가 발생한다.

```python
# 방법 2: range(len()) 사용 (장황함)
for i in range(len(fruits)):
    print(f"{i}: {fruits[i]}")
```

작동은 하지만 `fruits[i]`로 매번 접근해야 해서 장황하다.

### 1.2 enumerate의 등장

```python
# 방법 3: enumerate (Pythonic)
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")
```

- 인덱스(`i`)와 값(`fruit`)을 동시에 받음
- 인덱스 증가를 신경 쓸 필요 없음
- 코드가 간결하고 의도가 명확함

## 2. 기본 사용법

### 2.1 기본 문법

```python
enumerate(iterable, start=0)
```

| 파라미터 | 설명 |
|----------|------|
| `iterable` | 순회할 객체 (리스트, 튜플, 문자열 등) |
| `start` | 인덱스 시작값 (기본값: 0) |

```python
names = ["Alice", "Bob", "Charlie"]

for index, name in enumerate(names):
    print(f"{index}: {name}")

# 출력:
# 0: Alice
# 1: Bob
# 2: Charlie
```

### 2.2 시작 인덱스 변경

사용자에게 보여줄 때는 1부터 시작하는 게 자연스럽다.

```python
for index, name in enumerate(names, start=1):
    print(f"{index}. {name}")

# 출력:
# 1. Alice
# 2. Bob
# 3. Charlie
```

> **주의**: `start`는 **인덱스 카운터의 시작 숫자** 만 바꾼다. 순회 시작 위치(슬라이싱)에는 영향을 주지 않는다. `start=1`이어도 첫 번째 요소부터 순회한다.

### 2.3 enumerate가 반환하는 것

`enumerate()`는 enumerate 객체(iterator)를 반환하고, 각 요소는 `(index, value)` 튜플이다.

```python
result = enumerate(["a", "b", "c"])
print(list(result))
# [(0, 'a'), (1, 'b'), (2, 'c')]
```

튜플 언패킹으로 `i, value`로 받는 것이 일반적이다.

**메모리 효율성**: `enumerate()`는 모든 쌍을 미리 생성하지 않고, 반복할 때마다 하나씩 생성한다(Lazy Evaluation). 수백만 개의 요소를 순회해도 메모리 점유율이 거의 늘어나지 않는다.

## 3. 실무 활용 패턴

### 3.1 조건에 맞는 인덱스 찾기

```python
scores = [85, 92, 78, 95, 88]

# 90점 이상인 학생의 인덱스 찾기
high_scorers = [i for i, score in enumerate(scores) if score >= 90]
print(high_scorers)  # [1, 3]
```

### 3.2 딕셔너리 생성

`enumerate()`는 `(index, value)` 튜플을 반환하고, `dict()`는 `(key, value)` 쌍의 iterable을 받으므로 바로 변환할 수 있다.

```python
fruits = ["apple", "banana", "cherry"]

# 인덱스를 키로 하는 딕셔너리 (간결한 방식)
fruit_dict = dict(enumerate(fruits))
print(fruit_dict)  # {0: 'apple', 1: 'banana', 2: 'cherry'}

# 컴프리헨션 방식 (커스텀 로직 필요 시)
fruit_dict = {i: fruit.upper() for i, fruit in enumerate(fruits)}

# 값을 키로, 인덱스를 값으로 (역방향 룩업)
index_lookup = {fruit: i for i, fruit in enumerate(fruits)}
print(index_lookup)  # {'apple': 0, 'banana': 1, 'cherry': 2}
# 주의: 중복 값이 있으면 마지막 인덱스만 저장됨
```

### 3.3 병렬 리스트 처리 (zip과 함께)

```python
names = ["Alice", "Bob", "Charlie"]
scores = [85, 92, 78]

for i, (name, score) in enumerate(zip(names, scores), start=1):
    print(f"{i}. {name}: {score}점")

# 출력:
# 1. Alice: 85점
# 2. Bob: 92점
# 3. Charlie: 78점
```

> **중첩 언패킹**: `enumerate`는 `(index, value)` 튜플을 반환하는데, `value`가 `zip`이 반환한 `(name, score)` 튜플이다. 중첩 구조를 해체하려면 `(name, score)`에 괄호가 필요하다.

> **주의**: `zip`은 짧은 쪽 길이에 맞춰 순회하므로, 리스트 길이가 다르면 데이터가 누락된다. Python 3.10+에서는 `zip(..., strict=True)`로 길이 불일치 시 에러를 발생시킬 수 있다.

### 3.4 파일 라인 번호 표시

```python
with open("code.py") as f:
    for line_no, line in enumerate(f, start=1):
        print(f"{line_no:4d} | {line}", end="")

# 출력:
#    1 | def hello():
#    2 |     print("Hello")
#    3 |
```

### 3.5 진행 상황 표시

```python
items = ["task1", "task2", "task3", "task4", "task5"]

for i, item in enumerate(items, start=1):
    print(f"Processing {i}/{len(items)}: {item}")

# 출력:
# Processing 1/5: task1
# Processing 2/5: task2
# ...
```

### 3.6 특정 위치에서 다른 처리

```python
items = ["header", "data1", "data2", "data3"]

for i, item in enumerate(items):
    if i == 0:
        print(f"[HEADER] {item}")
    else:
        print(f"  - {item}")

# 출력:
# [HEADER] header
#   - data1
#   - data2
#   - data3
```

### 3.7 프롬프트 체이닝에서 단계 번호 표시

LLM 워크플로에서 단계별 프롬프트를 순차 실행할 때 유용하다.

```python
def prompt_chain_workflow(initial_input: str, prompt_chain: list[str]) -> list[str]:
    response_chain = []
    response = initial_input

    for i, prompt in enumerate(prompt_chain, 1):  # 1부터 시작
        print(f"\n============ {i} 단계 ============\n")

        final_prompt = f"""{prompt}

사용자 입력: {initial_input}
이전 응답: {response}"""

        response = llm_call(final_prompt)
        response_chain.append(response)

    return response_chain

# 사용 예시
prompts = [
    "여행지 세 곳을 추천해줘.",
    "가장 추천하는 한 곳을 선정하고 활동 5가지를 알려줘.",
    "선정한 여행지의 하루 일정을 계획해줘.",
]
results = prompt_chain_workflow("따뜻한 날씨와 역사 탐방을 좋아해", prompts)
```

`start=1`로 설정하여 "1단계", "2단계", "3단계"로 자연스럽게 출력된다.

## 4. Java 개발자를 위한 비교

### 4.1 전통적인 for 루프

```java
// Java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");
for (int i = 0; i < names.size(); i++) {
    System.out.println(i + ": " + names.get(i));
}
```

```python
# Python
names = ["Alice", "Bob", "Charlie"]
for i, name in enumerate(names):
    print(f"{i}: {name}")
```

### 4.2 Java의 Stream API와 비교

```java
// Java (Stream API)
IntStream.range(0, names.size())
    .forEach(i -> System.out.println(i + ": " + names.get(i)));
```

```python
# Python
for i, name in enumerate(names):
    print(f"{i}: {name}")
```

Python이 더 직관적이다.

### 4.3 Java의 forEach와 비교

```java
// Java (인덱스 없음)
names.forEach(name -> System.out.println(name));
```

Java의 `forEach`는 순서는 보장되지만 **인덱스를 제공하지 않는다.** 인덱스가 필요하면 `IntStream.range()`를 써야 한다.

## 5. 주의사항

### 5.1 enumerate는 iterator를 반환

```python
numbers = [1, 2, 3]
enum_obj = enumerate(numbers)

print(list(enum_obj))  # [(0, 1), (1, 2), (2, 3)]
print(list(enum_obj))  # [] - 이미 소진됨!
```

한 번 순회하면 소진된다. 재사용하려면 다시 `enumerate()`를 호출해야 한다.

### 5.2 원본 리스트 수정 주의

```python
names = ["Alice", "Bob", "Charlie"]

# Bad: 순회 중 리스트 수정
for i, name in enumerate(names):
    if name == "Bob":
        names.remove(name)  # 위험!
```

순회 중 리스트를 수정하면 예상치 못한 동작이 발생할 수 있다.

```python
# Best: 리스트 컴프리헨션으로 새 리스트 생성 (권장)
names = [name for name in names if name != "Bob"]

# Alternative: 역순 순회로 삭제 (인덱스 밀림 방지)
# list()로 감싸는 이유: reversed()는 시퀀스를 요구하지만 enumerate()는 이터레이터를 반환
for i, name in reversed(list(enumerate(names))):
    if name == "Bob":
        del names[i]  # 뒤에서부터 삭제하므로 앞 인덱스에 영향 없음
```

### 5.3 언패킹하지 않으면 튜플

```python
for item in enumerate(["a", "b"]):
    print(item)
    # (0, 'a')
    # (1, 'b')

for i, value in enumerate(["a", "b"]):
    print(i, value)
    # 0 a
    # 1 b
```

## 6. 정리

| 상황 | 코드 |
|------|------|
| 기본 사용 | `for i, item in enumerate(items)` |
| 1부터 시작 | `for i, item in enumerate(items, start=1)` |
| 조건 필터링 | `[i for i, x in enumerate(items) if 조건]` |
| zip과 함께 | `for i, (a, b) in enumerate(zip(list1, list2))` |

**핵심**: 인덱스와 값이 동시에 필요하면 `enumerate()`를 쓰자. `range(len())`보다 Pythonic하고, 수동 인덱스 관리보다 안전하다.

---

## 출처

- [Python 공식 문서 - enumerate](https://docs.python.org/3/library/functions.html#enumerate)
- [PEP 279 - The enumerate() built-in function](https://peps.python.org/pep-0279/)
