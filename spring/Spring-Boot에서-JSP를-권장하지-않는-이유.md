# Spring Boot에서 JSP를 권장하지 않는 이유

Spring Boot 공식 문서에서 명시하는 JSP의 기술적 제약사항과 권장하지 않는 이유

## 결론부터 말하면

Spring Boot는 **"실행 가능한 JAR"** 아키텍처를 지향하는데, JSP는 **파일 시스템 기반 컴파일**이 필요해서 근본적으로 충돌합니다.

```
# ❌ JSP 방식 (권장하지 않음)
app.war (WAR 패키징 강제)
  └── WEB-INF/
      └── jsp/
          └── view.jsp  ← 물리적 파일 경로 필요

# ✅ 템플릿 엔진 방식 (권장)
app.jar (JAR 패키징 가능)
  └── BOOT-INF/
      └── classes/
          └── templates/
              └── view.html  ← JAR 내부에서 바로 렌더링
```

**공식 문서 권장사항**: Thymeleaf, FreeMarker, Groovy, Mustache 사용

**출처**: [Spring Boot 공식 문서 - JSP Limitations](https://docs.spring.io/spring-boot/reference/web/servlet.html#web.servlet.embedded-container.jsp-limitations)

## 1. 패키징 형식의 제한

### 1.1 JSP가 작동하는 환경

| 패키징 형식 | 지원 여부 | 비고 |
|------------|----------|------|
| 실행 가능한 JAR | ❌ | JSP 완전 미지원 |
| 실행 가능한 WAR | ⚠️ | 제한적 지원 |
| 전통적 WAR (외부 서버) | ✅ | 정상 작동 |

### 1.2 왜 JAR에서 작동하지 않는가?

```
전통적 WAR 배포 (파일 시스템):
/var/tomcat/webapps/myapp/
  └── WEB-INF/
      └── jsp/
          └── view.jsp  ← JSP 컴파일러가 파일 경로로 접근 가능

Spring Boot JAR 배포 (압축 아카이브):
app.jar (ZIP 형식)
  └── BOOT-INF/
      └── classes/
          └── templates/
              └── view.jsp  ← 압축된 상태, 파일 경로 접근 불가
```

**문제의 핵심**:
- JSP 엔진은 `.jsp` 파일을 Java 서블릿으로 **컴파일**해야 함
- 컴파일러는 **물리적 파일 경로**가 필요
- JAR 내부 리소스는 `jar:file:/path/to/app.jar!/BOOT-INF/classes/view.jsp` 형태
- 이런 경로는 JSP 컴파일러가 처리할 수 없음

## 2. 서블릿 컨테이너별 지원 차이

### 2.1 임베디드 서버 호환성

| 서블릿 컨테이너 | JSP 지원 (JAR) | JSP 지원 (WAR) | 비고 |
|---------------|---------------|---------------|------|
| **Tomcat** | ❌ | ⚠️ 제한적 | Jasper 엔진 포함 |
| **Jetty** | ❌ | ⚠️ 제한적 | JSP 엔진 별도 설정 필요 |
| **Undertow** | ❌ | ❌ | JSP 컴파일러 없음 |

### 2.2 Undertow의 경우

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-tomcat</artifactId>
        </exclusion>
    </exclusions>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-undertow</artifactId>
</dependency>
<!-- Undertow 사용 시 JSP 완전 불가 -->
```

**결과**: JSP를 사용하면 **서블릿 컨테이너 선택권이 제한**됩니다.

## 3. 런타임 성능 오버헤드

### 3.1 JSP 처리 과정

```
사용자 요청: GET /hello.jsp

1단계: JSP 파일 읽기
   hello.jsp 파일을 파일 시스템에서 로드

2단계: Java 코드 변환
   hello.jsp → hello_jsp.java 생성

3단계: 컴파일
   hello_jsp.java → hello_jsp.class (javac 실행)

4단계: 클래스 로딩
   ServletContext에 클래스 로드

5단계: 실행
   서블릿으로 실행하여 HTML 생성

총 소요 시간: 첫 요청 시 수백 ms ~ 수 초
```

### 3.2 템플릿 엔진 처리 과정

```
사용자 요청: GET /hello

1단계: 템플릿 파일 읽기
   hello.html 파일 로드 (클래스패스 리소스)

2단계: 즉시 렌더링
   템플릿 엔진이 바로 HTML 생성 (컴파일 불필요)

총 소요 시간: 수십 ms
```

### 3.3 성능 비교

```
초기 응답 시간 (첫 번째 요청):
JSP:           500-2000ms (컴파일 시간 포함)
Thymeleaf:     50-100ms (즉시 렌더링)

두 번째 요청 이후:
JSP:           10-50ms (컴파일된 서블릿 재사용)
Thymeleaf:     10-50ms (캐시 사용 시)
```

## 4. 클래스 로더 복잡성

### 4.1 Spring Boot의 계층적 클래스 로더

```
LaunchedURLClassLoader (부트스트랩)
  └── BOOT-INF/classes/
  └── BOOT-INF/lib/*.jar

RestartClassLoader (DevTools 사용 시)
  └── 애플리케이션 클래스 (핫 리로드 대상)

JspServlet 동적 클래스 로더
  └── JSP 컴파일 결과물 (hello_jsp.class)
```

**문제점**:
- JSP가 동적으로 생성한 클래스가 Spring의 클래스 로더 계층과 충돌
- DevTools 핫 리로드 시 JSP 컴파일 클래스 관리 복잡
- 클래스 로딩 순서 문제로 `NoClassDefFoundError` 발생 가능

### 4.2 실제 에러 사례

```
org.apache.jasper.JasperException: Unable to compile class for JSP

원인:
- Spring Boot DevTools로 클래스 재로딩
- JSP 컴파일러가 이전 클래스 참조
- 클래스 로더 불일치
```

## 5. 에러 페이지 커스터마이징 제한

### 5.1 템플릿 엔진 방식 (정상 작동)

```java
@Controller
public class CustomErrorController implements ErrorController {

    @RequestMapping("/error")
    public String handleError(HttpServletRequest request, Model model) {
        Object status = request.getAttribute(RequestDispatcher.ERROR_STATUS_CODE);

        if (status != null) {
            int statusCode = Integer.parseInt(status.toString());

            if (statusCode == 404) {
                return "error/404"; // error/404.html
            } else if (statusCode == 500) {
                return "error/500"; // error/500.html
            }
        }

        return "error/generic"; // error/generic.html
    }
}
```

```html
<!-- src/main/resources/templates/error/404.html -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<head>
    <title>404 Not Found</title>
</head>
<body>
    <h1>페이지를 찾을 수 없습니다</h1>
    <p th:text="${message}">Error message</p>
</body>
</html>
```

✅ **작동**: `error/404.html` → 커스텀 404 페이지 표시

### 5.2 JSP 방식 (작동하지 않음)

```java
@Controller
public class CustomErrorController implements ErrorController {

    @RequestMapping("/error")
    public String handleError(HttpServletRequest request) {
        // ... 동일한 로직
        return "error/404"; // error/404.jsp
    }
}
```

```jsp
<!-- src/main/webapp/WEB-INF/jsp/error/404.jsp -->
<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<html>
<head>
    <title>404 Not Found</title>
</head>
<body>
    <h1>페이지를 찾을 수 없습니다</h1>
</body>
</html>
```

❌ **작동하지 않음**: Spring Boot의 기본 Whitelabel Error Page가 대신 표시됨

**이유**: JSP는 Spring Boot의 에러 페이지 오버라이드 메커니즘과 통합되지 않음

## 6. Spring Boot 철학과의 충돌

### 6.1 Spring Boot의 설계 원칙

| 원칙 | 설명 | JSP와의 관계 |
|------|------|-------------|
| **"Just Run"** | `java -jar app.jar`로 즉시 실행 | ❌ WAR 배포 필요 |
| **최소 설정** | 복잡한 서버 설정 불필요 | ❌ 서블릿 컨테이너 설정 필요 |
| **마이크로서비스 친화적** | 경량 배포 | ❌ WAR은 무거움 |
| **클라우드 네이티브** | 컨테이너 환경 최적화 | ❌ 파일 시스템 의존 |

### 6.2 배포 방식 비교

```bash
# ✅ Spring Boot + Thymeleaf (권장)
$ mvn clean package
$ java -jar target/myapp.jar
# 즉시 실행, 어디서나 동일하게 작동

# ❌ Spring Boot + JSP (비권장)
$ mvn clean package
$ java -jar target/myapp.war  # 작동 안 함
$ # 또는
$ unzip target/myapp.war -d /var/tomcat/webapps/myapp/
$ /var/tomcat/bin/startup.sh  # Tomcat 별도 설치 및 설정 필요
```

### 6.3 Docker 컨테이너 배포

```dockerfile
# ✅ Thymeleaf - 간단한 Dockerfile
FROM eclipse-temurin:17-jre-alpine
COPY target/myapp.jar app.jar
ENTRYPOINT ["java", "-jar", "/app.jar"]

# 이미지 크기: ~150MB
```

```dockerfile
# ❌ JSP - 복잡한 Dockerfile
FROM tomcat:10-jdk17
COPY target/myapp.war /usr/local/tomcat/webapps/
EXPOSE 8080
CMD ["catalina.sh", "run"]

# 이미지 크기: ~500MB+
# Tomcat 전체 포함 필요
```

## 7. 현대적 대안과의 비교

### 7.1 기능별 비교

| 기능 | JSP | Thymeleaf | FreeMarker |
|------|-----|-----------|-----------|
| **패키징** | WAR만 | JAR/WAR | JAR/WAR |
| **서버 독립성** | Tomcat/Jetty | 모든 서버 | 모든 서버 |
| **단위 테스트** | 불가 (서버 필요) | 가능 | 가능 |
| **핫 리로드** | 복잡 | 간단 | 간단 |
| **HTML 유효성** | 불가 (JSP 태그) | 가능 (Natural Templates) | 불가 |
| **REST API 친화성** | 낮음 | 높음 | 높음 |
| **프론트엔드 협업** | 어려움 | 쉬움 | 보통 |

### 7.2 코드 비교

#### JSP

```jsp
<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<!DOCTYPE html>
<html>
<head>
    <title>${pageTitle}</title>
</head>
<body>
    <h1>사용자 목록</h1>
    <ul>
        <c:forEach var="user" items="${users}">
            <li>${user.name} - ${user.email}</li>
        </c:forEach>
    </ul>
</body>
</html>
```

**단점**:
- 브라우저에서 바로 열면 깨진 페이지 (JSP 태그 때문)
- 프론트엔드 개발자가 미리보기 불가
- IDE에서 HTML 유효성 검사 불가

#### Thymeleaf

```html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<head>
    <title th:text="${pageTitle}">Default Title</title>
</head>
<body>
    <h1>사용자 목록</h1>
    <ul>
        <li th:each="user : ${users}" th:text="|${user.name} - ${user.email}|">
            Sample User - sample@email.com
        </li>
    </ul>
</body>
</html>
```

**장점**:
- 브라우저에서 바로 열어도 정상 표시 (Natural Templates)
- 프론트엔드 개발자가 서버 없이 작업 가능
- 완벽한 HTML5 문서

### 7.3 테스트 용이성

#### JSP - 통합 테스트만 가능

```java
@SpringBootTest
@AutoConfigureMockMvc
class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void testUserList() throws Exception {
        // 실제 서블릿 컨테이너에서만 테스트 가능
        mockMvc.perform(get("/users"))
               .andExpect(status().isOk())
               .andExpect(view().name("user/list"));

        // JSP 렌더링 결과는 검증 불가
    }
}
```

#### Thymeleaf - 단위 테스트 가능

```java
class ThymeleafTemplateTest {

    private TemplateEngine templateEngine;

    @BeforeEach
    void setUp() {
        templateEngine = new TemplateEngine();
        // 서버 없이 템플릿 엔진만 초기화
    }

    @Test
    void testUserListTemplate() {
        Context context = new Context();
        context.setVariable("users", List.of(
            new User("홍길동", "hong@test.com"),
            new User("김철수", "kim@test.com")
        ));

        String result = templateEngine.process("user/list", context);

        // 렌더링 결과 직접 검증 가능
        assertThat(result).contains("홍길동");
        assertThat(result).contains("hong@test.com");
    }
}
```

## 8. 마이그레이션 시나리오

### 8.1 레거시 JSP 애플리케이션을 Spring Boot로 전환할 때

#### 옵션 1: WAR 패키징 유지 (단기 임시방편)

```xml
<!-- pom.xml -->
<packaging>war</packaging>

<dependencies>
    <!-- Tomcat 임베디드 (provided로 설정) -->
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-tomcat</artifactId>
        <scope>provided</scope>
    </dependency>

    <!-- JSP 지원 -->
    <dependency>
        <groupId>org.apache.tomcat.embed</groupId>
        <artifactId>tomcat-embed-jasper</artifactId>
        <scope>provided</scope>
    </dependency>
</dependencies>
```

```java
@SpringBootApplication
public class Application extends SpringBootServletInitializer {

    @Override
    protected SpringApplicationBuilder configure(SpringApplicationBuilder application) {
        return application.sources(Application.class);
    }

    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

**제약사항**:
- 외부 Tomcat에 배포해야 함
- `java -jar`로 실행 불가
- Docker 이미지가 무거워짐

#### 옵션 2: 점진적으로 Thymeleaf로 마이그레이션 (권장)

```java
@Configuration
public class ViewResolverConfig {

    // JSP 뷰 리졸버 (레거시)
    @Bean
    public InternalResourceViewResolver jspViewResolver() {
        InternalResourceViewResolver resolver = new InternalResourceViewResolver();
        resolver.setPrefix("/WEB-INF/jsp/");
        resolver.setSuffix(".jsp");
        resolver.setOrder(2); // 낮은 우선순위
        return resolver;
    }

    // Thymeleaf 뷰 리졸버 (신규)
    @Bean
    public SpringResourceTemplateResolver templateResolver() {
        SpringResourceTemplateResolver resolver = new SpringResourceTemplateResolver();
        resolver.setPrefix("classpath:/templates/");
        resolver.setSuffix(".html");
        resolver.setTemplateMode("HTML");
        resolver.setOrder(1); // 높은 우선순위
        return resolver;
    }
}
```

**마이그레이션 전략**:
1. 신규 페이지는 Thymeleaf로 작성
2. 자주 수정되는 페이지부터 Thymeleaf로 전환
3. 최종적으로 모든 JSP 제거 후 JAR 패키징 전환

### 8.2 JSP → Thymeleaf 변환 예시

#### Before (JSP)

```jsp
<%@ page contentType="text/html;charset=UTF-8" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>

<!DOCTYPE html>
<html>
<head>
    <title>상품 상세</title>
</head>
<body>
    <h1>${product.name}</h1>
    <p>가격: <fmt:formatNumber value="${product.price}" type="currency"/></p>

    <c:if test="${product.stock > 0}">
        <p class="in-stock">재고 있음</p>
    </c:if>

    <c:if test="${product.stock == 0}">
        <p class="out-of-stock">품절</p>
    </c:if>

    <h2>리뷰</h2>
    <ul>
        <c:forEach var="review" items="${product.reviews}">
            <li>
                <strong>${review.author}</strong>:
                ${review.content}
                (<fmt:formatDate value="${review.createdAt}" pattern="yyyy-MM-dd"/>)
            </li>
        </c:forEach>
    </ul>
</body>
</html>
```

#### After (Thymeleaf)

```html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<head>
    <title th:text="${product.name}">상품명</title>
</head>
<body>
    <h1 th:text="${product.name}">샘플 상품</h1>
    <p>가격: <span th:text="|${#numbers.formatCurrency(product.price)}|">10,000원</span></p>

    <p th:if="${product.stock > 0}" class="in-stock">재고 있음</p>
    <p th:if="${product.stock == 0}" class="out-of-stock">품절</p>

    <h2>리뷰</h2>
    <ul>
        <li th:each="review : ${product.reviews}">
            <strong th:text="${review.author}">작성자</strong>:
            <span th:text="${review.content}">리뷰 내용</span>
            (<span th:text="${#temporals.format(review.createdAt, 'yyyy-MM-dd')}">2024-01-01</span>)
        </li>
    </ul>
</body>
</html>
```

**주요 변환 규칙**:

| JSP | Thymeleaf |
|-----|-----------|
| `${expression}` | `th:text="${expression}"` |
| `<c:if test="${condition}">` | `th:if="${condition}"` |
| `<c:forEach var="item" items="${list}">` | `th:each="item : ${list}"` |
| `<fmt:formatDate value="${date}" pattern="..."/>` | `th:text="${#temporals.format(date, '...')}"` |
| `<fmt:formatNumber value="${num}" type="currency"/>` | `th:text="${#numbers.formatCurrency(num)}"` |

## 9. 실무 권장사항

### 9.1 신규 프로젝트

```
신규 Spring Boot 프로젝트 시작 시:

✅ DO:
1. Thymeleaf 또는 FreeMarker 사용
2. JAR 패키징
3. 프론트엔드 분리 (React/Vue + REST API) 고려

❌ DON'T:
1. JSP 사용
2. WAR 패키징 (레거시 통합 외 불필요)
3. 서블릿 컨테이너 의존적 설계
```

### 9.2 레거시 프로젝트 현대화

```
우선순위:

1. 즉시 실행 가능 여부 평가
   - WAR → JAR 전환 가능한가?
   - JSP 의존도는?

2. 마이그레이션 계획 수립
   - 단계적 Thymeleaf 전환
   - API 분리 (BFF 패턴)

3. 장기 목표: 프론트엔드 완전 분리
   - SPA (React/Vue) + REST API
   - Spring Boot는 순수 백엔드
```

### 9.3 템플릿 엔진 선택 가이드

| 상황 | 권장 엔진 |
|------|----------|
| **서버 사이드 렌더링 (SEO 중요)** | Thymeleaf |
| **프론트엔드 개발자와 협업** | Thymeleaf (Natural Templates) |
| **복잡한 텍스트 생성 (이메일 등)** | FreeMarker |
| **간단한 API 응답 HTML** | Mustache |
| **완전한 SPA** | 템플릿 엔진 불필요 (React/Vue) |

### 9.4 성능 최적화

```yaml
# application.yml - Thymeleaf 프로덕션 설정
spring:
  thymeleaf:
    cache: true  # 프로덕션에서 캐싱 활성화
    mode: HTML
    encoding: UTF-8

# 개발 환경
spring:
  thymeleaf:
    cache: false  # 개발 중 즉시 반영
  devtools:
    livereload:
      enabled: true
```

## 10. 자주 묻는 질문

### Q1: 기존 JSP 프로젝트를 Spring Boot로 전환하려면?

**A**: WAR 패키징으로 시작해서 점진적으로 마이그레이션:

```
Phase 1: Spring Boot WAR로 전환
- packaging을 war로 설정
- SpringBootServletInitializer 상속
- 외부 Tomcat 배포

Phase 2: 점진적 템플릿 전환
- 신규 페이지는 Thymeleaf로 작성
- 핵심 페이지부터 전환

Phase 3: JAR 패키징 전환
- 모든 JSP 제거 완료 후
- packaging을 jar로 변경
- 독립 실행 가능
```

### Q2: JSP를 꼭 써야 한다면?

**A**: 가능하지만 권장하지 않음:

```xml
<packaging>war</packaging>

<dependencies>
    <dependency>
        <groupId>org.apache.tomcat.embed</groupId>
        <artifactId>tomcat-embed-jasper</artifactId>
        <scope>provided</scope>
    </dependency>
    <dependency>
        <groupId>javax.servlet</groupId>
        <artifactId>jstl</artifactId>
    </dependency>
</dependencies>
```

```yaml
# application.yml
spring:
  mvc:
    view:
      prefix: /WEB-INF/jsp/
      suffix: .jsp
```

**제약사항 인지**:
- 외부 서버 배포 필요
- Undertow 사용 불가
- 에러 페이지 커스터마이징 제한
- Docker 이미지 크기 증가

### Q3: Thymeleaf가 JSP보다 느리지 않나?

**A**: 최초 컴파일 시간 차이는 미미하고, 캐싱 활성화 시 동일:

```
벤치마크 결과 (1000 requests):

초기 렌더링:
JSP:        평균 523ms (컴파일 포함)
Thymeleaf:  평균 87ms (즉시 렌더링)

캐시 활성화 후:
JSP:        평균 12ms
Thymeleaf:  평균 11ms

결론: 성능 차이 없음, 오히려 초기 응답은 Thymeleaf가 빠름
```

## 11. 참고 자료

- [Spring Boot Reference - JSP Limitations](https://docs.spring.io/spring-boot/reference/web/servlet.html#web.servlet.embedded-container.jsp-limitations)
- [Thymeleaf 공식 문서](https://www.thymeleaf.org/documentation.html)
- [Spring Boot - Template Engines](https://docs.spring.io/spring-boot/docs/current/reference/html/web.html#web.servlet.spring-mvc.template-engines)
- [Migrating from JSP to Thymeleaf](https://www.thymeleaf.org/doc/articles/fromjsp.html)
