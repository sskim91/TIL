# Python 패키지의 __init__.py

패키지 디렉토리에 있는 `__init__.py` 파일에 대해 알아봅니다.

## 결론부터 말하면

`__init__.py`는 **디렉토리를 Python 패키지로 만들고**, 패키지가 import될 때 **자동으로 실행**되는 초기화 파일입니다.

## 1. 기본 개념

### 패키지 구조

```
myproject/
├── mypackage/
│   ├── __init__.py     # 이 파일이 있으면 패키지!
│   ├── module1.py
│   └── module2.py
└── main.py
```

### 가장 간단한 형태

```python
# mypackage/__init__.py
# 빈 파일이어도 OK
```

```python
# main.py
from mypackage import module1
from mypackage.module2 import some_function
```

## 2. 주요 역할

### 역할 1: 편리한 import 경로

**Before:**

```python
# 패키지 구조
mypackage/
├── __init__.py
├── models/
│   ├── user.py        # class User
│   └── product.py     # class Product

# 사용 - 불편함
from mypackage.models.user import User
from mypackage.models.product import Product
```

**After:**

```python
# mypackage/__init__.py
from .models.user import User
from .models.product import Product

__all__ = ['User', 'Product']
```

```python
# 사용 - 편리함!
from mypackage import User, Product
```

### 역할 2: 패키지 초기화

```python
# mypackage/__init__.py
print("mypackage가 로드되었습니다!")

# 패키지 레벨 변수
__version__ = '1.0.0'
__author__ = 'Your Name'

# 설정 초기화
_config = {'debug': False}

def configure(**kwargs):
    _config.update(kwargs)
```

```python
# 사용
import mypackage  # "mypackage가 로드되었습니다!" 출력

print(mypackage.__version__)  # "1.0.0"
mypackage.configure(debug=True)
```

### 역할 3: 공개 API 제어

```python
# mypackage/__init__.py
from .api import get, post
from .models import User
from ._internal import _helper  # 내부용

# 공개 API만 명시
__all__ = ['get', 'post', 'User']
```

```python
from mypackage import *

get()   # OK
post()  # OK
User()  # OK
# _helper()  # NameError! __all__에 없음
```

## 3. 실전 예시

### 예시 1: HTTP 라이브러리 (requests 스타일)

```python
# requests/__init__.py
"""HTTP 라이브러리"""

__version__ = '2.31.0'

from .api import request, get, post, put, delete
from .models import Response
from .exceptions import RequestException, HTTPError

__all__ = [
    'request', 'get', 'post', 'put', 'delete',
    'Response', 'RequestException', 'HTTPError'
]
```

```python
# 사용 - 매우 간단!
import requests

response = requests.get('https://api.example.com')
```

### 예시 2: 데이터베이스 패키지

```python
# mydb/__init__.py
from .connection import connect, Connection
from .models import Model

# 기본 설정
_config = {
    'host': 'localhost',
    'port': 5432
}

def configure(**kwargs):
    """데이터베이스 설정"""
    _config.update(kwargs)

def get_config():
    """현재 설정 조회"""
    return _config.copy()

__all__ = ['connect', 'Connection', 'Model', 'configure']
__version__ = '1.0.0'
```

```python
# 사용
import mydb

mydb.configure(host='db.example.com', port=3306)
conn = mydb.connect()
```

### 예시 3: 계층적 패키지

```
myapp/
├── __init__.py
├── core/
│   ├── __init__.py
│   └── config.py
└── api/
    ├── __init__.py
    ├── v1/
    │   ├── __init__.py
    │   └── endpoints.py
    └── v2/
        ├── __init__.py
        └── endpoints.py
```

```python
# myapp/__init__.py
from .core import config
from .api import v1, v2

__version__ = '1.0.0'
__all__ = ['config', 'v1', 'v2']
```

```python
# myapp/api/__init__.py
from . import v1
from . import v2

__all__ = ['v1', 'v2']
```

```python
# 사용
from myapp import v1, v2, config

v1_response = v1.get_users()
v2_response = v2.get_users()
```

## 4. 자동 플러그인 로딩

```python
# plugins/__init__.py
"""플러그인을 자동으로 발견하고 등록"""

import os
import importlib

_plugins = {}

def register_plugin(name, plugin_class):
    """플러그인 등록"""
    _plugins[name] = plugin_class

def get_plugin(name):
    """플러그인 조회"""
    return _plugins.get(name)

# 패키지 로드 시 모든 플러그인 자동 로딩
plugin_dir = os.path.dirname(__file__)
for filename in os.listdir(plugin_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]
        importlib.import_module(f'.{module_name}', package=__package__)

__all__ = ['register_plugin', 'get_plugin']
```

## 5. Python 3.3+ Namespace Package

`__init__.py` **없이도** 패키지 사용 가능합니다 (Python 3.3+):

```
myproject/
├── namespace_pkg/    # __init__.py 없음!
│   └── module.py
└── main.py
```

```python
# main.py
from namespace_pkg import module  # 동작함!
```

### 그럼 언제 __init__.py를 사용하나?

| 상황 | __init__.py 필요? |
|------|------------------|
| 초기화 코드 실행 | ✅ 필요 |
| 편리한 import 제공 | ✅ 필요 |
| 공개 API 제어 | ✅ 필요 |
| 단순 네임스페이스만 | ❌ 불필요 (Python 3.3+) |
| Python 2.7 지원 | ✅ 필수 |

## 6. 주의사항

### 순환 import 주의

```python
# mypackage/__init__.py
from .module_a import ClassA  # ❌
```

```python
# mypackage/module_a.py
from mypackage import ClassB  # ❌ 순환 import 발생!
```

**해결책 1: Lazy Import**

```python
# mypackage/__init__.py
def get_class_a():
    from .module_a import ClassA
    return ClassA
```

**해결책 2: 상대 import**

```python
# mypackage/module_a.py
from .module_b import ClassB  # ✅
```

### 무거운 작업은 피하기

```python
# ❌ 나쁜 예
import time

# 패키지 로드할 때마다 5초 걸림
time.sleep(5)
expensive_data = load_big_database()
```

```python
# ✅ 좋은 예 - Lazy Loading
_cache = None

def get_data():
    """필요할 때만 로드"""
    global _cache
    if _cache is None:
        _cache = load_big_database()
    return _cache
```

## 7. 실무 패턴

### 패턴 1: 미니멀 패키지

```python
# mypackage/__init__.py
"""간단한 유틸리티 패키지"""

from .utils import helper_function
from .core import MainClass

__version__ = '1.0.0'
__all__ = ['helper_function', 'MainClass']
```

### 패턴 2: 설정 가능한 패키지

```python
# mypackage/__init__.py
from .core import Engine

# 기본 설정
_default_config = {
    'timeout': 30,
    'retries': 3
}

class Config:
    def __init__(self):
        self.settings = _default_config.copy()

    def update(self, **kwargs):
        self.settings.update(kwargs)

config = Config()

__all__ = ['Engine', 'config']
__version__ = '1.0.0'
```

```python
# 사용
import mypackage

mypackage.config.update(timeout=60)
engine = mypackage.Engine()
```

### 패턴 3: 조건부 import

```python
# mypackage/__init__.py
import sys

__version__ = '1.0.0'

# Python 버전에 따라 다른 모듈 사용
if sys.version_info >= (3, 8):
    from .modern import new_feature
else:
    from .legacy import new_feature

__all__ = ['new_feature']
```

## 8. 비교: __init__.py vs __init__

| 항목 | `__init__.py` (파일) | `__init__` (메서드) |
|------|---------------------|-------------------|
| **위치** | 패키지 디렉토리 | 클래스 내부 |
| **용도** | 패키지 초기화 | 객체 초기화 |
| **실행 시점** | 패키지 import 시 | 객체 생성 시 |
| **예시** | `import mypackage` | `obj = MyClass()` |

## 요약

### __init__.py의 역할

```python
# mypackage/__init__.py

# 1️⃣ 버전 정보
__version__ = '1.0.0'

# 2️⃣ 편리한 import
from .models import User, Product

# 3️⃣ 공개 API 정의
__all__ = ['User', 'Product']

# 4️⃣ 초기화 코드
_config = {}

def configure(**kwargs):
    _config.update(kwargs)
```

### 빠른 참조

| 궁금한 것 | 답 |
|---------|-----|
| 빈 파일도 되나요? | ✅ 가능 (패키지 표시 역할만) |
| 없어도 되나요? | Python 3.3+에서는 가능 (하지만 권장 X) |
| 언제 실행되나요? | 패키지를 처음 import할 때 |
| 여러 번 실행되나요? | ❌ 한 번만 (캐시됨) |
| 순환 import 주의 | ✅ 상대 import나 lazy loading 사용 |

### 권장 사항

```python
# ✅ 좋은 __init__.py
# - 버전 정보 포함
# - 핵심 API만 노출
# - 가볍게 유지
# - 명확한 __all__ 정의

__version__ = '1.0.0'

from .core import MainClass
from .utils import helper

__all__ = ['MainClass', 'helper']
```

## 참고 자료

- [Python Documentation - Packages](https://docs.python.org/3/tutorial/modules.html#packages)
- [PEP 420 - Implicit Namespace Packages](https://www.python.org/dev/peps/pep-0420/)
- [Real Python - Python Modules and Packages](https://realpython.com/python-modules-packages/)
