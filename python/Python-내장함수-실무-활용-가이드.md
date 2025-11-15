# Python 내장함수 실무 활용 가이드

파이썬에서 실무에서 가장 자주 사용되는 내장함수들을 실전 예제와 함께 정리합니다.

## 결론부터 말하면

파이썬 내장함수는 **별도 import 없이 바로 사용할 수 있는 강력한 도구**들입니다. 특히 `len()`, `enumerate()`, `zip()`, `isinstance()`, `all()`, `any()` 등은 거의 매일 사용하게 되며, 이들을 잘 활용하면 코드를 간결하고 pythonic하게 작성할 수 있습니다.

```python
# 내장함수의 강력함
users = [{"name": "Alice", "active": True}, {"name": "Bob", "active": False}]

# len, filter, lambda를 조합한 간결한 코드
active_count = len(list(filter(lambda u: u["active"], users)))

# enumerate로 인덱스와 값 동시 접근
for idx, user in enumerate(users, start=1):
    print(f"{idx}. {user['name']}")
```

## 1. 데이터 변환 & 타입 관련

### len() - 길이 측정

**가장 기본적이면서 필수적인 함수**

```python
# 데이터 검증
def validate_password(password):
    if len(password) < 8:
        raise ValueError("비밀번호는 8자 이상이어야 합니다")
    return True

# 페이지네이션
def paginate(items, page_size=10):
    total_items = len(items)
    total_pages = total_items // page_size + (1 if total_items % page_size else 0)
    return total_pages

# 빈 값 체크
data = []
if len(data) == 0:  # 또는 if not data:
    print("데이터가 없습니다")
```

**언제 사용?**
- 컬렉션 크기 확인
- 페이지네이션 계산
- 빈 값 검증

### str(), int(), float() - 타입 변환

**외부 데이터 처리시 필수**

```python
# API 응답 처리
response_data = {
    "price": "29.99",
    "quantity": "5",
    "user_id": "12345"
}

total = float(response_data["price"]) * int(response_data["quantity"])
# 149.95

# CSV 데이터 처리
csv_row = "Alice,30,85.5"
name, age, score = csv_row.split(",")
age = int(age)          # "30" -> 30
score = float(score)    # "85.5" -> 85.5

# 로깅용 문자열 변환
user_id = 12345
log_message = f"User {str(user_id)} logged in at {str(datetime.now())}"
```

**언제 사용?**
- API/CSV 데이터 파싱
- 사용자 입력 처리
- 로그 메시지 생성

### type(), isinstance() - 타입 체크

**안전한 코드 작성의 핵심**

```python
# 다형성 처리
def process_data(data):
    """다양한 타입의 데이터를 처리"""
    if isinstance(data, dict):
        return data.get("value")
    elif isinstance(data, list):
        return data[0] if data else None
    elif isinstance(data, str):
        return data.strip()
    elif isinstance(data, (int, float)):
        return data * 2
    return data

# 입력 검증
def safe_divide(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("숫자만 입력 가능합니다")
    if b == 0:
        raise ValueError("0으로 나눌 수 없습니다")
    return a / b

# 클래스 체크
class User:
    pass

obj = User()
print(isinstance(obj, User))  # True
print(type(obj) == User)      # True

# 여러 타입 체크 (isinstance가 더 pythonic)
value = 42
if isinstance(value, (int, float)):  # int 또는 float
    print("숫자입니다")
```

**언제 사용?**
- 함수 인자 검증
- 다형성 구현
- 타입별 분기 처리

## 2. 시퀀스 처리

### enumerate() - 인덱스와 값 동시 접근

**for문에서 인덱스가 필요할 때 필수**

```python
# 에러 위치 표시
def validate_rows(data_rows):
    errors = []
    for idx, row in enumerate(data_rows, start=1):
        if not row.get("email"):
            errors.append(f"Line {idx}: 이메일이 누락되었습니다")
        if not row.get("name"):
            errors.append(f"Line {idx}: 이름이 누락되었습니다")
    return errors

# CSV 처리 (헤더 스킵)
csv_lines = [
    "name,age,city",
    "Alice,30,Seoul",
    "Bob,25,Busan"
]

for i, line in enumerate(csv_lines):
    if i == 0:  # 헤더 스킵
        continue
    print(f"Row {i}: {line}")

# 순위 매기기
scores = [95, 88, 92, 85]
for rank, score in enumerate(sorted(scores, reverse=True), start=1):
    print(f"{rank}등: {score}점")
# 1등: 95점
# 2등: 92점
# 3등: 88점
# 4등: 85점
```

**언제 사용?**
- 인덱스와 값이 모두 필요할 때
- 에러 메시지에 라인 번호 표시
- 순위/순서 부여

### zip() - 여러 시퀀스 병합

**병렬 데이터 처리의 핵심**

```python
# 데이터베이스 결과를 딕셔너리로 변환
columns = ["id", "name", "email", "age"]
row = [1, "Alice", "alice@example.com", 30]
user_dict = dict(zip(columns, row))
# {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'age': 30}

# 여러 리스트 병렬 처리
names = ["file1.txt", "file2.txt", "file3.txt"]
sizes = [1024, 2048, 512]
dates = ["2024-01-01", "2024-01-02", "2024-01-03"]

for name, size, date in zip(names, sizes, dates):
    print(f"{name}: {size}KB (created: {date})")

# 두 리스트 비교
expected = [1, 2, 3, 4]
actual = [1, 2, 5, 4]

for i, (exp, act) in enumerate(zip(expected, actual)):
    if exp != act:
        print(f"Index {i}: expected {exp}, got {act}")
# Index 2: expected 3, got 5

# 딕셔너리 키-값 쌍으로 분리
data = {"a": 1, "b": 2, "c": 3}
keys, values = zip(*data.items())
# keys: ('a', 'b', 'c')
# values: (1, 2, 3)
```

**언제 사용?**
- DB 결과를 딕셔너리로 변환
- 여러 리스트를 동시에 순회
- 데이터 비교

### sorted(), reversed() - 정렬

**데이터 정렬의 표준**

```python
# 숫자 정렬
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
print(sorted(numbers))              # [1, 1, 2, 3, 4, 5, 6, 9]
print(sorted(numbers, reverse=True)) # [9, 6, 5, 4, 3, 2, 1, 1]

# 문자열 정렬
names = ["Bob", "alice", "Charlie"]
print(sorted(names))                # ['Bob', 'Charlie', 'alice'] (대문자 우선)
print(sorted(names, key=str.lower)) # ['alice', 'Bob', 'Charlie']

# 복잡한 객체 정렬
users = [
    {"name": "Alice", "age": 30, "score": 85},
    {"name": "Bob", "age": 25, "score": 92},
    {"name": "Charlie", "age": 35, "score": 78}
]

# 나이순 정렬
sorted_by_age = sorted(users, key=lambda x: x["age"])

# 점수 역순 정렬
sorted_by_score = sorted(users, key=lambda x: x["score"], reverse=True)

# 다중 정렬 (점수 내림차순, 같으면 나이 오름차순)
sorted_multi = sorted(users, key=lambda x: (-x["score"], x["age"]))

# 성능 분석 결과 정렬
api_metrics = [
    {"endpoint": "/api/users", "latency": 120},
    {"endpoint": "/api/posts", "latency": 45},
    {"endpoint": "/api/comments", "latency": 200}
]
fastest_apis = sorted(api_metrics, key=lambda x: x["latency"])

# reversed() - 역순 반복
for num in reversed(range(1, 6)):
    print(num)  # 5, 4, 3, 2, 1
```

**언제 사용?**
- 데이터 정렬
- 순위 계산
- 성능 분석 결과 표시

### range() - 반복 범위

**반복문의 기본**

```python
# 기본 사용
for i in range(5):
    print(i)  # 0, 1, 2, 3, 4

# 시작-끝
for i in range(1, 6):
    print(i)  # 1, 2, 3, 4, 5

# 시작-끝-스텝
for i in range(0, 10, 2):
    print(i)  # 0, 2, 4, 6, 8

# 배치 처리
def process_in_batches(items, batch_size=100):
    """대용량 데이터를 배치로 처리"""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        save_to_database(batch)
        print(f"Processed {i + len(batch)}/{len(items)}")

# 재시도 로직
def api_call_with_retry(url, max_retries=3):
    """API 호출 실패시 재시도"""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == max_retries:
                raise
            wait_time = 2 ** attempt  # 지수 백오프
            print(f"Retry {attempt}/{max_retries} after {wait_time}s...")
            time.sleep(wait_time)

# 역순 range
for i in range(10, 0, -1):
    print(i)  # 10, 9, 8, ..., 1
```

**언제 사용?**
- 특정 횟수만큼 반복
- 배치 처리
- 재시도 로직

## 3. 컬렉션 처리

### all(), any() - 조건 검사

**여러 조건을 한번에 체크**

```python
# 폼 검증
def validate_form(form_data):
    """모든 필수 필드가 있고 비어있지 않은지 확인"""
    required_fields = ["email", "password", "name", "phone"]

    # 모든 필드가 존재하는지
    if not all(field in form_data for field in required_fields):
        return False, "필수 필드가 누락되었습니다"

    # 모든 필드가 비어있지 않은지
    if not all(len(form_data[f].strip()) > 0 for f in required_fields):
        return False, "빈 필드가 있습니다"

    return True, "OK"

# 권한 검사
def check_permissions(user_permissions, required_permissions):
    """사용자가 모든 필요한 권한을 가지고 있는지"""
    return all(perm in user_permissions for perm in required_permissions)

user_perms = ["read", "write"]
required = ["read", "write", "delete"]
has_access = check_permissions(user_perms, required)  # False

# 하나라도 있으면 True
def has_any_error(responses):
    """응답 중 하나라도 에러가 있는지"""
    return any(r.get("error") is not None for r in responses)

responses = [
    {"status": "success", "error": None},
    {"status": "failed", "error": "Connection timeout"},
    {"status": "success", "error": None}
]
has_error = has_any_error(responses)  # True

# 빈 리스트 체크
numbers = [0, 0, 0]
print(any(numbers))  # True (0이 아닌 값이 있는지)
print(all(numbers))  # False (모두 True인지)

empty = []
print(any(empty))   # False
print(all(empty))   # True (공집합은 all에서 True)
```

**언제 사용?**
- 여러 조건 동시 검사
- 폼 검증
- 권한 체크

### sum(), min(), max() - 집계 함수

**간단한 통계 계산**

```python
# 대시보드 통계
daily_sales = [1200, 3400, 2100, 5600, 4200]

total_sales = sum(daily_sales)           # 16500
avg_sales = sum(daily_sales) / len(daily_sales)  # 3300.0
best_day = max(daily_sales)              # 5600
worst_day = min(daily_sales)             # 1200

print(f"총 매출: {total_sales:,}원")
print(f"평균: {avg_sales:,.0f}원")
print(f"최고: {best_day:,}원 / 최저: {worst_day:,}원")

# 점수 계산
scores = [85, 92, 78, 95, 88]
total = sum(scores)
max_score = max(scores)
min_score = min(scores)
average = total / len(scores)

# key 파라미터 활용
users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Charlie", "age": 35}
]

oldest = max(users, key=lambda u: u["age"])  # {"name": "Charlie", "age": 35}
youngest = min(users, key=lambda u: u["age"])  # {"name": "Bob", "age": 25}

# 문자열도 가능
names = ["Alice", "Bob", "Charlie", "David"]
print(min(names))  # "Alice"
print(max(names))  # "David"

longest_name = max(names, key=len)  # "Charlie"

# sum with start value
numbers = [1, 2, 3, 4, 5]
print(sum(numbers, 10))  # 25 (10 + 1 + 2 + 3 + 4 + 5)
```

**언제 사용?**
- 통계 계산
- 최댓값/최솟값 찾기
- 평균 계산

### filter(), map() - 함수형 처리

**데이터 변환과 필터링**

```python
# 활성 사용자 필터링
users = [
    {"name": "Alice", "active": True, "age": 30},
    {"name": "Bob", "active": False, "age": 25},
    {"name": "Charlie", "active": True, "age": 35},
    {"name": "David", "active": False, "age": 28}
]

# filter - 조건에 맞는 항목만
active_users = list(filter(lambda u: u["active"], users))
# [{"name": "Alice", ...}, {"name": "Charlie", ...}]

# 30세 이상 활성 사용자
senior_active = list(filter(
    lambda u: u["active"] and u["age"] >= 30,
    users
))

# map - 각 항목을 변환
# 가격에 할인 적용
prices = [100, 200, 300, 400]
discounted = list(map(lambda p: p * 0.9, prices))
# [90.0, 180.0, 270.0, 360.0]

# ID만 추출
user_ids = list(map(lambda u: u["name"], users))
# ["Alice", "Bob", "Charlie", "David"]

# map과 filter 조합
# 활성 사용자의 이름만 추출
active_names = list(map(
    lambda u: u["name"],
    filter(lambda u: u["active"], users)
))
# ["Alice", "Charlie"]

# 실무 예제: API 응답 변환
api_response = [
    {"user_id": "1", "score": "85"},
    {"user_id": "2", "score": "92"},
    {"user_id": "3", "score": "78"}
]

# 타입 변환
processed = list(map(
    lambda item: {
        "user_id": int(item["user_id"]),
        "score": int(item["score"])
    },
    api_response
))

# 리스트 컴프리헨션과 비교 (더 pythonic)
# filter + map
result1 = list(map(lambda u: u["name"], filter(lambda u: u["active"], users)))

# list comprehension (권장)
result2 = [u["name"] for u in users if u["active"]]
```

**언제 사용?**
- 데이터 필터링
- 데이터 변환
- 함수형 프로그래밍 스타일

## 4. 딕셔너리 & 속성 접근

### getattr(), setattr(), hasattr() - 동적 속성 접근

**런타임에 속성 다루기**

```python
# 설정 클래스
class Config:
    DEBUG = False
    DATABASE_URL = "postgresql://localhost/db"
    API_KEY = ""
    MAX_CONNECTIONS = 10

config = Config()

# 환경변수로 설정 덮어쓰기
env_vars = {
    "DEBUG": "true",
    "API_KEY": "secret123",
    "UNKNOWN_KEY": "value"
}

for key, value in env_vars.items():
    if hasattr(config, key):
        setattr(config, key, value)
        print(f"Set {key} = {value}")

# 동적 메서드 호출
class DataProcessor:
    def process_json(self, data):
        return json.loads(data)

    def process_xml(self, data):
        return xmltodict.parse(data)

    def process_csv(self, data):
        return list(csv.reader(data.splitlines()))

processor = DataProcessor()
data_type = "json"  # 사용자 입력 또는 파일 확장자
data = '{"name": "Alice"}'

method_name = f"process_{data_type}"
if hasattr(processor, method_name):
    method = getattr(processor, method_name)
    result = method(data)
else:
    raise ValueError(f"지원하지 않는 형식: {data_type}")

# 기본값과 함께 getattr
class User:
    name = "Alice"

user = User()
print(getattr(user, "name", "Unknown"))   # "Alice"
print(getattr(user, "email", "Unknown"))  # "Unknown"
```

**언제 사용?**
- 동적 속성/메서드 접근
- 설정 관리
- 플러그인 시스템

### dict.get(), dict.setdefault() - 안전한 딕셔너리 접근

**KeyError 방지**

```python
# API 응답 안전하게 처리
response = {
    "status": "success",
    "data": {
        "user": "Alice",
        "age": 30
    }
}

# get() - KeyError 방지
user = response.get("data", {}).get("user", "Anonymous")
email = response.get("data", {}).get("email", "no-email@example.com")
error_msg = response.get("error", "No error")

# 중첩된 딕셔너리 안전하게 접근
config = {
    "database": {
        "host": "localhost",
        "port": 5432
    }
}

db_host = config.get("database", {}).get("host", "127.0.0.1")
db_user = config.get("database", {}).get("user", "postgres")

# setdefault() - 없으면 설정하고 반환
# 단어 빈도 카운터
text = "apple banana apple cherry banana apple"
word_count = {}

for word in text.split():
    word_count.setdefault(word, 0)
    word_count[word] += 1
# {'apple': 3, 'banana': 2, 'cherry': 1}

# 또는 get() 사용
word_count2 = {}
for word in text.split():
    word_count2[word] = word_count2.get(word, 0) + 1

# 그룹핑
users = [
    {"name": "Alice", "dept": "Engineering"},
    {"name": "Bob", "dept": "Sales"},
    {"name": "Charlie", "dept": "Engineering"}
]

by_dept = {}
for user in users:
    dept = user["dept"]
    by_dept.setdefault(dept, []).append(user["name"])
# {
#   "Engineering": ["Alice", "Charlie"],
#   "Sales": ["Bob"]
# }
```

**언제 사용?**
- API 응답 파싱
- 기본값 설정
- 그룹핑/카운팅

## 5. 입출력 & 파일 처리

### open() - 파일 처리

**파일 읽기/쓰기의 기본**

```python
# 텍스트 파일 읽기
with open('config.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 라인별로 읽기
with open('logs.txt', 'r', encoding='utf-8') as f:
    for line in f:
        print(line.strip())

# 에러 로그만 필터링
def read_error_logs(log_file):
    errors = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            if 'ERROR' in line or 'CRITICAL' in line:
                errors.append({
                    'line': line_num,
                    'message': line.strip()
                })
    return errors

# JSON 파일 읽기/쓰기
import json

# 읽기
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 쓰기
data = {"users": ["Alice", "Bob"], "count": 2}
with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# CSV 내보내기
users = [
    {"name": "Alice", "email": "alice@example.com"},
    {"name": "Bob", "email": "bob@example.com"}
]

with open('users.csv', 'w', encoding='utf-8') as f:
    f.write('name,email\n')
    for user in users:
        f.write(f"{user['name']},{user['email']}\n")

# 대용량 파일 처리 (메모리 효율적)
def process_large_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:  # 한 줄씩 읽어서 처리
            process_line(line)
            # 메모리에 전체 파일을 로드하지 않음

# 파일 append
with open('log.txt', 'a', encoding='utf-8') as f:
    f.write(f"{datetime.now()}: User logged in\n")
```

**언제 사용?**
- 설정 파일 읽기
- 로그 파일 처리
- 데이터 내보내기

### print() - 출력 & 디버깅

**디버깅과 로깅의 기본**

```python
# 기본 출력
name = "Alice"
age = 30
print(f"{name}은 {age}세입니다")

# 여러 값 출력
print("Name:", name, "Age:", age)

# sep, end 파라미터
print("A", "B", "C", sep="-")  # A-B-C
print("Loading", end="... ")   # 줄바꿈 없음
print("Done!")                 # Loading... Done!

# 진행률 표시
def process_files(files):
    total = len(files)
    for idx, file in enumerate(files, 1):
        # \r로 같은 줄에 덮어쓰기
        print(f"Processing {idx}/{total}: {file}", end='\r')
        time.sleep(0.1)  # 실제 처리
    print("\nComplete!")

# 디버깅용 출력
def debug_api_call(url, params):
    print(f"[DEBUG] URL: {url}")
    print(f"[DEBUG] Params: {params}")
    print(f"[DEBUG] Timestamp: {datetime.now()}", flush=True)

    response = requests.get(url, params=params)

    print(f"[DEBUG] Status: {response.status_code}")
    print(f"[DEBUG] Response: {response.text[:100]}...")

    return response

# 에러 출력 (stderr)
import sys
print("에러 발생!", file=sys.stderr)

# 파일로 출력
with open('output.txt', 'w') as f:
    print("Hello", "World", file=f)
```

**언제 사용?**
- 디버깅
- 진행률 표시
- 로깅

## 6. 객체 & 반복자

### iter(), next() - 반복자 제어

**메모리 효율적인 데이터 처리**

```python
# 기본 사용
numbers = [1, 2, 3, 4, 5]
it = iter(numbers)

print(next(it))  # 1
print(next(it))  # 2
print(next(it))  # 3

# 기본값 지정 (StopIteration 방지)
print(next(it, "끝"))  # 4
print(next(it, "끝"))  # 5
print(next(it, "끝"))  # "끝"

# 대용량 파일 청크 처리
from itertools import islice

def read_in_chunks(file_path, chunk_size=1000):
    """파일을 청크 단위로 읽기"""
    with open(file_path) as f:
        lines = iter(f)
        while True:
            chunk = list(islice(lines, chunk_size))
            if not chunk:
                break
            yield chunk

# 사용
for chunk in read_in_chunks('large_file.txt', chunk_size=100):
    process_chunk(chunk)  # 100줄씩 처리

# API 페이지네이션
class APIPageIterator:
    def __init__(self, url):
        self.url = url
        self.page = 1
        self.has_more = True

    def __iter__(self):
        return self

    def __next__(self):
        if not self.has_more:
            raise StopIteration

        response = requests.get(f"{self.url}?page={self.page}")
        data = response.json()

        if not data or len(data) == 0:
            raise StopIteration

        self.page += 1
        return data

# 사용
for page_data in APIPageIterator("https://api.example.com/users"):
    process_users(page_data)
```

**언제 사용?**
- 대용량 데이터 처리
- 메모리 효율 최적화
- 커스텀 반복자 구현

### vars(), dir() - 객체 검사

**디버깅과 리플렉션**

```python
# vars() - 객체의 __dict__ 반환
class User:
    def __init__(self, name, email, age):
        self.name = name
        self.email = email
        self.age = age

user = User("Alice", "alice@example.com", 30)
print(vars(user))
# {'name': 'Alice', 'email': 'alice@example.com', 'age': 30}

# 객체를 딕셔너리로 변환 (직렬화)
user_dict = vars(user)
json_str = json.dumps(user_dict)

# dir() - 객체의 속성과 메서드 목록
print(dir(user))
# ['__class__', ..., 'age', 'email', 'name']

# 사용자 정의 속성만 필터링
user_attrs = [attr for attr in dir(user) if not attr.startswith('_')]
print(user_attrs)  # ['age', 'email', 'name']

# API 응답 객체 디버깅
response = requests.get("https://api.example.com")

# 사용 가능한 메서드 확인
methods = [m for m in dir(response) if not m.startswith('_')]
print("Available methods:", methods)

# 속성 확인
if hasattr(response, 'json'):
    data = response.json()

# 모듈 탐색
import math
math_functions = [f for f in dir(math) if not f.startswith('_')]
print(math_functions)
# ['acos', 'asin', 'atan', 'ceil', 'cos', 'sin', ...]
```

**언제 사용?**
- 객체 직렬화
- 디버깅
- 동적 속성 탐색

## 7. 실무 통합 예제

### 예제 1: CSV 데이터 처리 파이프라인

```python
def process_user_csv(filename):
    """
    CSV 파일에서 사용자 데이터를 읽어
    검증하고 통계를 계산하는 완전한 파이프라인
    """

    # 1. 파일 읽기
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 2. 헤더와 데이터 분리
    if len(lines) == 0:
        return {"error": "파일이 비어있습니다"}

    headers = lines[0].strip().split(',')
    data_rows = lines[1:]

    # 3. 딕셔너리로 변환
    users = []
    errors = []

    for idx, row in enumerate(data_rows, start=2):  # 라인 번호는 2부터
        values = row.strip().split(',')

        # 컬럼 수 체크
        if len(values) != len(headers):
            errors.append(f"Line {idx}: 컬럼 수 불일치")
            continue

        user = dict(zip(headers, values))

        # 4. 검증
        required_fields = ['name', 'email', 'age', 'active']

        # 모든 필수 필드가 있는지
        if not all(field in user for field in required_fields):
            errors.append(f"Line {idx}: 필수 필드 누락")
            continue

        # 빈 값이 있는지
        if any(not user.get(f) for f in required_fields):
            errors.append(f"Line {idx}: 빈 필드 존재")
            continue

        # 5. 타입 변환
        try:
            user['age'] = int(user['age'])
            user['active'] = user['active'].lower() == 'true'
        except ValueError as e:
            errors.append(f"Line {idx}: 타입 변환 오류 - {e}")
            continue

        users.append(user)

    # 6. 통계 계산
    if not users:
        return {
            "error": "유효한 사용자 데이터가 없습니다",
            "errors": errors
        }

    # 활성 사용자 필터링
    active_users = list(filter(lambda u: u['active'], users))

    # 나이 통계
    ages = [u['age'] for u in users]

    stats = {
        "total_users": len(users),
        "active_users": len(active_users),
        "inactive_users": len(users) - len(active_users),
        "age_stats": {
            "min": min(ages),
            "max": max(ages),
            "average": sum(ages) / len(ages)
        }
    }

    # 7. 나이순 정렬
    sorted_users = sorted(users, key=lambda u: u['age'], reverse=True)

    # 8. 결과 반환
    return {
        "users": sorted_users,
        "stats": stats,
        "errors": errors if errors else None
    }

# 사용
result = process_user_csv('users.csv')
print(f"총 {result['stats']['total_users']}명 처리")
print(f"활성 사용자: {result['stats']['active_users']}명")
print(f"평균 나이: {result['stats']['age_stats']['average']:.1f}세")
```

### 예제 2: API 응답 처리 및 검증

```python
def process_api_response(response_data):
    """
    API 응답을 안전하게 파싱하고 검증
    """

    # 1. 기본 구조 검증
    if not isinstance(response_data, dict):
        raise TypeError("응답은 딕셔너리여야 합니다")

    # 2. 필수 필드 확인
    required_keys = ['status', 'data']
    if not all(key in response_data for key in required_keys):
        missing = [k for k in required_keys if k not in response_data]
        raise ValueError(f"필수 필드 누락: {missing}")

    # 3. 안전한 데이터 추출
    status = response_data.get('status')
    data = response_data.get('data', {})
    error = response_data.get('error')
    metadata = response_data.get('metadata', {})

    # 4. 상태 검증
    if status != 'success':
        error_msg = error or "알 수 없는 오류"
        raise Exception(f"API 오류: {error_msg}")

    # 5. 데이터 타입 검증
    if not isinstance(data, (dict, list)):
        raise TypeError("data는 dict 또는 list여야 합니다")

    # 6. 리스트인 경우 각 항목 검증
    if isinstance(data, list):
        validated_items = []

        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                print(f"Warning: Item {idx}는 딕셔너리가 아닙니다")
                continue

            # 필수 필드 체크
            if hasattr(item, 'get'):
                validated_items.append(item)

        data = validated_items

    # 7. 페이지네이션 정보 추출
    page_info = {
        'page': metadata.get('page', 1),
        'per_page': metadata.get('per_page', 10),
        'total': metadata.get('total', len(data) if isinstance(data, list) else 1)
    }

    return {
        'data': data,
        'pagination': page_info,
        'timestamp': metadata.get('timestamp')
    }

# 사용 예제
response = {
    "status": "success",
    "data": [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ],
    "metadata": {
        "page": 1,
        "per_page": 10,
        "total": 2
    }
}

result = process_api_response(response)
print(f"총 {result['pagination']['total']}개 항목")
```

### 예제 3: 배치 작업 처리기

```python
def batch_processor(items, batch_size=100, max_retries=3):
    """
    대량의 데이터를 배치로 나누어 안전하게 처리
    """

    total_items = len(items)
    total_batches = (total_items + batch_size - 1) // batch_size

    results = []
    failed_batches = []

    print(f"총 {total_items}개 항목을 {total_batches}개 배치로 처리")

    # 배치 단위로 처리
    for batch_idx in range(0, total_items, batch_size):
        batch_num = batch_idx // batch_size + 1
        batch = items[batch_idx:batch_idx + batch_size]

        # 재시도 로직
        for attempt in range(1, max_retries + 1):
            try:
                # 진행률 표시
                progress = (batch_idx + len(batch)) / total_items * 100
                print(f"배치 {batch_num}/{total_batches} "
                      f"({progress:.1f}%) 처리 중...", end='\r')

                # 실제 처리 (예: DB 저장)
                batch_result = save_to_database(batch)
                results.extend(batch_result)

                break  # 성공하면 재시도 루프 탈출

            except Exception as e:
                if attempt == max_retries:
                    print(f"\n배치 {batch_num} 실패: {e}")
                    failed_batches.append({
                        'batch_num': batch_num,
                        'items': batch,
                        'error': str(e)
                    })
                else:
                    wait_time = 2 ** attempt
                    print(f"\n재시도 {attempt}/{max_retries} "
                          f"(대기: {wait_time}초)...")
                    time.sleep(wait_time)

    print("\n처리 완료!")

    # 통계
    total_processed = len(results)
    total_failed = sum(len(b['items']) for b in failed_batches)

    return {
        'total_items': total_items,
        'processed': total_processed,
        'failed': total_failed,
        'success_rate': (total_processed / total_items * 100) if total_items > 0 else 0,
        'failed_batches': failed_batches if failed_batches else None,
        'results': results
    }

# 사용
items = range(1, 1001)  # 1000개 항목
result = batch_processor(list(items), batch_size=100)
print(f"성공률: {result['success_rate']:.1f}%")
```

## 핵심 요약

### 가장 자주 쓰는 TOP 10

1. **len()** - 길이 확인 (필수)
2. **enumerate()** - 인덱스와 값 동시 접근
3. **zip()** - 여러 리스트 병합
4. **isinstance()** - 타입 체크
5. **all() / any()** - 조건 검사
6. **sorted()** - 정렬
7. **range()** - 반복
8. **sum() / min() / max()** - 집계
9. **open()** - 파일 처리
10. **print()** - 디버깅

### 실무 팁

**타입 안전성**
```python
# ❌ 나쁜 예
def process(data):
    return data["value"]  # KeyError 가능

# ✅ 좋은 예
def process(data):
    if not isinstance(data, dict):
        raise TypeError("딕셔너리가 필요합니다")
    return data.get("value", "기본값")
```

**리스트 컴프리헨션 vs filter/map**
```python
# filter + map (함수형)
result = list(map(lambda x: x * 2, filter(lambda x: x > 0, numbers)))

# 리스트 컴프리헨션 (pythonic - 권장)
result = [x * 2 for x in numbers if x > 0]
```

**안전한 딕셔너리 접근**
```python
# ❌ 위험
value = data["key"]["nested"]["deep"]

# ✅ 안전
value = data.get("key", {}).get("nested", {}).get("deep", "기본값")
```

이 내장함수들을 마스터하면 파이썬 코드가 훨씬 간결하고 pythonic해집니다!
