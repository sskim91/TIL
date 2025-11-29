# Python에서 데이터베이스 연결하기

Spring Boot에서 HikariCP + JPA를 쓰듯, Python에서는 어떻게 할까?

## 결론부터 말하면

Python에는 **DB-API 2.0**이라는 표준 인터페이스(Java의 JDBC 역할)가 있고, **SQLAlchemy**가 Connection Pool과 ORM을 제공하는 가장 인기 있는 라이브러리입니다.

```python
# Java/Spring Boot 스타일
# application.yml + HikariCP + JPA

# Python 스타일 (가장 유사한 조합)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    "postgresql://user:password@localhost:5432/mydb",
    pool_size=10,           # HikariCP의 maximumPoolSize
    max_overflow=20,        # 추가 연결 수
    pool_pre_ping=True      # 연결 유효성 검사
)

SessionLocal = sessionmaker(bind=engine)
```

## 1. Python vs Java 데이터베이스 스택 비교

### 아키텍처 비교

```mermaid
flowchart TB
    subgraph Java/Spring
        J1[JDBC<br/>표준 인터페이스] --> J2[JDBC Driver<br/>MySQL/PostgreSQL Driver]
        J2 --> J3[Connection Pool<br/>HikariCP]
        J3 --> J4[ORM<br/>JPA/Hibernate]
    end

    subgraph Python
        P1[DB-API 2.0<br/>PEP 249 표준] --> P2[DB Driver<br/>psycopg2, pymysql]
        P2 --> P3[Connection Pool<br/>SQLAlchemy Engine]
        P3 --> P4[ORM<br/>SQLAlchemy ORM]
    end

    style J1 fill:#E3F2FD,color:#000
    style P1 fill:#FFF3E0,color:#000
```

### 대응 관계

| Java/Spring | Python | 역할 |
|------------|--------|------|
| JDBC | DB-API 2.0 (PEP 249) | 표준 인터페이스 |
| HikariCP | SQLAlchemy Engine | Connection Pool |
| JPA/Hibernate | SQLAlchemy ORM | ORM |
| application.yml | .env + pydantic-settings | 설정 관리 |
| MySQL Connector | PyMySQL, mysqlclient | MySQL 드라이버 |
| PostgreSQL Driver | psycopg2, asyncpg | PostgreSQL 드라이버 |

## 2. DB-API 2.0 (JDBC의 Python 버전)

### PEP 249 표준

Python에는 **PEP 249**로 정의된 **DB-API 2.0** 표준이 있습니다. 이것이 Java의 JDBC와 같은 역할입니다.

```python
# 모든 DB 드라이버가 동일한 인터페이스를 따름
import psycopg2  # PostgreSQL
# 또는
import pymysql   # MySQL
# 또는
import sqlite3   # SQLite

# 공통 패턴
# 1. 연결
conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="user",
    password="password"
)

# 2. 커서 생성
cursor = conn.cursor()

# 3. 쿼리 실행
cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
result = cursor.fetchone()

# 4. 커밋/롤백
conn.commit()
# conn.rollback()

# 5. 종료
cursor.close()
conn.close()
```

### Context Manager 사용 (권장)

```python
# ✅ 자동으로 연결 종료
with psycopg2.connect(...) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        for row in results:
            print(row)
# conn과 cursor 자동 close
```

## 3. SELECT 결과 받기 (중요!)

### Java와 비교

```java
// Java/Spring
@Repository
public class UserRepository {
    public List<User> findAll() {
        String sql = "SELECT id, username, email FROM users";
        return jdbcTemplate.query(sql, new RowMapper<User>() {
            @Override
            public User mapRow(ResultSet rs, int rowNum) {
                User user = new User();
                user.setId(rs.getInt("id"));
                user.setUsername(rs.getString("username"));
                user.setEmail(rs.getString("email"));
                return user;
            }
        });
    }
}
```

### Python - 방법 1: 튜플로 받기 (기본)

```python
import psycopg2

conn = psycopg2.connect(...)
cursor = conn.cursor()

# 단일 행 조회
cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (1,))
row = cursor.fetchone()
print(row)  # (1, 'hong', 'hong@example.com')

# 인덱스로 접근
user_id = row[0]      # 1
username = row[1]     # 'hong'
email = row[2]        # 'hong@example.com'

# 여러 행 조회
cursor.execute("SELECT id, username, email FROM users")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]}, Username: {row[1]}, Email: {row[2]}")
# 출력:
# ID: 1, Username: hong, Email: hong@example.com
# ID: 2, Username: kim, Email: kim@example.com
```

### Python - 방법 2: 딕셔너리로 받기 (추천!)

```python
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(...)

# RealDictCursor 사용
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 단일 행 조회
cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (1,))
row = cursor.fetchone()
print(row)  # {'id': 1, 'username': 'hong', 'email': 'hong@example.com'}

# 컬럼명으로 접근 (Java의 ResultSet.getString("username")과 유사)
user_id = row['id']          # 1
username = row['username']   # 'hong'
email = row['email']         # 'hong@example.com'

# 여러 행 조회
cursor.execute("SELECT id, username, email FROM users")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row['id']}, Username: {row['username']}, Email: {row['email']}")
```

### Python - 방법 3: 클래스 객체로 받기 (Java의 DTO처럼)

```python
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor

@dataclass
class User:
    id: int
    username: str
    email: str

conn = psycopg2.connect(...)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 단일 행을 객체로 변환
cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (1,))
row = cursor.fetchone()
user = User(**row)  # 딕셔너리를 언패킹하여 객체 생성
print(user)  # User(id=1, username='hong', email='hong@example.com')
print(user.username)  # 'hong'

# 여러 행을 객체 리스트로 변환 (Java의 List<User>와 동일!)
cursor.execute("SELECT id, username, email FROM users")
rows = cursor.fetchall()
users: list[User] = [User(**row) for row in rows]

for user in users:
    print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
```

### Python - 방법 4: Pydantic 모델로 받기 (타입 검증 포함)

```python
from pydantic import BaseModel, EmailStr
import psycopg2
from psycopg2.extras import RealDictCursor

class User(BaseModel):
    id: int
    username: str
    email: EmailStr  # 이메일 형식 자동 검증

conn = psycopg2.connect(...)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 단일 행
cursor.execute("SELECT id, username, email FROM users WHERE id = %s", (1,))
row = cursor.fetchone()
user = User(**row)  # 타입 검증 + 객체 생성
print(user.model_dump())  # {'id': 1, 'username': 'hong', 'email': 'hong@example.com'}

# 여러 행
cursor.execute("SELECT id, username, email FROM users")
rows = cursor.fetchall()
users: list[User] = [User(**row) for row in rows]
```

### MySQL에서도 동일한 패턴

```python
import pymysql
from pymysql.cursors import DictCursor

# 딕셔너리로 받기
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="password",
    database="mydb",
    charset="utf8mb4",
    cursorclass=DictCursor  # 딕셔너리 커서
)

cursor = conn.cursor()
cursor.execute("SELECT id, username, email FROM users")
rows = cursor.fetchall()

for row in rows:
    print(row['id'], row['username'], row['email'])
```

### fetchone() vs fetchall() vs fetchmany()

```python
cursor.execute("SELECT id, username, email FROM users")

# fetchone(): 한 행씩 가져오기
row = cursor.fetchone()
print(row)  # 첫 번째 행
row = cursor.fetchone()
print(row)  # 두 번째 행

# fetchall(): 모든 행을 리스트로 가져오기
cursor.execute("SELECT id, username, email FROM users")
rows = cursor.fetchall()
print(len(rows))  # 전체 행 개수
print(rows)  # [(1, 'hong', 'hong@...'), (2, 'kim', 'kim@...'), ...]

# fetchmany(size): 지정한 개수만큼 가져오기
cursor.execute("SELECT id, username, email FROM users")
rows = cursor.fetchmany(10)  # 10개만 가져오기
print(len(rows))  # 10

# 반복문으로 한 행씩 처리 (메모리 효율적)
cursor.execute("SELECT id, username, email FROM users")
for row in cursor:
    print(row)  # 한 행씩 처리
```

## 4. 주요 DB 드라이버 (DBMS별)

### PostgreSQL

```python
# 1. psycopg2 (가장 인기, C로 작성, 빠름)
pip install psycopg2-binary

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="password"
)

# 튜플로 받기
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")

# 딕셔너리로 받기 (추천)
cursor = conn.cursor(cursor_factory=RealDictCursor)
cursor.execute("SELECT * FROM users")
```

### MySQL/MariaDB

```python
# 1. PyMySQL (순수 Python, 가장 인기)
pip install pymysql

import pymysql
from pymysql.cursors import DictCursor

conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="password",
    database="mydb",
    charset="utf8mb4",
    cursorclass=DictCursor  # 딕셔너리로 받기
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
```

```python
# 2. mysql-connector-python (Oracle 공식)
pip install mysql-connector-python

import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="mydb"
)

# 딕셔너리로 받기
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
```

### SQLite

```python
# 기본 내장 (별도 설치 불필요)
import sqlite3

# 파일 기반 DB
conn = sqlite3.connect("mydb.db")

# 딕셔너리로 받기
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

for row in rows:
    print(row['id'], row['username'], row['email'])
```

## 5. Connection Pool (HikariCP의 Python 버전)

### psycopg2 내장 풀

```python
from psycopg2 import pool

# Connection Pool 생성
connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host="localhost",
    database="mydb",
    user="postgres",
    password="password"
)

# 풀에서 연결 가져오기
conn = connection_pool.getconn()

try:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
finally:
    # 풀에 반환 (close가 아님!)
    connection_pool.putconn(conn)

# 모든 연결 종료
connection_pool.closeall()
```

### SQLAlchemy Engine (가장 인기! 추천)

**SQLAlchemy는 Python의 HikariCP + Hibernate 같은 존재**입니다.

```python
pip install sqlalchemy psycopg2-binary

from sqlalchemy import create_engine, text

# Engine 생성 (Connection Pool 자동 관리)
engine = create_engine(
    "postgresql://user:password@localhost:5432/mydb",
    pool_size=10,          # 기본 연결 수 (HikariCP의 maximumPoolSize)
    max_overflow=20,       # 추가로 생성 가능한 연결 수
    pool_timeout=30,       # 연결 대기 시간 (초)
    pool_pre_ping=True,    # 연결 유효성 검사
    pool_recycle=3600,     # 연결 재사용 시간 (초)
    echo=True              # SQL 로깅 (개발용)
)

# 연결 사용 (자동으로 풀에서 가져오고 반환)
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM users"))
    for row in result:
        print(row)
# 자동으로 풀에 반환됨

# 트랜잭션
with engine.begin() as conn:
    conn.execute(text("INSERT INTO users (username) VALUES (:name)"), {"name": "hong"})
# 자동 커밋
```

## 6. SQLAlchemy ORM (JPA/Hibernate 역할)

### 모델 정의

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Base 클래스
Base = declarative_base()

# 모델 정의 (Java의 @Entity와 유사)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"

# Engine 생성
engine = create_engine("sqlite:///mydb.db", echo=True)

# 테이블 생성
Base.metadata.create_all(engine)

# Session 팩토리
Session = sessionmaker(bind=engine)
session = Session()
```

### CRUD 작업

```python
# CREATE
user = User(username="hong", email="hong@example.com")
session.add(user)
session.commit()

# READ - 단일 객체 조회
user = session.query(User).filter_by(username="hong").first()
print(user)  # <User(id=1, username='hong')>
print(user.username)  # 'hong'
print(user.email)     # 'hong@example.com'

# READ - 여러 객체 조회 (Java의 List<User>와 동일!)
users = session.query(User).filter(User.id > 10).all()
for user in users:
    print(user.id, user.username, user.email)

# UPDATE
user = session.query(User).filter_by(username="hong").first()
user.email = "newemail@example.com"
session.commit()

# DELETE
user = session.query(User).filter_by(username="hong").first()
session.delete(user)
session.commit()

# 세션 종료
session.close()
```

### 쿼리 결과를 객체로 자동 매핑

```python
# SQLAlchemy ORM은 자동으로 객체로 매핑됩니다
users: list[User] = session.query(User).all()

# Java의 다음 코드와 동일합니다:
# List<User> users = userRepository.findAll();

for user in users:
    print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
```

## 7. FastAPI + SQLAlchemy 실전 패턴

### 프로젝트 구조

```
project/
├── .env
├── requirements.txt
├── main.py
├── database.py
├── models.py
└── config.py
```

### 의존성 설치

```bash
pip install fastapi sqlalchemy psycopg2-binary pydantic-settings uvicorn
```

### 환경 설정

```python
# .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/mydb
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    class Config:
        env_file = ".env"

settings = Settings()
```

### 데이터베이스 연결

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Engine 생성 (Connection Pool 포함)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow
)

# Session 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()

# Dependency (Spring의 @Autowired 같은 역할)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 모델 정의

```python
# models.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### FastAPI 앱

```python
# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database import engine, get_db, Base
from models import User

# 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="My API")

# Pydantic 스키마 (Request/Response DTO)
class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True  # ORM 객체를 자동 변환

# CREATE
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# READ - 단일 조회
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# READ - 목록 조회 (Java의 List<UserResponse>와 동일!)
@app.get("/users/", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# 실행: uvicorn main:app --reload
```

## 8. 실전 예제: 복잡한 쿼리 결과 받기

### 조인 쿼리 결과를 DTO로 받기

```python
import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass

@dataclass
class UserWithPostCount:
    user_id: int
    username: str
    email: str
    post_count: int

conn = psycopg2.connect(..., cursor_factory=RealDictCursor)
cursor = conn.cursor()

query = """
    SELECT
        u.id as user_id,
        u.username,
        u.email,
        COUNT(p.id) as post_count
    FROM users u
    LEFT JOIN posts p ON u.id = p.user_id
    GROUP BY u.id, u.username, u.email
"""

cursor.execute(query)
rows = cursor.fetchall()

# 딕셔너리를 객체로 변환
results: list[UserWithPostCount] = [UserWithPostCount(**row) for row in rows]

for result in results:
    print(f"{result.username}: {result.post_count} posts")
```

### SQLAlchemy로 조인 쿼리

```python
from sqlalchemy import func
from sqlalchemy.orm import Session

# 방법 1: ORM 쿼리
results = (
    session.query(
        User.id,
        User.username,
        User.email,
        func.count(Post.id).label('post_count')
    )
    .outerjoin(Post, User.id == Post.user_id)
    .group_by(User.id, User.username, User.email)
    .all()
)

for row in results:
    print(f"ID: {row.id}, Username: {row.username}, Posts: {row.post_count}")

# 방법 2: SQL 직접 실행 + 결과를 DTO로
from sqlalchemy import text

@dataclass
class UserStats:
    user_id: int
    username: str
    post_count: int

query = text("""
    SELECT
        u.id as user_id,
        u.username,
        COUNT(p.id) as post_count
    FROM users u
    LEFT JOIN posts p ON u.id = p.user_id
    GROUP BY u.id, u.username
""")

result = session.execute(query)
rows = result.fetchall()

# RowProxy를 딕셔너리로 변환 후 객체 생성
stats: list[UserStats] = [UserStats(**dict(row._mapping)) for row in rows]
```

## 요약

### Python 데이터베이스 스택

| 역할 | Java/Spring | Python | 추천 |
|------|------------|--------|------|
| **표준 인터페이스** | JDBC | DB-API 2.0 | - |
| **Connection Pool** | HikariCP | SQLAlchemy Engine | ⭐⭐⭐⭐⭐ |
| **ORM** | Hibernate/JPA | SQLAlchemy ORM | ⭐⭐⭐⭐⭐ |
| **PostgreSQL Driver** | PostgreSQL JDBC | psycopg2 | ⭐⭐⭐⭐⭐ |
| **MySQL Driver** | MySQL Connector | PyMySQL | ⭐⭐⭐⭐⭐ |
| **설정 관리** | application.yml | pydantic-settings | ⭐⭐⭐⭐⭐ |

### SELECT 결과 받는 방법 정리

```python
# 1. 튜플로 받기 (기본)
cursor = conn.cursor()
cursor.execute("SELECT id, username, email FROM users")
row = cursor.fetchone()
print(row[0], row[1], row[2])  # 인덱스 접근

# 2. 딕셔너리로 받기 (추천!)
cursor = conn.cursor(cursor_factory=RealDictCursor)  # psycopg2
# cursor = conn.cursor(cursorclass=DictCursor)        # pymysql
cursor.execute("SELECT id, username, email FROM users")
row = cursor.fetchone()
print(row['id'], row['username'], row['email'])  # 키로 접근

# 3. 객체로 받기 (Java의 List<DTO>처럼)
@dataclass
class User:
    id: int
    username: str
    email: str

cursor.execute("SELECT id, username, email FROM users")
rows = cursor.fetchall()
users: list[User] = [User(**row) for row in rows]  # Java의 List<User>와 동일!

# 4. SQLAlchemy ORM (자동 매핑)
users: list[User] = session.query(User).all()  # 자동으로 객체로 변환
```

### Spring Boot 개발자를 위한 추천 스택

```bash
pip install fastapi sqlalchemy psycopg2-binary pydantic-settings uvicorn
```

**조합:**
- **FastAPI**: Spring Boot와 유사한 웹 프레임워크
- **SQLAlchemy**: Hibernate + HikariCP 역할
- **psycopg2**: PostgreSQL JDBC Driver 역할
- **pydantic-settings**: application.yml 같은 설정 관리

### 빠른 시작 템플릿

```python
# 1. 설치
pip install psycopg2-binary

# 2. 딕셔너리로 조회 (가장 실용적)
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="user",
    password="password"
)

cursor = conn.cursor(cursor_factory=RealDictCursor)
cursor.execute("SELECT id, username, email FROM users")
rows = cursor.fetchall()

for row in rows:
    print(f"ID: {row['id']}, Username: {row['username']}")

# 3. 객체로 변환 (Java 스타일)
from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
    email: str

users: list[User] = [User(**row) for row in rows]
```

### 핵심 포인트

1. **DB-API 2.0**은 Python의 JDBC 표준
2. **SQLAlchemy**는 가장 인기 있는 ORM + Connection Pool
3. **psycopg2**는 PostgreSQL의 사실상 표준 드라이버
4. **PyMySQL**은 MySQL의 순수 Python 드라이버
5. SELECT 결과는 **딕셔너리로 받거나** **객체로 변환**하는 것이 일반적
6. **RealDictCursor/DictCursor**를 사용하면 컬럼명으로 접근 가능
7. SQLAlchemy ORM은 **자동으로 객체 매핑** (Java의 JPA처럼)

## 참고 자료

- [PEP 249 - Python Database API Specification v2.0](https://www.python.org/dev/peps/pep-0249/)
- [SQLAlchemy 공식 문서](https://docs.sqlalchemy.org/)
- [FastAPI 공식 문서 - SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [psycopg2 문서](https://www.psycopg.org/docs/)
- [PyMySQL 문서](https://pymysql.readthedocs.io/)
