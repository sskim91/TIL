# httpx: 왜 requests 대신 쓰는가

Python HTTP 클라이언트의 현대적인 선택

## 결론부터 말하면

**httpx는 requests의 현대적인 대안이다.** requests와 거의 동일한 API를 제공하면서, async/await와 HTTP/2를 지원한다.

| 특징 | requests | httpx |
|------|----------|-------|
| **동기 지원** | ✅ | ✅ |
| **비동기 지원** | ❌ | ✅ `AsyncClient` |
| **HTTP/2** | ❌ | ✅ |
| **타입 힌트** | 부분적 | ✅ 완전 지원 |
| **API 호환성** | - | requests와 거의 동일 |

```python
# requests 스타일 (동기)
import httpx

response = httpx.get("https://api.example.com/users")
print(response.json())

# 비동기 스타일 (async/await)
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/users")
    print(response.json())
```

**Java로 비유하면:**

| Python | Java |
|--------|------|
| `requests` | Apache HttpClient (레거시) |
| `httpx` | Java 11+ HttpClient (현대적) |
| `httpx.AsyncClient` | `HttpClient.sendAsync()` |

## 1. 왜 httpx인가?

### 만약 requests로 비동기 호출을 해야 한다면?

```python
# ❌ requests는 비동기를 지원하지 않는다
import requests
import asyncio

async def fetch_users():
    # 이건 동기 호출이라 이벤트 루프를 블로킹한다!
    response = requests.get("https://api.example.com/users")
    return response.json()

# 해결책? aiohttp를 배워야 한다 (API가 완전히 다름)
import aiohttp

async def fetch_users():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/users") as response:
            return await response.json()
```

**문제점:**
- requests는 비동기를 지원하지 않음
- aiohttp는 API가 완전히 다름 (학습 비용)
- 동기/비동기 코드를 따로 작성해야 함

### httpx를 쓰면?

```python
import httpx

# ✅ 동기 호출 (requests와 동일한 API)
response = httpx.get("https://api.example.com/users")

# ✅ 비동기 호출 (같은 API, await만 추가)
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/users")
```

**하나의 라이브러리로 동기/비동기 모두 커버.**

## 2. 기본 사용법

### 간단한 요청 (requests 스타일)

```python
import httpx

# GET 요청
response = httpx.get("https://api.example.com/users")
print(response.status_code)  # 200
print(response.json())       # {'users': [...]}

# POST 요청 (JSON)
response = httpx.post(
    "https://api.example.com/users",
    json={"name": "홍길동", "email": "hong@example.com"}
)

# POST 요청 (Form 데이터)
response = httpx.post(
    "https://api.example.com/login",
    data={"username": "hong", "password": "secret"}
)

# 헤더 추가
response = httpx.get(
    "https://api.example.com/users",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Client 사용 (권장)

여러 요청을 보낼 때는 `Client`를 사용하는 것이 효율적이다. **커넥션 풀링**을 통해 성능이 향상된다.

```python
import httpx

# ✅ 권장: Client 사용 (커넥션 재사용)
with httpx.Client() as client:
    response1 = client.get("https://api.example.com/users")
    response2 = client.get("https://api.example.com/posts")
    response3 = client.post("https://api.example.com/users", json={...})

# ❌ 비권장: 매번 새 연결 (비효율적)
response1 = httpx.get("https://api.example.com/users")
response2 = httpx.get("https://api.example.com/posts")
```

**Java 비유:**
```java
// httpx.Client() ≈ HttpClient.newHttpClient()
HttpClient client = HttpClient.newHttpClient();
// 같은 클라이언트로 여러 요청 (커넥션 풀링)
```

### base_url 설정

API 서버 주소를 매번 쓰기 귀찮을 때:

```python
with httpx.Client(base_url="https://api.example.com") as client:
    # base_url이 자동으로 붙음
    users = client.get("/users")      # https://api.example.com/users
    posts = client.get("/posts")      # https://api.example.com/posts
    user = client.post("/users", json={...})
```

## 3. 비동기 사용법 (AsyncClient)

### 기본 패턴

```python
import httpx
import asyncio

async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/users")
        return response.json()

# 실행
result = asyncio.run(fetch_data())
```

### 병렬 요청 (핵심 장점)

비동기의 진짜 장점은 **여러 요청을 동시에** 보낼 수 있다는 것이다.

```python
import httpx
import asyncio

async def fetch_all():
    async with httpx.AsyncClient() as client:
        # 3개의 요청을 동시에 실행
        results = await asyncio.gather(
            client.get("https://api.example.com/users"),
            client.get("https://api.example.com/posts"),
            client.get("https://api.example.com/comments"),
        )
        return [r.json() for r in results]

# 동기로 하면 3초, 비동기로 하면 ~1초 (병렬 실행)
```

**동기 vs 비동기 시간 비교:**

```
동기 (requests):     [요청1: 1초] → [요청2: 1초] → [요청3: 1초] = 3초
비동기 (httpx):      [요청1: 1초]
                     [요청2: 1초]  = ~1초 (병렬)
                     [요청3: 1초]
```

### FastAPI와 함께 사용

FastAPI 같은 비동기 웹 프레임워크에서 외부 API를 호출할 때 필수:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 앱 시작 시 클라이언트 생성
    app.state.http_client = httpx.AsyncClient(
        base_url="https://api.external.com",
        timeout=30.0,
    )
    yield
    # 앱 종료 시 클라이언트 정리
    await app.state.http_client.aclose()

app = FastAPI(lifespan=lifespan)

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # 비동기로 외부 API 호출
    response = await app.state.http_client.get(f"/users/{user_id}")
    return response.json()
```

> **참고:** `@app.on_event("startup")`은 FastAPI 0.109.0부터 deprecated되었다. `lifespan` 컨텍스트 매니저를 사용하자.

## 4. 타임아웃 설정

```python
import httpx

# 전체 타임아웃 (초)
response = httpx.get("https://api.example.com", timeout=10.0)

# 세분화된 타임아웃
timeout = httpx.Timeout(
    connect=5.0,    # 연결 타임아웃
    read=10.0,      # 읽기 타임아웃
    write=10.0,     # 쓰기 타임아웃
    pool=5.0,       # 커넥션 풀 대기 타임아웃
)

with httpx.Client(timeout=timeout) as client:
    response = client.get("https://api.example.com")
```

## 5. 에러 처리

```python
import httpx

try:
    response = httpx.get("https://api.example.com/users")
    response.raise_for_status()  # 4xx, 5xx 에러 시 예외 발생
except httpx.ConnectError:
    print("연결 실패")
except httpx.TimeoutException:
    print("타임아웃")
except httpx.HTTPStatusError as e:
    print(f"HTTP 에러: {e.response.status_code}")
```

## 6. HTTP/2 지원

```python
# HTTP/2 활성화
with httpx.Client(http2=True) as client:
    response = client.get("https://http2.example.com")
    print(response.http_version)  # "HTTP/2"
```

**HTTP/2 장점:**
- 멀티플렉싱 (하나의 연결로 여러 요청)
- 헤더 압축
- 서버 푸시

## 7. requests에서 마이그레이션

대부분의 코드는 `import requests`를 `import httpx`로 바꾸면 동작한다.

```python
# Before (requests)
import requests

response = requests.get("https://api.example.com/users")
response = requests.post("https://api.example.com/users", json={...})

# After (httpx) - 거의 동일!
import httpx

response = httpx.get("https://api.example.com/users")
response = httpx.post("https://api.example.com/users", json={...})
```

**주요 차이점:**

| requests | httpx | 비고 |
|----------|-------|------|
| `requests.Session()` | `httpx.Client()` | 이름만 다름 |
| 자동 리다이렉트 | `follow_redirects=True` 명시 | 기본값 차이 |
| `response.content` | `response.content` | 동일 |
| `response.json()` | `response.json()` | 동일 |

## 8. 언제 뭘 쓰나?

| 상황 | 선택 |
|------|------|
| 간단한 스크립트 | `requests` 또는 `httpx` |
| FastAPI/비동기 앱 | `httpx.AsyncClient` (필수) |
| 병렬 API 호출 | `httpx.AsyncClient` |
| HTTP/2 필요 | `httpx` |
| 새 프로젝트 | `httpx` (미래 대비) |
| 레거시 유지보수 | `requests` (굳이 바꿀 필요 없음) |

## 정리

| 기능 | 사용법 |
|------|--------|
| 동기 요청 | `httpx.get()`, `httpx.post()` |
| 동기 클라이언트 | `with httpx.Client() as client:` |
| 비동기 클라이언트 | `async with httpx.AsyncClient() as client:` |
| base_url | `Client(base_url="https://...")` |
| 타임아웃 | `Client(timeout=10.0)` |
| HTTP/2 | `Client(http2=True)` |
| 헤더 | `headers={"Authorization": "Bearer ..."}` |
| JSON 전송 | `json={"key": "value"}` |
| Form 전송 | `data={"key": "value"}` |

---

## 출처

- [httpx 공식 문서](https://www.python-httpx.org/)
- [httpx GitHub](https://github.com/encode/httpx)
- [httpx vs requests 비교](https://www.python-httpx.org/compatibility/)
