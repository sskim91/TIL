# Python f-string 완전 정복

Python 3.6+에서 사용하는 f-string (formatted string literals)에 대해 알아봅니다.

## 결론부터 말하면

f-string은 **가장 빠르고 읽기 쉬운** 문자열 포매팅 방법입니다.

```python
name = "홍길동"
age = 30

# f-string (권장)
f"이름: {name}, 나이: {age}"  # "이름: 홍길동, 나이: 30"

# 다른 방법들 (구식)
"이름: %s, 나이: %d" % (name, age)           # % 포매팅
"이름: {}, 나이: {}".format(name, age)       # .format()
"이름: " + name + ", 나이: " + str(age)      # 문자열 연결
```

## 1. 기본 사용법

### 변수 삽입

```python
name = "홍길동"
city = "서울"

# f-string
message = f"{name}님은 {city}에 삽니다"
print(message)  # "홍길동님은 서울에 삽니다"

# 여러 줄
text = f"""
이름: {name}
도시: {city}
"""
```

### 표현식 사용

```python
a = 10
b = 20

# 계산
print(f"{a} + {b} = {a + b}")  # "10 + 20 = 30"

# 함수 호출
print(f"대문자: {name.upper()}")  # "대문자: 홍길동"

# 메서드 체이닝
text = "  hello  "
print(f"정리: '{text.strip().upper()}'")  # "정리: 'HELLO'"
```

### 조건식

```python
score = 85
result = f"{'합격' if score >= 60 else '불합격'}"
print(result)  # "합격"

# 복잡한 표현식
age = 15
status = f"{'성인' if age >= 18 else '미성년자'} ({age}세)"
print(status)  # "미성년자 (15세)"
```

## 2. 포매팅 옵션

### 숫자 포매팅

```python
number = 1234567.89

# 천 단위 구분자
print(f"{number:,}")           # "1,234,567.89"

# 소수점 자리수
print(f"{number:.2f}")         # "1234567.89"
print(f"{number:,.2f}")        # "1,234,567.89"

# 퍼센트
rate = 0.856
print(f"{rate:.1%}")           # "85.6%"

# 지수 표기
print(f"{number:.2e}")         # "1.23e+06"
```

### 정렬과 패딩

```python
text = "Python"

# 왼쪽 정렬 (기본)
print(f"{text:<10}|")          # "Python    |"

# 오른쪽 정렬
print(f"{text:>10}|")          # "    Python|"

# 가운데 정렬
print(f"{text:^10}|")          # "  Python  |"

# 특정 문자로 채우기
print(f"{text:*<10}")          # "Python****"
print(f"{text:->10}")          # "----Python"
print(f"{text:=^10}")          # "==Python=="
```

### 숫자 정렬과 부호

```python
numbers = [42, -17, 100, -5]

for num in numbers:
    # 오른쪽 정렬, 5자리
    print(f"{num:5d}")
# 출력:
#    42
#   -17
#   100
#    -5

# 부호 표시
positive = 42
print(f"{positive:+d}")        # "+42"
print(f"{positive: d}")        # " 42" (양수는 공백)

# 0으로 패딩
num = 42
print(f"{num:05d}")            # "00042"
```

## 3. 변환 지정자: !s, !r, !a

### !s (str)

```python
class Person:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Person: {self.name}"

person = Person("홍길동")

print(f"{person}")             # "Person: 홍길동"
print(f"{person!s}")           # "Person: 홍길동" (동일)

# 예외 메시지
try:
    1 / 0
except Exception as e:
    print(f"오류: {e!s}")      # "오류: division by zero"
```

### !r (repr) - 디버깅용

```python
text = "Hello\nWorld"

print(f"{text!s}")             # Hello
                               # World (실제 줄바꿈)

print(f"{text!r}")             # 'Hello\nWorld' (이스케이프 문자 보임)

# 문자열 디버깅
name = "홍길동"
print(f"{name!s}")             # 홍길동
print(f"{name!r}")             # '홍길동' (따옴표 포함)

# None, 숫자 등
value = None
print(f"값: {value!r}")        # "값: None"
```

### !a (ascii)

```python
text = "안녕하세요 😀"

print(f"{text!s}")             # "안녕하세요 😀"
print(f"{text!a}")             # "'\uc548\ub155\ud558\uc138\uc694 \U0001f600'"

# ASCII만 포함된 로그 파일 생성 시 유용
```

### 비교: str() vs !s

```python
exception = ValueError("잘못된 값")

# ❌ 불필요한 함수 호출 (RUFF가 지적)
f"오류: {str(exception)}"

# ✅ 더 간결 (RUFF 권장)
f"오류: {exception!s}"

# ✅ 가장 간단 (일반적으로 충분)
f"오류: {exception}"
```

## 4. 중괄호 이스케이프

```python
# 중괄호를 문자로 사용하려면 두 번 써야 함
print(f"{{중괄호}}")           # "{중괄호}"
print(f"{{{{이중}}}}")         # "{{이중}}"

# 변수와 섞어서
value = 42
print(f"값 = {{{value}}}")     # "값 = {42}"
```

## 5. 딕셔너리와 함께 사용

```python
user = {"name": "홍길동", "age": 30, "city": "서울"}

# 기본
print(f"이름: {user['name']}")  # "이름: 홍길동"

# 여러 값
print(f"{user['name']}({user['age']}세)는 {user['city']}에 삽니다")
# "홍길동(30세)는 서울에 삽니다"

# ** unpacking (변수명이 키와 같을 때)
name = user["name"]
age = user["age"]
print(f"{name}님은 {age}세입니다")
```

## 6. 날짜/시간 포매팅

```python
from datetime import datetime

now = datetime.now()

# 기본
print(f"현재: {now}")
# "현재: 2025-01-11 14:30:45.123456"

# 커스텀 포맷
print(f"{now:%Y-%m-%d}")                    # "2025-01-11"
print(f"{now:%Y년 %m월 %d일}")              # "2025년 01월 11일"
print(f"{now:%H:%M:%S}")                    # "14:30:45"
print(f"{now:%Y-%m-%d %H:%M:%S}")           # "2025-01-11 14:30:45"

# 요일
print(f"{now:%A}")                          # "Saturday"
print(f"{now:%a}")                          # "Sat"
```

## 7. 실전 예시

### 테이블 출력

```python
products = [
    {"name": "노트북", "price": 1200000, "stock": 5},
    {"name": "마우스", "price": 35000, "stock": 150},
    {"name": "키보드", "price": 89000, "stock": 42},
]

# 헤더
print(f"{'상품명':<10} {'가격':>10} {'재고':>5}")
print("-" * 30)

# 데이터
for p in products:
    print(f"{p['name']:<10} {p['price']:>10,}원 {p['stock']:>5}개")

# 출력:
# 상품명            가격    재고
# ------------------------------
# 노트북       1,200,000원     5개
# 마우스          35,000원   150개
# 키보드          89,000원    42개
```

### 진행률 표시

```python
def show_progress(current, total):
    percent = current / total
    bar_length = 20
    filled = int(bar_length * percent)
    bar = "█" * filled + "░" * (bar_length - filled)

    return f"[{bar}] {percent:.1%} ({current}/{total})"

print(show_progress(30, 100))
# [██████░░░░░░░░░░░░░░] 30.0% (30/100)

print(show_progress(75, 100))
# [███████████████░░░░░] 75.0% (75/100)
```

### 로그 메시지

```python
import logging
from datetime import datetime

def log(level, message, **context):
    timestamp = datetime.now()
    ctx = ", ".join(f"{k}={v!r}" for k, v in context.items())
    log_msg = f"[{timestamp:%Y-%m-%d %H:%M:%S}] {level:8} | {message}"
    if ctx:
        log_msg += f" | {ctx}"
    print(log_msg)

log("INFO", "서버 시작")
# [2025-01-11 14:30:45] INFO     | 서버 시작

log("ERROR", "DB 연결 실패", host="localhost", port=5432, retry=3)
# [2025-01-11 14:30:45] ERROR    | DB 연결 실패 | host='localhost', port=5432, retry=3
```

### 금액 표시

```python
def format_money(amount):
    return f"{amount:,}원"

def format_card_number(number):
    # 카드번호: 1234-5678-9012-3456
    return f"{number[0:4]}-{number[4:8]}-{number[8:12]}-{number[12:16]}"

print(format_money(1234567))              # "1,234,567원"
print(format_card_number("1234567890123456"))
# "1234-5678-9012-3456"
```

## 8. 성능 비교

```python
name = "홍길동"
age = 30

# 1. f-string (가장 빠름)
f"{name}님은 {age}세입니다"

# 2. .format() (중간)
"{}님은 {}세입니다".format(name, age)

# 3. % 포매팅 (느림)
"%s님은 %d세입니다" % (name, age)

# 4. 문자열 연결 (가장 느림)
name + "님은 " + str(age) + "세입니다"
```

**f-string이 가장 빠르고 읽기 쉽습니다!**

## 9. 고급 기법

### 중첩된 포매팅

```python
width = 10
precision = 2
value = 12.34567

# 동적 width와 precision
print(f"{value:{width}.{precision}f}")  # "     12.35"

# 동적 정렬
align = "^"
print(f"{'Python':{align}{width}}")     # "  Python  "
```

### 딕셔너리 키 접근

```python
data = {
    "user": {
        "name": "홍길동",
        "profile": {
            "age": 30,
            "city": "서울"
        }
    }
}

# 중첩된 딕셔너리
print(f"{data['user']['profile']['city']}")  # "서울"
```

### 표현식 디버깅 (Python 3.8+)

```python
x = 10
y = 20

# = 를 붙이면 변수명과 값을 모두 출력
print(f"{x=}")              # "x=10"
print(f"{y=}")              # "y=20"
print(f"{x + y=}")          # "x + y=30"

# 함수 호출
def square(n):
    return n ** 2

print(f"{square(5)=}")      # "square(5)=25"

# 포매팅과 함께
print(f"{x=:5d}")           # "x=   10"
```

## 10. 주의사항

### 백슬래시 사용 불가

```python
# ❌ f-string 내부에서 백슬래시 직접 사용 불가
# print(f"{'\n'.join(items)}")  # SyntaxError!

# ✅ 미리 변수에 할당
items = ["a", "b", "c"]
newline = "\n"
print(f"{newline.join(items)}")

# ✅ 또는 f-string 밖에서 처리
print("\n".join(items))
```

### 주석 사용 불가

```python
value = 42

# ❌ f-string 내부에 주석 불가
# print(f"{value # 이 값}")  # SyntaxError!

# ✅ f-string 밖에 주석
# 이 값은 중요합니다
print(f"{value}")
```

## 요약 정리

### 기본 문법

```python
name = "홍길동"
age = 30

f"{name}"                    # 변수
f"{name.upper()}"            # 메서드 호출
f"{age + 10}"                # 표현식
f"{'성인' if age >= 18 else '미성년자'}"  # 조건식
```

### 포매팅

```python
number = 1234567.89

f"{number:,}"                # 1,234,567.89 (천 단위)
f"{number:.2f}"              # 1234567.89 (소수점 2자리)
f"{number:,.2f}"             # 1,234,567.89 (조합)

text = "Python"
f"{text:<10}"                # 왼쪽 정렬
f"{text:>10}"                # 오른쪽 정렬
f"{text:^10}"                # 가운데 정렬
```

### 변환 지정자

```python
value = "Hello\nWorld"

f"{value}"                   # 일반 (str)
f"{value!s}"                 # str() 명시적
f"{value!r}"                 # repr() - 디버깅용
f"{value!a}"                 # ascii() - ASCII 변환
```

### 디버깅 (Python 3.8+)

```python
x = 10
f"{x=}"                      # "x=10"
f"{x + 5=}"                  # "x + 5=15"
```

## 빠른 참조표

| 용도 | 예시 | 결과 |
|------|------|------|
| 기본 | `f"{name}"` | `홍길동` |
| 천 단위 | `f"{1234567:,}"` | `1,234,567` |
| 소수점 | `f"{3.14159:.2f}"` | `3.14` |
| 퍼센트 | `f"{0.856:.1%}"` | `85.6%` |
| 정렬 | `f"{'Hi':<5}"` | `Hi   ` |
| 날짜 | `f"{now:%Y-%m-%d}"` | `2025-01-11` |
| 디버깅 | `f"{x=}"` | `x=10` |

## 참고 자료

- [PEP 498 - Literal String Interpolation](https://www.python.org/dev/peps/pep-0498/)
- [Python Format Specification Mini-Language](https://docs.python.org/3/library/string.html#formatspec)
- [Real Python - Python f-strings](https://realpython.com/python-f-strings/)
