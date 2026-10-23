# Kubernetes DaemonSet, Job, CronJob: 특수 목적 워크로드

> **개발자를 위한 쉬운 쿠버네티스 · 16장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-StatefulSet.md) · [다음 장](./Kubernetes-Deployment-Strategy.md)

주문 API는 요청을 기다리며 계속 실행되어야 하지만, 주문 집계 프로그램은 하루 데이터를 처리한 뒤 끝나야 한다. 한편 Node의 로그 수집기는 API replica 수가 아니라 Node 구성에 맞춰 배치되어야 한다. 같은 컨테이너 이미지 실행이라도 무엇을 정상 상태로 삼는지가 다르다.

## 결론부터 말하면

DaemonSet은 조건에 맞는 Node마다 필요한 Pod를 유지하고, Job은 필요한 성공 완료를 추적하며, CronJob은 시각에 따라 Job 생성을 요청한다. Deployment의 `replicas`를 조금 바꾸어 이 세 동작을 모두 대신할 수는 없다.

Job과 CronJob은 업무 처리를 정확히 한 번만 실행하는 보장이 아니다. 장애와 재시도 때문에 같은 프로그램이 다시 시작되거나 중복 실행될 수 있다. 주문 정산·결제·DB 변경의 중복을 막는 일은 앱과 데이터 저장소의 설계에 포함되어야 한다.

| 정상 상태의 기준 | 사용할 실행 모델 |
|---|---|
| 교체 가능한 서버 N개가 계속 실행됨 | Deployment |
| 정체성이 있는 인스턴스가 계속 실행됨 | StatefulSet |
| 대상 Node마다 에이전트가 실행됨 | DaemonSet |
| 정해진 성공 완료에 도달함 | Job |
| 정해진 schedule에 따라 Job 생성 시도 | CronJob |

## 1. 로그 수집기를 replicas로 관리하면 생기는 빈칸

Node가 세 개라고 Deployment replicas도 3으로 정해 보자. scheduler는 자원과 배치 조건을 고려하므로 한 Node에 두 Pod가 놓이고 다른 Node에는 하나도 없을 수 있다. Node가 늘어날 때 replicas 숫자도 자동으로 같은 수만큼 늘어나지는 않는다. Node마다 로컬 로그를 읽는 에이전트에는 총개수와 다른 목표가 필요하다.

DaemonSet controller는 selector·Node affinity·taint/toleration 등을 고려해 대상 Node를 정하고 그 Node에 필요한 Pod를 만든다. 일반적으로 각 대상 Node에 하나씩 유지하는 모델이지만, 모든 Node에 항상 정확히 하나의 Ready Pod가 있다는 보장은 아니다. 이미지 pull, 자원, 권한 문제로 실행이 지연될 수 있고 rollout의 surge 설정에 따라 같은 Node에 구·신 Pod가 잠시 겹칠 수 있다.

### controller와 scheduler의 역할

DaemonSet controller가 모든 scheduling을 직접 끝내는 것도 아니다. controller는 대상 Node를 제한하는 nodeAffinity를 생성 Pod에 넣고 scheduler가 그 Node에 바인딩하도록 한다. 따라서 affinity와 실제 Node 배정, kubelet의 실행 결과를 나누어 볼 수 있다.

아래는 로그 에이전트의 형태를 설명하는 독립 예제다. 주문 API 이미지가 아니며, 가상 에이전트 이미지가 `/host/var/log`를 읽고 중앙 저장소로 전송하도록 별도 설정되어 있다고 가정한다. 운영용 수집기 설치 파일 전체는 아니다.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-log-agent
  namespace: bookstore
spec:
  selector:
    matchLabels:
      app: node-log-agent
  template:
    metadata:
      labels:
        app: node-log-agent
    spec:
      nodeSelector:
        logging: enabled
      containers:
      - name: agent
        image: registry.example.com/book/log-agent:1.0.0
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
        volumeMounts:
        - name: node-logs
          mountPath: /host/var/log
          readOnly: true
      volumes:
      - name: node-logs
        hostPath:
          path: /var/log
          type: Directory
```

`logging: enabled` label이 있는 Node가 대상이며 replicas 필드는 없다. hostPath를 쓰므로 이 워크로드의 권한은 일반 API와 다르다. namespace의 보안 정책이 이를 허용하는지, 읽을 로그에 민감 정보가 있는지도 확인해야 한다.

현대 CRI 런타임에서는 kubelet의 기본 Pod 로그 경로인 `/var/log/pods`와 `/var/log/containers`의 symlink 관계가 중요하다. kubelet 설정으로 로그 디렉터리가 바뀔 수 있고, 수집 컨테이너의 mount 경로가 symlink 해석과 맞아야 한다. 과거 Docker의 `/var/lib/docker/containers`만 고정해 읽으면 containerd/CRI-O 환경의 로그를 놓칠 수 있다. 이 저장 경계는 [Volume 장의 hostPath](Kubernetes-Volume-PersistentVolume.md#node의-경로를-연결하면-영구-저장소인가)와 연결된다.

## 2. DaemonSet의 업데이트와 자원도 운영에 영향을 준다

기본 `RollingUpdate`는 배포된 에이전트를 자동 교체한다. `OnDelete`는 template 변경 후 기존 Pod를 자동 교체하지 않으므로 운영자가 Node별로 진행을 통제할 때 사용할 수 있다. CNI처럼 Node 네트워크에 영향을 주는 컴포넌트는 무조건 어느 전략을 고르기보다 제품의 지원 upgrade/rollback 절차를 따른다.

다음은 DaemonSet spec의 발췌다. 추가 Pod를 먼저 만들려면 같은 Node에서 두 인스턴스가 공존할 수 있어야 한다.

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0
    maxSurge: 1
minReadySeconds: 30
```

hostPort나 장치, 로컬 lock을 독점한다면 새 Pod가 먼저 실행되지 못할 수 있다. 반대로 기본적인 `maxSurge: 0`, `maxUnavailable: 1` 방식은 이전 인스턴스를 내린 동안 수집 공백이 생길 수 있다. 무조건 surge를 늘리는 것보다 공존 가능성, 유실 허용 범위, 자원 여유를 함께 판단한다. `minReadySeconds`는 새 Pod가 계속 Ready인 시간을 본다. 중앙 로그 저장소에 전송이 성공했다는 업무 검증을 대신하지 않는다.

### toleration은 실행이나 퇴거 면제 보장이 아니다

control-plane Node나 특수 장치 Node에 필요한 에이전트는 해당 taint를 허용하는 toleration이 필요할 수 있다. DaemonSet에는 일부 Node 상태 taint의 toleration이 자동 추가된다. 예를 들어 disk-pressure의 `NoSchedule` toleration이 있다고 해서 디스크 부족 상태에서 kubelet eviction까지 면제되는 것은 아니다.

PriorityClass 역시 절대 보호 장치가 아니다. scheduler의 preemption과 kubelet의 node-pressure eviction은 다른 판단 경로다. 일반 로그 수집기에 `system-node-critical`이나 `system-cluster-critical`을 일괄 지정하면 다른 필수 워크로드를 밀어낼 수 있다. 시스템 예약 우선순위는 실제 클러스터 필수 구성 요소에 한정하고, 일반 에이전트에는 운영자가 정한 정책·requests·디스크 사용 관리가 먼저다.

### 새 Node에도 에이전트의 비용이 들어간다

Karpenter 같은 Node autoscaler는 일반 워크로드의 배치 불가능 상태를 해소할 Node를 마련할 때, 새 Node에서 실행될 DaemonSet의 requests도 overhead로 고려한다. 앱 requests만 보고 instance 크기를 정하면 실제 Node에는 에이전트 때문에 여유가 부족할 수 있다.

특정 기존 Node를 대상으로 만들어진 DaemonSet Pod 하나가 Pending이라고 새 Node를 만들면 그 문제가 해결되는 것은 아니다. 그 Pod의 대상은 이미 있는 Node이기 때문이다. PriorityClass를 높이는 것을 만능 해결로 쓰기보다 해당 Node의 allocatable과 요청 합, 어떤 대상 DaemonSet이 overhead에 포함되는지 확인한다. [Karpenter Scheduling 문서](https://karpenter.sh/docs/concepts/scheduling/)는 Node 조건과 DaemonSet overhead의 관계를 설명한다.

## 3. Job은 실행 유지 대신 성공 완료를 추적한다

주문 DB migration을 Deployment로 실행하면 스크립트가 exit 0으로 끝나도 서버처럼 계속 실행되기를 원하는 template의 `restartPolicy: Always` 때문에 kubelet이 같은 Pod 안의 컨테이너를 다시 시작한다. Deployment가 매번 새 Pod를 만드는 것과 구분해야 한다.

Job은 성공 종료를 정상 상태로 받아들인다. 다음은 가상 주문 앱 이미지가 `migrate` subcommand를 제공하고 DB 접속 설정과 잠금을 별도로 갖춘다는 전제의 예다. 일반 `order-api` 서버와 다른 실행 모드다.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: order-schema-v2
  namespace: bookstore
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 3
  activeDeadlineSeconds: 900
  ttlSecondsAfterFinished: 86400
  template:
    metadata:
      labels:
        app: order-schema-migration
    spec:
      restartPolicy: Never
      containers:
      - name: migration
        image: registry.example.com/book/order-api:1.0.0
        args: [migrate]
```

Job controller는 template으로 Pod를 만들고 성공·실패를 관찰한다. `completions`는 필요한 성공 완료 수, `parallelism`은 동시에 실행하려는 Pod 수다. 실패하거나 Pod를 잃으면 정책에 따라 다시 시도할 수 있다. `completions: 1`, `parallelism: 1`이어도 프로그램이 정확히 한 번만 시작된다는 뜻은 아니다.

`activeDeadlineSeconds`는 Job의 전체 활동 시간을 제한한다. 개별 HTTP 호출 timeout도, schedule에 늦게 출발해도 되는 시간도 아니다. 컨트롤러가 더 시도할 시간을 제한하는 것과 이미 보낸 외부 결제 요청을 취소하는 것은 별개다.

### kubelet의 재시작과 Job controller의 재시도

| restartPolicy | 실패 시 경로 |
|---|---|
| Never | 해당 컨테이너를 재시작하지 않음. Pod 실패 후 Job controller가 새 Pod 생성 가능 |
| OnFailure | kubelet이 같은 Pod에서 실패 컨테이너 재시작 가능. Pod 실패·소실 때는 새 Pod도 가능 |

일반 Job의 `backoffLimit` 기본값은 6이다. 실패 Pod 수와, OnFailure인 Running/Pending Pod의 컨테이너 재시작 수를 두 방식으로 계산하며 어느 하나가 기준에 도달하면 Job 실패로 판단할 수 있다. 둘을 무조건 하나의 합계로 설명하거나 OnFailure의 컨테이너 재시작은 제한을 소비하지 않는다고 해석하면 안 된다. per-index backoff처럼 별도 설정이 있는 Job에는 그 정책도 함께 읽는다.

Never는 시도별 Pod와 로그를 구분하기 편하지만 새 Pod 생성 비용이 있다. OnFailure는 같은 Node에서 다시 시도하므로 그 Node의 네트워크나 디스크 문제가 그대로 남을 수 있다. 어느 쪽도 재실행의 업무 안전성을 자동으로 제공하지 않는다.

## 4. 재실행되는 작업의 안전성은 저장소에서 결정된다

정산 프로그램이 DB에 결과를 기록한 직후, 성공 상태를 보고하기 전에 Node가 끊겼다고 하자. Job controller는 완료 사실을 확인하지 못하고 작업을 다시 시작할 수 있다. 두 번째 프로그램은 첫 번째 프로그램이 이미 만든 결과와 마주한다.

그래서 멱등성은 단순히 시작 전에 `is_already_applied()`를 호출하는 수준으로 끝나지 않는다. 두 프로세스가 동시에 미완료를 읽으면 둘 다 실행할 수 있다. 업무 키에 unique constraint를 걸고 같은 transaction 안에서 결과와 처리 기록을 저장하거나, DB migration 도구의 lock과 이력 테이블을 사용하는 식으로 경쟁까지 제어해야 한다.

```sql
-- 개념 예시: DB가 지원하는 transaction과 unique constraint를 전제한다.
BEGIN;
INSERT INTO settlement_runs (business_date) VALUES ('2026-10-22');
-- business_date에 UNIQUE 제약이 있어 중복 실행은 이 지점에서 충돌한다.
-- 같은 transaction에서 해당 날짜의 결과를 기록한다.
COMMIT;
```

이 예는 DB 내부의 원자성만 설명한다. transaction 중 외부 결제 API를 호출하면 DB rollback이 결제를 되돌리지 않는다. 외부 서비스의 idempotency key, outbox와 재전송 처리, 보상 절차 같은 별도의 경계가 필요하다. 실행 한 번이라는 인프라 목표와 업무 결과 한 번이라는 목표를 나누어 설계하는 이유다.

### Indexed Job은 분할 번호를 준다

여러 파일이나 테스트 묶음을 나눠 처리하려면 `completionMode: Indexed`를 쓸 수 있다. 다음은 Job spec의 발췌이며 이미지가 `process-partition` 명령을 제공한다는 전제다.

```yaml
completionMode: Indexed
completions: 5
parallelism: 3
template:
  spec:
    restartPolicy: Never
    containers:
    - name: worker
      image: registry.example.com/book/batch-worker:1.0.0
      args: [process-partition, "$(JOB_COMPLETION_INDEX)"]
```

completion index는 0부터 4까지이며 환경 변수 `JOB_COMPLETION_INDEX`로 전달된다. index는 담당 partition을 식별하는 수단이지 실행 횟수를 제한하는 lock이 아니다. 같은 index의 작업도 재시도될 수 있으므로 결과 키와 멱등성을 partition 단위로 설계한다.

### 실패의 종류에 따라 재시도 의미가 다르다

설정 오류를 나타내는 앱 고유 exit code는 재시도해도 해결되지 않을 수 있고, drain으로 중단된 작업은 다시 시도할 가치가 있다. `podFailurePolicy`는 이런 조건을 규칙으로 표현한다. 다음은 Job spec의 발췌이며 Pod template의 restartPolicy는 `Never`여야 한다.

```yaml
podFailurePolicy:
  rules:
  - action: FailJob
    onExitCodes:
      containerName: migration
      operator: In
      values: [42]
  - action: Ignore
    onPodConditions:
    - type: DisruptionTarget
```

42는 이 앱이 설정 오류로 정의한 코드다. 규칙은 순서대로 평가하고 첫 일치가 적용되므로 FailJob과 Ignore의 순서도 정책의 일부다. 일치하지 않는 실패는 기본 Count 경로로 처리한다. exit 137은 SIGKILL을 나타낼 수 있을 뿐 OOM의 확정 증거가 아니다. container terminated reason, Pod Events와 Node/커널 증거를 함께 본다.

## 5. 완료되지 않는 Job과 sidecar의 수명

메인 프로그램은 성공 종료했지만 일반 `containers`에 선언한 로그 전송기나 메시 proxy가 계속 실행되면 Job 완료가 막힐 수 있다. 이는 앱의 업무가 끝난 시점과 Pod의 컨테이너 수명이 다른 문제다.

Kubernetes의 native sidecar는 `initContainers`에 컨테이너 단위 `restartPolicy: Always`를 지정해 선언한다. 메인 컨테이너가 끝난 뒤에도 무한히 완료를 막는 일반 컨테이너와 다른 종료 처리를 제공한다. 1.29에서 beta 기본 활성화, 1.33에서 stable이 된 기능이다. 아래는 수명 형태만 보여 주는 Pod spec 발췌다.

```yaml
initContainers:
- name: log-forwarder
  image: registry.example.com/book/log-forwarder:1.0.0
  restartPolicy: Always
containers:
- name: worker
  image: registry.example.com/book/batch-worker:1.0.0
  args: [run]
restartPolicy: Never
```

실제 로그 volume·전송 설정과 종료 시 flush는 수집기별로 준비해야 한다. Istio proxy 이미지 하나를 이 자리에 넣는다고 완전한 메시 주입 설정이 되지는 않는다. 메시 제품과 injector가 지원하는 native sidecar 모드를 확인하는 것이 먼저다.

`shareProcessNamespace: true`도 자동 종료 기능이 아니다. 프로세스 namespace를 공유하면 서로의 프로세스를 볼 수 있지만 메인이 끝났다고 나머지가 저절로 끝나지 않는다. 이 모드에서 PID 1은 보통 앱이 아니라 Pod sandbox 프로세스다. PID 1을 죽이는 패턴을 일반적인 Job 해결책으로 쓰지 않는다. 레거시 proxy 종료 API가 필요한 경우에도 제품 지원 방식, 호출 실패, 앱 exit code 보존과 로그 유실을 별도로 처리한다.

## 6. CronJob은 시계와 Job 사이의 controller다

CronJob은 정해진 시각에 Job 생성을 시도하고, 생성된 Job이 Pod의 완료를 관리한다. schedule 시각, Job 생성 시각, Pod가 실제 실행된 시각, 업무 완료 시각은 서로 다르다. 자원이 부족하면 시각에 맞춰 Job이 생겨도 Pod는 Pending으로 기다릴 수 있다.

다음은 매일 한국 시간 03:00에 전날 주문을 집계하는 가상 앱이다. 날짜 범위와 업무 키를 결정하는 로직은 앱에 있고, DB 접속·중복 제어가 구성되었다고 가정한다.

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: order-daily-summary
  namespace: bookstore
spec:
  schedule: "0 3 * * *"
  timeZone: Asia/Seoul
  concurrencyPolicy: Forbid
  startingDeadlineSeconds: 600
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      activeDeadlineSeconds: 1800
      backoffLimit: 2
      ttlSecondsAfterFinished: 172800
      template:
        spec:
          restartPolicy: Never
          containers:
          - name: summary
            image: registry.example.com/book/order-api:1.0.0
            args: [summarize-previous-day]
```

cron의 다섯 필드는 분·시·일·월·요일 순서다. `*/15 * * * *`는 15분 간격, `0 0 * * 0`은 매주 일요일 00:00이다. `timeZone`은 Kubernetes 1.27 stable 기능이며 생략하면 controller의 시간대에 의존한다. `TZ=`나 `CRON_TZ=` 문자열을 schedule에 넣는 대신 별도 필드를 사용한다. 과거 환경에서 UTC로 변환한다면 controller가 실제로 UTC를 사용하는지도 먼저 확인한다.

### concurrencyPolicy는 중복 업무 lock이 아니다

`Allow`는 이전 Job과 새 Job의 겹침을 허용한다. `Forbid`는 해당 CronJob이 만든 이전 Job이 실행 중이면 새 schedule의 생성을 건너뛴다. 다른 CronJob이나 수동으로 만든 Job까지 같은 업무의 실행을 막는 분산 lock은 아니다.

`Replace`는 이전 실행을 취소하고 새 실행으로 대체한다. 그러나 중단 전에 이미 쓴 DB 데이터나 외부 요청을 rollback하지는 않는다. 부분 처리 후 재실행되는 상황을 앱이 안전하게 다룰 수 있어야 한다.

CronJob은 상황에 따라 같은 예정 실행에 Job을 둘 만들거나 만들지 못할 수 있으므로 멱등성이 필요하다. 작업의 업무 날짜를 단순한 실제 시작 시각으로만 계산하면 지연·재실행 때 잘못된 날짜를 처리할 수도 있다. 예정된 처리 대상과 실제 시작 시간을 구분해 기록하는 것이 복구에 도움이 된다.

### 늦게 시작해도 되는 범위

`startingDeadlineSeconds`는 예정 시각 이후 얼마 동안 늦은 Job 생성을 허용할지를 정한다. 위 예의 600은 집계 수행 시간을 10분으로 제한하는 값이 아니다. 작업 수행 제한은 Job의 `activeDeadlineSeconds`다.

Forbid로 놓친 schedule도 controller가 뒤늦게 검토할 수 있다. 생성 가능 여부는 그 시점의 이전 Job 상태와 deadline 등 조건에 달려 있으므로 건너뛰면 무조건 영구 삭제된다거나 놓친 것을 모두 즉시 실행한다고 생각하면 안 된다. controller가 약 10초마다 확인하는 특성상 10초보다 작은 deadline은 실행 기회를 놓칠 수 있다.

누락 schedule 계산 범위에서 100회를 초과하면 controller가 너무 많은 missed start times를 보고하며 그 계산에서 새 실행을 결정하지 못할 수 있다. 이는 정확히 100회와도 다르고, CronJob 오브젝트가 영구적으로 비활성화되는 동작도 아니다. deadline을 지정하면 그 window를 중심으로 계산하므로 장기 중단 후의 판단이 달라질 수 있다. 필요한 과거 집계는 업무 키를 지정한 수동 Job으로 복구하는 방안을 별도로 정한다.

`suspend: true`는 이후 생성을 중단하지만 이미 실행 중인 Job을 멈추지는 않는다. 해제할 때 미처리 schedule과 deadline의 관계를 확인해야 한다. 특정 실행 시점이 중요한 경우 scheduled timestamp, Job creationTimestamp, Pod startTime, 실제 업무 완료 기록을 나눠 비교한다.

## 7. 기록을 남기고 정리하는 두 가지 시간축

완료된 Job과 Pod를 계속 쌓으면 API 오브젝트와 로그 관리 비용이 늘어난다. `ttlSecondsAfterFinished`는 Job이 완료·실패한 뒤 일정 시간이 지나면 종속 Pod까지 정리하는 경로다. CronJob의 history limit은 성공/실패 Job의 개수를 기준으로 정리한다. 둘이 함께 있으면 먼저 정리 조건을 충족한 쪽 때문에 생각보다 빨리 기록이 없어질 수 있다.

보존 기간은 배치 주기보다 장애 발견 시간과 감사 요구에 맞춰 정한다. Job 오브젝트를 오래 유지한다고 로그와 업무 감사 기록까지 안전하게 영구 보관되는 것은 아니다. 중앙 로그·업무 결과 저장소와 별도의 retention이 필요하다.

```bash
kubectl get daemonset node-log-agent -n bookstore
kubectl describe daemonset node-log-agent -n bookstore
kubectl get jobs -n bookstore
kubectl describe job order-schema-v2 -n bookstore
kubectl logs job/order-schema-v2 -n bookstore
kubectl describe cronjob order-daily-summary -n bookstore
```

Job에 여러 Pod와 여러 시도가 있다면 대표 로그 하나만으로 성공 여부를 판정하지 않는다. Job conditions와 각 시도의 종료 상태, 업무 완료 기록을 연결한다. CronJob의 `lastScheduleTime`은 Job 생성 관련 상태이지 모든 업무가 성공했다는 증거가 아니다.

## 8. 심화: 관리형 실행 환경과 schedule 분산

2026-10-23 기준 EKS Fargate는 DaemonSet을 지원하지 않는다. 그렇다고 모든 DaemonSet이 반드시 Fargate Node에 배치된 뒤 Pending이 된다는 고정 경로로 설명할 수는 없다. 혼합 클러스터에서는 Node label·taint·affinity와 실제 Events를 통해 EC2의 대상 범위를 확인한다. Fargate에는 지원되는 built-in logging이나 Pod 단위 수집을 검토하며, ECS의 FireLens를 EKS의 동일 기능처럼 섞지 않는다.

AKS Virtual Nodes도 일반 VM Node와 같은 호스트 에이전트 전제를 적용할 수 없다. GKE Autopilot에서는 사용자 DaemonSet 자체와 hostPath·privileged 등 고권한 동작 허용 여부를 구분한다. 지원되는 제한적 경로나 검증된 파트너 예외가 있을 수 있으므로 모든 hostPath가 무조건 가능하거나 불가능하다고 일반화하지 않는다. 제품의 보안 정책과 실제 admission 결과가 기준이다.

Node pool 업그레이드와 에이전트 rollout을 동시에 진행하면 어느 변경이 수집 공백을 만들었는지 구분하기 어렵다. Node 교체의 surge/blue-green 정책과 DaemonSet의 rollout 정책은 다른 계층이므로 각각 capacity와 관찰 기간을 확보한다.

CronJob도 자원 계획에 들어간다. 수백 개가 매시 정각에 동시에 이미지 pull과 DB 쿼리를 시작하면 API server뿐 아니라 registry, Node 디스크, DB가 함께 영향을 받는다. schedule을 몇 분씩 분산하거나 앱이 허용하는 지연을 설계하는 방법이 있지만, 모든 업무에 공통으로 몇 분의 간격을 강제할 수는 없다. 완료 기한과 실제 병목을 기준으로 정한다.

## 생각해 볼 질문

### 1. Node 세 개에 로그 수집기 replicas 3을 띄우는 것과 DaemonSet은 왜 다른가?

Deployment는 총개수를 유지하고 DaemonSet은 대상 Node별 배치를 유지한다. Node 추가와 대상 조건 변경에 반응하는 목표가 다르다. 다만 DaemonSet도 Ready를 무조건 보장하지 않으므로 status와 Node별 Pod를 확인한다.

### 2. parallelism이 1인 Job에 unique 업무 키가 왜 필요한가?

첫 실행이 외부 효과를 만든 뒤 성공 상태를 보고하지 못하면 재실행될 수 있다. 동시 Pod 목표 수를 제한하는 것과 결과 중복을 막는 것은 다르므로 DB 제약·transaction·외부 idempotency key가 필요하다.

### 3. 매일 03:00 CronJob의 Job이 생성되었으면 03:00 백업 성공을 주장할 수 있는가?

생성 요청·Pod 시작·업무 완료는 별개다. scheduling, 이미지 공급, 권한, 저장소, backup 프로그램의 결과와 복원 가능성까지 확인해야 한다. deadline과 history도 각각 어떤 시간을 의미하는지 구분해야 한다.

## 다음 장으로

계속 실행할 서버와 끝나는 작업을 구분했다. 다음 [배포 전략](Kubernetes-Deployment-Strategy.md)에서는 이미 요청을 처리 중인 서버를 새 버전으로 교체할 때, Pod 상태와 사용자 트래픽이 어떻게 따로 변하는지 살펴본다. 이 장의 재실행·중복 효과는 배포 중 두 버전의 consumer와 migration이 공존할 때 다시 등장한다.

## 출처

- [Kubernetes DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) — 대상 Node와 scheduling
- [DaemonSet rolling update](https://kubernetes.io/docs/tasks/manage-daemon/update-daemon-set/) — 업데이트와 surge
- [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) — 완료, 재시도, Indexed Job와 failure policy
- [Kubernetes CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) — schedule, deadline, 중복과 시간대
- [TTL after finished](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/) — 완료 후 정리
- [Kubernetes Sidecar Containers](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/) — native sidecar lifecycle
- [Share Process Namespace](https://kubernetes.io/docs/tasks/configure-pod-container/share-process-namespace/) — PID 1과 process namespace
- [Pod Priority and Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/) — 우선순위의 범위
- [Node pressure eviction](https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/) — kubelet의 퇴거 판단
- [Karpenter Scheduling](https://karpenter.sh/docs/concepts/scheduling/) — Node 제약과 DaemonSet overhead
- [AWS EKS Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html) — 실행 환경의 제한
- [EKS Fargate logging](https://docs.aws.amazon.com/eks/latest/userguide/fargate-logging.html) — 지원 로그 수집 경로
- [AKS Virtual Nodes limitations](https://learn.microsoft.com/en-us/azure/aks/virtual-nodes#limitations) — 가상 Node의 제약
- [GKE Autopilot security](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-security) — workload별 권한과 예외
