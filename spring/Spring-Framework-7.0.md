# Spring Framework 7.0

Spring Framework 7.0 GA 릴리즈의 주요 변경사항과 새로운 기능을 정리합니다.

## 결론부터 말하면

Spring Framework 7.0은 **2025년 11월 13일 정식 출시**된 차세대 프레임워크로, **Jakarta EE 11**, **Jackson 3.0**, **JDK 25**를 지원하며 Spring Boot 4.0의 기반이 됩니다. Java 17 최소 요구사항은 유지되지만, 많은 레거시 기능들이 제거되었고 특히 **javax 패키지 지원이 완전히 중단**되었습니다.

```java
// Spring 7.0의 주요 변화
// 1. Jackson 3.x 기본 지원
ObjectMapper mapper = JsonMapper.builder().build();  // tools.jackson 패키지

// 2. 회복력 기능 내장
@Service
@EnableResilientMethods
public class UserService {
    @Retryable(maxRetries = 2)
    @ConcurrencyLimit(10)
    public User getUser(Long id) {
        return userRepository.findById(id);
    }
}

// 3. API 버전 관리
@GetMapping(path = "/users", version = "1")
public List<UserV1> getUsersV1() { ... }

@GetMapping(path = "/users", version = "2")
public List<UserV2> getUsersV2() { ... }
```

## 1. 시스템 요구사항

### Java 버전

```
최소: JDK 17
권장: JDK 25 LTS
```

**왜 JDK 25를 권장?**
- Virtual Threads 성능 최적화
- 최신 GraalVM 네이티브 이미지 지원
- 향후 Spring 업데이트에서 JDK 25 기능 활용 예정

### 주요 의존성 업그레이드

| 항목 | 6.x | 7.0 |
|------|-----|-----|
| Jakarta EE | 10 | **11** |
| Servlet | 6.0 | **6.1** |
| JPA | 3.1 | **3.2** |
| Tomcat | 10.1 | **11.0** |
| Jetty | 12.0 | **12.1** |
| Hibernate ORM | 6.x | **7.1/7.2** |
| Kotlin | 2.0 | **2.2** |
| JUnit | 5 | **6** |
| Netty | 4.1 | **4.2** |
| GraalVM | 23/24 | **25** |

## 2. Breaking Changes (호환성 깨짐)

### javax 패키지 완전 제거 ❌

```java
// ❌ 더 이상 작동 안 함 (Spring 7.0)
import javax.annotation.Resource;
import javax.inject.Inject;
import javax.validation.Valid;

@Resource
private DataSource dataSource;

// ✅ 변경 필요 (Jakarta 패키지 사용)
import jakarta.annotation.Resource;
import jakarta.inject.Inject;
import jakarta.validation.Valid;

@Resource
private DataSource dataSource;
```

**영향받는 주요 애노테이션:**
- `@javax.annotation.Resource` → `@jakarta.annotation.Resource`
- `@javax.inject.Inject` → `@jakarta.inject.Inject`
- `@javax.validation.Valid` → `@jakarta.validation.Valid`
- `@javax.persistence.*` → `@jakarta.persistence.*`

### spring-jcl 모듈 제거

```xml
<!-- ❌ Spring 7.0에서 제거됨 -->
<dependency>
    <groupId>org.springframework</groupId>
    <artifactId>spring-jcl</artifactId>
</dependency>

<!-- ✅ Apache Commons Logging 1.3.0 직접 사용 -->
<dependency>
    <groupId>commons-logging</groupId>
    <artifactId>commons-logging</artifactId>
    <version>1.3.0</version>
</dependency>
```

### ListenableFuture 제거

```java
// ❌ 제거됨
import org.springframework.util.concurrent.ListenableFuture;

ListenableFuture<User> future = asyncService.getUser(id);
future.addCallback(
    user -> log.info("Success: {}", user),
    ex -> log.error("Failed", ex)
);

// ✅ CompletableFuture 사용
import java.util.concurrent.CompletableFuture;

CompletableFuture<User> future = asyncService.getUser(id);
future
    .thenAccept(user -> log.info("Success: {}", user))
    .exceptionally(ex -> {
        log.error("Failed", ex);
        return null;
    });
```

### 경로 매칭 옵션 제거

```java
// ❌ 제거된 설정들
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configurePathMatch(PathMatchConfigurer configurer) {
        configurer
            .setUseSuffixPatternMatch(true)        // 제거됨
            .setUseTrailingSlashMatch(true)        // 제거됨
            .setUseRegisteredSuffixPatternMatch(true); // 제거됨
    }
}

// ✅ 명시적 경로 매핑 사용
@GetMapping({"/users", "/users/"})  // 두 경로 모두 명시
public List<User> getUsers() { ... }
```

### Undertow 지원 중단

```xml
<!-- ❌ Spring 7.0에서 지원 안 함 -->
<dependency>
    <groupId>io.undertow</groupId>
    <artifactId>undertow-core</artifactId>
</dependency>

<!-- ✅ Tomcat 11 또는 Jetty 12 사용 -->
<dependency>
    <groupId>org.apache.tomcat.embed</groupId>
    <artifactId>tomcat-embed-core</artifactId>
    <version>11.0.0</version>
</dependency>
```

**이유:** Undertow가 Servlet 6.1을 지원하지 않음

### Theme 지원 제거

```java
// ❌ 제거됨
@Controller
public class ThemeController {
    @Autowired
    private ThemeSource themeSource;

    @GetMapping("/theme")
    public String getTheme(Model model) {
        Theme theme = themeSource.getTheme("default");
        model.addAttribute("theme", theme);
        return "themePage";
    }
}

// ✅ CSS 변수나 프론트엔드 솔루션 사용
// CSS Variables, Styled Components, Tailwind CSS 등
```

## 3. Jackson 3.0 지원

Spring 7.0은 **Jackson 3.x를 기본으로 지원**하며, 2.x는 폴백으로 동작합니다.

**핵심 변경사항:**
- 패키지명: `com.fasterxml.jackson` → `tools.jackson`
- 빌더 패턴: `JsonMapper.builder()` 사용 권장
- Java Records, Optional, java.time 자동 지원

```java
// Spring 7.0에서 Jackson 3.x 설정
import tools.jackson.databind.json.JsonMapper;
import tools.jackson.databind.SerializationFeature;

@Configuration
public class JacksonConfig {
    @Bean
    public ObjectMapper objectMapper() {
        return JsonMapper.builder()
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
            .build();
    }
}
```

**⚠️ 주의:**
- Spring 7.1에서 Jackson 2.x 자동 감지가 비활성화되고, **Spring 7.2에서 지원이 완전히 제거** 될 예정
- Annotation 패키지(`@JsonProperty` 등)는 `com.fasterxml.jackson` 유지

**📚 자세한 내용:**
Jackson 3.0의 모든 변경사항, 마이그레이션 가이드는 [Jackson 3.0 완전 정복](../jackson/Jackson-3.0-완전-정복.md)을 참조하세요.

## 4. 새로운 기능

### 1) 회복력 기능 (Resilience) 내장

**이전 (Spring 6.x):**
```xml
<!-- 별도 라이브러리 필요 -->
<dependency>
    <groupId>org.springframework.retry</groupId>
    <artifactId>spring-retry</artifactId>
</dependency>
```

```java
// 옛 spring-retry 라이브러리의 어노테이션
import org.springframework.retry.annotation.Retryable;
import org.springframework.retry.annotation.EnableRetry;
```

**이후 (Spring 7.0):** `spring-context` 모듈에 새 `@Retryable`/`@ConcurrencyLimit`/`@EnableResilientMethods`가 들어왔다. 패키지가 다르니 임포트를 반드시 새 패키지로 바꿔야 하며, 별도 `spring-retry` 의존성은 더 이상 필요 없다.

```java
// Spring Framework 7의 내장 회복력 어노테이션
import org.springframework.resilience.annotation.Retryable;
import org.springframework.resilience.annotation.ConcurrencyLimit;
import org.springframework.resilience.annotation.EnableResilientMethods;

@Configuration
@EnableResilientMethods  // @Retryable + @ConcurrencyLimit 활성화
public class AppConfig {
}

@Service
public class PaymentService {

    // 재시도: maxRetries는 "추가 재시도 횟수"(첫 호출 제외). delay/multiplier/maxDelay는 분 단위가 아니라 ms 단위로 주는 식.
    @Retryable(maxRetries = 2, delay = 1000, multiplier = 2.0, maxDelay = 10000)
    public PaymentResult processPayment(Order order) {
        return paymentGateway.charge(order);
    }

    // 동시성 제한
    @ConcurrencyLimit(10)
    public void heavyOperation() {
        // 최대 10개 동시 실행
    }
}
```

**실전 활용:**
```java
@Service
public class ExternalApiService {

    // 특정 예외만 재시도 대상으로 지정하려면 includes 속성 사용
    @Retryable(
        includes = {ConnectException.class, TimeoutException.class},
        maxRetries = 4,
        delay = 1000,
        multiplier = 2.0,
        maxDelay = 10000
    )
    public ApiResponse callExternalApi(Request request) {
        return restClient.post().uri(apiUrl).body(request).retrieve().body(ApiResponse.class);
    }
}

// Note: Spring 7 내장 @Retryable에는 spring-retry의 @Recover에 해당하는 메서드 단위 폴백이 없다.
// 모든 재시도가 소진되어 RetryException이 던져지면, 호출 측에서 try/catch로 대체 응답을 만들거나
// RetryListener를 등록하여 횡단 처리해야 한다.
```

### 2) API 버전 관리 (First-class Support)

```java
@RestController
@RequestMapping("/api")
public class UserApiController {

    // Version 1 API
    @GetMapping(path = "/users/{id}", version = "1")
    public UserV1Response getUserV1(@PathVariable Long id) {
        return userService.getUserV1(id);
    }

    // Version 2 API (새 필드 추가)
    @GetMapping(path = "/users/{id}", version = "2")
    public UserV2Response getUserV2(@PathVariable Long id) {
        return userService.getUserV2(id);
    }

    // 헤더 기반 버전 관리
    @GetMapping(
        path = "/users/{id}",
        headers = "API-Version=3"
    )
    public UserV3Response getUserV3(@PathVariable Long id) {
        return userService.getUserV3(id);
    }
}
```

**클라이언트 사용:**
```bash
# Version 1
curl http://localhost:8080/api/users/1?version=1

# Version 2
curl http://localhost:8080/api/users/1?version=2

# Version 3 (헤더)
curl -H "API-Version: 3" http://localhost:8080/api/users/1
```

**설정:** `@GetMapping(version = "...")` 매핑이 실제로 동작하려면 Spring 7의 전용 API 버전 설정 메서드를 사용해야 한다. `ContentNegotiationConfigurer`의 `parameterName(...)`은 콘텐츠 협상용이지 버전 리졸버가 아니다.

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureApiVersioning(ApiVersionConfigurer configurer) {
        configurer
            .useQueryParam("version")          // ?version=1 형태로 받기
            .useRequestHeader("API-Version")   // 또는 헤더 기반
            .setDefaultVersion("1");
    }
}
```

### 3) JPA 3.2 지원

```java
@Configuration
public class JpaConfig {

    // JPA 3.2의 PersistenceConfiguration 지원
    @Bean
    public LocalContainerEntityManagerFactoryBean entityManagerFactory(
            DataSource dataSource,
            PersistenceConfiguration config) {

        LocalContainerEntityManagerFactoryBean em =
            new LocalContainerEntityManagerFactoryBean();
        em.setDataSource(dataSource);
        em.setPersistenceConfiguration(config);  // 새로운 방식
        em.setJpaVendorAdapter(new HibernateJpaVendorAdapter());

        return em;
    }
}

// EntityManager 직접 주입
@Repository
public class UserRepository {

    @PersistenceContext
    private EntityManager em;  // 자동 주입

    public User findById(Long id) {
        return em.find(User.class, id);
    }
}

// StatelessSession 지원 (Hibernate 7)
@Repository
public class BulkOperationRepository {

    @Autowired
    private StatelessSession statelessSession;  // 새로운 지원

    public void bulkUpdate(List<User> users) {
        users.forEach(statelessSession::update);
    }
}
```

### 4) 새로운 클라이언트 API

**JmsClient (JMS 간소화):**
```java
// 기존 (JmsTemplate)
@Service
public class NotificationService {
    @Autowired
    private JmsTemplate jmsTemplate;

    public void sendNotification(Notification notification) {
        jmsTemplate.convertAndSend("notifications", notification);
    }
}

// 신규 (JmsClient — Spring 7의 destination(...) 기반 fluent API)
@Service
public class NotificationService {
    @Autowired
    private JmsClient jmsClient;

    public void sendNotification(Notification notification) {
        // 헤더는 두 번째 인자 Map으로 전달
        jmsClient.destination("notifications")
            .send(notification, Map.of("priority", "high"));
    }

    public Notification receiveNotification() {
        // withReceiveTimeout은 밀리초 단위 long
        return jmsClient.destination("notifications")
            .withReceiveTimeout(5_000L)
            .receive(Notification.class)
            .orElse(null);
    }
}
```

**JdbcClient 확장:**
```java
@Repository
public class UserRepository {
    @Autowired
    private JdbcClient jdbcClient;

    // 확장된 쿼리 설정
    public List<User> findActiveUsers(LocalDate since) {
        return jdbcClient.sql("""
            SELECT * FROM users
            WHERE active = true
            AND created_at >= :since
            ORDER BY created_at DESC
            """)
            .param("since", since)
            .withFetchSize(100)          // 새로운 옵션
            .withMaxRows(1000)           // 새로운 옵션
            .withQueryTimeout(30)        // 새로운 옵션 — 초 단위 int
            .query(User.class)
            .list();
    }
}
```

### 5) 테스트 개선

**RestTestClient (비반응형):**
```java
// WebFlux 없이도 사용 가능
@SpringBootTest
class UserControllerTest {

    @Autowired
    private WebApplicationContext context;

    private RestTestClient restClient;

    @BeforeEach
    void setUp() {
        restClient = RestTestClient.bindToApplicationContext(context)
            .baseUrl("http://localhost:8080")
            .build();
    }

    @Test
    void testGetUser() {
        restClient.get()
            .uri("/api/users/1")
            .exchange()
            .expectStatus().isOk()
            .expectBody(User.class)
            .value(user -> {
                assertThat(user.getName()).isEqualTo("Alice");
                assertThat(user.getEmail()).contains("@");
            });
    }
}
```

**@Nested 계층 의존성 주입:**
```java
@SpringBootTest
class UserServiceTest {

    @Autowired
    private UserService userService;  // 외부 클래스에서 주입

    @Nested
    class CreateUserTests {
        // Spring 7.0에서 자동으로 상속됨
        // userService 사용 가능!

        @Test
        void createValidUser() {
            User user = userService.create("Alice", "alice@example.com");
            assertThat(user.getId()).isNotNull();
        }
    }

    @Nested
    class DeleteUserTests {
        // 여기서도 userService 사용 가능

        @Test
        void deleteExistingUser() {
            userService.delete(1L);
            assertThat(userService.exists(1L)).isFalse();
        }
    }
}
```

### 6) Kotlin 코루틴 개선

```kotlin
@Service
class UserService {

    @Transactional
    suspend fun createUser(name: String): User {
        // PropagationContextElement가 자동으로 전파됨
        // 트랜잭션, 보안 컨텍스트 등이 코루틴 간 유지됨

        val user = User(name = name)
        return withContext(Dispatchers.IO) {
            userRepository.save(user)  // 트랜잭션 유지됨
        }
    }

    suspend fun processUsers(ids: List<Long>) = coroutineScope {
        ids.map { id ->
            async {
                getUser(id)  // 병렬 실행, 컨텍스트 자동 전파
            }
        }.awaitAll()
    }
}
```

## 5. 주요 API 변경

### HttpHeaders API 변경

```java
// Spring 6.x
public class OldController {
    @GetMapping("/data")
    public ResponseEntity<String> getData() {
        HttpHeaders headers = new HttpHeaders();
        // MultiValueMap 메서드 사용
        headers.add("X-Custom", "value1");
        headers.add("X-Custom", "value2");

        List<String> values = headers.get("x-custom");  // 대소문자 무시
        return ResponseEntity.ok().headers(headers).body("data");
    }
}

// Spring 7.0
public class NewController {
    @GetMapping("/data")
    public ResponseEntity<String> getData() {
        HttpHeaders headers = new HttpHeaders();
        // 대소문자 무시 특성 내장
        headers.add("X-Custom", "value1");
        headers.add("X-Custom", "value2");

        // 명시적 메서드 사용
        List<String> values = headers.getValuesAsList("X-Custom");
        return ResponseEntity.ok().headers(headers).body("data");
    }
}
```

### Null Safety 개선 (JSpecify)

```java
// 기존 (JSR 305)
import org.springframework.lang.NonNull;
import org.springframework.lang.Nullable;

public class UserService {
    @NonNull
    public User getUser(@Nullable Long id) {
        if (id == null) {
            throw new IllegalArgumentException("ID required");
        }
        return repository.findById(id).orElseThrow();
    }
}

// Spring 7.0 (JSpecify)
import org.jspecify.annotations.NonNull;
import org.jspecify.annotations.Nullable;

public class UserService {
    // 제네릭 타입에도 적용 가능
    public @NonNull List<@NonNull User> getUsers() {
        return repository.findAll();
    }

    // 배열에도 적용
    public @NonNull User @NonNull [] getUserArray() {
        return new User[10];
    }

    // 가변인수에도 적용
    public void addUsers(@NonNull User @NonNull ... users) {
        Arrays.stream(users).forEach(repository::save);
    }
}
```

### 프록시 설정 개선

```java
// Spring Framework의 기본 프록시 정책은 여전히 "인터페이스가 있으면 JDK 동적 프록시, 없으면 CGLIB"이다.
// CGLIB을 강제하려면 @EnableTransactionManagement(proxyTargetClass = true)처럼 명시해야 한다.
// (Spring Boot에서는 자동 설정이 CGLIB을 기본으로 켜는 경우가 있으니, 프레임워크 기본값과 구분해서 이해해야 한다.)
@Configuration
@EnableTransactionManagement
public class AppConfig {
}

// Spring 7의 새 @Proxyable 어노테이션으로 클래스 단위 프록시 정책을 선언한다.
// 속성은 ProxyType 열거형(INTERFACES / TARGET_CLASS)을 받는다 — proxyTargetClass 같은 boolean 속성은 없다.
import org.springframework.context.annotation.Proxyable;
import org.springframework.context.annotation.ProxyType;

@Service
@Proxyable(ProxyType.INTERFACES)  // JDK 동적 프록시 사용
public class UserService implements UserOperations {
    @Transactional
    public User getUser(Long id) {
        return repository.findById(id);
    }
}

@Service
@Proxyable(ProxyType.TARGET_CLASS)  // CGLIB 프록시 강제
public class OrderService {  // 인터페이스 없음
    @Transactional
    public Order createOrder(OrderRequest request) {
        return repository.save(new Order(request));
    }
}
```

## 6. GraalVM 네이티브 이미지 개선

### 리소스/리플렉션 힌트 — `RuntimeHintsRegistrar` 기반

Spring Framework 7의 네이티브 힌트는 옛 Spring Native(`@NativeHint`/`@TypeHint`/`@ResourceHint`) 어노테이션이 아니라 `org.springframework.aot.hint` 패키지의 프로그래밍 API와 `@RegisterReflection`/`@RegisterReflectionForBinding` 어노테이션으로 작성한다. 7.0에서는 리소스 패턴이 글롭(glob) 표기까지 지원하도록 개선되었다.

**프로그래밍 방식 — `RuntimeHintsRegistrar`:**

```java
import org.springframework.aot.hint.RuntimeHints;
import org.springframework.aot.hint.RuntimeHintsRegistrar;
import org.springframework.aot.hint.MemberCategory;

public class AppHints implements RuntimeHintsRegistrar {

    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // 클래스패스 리소스 — Spring 7부터 glob 패턴 지원
        hints.resources().registerPattern("**/*.properties");
        hints.resources().registerPattern("config/*.yml");

        // 리플렉션 힌트
        hints.reflection().registerType(com.example.model.User.class,
                MemberCategory.INVOKE_DECLARED_CONSTRUCTORS,
                MemberCategory.DECLARED_FIELDS);
    }
}
```

`RuntimeHintsRegistrar` 구현체는 `META-INF/spring/aot.factories`에 등록하거나, `@ImportRuntimeHints(AppHints.class)`로 설정 클래스에서 가져온다.

**어노테이션 방식 — `@RegisterReflectionForBinding`:**

```java
import org.springframework.aot.hint.annotation.RegisterReflectionForBinding;

@Configuration
@RegisterReflectionForBinding({UserDto.class, OrderDto.class})  // 직렬화 대상 DTO들
public class NativeConfig {
}
```

힌트 작성에 정규식이 아닌 글롭 패턴이 적용되는 영역은 주로 `ResourceHints#registerPattern(...)`이다. 옛 `@NativeHint`/`@TypeHint`는 더 이상 사용하지 않는다.

## 7. 실무 마이그레이션 가이드

### 단계별 업그레이드

**Phase 1: 준비 단계**

```bash
# 1. Java 17+ 확인
java -version

# 2. 의존성 버전 확인
./mvnw dependency:tree

# 3. Spring Boot 4.0으로 업그레이드 (Spring 7.0 기반)
```

**Phase 2: 코드 변경**

```java
// 1. javax → jakarta 변경
// IntelliJ: Replace in Path
// javax.annotation -> jakarta.annotation
// javax.inject -> jakarta.inject
// javax.validation -> jakarta.validation
// javax.persistence -> jakarta.persistence

// 2. ListenableFuture → CompletableFuture
// 전역 검색 후 변경

// 3. Jackson 3.x 마이그레이션
// com.fasterxml.jackson -> tools.jackson (annotation 제외)
```

**Phase 3: 설정 변경**

```xml
<!-- pom.xml -->
<properties>
    <java.version>17</java.version>
    <spring-framework.version>7.0.0</spring-framework.version>
    <jakarta-servlet.version>6.1.0</jakarta-servlet.version>
</properties>

<dependencies>
    <!-- Jakarta EE 11 -->
    <dependency>
        <groupId>jakarta.platform</groupId>
        <artifactId>jakarta.jakartaee-api</artifactId>
        <version>11.0.0</version>
        <scope>provided</scope>
    </dependency>

    <!-- Jackson 3.x -->
    <dependency>
        <groupId>tools.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>3.0.0</version>
    </dependency>

    <!-- Tomcat 11 -->
    <dependency>
        <groupId>org.apache.tomcat.embed</groupId>
        <artifactId>tomcat-embed-core</artifactId>
        <version>11.0.0</version>
    </dependency>
</dependencies>
```

**Phase 4: 테스트**

```java
@SpringBootTest
class MigrationTest {

    @Test
    void testJakartaAnnotations() {
        // jakarta 패키지 정상 동작 확인
    }

    @Test
    void testJackson3Serialization() {
        // Jackson 3.x 직렬화 확인
    }

    @Test
    void testApiVersioning() {
        // API 버전 관리 동작 확인
    }
}
```

### 체크리스트

```markdown
□ Java 17+ 설치 및 확인
□ javax → jakarta 패키지 변경
  □ @Resource, @Inject
  □ @Valid, @NotNull
  □ @Entity, @Table, @Column
□ ListenableFuture → CompletableFuture 변경
□ Jackson 3.x 마이그레이션
  □ import 문 변경 (tools.jackson)
  □ ObjectMapper 빌더 패턴 적용
□ 제거된 설정 확인
  □ PathMatch 설정
  □ Theme 관련 코드
□ Servlet 컨테이너 업그레이드
  □ Tomcat 11 또는 Jetty 12
□ Hibernate 7.x 업그레이드 (JPA 사용시)
□ 통합 테스트 실행
□ 네이티브 이미지 빌드 테스트 (사용시)
```

## 8. 실전 예제

### 완전한 마이그레이션 예제

**Before (Spring 6.x):**
```java
// UserController.java
import javax.validation.Valid;
import org.springframework.util.concurrent.ListenableFuture;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @PostMapping
    public ResponseEntity<User> createUser(@Valid @RequestBody UserRequest request) {
        User user = userService.create(request);
        return ResponseEntity.ok(user);
    }

    @GetMapping("/{id}/async")
    public ListenableFuture<User> getUserAsync(@PathVariable Long id) {
        return userService.getUserAsync(id);
    }
}

// UserService.java
import org.springframework.retry.annotation.Retryable;

@Service
public class UserService {

    @Autowired
    private UserRepository repository;

    // Spring Retry는 별도 라이브러리 (속성명: maxAttempts — 총 시도 횟수)
    @Retryable(maxAttempts = 3)
    public User create(UserRequest request) {
        return repository.save(new User(request));
    }

    @Async
    public ListenableFuture<User> getUserAsync(Long id) {
        User user = repository.findById(id).orElseThrow();
        return AsyncResult.forValue(user);
    }
}
```

**After (Spring 7.0):**
```java
// UserController.java
import jakarta.validation.Valid;
import java.util.concurrent.CompletableFuture;
import tools.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    // API 버전 관리
    @PostMapping(version = "1")
    public ResponseEntity<UserV1> createUserV1(@Valid @RequestBody UserRequest request) {
        User user = userService.create(request);
        return ResponseEntity.ok(new UserV1(user));
    }

    @PostMapping(version = "2")
    public ResponseEntity<UserV2> createUserV2(@Valid @RequestBody UserRequest request) {
        User user = userService.create(request);
        return ResponseEntity.ok(new UserV2(user));
    }

    @GetMapping("/{id}/async")
    public CompletableFuture<User> getUserAsync(@PathVariable Long id) {
        return userService.getUserAsync(id);
    }
}

// UserService.java
import org.springframework.resilience.annotation.Retryable;
import org.springframework.resilience.annotation.ConcurrencyLimit;
import org.springframework.resilience.annotation.EnableResilientMethods;

@Configuration
@EnableResilientMethods  // 회복력 기능 활성화 (@Configuration 클래스에 부착)
class ResilienceConfig {}

@Service
public class UserService {

    @Autowired
    private UserRepository repository;

    // 내장 Retry 기능 (Spring 7 속성 체계: maxRetries / delay / multiplier / maxDelay)
    @Retryable(maxRetries = 2, delay = 1000, multiplier = 2.0)
    @ConcurrencyLimit(10)  // 동시성 제한
    public User create(UserRequest request) {
        return repository.save(new User(request));
    }

    @Async
    public CompletableFuture<User> getUserAsync(Long id) {
        User user = repository.findById(id).orElseThrow();
        return CompletableFuture.completedFuture(user);
    }
}

// AppConfig.java
import tools.jackson.databind.json.JsonMapper;
import tools.jackson.databind.SerializationFeature;

@Configuration
public class AppConfig {

    @Bean
    public ObjectMapper objectMapper() {
        return JsonMapper.builder()
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
            .build();
    }
}
```

## 핵심 요약

### Breaking Changes Top 5

1. **javax → jakarta 패키지 완전 전환** (필수)
2. **Jackson 3.x 기본 지원** (tools.jackson 패키지)
3. **ListenableFuture 제거** (CompletableFuture 사용)
4. **Servlet 6.1 필수** (Tomcat 11, Jetty 12)
5. **spring-jcl 제거** (Apache Commons Logging 직접 사용)

### 새로운 기능 Top 5

1. **회복력 기능 내장** (@Retryable, @ConcurrencyLimit)
2. **API 버전 관리** (First-class support)
3. **JPA 3.2 지원** (Hibernate 7.x)
4. **향상된 테스트** (RestTestClient, @Nested DI)
5. **Kotlin 코루틴 개선** (자동 컨텍스트 전파)

### 마이그레이션 난이도

- **소규모 프로젝트**: 🟢 쉬움 (2-3일)
  - javax → jakarta만 변경하면 대부분 완료

- **중규모 프로젝트**: 🟡 보통 (1-2주)
  - Jackson, ListenableFuture 마이그레이션 필요

- **대규모 레거시**: 🔴 어려움 (1개월+)
  - 서드파티 라이브러리 호환성 이슈
  - 대규모 테스트 필요

### 언제 업그레이드?

**✅ 지금 바로:**
- 새 프로젝트 시작
- Spring Boot 4.0 사용 예정
- Jakarta EE 11 지원 필요
- 최신 보안 패치 필요

**⏸️ 신중히:**
- 레거시 시스템 (javax 의존성 높음)
- 서드파티 라이브러리가 Jakarta EE 11 미지원
- 충분한 테스트 시간 확보 어려움

### 참고 자료

- [공식 릴리즈 노트](https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-7.0-Release-Notes)
- [Spring Boot 4.0 문서](https://spring.io/projects/spring-boot)
- [Jackson 3.0 마이그레이션 가이드](https://github.com/FasterXML/jackson/wiki/Jackson-Release-3.0)
- [Jakarta EE 11 스펙](https://jakarta.ee/specifications/platform/11/)
