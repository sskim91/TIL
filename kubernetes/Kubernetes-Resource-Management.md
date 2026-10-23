# Kubernetes Resource Management

> **개발자를 위한 쉬운 쿠버네티스 · 21장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-DaemonSet-Job-CronJob.md) · [다음 장](./Kubernetes-Scheduling.md)

노드 CPU는 한가한데 왜 새 Pod는 Pending이고, 이미 실행 중인 앱은 왜 느려질까?

[Pod](Kubernetes-Pod.md)에서 실행 단위와 상태를 배웠다면 이 장을 읽을 수 있다. Pod 하나를 실행하는 데 성공한 다음에는 여러 앱이 같은 노드의 CPU·메모리를 나눠 쓸 때를 생각해야 한다. 자원 선언은 배치 단계의 수용 판단과 실행 단계의 제한에 서로 다르게 쓰인다. 두 단계를 나누어야 Pending을 고치려고 request를 낮추거나 OOM을 고치려고 CPU limit을 높이는 실수를 피할 수 있다.

## 결론부터 말하면

requests는 scheduler가 배치할 자리를 계산하고 실행 중 자원을 배분하는 기준이며, limits는 실행 중 사용을 제한하는 조건이다. Linux에서 CPU limit은 throttling에, 메모리 limit은 한도 압박에 따른 OOM에 연결된다. 이와 별개로 노드 압박은 kubelet의 Pod 퇴거를 일으킬 수 있다.

| 질문 | 먼저 볼 선언·관찰 |
|---|---|
| 왜 새 Pod를 배치하지 못했나? | requests, 노드 allocatable, `FailedScheduling` |
| 왜 실행 중 응답이 느린가? | CPU 사용·throttling 지표, 앱 지연 |
| 왜 프로세스가 강제 종료되었나? | container last state, `OOMKilled`, 메모리 추이 |
| 왜 Pod 자체가 퇴거되었나? | Pod reason, 노드 압박·Events |
| 왜 API 생성부터 거절되었나? | LimitRange·ResourceQuota와 admission 오류 |

이 장의 `order-api`, namespace `bookstore`, `registry.example.com/book/order-api:1.0.0`은 기존 책의 가상 사례다. 이미지를 실제 공개 이미지로 제공하는 실습이 아니며 YAML은 표시한 범위의 설명용 예제다. 명령은 실행 기록이 아니다. `example-node`·`example-gpu-node`는 실제 대상 노드 이름으로 바꿀 자리표시자다.

## 1. 왜 사용률과 배치 가능량이 다를까?

앱이 평소 CPU를 거의 쓰지 않아도 트래픽이 몰리면 동시에 CPU를 요구할 수 있다. scheduler가 순간 사용률만 보고 빈자리를 채우면 한꺼번에 바빠지는 순간 경쟁이 커진다. 그래서 requests라는 선언을 바탕으로 새 Pod를 수용할 수 있는지 계산한다. request는 측정된 현재 사용량도, CPU 코어 하나의 독점 예약도 아니다. CPU 경쟁 시 자원 배분의 기준이 되며 CPU Manager의 전용 CPU 정책 같은 별도 기능과 구분한다.

노드의 물리 용량 전체를 Pod에 줄 수도 없다. 운영체제·Kubernetes 구성 요소의 예약 등을 제외하고 Pod에 제공하는 양을 **allocatable** 이라고 한다. CPU·메모리 등 자원별로 이 양과 이미 배치한 Pod의 유효 requests를 비교한다. 예를 들어 allocatable CPU가 4이고 이미 배정한 requests가 2라면 CPU request 3인 새 Pod는 순간 사용률이 10%여도 들어갈 수 없다. 남은 2를 만족해도 [스케줄링 조건](Kubernetes-Scheduling.md)과 volume 제약 등을 추가로 통과해야 한다.

`kubectl top`은 Metrics API의 사용량을, `kubectl describe node`의 Allocated resources는 배정된 requests·limits를 보여 준다. 서로 다른 질문에 답하므로 두 숫자가 같아야 정상인 것은 아니다. limits 합계는 노드 용량보다 클 수도 있다. 그런 overcommit을 허용했다면 동시 최대 부하에서 경쟁·OOM·퇴거 위험을 감당할 수 있는지는 별도 판단해야 한다.

## 2. Requests와 Limits를 읽는 법

다음은 Pod의 `spec` 아래에 들어갈 구조 발췌다. CPU request 250m와 limit 1000m은 각각 CPU 0.25와 1에 해당한다.

```yaml
containers:
- name: order-api
  image: registry.example.com/book/order-api:1.0.0
  resources:
    requests:
      cpu: "250m"
      memory: "256Mi"
    limits:
      cpu: "1000m"
      memory: "512Mi"
```

| 단위 | 뜻 | 주의점 |
|---|---|---|
| CPU `1`, `500m`, `100m` | CPU 1, 0.5, 0.1 | `m`은 milli CPU |
| 메모리 `128Mi`, `1Gi` | 128 MiB, 1 GiB | 2진수 단위 |
| 메모리 `128M` | 128 MB | 10진수 단위로 `128Mi`와 다름 |

request보다 많이 쓰는 것 자체는 오류가 아니다. limit과 노드의 여유가 허용하면 더 사용할 수 있다. 반대로 limit만 쓰고 request를 생략했으며 admission 기본값도 없다면 Kubernetes는 그 limit을 request로 복사한다. 작성한 YAML만 보지 말고 admission 이후 저장된 Pod spec을 읽어야 하는 이유다.

Pod 안에 앱 컨테이너가 여러 개면 그 자원을 합산한다. 완료 후 종료되는 일반 init container만 있다면 자원별 init 최댓값과 앱 컨테이너 합계 중 큰 값을 사용하고, Pod overhead가 있으면 더한다. native sidecar는 초기화 뒤에도 실행되므로 초기화 단계마다 함께 실행되는 sidecar와 앱 실행 단계의 자원을 함께 계산한다. init 하나만 보고 Pod 전체 request를 정하면 기동에 필요한 용량을 놓친다. 이 장은 컨테이너별 CPU·메모리 선언을 기준으로 하며, Pod 수준 자원 선언과 GPU 같은 확장 자원은 별도의 지원 조건을 확인한다.

## 3. 실행 중에는 CPU와 메모리가 다르게 실패한다

### 3.1 CPU throttling은 지연으로 드러날 수 있다

일반적인 Linux 환경에서 CPU limit은 cgroup을 통해 일정 기간 사용할 CPU 시간을 제한한다. 앱이 더 계산하려 해도 제한에 걸리면 다음 실행 기회를 기다린다. CPU limit 자체가 메모리 OOM처럼 프로세스를 죽이는 것은 아니지만, 그 지연이 timeout이나 probe 실패를 유발하여 간접적으로 재시작에 이어질 수 있다.

평균 CPU가 낮아도 짧은 burst에서 throttling이 발생할 수 있다. 앱 요청 지연·동시성·CPU 사용량과 함께 제공되는 cgroup·컨테이너의 throttling 지표를 본다. CPU limit을 올리거나 생략하면 burst 여지는 늘지만 같은 노드의 다른 앱과 경쟁할 수 있으므로 request·노드 여유·격리 정책도 같이 검토한다.

### 3.2 메모리 한도와 OOMKilled

메모리는 계산 시간을 잠깐 미루는 방식으로만 해결되지 않는다. 컨테이너 한도 압박에서 커널이 프로세스를 OOM 종료할 수 있다. 같은 Pod 안의 재시작 여부는 restart policy 등에 달려 있다. 다음은 실제 출력이 아닌 관찰 항목의 예다.

```text
Last State: Terminated
  Reason: OOMKilled
  Exit Code: 137
```

137은 일반적으로 SIGKILL에 대응하는 exit code다. SIGKILL의 원인이 항상 OOM인 것은 아니므로 `reason: OOMKilled`, 노드·컨테이너 지표와 Events를 함께 확인한다. 재시작 후 현재 메모리가 낮다는 관찰도 종료 직전 peak를 반박하지 않는다.

Java 앱이라면 heap 외에 metaspace·thread stack·direct buffer·native memory가 필요하다. 메모리 limit을 JVM heap 크기와 같게 두면 이 여유를 놓친다. leak인지 정상 peak인지 구분하고 기동·정상·최대 부하를 측정한 뒤 request와 limit을 정한다.

### 3.3 Requests = Limits가 언제나 정답일까?

다음 두 발췌는 정책의 차이를 보여 준다. 첫 구성은 CPU·메모리 request와 limit을 같게 하고, 둘째는 더 큰 사용 여지를 둔다. 숫자는 공통 권장값이 아니다.

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

```yaml
resources:
  requests:
    cpu: "250m"
    memory: "512Mi"
  limits:
    cpu: "1000m"
    memory: "768Mi"
```

request를 지나치게 높이면 들어갈 Pod 수가 줄고, 지나치게 낮으면 실제 부하가 한 노드에 몰릴 수 있다. limit이 지나치게 낮으면 CPU 지연이나 메모리 OOM을 만들 수 있다. 앱의 부하 특성·지연 목표·비용·조직의 격리 정책으로 선택하고 운영 지표로 조정한다.

## 4. QoS와 노드 압박을 함께 읽기

Kubernetes는 자원 선언을 바탕으로 Pod에 Quality of Service(QoS) class를 부여한다. 컨테이너별 CPU·메모리 선언을 쓰는 일반적인 경우는 다음과 같다. 앱뿐 아니라 init container의 조건도 포함해 판별한다.

| QoS class | 조건 |
|---|---|
| Guaranteed | 모든 컨테이너에 CPU·메모리 request와 limit이 있고, 각 자원의 request와 limit이 같음 |
| Burstable | Guaranteed가 아니면서 하나 이상의 CPU·메모리 request 또는 limit이 있음 |
| BestEffort | CPU·메모리 request와 limit이 없음 |

QoS를 생존 보장 등급으로 해석하면 곤란하다. 노드 메모리·디스크 등이 부족해 kubelet이 회수와 퇴거를 판단할 때는 해당 자원의 request 초과 여부, Pod Priority, request 대비 사용량 등을 고려한다. 따라서 모든 압박을 BestEffort → Burstable → Guaranteed 하나의 순서로 설명할 수 없다. 디스크 압박에서는 CPU·메모리 QoS만으로 판단할 수도 없다. Guaranteed도 노드 장애나 심각한 압박에서 안전을 보장받지 않는다.

컨테이너 memory limit 때문에 발생하는 OOM과 노드 압박으로 Pod 전체가 퇴거되는 사건을 구분한다. 전자는 같은 Pod의 컨테이너 재시작으로 이어질 수 있고, 후자는 기존 Pod가 끝난 뒤 상위 controller가 대체 Pod를 만드는 경로다. 노드 압박 퇴거에는 일반 API eviction과 다른 제약이 있으므로 PodDisruptionBudget만으로 이를 막는다고 기대하지 않는다.

## 5. LimitRange와 ResourceQuota는 무엇을 막을까?

한 팀이 request를 누락하거나 수백 개 Pod를 만들면 같은 namespace 안에서도 자원 선언이 흐트러질 수 있다. **LimitRange** 는 개별 컨테이너·Pod 등의 기본값과 허용 범위를, **ResourceQuota** 는 namespace의 자원 총량·객체 수 등을 제한한다. 둘 다 실제 물리 자원을 새로 확보하는 기능은 아니다.

다음은 완전한 설명용 객체 두 개다. `bookstore` namespace가 이미 존재한다고 가정한다. 이 LimitRange는 컨테이너의 기본 request·limit을 넣으며 최소·최대 범위도 제한한다. Quota는 namespace의 집계 예산을 제한한다.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: container-defaults
  namespace: bookstore
spec:
  limits:
  - type: Container
    defaultRequest:
      cpu: "250m"
      memory: "256Mi"
    default:
      cpu: "1000m"
      memory: "512Mi"
    min:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "2Gi"
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-budget
  namespace: bookstore
spec:
  hard:
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "8"
    limits.memory: "16Gi"
    pods: "20"
```

유효한 request·limit을 갖춰도 Quota가 소진되면 생성 요청이 거절될 수 있다. 반대로 Quota에 여유가 있어도 실제 노드 용량·배치 조건이 없으면 생성된 Pod는 Pending에 남는다. Deployment 자체는 생성되었지만 controller가 Pod를 만드는 단계에서 quota 오류를 만날 수도 있으므로 Deployment·ReplicaSet의 Events까지 확인한다. API 거절과 scheduler 대기를 구분해야 다음 조치가 맞는다.

LimitRange의 변경이 이미 실행 중인 모든 Pod의 자원을 소급 변경하지도 않는다. 새 Pod에 admission이 적용된 결과와 quota의 `used`·`hard`를 확인한다. 자원 quota를 사용하면 관련 request·limit 명시가 요구될 수 있으므로 기본값 정책과 함께 설계한다.

## 6. 관찰에서 조정까지

다음은 개인 실습 context가 준비되었을 때의 읽기 전용 명령 예다. `top`은 Metrics API가 필요하고, 짧은 샘플은 peak나 장기 추이를 대신하지 않는다.

```bash
kubectl -n bookstore get pod order-api-pod -o yaml
kubectl -n bookstore describe pod order-api-pod
kubectl describe node example-node
kubectl -n bookstore get limitrange,resourcequota
kubectl -n bookstore describe resourcequota team-budget
kubectl -n bookstore top pod order-api-pod --containers
```

먼저 admission 이후의 선언과 Events를 본다. Pending이면 [Scheduling](Kubernetes-Scheduling.md)에서 노드별 제외 이유를 좁히고, 실행 중 지연이면 throttling과 앱 지연을, 재시작이면 이전 종료 이유·로그·메모리 peak를 본다. 자원 변경은 원인에 대한 가설을 세운 뒤 부하 검증과 배포 관찰로 확인한다.

### 6.1 In-place Pod Resize: 재생성 없이 requests/limits 바꾸기

2026-10-23에 확인한 [공식 문서](https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/)는 컨테이너의 in-place resize를 Kubernetes v1.35부터 stable로 설명한다. `resize` 서브리소스로 실행 중 Pod의 CPU·메모리 requests·limits를 변경한다. 지원 버전·runtime·노드 여유·변경 정책에 제약이 있으므로 일반 학습 경로에서는 Deployment 템플릿을 바꿔 Pod를 교체하는 모델을 먼저 익힌다.

아래는 형식을 설명하는 쓰기 명령이며 실행하지 않았다. 기능을 지원하는 개인 실습 클러스터에 해당 Pod가 있다는 전제가 필요하다. resize 전후 Pod의 QoS class가 같아야 한다. CPU request와 limit를 같게 만드는 이 예도 메모리·다른 컨테이너 설정에 따라 QoS 전환을 일으키지 않는지 먼저 확인한다.

```bash
kubectl -n bookstore patch pod order-api-pod --subresource resize --patch \
  '{"spec":{"containers":[{"name":"order-api","resources":{"requests":{"cpu":"800m"},"limits":{"cpu":"800m"}}}]}}'
```

컨테이너별 `resizePolicy`로 변경에 재시작이 필요한지 표현하고 `PodResizePending`·`PodResizeInProgress` condition으로 진행을 관찰한다. 요청한 `spec` 값만 보고 실제 할당 완료로 판단하지 않는다. 현재 노드에서 불가능한 증가라면 지연·불가 상태가 될 수 있고 이 기능이 Pod를 다른 노드로 옮겨 주지는 않는다. 메모리 축소처럼 제약이 있는 변경은 공식 제한사항을 확인한다.

Pod를 직접 resize해도 Deployment 템플릿이 바뀌지 않는다는 점이 핵심이다. 교체될 다음 Pod에도 유지할 값이면 템플릿과 Helm values·GitOps 같은 배포 정본에 반영한다. 같은 UID를 유지하는 기능이 항상 프로세스 무중단을 보장하는 것도 아니다.

## 7. 정리

자원 문제는 API admission, scheduler의 자리 계산, 실행 중 CPU·메모리 제약, 노드 압박을 차례로 나누어 읽는다. request를 낮춰 배치를 통과하는 것과 앱에 필요한 자원을 확보하는 것은 다른 일이다. 먼저 원인에 맞는 상태와 지표를 확보하고, 자원 선언과 앱의 실제 부하를 함께 조정한다.

다음 [스케줄링](Kubernetes-Scheduling.md)에서는 이렇게 계산한 자원 조건에 label·affinity·taint·장애 범위 조건을 더해 실행할 Node를 고르는 과정을 살펴본다.

## 생각해 볼 질문

1. **Quota에 CPU 4가 남아 있으면 CPU request 2인 Pod는 실행될까?**
   해설: Quota는 namespace의 사용 예산이다. 실제 노드 allocatable과 이미 배정한 requests, affinity·taint·volume 조건을 만족해야 배치되므로 실행을 보장하지 않는다.
2. **Guaranteed Pod도 OOMKilled가 될 수 있을까?**
   해설: QoS는 컨테이너의 memory limit을 없애지 않는다. limit 압박에 따른 OOM과 노드 압박 퇴거를 나누어 확인한다. heap 외 메모리도 포함해 측정해야 한다.
3. **In-place resize 성공 응답 뒤 Deployment를 재배포하면 왜 이전 자원으로 돌아올까?**
   해설: 개별 Pod 수정과 Deployment의 Pod 템플릿은 다른 객체다. 진행 상태를 확인하고 유지할 값은 배포 정본에 반영해야 한다.

## 출처

2026-10-23 기준 공식 문서로 개념·제약과 resize의 버전 경계를 확인했다. 예제는 정적으로 확인했으며 실제 부하·OOM·퇴거·resize를 실행한 결과가 아니다.

- [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) — requests·limits·단위·기본값
- [Reserve Compute Resources for System Daemons](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/) — allocatable과 시스템 예약
- [Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/) · [Sidecar Containers](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/) — Pod 자원 계산
- [Pod Quality of Service Classes](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/) — QoS 조건
- [Node-pressure Eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/) — 퇴거와 순위 판단
- [Limit Ranges](https://kubernetes.io/docs/concepts/policy/limit-range/) · [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/) — admission 범위와 namespace 예산
- [Resize CPU and Memory Resources assigned to Containers](https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/) — in-place resize와 제약
