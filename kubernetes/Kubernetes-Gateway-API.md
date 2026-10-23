# Kubernetes Gateway API

> **개발자를 위한 쉬운 쿠버네티스 · 12장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-Ingress.md) · [다음 장](./Kubernetes-Ingress-vs-Egress.md)

**왜 Kubernetes Gateway API는 Ingress를 역할별로 쪼갰을까**

[Ingress 장](Kubernetes-Ingress.md)에서 `order-api`의 host·경로·TLS를 한 리소스에 적었다. 이제 플랫폼 운영자는 인증서와 외부 진입점을 관리하고, 주문 팀은 `/api` 경로만 바꾸려 한다. 같은 Ingress를 공동 편집하는 대신 그 책임을 API에서 나눌 수 있을까?

## 결론부터 말하면

**Gateway API는 Ingress의 필드를 다른 이름으로 옮긴 것이 아니다. "누가 무엇을 결정하는가"를 기준으로 리소스를 다시 나눈 것이다.** 인프라 제공자는 `GatewayClass`로 어떤 구현체를 쓸지 정하고, 클러스터 운영자는 `Gateway`로 포트·TLS·허용 네임스페이스를 정하고, 애플리케이션 개발자는 `HTTPRoute`로 경로와 백엔드를 정한다. 각 역할에 맞는 리소스 권한을 부여할 수 있다. 다만 리소스 사이의 연결 허가와 실제 네트워크 통신 허가는 각각 확인해야 한다.

역할을 나누면 **서로 다른 소유자의 리소스가 연결되는 지점** 이 생긴다. Gateway API는 이 연결을 **양쪽이 모두 동의해야 성립하는 핸드셰이크** 로 설계했다. Route가 `parentRefs`로 Gateway를 가리키고 Gateway의 listener가 `allowedRoutes`로 그 Route를 받아들여야 붙는다. 다른 네임스페이스의 Service나 Secret을 참조하려면 그 네임스페이스 쪽에 `ReferenceGrant`가 있어야 한다.

```mermaid
flowchart TB
    GC["GatewayClass<br>(cluster-scoped)<br>인프라 제공자"]
    GW["Gateway<br>listeners · TLS · allowedRoutes<br>클러스터 운영자"]
    HR["HTTPRoute / GRPCRoute<br>TLSRoute / TCPRoute / UDPRoute<br>애플리케이션 개발자"]
    SVC["Service<br>(백엔드)"]
    RG["ReferenceGrant<br>참조 대상 네임스페이스 소유자"]

    GW -->|gatewayClassName| GC
    HR -->|"parentRefs (요청)"| GW
    GW -.->|"allowedRoutes (수락)"| HR
    HR -->|backendRefs| SVC
    RG -.->|"다른 네임스페이스 참조 허용"| SVC

    style GC fill:#1565C0,color:#fff
    style GW fill:#BF360C,color:#fff
    style HR fill:#2E7D32,color:#fff
    style RG fill:#C62828,color:#fff
```

| 리소스 | 범위 | 누가 만드나 | 무엇을 결정하나 | Standard(GA) 편입 |
|--------|------|------------|----------------|-------------------|
| `GatewayClass` | 클러스터 | 인프라 제공자 | 어떤 컨트롤러가 처리할지 (`controllerName`) | v1.0 (2023-10) |
| `Gateway` | 네임스페이스 | 클러스터 운영자 | 주소, listener(포트·프로토콜·hostname·TLS), 붙을 수 있는 Route | v1.0 |
| `HTTPRoute` | 네임스페이스 | 앱 개발자 | 경로·헤더 매칭, 필터, 백엔드와 가중치 | v1.0 |
| `GRPCRoute` | 네임스페이스 | 앱 개발자 | gRPC service/method 매칭 | v1.1 (2024) |
| `TLSRoute` | 네임스페이스 | 앱 개발자 | SNI로 TLS 연결 분기 (Passthrough 또는 Terminate) | v1.5 (2026-02) |
| `TCPRoute` / `UDPRoute` | 네임스페이스 | 앱 개발자 | 포트 단위 L4 전달 | v1.6 (2026-06) |
| `ReferenceGrant` | 네임스페이스 | 참조 **당하는** 쪽 소유자 | 다른 네임스페이스의 참조 허용 | v1.5에서 `v1` |
| `ListenerSet` | 네임스페이스 | 팀 / 운영자 | 공유 Gateway에 listener를 따로 붙이기 | v1.5 |

> 이 장은 2026-10-23에 확인한 Gateway API v1.5·v1.6 공식 자료를 기준으로 쓴다. 이 버전들은 Kubernetes 자체 버전과 별개이며 최신 patch 번호를 뜻하지 않는다. ingress-nginx 은퇴와 이전 경로는 [Kubernetes Ingress 12절](./Kubernetes-Ingress.md#12-2026년-현재--ingress-nginx-은퇴와-gateway-api), 메시 내부(east-west)에서 쓰는 GAMMA는 [서비스 메시 노트 6절](./Kubernetes-Service-Mesh.md), 가중치로 하는 카나리 배포는 [Deployment Strategy의 HTTPRoute 절](./Kubernetes-Deployment-Strategy.md#httproute로-의도를-표현한다)에서 다뤘다. 여기서는 리소스 모델과 "붙는 규칙"에 집중한다.

---

## 1. 왜 Ingress 하나로는 부족했나

### 1.1 Ingress 한 장에 세 사람의 결정이 섞여 있다

Ingress를 먼저 짚고 가자. **Ingress** 는 "`app.example.com/api`로 온 HTTP 요청은 `api-svc`로 보내라"는 규칙을 적는 쿠버네티스 리소스다. 규칙을 실제로 실행하는 것은 별도로 설치하는 **Ingress Controller** (NGINX, Traefik, AWS ALB 등)다.

작은 팀이라면 이 모델이 편하다. 한 사람이 Ingress 한 장에 호스트, 인증서, 경로를 모두 적으면 끝난다. 그런데 클러스터를 여러 팀이 같이 쓰기 시작하면 이상한 점이 보인다. Ingress 한 장에 적힌 내용을 결정하는 사람이 사실은 셋이다.

| Ingress의 필드 | 실제로 결정하는 사람 | 바꾸는 빈도 |
|---------------|--------------------|-----------|
| `ingressClassName` (어떤 컨트롤러) | 인프라·플랫폼 팀 | 거의 안 바뀜 |
| `tls` (어떤 인증서, 어느 호스트) | 클러스터 운영자, 보안 팀 | 인증서 갱신 때 |
| `rules` (경로 → Service) | 애플리케이션 개발자 | 배포할 때마다 |

세 사람의 결정이 한 리소스에 있으니 권한도 한 단위로만 줄 수 있다. 개발자에게 Ingress 수정 권한을 주면 경로와 함께 인증서와 호스트도 바꿀 수 있다. 반대로 운영자만 Ingress를 고치게 하면 개발자는 경로 하나를 추가할 때마다 티켓을 올려야 한다. 쿠버네티스 RBAC은 **리소스 단위** 로 권한을 주기 때문에 필드 단위로 나누는 방법이 없다.

### 1.2 표준에 없는 것은 annotation으로 흘러갔다

두 번째 문제는 표현력이다. Ingress 스펙이 표준으로 정한 것은 호스트, 경로, TLS 정도다. 헤더로 분기하기, 트래픽 10%만 새 버전에 보내기, 타임아웃, 경로 rewrite는 스펙에 없다. 그래서 컨트롤러마다 `nginx.ingress.kubernetes.io/canary-weight` 같은 **annotation** 으로 기능을 넣었다.

annotation은 쿠버네티스가 스키마 검증을 하지 않는 문자열 key-value다. 오타를 내도 `kubectl apply`는 성공하고, 컨트롤러가 조용히 무시한다. 무엇보다 **컨트롤러를 바꾸면 annotation을 전부 다시 써야 한다.** "쿠버네티스 표준 리소스"를 쓴다고 생각했는데, 실제로 기능이 들어 있는 부분은 특정 구현체 전용 문법이었던 것이다. 2026년 3월 ingress-nginx가 은퇴하면서 많은 팀이 이 비용을 한꺼번에 치르고 있다.

### 1.3 두 팀이 같은 호스트를 쓰면 어떻게 될까

세 번째 문제는 여러 팀이 쓰는 클러스터에서 드러난다. A팀과 B팀이 각자 Ingress에 `host: shop.example.com`, `path: /`를 적었다고 해보자. 어느 쪽이 이길까?

Ingress 스펙은 이 상황의 답을 정하지 않았다. 컨트롤러마다 병합하거나, 먼저 만든 쪽을 쓰거나, 나중 것으로 덮어쓴다. 게다가 **B팀이 A팀의 호스트를 가로채는 것을 막을 표준 장치가 없다.** 네임스페이스로 팀을 나눠도, 라우팅 테이블은 컨트롤러 안에서 하나로 합쳐지기 때문이다.

정리하면 Ingress의 한계는 세 가지다. 권한을 역할별로 나눌 수 없고, 고급 기능이 구현체 전용 문법에 묶여 있고, 여러 팀이 한 진입점을 안전하게 나눠 쓸 수 없다. Gateway API는 이 세 가지를 풀려고 설계됐다. 다만 세 번째는 Gateway API만으로 완전히 풀리지 않는다. 어디까지 막아 주는지는 2.4절에서 본다.

---

## 2. 핵심 개념 — 리소스 네 가지와 붙는 규칙

### 2.1 GatewayClass: "어떤 구현체로 처리할까"

**GatewayClass** 는 namespace에 속하지 않는 cluster-scoped 리소스로, "이 종류의 Gateway는 이 컨트롤러가 처리한다"를 선언한다. Ingress의 `IngressClass`에 해당한다.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: envoy
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller  # 구현체가 정한 고정 문자열
```

GatewayClass 하나는 컨트롤러 하나가 맡는다. 보통 구현체를 설치하면 GatewayClass가 함께 만들어진다. 인프라 팀이 이 리소스를 관리하고 앱 팀은 이름만 알면 된다.

### 2.2 Gateway: Ingress에는 없던 층

**Gateway** 는 "이 클러스터의 입구를 이렇게 연다"를 선언하는 리소스다. 여기에 이 설계의 핵심이 있다. Ingress 세계에는 Gateway에 해당하는 리소스가 없었다. 입구 설정은 컨트롤러의 Service(LoadBalancer)와 Ingress의 `tls` 필드에 흩어져 있었다.

Gateway에는 **listener** 가 여러 개 들어간다. listener 하나는 "이 포트에서 이 프로토콜로, 이 hostname에 대해, 이 인증서로 받는다"를 뜻한다.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: shared-gw
  namespace: infra                 # 운영자가 관리하는 네임스페이스
spec:
  gatewayClassName: envoy
  listeners:
  - name: https                    # Route가 sectionName으로 고를 수 있는 이름
    port: 443
    protocol: HTTPS
    hostname: "*.example.com"
    tls:
      mode: Terminate              # Gateway에서 TLS를 풀고 HTTP로 라우팅
      certificateRefs:
      - name: wildcard-cert        # 같은 네임스페이스의 Secret
    allowedRoutes:
      namespaces:
        from: Selector             # 라벨이 붙은 네임스페이스의 Route만 받는다
        selector:
          matchLabels:
            gateway-access: "true"
```

Gateway 생성은 구현체가 실제 진입점 인프라를 구성하도록 요청하는 계기가 된다. 새 프록시 Deployment·Service를 만들거나, 클라우드 LB를 생성하거나, 이미 실행 중인 LB에 설정을 더하거나, SDN을 구성할 수 있다. API는 이 중 하나를 강제하지 않는다. 따라서 Gateway 개수만 세어 프록시 개수·외부 IP·비용을 계산할 수 없다.

Controller는 Gateway·Route·Service 등을 관찰해 데이터 경로를 구성한다. 사용자 요청은 그 프록시나 LB를 통과한다. Gateway와 HTTPRoute 오브젝트를 패킷이 차례로 통과하는 서버처럼 이해하면 안 된다. 이 구분은 Ingress에서 배운 선언과 실행의 구분을 그대로 확장한다.

### 2.3 Route: 프로토콜별로 나뉜 라우팅 규칙

**Route** 는 "들어온 요청을 어느 백엔드로 보낼까"를 적는 리소스다. Ingress는 HTTP만 다뤘지만 Gateway API는 프로토콜별로 Route 종류를 나눴다.

| Route | 무엇을 보고 분기하나 | 대표 용도 |
|-------|-------------------|----------|
| `HTTPRoute` | hostname, path, header, query, method | 일반 웹·API |
| `GRPCRoute` | gRPC service, method, header | gRPC 마이크로서비스 |
| `TLSRoute` | TLS의 SNI | listener가 `Passthrough`면 복호화 없이 백엔드로 넘기고(백엔드가 TLS 종료), `Terminate`면 Gateway가 TLS를 풀고 TCP 스트림을 넘긴다 |
| `TCPRoute` / `UDPRoute` | listener 포트 | DB, DNS, 게임 서버처럼 L7 정보가 없는 트래픽 |

HTTPRoute에서 Ingress annotation이 하던 일은 **스키마가 있는 필드** 가 됐다. 헤더 매칭은 `matches.headers`, 가중치는 `backendRefs[].weight`, rewrite·리다이렉트·헤더 수정은 `filters`로 쓴다. 스키마와 validation 덕분에 잘못된 필드·값을 더 일찍 발견할 수 있다. unknown field의 거부·경고·제거는 요청의 validation 모드 등에도 영향을 받으므로, apply 성공만으로 모든 필드가 의도대로 처리되었다고 보지는 않는다. 같은 YAML의 이식성도 설치 CRD 버전, 기능의 Core/Extended 지원, conformance profile, 구현체 정책과 외부 인프라 조건이 맞아야 성립한다.

충돌 규칙도 스펙이 정한다. 같은 요청에 여러 Route 규칙이 맞으면 더 구체적인 쪽(정확한 hostname, 긴 경로, 헤더 매치가 많은 쪽 등)이 이긴다. 조건이 같으면 **먼저 만든 Route** 가, 만든 시각도 같으면 `namespace/name` 알파벳 순서로 앞선 쪽이 이긴다. 1.3절에서 컨트롤러마다 달랐던 결과가 구현체와 상관없이 하나로 정해진다.

### 2.4 붙이기: 양쪽이 동의해야 성립한다

역할을 나누면 새로운 문제가 생긴다. **앱 팀의 Route가 운영 팀의 Gateway에 어떻게 연결되는가?** Route가 원하는 Gateway를 마음대로 고를 수 있다면 1.3절의 호스트 가로채기가 그대로 남는다. Gateway가 Route를 일일이 지정해야 한다면, 개발자가 경로를 추가할 때마다 운영자에게 요청해야 하는 1.1절의 문제로 돌아간다.

Gateway API는 **양방향 핸드셰이크** 로 이 문제를 푼다. 두 조건이 모두 맞아야 Route가 붙는다.

1. **Route가 요청한다.** `spec.parentRefs`에 붙고 싶은 Gateway를 적는다. `sectionName`을 쓰면 특정 listener만 고를 수 있다.
2. **Gateway listener가 수락한다.** listener의 `allowedRoutes`가 Route를 허용해야 한다.

`allowedRoutes.namespaces.from`의 값은 세 가지다.

| 값 | 의미 | 쓰는 경우 |
|----|------|----------|
| `Same` **(기본값)** | Gateway와 같은 네임스페이스의 Route만 | 팀 전용 Gateway |
| `Selector` | 라벨 셀렉터에 맞는 네임스페이스의 Route만 | 여러 팀이 쓰는 공유 Gateway (권장) |
| `All` | 모든 네임스페이스 | 신뢰하는 단일 팀 클러스터 |

여기서 가장 흔한 함정이 나온다. **기본값이 `Same`** 이다. 운영자가 `infra` 네임스페이스에 Gateway를 만들고 `allowedRoutes`를 적지 않으면, 다른 네임스페이스의 HTTPRoute는 `parentRefs`를 제대로 적어도 붙지 않는다. `kubectl apply`는 성공하므로 에러도 보이지 않는다.

```mermaid
sequenceDiagram
    participant Dev as 앱 개발자 (team-a)
    participant HR as HTTPRoute
    participant GW as Gateway (infra)
    participant Ctrl as Gateway Controller

    Dev->>HR: parentRefs: infra/shared-gw
    Ctrl->>GW: listener allowedRoutes 확인
    rect rgba(198, 40, 40, 0.3)
    Note over Ctrl,GW: from: Same (기본값)<br>team-a는 허용 안 됨
    Ctrl-->>HR: status Accepted=False<br>reason: NotAllowedByListeners
    end
    rect rgba(46, 125, 50, 0.3)
    Note over Ctrl,GW: from: Selector + team-a에 라벨
    Ctrl-->>HR: status Accepted=True
    end
```

hostname에도 비슷한 규칙이 있다. Route의 `hostnames`와 listener의 `hostname`이 겹치는 부분이 있어야 붙는다. listener가 `*.example.com`인데 Route가 `api.other.com`이면 `NoMatchingListenerHostname`으로 거부된다. 운영자가 listener hostname으로 테두리를 치고, 앱 팀은 그 안에서만 호스트를 고른다.

그렇다면 1.3절의 호스트 가로채기는 완전히 막혔을까? **아니다.** Gateway API가 막아 주는 것은 두 가지다. 허락받지 않은 네임스페이스는 `allowedRoutes`에서 걸러지고, 허락받은 네임스페이스도 listener hostname 밖의 도메인은 쓸 수 없다. 하지만 `Selector`로 허용된 A팀과 B팀이 **둘 다** `shop.example.com`을 선언하는 것은 막지 않는다. 이때는 2.3절의 우선순위 규칙이 이긴 쪽을 정할 뿐이고, 누가 그 hostname의 주인인지는 확인하지 않는다. 이긴 쪽이 구현체와 상관없이 같다는 점만 Ingress보다 나아진 것이다.

팀별 hostname 사용 범위를 강제하려면 **누가 listener의 hostname을 정할 수 있는가** 까지 제한해야 한다. 운영자가 Gateway의 `spec.listeners`에 팀별 hostname을 `a.example.com`처럼 고정하고, 그 listener의 `allowedRoutes`를 A팀 namespace로만 열면 A팀 Route의 연결 경계를 만들 수 있다. 이 전제에는 Gateway와 namespace 허용 label의 수정 권한을 운영자가 통제한다는 조건도 포함된다.

2.6절의 ListenerSet은 listener 추가 권한을 팀에 위임하는 도구다. 팀이 hostname까지 고를 수 있게 하는 것은 운영자가 hostname을 고정해 두는 방식과 다르다. `allowedListeners`로 허용된 팀들이 같은 hostname을 선언했을 때 충돌 우선순위는 승자만 정할 뿐 정당한 소유자를 인증하지 않는다. ListenerSet에 위임할 hostname 범위를 강제하려면 `ValidatingAdmissionPolicy` 같은 admission 정책으로 namespace별 허용 hostname을 제한해야 한다. Route의 hostnames도 팀 경계에 맞게 제한하는 방식과 함께 설계한다.

### 2.5 ReferenceGrant: 참조 당하는 쪽이 허락한다

Route가 Gateway에 붙는 문제는 풀렸다. 그런데 참조는 이것만 있는 게 아니다. `team-a`의 HTTPRoute가 `shared-services` 네임스페이스의 `auth-svc`로 트래픽을 보내고 싶다면? `infra`의 Gateway가 `certs` 네임스페이스에 있는 인증서 Secret을 쓰고 싶다면?

네임스페이스를 넘는 참조를 그냥 허용하면 위험하다. 공격자가 자기 네임스페이스에 HTTPRoute를 만들고 `backendRefs`에 다른 팀의 내부 Service를 적으면, **컨트롤러가 대신 트래픽을 보내준다.** 컨트롤러는 모든 네임스페이스를 볼 권한이 있기 때문이다. 권한 있는 대리인이 권한 없는 사용자의 요청을 대신 수행하는 이런 공격을 **confused deputy** 라고 부른다. 실제로 Ingress·Endpoints 쪽에서 CVE-2021-25740이 이 유형으로 보고됐다.

**ReferenceGrant** 는 이 문제를 푸는 리소스다. 규칙은 하나다. **참조를 당하는 쪽 네임스페이스의 소유자가 ReferenceGrant를 만들어야 한다.**

```yaml
apiVersion: gateway.networking.k8s.io/v1   # v1.5부터 v1
kind: ReferenceGrant
metadata:
  name: allow-team-a-routes
  namespace: shared-services   # 참조 "대상"이 있는 네임스페이스에 만든다
spec:
  from:                        # 누가 참조하나
  - group: gateway.networking.k8s.io
    kind: HTTPRoute
    namespace: team-a
  to:                          # 무엇을 참조하게 허락하나
  - group: ""                  # core API group
    kind: Service
    # name을 생략하면 이 네임스페이스의 모든 Service
```

ReferenceGrant가 필요한 곳과 필요 없는 곳은 다음과 같다.

| 참조 | 필요한 것 |
|------|----------|
| Route `backendRefs` → 다른 네임스페이스 Service | 대상 네임스페이스에 **ReferenceGrant** |
| Gateway `certificateRefs` → 다른 네임스페이스 Secret | 대상 네임스페이스에 **ReferenceGrant** |
| Route `parentRefs` → 다른 네임스페이스 Gateway | ReferenceGrant 불필요. Gateway의 **allowedRoutes** 가 대신한다 (2.4절) |

ReferenceGrant가 없으면 Route는 붙지만 해당 백엔드로 보낼 수 없다. status에 `ResolvedRefs=False`, reason `RefNotPermitted`가 찍힌다.

### 2.6 ListenerSet: 공유 Gateway의 listener를 팀에게 맡기기

2.4절까지의 모델에는 빈틈이 하나 남아 있었다. **listener는 Gateway 안에만 적을 수 있었다.** 팀마다 자기 호스트와 인증서로 HTTPS listener를 추가하려면 운영 팀의 Gateway 리소스를 직접 고쳐야 했다. 역할을 나눴는데 listener만은 다시 한 리소스에 모이는 셈이다. 그리고 Gateway 하나에는 listener를 64개까지만 넣을 수 있다.

v1.5에서 Standard가 된 **ListenerSet** 이 이 빈틈을 메운다. 팀이 자기 네임스페이스에 listener 묶음을 만들고 공유 Gateway에 붙인다. Gateway 쪽은 `allowedListeners`로 받아들일 네임스페이스를 정한다. 연결을 양쪽이 허용한다는 구조는 Route와 비슷하지만, 기본값은 다르다. `allowedRoutes.namespaces.from`은 `Same`인 반면 **allowedListeners의 기본값은 `None`** 이다. `allowedListeners`를 생략하면 같은 namespace의 ListenerSet도 붙지 않는다.

이 위임은 운영자의 Gateway 편집 부담을 줄이는 대신 팀이 listener의 hostname·인증서를 선택하게 한다. 아래 YAML의 `a.example.com`은 A팀의 사용 의도를 보여 줄 뿐 그 hostname의 소유권을 자동으로 등록하지 않는다. 허용할 팀·hostname 범위의 admission 정책과 namespace label 관리 권한은 이 예제 밖에서 준비해야 한다.

```yaml
# 운영자: listener 위임을 허용
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: shared-gw
  namespace: infra
spec:
  gatewayClassName: envoy
  allowedListeners:
    namespaces:
      from: Selector
      selector:
        matchLabels:
          gateway-access: "true"
  listeners:
  - name: http
    port: 80
    protocol: HTTP
---
# team-a: 자기 호스트와 인증서로 listener 추가
apiVersion: gateway.networking.k8s.io/v1
kind: ListenerSet
metadata:
  name: team-a-listeners
  namespace: team-a
spec:
  parentRef:
    name: shared-gw
    namespace: infra
  listeners:
  - name: https-a
    port: 443
    protocol: HTTPS
    hostname: a.example.com
    tls:
      certificateRefs:
      - name: a-cert             # team-a 네임스페이스의 Secret
```

Route를 ListenerSet의 listener에 붙일 때는 `parentRefs`에 Gateway가 아니라 ListenerSet을 적는다(`kind: ListenerSet`, `name: team-a-listeners`, 필요하면 `sectionName: https-a`). 공유 Gateway를 가리키면 ListenerSet의 listener에는 붙지 않는다.

같은 port·hostname 등으로 listener가 충돌하면 부모 Gateway에 직접 정의된 listener가 ListenerSet의 listener보다 우선한다. ListenerSet 사이에는 생성 시각이 오래된 쪽, 동률이면 `namespace/name` 순서가 적용되고, 충돌에서 밀린 listener에는 `Conflicted` 상태가 기록된다. 따라서 운영자가 고정한 listener의 연결 경계와, 팀에게 자유롭게 위임한 listener의 경계는 다르다. B팀이 먼저 A팀 hostname을 선언해 이기는 상황을 막으려면 충돌 순서가 아니라 admission에서 위임 범위를 제한해야 한다.

ListenerSet은 비교적 새 기능이라 구현체마다 지원 여부가 다르다. 쓰기 전에 5절의 conformance 표에서 `ListenerSet` 기능을 확인한다.

---

## 3. 실제 사례 — order-api를 공유 진입점에 연결하기

### 3.1 먼저 운영자가 연결 가능한 범위를 만든다

2.2절의 `infra/shared-gw`에는 `https` listener가 있고, `*.example.com` 인증서를 담은 `wildcard-cert` Secret이 같은 namespace에 준비되어 있다고 가정한다. Gateway API CRD와 선택한 Envoy Gateway 구현체도 별도로 설치되어 있어야 한다. Class나 Gateway YAML 자체는 구현체 설치 명령이 아니다.

운영자가 `allowedRoutes.namespaces.from: Selector`로 `gateway-access: "true"` namespace를 허용했으므로 앱 팀의 `bookstore`에도 그 label이 필요하다. label 수정 권한까지 모든 앱 팀에 주면 허용 범위를 스스로 넓힐 수 있으므로 namespace label의 관리 주체도 정한다.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: bookstore
  labels:
    gateway-access: "true"
```

이 장의 앱은 앞 장과 같은 가상의 `order-api`다. `bookstore/order-api` Service의 `port: 80`이 `app: order-api` Pod의 `8080`으로 연결되어 있다고 가정한다. 이미지 `registry.example.com/book/order-api:1.0.0`과 health·업무 endpoint는 설명용이며 실행 가능한 배포 묶음을 제공하지 않는다.

### 3.2 개발자는 HTTPRoute로 경로를 연결한다

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: order-api
  namespace: bookstore
spec:
  parentRefs:
  - name: shared-gw
    namespace: infra
    sectionName: https
  hostnames:
  - orders.example.com
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: order-api
      port: 80
```

여기서 `parentRefs`는 어떤 입구의 어떤 listener에 붙을지, `hostnames`와 `matches`는 어떤 요청을 받을지, `backendRefs`는 어디로 보낼지를 표현한다. `backendRefs.port`는 Service port인 `80`이다. namespace를 생략했으므로 같은 `bookstore`의 Service를 참조한다. Route가 `infra`의 Gateway를 참조하는 데는 ReferenceGrant가 필요 없고 Gateway의 `allowedRoutes`가 허가를 담당한다.

요청의 논리적 조건은 세 층이다. 먼저 HTTPS listener가 연결을 받고 인증서를 제공한다. 다음으로 listener hostname과 Route hostname이 겹쳐야 하고, 요청 path가 `/api`의 PathPrefix에 맞아야 한다. 그 뒤에 backend로 전달된다. Ingress와 마찬가지로 `/api`를 매칭했다고 그 부분이 자동 삭제되지 않는다.

앱이 `/orders`만 처리한다면 URLRewrite를 추가할 수 있다. Gateway API의 ReplacePrefixMatch는 경로 요소를 기준으로 하므로 아래 `/api`→`/` 설정은 `/api/orders`를 `/orders`로 바꾼다. 문자열을 그대로 이어 붙여 `//orders`를 만드는 규칙이 아니다. 다음은 앞 rule에 합칠 발췌이며, 구현체가 해당 Extended 기능을 지원하는지 먼저 확인한다.

```yaml
# HTTPRoute spec.rules의 항목 발췌
- matches:
  - path:
      type: PathPrefix
      value: /api
  filters:
  - type: URLRewrite
    urlRewrite:
      path:
        type: ReplacePrefixMatch
        replacePrefixMatch: /
  backendRefs:
  - name: order-api
    port: 80
```

반대로 앱이 원래 `/api/orders`를 처리한다면 rewrite를 넣을 이유가 없다. API가 표현할 수 있다는 사실과 앱에 필요한 변경인지는 구분한다. 헤더 매칭·가중치도 같은 방식으로 rule을 확장할 수 있으며, [배포 전략 장](Kubernetes-Deployment-Strategy.md)에서 버전 전환의 의미와 함께 다룬다.

다른 namespace의 인증 Service를 연결하려면 `backendRefs.namespace`와 2.5절의 ReferenceGrant를 함께 준비한다. 이것은 controller가 그 참조를 설정해도 된다는 허가다. 그 Service까지의 NetworkPolicy·라우팅·프로토콜과 실제 응답은 여전히 별도다.

### 3.3 team-b의 GRPCRoute

이 절은 주 예제와 별개인 두 번째 팀의 확장 사례다. `team-b` namespace에도 `gateway-access: "true"` label이 있어야 하고, 구현체가 HTTPS listener에 GRPCRoute를 연결하고 backend에 필요한 HTTP/2/gRPC 프로토콜을 사용할 수 있어야 한다. 같은 `team-b`에 `orders-svc` Service의 port `9090`과 준비된 gRPC backend가 있다고 가정한다.

gRPC는 HTTP/2 위에서 `/패키지.서비스/메서드` 경로로 요청을 보낸다. HTTPRoute로 경로 매칭을 해도 되지만, GRPCRoute는 service와 method를 필드로 받으므로 의도가 더 분명하다.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GRPCRoute
metadata:
  name: orders
  namespace: team-b
spec:
  parentRefs:
  - name: shared-gw
    namespace: infra
  hostnames:
  - grpc.example.com
  rules:
  - matches:
    - method:
        service: shop.v1.OrderService   # 메서드를 생략하면 서비스 전체
    backendRefs:
    - name: orders-svc
      port: 9090
```

### 3.4 status로 선언의 연결을 확인하고 요청으로 경로를 확인한다

Gateway API는 연결 결과를 status에 남긴다. 먼저 `metadata.generation`과 condition의 `observedGeneration`을 비교해 현재 spec에 대한 상태인지 확인한다. 오래된 `True`를 새 설정의 성공으로 읽으면 안 된다. 다음은 관찰 명령이며 이 원고에서 실행한 결과가 아니다.

```bash
kubectl get gatewayclasses.gateway.networking.k8s.io envoy -o yaml
kubectl get gateways.gateway.networking.k8s.io -n infra shared-gw -o yaml
kubectl get httproutes.gateway.networking.k8s.io -n bookstore order-api -o yaml
kubectl get endpointslices -n bookstore -l kubernetes.io/service-name=order-api -o yaml
```

`Gateway`라는 이름은 Istio의 `networking.istio.io` API에도 존재한다. Istio를 구현체로 선택해도 이 장은 `gateway.networking.k8s.io` API를 다루므로 명령에 API group을 명시한다. Istio 자체 Gateway는 기존 workload를 selector로 구성하는 별도 모델이며 같은 YAML로 바꾸어 읽을 수 없다.

| 관찰 | 의미와 다음 확인 |
|---|---|
| Route `Accepted=False`, `NotAllowedByListeners` | parent·listener와 `allowedRoutes`, namespace label을 확인한다 |
| `NoMatchingListenerHostname` | listener hostname과 Route hostnames의 교집합을 확인한다 |
| `NoMatchingParent` | 참조 대상·sectionName·포트와 listener 조건을 확인한다 |
| `ResolvedRefs=False`, `RefNotPermitted` | 참조 대상 namespace의 ReferenceGrant를 확인한다 |
| `ResolvedRefs=False`, `BackendNotFound` | Service 이름·namespace·port가 존재하는지 확인한다 |
| Gateway `Programmed=True`, Route 연결 정상 | 설정 반영 상태의 증거다. DNS·TLS·LB health·endpoint 준비·NetworkPolicy·앱 응답은 실제 요청으로 확인한다 |
| status가 없음 또는 오래됨 | 담당 Class·parent 존재, controller 상태·처리 지연·status 쓰기 권한과 observedGeneration을 함께 확인한다 |

`Accepted`는 선언이 받아들여졌는지, `ResolvedRefs`는 참조를 사용할 수 있는지, `Programmed`는 해당 리소스의 설정이 데이터 경로에 반영되었는지를 판단하는 단서다. 리소스 종류별로 기록되는 condition을 확인해야 한다. 이 값이 True여도 앱의 `/api/orders`가 200을 반환했다는 뜻은 아니다.

실제 요청이 timeout이면 NetworkPolicy는 후보 중 하나다. listener 외부 노출, 클라이언트→LB 방화벽, backend 연결·프로토콜, ready endpoint까지 조사한다. 404·503은 proxy와 앱 로그를 연결해 누가 응답했는지 구분한다. status가 없는 경우도 "controller가 담당하지 않는다" 하나로 확정하지 않는다.

---

## 4. Ingress에서 옮기기 — ingress2gateway

기존 Ingress가 많다면 공식 변환 도구 **ingress2gateway** 로 시작한다. 2026년 기준 v1.0이 Gateway API v1.5 리소스를 생성하고, ingress-nginx, Traefik, Istio, Kong, Cilium, GCE, APISIX 등의 Ingress를 읽는다.

```bash
# 현재 kubeconfig 클러스터의 ingress-nginx Ingress를 읽어 Gateway API YAML로 출력 (적용은 하지 않음)
ingress2gateway print --providers=ingress-nginx --all-namespaces > gateway-resources.yaml

# 클러스터 대신 파일로 입력
ingress2gateway print --providers=ingress-nginx --input-file=ingress.yaml
```

변환되는 것과 안 되는 것의 경계를 알고 시작해야 한다.

| 자동 변환됨 | 직접 다시 설계해야 함 |
|------------|---------------------|
| `ingressClassName` → `gatewayClassName` | 지원하지 않는 annotation, 임의 `configuration-snippet` 등 |
| `tls[].hosts` / `secretName` → HTTPS listener + `certificateRefs` | 네임스페이스 구조 (Gateway를 어디 두고 `allowedRoutes`를 어떻게 열지) |
| `rules[].host` → `hostnames` | 다른 네임스페이스 참조에 필요한 ReferenceGrant |
| path / pathType / backend → HTTPRoute `matches` + `backendRefs` | 구현체 고유 정책 리소스 (타임아웃·재시도 세부 설정 등) |
| 지원 목록에 있는 annotation의 **동작** (ingress-nginx는 CORS·backend TLS·정규식 매칭·rewrite 등 30개 이상) | 지원 목록에 없거나 의미가 딱 맞지 않는 annotation (경고로 표시됨) |

도구 README는 "annotation을 옮기려는 도구가 아니다"라고 밝힌다. annotation 문자열을 Gateway API 리소스에 그대로 **복사하지 않는다** 는 뜻이다. 지원하는 annotation은 그 동작을 Gateway API 필드로 **변환한다**. 2026년 3월 v1.0 발표 기준으로 ingress-nginx annotation 30개 이상이 여기에 해당한다. 지원하지 않거나 의미가 완전히 대응하지 않는 항목은 경고로 표시되고, 이 부분은 사람이 옮겨야 한다. 실무 순서는 다음과 같다.

1. `print`로 결과를 뽑아 **경고 목록** 부터 본다. 이전 작업량은 여기서 정해진다.
2. 변환 결과를 그대로 쓰지 말고 **Gateway를 공유할지, 네임스페이스를 어떻게 나눌지** 먼저 정한다. 도구는 Ingress마다 Gateway를 만들 수 있는데, 구현체에 따라서는 Gateway마다 로드밸런서가 생긴다.
3. 새 Gateway를 **다른 IP로** 띄우고, 같은 요청을 양쪽에 보내 응답을 비교한다.
4. DNS를 새 주소로 옮기고, 한동안 Ingress를 남겨 뒀다가 지운다.

---

## 5. 구현체와 CRD 고르기

### 5.1 Gateway API는 쿠버네티스에 기본으로 들어 있지 않다

Ingress API는 쿠버네티스 본체에 들어 있다. Gateway API는 **CRD로 따로 설치** 한다. 그래서 클러스터 버전과 Gateway API 버전이 따로 움직인다. v1.5 공식 자료는 Kubernetes 1.30 이상을 요구하고, TLSRoute의 CEL 검증에는 1.31 이상이 필요하다고 설명한다. 다른 Gateway API 릴리스는 해당 릴리스와 구현체의 호환성 조건을 따로 확인한다.

CRD는 두 채널로 배포된다.

| 채널 | 들어 있는 것 | 권장 |
|------|------------|------|
| **Standard** | GA 리소스와 필드만. 하위 호환 보장 | 운영 클러스터 기본 |
| **Experimental** | Standard + 실험 리소스·필드. 깨지는 변경 가능 | 특정 기능이 꼭 필요할 때만 |

v1.3부터 **새로 추가되는** 실험 리소스에는 `X` 접두사와 별도 API group `gateway.networking.x-k8s.io`를 사용한다. 당시 도입된 `XListenerSet`은 v1.5에서 `gateway.networking.k8s.io/v1`의 `ListenerSet`으로 Standard에 편입되었다. 이 규칙이 기존 API 버전을 소급해서 옮긴 것은 아니다. v1.6에서 TCPRoute·UDPRoute는 Standard로 졸업했고, 남은 `v1alpha2`는 deprecated 버전이다. 또한 Experimental bundle은 `gateway.networking.k8s.io/v1` kind에도 실험 필드를 추가할 수 있으므로 API group이나 version 문자열만으로 채널을 판단하면 안 된다. 설치한 CRD의 `gateway.networking.k8s.io/channel`과 `gateway.networking.k8s.io/bundle-version` annotation으로 채널과 bundle 버전을 함께 확인한다. [GEP-922](https://gateway-api.sigs.k8s.io/geps/gep-922/)의 채널·버전 구분도 이 경계를 설명한다.

설치할 때 함정이 두 가지 있다.

- **CRD를 누가 설치하나.** 많은 구현체가 Helm 차트에 Gateway API CRD를 포함한다. 구현체 두 개를 설치하거나 클라우드가 CRD를 관리하는 클러스터(GKE 등)에 차트로 다시 설치하면 CRD 버전이 서로 덮어쓰인다. 클러스터에서 CRD 설치 주체를 하나로 정한다.
- **Experimental CRD는 `kubectl apply --server-side=true`로 설치한다.** 크기가 커서 일반 apply가 annotation 크기 제한에 걸린다.

채널 변경은 설치 명령만 바꾸는 일이 아니다. v1.5 Standard의 TLSRoute는 `v1`을 제공하며, 기존 `v1alpha2`·`v1alpha3`를 사용하는 선언은 served version과 저장 버전·변환 조건을 확인해 먼저 이전해야 한다. v1.5 릴리스의 `safe-upgrades.gateway.networking.k8s.io` ValidatingAdmissionPolicy는 Experimental 전용 보호가 아니다. Standard 설치 후 Experimental 설치와 1.5 미만으로의 downgrade를 막는다. 우회부터 시도하지 말고 릴리스 노트의 migration 조건과 영향을 확인한다.

### 5.2 구현체 선택

구현체마다 Gateway API를 얼마나 지원하는지는 공식 **conformance 보고서** 로 확인한다. 기능은 **Core** (모든 구현체가 반드시 지원), **Extended** (선택 지원, 지원한다면 스펙대로), **Implementation-specific** 세 단계로 나뉜다. 헤더 매칭은 Core지만 URL rewrite, 요청 미러링, 재시도는 Extended다. 쓰려는 기능이 Extended라면 보고서에서 그 기능 칸을 확인해야 한다.

| 상황 | 후보 | 이유 |
|------|------|------|
| 벤더 중립, Gateway API 네이티브 | **Envoy Gateway**, kgateway | 처음부터 Gateway API를 기준으로 만든 Envoy 기반 구현 |
| 이미 Istio 메시 사용 | **Istio** | ingress와 메시(GAMMA)를 같은 API로 |
| Cilium CNI 사용 | **Cilium** | Envoy L7 proxy를 Cilium 네트워크와 통합. kubeProxyReplacement·l7Proxy 등 전제 확인 |
| 기존 Ingress와 함께 운영 | **Traefik** | 컨트롤러 하나가 Ingress와 Gateway API를 동시에 처리해 점진 이전 가능 |
| NGINX 계열 유지 | **NGINX Gateway Fabric** | Gateway API 전용 구현체다. 기존 Ingress는 처리하지 않으므로 Ingress Controller와 나란히 두고 리소스를 변환하며 옮긴다 |
| 관리형 클라우드 LB | **GKE Gateway**, **AWS Load Balancer Controller** | 클라우드 LB를 직접 프로비저닝 (AWS는 2026년 기준 부분 conformance) |

---

## 6. 정리

### 핵심 포인트

1. **Gateway API는 리소스를 "누가 결정하나"로 나눴다**
   - `GatewayClass`(인프라) · `Gateway`(운영자) · `*Route`(개발자). Ingress 한 장에 섞여 있던 권한을 RBAC으로 따로 줄 수 있다.

2. **연결은 양쪽이 동의해야 성립한다**
   - Route의 `parentRefs`와 listener의 `allowedRoutes`가 모두 맞아야 붙는다. `allowedRoutes` 기본값은 `Same`이라, 다른 네임스페이스 Route가 안 붙는 가장 흔한 원인이다.

3. **다른 네임스페이스의 백엔드·Secret 참조는 참조 당하는 쪽이 허락한다**
   - 대상 네임스페이스에 `ReferenceGrant`를 둔다. confused deputy 공격을 막는 장치다. Route → Gateway 연결은 예외로 `allowedRoutes`가 담당한다.

4. **annotation이 표준 필드가 됐고, 결과는 status에 남는다**
   - 헤더 매칭·가중치·rewrite를 스키마 필드로 쓰고, 연결 판단은 `Accepted`/`ResolvedRefs`와 reason으로 좁힌다. 실제 요청 성공은 별도로 확인한다.

5. **2026-10-23 확인한 v1.6 자료에서는 TCP·UDP Route도 Standard다**
   - HTTP·gRPC·TLS·TCP·UDP Route와 ReferenceGrant, ListenerSet이 모두 Standard다. CRD는 따로 설치하고 설치 주체는 하나로 정한다. 기능 지원 여부는 conformance 보고서로 확인한다.

> 📖 관련 문서:
> - [Kubernetes Ingress](./Kubernetes-Ingress.md) — Ingress 기본과 12절 ingress-nginx 은퇴
> - [Ingress 리소스가 하나도 없는데 트래픽은 어떻게 들어올까](./Kubernetes-Service-Mesh.md) — 6절 GAMMA, `parentRef`가 Service를 가리키는 메시 라우팅
> - [Kubernetes Deployment Strategy의 HTTPRoute 절](./Kubernetes-Deployment-Strategy.md#httproute로-의도를-표현한다) — HTTPRoute `weight`로 하는 카나리
> - [쿠버네티스 Ingress와 Egress는 왜 대칭이 아닐까](./Kubernetes-Ingress-vs-Egress.md) — Ingress 동결과 Gateway API 전망

---

## 생각해 볼 질문

**Route가 Gateway를 정확히 가리키는데 다른 namespace에서는 붙지 않는다. ReferenceGrant를 추가하면 될까?**

Route→Gateway 연결은 ReferenceGrant 대상이 아니다. Gateway listener의 allowedRoutes와 namespace label, hostname·sectionName 조건을 확인한다. ReferenceGrant는 다른 namespace의 backend·Secret 참조를 허가하는 별도 장치다.

**Programmed=True인데 앱 응답은 실패한다. status가 거짓인가?**

설정 반영과 앱 통신 성공은 서로 다른 주장이다. 현재 generation의 condition인지 확인한 뒤 DNS·TLS·LB와 backend 경로·Readiness·앱 처리를 이어서 확인한다.

**같은 hostname을 A팀과 B팀에 허용하면 소유권도 보장되는가?**

스펙의 충돌 우선순위는 승자를 정하지만 정당한 hostname 소유자를 인증하지는 않는다. 운영자가 hostname을 고정한 Gateway listener와 팀별 allowedRoutes로 연결 경계를 제한할 수 있다. ListenerSet으로 hostname 선택까지 위임한다면 namespace별 허용 hostname을 admission 정책으로 강제해야 한다.

이제 요청이 들어오는 입구의 선언과 권한을 나눌 수 있다. [다음 장](Kubernetes-Ingress-vs-Egress.md)에서는 그 연결 허가와 별개로, Pod 기준으로 들어오고 나가는 통신을 통제하는 NetworkPolicy를 다룬다.

## 출처

- [Gateway API 공식 문서](https://gateway-api.sigs.k8s.io/) — 공식 문서. 리소스 모델, 역할(persona), Route 연결 규칙
- [Gateway API — ReferenceGrant](https://gateway-api.sigs.k8s.io/reference/api-types/referencegrant) — 공식 문서. 참조 대상 네임스페이스에 생성, Core conformance 요구 사항
- [Gateway API — API Reference](https://gateway-api.sigs.k8s.io/reference/api-spec/main/spec) — 공식 스펙. Route-Gateway 연결이 ReferenceGrant 예외라는 규정, status reason 목록
- [gateway-api `apis/v1/shared_types.go`](https://github.com/kubernetes-sigs/gateway-api/blob/main/apis/v1/shared_types.go) — `RouteConditionReason` 상수 정의 (`NotAllowedByListeners`, `RefNotPermitted` 등 3.4절 진단 표의 reason 문자열)
- [Gateway API — Implementer's Guide](https://gateway-api.sigs.k8s.io/guides/implementers-guide) — 공식 문서. Core/Extended 기능 구분
- [Gateway API — Implementations](https://gateway-api.sigs.k8s.io/implementations/) — 공식 conformance 구현체 목록
- [GEP-709: Cross Namespace References from Routes](https://gateway-api.sigs.k8s.io/geps/gep-709) — ReferenceGrant 설계 배경, CVE-2021-25740과 confused deputy
- [Gateway API v1.6: TCPRoute and UDPRoute Graduate to Standard (Kubernetes Blog, 2026-08-03)](https://kubernetes.io/blog/2026/08/03/gateway-api-v1-6-release) — v1.6.0(2026-06-30), TCPRoute·UDPRoute GA
- [Gateway API v1.5: Moving features to Stable (Kubernetes Blog, 2026-04-21)](https://kubernetes.io/blog/2026/04/21/gateway-api-v1-5) — v1.5(2026-02-27), ListenerSet·TLSRoute·CORS·ReferenceGrant v1, 쿠버네티스 1.30 이상
- [Gateway API 1.4: New Features (Kubernetes Blog, 2025-11-06)](https://kubernetes.io/blog/2025/11/06/gateway-api-v1-4) — v1.4에서 GRPCRoute CRD의 `spec` 필드가 필수가 된 변경 (GRPCRoute 자체는 v1.1부터 Standard)
- [kubernetes-sigs/gateway-api Releases](https://github.com/kubernetes-sigs/gateway-api/releases) — Experimental CRD server-side apply 안내, safe-upgrades VAP
- [Ingress2Gateway v1.0 (Kubernetes Blog, 2026-03-20)](https://kubernetes.io/blog/2026/03/20/ingress2gateway-1-0-release/) — ingress-nginx annotation 30개 이상 변환 지원
- [kubernetes-sigs/ingress2gateway](https://github.com/kubernetes-sigs/ingress2gateway) — 공식 변환 도구. 지원 provider, 변환 범위, annotation 비변환 원칙

- [Gateway deployment models](https://gateway-api.sigs.k8s.io/reference/api-types/gateway/)
- [Cilium Gateway API prerequisites](https://docs.cilium.io/en/stable/network/servicemesh/gateway-api/gateway-api/)
- [Istio gateway deployment models](https://istio.io/latest/docs/setup/additional-setup/gateway/)

- [Gateway API v1.3 (2025-06-02)](https://kubernetes.io/blog/2025/06/02/gateway-api-v1-3/) — 새 실험 kind의 X 접두사·별도 API group
- [Gateway API v1.5.0 release notes](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.5.0) — served version 전환과 safe-upgrades VAP
- [HTTPPathModifier v1.5.0 specification](https://github.com/kubernetes-sigs/gateway-api/blob/v1.5.0/apis/v1/httproute_types.go#L1099-L1126) — ReplacePrefixMatch의 경로 요소·슬래시 처리

- [GEP-1713 — ListenerSets](https://gateway-api.sigs.k8s.io/geps/gep-1713/) — listener 위임과 충돌 우선순위
- [Gateway API v1.5 AllowedListeners definition](https://github.com/kubernetes-sigs/gateway-api/blob/v1.5.0/apis/v1/gateway_types.go#L272-L330) — 기본값 None
