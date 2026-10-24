# Kubernetes Admission Webhook

> **개발자를 위한 쉬운 쿠버네티스 · 29장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-CRD-Controller-Operator.md) · [다음 장](./Kubernetes-Cluster-Operations.md)

**내가 만들지 않은 컨테이너가 왜 Pod에 들어와 있을까 — Admission Webhook**

[앞 장](Kubernetes-CRD-Controller-Operator.md)에서는 저장된 리소스를 컨트롤러가 관찰해 작업을 이어 가는 모습을 보았다. 이번에는 저장되기 전으로 돌아간다. 권한이 있는 사용자가 보낸 YAML도 그대로 저장된다고 보장할 수 있을까?

주문 앱 Deployment에는 컨테이너를 하나만 적었는데 실제 Pod에서는 앱 외에 프록시가 보인다고 가정하자. 아래는 Deployment의 **구조 설명용 발췌** 다. 실제 공개 이미지가 아닌 가상 앱을 사용하며, 네트워크·정책·애드온 설치를 검증하는 실행 예제가 아니다.

```yaml
spec:
  template:
    metadata:
      labels:
        app: order-api
    spec:
      containers:
      - name: order-api
        image: registry.example.com/book/order-api:1.0.0
        ports:
        - containerPort: 8080
```

여기서 비교 대상은 세 가지다. 내가 제출한 Deployment, 저장된 Deployment의 Pod template, 그리고 나중에 생성된 실제 Pod다. Deployment와 Pod는 다른 API 객체이므로, 두 객체가 같지 않다는 사실만으로 Deployment 요청을 누가 바꿨다고 결론 내리면 안 된다. 이 구분을 출발점으로 사이드카 주입과 정책 거절을 따라가 보자.

---

## 결론부터 말하면

**`kubectl apply`가 보낸 오브젝트는 그대로 저장되지 않는다.** API 서버는 요청을 받아 etcd에 쓰기 전까지 여러 관문을 통과시키는데, 그중 **admission** 단계에는 오브젝트를 **고치는(mutating)** 권한과 **거부하는(validating)** 권한이 있다. 사이드카 주입은 mutating admission의 대표 사례이고, 정책 위반 거절은 validating admission이 맡을 수 있다. 다만 실제 Pod spec과 적용된 정책·설정을 확인해야 원인을 확정할 수 있다.

```mermaid
sequenceDiagram
    participant U as kubectl
    participant API as API Server
    participant MW as Mutating Webhook
    participant VW as Validating Webhook
    participant E as etcd

    U->>API: POST /apis/apps/v1/namespaces/bookstore/deployments
    rect rgba(69, 90, 100, 0.3)
        Note over API: 1) 인증 authentication — 너는 누구인가
        Note over API: 2) 인가 authorization — 그 일을 할 권한이 있는가
    end
    rect rgba(21, 101, 192, 0.3)
        Note over API,MW: 3) Mutating Admission — 오브젝트를 고칠 수 있다
        API->>API: 요청 종류에 맞는 내장 mutator
        API->>MW: AdmissionReview (여러 개면 순차 호출)
        MW-->>API: allowed=true + JSON Patch
    end
    rect rgba(230, 81, 0, 0.3)
        Note over API: 4) Object schema validation — 변형이 끝난 최종 형태를 검사
    end
    rect rgba(198, 40, 40, 0.3)
        Note over API,VW: 5) Validating Admission — 거부만 할 수 있다
        API->>API: ValidatingAdmissionPolicy (CEL, 서버 내부)
        API->>VW: AdmissionReview (병렬 호출)
        VW-->>API: allowed=true / false
    end
    rect rgba(46, 125, 50, 0.3)
        API->>E: 6) 저장
        E-->>API: 저장 결과
        API-->>U: 요청 결과
    end
```

여기서 놀라운 사실이 하나 더 있다. **웹훅을 하나도 설치하지 않은 평범한 클러스터에서도 내 YAML은 이미 조용히 수정되고 있다.** API 서버에는 admission plugin이 컴파일되어 들어 있고, 그중 상당수가 기본 활성화 상태다.

| 내장 plugin | 내 YAML에 하는 일 | 성격 |
|-------------|-------------------|------|
| `ServiceAccount` | ServiceAccount를 정해주고 API 토큰을 projected volume으로 붙인다 | Mutating + Validating |
| `LimitRanger` | 네임스페이스의 LimitRange에 따라 기본 requests/limits를 채운다 | Mutating + Validating |
| `ResourceQuota` | 네임스페이스 할당량을 넘으면 거부한다 | Validating |
| `PodSecurity` | 네임스페이스 라벨에 선언된 Pod Security Standards를 강제한다 | Validating |
| `DefaultStorageClass` | PVC에 StorageClass가 없으면 기본값을 채운다 | Mutating |
| `MutatingAdmissionWebhook` / `ValidatingAdmissionWebhook` | **외부 웹훅을 호출한다** — 확장 지점 | 각각 |

즉 "내 YAML이 그대로 저장된다"는 직관은 처음부터 틀렸다. 웹훅은 이 자리에 남의 코드를 꽂을 수 있게 열어둔 **확장 지점** 일 뿐이다. 이제 이 관문들을 하나씩 열어보자.

---

## 1. `kubectl apply`를 누르면 실제로 무슨 일이 벌어지는가

### 1-1. 여섯 개의 관문

`kubectl apply`는 결국 API 서버에 HTTP 요청 하나를 보내는 일이다. 그 요청은 다음 순서로 처리된다.

| 순서 | 단계 | 하는 일 | 실패하면 |
|------|------|---------|----------|
| 1 | **인증(authentication)** | 요청자가 누구인지 확정 | 401 |
| 2 | **인가(authorization)** | 그 사용자가 이 verb·리소스를 다룰 권한이 있는지 | 403 |
| 3 | **Mutating Admission** | 오브젝트를 **고친다** (기본값 채우기, 컨테이너 주입) | 거부 시 요청 실패 |
| 4 | **Object schema validation** | 최종 오브젝트가 API 스키마에 맞는지 | 422 등 |
| 5 | **Validating Admission** | 오브젝트를 **검사한다** (통과/거부만) | 거부 시 요청 실패 |
| 6 | **etcd 저장** | 비로소 클러스터의 사실이 된다 | — |

1·2단계에서 판단하는 것은 "이 요청을 보낸 주체가 누구고 무엇을 할 수 있는가"이지 오브젝트의 내용이 아니다. 반면 admission 단계는 공식 문서 표현대로 **"인가 모듈이 볼 수 있는 속성에 더해, 생성·수정되는 오브젝트의 내용 자체에 접근할 수 있다"**. 그래서 "replica가 5개를 넘으면 안 된다", "이미지 태그에 `latest`를 쓰면 안 된다" 같은 판단은 인가가 아니라 admission의 일이다.

ServiceAccount 신원과 RBAC verb 문법 같은 1·2단계의 상세는 [Kubernetes ServiceAccount, RBAC](Kubernetes-ServiceAccount-RBAC.md)에서 다룬다. 이 노트는 3~5단계에 집중한다.

또 하나 중요한 전제. **admission은 읽기 요청에는 걸리지 않는다.** 공식 문서가 못 박아 두듯 admission controller는 오브젝트를 생성·수정·삭제·프록시 연결하는 요청에만 작동하고, 단순히 읽는 요청에는 개입하지 않는다. 단순 get 요청은 이 웹훅 호출로 지연되지 않는다. 쓰기 요청 지연은 매칭되는 웹훅의 수·실행 시간·순차와 병렬 호출에 영향을 받는다. 모든 get이 언제나 빠르다는 뜻은 아니다.

### 1-2. 왜 mutating이 validating보다 먼저인가

순서가 이렇게 정해진 이유는 하나뿐이다. **검사는 최종 형태를 대상으로 해야 의미가 있기 때문이다.**

만약 검증이 먼저였다면 이런 일이 벌어진다. 내가 컨테이너 하나짜리 Pod를 보내고, 검증 웹훅이 "모든 컨테이너에 CPU limit이 있어야 한다"를 확인해 통과시킨다. 그런데 그 뒤에 mutating 웹훅이 CPU limit 없는 프록시 컨테이너를 하나 주입한다. 결과는 **정책을 위반한 오브젝트가 정책 검사를 통과한 상태로 저장되는 것** 이다. 검증의 의미가 사라진다.

그래서 공식 문서는 이 원칙을 명시한다.

> 정책을 강제하기 위해 오브젝트의 **최종 상태** 를 반드시 봐야 하는 admission webhook은 validating admission webhook을 써야 한다. 오브젝트는 mutating webhook이 본 이후에도 변경될 수 있기 때문이다.

이 한 문장이 mutating과 validating을 나누는 근거 전부다. mutating은 "고칠 수 있지만 자기 뒤에 무엇이 올지 모르는" 단계이고, validating은 "고칠 수 없지만 모든 변형이 끝난 것을 보는" 단계다. 4단계의 스키마 검증이 mutating 다음에 오는 것도 같은 이유다 — 주입된 컨테이너까지 포함한 최종 오브젝트가 API 스키마에 맞는지를 봐야 한다.

### 1-3. 왜 "etcd 저장 전"이라는 점이 중요한가

admission은 저장 **전** 에 끼어든다. 이 위치가 컨트롤러와 admission을 완전히 다른 도구로 만든다.

컨트롤러는 이미 저장된 상태를 관찰하고 원하는 상태로 수렴시킨다(desired vs observed의 reconciliation loop는 [쿠버네티스는 어떻게 자기 자신을 확장할까 — CRD와 컨트롤러 그리고 Operator](Kubernetes-CRD-Controller-Operator.md)가 다룬다). 즉 컨트롤러 방식으로 정책을 강제하면 **잘못된 오브젝트가 일단 클러스터에 들어온 뒤** 누군가 그것을 고치거나 지운다. 그 사이의 시간 동안 규칙을 어긴 Pod가 실제로 떠 있을 수 있다.

admission은 그 창을 없앤다. 규칙을 어긴 오브젝트는 **애초에 클러스터의 사실이 되지 못한다.** 사용자에게는 `kubectl apply`가 실패하고 그 자리에서 이유가 보인다. "잘못된 상태를 나중에 고치기"와 "잘못된 상태가 생기지 않게 하기"의 차이이며, 정책 강제를 admission에 두는 이유다.

---

## 2. admission은 웹훅만이 아니다

여기서 도입부의 미스터리로 돌아가기 전에 다리를 하나 놓아야 한다. **admission은 웹훅이라는 이름이 붙기 전에 이미 API 서버 안에 있었다.**

`kube-apiserver`에는 admission plugin들이 컴파일되어 들어 있고, `--enable-admission-plugins`와 `--disable-admission-plugins` 등 서버 설정으로 활성화 범위를 정한다. 이 장에서는 앞 표의 ServiceAccount·LimitRanger·ResourceQuota·PodSecurity를 대표 사례로 삼는다. 정확한 전체 기본 목록은 버전별 [Admission Controllers Reference](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)에서 확인해야 한다. 설치한 배포판의 실제 설정까지 웹 문서의 목록으로 단정할 수는 없다.

ServiceAccount plugin이 Pod에 SA와 projected token volume을 설정해도 토큰을 발급·갱신하고 파일을 전달하는 후속 작업은 kubelet 등 다른 구성 요소가 수행한다. 저장 전 spec 변형과 실행 단계의 파일 공급을 한 동작으로 합치지 않는 것이 핵심이다.

> **PodSecurity의 현재 위치.** 과거의 `PodSecurityPolicy`(PSP)는 v1.21에서 deprecated된 뒤 **v1.25에서 제거** 됐고, v1.25 이후 클러스터에서는 아예 동작하지 않는다. 그 자리를 대신하는 것이 같은 릴리스에서 **stable로 승격된 Pod Security Admission**, 즉 위 목록의 `PodSecurity` plugin이다. PSP처럼 별도 정책 오브젝트를 쓰지 않고 **네임스페이스에 라벨을 붙여** 표준(privileged/baseline/restricted)을 적용한다. 오래된 블로그를 보고 PSP YAML을 쓰려다 막히는 일이 아직 흔하다.

그리고 이 admission plugin들에는 `MutatingAdmissionWebhook`과 `ValidatingAdmissionWebhook`이 있다. 이 둘이 하는 일은 정책 판단이 아니라 **"이 요청에 매칭되는 외부 웹훅을 호출하는 것"** 이다. 즉 admission이라는 파이프라인 자체는 원래부터 있었고, 웹훅은 그 파이프라인에 API server 프로세스 밖의 코드를 연결하는 문이다.

---

<a id="3-웹훅--admission을-클러스터-밖으로-확장하기"></a>

## 3. 웹훅 — API server 밖의 프로그램에 판단을 맡기기

### 3-1. WebhookConfiguration이 선언하는 것

아래는 연결 필드를 보여주는 구조 설명용 설정이다. 실제 Service·서버 인증서·CA가 준비되어야 하며 `<CA_BUNDLE>`은 실제 base64 CA로 바꿀 자리표시자다.

웹훅을 등록한다는 것은 API 서버에게 **"이런 요청이 오면 저기로 물어봐라"** 를 알려주는 일이다. 그 선언이 `MutatingWebhookConfiguration` / `ValidatingWebhookConfiguration`이고, API 그룹은 안정 버전인 `admissionregistration.k8s.io/v1`이다.

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: pod-policy.example.com
webhooks:
- name: pod-policy.example.com
  rules:                          # 어떤 요청에 반응할지
  - apiGroups:   [""]
    apiVersions: ["v1"]
    operations:  ["CREATE"]
    resources:   ["pods"]
    scope:       "Namespaced"
  clientConfig:                   # 어디로 물어볼지
    service:
      namespace: bookstore
      name: policy-webhook
    caBundle: <CA_BUNDLE>         # API 서버가 이 서버를 신뢰할 근거
  namespaceSelector:              # 대상 범위 좁히기 (네임스페이스 라벨 기준)
    matchExpressions:
    - key: kubernetes.io/metadata.name
      operator: NotIn
      values: ["kube-system", "kube-node-lease"]
  admissionReviewVersions: ["v1"]
  sideEffects: None               # 필수 — 부수효과가 있는지 선언
  timeoutSeconds: 5               # 기본 10초, 허용 범위 1~30초
  failurePolicy: Fail             # 기본값 Fail
  matchPolicy: Equivalent         # 기본값 Equivalent
```

각 필드가 무엇을 결정하는지가 이 장의 나머지 절반을 설명한다.

| 필드 | 결정하는 것 | 기본값 |
|------|-------------|--------|
| `rules` | 어떤 apiGroup·apiVersion·resource·operation·scope에 반응할지 | 없음(필수) |
| `clientConfig` | 호출 대상 — 클러스터 안 `service` 또는 외부 `url` | 없음(필수) |
| `caBundle` | API 서버가 웹훅 서버의 TLS 인증서를 검증할 CA | 생략하면 API 서버의 system trust roots |
| `namespaceSelector` | **네임스페이스 라벨** 로 대상 좁히기 | 전체 |
| `objectSelector` | **오브젝트 라벨** 로 대상 좁히기 | 전체 |
| `failurePolicy` | 웹훅을 **호출할 수 없을 때** 요청을 통과시킬지 거부할지 | **`Fail`** |
| `timeoutSeconds` | 응답 대기 시간 (1~30) | **10** |
| `sideEffects` | 오브젝트 밖을 건드리는지 (`None` / `NoneOnDryRun`) | 없음(필수) |
| `matchPolicy` | 다른 API 버전으로 온 같은 리소스도 잡을지 (`Exact` / `Equivalent`) | **`Equivalent`** |
| `reinvocationPolicy` | 다른 plugin이 오브젝트를 고친 뒤 다시 호출받을지 | **`Never`** |

`matchPolicy`의 기본값이 `Equivalent`인 이유가 재미있다. 같은 리소스가 여러 API 그룹·버전으로 제공될 수 있어서, `apps/v1`에만 규칙을 걸어둔 웹훅이 다른 버전으로 온 요청을 놓칠 수 있다. `Equivalent`는 그런 요청도 웹훅이 등록한 버전으로 변환해 보내준다. 공식 문서도 `Equivalent`를 권장한다 — 클러스터를 업그레이드해 새 버전이 열릴 때 웹훅이 조용히 빠지는 사고를 막아준다.

### 3-2. AdmissionReview — 실제로 주고받는 것

API 서버는 웹훅에 `Content-Type: application/json`으로 POST를 보낸다. 본문은 `admission.k8s.io` API 그룹의 **`AdmissionReview`** 오브젝트다. 웹훅은 자기가 이해하는 버전을 `admissionReviewVersions`로 미리 선언해야 한다(필수 필드).

응답도 같은 `AdmissionReview`이고, `response`에 최소 두 필드만 있으면 된다 — 요청의 `uid`를 그대로 복사한 값, 그리고 `allowed`.

```json
// validating: 거부하면서 사용자에게 보일 메시지까지 지정
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "<request.uid 그대로>",
    "allowed": false,
    "status": { "code": 403, "message": "image tag 'latest' is not allowed" }
  }
}
```

```json
// mutating: 통과시키면서 오브젝트를 고친다 — patchType은 JSONPatch만 지원
{
  "apiVersion": "admission.k8s.io/v1",
  "kind": "AdmissionReview",
  "response": {
    "uid": "<request.uid 그대로>",
    "allowed": true,
    "patchType": "JSONPatch",
    "patch": "W3sib3AiOiAiYWRkIiwgInBhdGgiOiAiL3NwZWMvcmVwbGljYXMiLCAidmFsdWUiOiAzfV0="
  }
}
```

여기서 중요한 비대칭이 드러난다. **validating 웹훅은 `allowed`만 답할 수 있고, mutating 웹훅은 거기에 JSON Patch를 얹을 수 있다.** 위 base64를 풀면 `[{"op": "add", "path": "/spec/replicas", "value": 3}]`이다. 즉 mutating 웹훅은 오브젝트를 통째로 돌려주지 않고 **패치만** 돌려준다. 내가 만들지 않은 컨테이너가 Pod에 들어와 있는 이유가 바로 이 몇 줄의 JSON Patch다.

거부 메시지에 웹훅이 직접 쓴 `message`가 담긴다는 점도 기억할 만하다. 나중에 디버깅에서 이 메시지가 결정적인 단서가 된다.

### 3-3. 사이드카 주입이 바로 이것이다

이제 도입부의 장면, 컨테이너를 하나만 적었는데 실제 Pod에는 프록시가 함께 보이는 이유를 설명할 수 있다. 이런 Pod는 `kubectl get pods`에서 `READY 2/2`로 나타난다. 서비스 메시를 도입할 때 하는 일은 대개 이 한 줄이다.

```bash
$ kubectl label namespace bookstore istio-injection=enabled
```

이 라벨은 Pod를 만들지 않는다. **네임스페이스에 라벨을 붙였을 뿐이다.** 그런데 이후 그 namespace에서 **주입 조건에 매칭되는 새 Pod CREATE 요청** 에 프록시 등이 추가될 수 있다. 기존 Pod를 라벨만으로 바꾸지는 않으며 revision·opt-out·CNI·native sidecar 설정에 따라 실제 Pod 구조가 달라진다. 메커니즘은 정확히 3-1에서 본 그것이다.

```mermaid
flowchart LR
    subgraph before["ReplicaSet이 생성 요청한 Pod"]
        y["containers:<br>- order-api"]
    end
    subgraph mech["Mutating Admission"]
        wh["injection webhook<br>namespaceSelector 매칭"]
        p["JSON Patch<br>add /spec/containers/-<br>add /spec/initContainers/-"]
    end
    subgraph after["실제 생성된 Pod — READY 2/2"]
        c1["initContainer<br>네트워크 설정"]
        c2["container: order-api<br>내가 쓴 것"]
        c3["container: proxy<br>주입된 것"]
    end
    y --> wh --> p
    p --> c1
    p --> c2
    p --> c3

    style y fill:#1565C0,color:#fff
    style wh fill:#6A1B9A,color:#fff
    style p fill:#455A64,color:#fff
    style c1 fill:#BF360C,color:#fff
    style c2 fill:#2E7D32,color:#fff
    style c3 fill:#BF360C,color:#fff
```

Deployment 생성 요청이 먼저 admission을 통과해 저장된다. Deployment controller가 ReplicaSet을 만들고, ReplicaSet controller는 template을 바탕으로 별도의 Pod CREATE 요청을 보낸다. 일반적인 Istio 자동 주입은 이 **Pod 요청** 에 매칭된다. Deployment template에 프록시가 없어도 저장된 Pod에는 있을 수 있는 이유다.

메시 컨트롤 플레인이 `MutatingWebhookConfiguration`을 등록해 두고, 그 `namespaceSelector`가 방금 붙인 라벨을 매칭한다. Pod 생성 요청이 올 때마다 API 서버가 선택된 웹훅 endpoint를 호출한다. API server에서 그 endpoint까지의 네트워크 도달성도 별도 전제다. 웹훅은 컨테이너를 추가하는 JSON Patch를 돌려준다. Istio 공식 문서의 예제도 같은 장면을 보여준다 — 라벨 전에는 `1/1`, 라벨 후에는 `2/2`이고 `istio-init`·`istio-proxy` 컨테이너가 추가된다.

여기서 왜 **전 클러스터에 걸지 않고 라벨로 좁히는가** 가 핵심이다. 만약 selector 없이 모든 네임스페이스에 주입한다면 `kube-system`의 컨트롤 플레인 구성요소, CNI·CSI 플러그인 Pod, DNS Pod에까지 프록시가 주입된다. 그러면 클러스터의 네트워킹 자체가 아직 뜨지 않은 프록시에 의존하게 되고, 클러스터가 부팅되지 못한다. 공식 good practices 문서가 명시적으로 권고하는 바도 같다 — `kube-system` 네임스페이스의 오브젝트 매칭을 피하고, `kube-node-lease` 네임스페이스의 Lease 오브젝트는 절대 mutate하지 말라(노드 업그레이드가 실패할 수 있다). 웹훅에서 **범위를 좁히는 것은 최적화가 아니라 안전 장치다.**

(사이드카·서비스 메시를 **왜** 쓰는가, 그 가치와 비용은 [Kubernetes Service Mesh](Kubernetes-Service-Mesh.md)이 다룬다. Pod 안에서 init/sidecar 컨테이너가 어떤 수명주기를 갖는지는 [Kubernetes-Pod](Kubernetes-Pod.md)에 있다. 이 노트는 "어떻게 들어왔는가"만 책임진다.)

### 3-4. 웹훅은 반드시 HTTPS다 — caBundle과 인증서 만료 장애

`clientConfig`에 `caBundle`이 있는 이유를 짚어야 한다. API 서버가 웹훅을 호출한다는 것은 **rules·selector 등에 매칭된 쓰기 요청 내용을 그 서버에 넘긴다** 는 뜻이다. 중간에 누가 가로채거나 웹훅 서버를 사칭하면 클러스터 전체가 조작된다. 그래서 웹훅 호출은 HTTPS만 허용되고, API 서버는 웹훅 서버의 인증서를 검증한다. `caBundle`(PEM을 base64로 담은 필드)은 그 검증에 쓸 CA를 지정하는 선택 필드다. 생략하면 API 서버의 system trust roots로 검증하므로, 사설 CA나 자체 서명 CA로 발급한 인증서라면 `caBundle`로 그 CA를 알려줘야 한다. 공인 CA는 `.svc` 같은 클러스터 내부 이름으로 인증서를 발급하지 않으므로, 클러스터 안 Service로 호출하는 웹훅은 보통 이 경우다. `clientConfig.service`를 쓸 때는 서버 인증서가 `<svc_name>.<svc_namespace>.svc`에 대해 유효해야 한다.

문제는 이 인증서를 누가 관리하느냐다. 손으로 발급하면 만료일에 장애가 예약된다. 그래서 실무 표준은 **cert-manager** 같은 도구에 맡기는 것이다. cert-manager의 `cainjector`는 `ValidatingWebhookConfiguration` · `MutatingWebhookConfiguration` · `CustomResourceDefinition` · `APIService`의 `caBundle` 필드를 채워주며, 웹훅 설정에 `cert-manager.io/inject-ca-from: <namespace>/<certificate>` 애노테이션만 붙이면 CA 데이터가 자동으로 주입된다.

**인증서 만료가 어떻게 클러스터 장애로 번지는가** 가 여기서 나온다. 인증서가 만료되면 API 서버는 웹훅 서버의 TLS를 검증할 수 없다. 이것은 웹훅이 "거부했다"가 아니라 **"호출에 실패했다"** 로 분류된다. 공식 문서가 정리한 `failurePolicy` 적용 대상에 그대로 들어 있다.

- 웹훅 접속 시 네트워크 오류·타임아웃·연결 실패
- 웹훅이 2xx가 아닌 응답이나 잘못된 형식의 응답을 반환
- API 서버가 요청 직렬화나 HTTP 클라이언트 생성에 실패
- (mutating만) 응답의 patch type을 해석할 수 없음

반대로 웹훅이 정상적으로 도달했고 스스로 `allowed: false`로 거부한 경우는 **failure가 아니라 rejection** 이며, `failurePolicy`와 무관하게 항상 요청이 거부된다. 이 구분이 다음 절의 전부다.

---

## 4. 가장 위험한 함정 — `failurePolicy: Fail`과 자기 자신을 막는 교착

### 4-1. `Fail`은 안전한 기본값처럼 보인다

`failurePolicy`의 기본값은 `Fail`이다. 웹훅을 부를 수 없으면 요청을 거부한다. 보안 관점에서 지극히 합리적으로 들린다 — 검사할 수 없으면 통과시키지 않는 게 맞지 않나?

여기서 직관이 무너진다. 이 정책은 **목표한 검사를 수행할 수 있을 때만** 배포 성공과 양립한다. 웹훅 서버 Pod가 전부 죽으면 그 웹훅의 `rules`에 매칭되는 모든 리소스를 **아무것도 만들 수 없다.** 그리고 매칭 범위 안에 **웹훅 서버 자신의 Pod가 포함되어 있으면**, 웹훅 서버를 다시 띄우려는 요청조차 그 죽은 웹훅에 물어봐야 한다. 자력 복구가 불가능한 교착이다.

```mermaid
flowchart TD
    down["웹훅 서버 Pod 전멸<br>노드 장애 · 인증서 만료 · OOM"]
    down --> attempt{"API 서버가<br>웹훅 호출 시도"}
    attempt -->|"연결 실패 / timeout"| fp{"failurePolicy?"}
    fp -->|"Ignore"| ig["요청 통과<br>정책이 조용히 무력화"]
    fp -->|"Fail"| rej["매칭되는 요청 전부 거부"]
    rej --> self{"매칭 범위에 웹훅 서버<br>자신의 네임스페이스가 포함?"}
    self -->|"아니오"| partial["그 범위만 마비<br>웹훅 서버는 재기동 가능"]
    self -->|"예"| dead["교착 — 웹훅 서버 Pod도<br>생성 불가, 자력 복구 불가"]
    dead --> esc["비상 스위치<br>WebhookConfiguration 삭제"]

    style down fill:#C62828,color:#fff
    style ig fill:#BF360C,color:#fff
    style rej fill:#455A64,color:#fff
    style partial fill:#2E7D32,color:#fff
    style dead fill:#C62828,color:#fff
    style esc fill:#1565C0,color:#fff
```

공식 good practices 문서는 이런 순환 의존을 **dependency loop** 로 부르며 두 가지 전형을 든다. 첫째, 두 웹훅이 서로의 Pod를 검사하는 경우 — 둘이 동시에 죽으면 어느 쪽도 시작할 수 없다. 둘째, 웹훅이 자신이 의존하는 애드온(네트워킹·스토리지 플러그인)을 가로채는 경우 — 둘이 함께 죽으면 어느 쪽도 동작할 수 없다.

그래서 처방은 범위를 좁히는 것이다. `namespaceSelector`로 시스템 네임스페이스와 웹훅 자신의 네임스페이스를 제외하고, `objectSelector`로 의존 애드온을 제외하고, 웹훅 서버는 여러 replica로 `ClusterIP` Service 뒤에 두고, `rules`를 정말 필요한 리소스·verb로만 최소화한다. 공식 문서의 배포 순서 권고도 이 사고방식이다 — **웹훅 서버를 먼저 띄우고, `failurePolicy: Ignore`로, `namespaceSelector`를 테스트 네임스페이스로 좁혀서 배포한 뒤** 문제가 없는지 보고 범위를 넓혀라.

### 4-2. 클러스터를 잠갔을 때 빠져나오는 길

먼저 실패한 요청에서 웹훅 이름과 호출 실패 원인을 특정한다. endpoint 복구, 인증서·CA 갱신, selector 범위 조정, 일시적인 failure policy 변경, 설정 제거 중 무엇이 필요한지 결정한다. 정책을 우회하면 그동안 검사가 빠지므로 대상과 기간, 복원 조건을 함께 정해야 한다.

일반적인 API 기반 등록에서는 WebhookConfiguration 변경·삭제가 비상 복구 수단이 될 수 있다. 이 설정 객체들을 일반 동적 웹훅으로 다시 검사하지 않는 예외가 있기 때문이다. 그러나 API 접근과 해당 RBAC 권한이 먼저 필요하고, 모든 구성에서 삭제가 항상 된다고 보장하지 않는다. **Manifest-based admission** 은 웹훅과 CEL 정책을 API 오브젝트가 아니라 API server가 읽는 정적 파일(`AdmissionConfiguration`의 `staticManifestsDir`)에서 불러온다. 이 설정은 API로 조회·변경되지 않고, API 기반 admission 설정 객체에 대한 요청도 검사할 수 있어 설정 자체를 보호하는 데 쓰인다. 2026-10-24 확인한 공식 문서 기준 v1.37에서 Beta가 되었고 feature gate `ManifestBasedAdmissionControlConfig`는 기본 활성이다. gate가 켜져 있어도 정적 manifest 디렉터리를 구성하지 않으면 추가되는 설정은 없다. [Manifest-Based Admission Control](https://kubernetes.io/docs/reference/access-authn-authz/manifest-admission-control/)

따라서 장애 전에 웹훅 서버와 의존 애드온이 서로의 재생성을 막지 않게 설계하고, 실제 서버 구성에서 사용할 수 있는 복구 경로를 확인해야 한다. 설정을 지울 수 있다는 설명만으로 가용성 설계를 대신할 수는 없다.

그래서 이 오브젝트에 대한 쓰기 권한은 정확히 그만큼 위험하다. 공식 문서는 `admissionregistration.k8s.io/v1`의 `MutatingWebhookConfigurations`에 대한 **create·update·patch·delete·deletecollection** 권한을 신뢰할 수 있는 주체에게만 주라고 권고한다. 그 권한이 있으면 매칭 범위를 넓혀 다수의 쓰기 요청을 조작하거나 중요한 정책을 무력화할 수 있다.

### 4-3. `Ignore`의 반대 위험 — 그리고 공식 권고

그렇다면 전부 `Ignore`로 두면 되는가? 여기서 반대편 위험이 있다. 보안 정책 웹훅이 `Ignore`면, 서버가 죽어 있는 동안 **정책이 조용히 무력화된다.** 요청은 통과하고, 아무 에러도 나지 않고, 아무도 모른다. 요청은 거부 기록으로 남지 않지만, 감사 설정에 따라 webhook 실패와 관련된 정보는 기록될 수 있다. 공격자 입장에서는 웹훅 서버 하나만 죽이면 정책이 사라지는 셈이다.

즉 `failurePolicy`는 **가용성과 강제력의 트레이드오프** 이고, 웹훅의 목적에 따라 답이 다르다.

| 웹훅의 목적 | 권장 | 이유 |
|-------------|------|------|
| 선택적 기본값·주입 (mutating) | `Ignore` 검토 | 누락을 허용할 수 있는 기능이면 API 가용성에 유리 |
| 필수 보안 검증·보안에 필수인 주입 | `Fail` 또는 최종 상태 강제 | 검사·필수 주입 누락 시 요청 거절을 수용하고 고가용성을 설계 |

공식 good practices 문서는 여기서 한 걸음 더 나간 조합을 권한다. **mutating 웹훅은 `Ignore`로 fail open 시키고, 강제는 validating 단계에서 하라.**

> mutating 웹훅은 `failurePolicy`를 `Ignore`로 두어 "fail open"하게 하라. 그리고 validating controller로 요청의 상태가 정책을 만족하는지 검사하라.

이 조합은 변형과 강제의 책임을 나눈다. mutator가 실패해도 최종 객체가 이미 규칙을 만족하면 validator가 허용할 수 있다. 반대로 필수 주입이 빠진 객체를 validator가 거절하면 **그 요청은 실패한다**. 배포 가용성과 필수 주입을 동시에 무조건 보장하는 조합은 아니다. 사이드카가 관측용 편의 기능인지, 통신 보안의 필수 요소인지부터 판단해야 한다. 또한 `Ignore`는 호출 오류 처리 정책이며 정상 응답의 `allowed: false`를 허용으로 뒤집지 않는다.

### 4-4. 여러 웹훅의 순서와 재호출

웹훅이 여러 개면 또 다른 문제가 생긴다. 공식 문서에 따르면 mutating 웹훅은 **순차(serial)** 로 호출되고 각각이 오브젝트를 고칠 수 있다. 반면 validating 웹훅은 병렬로 호출되며 전부 통과해야 저장된다(고치지 않으므로 순서가 의미 없다).

순차라는 말은 **앞 웹훅의 결과를 뒤 웹훅이 본다** 는 뜻이다. 서로 같은 필드를 건드리면 최종 결과가 순서에 의존한다. 그런데 공식 good practices는 이렇게 못 박는다.

> mutating admission 웹훅은 일관된 순서로 실행되지 않는다. 여러 요인이 특정 웹훅이 호출되는 시점을 바꿀 수 있다. 웹훅이 admission 과정의 특정 지점에서 실행된다고 가정하지 마라.

즉 **순차 호출이지만 순서를 신뢰할 수는 없다.** 그래서 모든 mutating 웹훅은 **멱등(idempotent)** 해야 한다 — 자기가 이미 고친 오브젝트에 다시 실행돼도 추가 변경을 만들지 않아야 한다. 사이드카 주입 웹훅이 "이미 프록시 컨테이너가 있으면 아무것도 하지 않는다"를 반드시 체크하는 이유가 이것이다.

`reinvocationPolicy`는 이 문제의 부분적 해법이다. 여기서 정확히 구분해야 할 것이 있다.

- **내장 mutating plugin** 은 mutating 웹훅이 오브젝트를 고치면 **자동으로 다시 실행된다.** (그래서 주입된 컨테이너에도 LimitRanger의 기본값이 채워진다.)
- **mutating 웹훅** 은 자동 재호출되지 **않는다.** 재호출을 원하면 `reinvocationPolicy: IfNeeded`를 명시해야 한다. 기본값은 `Never`다.

`IfNeeded`도 완전한 보장은 아니다. 공식 문서는 추가 호출 횟수가 정확히 한 번이라는 보장이 없고, 재호출로 오브젝트가 또 바뀌면 다시 호출된다는 보장도 없다고 명시한다. 그래서 결론은 다시 같은 곳으로 온다 — **모든 변형이 완료된 상태를 확실히 검사하려면 validating admission 웹훅을 쓰라.** `reinvocationPolicy`에 기대는 대신 validating으로 최종 상태를 확인하는 것이 정석이다.

---

## 5. 웹훅 없이 하기 — CEL 기반 정책과 정책 엔진의 실체

### 5-1. Validating Admission Policy — 서버 안에서 검증하기

4절 전체가 하나의 문제로 요약된다. **웹훅은 kube-apiserver 프로세스 밖의 서버이며, 호출 실패가 매칭된 API 요청에 영향을 줄 수 있다. 클러스터 안의 Service로 배포되어 있어도 이 의존성은 남는다.** TLS 인증서, replica, `failurePolicy`, 순환 의존 — 전부 "외부 서버"에서 파생된 비용이다.

그렇다면 검증 로직을 API 서버 **안에서** 실행할 수 있다면? 그것이 **ValidatingAdmissionPolicy** 다. CEL(Common Expression Language) 표현식으로 규칙을 쓰고, API 서버가 그것을 in-process로 평가한다.

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: "demo-policy.example.com"
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups:   ["apps"]
      apiVersions: ["v1"]
      operations:  ["CREATE", "UPDATE"]
      resources:   ["deployments"]
  validations:
  - expression: "object.spec.replicas <= 5"   # 서버 안에서 평가된다
```
```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: "demo-binding-test.example.com"
spec:
  policyName: "demo-policy.example.com"
  validationActions: [Deny]
  matchResources:
    namespaceSelector:
      matchLabels:
        environment: test          # 정책 정의와 적용 범위가 분리된다
```

정책 정의(`ValidatingAdmissionPolicy`)와 적용 범위(`...Binding`)를 분리하는 구조가 특징이다. 하나의 정책을 여러 범위에 다르게 붙일 수 있다.

핵심 장점은 별도 웹훅 서버의 네트워크·TLS·replica 의존을 줄이는 데 있다. 잘못된 거부 규칙이나 정책 평가 오류까지 사라지는 것은 아니다. 띄울 Pod도, 관리할 TLS 인증서도, 죽어서 클러스터를 잠글 서버도 없다. 공식 good practices 문서가 순환 의존을 피하는 방법의 첫 번째로 ValidatingAdmissionPolicy를 드는 것도 이 때문이다. 지연도 네트워크 왕복이 없어 훨씬 작다.

### 5-2. 현재 상태와 선택 기준

두 CEL 기반 정책의 성숙도는 이제 충분하다(2026-10-23 기준, 공식 문서 확인).

| 기능 | 상태 | API |
|------|------|-----|
| **ValidatingAdmissionPolicy** | v1.30 **stable(GA)** | `admissionregistration.k8s.io/v1` |
| **MutatingAdmissionPolicy** | v1.36 **stable(GA)**, 기본 활성화 | `admissionregistration.k8s.io/v1` |

`ValidatingAdmissionPolicy`의 기본 활성화 여부는 [공식 admission controller 목록](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#which-plugins-are-enabled-by-default)과 사용 중인 API server 설정에서 확인한다. `MutatingAdmissionPolicy`는 CEL의 오브젝트 생성 구문과 Server-Side Apply merge 전략(또는 JSON Patch)을 써서 **사이드카 주입·기본 라벨 설정 같은 변형까지 서버 안에서** 처리한다. 즉 3-3절의 사이드카 주입도 이제 웹훅 없이 선언할 수 있다.

그렇다면 웹훅은 언제 쓰는가. 공식 문서의 정리가 그대로 선택 기준이다.

| 요구 | 도구 | 이유 |
|------|------|------|
| 오브젝트 필드만 보고 판단 가능한 규칙 | **CEL 정책** | 외부 서버 없음. 공식 문서 권장 |
| 라벨·기본값·replica 조정 같은 단순 변형 | **MutatingAdmissionPolicy** | 위와 동일 |
| 외부 API 호출이 필요한 판단 (레지스트리 조회, 서명 검증 등) | **웹훅** | CEL은 외부 통신을 할 수 없다 |
| CEL로 표현하기 어려운 복잡한 로직 | **웹훅** | 임의의 코드를 쓸 수 있다 |

> 일반적으로 로직을 선언·설정하는 확장 가능한 방식이 필요하면 **웹훅** 을, 웹훅 서버를 운영하는 부담 없이 단순한 로직을 선언하려면 **내장 CEL 기반 admission** 을 쓰라. 쿠버네티스 프로젝트는 **가능하면 CEL 기반 admission을 권장한다.**

즉 방향은 분명하다. **웹훅은 "외부 세계와 대화해야 할 때"를 위한 도구로 좁혀지고 있다.**

### 5-3. 정책 엔진은 결국 웹훅이다

여기서 실무의 큰 그림이 맞춰진다. Kyverno나 OPA Gatekeeper 같은 정책 엔진을 설치하면 정책을 CRD로 선언하게 되는데, **그 정책이 실제로 강제되는 지점은 3절에서 본 그 웹훅이다.** Kyverno 공식 문서가 직접 밝힌다 — 설치 시 정책과 리소스 요청을 받기 위한 `ValidatingWebhookConfiguration`과 `MutatingWebhookConfiguration`을 만들고, admission controller Deployment가 API 서버의 웹훅 콜백을 처리한다.

그래서 정책 엔진에도 4절의 함정이 **그대로** 적용된다. Kyverno 문서가 직접 경고하는 시나리오가 정확히 그것이다 — 정책을 fail-closed로 설정한 상태에서 클러스터 장애가 나면 Kyverno Pod가 뜨지 못하고, 웹훅 설정 조정·제거 같은 비상 조치가 필요할 수 있다. 서버 복구와 정책 복원 경로를 함께 마련해야 한다. 정책 엔진을 쓴다고 웹훅의 운영 부담이 사라지는 게 아니라, 남이 만든 웹훅을 운영하게 되는 것이다.

이 구조를 알면 공급망 보안이 왜 admission에 걸리는지도 보인다. [Helm과 Harbor를 왜 같이 써야 하는가](Helm과-Harbor를-왜-같이-써야-하는가.md)에서 다룬 이미지 서명 검증이 그 예다. "서명되지 않은 이미지를 쓰는 Pod를 거부한다"는 규칙은 레지스트리에 서명을 조회해야 하니 CEL로는 표현할 수 없다 — 즉 5-2절 표의 "외부 API 호출이 필요한 판단"에 해당하고, 그래서 정책 엔진의 **admission webhook에서 정책에 따라 검증한다.** Kyverno의 기존 `ClusterPolicy` `verifyImages` 규칙은 [공식 실행 단계 설명](https://kyverno.io/docs/policy-types/cluster-policy/verify-images/overview/)처럼 mutation webhook 단계에서도 수행된다. 다만 2026-10-24 확인 기준 `ClusterPolicy`와 `Policy`는 Kyverno v1.19(2026-08-20)에서 deprecated되었고 v1.20에서 제거될 예정이다. 이미지 검증의 대체 정책 타입은 `ImageValidatingPolicy`이며, 새 정책 타입이 어느 webhook 단계에서 동작하는지는 이 설명을 그대로 적용하지 말고 해당 문서에서 확인한다. 해당 요청이 정책에 매칭되어 거부되면 서명 없는 이미지의 Pod는 **애초에 etcd에 들어오지 못한다.**

CRD로 만든 커스텀 리소스를 검증할 때도 같은 웹훅 메커니즘이 쓰인다. 다만 공식 문서는 CRD의 경우 웹훅보다 **내장 검증·기본값 기능(OpenAPI 스키마, CEL validation rules)을 먼저 쓰라** 고 권한다. CRD와 컨트롤러 쪽 상세는 [쿠버네티스는 어떻게 자기 자신을 확장할까 — CRD와 컨트롤러 그리고 Operator](Kubernetes-CRD-Controller-Operator.md)에 있다.

---

## 6. 디버깅 — 누가 내 리소스에 끼어들었나

이제 도입부의 두 미스터리를 실제로 추적할 수 있다.

**첫째, 누가 끼어들 수 있는지 목록을 본다.** 공식 문서가 안내하는 첫 명령이다. 내 웹훅을 하나도 만들지 않았어도 서드파티 애드온이 심어둔 웹훅이 있을 수 있다.

```bash
$ kubectl get mutatingwebhookconfigurations,validatingwebhookconfigurations -o custom-columns='KIND:.kind,CONFIGURATION:.metadata.name,WEBHOOKS:.webhooks[*].name'
KIND                            CONFIGURATION      WEBHOOKS
MutatingWebhookConfiguration    sidecar-injector   sidecar-injector.example.com
ValidatingWebhookConfiguration  policy-enforcer    policy-enforcer.example.com,other-policy.example.com
```

위 출력은 설명용이다. `CONFIGURATION`은 `metadata.name`, `WEBHOOKS`는 각 `webhooks[].name`이며 서로 다른 이름이다.

**둘째, 거부 메시지에서 웹훅 이름을 읽는다.** 3-2절에서 본 대로 거부 응답의 `status.message`가 사용자에게 그대로 전달되고, API 서버는 어느 웹훅이 거부했는지도 함께 알려준다.

```bash
$ kubectl apply -f order-api.yaml
Error from server: admission webhook "policy-enforcer.example.com" denied the request:
  image tag 'latest' is not allowed
# WEBHOOKS 열의 이름과 대조하고 같은 행의 CONFIGURATION을 확인한다
```

`admission webhook "<이름>" denied the request` 형태가 보이면 **웹훅이 정상 동작하며 거부한 것**(rejection)이다. 반면 `failed calling webhook`, `context deadline exceeded`, `x509: certificate has expired` 같은 메시지가 보이면 **호출 자체가 실패한 것**(failure)이고, 3-4절에서 정리한 대로 `failurePolicy`가 적용된 결과다. 이 구분이 "정책을 고쳐야 하는가" vs "웹훅 서버를 살려야 하는가"를 가른다.

**셋째, 어떤 객체의 admission을 확인할지 정한 뒤 서버 dry-run을 쓴다.** Deployment dry-run은 Deployment 요청의 변형·검증을 보여준다. 저장하지 않으므로 후속 Deployment·ReplicaSet controller가 Pod를 만드는 과정은 실행하지 않는다. 따라서 그 출력에서 Pod 사이드카 주입 결과를 기대하면 안 된다.

Pod 자동 주입을 확인하려면 해당 namespace·라벨·SA 등 주입 조건을 맞춘 **Pod CREATE** 를 검사한다. 아래는 완전한 설명용 Pod manifest이며 `order-api-pod.yaml`로 저장했다고 가정한다. `bookstore` namespace와 대상 injector·인증서·연결이 준비되어야 한다. 앱·이미지는 가상이고, 실제 실행 결과가 아닌 검사 방법을 설명한다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: order-api-admission-check
  namespace: bookstore
  labels:
    app: order-api
spec:
  containers:
  - name: order-api
    image: registry.example.com/book/order-api:1.0.0
    ports:
    - containerPort: 8080
```

```bash
# 이 Pod 요청의 admission 결과만 확인한다. 저장하거나 실행하지 않는다.
kubectl create -f order-api-pod.yaml --dry-run=server -o yaml

# 실제 Deployment가 이미 존재한다면 template과 생성된 Pod를 따로 비교한다.
kubectl get deployment order-api -n bookstore -o yaml
kubectl get pods -n bookstore -l app=order-api -o yaml
```

서버 dry-run은 보낸 객체의 admission·검증 등 통상 요청 처리를 수행하고 저장을 생략한다. 출력에 프록시가 추가되면 해당 조건의 Pod 요청이 변형될 수 있음을 보여주지만, 스케줄링·이미지 pull·프록시 readiness·앱 통신 성공은 증명하지 않는다. 반대로 `--dry-run=client`는 이 서버 admission을 거치지 않는다. [API Concepts: Dry-run](https://kubernetes.io/docs/reference/using-api/api-concepts/#dry-run)

Deployment 저장은 성공했는데 Pod가 하나도 없다면 ReplicaSet의 Events도 중요하다. 사용자의 Deployment 요청은 허용됐지만 컨트롤러가 보낸 Pod CREATE가 정책 거절이나 웹훅 timeout으로 실패했을 수 있다. 두 요청의 주체와 대상 리소스가 다르므로 사용자에게 Pod 생성 권한을 더 주는 것이 자동 해법은 아니다.

여기에 3-1절의 `sideEffects` 필드가 왜 필수인지도 연결된다. 부수효과가 있는 웹훅은 `dryRun: true` 요청에서 그 효과를 억제해야 하고, 억제할 수 있다고(`NoneOnDryRun`) 또는 애초에 부수효과가 없다고(`None`) 명시적으로 선언하지 않으면 **dry-run 요청이 그 웹훅에 전달되지 않고 API 요청 자체가 실패한다.** 즉 `sideEffects`는 dry-run이 안전하게 동작하기 위한 계약이다.

---

## 정리

### 핵심 포인트

1. **내 YAML은 그대로 저장되지 않는다 — admission이 etcd 앞에 서 있다**
   - API 요청은 인증 → 인가 → **mutating admission** → 스키마 검증 → **validating admission** → etcd 저장 순서로 처리된다. mutating이 먼저인 이유는 검사가 최종 형태를 대상으로 해야 의미가 있기 때문이고, etcd 저장 전이라는 위치 때문에 잘못된 상태가 애초에 클러스터에 들어오지 못한다.

2. **admission은 웹훅만이 아니다 — 평범한 클러스터도 이미 내 YAML을 고친다**
   - `ServiceAccount`(토큰 볼륨), `LimitRanger`(기본 requests/limits), `ResourceQuota`(초과 거부), `PodSecurity`(보안 표준) 같은 내장 plugin이 기본 활성화되어 있다. 웹훅은 그 파이프라인에 API server 프로세스 밖의 코드를 호출하는 확장 지점이다. `PodSecurityPolicy`는 v1.25에서 제거되고 Pod Security Admission이 그 자리를 대신한다.

3. **사이드카 주입의 실체는 mutating webhook + `namespaceSelector`**
   - 네임스페이스에 라벨 하나를 붙이면 그 안의 Pod에 프록시가 주입되는 것은, 웹훅이 JSON Patch로 컨테이너를 추가하기 때문이다. 범위를 라벨로 좁히는 것은 최적화가 아니라 안전 장치다 — 시스템 네임스페이스까지 주입되면 클러스터 자체가 부팅되지 못한다.

4. **`failurePolicy`는 가용성과 강제력의 트레이드오프다**
   - 기본값 `Fail`은 웹훅 서버가 죽으면 매칭 리소스를 아무것도 만들 수 없게 하고, 매칭 범위에 웹훅 서버 자신이 포함되면 자력 복구 불가 교착이 된다. `Ignore`는 반대로 호출하지 못한 정책의 강제를 생략한다. 공식 권고는 **mutating을 `Ignore`로 fail open 시키고 강제는 validating에서 하는 것** 이다. 복구에는 서버·인증서 복구나 설정 조정·제거가 쓰이며, 가능한 방법은 API 접근 권한과 admission 등록 방식에 따라 달라진다.

5. **외부 서버가 필요 없는 길이 열렸다 — 웹훅은 "외부와 대화할 때"로 좁혀진다**
   - CEL 기반 **ValidatingAdmissionPolicy(v1.30 GA)** 와 **MutatingAdmissionPolicy(v1.36 GA)** 는 API 서버 안에서 평가되므로 외부 웹훅 서버의 네트워크·TLS 의존을 줄인다. 공식 문서도 가능하면 CEL 기반을 권장한다. 반대로 이미지 서명 검증처럼 외부 API를 조회해야 하는 판단은 여전히 웹훅의 몫이고, Kyverno·OPA Gatekeeper 같은 정책 엔진의 실체도 결국 이 웹훅이다.

---

저장 전 정책 적용을 보았으니 다음 [클러스터 운영](Kubernetes-Cluster-Operations.md)에서는 이 제어 경로와 앱을 지탱하는 Node·runtime·네트워크·저장소를 어떻게 유지하는지 살펴본다. 이후 종합 장애 사례에서 배포와 요청 경로의 관찰을 하나로 연결한다.

## 생각해 볼 질문

1. **Deployment apply가 성공했는데 ReplicaSet에 FailedCreate가 있다. admission과 무관할까?** Deployment와 Pod 생성은 별도 API 요청이다. Pod CREATE에만 매칭되는 웹훅이 후속 요청을 거절할 수 있으므로 ReplicaSet Events와 웹훅 이름·오류를 확인한다.
2. **Deployment의 서버 dry-run에 프록시가 없으면 주입이 꺼진 것일까?** 그 요청은 Pod CREATE가 아니다. namespace·라벨 등 실제 조건을 맞춘 Pod dry-run이나 실제 생성 Pod를 확인해야 한다.
3. **mutator를 Ignore, validator를 Fail로 두면 배포 가용성과 필수 주입이 모두 보장될까?** 필수 주입이 빠지면 validator가 요청을 거절한다. 최종 상태 강제와 무조건 배포 성공은 같은 약속이 아니다.

클러스터 운영까지 읽은 뒤 마지막 [종합 장애 추적](Kubernetes-Troubleshooting-From-Apply-to-Request.md)에서 요청 거절, 후속 Pod 생성, 실행, 실제 사용자 트래픽을 서로 다른 증거로 이어 볼 수 있다.

## 출처

- [Admission Controllers Reference | Kubernetes](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/) — 기본 활성화 plugin 목록(2026-10-24 확인 시 v1.37 기준), 각 plugin의 mutating/validating 성격, mutating 웹훅의 순차 호출, PodSecurity(v1.25 stable)
- [Dynamic Admission Control | Kubernetes](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) — `admissionregistration.k8s.io/v1`, AdmissionReview(`admission.k8s.io/v1`) 요청·응답, JSONPatch, `failurePolicy` 기본값 `Fail`, `timeoutSeconds` 기본값 10(1~30), `matchPolicy` 기본값 `Equivalent`, `reinvocationPolicy` 기본값 `Never`, `sideEffects`, `namespaceSelector`
- [Admission Webhooks Good Practices | Kubernetes](https://kubernetes.io/docs/concepts/cluster-administration/admission-webhooks-good-practices/) — 웹훅 목록 확인 명령, `kube-system`·`kube-node-lease` 제외 권고, dependency loop, fail open 권고, 순서 비의존·멱등성, 배포 순서, RBAC 제한, CRD 내장 검증 우선
- [Controlling Access to the Kubernetes API | Kubernetes](https://kubernetes.io/docs/concepts/security/controlling-access/) — 인증 → 인가 → admission 단계, admission이 오브젝트 내용에 접근한다는 점, 읽기 요청 미적용
- [Validating Admission Policy | Kubernetes](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/) — `Kubernetes v1.30 [stable]`, Policy/Binding 구조
- [Mutating Admission Policy | Kubernetes](https://kubernetes.io/docs/reference/access-authn-authz/mutating-admission-policy/) — `Kubernetes v1.36 [stable]` (기본 활성화), CEL + Server-Side Apply / JSON Patch
- [Kubernetes API Concepts — Dry-run](https://kubernetes.io/docs/reference/using-api/api-concepts/#dry-run) — 서버 dry-run이 admission chain을 통과하고 저장 단계만 건너뛴다는 점
- [Kubernetes v1.25: Pod Security Admission Controller in Stable](https://kubernetes.io/blog/2022/08/25/pod-security-admission-stable/) — PSP 제거와 PSA stable 승격
- [Service Accounts | Kubernetes](https://kubernetes.io/docs/concepts/security/service-accounts/) — ServiceAccount 토큰이 projected volume으로 마운트되는 동작
- [Istio — Installing the Sidecar](https://istio.io/latest/docs/setup/additional-setup/sidecar-injection/) — mutating webhook admission controller 기반 자동 주입, `istio-injection=enabled` 라벨, `1/1` → `2/2`
- [cert-manager — CA Injector](https://cert-manager.io/docs/concepts/ca-injector/) — `cert-manager.io/inject-ca-from` 애노테이션으로 `caBundle` 자동 주입
- [Kyverno — Kubernetes Admission Controllers](https://kyverno.io/docs/guides/admission-controllers/) — mutating은 순차·validating은 병렬 호출
- [Kyverno — Installation / Troubleshooting](https://kyverno.io/docs/installation/) — 정책 엔진이 만드는 웹훅 설정, 웹훅 설정 오브젝트는 admission controller에 전달되지 않는다는 점, 교착 복구 절차
- [Kyverno 1.19 발표](https://kyverno.io/blog/2026/08/20/announcing-kyverno-release-1.19/) — `ClusterPolicy`·`Policy` deprecated(v1.20 제거 예정), `verifyImages` → `ImageValidatingPolicy`, 2026-10-24 확인

- [Manifest-Based Admission Control | Kubernetes](https://kubernetes.io/docs/reference/access-authn-authz/manifest-admission-control/) — v1.37 Beta·기본 활성 gate, `staticManifestsDir`, API로 보이지 않는 정적 설정과 설정 보호, 2026-10-24 확인
