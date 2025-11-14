# MITM (Man-In-The-Middle) 중간자 공격

중간자 공격의 원리와 방어 방법, 그리고 Python Elasticsearch 연결에서의 실전 보안 설정에 대해 알아봅니다.

## 결론부터 말하면

MITM 공격은 **통신 중간에 끼어들어 데이터를 탈취하거나 조작하는 공격**이며, SSL/TLS 인증서 검증과 암호화로만 방어할 수 있습니다.

```python
# ❌ MITM 공격에 취약 (절대 금지!)
es = Elasticsearch(
    "https://localhost:9200",
    verify_certs=False,  # 인증서 검증 비활성화
    ssl_show_warn=False
)

# ✅ 안전한 연결
es = Elasticsearch(
    "https://localhost:9200",
    ca_certs="/path/to/ca.crt",
    verify_certs=True,  # 인증서 검증 활성화
    basic_auth=("username", "password")
)
```

## 1. MITM 공격의 본질

### 정의

**MITM (Man-In-The-Middle)**: 공격자가 두 통신 주체(클라이언트와 서버) 사이에 몰래 끼어들어, 통신 내용을 가로채거나 조작하는 공격

### 작동 원리

```
정상 통신:
[클라이언트] ←──암호화된 통신──→ [서버]

MITM 공격:
[클라이언트] ←──→ [공격자] ←──→ [서버]
                     ↓
              데이터 탈취/변조
```

**핵심 문제점**: 양쪽 모두 정상적인 통신이라고 착각

### CIA 트라이어드 위협

- **기밀성 (Confidentiality)**: 비밀번호, API 키, 개인정보 탈취
- **무결성 (Integrity)**: 데이터 변조, 악성 코드 삽입
- **인증 (Authentication)**: 신원 위장, 세션 하이재킹

## 2. 실제 공격 시나리오

### 2.1 ARP Spoofing (로컬 네트워크)

```
공격자가 같은 WiFi에 접속
→ ARP 테이블 조작으로 게이트웨이 위장
→ 모든 트래픽이 공격자 장비 경유
→ HTTP 트래픽에서 쿠키, 비밀번호 즉시 탈취
```

**도구**: Ettercap, Bettercap, arpspoof

### 2.2 DNS Spoofing

```
사용자: "bank.com에 접속하자"
공격자: 가짜 DNS 응답 전송 (bank.com → 공격자 IP)
→ 사용자는 가짜 은행 사이트에 로그인
→ 계정 정보 탈취
```

### 2.3 SSL Stripping

```
사용자: http://bank.com 접속
공격자: HTTPS를 HTTP로 다운그레이드
[사용자] ← HTTP (평문) → [공격자] ← HTTPS → [실제 서버]
→ 사용자는 평문으로 통신 (암호화 없음)
```

**도구**: sslstrip, mitmproxy

### 2.4 Rogue Certificate (가짜 인증서)

```
공격자가 자체 서명 인증서 또는 탈취한 CA로 가짜 인증서 발급
→ 클라이언트가 인증서 검증하지 않으면 (verify_certs=False)
→ 암호화된 HTTPS 트래픽도 완전히 복호화 가능
```

## 3. 탈취 가능한 정보

### 인증 정보
- 로그인 아이디/비밀번호
- Session Cookie
- JWT 토큰
- OAuth Access Token
- API 키

### 개인정보
- 신용카드 번호
- 주민등록번호
- 의료/금융 기록
- 위치 정보

### 비즈니스 정보
- 데이터베이스 접속 정보
- 내부 문서
- 거래 내역
- 소스 코드

## 4. Elasticsearch 연결에서의 MITM 취약점

### 문제가 되는 코드

```python
from elasticsearch import Elasticsearch

# ⚠️ 개발 편의를 위해 인증서 검증 비활성화
es = Elasticsearch(
    ["https://localhost:9200"],
    verify_certs=False,        # SSL 인증서 검증 안 함
    ssl_show_warn=False        # 경고도 숨김
)

# 공격자가 중간에 끼어들어도 감지 못함!
result = es.search(index="users", body={"query": {"match_all": {}}})
```

### 왜 위험한가?

```
1. 클라이언트가 서버 인증서를 검증하지 않음
2. 공격자가 가짜 인증서로 Elasticsearch 서버 위장 가능
3. 클라이언트 ←→ 공격자 ←→ 실제 서버
4. 모든 쿼리와 데이터가 공격자에게 노출
```

**탈취되는 정보**:
- Elasticsearch 쿼리 (민감한 검색어)
- 검색 결과 (개인정보, 비즈니스 데이터)
- 인증 정보 (username, password, API key)
- 인덱스 구조 및 데이터 스키마

### 안전한 연결 방법

#### 방법 1: CA 인증서 사용 (권장)

```python
from elasticsearch import Elasticsearch

es = Elasticsearch(
    ["https://es-prod.company.com:9200"],
    ca_certs="/etc/elasticsearch/certs/ca.crt",  # CA 인증서 경로
    verify_certs=True,                           # 인증서 검증 활성화
    basic_auth=("elastic", "strong_password"),
    request_timeout=30
)
```

#### 방법 2: 자체 서명 인증서 (개발/테스트)

```python
es = Elasticsearch(
    ["https://localhost:9200"],
    ca_certs="/path/to/self-signed-cert.pem",
    verify_certs=True,
    basic_auth=("elastic", "password")
)
```

#### 방법 3: 환경별 설정 분리

```python
import os
from elasticsearch import Elasticsearch

# 환경 변수로 설정 관리
ES_HOST = os.getenv("ES_HOST", "localhost:9200")
ES_VERIFY_CERTS = os.getenv("ES_VERIFY_CERTS", "true").lower() == "true"
ES_CA_CERTS = os.getenv("ES_CA_CERTS", "/etc/elasticsearch/certs/ca.crt")

# Production에서는 반드시 verify_certs=True
if os.getenv("ENV") == "production" and not ES_VERIFY_CERTS:
    raise ValueError("Production 환경에서는 SSL 인증서 검증이 필수입니다!")

es = Elasticsearch(
    [f"https://{ES_HOST}"],
    ca_certs=ES_CA_CERTS if ES_VERIFY_CERTS else None,
    verify_certs=ES_VERIFY_CERTS,
    basic_auth=(
        os.getenv("ES_USERNAME", "elastic"),
        os.getenv("ES_PASSWORD")
    )
)
```

#### 방법 4: Certificate Pinning (고급)

```python
from elasticsearch import Elasticsearch
import ssl
import hashlib

def verify_cert_fingerprint(cert_path, expected_fingerprint):
    """인증서 지문(fingerprint) 검증"""
    with open(cert_path, 'rb') as f:
        cert_data = f.read()
    fingerprint = hashlib.sha256(cert_data).hexdigest()

    if fingerprint != expected_fingerprint:
        raise ssl.SSLError(
            f"인증서 지문 불일치! MITM 공격 가능성\n"
            f"Expected: {expected_fingerprint}\n"
            f"Got: {fingerprint}"
        )

# 사전에 알고 있는 인증서 지문
EXPECTED_FINGERPRINT = "a1b2c3d4e5f6..."

verify_cert_fingerprint("/etc/elasticsearch/certs/ca.crt", EXPECTED_FINGERPRINT)

es = Elasticsearch(
    ["https://es-prod.company.com:9200"],
    ca_certs="/etc/elasticsearch/certs/ca.crt",
    verify_certs=True,
    basic_auth=("elastic", "password")
)
```

## 5. 방어 메커니즘

### 5.1 TLS/SSL 암호화

```
TLS 1.3 핸드셰이크:
1. 클라이언트 → 서버: ClientHello (지원하는 암호화 스위트)
2. 서버 → 클라이언트: ServerHello + 인증서 + 공개키
3. 클라이언트: 인증서 검증 (CA 체인, 유효기간, 도메인)
4. 양방향 암호화 키 교환 (Diffie-Hellman)
5. 통신 시작 (Perfect Forward Secrecy)

→ 중간자가 끼어들 틈 없음
```

**중요**: `verify_certs=False`는 3번 단계를 건너뜀 → MITM 공격 허용

### 5.2 HSTS (HTTP Strict Transport Security)

```python
# Flask 예시
from flask import Flask

app = Flask(__name__)

@app.after_request
def set_security_headers(response):
    # 브라우저가 강제로 HTTPS만 사용
    response.headers['Strict-Transport-Security'] = \
        'max-age=31536000; includeSubDomains; preload'
    return response
```

→ SSL Stripping 공격 방어

### 5.3 Certificate Transparency

```
모든 SSL 인증서 발급이 공개 로그에 기록
→ 불법적으로 발급된 인증서 탐지 가능
→ CA가 악의적으로 인증서 발급해도 추적 가능
```

확인 도구: https://crt.sh/

### 5.4 네트워크 레벨 방어

```
✅ VPN 사용 (암호화된 터널)
✅ IPsec (네트워크 계층 암호화)
✅ WPA3 (강력한 WiFi 암호화)
✅ ARP Spoofing 방지 (DHCP Snooping, DAI)
✅ DNSSEC (DNS 응답 무결성 검증)
```

## 6. 공격 탐지 방법

### 클라이언트 측 탐지

```python
import ssl
import socket
from datetime import datetime

def check_certificate(host, port=443):
    """SSL 인증서 검증 및 정보 출력"""
    context = ssl.create_default_context()

    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()

            # 인증서 정보
            print(f"Subject: {cert['subject']}")
            print(f"Issuer: {cert['issuer']}")
            print(f"Valid from: {cert['notBefore']}")
            print(f"Valid until: {cert['notAfter']}")
            print(f"Serial: {cert['serialNumber']}")

            # 유효기간 확인
            not_after = datetime.strptime(
                cert['notAfter'],
                '%b %d %H:%M:%S %Y %Z'
            )
            if datetime.now() > not_after:
                print("⚠️ 인증서 만료됨!")

            return cert

# 사용 예시
cert = check_certificate("elasticsearch.company.com")
```

### 네트워크 모니터링

```bash
# ARP 테이블 이상 감지
arp -a

# 동일 IP에 여러 MAC 주소가 있으면 의심
# Gateway IP에 다른 MAC이 있으면 ARP Spoofing 가능성

# Wireshark로 트래픽 분석
# - ARP 요청/응답 패턴
# - 비정상적인 SSL/TLS 핸드셰이크
# - DNS 응답 시간 및 패턴
```

## 7. 실전 체크리스트

### 개발자

```
✅ 모든 통신에 HTTPS 강제 사용
✅ verify_certs=True 필수 (프로덕션)
✅ 최신 TLS 버전 사용 (TLS 1.2+)
✅ 강력한 암호화 스위트 설정
✅ Certificate Pinning (중요 서비스)
✅ HSTS 헤더 설정
✅ 환경별 설정 분리 (dev/staging/prod)
❌ Self-signed 인증서 프로덕션 사용 금지
❌ SSL 경고 무시 금지 (ssl_show_warn=False)
❌ 하드코딩된 인증 정보 금지
```

### 인프라/DevOps

```
✅ 유효한 SSL/TLS 인증서 발급 및 관리
✅ 인증서 자동 갱신 (Let's Encrypt)
✅ 정기적인 인증서 만료 확인
✅ TLS 설정 강화 (약한 cipher suite 비활성화)
✅ IDS/IPS 설치 및 모니터링
✅ 네트워크 세그먼테이션
✅ VPN/전용선 사용
```

### 사용자

```
✅ 공공 WiFi에서 중요 작업 자제
✅ VPN 사용
✅ HTTPS 확인 (주소창 자물쇠 아이콘)
✅ 인증서 경고 무시하지 않기
✅ 브라우저/OS 최신 버전 유지
⚠️ "안전하지 않음" 경고 나오면 접속 중단
```

## 8. 실제 사례

### DigiNotar 사건 (2011)

```
네덜란드 CA 'DigiNotar'가 해킹당함
→ 공격자가 500개 이상의 가짜 인증서 발급
→ 이란 정부가 Gmail, Facebook 등에 MITM 공격
→ 30만 명 이상의 이란 시민 감시
→ DigiNotar 파산, 브라우저에서 신뢰 제거
```

**교훈**: CA도 해킹될 수 있음 → Certificate Transparency 도입

### 공공 WiFi 스니핑

```
카페/공항 WiFi에서 Wireshark 실행
→ HTTP 트래픽 평문 캡처
→ Cookie, Session ID 즉시 탈취
→ 실시간 세션 하이재킹 (로그인 우회)
```

**교훈**: 공공 WiFi에서는 항상 VPN 사용

### Superfish 사건 (2015)

```
Lenovo 노트북에 'Superfish' 애드웨어 사전 설치
→ 자체 CA 인증서 설치로 모든 HTTPS 트래픽 복호화
→ 광고 삽입 목적이었지만 MITM 공격 도구로 악용 가능
→ 개인키가 모든 기기에 동일 → 전 세계 Lenovo 사용자 위험
```

**교훈**: 루트 CA 설치는 매우 위험

## 9. 테스트 환경 설정

### 개발 환경에서 안전하게 테스트하기

```python
import os
from elasticsearch import Elasticsearch

class ElasticsearchClient:
    def __init__(self, env="development"):
        self.env = env
        self.es = self._connect()

    def _connect(self):
        """환경별 연결 설정"""
        config = {
            "development": {
                "hosts": ["https://localhost:9200"],
                "ca_certs": "./certs/dev-ca.crt",
                "verify_certs": True,  # 개발환경도 검증!
                "basic_auth": ("elastic", "dev_password")
            },
            "staging": {
                "hosts": ["https://es-staging.company.com:9200"],
                "ca_certs": "/etc/elasticsearch/certs/staging-ca.crt",
                "verify_certs": True,
                "basic_auth": (
                    os.getenv("ES_USERNAME"),
                    os.getenv("ES_PASSWORD")
                )
            },
            "production": {
                "hosts": ["https://es-prod.company.com:9200"],
                "ca_certs": "/etc/elasticsearch/certs/prod-ca.crt",
                "verify_certs": True,
                "basic_auth": (
                    os.getenv("ES_USERNAME"),
                    os.getenv("ES_PASSWORD")
                )
            }
        }

        env_config = config.get(self.env)
        if not env_config:
            raise ValueError(f"Unknown environment: {self.env}")

        # Production에서는 추가 검증
        if self.env == "production":
            self._validate_production_config(env_config)

        return Elasticsearch(**env_config)

    def _validate_production_config(self, config):
        """프로덕션 설정 검증"""
        if not config.get("verify_certs", False):
            raise ValueError(
                "❌ Production에서 verify_certs=False는 절대 금지!"
            )

        if not config.get("ca_certs"):
            raise ValueError(
                "❌ Production에서 CA 인증서는 필수!"
            )

        if not all(config.get("basic_auth", [])):
            raise ValueError(
                "❌ Production에서 인증 정보는 필수!"
            )

# 사용 예시
client = ElasticsearchClient(env=os.getenv("ENV", "development"))
```

## 요약

### MITM이란?

통신 중간에 끼어들어 **데이터를 탈취하거나 변조**하는 공격으로, **탐지가 어렵고 피해가 큼**

### 핵심 방어 수단

1. **TLS/SSL 암호화**: 통신 내용 보호
2. **인증서 검증**: 서버 신원 확인 (`verify_certs=True`)
3. **강력한 인증**: 비밀번호, API 키, 2FA
4. **HSTS**: HTTPS 강제 사용

### Elasticsearch 연결 시 필수 사항

```python
# ✅ 항상 이렇게!
es = Elasticsearch(
    ["https://es.company.com:9200"],
    ca_certs="/path/to/ca.crt",
    verify_certs=True,  # 반드시 True
    basic_auth=("user", "pass")
)

# ❌ 절대 이렇게 하지 말 것!
es = Elasticsearch(
    ["https://localhost:9200"],
    verify_certs=False  # MITM 공격 허용
)
```

### 개발자가 기억할 것

- ❌ 편의를 위해 보안을 희생하지 말 것
- ❌ `verify_certs=False`는 나쁜 습관
- ✅ 개발 환경도 올바른 보안 설정 사용
- ✅ 환경별 설정 분리 및 검증
- ✅ 인증서 만료 모니터링

## 참고 자료

- [OWASP - Man-in-the-middle attack](https://owasp.org/www-community/attacks/Manipulator-in-the-middle_attack)
- [Elasticsearch Python Client - SSL/TLS](https://elasticsearch-py.readthedocs.io/en/latest/api.html#ssl-and-authentication)
- [RFC 8446 - TLS 1.3](https://tools.ietf.org/html/rfc8446)
- [Certificate Transparency](https://certificate.transparency.dev/)
- [MDN - HSTS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security)
