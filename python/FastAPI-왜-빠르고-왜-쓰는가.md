# FastAPI: 왜 빠르고 왜 쓰는가

Python으로 API 서버를 만들어야 한다. Flask? Django? 아니면 요즘 핫하다는 FastAPI? 선택지가 많아서 고민된다. FastAPI가 "Fast"한 이유는 뭘까? 그냥 이름만 그런 걸까?

## 결론부터 말하면

**FastAPI는 "개발 속도"와 "실행 속도" 두 마리 토끼를 잡은 프레임워크다.**

| 특성 | Flask | Django | FastAPI |
|------|-------|--------|---------|
| 개발 속도 | 빠름 | 보통 | **매우 빠름** |
| 실행 속도 | 보통 | 느림 | **매우 빠름** |
| 타입 힌트 | 선택 | 선택 | **필수/자동** |
| API 문서 | 수동 | 수동 | **자동 생성** |
| 비동기 지원 | 제한적 | 제한적 | **네이티브** |
| 학습 곡선 | 낮음 | 높음 | 낮음 |

```mermaid
flowchart LR
    subgraph FastAPI["FastAPI의 핵심"]
        Starlette["Starlette<br>(비동기 웹)"]
        Pydantic["Pydantic<br>(데이터 검증)"]
        TypeHints["Python Type Hints<br>(자동 문서화)"]
    end

    Starlette --> Performance["높은 성능"]
    Pydantic --> Validation["자동 검증"]
    TypeHints --> Docs["자동 API 문서"]

    style Starlette fill:#1565C0,color:#fff
    style Pydantic fill:#2E7D32,color:#fff
    style TypeHints fill:#E65100,color:#fff
```

---

## 1. 왜 "Fast"인가?

### 1.1 두 가지 의미의 Fast

FastAPI의 "Fast"는 두 가지 의미를 가진다:

1. **개발이 빠르다** (Developer Experience)
2. **실행이 빠르다** (Runtime Performance)

### 1.2 실행 속도: Starlette 덕분

FastAPI는 내부적으로 **Starlette** 위에서 동작한다. Starlette는 비동기 웹 프레임워크의 핵심이다.

```python
# Flask (WSGI, 동기)
@app.route("/users")
def get_users():
    users = db.query(User).all()  # 블로킹! 다른 요청은 대기
    return jsonify(users)

# FastAPI (ASGI, 비동기)
@app.get("/users")
async def get_users():
    users = await db.query(User).all()  # 논블로킹! 다른 요청 처리 가능
    return users
```

> **주의:** `await`만 붙인다고 마법처럼 비동기가 되는 건 아니다. 비동기 DB 드라이버(`asyncpg`, `databases`, `SQLAlchemy async` 등)를 사용해야 진짜 논블로킹 I/O가 가능하다.

**벤치마크 (초당 요청 수, 높을수록 좋음):**

| 프레임워크 | 요청/초 | 비고 |
|-----------|--------|------|
| FastAPI | ~15,000 | ASGI + uvicorn |
| Flask | ~2,000 | WSGI + gunicorn |
| Django | ~1,500 | WSGI + gunicorn |

> **왜 이렇게 차이가 날까?** WSGI는 동기 방식이라 I/O 대기 시간에 스레드가 놀고 있다. ASGI는 비동기라서 I/O 대기 중에도 다른 요청을 처리할 수 있다.

### 1.3 개발 속도: Pydantic + Type Hints

Flask로 요청 데이터를 검증하려면:

```python
# Flask - 수동 검증 (지옥의 시작)
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    # 일일이 검증해야 한다
    if not data.get("name"):
        return {"error": "name is required"}, 400
    if not isinstance(data.get("age"), int):
        return {"error": "age must be integer"}, 400
    if data.get("age") < 0:
        return {"error": "age must be positive"}, 400
    if not data.get("email"):
        return {"error": "email is required"}, 400
    if "@" not in data.get("email", ""):
        return {"error": "invalid email format"}, 400

    # 드디어 비즈니스 로직...
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return {"id": user.id}
```

FastAPI로 같은 작업을:

```python
# FastAPI - 자동 검증 (천국)
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    name: str
    age: int = Field(ge=0)  # >= 0
    email: EmailStr

@app.post("/users")
async def create_user(user: UserCreate):
    # 검증은 이미 완료됨! 바로 비즈니스 로직
    db_user = User(**user.model_dump())
    await db.add(db_user)
    return {"id": db_user.id}
```

**Pydantic이 자동으로 해주는 것:**
- 타입 변환 (`"123"` → `123`)
- 필수 필드 검증
- 값 범위 검증 (`ge=0`)
- 이메일 형식 검증 (`EmailStr`)
- 에러 메시지 자동 생성

---

## 2. 자동 API 문서화

### 2.1 Swagger UI와 ReDoc

FastAPI를 실행하면 **두 가지 API 문서가 자동 생성** 된다:

- `http://localhost:8000/docs` → Swagger UI
- `http://localhost:8000/redoc` → ReDoc

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="My API",
    description="사용자 관리 API",
    version="1.0.0"
)

class User(BaseModel):
    """사용자 정보"""
    name: str
    email: str

@app.post("/users", summary="사용자 생성", tags=["Users"])
async def create_user(user: User) -> dict:
    """
    새 사용자를 생성합니다.

    - **name**: 사용자 이름 (필수)
    - **email**: 이메일 주소 (필수)
    """
    return {"id": 1, "name": user.name}
```

이 코드만으로 완전한 API 문서가 생성된다. Swagger에서 직접 API를 테스트할 수도 있다.

### 2.2 Flask/Django와 비교

| 기능 | Flask | Django | FastAPI |
|------|-------|--------|---------|
| API 문서 생성 | flask-swagger 설치 + 설정 | drf-yasg 설치 + 설정 | **기본 내장** |
| 요청 예시 | 수동 작성 | 수동 작성 | **자동 생성** |
| 응답 스키마 | 수동 작성 | Serializer 정의 | **Type Hint에서 추론** |
| 대화형 테스트 | 별도 설정 | 별도 설정 | **기본 내장** |

---

## 3. 비동기 처리: async/await

### 3.1 왜 비동기가 중요한가?

API 서버의 대부분 시간은 **I/O 대기** 에 쓰인다:

```
[요청 처리 시간 분석]
├── DB 쿼리 대기: 50ms ████████████████████
├── 외부 API 호출 대기: 30ms ████████████
├── 파일 읽기 대기: 10ms ████
└── 실제 연산: 1ms ▌

→ 99%가 대기 시간!
```

동기 방식(Flask)에서는 대기 중에 스레드가 **아무것도 못 한다.** 비동기 방식(FastAPI)에서는 대기 중에 **다른 요청을 처리** 한다.

### 3.2 실전 예시: 여러 외부 API 호출

```python
import asyncio
import httpx

# 동기 방식 - 순차 실행 (느림)
def get_data_sync():
    result1 = requests.get("https://api1.com/data").json()  # 100ms
    result2 = requests.get("https://api2.com/data").json()  # 100ms
    result3 = requests.get("https://api3.com/data").json()  # 100ms
    return [result1, result2, result3]  # 총 300ms

# 비동기 방식 - 동시 실행 (빠름)
async def get_data_async():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get("https://api1.com/data"),  # 100ms
            client.get("https://api2.com/data"),  # 100ms (동시)
            client.get("https://api3.com/data"),  # 100ms (동시)
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]  # 총 ~100ms
```

### 3.3 동기 함수도 사용 가능

FastAPI는 `async def`와 일반 `def` 모두 지원한다:

```python
# 비동기 함수 - I/O 작업에 적합
@app.get("/async-endpoint")
async def async_handler():
    data = await async_db_query()
    return data

# 동기 함수 - CPU 작업에 적합 (자동으로 스레드풀에서 실행)
@app.get("/sync-endpoint")
def sync_handler():
    result = heavy_cpu_computation()
    return result
```

---

## 4. 의존성 주입 (Dependency Injection)

### 4.1 DI가 필요한 이유

인증, DB 세션, 설정 등 **여러 엔드포인트에서 공통으로 필요한 것들** 이 있다:

```python
# DI 없이 - 반복 코드 지옥
@app.get("/users")
async def get_users():
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(401)
    user = verify_token(token)  # 매번 반복
    db = get_db_session()        # 매번 반복
    ...

@app.get("/posts")
async def get_posts():
    token = request.headers.get("Authorization")  # 또 반복
    if not token:
        raise HTTPException(401)
    user = verify_token(token)   # 또 반복
    db = get_db_session()         # 또 반복
    ...
```

### 4.2 FastAPI의 Depends

```python
from fastapi import Depends, HTTPException

# 의존성 정의
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: str = Header(...),
    db: Session = Depends(get_db)
):
    user = await verify_token(token, db)
    if not user:
        raise HTTPException(401, "Invalid token")
    return user

# 사용 - 깔끔!
@app.get("/users")
async def get_users(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return await db.query(User).all()

@app.get("/posts")
async def get_posts(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return await db.query(Post).filter(Post.author == user).all()
```

### 4.3 Java 개발자를 위한 비교

```java
// Spring의 DI
@RestController
public class UserController {
    @Autowired
    private UserService userService;

    @GetMapping("/users")
    public List<User> getUsers(@AuthenticationPrincipal User user) {
        return userService.findAll();
    }
}
```

```python
# FastAPI의 DI

# 서비스 의존성 정의 (Spring의 @Bean과 유사)
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

@app.get("/users")
async def get_users(
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)  # 서비스 주입
):
    return await service.find_all()
```

**비슷한 개념:**
- Spring `@Autowired` ≈ FastAPI `Depends()`
- Spring `@AuthenticationPrincipal` ≈ FastAPI `Depends(get_current_user)`

---

## 5. 실전 프로젝트 구조

### 5.1 권장 구조

```
my_project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 생성
│   ├── config.py            # 설정
│   ├── dependencies.py      # 공통 의존성
│   │
│   ├── routers/             # 라우터 (컨트롤러)
│   │   ├── __init__.py
│   │   ├── users.py
│   │   └── posts.py
│   │
│   ├── schemas/             # Pydantic 모델 (DTO)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── post.py
│   │
│   ├── models/              # DB 모델 (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── post.py
│   │
│   └── services/            # 비즈니스 로직
│       ├── __init__.py
│       ├── user_service.py
│       └── post_service.py
│
├── tests/
├── requirements.txt
└── Dockerfile
```

### 5.2 라우터 분리

```python
# app/routers/users.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
async def list_users():
    ...

@router.get("/{user_id}")
async def get_user(user_id: int):
    ...

# app/main.py
from fastapi import FastAPI
from app.routers import users, posts

app = FastAPI()
app.include_router(users.router)
app.include_router(posts.router)
```

---

## 6. FastAPI vs Flask vs Django 선택 기준

```mermaid
flowchart TD
    Q1{"API 서버만<br>필요한가?"}
    Q2{"고성능이<br>필요한가?"}
    Q3{"풀스택 웹앱이<br>필요한가?"}
    Q4{"빠른 프로토타입이<br>필요한가?"}

    Flask["Flask<br>(간단, 유연)"]
    Django["Django<br>(풀스택, 배터리 포함)"]
    FastAPI["FastAPI<br>(고성능 API)"]

    Q1 -->|Yes| Q2
    Q1 -->|No| Q3
    Q2 -->|Yes| FastAPI
    Q2 -->|No| Q4
    Q4 -->|Yes| Flask
    Q4 -->|No| FastAPI
    Q3 -->|Yes| Django
    Q3 -->|No| Flask

    style FastAPI fill:#1565C0,color:#fff
    style Flask fill:#2E7D32,color:#fff
    style Django fill:#E65100,color:#fff
```

### 선택 가이드

| 상황 | 추천 | 이유 |
|------|------|------|
| REST API 서버 | **FastAPI** | 자동 문서화, 타입 안전성, 고성능 |
| ML 모델 서빙 | **FastAPI** | 비동기, Pydantic 검증, 확장성 |
| 간단한 웹훅/스크립트 | **Flask** | 최소 설정, 빠른 시작 |
| 관리자 페이지 필요 | **Django** | Admin 내장, ORM 완성도 |
| 풀스택 웹앱 | **Django** | 템플릿, 인증, 세션 내장 |
| 마이크로서비스 | **FastAPI** | 경량, 고성능, 컨테이너 친화적 |

---

## 7. 빠른 시작

### 7.1 설치 및 실행

```bash
# 설치
pip install fastapi uvicorn

# 최소 코드 (main.py)
cat << 'EOF' > main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}
EOF

# 실행 (개발용)
uvicorn main:app --reload

# 확인
# http://localhost:8000      → API
# http://localhost:8000/docs → Swagger UI
```

> **프로덕션 배포:** 개발 시에는 `--reload` 옵션이 편리하지만, 프로덕션에서는 Gunicorn과 Uvicorn 워커를 조합하여 멀티 프로세스로 실행한다:
> ```bash
> gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
> ```

### 7.2 CRUD 예시

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# 인메모리 DB (예시용)
users_db: dict[int, dict] = {}
counter = 0

class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

# Create
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    global counter
    counter += 1
    users_db[counter] = {"id": counter, **user.model_dump()}
    return users_db[counter]

# Read
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(404, "User not found")
    return users_db[user_id]

# Update
@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserCreate):
    if user_id not in users_db:
        raise HTTPException(404, "User not found")
    users_db[user_id] = {"id": user_id, **user.model_dump()}
    return users_db[user_id]

# Delete
@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(404, "User not found")
    del users_db[user_id]
    return {"message": "Deleted"}
```

---

## 8. 정리

**FastAPI를 선택해야 하는 이유:**

1. **타입 안전성**: Python Type Hints로 버그를 컴파일 타임에 잡는다
2. **자동 문서화**: Swagger/ReDoc이 기본 내장
3. **고성능**: Starlette + uvicorn으로 Node.js급 성능
4. **개발 생산성**: Pydantic으로 검증 코드 90% 감소
5. **비동기 네이티브**: async/await 완벽 지원
6. **의존성 주입**: Spring처럼 깔끔한 DI

**FastAPI가 적합하지 않은 경우:**

- 풀스택 웹앱 (Django 추천)
- 레거시 Python 2 환경 (Flask 추천)
- 극도로 단순한 스크립트 (Flask 추천)

---

## 출처

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/) - 공식 문서
- [Starlette 공식 문서](https://www.starlette.io/) - FastAPI의 기반 프레임워크
- [Pydantic 공식 문서](https://docs.pydantic.dev/) - 데이터 검증 라이브러리
- [TechEmpower Benchmarks](https://www.techempower.com/benchmarks/) - 웹 프레임워크 벤치마크
