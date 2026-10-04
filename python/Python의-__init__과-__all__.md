# Python의 __init__과 __all__

이 노트는 클래스 생성자 쪽(`__init__`/`__new__`)을 다룬다.

> [!note] `__all__`(공개 API 제어)과 패키지 `__init__.py`는 [Python-패키지의-__init__py](./Python-패키지의-__init__py.md) 참고

## 결론부터 말하면

`__init__`은 객체가 만들어진 직후 **초기화**를 담당하는 메서드로, Java 생성자에 대응한다. 객체 **생성 자체**는 `__new__`가 맡는다.

```python
# __init__: Java 생성자와 동일
class Person:
    def __init__(self, name):  # Java: public Person(String name)
        self.name = name
```

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

## 2. 헷갈리는 포인트

이름이 비슷한 `__init__.py`(패키지 초기화 파일)와 `__all__`(공개 API 리스트)은 생성자와 무관하다. 둘 다 [Python-패키지의-__init__py](./Python-패키지의-__init__py.md)에서 다룬다.

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

**일반적으로 `__init__`만 사용합니다.** `__new__`는 **객체 생성 자체**를 제어해야 하는 특수 케이스에만 필요하다:

- **불변 타입 서브클래싱** (`str`, `tuple`, `int`, `frozenset` 등) — `__init__`은 이미 만들어진 불변 객체를 수정할 수 없으므로 `__new__`에서 값을 결정해야 한다
- **싱글톤 패턴** — 같은 인스턴스를 반복 반환해야 할 때
- **메타클래스 / 객체 풀링** — 클래스 자체나 인스턴스 캐싱을 제어할 때

`__init__`이 `None` 외 값을 반환하면 `TypeError`가 발생한다. 반면 `__new__`의 반환값에는 그런 강제 제약이 없다. 보통은 `cls`의 인스턴스를 반환하지만 다른 객체를 반환해도 오류가 나지 않으며, 다만 **반환값이 `cls`의 인스턴스일 때만** 이어서 `__init__`이 호출된다.

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

## 참고 자료

- [Python Documentation - Classes](https://docs.python.org/3/tutorial/classes.html)
- [Python Data Model - object.__new__ / object.__init__](https://docs.python.org/3/reference/datamodel.html#object.__new__)
