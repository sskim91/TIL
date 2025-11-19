# Python asyncio

Python 비동기 프로그래밍의 핵심 asyncio 라이브러리 완벽 가이드

## 결론부터 말하면

**asyncio는 Python 표준 라이브러리**로, **단일 스레드**에서 **비동기 I/O**를 처리합니다.

```python
# ========== Before: 동기 방식 (느림 ❌) ==========
import requests
import time

def fetch_websites():
    urls = ["https://api1.com", "https://api2.com", "https://api3.com"]
    results = []

    for url in urls:
        response = requests.get(url)  # 각각 1초씩 대기 (블로킹!)
        results.append(response.json())

    return results

start = time.time()
data = fetch_websites()
print(f"소요 시간: {time.time() - start:.2f}초")  # 약 3초 ❌


# ========== After: 비동기 방식 (빠름 ✅) ==========
import aiohttp
import asyncio

async def fetch_websites():
    urls = ["https://api1.com", "https://api2.com", "https://api3.com"]

    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)  # 동시에 요청!
        return [await r.json() for r in responses]

start = time.time()
data = asyncio.run(fetch_websites())
print(f"소요 시간: {time.time() - start:.2f}초")  # 약 1초 ✅ (3배 빠름!)
```

**핵심 개념:**
- **`async def`**: 비동기 함수 정의
- **`await`**: 대기하는 동안 다른 작업 가능
- **`asyncio.gather()`**: 여러 작업 동시 실행
- **I/O 대기 시간 활용**: CPU는 쉬지 않고 다른 작업 처리

**언제 사용하는가?**
- ✅ **I/O 집약적**: API 호출, 데이터베이스 쿼리, 파일 읽기/쓰기, 웹 스크래핑
- ❌ **CPU 집약적**: 수학 계산, 이미지 처리, 동영상 인코딩 (multiprocessing 사용)

## 1. asyncio란?

### 정의

```python
import asyncio  # Python 표준 라이브러리 (3.4+)

# asyncio = async + I/O
# "비동기 입출력 라이브러리"
```

**특징:**
- Python 3.4에 도입, 3.7부터 안정화
- 별도 설치 불필요 (표준 라이브러리)
- 단일 스레드 기반 동시성
- 이벤트 루프(Event Loop) 패턴

### asyncio가 해결하는 문제

```python
# ========== 문제: 블로킹 I/O ==========
import time

def download_file(filename):
    print(f"{filename} 다운로드 시작")
    time.sleep(2)  # 네트워크 대기 (블로킹!)
    print(f"{filename} 완료")
    return f"{filename} 데이터"

# 순차 실행
download_file("file1.txt")  # 2초
download_file("file2.txt")  # 2초
download_file("file3.txt")  # 2초
# 총 6초 소요 ❌


# ========== 해결: 비동기 I/O ==========
import asyncio

async def download_file(filename):
    print(f"{filename} 다운로드 시작")
    await asyncio.sleep(2)  # 다른 파일도 다운로드 가능!
    print(f"{filename} 완료")
    return f"{filename} 데이터"

async def main():
    # 3개 파일 동시 다운로드
    results = await asyncio.gather(
        download_file("file1.txt"),
        download_file("file2.txt"),
        download_file("file3.txt")
    )
    return results

asyncio.run(main())
# 총 2초 소요 ✅ (3배 빠름!)
```

## 2. 동기 vs 비동기

### 개념 비교

```python
# ========== 동기 (Synchronous) ==========
# "순차적 실행, 대기 시간에 아무것도 못함"

def cook_meal():
    # 밥 짓기
    print("밥 짓기 시작")
    time.sleep(3)  # 3초 대기 (블로킹!)
    print("밥 완성")

    # 국 끓이기
    print("국 끓이기 시작")
    time.sleep(2)  # 2초 대기 (블로킹!)
    print("국 완성")

    print("식사 준비 완료!")

cook_meal()
# 총 5초 소요

# 실행 순서:
# 밥 짓기 시작 (0초)
# ... 3초 대기 (밥솥만 동작, 사람은 가만히 있음) ...
# 밥 완성 (3초)
# 국 끓이기 시작 (3초)
# ... 2초 대기 (냄비만 동작, 사람은 가만히 있음) ...
# 국 완성 (5초)


# ========== 비동기 (Asynchronous) ==========
# "동시에 여러 일, 대기 시간 활용"

async def cook_rice():
    print("밥 짓기 시작")
    await asyncio.sleep(3)  # 기다리는 동안 다른 일 가능!
    print("밥 완성")

async def make_soup():
    print("국 끓이기 시작")
    await asyncio.sleep(2)  # 기다리는 동안 다른 일 가능!
    print("국 완성")

async def cook_meal():
    # 밥과 국을 동시에!
    await asyncio.gather(
        cook_rice(),
        make_soup()
    )
    print("식사 준비 완료!")

asyncio.run(cook_meal())
# 총 3초 소요 (밥 짓는 시간만큼)

# 실행 순서:
# 밥 짓기 시작 (0초)
# 국 끓이기 시작 (0초)
# ... 동시 진행 ...
# 국 완성 (2초)
# 밥 완성 (3초)
```

### 일상 생활 비유

```python
# ========== 동기: 빨래방에서 기다리기 ==========
def do_laundry_sync():
    print("세탁기에 빨래 넣기")
    time.sleep(30)  # 30분 대기 (세탁기만 동작)
    print("세탁 완료")

    print("건조기에 빨래 넣기")
    time.sleep(20)  # 20분 대기 (건조기만 동작)
    print("건조 완료")

# 총 50분 (빨래방에서 50분 대기)


# ========== 비동기: 빨래 돌리고 카페 가기 ==========
async def do_laundry_async():
    print("세탁기에 빨래 넣기")

    # 세탁하는 동안 다른 일 가능!
    await asyncio.gather(
        wash_clothes(),    # 30분 세탁
        go_to_cafe()       # 카페에서 커피 마시기
    )

    print("건조기에 빨래 넣기")

    # 건조하는 동안 다른 일 가능!
    await asyncio.gather(
        dry_clothes(),     # 20분 건조
        read_book()        # 책 읽기
    )

# 총 50분이지만 유용하게 시간 활용!
```

## 3. 블로킹 vs 논블로킹

### 블로킹 I/O (일반 Python)

```python
import requests

def fetch_user_data(user_id):
    # ❌ 블로킹: 응답 올 때까지 아무것도 못함
    response = requests.get(f"https://api.example.com/users/{user_id}")
    # 네트워크 응답 기다리는 중... (CPU는 쉼)
    return response.json()

# 3명의 사용자 데이터 가져오기
users = []
for user_id in [1, 2, 3]:
    user = fetch_user_data(user_id)  # 각각 1초씩 블로킹
    users.append(user)

# 총 3초 소요
```

### 논블로킹 I/O (asyncio)

```python
import aiohttp

async def fetch_user_data(user_id):
    # ✅ 논블로킹: 기다리는 동안 다른 요청 가능
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/users/{user_id}") as response:
            # 응답 기다리는 동안 다른 작업으로 전환!
            return await response.json()

# 3명의 사용자 데이터 동시에 가져오기
async def main():
    users = await asyncio.gather(
        fetch_user_data(1),
        fetch_user_data(2),
        fetch_user_data(3)
    )
    return users

asyncio.run(main())
# 총 1초 소요 (가장 느린 요청 시간만큼)
```

### 블로킹 상황 예시

```python
# ❌ 블로킹이 발생하는 작업들
import time
import requests

# 1. 네트워크 I/O
response = requests.get("https://api.example.com")  # 블로킹!

# 2. 파일 I/O
with open("large_file.txt") as f:
    data = f.read()  # 블로킹!

# 3. 데이터베이스 쿼리
cursor.execute("SELECT * FROM users WHERE age > 20")  # 블로킹!

# 4. time.sleep()
time.sleep(5)  # 블로킹!


# ✅ 논블로킹 대안 (asyncio)
import aiohttp
import aiofiles
import asyncpg

# 1. 비동기 HTTP
async with aiohttp.ClientSession() as session:
    response = await session.get("https://api.example.com")

# 2. 비동기 파일 I/O
async with aiofiles.open("large_file.txt") as f:
    data = await f.read()

# 3. 비동기 데이터베이스
conn = await asyncpg.connect("postgresql://...")
rows = await conn.fetch("SELECT * FROM users WHERE age > 20")

# 4. 비동기 sleep
await asyncio.sleep(5)
```

## 4. 동시성 vs 병렬성

### 개념 차이

```python
# ========== 동시성 (Concurrency) - asyncio ==========
# "여러 일을 번갈아가며 처리 (단일 스레드)"
# 식당에서 웨이터 1명이 여러 테이블 서빙

import asyncio

async def serve_table(table_num):
    print(f"테이블 {table_num} 주문 받기")
    await asyncio.sleep(1)  # 주문 받는 중

    print(f"테이블 {table_num} 음식 서빙")
    await asyncio.sleep(1)  # 서빙 중

    print(f"테이블 {table_num} 완료")

async def main():
    # 웨이터 1명이 3개 테이블 동시에 처리
    await asyncio.gather(
        serve_table(1),
        serve_table(2),
        serve_table(3)
    )

# 실행 순서 (빠르게 전환):
# 테이블1 주문 → 테이블2 주문 → 테이블3 주문
# 테이블1 서빙 → 테이블2 서빙 → 테이블3 서빙


# ========== 병렬성 (Parallelism) - multiprocessing ==========
# "여러 일을 실제로 동시에 처리 (여러 CPU)"
# 식당에서 웨이터 3명이 각자 테이블 서빙

from multiprocessing import Pool

def serve_table(table_num):
    print(f"웨이터{table_num}: 테이블 {table_num} 서빙")
    # CPU 집약적 작업 (복잡한 계산 등)
    result = sum(i * i for i in range(10**7))
    return result

# 웨이터 3명이 각자 동시에 처리
with Pool(3) as pool:
    results = pool.map(serve_table, [1, 2, 3])
```

### 비교표

| 특징 | 동시성 (asyncio) | 병렬성 (multiprocessing) |
|------|-----------------|------------------------|
| **실행 방식** | 단일 스레드, 번갈아 실행 | 여러 CPU 코어, 동시 실행 |
| **적합한 작업** | I/O 대기 (네트워크, DB, 파일) | CPU 집약적 (계산, 인코딩) |
| **자원 사용** | 가벼움 (메모리 적게 사용) | 무거움 (프로세스마다 메모리) |
| **전환 방식** | `await`로 자발적 양보 | OS 스케줄링 |
| **GIL 영향** | 영향 없음 (단일 스레드) | 우회 (각 프로세스마다 GIL) |
| **예시** | 웹 스크래핑, API 호출 | 동영상 인코딩, 머신러닝 |

### 실전 예시

```python
# ========== I/O 집약적 → asyncio 사용 ==========
import asyncio
import aiohttp

async def download_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # 네트워크 대기 시간이 대부분
            return await response.read()

async def main():
    urls = [f"https://example.com/image{i}.jpg" for i in range(100)]

    # 100개 이미지 동시 다운로드 (빠름!)
    images = await asyncio.gather(*[download_image(url) for url in urls])

asyncio.run(main())


# ========== CPU 집약적 → multiprocessing 사용 ==========
from multiprocessing import Pool
import numpy as np

def process_image(image_data):
    # CPU 집약적: 이미지 필터링, 리사이징 등
    image = np.array(image_data)
    # 복잡한 계산...
    return processed_image

# 4개 CPU 코어로 병렬 처리
with Pool(4) as pool:
    results = pool.map(process_image, images)
```

## 5. async/await 문법

### 기본 문법

```python
import asyncio

# ========== async def: 비동기 함수 정의 ==========
async def greet(name):
    print(f"안녕하세요, {name}님!")
    await asyncio.sleep(1)  # 1초 대기
    print(f"{name}님, 다시 만나요!")
    return f"{name} 인사 완료"


# ========== await: 비동기 함수 실행 ==========
async def main():
    # ❌ 잘못된 사용
    result = greet("홍길동")  # 코루틴 객체만 생성됨 (실행 안됨!)
    print(type(result))  # <class 'coroutine'>

    # ✅ 올바른 사용
    result = await greet("홍길동")  # 실제로 실행!
    print(result)  # "홍길동 인사 완료"

# asyncio.run(): 이벤트 루프 시작
asyncio.run(main())
```

### 규칙

```python
# 규칙 1: async 함수 안에서만 await 사용 가능
async def correct():
    await asyncio.sleep(1)  # ✅ OK

def wrong():
    await asyncio.sleep(1)  # ❌ SyntaxError!


# 규칙 2: await는 awaitable 객체에만 사용
async def example():
    await asyncio.sleep(1)  # ✅ OK (코루틴)
    await some_async_function()  # ✅ OK

    await 123  # ❌ TypeError! (int는 awaitable 아님)
    await normal_function()  # ❌ TypeError!


# 규칙 3: async 함수는 반드시 await 또는 asyncio.run으로 실행
async def task():
    return "완료"

# ❌ 실행 안됨
result = task()  # 코루틴 객체만 생성

# ✅ 방법 1: 다른 async 함수 안에서 await
async def main():
    result = await task()

# ✅ 방법 2: asyncio.run
result = asyncio.run(task())
```

### 실전 예시

```python
import asyncio
import aiohttp

async def fetch_weather(city):
    """날씨 정보 가져오기"""
    async with aiohttp.ClientSession() as session:
        url = f"https://api.weather.com/{city}"
        async with session.get(url) as response:
            return await response.json()

async def fetch_news(category):
    """뉴스 가져오기"""
    async with aiohttp.ClientSession() as session:
        url = f"https://api.news.com/{category}"
        async with session.get(url) as response:
            return await response.json()

async def main():
    # 순차 실행 (느림)
    weather = await fetch_weather("Seoul")  # 1초
    news = await fetch_news("tech")         # 1초
    # 총 2초

    # 동시 실행 (빠름)
    weather, news = await asyncio.gather(
        fetch_weather("Seoul"),
        fetch_news("tech")
    )
    # 총 1초 (동시에 요청)

    return weather, news

asyncio.run(main())
```

## 6. 코루틴(Coroutine)

### 일반 함수 vs 코루틴

```python
# ========== 일반 함수 ==========
def normal_function():
    print("시작")
    # 중간에 멈출 수 없음
    print("끝")
    return "결과"

result = normal_function()
# 시작
# 끝
print(result)  # "결과"


# ========== 코루틴 ==========
async def coroutine():
    print("시작")
    await asyncio.sleep(1)  # 여기서 멈췄다가 재개 가능!
    print("끝")
    return "결과"

# ❌ 직접 호출 불가
coro = coroutine()  # 코루틴 객체만 생성
print(type(coro))  # <class 'coroutine'>

# ✅ await 또는 asyncio.run 필요
result = asyncio.run(coroutine())
# 시작
# (1초 대기)
# 끝
print(result)  # "결과"
```

### 코루틴의 상태

```python
import asyncio

async def my_coroutine():
    print("1단계")
    await asyncio.sleep(1)
    print("2단계")
    await asyncio.sleep(1)
    print("3단계")
    return "완료"

# 코루틴 생성 → CREATED 상태
coro = my_coroutine()
print(f"상태: {coro}")  # <coroutine object>

# asyncio.run() → RUNNING → FINISHED
result = asyncio.run(coro)
```

### 코루틴 체이닝

```python
import asyncio

async def step1():
    print("1단계 시작")
    await asyncio.sleep(1)
    print("1단계 완료")
    return "1단계 결과"

async def step2(data):
    print(f"2단계 시작 (입력: {data})")
    await asyncio.sleep(1)
    print("2단계 완료")
    return "2단계 결과"

async def step3(data):
    print(f"3단계 시작 (입력: {data})")
    await asyncio.sleep(1)
    print("3단계 완료")
    return "최종 결과"

async def pipeline():
    # 순차적으로 실행 (각 단계의 결과를 다음 단계에 전달)
    result1 = await step1()
    result2 = await step2(result1)
    result3 = await step3(result2)
    return result3

final = asyncio.run(pipeline())
print(final)
```

## 7. 이벤트 루프(Event Loop)

### 개념

```python
# 이벤트 루프 = asyncio의 심장

# ┌─────────────────────────────────────┐
# │         Event Loop                  │
# │                                     │
# │  while True:                        │
# │      1. 실행 가능한 태스크 찾기      │
# │      2. 태스크 실행                  │
# │      3. await 만나면 다른 태스크로   │
# │      4. I/O 완료 확인 후 재개        │
# │      5. 모든 태스크 완료까지 반복    │
# └─────────────────────────────────────┘

import asyncio

async def task1():
    print("Task 1 시작")
    await asyncio.sleep(1)
    print("Task 1 완료")

async def task2():
    print("Task 2 시작")
    await asyncio.sleep(0.5)
    print("Task 2 완료")

# asyncio.run()이 이벤트 루프를 생성하고 실행
asyncio.run(asyncio.gather(task1(), task2()))

# 실행 순서:
# Task 1 시작
# Task 2 시작
# (0.5초 후) Task 2 완료
# (1초 후) Task 1 완료
```

### 이벤트 루프 직접 제어 (고급)

```python
import asyncio

async def my_task():
    print("작업 시작")
    await asyncio.sleep(1)
    print("작업 완료")
    return "결과"

# ========== 방법 1: asyncio.run() (권장, Python 3.7+) ==========
result = asyncio.run(my_task())


# ========== 방법 2: 이벤트 루프 직접 제어 (고급) ==========
# 이벤트 루프 생성
loop = asyncio.get_event_loop()

# 태스크 실행
result = loop.run_until_complete(my_task())

# 루프 종료
loop.close()


# ========== 방법 3: 여러 태스크 실행 ==========
async def main():
    tasks = [my_task() for _ in range(3)]
    results = await asyncio.gather(*tasks)
    return results

loop = asyncio.get_event_loop()
results = loop.run_until_complete(main())
loop.close()
```

### 이벤트 루프 동작 원리

```python
import asyncio

async def download(name, delay):
    print(f"{name} 다운로드 시작")
    await asyncio.sleep(delay)
    print(f"{name} 다운로드 완료")
    return f"{name} 데이터"

async def main():
    tasks = [
        download("파일A", 2),
        download("파일B", 1),
        download("파일C", 3)
    ]
    results = await asyncio.gather(*tasks)
    return results

# 이벤트 루프 동작 시뮬레이션:
#
# 시간(초) | 이벤트 루프 상태
# ---------|------------------
# 0.0      | 파일A 시작 → sleep(2) → 다른 태스크로
# 0.0      | 파일B 시작 → sleep(1) → 다른 태스크로
# 0.0      | 파일C 시작 → sleep(3) → 대기
# 1.0      | 파일B 완료! (sleep 1초 끝)
# 2.0      | 파일A 완료! (sleep 2초 끝)
# 3.0      | 파일C 완료! (sleep 3초 끝)
# 3.0      | 모든 태스크 완료 → 종료

asyncio.run(main())
```

## 8. asyncio 핵심 API

### asyncio.gather()

```python
import asyncio

async def task(name, delay):
    print(f"{name} 시작")
    await asyncio.sleep(delay)
    print(f"{name} 완료")
    return f"{name} 결과"

async def main():
    # 여러 태스크 동시 실행
    results = await asyncio.gather(
        task("작업1", 2),
        task("작업2", 1),
        task("작업3", 3)
    )

    print(results)
    # ['작업1 결과', '작업2 결과', '작업3 결과']

asyncio.run(main())

# 출력:
# 작업1 시작
# 작업2 시작
# 작업3 시작
# 작업2 완료 (1초 후)
# 작업1 완료 (2초 후)
# 작업3 완료 (3초 후)
# ['작업1 결과', '작업2 결과', '작업3 결과']
```

### asyncio.create_task()

```python
import asyncio

async def background_task(name):
    print(f"{name} 백그라운드 작업 시작")
    await asyncio.sleep(2)
    print(f"{name} 백그라운드 작업 완료")
    return f"{name} 결과"

async def main():
    # Task 생성 (즉시 실행 시작!)
    task1 = asyncio.create_task(background_task("Task1"))
    task2 = asyncio.create_task(background_task("Task2"))

    # 다른 작업 수행 가능
    print("메인 작업 수행 중...")
    await asyncio.sleep(1)
    print("메인 작업 완료")

    # Task 완료 대기
    result1 = await task1
    result2 = await task2

    print(result1, result2)

asyncio.run(main())

# 출력:
# Task1 백그라운드 작업 시작
# Task2 백그라운드 작업 시작
# 메인 작업 수행 중...
# 메인 작업 완료
# Task1 백그라운드 작업 완료
# Task2 백그라운드 작업 완료
# Task1 결과 Task2 결과
```

### asyncio.wait_for() (타임아웃)

```python
import asyncio

async def slow_task():
    print("느린 작업 시작")
    await asyncio.sleep(5)  # 5초 걸림
    print("느린 작업 완료")
    return "결과"

async def main():
    try:
        # 최대 2초만 기다림
        result = await asyncio.wait_for(slow_task(), timeout=2.0)
        print(result)
    except asyncio.TimeoutError:
        print("타임아웃! 2초 안에 완료되지 않음")

asyncio.run(main())

# 출력:
# 느린 작업 시작
# (2초 후) 타임아웃! 2초 안에 완료되지 않음
```

### asyncio.sleep()

```python
import asyncio
import time

# ❌ time.sleep() - 블로킹 (사용 금지!)
def bad_example():
    print("시작")
    time.sleep(1)  # 블로킹! 다른 작업 불가
    print("완료")

# ✅ asyncio.sleep() - 논블로킹
async def good_example():
    print("시작")
    await asyncio.sleep(1)  # 다른 작업 가능!
    print("완료")
```

## 9. 실전 활용: 웹 스크래핑

### 동기 방식 (느림)

```python
import requests
import time

def scrape_sync(urls):
    """동기 방식 웹 스크래핑"""
    results = []

    for url in urls:
        response = requests.get(url)
        results.append({
            "url": url,
            "status": response.status_code,
            "length": len(response.text)
        })

    return results

# 테스트
urls = [
    "https://example.com",
    "https://google.com",
    "https://github.com",
    "https://stackoverflow.com",
    "https://reddit.com"
]

start = time.time()
results = scrape_sync(urls)
print(f"동기 방식 소요 시간: {time.time() - start:.2f}초")
# 약 5초 (각 사이트당 1초씩)
```

### 비동기 방식 (빠름)

```python
import aiohttp
import asyncio
import time

async def fetch(session, url):
    """단일 URL 가져오기"""
    async with session.get(url) as response:
        return {
            "url": url,
            "status": response.status,
            "length": len(await response.text())
        }

async def scrape_async(urls):
    """비동기 방식 웹 스크래핑"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# 테스트
start = time.time()
results = asyncio.run(scrape_async(urls))
print(f"비동기 방식 소요 시간: {time.time() - start:.2f}초")
# 약 1초 (모든 사이트 동시 요청)
```

### 실전 예제: 뉴스 크롤러

```python
import aiohttp
import asyncio
from bs4 import BeautifulSoup

async def fetch_article(session, url):
    """기사 하나 가져오기"""
    async with session.get(url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'html.parser')

        return {
            "url": url,
            "title": soup.find('h1').text if soup.find('h1') else "제목 없음",
            "content": soup.find('article').text[:200] if soup.find('article') else ""
        }

async def crawl_news(article_urls):
    """여러 기사 동시 크롤링"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_article(session, url) for url in article_urls]
        articles = await asyncio.gather(*tasks, return_exceptions=True)

        # 에러 필터링
        valid_articles = [a for a in articles if not isinstance(a, Exception)]
        return valid_articles

# 사용
article_urls = [
    "https://news.example.com/article1",
    "https://news.example.com/article2",
    "https://news.example.com/article3",
    # ... 100개 기사
]

articles = asyncio.run(crawl_news(article_urls))
print(f"크롤링 완료: {len(articles)}개 기사")
```

## 10. 실전 활용: 데이터베이스

### 동기 방식 (psycopg2)

```python
import psycopg2

def fetch_users_sync():
    """동기 방식 데이터베이스 쿼리"""
    conn = psycopg2.connect("postgresql://localhost/mydb")
    cursor = conn.cursor()

    # 각 쿼리마다 블로킹
    cursor.execute("SELECT * FROM users WHERE age > 20")
    users = cursor.fetchall()

    cursor.execute("SELECT * FROM orders WHERE user_id = 1")
    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return users, orders
```

### 비동기 방식 (asyncpg)

```python
import asyncpg
import asyncio

async def fetch_users_async():
    """비동기 방식 데이터베이스 쿼리"""
    conn = await asyncpg.connect("postgresql://localhost/mydb")

    # 두 쿼리 동시 실행!
    users, orders = await asyncio.gather(
        conn.fetch("SELECT * FROM users WHERE age > 20"),
        conn.fetch("SELECT * FROM orders WHERE user_id = 1")
    )

    await conn.close()

    return users, orders

# 사용
users, orders = asyncio.run(fetch_users_async())
```

### 실전 예제: API + DB 통합

```python
import asyncio
import aiohttp
import asyncpg

async def get_user_profile(user_id):
    """사용자 프로필 (DB + 외부 API 통합)"""

    # DB 연결
    conn = await asyncpg.connect("postgresql://localhost/mydb")

    # 1. DB에서 사용자 기본 정보
    # 2. 외부 API에서 사용자 활동 정보
    # → 동시 실행!

    user_info, activity_info = await asyncio.gather(
        conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id),
        fetch_user_activity(user_id)  # 외부 API
    )

    await conn.close()

    return {
        "user": dict(user_info),
        "activity": activity_info
    }

async def fetch_user_activity(user_id):
    """외부 API에서 활동 정보"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/activity/{user_id}") as resp:
            return await resp.json()

# 사용
profile = asyncio.run(get_user_profile(123))
```

## 11. 실전 활용: FastAPI

```python
from fastapi import FastAPI
import asyncio
import aiohttp

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """비동기 API 엔드포인트"""

    # DB, 외부 API 동시 호출
    user_data, user_posts = await asyncio.gather(
        fetch_user_from_db(user_id),
        fetch_user_posts(user_id)
    )

    return {
        "user": user_data,
        "posts": user_posts
    }

async def fetch_user_from_db(user_id):
    """DB에서 사용자 정보"""
    # asyncpg 등 사용
    await asyncio.sleep(0.1)  # DB 쿼리 시뮬레이션
    return {"id": user_id, "name": "홍길동"}

async def fetch_user_posts(user_id):
    """외부 API에서 게시물"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.blog.com/posts?user={user_id}") as resp:
            return await resp.json()

# uvicorn main:app --reload
```

## 12. 예외 처리

### 단일 태스크 예외

```python
import asyncio

async def risky_task():
    await asyncio.sleep(1)
    raise ValueError("에러 발생!")

async def main():
    try:
        result = await risky_task()
    except ValueError as e:
        print(f"예외 포착: {e}")

asyncio.run(main())
```

### gather()에서 예외 처리

```python
import asyncio

async def task1():
    await asyncio.sleep(1)
    return "성공"

async def task2():
    await asyncio.sleep(0.5)
    raise ValueError("Task2 실패!")

async def task3():
    await asyncio.sleep(1.5)
    return "성공"

async def main():
    # return_exceptions=True: 예외를 결과로 반환
    results = await asyncio.gather(
        task1(),
        task2(),
        task3(),
        return_exceptions=True  # 중요!
    )

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Task{i+1} 실패: {result}")
        else:
            print(f"Task{i+1} 성공: {result}")

asyncio.run(main())

# 출력:
# Task1 성공: 성공
# Task2 실패: Task2 실패!
# Task3 성공: 성공
```

### 타임아웃 예외

```python
import asyncio

async def slow_task():
    await asyncio.sleep(5)
    return "완료"

async def main():
    try:
        result = await asyncio.wait_for(slow_task(), timeout=2.0)
    except asyncio.TimeoutError:
        print("타임아웃! 작업 취소됨")
    except Exception as e:
        print(f"기타 에러: {e}")

asyncio.run(main())
```

## 13. 동기 코드를 비동기로 실행

### run_in_executor() (블로킹 함수 처리)

```python
import asyncio
import time
import requests  # 동기 라이브러리

def blocking_function(url):
    """동기 함수 (블로킹)"""
    response = requests.get(url)
    return response.text

async def main():
    loop = asyncio.get_event_loop()

    # 동기 함수를 별도 스레드에서 실행
    result = await loop.run_in_executor(
        None,  # 기본 executor 사용
        blocking_function,
        "https://example.com"
    )

    print(f"결과 길이: {len(result)}")

asyncio.run(main())
```

### CPU 집약적 작업 처리

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

def cpu_intensive_task(n):
    """CPU 집약적 작업"""
    return sum(i * i for i in range(n))

async def main():
    loop = asyncio.get_event_loop()

    # ProcessPoolExecutor로 CPU 집약적 작업 처리
    with ProcessPoolExecutor() as executor:
        results = await asyncio.gather(*[
            loop.run_in_executor(executor, cpu_intensive_task, 10**7)
            for _ in range(4)
        ])

    print(f"결과: {results}")

asyncio.run(main())
```

## 14. Java와의 비교

### CompletableFuture vs asyncio

```python
# ========== Python asyncio ==========
import asyncio

async def fetch_data(id):
    await asyncio.sleep(1)
    return f"데이터 {id}"

async def main():
    results = await asyncio.gather(
        fetch_data(1),
        fetch_data(2),
        fetch_data(3)
    )
    print(results)

asyncio.run(main())


# ========== Java CompletableFuture ==========
// import java.util.concurrent.CompletableFuture;

CompletableFuture<String> future1 = CompletableFuture.supplyAsync(() -> {
    Thread.sleep(1000);
    return "데이터 1";
});

CompletableFuture<String> future2 = CompletableFuture.supplyAsync(() -> {
    Thread.sleep(1000);
    return "데이터 2";
});

CompletableFuture<String> future3 = CompletableFuture.supplyAsync(() -> {
    Thread.sleep(1000);
    return "데이터 3";
});

CompletableFuture.allOf(future1, future2, future3).join();
```

### Reactor (Spring WebFlux) vs asyncio

```python
# ========== Python asyncio + FastAPI ==========
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/users/{id}")
async def get_user(id: int):
    user = await fetch_user_from_db(id)
    posts = await fetch_user_posts(id)
    return {"user": user, "posts": posts}


# ========== Java Spring WebFlux ==========
// @RestController
// public class UserController {
//
//     @GetMapping("/users/{id}")
//     public Mono<UserResponse> getUser(@PathVariable int id) {
//         Mono<User> user = userRepository.findById(id);
//         Mono<List<Post>> posts = postRepository.findByUserId(id);
//
//         return Mono.zip(user, posts)
//             .map(tuple -> new UserResponse(tuple.getT1(), tuple.getT2()));
//     }
// }
```

### Virtual Threads (Java 21+) vs asyncio

```python
# ========== Python asyncio ==========
import asyncio

async def task(name):
    print(f"{name} 시작")
    await asyncio.sleep(1)
    print(f"{name} 완료")

async def main():
    await asyncio.gather(*[task(f"Task{i}") for i in range(1000)])

asyncio.run(main())


# ========== Java Virtual Threads (Java 21+) ==========
// try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
//     for (int i = 0; i < 1000; i++) {
//         int taskId = i;
//         executor.submit(() -> {
//             System.out.println("Task" + taskId + " 시작");
//             Thread.sleep(1000);
//             System.out.println("Task" + taskId + " 완료");
//         });
//     }
// }
```

### 비교표

| 특징 | Python asyncio | Java CompletableFuture | Java Virtual Threads |
|------|---------------|----------------------|---------------------|
| **도입 버전** | Python 3.4+ | Java 8+ | Java 21+ |
| **문법** | async/await | .thenApply(), .thenCompose() | 기존 Thread API |
| **스레드** | 단일 스레드 | 스레드 풀 | 가상 스레드 (경량) |
| **적합 작업** | I/O 집약적 | I/O 집약적 | I/O 집약적 |
| **학습 곡선** | 중간 | 높음 | 낮음 (기존 Thread와 유사) |

## 실무 팁

### 1. 언제 asyncio를 사용할까?

```python
# ✅ asyncio 사용하세요
# - API 호출 (여러 API 동시 호출)
# - 웹 스크래핑 (여러 페이지 동시 크롤링)
# - 데이터베이스 쿼리 (여러 쿼리 동시 실행)
# - 파일 I/O (대용량 파일 읽기/쓰기)
# - 웹소켓 (실시간 통신)

# ❌ asyncio 사용하지 마세요
# - CPU 집약적 작업 (수학 계산, 이미지 처리)
#   → multiprocessing 사용
# - 간단한 스크립트 (오버헤드만 증가)
#   → 일반 동기 코드 사용
```

### 2. 성능 비교

```python
import asyncio
import aiohttp
import requests
import time

# ========== 동기 방식 ==========
def benchmark_sync(urls):
    start = time.time()
    for url in urls:
        requests.get(url)
    return time.time() - start

# ========== 비동기 방식 ==========
async def benchmark_async(urls):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        await asyncio.gather(*tasks)
    return time.time() - start

urls = ["https://httpbin.org/delay/1"] * 10

sync_time = benchmark_sync(urls)
async_time = asyncio.run(benchmark_async(urls))

print(f"동기: {sync_time:.2f}초")    # 약 10초
print(f"비동기: {async_time:.2f}초")  # 약 1초
print(f"성능 향상: {sync_time / async_time:.1f}배")
```

### 3. 일반적인 실수

```python
# ❌ 실수 1: await 없이 코루틴 호출
async def wrong():
    result = async_function()  # 실행 안됨!
    print(result)  # <coroutine object>

# ✅ 올바른 방법
async def correct():
    result = await async_function()
    print(result)


# ❌ 실수 2: 동기 함수에서 await 사용
def wrong():
    await asyncio.sleep(1)  # SyntaxError!

# ✅ 올바른 방법
async def correct():
    await asyncio.sleep(1)


# ❌ 실수 3: time.sleep() 사용
async def wrong():
    time.sleep(1)  # 블로킹! 다른 작업 못함

# ✅ 올바른 방법
async def correct():
    await asyncio.sleep(1)  # 논블로킹


# ❌ 실수 4: 동기 라이브러리 사용
async def wrong():
    response = requests.get("https://api.example.com")  # 블로킹!

# ✅ 올바른 방법
async def correct():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com") as response:
            return await response.json()
```

### 4. 학습 순서

1. ✅ **기초 (1주)**
   - 동기 vs 비동기 개념
   - async/await 문법
   - asyncio.sleep() 실험
   - asyncio.gather() 사용

2. ✅ **실전 (2주)**
   - aiohttp로 웹 스크래핑
   - asyncpg로 데이터베이스 쿼리
   - FastAPI로 비동기 API 서버

3. ✅ **고급 (선택)**
   - 이벤트 루프 직접 제어
   - asyncio.create_task()
   - 예외 처리와 타임아웃
   - 성능 최적화

---

## 참고 자료

- [Python asyncio 공식 문서](https://docs.python.org/3/library/asyncio.html)
- [aiohttp 공식 문서](https://docs.aiohttp.org/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Real Python - Async IO in Python](https://realpython.com/async-io-python/)
