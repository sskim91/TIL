# JWT는 어떻게 만들어지고 어떻게 깨지는가 -- 액세스 토큰, 리프레시 토큰, 그리고 알고리즘 함정

## 결론부터 말하면

JWT는 RFC 7519 기준으로 JWS(서명) 또는 JWE(암호화) 구조 모두를 포괄하지만, **실무에서 인증/인가에 흔히 쓰는 액세스 토큰 형태의 JWT는 거의 항상 서명된 JWS** 다. 즉 **암호화가 아니라 서명** 이고, 누구나 페이로드를 읽을 수 있다. 서버가 확인하는 건 단 하나 -- "내가 발급한 게 맞나?" 그래서 실무에서는 **수명이 짧은 액세스 토큰** 과 **회전(rotation)되는 리프레시 토큰** 을 짝지어 쓰고, 검증 시에는 알고리즘 화이트리스트를 강제한다. JWT가 깨지는 사고의 대부분은 결국 세 가지 -- **알고리즘 혼동, 검증 누락, 무효화 부재** 에서 나온다.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Server
    participant V as JWT Verifier
    rect rgba(21, 101, 192, 0.1)
        Note over C,V: Verification on every request
        C->>API: GET /api/me<br>Authorization: Bearer eyJhbGc...
        API->>V: verify(token, allowedAlgs=[RS256])
        V->>V: Split header.payload.signature
        V->>V: Check alg in allowlist
        V->>V: Verify signature with public key
        V->>V: Check exp, nbf, iss, aud
        V-->>API: claims OR throw
        API-->>C: 200 / 401
    end
```

이 검증 다섯 단계 중 하나만 빠뜨려도 JWT는 무용지물이 된다. 그게 이 글의 출발점이다.

---

## 1. 왜 JWT를 쓰는가 -- 세션이 풀리는 순간

전통적인 로그인은 서버가 세션을 들고 있는 방식이다. 사용자가 로그인하면 서버 메모리(또는 Redis)에 `session_id → user_id` 매핑을 저장하고, 클라이언트에는 세션 ID 쿠키를 내려준다. 이후 매 요청마다 서버는 쿠키의 세션 ID로 자신의 저장소를 조회해 사용자가 누구인지를 확인한다.

이 방식은 단일 서버에서는 깔끔하다. 그러나 서버를 두 대로 늘리는 순간 문제가 시작된다. A 서버에서 로그인한 사용자의 다음 요청이 B 서버로 갈 수 있고, B 서버는 그 세션을 모른다. 해결책은 **sticky session**(같은 사용자를 같은 서버로 고정)이거나 **공유 세션 저장소**(Redis 등)인데, 둘 다 운영 부담을 늘린다. 마이크로서비스가 10개 늘면 10개 서비스가 모두 같은 세션 저장소를 들여다보거나 인증 서버에 매번 물어봐야 한다.

JWT는 이 그림을 뒤집는다. **토큰 자체가 자기 자신을 증명하는 자료** 이기 때문에, 서버가 세션을 들고 있을 필요가 없다. 클라이언트가 매 요청마다 토큰을 들고 오고, 서버는 자기 비밀키(또는 공개키)로 그 토큰의 서명만 검증하면 된다. 어느 서버로 요청이 가든 검증 결과는 동일하다. 이 성질을 **stateless** 라고 부르고, 수평 확장과 다중 서비스 환경에 유리한 이유가 여기에 있다.

세션과 JWT의 분기가 바로 이 한 줄이다. **"인증 상태를 누가 들고 있느냐."** 세션은 서버가, JWT는 클라이언트가 들고 있다.

---

## 2. JWT의 해부도 -- 점 두 개로 나뉜 세 조각

JWT를 처음 보면 이렇게 생겼다.

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

점(`.`) 두 개로 나뉜 세 덩어리. 각각 **헤더(header) / 페이로드(payload) / 시그니처(signature)** 다.

| 부분 | 내용 | 인코딩 |
|------|------|--------|
| 헤더 | 서명 알고리즘과 토큰 타입 | base64url(JSON) |
| 페이로드 | 클레임(claims) 묶음 | base64url(JSON) |
| 시그니처 | 헤더+페이로드를 비밀키로 서명한 값 | base64url(bytes) |

헤더와 페이로드는 단순한 JSON을 base64url로 인코딩한 것이다. 여기서 가장 중요한 사실 하나 -- **base64url은 "암호화"가 아니라 "인코딩"이다.** 누구든 토큰 문자열의 두 번째 조각을 base64url 디코드하면 페이로드 JSON을 평문으로 읽을 수 있다. [jwt.io](https://jwt.io)에 토큰을 붙여넣으면 누구나 그 안을 본다. 페이로드는 평문이라고 가정하고 써야 한다.

### 2.1 표준 클레임 (RFC 7519)

페이로드는 자유롭게 키-값을 넣을 수 있지만, RFC 7519가 약속해둔 표준 클레임이 있다.

| 클레임 | 이름 | 의미 |
|--------|------|------|
| `iss` | issuer | 누가 발급했는가 |
| `sub` | subject | 이 토큰의 주인공(보통 user id) |
| `aud` | audience | 누구한테 가야 하는 토큰인가 |
| `exp` | expiration time | 언제까지 유효한가 (Unix epoch) |
| `nbf` | not before | 언제부터 유효한가 |
| `iat` | issued at | 언제 발급되었는가 |
| `jti` | JWT ID | 토큰 식별자(중복 방지/블랙리스트용) |

이 일곱 개 중 `exp`와 `aud`, `iss`는 검증 단계에서 반드시 확인해야 한다. 자세한 함정은 6장에서 다룬다.

### 2.2 시그니처 -- 진짜 보안은 여기서 나온다

시그니처는 다음 식으로 만들어진다(HS256 기준).

$$
\text{signature} = \text{HMAC-SHA256}(\text{base64url}(header) + \text{"."} + \text{base64url}(payload),\ secret)
$$

서버는 토큰을 받으면 같은 식을 다시 계산해서 마지막 조각과 비교한다. 일치하면 "내가 발급한 게 맞다"가 된다. 비밀키를 모르면 이 식을 복원할 수 없으므로 위조가 불가능하다 -- **단, 비밀키가 충분히 길고, 라이브러리가 알고리즘을 제대로 강제할 때만 그렇다.** 이 두 전제가 깨지는 사례가 6장의 함정들이다.

---

## 3. 서명 알고리즘 -- HS256, RS256, ES256 무엇을 쓸까

대표적인 알고리즘 세 가지를 비교해보자.

| 알고리즘 | 종류 | 발급에 쓰는 키 | 검증에 쓰는 키 | 어울리는 시나리오 |
|----------|------|-----------------|-----------------|-------------------|
| **HS256** | 대칭 (HMAC + SHA-256) | 같은 비밀키 | 같은 비밀키 | 단일 모놀리식 서버 |
| **RS256** | 비대칭 (RSA + SHA-256) | 개인키 | 공개키 | 다수 리소스 서버, OIDC |
| **ES256** | 비대칭 (ECDSA + SHA-256) | 개인키 | 공개키 | RS256보다 짧은 토큰, 빠른 서명 |

핵심 차이는 **키의 분리 가능성** 이다. HS256은 하나의 비밀키로 발급도 검증도 한다. 검증해야 하는 모든 서비스가 같은 비밀키를 알고 있어야 하므로, 검증자가 곧 발급자가 될 수도 있다(보안 경계가 약하다). RS256/ES256은 발급은 개인키로, 검증은 공개키로 -- 즉 **검증 권한과 발급 권한을 분리** 할 수 있다. 인증 서버만 개인키를 들고 있고, 다른 마이크로서비스들은 공개키 또는 JWKS 엔드포인트만 알면 된다. 보안 경계가 또렷해진다.

Java 진영에서 이 차이는 익숙한 풍경이다. HMAC은 `javax.crypto.Mac`이고 RSA는 `java.security.Signature`다. Spring Security 6의 OAuth2 Resource Server는 `JwkSetUri`로 발급자의 JWKS 엔드포인트를 등록해두면 공개키를 자동으로 받아와 RS256 검증을 수행한다.

```java
// Spring Security 6 -- RS256만 받도록 명시
@Bean
JwtDecoder jwtDecoder() {
    return NimbusJwtDecoder
        .withJwkSetUri("https://auth.example.com/.well-known/jwks.json")
        .jwsAlgorithm(SignatureAlgorithm.RS256)  // 알고리즘 화이트리스트
        .build();
}

@Bean
SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .oauth2ResourceServer(o -> o.jwt(Customizer.withDefaults()))
        .build();
}
```

또는 properties로도 가능하다.

```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          jwk-set-uri: https://auth.example.com/.well-known/jwks.json
          jws-algorithms: RS256
```

핵심은 `JwtDecoder`(또는 properties) 단계에서 알고리즘을 잠그는 것이다. 이게 6.1, 6.2의 함정을 막는 단 하나의 핵심 한 줄이다. `JwtConfigurer` 자체에는 알고리즘 제한 메서드가 없다는 점에 주의한다.

---

## 4. 액세스 토큰과 리프레시 토큰 -- 왜 둘로 나누었는가

여기서부터가 실무다. JWT의 가장 큰 약점은 **무효화가 어렵다** 는 점이다. 한 번 발급된 토큰은 `exp`가 지나기 전까지 유효하다. 사용자가 로그아웃 버튼을 눌러도, 비밀번호를 바꿔도, 회사에서 해고되어도 -- 그 토큰을 들고 있는 누군가가 `exp` 이전에 쓰면 통과한다.

해결책은 의외로 단순하다. **수명을 아주 짧게 만들어버리자.** 액세스 토큰을 15분짜리로 발급하면, 도난당해도 최대 15분만 유효하다. 피해 시간을 내가 통제할 수 있게 된다.

근데 사용자에게 15분마다 다시 로그인하라고 하면 폭동이 일어난다. 그래서 **리프레시 토큰** 이 등장한다. 사용자가 로그인하면 두 개의 토큰을 한꺼번에 내려준다 -- 짧은 액세스 토큰과, 액세스 토큰을 갱신하기 위한 긴 수명의 리프레시 토큰. 액세스 토큰이 만료되면 리프레시 토큰을 인증 서버에 보내 새 액세스 토큰을 받아온다. 사용자는 다시 로그인하지 않아도 되고, 도난 피해는 15분으로 제한된다.

```mermaid
sequenceDiagram
    participant C as Client
    participant Auth as Auth Server
    participant API as Resource API
    participant DB as Token Store

    rect rgba(46, 125, 50, 0.1)
        Note over C,DB: 1. Login
        C->>Auth: POST /login (id, pw)
        Auth->>DB: store refresh_token<br>(family_id, hash)
        Auth-->>C: access_token (15m)<br>refresh_token (14d)
    end

    rect rgba(21, 101, 192, 0.1)
        Note over C,API: 2. Normal API call
        C->>API: GET /resource<br>Authorization: Bearer access
        API->>API: verify JWT signature & exp
        API-->>C: 200 OK
    end

    rect rgba(245, 124, 0, 0.1)
        Note over C,DB: 3. After 15m, access token expired
        C->>API: GET /resource (expired)
        API-->>C: 401 Unauthorized
        C->>Auth: POST /token/refresh (refresh_token)
        Auth->>DB: lookup, rotate
        Auth-->>C: new access + new refresh
    end
```

두 토큰의 성격은 정반대로 설계된다.

| 항목 | 액세스 토큰 | 리프레시 토큰 |
|------|--------------|----------------|
| 수명 | 짧음 (5~15분) | 김 (7~30일) |
| 형태 | 보통 JWT | **opaque(불투명) 토큰 권장** |
| 서버 측 저장 | 저장 안 함 (stateless) | **DB에 반드시 저장** |
| 클라이언트 저장 | 메모리 또는 Authorization 헤더 | HttpOnly + Secure + SameSite 쿠키 |
| 매 API 요청에 동봉 | O | X (갱신 시에만) |
| 무효화 | `exp` 만료까지 대기 | DB에서 즉시 삭제 가능 |
| 노출 빈도 | 매 요청 | 갱신 시에만 |

이 분리에서 가장 의외인 부분은 **리프레시 토큰은 JWT가 아니어도 된다(그리고 안 쓰는 게 권장된다)** 는 것이다. 왜냐하면 리프레시 토큰은 어차피 매번 DB를 조회해 유효성을 확인해야 하기 때문이다. 즉 stateless가 아니다. 그렇다면 굳이 JWT 형태일 필요가 없다. `crypto.randomBytes(64)` 같은 무작위 문자열(opaque token)이면 충분하고, 그 편이 토큰 안에 정보를 노출하지 않는다는 점에서 더 안전하다.

토큰을 어디에 저장할지(Cookie/Authorization/Storage)에 따른 공격 표면 차이는 별도 문서에서 다룬다. 여기서 [`web/토큰을-어디에-둘-것인가...`](토큰을-어디에-둘-것인가-Cookie-Authorization-Header-Storage-5종-완전-비교.md) 를 함께 읽으면 좋다.

---

## 5. 리프레시 토큰 회전(Rotation)과 재사용 감지

수명을 분리한 것까지는 좋다. 그런데 한 가지 시나리오가 남는다. **공격자가 리프레시 토큰을 훔쳤다면?**

리프레시 토큰은 14일짜리다. 공격자는 이걸로 14일 동안 마음대로 새 액세스 토큰을 발급받을 수 있다. 액세스 토큰을 짧게 만든 의미가 사라진다. 그래서 등장하는 두 가지 기법이 **rotation** 과 **reuse detection** 이다.

**Rotation(회전)** 은 단순하다. 리프레시 토큰을 한 번 쓰면, 새 액세스 토큰과 함께 **새 리프레시 토큰** 도 같이 발급한다. 옛 리프레시 토큰은 즉시 무효화한다. 즉 리프레시 토큰은 일회용이다.

**Reuse Detection(재사용 감지)** 이 진짜 묘수다. 이미 무효화된 옛 리프레시 토큰이 다시 들어오면, 그건 **누군가 토큰을 훔쳐서 쓰는 중** 이라는 신호다. 정상 사용자라면 자기 토큰을 두 번 쓸 일이 없다(이미 새 토큰을 받았으니). 따라서 재사용이 감지되는 순간, **이 토큰의 family 전체를 무효화하고 강제 로그아웃** 시킨다.

```mermaid
flowchart TD
    A[Client submits refresh_token] --> B{Found in DB?}
    B -->|No| Z[Reject 401<br>Force re-login]
    B -->|Yes| C{Already rotated?}
    C -->|Yes -- REUSE DETECTED| D[Invalidate ENTIRE family<br>refresh tokens revoked<br>access tokens live until exp<br>unless extra check]
    C -->|No - first use| E[Mark old refresh as rotated]
    E --> F[Issue new access + new refresh<br>same family_id]
    F --> G[Return new tokens]

    style D fill:#C62828,color:#fff
    style G fill:#2E7D32,color:#fff
    style Z fill:#757575,color:#fff
```

흐름의 묘미는 이렇다. 공격자가 훔친 토큰을 한 번 쓰면 새 토큰을 받지만, 정상 사용자도 곧 자기 토큰으로 갱신을 시도한다. 둘 중 한 명은 반드시 "이미 회전된 토큰"을 들이밀게 되고 -- 바로 그 순간 양쪽 다 family째 폭파된다. 공격자도 정상 사용자도 다시 로그인해야 하지만, **공격자는 비밀번호를 모르니 거기서 끝** 이다. 토큰 도난을 자동 탐지하고 끊어내는 메커니즘이 만들어진다.

Okta는 이를 정식 기능으로 제공하며, 재사용 감지 시 `app.oauth2.token.detect_reuse` 시스템 로그 이벤트를 발생시킨다.

현실에서 이 메커니즘을 처음 켜면 가장 먼저 만나는 문제는 **정상 사용자가 공격자로 잘못 잡히는 race condition** 이다. 모바일 앱이 불안정한 네트워크에서 같은 refresh 요청을 재시도하거나, 사용자가 여러 탭을 동시에 띄워 같은 시점에 갱신하면 동일한 리프레시 토큰이 서버에 두 번 도착할 수 있다. 이를 곧장 도용으로 판정해 family를 폭파하면 멀쩡한 사용자를 강제 로그아웃시키게 된다. 실무 절충안은 둘을 함께 둔다 -- (1) **클라이언트 측에서 refresh 요청을 직렬화** (같은 시점에 단 하나의 갱신만 진행되도록 mutex나 in-flight Promise로 묶기), (2) **서버 측에서 짧은 grace window** (예: 5~10초) 동안은 동일 토큰의 중복 도착을 허용. 위에서 언급한 Okta의 grace period가 정확히 (2)의 역할이다. 둘 중 하나만 두면 상대편 시나리오에서 오탐이 그대로 노출된다.

구현의 핵심은 **token family** 라는 개념이다. 로그인 시 family_id를 발급하고, 그 family에서 회전되는 모든 리프레시 토큰을 추적한다. family 단위로 폭파한다. DB 스키마는 보통 이렇게 생겼다.

```
refresh_tokens
├─ token_id (PK)
├─ family_id      -- 같은 로그인 세션의 토큰들이 공유
├─ user_id
├─ token_hash     -- 평문 저장 금지, 해시만
├─ rotated        -- 이미 회전되었는가
├─ revoked        -- family 전체 무효화 여부
├─ expires_at
└─ created_at
```

`token_hash` 컬럼이 보이는가? 리프레시 토큰을 평문으로 DB에 저장하면 DB 유출 시 모든 사용자 토큰이 바로 새는 셈이다. 비밀번호처럼 해시해서 저장한다.

---

## 6. JWT 사용 시 피해야 할 함정 7가지

JWT는 도구다. 도구를 잘못 쓰면 서명이 된 척하면서 위조를 통과시키는 보안 사고가 된다. 실제로 RFC 8725(JWT Best Current Practices)와 그 갱신 드래프트 `rfc8725bis-04`(2026년 3월)는 그동안 발견된 사고 패턴들을 정리해 놓은 일종의 "함정 카탈로그"다. 그중 실무에서 가장 자주 만나는 일곱 가지를 추린다.

### 6.1 `alg: none` 공격 -- 서명 자체를 끄는 헤더

JWS 표준에는 `alg: none`이라는 옵션이 있다. "이 토큰은 서명이 없다"는 뜻이다. 옛날 일부 라이브러리는 헤더의 `alg` 값을 그대로 신뢰해서, 공격자가 토큰을 다음과 같이 조작하면 그대로 통과시켰다.

```
{ "alg": "none", "typ": "JWT" } . { "sub": "admin" } . (서명 부분 비움)
```

서명 검증 함수가 "alg가 none이니 서명 검증 생략"으로 동작하면 위조 토큰이 그대로 신뢰된다. 관리자 권한 탈취가 한 줄 헤더로 가능해진다.

**방어**: 검증 시 받아들일 알고리즘을 **명시적으로 지정** 한다. RFC 8725 §3.1은 라이브러리가 호출자에게 supported algorithms 목록을 강제로 받도록 요구한다.

```java
// jjwt 라이브러리 -- 자동으로 alg=none을 거부하지만, 명시가 안전하다
Jws<Claims> jws = Jwts.parser()
    .verifyWith(secretKey)
    .build()
    .parseSignedClaims(token);  // SignedClaims만 받음. UnsignedJws는 거부

// Nimbus JOSE+JWT -- 명시적으로 알고리즘 잠금
JWSVerifier verifier = new MACVerifier(secret);
JWSObject jws = JWSObject.parse(token);
if (!jws.getHeader().getAlgorithm().equals(JWSAlgorithm.HS256)) {
    throw new SecurityException("unexpected alg");
}
jws.verify(verifier);
```

### 6.2 알고리즘 혼동 (Key Confusion) -- 공개키를 HMAC 비밀키로 둔갑

이게 진짜로 흥미로운 공격이다. 서버가 RS256(비대칭)으로 토큰을 발급한다고 가정하자. 공격자가 헤더의 `alg`를 `HS256`으로 바꾸고, 공개되어 있는 **RSA 공개키를 그대로 HMAC 비밀키로 써서** 서명한다.

라이브러리가 만약 "alg에 따라 검증 함수를 골라 호출"한다면, alg가 HS256이니 HMAC 검증을 시도하고, 검증에 사용할 키로 자기가 알고 있는 RSA 키를 쓴다. 그런데 HMAC은 키 타입을 가리지 않는다 -- 바이트열이면 다 키다. 결과적으로 공개키 + HMAC + 공격자가 만든 시그니처가 맞아떨어지고, **위조 토큰이 통과** 된다.

이 공격이 무서운 이유는 RSA 공개키가 보통 진짜로 공개되어 있다는 점이다(JWKS 엔드포인트). 공격자가 따로 훔칠 게 없다.

**방어**: RFC 8725 §3.1의 핵심 원칙 -- **각 키는 정확히 하나의 알고리즘에만 쓰여야 한다.** 검증 시 알고리즘을 키와 함께 명시적으로 묶는다.

```java
// 잘못됨: alg를 토큰 헤더에서 읽어서 검증 함수를 결정
verify(token, key);  // 라이브러리가 헤더의 alg를 신뢰

// 올바름: 받을 알고리즘을 외부에서 강제
NimbusJwtDecoder decoder = NimbusJwtDecoder
    .withPublicKey(rsaPublicKey)
    .signatureAlgorithm(SignatureAlgorithm.RS256)  // RS256만 허용
    .build();
Jwt jwt = decoder.decode(token);  // 헤더 alg가 HS256이면 즉시 거부
```

### 6.3 검증(verify) 없이 디코드(decode)만 하기

실무에서 가장 흔한 사고가 이거다. JWT 라이브러리들은 보통 두 가지 함수를 제공한다.

| 함수 | 동작 |
|------|------|
| `decode()` 또는 `parse()` | 서명 검증 없이 base64url 디코드만 수행 |
| `verify()` 또는 `parseSignedClaims()` | 서명 검증 후 페이로드 반환 |

피곤한 개발자가 이런 코드를 짠다.

```javascript
// 신고하면 진짜로 사고가 나는 코드
const payload = JSON.parse(atob(token.split('.')[1]));
const userId = payload.sub;  // 이걸 신뢰...
```

이건 토큰을 "조립한 사람이 누구든 그 페이로드를 신뢰하겠다"는 코드다. 공격자가 `{"sub":"admin","exp":99999999999}` 페이로드를 만들고 시그니처를 아무 문자열로 채워서 보내도, 이 코드는 통과한다. **JWT 보안의 99%는 시그니처 검증 단계에 있다.** 그걸 건너뛰면 JWT가 아니라 그냥 base64 인코딩된 평문 JSON에 불과하다.

### 6.4 페이로드에 민감 정보 넣기

페이로드는 base64url일 뿐 평문이다. 그런데 자꾸 민감 정보를 거기에 박는 사례가 생긴다.

| 페이로드에 절대 넣지 말 것 | 페이로드에 넣어도 되는 것 |
|----------------------------|----------------------------|
| 비밀번호, 비밀번호 해시 | user id (`sub`) |
| 주민번호, 신용카드, 의료 기록 | 역할 키워드 (`role: "admin"`) |
| 세션 비밀, API 키 | 발급 시각 (`iat`), 만료 시각 (`exp`) |
| 권한 상세 목록(전부) | 토큰 식별자 (`jti`) |
| 내부 시스템 식별자 | 발급자, 청중 (`iss`, `aud`) |

권한이 자주 바뀌는 시스템에서는 권한 목록을 JWT에 박는 것 자체가 문제다. 권한을 뺏어도 토큰이 만료되기 전까지는 그 권한이 살아 있다. 권한은 매 요청마다 DB에서 조회하거나, 적어도 짧은 TTL의 캐시로 관리하는 게 안전하다. 이건 RFC 8725 §3.10의 "Do Not Trust Received Claims" 정신과도 통한다.

진짜 기밀이 필요하면 JWE(JSON Web Encryption)를 쓰거나, JWT를 쓰지 말아야 한다.

### 6.5 `exp`, `aud`, `iss` 검증 누락

검증 코드에서 시그니처만 확인하고 클레임은 신뢰하는 사례도 많다. 특히 다음 네 가지는 빠뜨리면 큰일이다.

| 클레임 | 무엇을 검증 | 누락 시 일어나는 일 |
|--------|-------------|---------------------|
| `exp` | 현재 시각 < `exp` | **무한 수명 토큰**. 한 번 발급된 토큰이 영원히 유효 |
| `nbf` | 현재 시각 ≥ `nbf` | 미래에 활성화될 토큰 또는 시계 조작 공격 |
| `aud` | 우리 서비스가 대상인가 | 다른 서비스용 토큰이 우리 서비스에서 통함 |
| `iss` | 신뢰하는 발급자인가 | 위조 발급자 토큰이 통과 |

**`aud` 검증 누락** 은 다중 리소스 서버에서 특히 자주 본다. 인증 서버가 발급한 모든 토큰이 모든 마이크로서비스에서 통하는 상태가 되는데, 사용자가 결제 API용으로 받은 토큰을 관리자 API에 그대로 던져도 통과한다. `aud`는 "이 토큰은 X 서비스용입니다"를 박아두는 자물쇠다.

라이브러리들은 보통 이런 검증을 자동으로 해주지만, **자동으로 해주는지는 반드시 확인해야 한다.** 일부 라이브러리는 명시적으로 옵션을 켜야 한다.

```java
// Spring Security 6 -- audience와 issuer를 명시적으로 검증
@Bean
JwtDecoder jwtDecoder() {
    NimbusJwtDecoder decoder = NimbusJwtDecoder
        .withJwkSetUri(jwkSetUri)
        .build();
    OAuth2TokenValidator<Jwt> withIssuer = JwtValidators.createDefaultWithIssuer(issuer);
    OAuth2TokenValidator<Jwt> withAudience = new JwtClaimValidator<List<String>>(
        "aud", aud -> aud != null && aud.contains("my-api"));
    decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(withIssuer, withAudience));
    return decoder;
}
```

한 가지 더 -- `exp`/`nbf` 검증에는 **clock skew(시계 오차) 허용치** 를 함께 설정해야 한다. 분산 환경에서 인증 서버와 리소스 서버의 시계가 미세하게 어긋나면, 방금 발급된 토큰이 "아직 활성화되지 않음(`nbf` 미달)"으로 거부되거나 정상 토큰이 만료된 것으로 오판될 수 있다. 대부분의 라이브러리는 30~60초 정도의 leeway 옵션을 제공한다 -- Nimbus의 `DefaultJWTClaimsVerifier`, jjwt의 `clockSkewSeconds()`. 너무 길면 만료된 토큰이 통과될 위험이 커지므로 보통 60초 이내가 권장된다.

### 6.6 약한 HMAC 시크릿

HS256은 시크릿이 짧으면 무차별 대입 공격으로 깨진다. JWT를 통째로 GPU 클러스터에 던져 후보 시크릿들로 시그니처를 재계산해 비교하는 도구가 공개되어 있다. 시크릿이 사전 단어이거나 16자 미만이면 분 단위로 깨진다.

RFC 8725 §3.2와 OWASP는 **충분히 긴 랜덤 바이트** 를 요구한다. 실무 가이드는 보통 **32바이트(256비트) 이상** 이다.

```bash
# 안전한 시크릿 생성
openssl rand -base64 64
# 또는
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
```

`"my-secret-key-2024"` 같은 건 시크릿이 아니다. 그건 그냥 다음 사고의 자기소개서다.

이 함정을 피하는 더 근본적인 방법은 **HS256 대신 RS256/ES256으로 가는 것** 이다. RS256은 2048비트 이상의 RSA 키, ES256은 P-256 곡선의 EC 키를 쓴다(RFC 7518 §3) -- 알고리즘별로 키 종류가 다르다는 점만 주의하면 된다. 어느 쪽이든 검증자가 개인키를 모르므로 시크릿 유출 위험이 구조적으로 작다.

### 6.7 무효화의 딜레마 -- 즉시 로그아웃이 안 된다

JWT가 stateless라는 말은 곧 "서버는 발급한 토큰을 모른다"는 뜻이다. 그래서 사용자가 로그아웃 버튼을 눌러도, 비밀번호를 바꿔도, 그 사실은 이미 발급된 액세스 토큰에는 반영되지 않는다. `exp`까지 토큰은 유효하다.

이게 JWT의 가장 큰 트레이드오프다. 완벽한 즉시 무효화는 stateless를 포기해야만 가능하다. 실무에서는 다음 네 가지 전략을 조합한다.

| 전략 | 메커니즘 | 단점 |
|------|----------|------|
| **짧은 수명 + 리프레시 토큰** | 액세스 토큰을 5~15분으로 | 완전 즉시 무효화는 불가 (최대 수명만큼 시차) |
| **`jti` 블랙리스트** | Redis에 무효화된 jti 저장, 검증 시 조회 | stateless 장점 일부 상실, Redis 의존 |
| **토큰 버전 (token versioning)** | 사용자별 `token_version` 컬럼, 페이로드에 버전 포함, DB 버전과 비교 | 매 요청 DB 조회 |
| **키 회전 (key rotation)** | 시크릿/개인키를 주기적으로 교체 | 모든 사용자 토큰 일괄 무효화(과한 충격) |

**현실적인 절충안** 은 거의 항상 비슷하다. **짧은 액세스 토큰(15분 이하) + 리프레시 토큰 회전 + 비상 시 jti 블랙리스트.** 100% 즉시 무효화는 의도적으로 포기한다. 대신 도난 시 최대 노출 시간을 통제 가능한 범위(수 분)로 좁히는 것을 목표로 삼는다.

비밀번호 변경 시에도 비슷하다. 구식 세션은 즉시 invalidate되지만, JWT 환경에서는 보통 -- (1) 사용자의 모든 리프레시 토큰을 DB에서 삭제, (2) 액세스 토큰은 `exp`까지 살려두고 다음 갱신 시점에 자연 폐기. 이 정도가 stateless의 실용적 타협점이다.

---

## 7. 정리 -- JWT 점검 체크리스트

다음 여덟 가지를 점검할 수 있으면 JWT 사용의 90%는 안전 영역에 있다.

```
□ 라이브러리에 알고리즘 화이트리스트(예: ["RS256"])를 명시했는가
□ HS256이라면 32바이트 이상의 랜덤 시크릿인가
□ RS256/ES256이라면 개인키를 안전하게 보관하고 JWKS로 공개키만 배포하는가
□ exp / nbf / iss / aud 를 모두 검증하는가
□ 페이로드에 민감 정보가 들어 있지 않은가
□ 액세스 토큰 수명이 1시간 이하인가
□ 리프레시 토큰은 DB 추적 + rotation + reuse detection이 있는가
□ 로그아웃/비밀번호 변경 시 무효화 경로가 있는가 (jti 블랙리스트 또는 token versioning)
```

JWT는 도구다. 그 도구가 무엇을 보장하는지(**서명 = 발급자 확인**)와 무엇을 보장하지 않는지(**기밀성 X, 즉시 무효화 X**)를 정확히 분리해서 이해하면, 6장의 함정 대부분은 자연스럽게 피해갈 수 있다. 반대로 "JWT를 쓰면 보안이 좋아진다"는 막연한 기대로 시작하면, RFC 8725의 함정 카탈로그를 한 번씩 다 밟아보는 것으로 끝난다.

---

## 8. 다음 단계 -- Bearer의 한계를 넘는 DPoP

이 글에서 다룬 모든 함정을 피하더라도, JWT는 본질적으로 **Bearer 토큰** 이다 -- 들고 있는 자가 곧 주인이다. 토큰이 한 번 탈취되면 공격자가 그대로 사용할 수 있다는 구조적 약점은 남는다. 5장의 rotation과 reuse detection은 "탈취 이후 피해 시간을 줄이는" 전략이지, 탈취 자체를 막지는 못한다.

이를 근본적으로 해결하려는 표준이 **DPoP(Demonstrating Proof-of-Possession, RFC 9449)** 다. 클라이언트가 자기 비대칭 키 쌍을 만들고, 발급된 액세스 토큰의 `cnf.jkt` 클레임에 그 공개키 지문(JWK Thumbprint)이 박힌다. 매 API 요청마다 클라이언트는 개인키로 서명한 짧은 수명의 proof JWT를 `DPoP` 헤더에 함께 보낸다. 결과적으로 **토큰만 훔쳐서는 사용할 수 없다** -- 클라이언트의 개인키까지 함께 훔쳐야 한다. 이를 sender-constraining이라고 부른다.

DPoP의 동작 메커니즘과 브라우저 환경에서의 구현은 [`web/Web-Crypto-API와-Passkey-DPoP...`](Web-Crypto-API와-Passkey-DPoP-브라우저에서-진짜-보안이-필요할-때.md) 에서 다룬다. 이 글에서 정리한 액세스/리프레시 토큰 모델 위에 DPoP를 얹으면 "토큰 탈취 → 그대로 사용" 시나리오 자체가 무력화된다.

---

## 출처

- [RFC 7519 -- JSON Web Token (JWT)](https://www.rfc-editor.org/rfc/rfc7519) -- JWT 본 스펙
- [RFC 8725 -- JSON Web Token Best Current Practices](https://datatracker.ietf.org/doc/html/rfc8725) -- 운영 보안 가이드
- [draft-ietf-oauth-rfc8725bis-04 (March 2026)](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-rfc8725bis-04) -- BCP 갱신 드래프트
- [RFC 7515 -- JSON Web Signature (JWS)](https://www.rfc-editor.org/rfc/rfc7515) -- 시그니처 구조 정의
- [OWASP -- JSON Web Token Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Okta Developer -- Refresh access tokens and rotate refresh tokens](https://developer.okta.com/docs/guides/refresh-tokens/main/)
- [Spring Security 6 -- OAuth2 Resource Server (JWT)](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)
- 관련 TIL: [`web/토큰을-어디에-둘-것인가...`](토큰을-어디에-둘-것인가-Cookie-Authorization-Header-Storage-5종-완전-비교.md), [`web/브라우저는-어떻게-토큰을-받아오는가...`](브라우저는-어떻게-토큰을-받아오는가-OAuth-2.1-PKCE-BFF의-시퀀스를-끝까지-따라가기.md), [`web/Web-Crypto-API와-Passkey-DPoP...`](Web-Crypto-API와-Passkey-DPoP-브라우저에서-진짜-보안이-필요할-때.md)
