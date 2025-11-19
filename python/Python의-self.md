# Python의 self

Python 클래스에서 사용하는 `self`에 대해 알아봅니다.

## 결론부터 말하면

`self`는 **인스턴스 자기 자신**을 가리키는 참조입니다. (Java의 `this`와 동일)

## 1. self의 기본 개념

`self`는 "이 객체 자신"을 의미합니다.

```python
class Dog:
    def __init__(self, name):
        self.name = name  # 이 개의 이름

    def bark(self):
        print(f"{self.name}가 짖습니다!")

# 사용
my_dog = Dog("뽀삐")
my_dog.bark()  # "뽀삐가 짖습니다!"

your_dog = Dog("멍멍이")
your_dog.bark()  # "멍멍이가 짖습니다!"
```

**각 객체는 자신만의 데이터를 가집니다.**

## 2. Python이 자동으로 전달

```python
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1

counter = Counter()

# 우리가 쓰는 코드
counter.increment()

# Python이 실제로 하는 일
Counter.increment(counter)  # counter 객체를 self로 자동 전달
```

**핵심:** 메서드 호출 시 Python이 자동으로 객체 자신을 첫 번째 인자로 전달합니다.

## 3. Java의 this와 비교

### Java (암묵적)

```java
public class Dog {
    private String name;

    public Dog(String name) {
        this.name = name;  // this는 생략 가능
    }

    public void bark() {
        System.out.println(name + " barks!");  // this 생략
    }
}
```

### Python (명시적)

```python
class Dog:
    def __init__(self, name):
        self.name = name  # self는 필수

    def bark(self):
        print(f"{self.name} barks!")  # self 생략 불가
```

### 핵심 차이

| 언어 | 방식 | 특징 |
|------|------|------|
| **Java** | 암묵적 | `this` 생략 가능, 컴파일러가 자동 추론 |
| **Python** | 명시적 | `self` 반드시 명시 |

**Python의 철학:**
> "Explicit is better than implicit" (명시적인 것이 암묵적인 것보다 낫다)

## 4. 인스턴스 변수 vs 지역 변수

```python
class Student:
    def __init__(self, name, score):
        self.name = name      # 인스턴스 변수 (객체에 저장)
        self.score = score

    def study(self, hours):
        improvement = hours * 5  # 지역 변수 (함수 끝나면 사라짐)
        self.score += improvement

        # self 없으면 지역 변수
        temp_message = f"{hours}시간 공부!"
        print(temp_message)

        # self 있으면 인스턴스 변수
        self.last_study_hours = hours

student = Student("홍길동", 70)
student.study(3)

print(student.score)            # 85 (인스턴스 변수, 유지됨)
print(student.last_study_hours) # 3 (인스턴스 변수, 유지됨)
# print(student.improvement)    # AttributeError! (지역 변수, 사라짐)
```

**핵심:**
- `self.` 붙이면 → 인스턴스 변수 (객체에 저장, 유지됨)
- `self.` 없으면 → 지역 변수 (함수 끝나면 사라짐)

## 5. 실전 예시: 은행 계좌

```python
class BankAccount:
    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance
        self.transactions = []

    def deposit(self, amount):
        self.balance += amount
        self.transactions.append(f"+{amount}")
        print(f"{self.owner}님: {amount}원 입금 완료")

    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.transactions.append(f"-{amount}")
            print(f"{self.owner}님: {amount}원 출금 완료")
        else:
            print(f"{self.owner}님: 잔액 부족 (현재: {self.balance}원)")

    def get_statement(self):
        print(f"\n=== {self.owner}님 계좌 ===")
        print(f"잔액: {self.balance}원")
        print(f"거래내역: {', '.join(self.transactions)}")

# 각각 독립적인 계좌
account1 = BankAccount("홍길동", 10000)
account2 = BankAccount("김철수", 5000)

account1.deposit(5000)
account2.withdraw(2000)

account1.get_statement()
# === 홍길동님 계좌 ===
# 잔액: 15000원
# 거래내역: +5000

account2.get_statement()
# === 김철수님 계좌 ===
# 잔액: 3000원
# 거래내역: -2000
```

## 6. self는 이름일 뿐 (하지만 관례!)

```python
# ✅ 권장 (관례)
class MyClass:
    def method(self):
        self.value = 10

# ⚠️ 가능하지만 절대 비추천
class MyClass:
    def method(this):  # Java 스타일
        this.value = 10

    def method2(me):
        me.value = 20
```

**관례를 따르세요!** 모든 Python 개발자가 `self`를 기대합니다.

## 7. 메서드 체이닝 패턴

`self`를 반환하면 메서드를 연속으로 호출할 수 있습니다.

```python
class QueryBuilder:
    def __init__(self):
        self.query = ""

    def select(self, fields):
        self.query += f"SELECT {fields} "
        return self  # self 반환!

    def from_table(self, table):
        self.query += f"FROM {table} "
        return self

    def where(self, condition):
        self.query += f"WHERE {condition} "
        return self

    def build(self):
        return self.query.strip()

# 메서드 체이닝
query = (QueryBuilder()
         .select("name, age")
         .from_table("users")
         .where("age > 18")
         .build())

print(query)
# SELECT name, age FROM users WHERE age > 18
```

## 8. 상속에서의 self

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return f"{self.name}이(가) 소리냅니다"

class Dog(Animal):
    def speak(self):
        return f"{self.name}이(가) 멍멍!"

# self는 실제 인스턴스 타입을 따름
dog = Dog("뽀삐")
print(dog.speak())  # 뽀삐이(가) 멍멍! (Dog의 speak 호출)
```

## 9. 실전 팁

### Tip 1: __init__에서 검증

```python
class Person:
    def __init__(self, name, age):
        self.name = self._validate_name(name)
        self.age = self._validate_age(age)

    def _validate_name(self, name):
        """private 메서드 (관례상 _로 시작)"""
        if not name or len(name) < 2:
            raise ValueError("이름은 2글자 이상이어야 합니다")
        return name

    def _validate_age(self, age):
        if age < 0 or age > 150:
            raise ValueError("유효하지 않은 나이입니다")
        return age

# 사용
person = Person("홍길동", 30)  # OK
# person = Person("홍", 30)    # ValueError!
```

### Tip 2: Property 사용

```python
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("절대 영도 이하는 불가능합니다")
        self._celsius = value

    @property
    def fahrenheit(self):
        return self._celsius * 9/5 + 32

temp = Temperature(25)
print(temp.celsius)     # 25
print(temp.fahrenheit)  # 77.0

temp.celsius = 30       # setter 호출
print(temp.fahrenheit)  # 86.0
```

## 요약 정리

| 항목 | 설명 |
|------|------|
| **의미** | 인스턴스 자신을 가리키는 참조 |
| **위치** | 인스턴스 메서드의 첫 번째 파라미터 |
| **자동 전달** | Python이 자동으로 전달 (호출 시 신경 쓸 필요 없음) |
| **명시성** | Java와 달리 명시적으로 작성 필수 |
| **관례** | `self`라는 이름 사용 (필수 아님, 하지만 강력한 관례) |

**기억할 것:**
- `self` = "나 자신" (this object)
- Java의 `this`와 동일하지만 명시적으로 작성
- 인스턴스 변수/메서드 접근 시 반드시 `self.` 사용
- Python이 자동으로 전달하므로 호출 시 신경 쓸 필요 없음

## 참고 자료

- [Python Documentation - Classes](https://docs.python.org/3/tutorial/classes.html)
- [PEP 8 - Style Guide](https://pep8.org/#function-and-method-arguments)
- [Real Python - Instance, Class, and Static Methods](https://realpython.com/instance-class-and-static-methods-demystified/)
