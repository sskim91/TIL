# Python은 Call by Value? Call by Reference?

Python의 함수 인자 전달 방식에 대해 알아봅니다.

## 결론부터 말하면

Python은 **"Call by Object Reference"** 방식입니다.

- Call by Value도 아니고
- Call by Reference도 아닌
- Python만의 독특한 방식!

## 쉽게 이해하기: 상자와 리모컨 비유

### 1. 불변 객체 (숫자, 문자열) - "교체 불가능한 상자"

```python
def change_number(x):
    x = 100  # 새로운 상자로 교체
    print(f"함수 안: {x}")

num = 10
change_number(num)
print(f"함수 밖: {num}")

# 출력:
# 함수 안: 100
# 함수 밖: 10  ← 원본은 그대로!
```

**무슨 일이 일어났나?**
- `num`이라는 상자에 10이 들어있음
- 함수에 상자를 복사해서 넘겨줌
- 함수 안에서 새 상자(100)로 교체
- 원본 상자는 그대로 10

### 2. 가변 객체 (리스트, 딕셔너리) - "리모컨"

```python
def add_item(my_list):
    my_list.append(4)  # 리모컨으로 TV 채널 변경
    print(f"함수 안: {my_list}")

numbers = [1, 2, 3]
add_item(numbers)
print(f"함수 밖: {numbers}")

# 출력:
# 함수 안: [1, 2, 3, 4]
# 함수 밖: [1, 2, 3, 4]  ← 원본이 바뀜!
```

**무슨 일이 일어났나?**
- `numbers`는 실제 리스트를 가리키는 리모컨
- 함수에 리모컨을 복사해서 넘겨줌
- 복사된 리모컨도 같은 리스트를 조작
- 같은 리스트를 가리키므로 원본도 변경됨

## 핵심 규칙

### 불변 객체 (Immutable)
- `int`, `float`, `str`, `tuple`
- 값을 바꾸려면 **새로운 객체**를 만들어야 함
- 함수 안에서 바꿔도 **원본은 안전**

```python
# 예시: 문자열
def change_name(name):
    name = "김철수"  # 새 문자열 생성

my_name = "홍길동"
change_name(my_name)
print(my_name)  # "홍길동" ← 그대로
```

### 가변 객체 (Mutable)
- `list`, `dict`, `set`
- 내부를 직접 수정 가능
- 함수 안에서 바꾸면 **원본도 변경**

```python
# 예시: 딕셔너리
def update_score(scores):
    scores["python"] = 100  # 원본 수정

my_scores = {"java": 90}
update_score(my_scores)
print(my_scores)  # {"java": 90, "python": 100} ← 변경됨!
```

## 헷갈리는 케이스

### 케이스 1: 리스트를 통째로 바꾸면?

```python
def replace_list(lst):
    lst = [9, 9, 9]  # 새 리스트로 교체 (재할당)

my_list = [1, 2, 3]
replace_list(my_list)
print(my_list)  # [1, 2, 3] ← 안 바뀜!
```

**왜?**
- `lst = [9, 9, 9]`는 **새로운 리스트 생성**
- 원본 리스트와 연결이 끊어짐

### 케이스 2: 리스트 내부를 수정하면?

```python
def modify_list(lst):
    lst[0] = 999  # 리스트 내부 수정

my_list = [1, 2, 3]
modify_list(my_list)
print(my_list)  # [999, 2, 3] ← 바뀜!
```

**왜?**
- `lst[0] = 999`는 **같은 리스트를 수정**
- 원본과 같은 리스트를 가리킴

## 실무 팁

### 1. 원본을 보호하고 싶다면 복사본을 만들기

```python
def safe_add(lst):
    new_list = lst.copy()  # 복사본 생성
    new_list.append(4)
    return new_list

original = [1, 2, 3]
result = safe_add(original)
print(original)  # [1, 2, 3] ← 안전!
print(result)    # [1, 2, 3, 4]
```

### 2. 깊은 복사 (중첩된 리스트)

```python
import copy

def deep_modify(lst):
    new_list = copy.deepcopy(lst)  # 깊은 복사
    new_list[0][0] = 999
    return new_list

original = [[1, 2], [3, 4]]
result = deep_modify(original)
print(original)  # [[1, 2], [3, 4]] ← 안전!
print(result)    # [[999, 2], [3, 4]]
```

### 3. 불변 객체 반환하기

```python
def add_item(lst, item):
    return lst + [item]  # 새 리스트 반환
    # lst.append(item) ← 원본 수정 (위험)

my_list = [1, 2, 3]
new_list = add_item(my_list, 4)
print(my_list)   # [1, 2, 3]
print(new_list)  # [1, 2, 3, 4]
```

## 디버깅: id()로 확인하기

```python
def check_reference(x):
    print(f"1. 함수 시작: id={id(x)}")
    x.append(4)
    print(f"2. 수정 후: id={id(x)}")

my_list = [1, 2, 3]
print(f"0. 원본: id={id(my_list)}")
check_reference(my_list)
print(f"3. 함수 종료 후: id={id(my_list)}")

# 출력:
# 0. 원본: id=140234567890
# 1. 함수 시작: id=140234567890  ← 같은 객체!
# 2. 수정 후: id=140234567890    ← 여전히 같음
# 3. 함수 종료 후: id=140234567890
```

모두 같은 `id`! = 같은 객체를 가리킴

## 요약 정리

| 구분 | 타입 | 함수에서 수정 | 원본 영향 | 예시 |
|------|------|--------------|----------|------|
| **불변 객체** | int, str, tuple | 재할당 필요 | ❌ 없음 | `x = 100` |
| **가변 객체** | list, dict, set | 직접 수정 가능 | ✅ 있음 | `lst.append(4)` |

**기억할 것:**
- 재할당(`=`) → 새 객체 → 원본 안전
- 내부 수정(`.append()`, `[0] = ...`) → 같은 객체 → 원본 변경

## 참고 자료

- [Python Documentation - Defining Functions](https://docs.python.org/3/tutorial/controlflow.html#defining-functions)
- [Real Python - Pass by Reference in Python](https://realpython.com/python-pass-by-reference/)
