# Pydantic 실무 활용: BaseSettings와 Field

Python에서 환경변수와 설정을 타입 안전하게 관리하는 방법

## 결론부터 말하면

**Pydantic은 "데이터 검증 + 타입 변환"을 자동으로 해주는 라이브러리다.** 실무에서는 크게 두 가지 용도로 쓴다:

| 용도 | 클래스 | 설명 |
|------|--------|------|
| **설정 관리** | `BaseSettings` | 환경변수/.env 파일 자동 바인딩 |
| **데이터 검증** | `BaseModel` | API 요청/응답 검증 |

**Java로 비유하면:**

| Pydantic | Java |
|----------|------|
| `BaseSettings` | `@ConfigurationProperties` |
| `BaseModel` | DTO + `@Valid` |
| `Field(...)` | `@NotNull`, `@Size`, `@Value` |
| `AnyUrl`, `EmailStr` | `@URL`, `@Email` |

```python
# 환경변수 APP_PORT=8080, APP_LOG_LEVEL=DEBUG 가 있다면...
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="app_")

    PORT: int = Field(default=12000)           # APP_PORT → 8080 (자동 변환)
    LOG_LEVEL: str = Field(default="INFO")     # APP_LOG_LEVEL → "DEBUG"

config = AppConfig()
print(config.PORT)       # 8080 (int)
print(config.LOG_LEVEL)  # "DEBUG"
```

## 1. 왜 Pydantic인가?

### 만약 Pydantic 없이 설정을 관리한다면?

```python
# ❌ Pydantic 없이
import os

class Config:
    def __init__(self):
        # 직접 타입 변환해야 함
        self.port = int(os.getenv("APP_PORT", "12000"))
        self.debug = os.getenv("APP_DEBUG", "false").lower() == "true"
        self.redis_url = os.getenv("APP_REDIS_URL", "redis://localhost:6379")

        # 검증? 직접 해야 함
        if self.port < 0 or self.port > 65535:
            raise ValueError("Invalid port")

        # URL 형식 검증? 정규식으로 직접...
        import re
        if not re.match(r'^redis://.*', self.redis_url):
            raise ValueError("Invalid Redis URL")
```

**문제점:**
- 타입 변환을 직접 해야 함 (`int()`, `bool()` 등)
- 검증 로직을 직접 작성해야 함
- `.env` 파일 로딩도 직접 구현해야 함
- 에러 메시지가 불친절함

### Pydantic을 쓰면?

```python
# ✅ Pydantic 사용
from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="app_",
    )

    PORT: int = Field(default=12000, ge=0, le=65535)  # 범위 검증 포함
    DEBUG: bool = Field(default=False)
    REDIS_URL: AnyUrl = Field(default="redis://localhost:6379")

config = AppConfig()
# 타입 변환, 검증, .env 로딩 모두 자동!
```

## 2. BaseSettings: 환경변수 자동 바인딩

### 기본 사용법

```python
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 12000
    DEBUG: bool = False

config = AppConfig()
```

이 코드만으로:
- `HOST` 환경변수 → `config.HOST`
- `PORT` 환경변수 → `config.PORT` (문자열 → int 자동 변환)
- `DEBUG` 환경변수 → `config.DEBUG` ("true"/"false" → bool 자동 변환)

### SettingsConfigDict: 설정 소스 지정

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # .env 파일에서 읽기
        env_prefix="app_",         # APP_ 접두사 붙은 환경변수만
        env_file_encoding="utf-8",
        extra="ignore"             # 정의 안 된 필드는 무시
    )

    PORT: int = 12000
    LOG_LEVEL: str = "INFO"
```

**env_prefix 동작 방식:**

| 환경변수 | 필드명 | 매핑 |
|----------|--------|------|
| `APP_PORT=8080` | `PORT` | ✅ 매핑됨 |
| `APP_LOG_LEVEL=DEBUG` | `LOG_LEVEL` | ✅ 매핑됨 |
| `PORT=9999` | `PORT` | ❌ 무시 (접두사 없음) |

**대소문자는 구분하지 않는다** (case-insensitive):
- `APP_PORT`, `app_port`, `App_Port` 모두 `PORT` 필드에 매핑
- 이 동작은 `case_sensitive=False` (기본값) 설정에 의해 제어됨
- 대소문자를 엄격하게 구분해야 한다면 `case_sensitive=True`로 설정

**설정 값 우선순위** (높은 순):
1. 시스템 환경변수 (가장 우선)
2. `.env` 파일
3. `Field(default=...)` 기본값

배포 환경에서는 시스템 환경변수가 `.env` 파일보다 우선하므로, 운영 환경별로 다른 설정을 쉽게 적용할 수 있다.

### 실제 .env 파일 예시

```bash
# .env
APP_PORT=12000
APP_LOG_LEVEL=INFO
APP_LOG_FILE_ENABLED=true
APP_REDIS_URL=redis://localhost:6380/0
APP_AICC_API_URL=http://localhost:8000
```

## 3. Field: 필드 메타데이터와 검증

### 기본값 설정

```python
from pydantic import Field

class AppConfig(BaseSettings):
    # 단순 기본값
    ENV: str = Field(default="development")
    PORT: int = Field(default=12000)

    # 설명 추가 (문서화, IDE 힌트)
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Root logger level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
```

### default vs default_factory

```python
from pydantic import Field
from typing import Any

# ❌ 잘못된 사용: mutable 객체를 default로
class BadConfig(BaseSettings):
    TAGS: list = Field(default=[])  # 위험! 모든 인스턴스가 같은 리스트 공유

# ✅ 올바른 사용: default_factory로
class GoodConfig(BaseSettings):
    TAGS: list = Field(default_factory=list)  # 매번 새 리스트 생성

    # 함수로 복잡한 기본값 생성
    REDIS_OPTIONS: dict[str, Any] = Field(
        default_factory=lambda: {
            "max_connections": 20,
            "socket_keepalive": True,
        }
    )
```

**언제 뭘 쓰나?**

| 타입 | 사용 | 이유 |
|------|------|------|
| `str`, `int`, `bool` | `default=` | immutable이라 안전 |
| `list`, `dict`, `set` | `default_factory=` | mutable이라 공유 위험 |
| 복잡한 로직 | `default_factory=func` | 함수로 계산 |

### 검증 규칙 추가

```python
from pydantic import Field

class AppConfig(BaseSettings):
    # 숫자 범위
    PORT: int = Field(default=12000, ge=0, le=65535)
    TIMEOUT: int = Field(default=30, gt=0)  # 0보다 커야 함

    # 문자열 길이
    API_KEY: str = Field(min_length=10, max_length=100)

    # 정규식 패턴
    LOG_LEVEL: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"
    )
```

**검증 옵션:**

| 옵션 | 의미 | 예시 |
|------|------|------|
| `gt` | greater than (초과) | `gt=0` → 0보다 커야 함 |
| `ge` | greater or equal (이상) | `ge=0` → 0 이상 |
| `lt` | less than (미만) | `lt=100` → 100 미만 |
| `le` | less or equal (이하) | `le=100` → 100 이하 |
| `min_length` | 최소 길이 | 문자열, 리스트 |
| `max_length` | 최대 길이 | 문자열, 리스트 |
| `pattern` | 정규식 패턴 | 문자열만 |

## 4. 타입 검증: AnyUrl, EmailStr 등

### URL 검증

```python
from pydantic import AnyUrl, HttpUrl, Field
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    # 모든 URL 스킴 허용 (redis://, http://, https://, ...)
    REDIS_URL: AnyUrl = Field(default="redis://localhost:6380/0")

    # HTTP/HTTPS만 허용
    API_URL: HttpUrl = Field(default="https://api.example.com")
```

**AnyUrl의 장점:**

```python
config = AppConfig()

# URL 파싱 결과에 접근 가능
print(config.REDIS_URL.scheme)  # "redis"
print(config.REDIS_URL.host)    # "localhost"
print(config.REDIS_URL.port)    # 6380
print(config.REDIS_URL.path)    # "/0"
```

### 기타 유용한 타입들

```python
from pydantic import (
    EmailStr,      # 이메일 형식 검증
    SecretStr,     # 비밀번호 (출력 시 마스킹)
    DirectoryPath, # 존재하는 디렉토리
    FilePath,      # 존재하는 파일
    PositiveInt,   # 양수
    NegativeInt,   # 음수
)

class AppConfig(BaseSettings):
    ADMIN_EMAIL: EmailStr = "admin@example.com"
    DB_PASSWORD: SecretStr
    LOG_DIR: DirectoryPath = "/var/log/app"
    CONFIG_FILE: FilePath = "/etc/app/config.yaml"
    MAX_WORKERS: PositiveInt = 4
```

**SecretStr 동작:**

```python
config = AppConfig(DB_PASSWORD="super_secret_123")

print(config.DB_PASSWORD)                    # SecretStr('**********')
print(config.DB_PASSWORD.get_secret_value()) # "super_secret_123"
```

## 5. 싱글톤 패턴: 설정 한 번만 로드

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    PORT: int = 12000
    DEBUG: bool = False

@lru_cache  # 결과를 캐싱해서 한 번만 생성
def get_config() -> AppConfig:
    return AppConfig()

# 사용
config = get_config()  # 첫 호출: AppConfig 생성
config = get_config()  # 두 번째 호출: 캐시된 인스턴스 반환
```

**왜 `@lru_cache`를 쓰나?**
- 환경변수는 앱 실행 중 변하지 않음
- 매번 새로 파싱하면 비효율적
- 싱글톤처럼 동작하게 만듦

## 6. 실전 예시: 전체 설정 클래스

실무에서 흔히 보는 패턴:

```python
import platform
import socket
from functools import lru_cache
from typing import Any

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_default_redis_options() -> dict[str, Any]:
    """OS별 Redis 연결 옵션"""
    is_darwin = platform.system() == "Darwin"

    if is_darwin:
        keepalive = {socket.TCP_KEEPALIVE: 30}
    else:
        keepalive = {
            socket.TCP_KEEPIDLE: 30,
            socket.TCP_KEEPINTVL: 15,
        }

    return {
        "max_connections": 20,
        "socket_keepalive": True,
        "socket_keepalive_options": keepalive,
    }


class AppConfig(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="app_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 기본 설정
    ENV: str = Field(default="development")
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=12000, ge=0, le=65535)

    # 로깅
    LOG_LEVEL: str = Field(
        default="INFO",
        description="DEBUG, INFO, WARNING, ERROR, CRITICAL",
    )
    LOG_FILE_ENABLED: bool = Field(default=True)
    LOG_FILE_PATH: str = Field(default="logs/app.log")

    # Redis
    REDIS_URL: AnyUrl = Field(default="redis://localhost:6380/0")
    REDIS_OPTIONS: dict[str, Any] = Field(
        default_factory=_get_default_redis_options,
    )

    # 외부 API
    API_URL: AnyUrl = Field(default="http://localhost:8000")


@lru_cache
def get_config() -> AppConfig:
    return AppConfig()


# 전역에서 사용
config = get_config()
```

## 7. BaseModel vs BaseSettings

`BaseSettings`는 `BaseModel`을 상속받아 **모든 데이터 검증 기능을 포함**하면서, 환경변수/.env 파일 로딩 기능이 추가된 클래스다.

| 특징 | BaseModel | BaseSettings |
|------|-----------|--------------|
| **용도** | 데이터 검증 | 설정 관리 |
| **데이터 소스** | 생성자 인자 | 환경변수, .env 파일 |
| **사용 사례** | API 요청/응답 DTO | 앱 설정, 환경변수 |
| **패키지** | `pydantic` | `pydantic_settings` |

```python
# BaseModel: API 요청 검증
from pydantic import BaseModel

class UserCreateRequest(BaseModel):
    username: str
    email: str
    age: int

# 사용: JSON → 객체
user = UserCreateRequest(**request.json())


# BaseSettings: 환경변수 로딩
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

# 사용: 환경변수 → 객체
config = AppConfig()  # 환경변수에서 자동 로딩
```

## 8. Java와의 비교

### Spring @ConfigurationProperties vs Pydantic BaseSettings

```java
// Java Spring
@ConfigurationProperties(prefix = "app")
public class AppConfig {
    private String env = "development";
    private int port = 12000;
    private String logLevel = "INFO";

    // getter, setter 필요
}
```

```python
# Python Pydantic
class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="app_")

    ENV: str = "development"
    PORT: int = 12000
    LOG_LEVEL: str = "INFO"
    # getter, setter 불필요
```

### Bean Validation vs Field

```java
// Java
public class Config {
    @NotNull
    private String apiKey;

    @Min(0) @Max(65535)
    private int port;

    @Pattern(regexp = "^(DEBUG|INFO|WARNING|ERROR)$")
    private String logLevel;
}
```

```python
# Python
class Config(BaseSettings):
    API_KEY: str  # 기본적으로 required
    PORT: int = Field(ge=0, le=65535)
    LOG_LEVEL: str = Field(pattern="^(DEBUG|INFO|WARNING|ERROR)$")
```

## 정리

| 기능 | 사용법 | 용도 |
|------|--------|------|
| `BaseSettings` | 클래스 상속 | 환경변수 자동 바인딩 |
| `SettingsConfigDict` | `model_config =` | .env 파일, 접두사 설정 |
| `Field(default=)` | 기본값 | immutable 타입 기본값 |
| `Field(default_factory=)` | 함수로 기본값 | mutable 타입, 복잡한 로직 |
| `Field(description=)` | 설명 | 문서화, IDE 힌트 |
| `Field(ge=, le=, ...)` | 검증 규칙 | 값 범위 제한 |
| `AnyUrl`, `EmailStr` | 타입 | 형식 검증 |
| `@lru_cache` | 함수 데코레이터 | 싱글톤 패턴 |

---

## 출처

- [Pydantic 공식 문서](https://docs.pydantic.dev/)
- [pydantic-settings 공식 문서](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Pydantic Field 공식 문서](https://docs.pydantic.dev/latest/concepts/fields/)
