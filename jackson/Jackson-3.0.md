# Jackson 3.0

Jackson 3.0의 주요 변경사항과 2.x에서 마이그레이션하는 방법을 정리합니다.

## 결론부터 말하면

Jackson 3.0은 **2025년 10월 3일 정식 출시**된 메이저 버전으로, **Java 17 필수**, **패키지명 변경** (`com.fasterxml.jackson` → `tools.jackson`), **기본값 변경** 등 2.x와 호환되지 않는 대규모 변경이 있습니다. 하지만 Java Records, Sealed Types 완벽 지원, 성능 개선, 내장된 Java 8+ 기능 지원으로 더 현대적이고 강력해졌습니다.

```java
// Jackson 3.0의 핵심 변화
// 1. 패키지명 변경
import tools.jackson.databind.ObjectMapper;
import tools.jackson.databind.json.JsonMapper;

// 2. 빌더 패턴으로 불변 객체 생성
ObjectMapper mapper = JsonMapper.builder()
    .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
    .build();

// 3. Java Records 자동 지원 (별도 설정 불필요)
public record User(String name, int age, Optional<String> email) {}

String json = mapper.writeValueAsString(new User("Alice", 30, Optional.of("alice@example.com")));
User user = mapper.readValue(json, User.class);  // 바로 동작
```

## 1. 시스템 요구사항

### Java 버전

```
기존 (2.x): Java 8+
변경 (3.0): Java 17+ (필수)
```

**왜 상향?**
- Java Records 완벽 지원
- Sealed Types 지원
- 성능 최적화
- 현대적인 Java 기능 활용

### Android

```
기존: API Level 26
변경: API Level 34 (Java Records 지원 필요)
```

## 2. Breaking Changes (호환성 깨짐)

### 📦 패키지 및 아티팩트명 변경

**Maven Coordinates:**
```xml
<!-- 기존 (2.x) -->
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.18.0</version>
</dependency>

<!-- 신규 (3.0) -->
<dependency>
    <groupId>tools.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>3.0.0</version>
</dependency>
```

**Java 패키지명:**
```java
// 기존 (2.x)
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.core.JsonFactory;

// 변경 (3.0)
import tools.jackson.databind.ObjectMapper;
import tools.jackson.databind.JsonNode;
import tools.jackson.core.TokenStreamFactory;
```

**예외: Annotations는 그대로!**
```java
// ✅ 변경 없음 (하위 호환성 유지)
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonView;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
```

### 🔄 핵심 클래스명 변경

| 2.x | 3.0 | 설명 |
|-----|-----|------|
| `JsonFactory` | `TokenStreamFactory` | 파서/생성기 팩토리 |
| `JsonParser.getText()` | `JsonParser.getString()` | 파서의 텍스트 토큰 값 가져오기 (JsonNode는 `asString()`/`stringValue()` 사용) |
| `TextNode` | `StringNode` | 문자열 노드 타입 |
| `Module` | `JacksonModule` | 모듈 인터페이스 |
| `JsonDeserializer` | `ValueDeserializer` | 커스텀 역직렬화 |
| `JsonSerializer` | `ValueSerializer` | 커스텀 직렬화 |
| `JsonStreamContext` | `TokenStreamContext` | 스트림 컨텍스트 |

**예제:**
```java
// 기존 (2.x)
JsonFactory factory = new JsonFactory();
JsonParser parser = factory.createParser(json);
JsonNode node = mapper.readTree(json);
String text = node.get("name").asText();           // 2.x JsonNode는 asText() 사용 (getText는 JsonParser 메서드)

// 변경 (3.0) — TokenStreamFactory는 추상 부모 클래스, JSON용 구체 클래스는 여전히 JsonFactory
JsonFactory factory = new JsonFactory();          // (또는 JsonFactory.builder().build())
JsonParser parser = factory.createParser(json);
JsonNode node = mapper.readTree(json);
String text = node.get("name").asString();         // JsonNode는 asString() 또는 stringValue() (getText/getString은 JsonParser 전용)
```

> **`TokenStreamFactory` vs `JsonFactory` 정확히:** Jackson 3.0의 [`TokenStreamFactory`](https://javadoc.io/static/tools.jackson.core/jackson-core/3.0.0/tools/jackson/core/TokenStreamFactory.html)는 JSON 외 다른 포맷(YAML, CBOR, XML 등)도 통합하기 위한 **추상 부모 클래스**다. `JsonFactory`는 이를 상속한 JSON 전용 구체 클래스로 그대로 사용 가능. 위 표는 "공통 추상 타입의 이름이 바뀌었다"는 의미이지, 모든 호출 위치에서 `JsonFactory`를 `TokenStreamFactory`로 치환하라는 뜻이 아니다.

### 🚨 예외 체계 개편

```java
// 기존 (2.x)
try {
    User user = mapper.readValue(json, User.class);
} catch (JsonProcessingException e) {
    log.error("Parse failed", e);
}

// 변경 (3.0)
try {
    User user = mapper.readValue(json, User.class);
} catch (JacksonException e) {  // 최상위 예외 변경
    log.error("Parse failed", e);
}
```

**새로운 예외 계층:**
```
JacksonException (최상위)
├── StreamReadException (읽기 오류)
├── StreamWriteException (쓰기 오류)
└── UnexpectedEndOfInputException (기존 JsonEOFException)
```

**실무 활용:**
```java
try {
    return mapper.readValue(json, User.class);
} catch (StreamReadException e) {
    log.error("JSON 파싱 실패: {}", e.getMessage());
    throw new InvalidJsonException("잘못된 JSON 형식", e);
} catch (UnexpectedEndOfInputException e) {
    log.error("JSON이 불완전합니다");
    throw new InvalidJsonException("JSON이 잘려있습니다", e);
} catch (JacksonException e) {
    log.error("Jackson 오류", e);
    throw new SystemException("시스템 오류", e);
}
```

## 3. 기본값 변경 (동작 변화 주의!)

### ⚙️ 직렬화/역직렬화 기본값

| 설정 | 2.x | 3.0 | 영향 |
|------|-----|-----|------|
| `FAIL_ON_UNKNOWN_PROPERTIES` | true | **false** | 알 수 없는 필드 무시 |
| `WRITE_DATES_AS_TIMESTAMPS` | true | **false** | 날짜를 ISO-8601로 출력 |
| `READ_ENUMS_USING_TO_STRING` | false | **true** | Enum을 toString()으로 읽기 |
| `FAIL_ON_TRAILING_TOKENS` | false | **true** | 후행 토큰 시 에러 |
| `INTERN_FIELD_NAMES` | true | **false** | 필드명 인턴 안 함 |

**실전 영향 예제:**

#### 1) 알 수 없는 필드 처리
```java
public class User {
    private String name;
    private int age;
    // email 필드 없음
}

String json = "{\"name\":\"Alice\",\"age\":30,\"email\":\"alice@example.com\"}";

// 2.x: UnrecognizedPropertyException 발생!
// 3.0: email 필드를 무시하고 성공

// 3.0에서 기존 동작 유지하려면:
ObjectMapper mapper = JsonMapper.builder()
    .enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
    .build();
```

#### 2) 날짜 직렬화 형식
```java
public class Event {
    private LocalDateTime timestamp;
}

Event event = new Event(LocalDateTime.of(2024, 11, 15, 10, 30));

// 2.x 출력 (JavaTimeModule 등록 + WRITE_DATES_AS_TIMESTAMPS=true 기본):
//   LocalDateTime은 epoch millis가 아니라 정수 배열로 직렬화된다 — {"timestamp": [2024,11,15,10,30]}
//   epoch millis로 출력되는 것은 java.util.Date / Instant 같은 타입.
// 3.0 출력 (WRITE_DATES_AS_TIMESTAMPS=false 기본): {"timestamp": "2024-11-15T10:30:00"}  (ISO-8601)

// 3.0에서 타임스탬프로 변경하려면:
ObjectMapper mapper = JsonMapper.builder()
    .enable(DateTimeFeature.WRITE_DATES_AS_TIMESTAMPS)
    .build();
```

#### 3) Enum 처리
```java
public enum Status {
    ACTIVE, INACTIVE;

    @Override
    public String toString() {
        return name().toLowerCase();
    }
}

// 2.x: "ACTIVE" (name() 사용)
// 3.0: "active" (toString() 사용)
```

### 🔢 중첩 깊이 제한

```
기존: 최대 1000 깊이
변경: 최대 500 깊이
```

**이유:** DoS 공격 방어 강화

```java
// 깊이 조정 — streamReadConstraints는 TokenStreamFactory 빌더에 설정한다
JsonFactory factory = JsonFactory.builder()
    .streamReadConstraints(
        StreamReadConstraints.builder()
            .maxNestingDepth(1000)  // 기존처럼 1000으로 설정
            .build()
    )
    .build();

JsonMapper mapper = JsonMapper.builder(factory).build();
```

## 4. 새로운 기능 ✨

### 1) 빌더 패턴 기반 불변성

```java
// 기존 (2.x) - Mutable. 초기 설정 완료 후 공유는 thread-safe하지만, 런타임 재설정은 안전성이 보장되지 않음
ObjectMapper mapper = new ObjectMapper();
mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);
mapper.registerModule(new JavaTimeModule());

// 신규 (3.0) - Immutable, Thread-safe
ObjectMapper mapper = JsonMapper.builder()
    .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
    .serializationInclusion(JsonInclude.Include.NON_NULL)
    .addModule(new JavaTimeModule())
    .build();
```

**장점:**
- Thread-safe한 불변 객체
- 설정 오류 방지
- 더 명확한 초기화 코드

**실무 설정 예제:**
```java
@Configuration
public class JacksonConfig {

    @Bean
    public ObjectMapper objectMapper() {
        return JsonMapper.builder()
            // 역직렬화 설정
            .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
            .enable(DeserializationFeature.ACCEPT_EMPTY_STRING_AS_NULL_OBJECT)

            // 직렬화 설정
            .disable(DateTimeFeature.WRITE_DATES_AS_TIMESTAMPS)
            .enable(SerializationFeature.INDENT_OUTPUT)
            .serializationInclusion(JsonInclude.Include.NON_NULL)

            // 타임존 설정
            .defaultTimeZone(TimeZone.getTimeZone("Asia/Seoul"))

            // Null 처리
            .defaultSetterInfo(JsonSetter.Value.forValueNulls(Nulls.AS_EMPTY))

            .build();
    }
}
```

### 2) Java 8+ 기능 내장 지원

```java
// 기존 (2.x) - 별도 모듈 등록 필수
ObjectMapper mapper = new ObjectMapper();
mapper.registerModule(new JavaTimeModule());      // java.time
mapper.registerModule(new Jdk8Module());          // Optional
mapper.registerModule(new ParameterNamesModule()); // Constructor names

// 신규 (3.0) - 자동 지원, 등록 불필요!
ObjectMapper mapper = new ObjectMapper();
// Optional, LocalDateTime, Constructor 파라미터명 모두 자동 지원
```

**자동 지원되는 타입:**
```java
public class User {
    private Optional<String> nickname;        // ✅ 자동 지원
    private LocalDateTime createdAt;          // ✅ 자동 지원
    private LocalDate birthDate;              // ✅ 자동 지원
    private Instant updatedAt;                // ✅ 자동 지원
    private Duration sessionDuration;         // ✅ 자동 지원
    private Period membershipPeriod;          // ✅ 자동 지원

    // Constructor parameter names도 자동 감지
    public User(String name, Optional<String> nickname) {
        // @JsonProperty 애노테이션 없이도 동작!
    }
}
```

**실전 예제:**
```java
// Optional 처리
public class UserProfile {
    private String name;                    // 필수
    private Optional<String> bio;           // 선택
    private Optional<String> website;       // 선택
}

// JSON → Object
String json = "{\"name\":\"Alice\",\"bio\":\"Developer\"}";
UserProfile profile = mapper.readValue(json, UserProfile.class);

profile.getName();        // "Alice"
profile.getBio();         // Optional.of("Developer")
profile.getWebsite();     // Optional.empty()

// Object → JSON (기본 매퍼 — 빈 Optional은 null로 직렬화되어 그대로 출력됨)
String output = mapper.writeValueAsString(profile);
// {"name":"Alice","bio":"Developer","website":null}

// 빈 Optional을 응답에서 제외하려면 Include.NON_ABSENT를 명시 설정해야 한다
ObjectMapper compactMapper = JsonMapper.builder()
    .serializationInclusion(JsonInclude.Include.NON_ABSENT)   // null + Optional.empty() 모두 제외
    .build();
String compact = compactMapper.writeValueAsString(profile);
// {"name":"Alice","bio":"Developer"}
```

### 3) Java Records 완벽 지원

```java
// Java Record (Java 17+)
public record User(
    @JsonProperty("user_name") String name,
    int age,
    Optional<String> email,
    LocalDateTime createdAt
) {
    // Compact constructor
    public User {
        if (age < 0) {
            throw new IllegalArgumentException("Age must be positive");
        }
    }
}

// Jackson 3.0에서 바로 동작 (별도 설정 불필요)
ObjectMapper mapper = new ObjectMapper();

User user = new User("Alice", 30, Optional.of("alice@example.com"), LocalDateTime.now());
String json = mapper.writeValueAsString(user);
// {"user_name":"Alice","age":30,"email":"alice@example.com","createdAt":"2024-11-15T10:30:00"}

User deserialized = mapper.readValue(json, User.class);
```

**Record의 장점:**
- 불변 객체 (Thread-safe)
- 자동 `equals()`, `hashCode()`, `toString()`
- 간결한 코드
- `@JsonCreator` 자동 감지

**복잡한 Record 예제:**
```java
public record ApiResponse<T>(
    boolean success,
    Optional<T> data,
    Optional<String> errorMessage,
    LocalDateTime timestamp
) {
    // 정적 팩토리 메서드
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(true, Optional.of(data), Optional.empty(), LocalDateTime.now());
    }

    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, Optional.empty(), Optional.of(message), LocalDateTime.now());
    }
}

// 사용
ApiResponse<User> response = ApiResponse.success(user);
String json = mapper.writeValueAsString(response);
```

### 4) Sealed Types 자동 감지

```java
// Sealed interface (Java 17+)
public sealed interface Payment permits CreditCard, BankTransfer, Cash {}

public final class CreditCard implements Payment {
    private String cardNumber;
    private String cvv;
}

public final class BankTransfer implements Payment {
    private String accountNumber;
    private String bankCode;
}

public final class Cash implements Payment {
    private BigDecimal amount;
}

// Jackson 3.0의 sealed type 지원은 "subtype 목록을 자동 감지"하는 것이지
// 다형성 역직렬화 자체를 자동 활성화하는 것은 아니다.
// → @JsonSubTypes는 불필요하지만, @JsonTypeInfo로 type discriminator는 여전히 명시 필요.
@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, include = JsonTypeInfo.As.PROPERTY, property = "type")
public sealed interface Payment permits CreditCard, BankTransfer, Cash {}

ObjectMapper mapper = JsonMapper.builder().build();

String json = """
    {
        "type": "CreditCard",
        "cardNumber": "1234-5678-9012-3456",
        "cvv": "123"
    }
    """;

Payment payment = mapper.readValue(json, Payment.class);
// CreditCard 인스턴스로 자동 역직렬화됨 (@JsonSubTypes 없이도 OK)
```

**Sealed Class 활용:** (다형성 역직렬화는 여전히 `@JsonTypeInfo` 필요)
```java
@JsonTypeInfo(use = JsonTypeInfo.Id.NAME, include = JsonTypeInfo.As.PROPERTY, property = "type")
public sealed abstract class Shape permits Circle, Rectangle, Triangle {
    public abstract double area();
}

public final class Circle extends Shape {
    private double radius;

    @Override
    public double area() {
        return Math.PI * radius * radius;
    }
}

public final class Rectangle extends Shape {
    private double width;
    private double height;

    @Override
    public double area() {
        return width * height;
    }
}

// @JsonTypeInfo로 다형성 활성화 + sealed permits로 subtype 자동 감지
List<Shape> shapes = mapper.readValue(jsonArray, new TypeReference<List<Shape>>() {});
```

## 5. 제거된 기능 ❌

### 삭제된 메서드들

```java
// ❌ 제거됨
mapper.canSerialize(MyClass.class);
mapper.canDeserialize(JavaType.class);

JsonNode node = mapper.readTree(json);
Iterator<Map.Entry<String, JsonNode>> fields = node.fields();  // 제거

// ✅ 대안 (Jackson 3.0 신규 API)
Collection<String> propertyNames = node.propertyNames();   // Iterator가 아닌 Collection 반환
node.properties().forEach(entry -> {           // properties()는 Set<Map.Entry<String, JsonNode>>
    // 처리: entry.getKey(), entry.getValue()
});
// 또는 forEachEntry로 한번에:
node.forEachEntry((name, value) -> { /* 처리 */ });

// ❌ URL 기반 메서드 제거
mapper.readValue(new URL("http://example.com/data.json"), MyClass.class);

// ✅ 대안: 직접 가져오기
String json = fetchFromUrl("http://example.com/data.json");
MyClass obj = mapper.readValue(json, MyClass.class);
```

### 기타 제거된 기능

- **포맷 자동 감지** 제거
- `ObjectCodec` 제거
- 일부 deprecated API 완전 제거

## 6. 모듈별 변경사항

### YAML 모듈

```xml
<!-- 기존 (2.x): SnakeYAML -->
<dependency>
    <groupId>com.fasterxml.jackson.dataformat</groupId>
    <artifactId>jackson-dataformat-yaml</artifactId>
    <version>2.18.0</version>
</dependency>

<!-- 신규 (3.0): SnakeYAML Engine -->
<dependency>
    <groupId>tools.jackson.dataformat</groupId>
    <artifactId>jackson-dataformat-yaml</artifactId>
    <version>3.0.0</version>
</dependency>
```

**SnakeYAML Engine 장점:**
- 더 현대적인 API
- 성능 개선
- 보안 강화

### Afterburner / Mr Bean

```
기존: ASM (바이트코드 조작)
변경: ByteBuddy (더 안정적, 더 빠름)
```

**성능 개선:**
- 직렬화 5-10% 빠름
- 역직렬화 5-10% 빠름
- 메모리 사용량 감소

### 데이터 포맷 (CSV, XML 등)

```java
// Feature 이름 통일 및 명확화
// CSV
import tools.jackson.dataformat.csv.CsvReadFeature;
import tools.jackson.dataformat.csv.CsvWriteFeature;

CsvMapper mapper = CsvMapper.builder()
    .enable(CsvReadFeature.TRIM_SPACES)
    .enable(CsvWriteFeature.ALWAYS_QUOTE_STRINGS)
    .build();

// XML
import tools.jackson.dataformat.xml.XmlReadFeature;
import tools.jackson.dataformat.xml.XmlWriteFeature;

XmlMapper xmlMapper = XmlMapper.builder()
    .enable(XmlReadFeature.ALLOW_COMMENTS)
    .enable(XmlWriteFeature.WRITE_XML_DECLARATION)
    .build();
```

## 7. 마이그레이션 가이드

### 단계별 업그레이드 체크리스트

```markdown
□ Java 17+ 사용 확인
  - `java -version` 실행
  - IDE 프로젝트 설정 확인

□ Maven/Gradle dependency 업데이트
  - groupId: `tools.jackson`으로 변경
  - 버전: `3.0.0`으로 변경

□ import 문 변경
  - `com.fasterxml.jackson` → `tools.jackson`
  - Annotation은 그대로 유지

□ 클래스명 변경
  - `JsonFactory` → `TokenStreamFactory`
  - `Module` → `JacksonModule`
  - `getText()` → `getString()`

□ 예외 처리 변경
  - `JsonProcessingException` → `JacksonException`
  - 세부 예외 타입 확인

□ 기본값 변경 확인
  - 날짜 직렬화 형식 (타임스탬프 → ISO-8601)
  - 알 수 없는 필드 처리 (에러 → 무시)
  - Enum 직렬화 (name() → toString())

□ 삭제된 메서드 대체
  - `canSerialize()`, `canDeserialize()` 제거
  - `fields()` → `propertyNames()` / `properties()` / `forEachEntry()` (Jackson 3.0 신규 API)

□ ObjectMapper 빌더 패턴 적용
  - 설정 코드를 빌더 방식으로 변경

□ 통합 테스트 실행
  - 직렬화/역직렬화 테스트
  - API 응답 형식 확인

□ 성능 테스트
  - 벤치마크 실행
  - 메모리 사용량 확인
```

### Gradle 마이그레이션

```gradle
// 기존 (2.x)
dependencies {
    implementation 'com.fasterxml.jackson.core:jackson-databind:2.18.0'
    implementation 'com.fasterxml.jackson.datatype:jackson-datatype-jsr310:2.18.0'
    implementation 'com.fasterxml.jackson.datatype:jackson-datatype-jdk8:2.18.0'
    implementation 'com.fasterxml.jackson.module:jackson-module-parameter-names:2.18.0'
}

// 변경 (3.0)
dependencies {
    implementation 'tools.jackson.core:jackson-databind:3.0.0'
    // java.time, Optional, parameter names는 내장되어 불필요
}
```

### Maven 마이그레이션

```xml
<!-- 기존 (2.x) -->
<dependencies>
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.18.0</version>
    </dependency>
    <dependency>
        <groupId>com.fasterxml.jackson.datatype</groupId>
        <artifactId>jackson-datatype-jsr310</artifactId>
        <version>2.18.0</version>
    </dependency>
</dependencies>

<!-- 변경 (3.0) -->
<dependencies>
    <dependency>
        <groupId>tools.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>3.0.0</version>
    </dependency>
</dependencies>
```

### 코드 마이그레이션 예제

```java
// ========== Before (Jackson 2.x) ==========
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

public class JacksonConfig {
    public ObjectMapper createMapper() {
        ObjectMapper mapper = new ObjectMapper();

        // 모듈 등록
        mapper.registerModule(new JavaTimeModule());

        // 설정
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        mapper.configure(DateTimeFeature.WRITE_DATES_AS_TIMESTAMPS, false);
        mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);

        return mapper;
    }

    public void processJson(String json) throws JsonProcessingException {
        try {
            User user = mapper.readValue(json, User.class);
            processUser(user);
        } catch (JsonProcessingException e) {
            log.error("Parse failed", e);
            throw e;
        }
    }
}

// ========== After (Jackson 3.0) ==========
import tools.jackson.databind.ObjectMapper;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.SerializationFeature;
import tools.jackson.databind.json.JsonMapper;
import tools.jackson.core.JacksonException;

public class JacksonConfig {
    public ObjectMapper createMapper() {
        // 빌더 패턴 + Java 8+ 모듈 자동 로드
        return JsonMapper.builder()
            .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
            .disable(DateTimeFeature.WRITE_DATES_AS_TIMESTAMPS)
            .serializationInclusion(JsonInclude.Include.NON_NULL)
            .build();
    }

    public void processJson(String json) throws JacksonException {
        try {
            User user = mapper.readValue(json, User.class);
            processUser(user);
        } catch (JacksonException e) {  // 예외 타입 변경
            log.error("Parse failed", e);
            throw e;
        }
    }
}
```

## 8. 실무 전환 전략

### 점진적 마이그레이션 (대규모 프로젝트)

**Phase 1: 준비 (1주)**
```bash
# 1. Java 17 업그레이드
sdk install java 17.0.9-tem
sdk use java 17.0.9-tem

# 2. Jackson 버전 확인
./gradlew dependencies | grep jackson

# 3. 테스트 커버리지 확보
./gradlew test jacocoTestReport
```

**Phase 2: 별도 브랜치에서 테스트 (2주)**
```bash
git checkout -b feat/jackson-3-migration

# 1. Dependency 변경
# 2. import 문 변경 (IDE 기능 활용)
# 3. 컴파일 에러 수정
# 4. 테스트 실행

./gradlew clean build
./gradlew test
```

**Phase 3: 통합 및 배포 (1주)**
```bash
# 1. 스테이징 환경 배포
# 2. 통합 테스트
# 3. 성능 테스트
# 4. 프로덕션 배포 (카나리, 블루-그린)
```

### IntelliJ IDEA 마이그레이션 도움

```
1. Structural Search and Replace
   - Edit → Find → Replace Structurally
   - Pattern: com.fasterxml.jackson.$rest$
   - Replacement: tools.jackson.$rest$

2. Refactoring
   - 클래스명 변경: Shift + F6
   - 메서드명 변경: Shift + F6

3. Migration
   - Analyze → Run Inspection by Name
   - "Deprecated API usage" 검사
```

### 호환성 레이어 (임시 방안)

```java
// 과도기에 2.x와 3.0 동시 지원
public class ObjectMapperFactory {

    public static ObjectMapper createMapper() {
        try {
            // Jackson 3.0 시도
            Class.forName("tools.jackson.databind.json.JsonMapper");
            return createJackson3Mapper();
        } catch (ClassNotFoundException e) {
            // Jackson 2.x 폴백
            return createJackson2Mapper();
        }
    }

    private static ObjectMapper createJackson3Mapper() {
        return tools.jackson.databind.json.JsonMapper.builder()
            .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
            .build();
    }

    private static ObjectMapper createJackson2Mapper() {
        ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        return mapper;
    }
}
```

## 9. 실전 예제

### RESTful API 직렬화

```java
// Spring Boot Controller
@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    @Autowired
    private ObjectMapper objectMapper;

    @PostMapping
    public ResponseEntity<ApiResponse<User>> createUser(@RequestBody UserRequest request) {
        User user = userService.create(request);

        // Jackson 3.0으로 자동 직렬화
        return ResponseEntity.ok(ApiResponse.success(user));
    }

    @GetMapping("/{id}")
    public ResponseEntity<String> getUserAsJson(@PathVariable Long id) throws JacksonException {
        User user = userService.findById(id);

        // 수동 직렬화
        String json = objectMapper.writeValueAsString(user);
        return ResponseEntity.ok(json);
    }
}

// DTO with Record
public record UserRequest(
    @JsonProperty("user_name")
    String name,

    @Email
    String email,

    @Min(0) @Max(150)
    int age,

    Optional<String> bio
) {}

public record ApiResponse<T>(
    boolean success,
    Optional<T> data,
    Optional<String> error,
    LocalDateTime timestamp
) {
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(true, Optional.of(data), Optional.empty(), LocalDateTime.now());
    }

    public static <T> ApiResponse<T> error(String message) {
        return new ApiResponse<>(false, Optional.empty(), Optional.of(message), LocalDateTime.now());
    }
}
```

### 커스텀 직렬화/역직렬화

```java
// Jackson 3.0 커스텀 Serializer
public class MoneySerializer extends ValueSerializer<BigDecimal> {

    @Override
    public void serialize(BigDecimal value, JsonGenerator gen, SerializationContext ctxt)
            throws JacksonException {                                  // 3.0: SerializationContext (구 SerializerProvider)
        gen.writeNumber(value.setScale(2, RoundingMode.HALF_UP));
    }
}

// Jackson 3.0 커스텀 Deserializer
public class MoneyDeserializer extends ValueDeserializer<BigDecimal> {

    @Override
    public BigDecimal deserialize(JsonParser p, DeserializationContext ctxt)
            throws JacksonException {
        String value = p.getValueAsString();
        return new BigDecimal(value).setScale(2, RoundingMode.HALF_UP);
    }
}

// 사용
public class Order {
    @JsonSerialize(using = MoneySerializer.class)
    @JsonDeserialize(using = MoneyDeserializer.class)
    private BigDecimal totalAmount;
}
```

## 핵심 요약

### Breaking Changes Top 5

1. **패키지명 변경**: `com.fasterxml.jackson` → `tools.jackson`
2. **Java 17 필수**: Java 8/11 사용 불가
3. **클래스명 변경**: `JsonFactory` → `TokenStreamFactory` 등
4. **예외 체계 변경**: `JsonProcessingException` → `JacksonException`
5. **기본값 변경**: 날짜 형식, 알 수 없는 필드 처리 등

### 새로운 기능 Top 5

1. **빌더 패턴**: 불변 `ObjectMapper` 생성
2. **Java 8+ 내장**: Optional, java.time 자동 지원
3. **Records 지원**: Java Records 완벽 지원
4. **Sealed Types**: `permits`로 선언된 subtype 목록 자동 감지 (`@JsonSubTypes` 불필요). 단, type discriminator 활성화는 여전히 `@JsonTypeInfo`로 명시 필요
5. **성능 개선**: 5-10% 빠른 직렬화/역직렬화

### 언제 업그레이드?

**✅ 지금 바로:**
- 새 프로젝트 시작
- Java 17+ 사용 중
- Records, Sealed Types 활용
- Spring Framework 7.0 사용

**⏸️ 대기 권장:**
- Java 8/11 사용 중 (필수 요구사항)
- 레거시 시스템 (리스크 높음)
- 서드파티 라이브러리가 3.0 미지원

### 마이그레이션 난이도

- **소규모 프로젝트**: 🟢 쉬움 (1-2일)
  - import 변경과 테스트만으로 완료

- **중규모 프로젝트**: 🟡 보통 (1주)
  - 커스텀 Serializer/Deserializer 수정 필요

- **대규모 레거시**: 🔴 어려움 (2주+)
  - 서드파티 라이브러리 호환성 확인
  - 광범위한 테스트 필요

### 참고 자료

- [공식 릴리즈 노트](https://github.com/FasterXML/jackson/wiki/Jackson-Release-3.0)
- [마이그레이션 가이드](https://github.com/FasterXML/jackson/blob/main/jackson3/MIGRATING_TO_JACKSON_3.md)
- [Jackson 3.0.0 (GA) released 블로그](https://cowtowncoder.medium.com/jackson-3-0-0-ga-released-1f669cda529a)
