# Python 자료형과 간결한 문법 완전 정복

파이썬에서 자주 사용되는 자료형과 파이썬만의 간결하고 강력한 문법들을 알아봅니다.

## 결론부터 말하면

파이썬은 **적은 코드로 많은 일을 할 수 있는 간결한 문법**이 최대 강점입니다. 슬라이싱, 언패킹, 컴프리헨션 등의 독특한 문법으로 생산성을 크게 높일 수 있습니다.

```python
# 간결함의 예시
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 짝수만 골라서 제곱
squares = [x**2 for x in numbers if x % 2 == 0]
# [4, 16, 36, 64, 100]

# 역순으로 출력
print(numbers[::-1])
# [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
```

## 1. 자주 사용되는 자료형

### List (리스트)

**가장 많이 사용하는 컬렉션**

```python
# 생성
fruits = ["사과", "바나나", "오렌지"]
mixed = [1, "two", 3.0, True]  # 타입 혼용 가능

# 추가/삭제
fruits.append("포도")         # ["사과", "바나나", "오렌지", "포도"]
fruits.insert(1, "딸기")      # 특정 위치에 삽입
fruits.remove("바나나")       # 값으로 삭제
last = fruits.pop()          # 마지막 요소 제거 후 반환

# 인덱싱
print(fruits[0])             # "사과"
print(fruits[-1])            # 마지막 요소
print(fruits[-2])            # 뒤에서 두 번째

# 정렬
numbers = [3, 1, 4, 1, 5]
numbers.sort()               # [1, 1, 3, 4, 5] - 원본 변경
sorted_nums = sorted(numbers) # 새 리스트 반환
```

**언제 사용?**
- 순서가 중요한 데이터
- 데이터 추가/삭제가 빈번한 경우
- 인덱스로 접근해야 하는 경우

### Tuple (튜플)

**불변(immutable) 리스트, 가볍고 안전**

```python
# 생성
point = (10, 20)
single = (42,)  # 요소 하나일 때 쉼표 필수!

# 다중 반환에 최적
def get_user_info():
    return "홍길동", 30, "hong@email.com"

name, age, email = get_user_info()  # 언패킹

# 불변성
point[0] = 15  # TypeError! 수정 불가

# 딕셔너리 키로 사용 가능
locations = {
    (0, 0): "원점",
    (10, 20): "포인트A"
}
```

**언제 사용?**
- 변경되지 않아야 하는 데이터
- 여러 값을 묶어서 반환할 때
- 딕셔너리의 키로 사용할 때

### Dictionary (딕셔너리)

**키-값 쌍, 가장 유용한 자료구조**

```python
# 생성 (JSON처럼 간단!)
user = {
    "name": "홍길동",
    "age": 30,
    "skills": ["Python", "JavaScript"]
}

# 접근
print(user["name"])              # "홍길동"
print(user.get("phone", "없음"))  # 안전한 접근, 기본값 지정

# 추가/수정
user["city"] = "서울"             # 동적 추가
user["age"] = 31                 # 수정

# 삭제
del user["age"]
removed = user.pop("city", None) # 안전한 삭제

# 순회
for key, value in user.items():
    print(f"{key}: {value}")

# 키/값만 가져오기
keys = list(user.keys())
values = list(user.values())

# 존재 확인
if "name" in user:
    print(user["name"])
```

**언제 사용?**
- 키로 데이터를 찾아야 할 때
- 설정, 옵션, 메타데이터 저장
- JSON 데이터 처리
- 빠른 조회가 필요할 때 (O(1))

### Set (세트)

**중복 없는 집합**

```python
# 생성
numbers = {1, 2, 3, 3, 4}  # {1, 2, 3, 4} - 중복 자동 제거
empty = set()              # 빈 세트 ({}는 딕셔너리!)

# 중복 제거에 최적
duplicates = [1, 2, 2, 3, 3, 3, 4]
unique = set(duplicates)   # {1, 2, 3, 4}
unique_list = list(unique) # 다시 리스트로

# 집합 연산
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

print(a & b)  # {3, 4} - 교집합
print(a | b)  # {1, 2, 3, 4, 5, 6} - 합집합
print(a - b)  # {1, 2} - 차집합
print(a ^ b)  # {1, 2, 5, 6} - 대칭 차집합

# 멤버십 테스트 (매우 빠름!)
if 3 in numbers:
    print("3이 있습니다")
```

**언제 사용?**
- 중복을 제거해야 할 때
- 빠른 멤버십 테스트 (있는지 확인)
- 집합 연산이 필요할 때

## 2. 파이썬의 간결한 문법

### 슬라이싱 (Slicing)

**리스트, 문자열을 쉽게 자르기**

```python
numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# 기본 슬라이싱 [시작:끝:스텝]
numbers[2:5]      # [2, 3, 4]
numbers[:3]       # [0, 1, 2] - 처음부터
numbers[7:]       # [7, 8, 9] - 끝까지
numbers[:]        # 전체 복사

# 음수 인덱스
numbers[-3:]      # [7, 8, 9] - 뒤에서 3개
numbers[:-2]      # [0, 1, 2, 3, 4, 5, 6, 7] - 뒤 2개 제외

# 스텝 사용
numbers[::2]      # [0, 2, 4, 6, 8] - 2칸씩
numbers[1::2]     # [1, 3, 5, 7, 9] - 홀수만
numbers[::-1]     # [9, 8, 7, 6, 5, 4, 3, 2, 1, 0] - 역순!

# 문자열에도 동일하게 적용
text = "Hello World"
print(text[:5])   # "Hello"
print(text[6:])   # "World"
print(text[::-1]) # "dlroW olleH"
```

**활용:**
```python
# 첫 글자 대문자로
name = "python"
capitalized = name[0].upper() + name[1:]  # "Python"

# 확장자 추출
filename = "document.pdf"
extension = filename[-3:]  # "pdf"

# 리스트 일부만 처리
data = list(range(100))
first_ten = data[:10]
last_ten = data[-10:]
```

### 언패킹 (Unpacking)

**여러 변수에 한 번에 할당**

```python
# 기본 언패킹
a, b, c = 1, 2, 3
print(a, b, c)  # 1 2 3

# 스왑이 정말 쉬움!
x, y = 10, 20
x, y = y, x
print(x, y)  # 20 10

# 나머지 모두 받기 (*)
first, *middle, last = [1, 2, 3, 4, 5]
print(first)   # 1
print(middle)  # [2, 3, 4]
print(last)    # 5

# 딕셔너리 언패킹
user = {"name": "홍길동", "age": 30}
admin = {**user, "role": "admin"}
# {"name": "홍길동", "age": 30, "role": "admin"}

# 함수 인자로 언패킹
def create_user(name, age, city):
    print(f"{name}, {age}세, {city}")

data = ["김철수", 25, "부산"]
create_user(*data)  # 리스트를 위치 인자로

options = {"name": "이영희", "age": 28, "city": "서울"}
create_user(**options)  # 딕셔너리를 키워드 인자로
```

**실용 예시:**
```python
# 파일 경로 분리
path = "/home/user/documents/file.txt"
*directories, filename = path.split('/')
print(directories)  # ['', 'home', 'user', 'documents']
print(filename)     # 'file.txt'

# 첫 번째와 나머지 분리
numbers = [1, 2, 3, 4, 5]
head, *tail = numbers
print(f"첫 번째: {head}, 나머지: {tail}")
# 첫 번째: 1, 나머지: [2, 3, 4, 5]
```

### 리스트 컴프리헨션 (List Comprehension)

**한 줄로 리스트 생성**

```python
# 기본 형태: [표현식 for 항목 in 반복가능객체]
squares = [x**2 for x in range(10)]
# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# 조건 포함: [표현식 for 항목 in 반복가능객체 if 조건]
evens = [x for x in range(10) if x % 2 == 0]
# [0, 2, 4, 6, 8]

# 조건부 표현식
labels = ["짝수" if x % 2 == 0 else "홀수" for x in range(5)]
# ["짝수", "홀수", "짝수", "홀수", "짝수"]

# 중첩 반복
matrix = [[i*j for j in range(3)] for i in range(3)]
# [[0, 0, 0], [0, 1, 2], [0, 2, 4]]

# 문자열 처리
words = ["hello", "world", "python"]
upper_words = [w.upper() for w in words]
# ["HELLO", "WORLD", "PYTHON"]

# 필터링 + 변환
numbers = [1, 2, 3, 4, 5, 6]
doubled_evens = [x * 2 for x in numbers if x % 2 == 0]
# [4, 8, 12]
```

**실용 예시:**
```python
# 파일 목록에서 특정 확장자만
files = ["data.csv", "image.png", "doc.txt", "sheet.csv"]
csv_files = [f for f in files if f.endswith('.csv')]
# ["data.csv", "sheet.csv"]

# 다차원 리스트 평탄화
nested = [[1, 2], [3, 4], [5, 6]]
flat = [num for sublist in nested for num in sublist]
# [1, 2, 3, 4, 5, 6]

# 딕셔너리에서 특정 값 추출
users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]
names = [user["name"] for user in users if user["age"] >= 30]
# ["Alice", "Charlie"]
```

### 딕셔너리 컴프리헨션

**한 줄로 딕셔너리 생성**

```python
# 기본 형태
squared = {x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# 조건부
positive = {k: v for k, v in {"a": 1, "b": -2, "c": 3}.items() if v > 0}
# {"a": 1, "c": 3}

# 키-값 변환
original = {"apple": 1, "banana": 2}
swapped = {v: k for k, v in original.items()}
# {1: "apple", 2: "banana"}

# 리스트를 딕셔너리로
words = ["apple", "banana", "cherry"]
word_lengths = {word: len(word) for word in words}
# {"apple": 5, "banana": 6, "cherry": 6}
```

### 세트 컴프리헨션

```python
# 중복 제거하면서 변환
numbers = [1, 2, 2, 3, 3, 3]
squared_set = {x**2 for x in numbers}
# {1, 4, 9}
```

### 다중 비교

**수학적 표현 그대로 사용**

```python
# 범위 체크
age = 25
if 18 <= age < 65:
    print("성인이며 65세 미만")

# 여러 조건
score = 85
if 0 <= score <= 100:
    print("유효한 점수")

# 체이닝
x = 5
if 1 < x < 10 < 100:
    print("x는 1과 10 사이, 10은 100보다 작음")
```

### Enumerate와 Zip

**반복문을 더 강력하게**

```python
# enumerate: 인덱스와 값 함께
fruits = ["사과", "바나나", "오렌지"]
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")
# 0: 사과
# 1: 바나나
# 2: 오렌지

# 시작 번호 지정
for i, fruit in enumerate(fruits, start=1):
    print(f"{i}. {fruit}")
# 1. 사과
# 2. 바나나
# 3. 오렌지

# zip: 여러 리스트 동시 순회
names = ["Alice", "Bob", "Charlie"]
ages = [25, 30, 35]
cities = ["Seoul", "Busan", "Daegu"]

for name, age, city in zip(names, ages, cities):
    print(f"{name}({age}세) - {city}")
# Alice(25세) - Seoul
# Bob(30세) - Busan
# Charlie(35세) - Daegu

# zip으로 딕셔너리 만들기
keys = ["name", "age", "city"]
values = ["홍길동", 30, "서울"]
user = dict(zip(keys, values))
# {"name": "홍길동", "age": 30, "city": "서울"}
```

## 3. 자주 사용되는 패턴

### 기본값 처리

```python
# get() 메서드로 안전하게
user = {"name": "홍길동"}
age = user.get("age", 0)  # 키가 없으면 0 반환

# setdefault()로 기본값 설정하며 가져오기
counts = {}
counts.setdefault("apple", 0)
counts["apple"] += 1

# defaultdict 사용
from collections import defaultdict

word_count = defaultdict(int)  # 기본값 0
for word in ["a", "b", "a", "c"]:
    word_count[word] += 1
# {"a": 2, "b": 1, "c": 1}
```

### 파일 처리

```python
# with 문으로 자동 닫기
with open("data.txt") as f:
    content = f.read()
# 파일 자동으로 닫힘

# 한 줄씩 읽기
with open("data.txt") as f:
    for line in f:
        print(line.strip())

# 한 번에 읽기
with open("data.txt") as f:
    lines = f.readlines()  # 리스트로

# 쓰기
with open("output.txt", "w") as f:
    f.write("Hello World\n")
    f.writelines(["Line 1\n", "Line 2\n"])
```

### any()와 all()

```python
# any: 하나라도 True면 True
numbers = [0, 0, 1, 0]
print(any(numbers))  # True

# all: 모두 True여야 True
numbers = [1, 2, 3, 4]
print(all(numbers))  # True (0이 아닌 수는 True)

# 조건 검사에 유용
scores = [85, 92, 78, 95]
all_passed = all(score >= 60 for score in scores)  # True
has_excellent = any(score >= 90 for score in scores)  # True
```

### 문자열 조인/스플릿

```python
# join: 리스트를 문자열로
words = ["Hello", "World", "Python"]
sentence = " ".join(words)  # "Hello World Python"
csv = ",".join(words)       # "Hello,World,Python"

# split: 문자열을 리스트로
sentence = "Hello World Python"
words = sentence.split()    # ["Hello", "World", "Python"]
words = sentence.split(" ") # 동일

# 구분자 여러 개일 때
import re
text = "apple, banana; orange: grape"
fruits = re.split(r'[,;:]\s*', text)
# ["apple", "banana", "orange", "grape"]
```

### 정렬

```python
# 기본 정렬
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
numbers.sort()  # [1, 1, 2, 3, 4, 5, 6, 9] - 원본 변경

sorted_nums = sorted(numbers)  # 새 리스트 반환

# 역순 정렬
numbers.sort(reverse=True)
# sorted(numbers, reverse=True)

# 키 함수로 정렬
words = ["apple", "pie", "zoo", "a"]
words.sort(key=len)  # ["a", "pie", "zoo", "apple"] - 길이순

# 복잡한 정렬
users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]
users.sort(key=lambda u: u["age"])  # 나이순
users.sort(key=lambda u: u["name"])  # 이름순
```

## 4. 실전 예시

### 데이터 필터링 및 변환

```python
# 데이터
sales = [
    {"product": "노트북", "price": 1200000, "quantity": 2},
    {"product": "마우스", "price": 35000, "quantity": 10},
    {"product": "키보드", "price": 89000, "quantity": 5}
]

# 총액 계산
total_values = [
    sale["price"] * sale["quantity"]
    for sale in sales
]

# 100만원 이상 상품만
expensive = [
    sale for sale in sales
    if sale["price"] >= 100000
]

# 상품명만 추출
products = [sale["product"] for sale in sales]

# 총 매출
total_revenue = sum(s["price"] * s["quantity"] for s in sales)
```

### 그룹화

```python
from collections import defaultdict

# 나이별로 사용자 그룹화
users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 30},
    {"name": "David", "age": 25}
]

age_groups = defaultdict(list)
for user in users:
    age_groups[user["age"]].append(user["name"])

# {30: ["Alice", "Charlie"], 25: ["Bob", "David"]}
```

### 카운팅

```python
from collections import Counter

# 단어 빈도 계산
words = ["apple", "banana", "apple", "cherry", "banana", "apple"]
word_count = Counter(words)
# Counter({"apple": 3, "banana": 2, "cherry": 1})

# 가장 많이 나온 것
most_common = word_count.most_common(2)
# [("apple", 3), ("banana", 2)]

# 리스트에서 가장 많은 요소
numbers = [1, 2, 3, 2, 1, 2, 3, 2]
most_frequent = Counter(numbers).most_common(1)[0][0]  # 2
```

### CSV 처리

```python
import csv

# 읽기
with open("data.csv") as f:
    reader = csv.DictReader(f)
    data = [row for row in reader]

# 쓰기
with open("output.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "age"])
    writer.writeheader()
    writer.writerow({"name": "Alice", "age": 30})
    writer.writerows([
        {"name": "Bob", "age": 25},
        {"name": "Charlie", "age": 35}
    ])
```

### JSON 처리

```python
import json

# 딕셔너리 → JSON 문자열
user = {"name": "홍길동", "age": 30}
json_str = json.dumps(user, ensure_ascii=False)

# JSON 문자열 → 딕셔너리
data = json.loads(json_str)

# 파일로 저장
with open("user.json", "w") as f:
    json.dump(user, f, ensure_ascii=False, indent=2)

# 파일에서 읽기
with open("user.json") as f:
    loaded_user = json.load(f)
```

## 5. 비교표

### 자료형 선택 가이드

| 상황 | 사용할 자료형 | 이유 |
|------|--------------|------|
| 순서있는 데이터, 변경 필요 | `list` | 가변, 순서 보장, 인덱싱 |
| 변경 불가, 여러 값 묶기 | `tuple` | 불변, 가벼움 |
| 키로 값 찾기 | `dict` | O(1) 조회 |
| 중복 제거 | `set` | 자동 중복 제거 |
| 빠른 존재 확인 | `set` | O(1) 멤버십 테스트 |

### 메서드 체크리스트

**List:**
```python
.append(x)      # 끝에 추가
.insert(i, x)   # 위치 i에 삽입
.remove(x)      # 값 x 삭제 (첫 번째)
.pop(i)         # 위치 i 삭제 후 반환
.sort()         # 정렬 (원본 변경)
.reverse()      # 역순 (원본 변경)
.count(x)       # 값 x 개수
.index(x)       # 값 x의 인덱스
```

**Dictionary:**
```python
.get(k, default)    # 안전한 접근
.keys()             # 키 목록
.values()           # 값 목록
.items()            # (키, 값) 쌍
.pop(k, default)    # 키 삭제 후 반환
.update(other)      # 다른 딕셔너리 병합
.setdefault(k, v)   # 없으면 설정
```

**Set:**
```python
.add(x)         # 추가
.remove(x)      # 삭제 (없으면 에러)
.discard(x)     # 삭제 (없어도 OK)
.union(other)   # 합집합
.intersection(other)  # 교집합
.difference(other)    # 차집합
```

## 6. 성능 팁

### 멤버십 테스트

```python
# 리스트 vs 세트
items_list = list(range(10000))
items_set = set(range(10000))

# ❌ 느림 (O(n))
if 9999 in items_list:
    pass

# ✅ 빠름 (O(1))
if 9999 in items_set:
    pass
```

### 문자열 연결

```python
# ❌ 느림 (매번 새 문자열 생성)
result = ""
for word in words:
    result += word + " "

# ✅ 빠름 (join 사용)
result = " ".join(words)
```

### 리스트 vs 제너레이터

```python
# 메모리 많이 사용
squares_list = [x**2 for x in range(1000000)]

# 메모리 효율적 (필요할 때만 생성)
squares_gen = (x**2 for x in range(1000000))
for square in squares_gen:
    print(square)
```

## 요약 정리

### 핵심 자료형

| 자료형 | 특징 | 주요 용도 |
|--------|------|-----------|
| `list` | 가변, 순서O, 중복O | 일반적인 순차 데이터 |
| `tuple` | 불변, 순서O, 중복O | 고정 데이터, 다중 반환 |
| `dict` | 가변, 키-값, 순서O | 빠른 조회, 설정, JSON |
| `set` | 가변, 순서X, 중복X | 중복 제거, 집합 연산 |

### 강력한 문법

```python
# 슬라이싱
list[1:4]       # 일부
list[::-1]      # 역순

# 언패킹
a, b = b, a     # 스왑
first, *rest = list

# 컴프리헨션
[x**2 for x in range(10) if x % 2 == 0]
{k: v for k, v in dict.items() if v > 0}

# 다중 비교
if 1 < x < 10:
    pass

# enumerate, zip
for i, item in enumerate(items):
    pass
for a, b in zip(list1, list2):
    pass
```

### 자주 쓰는 패턴

```python
# 안전한 접근
dict.get(key, default)

# 중복 제거
unique = list(set(items))

# 정렬
sorted(items, key=lambda x: x['field'])

# 파일 처리
with open('file.txt') as f:
    content = f.read()

# 조인/스플릿
" ".join(words)
text.split()
```

## 참고 자료

- [Python 공식 문서 - Data Structures](https://docs.python.org/3/tutorial/datastructures.html)
- [Python 공식 문서 - Built-in Types](https://docs.python.org/3/library/stdtypes.html)
- [Real Python - Python Data Structures](https://realpython.com/python-data-structures/)
- [Effective Python (Book)](https://effectivepython.com/)
