# Python 컬렉션 타입 비교: list[tuple] vs list[dict]

> 복잡한 컬렉션 타입의 실전 활용과 list[tuple], list[dict] 선택 가이드

## 목차
1. [복잡한 타입 해석하기](#복잡한-타입-해석하기)
2. [list[tuple] vs list[dict] 핵심 차이](#listtuple-vs-listdict-핵심-차이)
3. [list[tuple]을 쓰는 실무 상황](#listtuple을-쓰는-실무-상황)
4. [list[dict]를 쓰는 실무 상황](#listdict를-쓰는-실무-상황)
5. [결정 가이드](#결정-가이드)
6. [Java와의 비교](#java와의-비교)

---

## 복잡한 타입 해석하기

### 타입 시그니처 이해하기

```python
def process_data(data: dict[str, list[int]]) -> list[tuple[str, float]]:
    # 100줄의 복잡한 로직...
    return result
```

**이 함수의 타입을 해석하면:**

```python
# 입력: dict[str, list[int]]
# → Java: Map<String, List<Integer>>
# → 문자열 키와 정수 리스트 값을 가진 딕셔너리

# 출력: list[tuple[str, float]]
# → Java: List<Pair<String, Float>>
# → (문자열, 실수) 튜플의 리스트
```

### 구체적인 예시 1: 과목별 점수 평균 계산

```python
def process_data(data: dict[str, list[int]]) -> list[tuple[str, float]]:
    """각 과목의 점수 리스트를 받아서 평균을 계산"""
    result = []
    for subject, scores in data.items():
        average = sum(scores) / len(scores)
        result.append((subject, average))
    return result

# ========== 입력 데이터 ==========
input_data: dict[str, list[int]] = {
    "math": [90, 85, 88, 92],      # 수학 점수들
    "english": [75, 80, 78, 82],   # 영어 점수들
    "science": [95, 88, 91, 89]    # 과학 점수들
}

# Java로 치면:
# Map<String, List<Integer>> inputData = new HashMap<>();
# inputData.put("math", Arrays.asList(90, 85, 88, 92));

# ========== 출력 데이터 ==========
output: list[tuple[str, float]] = process_data(input_data)

print(output)
# [
#     ("math", 88.75),      # 튜플: (과목명, 평균)
#     ("english", 78.75),
#     ("science", 90.75)
# ]

# Java로 치면:
# List<Pair<String, Float>> output = processData(inputData);
```

### 구체적인 예시 2: 사용자별 구매 금액 집계

```python
def calculate_total_with_tax(
    data: dict[str, list[int]]
) -> list[tuple[str, float]]:
    """사용자별 구매 금액 리스트를 받아서 총합과 부가세 계산"""
    result = []
    for username, purchase_amounts in data.items():
        total = sum(purchase_amounts)
        total_with_tax = total * 1.1  # 10% 부가세
        result.append((username, total_with_tax))
    return result

# ========== 입력 ==========
purchases: dict[str, list[int]] = {
    "john": [10000, 20000, 15000],    # John의 구매 내역들
    "jane": [50000, 30000],           # Jane의 구매 내역들
    "bob": [100000, 25000, 30000]     # Bob의 구매 내역들
}

# ========== 출력 ==========
result: list[tuple[str, float]] = calculate_total_with_tax(purchases)
# [("john", 49500.0), ("jane", 88000.0), ("bob", 170500.0)]
```

### 단계별 변환 과정

```python
def process_data(data: dict[str, list[int]]) -> list[tuple[str, float]]:
    """단계별로 보면 더 명확!"""
    result: list[tuple[str, float]] = []

    # 1단계: 딕셔너리를 순회
    for subject, scores in data.items():
        # subject: str = "math"
        # scores: list[int] = [90, 85, 88]

        # 2단계: 리스트를 처리해서 하나의 float 값으로
        average: float = sum(scores) / len(scores)
        # average: float = 87.67

        # 3단계: (str, float) 튜플 생성
        item: tuple[str, float] = (subject, average)
        # item = ("math", 87.67)

        # 4단계: 결과 리스트에 추가
        result.append(item)

    return result

# 실행
data = {"math": [90, 85, 88], "english": [75, 80]}
result = process_data(data)

print(result)
# [("math", 87.67), ("english", 77.5)]
#   └─ 튜플1        └─ 튜플2
```

---

## list[tuple] vs list[dict] 핵심 차이

### 같은 데이터, 다른 표현

```python
# ========== list[tuple[str, float]] ==========
sales_tuple: list[tuple[str, float]] = [
    ("서울", 1500000.0),
    ("부산", 980000.0),
    ("대구", 750000.0)
]

# 접근 방법
for region, amount in sales_tuple:
    print(region, amount)

# 또는 인덱스로
for item in sales_tuple:
    print(item[0], item[1])  # 인덱스로만 접근


# ========== list[dict[str, str | float]] ==========
sales_dict: list[dict[str, str | float]] = [
    {"region": "서울", "sales": 1500000.0},
    {"region": "부산", "sales": 980000.0},
    {"region": "대구", "sales": 750000.0}
]

# 접근 방법
for item in sales_dict:
    print(item["region"], item["sales"])  # 키로 접근!
```

### 비교표

| 특징 | `list[tuple]` | `list[dict]` |
|------|--------------|--------------|
| **가독성** | 2-3개 필드까지 OK | 많은 필드에 좋음 |
| **접근 방법** | `item[0]`, `item[1]` (인덱스) | `item["key"]` (키) |
| **JSON 변환** | 수동 변환 필요 | 바로 변환 가능 |
| **불변성** | 불변 (수정 불가) | 가변 (수정 가능) |
| **메모리** | 가벼움 (~50 bytes) | 무거움 (~230 bytes) |
| **타입 힌트** | `tuple[str, int]` 명확 | `dict[str, Any]` 느슨 |
| **해시 가능** | O (set/dict 키 가능) | X |
| **실무 용도** | DB 조회, 차트, CSV | API 응답, 복잡한 데이터 |

### 1. 가독성: 필드 개수에 따라

```python
# ========== tuple: 2-3개 필드는 OK ==========
user = ("john", 30)  # 이름, 나이
user = ("john", 30, "john@example.com")  # 이름, 나이, 이메일
# → 아직 괜찮음

# ❌ 5개 이상이면 혼란스러움!
user = ("john", 30, "john@example.com", "010-1234-5678", "서울", 180.5, 75.0)
# 뭐가 뭔지 모르겠음! item[0]? item[3]? item[5]?


# ========== dict: 많은 필드에 적합 ==========
user: dict[str, str | int | float] = {
    "name": "john",
    "age": 30,
    "email": "john@example.com",
    "phone": "010-1234-5678",
    "address": "서울",
    "height": 180.5,
    "weight": 75.0
}
# ✅ 한눈에 명확함! user["email"], user["height"]
```

### 2. API 응답 (JSON 변환)

```python
from flask import jsonify

# ========== tuple → JSON (추가 작업 필요) ==========
def get_users_tuple() -> list[tuple[str, int]]:
    return [("john", 30), ("jane", 25)]

@app.route("/api/users")
def api_users_tuple():
    users = get_users_tuple()

    # ❌ 그냥 변환하면 배열로 나옴
    # return jsonify(users)
    # → [["john", 30], ["jane", 25]]  이게 뭔지 모름!

    # ✅ 수동으로 dict 변환 필요
    return jsonify([
        {"name": name, "age": age}
        for name, age in users
    ])


# ========== dict → JSON (바로 가능!) ==========
def get_users_dict() -> list[dict[str, str | int]]:
    return [
        {"name": "john", "age": 30},
        {"name": "jane", "age": 25}
    ]

@app.route("/api/users")
def api_users_dict():
    return jsonify(get_users_dict())  # ✅ 바로 변환!
    # → [{"name": "john", "age": 30}, {"name": "jane", "age": 25}]
```

### 3. 불변 vs 가변

```python
# ========== tuple: 불변(Immutable) ==========
user: tuple[str, int] = ("john", 30)
user[1] = 31  # ❌ TypeError! 수정 불가능!

# 수정하려면 새로 만들어야 함
user = ("john", 31)  # 새로운 튜플 생성


# ========== dict: 가변(Mutable) ==========
user: dict[str, str | int] = {"name": "john", "age": 30}
user["age"] = 31  # ✅ 수정 가능!

# 필드 추가도 가능
user["email"] = "john@example.com"  # ✅ OK
```

### 4. 메모리 사용량

```python
import sys

# tuple: 가벼움
t = ("john", 30)
print(sys.getsizeof(t))  # 48 bytes

# dict: 무거움
d = {"name": "john", "age": 30}
print(sys.getsizeof(d))  # 232 bytes

# ⚠️ dict가 약 5배 더 큼!
```

---

## list[tuple]을 쓰는 실무 상황

### 1. 순위/랭킹 시스템 (게임, 쇼핑몰)

```python
def get_top_products() -> list[tuple[str, float]]:
    """인기 상품 TOP 10 (평점순)"""
    # 데이터베이스에서 평점 높은 순으로 정렬해서 가져옴
    return [
        ("iPhone 15", 4.8),
        ("Galaxy S24", 4.7),
        ("Pixel 8", 4.6),
    ]

# ✅ list[tuple]을 쓰는 이유:
# - 순서가 중요함 (1등, 2등, 3등)
# - 간단한 2개 필드만 있음
# - 정렬된 상태 유지

# 사용
top_products = get_top_products()
for rank, (product, rating) in enumerate(top_products, 1):
    print(f"{rank}위: {product} ({rating}점)")
# 1위: iPhone 15 (4.8점)
# 2위: Galaxy S24 (4.7점)
# 3위: Pixel 8 (4.6점)
```

### 2. 시계열 데이터 (시간별 통계)

```python
def get_hourly_traffic() -> list[tuple[str, float]]:
    """시간대별 평균 트래픽 (00시~23시 순서대로!)"""
    return [
        ("00:00", 120.5),
        ("01:00", 80.3),
        ("02:00", 45.2),
        # ... 순서대로 23:00까지
        ("23:00", 200.1)
    ]

# ✅ list[tuple]을 쓰는 이유:
# - 시간 순서가 절대적으로 중요!
# - 꺾은선 그래프로 바로 그릴 수 있음

# 실무: 모니터링 대시보드
traffic_data = get_hourly_traffic()
# → Grafana, Kibana 같은 모니터링 툴로 바로 전송
```

### 3. 데이터베이스 조회 결과

```python
import psycopg2

def get_user_activity() -> list[tuple[str, float]]:
    """사용자별 활동 점수 (높은 순)"""
    conn = psycopg2.connect("...")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, activity_score
        FROM users
        ORDER BY activity_score DESC
        LIMIT 10
    """)

    # ✅ 데이터베이스에서 이미 tuple 형태로 나옴!
    results: list[tuple[str, float]] = cursor.fetchall()

    cursor.close()
    conn.close()

    return results
    # [("john", 95.5), ("jane", 88.3), ...]

# ✅ list[tuple]을 쓰는 이유:
# - DB 조회 결과가 원래 tuple 형태
# - 정렬된 순서 유지
# - 데이터베이스 조회 결과는 원래 tuple!
```

### 4. CSV/엑셀 변환 (데이터 export)

```python
def get_employee_salaries() -> list[tuple[str, float]]:
    """직원별 급여 리스트"""
    return [
        ("김철수", 5000000.0),
        ("이영희", 4500000.0),
        ("박민수", 4200000.0)
    ]

# CSV 파일로 저장
import csv

data = get_employee_salaries()

with open("salaries.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["이름", "급여"])  # 헤더
    writer.writerows(data)  # ✅ tuple 리스트를 바로 입력!

# 결과 (salaries.csv):
# 이름,급여
# 김철수,5000000.0
# 이영희,4500000.0
# 박민수,4200000.0

# ✅ list[tuple]을 쓰는 이유:
# - CSV는 행(row) 단위 = tuple
# - writerows()에 바로 전달 가능
```

### 5. 차트/그래프 데이터

```python
def get_sales_by_region() -> list[tuple[str, float]]:
    """지역별 매출 (높은 순)"""
    return [
        ("서울", 1500000.0),
        ("부산", 980000.0),
        ("대구", 750000.0)
    ]

# 차트 라이브러리에 바로 전달
import matplotlib.pyplot as plt

sales = get_sales_by_region()
regions = [item[0] for item in sales]  # ["서울", "부산", "대구"]
amounts = [item[1] for item in sales]  # [1500000.0, 980000.0, 750000.0]

plt.bar(regions, amounts)  # ✅ 바로 막대그래프 생성!
plt.show()

# ✅ list[tuple]을 쓰는 이유:
# - 정렬된 순서가 중요 (매출 높은 순)
# - 차트 데이터로 바로 변환 가능
```

### 6. 집계 후 정렬 (실무 초초 빈번!)

```python
def get_product_conversion_rate() -> list[tuple[str, float]]:
    """상품별 전환율 (높은 순으로 정렬)"""

    # 데이터 집계
    raw_data = {
        "상품A": {"views": 1000, "purchases": 50},
        "상품B": {"views": 2000, "purchases": 150},
        "상품C": {"views": 500, "purchases": 30}
    }

    # 전환율 계산
    rates = []
    for product, stats in raw_data.items():
        conversion_rate = (stats["purchases"] / stats["views"]) * 100
        rates.append((product, conversion_rate))

    # ✅ 정렬! (dict는 정렬 개념이 약함)
    rates.sort(key=lambda x: x[1], reverse=True)

    return rates
    # [("상품B", 7.5), ("상품C", 6.0), ("상품A", 5.0)]

# ✅ list[tuple]을 쓰는 이유:
# - 정렬된 순서가 핵심!
# - list는 순서 보장
# - dict로 하면 정렬 의미 약함
```

---

## list[dict]를 쓰는 실무 상황

### 1. API 응답 (JSON 변환)

```python
def get_products() -> list[dict[str, str | int | float]]:
    """상품 목록 API"""
    return [
        {
            "id": 1,
            "name": "iPhone",
            "price": 1200000,
            "rating": 4.8,
            "category": "전자제품"
        },
        {
            "id": 2,
            "name": "Galaxy",
            "price": 1100000,
            "rating": 4.7,
            "category": "전자제품"
        }
    ]

# ✅ list[dict]를 쓰는 이유:
# - JSON으로 바로 변환 가능
# - 많은 필드 (5개)
# - 키 이름이 명확함

# 사용: Flask API
from flask import jsonify

@app.route("/api/products")
def api_products():
    products = get_products()
    return jsonify(products)  # ✅ 바로 JSON 응답!

# API 응답:
# [
#   {"id": 1, "name": "iPhone", "price": 1200000, ...},
#   {"id": 2, "name": "Galaxy", "price": 1100000, ...}
# ]
```

### 2. 복잡한 데이터 구조 (많은 필드)

```python
def get_user_profile() -> list[dict[str, str | int | bool]]:
    """사용자 프로필 (필드가 많음)"""
    return [
        {
            "username": "john",
            "email": "john@example.com",
            "age": 30,
            "address": "서울",
            "phone": "010-1234-5678",
            "is_active": True,
            "last_login": "2024-01-15"
        }
    ]

# ✅ list[dict]를 쓰는 이유:
# - 필드가 7개 이상 (tuple은 혼란)
# - 각 필드의 의미가 명확해야 함
# - 가독성이 최우선

# 사용
for user in get_user_profile():
    print(f"{user['username']}: {user['total_orders']}건, "
          f"{user['total_spent']}원")
```

### 3. Pandas DataFrame 변환

```python
import pandas as pd

def get_analytics_data() -> list[dict[str, str | int]]:
    """분석 데이터"""
    return [
        {"name": "john", "age": 30, "city": "서울", "score": 95},
        {"name": "jane", "age": 25, "city": "부산", "score": 88}
    ]

data = get_analytics_data()
df = pd.DataFrame(data)  # ✅ dict 리스트는 바로 변환!

print(df)
#    name  age city  score
# 0  john   30   서울     95
# 1  jane   25   부산     88

# ✅ list[dict]를 쓰는 이유:
# - pandas는 dict 리스트를 선호
# - 컬럼명이 명확함
```

### 4. ORM 결과를 dict로 변환

```python
from sqlalchemy import select

def get_users_from_db() -> list[dict[str, str | int]]:
    """데이터베이스에서 사용자 조회 후 dict로 변환"""
    users = session.execute(select(User)).scalars().all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "age": user.age
        }
        for user in users
    ]

# ✅ list[dict]를 쓰는 이유:
# - API 응답으로 바로 전달
# - JSON 변환 쉬움
# - 필드명이 명확
```

### 5. 중첩된 복잡한 구조

```python
def get_order_details() -> list[dict]:
    """주문 상세 정보 (중첩 구조)"""
    return [
        {
            "order_id": 1,
            "customer": {
                "name": "john",
                "email": "john@example.com"
            },
            "items": [
                {"product": "iPhone", "quantity": 1, "price": 1200000},
                {"product": "AirPods", "quantity": 2, "price": 300000}
            ],
            "total": 1800000,
            "status": "completed"
        }
    ]

# ✅ list[dict]를 쓰는 이유:
# - 중첩된 구조 표현 쉬움
# - JSON과 1:1 매칭
# - 가독성 최고
```

---

## 결정 가이드

### 언제 뭘 쓸까?

```python
# ========== list[tuple]을 쓰세요 ==========
# ✅ 2-3개의 간단한 값
# ✅ 순서/순위가 중요할 때
# ✅ 정렬된 통계 데이터
# ✅ 차트/그래프 데이터
# ✅ CSV 변환
# ✅ 데이터베이스 조회 결과
# ✅ 메모리 효율이 중요할 때

def get_top_scores() -> list[tuple[str, int]]:
    """간단한 2개 값: 이름, 점수"""
    return [("john", 95), ("jane", 88), ("bob", 92)]


# ========== list[dict]를 쓰세요 ==========
# ✅ 4개 이상의 필드
# ✅ API 응답 (JSON)
# ✅ 복잡한 데이터 구조
# ✅ 가독성이 최우선일 때
# ✅ 필드 추가/수정이 필요할 때
# ✅ Pandas 변환

def get_user_details() -> list[dict[str, str | int]]:
    """복잡한 여러 필드"""
    return [
        {
            "name": "john",
            "age": 30,
            "email": "john@example.com",
            "address": "서울",
            "phone": "010-1234-5678"
        }
    ]
```

### 의사결정 플로우차트

```
데이터를 반환해야 한다면?
    │
    ├─ 필드가 2-3개? ─────────────────────→ list[tuple]
    │                                        (간단, 가벼움)
    │
    ├─ 필드가 4개 이상? ──────────────────→ list[dict]
    │                                        (가독성)
    │
    ├─ API 응답 (JSON 변환)? ─────────────→ list[dict]
    │                                        (바로 변환)
    │
    ├─ 순서/정렬이 핵심? ─────────────────→ list[tuple]
    │                                        (순서 보장)
    │
    ├─ DB 조회 결과? ─────────────────────→ list[tuple]
    │                                        (원래 tuple)
    │
    ├─ 차트/그래프 데이터? ───────────────→ list[tuple]
    │                                        (바로 변환)
    │
    └─ Pandas 변환? ──────────────────────→ list[dict]
                                             (컬럼명 명확)
```

---

## Java와의 비교

### Tuple 스타일

```python
# ========== Python ==========
def get_tuple_data() -> list[tuple[str, int]]:
    return [
        ("서울", 1500000),
        ("부산", 980000)
    ]

# 접근
for region, sales in get_tuple_data():
    print(region, sales)


# ========== Java ==========
// Pair 사용 (Apache Commons, JavaFX 등)
List<Pair<String, Integer>> getTupleData() {
    return Arrays.asList(
        Pair.of("서울", 1500000),
        Pair.of("부산", 980000)
    );
}

// 접근
for (Pair<String, Integer> pair : getTupleData()) {
    System.out.println(pair.getKey() + ", " + pair.getValue());
    // 또는: pair.getFirst(), pair.getSecond()
}
```

### Dict/Map 스타일

```python
# ========== Python ==========
def get_dict_data() -> list[dict[str, str | int]]:
    return [
        {"region": "서울", "sales": 1500000},
        {"region": "부산", "sales": 980000}
    ]

# 접근
for item in get_dict_data():
    print(item["region"], item["sales"])


# ========== Java ==========
// Map 사용
List<Map<String, Object>> getMapData() {
    return Arrays.asList(
        Map.of("region", "서울", "sales", 1500000),
        Map.of("region", "부산", "sales", 980000)
    );
}

// 접근
for (Map<String, Object> item : getMapData()) {
    System.out.println(item.get("region") + ", " + item.get("sales"));
}
```

### DTO/Record 스타일 (Java 14+)

```python
# ========== Python (dataclass) ==========
from dataclasses import dataclass

@dataclass
class SalesData:
    region: str
    sales: int

def get_sales_data() -> list[SalesData]:
    return [
        SalesData("서울", 1500000),
        SalesData("부산", 980000)
    ]

# 접근
for data in get_sales_data():
    print(data.region, data.sales)


# ========== Java (Record) ==========
public record SalesData(String region, Integer sales) {}

List<SalesData> getSalesData() {
    return Arrays.asList(
        new SalesData("서울", 1500000),
        new SalesData("부산", 980000)
    );
}

// 접근
for (SalesData data : getSalesData()) {
    System.out.println(data.region() + ", " + data.sales());
}
```

---

## 정리

### 핵심 요점

1. **필드 개수가 결정 기준**
   - 2-3개: `list[tuple]` (간단, 가벼움)
   - 4개 이상: `list[dict]` (가독성)

2. **용도별 선택**
   - API/JSON: `list[dict]`
   - DB 조회/차트/CSV: `list[tuple]`

3. **메모리 vs 가독성**
   - tuple: 5배 가벼움, 불변
   - dict: 무겁지만 명확함, 가변

4. **Java와의 비교**
   - `list[tuple]` ≈ `List<Pair<K, V>>`
   - `list[dict]` ≈ `List<Map<K, V>>` 또는 `List<DTO>`

### 실전 팁

```python
# ✅ 좋은 예시
def get_top_10() -> list[tuple[str, float]]:
    """간단한 2개 값"""
    return [("item1", 9.5), ("item2", 9.3)]

def get_user_info() -> list[dict[str, str | int | bool]]:
    """복잡한 여러 필드"""
    return [
        {
            "id": 1,
            "name": "john",
            "email": "john@example.com",
            "age": 30,
            "is_active": True
        }
    ]


# ❌ 피해야 할 예시
def get_user_bad() -> list[tuple[int, str, str, int, bool, str, str]]:
    """tuple에 7개 필드 → 혼란스러움!"""
    return [(1, "john", "john@example.com", 30, True, "서울", "010-1234")]
    # 뭐가 뭔지 모르겠음!
```

### 마지막 조언

- **간단하면 tuple, 복잡하면 dict**
- **정렬/순서가 중요하면 tuple**
- **API/JSON이면 dict**
- **헷갈리면 dict (명확함이 최고)**
