# Kubernetes Scheduling

> **개발자를 위한 쉬운 쿠버네티스 · 22장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-Resource-Management.md) · [다음 장](./Kubernetes-Deployment-Strategy.md)

노드를 지정하면 실행이 보장될까? toleration이 있으면 전용 노드로 갈까?

[Pod](Kubernetes-Pod.md)와 [자원 관리](Kubernetes-Resource-Management.md)를 먼저 읽으면 이 장의 requests·allocatable이 익숙할 것이다. 앱을 세 개 실행한다고 선언해도 세 개가 서로 다른 노드나 가용 영역에 놓인다는 뜻은 아니다. 노드 용량뿐 아니라 데이터 위치·하드웨어·장애 범위까지 생각하면 실행 위치를 정하는 조건이 필요하다.

## 결론부터 말하면

scheduler는 새 Pod를 수용할 수 없는 노드를 먼저 제외하고, 남은 후보에 점수를 매겨 실행 위치를 선택한다. 필수 조건은 후보를 줄이고 선호 조건은 후보 사이의 선택을 돕는다. 조건이 충족되어 노드가 정해져도 이미지·volume·앱 준비가 성공했다는 뜻은 아니다.

| 바꾸고 싶은 것 | 선언 수단 | 보장하지 않는 것 |
|---|---|---|
| 특정 노드 특성만 허용 | `nodeSelector`, required node affinity | 자원·volume·앱 실행 성공 |
| 가능하면 특정 특성 선호 | preferred node affinity | 선호 노드로의 확정 배치 |
| 다른 Pod와 가까이/멀리 | Pod affinity·anti-affinity | 지속적 재배치와 종단 가용성 |
| 노드의 배치 제한을 허용 | toleration | 해당 노드로 유도·독점 |
| 노드·zone 사이 분포 제어 | topology spread constraints | 장애 시 자동 재균형·요청 성공 |

이 장의 YAML은 `bookstore`의 가상 `order-api` Pod 또는 Deployment Pod 템플릿에 넣는 구조 설명이다. `registry.example.com` 이미지가 공개 이미지라는 뜻이 아니며, 노드 라벨·zone·taint는 환경에 맞게 준비되어야 한다. 아래 명령은 실행 기록이 아니다. `example-node`·`example-gpu-node`는 실제 대상 노드 이름으로 바꿀 자리표시자다.

## 1. 왜 빈 노드가 있는데 배치하지 못할까?

CPU가 남아 있는 노드에도 앱이 요구한 volume을 연결할 수 없거나, 허용한 zone 라벨이 없을 수 있다. scheduler는 모든 자원을 합쳐 하나의 큰 서버처럼 사용하지 않는다. Pod가 실행될 **한 노드** 가 그 Pod의 필수 조건을 만족해야 한다.

기본 kube-scheduler의 판단을 두 단계로 단순화하면 **filter** 는 조건을 만족하지 않는 노드를 후보에서 빼는 단계이고, **score** 는 남은 후보를 평가하는 단계다. requests·노드 상태·taint·affinity·volume 등 여러 요소가 함께 작용한다. 한 조건을 만족했다고 다른 조건이 면제되지 않으며 후보가 없으면 점수를 높일 노드도 없다.

선택 뒤에는 Pod의 노드 연결이 기록되고 그 노드 kubelet이 컨테이너 준비를 진행한다. 그러므로 scheduler가 배치한 Pod에도 image pull이나 mount 실패가 생긴다. Pod는 한 번 배치된 뒤 노드 사이를 이동하지 않으며, 교체가 필요하면 새 Pod를 배치하는 흐름이다.

## 2. 노드의 특성을 선택하기

### 2.1 nodeSelector: 라벨이 정확히 맞는 노드

노드 label은 하드웨어·노드 풀·zone 같은 특성을 key·value로 표현한다. `nodeSelector`는 지정한 key·value를 모두 가진 노드만 허용한다. 다음은 `spec` 아래 발췌로, 라벨을 조직에서 관리한다는 전제다.

```yaml
nodeSelector:
  example.com/node-pool: general
```

원래 GPU 예제의 `accelerator: nvidia-tesla-v100` 같은 라벨도 이 선택 원리는 같다. 다만 라벨 선택은 GPU 자원 요청이 아니다. 실제 GPU 사용에는 driver·device plugin·`nvidia.com/gpu` 같은 확장 자원의 request·limit과 실행 이미지 호환성도 필요하며 [GPU Device Plugin](Kubernetes-GPU-Device-Plugin.md)에서 이어진다.

라벨 추가는 다음처럼 표현하지만 노드의 속성을 바꾸는 관리 작업이다. 여기서는 실행하지 않았다. 임의 라벨이 그 하드웨어나 보안 격리를 실제로 만든다고 생각하지 않는다.

```bash
kubectl label node example-node example.com/node-pool=general
```

### 2.2 Node affinity: 필수와 선호를 나누기

**Node affinity** 는 노드 라벨에 대한 더 풍부한 조건식이다. 아래 발췌는 두 zone 중 하나를 필수로 요구하고, 그 안에서 `high-memory` 노드를 선호한다. zone 문자열은 설명용이며 노드에 실제로 있어야 한다.

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: topology.kubernetes.io/zone
          operator: In
          values: [ap-northeast-2a, ap-northeast-2b]
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      preference:
        matchExpressions:
        - key: node-type
          operator: In
          values: [high-memory]
```

`requiredDuringScheduling...`는 filter에 해당하는 필수 조건이다. `preferredDuringScheduling...`의 weight는 score에 기여하지만 다른 평가도 있으므로 가장 큰 weight를 적어도 그 노드로의 배치가 보장되지 않는다. `IgnoredDuringExecution`은 배치 후 라벨이 바뀌어 조건이 깨져도 이 affinity 규칙 자체가 기존 Pod를 내보내지는 않는다는 뜻이다.

`nodeSelectorTerms` 여러 항목은 OR, 한 항목의 여러 `matchExpressions`는 AND 관계다. `nodeSelector`와 node affinity를 함께 쓰면 둘 다 만족해야 한다. `In`·`NotIn`은 값 목록, `Exists`·`DoesNotExist`는 key 존재 여부를 판단한다. `Gt`·`Lt`는 node affinity에서 숫자 비교에 쓰며 문자열을 숫자로 해석할 수 있어야 한다. 조건을 늘릴수록 후보가 줄어든다는 점을 기억한다.

## 3. 다른 Pod와의 관계로 위치 정하기

### 3.1 Pod affinity와 topologyKey

앱이 캐시와 같은 노드에 있으면 통신 경로를 줄일 수 있지만, 이를 필수로 만들면 캐시 Pod가 없는 노드에는 앱도 배치하지 못한다. **Pod affinity** 는 노드 라벨 대신 다른 Pod의 label과 그 Pod가 놓인 topology 영역을 기준으로 삼는다.

```yaml
affinity:
  podAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app: redis
      topologyKey: kubernetes.io/hostname
```

이 발췌는 기본 namespace 범위에서 `app: redis` Pod와 같은 hostname 영역을 요구한다. Redis의 Ready나 연결 성공을 검증하는 규칙은 아니다. 다른 namespace까지 선택하려면 namespaces·namespaceSelector의 의미와 권한 경계를 따로 확인한다.

`topologyKey`는 같은 곳·다른 곳의 경계를 정하는 노드 label key다. `kubernetes.io/hostname`이면 노드, `topology.kubernetes.io/zone`이면 zone, `topology.kubernetes.io/region`이면 region 경계다. 클러스터의 노드들이 해당 라벨을 일관되게 가져야 의도한 비교가 된다.

### 3.2 Pod anti-affinity: 같은 장애 범위 피하기

반대로 동일 앱을 한 노드에 모으고 싶지 않다면 anti-affinity를 사용한다. 다음은 `app: order-api` Pod끼리 같은 hostname에 배치하지 않는 필수 조건의 발췌다. 새 Pod 자신과 기존 Pod에 해당 label이 있어야 한다.

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app: order-api
      topologyKey: kubernetes.io/hostname
```

조건에 맞는 노드가 두 개뿐이면 세 번째 replica는 Pending일 수 있다. RollingUpdate에서 기존 Pod를 남긴 채 surge Pod를 만들 때도 새 자리가 필요하다. 가용성을 높이기 위한 필수 분산 조건이 배포 진행을 막을 수 있으므로 replica 수·노드 수·업데이트 전략을 함께 계산한다.

zone을 경계로 삼는 anti-affinity도 표현할 수 있지만 `LimitPodHardAntiAffinityTopology` admission plugin이 활성화된 환경에서는 required anti-affinity의 topologyKey를 hostname으로 제한한다. 이 plugin은 upstream 기본값으로 비활성화되어 있으므로 모든 클러스터에 같은 제한이 있다고 가정하지 않는다. zone 분산이 목적이면 topology spread도 검토하고, API에서 정책상 허용하는지 확인한다. affinity는 앱 준비와 지속적인 재균형을 대신하지 않는다.

## 4. Taint와 toleration은 노드의 제한을 다룬다

affinity가 Pod 쪽의 선택 조건이라면 **taint** 는 노드 쪽에 두는 배치·유지 제한이다. **toleration** 은 Pod가 그 taint를 허용함을 선언한다. GPU·Spot·control plane 같은 노드에 일반 앱이 무심코 들어오는 것을 제한할 때 사용한다.

다음은 관리자가 특정 노드에 조직 정의 taint를 추가하는 명령 형식과 이를 허용하는 Pod spec 발췌다. 클라우드나 device plugin이 같은 taint를 자동으로 붙인다는 뜻은 아니다.

```bash
kubectl taint node example-gpu-node example.com/dedicated-gpu=true:NoSchedule
```

```yaml
tolerations:
- key: example.com/dedicated-gpu
  operator: Equal
  value: "true"
  effect: NoSchedule
```

이 Pod는 해당 제한을 통과할 수 있지만 GPU 노드로 보내 달라는 요구는 하지 않았다. 전용 노드로 한정하려면 label과 node affinity/selector를 함께 쓰고, 실제 자원 request도 맞춰야 한다. 한 toleration이 여러 개의 다른 taint까지 모두 허용하는 것도 아니다.

| Effect | 일치하는 toleration이 없을 때 |
|---|---|
| `NoSchedule` | 새 배치를 제한하며 기존 Pod를 그 이유만으로 퇴거하지 않음 |
| `PreferNoSchedule` | 새 배치를 가능하면 피하는 선호 수준의 제한 |
| `NoExecute` | 새 배치 제한과 기존 Pod 퇴거에 영향을 줌 |

`NoExecute`의 toleration에 `tolerationSeconds`를 넣으면 허용 기간 뒤 퇴거될 수 있다. 지정하지 않은 일치 toleration은 그 taint를 계속 허용한다. 노드 장애 관련 taint는 자동으로 생길 수 있고 controller가 붙이는 기본 toleration도 있으므로 작성한 YAML만으로 퇴거 시각을 단정하지 않는다. toleration은 노드 장애 중 서비스가 계속 응답한다는 보장도 아니다.

조직 예시로 `example.com/spot=true:NoSchedule`을 쓸 수 있고, control plane에는 `node-role.kubernetes.io/control-plane:NoSchedule`이 흔히 쓰인다. 실제 key·value·effect와 노드 운영 정책을 확인한다.

## 5. Topology spread: replica 수의 차이 제어하기

노드마다 한 개만 허용하는 anti-affinity보다 여러 zone 사이의 개수 차이를 제어하고 싶을 수 있다. **Topology spread constraints** 는 선택한 label의 Pod 수가 topology 영역마다 얼마나 차이 날 수 있는지 선언한다. 다음은 Pod spec의 발췌이며 Pod template의 label도 `app: order-api`여야 한다.

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: DoNotSchedule
  labelSelector:
    matchLabels:
      app: order-api
```

여기서 `maxSkew: 1`은 eligible domain 사이의 분포 차이를 계산하는 상한이다. 단순한 환경에서는 zone별 Pod 수 차이를 1 이내로 유지하는 규칙으로 이해할 수 있지만, 실제 계산에는 eligible domain·minDomains·노드 affinity/taint를 계산에 포함하는 정책이 관여한다. 사용 중인 API 지원과 공식 계산 규칙을 확인한다.

`DoNotSchedule`은 분포 조건을 만족하지 못하면 새 배치를 막고, `ScheduleAnyway`는 더 고르게 놓는 쪽을 선호한다. 후자는 필수 자원·affinity 조건까지 무시하고 실행시키는 옵션이 아니다. 여러 `DoNotSchedule` 제약은 모두 만족해야 하며 `ScheduleAnyway`는 skew를 줄이는 선호에 반영된다. 모든 대상 노드의 topology label, selector와 Pod label의 일치, zone별 실제 용량을 함께 본다.

이 규칙은 새 Pod를 배치할 때의 판단이다. scale down·장애로 분포가 깨졌다고 기존 Pod를 자동으로 옮겨 균형을 되돌리는 기능은 아니다. zone이 여러 개라는 사실도 DB·스토리지·외부 경로의 장애 독립성을 보장하지 않으므로 앱 전체 가용성으로 확장해 판단한다.

## 6. Pending에서 조치까지: 실패한 단계를 먼저 찾는다

다음 명령은 준비된 개인 실습 context에서의 읽기 전용 관찰 예다.

```bash
kubectl -n bookstore get pod order-api-pod -o wide
kubectl -n bookstore get pod order-api-pod -o jsonpath='{.spec.nodeName}{"\n"}'
kubectl -n bookstore describe pod order-api-pod
kubectl get nodes --show-labels
kubectl describe node example-node
```

먼저 `.spec.nodeName`이 비어 있는지 본다. 비어 있고 Events에 `FailedScheduling`이 있으면 노드별 제외 이유를 확인한다. scheduler를 우회한 특수 설정은 별도로 구분한다. 노드가 정해졌는데 Pending이면 scheduler 조건보다 이미지·Secret·volume mount 같은 준비 단계를 먼저 본다.

| 관찰 | 확인할 증거 | 피할 성급한 조치 |
|---|---|---|
| `Insufficient cpu`·`memory` | allocatable과 이미 배정한 유효 requests | 사용량이 낮다는 이유로 request를 임의 축소 |
| affinity/selector 불일치 | Pod의 필수 식·실제 노드 라벨 | 라벨만 붙여 하드웨어·보안 조건 충족으로 간주 |
| untolerated taint | 노드의 모든 taint와 일치 toleration | 모든 앱에 광범위 `Exists` 허용 추가 |
| topology spread 불충족 | selector·영역별 수·노드 라벨·용량 | 분포 정책의 목적 확인 없이 필수 조건 해제 |
| volume node affinity 충돌 | PVC·PV의 zone·노드 조건 | CPU만 늘려 해결 시도 |
| 노드 배치 뒤 `FailedMount`·pull 오류 | driver·provider·registry Events | scheduler 조건만 계속 변경 |

Events는 여러 노드의 서로 다른 실패 원인을 요약할 수 있다. 하나를 고쳤는데 다른 조건 때문에 여전히 Pending일 수도 있다. Preemption이 언급되어도 낮은 Priority Pod를 제거하면 모든 affinity·volume 제약이 해결된다는 의미는 아니다. 노드 증설 역시 필요한 label·zone·taint·storage 접근을 갖춘 용량이어야 도움이 된다.

**에어갭 환경에서 짚어볼 점:** 스케줄링 통과는 그 노드에서 이미지를 가져오거나 CSI provider가 비밀 저장소에 연결할 수 있다는 증거가 아니다. 사내 registry의 이미지·인증·CA와 노드별 driver·통신 경로를 배치 뒤 단계에서 따로 관찰한다.

## 7. 정리

먼저 필수 조건으로 후보가 존재하는지 확인하고 그다음 선호와 분포를 읽는다. toleration은 제한을 허용하고 affinity는 위치를 선택한다. 조건을 강하게 만들 때는 정상 replica뿐 아니라 업데이트·장애 중의 여유 자리까지 계산해야 한다. 배치 완료 뒤에는 kubelet과 앱의 준비를 이어서 확인한다.

실행 위치를 정했으니 다음 [배포 전략](Kubernetes-Deployment-Strategy.md)에서는 요청을 처리 중인 앱을 새 버전으로 교체할 때 준비 상태와 사용자 트래픽을 어떻게 확인하는지 연결한다.

## 생각해 볼 질문

1. **GPU taint의 toleration을 넣었는데 왜 일반 노드로 갔을까?**
   해설: toleration은 GPU 노드의 제한을 허용할 뿐 그쪽을 선택하지 않는다. 필요하면 node selector/affinity와 실제 GPU request를 함께 지정한다.
2. **노드 두 개에 replica 두 개가 정상인데 required anti-affinity로 업데이트가 멈출 수 있을까?**
   해설: surge Pod에도 별도의 허용 노드가 필요할 수 있다. 기존 Pod와 새 Pod가 같은 selector에 걸리는지, 배포 전략이 여유 자리를 요구하는지 확인한다.
3. **Topology spread를 넣으면 zone 장애 뒤 기존 Pod도 자동 이동할까?**
   해설: 새 Pod의 배치 규칙이다. 기존 Pod를 옮기는 기능이 아니며 대체 생성·eligible domain·남은 zone 용량과 다른 조건을 별도로 확인한다.

## 출처

2026-10-23 기준 공식 개념·조건을 확인했다. YAML은 정적 확인 대상이며 실제 scheduler 이벤트·분산·장애 복구를 실행 검증하지 않았다.

- [Kubernetes Scheduler](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/) — filter·score와 노드 선택
- [Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) — selector·affinity·연산자·admission 제한
- [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) — effect·허용 기간·자동 taint
- [Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/) — skew·eligible domain·제한사항
- [Resource Management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) — requests 기반 용량 판단
- [Volume Scheduling](https://kubernetes.io/docs/concepts/storage/storage-classes/#volume-binding-mode) — volume과 topology 제약
- [Admission Controllers — LimitPodHardAntiAffinityTopology](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#limitpodhardantiaffinitytopology) — 선택적 topology 제한과 기본 비활성화
