# Python의 __init__과 __all__

이름은 비슷한데 전혀 다른 두 가지: 하나는 Java 생성자, 하나는 public API 제어.

## 결론부터 말하면

| 항목 | `__init__` | `__all__` |
|------|-----------|----------|
| **정체** | 메서드 | 리스트 |
| **Java 대응** | 생성자 (Constructor) | `public` 키워드 역할 |
| **용도** | 객체 초기화 | 공개 API 정의 |
| **위치** | 클래스 안 | 모듈 최상위 |

```python
# __init__: Java 생성자와 동일
class Person:
    def __init__(self, name):  # Java: public Person(String name)
        self.name = name

# __all__: from module import * 할 때 공개할 이름
__all__ = ['Person', 'create_person']  # Java의 public 클래스/메서드만 노출하는 것과 유사
```

**완전히 다른 용도다!**

## 1. __init__ - 생성자 메서드

객체가 생성될 때 **자동으로 호출**되는 메서드입니다.

### 기본 사용법

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

person = Person("홍길동", 30)  # __init__ 자동 호출
print(person.name)  # 홍길동
```

### 기본값과 검증

```python
class BankAccount:
    def __init__(self, owner, balance=0):
        if balance < 0:
            raise ValueError("잔액은 0 이상이어야 합니다")

        self.owner = owner
        self.balance = balance

# 사용
account = BankAccount("홍길동", 10000)
# account = BankAccount("김철수", -100)  # ValueError!
```

### 부모 클래스 초기화

```python
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)  # 부모 __init__ 호출
        self.breed = breed

dog = Dog("뽀삐", "포메라니안")
print(dog.name)   # 뽀삐
print(dog.breed)  # 포메라니안
```

## 2. __all__ - 공개 API 정의

모듈에서 **공개할 이름들을 명시**하는 리스트입니다.

### 기본 사용법

```python
# calculator.py
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def _internal_helper():
    """내부 함수 (공개하지 않음)"""
    pass

# 공개 API만 지정
__all__ = ['add', 'subtract']
```

```python
# main.py
from calculator import *

print(add(5, 3))       # OK: 8
print(subtract(5, 3))  # OK: 2
# _internal_helper()   # NameError! __all__에 없음
```

### 명시적 import는 여전히 가능

```python
# __all__과 상관없이 명시적으로는 import 가능
from calculator import _internal_helper
_internal_helper()  # OK
```

### 패키지에서 사용

```python
# mypackage/__init__.py
from .user import User
from .account import Account

# 패키지 공개 API 지정
__all__ = ['User', 'Account']

__version__ = '1.0.0'
```

```python
# 사용
from mypackage import *
user = User("hong")     # OK
account = Account("홍")  # OK
```

## 3. 비교 정리

| 항목 | `__init__` | `__all__` |
|------|-----------|----------|
| **타입** | 메서드 | 리스트 |
| **위치** | 클래스 안 | 모듈 최상위 |
| **용도** | 객체 초기화 | 공개 API 정의 |
| **자동 실행** | 객체 생성 시 | 실행 안됨 |

## 4. 헷갈리는 포인트

### __init__.py 파일

디렉토리를 Python 패키지로 만드는 특수 파일입니다.

```
mypackage/
├── __init__.py      # 패키지 초기화
├── user.py
└── account.py
```

```python
# mypackage/__init__.py
"""패키지가 import될 때 실행됨"""

from .user import User
__all__ = ['User']
```

### __init__ vs __new__

```python
class MyClass:
    def __new__(cls):
        print("1. __new__ 실행 (객체 생성)")
        return super().__new__(cls)

    def __init__(self):
        print("2. __init__ 실행 (객체 초기화)")

obj = MyClass()
# 출력:
# 1. __new__ 실행 (객체 생성)
# 2. __init__ 실행 (객체 초기화)
```

**일반적으로 `__init__`만 사용합니다.**

### __all__ 없이 import *를 쓰면?

```python
# module.py
def public():
    pass

def _private():  # _로 시작
    pass

# __all__ 없음
```

```python
from module import *

public()    # OK
# _private()  # NameError! (_로 시작하면 import 안됨)
```

**`__all__`이 없으면 `_`로 시작하지 않는 모든 이름이 import됩니다.**

## 요약

### __init__ 핵심

```python
class Example:
    def __init__(self, value):
        # ✅ 인스턴스 변수 설정
        self.value = value

        # ✅ 검증
        if value < 0:
            raise ValueError()

        # ❌ 반환값 작성 금지 (None만 가능)
```

### __all__ 핵심

```python
# ✅ 공개 함수
def public():
    pass

# ❌ 내부 함수
def _private():
    pass

__all__ = ['public']  # 공개 API만 명시
```

## 참고 자료

- [Python Documentation - Classes](https://docs.python.org/3/tutorial/classes.html)
- [Python Documentation - Modules](https://docs.python.org/3/tutorial/modules.html)
- [PEP 8 - Module Level Dunder Names](https://pep8.org/#module-level-dunder-names)
