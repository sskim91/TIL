# Python Factory 패턴 완전 정복

객체 생성 로직을 캡슐화하여 코드의 유연성과 확장성을 높이는 생성 패턴

## 결론부터 말하면

Factory 패턴은 **객체 생성 방법을 숨기고**, 인터페이스를 통해 객체를 생성하는 패턴입니다.

Python은 **3가지 Factory 패턴**을 지원하며, Duck typing 덕분에 Java보다 훨씬 간결합니다:

| 패턴 | 복잡도 | 유연성 | 사용 시기 |
|------|--------|--------|-----------|
| Simple Factory | ⭐ | ⭐ | 객체 타입이 적을 때 |
| Factory Method | ⭐⭐ | ⭐⭐ | 서브클래스가 생성 결정 |
| Abstract Factory | ⭐⭐⭐ | ⭐⭐⭐ | 관련 객체군 생성 |

```python
# Before: 직접 생성 (타입별 분기)
if payment_type == "card":
    payment = CardPayment()
elif payment_type == "bank":
    payment = BankPayment()

# After: Factory 사용 (확장 가능)
payment = PaymentFactory.create(payment_type)
```

**Java와의 차이**: Java는 인터페이스/추상 클래스가 필수지만, Python은 Duck typing으로 더 유연하며, 함수만으로도 Factory를 만들 수 있습니다.

---

## 1. Factory 패턴이란?

### 1.1 정의

**Factory 패턴**은 객체 생성 로직을 별도의 클래스나 메서드로 분리하여:
- 객체 생성 방법을 숨기고
- 클라이언트 코드와 구체적인 클래스를 분리
- 새로운 타입 추가 시 기존 코드 수정 최소화

### 1.2 언제 사용하나?

✅ **사용해야 할 때**:
- 생성할 객체의 정확한 타입을 미리 알 수 없을 때
- 객체 생성 로직이 복잡할 때
- 새로운 타입을 자주 추가해야 할 때
- 설정 파일이나 외부 입력에 따라 객체를 생성할 때

❌ **불필요할 때**:
- 객체 타입이 하나뿐일 때
- 객체 생성이 매우 단순할 때
- 확장 가능성이 없을 때

---

## 2. Simple Factory (간단한 팩토리)

### 2.1 기본 구현

가장 단순한 형태로, **하나의 메서드**가 모든 객체 생성을 담당합니다.

```python
from abc import ABC, abstractmethod
from typing import Protocol

# Protocol (Duck typing)
class Payment(Protocol):
    def pay(self, amount: float) -> str:
        ...

# 구체적인 클래스들
class CardPayment:
    def pay(self, amount: float) -> str:
        return f"카드로 {amount}원 결제"

class BankTransfer:
    def pay(self, amount: float) -> str:
        return f"계좌이체로 {amount}원 결제"

class CashPayment:
    def pay(self, amount: float) -> str:
        return f"현금으로 {amount}원 결제"

# Simple Factory
class PaymentFactory:
    @staticmethod
    def create(payment_type: str) -> Payment:
        if payment_type == "card":
            return CardPayment()
        elif payment_type == "bank":
            return BankTransfer()
        elif payment_type == "cash":
            return CashPayment()
        else:
            raise ValueError(f"Unknown payment type: {payment_type}")

# 사용
payment = PaymentFactory.create("card")
print(payment.pay(10000))  # 카드로 10000원 결제
```

### 2.2 딕셔너리 기반 Factory (더 Pythonic!)

if-elif 대신 **딕셔너리 맵핑**을 사용하면 더 깔끔합니다:

```python
class PaymentFactory:
    _payment_types = {
        "card": CardPayment,
        "bank": BankTransfer,
        "cash": CashPayment,
    }

    @classmethod
    def create(cls, payment_type: str) -> Payment:
        payment_class = cls._payment_types.get(payment_type)
        if payment_class is None:
            raise ValueError(f"Unknown payment type: {payment_type}")
        return payment_class()

    @classmethod
    def register(cls, name: str, payment_class: type):
        """새로운 결제 방식 동적 등록"""
        cls._payment_types[name] = payment_class

# 새로운 타입 추가 (기존 코드 수정 없이!)
class CryptoPayment:
    def pay(self, amount: float) -> str:
        return f"암호화폐로 {amount}원 결제"

PaymentFactory.register("crypto", CryptoPayment)

payment = PaymentFactory.create("crypto")
print(payment.pay(10000))  # 암호화폐로 10000원 결제
```

### 2.3 함수 기반 Factory (가장 간단)

Python은 함수가 First-class이므로 클래스 없이도 가능합니다:

```python
def create_payment(payment_type: str) -> Payment:
    factories = {
        "card": CardPayment,
        "bank": BankTransfer,
        "cash": CashPayment,
    }

    payment_class = factories.get(payment_type)
    if payment_class is None:
        raise ValueError(f"Unknown payment type: {payment_type}")

    return payment_class()

# 사용
payment = create_payment("card")
```

---

## 3. Factory Method (팩토리 메서드)

### 3.1 개념

**서브클래스**가 어떤 객체를 생성할지 결정하는 패턴입니다.

- 부모 클래스: 객체 생성 인터페이스 정의
- 자식 클래스: 실제 생성할 객체 결정

### 3.2 구현 예시: 문서 생성기

```python
from abc import ABC, abstractmethod

# 생성될 객체들
class Document(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

class PDFDocument(Document):
    def render(self) -> str:
        return "PDF 문서 렌더링"

class WordDocument(Document):
    def render(self) -> str:
        return "Word 문서 렌더링"

class HTMLDocument(Document):
    def render(self) -> str:
        return "HTML 문서 렌더링"

# Factory Method 패턴
class DocumentCreator(ABC):
    """추상 Creator 클래스"""

    @abstractmethod
    def create_document(self) -> Document:
        """Factory Method: 서브클래스가 구현"""
        pass

    def export(self) -> str:
        """템플릿 메서드: Factory Method 사용"""
        doc = self.create_document()
        return f"문서 생성 중... {doc.render()}"

# 구체적인 Creator들
class PDFCreator(DocumentCreator):
    def create_document(self) -> Document:
        return PDFDocument()

class WordCreator(DocumentCreator):
    def create_document(self) -> Document:
        return WordDocument()

class HTMLCreator(DocumentCreator):
    def create_document(self) -> Document:
        return HTMLDocument()

# 사용
def export_document(creator: DocumentCreator):
    print(creator.export())

export_document(PDFCreator())   # PDF 문서 렌더링
export_document(WordCreator())  # Word 문서 렌더링
```

### 3.3 동적 Factory Method (Python 스타일)

Python은 타입을 인자로 받아 더 유연하게 만들 수 있습니다:

```python
class FlexibleDocumentCreator:
    def __init__(self, document_class: type[Document]):
        self.document_class = document_class

    def create_document(self) -> Document:
        return self.document_class()

    def export(self) -> str:
        doc = self.create_document()
        return f"문서 생성 중... {doc.render()}"

# 사용
creator = FlexibleDocumentCreator(PDFDocument)
print(creator.export())  # PDF 문서 렌더링
```

---

## 4. Abstract Factory (추상 팩토리)

### 4.1 개념

**관련된 객체군**을 일관성 있게 생성하는 패턴입니다.

예: UI 테마별로 버튼, 체크박스, 텍스트박스를 함께 생성

### 4.2 구현 예시: UI 테마

```python
from abc import ABC, abstractmethod

# 생성될 제품군: 버튼, 체크박스
class Button(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

class Checkbox(ABC):
    @abstractmethod
    def render(self) -> str:
        pass

# Dark 테마 제품군
class DarkButton(Button):
    def render(self) -> str:
        return "🌑 Dark 버튼"

class DarkCheckbox(Checkbox):
    def render(self) -> str:
        return "🌑 Dark 체크박스"

# Light 테마 제품군
class LightButton(Button):
    def render(self) -> str:
        return "☀️ Light 버튼"

class LightCheckbox(Checkbox):
    def render(self) -> str:
        return "☀️ Light 체크박스"

# Abstract Factory
class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button:
        pass

    @abstractmethod
    def create_checkbox(self) -> Checkbox:
        pass

# 구체적인 Factory들
class DarkThemeFactory(UIFactory):
    def create_button(self) -> Button:
        return DarkButton()

    def create_checkbox(self) -> Checkbox:
        return DarkCheckbox()

class LightThemeFactory(UIFactory):
    def create_button(self) -> Button:
        return LightButton()

    def create_checkbox(self) -> Checkbox:
        return LightCheckbox()

# 클라이언트 코드
def render_ui(factory: UIFactory):
    button = factory.create_button()
    checkbox = factory.create_checkbox()

    print(button.render())
    print(checkbox.render())

# 사용
print("=== Dark 테마 ===")
render_ui(DarkThemeFactory())

print("\n=== Light 테마 ===")
render_ui(LightThemeFactory())
```

**출력**:
```
=== Dark 테마 ===
🌑 Dark 버튼
🌑 Dark 체크박스

=== Light 테마 ===
☀️ Light 버튼
☀️ Light 체크박스
```

### 4.3 Python 스타일: 딕셔너리 + 튜플

```python
# 더 Pythonic한 방식
class SimpleUIFactory:
    themes = {
        "dark": (DarkButton, DarkCheckbox),
        "light": (LightButton, LightCheckbox),
    }

    @classmethod
    def create_ui(cls, theme: str) -> tuple[Button, Checkbox]:
        button_class, checkbox_class = cls.themes[theme]
        return button_class(), checkbox_class()

# 사용
button, checkbox = SimpleUIFactory.create_ui("dark")
print(button.render())
print(checkbox.render())
```

---

## 5. 실전 예제

### 5.1 데이터베이스 연결 Factory

```python
from abc import ABC, abstractmethod
from typing import Any

class DatabaseConnection(ABC):
    @abstractmethod
    def connect(self) -> str:
        pass

    @abstractmethod
    def query(self, sql: str) -> Any:
        pass

class MySQLConnection(DatabaseConnection):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def connect(self) -> str:
        return f"MySQL 연결: {self.host}:{self.port}"

    def query(self, sql: str) -> Any:
        return f"MySQL 쿼리 실행: {sql}"

class PostgreSQLConnection(DatabaseConnection):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def connect(self) -> str:
        return f"PostgreSQL 연결: {self.host}:{self.port}"

    def query(self, sql: str) -> Any:
        return f"PostgreSQL 쿼리 실행: {sql}"

class SQLiteConnection(DatabaseConnection):
    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self) -> str:
        return f"SQLite 연결: {self.db_path}"

    def query(self, sql: str) -> Any:
        return f"SQLite 쿼리 실행: {sql}"

# Factory with configuration
class DatabaseFactory:
    @staticmethod
    def create(db_type: str, **config) -> DatabaseConnection:
        if db_type == "mysql":
            return MySQLConnection(
                host=config.get("host", "localhost"),
                port=config.get("port", 3306)
            )
        elif db_type == "postgresql":
            return PostgreSQLConnection(
                host=config.get("host", "localhost"),
                port=config.get("port", 5432)
            )
        elif db_type == "sqlite":
            return SQLiteConnection(
                db_path=config.get("db_path", ":memory:")
            )
        else:
            raise ValueError(f"Unknown database type: {db_type}")

# 사용: 설정 기반 객체 생성
db = DatabaseFactory.create("mysql", host="db.example.com", port=3306)
print(db.connect())  # MySQL 연결: db.example.com:3306
print(db.query("SELECT * FROM users"))
```

### 5.2 로깅 Handler Factory

```python
import logging
from typing import Optional

class LogHandlerFactory:
    """환경별로 다른 로깅 핸들러 생성"""

    @staticmethod
    def create(env: str, log_file: Optional[str] = None) -> logging.Handler:
        if env == "development":
            # 개발: 콘솔에 상세 로그
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        elif env == "production":
            # 프로덕션: 파일에 간결한 로그
            handler = logging.FileHandler(log_file or "app.log")
            handler.setLevel(logging.WARNING)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )

        elif env == "testing":
            # 테스트: NullHandler (로그 무시)
            handler = logging.NullHandler()
            formatter = logging.Formatter('%(message)s')

        else:
            raise ValueError(f"Unknown environment: {env}")

        handler.setFormatter(formatter)
        return handler

# 사용
logger = logging.getLogger(__name__)
logger.addHandler(LogHandlerFactory.create("development"))
logger.info("애플리케이션 시작")
```

### 5.3 API 클라이언트 Factory (실무)

```python
from abc import ABC, abstractmethod
from typing import Any, Dict

class APIClient(ABC):
    @abstractmethod
    def get(self, endpoint: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def post(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        pass

class RestAPIClient(APIClient):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def get(self, endpoint: str) -> Dict[str, Any]:
        return {"method": "GET", "url": f"{self.base_url}{endpoint}"}

    def post(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        return {"method": "POST", "url": f"{self.base_url}{endpoint}", "data": data}

class GraphQLClient(APIClient):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def get(self, endpoint: str) -> Dict[str, Any]:
        query = f"query {{ {endpoint} }}"
        return {"query": query, "url": self.base_url}

    def post(self, endpoint: str, data: Dict) -> Dict[str, Any]:
        mutation = f"mutation {{ {endpoint} }}"
        return {"mutation": mutation, "variables": data, "url": self.base_url}

class APIClientFactory:
    """환경 변수나 설정 파일 기반으로 API 클라이언트 생성"""

    _clients = {
        "rest": RestAPIClient,
        "graphql": GraphQLClient,
    }

    @classmethod
    def create(cls, api_type: str, base_url: str, api_key: str) -> APIClient:
        client_class = cls._clients.get(api_type)
        if client_class is None:
            raise ValueError(f"Unknown API type: {api_type}")

        return client_class(base_url, api_key)

    @classmethod
    def from_config(cls, config: Dict[str, str]) -> APIClient:
        """설정 딕셔너리로부터 생성"""
        return cls.create(
            api_type=config["api_type"],
            base_url=config["base_url"],
            api_key=config["api_key"]
        )

# 사용: 설정 기반
config = {
    "api_type": "rest",
    "base_url": "https://api.example.com",
    "api_key": "secret-key-123"
}

client = APIClientFactory.from_config(config)
print(client.get("/users"))
```

---

## 6. Java와의 비교

### 6.1 구현 방식 차이

| 측면 | Python | Java |
|------|--------|------|
| 인터페이스 | Protocol, Duck typing | interface, abstract class 필수 |
| Factory 구현 | 함수, 클래스, 딕셔너리 | 주로 클래스 기반 |
| 타입 안정성 | 런타임 (선택적 타입 힌팅) | 컴파일 타임 |
| 유연성 | 매우 높음 | 중간 |
| 보일러플레이트 | 적음 | 많음 |

### 6.2 Simple Factory 비교

**Python**:
```python
# 함수로 간단히
def create_payment(payment_type: str) -> Payment:
    return {
        "card": CardPayment,
        "bank": BankTransfer,
    }[payment_type]()
```

**Java**:
```java
// 클래스 필수
public class PaymentFactory {
    public static Payment create(String paymentType) {
        switch (paymentType) {
            case "card":
                return new CardPayment();
            case "bank":
                return new BankTransfer();
            default:
                throw new IllegalArgumentException("Unknown type");
        }
    }
}
```

### 6.3 Factory Method 비교

**Python** (Duck typing):
```python
class DocumentCreator(ABC):
    @abstractmethod
    def create_document(self) -> Document:  # Protocol로도 가능
        pass

class PDFCreator(DocumentCreator):
    def create_document(self) -> Document:
        return PDFDocument()
```

**Java** (인터페이스 필수):
```java
// 인터페이스 정의 필수
public interface Document {
    String render();
}

// 추상 Creator
public abstract class DocumentCreator {
    public abstract Document createDocument();

    public String export() {
        Document doc = createDocument();
        return "문서 생성 중... " + doc.render();
    }
}

// 구체적인 Creator
public class PDFCreator extends DocumentCreator {
    @Override
    public Document createDocument() {
        return new PDFDocument();
    }
}
```

### 6.4 장단점 비교

**Python의 장점**:
- ✅ 간결함: 함수만으로도 Factory 가능
- ✅ 유연성: Duck typing으로 인터페이스 불필요
- ✅ 동적 등록: 런타임에 새 타입 추가 가능
- ✅ 딕셔너리 맵핑: if-elif 대신 깔끔한 맵핑

**Java의 장점**:
- ✅ 타입 안정성: 컴파일 타임 에러 검출
- ✅ 명시적 계약: 인터페이스로 명확한 규약
- ✅ IDE 지원: 자동완성, 리팩토링 강력
- ✅ 대규모 프로젝트: 타입 시스템으로 안정성 확보

---

## 7. 실무 활용 패턴

### 7.1 Django에서의 Factory 패턴

```python
# Django View Factory
from django.views import View
from django.http import HttpResponse

class ViewFactory:
    """요청 타입에 따라 다른 뷰 반환"""

    _views = {
        "list": lambda: ListView.as_view(),
        "detail": lambda: DetailView.as_view(),
        "create": lambda: CreateView.as_view(),
    }

    @classmethod
    def get_view(cls, view_type: str):
        view_func = cls._views.get(view_type)
        if view_func is None:
            raise ValueError(f"Unknown view type: {view_type}")
        return view_func()
```

### 7.2 FastAPI에서의 Dependency Factory

```python
from fastapi import Depends, FastAPI
from typing import Annotated

app = FastAPI()

# Database Factory for Dependency Injection
def get_db_factory(env: str):
    """환경별로 다른 DB 반환하는 Factory"""
    def get_db():
        if env == "production":
            db = DatabaseFactory.create("postgresql", host="prod.db.com")
        elif env == "development":
            db = DatabaseFactory.create("sqlite", db_path="dev.db")
        else:
            db = DatabaseFactory.create("sqlite", db_path=":memory:")

        try:
            yield db
        finally:
            # cleanup
            pass

    return get_db

# 사용
DatabaseDep = Annotated[DatabaseConnection, Depends(get_db_factory("development"))]

@app.get("/users")
def get_users(db: DatabaseDep):
    return db.query("SELECT * FROM users")
```

### 7.3 Strategy + Factory 조합

```python
from typing import Protocol

# Strategy 인터페이스
class CompressionStrategy(Protocol):
    def compress(self, data: bytes) -> bytes:
        ...

class ZipCompression:
    def compress(self, data: bytes) -> bytes:
        return b"ZIP: " + data

class GzipCompression:
    def compress(self, data: bytes) -> bytes:
        return b"GZIP: " + data

class Brotli Compression:
    def compress(self, data: bytes) -> bytes:
        return b"Brotli: " + data

# Factory로 Strategy 생성
class CompressionFactory:
    _strategies = {
        "zip": ZipCompression,
        "gzip": GzipCompression,
        "brotli": BrotliCompression,
    }

    @classmethod
    def get_strategy(cls, compression_type: str) -> CompressionStrategy:
        strategy_class = cls._strategies.get(compression_type)
        if strategy_class is None:
            raise ValueError(f"Unknown compression: {compression_type}")
        return strategy_class()

# 사용
class FileCompressor:
    def __init__(self, compression_type: str):
        self.strategy = CompressionFactory.get_strategy(compression_type)

    def compress_file(self, data: bytes) -> bytes:
        return self.strategy.compress(data)

# 클라이언트 코드
compressor = FileCompressor("gzip")
result = compressor.compress_file(b"Hello World")
print(result)  # b'GZIP: Hello World'
```

---

## 8. 안티패턴과 주의사항

### 8.1 과도한 Factory 사용

❌ **잘못된 예**: 단순한 경우에도 Factory 사용
```python
# 불필요한 Factory
class UserFactory:
    @staticmethod
    def create(name: str, email: str):
        return User(name, email)

# 그냥 직접 생성하는 게 나음
user = User(name="John", email="john@example.com")
```

✅ **올바른 예**: 복잡한 생성 로직이 있을 때만
```python
class UserFactory:
    @staticmethod
    def create_from_oauth(oauth_data: dict):
        # 복잡한 변환 로직
        name = oauth_data["profile"]["name"]
        email = oauth_data["profile"]["email"]
        avatar = oauth_data["profile"]["picture"]

        # 검증
        if not email:
            raise ValueError("Email required")

        # 객체 생성
        user = User(name=name, email=email)
        user.set_avatar(avatar)
        return user
```

### 8.2 God Object Factory

❌ **잘못된 예**: 하나의 Factory가 너무 많은 책임
```python
class ObjectFactory:
    """안티패턴: 모든 객체를 생성하는 God Object"""
    @staticmethod
    def create(obj_type: str, **kwargs):
        if obj_type == "user":
            return User(**kwargs)
        elif obj_type == "product":
            return Product(**kwargs)
        elif obj_type == "order":
            return Order(**kwargs)
        # ... 100개 이상의 타입
```

✅ **올바른 예**: 도메인별로 Factory 분리
```python
class UserFactory:
    @staticmethod
    def create(**kwargs):
        return User(**kwargs)

class ProductFactory:
    @staticmethod
    def create(**kwargs):
        return Product(**kwargs)

class OrderFactory:
    @staticmethod
    def create(**kwargs):
        return Order(**kwargs)
```

### 8.3 타입 힌팅 무시

❌ **잘못된 예**: 반환 타입 명시 안 함
```python
def create_payment(payment_type):  # 타입 힌팅 없음
    return payment_types[payment_type]()
```

✅ **올바른 예**: Protocol로 타입 명시
```python
from typing import Protocol

class Payment(Protocol):
    def pay(self, amount: float) -> str: ...

def create_payment(payment_type: str) -> Payment:
    return payment_types[payment_type]()
```

---

## 9. 성능 고려사항

### 9.1 Lazy Initialization

객체 생성 비용이 클 때는 지연 초기화를 고려하세요:

```python
class DatabaseFactory:
    _instances = {}  # 캐싱

    @classmethod
    def create(cls, db_type: str, **config) -> DatabaseConnection:
        # 캐시 키 생성
        cache_key = f"{db_type}:{config.get('host', '')}:{config.get('port', '')}"

        # 이미 생성된 인스턴스 재사용
        if cache_key not in cls._instances:
            # 최초 생성 시에만 인스턴스 생성
            if db_type == "mysql":
                cls._instances[cache_key] = MySQLConnection(**config)
            elif db_type == "postgresql":
                cls._instances[cache_key] = PostgreSQLConnection(**config)

        return cls._instances[cache_key]
```

### 9.2 딕셔너리 vs if-elif 성능

```python
import timeit

# if-elif 방식
def factory_if(payment_type: str):
    if payment_type == "card":
        return CardPayment()
    elif payment_type == "bank":
        return BankTransfer()
    # ... 10개 타입

# 딕셔너리 방식
payment_map = {
    "card": CardPayment,
    "bank": BankTransfer,
    # ... 10개 타입
}

def factory_dict(payment_type: str):
    return payment_map[payment_type]()

# 벤치마크
print(timeit.timeit(lambda: factory_if("card"), number=100000))      # 느림
print(timeit.timeit(lambda: factory_dict("card"), number=100000))    # 빠름
```

**결과**: 딕셔너리 방식이 약 2-3배 빠름 (타입이 많을수록 차이 커짐)

---

## 10. 면접 대비 핵심 문장

1. **Factory 패턴은 객체 생성 로직을 캡슐화하여 클라이언트 코드와 구체 클래스를 분리합니다.**

2. **Simple Factory는 하나의 메서드, Factory Method는 서브클래스, Abstract Factory는 관련 객체군을 생성합니다.**

3. **Python은 Duck typing 덕분에 Java보다 간결하게 Factory를 구현할 수 있으며, 함수만으로도 가능합니다.**

4. **딕셔너리 맵핑 방식이 if-elif보다 성능이 좋고 확장 가능합니다.**

5. **Factory 패턴은 Open-Closed Principle (OCP)을 따릅니다: 확장에는 열려있고, 수정에는 닫혀있습니다.**

6. **Django의 뷰, FastAPI의 의존성 주입, 데이터베이스 연결 등 실무에서 광범위하게 사용됩니다.**

7. **과도한 Factory 사용은 오히려 복잡도를 높이므로, 생성 로직이 복잡하거나 확장 가능성이 있을 때만 사용합니다.**

---

## 11. 학습 순서

1. **Simple Factory** (1-2일)
   - 기본 개념 이해
   - if-elif vs 딕셔너리 비교
   - 실습: 결제 시스템 만들기

2. **Factory Method** (2-3일)
   - 서브클래스가 결정하는 개념
   - Template Method와의 관계
   - 실습: 문서 생성기 만들기

3. **Abstract Factory** (3-4일)
   - 객체군 생성 이해
   - UI 테마 시스템 실습
   - 실습: 데이터베이스 드라이버 팩토리

4. **실무 적용** (1주)
   - Django/FastAPI 프로젝트에 적용
   - Strategy 패턴과 조합
   - 성능 최적화 (캐싱, Lazy Initialization)

---

## 12. 참고 자료

- **Python 공식 문서**: [Type Hints](https://docs.python.org/3/library/typing.html)
- **Design Patterns (GoF)**: Factory Method, Abstract Factory 챕터
- **Refactoring Guru**: [Factory Pattern](https://refactoring.guru/design-patterns/factory-method/python)
- **Real Python**: [Factory Method in Python](https://realpython.com/factory-method-python/)
