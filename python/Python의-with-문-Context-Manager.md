# Python의 with 문 (Context Manager)

Python의 `with` 문과 Context Manager에 대해 알아봅니다.

## 결론부터 말하면

`with` 문은 **자동으로 리소스를 정리**해주는 Python의 예약어입니다. Java의 `try-with-resources`와 비슷한 역할을 합니다.

```python
# ✅ with 사용: 자동으로 파일 닫힘
with open("file.txt", "r") as f:
    content = f.read()
# 여기서 자동으로 f.close() 호출됨

# ❌ with 없이: 직접 닫아야 함
f = open("file.txt", "r")
try:
    content = f.read()
finally:
    f.close()  # 직접 닫아야 함
```

## 1. with 문이 필요한 이유

### 문제 상황

```python
# ❌ 파일을 열고 닫는 것을 깜빡함
f = open("file.txt", "r")
content = f.read()
# f.close()를 안 함! → 메모리 누수!

# ❌ 예외 발생 시 파일이 안 닫힘
f = open("file.txt", "r")
content = f.read()
result = 1 / 0  # 에러 발생!
f.close()  # 실행 안 됨!

# ✅ try-finally로 해결 (하지만 코드가 길어짐)
f = open("file.txt", "r")
try:
    content = f.read()
    result = 1 / 0
finally:
    f.close()  # 에러가 나도 실행됨
```

### with 문으로 해결

```python
# ✅ with 문: 간결하고 안전함
with open("file.txt", "r") as f:
    content = f.read()
    result = 1 / 0  # 에러가 나도
# 자동으로 f.close() 호출됨!
```

## 2. 기본 문법

### 기본 형태

```python
with 표현식 as 변수:
    # 코드 블록
    pass
# 블록을 벗어나면 자동으로 정리됨
```

### 실제 예시

```python
# 파일 읽기
with open("data.txt", "r") as f:
    data = f.read()
    print(data)
# 자동으로 f.close()

# 파일 쓰기
with open("output.txt", "w") as f:
    f.write("Hello, World!")
# 자동으로 f.close()
```

## 3. Java와 비교

### Java의 try-with-resources

```java
// Java: try-with-resources (Java 7+)
try (FileReader reader = new FileReader("file.txt")) {
    int data = reader.read();
    // ...
} // 자동으로 reader.close() 호출

// Redis 예시
try (RedisClient client = new RedisClient(config)) {
    client.get("key");
} // 자동으로 client.close()
```

### Python의 with 문

```python
# Python: with 문
with open("file.txt", "r") as f:
    data = f.read()
    # ...
# 자동으로 f.close() 호출

# Redis 예시
with RedisClient(config) as client:
    client.get("key")
# 자동으로 정리
```

### 문법 비교

| 언어 | 문법 | 역할 |
|------|------|------|
| **Java** | `try (Resource r = ...)` | 자동 리소스 정리 |
| **Python** | `with expression as var:` | 자동 리소스 정리 |

## 4. 자주 쓰는 예시

### 파일 처리

```python
# 파일 읽기
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()
    print(content)

# 파일 쓰기
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("첫 번째 줄\n")
    f.write("두 번째 줄\n")

# 파일 추가
with open("log.txt", "a", encoding="utf-8") as f:
    f.write("새로운 로그\n")

# 여러 줄 읽기
with open("data.txt", "r") as f:
    for line in f:
        print(line.strip())
```

### 데이터베이스 연결

```python
import psycopg2

# PostgreSQL 연결
with psycopg2.connect(
    host="localhost",
    database="mydb",
    user="user",
    password="password"
) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        for row in results:
            print(row)
# 자동으로 cursor와 conn 정리
```

### Redis 연결

```python
import redis

# Redis 연결
with redis.Redis(host='localhost', port=6379) as client:
    client.set('key', 'value')
    value = client.get('key')
    print(value)
# 자동으로 연결 종료
```

### 파일 Lock

```python
import threading

lock = threading.Lock()

# Lock 사용
with lock:
    # 이 블록은 한 번에 하나의 스레드만 실행 가능
    print("Critical section")
# 자동으로 lock.release()
```

## 5. 여러 개 동시에 사용

### 여러 파일 동시에 열기

```python
# 방법 1: 한 줄에
with open("input.txt", "r") as infile, open("output.txt", "w") as outfile:
    content = infile.read()
    outfile.write(content.upper())

# 방법 2: 줄바꿈으로 구분 (Python 3.1+)
with open("input.txt", "r") as infile, \
     open("output.txt", "w") as outfile:
    content = infile.read()
    outfile.write(content.upper())

# 방법 3: 중첩
with open("input.txt", "r") as infile:
    with open("output.txt", "w") as outfile:
        content = infile.read()
        outfile.write(content.upper())
```

### 데이터베이스 트랜잭션

```python
import psycopg2

with psycopg2.connect(...) as conn:
    with conn.cursor() as cursor:
        # 여러 쿼리 실행
        cursor.execute("INSERT INTO users (name) VALUES (%s)", ("홍길동",))
        cursor.execute("UPDATE accounts SET balance = balance - 1000")
    # 커밋 또는 롤백 자동 처리
```

## 6. Context Manager 작동 원리

### 간단한 설명

`with` 문은 **Context Manager**라는 객체를 사용합니다. Context Manager는 두 가지 특별한 메서드를 가지고 있습니다:

- `__enter__()`: `with` 블록에 들어갈 때 실행
- `__exit__()`: `with` 블록을 나갈 때 실행

### 직접 만들어보기

```python
class FileManager:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        """with 블록에 들어갈 때 실행"""
        print(f"파일 열기: {self.filename}")
        self.file = open(self.filename, self.mode)
        return self.file  # as 변수에 할당됨

    def __exit__(self, exc_type, exc_val, exc_tb):
        """with 블록을 나갈 때 실행"""
        if self.file:
            print(f"파일 닫기: {self.filename}")
            self.file.close()
        return False  # 예외를 다시 발생시킴

# 사용
with FileManager("test.txt", "w") as f:
    f.write("Hello, World!")
# 출력:
# 파일 열기: test.txt
# 파일 닫기: test.txt
```

### 실행 순서

```python
with FileManager("test.txt", "w") as f:
    # 1. __enter__() 실행
    # 2. 반환값이 f에 할당됨
    f.write("Hello")
    # 3. 블록 내 코드 실행
# 4. __exit__() 실행 (에러가 나도 실행됨!)
```

## 7. 실전 예제

### 타이머 Context Manager

```python
import time

class Timer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        self.elapsed = self.end - self.start
        print(f"실행 시간: {self.elapsed:.2f}초")
        return False

# 사용
with Timer():
    # 시간을 측정하고 싶은 코드
    total = 0
    for i in range(1000000):
        total += i
    print(f"합계: {total}")
# 출력:
# 합계: 499999500000
# 실행 시간: 0.05초
```

### 임시 디렉토리 변경

```python
import os

class ChangeDirectory:
    def __init__(self, new_path):
        self.new_path = new_path
        self.old_path = None

    def __enter__(self):
        self.old_path = os.getcwd()
        os.chdir(self.new_path)
        print(f"디렉토리 변경: {self.old_path} → {self.new_path}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.old_path)
        print(f"디렉토리 복원: {self.new_path} → {self.old_path}")
        return False

# 사용
print(f"현재 위치: {os.getcwd()}")
with ChangeDirectory("/tmp"):
    print(f"임시 위치: {os.getcwd()}")
    # /tmp에서 작업
print(f"다시 원래 위치: {os.getcwd()}")
```

### 데이터베이스 트랜잭션

```python
class DatabaseTransaction:
    def __init__(self, connection):
        self.conn = connection

    def __enter__(self):
        # 트랜잭션 시작
        self.conn.execute("BEGIN")
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # 에러 없음 → 커밋
            self.conn.execute("COMMIT")
            print("커밋 완료")
        else:
            # 에러 발생 → 롤백
            self.conn.execute("ROLLBACK")
            print("롤백 완료")
        return False  # 예외 전파

# 사용
with DatabaseTransaction(conn) as db:
    db.execute("INSERT INTO users (name) VALUES ('홍길동')")
    db.execute("UPDATE accounts SET balance = balance - 1000")
# 자동으로 커밋 또는 롤백
```

## 8. contextlib 모듈

Python의 `contextlib` 모듈을 사용하면 더 간단하게 Context Manager를 만들 수 있습니다.

### @contextmanager 데코레이터

```python
from contextlib import contextmanager

@contextmanager
def file_manager(filename, mode):
    # __enter__ 부분
    print(f"파일 열기: {filename}")
    f = open(filename, mode)
    try:
        yield f  # as 변수에 할당됨
    finally:
        # __exit__ 부분
        print(f"파일 닫기: {filename}")
        f.close()

# 사용
with file_manager("test.txt", "w") as f:
    f.write("Hello, World!")
```

### 타이머 예제 (간단 버전)

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(name):
    start = time.time()
    print(f"[{name}] 시작")
    try:
        yield
    finally:
        end = time.time()
        print(f"[{name}] 완료 - {end - start:.2f}초")

# 사용
with timer("데이터 처리"):
    total = sum(range(1000000))
    print(f"합계: {total}")
# 출력:
# [데이터 처리] 시작
# 합계: 499999500000
# [데이터 처리] 완료 - 0.05초
```

### 임시 환경변수 설정

```python
from contextlib import contextmanager
import os

@contextmanager
def temp_env_var(key, value):
    old_value = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old_value is None:
            del os.environ[key]
        else:
            os.environ[key] = old_value

# 사용
print(os.environ.get("MY_VAR"))  # None
with temp_env_var("MY_VAR", "temporary"):
    print(os.environ.get("MY_VAR"))  # "temporary"
print(os.environ.get("MY_VAR"))  # None (복원됨)
```

## 9. 예외 처리

### with 문에서 예외 발생 시

```python
class MyContext:
    def __enter__(self):
        print("들어감")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"나감 - 예외 타입: {exc_type}")
        if exc_type is not None:
            print(f"예외 발생: {exc_val}")
        return False  # False = 예외를 다시 발생시킴

# 정상 종료
with MyContext():
    print("작업 중")
# 출력:
# 들어감
# 작업 중
# 나감 - 예외 타입: None

# 예외 발생
try:
    with MyContext():
        print("작업 중")
        raise ValueError("에러 발생!")
except ValueError as e:
    print(f"예외 잡음: {e}")
# 출력:
# 들어감
# 작업 중
# 나감 - 예외 타입: <class 'ValueError'>
# 예외 발생: 에러 발생!
# 예외 잡음: 에러 발생!
```

### 예외를 삼키기 (조심해서 사용!)

```python
class SuppressException:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print(f"예외 무시: {exc_val}")
            return True  # True = 예외를 삼킴

# 예외가 발생해도 프로그램이 멈추지 않음
with SuppressException():
    print("1")
    raise ValueError("에러!")
    print("2")  # 실행 안 됨
print("3")  # 실행됨!
# 출력:
# 1
# 예외 무시: 에러!
# 3
```

## 10. 자주 사용하는 패턴 정리

### 파일 작업

```python
# 읽기
with open("file.txt", "r", encoding="utf-8") as f:
    content = f.read()

# 쓰기
with open("file.txt", "w", encoding="utf-8") as f:
    f.write("내용")

# 한 줄씩 읽기
with open("file.txt", "r") as f:
    for line in f:
        print(line.strip())

# 복사
with open("input.txt", "r") as src, open("output.txt", "w") as dst:
    dst.write(src.read())
```

### 데이터베이스

```python
# PostgreSQL
import psycopg2

with psycopg2.connect(...) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()

# SQLite
import sqlite3

with sqlite3.connect("database.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
```

### Lock (멀티스레딩)

```python
import threading

lock = threading.Lock()

with lock:
    # 한 번에 하나의 스레드만 실행
    shared_resource += 1
```

### 환경 변수

```python
import os
from contextlib import contextmanager

@contextmanager
def env_var(key, value):
    old = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old is None:
            del os.environ[key]
        else:
            os.environ[key] = old
```

## 요약

### with 문이란?

**자동으로 리소스를 정리**해주는 Python의 예약어

### 문법

```python
with 표현식 as 변수:
    # 코드
# 자동으로 정리됨
```

### Java와 비교

| Python | Java |
|--------|------|
| `with open(...) as f:` | `try (FileReader f = ...)` |
| Context Manager | AutoCloseable |

### 핵심 포인트

1. **자동 리소스 관리**: 파일, 연결, Lock 등 자동으로 정리
2. **예외 안전**: 에러가 나도 정리 보장
3. **간결한 코드**: try-finally 불필요
4. **작동 원리**: `__enter__`와 `__exit__` 메서드

### 자주 쓰는 경우

```python
# 1. 파일
with open("file.txt") as f:
    content = f.read()

# 2. 데이터베이스
with psycopg2.connect(...) as conn:
    with conn.cursor() as cursor:
        cursor.execute(...)

# 3. Lock
with lock:
    shared_resource += 1

# 4. 여러 개 동시에
with open("in.txt") as f1, open("out.txt", "w") as f2:
    f2.write(f1.read())
```

### Context Manager 만들기

```python
# 방법 1: 클래스
class MyContext:
    def __enter__(self):
        # 준비 작업
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 정리 작업
        return False

# 방법 2: @contextmanager
from contextlib import contextmanager

@contextmanager
def my_context():
    # 준비 작업
    try:
        yield
    finally:
        # 정리 작업
        pass
```

### 언제 사용?

**✅ with 문 사용:**
- 파일 작업
- 데이터베이스 연결
- Lock, Semaphore
- 네트워크 연결
- 자동으로 정리가 필요한 모든 리소스

**❌ with 문 불필요:**
- 간단한 계산
- 리소스 정리가 필요 없는 경우

## 참고 자료

- [PEP 343 - The "with" Statement](https://www.python.org/dev/peps/pep-0343/)
- [Python 공식 문서 - with statement](https://docs.python.org/3/reference/compound_stmts.html#with)
- [Python 공식 문서 - contextlib](https://docs.python.org/3/library/contextlib.html)
- [Real Python - Context Managers and Python's with Statement](https://realpython.com/python-with-statement/)
