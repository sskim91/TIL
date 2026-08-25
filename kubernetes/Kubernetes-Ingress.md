# Kubernetes Ingress

Service마다 LoadBalancer를 만들면 비용이 얼마나 나올까?

## 결론부터 말하면

**Ingress**는 클러스터 외부에서 들어오는 HTTP/HTTPS 트래픽을 **하나의 진입점**으로 받아서, URL 경로나 호스트 이름에 따라 적절한 Service로 라우팅한다.

```mermaid
flowchart LR
    subgraph "Service마다 LB (비효율)"
        U1[사용자] --> LB1[LB for api-svc]
        U1 --> LB2[LB for web-svc]
        U1 --> LB3[LB for admin-svc]
    end

    subgraph "Ingress (효율)"
        U2[사용자] --> ING[Ingress<br>단일 진입점]
        ING -->|"/api"| API[api-svc]
        ING -->|"/web"| WEB[web-svc]
        ING -->|"/admin"| ADM[admin-svc]
    end

    style ING stroke:#9C27B0,stroke-width:3px
```

| 기능 | Service (LoadBalancer) | Ingress |
|------|----------------------|---------|
| L4/L7 | L4 (TCP/UDP) | **L7 (HTTP/HTTPS)** |
| URL 라우팅 | ❌ | ✅ `/api`, `/web` |
| 호스트 라우팅 | ❌ | ✅ `api.example.com` |
| TLS 종료 | ❌ | ✅ 인증서 관리 |
| 비용 | LB당 비용 | **하나의 LB** |

---

## 1. 왜 Ingress가 필요한가?

### 1.1 LoadBalancer Service의 한계

Service 문서에서 `LoadBalancer` 타입을 배웠다. 외부에서 접근할 수 있어서 좋은데, 문제가 있다.

**문제 1: 서비스마다 LoadBalancer가 생긴다**

```yaml
# 3개의 서비스 = 3개의 LoadBalancer = 3배 비용
api-svc:     LoadBalancer → 52.10.1.1
web-svc:     LoadBalancer → 52.10.1.2
admin-svc:   LoadBalancer → 52.10.1.3
```

AWS 기준 `Service(type: LoadBalancer)`는 기본적으로 L4 로드밸런서(NLB 또는 CLB)를 프로비저닝한다. NLB만 해도 시간당 요금 + LCU × 서비스 개수로 비용이 폭발한다. (ALB는 L7 로드밸런서로, Ingress 리소스 + AWS Load Balancer Controller를 통해 생성되는 별개의 경로다.)

**문제 2: URL 경로 기반 라우팅이 안 된다**

LoadBalancer는 L4(TCP) 레벨에서 동작한다. "HTTP 요청의 경로"를 보고 분기하는 건 불가능하다.

```
# 이런 라우팅을 하고 싶다면?
/api/*   → api-svc
/web/*   → web-svc
/admin/* → admin-svc

# LoadBalancer로는 불가능!
```

**문제 3: TLS 인증서 관리가 분산된다**

각 LoadBalancer마다 인증서를 따로 설정해야 한다. 갱신도 따로, 관리도 따로.

### 1.2 Ingress의 해결책

Ingress는 **하나의 진입점**에서 모든 걸 처리한다:

| 문제 | Ingress의 해결책 |
|------|-----------------|
| LB 비용 폭발 | **하나의 LB**로 여러 서비스 |
| URL 라우팅 | **경로 기반** 라우팅 |
| 호스트 라우팅 | **도메인 기반** 라우팅 |
| TLS 관리 | **한 곳에서** 인증서 관리 |

---

## 2. Ingress의 구조

### 2.1 Ingress vs Ingress Controller

여기서 중요한 개념이 있다. **Ingress는 규칙일 뿐이다.**

```mermaid
flowchart TB
    subgraph "Ingress (규칙)"
        ING["Ingress YAML<br>'이 경로는 이 서비스로'"]
    end

    subgraph "Ingress Controller (실행자)"
        IC["Nginx / Traefik / ALB<br>실제 트래픽 처리"]
    end

    ING -->|"규칙 읽음"| IC
    User[사용자] -->|"HTTP 요청"| IC
    IC --> SVC[Service]

    style ING stroke:#9C27B0,stroke-width:2px
    style IC stroke:#2196F3,stroke-width:3px
```

| 구분 | Ingress | Ingress Controller |
|------|---------|-------------------|
| 역할 | 라우팅 **규칙** 정의 | 규칙을 **실행** |
| 타입 | Kubernetes 리소스 | 별도 설치 필요 |
| 예시 | YAML 파일 | Nginx, Traefik, AWS ALB |

**중요:** Ingress Controller가 없으면 Ingress 리소스를 만들어도 **아무 일도 일어나지 않는다!**

### 2.2 IngressClass: 어떤 Controller가 처리할지 지정

클러스터에 여러 Ingress Controller가 있을 수 있다. `IngressClass`는 **어떤 Controller가 이 Ingress를 처리할지** 지정한다.

```yaml
# IngressClass 리소스
apiVersion: networking.k8s.io/v1
kind: IngressClass
metadata:
  name: nginx
  annotations:
    ingressclass.kubernetes.io/is-default-class: "true"  # 기본 IngressClass
spec:
  controller: k8s.io/ingress-nginx
```

```yaml
# Ingress에서 IngressClass 참조
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: nginx    # 이 IngressClass를 사용
  rules:
  # ...
```

**Default IngressClass:**
- `ingressclass.kubernetes.io/is-default-class: "true"` 어노테이션으로 지정
- `ingressClassName`을 생략하면 기본 IngressClass가 사용됨
- 클라우드 환경에서는 보통 자동 설정됨

### 2.3 Ingress Controller 종류

> **⚠️ 먼저 알아야 할 것 (2026년 8월 기준).** 오랫동안 "일단 이거"였던 커뮤니티 **ingress-nginx** 는 **2026년 3월에 은퇴** 했다. 저장소는 아카이브되어 읽기 전용이고, 버그 수정도 보안 패치도 더 이상 없다. 신규 도입 대상에서 빼야 한다. 자세한 배경과 이전 경로는 [12절](#12-2026년-현재--ingress-nginx-은퇴와-gateway-api)에 정리했다.

| Controller | 특징 | 환경 | 상태 |
|------------|------|------|------|
| ~~**ingress-nginx**~~ | 커뮤니티 프로젝트. 과거 사실상의 표준 | — | ❌ **2026-03 은퇴, 아카이브** |
| **Traefik** | 가벼움, 자동 설정. Ingress·Gateway API 동시 지원 | 모든 환경 | ✅ 유지보수 중 |
| **Envoy Gateway** | Gateway API 네이티브, 스펙 준수도 높음 | 모든 환경 | ✅ 유지보수 중 |
| **Cilium** | CNI와 통합된 단일 네트워킹 스택. 양쪽 API 지원 | 모든 환경 | ✅ 유지보수 중 |
| **NGINX Gateway Fabric** | F5/NGINX의 Gateway API 구현체 | 모든 환경 | ✅ 유지보수 중 |
| **F5 NGINX Ingress Controller** | 이름이 비슷하나 **위 ingress-nginx와 다른 프로젝트** | 모든 환경 | ✅ 유지보수 중 |
| **AWS ALB** | AWS 네이티브, ALB 자동 생성 | AWS | ✅ 유지보수 중 |
| **GKE Ingress** | GCP 네이티브 | GCP | ✅ 유지보수 중 |
| **Istio Gateway** | 서비스 메시 연동 | Istio 사용 시 | ✅ 유지보수 중 |

> **이름 함정 하나.** `ingress-nginx`(쿠버네티스 커뮤니티, 은퇴)와 `nginx-ingress`(F5/NGINX Inc., 유지보수 중)는 **하이픈 순서만 다른 별개 프로젝트** 다. 은퇴한 것은 앞의 것이다. 그리고 웹 서버 NGINX 자체는 이 일과 **아무 관계가 없다** — 은퇴한 것은 쿠버네티스 컨트롤러 하나지 NGINX 생태계가 아니다.

> **서비스 메시를 쓰는 클러스터에서는 `Ingress` 리소스가 아예 없을 수 있다.** 메시의 게이트웨이가 Ingress Controller 역할을 대신하고, 라우팅 규칙은 `Ingress`가 아니라 메시 자신의 커스텀 리소스에 적히기 때문이다. `kubectl get ingress`가 비어 있는데 서비스는 정상 응답하는 상황을 만나면 [Ingress 리소스가 하나도 없는데 트래픽은 어떻게 들어올까 — 서비스 메시가 대체하는 것들](Ingress-리소스가-하나도-없는데-트래픽은-어떻게-들어올까-서비스-메시가-대체하는-것들.md)을 보라. 아래 6절에서 다루는 annotation 확장이 왜 생겼고 메시는 그것을 어떻게 1급 필드로 바꿨는지도 함께 다룬다.

---

## 3. Ingress 기본 설정

### 3.1 경로 기반 라우팅

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: nginx    # 사용할 Ingress Controller
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix     # /api, /api/users, /api/v1/... 모두 매칭
        backend:
          service:
            name: api-svc
            port:
              number: 80
      - path: /web
        pathType: Prefix
        backend:
          service:
            name: web-svc
            port:
              number: 80
```

```mermaid
flowchart LR
    User[사용자] --> ING[Ingress]

    ING -->|"/api/*"| API[api-svc]
    ING -->|"/web/*"| WEB[web-svc]

    API --> P1[API Pod 1]
    API --> P2[API Pod 2]
    WEB --> P3[Web Pod]

    style ING stroke:#9C27B0,stroke-width:3px
```

### 3.2 pathType 이해하기

| pathType | 설명 | 예시 |
|----------|------|------|
| **Prefix** | 경로 접두사 매칭 | `/api` → `/api`, `/api/users`, `/api/v1` |
| **Exact** | 정확히 일치해야 함 | `/api` → `/api`만 (❌ `/api/users`) |
| **ImplementationSpecific** | Controller마다 다름 | - |

> **참고:** `path: /`와 `pathType: Prefix`를 함께 사용하면 해당 호스트의 **모든 경로** 를 매칭하는 "catch-all" 규칙이 된다.

### 3.3 호스트 기반 라우팅

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-host-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com     # 호스트별 분기
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-svc
            port:
              number: 80
```

```mermaid
flowchart LR
    User[사용자]

    User -->|"api.example.com"| ING[Ingress]
    User -->|"web.example.com"| ING

    ING -->|"api.example.com"| API[api-svc]
    ING -->|"web.example.com"| WEB[web-svc]

    style ING stroke:#9C27B0,stroke-width:3px
```

---

## 4. TLS/HTTPS 설정

### 4.1 왜 Ingress에서 TLS를 처리하나?

TLS 종료(termination)를 Ingress에서 하면:
- 인증서를 **한 곳에서** 관리
- 백엔드 Pod는 **HTTP**로 통신 (단순화)
- 인증서 갱신이 **쉬움**

```mermaid
flowchart LR
    User[사용자] -->|"HTTPS"| ING[Ingress<br>TLS 종료]
    ING -->|"HTTP"| SVC[Service]
    SVC --> Pod[Pod]

    style ING stroke:#9C27B0,stroke-width:3px
```

### 4.2 TLS Secret 생성

```bash
# 인증서와 키로 Secret 생성
kubectl create secret tls my-tls-secret \
  --cert=path/to/cert.crt \
  --key=path/to/cert.key
```

### 4.3 Ingress에 TLS 적용

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    - web.example.com
    secretName: my-tls-secret    # TLS Secret 참조
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

### 4.4 cert-manager로 자동 인증서 관리

수동으로 인증서를 관리하기 어렵다면 **cert-manager**를 사용하라.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: auto-tls-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod  # 자동 발급
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: api-tls    # cert-manager가 자동 생성
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

cert-manager가 Let's Encrypt에서 인증서를 자동 발급하고, 만료 전에 자동 갱신한다.

---

## 5. Default Backend

### 5.1 매칭되지 않는 요청 처리

어떤 규칙에도 매칭되지 않는 요청은 어떻게 될까?

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-with-default
spec:
  ingressClassName: nginx
  defaultBackend:           # 기본 백엔드
    service:
      name: default-svc
      port:
        number: 80
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

```mermaid
flowchart LR
    User[사용자] --> ING[Ingress]

    ING -->|"/api"| API[api-svc]
    ING -->|"그 외 모든 요청"| DEF[default-svc<br>404 페이지 등]

    style DEF stroke:#9E9E9E,stroke-width:2px
```

---

## 6. Annotations: Controller별 고급 설정

### 6.1 Nginx Ingress 예시

Ingress Controller마다 **annotations**로 세부 설정을 한다.

> **이 절을 읽는 법 (2026년 8월).** 아래 `nginx.ingress.kubernetes.io/*` annotation들은 **은퇴한 커뮤니티 ingress-nginx의 문법** 이다([12절](#12-2026년-현재--ingress-nginx-은퇴와-gateway-api)). 지금도 이 절이 유효한 이유는 두 가지다 — 이미 돌아가는 클러스터를 **읽고 이해하려면** 필요하고, Gateway API로 **이전할 때 무엇을 다시 설계해야 하는지** 목록이 바로 이 annotation들이기 때문이다. 반대로 **신규 클러스터를 구성한다면 이 문법을 그대로 쓰면 안 된다.** 고른 컨트롤러의 자체 문법이나 Gateway API 표준 필드로 옮겨야 한다.
>
> 그리고 annotation이 이렇게 컨트롤러마다 제각각이라는 사실 자체가, Gateway API가 헤더 매칭·트래픽 가중치를 **표준 스키마 필드로 끌어올린** 이유다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress
  annotations:
    # HTTPS 리다이렉트
    nginx.ingress.kubernetes.io/ssl-redirect: "true"

    # 타임아웃
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"

    # CORS
    nginx.ingress.kubernetes.io/enable-cors: "true"

    # Rate Limiting
    nginx.ingress.kubernetes.io/limit-rps: "10"
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

### 6.2 경로 재작성 (Rewrite)

`/api/users` 요청을 백엔드에 `/users`로 전달하고 싶을 때 `rewrite-target` annotation을 사용한다.

**v0.22.0 이후:** 반드시 **캡처 그룹**을 명시적으로 정의해야 한다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rewrite-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2    # 두 번째 캡처 그룹으로 재작성
    nginx.ingress.kubernetes.io/use-regex: "true"
spec:
  ingressClassName: nginx
  rules:
  - host: example.com
    http:
      paths:
      - path: /api(/|$)(.*)      # 캡처 그룹: $1=(/|$), $2=(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

| 요청 경로 | 백엔드 전달 경로 | 설명 |
|----------|-----------------|------|
| `/api` | `/` | `$2`가 빈 문자열 |
| `/api/` | `/` | `$2`가 빈 문자열 |
| `/api/users` | `/users` | `$2`가 `users` |
| `/api/v1/products` | `/v1/products` | `$2`가 `v1/products` |

**캡처 그룹 설명:**
- `(/|$)` → `$1`: `/` 또는 문자열 끝 매칭
- `(.*)` → `$2`: 나머지 경로 캡처 (이것을 `rewrite-target`에서 사용)

> 📖 자세한 내용은 [Nginx Ingress Rewrite 문서](https://kubernetes.github.io/ingress-nginx/examples/rewrite/)를 참고하라. ⚠️ 이 문서는 **2026년 3월 아카이브** 되어 더 이상 갱신되지 않는다 — 기존 설정을 해석하는 용도로만 쓰라.

### 6.3 자주 쓰는 Nginx Annotations

| Annotation | 설명 |
|------------|------|
| `ssl-redirect` | HTTP → HTTPS 리다이렉트 |
| `rewrite-target` | 경로 재작성 |
| `proxy-body-size` | 요청 본문 크기 제한 |
| `proxy-read-timeout` | 백엔드 응답 타임아웃 |
| `whitelist-source-range` | IP 허용 목록 |

---

## 7. Ingress vs Service 언제 뭘 쓰나?

```mermaid
flowchart TB
    Q{외부 노출 필요?}

    Q -->|"아니오"| CI[ClusterIP]
    Q -->|"예"| Proto{프로토콜?}

    Proto -->|"TCP/UDP"| LB[LoadBalancer]
    Proto -->|"HTTP/HTTPS"| HTTP{서비스 개수?}

    HTTP -->|"1개"| LB2[LoadBalancer도 OK]
    HTTP -->|"여러 개"| ING[Ingress 권장]

    style CI stroke:#4CAF50,stroke-width:2px
    style LB stroke:#FF9800,stroke-width:2px
    style ING stroke:#9C27B0,stroke-width:3px
```

| 상황 | 추천 |
|------|------|
| 내부 서비스 간 통신 | **ClusterIP** |
| TCP/UDP 외부 노출 (DB 등) | **LoadBalancer** |
| HTTP/HTTPS 1개 서비스 | LoadBalancer 또는 Ingress |
| HTTP/HTTPS 여러 서비스 | **Ingress** |
| URL/호스트 기반 라우팅 필요 | **Ingress** |
| TLS 중앙 관리 필요 | **Ingress** |

---

## 8. 실전 예시: 전체 구성

> **이 예시의 유효 범위.** 아래 구성은 `ingressClassName: nginx`와 `nginx.ingress.kubernetes.io/*` annotation을 쓴다. **이미 ingress-nginx가 돌고 있는 클러스터를 읽고 이해하는 용도** 로는 그대로 유효하다. 반면 **2026년에 새로 구성한다면 그대로 복사하면 안 된다** — ingress-nginx는 은퇴했다([12절](#12-2026년-현재--ingress-nginx-은퇴와-gateway-api)). 유지보수되는 컨트롤러를 고른 뒤 `ingressClassName`과 annotation을 그 구현체의 것으로 바꾸거나, Gateway API의 `Gateway` + `HTTPRoute`로 설계하라. Ingress 리소스의 **구조 자체**(Service → Ingress → TLS → 라우팅 규칙)는 어느 쪽이든 그대로 배울 가치가 있다.

```yaml
---
# 1. API Service (ClusterIP)
apiVersion: v1
kind: Service
metadata:
  name: api-svc
spec:
  type: ClusterIP
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8080

---
# 2. Web Service (ClusterIP)
apiVersion: v1
kind: Service
metadata:
  name: web-svc
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
  - port: 80
    targetPort: 3000

---
# 3. Ingress (외부 진입점)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: main-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - example.com
    - api.example.com
    secretName: example-tls
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-svc
            port:
              number: 80
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

```mermaid
flowchart LR
    User[사용자] -->|"HTTPS"| ING[Ingress<br>TLS 종료]

    ING -->|"example.com"| WEB[web-svc<br>ClusterIP]
    ING -->|"api.example.com"| API[api-svc<br>ClusterIP]

    WEB --> W1[Web Pod]
    API --> A1[API Pod 1]
    API --> A2[API Pod 2]

    style ING stroke:#9C27B0,stroke-width:3px
    style WEB stroke:#4CAF50,stroke-width:2px
    style API stroke:#4CAF50,stroke-width:2px
```

**핵심:** 백엔드 Service는 `ClusterIP`로 충분하다. 외부 노출은 Ingress가 담당!

---

## 9. 클라우드별 Ingress Controller

클라우드 환경에서는 각 클라우드의 **네이티브 로드밸런서** 와 통합된 Ingress Controller를 사용한다.

> **⚠️ IngressClass 지정 방식 주의:** Kubernetes **1.18부터** 일반 Ingress 리소스는 `kubernetes.io/ingress.class` **annotation이 deprecated**되었고 `spec.ingressClassName` **필드**가 표준이다. **단, 클라우드별 Controller마다 규칙이 다르므로 공식 문서를 따라야 한다:**
> - **AWS Load Balancer Controller**: `ingressClassName: alb` (표준 방식) 사용
> - **Azure AGIC**: `ingressClassName` 또는 legacy annotation 모두 지원
> - **GKE Ingress(GCE)**: 공식 문서가 여전히 [`kubernetes.io/ingress.class: "gce"` / `"gce-internal"` annotation 방식을 사용](https://cloud.google.com/kubernetes-engine/docs/how-to/internal-load-balance-ingress)하며, 특히 internal Ingress는 annotation으로만 지정 가능
>
> 즉 "일반 k8s Ingress는 `ingressClassName` 권장, GKE는 예외"로 기억하라.

### 9.1 AWS: ALB Ingress Controller (AWS Load Balancer Controller)

AWS에서는 **AWS Load Balancer Controller** 가 Ingress 리소스를 **Application Load Balancer(ALB)** 로 프로비저닝한다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    # ALB 기본 설정
    alb.ingress.kubernetes.io/scheme: internet-facing          # 또는 internal
    alb.ingress.kubernetes.io/target-type: ip                  # ip 또는 instance

    # Health Check 설정
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/healthcheck-interval-seconds: "15"
    alb.ingress.kubernetes.io/healthcheck-timeout-seconds: "5"
    alb.ingress.kubernetes.io/success-codes: "200"
    alb.ingress.kubernetes.io/healthy-threshold-count: "2"
    alb.ingress.kubernetes.io/unhealthy-threshold-count: "2"

    # SSL/TLS (ACM 인증서 사용)
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:region:account:certificate/xxx
    alb.ingress.kubernetes.io/ssl-redirect: "443"

    # WAF 연동
    alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:region:account:regional/webacl/xxx
spec:
  ingressClassName: alb
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

| 어노테이션 | 설명 |
|-----------|------|
| `scheme: internet-facing` | Public ALB (외부 노출) |
| `scheme: internal` | Internal ALB (VPC 내부만) |
| `target-type: ip` | Pod IP 직접 타겟 (권장, Fargate 필수) |
| `target-type: instance` | NodePort 통해 라우팅 |
| `ssl-redirect: "443"` | HTTP → HTTPS 리다이렉트 |

**IngressGroup: 여러 Ingress를 하나의 ALB로**

```yaml
metadata:
  annotations:
    alb.ingress.kubernetes.io/group.name: my-group    # 같은 그룹 = 같은 ALB
    alb.ingress.kubernetes.io/group.order: "1"        # 규칙 우선순위 (낮을수록 먼저 평가)
```

여러 Ingress 리소스에 같은 `group.name`을 지정하면 **하나의 ALB** 로 통합된다. ALB 비용을 절감할 수 있다.

> **주의:** `group.order`는 규칙 충돌 시 **우선순위** 를 결정한다. 같은 경로에 여러 규칙이 있을 때 낮은 숫자가 먼저 평가되므로, 의도치 않은 라우팅 오류를 방지하려면 반드시 설정해야 한다.

### 9.2 GKE: GCE Ingress Controller (Container-Native Load Balancing)

GKE에서는 **GCE Ingress Controller** 가 기본 제공되며, **Network Endpoint Group(NEG)** 을 통해 Pod에 직접 트래픽을 전달한다.

**External GKE Ingress (외부 공개용):**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    # External GKE Ingress (기본값)
    kubernetes.io/ingress.class: "gce"

    # Global Static IP (외부 LB용)
    kubernetes.io/ingress.global-static-ip-name: "my-static-ip"

    # Google Managed Certificate
    networking.gke.io/managed-certificates: "my-cert"
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

**Internal GKE Ingress (VPC 내부 전용):**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-internal-ingress
  annotations:
    # Internal Load Balancer
    kubernetes.io/ingress.class: "gce-internal"

    # Regional Static IP (internal LB는 regional 사용, global이 아님!)
    kubernetes.io/ingress.regional-static-ip-name: "my-regional-static-ip"
spec:
  rules:
  - host: internal-api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

> **⚠️ Static IP 종류 주의:** External GKE Ingress는 **Global Static IP** (`global-static-ip-name`), Internal GKE Ingress는 **Regional Static IP** (`regional-static-ip-name`)를 사용한다. 섞어 쓰면 프로비저닝이 실패한다.

**NEG (Container-Native Load Balancing) 설정:**

```yaml
# Service에 NEG 어노테이션 추가
apiVersion: v1
kind: Service
metadata:
  name: api-svc
  annotations:
    cloud.google.com/neg: '{"ingress": true}'    # NEG 활성화
spec:
  type: ClusterIP
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8080
```

```mermaid
flowchart LR
    subgraph "기존 방식 (Instance Group)"
        LB1[Load Balancer] --> Node1[Node]
        Node1 --> kube-proxy1[kube-proxy]
        kube-proxy1 --> Pod1[Pod]
    end

    subgraph "NEG 방식 (Container-Native)"
        LB2[Load Balancer] -->|"직접"| Pod2[Pod]
    end

    style Pod2 stroke:#4CAF50,stroke-width:2px
```

**NEG의 장점:**
- **낮은 지연 시간:** Node/kube-proxy를 거치지 않고 Pod에 직접 연결
- **정확한 Health Check:** Pod 단위로 상태 확인
- **효율적인 로드밸런싱:** 실제 Pod 분포에 따른 균등 분배

**BackendConfig: 고급 Health Check 설정**

```yaml
apiVersion: cloud.google.com/v1
kind: BackendConfig
metadata:
  name: api-backend-config
spec:
  healthCheck:
    checkIntervalSec: 15
    timeoutSec: 5
    healthyThreshold: 2
    unhealthyThreshold: 2
    type: HTTP
    requestPath: /health
    port: 8080
  connectionDraining:
    drainingTimeoutSec: 60
  cdn:
    enabled: true
    cachePolicy:
      includeHost: true
      includeProtocol: true
---
apiVersion: v1
kind: Service
metadata:
  name: api-svc
  annotations:
    cloud.google.com/neg: '{"ingress": true}'
    cloud.google.com/backend-config: '{"default": "api-backend-config"}'
spec:
  # ...
```

### 9.3 Azure: Application Gateway Ingress Controller (AGIC)

Azure에서는 **AGIC** 가 Ingress를 **Azure Application Gateway** 로 변환한다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway

    # Backend Protocol
    appgw.ingress.kubernetes.io/backend-protocol: "http"         # 또는 https

    # Health Check
    appgw.ingress.kubernetes.io/health-probe-path: "/health"
    appgw.ingress.kubernetes.io/health-probe-interval: "15"
    appgw.ingress.kubernetes.io/health-probe-timeout: "5"

    # WAF Policy
    appgw.ingress.kubernetes.io/waf-policy-for-path: "/subscriptions/.../wafPolicies/my-waf"

    # Private IP 사용 (Internal)
    appgw.ingress.kubernetes.io/use-private-ip: "true"

    # SSL Redirect
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
```

| 어노테이션 | 설명 |
|-----------|------|
| `use-private-ip: "true"` | Internal LB (Private IP 사용) |
| `backend-protocol: "https"` | 백엔드 Pod와 HTTPS 통신 |
| `waf-policy-for-path` | WAF 정책 연동 |
| `ssl-redirect: "true"` | HTTP → HTTPS 리다이렉트 |

> **참고:** Azure는 차세대 솔루션으로 **Application Gateway for Containers** 를 출시했다. Gateway API 표준을 지원하며 더 빠른 설정 반영과 향상된 성능을 제공한다.

### 9.4 클라우드별 Ingress Controller 비교

| 기능 | AWS ALB | GKE GCE | Azure AGIC |
|------|---------|---------|------------|
| **L7 Load Balancer** | ALB | HTTP(S) LB | App Gateway |
| **Pod 직접 연결** | target-type: ip | NEG | ✅ (Endpoint 기반) |
| **WAF 연동** | WAFv2 | Cloud Armor | WAF Policy |
| **관리형 인증서** | ACM | Google Managed Cert | Key Vault |
| **IngressGroup** | ✅ 지원 | ❌ | ❌ |
| **비용** | ALB 시간당 + LCU | LB 시간당 + 트래픽 | App GW 시간당 + CU |

---

## 10. Ingress 디버깅

### 10.1 연결 문제 체크리스트

```mermaid
flowchart TB
    A["Ingress 연결 실패"] --> B{"Ingress Controller<br>Pod 실행 중?"}
    B -->|"아니오"| C["Controller 설치/상태 확인"]
    B -->|"예"| D{"Ingress ADDRESS<br>할당됨?"}
    D -->|"아니오"| E["IngressClass 확인<br>Controller 로그 확인"]
    D -->|"예"| F{"Backend Service<br>Endpoints 있음?"}
    F -->|"아니오"| G["Service selector/label 확인"]
    F -->|"예"| H{"Pod가<br>Ready인가?"}
    H -->|"아니오"| I["Readiness Probe 확인"]
    H -->|"예"| J["Health Check 설정 확인"]

    style A stroke:#f44336,stroke-width:2px
    style C stroke:#FF9800,stroke-width:2px
    style E stroke:#FF9800,stroke-width:2px
    style G stroke:#FF9800,stroke-width:2px
    style I stroke:#FF9800,stroke-width:2px
    style J stroke:#FF9800,stroke-width:2px
```

### 10.2 디버깅 명령어

```bash
# 1. Ingress 상태 확인 (ADDRESS가 있는지)
kubectl get ingress my-ingress
# ADDRESS가 비어있으면 → Ingress Controller 문제

# 2. Ingress 상세 정보
kubectl describe ingress my-ingress
# Events 섹션에서 에러 메시지 확인

# 3. Ingress Controller 로그 (Nginx)
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=100

# 4. Backend Service Endpoints 확인
kubectl get endpoints api-svc
# ENDPOINTS가 비어있으면 → Service/Pod 문제

# 5. IngressClass 확인
kubectl get ingressclass
kubectl describe ingressclass nginx

# 6. 클라우드별 LB 상태 확인
# AWS: ALB Target Group Health
aws elbv2 describe-target-health --target-group-arn <arn>

# GKE: NEG 상태
kubectl get svc api-svc -o yaml | grep neg-status
```

### 10.3 자주 발생하는 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| ADDRESS가 비어있음 | IngressClass 미지정/불일치 | `ingressClassName` 확인 |
| 404 Not Found | path/pathType 불일치 | pathType: Prefix 확인 |
| 502 Bad Gateway | Backend Pod 응답 안 함 | Pod 상태, targetPort 확인 |
| 503 Service Unavailable | Endpoints 없음 | Service selector 확인 |
| Health Check 실패 | Health Check 경로/포트 불일치 | 어노테이션 설정 확인 |
| TLS 인증서 에러 | Secret 없음/잘못된 형식 | `kubectl get secret` 확인 |

**404 에러 구분하기: 누가 404를 줬는가?**

404 Not Found가 발생하면 **누가** 404를 응답했는지 확인하는 것이 핵심이다.

| 404 종류 | 응답 모양 | 원인 | 해결 |
|----------|----------|------|------|
| **Ingress Controller 404** | "default backend - 404" 텍스트만 나오거나, Nginx 스타일 에러 페이지 | Ingress 규칙 미매칭, IngressClass 불일치 | path, pathType, host 설정 확인 |
| **애플리케이션 404** | 디자인된 404 페이지, JSON 에러 (`{"error": "not found"}`) | Ingress는 통과했지만 앱 내부 라우터에 경로 없음 | rewrite-target 설정, 앱 라우팅 확인 |

```bash
# 404 응답의 출처 확인
curl -v https://example.com/api/unknown

# Ingress Controller의 404 예시 (Nginx)
# < HTTP/1.1 404 Not Found
# < Server: nginx/1.25.3
# default backend - 404

# 애플리케이션의 404 예시
# < HTTP/1.1 404 Not Found
# < Content-Type: application/json
# {"error": "Resource not found", "path": "/api/unknown"}
```

> **팁:** 에러 페이지의 **모양** 을 보고 Ingress 설정 문제인지, 애플리케이션 내부 라우팅 문제인지 판단하라. 특히 `rewrite-target` 사용 시 경로가 의도대로 변환되는지 확인이 필요하다.

### 10.4 Health Check 실패 해결

클라우드 LB의 Health Check가 실패하는 일반적인 원인:

```yaml
# 1. Health Check 경로가 200을 반환하는지 확인
kubectl exec -it <pod-name> -- curl -v localhost:8080/health

# 2. Health Check 포트가 정확한지 확인
# - Service의 targetPort와 일치해야 함
# - Named port 사용 시 이름이 정확한지 확인

# 3. Readiness Probe와 LB Health Check 경로를 일치시키는 것을 권장
spec:
  containers:
  - name: app
    readinessProbe:
      httpGet:
        path: /health    # LB Health Check 경로와 동일
        port: 8080
```

---

## 11. 자주 쓰는 명령어

```bash
# Ingress 목록
kubectl get ingress

# Ingress 상세 (주소, 규칙 확인)
kubectl describe ingress my-ingress

# Ingress Controller Pod 로그 확인
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# TLS Secret 확인
kubectl get secret my-tls-secret
```

---

## 12. 2026년 현재 — ingress-nginx 은퇴와 Gateway API

지금까지 이 문서가 설명한 Ingress의 문법과 동작은 그대로 유효하다. 그런데 2026년에 이 문서를 읽는 사람은 **"그래서 어떤 Controller를 깔지"** 에서 예전과 다른 답을 받아야 한다. 가장 흔한 답이었던 것이 사라졌기 때문이다.

### 12.1 무슨 일이 있었나

2025년 11월 12일, 커뮤니티 **ingress-nginx** 메인테이너들이 프로젝트 은퇴를 발표했고 **2026년 3월 실제로 은퇴** 했다. 저장소는 아카이브되어 읽기 전용이 됐다. 이후로는 릴리스도, 버그 수정도, **보안 패치도 없다.**

쿠버네티스 Steering Committee와 Security Response Committee가 공동 성명까지 낸 이유는 규모 때문이다. 이 컨트롤러는 **클라우드 네이티브 환경의 약 절반** 이 쓰고 있었는데, 실제 유지보수는 **자원봉사자 한두 명이 여가 시간에** 감당하고 있었다. 기여자를 찾는 공개 호소가 몇 년간 응답을 받지 못했고, 결정타는 2025년 3월 공개된 **IngressNightmare(CVE-2025-1974)** 였다 — 클러스터 전체를 장악당할 수 있는 치명적 취약점이, 고칠 사람이 사실상 없는 컴포넌트에서 나온 것이다.

기술적 배경도 있다. ingress-nginx의 최대 장점이던 유연성 — 특히 `configuration-snippet` annotation으로 **임의의 NGINX 설정을 주입** 할 수 있던 기능 — 이 그대로 보안 부채가 됐다. 설계 자체가 문제라서 메인테이너가 늘어난다고 고칠 수 있는 성질이 아니었다. 후계자로 시작했던 **InGate** 프로젝트도 성숙 단계에 이르지 못하고 함께 접혔다.

```mermaid
timeline
    title ingress-nginx의 마지막 1년
    2025-03 : IngressNightmare(CVE-2025-1974) 공개
    2025-11 : 은퇴 발표 (11월 12일)
    2026-01 : Steering·Security 위원회 공동 성명
    2026-03 : 은퇴 완료, 저장소 아카이브
```

### 12.2 오해하면 안 되는 것 두 가지

여기서 범위를 정확히 잡는 게 중요하다. 은퇴한 것은 **컨트롤러 구현체 하나** 지, 그 위나 아래가 아니다.

| 오해 | 실제 |
|------|------|
| "Ingress API가 없어진다" | ❌ **Ingress API는 GA로 남아 있고 제거 계획이 없다.** 다만 **feature-frozen** — 새 기능이 추가되지 않을 뿐 |
| "NGINX를 쓰면 안 된다" | ❌ 웹 서버 **NGINX 자체는 무관하다.** 은퇴한 건 쿠버네티스 컨트롤러 하나 |
| "nginx-ingress도 죽었다" | ❌ **F5/NGINX Inc.의 `nginx-ingress`는 별개 프로젝트** 이고 유지보수 중 |
| "당장 안 고치면 서비스가 멈춘다" | ❌ 기존 배포는 계속 **동작한다.** 문제는 조용히 동작한다는 것 — 새 취약점이 나와도 영원히 패치되지 않는다 |

마지막 항목이 위원회 성명이 가장 강조한 지점이다. 멈추지 않기 때문에 **당한 뒤에야 알게 된다.**

### 12.3 내 클러스터가 해당되는지 확인하기

```bash
# 위원회 성명이 제시한 확인 명령 (클러스터 관리자 권한 필요)
kubectl get pods --all-namespaces \
  --selector app.kubernetes.io/name=ingress-nginx

# IngressClass 쪽에서도 확인
kubectl get ingressclass -o custom-columns=NAME:.metadata.name,CONTROLLER:.spec.controller
```

`CONTROLLER` 컬럼에 `k8s.io/ingress-nginx`가 보이면 해당된다.

### 12.4 어디로 갈 것인가

위원회가 못박은 전제가 하나 있다. **드롭인 대체제는 없다.** 어느 길을 골라도 실제 설계와 검증이 필요하다.

| 경로 | 언제 | 비용 |
|------|------|------|
| **Gateway API로 이전** | 신규 설계, 장기적으로 옳은 방향 | 리소스 모델을 새로 배워야 함 |
| **양쪽 지원 컨트롤러로 교체** (Traefik, Cilium) | 기존 Ingress 자산이 많을 때 | `ingressClassName`만 먼저 바꾸고, 이후 천천히 이전 |
| **다른 Ingress 컨트롤러로 교체** | 당장 Ingress를 유지해야 할 때 | annotation이 컨트롤러별로 달라 재작성 필요 |

장기 목적지는 **Gateway API** 다. 쿠버네티스 프로젝트가 지정한 Ingress의 후계 표준이고, 위원회 성명도 이쪽을 먼저 지목했다. Ingress가 컨트롤러별 annotation으로 떠넘기던 것들 — 헤더 매칭, 트래픽 가중치 — 을 **표준 스키마 필드** 로 올렸고, 리소스를 역할별로 나눈다.

| Ingress 세계 | Gateway API 세계 | 소유자 |
|---|---|---|
| `IngressClass` (`spec.controller`로 구현체 지정) | `GatewayClass` (`spec.controllerName`로 구현체 지정) | 인프라 제공자 |
| **대응 리소스 없음** — 진입점 설정이 Controller의 Service/LB와 `Ingress`의 `tls`·`host` 필드로 흩어져 있었다 | `Gateway` — listener(포트·프로토콜·TLS)를 한곳에 명시하는 진입점 리소스 | 클러스터 운영자 |
| `Ingress`의 `rules` (라우팅 규칙) | `HTTPRoute` | 애플리케이션 개발자 |

가운데 줄이 이 표의 핵심이다. Gateway API는 Ingress 리소스를 셋으로 **이름만 바꿔 쪼갠 게 아니라**, 원래 없던 층을 하나 만들었다. Ingress에서는 "이 클러스터의 진입점은 443 포트로 이 인증서를 쓴다"는 운영자의 결정과 "`/api`는 api-svc로 보낸다"는 개발자의 결정이 **같은 리소스에 섞여** 있었다. 이걸 `Gateway`와 `HTTPRoute`로 분리했기 때문에, 개발자가 라우팅 규칙을 바꾸려고 클러스터 전체 진입점 설정을 건드릴 필요가 없어진다. 반대로 운영자는 인증서를 교체하면서 개발자의 라우팅 규칙을 건드릴 위험이 없다.

```yaml
# Ingress로 쓰던 것을
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-svc
            port:
              number: 80
---
# HTTPRoute로 옮기면
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-route
spec:
  parentRefs:
  - name: prod-gateway        # Gateway 리소스를 참조
  hostnames:
  - "app.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api-svc
      port: 80
```

손으로 다 옮길 필요는 없다. 공식 변환 도구 **`ingress2gateway`** 가 기존 `Ingress` 리소스를 Gateway API 리소스로 상당 부분 자동 변환해준다.

```bash
# 기존 Ingress를 Gateway API 리소스로 변환해 출력
ingress2gateway print --namespace=default
```

> **주의:** 자동 변환은 표준 필드까지다. 컨트롤러별 annotation으로 구현했던 것(rewrite, rate limit, 인증 등 — 이 문서 6절의 내용)은 **대상 구현체의 방식으로 직접 다시 설계해야 한다.** 여기가 이전 작업의 실제 비용이 발생하는 지점이다.

### 12.5 그래서 지금 무엇을 해야 하나

기존 Ingress를 쓰는 클러스터라면 서두를 필요는 없되 방치하면 안 된다. 순서는 이렇다.

1. `kubectl`로 ingress-nginx 사용 여부를 **확인** 한다 (12.3)
2. 쓰고 있다면 유지보수되는 컨트롤러로 **교체 계획** 을 세운다 — 인터넷에 노출된 워크로드가 우선순위다
3. 신규 라우팅 규칙은 **Gateway API로 먼저 검토** 한다
4. 기존 Ingress 리소스 자체는 급히 걷어낼 필요 없다 — API는 살아 있다

---

## 13. 정리

```mermaid
flowchart TB
    subgraph "Ingress 구성요소"
        ING[Ingress 리소스<br>라우팅 규칙]
        IC[Ingress Controller<br>Nginx, Traefik 등]
        TLS[TLS Secret<br>인증서]
    end

    subgraph "기능"
        F1[경로 라우팅]
        F2[호스트 라우팅]
        F3[TLS 종료]
        F4[로드밸런싱]
    end

    ING --> IC
    TLS --> ING
    IC --> F1
    IC --> F2
    IC --> F3
    IC --> F4

    style ING stroke:#9C27B0,stroke-width:2px
    style IC stroke:#2196F3,stroke-width:3px
```

| 질문 | 답변 |
|------|------|
| Ingress만 만들면 동작하나요? | ❌ Ingress Controller 필요 |
| LoadBalancer 대신 Ingress? | HTTP/HTTPS면 Ingress 권장 |
| TLS는 어디서 처리? | Ingress에서 종료 (권장) |

**핵심 기억:**
1. **Ingress** 는 규칙, **Ingress Controller** 가 실행
2. **하나의 진입점** 으로 여러 서비스 라우팅 → 비용 절감
3. **경로** (`/api`)와 **호스트** (`api.example.com`) 기반 라우팅
4. **TLS** 인증서를 한 곳에서 관리
5. 백엔드 Service는 **ClusterIP** 로 충분
6. 클라우드별 **네이티브 LB** 통합: AWS ALB, GKE GCE, Azure App Gateway
7. **커뮤니티 ingress-nginx는 2026년 3월 은퇴** 했다. Ingress **API** 는 멀쩡히 살아 있고(feature-frozen일 뿐) 새 표준은 **Gateway API** 다

> 📖 관련 문서:
> - [Kubernetes Service](./Kubernetes-Service-ClusterIP-NodePort-LoadBalancer.md)
> - [Kubernetes Probe](./Kubernetes-Probe-Liveness-Readiness-Startup.md)
> - [쿠버네티스 Ingress와 Egress는 왜 대칭이 아닐까](./쿠버네티스-Ingress와-Egress는-왜-대칭이-아닐까.md) — Ingress의 반대 방향과 Gateway API 전망
> - [Ingress 리소스가 하나도 없는데 트래픽은 어떻게 들어올까](./Ingress-리소스가-하나도-없는데-트래픽은-어떻게-들어올까-서비스-메시가-대체하는-것들.md) — 서비스 메시가 Ingress를 대체하는 경우

---

## 출처

- [Kubernetes Documentation - Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) - 공식 문서
- [Kubernetes Documentation - Ingress Controllers](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/) - 공식 문서. 유지보수되는 컨트롤러 목록

**ingress-nginx 은퇴 (12절 근거)**

- [Ingress NGINX: Statement from the Kubernetes Steering and Security Response Committees (2026-01-29)](https://kubernetes.io/blog/2026/01/29/ingress-nginx-statement) — **1차 출처.** 2026년 3월 은퇴, 이후 릴리스·버그 수정·보안 패치 없음, 클라우드 네이티브 환경의 약 50%가 사용, 드롭인 대체제 없음, 확인용 `kubectl` 명령
- [CVE-2025-1974 — IngressNightmare](https://nvd.nist.gov/vuln/detail/CVE-2025-1974) — 은퇴 결정을 앞당긴 치명적 취약점
- [Gateway API](https://gateway-api.sigs.k8s.io/) — 위원회가 지목한 후계 표준. `GatewayClass`/`Gateway`/`HTTPRoute` 역할 분리
- [Gateway API — HTTP traffic splitting](https://gateway-api.sigs.k8s.io/guides/user-guides/traffic-splitting/) — `backendRefs`의 `weight`로 가중치 분배
- [ingress2gateway](https://github.com/kubernetes-sigs/ingress2gateway) — Ingress → Gateway API 공식 변환 도구
- [~~Nginx Ingress Controller Documentation~~](https://kubernetes.github.io/ingress-nginx/) — ⚠️ **2026년 3월 아카이브됨.** 본문 6절 annotation 설명의 원 출처이나 더 이상 유지보수되지 않는다
- [AWS Load Balancer Controller - Ingress Annotations](https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/guide/ingress/annotations/) - AWS 공식
- [GKE Container-Native Load Balancing](https://cloud.google.com/kubernetes-engine/docs/how-to/container-native-load-balancing) - GCP 공식
- [Azure Application Gateway Ingress Controller](https://learn.microsoft.com/en-us/azure/application-gateway/ingress-controller-overview) - Azure 공식
- [cert-manager Documentation](https://cert-manager.io/docs/) - cert-manager 공식
