# Python의 @abstractmethod와 추상 클래스

Python에서 추상 클래스와 추상 메서드를 정의하는 방법에 대해 알아봅니다.

## 결론부터 말하면

Python의 **ABC**(Abstract Base Class)를 상속하고 `@abstractmethod` 데코레이터를 사용하면 추상 클래스를 만들 수 있습니다. Java의 `@Override`는 없으며, 구현 강제는 **런타임(인스턴스화 시)**에 검증됩니다.

```python
from abc import ABC, abstractmethod

# 추상 클래스 (ABC = Abstract Base Class, 장난 아님!)
class Animal(ABC):
    @abstractmethod
    def make_sound(self):
        pass

# 구현 클래스 (@Override 같은 거 없음, 그냥 구현하면 됨)
class Dog(Animal):  # 괄호 안에 부모 클래스!
    def make_sound(self):
        return "멍멍!"

dog = Dog()  # 정상 작동
```

## 1. ABC란? (Abstract Base Class)

**ABC**는 **Abstract Base Class**의 약자입니다. 정말로 ABC입니다!

```python
from abc import ABC, abstractmethod

# ABC: Abstract Base Class
# 추상 클래스를 만들기 위한 기본 클래스
class Shape(ABC):
    @abstractmethod
    def area(self):
        pass
```

### ABC를 사용하는 이유

```python
# ❌ ABC 없이 추상 클래스 시도
class Animal:
    def make_sound(self):
        raise NotImplementedError("서브클래스에서 구현해야 합니다")

# 문제: 인스턴스화가 가능함 (추상 클래스인데!)
animal = Animal()  # 에러 없음
animal.make_sound()  # 실행 시에만 에러 발생

# ✅ ABC 사용
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def make_sound(self):
        pass

# 인스턴스화 자체가 불가능!
try:
    animal = Animal()
except TypeError as e:
    print(e)
    # Can't instantiate abstract class Animal with abstract method make_sound
```

## 2. 상속 문법 (Java와 비교)

### Java의 상속

```java
// Java: extends 키워드 사용
abstract class Animal {
    abstract void makeSound();
}

class Dog extends Animal {  // extends!
    @Override
    void makeSound() {
        System.out.println("멍멍!");
    }
}
```

### Python의 상속

```python
from abc import ABC, abstractmethod

# Python: 괄호 안에 부모 클래스 이름
class Animal(ABC):  # (부모클래스)
    @abstractmethod
    def make_sound(self):
        pass

class Dog(Animal):  # (부모클래스) - extends 없음!
    def make_sound(self):
        return "멍멍!"

# 다중 상속도 가능
class FlyingDog(Animal, Flyable):  # 여러 부모 가능
    def make_sound(self):
        return "멍멍!"

    def fly(self):
        return "날아가는 강아지!"
```

### 상속 문법 비교

| 언어 | 상속 문법 | 예시 |
|------|----------|------|
| **Java** | `extends` 키워드 | `class Dog extends Animal` |
| **Python** | 괄호 안에 부모 클래스 | `class Dog(Animal)` |
| **다중 상속** | 인터페이스만 가능 | 여러 부모 클래스 가능 |

```python
# Python 상속 문법 정리
class Parent:
    pass

class Child(Parent):  # 단일 상속
    pass

class MultiChild(Parent1, Parent2):  # 다중 상속
    pass

# Java처럼 extends 키워드 없음!
# 괄호 안에 부모 클래스 이름을 넣으면 됨
```

## 3. Java와 Python 비교

### Java의 추상 클래스

```java
// 추상 클래스 정의
abstract class Animal {
    // 추상 메서드
    abstract void makeSound();
    abstract void move();

    // 일반 메서드
    void sleep() {
        System.out.println("zzz...");
    }
}

// 구현 클래스
class Dog extends Animal {  // extends 사용
    @Override  // 명시적으로 오버라이드 표시
    void makeSound() {
        System.out.println("멍멍!");
    }

    @Override
    void move() {
        System.out.println("네 발로 걷습니다");
    }
}

// 컴파일 타임에 검증
// makeSound()를 구현 안 하면 → 컴파일 에러!
```

### Python의 추상 클래스

```python
from abc import ABC, abstractmethod

# 추상 클래스 정의
class Animal(ABC):  # (부모클래스) 형태
    # 추상 메서드
    @abstractmethod
    def make_sound(self):
        pass

    @abstractmethod
    def move(self):
        pass

    # 일반 메서드
    def sleep(self):
        print("zzz...")

# 구현 클래스
class Dog(Animal):  # (부모클래스) 형태
    # @Override 같은 게 없음! 그냥 구현하면 됨
    def make_sound(self):
        print("멍멍!")

    def move(self):
        print("네 발로 걷습니다")

# 런타임에 검증
# make_sound()를 구현 안 하면 → 인스턴스화 시 TypeError!
```

### 주요 차이점

| 특징 | Java | Python |
|------|------|--------|
| **추상 클래스 선언** | `abstract class` 키워드 | `ABC` 상속 |
| **상속 문법** | `extends` 키워드 | `(부모클래스)` |
| **추상 메서드 선언** | `abstract` 키워드 | `@abstractmethod` 데코레이터 |
| **오버라이드 표시** | `@Override` 어노테이션 | **표시 없음** (그냥 구현) |
| **검증 시점** | **컴파일 타임** | **런타임** (인스턴스화 시) |
| **구현 안 할 시** | 컴파일 에러 | `TypeError` (인스턴스화 시) |
| **다중 상속** | 인터페이스로 가능 | 다중 상속 가능 |

## 4. 기본 사용법

### 추상 클래스 정의

```python
from abc import ABC, abstractmethod

class Vehicle(ABC):
    """교통수단 추상 클래스"""

    @abstractmethod
    def start(self):
        """시동 걸기 (필수 구현)"""
        pass

    @abstractmethod
    def stop(self):
        """정지하기 (필수 구현)"""
        pass

    # 일반 메서드 (선택적 오버라이드)
    def honk(self):
        """경적 울리기 (기본 구현 제공)"""
        print("빵빵!")
```

### 구현 클래스

```python
class Car(Vehicle):  # (부모클래스)
    def start(self):
        print("자동차 시동 걸림")

    def stop(self):
        print("자동차 정지")

    # honk()는 오버라이드 안 해도 됨 (기본 구현 사용)

car = Car()
car.start()  # "자동차 시동 걸림"
car.honk()   # "빵빵!"
```

### 구현 강제 확인

```python
# ❌ 추상 메서드 일부만 구현
class Bicycle(Vehicle):
    def start(self):
        print("자전거 페달 밟기")

    # stop() 구현 안 함!

# 인스턴스화 시도 → TypeError!
try:
    bike = Bicycle()
except TypeError as e:
    print(e)
    # Can't instantiate abstract class Bicycle with abstract method stop

# ✅ 모든 추상 메서드 구현
class Motorcycle(Vehicle):
    def start(self):
        print("오토바이 시동 걸림")

    def stop(self):
        print("오토바이 정지")

motorcycle = Motorcycle()  # 정상 작동!
```

## 5. 추상 메서드에 기본 구현 제공

Java와 달리 Python은 추상 메서드에도 기본 구현을 제공할 수 있습니다.

```python
from abc import ABC, abstractmethod

class Database(ABC):
    @abstractmethod
    def connect(self):
        """연결 (기본 구현 제공)"""
        print("연결 준비 중...")
        print("인증 확인 중...")
        return True

    @abstractmethod
    def disconnect(self):
        """연결 해제"""
        pass

class PostgreSQL(Database):
    def connect(self):
        # 부모의 기본 구현 호출 가능
        super().connect()
        print("PostgreSQL 연결 완료")

    def disconnect(self):
        print("PostgreSQL 연결 해제")

db = PostgreSQL()
db.connect()
# 출력:
# 연결 준비 중...
# 인증 확인 중...
# PostgreSQL 연결 완료
```

## 6. 추상 프로퍼티

프로퍼티도 추상으로 만들 수 있습니다.

```python
from abc import ABC, abstractmethod

class Person(ABC):
    @property
    @abstractmethod
    def name(self):
        """이름 (필수 구현)"""
        pass

    @property
    @abstractmethod
    def age(self):
        """나이 (필수 구현)"""
        pass

    @abstractmethod
    def introduce(self):
        """자기소개"""
        pass

class Student(Person):  # (부모클래스)
    def __init__(self, name, age, student_id):
        self._name = name
        self._age = age
        self.student_id = student_id

    @property
    def name(self):
        return self._name

    @property
    def age(self):
        return self._age

    def introduce(self):
        return f"안녕하세요, {self.name}입니다. {self.age}살 학생입니다."

student = Student("홍길동", 20, "2024001")
print(student.name)        # "홍길동"
print(student.age)         # 20
print(student.introduce()) # "안녕하세요, 홍길동입니다. 20살 학생입니다."
```

## 7. 추상 클래스 메서드와 정적 메서드

```python
from abc import ABC, abstractmethod

class MathOperation(ABC):
    @classmethod
    @abstractmethod
    def create(cls, *args):
        """팩토리 메서드 (클래스 메서드)"""
        pass

    @staticmethod
    @abstractmethod
    def validate(value):
        """유효성 검사 (정적 메서드)"""
        pass

    @abstractmethod
    def calculate(self):
        """계산 (인스턴스 메서드)"""
        pass

class Addition(MathOperation):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    @classmethod
    def create(cls, *args):
        if len(args) != 2:
            raise ValueError("두 개의 숫자가 필요합니다")
        return cls(*args)

    @staticmethod
    def validate(value):
        if not isinstance(value, (int, float)):
            raise TypeError("숫자만 가능합니다")
        return True

    def calculate(self):
        return self.a + self.b

# 사용
add = Addition.create(10, 20)
Addition.validate(10)
print(add.calculate())  # 30
```

## 8. 다중 상속

Python은 다중 상속을 지원하므로 여러 추상 클래스를 동시에 상속할 수 있습니다.

```python
from abc import ABC, abstractmethod

class Flyable(ABC):
    @abstractmethod
    def fly(self):
        pass

class Swimmable(ABC):
    @abstractmethod
    def swim(self):
        pass

# 다중 상속: (부모1, 부모2, ...)
class Duck(Flyable, Swimmable):
    def fly(self):
        print("오리가 날아갑니다")

    def swim(self):
        print("오리가 헤엄칩니다")

duck = Duck()
duck.fly()   # "오리가 날아갑니다"
duck.swim()  # "오리가 헤엄칩니다"
```

## 9. 간단한 실전 예제

### 도형 계산

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    """도형 추상 클래스"""

    @abstractmethod
    def area(self):
        """넓이 계산"""
        pass

    @abstractmethod
    def perimeter(self):
        """둘레 계산"""
        pass

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14159 * self.radius ** 2

    def perimeter(self):
        return 2 * 3.14159 * self.radius

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

# 사용
circle = Circle(5)
print(f"원 넓이: {circle.area():.2f}")      # 78.54
print(f"원 둘레: {circle.perimeter():.2f}")  # 31.42

rect = Rectangle(10, 5)
print(f"사각형 넓이: {rect.area()}")        # 50
print(f"사각형 둘레: {rect.perimeter()}")    # 30
```

### 동물 소리

```python
from abc import ABC, abstractmethod

class Animal(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def make_sound(self):
        """동물 소리"""
        pass

    def introduce(self):
        """자기소개 (기본 구현)"""
        sound = self.make_sound()
        return f"저는 {self.name}입니다. {sound}"

class Dog(Animal):
    def make_sound(self):
        return "멍멍!"

class Cat(Animal):
    def make_sound(self):
        return "야옹~"

class Cow(Animal):
    def make_sound(self):
        return "음메~"

# 사용
animals = [
    Dog("바둑이"),
    Cat("나비"),
    Cow("얼룩이")
]

for animal in animals:
    print(animal.introduce())
# 출력:
# 저는 바둑이입니다. 멍멍!
# 저는 나비입니다. 야옹~
# 저는 얼룩이입니다. 음메~
```

## 10. 주의사항

### 1. 런타임 검증

```python
# 클래스 정의 시점에는 에러 없음
class BadDog(Animal):
    pass  # make_sound() 구현 안 함

# 인스턴스화할 때 비로소 에러!
try:
    dog = BadDog("바둑이")
except TypeError as e:
    print(e)
    # Can't instantiate abstract class BadDog with abstract method make_sound
```

### 2. 추상 클래스 인스턴스화 불가

```python
from abc import ABC, abstractmethod

class Base(ABC):
    @abstractmethod
    def method(self):
        pass

# ❌ 추상 클래스는 인스턴스화 불가
try:
    obj = Base()
except TypeError as e:
    print(e)
    # Can't instantiate abstract class Base with abstract method method
```

### 3. 모든 추상 메서드 구현 필수

```python
class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

    @abstractmethod
    def perimeter(self):
        pass

# ❌ area만 구현
class Rectangle(Shape):
    def area(self):
        return 0
    # perimeter 구현 안 함

try:
    rect = Rectangle()
except TypeError as e:
    print(e)
    # Can't instantiate abstract class Rectangle with abstract method perimeter
```

### 4. ABC 없이 @abstractmethod 사용 불가

```python
from abc import abstractmethod

# ❌ ABC 상속 없이 @abstractmethod 사용
class Wrong:
    @abstractmethod
    def method(self):
        pass

# 인스턴스화 가능함! (추상 클래스가 아님)
obj = Wrong()  # 에러 없음
```

## 11. Duck Typing과의 조화

### Duck Typing이란?

**Duck Typing**: "오리처럼 걷고, 오리처럼 소리내면, 그것은 오리다"

**타입보다 메서드의 존재 여부가 중요**한 Python의 철학입니다. 객체의 실제 타입이 무엇인지보다, 필요한 메서드나 속성이 있는지가 중요합니다.

```python
# Duck Typing 예시
# Java였다면: Animal 타입인지 체크 필요
# Python: make_sound() 메서드만 있으면 OK!

def make_sound(animal):
    # 타입 체크 없음!
    # animal이 Dog인지, Cat인지, 심지어 Animal을 상속했는지도 안 봄
    # make_sound() 메서드만 있으면 작동!
    print(animal.make_sound())

class Dog:
    def make_sound(self):
        return "멍멍"

class Cat:
    def make_sound(self):
        return "야옹"

class Robot:  # Animal을 상속하지 않음!
    def make_sound(self):
        return "삐빅삐빅"

make_sound(Dog())    # "멍멍" - 작동!
make_sound(Cat())    # "야옹" - 작동!
make_sound(Robot())  # "삐빅삐빅" - 이것도 작동! (make_sound()만 있으면 됨)

### Java와 비교

```java
// Java: 타입 체크가 엄격함
void makeSound(Animal animal) {  // Animal 타입만 받음
    animal.makeSound();
}

// Robot은 Animal을 상속 안 함 → 컴파일 에러!
makeSound(new Robot());  // ❌ 컴파일 에러
```

```python
# Python: 타입보다 메서드가 중요
def make_sound(animal):  # 타입 제한 없음
    animal.make_sound()

# Robot은 Animal을 상속 안 해도 됨 → 작동!
make_sound(Robot())  # ✅ 정상 작동
```

### 추상 클래스를 사용하는 이유

Python은 Duck Typing이지만, **추상 클래스로 명시적 계약을 정의**할 수 있습니다.

```python
# 추상 클래스: 명시적 계약
from abc import ABC, abstractmethod

class Animal(ABC):
    @abstractmethod
    def make_sound(self):
        pass

# 구현 강제
class Cow(Animal):
    def make_sound(self):
        return "음메"

cow = Cow()  # 정상
```

**언제 추상 클래스를 쓸까?**

- ✅ 명확한 계약(인터페이스)을 정의하고 싶을 때
- ✅ 팀 프로젝트에서 구현 강제가 필요할 때
- ✅ 프레임워크나 라이브러리를 만들 때
- ✅ 리팩토링 시 안전장치가 필요할 때

**Duck Typing만으로 충분할 때:**

- 작은 프로젝트
- 빠른 프로토타이핑
- 유연성이 중요한 경우

## 요약

### 핵심 개념

```python
from abc import ABC, abstractmethod

# ABC = Abstract Base Class (정말로 ABC입니다!)
class Animal(ABC):
    @abstractmethod
    def make_sound(self):
        pass

# 구현 클래스 (@Override 같은 거 없음)
class Dog(Animal):  # (부모클래스) - extends 없음!
    def make_sound(self):
        return "멍멍"
```

### 상속 문법 비교

```python
# Java
class Dog extends Animal { }

# Python
class Dog(Animal):  # 괄호 안에 부모 클래스
    pass
```

### Java vs Python

| 항목 | Java | Python |
|------|------|--------|
| **추상 클래스** | `abstract class` | `ABC` 상속 |
| **상속 문법** | `extends` | `(부모클래스)` |
| **추상 메서드** | `abstract` 키워드 | `@abstractmethod` |
| **오버라이드** | `@Override` 필요 | **표시 없음** |
| **검증** | 컴파일 타임 | 런타임 |
| **강제** | 컴파일 에러 | `TypeError` |

### 주요 특징

1. **ABC는 Abstract Base Class** (장난 아님!)
2. **상속은 (부모클래스) 형태** - extends 없음
3. **@Override 같은 어노테이션 없음** - 그냥 구현하면 됨
4. **런타임 검증** - 인스턴스화할 때 체크
5. **기본 구현 가능** - 추상 메서드에도 구현 제공 가능
6. **다중 상속 지원** - 여러 추상 클래스 동시 상속

### 빠른 참조

```python
# 1. 추상 클래스 정의
from abc import ABC, abstractmethod

class Base(ABC):
    @abstractmethod
    def method(self):
        pass

# 2. 구현
class Impl(Base):  # (부모클래스)
    def method(self):
        return "구현됨"

# 3. 추상 프로퍼티
class WithProperty(ABC):
    @property
    @abstractmethod
    def value(self):
        pass

# 4. 클래스 메서드
class WithClassMethod(ABC):
    @classmethod
    @abstractmethod
    def create(cls):
        pass

# 5. 다중 상속
class Multi(Base1, Base2):  # 여러 부모 클래스
    pass
```

### 언제 사용?

**추상 클래스 사용:**
- ✅ 명확한 인터페이스 정의
- ✅ 구현 강제 필요
- ✅ 팀 프로젝트

**Duck Typing:**
- ✅ 작은 프로젝트
- ✅ 빠른 프로토타이핑

## 참고 자료

- [PEP 3119 - Introducing Abstract Base Classes](https://www.python.org/dev/peps/pep-3119/)
- [Python abc 모듈 공식 문서](https://docs.python.org/3/library/abc.html)
- [Real Python - Abstract Base Classes in Python](https://realpython.com/python-interface/)
