# boto3: Python으로 AWS 인프라 제어하기

AWS 서비스를 Python 코드로 자동화하는 공식 SDK

## 결론부터 말하면

**boto3는 AWS의 공식 Python SDK** 다. AWS Console에서 클릭하는 모든 작업을 Python 코드로 할 수 있다.

```mermaid
flowchart LR
    subgraph "AWS 제어 방법"
        A["AWS Console<br>(웹 UI)"]
        B["AWS CLI<br>(명령어)"]
        C["boto3<br>(Python)"]
    end

    D["AWS 서비스<br>S3, EC2, Lambda..."]

    A --> D
    B --> D
    C --> D

    style C fill:#1565C0,color:#fff
```

| 방법 | 용도 | 장점 |
|------|------|------|
| AWS Console | 수동 작업, 확인 | 시각적, 직관적 |
| AWS CLI | 간단한 스크립트 | 빠른 실행, 셸 통합 |
| **boto3** | **자동화, 애플리케이션** | **프로그래밍 가능, 로직 처리** |

```python
import boto3

# S3 버킷의 파일 목록 조회
s3 = boto3.client('s3')
response = s3.list_objects_v2(Bucket='my-bucket')

for obj in response.get('Contents', []):
    print(f"{obj['Key']} - {obj['Size']} bytes")
```

**Java로 비유하면:**

| Python | Java |
|--------|------|
| boto3 | AWS SDK for Java |
| `boto3.client('s3')` | `S3Client.builder().build()` |
| `s3.list_objects_v2()` | `s3Client.listObjectsV2()` |

## 1. 왜 boto3가 필요한가?

### 만약 AWS Console만 쓴다면?

매일 아침 9시에 특정 S3 버킷의 어제 로그를 분석하고 결과를 Slack으로 보내야 한다고 하자.

**Console로 하면:**
1. 브라우저 열고 AWS 로그인
2. S3 콘솔로 이동
3. 버킷 찾아서 클릭
4. 어제 날짜 폴더로 이동
5. 파일 다운로드
6. 로컬에서 분석 스크립트 실행
7. 결과 복사해서 Slack에 붙여넣기

**매일 이걸 반복?** 시간 낭비다.

### boto3를 쓰면?

```python
import boto3
from datetime import datetime, timedelta

def daily_log_analysis():
    s3 = boto3.client('s3')

    # 어제 날짜 계산
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # S3에서 로그 가져오기
    response = s3.get_object(
        Bucket='my-logs',
        Key=f'logs/{yesterday}/access.log'
    )
    log_content = response['Body'].read().decode('utf-8')

    # 분석 로직
    error_count = log_content.count('ERROR')

    # Slack 전송 (별도 라이브러리 사용)
    send_to_slack(f"어제 에러 수: {error_count}건")

# cron으로 매일 9시에 실행
```

**자동화 완료.** 한 번 만들어두면 사람이 개입할 필요가 없다.

### boto3가 빛나는 순간들

| 상황 | 왜 boto3인가? |
|------|---------------|
| **대량 작업** | 1000개 파일 업로드? Console로는 고문이다 |
| **조건부 로직** | "파일 크기가 1GB 이상이면 다른 버킷으로" |
| **스케줄링** | 매일/매시간 자동 실행 |
| **다른 시스템 연동** | DB 조회 → S3 업로드 → Lambda 트리거 |
| **에러 처리** | 실패 시 재시도, 알림 발송 |

## 2. boto3 아키텍처: botocore 위에 세워진 SDK

### boto3와 botocore의 관계

```mermaid
flowchart TB
    subgraph "개발자가 사용"
        A["boto3<br>(고수준 SDK)"]
    end

    subgraph "내부 동작"
        B["botocore<br>(저수준 라이브러리)"]
        C["HTTP 요청/응답"]
    end

    D["AWS API"]

    A --> B
    B --> C
    C --> D

    style A fill:#1565C0,color:#fff
    style B fill:#E3F2FD,color:#000
```

| 라이브러리 | 역할 | 사용 대상 |
|------------|------|----------|
| **botocore** | AWS API 호출의 저수준 처리 (서명, 재시도, 파싱) | AWS CLI, boto3 내부 |
| **boto3** | 개발자 친화적인 고수준 인터페이스 | **Python 개발자** |

**botocore를 직접 쓸 일은 거의 없다.** boto3가 botocore를 감싸서 편리한 API를 제공한다.

### boto → boto3 역사

| 버전 | 시기 | 특징 |
|------|------|------|
| boto | 2006~ | 최초의 AWS Python SDK, 수동 유지보수 |
| boto3 | 2015~ | **현재 표준**, botocore 기반, 자동 생성 |

boto3는 AWS API 정의 파일에서 **자동으로 코드가 생성** 된다. 새 AWS 서비스가 나오면 boto3도 곧바로 지원된다.

## 3. Client vs Resource: 두 가지 인터페이스

boto3는 같은 AWS 서비스를 두 가지 방식으로 다룰 수 있다.

### Client (저수준)

AWS API와 1:1 매핑. 모든 AWS 서비스 지원.

```python
import boto3

# Client 생성
s3_client = boto3.client('s3')

# API 직접 호출
response = s3_client.list_objects_v2(Bucket='my-bucket')

# 응답은 dict
for obj in response['Contents']:
    print(obj['Key'])
```

### Resource (고수준)

객체지향 인터페이스. 일부 서비스만 지원 (S3, EC2, DynamoDB 등).

```python
import boto3

# Resource 생성
s3_resource = boto3.resource('s3')

# 객체처럼 다루기
bucket = s3_resource.Bucket('my-bucket')

# 컬렉션 순회
for obj in bucket.objects.all():
    print(obj.key)
```

### 비교

```mermaid
flowchart LR
    subgraph Client["Client (저수준)"]
        A1["s3_client.list_objects_v2()"]
        A2["응답: dict"]
    end

    subgraph Resource["Resource (고수준)"]
        B1["bucket.objects.all()"]
        B2["응답: Object 인스턴스"]
    end

    style Client fill:#E3F2FD,color:#000
    style Resource fill:#E8F5E9,color:#000
```

| 특성 | Client | Resource |
|------|--------|----------|
| **추상화 수준** | 낮음 (API 직접 호출) | 높음 (객체지향) |
| **응답 형태** | `dict` | 객체 인스턴스 |
| **서비스 지원** | **모든 서비스** | 일부 (S3, EC2, DynamoDB...) |
| **사용 권장** | 새 기능, 전체 제어 | 일반적인 CRUD 작업 |

**언제 뭘 쓸까?**

| 상황 | 선택 |
|------|------|
| S3, EC2, DynamoDB 일반 작업 | **Resource** (코드가 깔끔) |
| Resource가 지원하지 않는 서비스 | **Client** (유일한 선택) |
| 최신 API 기능 사용 | **Client** (먼저 지원됨) |
| 세밀한 제어 필요 | **Client** |

> **참고:** Resource에서도 내부 Client에 접근할 수 있다: `s3_resource.meta.client`

## 4. 실제 사용 예시

### S3: 파일 업로드/다운로드

```python
import boto3

s3 = boto3.client('s3')

# 파일 업로드
s3.upload_file(
    Filename='/local/path/data.csv',
    Bucket='my-bucket',
    Key='uploads/data.csv'
)

# 파일 다운로드
s3.download_file(
    Bucket='my-bucket',
    Key='uploads/data.csv',
    Filename='/local/path/downloaded.csv'
)

# 문자열 직접 업로드
s3.put_object(
    Bucket='my-bucket',
    Key='config/settings.json',
    Body='{"version": "1.0"}',
    ContentType='application/json'
)
```

### S3: Resource로 더 객체지향적으로

```python
import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket('my-bucket')

# 모든 파일 순회
for obj in bucket.objects.filter(Prefix='logs/'):
    print(f"{obj.key}: {obj.size} bytes")

# 파일 삭제
bucket.Object('old-file.txt').delete()

# 파일 복사
copy_source = {'Bucket': 'source-bucket', 'Key': 'original.txt'}
bucket.copy(copy_source, 'copied.txt')
```

### EC2: 인스턴스 관리

```python
import boto3

ec2 = boto3.client('ec2')

# 실행 중인 인스턴스 조회
response = ec2.describe_instances(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
)

for reservation in response['Reservations']:
    for instance in reservation['Instances']:
        print(f"ID: {instance['InstanceId']}, Type: {instance['InstanceType']}")

# 인스턴스 중지
ec2.stop_instances(InstanceIds=['i-1234567890abcdef0'])

# 인스턴스 시작
ec2.start_instances(InstanceIds=['i-1234567890abcdef0'])
```

### DynamoDB: 테이블 조작

```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

# 아이템 추가
table.put_item(Item={
    'user_id': 'user-001',
    'name': '홍길동',
    'email': 'hong@example.com'
})

# 아이템 조회
response = table.get_item(Key={'user_id': 'user-001'})
user = response.get('Item')

# 아이템 업데이트
table.update_item(
    Key={'user_id': 'user-001'},
    UpdateExpression='SET #n = :val',
    ExpressionAttributeNames={'#n': 'name'},
    ExpressionAttributeValues={':val': '김철수'}
)
```

## 5. 자격 증명 설정

boto3가 AWS API를 호출하려면 **인증 정보** 가 필요하다.

### 방법 1: 환경 변수 (가장 흔함)

```bash
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=ap-northeast-2
```

### 방법 2: 설정 파일 (~/.aws/credentials)

```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

[production]
aws_access_key_id = AKIAI44QH8DHBEXAMPLE
aws_secret_access_key = je7MtGbClwBF/2Zp9Utk/h3yCo8nvbEXAMPLEKEY
```

```python
import boto3

# default 프로파일 사용
s3 = boto3.client('s3')

# 특정 프로파일 사용
session = boto3.Session(profile_name='production')
s3_prod = session.client('s3')
```

### 방법 3: IAM Role (EC2/Lambda에서 권장)

EC2 인스턴스나 Lambda에서 실행할 때는 **IAM Role** 을 할당하면 코드에 자격 증명을 넣을 필요가 없다.

```python
# EC2에 IAM Role이 할당되어 있으면 자동으로 인증됨
import boto3
s3 = boto3.client('s3')  # 자격 증명 설정 불필요!
```

### 자격 증명 우선순위

boto3는 다음 순서로 자격 증명을 찾는다:

1. 코드에서 직접 전달한 값
2. 환경 변수 (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
3. 공유 자격 증명 파일 (`~/.aws/credentials`)
4. AWS 설정 파일 (`~/.aws/config`)
5. IAM Role (EC2, Lambda 등)

## 6. 에러 처리

```python
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

s3 = boto3.client('s3')

try:
    response = s3.get_object(Bucket='my-bucket', Key='non-existent.txt')
except NoCredentialsError:
    print("AWS 자격 증명을 찾을 수 없습니다")
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'NoSuchKey':
        print("파일이 존재하지 않습니다")
    elif error_code == 'NoSuchBucket':
        print("버킷이 존재하지 않습니다")
    elif error_code == 'AccessDenied':
        print("접근 권한이 없습니다")
    else:
        print(f"알 수 없는 에러: {error_code}")
```

**Java 비유:**
```java
// Java AWS SDK
try {
    s3Client.getObject(request);
} catch (NoSuchKeyException e) {
    // 파일 없음
} catch (S3Exception e) {
    // 기타 S3 에러
}
```

## 7. Waiter: 리소스 상태 대기

AWS 리소스 생성/삭제는 시간이 걸린다. Waiter는 원하는 상태가 될 때까지 **폴링** 한다.

```python
import boto3

ec2 = boto3.client('ec2')

# 인스턴스 시작
ec2.start_instances(InstanceIds=['i-1234567890abcdef0'])

# 인스턴스가 running 상태가 될 때까지 대기
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=['i-1234567890abcdef0'])

print("인스턴스가 실행 중입니다!")
```

| 서비스 | Waiter 예시 |
|--------|-------------|
| EC2 | `instance_running`, `instance_stopped`, `instance_terminated` |
| S3 | `bucket_exists`, `object_exists` |
| RDS | `db_instance_available`, `db_instance_deleted` |

## 8. 멀티스레딩 주의사항

**Resource는 스레드 안전하지 않다.** 멀티스레딩 시 각 스레드마다 새 Session을 만들어야 한다.

```python
import boto3
import threading

class S3Worker(threading.Thread):
    def run(self):
        # 각 스레드마다 새 세션 생성
        session = boto3.Session()
        s3 = session.resource('s3')

        # 스레드 안전한 작업
        bucket = s3.Bucket('my-bucket')
        # ...
```

**Client는 스레드 안전하다** (단, 같은 클라이언트 객체를 공유해도 됨).

## 정리

| 개념 | 설명 |
|------|------|
| **boto3** | AWS 공식 Python SDK |
| **botocore** | boto3의 저수준 기반 라이브러리 |
| **Client** | 저수준 API, 모든 서비스 지원 |
| **Resource** | 고수준 객체지향, 일부 서비스만 |
| **Session** | 자격 증명과 설정을 담는 컨테이너 |
| **Waiter** | 리소스 상태 변경까지 대기 |

```python
import boto3

# 가장 기본적인 사용법
s3 = boto3.client('s3')                    # Client
s3 = boto3.resource('s3')                  # Resource

# 리전 지정
s3 = boto3.client('s3', region_name='ap-northeast-2')

# 프로파일 지정
session = boto3.Session(profile_name='prod')
s3 = session.client('s3')
```

---

## 출처

- [boto3 공식 문서](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [boto3 GitHub](https://github.com/boto/boto3)
- [botocore PyPI](https://pypi.org/project/botocore/)
- [AWS SDK for Python (Boto3) 시작하기](https://docs.aws.amazon.com/ko_kr/pythonsdk/)
