# Python 예외 처리 완전 정복

파이썬에서 오류를 안전하게 처리하는 방법을 실무 중심으로 정리합니다.

## 결론부터 말하면

파이썬의 예외 처리는 **프로그램이 죽지 않게 하면서도 문제를 명확히 파악**할 수 있게 해줍니다. `try-except`를 사용하되, **구체적인 예외만 잡고**, **최소한의 범위만 감싸며**, **항상 로깅**하는 것이 핵심입니다.

```python
# 좋은 예외 처리의 예시
try:
    user_data = fetch_user(user_id)  # 에러 날 수 있는 부분만
except UserNotFoundError as e:       # 구체적인 예외
    logging.error(f"사용자 없음: {user_id}")  # 로깅
    return None
except DatabaseError as e:
    logging.critical(f"DB 오류: {e}", exc_info=True)
    raise  # 예상 못한 오류는 재발생
finally:
    close_connection()  # 정리 작업
```

## 1. 기본 구조: try-except

### 기본 형태

```python
# 가장 기본적인 형태
try:
    result = 10 / 0
except ZeroDivisionError:
    print("0으로 나눌 수 없습니다")
    result = 0

# 에러 정보 받기
try:
    number = int("abc")
except ValueError as e:
    print(f"변환 실패: {e}")  # 변환 실패: invalid literal for int()
```

**언제 사용?**
- 에러가 발생할 수 있는 모든 작업
- 외부 입력 처리
- 파일/네트워크/DB 접근

### 여러 예외 처리

```python
# 각각 다르게 처리
def read_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"파일 없음: {filename}")
        return ""
    except PermissionError:
        print(f"권한 없음: {filename}")
        return ""
    except UnicodeDecodeError:
        print(f"인코딩 오류: {filename}")
        return ""
    except Exception as e:
        print(f"알 수 없는 오류: {e}")
        return ""

# 같은 방식으로 처리 (튜플)
def convert_to_number(value):
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        print(f"숫자 변환 실패: {value}")
        return 0.0
```

**언제 사용?**
- 여러 종류의 에러가 발생할 수 있을 때
- 각 에러마다 다른 처리가 필요할 때

## 2. try-except-else-finally

### 완전한 구조

```python
def process_payment(order_id, amount):
    """
    결제 처리 - 완전한 예외 처리 구조
    """
    connection = None

    try:
        # 1. 에러가 날 수 있는 코드
        connection = get_db_connection()
        order = fetch_order(connection, order_id)
        charge_result = charge_credit_card(order.card, amount)

    except OrderNotFoundError as e:
        # 2. 예외 처리
        logging.error(f"주문 없음: {order_id}")
        return {"status": "failed", "reason": "order_not_found"}

    except PaymentDeclinedError as e:
        logging.warning(f"결제 거부: {e}")
        return {"status": "declined", "reason": str(e)}

    except DatabaseError as e:
        logging.critical(f"DB 오류: {e}", exc_info=True)
        return {"status": "error", "reason": "system_error"}

    else:
        # 3. 에러가 없을 때만 실행
        update_order_status(connection, order_id, "paid")
        send_confirmation_email(order.email)
        logging.info(f"결제 완료: {order_id}")
        return {"status": "success", "order_id": order_id}

    finally:
        # 4. 무조건 실행 (정리 작업)
        if connection:
            connection.close()
```

**구조 설명:**
- `try`: 에러가 발생할 수 있는 코드
- `except`: 에러 발생시 실행
- `else`: **에러가 없을 때만** 실행 (선택사항)
- `finally`: **항상** 실행 (정리 작업, 선택사항)

**언제 사용?**
- `else`: 성공했을 때만 추가 작업이 필요한 경우
- `finally`: 리소스 정리가 필요한 경우 (파일, DB 연결 등)

## 3. 자주 마주치는 예외들

### 내장 예외

```python
# ValueError - 잘못된 값
try:
    age = int("스물다섯")
except ValueError:
    print("숫자가 아닙니다")

# TypeError - 잘못된 타입
try:
    result = "문자열" + 123
except TypeError:
    print("타입이 맞지 않습니다")

# KeyError - 딕셔너리 키 없음
try:
    user = {"name": "Alice"}
    email = user["email"]
except KeyError:
    email = "no-email@example.com"

# IndexError - 인덱스 범위 초과
try:
    items = [1, 2, 3]
    value = items[10]
except IndexError:
    value = None

# FileNotFoundError - 파일 없음
try:
    with open("없는파일.txt") as f:
        content = f.read()
except FileNotFoundError:
    content = ""

# AttributeError - 속성 없음
try:
    result = None.some_method()
except AttributeError:
    result = None

# ZeroDivisionError - 0으로 나누기
try:
    result = 10 / 0
except ZeroDivisionError:
    result = float('inf')
```

### 외부 라이브러리 예외

```python
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError

# requests 예외
try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()
except Timeout:
    print("요청 시간 초과")
except ConnectionError:
    print("연결 실패")
except HTTPError as e:
    print(f"HTTP 오류: {e.response.status_code}")

# JSON 예외
import json
try:
    data = json.loads('{"invalid json}')
except json.JSONDecodeError as e:
    print(f"JSON 파싱 오류 (라인 {e.lineno}): {e.msg}")
```

## 4. 실무 예제

### 예제 1: API 호출 with 재시도

```python
import requests
import time
from requests.exceptions import RequestException, Timeout

def call_api_with_retry(url, max_retries=3):
    """
    실패시 자동으로 재시도하는 API 호출
    """

    for attempt in range(1, max_retries + 1):
        try:
            print(f"시도 {attempt}/{max_retries}...")

            response = requests.get(url, timeout=5)
            response.raise_for_status()  # 4xx, 5xx 에러 발생

            print("✓ 성공!")
            return response.json()

        except Timeout:
            print(f"✗ 타임아웃")
            if attempt == max_retries:
                raise Exception("최대 재시도 횟수 초과")
            time.sleep(2 ** attempt)  # 2, 4, 8초 대기

        except requests.HTTPError as e:
            status = e.response.status_code

            if status >= 500:
                # 서버 에러는 재시도
                print(f"✗ 서버 에러 ({status})")
                if attempt == max_retries:
                    raise
                time.sleep(2)
            else:
                # 클라이언트 에러는 재시도 안함
                print(f"✗ 클라이언트 에러 ({status})")
                raise

        except RequestException as e:
            print(f"✗ 요청 실패: {e}")
            if attempt == max_retries:
                raise
            time.sleep(2)

# 사용
try:
    data = call_api_with_retry("https://api.example.com/users")
    print(f"데이터 받음: {len(data)} 항목")
except Exception as e:
    print(f"API 호출 최종 실패: {e}")
```

### 예제 2: 파일 처리

```python
import json
from pathlib import Path

def load_config(filepath, create_if_missing=True):
    """
    설정 파일을 안전하게 로드
    """

    try:
        # 파일 존재 확인
        path = Path(filepath)
        if not path.exists():
            if create_if_missing:
                print(f"설정 파일 없음, 기본값 생성: {filepath}")
                default_config = {
                    "api_key": "",
                    "database_url": "sqlite:///app.db",
                    "debug": False
                }
                save_config(filepath, default_config)
                return default_config
            else:
                raise FileNotFoundError(f"설정 파일 없음: {filepath}")

        # 파일 읽기
        with open(filepath, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 필수 키 검증
        required_keys = ['api_key', 'database_url']
        missing = [k for k in required_keys if k not in config]
        if missing:
            raise ValueError(f"필수 설정 누락: {missing}")

        print(f"✓ 설정 로드 완료: {filepath}")
        return config

    except FileNotFoundError as e:
        print(f"✗ 파일 오류: {e}")
        raise

    except json.JSONDecodeError as e:
        print(f"✗ JSON 파싱 오류 (라인 {e.lineno}): {e.msg}")
        print(f"힌트: {filepath} 파일의 JSON 형식을 확인하세요")
        raise

    except PermissionError:
        print(f"✗ 권한 오류: {filepath} 읽기 권한이 없습니다")
        raise

    except ValueError as e:
        print(f"✗ 검증 오류: {e}")
        raise

    except Exception as e:
        print(f"✗ 예상치 못한 오류: {type(e).__name__} - {e}")
        raise

def save_config(filepath, config):
    """설정 저장"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✓ 설정 저장 완료: {filepath}")
    except Exception as e:
        print(f"✗ 저장 실패: {e}")
        raise
```

### 예제 3: 데이터베이스 트랜잭션

```python
import sqlite3

def transfer_money(db_path, from_account, to_account, amount):
    """
    계좌 이체 - 트랜잭션 예제
    실패시 자동으로 롤백
    """

    connection = None

    try:
        # DB 연결
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()

        # 1. 출금 계좌 잔액 확인
        cursor.execute(
            "SELECT balance FROM accounts WHERE id = ?",
            (from_account,)
        )
        result = cursor.fetchone()

        if not result:
            raise ValueError(f"계좌 없음: {from_account}")

        balance = result[0]
        if balance < amount:
            raise ValueError(
                f"잔액 부족: 현재 {balance:,}원, 필요 {amount:,}원"
            )

        # 2. 출금
        cursor.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?",
            (amount, from_account)
        )

        # 3. 입금
        cursor.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (amount, to_account)
        )

        # 4. 거래 내역 기록
        cursor.execute(
            """INSERT INTO transactions (from_acc, to_acc, amount, timestamp)
               VALUES (?, ?, ?, datetime('now'))""",
            (from_account, to_account, amount)
        )

        # 5. 커밋
        connection.commit()
        print(f"✓ 이체 완료: {from_account} → {to_account} ({amount:,}원)")
        return True

    except ValueError as e:
        # 비즈니스 로직 에러
        print(f"✗ 검증 실패: {e}")
        if connection:
            connection.rollback()
        return False

    except sqlite3.DatabaseError as e:
        # DB 에러
        print(f"✗ 데이터베이스 오류: {e}")
        if connection:
            connection.rollback()
        raise

    except Exception as e:
        # 예상 못한 에러
        print(f"✗ 예상치 못한 오류: {e}")
        if connection:
            connection.rollback()
        raise

    finally:
        # 항상 연결 종료
        if connection:
            connection.close()

# 사용
try:
    transfer_money("bank.db", from_account=1, to_account=2, amount=10000)
except Exception as e:
    print(f"이체 실패: {e}")
```

### 예제 4: 배치 처리 with 부분 실패 허용

```python
def process_users_batch(users):
    """
    사용자 배치 처리
    일부 실패해도 계속 진행
    """

    results = {
        "success": [],
        "failed": [],
        "total": len(users)
    }

    for idx, user in enumerate(users, start=1):
        try:
            # 사용자 처리
            validate_user(user)
            save_to_database(user)
            send_welcome_email(user['email'])

            results["success"].append(user['id'])
            print(f"[{idx}/{len(users)}] ✓ {user['name']}")

        except ValidationError as e:
            # 검증 실패 - 기록하고 계속
            results["failed"].append({
                "user_id": user.get('id'),
                "name": user.get('name'),
                "error": f"검증 실패: {e}"
            })
            print(f"[{idx}/{len(users)}] ✗ {user.get('name')}: {e}")

        except DatabaseError as e:
            # DB 에러 - 기록하고 계속
            results["failed"].append({
                "user_id": user.get('id'),
                "name": user.get('name'),
                "error": f"DB 오류: {e}"
            })
            print(f"[{idx}/{len(users)}] ✗ {user.get('name')}: DB 오류")

        except Exception as e:
            # 예상 못한 에러 - 기록하고 계속
            results["failed"].append({
                "user_id": user.get('id'),
                "name": user.get('name'),
                "error": f"알 수 없는 오류: {type(e).__name__}"
            })
            print(f"[{idx}/{len(users)}] ✗ {user.get('name')}: 예상치 못한 오류")

    # 결과 출력
    success_rate = len(results["success"]) / results["total"] * 100
    print(f"\n처리 완료: {len(results['success'])}/{results['total']} ({success_rate:.1f}%)")

    if results["failed"]:
        print(f"실패: {len(results['failed'])}건")
        for failed in results["failed"][:5]:  # 처음 5개만
            print(f"  - {failed['name']}: {failed['error']}")

    return results

# 사용
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "invalid-email"},  # 실패할 데이터
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
]

results = process_users_batch(users)
```

## 5. 커스텀 예외 만들기

### 기본 커스텀 예외

```python
# 단순한 커스텀 예외
class ValidationError(Exception):
    """데이터 검증 실패"""
    pass

class NotFoundError(Exception):
    """리소스를 찾을 수 없음"""
    pass

# 사용
def get_user(user_id):
    users = {1: "Alice", 2: "Bob"}
    if user_id not in users:
        raise NotFoundError(f"사용자를 찾을 수 없습니다: {user_id}")
    return users[user_id]

try:
    user = get_user(999)
except NotFoundError as e:
    print(f"오류: {e}")
```

### 상세 정보를 담는 예외

```python
class AuthenticationError(Exception):
    """인증 실패"""
    def __init__(self, user_id, reason, attempts=0):
        self.user_id = user_id
        self.reason = reason
        self.attempts = attempts
        message = f"인증 실패 (사용자: {user_id}, 사유: {reason})"
        if attempts > 0:
            message += f", 시도: {attempts}회"
        super().__init__(message)

class APIError(Exception):
    """API 호출 실패"""
    def __init__(self, endpoint, status_code, message):
        self.endpoint = endpoint
        self.status_code = status_code
        self.message = message
        super().__init__(f"{endpoint}: HTTP {status_code} - {message}")

# 사용
def login(user_id, password, attempts=0):
    if password != "correct":
        raise AuthenticationError(
            user_id=user_id,
            reason="비밀번호 불일치",
            attempts=attempts + 1
        )
    return "로그인 성공"

try:
    login("user123", "wrong_password", attempts=2)
except AuthenticationError as e:
    print(f"사용자: {e.user_id}")
    print(f"사유: {e.reason}")
    print(f"시도 횟수: {e.attempts}")
    if e.attempts >= 3:
        print("계정이 잠겼습니다")
```

### 예외 계층 구조

```python
# 기본 예외
class AppError(Exception):
    """애플리케이션의 모든 예외의 베이스"""
    pass

# 카테고리별 예외
class DatabaseError(AppError):
    """DB 관련 오류"""
    pass

class NetworkError(AppError):
    """네트워크 관련 오류"""
    pass

class ValidationError(AppError):
    """검증 관련 오류"""
    pass

# 구체적인 예외
class UserNotFoundError(DatabaseError):
    """사용자를 찾을 수 없음"""
    pass

class ConnectionTimeoutError(NetworkError):
    """연결 시간 초과"""
    pass

class InvalidEmailError(ValidationError):
    """잘못된 이메일 형식"""
    pass

# 사용 - 상위 예외로 여러 하위 예외를 잡을 수 있음
try:
    process_user()
except DatabaseError as e:
    # UserNotFoundError도 여기서 잡힘
    print(f"데이터베이스 오류: {e}")
except NetworkError as e:
    # ConnectionTimeoutError도 여기서 잡힘
    print(f"네트워크 오류: {e}")
except AppError as e:
    # 위에서 안 잡힌 모든 앱 에러
    print(f"애플리케이션 오류: {e}")
```

## 6. with문으로 자동 정리

### 파일 처리

```python
# ❌ 번거로운 방법
f = open('file.txt', 'r')
try:
    data = f.read()
finally:
    f.close()

# ✅ with문 사용 (권장)
with open('file.txt', 'r', encoding='utf-8') as f:
    data = f.read()
# 자동으로 f.close() 호출

# 여러 파일 동시에
with open('input.txt', 'r') as infile, \
     open('output.txt', 'w') as outfile:
    for line in infile:
        outfile.write(line.upper())
```

### 커스텀 컨텍스트 매니저

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(name):
    """실행 시간 측정"""
    start = time.time()
    print(f"[{name}] 시작...")

    try:
        yield
    finally:
        elapsed = time.time() - start
        print(f"[{name}] 완료 ({elapsed:.2f}초)")

# 사용
with timer("데이터 처리"):
    process_large_data()
# 자동으로 시간 측정 및 출력

@contextmanager
def database_transaction(connection):
    """데이터베이스 트랜잭션"""
    try:
        yield connection
        connection.commit()
        print("✓ 커밋 완료")
    except Exception as e:
        connection.rollback()
        print(f"✗ 롤백: {e}")
        raise
    finally:
        connection.close()
        print("연결 종료")

# 사용
with database_transaction(conn) as db:
    db.execute("INSERT INTO users VALUES (...)")
    db.execute("UPDATE accounts SET ...")
# 자동으로 커밋/롤백/종료
```

## 7. 실무 베스트 프랙티스

### ❌ 피해야 할 패턴

```python
# 1. 모든 예외 무시 (절대 금지!)
try:
    critical_operation()
except:
    pass  # 에러를 숨김 - 디버깅 불가능

# 2. 너무 넓은 try 범위
try:
    step1 = safe_operation()
    step2 = risky_operation()  # 여기만 에러 날 수 있음
    step3 = safe_operation()
except Exception:
    print("뭔가 잘못됨")  # 어디서 에러났는지 모름

# 3. Exception을 너무 광범위하게 잡기
try:
    do_something()
except Exception:  # 너무 넓음
    print("에러")

# 4. 의미없는 에러 메시지
try:
    process_data(data)
except Exception as e:
    print("에러 발생")  # 무슨 에러인지 알 수 없음

# 5. 에러를 잡고 다시 발생 (불필요)
try:
    operation()
except ValueError as e:
    raise ValueError(e)  # 그냥 안 잡는게 나음
```

### ✅ 권장 패턴

```python
# 1. 구체적인 예외만 처리
try:
    user_input = int(input("숫자 입력: "))
except ValueError:  # ValueError만 잡음
    print("숫자를 입력해주세요")
    user_input = 0

# 2. 최소한의 try 범위
step1 = safe_operation()

try:
    step2 = risky_operation()  # 여기만 감쌈
except SpecificError as e:
    logging.error(f"Step2 실패: {e}")
    step2 = default_value

step3 = safe_operation()

# 3. 자세한 로깅
import logging

try:
    process_data(data)
except ValueError as e:
    logging.error(f"데이터 처리 실패: {e}", exc_info=True)
    # exc_info=True로 전체 스택 트레이스 기록
except Exception as e:
    logging.critical(
        f"예상치 못한 오류: {type(e).__name__} - {e}",
        exc_info=True
    )
    raise  # 예상 못한 에러는 다시 발생

# 4. 의미있는 에러 메시지
try:
    user = get_user(user_id)
except NotFoundError:
    raise NotFoundError(
        f"사용자를 찾을 수 없습니다 (ID: {user_id}). "
        f"데이터베이스를 확인하세요."
    )

# 5. 예외 체이닝 (원인 보존)
try:
    data = json.loads(file_content)
except json.JSONDecodeError as e:
    raise ValueError(f"설정 파일 파싱 실패: {filename}") from e
    # 'from e'로 원래 예외 보존
```

### 예외 체이닝

```python
def load_user_config(user_id):
    """
    예외 체이닝으로 원인 추적
    """
    try:
        filename = f"users/{user_id}/config.json"
        with open(filename) as f:
            config = json.load(f)
            return config
    except FileNotFoundError as e:
        raise ValueError(
            f"사용자 {user_id}의 설정 파일을 찾을 수 없습니다"
        ) from e
    except json.JSONDecodeError as e:
        raise ValueError(
            f"사용자 {user_id}의 설정 파일이 손상되었습니다"
        ) from e

# 사용
try:
    config = load_user_config(123)
except ValueError as e:
    print(f"오류: {e}")
    print(f"원인: {e.__cause__}")  # 원래 예외 확인 가능
    print(f"타입: {type(e.__cause__)}")
```

### 로깅 베스트 프랙티스

```python
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def process_order(order_id):
    """로깅을 포함한 예외 처리"""

    try:
        logging.info(f"주문 처리 시작: {order_id}")

        order = fetch_order(order_id)
        payment = process_payment(order)
        ship_order(order)

        logging.info(f"주문 처리 완료: {order_id}")
        return True

    except OrderNotFoundError as e:
        logging.warning(f"주문 없음: {order_id}")
        return False

    except PaymentFailedError as e:
        logging.error(
            f"결제 실패: {order_id} - {e}",
            exc_info=True  # 스택 트레이스 포함
        )
        return False

    except Exception as e:
        logging.critical(
            f"예상치 못한 오류: {order_id} - {type(e).__name__}",
            exc_info=True
        )
        raise  # 예상 못한 에러는 재발생
```

## 8. 실전 통합 예제

### CSV 파일 처리 파이프라인

```python
import csv
import logging
from pathlib import Path

class CSVProcessingError(Exception):
    """CSV 처리 오류"""
    pass

def process_csv_file(filepath, output_path):
    """
    CSV 파일을 읽어 처리하고 결과 저장
    모든 단계에서 안전하게 에러 처리
    """

    stats = {
        "total_rows": 0,
        "processed": 0,
        "skipped": 0,
        "errors": []
    }

    input_file = None
    output_file = None

    try:
        # 1. 입력 파일 확인
        if not Path(filepath).exists():
            raise FileNotFoundError(f"파일 없음: {filepath}")

        logging.info(f"CSV 처리 시작: {filepath}")

        # 2. 파일 열기
        try:
            input_file = open(filepath, 'r', encoding='utf-8')
            output_file = open(output_path, 'w', encoding='utf-8', newline='')
        except UnicodeDecodeError:
            # UTF-8 실패시 CP949 시도
            input_file = open(filepath, 'r', encoding='cp949')
            output_file = open(output_path, 'w', encoding='utf-8', newline='')

        reader = csv.DictReader(input_file)
        writer = csv.DictWriter(
            output_file,
            fieldnames=['id', 'name', 'email', 'status']
        )
        writer.writeheader()

        # 3. 각 행 처리
        for row_num, row in enumerate(reader, start=2):
            stats["total_rows"] += 1

            try:
                # 검증
                if not row.get('email'):
                    raise ValueError("이메일 누락")

                if '@' not in row['email']:
                    raise ValueError("잘못된 이메일 형식")

                # 처리
                processed_row = {
                    'id': row.get('id', ''),
                    'name': row.get('name', ''),
                    'email': row['email'].lower().strip(),
                    'status': 'processed'
                }

                writer.writerow(processed_row)
                stats["processed"] += 1

            except (ValueError, KeyError) as e:
                # 개별 행 에러 - 기록하고 계속
                error_msg = f"라인 {row_num}: {e}"
                stats["errors"].append(error_msg)
                stats["skipped"] += 1
                logging.warning(error_msg)
                continue

        # 4. 결과 출력
        success_rate = (stats["processed"] / stats["total_rows"] * 100
                       if stats["total_rows"] > 0 else 0)

        logging.info(
            f"처리 완료: {stats['processed']}/{stats['total_rows']} "
            f"({success_rate:.1f}%), 스킵: {stats['skipped']}"
        )

        return stats

    except FileNotFoundError as e:
        logging.error(f"파일 오류: {e}")
        raise

    except PermissionError as e:
        logging.error(f"권한 오류: {filepath}")
        raise CSVProcessingError(f"파일 접근 권한 없음: {filepath}") from e

    except Exception as e:
        logging.critical(f"예상치 못한 오류: {type(e).__name__} - {e}")
        raise

    finally:
        # 5. 항상 파일 닫기
        if input_file:
            input_file.close()
        if output_file:
            output_file.close()
        logging.info("파일 리소스 해제 완료")

# 사용
try:
    stats = process_csv_file('users.csv', 'processed_users.csv')

    if stats["errors"]:
        print(f"\n⚠️  {len(stats['errors'])}개 오류 발생:")
        for error in stats["errors"][:5]:
            print(f"  - {error}")

except CSVProcessingError as e:
    print(f"CSV 처리 실패: {e}")
except Exception as e:
    print(f"치명적 오류: {e}")
```

## 핵심 요약

### 기억해야 할 원칙

1. **구체적인 예외만 잡기**
   ```python
   # ❌ except Exception:
   # ✅ except ValueError:
   ```

2. **최소한의 try 범위**
   ```python
   # 에러 날 부분만 try로 감싸기
   try:
       risky_operation()
   except SpecificError:
       handle_error()
   ```

3. **항상 로깅**
   ```python
   except Exception as e:
       logging.error(f"오류: {e}", exc_info=True)
   ```

4. **리소스는 반드시 해제**
   ```python
   # with문 사용 또는 finally에서 해제
   with open('file.txt') as f:
       data = f.read()
   ```

5. **예상 못한 에러는 재발생**
   ```python
   except KnownError:
       handle()
   except Exception as e:
       logging.critical(f"예상치 못한 오류: {e}")
       raise  # 다시 발생시켜 상위에서 처리
   ```

### 자주 쓰는 패턴

```python
# 패턴 1: 기본값 제공
try:
    value = get_value()
except NotFoundError:
    value = default_value

# 패턴 2: 재시도
for attempt in range(max_retries):
    try:
        return api_call()
    except TransientError:
        if attempt == max_retries - 1:
            raise
        time.sleep(2 ** attempt)

# 패턴 3: 리소스 정리
try:
    resource = acquire()
    use(resource)
finally:
    release(resource)

# 패턴 4: 예외 변환
try:
    low_level_operation()
except LowLevelError as e:
    raise HighLevelError("사용자 친화적 메시지") from e
```

### 언제 예외를 발생시킬까?

```python
# ✅ 예외를 발생시켜야 할 때
def withdraw(amount):
    if amount < 0:
        raise ValueError("금액은 양수여야 합니다")
    if amount > balance:
        raise InsufficientFundsError("잔액 부족")

# ✅ None/False를 반환해도 될 때
def find_user(user_id):
    users = get_all_users()
    for user in users:
        if user.id == user_id:
            return user
    return None  # 못 찾으면 None (예외 X)
```

**핵심**: 예외는 **예외적인 상황**에만 사용하고, 정상적인 흐름 제어는 if/else로!