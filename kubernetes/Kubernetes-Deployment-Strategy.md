# Kubernetes Deployment Strategy

> **개발자를 위한 쉬운 쿠버네티스 · 23장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-Scheduling.md) · [다음 장](./Kubernetes-Metrics-Server-Prometheus.md)

주문 API v2의 Pod가 모두 Running인데 배포 직후 일부 주문 요청이 실패했다고 하자. Pod를 만드는 일은 끝났지만, 준비되지 않은 앱으로 연결했거나 종료 중인 v1의 연결을 끊었을 수 있다. [Deployment](Kubernetes-ReplicaSet-Deployment.md)의 복제본 유지와 [Service](Kubernetes-Service-Object.md)의 대상 선택, [Readiness](Kubernetes-Probe-Liveness-Readiness-Startup.md)를 함께 보아야 배포 중의 요청을 설명할 수 있다.

## 결론부터 말하면

배포 전략은 새 버전의 실행 인스턴스와 사용자 요청 경로를 어떤 순서로 바꿀지 정하는 방법이다. RollingUpdate는 Pod를 점진적으로 교체하고, Blue/Green은 별도로 준비한 버전으로 진입점을 전환하며, Canary는 일부 요청부터 새 버전에 노출한다.

어느 전략도 설정 이름만으로 무중단이나 데이터 rollback을 보장하지 않는다. 준비 상태의 의미, 임시 capacity, 종료 처리, 버전·DB 호환성, 실패를 판단할 관측과 복구 경로가 함께 있어야 한다.

| 전략 | 주로 바꾸는 것 | 핵심 전제 |
|---|---|---|
| Recreate | 기존 Pod를 내린 뒤 새 Pod 생성 | 중단을 허용할 수 있음 |
| RollingUpdate | 구·신 Pod 수를 점진적으로 조정 | 두 버전 공존과 임시 capacity |
| Blue/Green | 준비한 두 환경 사이의 진입 경로 | 병행 환경과 전환·연결 종료 관리 |
| Canary | 새 버전이 받는 요청의 범위·비율 | 구분 가능한 지표와 트래픽 제어 |

## 1. Running, Ready, 사용자 성공은 다른 단계다

컨테이너 프로세스가 시작되었다고 주문을 처리할 준비가 된 것은 아니다. DB connection pool이나 캐시 준비가 남아 있을 수 있다. readinessProbe는 앱이 요청을 받을 수 있는지 검사하고, 그 결과가 Service endpoint의 준비 상태와 연결된다. 검사 경로가 항상 200만 돌려준다면 Kubernetes가 검사에 성공해도 실제 주문 요청은 실패할 수 있다.

Ready가 된 뒤에도 새 버전의 업무 오류는 남을 수 있다. 특정 주문 유형에서만 결제가 두 번 발생하거나 응답 시간이 나빠지는 문제는 단순 health endpoint로 잡기 어렵다. 그래서 배포 성공에는 controller 상태와 사용자 요청의 지표를 둘 다 보아야 한다.

이 장의 `order-api`, 이미지 `registry.example.com/book/order-api:1.0.0`, `/readyz`, `/livez`, `/startupz` 경로는 관계를 설명하는 가상 앱과 endpoint다. namespace는 `bookstore`, 앱 port는 8080, Service port는 80으로 사용한다. 실제 앱에서 어떤 조건을 검사하고 SIGTERM을 어떻게 처리할지는 별도로 구현해야 한다.

### Recreate도 목적이 있는 전략이다

Recreate는 기존 replica를 종료한 뒤 새 버전을 올린다. 그 사이 처리할 Pod가 없어 중단이 생길 수 있지만, 두 버전의 동시 실행을 피하거나 정해진 maintenance window를 쓰는 업무에는 적합할 수 있다. 운영에서는 무조건 금지하는 전략이 아니라 허용 가능한 중단과 상태 공유 조건으로 선택한다.

단, 교체를 순서대로 한다는 것만으로 외부 writer가 하나임이 보장되지는 않는다. 수동 삭제, 장애 Node의 잔존 프로세스, 외부 consumer까지 고려해야 한다. 이 차이는 [StatefulSet의 fencing](Kubernetes-StatefulSet.md#6-심화-네트워크-단절은-프로세스-종료-증거가-아니다)과 같은 문제다.

## 2. RollingUpdate는 복제본 수와 준비 상태를 조절한다

Deployment의 Pod template을 바꾸면 새 ReplicaSet이 만들어지고 controller가 구·신 ReplicaSet의 개수를 조절한다. Service selector가 앱 label만 선택하면 rollout 중 두 버전의 준비된 Pod가 함께 요청을 받는다. 따라서 API 요청·응답 형식, 세션, DB schema가 공존을 허용해야 한다.

아래는 이 관계를 보여 주는 Deployment와 Service다. 값은 보편적 운영 권장치가 아니라 추가 replica 하나를 수용할 수 있다는 예제의 선택이다.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-api
  namespace: bookstore
spec:
  replicas: 3
  minReadySeconds: 20
  progressDeadlineSeconds: 600
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: order-api
  template:
    metadata:
      labels:
        app: order-api
    spec:
      terminationGracePeriodSeconds: 60
      containers:
      - name: order-api
        image: registry.example.com/book/order-api:1.0.0
        ports:
        - name: http
          containerPort: 8080
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
        startupProbe:
          httpGet:
            path: /startupz
            port: http
          periodSeconds: 5
          failureThreshold: 24
        readinessProbe:
          httpGet:
            path: /readyz
            port: http
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /livez
            port: http
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: order-api
  namespace: bookstore
  labels:
    app: order-api
spec:
  selector:
    app: order-api
  ports:
  - name: http
    port: 80
    targetPort: http
```

`maxUnavailable: 0`은 rollout이 의도적으로 사용 가능한 replica 수를 줄이지 않도록 하고, `maxSurge: 1`은 목표 개수보다 추가 Pod를 만들 여지를 준다. 그러나 이미 실행 중인 Pod의 자연 장애까지 막지는 못한다. 새 Pod가 Pending이 되면 이 설정은 rollout을 기다리게 만들 수 있으므로 추가 Node 자원과 저장소·DB connection 수를 계획해야 한다.

기본 percentage 값은 둘 다 25%이며 surge는 올림, unavailable은 내림한다. replicas가 작으면 이 반올림이 실제 동작을 크게 바꾼다. 둘 다 0으로 설정할 수는 없다. replicas가 1인데 surge 없이 unavailable을 1 허용하면 기존 Pod를 먼저 내려 중단이 생길 수 있다.

또한 replicas+maxSurge는 종료 중인 프로세스까지 포함한 순간 자원 사용량의 절대 상한이 아니다. termination grace 동안 남은 Pod와 새 Pod가 겹칠 수 있다. 숫자만으로 메모리·CPU·외부 connection의 최대치를 계산하면 이 여유를 놓친다.

### minReadySeconds는 Ready를 늦추는 옵션이 아니다

`minReadySeconds: 20`은 새 Pod가 계속 Ready로 유지된 시간을 보고 Deployment의 available replica로 인정하는 기준이다. Service는 그 20초를 기다린 뒤에야 요청을 보내는 것이 아니다. Ready가 된 새 Pod는 그전부터 endpoint로 사용될 수 있다.

따라서 이 값은 잠깐 Ready였다가 다시 실패하는 Pod를 보고 구 replica를 너무 빨리 줄이는 것을 완화할 수 있지만, 워밍업이 끝나기 전 요청을 차단하려면 readiness의 의미를 바르게 구현해야 한다. 언어가 Java인지 Node.js인지 하나만으로 대기 시간을 결정하지 않고 실제 startup·부하 특성을 측정한다.

### progress deadline은 자동 rollback이 아니다

`progressDeadlineSeconds`는 rollout 진전이 없는 상태를 보고하는 기준이다. deadline을 넘으면 Deployment는 `Progressing=False`, `ProgressDeadlineExceeded` 같은 상태를 기록할 수 있지만 이전 버전으로 스스로 복원하지 않는다. CI에서 `rollout status`의 실패를 읽고 어떤 조치를 취할지 별도로 결정해야 한다. [Deployment 공식 문서](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)가 controller의 이 경계를 설명한다.

```bash
kubectl rollout status deployment/order-api -n bookstore --timeout=300s
kubectl get deployment order-api -n bookstore -o yaml
kubectl get rs,pods -n bookstore -l app=order-api
```

이 결과가 정상이어도 주문 성공률 검증은 남아 있다. 반대로 timeout이 났다고 즉시 같은 rollback 스크립트를 반복하면 현재 진행 중인 rollout과 경쟁할 수 있다. 실패 이유와 현재 revision을 읽고 배포 시스템의 소유권에 맞춰 처리한다.

## 3. 종료 중인 앱의 요청은 누가 마무리하는가

새 Pod가 준비되는 것만큼 구 Pod의 종료도 중요하다. Pod 삭제가 시작되면 endpoint 상태 갱신과 kubelet의 컨테이너 종료 처리는 비동기적으로 진행된다. 어느 한 단계가 모든 proxy와 외부 LB 갱신을 완료한 뒤 다음 단계가 시작되는 단일 transaction은 아니다.

앱은 SIGTERM을 받으면 새 요청의 수락을 조절하고 진행 중 요청과 background 작업을 마무리해야 한다. 서버 framework의 graceful shutdown 설정과 keepalive·WebSocket·gRPC 연결의 수명도 영향을 준다. `terminationGracePeriodSeconds` 안에 끝나지 않으면 강제 종료될 수 있다.

`preStop`을 사용한다면 그 실행 시간도 같은 grace period에 포함된다. 일정 시간 sleep은 전파 지연의 여유를 줄 수 있지만 모든 네트워크 경로가 정리되었다는 신호는 아니다. 앱 종료 시간·LB deregistration/drain·재시도 정책을 실제 경로에서 확인해야 한다. 재시도는 Job에서 배운 멱등성 문제를 HTTP 요청에도 다시 가져온다.

## 4. Blue/Green은 교체와 진입점 전환을 분리한다

Blue/Green은 현재 버전 Blue와 새 버전 Green을 별도 workload로 준비하고 검증한 뒤 사용자 진입점을 Green으로 바꾸는 방법이다. 새 환경 준비를 사용자 트래픽 전환과 분리할 수 있고, 이전 환경을 유지하면 경로를 되돌릴 선택지도 남는다. 그 대신 두 환경의 capacity와 외부 부작용을 함께 관리해야 한다.

주문 API의 두 Deployment를 `order-api-blue`, `order-api-green`으로 따로 만든다고 가정한다. 두 template은 `app: order-api` 외에 각각 `track: blue`, `track: green`을 가지며, 각 Deployment selector도 자기 track을 포함해야 한다. 공통 Service는 다음처럼 한쪽만 선택한다. 전체 Deployment YAML은 앞의 구조를 반복하지 않는다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-api
  namespace: bookstore
spec:
  selector:
    app: order-api
    track: blue
  ports:
  - name: http
    port: 80
    targetPort: 8080
```

Green 검증에는 별도의 preview Service나 제한된 진입 경로를 사용할 수 있다. 전환은 selector의 track을 바꾸는 형태로 표현한다.

```bash
kubectl patch service order-api -n bookstore \
  -p '{"spec":{"selector":{"track":"green"}}}'
```

이 patch의 성공은 API에 새 selector가 기록되었다는 뜻이다. EndpointSlice controller와 dataplane의 반영은 비동기이며 기존 연결이 모두 끊기는 것도 아니다. keepalive/WebSocket 연결은 이전 버전에서 계속 처리될 수 있다. 따라서 전환 중 두 버전이 사용자 트래픽을 동시에 받을 수 있고 한 사용자가 반드시 한 버전만 보게 된다는 보장도 없다.

구버전으로 selector를 돌리는 것은 새 Pod를 다시 만드는 것보다 빠른 복구 선택지가 될 수 있지만, 즉시·원자적 rollback은 아니다. 구버전을 이미 scale-to-zero했다면 다시 시작할 시간도 필요하다. 유지 시간은 임의의 몇 시간보다 장애 탐지 시간, 연결 수명, 비용과 복구 목표에 맞춘다.

### Service 밖의 일은 selector를 따르지 않는다

두 버전의 메시지 consumer나 scheduler는 Service를 거치지 않고 큐와 DB에 접근할 수 있다. Green을 preview 상태로 띄워도 이미 주문 알림을 보내거나 배치 작업을 실행할 수 있다. 진입 HTTP 요청만 분리했다고 업무 실행까지 분리되는 것은 아니다.

필요한 경우 consumer group·lease/leader election·fencing·기능 플래그 등 별도 제어가 필요하다. DB schema도 expand/contract 방식처럼 신·구 버전이 함께 읽고 쓸 수 있게 단계적으로 바꾼다. 앱 이미지를 되돌린다고 삭제한 컬럼이나 이미 발송한 알림이 복구되지는 않는다.

## 5. Canary는 적은 노출에서 배울 수 있어야 의미가 있다

Canary는 일부 요청을 새 버전에 보내고 관찰한 뒤 범위를 늘린다. Pod 수를 9:1로 두고 같은 Service가 모두 선택하게 하는 간단한 접근도 가능하지만, 그 비율이 HTTP 요청의 90:10을 보장하지는 않는다. 연결 재사용, session affinity, topology, 각 Pod의 처리 속도에 따라 분포가 달라진다.

정교하게 요청 비율을 조절하려면 Gateway/Ingress/service mesh 등 실제 요청을 분배하는 계층이 필요하다. Canary의 목표는 Pod 수 자체가 아니라 새 버전이 처리한 요청과 실패를 구별해 판단하는 것이다. 전체 성공률만 보면 작은 Canary의 오류가 큰 stable 트래픽에 가려질 수 있다.

### HTTPRoute로 의도를 표현한다

다음은 Gateway API CRD와 가중치 분배를 지원하는 controller가 있고, `prod-gateway` listener가 이 Route를 허용하는 경우다. stable/canary Service는 각각 다른 버전만 선택하고 Service port 80을 앱 8080으로 연결한다고 가정한다. Gateway와 Service 전체 생성 예제는 [Gateway API 장](Kubernetes-Gateway-API.md)에서 이어 읽는다.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: order-api-canary
  namespace: bookstore
spec:
  parentRefs:
  - name: prod-gateway
  hostnames:
  - orders.example.com
  rules:
  - matches:
    - headers:
      - name: X-Canary
        value: "true"
    backendRefs:
    - name: order-api-canary
      port: 80
  - backendRefs:
    - name: order-api-stable
      port: 80
      weight: 90
    - name: order-api-canary
      port: 80
      weight: 10
```

`weight`는 퍼센트 그 자체가 아니라 같은 backend 목록 안에서의 상대 비율이다. 3과 1은 75:25이며, 생략한 weight는 1이다. 더 구체적인 헤더 rule에 해당하는 요청은 Canary로 가고, 나머지는 fallback rule의 가중치 분배를 받는다. 유한한 수의 관찰에서 정확히 10%가 나온다는 뜻은 아니다.

fallback만 100:0으로 바꾸면 `X-Canary: true` 요청은 여전히 Canary로 간다. 모든 이 Route의 새 요청을 stable로 되돌리려면 헤더 rule까지 바꿔야 한다. 다음은 위 두 rule을 모두 stable 하나로 교체하는 JSON Patch다. 기존 연결과 다른 Route는 여전히 별도의 범위다.

```bash
kubectl patch httproute order-api-canary -n bookstore --type=json \
  -p '[{"op":"replace","path":"/spec/rules","value":[{"backendRefs":[{"name":"order-api-stable","port":80}]}]}]'
```

### 기존 ingress-nginx 설정을 읽을 때

2026-10-23 기준 커뮤니티 ingress-nginx는 2026년 3월 은퇴했으며 이후 보안·버그 수정 릴리스가 제공되지 않는다. 기존 시스템의 `nginx.ingress.kubernetes.io/canary`, `canary-weight`, `canary-by-header`, `canary-by-cookie`는 그 controller의 확장 문법이다. Ingress 표준 자체가 이 annotation을 실행하는 것은 아니다. 제품명이 비슷한 다른 NGINX controller와도 구분한다.

이 문법은 기존 경로를 이해하는 데 필요하지만 신규 예제의 전제로 삼지 않는다. Gateway API로 옮길 때는 가중치뿐 아니라 헤더·쿠키·우선순위·인증 등 기존 의미의 대응과 구현체 지원을 확인한다. 변환 도구가 파일을 생성했다고 실제 트래픽 전환이 끝난 것은 아니다. [공식 은퇴 공지](https://kubernetes.io/blog/2026/01/29/ingress-nginx-statement/)와 [HTTP traffic splitting](https://gateway-api.sigs.k8s.io/guides/traffic-splitting/)이 이 판단의 근거다.

## 6. rollback은 어떤 상태를 복원하는가

Deployment는 이전 Pod template의 revision을 ReplicaSet 이력으로 유지한다. `rollout undo`는 이전 template을 다시 적용하여 rollout을 진행한다. 이미지 값을 이전 값으로 바꾸어 apply하는 것과 모두 Pod 교체를 유발할 수 있으므로, undo 자체가 본질적으로 즉시 복구하는 별도 실행 엔진은 아니다.

```bash
kubectl rollout history deployment/order-api -n bookstore
kubectl rollout history deployment/order-api -n bookstore --revision=2
# 아래 명령은 상태를 변경하는 복구 예시다.
kubectl rollout undo deployment/order-api -n bookstore --to-revision=2
```

이력이 정리되었으면 해당 revision으로 돌아갈 수 없다. `revisionHistoryLimit`과 이미지 digest·배포 기록을 함께 관리해야 한다. `kubernetes.io/change-cause` annotation은 변경 의도를 설명하는 데 쓸 수 있지만 감사 시스템이나 불변 배포 식별자를 대신하지 않는다. 오래된 `--record` 옵션에 의존할 필요도 없다.

GitOps 환경에서는 Git과 live state의 소유권도 본다. Argo CD의 자동 sync/self-heal 정책에 따라 수동 undo가 이후 Git 상태로 다시 바뀔 수 있다. Git revert와 동기화가 정본을 복원하는 경로라면 그 절차를 사용한다. GitOps 도구 전체에 rollback 기능이 없다고 묶을 수도 없다. Flux HelmRelease의 remediation처럼 설정된 실패 복구 기능이 따로 존재한다.

무엇을 사용하든 Pod template이나 트래픽 경로 복원과 DB migration·외부 side effect의 복원은 다르다. rollback을 계획할 때는 이전 앱이 현재 데이터와 함께 동작하는지, 이미 실행한 업무를 어떻게 다룰지까지 확인한다.

## 7. PDB는 rollout의 예산이 아니다

PodDisruptionBudget은 Eviction API를 사용하는 자발적 중단을 제한하는 장치다. Node drain이나 지원 autoscaler의 Node 축소 때, 준비된 replica가 너무 많이 한꺼번에 사라지지 않도록 돕는다. Deployment controller의 rollout을 제한하는 스위치는 아니다.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: order-api
  namespace: bookstore
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: order-api
```

replicas가 3이고 healthy가 3이면 한 Pod의 eviction을 허용할 수 있지만 이미 하나가 unavailable이면 drain이 기다릴 수 있다. 준비된 replica가 늘지 못하는 상황에서 minAvailable을 replicas와 같게 잡으면 Node maintenance가 막힐 수 있다. 반대로 설정을 낮추기만 하면 허용한 만큼 업무 용량이 줄어드는 위험이 있다.

rollout의 replica 교체는 maxUnavailable/maxSurge와 readiness로 조절한다. 직접 Pod delete, `drain --disable-eviction`처럼 eviction을 우회하는 작업, Node 자연 장애는 PDB로 막지 못한다. 이미 발생한 자연 장애가 예산을 소비해 추가 eviction이 거절될 수는 있지만, PDB가 그 장애를 예방한 것은 아니다. [Disruptions 공식 문서](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)는 이 범위를 구분한다.

## 8. 심화: Kubernetes Ready와 외부 LB의 건강 상태

클라우드 LB가 Pod IP를 직접 target으로 쓰면, kubelet probe 성공과 LB target 등록·health check 완료 사이에 차이가 생긴다. Kubernetes가 새 Pod를 available로 보고 구 Pod를 줄였는데 외부 LB는 아직 새 target을 사용할 준비가 안 되었을 수 있다. Service 상태만으로 외부 경로까지 동기화되었다고 판단할 수 없는 이유다.

AWS ALB의 신규 등록 target은 health check 한 번 성공하면 healthy가 될 수 있다. 이미 unhealthy인 target이 회복할 때 필요한 연속 성공 threshold와는 다르다. 또한 ALB는 모든 등록 target이 unhealthy인 경우 fail-open으로 unhealthy target에도 보낼 수 있으므로, unhealthy이면 요청을 절대 받지 않는다는 전제를 세워서는 안 된다.

AWS Load Balancer Controller의 Pod readiness gate는 target의 health 상태를 Pod readiness에 포함하도록 돕는다. 그러나 namespace의 injection label 하나로 모든 Pod에 자동 적용되는 것은 아니다. Pod 생성 전에 matching Service와 TargetGroupBinding, IP target 조건, 정상 webhook 등 문서의 전제가 충족되어야 한다. 이미 만들어진 Pod에 label만 붙여 소급 주입되는 것도 아니다.

readiness gate condition과 target health를 실제로 확인해야 하며, healthcheck path·interval·threshold는 앱의 endpoint와 맞춰야 한다. `minReadySeconds: 30` 같은 시간 여유는 LB 상태와의 인과적 동기화가 아니다. 30초 안에 LB가 반드시 준비된다는 보장은 없으므로 gate를 대신하는 증거로 삼지 않는다.

이 문제는 ALB에만 있는 개념이 아니다. 어떤 외부 경로든 등록, health 판단, connection drain의 주체와 시간이 Kubernetes 안의 상태와 일치하는지 확인해야 한다.

## 9. 심화: 관측을 다음 단계의 조건으로 연결한다

Argo Rollouts는 Rollout CRD/controller로 단계, pause, 분석과 중단을 관리한다. Argo CD가 Git 상태를 동기화하는 역할과 다르다. `setWeight`만 적었다고 정확한 HTTP 비율이 제어되는 것은 아니다. trafficRouting 연동이 없으면 replica 수를 이용한 best effort이고, 해당 라우터/서비스 메시의 연동을 구성해야 요청 경로를 조절할 수 있다.

분석에는 끝나는 조건이 있어야 한다. 다음은 이미 설치된 Argo Rollouts가 사용하며, Canary만 나타내는 `app`·`track` label이 Prometheus 요청 지표에 실제로 기록된다는 가정의 독립 예제다. 해당 query와 endpoint는 가상이며 완전한 Rollout 설치 파일은 아니다.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: order-canary-success
  namespace: bookstore
spec:
  metrics:
  - name: success-rate
    interval: 1m
    count: 5
    failureLimit: 0
    successCondition: len(result) == 1 && !isNaN(result[0]) && result[0] >= 0.99
    failureCondition: len(result) == 0 || isNaN(result[0]) || result[0] < 0.99
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc:9090
        query: |
          sum(rate(http_requests_total{app="order-api",track="canary",status!~"5.."}[5m]))
          /
          sum(rate(http_requests_total{app="order-api",track="canary"}[5m]))
```

이 예의 정책은 1분 간격 다섯 번의 측정을 요구하고, 허용 실패는 0으로 잡는다. 빈 결과나 NaN도 안전하게 통과시키지 않겠다는 의도다. 5xx 외의 업무 실패를 성공으로 계산해도 되는지, 최소 요청 수가 충분한지는 실제 서비스 기준으로 보강해야 한다. HTTP 오류가 없더라도 주문 중복이나 결제 실패를 놓칠 수 있다.

provider 조회 오류는 측정 실패와 별개 Error 경로이므로 설치 버전의 error limit·inconclusive 정책과 운영자의 개입 절차도 확인한다. `count: 0`의 무기한 background 분석과 inline 분석의 의미도 다르다. 설치한 버전에서 지원 필드와 종료 조건을 검증하고, 분석 실패로 abort한 뒤 stable/canary replica와 트래픽이 실제로 어떻게 정리되는지도 관찰해야 한다.

배포 경보에는 kube-state-metrics의 Deployment condition을 사용할 수 있지만, 이는 controller 상태 경보다. 요청 성공률·지연·업무 결과 경보와 함께 보아야 한다. 실패하면 자동 undo하는 짧은 CI 스크립트만으로 모든 복구를 해결하려 하기보다, 어떤 증거가 promotion을 허용하고 어떤 실패가 정지·rollback·사람의 판단을 요구하는지 정한다.

## 생각해 볼 질문

### 1. maxUnavailable을 0으로 하면 왜 배포 중 요청이 실패할 수 있는가?

숫자는 controller가 교체하는 replica의 가용 기준을 제어한다. readiness가 실제 준비를 나타내지 않거나 외부 LB가 늦게 반영되거나 기존 연결이 강제 종료되면 사용자 요청은 실패할 수 있다. 앱·네트워크·종료 경로의 증거가 추가로 필요하다.

### 2. Blue/Green selector를 되돌리면 DB 변경도 되돌아가는가?

selector는 새 연결의 대상만 바꾼다. 기존 연결과 consumer 작업, DB schema와 이미 발생한 외부 효과는 남을 수 있다. 구버전이 현재 데이터와 호환되어야 하며 필요한 데이터 복구는 별도로 설계한다.

### 3. Canary 오류율을 전체 order-api 성공률로 평가하면 어떤 문제가 생기는가?

대부분의 stable 요청이 소수 Canary의 오류를 가릴 수 있다. 새 버전만 구별하는 label과 충분한 표본, NoData·조회 오류의 정책이 있어야 노출 확대의 근거가 된다.

## 다음 장으로

배포 전략은 결국 관찰한 상태를 근거로 다음 변경을 선택하는 과정이다. 다음 [Metrics Server와 Prometheus](Kubernetes-Metrics-Server-Prometheus.md)에서 현재 사용량, 과거 시계열, object 상태와 사용자 요청 지표의 출처를 구분하고 자동 확장에 어떻게 연결하는지 살펴본다.

## 출처

- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) — rollout, 가용 기준과 progress deadline
- [Pod lifecycle: termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) — 종료와 endpoint 처리
- [Kubernetes Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) — PDB와 eviction 경계
- [Gateway API traffic splitting](https://gateway-api.sigs.k8s.io/guides/traffic-splitting/) — 상대 가중치
- [HTTPRoute API](https://gateway-api.sigs.k8s.io/reference/api-types/httproute/) — route match와 backend
- [ingress-nginx statement, 2026-01-29](https://kubernetes.io/blog/2026/01/29/ingress-nginx-statement/) — 2026년 3월 은퇴와 지원 종료
- [Argo Rollouts Canary](https://argoproj.github.io/argo-rollouts/features/canary/) — traffic routing 없는 weight의 한계
- [Argo Rollouts Analysis](https://argoproj.github.io/argo-rollouts/features/analysis/) — count, 실패·오류와 분석 종료
- [Argo CD automated sync](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) — self-heal과 동기화 정책
- [Flux HelmRelease remediation](https://fluxcd.io/flux/components/helm/helmreleases/#upgrade-remediation) — Helm upgrade 복구 정책
- [ALB health checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html) — initial health와 fail-open
- [AWS Load Balancer Controller readiness gate](https://kubernetes-sigs.github.io/aws-load-balancer-controller/latest/deploy/pod_readiness_gate/) — 주입 조건과 대상 health
- [BlueGreenDeployment](https://martinfowler.com/bliki/BlueGreenDeployment.html) — 두 환경을 준비하는 설계
- [CanaryRelease](https://martinfowler.com/bliki/CanaryRelease.html) — 제한된 노출에서의 관찰
