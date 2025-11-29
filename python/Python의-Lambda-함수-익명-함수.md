# Python의 Lambda 함수 (익명 함수)

Java의 `x -> x * 2`와 비슷하지만, Python은 `lambda x: x * 2`로 작성한다. 언제, 왜 쓸까?

## 결론부터 말하면

Lambda는 **이름 없는 함수**를 **한 줄**로 작성하는 방법입니다. (Java의 람다 표현식과 유사)

```python
# ❌ Before: 일반 함수
def add(x, y):
    return x + y

result = add(3, 5)  # 8

# ✅ After: Lambda 함수
add = lambda x, y: x + y
result = add(3, 5)  # 8

# ✅ 주로 이렇게 사용 (변수에 할당하지 않고)
sorted([3, 1, 4, 2], key=lambda x: x)
```

**언제 사용하나?**
- `map()`, `filter()`, `sorted()` 등에서 간단한 함수가 필요할 때
- 한 번만 사용하는 간단한 함수일 때
- 함수를 인자로 전달할 때

## 1. Lambda 기본 문법

### 1.1 기본 구조

```python
lambda 매개변수: 표현식
```

```python
# 일반 함수
def square(x):
    return x ** 2

# Lambda 함수 (동일한 기능)
square = lambda x: x ** 2

print(square(5))  # 25
```

### 1.2 매개변수 개수

```python
# 매개변수 없음
greet = lambda: "Hello!"
print(greet())  # Hello!

# 매개변수 1개
double = lambda x: x * 2
print(double(5))  # 10

# 매개변수 2개
add = lambda x, y: x + y
print(add(3, 5))  # 8

# 매개변수 3개 이상
multiply = lambda x, y, z: x * y * z
print(multiply(2, 3, 4))  # 24
```

### 1.3 기본값 매개변수

```python
# 기본값 설정 가능
power = lambda x, n=2: x ** n

print(power(5))      # 25 (n=2가 기본값)
print(power(5, 3))   # 125
```

## 2. Lambda vs 일반 함수

### 2.1 차이점 비교

| 특징 | Lambda | 일반 함수 (def) |
|------|--------|----------------|
| **이름** | 익명 (anonymous) | 명시적 이름 필요 |
| **줄 수** | 한 줄만 가능 | 여러 줄 가능 |
| **return** | 암묵적 반환 | 명시적 `return` |
| **복잡도** | 간단한 로직만 | 복잡한 로직 가능 |
| **문서화** | docstring 불가 | docstring 가능 |
| **디버깅** | 어려움 | 쉬움 (함수 이름 표시) |

### 2.2 제약사항

Lambda 함수는 **단일 표현식**만 허용됩니다:

```python
# ✅ 가능: 단일 표현식
square = lambda x: x ** 2

# ✅ 가능: 조건부 표현식
abs_value = lambda x: x if x >= 0 else -x

# ❌ 불가능: 여러 문장
# invalid_lambda = lambda x:
#     result = x ** 2
#     return result

# ❌ 불가능: 할당문
# invalid_lambda = lambda x: y = x + 1

# ❌ 불가능: print 등의 문장 (표현식은 아니지만 가능)
# lambda x: print(x)  # 기술적으로 가능하지만 권장하지 않음
```

### 2.3 언제 Lambda를 쓸까?

```python
# ✅ Lambda 사용이 좋은 경우: 간단하고 한 번만 사용
sorted_list = sorted([3, 1, 4, 2], key=lambda x: x)

# ❌ Lambda 사용이 나쁜 경우: 복잡하거나 재사용
# 나쁜 예
complex_calc = lambda x, y, z: (x + y) * z if x > 0 else (x - y) / z if z != 0 else 0

# 좋은 예: 일반 함수로 작성
def complex_calculation(x, y, z):
    """복잡한 계산을 수행합니다."""
    if x > 0:
        return (x + y) * z
    elif z != 0:
        return (x - y) / z
    else:
        return 0
```

## 3. 실전 활용: map, filter, sorted

### 3.1 map() - 변환

```python
# 각 요소를 변환
numbers = [1, 2, 3, 4, 5]

# Lambda 사용
squared = list(map(lambda x: x ** 2, numbers))
print(squared)  # [1, 4, 9, 16, 25]

# 여러 iterable 동시 처리
a = [1, 2, 3]
b = [4, 5, 6]
result = list(map(lambda x, y: x + y, a, b))
print(result)  # [5, 7, 9]
```

**실무 예제: 데이터 변환**

```python
# 가격 데이터에 부가세 10% 추가
prices = [10000, 20000, 30000]
prices_with_tax = list(map(lambda p: p * 1.1, prices))
print(prices_with_tax)  # [11000.0, 22000.0, 33000.0]

# 문자열 처리
names = ['alice', 'bob', 'charlie']
capitalized = list(map(lambda name: name.capitalize(), names))
print(capitalized)  # ['Alice', 'Bob', 'Charlie']
```

### 3.2 filter() - 필터링

```python
# 조건에 맞는 요소만 선택
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 짝수만 필터링
even_numbers = list(filter(lambda x: x % 2 == 0, numbers))
print(even_numbers)  # [2, 4, 6, 8, 10]

# 5보다 큰 수만 필터링
greater_than_5 = list(filter(lambda x: x > 5, numbers))
print(greater_than_5)  # [6, 7, 8, 9, 10]
```

**실무 예제: 데이터 필터링**

```python
# 사용자 데이터 필터링
users = [
    {'name': 'Alice', 'age': 25, 'active': True},
    {'name': 'Bob', 'age': 17, 'active': True},
    {'name': 'Charlie', 'age': 30, 'active': False},
    {'name': 'David', 'age': 22, 'active': True},
]

# 성인이면서 활성 사용자만 필터링
adult_active_users = list(filter(
    lambda u: u['age'] >= 18 and u['active'],
    users
))
print(adult_active_users)
# [{'name': 'Alice', 'age': 25, 'active': True},
#  {'name': 'David', 'age': 22, 'active': True}]
```

### 3.3 sorted() - 정렬

```python
# key 매개변수에 Lambda 사용
students = [
    {'name': 'Alice', 'score': 85},
    {'name': 'Bob', 'score': 92},
    {'name': 'Charlie', 'score': 78},
]

# 점수로 정렬
sorted_by_score = sorted(students, key=lambda s: s['score'])
print(sorted_by_score)
# [{'name': 'Charlie', 'score': 78},
#  {'name': 'Alice', 'score': 85},
#  {'name': 'Bob', 'score': 92}]

# 점수로 내림차순 정렬
sorted_desc = sorted(students, key=lambda s: s['score'], reverse=True)

# 이름 길이로 정렬
names = ['Alice', 'Bob', 'Charlie', 'David']
sorted_by_length = sorted(names, key=lambda name: len(name))
print(sorted_by_length)  # ['Bob', 'Alice', 'David', 'Charlie']
```

**실무 예제: 복잡한 정렬**

```python
# 여러 조건으로 정렬 (튜플 반환)
employees = [
    {'name': 'Alice', 'dept': 'IT', 'salary': 5000},
    {'name': 'Bob', 'dept': 'HR', 'salary': 4500},
    {'name': 'Charlie', 'dept': 'IT', 'salary': 5500},
    {'name': 'David', 'dept': 'HR', 'salary': 4500},
]

# 부서별로 정렬 후, 같은 부서 내에서는 급여로 정렬
sorted_employees = sorted(
    employees,
    key=lambda e: (e['dept'], -e['salary'])  # dept 오름차순, salary 내림차순
)
for emp in sorted_employees:
    print(emp)
# {'name': 'Bob', 'dept': 'HR', 'salary': 4500}
# {'name': 'David', 'dept': 'HR', 'salary': 4500}
# {'name': 'Charlie', 'dept': 'IT', 'salary': 5500}
# {'name': 'Alice', 'dept': 'IT', 'salary': 5000}
```

## 4. 실무 활용 패턴

### 4.1 reduce() - 누적 계산

```python
from functools import reduce

# 모든 요소의 곱 계산
numbers = [1, 2, 3, 4, 5]
product = reduce(lambda x, y: x * y, numbers)
print(product)  # 120 (1*2*3*4*5)

# 최대값 찾기
max_value = reduce(lambda x, y: x if x > y else y, numbers)
print(max_value)  # 5
```

### 4.2 Dictionary 조작

```python
# Dictionary 키로 정렬
data = {'banana': 3, 'apple': 5, 'cherry': 2}
sorted_by_key = dict(sorted(data.items(), key=lambda item: item[0]))
print(sorted_by_key)  # {'apple': 5, 'banana': 3, 'cherry': 2}

# Dictionary 값으로 정렬
sorted_by_value = dict(sorted(data.items(), key=lambda item: item[1]))
print(sorted_by_value)  # {'cherry': 2, 'banana': 3, 'apple': 5}

# Dictionary comprehension과 함께
squared_dict = {k: v**2 for k, v in data.items()}
```

### 4.3 Event Handler / Callback

```python
# GUI 이벤트 핸들러 (tkinter 예시)
# button.config(command=lambda: print("Button clicked!"))

# 지연 실행 (간단한 경우)
def execute_later(callback):
    """나중에 콜백 실행"""
    callback()

execute_later(lambda: print("Executed!"))

# 매개변수가 있는 콜백
def process_data(data, callback):
    result = data * 2
    callback(result)

process_data(5, lambda x: print(f"Result: {x}"))  # Result: 10
```

### 4.4 조건부 표현식과 함께

```python
# if-else를 Lambda 안에서
get_grade = lambda score: 'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'F'

print(get_grade(95))  # A
print(get_grade(85))  # B
print(get_grade(75))  # C
print(get_grade(65))  # F

# 여러 조건 처리
classify_number = lambda x: 'positive' if x > 0 else 'negative' if x < 0 else 'zero'
print(classify_number(5))   # positive
print(classify_number(-3))  # negative
print(classify_number(0))   # zero
```

### 4.5 고차 함수 (Higher-Order Functions)

```python
# 함수를 반환하는 함수
def make_multiplier(n):
    return lambda x: x * n

double = make_multiplier(2)
triple = make_multiplier(3)

print(double(5))  # 10
print(triple(5))  # 15

# 함수를 인자로 받는 함수
def apply_operation(x, y, operation):
    return operation(x, y)

result1 = apply_operation(5, 3, lambda a, b: a + b)  # 8
result2 = apply_operation(5, 3, lambda a, b: a * b)  # 15
```

## 5. Java와의 비교

### 5.1 기본 문법 비교

```python
# Python
add = lambda x, y: x + y
result = add(3, 5)  # 8
```

```java
// Java 8+
BiFunction<Integer, Integer, Integer> add = (x, y) -> x + y;
int result = add.apply(3, 5);  // 8

// 또는 Function 사용
Function<Integer, Integer> square = x -> x * x;
int result2 = square.apply(5);  // 25
```

### 5.2 Stream API와 Lambda 비교

```python
# Python: map, filter
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x ** 2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

```java
// Java: Stream API
List<Integer> numbers = List.of(1, 2, 3, 4, 5);
List<Integer> squared = numbers.stream()
    .map(x -> x * x)
    .collect(Collectors.toList());

List<Integer> evens = numbers.stream()
    .filter(x -> x % 2 == 0)
    .collect(Collectors.toList());
```

### 5.3 정렬 비교

```python
# Python
students = [
    {'name': 'Alice', 'score': 85},
    {'name': 'Bob', 'score': 92}
]
sorted_students = sorted(students, key=lambda s: s['score'])
```

```java
// Java
List<Student> students = List.of(
    new Student("Alice", 85),
    new Student("Bob", 92)
);
List<Student> sortedStudents = students.stream()
    .sorted(Comparator.comparingInt(Student::getScore))
    .collect(Collectors.toList());

// 또는 Lambda 사용
students.sort((s1, s2) -> Integer.compare(s1.getScore(), s2.getScore()));
```

### 5.4 주요 차이점

| 특징 | Python Lambda | Java Lambda |
|------|--------------|-------------|
| **타입 선언** | 불필요 (동적 타입) | 필요 (정적 타입) |
| **함수형 인터페이스** | 없음 | 필수 (Function, Predicate 등) |
| **문법** | `lambda x: x + 1` | `x -> x + 1` |
| **변수 캡처** | 자유로움 | final 또는 effectively final만 |
| **메서드 참조** | 없음 | `::` 연산자 지원 |

## 6. Best Practices

### ✅ Lambda를 사용해야 할 때

```python
# 1. 간단한 한 줄 함수
sorted_list = sorted(data, key=lambda x: x['score'])

# 2. 일회성 함수
button.config(command=lambda: print("Clicked!"))

# 3. map, filter, sorted와 함께
doubled = list(map(lambda x: x * 2, numbers))
```

### ❌ Lambda를 피해야 할 때

```python
# 1. 복잡한 로직 (일반 함수 사용)
# 나쁜 예
validate = lambda x: True if x > 0 and x < 100 and x % 2 == 0 else False

# 좋은 예
def validate_number(x):
    """0과 100 사이의 짝수인지 검증합니다."""
    return 0 < x < 100 and x % 2 == 0

# 2. 재사용되는 함수 (명확한 이름 필요)
# 나쁜 예
calc = lambda x, y: (x + y) * 0.1

# 좋은 예
def calculate_tax(price, quantity):
    """총액의 10% 세금을 계산합니다."""
    return (price + quantity) * 0.1

# 3. 디버깅이 중요한 경우
# Lambda는 traceback에서 <lambda>로 표시되어 디버깅이 어려움
```

### 💡 코딩 가이드

```python
# 1. List Comprehension이 더 읽기 좋을 때는 그것을 사용
# Lambda + map
doubled = list(map(lambda x: x * 2, numbers))

# List Comprehension (더 Pythonic)
doubled = [x * 2 for x in numbers]

# 2. 변수에 Lambda를 할당하지 말 것 (PEP 8)
# ❌ 나쁜 예
square = lambda x: x ** 2

# ✅ 좋은 예
def square(x):
    return x ** 2

# 3. Lambda는 인라인으로 사용
# ✅ 좋은 예
sorted(data, key=lambda x: x['score'])
```

## 7. 성능 고려사항

```python
import timeit

# 일반 함수 vs Lambda (거의 차이 없음)
def square_func(x):
    return x ** 2

square_lambda = lambda x: x ** 2

# 성능 테스트
numbers = list(range(1000))

# 일반 함수
time_func = timeit.timeit(
    lambda: [square_func(x) for x in numbers],
    number=10000
)

# Lambda
time_lambda = timeit.timeit(
    lambda: [square_lambda(x) for x in numbers],
    number=10000
)

print(f"Function: {time_func:.4f}s")
print(f"Lambda: {time_lambda:.4f}s")
# 거의 동일한 성능
```

**결론**: Lambda와 일반 함수의 성능 차이는 거의 없습니다. **가독성과 유지보수성**을 기준으로 선택하세요.

## 8. 고급 패턴

### 8.1 Decorator와 Lambda

```python
from functools import wraps

def double_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result * 2
    return wrapper

# Lambda에 decorator 적용 (비추천이지만 가능)
decorated_lambda = double_decorator(lambda x: x + 1)
print(decorated_lambda(5))  # 12 ((5+1)*2)
```

### 8.2 Closure와 Lambda

```python
def make_power_func(exponent):
    """지수를 고정한 거듭제곱 함수를 반환"""
    return lambda base: base ** exponent

square = make_power_func(2)
cube = make_power_func(3)

print(square(5))  # 25
print(cube(5))    # 125
```

### 8.3 Partial Function과의 비교

```python
from functools import partial

# Lambda 사용
double = lambda x: x * 2

# Partial 사용
def multiply(x, y):
    return x * y

double_partial = partial(multiply, 2)

print(double(5))          # 10
print(double_partial(5))  # 10

# Partial이 더 나은 경우: 기존 함수를 재사용할 때
```

## 실무 팁

### 1. 가독성 우선

Lambda는 **간결함**이 장점이지만, **가독성**이 떨어지면 일반 함수를 사용하세요.

```python
# ❌ 너무 복잡한 Lambda
result = sorted(
    data,
    key=lambda x: (x['category'], -x['priority'], x['created_at'].timestamp())
)

# ✅ 명확한 함수
def sort_key(item):
    return (
        item['category'],
        -item['priority'],
        item['created_at'].timestamp()
    )

result = sorted(data, key=sort_key)
```

### 2. Type Hints와 Lambda

```python
from typing import Callable

# Lambda의 타입 힌트
transform: Callable[[int], int] = lambda x: x * 2

# 함수를 받는 함수의 타입 힌트
def apply_twice(func: Callable[[int], int], value: int) -> int:
    return func(func(value))

result = apply_twice(lambda x: x + 1, 5)  # 7
```

### 3. 실무에서 자주 쓰는 패턴

```python
# 1. 로깅 데이터 필터링
logs = [
    {'level': 'ERROR', 'message': 'Failed'},
    {'level': 'INFO', 'message': 'Success'},
    {'level': 'ERROR', 'message': 'Timeout'},
]
errors = list(filter(lambda log: log['level'] == 'ERROR', logs))

# 2. API 응답 변환
api_response = [
    {'id': 1, 'name': 'Item1', 'price': 1000},
    {'id': 2, 'name': 'Item2', 'price': 2000},
]
item_names = list(map(lambda item: item['name'], api_response))

# 3. 동적 함수 생성 (설정 기반)
def create_validator(min_value, max_value):
    return lambda x: min_value <= x <= max_value

age_validator = create_validator(0, 150)
print(age_validator(25))   # True
print(age_validator(200))  # False
```

## 요약

| 항목 | 내용 |
|------|------|
| **정의** | `lambda 매개변수: 표현식` 형태의 익명 함수 |
| **특징** | 한 줄, 암묵적 반환, 이름 없음 |
| **장점** | 간결, 인라인 사용 가능, 함수형 프로그래밍 스타일 |
| **단점** | 한 줄 제한, 디버깅 어려움, 가독성 저하 가능 |
| **주요 사용처** | `map()`, `filter()`, `sorted()`, 콜백 함수 |
| **Java 비교** | Java의 Lambda 표현식과 유사하지만 더 자유로움 |
| **Best Practice** | 간단한 경우만 사용, 복잡하면 일반 함수 사용 |

Lambda는 **도구**입니다. 상황에 맞게 사용하되, **가독성**을 최우선으로 고려하세요! 🎯
