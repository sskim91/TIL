# PII (Personally Identifiable Information)

개인 식별 정보에 대해 알아봅니다.

## 정의

**PII (Personally Identifiable Information)**: 개인을 식별하거나 추적하는 데 사용될 수 있는 정보

## 1. PII의 종류

### 직접 식별자 (Direct Identifiers)

단독으로 개인을 식별할 수 있는 정보:

- **주민등록번호**
- **여권번호**
- **운전면허번호**
- **신용카드번호**
- **계좌번호**
- **이메일 주소**
- **전화번호**
- **생체정보** (지문, 홍채, 얼굴인식 데이터)
- **IP 주소** (특정 상황에서)

### 간접 식별자 (Indirect Identifiers)

여러 개를 조합하면 개인을 식별할 수 있는 정보:

- 성명
- 생년월일
- 성별
- 주소 (우편번호, 시/구 등)
- 직장명
- 학력
- 소속

**예시:** "홍길동" + "1990년생" + "서울대 졸업" + "ABC회사 재직" → 특정 개인 식별 가능

## 2. 민감도에 따른 분류

### Sensitive PII (민감한 개인정보)

법적으로 강력히 보호되는 정보:

- 주민등록번호
- 여권번호, 운전면허번호
- **금융정보** (계좌번호, 카드번호, 신용등급)
- **의료정보** (병력, 처방 기록, 유전자 정보)
- **생체정보** (지문, 홍채, DNA)
- **범죄 경력**
- **사상/신념, 정치적 견해**

### Non-Sensitive PII (일반 개인정보)

공개되어 있거나 덜 민감한 정보:

- 성명 (공개된 경우)
- 전화번호 (공개된 경우)
- 회사 이메일 (공개된 경우)
- 우편번호

## 3. PII 보호 방법

### 마스킹 (Masking)

일부를 숨겨서 표시:

- 전화번호: `010-1234-5678` → `010-****-5678`
- 이메일: `hong@example.com` → `ho**@example.com`
- 카드번호: `1234-5678-9012-3456` → `1234-****-****-3456`
- 주민번호: `123456-1234567` → `123456-*******`

### 익명화 (Anonymization)

개인을 식별할 수 없도록 완전히 제거:

- 이름 삭제
- 식별자를 랜덤 ID로 대체
- 통계적 집계만 제공

### 가명화 (Pseudonymization)

실제 정보를 가명으로 대체:

- "홍길동" → "사용자A"
- 원본 데이터는 별도 안전한 곳에 보관
- 필요시 복원 가능 (하지만 통제됨)

### 암호화 (Encryption)

복호화 가능한 형태로 변환 (가역):

- **대칭키 암호화**: 같은 키로 암/복호화 (예: AES)
- **비대칭키 암호화**: 공개키/개인키 쌍 (예: RSA)

### 해싱 (Hashing)

복호화가 불가능한 일방향 변환 (비가역). **암호화와는 다른 범주**다.

- **단방향 해시**: 입력 → 고정 길이 출력, 역산 불가 (예: SHA-256)
- **비밀번호 저장 전용**: 단순 해시는 GPU 무차별 대입에 약함 → bcrypt, scrypt, Argon2 같은 KDF + salt 사용
- **PII 활용 예**: 이메일·전화번호를 해시해서 중복 검사·룩업 키로 사용 (단, salt 없는 해시는 rainbow table에 취약)

## 4. 관련 법규

### 한국

- **개인정보 보호법** (Personal Information Protection Act)
  - 개인정보 수집/이용/제공 시 동의 필요
  - 안전조치 의무
  - 위반 시 과태료/형사처벌
  - **2023 전면 개정** (법률 제19234호, 2023-03-14 공포, 2023-09-15 시행): 과징금 상한이 "위반행위 관련 매출액의 3%"에서 **"전체 매출액의 3% 이하"** 로 바뀌었다. 단, 산정 시 전체 매출액에서 위반행위와 관련 없는 매출액은 제외한다(제64조의2). 과징금 규정이 일원화돼 공공기관·수탁자를 포함한 모든 개인정보처리자에게 적용된다.
  - **2026 개정** (법률 제21445호, 2026-03-10 공포, 2026-09-11 시행): 원칙은 3% 그대로 두고, ① 과징금 처분 후 3년 내 고의·중과실 재위반 ② 고의·중과실로 피해 정보주체 1천만 명 이상 ③ 시정조치 명령 불이행으로 유출등 발생 중 하나면 **전체 매출액의 10% 이하** 로 가중할 수 있게 했다. 통지 대상 "유출등"에 위조·변조·훼손이 포함되고, 유출 가능성 단계의 통지도 신설됐다.

- **정보통신망법**
  - 온라인 서비스의 개인정보 보호

- **신용정보법**
  - 금융/신용 정보 보호

### 국제

- **GDPR** (EU General Data Protection Regulation)
  - EU 시민 데이터 보호
  - 잊혀질 권리
  - 위반 시 최대 전 세계 매출의 4% 또는 2천만 유로 벌금

- **CCPA** (California Consumer Privacy Act)
  - 캘리포니아 주민 데이터 보호
  - 개인정보 삭제 요청권
  - **CPRA로 개정·확장**: 2020-11 주민투표로 통과된 Proposition 24(CPRA)가 CCPA를 대체한 것이 아니라 개정했다. 개정 조항은 2023-01-01부터 시행됐고, 정정권·민감정보 이용 제한권이 추가됐으며, 집행 기관으로 California Privacy Protection Agency(CPPA)가 신설됐다. 현재는 "CCPA(as amended)"로 부른다.

- **EU AI Act** (Regulation (EU) 2024/1689)
  - 개인정보 법은 아니지만, 생체 인식·채용·신용평가처럼 PII를 다루는 AI 시스템에 위험 기반 의무를 부과한다(GDPR과 함께 적용)
  - 2024-08-01 발효 → 금지 관행·AI 리터러시 2025-02-02 적용 → 범용 AI(GPAI) 의무 2025-08-02 적용
  - 고위험 AI 의무는 원래 2026-08-02 예정이었으나 Digital Omnibus 개정(2026-07 관보 게재)으로 Annex III 독립형 고위험 시스템은 **2027-12-02**, Annex I 규제 제품 내장형은 **2028-08-02**로 연기됐다 (2026-09 기준)

- **HIPAA** (Health Insurance Portability and Accountability Act)
  - 미국 의료정보 보호

## 5. 개발 시 주의사항

### 로그 기록

- ❌ 로그에 PII를 그대로 기록하지 말 것
- ✅ 마스킹하거나 완전히 제거
- ✅ 별도 보안 로그 시스템 사용

### 데이터베이스 저장

- ✅ 민감 정보는 암호화하여 저장
- ✅ 접근 권한 엄격히 통제
- ✅ 정기적인 백업 및 보안 점검

### API 응답

- ❌ 불필요한 PII 노출 금지
- ✅ 필요한 경우만 마스킹하여 제공
- ✅ HTTPS 사용 필수

### 테스트 데이터

- ❌ 실제 PII를 테스트에 사용 금지
- ✅ 가짜 데이터 생성 도구 사용
- ✅ 프로덕션 데이터를 복사하지 말 것

## 6. PII 관련 용어

| 용어 | 설명 |
|------|------|
| **Data Minimization** | 필요한 최소한의 정보만 수집 |
| **Right to be Forgotten** | 잊혀질 권리 (데이터 삭제 요청) |
| **Data Subject** | 정보 주체 (본인) |
| **Data Controller** | 정보 관리자 (수집/처리 결정) |
| **Data Processor** | 정보 처리자 (대행) |
| **Consent** | 동의 (명시적, 자발적) |
| **Data Breach** | 정보 유출 |
| **De-identification** | 비식별화 |

## 요약

### PII란?

개인을 **식별**하거나 **추적**할 수 있는 모든 정보

### 보호 방법

1. **마스킹**: 일부 숨김 (`010-****-5678`)
2. **암호화**: 안전하게 변환
3. **접근 제어**: 권한 있는 사람만
4. **최소 수집**: 꼭 필요한 것만

### 개발자가 기억할 것

- ❌ 로그에 PII 남기지 않기
- ❌ 평문으로 저장하지 않기
- ❌ 불필요하게 수집하지 않기
- ✅ 항상 암호화
- ✅ HTTPS 사용
- ✅ 정기적인 보안 점검

## 참고 자료

- [개인정보 보호법 (한국)](https://www.privacy.go.kr/)
- [GDPR 공식 사이트](https://gdpr.eu/)
- [국가법령정보센터 — 개인정보 보호법 제64조의2 (시행 2026-09-11)](https://law.go.kr/LSW//lsLinkCommonInfo.do?lsJoLnkSeq=1020398647&chrClsCd=010202&ancYnChk=)
- [개인정보보호위원회 — 전면 개정 개인정보 보호법 9월 15일 시행 (2023)](https://m.blog.naver.com/pipcpr/223204172313)
- [California OAG — CCPA (CPRA 개정 포함)](https://oag.ca.gov/privacy/ccpa), [CPPA — About](https://cppa.ca.gov/about_us/)
- [European Commission — AI Act](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai), [EU Council — AI 규칙 간소화 최종 승인 (2026-06-29)](https://www.consilium.europa.eu/en/press/press-releases/2026/06/29/artificial-intelligence-council-gives-final-green-light-to-simplify-and-streamline-rules)
- [OWASP - PII](https://owasp.org/www-community/vulnerabilities/Information_exposure_through_query_strings_in_url)
