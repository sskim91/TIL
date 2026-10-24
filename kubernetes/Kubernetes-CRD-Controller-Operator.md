# Kubernetes CRD, Controller, Operator

> **개발자를 위한 쉬운 쿠버네티스 · 28장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-Workload-Security.md) · [다음 장](./Kubernetes-Admission-Webhook.md)

**쿠버네티스는 어떻게 자기 자신을 확장할까 — CRD와 컨트롤러, 그리고 Operator**

[ServiceAccount와 RBAC 장](Kubernetes-ServiceAccount-RBAC.md)에서 API를 호출하는 프로그램의 신원과 권한을 배웠다. 이제 그 프로그램이 Pod뿐 아니라 새로운 종류의 요청을 처리한다고 생각해 보자. 주문 앱에 필요한 데이터베이스를 `Database`라는 리소스로 선언하고 싶다면, API의 종류를 늘리는 일과 DB를 만드는 일을 각각 누가 맡아야 할까?

운영 중인 클러스터에서 `kubectl api-resources`를 실행하면, 쿠버네티스 공식 문서 어디에도 없는 `kind`가 수십 개 쏟아진다. 그런데 그것들도 `kubectl apply -f`로 만들어지고 `kubectl get`으로 조회된다. Deployment와 완전히 같은 방식으로 다뤄지는데, 쿠버네티스 코어에는 없는 타입이다. API는 어떻게 이렇게 늘어났고, 왜 그게 Deployment와 구별되지 않는가?

---

## 결론부터 말하면

CRD는 Kubernetes API에 새 리소스 타입과 검증·저장 경로를 등록한다. 컨트롤러는 그 선언을 관찰해 실제 작업을 수행하고 결과를 보고한다. Operator는 이 반복 처리에 특정 소프트웨어의 백업·복구·업그레이드 지식을 담은 운영 방식이다.

`CustomResourceDefinition`(CRD)을 apply하면 API 서버에 새 엔드포인트와 스키마가 생긴다. 여기까지가 API 서버의 일이다 — YAML을 검증해서 etcd에 저장하는 것. 그 리소스를 보고 "그래서 Pod를 몇 개 띄우고, 디스크를 붙이고, 백업을 뜬다"를 실행하는 주체는 **별도로 돌고 있는 컨트롤러** 다. 그래서 CRD만 만들고 커스텀 리소스를 apply하면 **DB나 Pod가 자동 생성되지는 않는다.**

```mermaid
flowchart LR
    subgraph before["CRD만 있을 때"]
        y1["kubectl apply<br>-f my-database.yaml"] --> a1["API Server<br>스키마 검증"]
        a1 --> e1["etcd 저장"]
        e1 --> n1["선언 저장 완료<br>DB 실행 주체 없음"]
    end
    subgraph after["CRD + 컨트롤러"]
        y2["kubectl apply<br>-f my-database.yaml"] --> a2["API Server<br>스키마 검증"]
        a2 --> e2["etcd 저장"]
        e2 -->|"watch"| c2["Controller<br>reconcile 루프"]
        c2 --> r2["StatefulSet · Service<br>· Secret 생성"]
    end
    style n1 fill:#C62828,color:#fff
    style c2 fill:#1565C0,color:#fff
    style r2 fill:#2E7D32,color:#fff
```

| 역할 | 담당 | 하는 일 |
|------|------|---------|
| **타입과 저장** | API 서버 (+ CRD) | 새 엔드포인트 개설, 스키마 검증, etcd에 저장, watch 스트림 제공 |
| **의미와 실행** | 컨트롤러 | spec을 읽고 실제 상태와 비교해 차이를 좁히는 행동, status 보고 |
| **도메인 운영 지식** | Operator | 위 컨트롤러 + "이 소프트웨어를 어떻게 운영하는가"(백업·승격·업그레이드) |

공식 문서가 이 분리를 한 문장으로 못 박는다.

공식 문서는 custom resource만으로는 구조화한 데이터를 저장·조회하고, custom controller와 결합하면 선언적 API를 구성한다고 설명한다.

이 글은 그 문장을 따라간다. CRD를 만들면 정확히 무엇이 생기는지, 왜 그것만으로는 아무 일도 안 일어나는지, 컨트롤러가 붙으면 무엇이 달라지는지, 그리고 **왜 Deployment도 결국 같은 구조인지** 까지.

---

## 1. CRD를 apply하면 정확히 무엇이 생기는가

CRD는 "쿠버네티스 API에 새 타입을 등록해 달라"는 요청서다. 그 자체가 하나의 쿠버네티스 리소스이고, 안정 버전은 `apiextensions.k8s.io/v1`(GA)다.

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.example.com     # <plural>.<group> 형식이 강제된다
spec:
  group: example.com
  scope: Namespaced               # 이 타입의 인스턴스를 네임스페이스에 둘지, 클러스터 전역에 둘지
  names:
    plural: databases
    singular: database
    kind: Database
    shortNames: [db]              # kubectl get db 가 동작하게 된다
  versions:
  - name: v1
    served: true                  # 이 버전의 REST 엔드포인트를 열 것인가
    storage: true                  # etcd에 저장할 때 쓸 버전 (정확히 하나만 true)
    schema:
      openAPIV3Schema:            # v1에서는 스키마가 필수다 (beta에서는 선택이었다)
        type: object
        properties:
          spec:
            type: object
            properties:
              version: { type: string }
              storageSize: { type: string }
            required: [version]
          status:
            type: object
            properties:
              phase:
                type: string
              observedGeneration:
                type: integer
                format: int64
                minimum: 0
    subresources:
      status: {}                  # 5절에서 다룬다
```

위 YAML은 가상 `Database` API의 완전한 설명용 CRD다. 이 API를 구현하는 실제 DB 컨트롤러는 제공하지 않는다. CRD 등록 뒤에는 `kubectl wait --for=condition=Established crd/databases.example.com --timeout=60s`로 준비를 확인한다. endpoint와 discovery 반영에 잠깐 시간이 걸릴 수 있기 때문이다. namespace `bookstore`도 별도로 존재해야 한다.

먼저 **새 REST 엔드포인트** 가 열린다. `/apis/example.com/v1/namespaces/bookstore/databases` 같은 경로가 생기고, API 서버가 이 경로의 요청을 직접 처리한다. 이 시점부터 `kubectl get databases`가 "the server doesn't have a resource type" 에러를 내지 않는다. `kubectl api-resources`에도 나타난다 — 처음의 질문, 공식 문서에 없는 `kind`가 수십 개 나오는 이유가 바로 이것이다. 누군가 이 클러스터에 CRD를 그만큼 설치했다는 뜻이다.

둘째로 **스키마 검증** 이 붙는다. `openAPIV3Schema`에 적힌 구조가 그대로 검증 규칙이 되어, 정의된 필드의 타입·필수 조건을 검사한다. 정의하지 않은 필드는 기본적으로 pruning으로 제거될 수 있고, field validation 모드에 따라 경고나 거부도 가능하다. 따라서 오타가 언제나 같은 오류로 거부된다고 기대하지 않는다. `apiextensions.k8s.io/v1`에서는 이 구조적 스키마(structural schema)가 **필수** 다 — beta 시절에는 생략할 수 있었지만 v1에서는 없으면 CRD 자체가 거부된다. API 서버가 저장 전에 요청을 검증하고 etcd에 쓰는 이 전체 흐름(인증 → 인가 → admission → 검증 → 저장)은 [Kubernetes Admission Webhook](Kubernetes-Admission-Webhook.md)에서 다룬다.

셋째로 **기존 생태계가 전부 따라붙는다.** 이게 CRD의 진짜 가치다. 새 타입은 `kubectl`의 모든 서브커맨드(`get`, `describe`, `edit`, `apply`, `label`)를 그냥 쓸 수 있고, RBAC의 대상이 되어 `resources: ["databases"]`로 권한을 나눌 수 있고, `kubectl get -w`나 클라이언트 라이브러리의 watch가 그대로 동작하고, 라벨과 어노테이션과 `ownerReferences`도 코어 리소스와 똑같이 붙는다. 자체 API 서버를 한 줄도 쓰지 않고 이 모든 것을 얻는다.

여기까지 오면 자연스럽게 이런 기대가 생긴다. **"타입이 생겼으니, 이제 이 리소스를 만들면 뭔가 돌아가겠지."**

---

## 2. 그런데 아무 일도 일어나지 않는다

같은 가상 API로 주문 앱의 DB를 선언해 보자. 아래 manifest는 `bookstore` namespace와 앞의 CRD가 준비되었다는 전제다. 이어지는 출력은 실행 기록이 아닌 설명용 예시다.

```yaml
apiVersion: example.com/v1
kind: Database
metadata:
  name: orders-db
  namespace: bookstore
spec:
  version: "16"
  storageSize: 20Gi
```

```bash
$ kubectl apply -f orders-db.yaml
database.example.com/orders-db created      # 성공했다

$ kubectl get databases -n bookstore
NAME    AGE
orders-db   30s                             # 조회도 된다

$ kubectl get pods,statefulsets,pvc -n bookstore
No resources found in bookstore namespace. # 그런데 아무것도 없다
```

**이 지점이 이 글의 전환점이다.** apply는 성공했고, `kubectl get`으로 조회되고, `kubectl edit`으로 수정도 된다. 리소스는 분명히 "존재"한다. 그런데 Pod도, StatefulSet도, PVC도 없다. 30분을 기다려도 없다.

버그가 아니다. CRD가 제공하는 것은 검증 가능한 데이터의 저장·조회이기 때문이다. 이 기능 자체도 설정 API로 유용하지만 DB 실행까지 구현하지는 않는다. API 서버가 하는 일은 "이 YAML을 스키마로 검증해서 etcd에 저장하고, 요청이 오면 되돌려주는" 것까지다. 그 안에 적힌 `version: "16"`이 "PostgreSQL 16을 띄워라"라는 뜻인지, "16개의 무언가를 만들어라"라는 뜻인지, API 서버는 알지도 못하고 알 필요도 없다. **의미를 부여하는 것은 API 서버의 일이 아니다.**

이 착각이 흔한 이유는 코어 리소스에서는 그 경계가 안 보이기 때문이다. Deployment를 apply하면 Pod가 알아서 생기니까 "API 서버가 만들어 주는 것"처럼 느껴진다. 실제로는 Deployment도 똑같다 — API 서버는 그것을 저장했을 뿐이고, 별도로 돌고 있던 컨트롤러가 그것을 보고 움직인 것이다. 우리가 그 컨트롤러를 설치한 기억이 없는 이유는, 쿠버네티스가 처음부터 그것을 `kube-controller-manager` 안에 넣어 함께 띄워 줬기 때문이다. 4절에서 이 이야기로 돌아온다.

그래서 답은 하나다. **누군가 이 리소스를 보고 움직여 줘야 한다.**

---

## 3. 그래서 컨트롤러가 필요하다 — reconciliation loop

컨트롤러는 특별한 것이 아니다. **API 서버에 접속해 특정 타입을 지켜보며, "원하는 상태"와 "실제 상태"의 차이를 계속 좁히는 프로그램** 이다. 클러스터 안의 Deployment로 실행하는 경우가 흔하지만, API에 접근할 신원·권한과 네트워크가 있으면 클러스터 밖에서도 실행할 수 있다.

공식 문서는 이것을 로봇공학의 **제어 루프(control loop)** 로 설명한다.

> In robotics and automation, a *control loop* is a non-terminating loop that regulates the state of a system.

가장 좋은 비유는 문서에 나오는 온도조절기다. 온도를 22도로 맞춰 두는 것이 **원하는 상태(desired state)** 이고, 지금 방의 온도가 **현재 상태(current state)** 다. 온도조절기는 이 둘을 계속 비교하다가 차이가 있으면 히터를 켜거나 끈다. 목표에 도달하면 아무것도 하지 않는다. 컨트롤러가 하는 일이 정확히 이것이다.

```mermaid
flowchart LR
    obs["관찰<br>spec = 원하는 상태<br>실제 리소스 = 현재 상태"] --> cmp{"두 상태가<br>다른가?"}
    cmp -->|"다르다"| act["행동<br>차이를 좁히는 API 호출<br>(생성 · 수정 · 삭제)"]
    cmp -->|"같다"| noop["아무것도 하지 않음"]
    act --> st["status에<br>관찰 결과 기록"]
    noop --> st
    st --> obs
    style cmp fill:#BF360C,color:#fff
    style act fill:#1565C0,color:#fff
    style noop fill:#455A64,color:#fff
    style st fill:#2E7D32,color:#fff
```

이제 예시 컨트롤러가 Database를 StatefulSet·Service·Secret으로 구현하도록 작성됐다고 가정하자. 실제 Operator마다 생성 리소스와 백업·스토리지 처리가 다르므로 아래는 동작 모델의 예시다. 컨트롤러는 `Database` 타입을 watch하다가 `orders-db`가 생긴 것을 안다. 그리고 "이 이름에 해당하는 StatefulSet이 있나?"를 조회한다. 없다. 그래서 만든다. Service도 없으니 만든다. 비밀번호 Secret도 만든다. 다음 루프에서 다시 조회한다. 이제 다 있다. 그러면 **아무것도 하지 않는다.**

여기서 컨트롤러는 대개 "직접 하는" 것이 아니라 API 서버에 다른 리소스를 만들어 달라고 요청한다는 점이 중요하다. 공식 문서가 Job 컨트롤러를 예로 들어 설명하듯, Job 컨트롤러는 Pod나 컨테이너를 직접 실행하지 않는다. API 서버에 "Pod를 만들어라"라고 말할 뿐이고, 그러면 또 다른 컨트롤러와 kubelet이 그다음을 이어받는다. 컨트롤러들은 서로를 직접 호출하지 않고, **주로 API 서버에 쓴 상태를 통해 협력한다.** 외부 서비스를 직접 호출하는 컨트롤러도 있지만, Deployment→ReplicaSet→Pod 관계를 컴포넌트 간 동기 호출 사슬로 이해하면 안 된다.

### 3-1. level-triggered vs edge-triggered — 신뢰성의 핵심

이제 이 루프의 가장 중요한 성질로 들어간다. 위 다이어그램에서 컨트롤러가 무엇을 보는지 다시 보라. **"무슨 이벤트가 왔는가"가 아니라 "지금 상태가 어떤가"를 본다.**

두 설계 방식을 구별해야 한다.

| 방식 | 판단 근거 | 이벤트를 놓치면 |
|------|-----------|-----------------|
| **edge-triggered** (변화 기반) | "방금 무엇이 변했다"는 이벤트 | 그 변화는 영구히 반영되지 않는다. 이벤트를 재생(replay)해야 복구된다 |
| **level-triggered** (상태 기반) | "지금 원하는 상태와 실제 상태가 무엇인가" | 다음 루프에서 어차피 다시 비교하므로 저절로 복구된다 |

쿠버네티스는 후자를 **설계 원칙으로 못 박았다.** 공식 설계 원칙 문서의 표현이다.

설계 원칙은 중간 업데이트를 놓쳤더라도 원하는 상태와 관찰한 현재 상태만으로 올바르게 동작해야 하며, 이벤트 기반 처리는 최적화로 사용하라고 설명한다.

마지막 문장이 핵심이다. **watch 이벤트는 최적화일 뿐이다.** 컨트롤러가 watch를 쓰는 이유는 "폴링보다 빠르게 알기 위해서"이고, 판단의 근거는 이벤트가 아니라 그때 조회한 실제 상태다. 그래서 이런 일들이 자동으로 해결된다.

네트워크가 끊겨 이벤트 몇 개를 놓쳐도 다음 루프에서 상태를 비교하면 차이가 드러난다. 컨트롤러 Pod가 재시작되면 그동안의 이벤트는 전부 사라지지만, 컨트롤러는 시작 시 해당 타입을 **초기 List로 조회하고 cache를 채운 뒤 watch를 이어 가며** 상태를 맞추므로 스스로 정합을 회복한다. 누군가 손으로 StatefulSet을 지워 버려도, 컨트롤러는 "있어야 할 것이 없다"를 발견하고 다시 만든다. API 서버의 상태가 곧 진실이고, 컨트롤러는 언제 끼어들어도 진실만 보면 무엇을 해야 할지 알아낸다.

같은 문서가 이 태도를 이렇게 표현한다 — "열린 세계를 가정하라(assume an open world)". 사용자가 ReplicaSet이 관리하는 Pod를 죽이는 것도 허용하고, 그냥 다시 만든다.

**그리고 이것이 곧 멱등성(idempotency) 요구로 이어진다.** 같은 리소스에 대한 reconcile은 수백 번 반복 호출될 수 있다. 이벤트가 중복되거나, 다른 리소스 변경 때문에 트리거되거나, 주기적 cache resync로 불려서다. controller-runtime의 resync는 로컬 cache의 같은 객체로 update event를 다시 발생시키는 동작이며, 매번 API server를 재조회해 동기화한다는 보장이 아니다. 초기 List·watch 재연결 시의 재조회와 구분하고 controller별 설정을 확인한다. [cache API의 SyncPeriod 설명](https://pkg.go.dev/sigs.k8s.io/controller-runtime/pkg/cache)이 이 차이를 명시한다. 그러므로 reconcile 함수는 **"이미 되어 있으면 아무것도 하지 않는다"** 를 반드시 만족해야 한다. "이벤트를 받았으니 StatefulSet을 만든다"라고 쓰면 중복 생성이나 에러로 무너진다. "있어야 할 StatefulSet이 있는지 확인하고, 없으면 만들고, 다르면 맞춘다"라고 써야 한다. level-triggered 설계는 신뢰성을 주는 대신 이 규율을 요구한다.

### 3-2. 이것이 선언적 모델의 실체다

4장 [오케스트레이션이 필요한 이유](Kubernetes-Why-Orchestration.md#6-세-개를-실행했다보다-세-개가-필요하다를-남긴다)에서 처음 소개한 "선언적(declarative)"이라는 말의 정체가 이것이다. 선언적이라는 건 YAML을 쓴다는 문법 이야기가 아니다.

사용자는 원하는 상태를 선언하고, 컨트롤러는 관찰한 상태를 그 선언에 가깝게 유지한다는 책임 분리가 선언적 API의 핵심이다.

사용자는 **원하는 상태를 쓰고** 끝낸다. 절차를 지시하지 않는다. 절차를 실행하고, 실패하면 다시 시도하고, 누가 망가뜨리면 되돌리는 것은 컨트롤러의 몫이다. 명령형 API라면 "이걸 해라"라고 지시하고 그 명령이 실패하면 사용자가 재시도해야 한다. 선언적 모델에서는 재시도가 시스템의 기본 동작이다. **선언적 모델 = 스키마 있는 저장소 + level-triggered 컨트롤러** 인 셈이고, CRD는 앞의 절반, 컨트롤러가 뒤의 절반이다.

---

## 4. 코어 리소스도 완전히 같은 방식으로 동작한다

이 글에서 딱 하나만 기억한다면 이 절이다. 지금까지 설명한 "CRD + 컨트롤러"는 **확장을 위한 예외적 기법이 아니다. 쿠버네티스가 자기 자신을 만드는 방식과 동일한 것이다.**

Deployment를 apply하면 무슨 일이 일어나는지 되짚어 보자. API 서버는 Deployment를 검증해서 etcd에 저장한다. 그것으로 끝이다. 그다음 **Deployment 컨트롤러** 가 그것을 watch하다가 ReplicaSet을 만든다. 이번엔 **ReplicaSet 컨트롤러** 가 ReplicaSet을 watch하다가 Pod를 만든다. 그리고 **스케줄러** 가 노드가 배정되지 않은 Pod를 watch하다가 노드를 배정하고, **kubelet** 이 자기 노드에 배정된 Pod를 watch하다가 컨테이너를 띄운다. 어디에도 "누가 누구를 직접 호출한다"가 없다. 전부 **API 서버에 쓰고, 상대는 그걸 읽고 반응하는** 구조다.

```mermaid
flowchart TB
    subgraph core["코어 리소스"]
        d["Deployment<br>spec: replicas 3"] -->|"Deployment controller"| rs["ReplicaSet"]
        rs -->|"ReplicaSet controller"| po["Pod × 3"]
    end
    subgraph custom["커스텀 리소스"]
        cr["Database<br>spec: version, storageSize"] -->|"Database operator"| sts["StatefulSet<br>+ Service + Secret"]
        sts -->|"StatefulSet controller"| po2["Pod × N"]
    end
    style d fill:#1565C0,color:#fff
    style cr fill:#6A1B9A,color:#fff
    style po fill:#2E7D32,color:#fff
    style po2 fill:#2E7D32,color:#fff
```

두 체인은 원하는 상태를 API에 기록하고 별도 제어 루프가 이를 관찰한다는 점에서 닮았다. 하지만 Deployment는 Kubernetes에 내장된 built-in API이고, `Database`는 CRD로 추가한 타입이다. API의 구현·버전 관리·설치와 업그레이드 책임도 다르다. 단순히 컨트롤러의 실행 위치 하나만 다른 것은 아니다.

따라서 처음의 질문에 대한 답은 도구의 일관성에 있다. 둘 다 Kubernetes API의 조회·watch·RBAC·metadata 규약을 사용하므로 `kubectl`에서는 비슷하게 다룰 수 있다. 그렇다고 Deployment가 CRD이거나 모든 리소스가 같은 컨트롤러로 처리되는 것은 아니다. Deployment의 소유 관계는 [ReplicaSet·Deployment](Kubernetes-ReplicaSet-Deployment.md)에서 배운 그대로다.

실물로 확인하고 싶다면 [Tekton의 Pipeline과 PipelineRun은 왜 따로 존재할까](Tekton의-Pipeline과-PipelineRun은-왜-따로-존재할까.md)를 보라. Tekton의 `Pipeline`·`Task`·`PipelineRun`은 전부 CRD로 만들어진 타입이고, 그 YAML이 실제 Pod와 컨테이너로 내려가는 것은 Tekton 컨트롤러가 하는 일이다. `kubectl get pipelineruns`가 `kubectl get deployments`와 똑같이 동작하는 이유가 이 절의 내용이다.

---

## 5. spec과 status의 분리 — 누가 쓰는 칸인가

컨트롤러가 등장하면 새로운 문제가 생긴다. 사용자와 컨트롤러가 **같은 객체를 동시에 쓴다.** 사용자는 "원하는 상태"를 쓰고 싶고, 컨트롤러는 "관찰한 결과"를 쓰고 싶다. 이 둘이 한 칸에 섞이면 서로를 덮어쓴다.

그래서 쿠버네티스 API 규약은 처음부터 객체를 두 칸으로 나눴다. `spec`은 **사람이 쓰는 칸**, `status`는 **컨트롤러가 쓰는 칸** 이다. API 규약 문서는 권한 경계까지 못 박는다.

사용자는 spec을 쓰고 status를 읽으며, 관련 컨트롤러는 spec을 읽고 status를 쓸 수 있게 권한을 나누는 것이 API 규약의 의도다.

CRD에서 이 분리를 실제로 강제하는 장치가 **status 서브리소스** 다. 앞의 CRD 예제에 있던 `subresources: { status: {} }` 한 줄이 그것이고, 켜면 세 가지가 달라진다.

첫째, `/status`라는 **별도 엔드포인트** 가 생긴다. 이는 RBAC에서 `databases/status`라는 독립적인 대상이 되므로, "컨트롤러 ServiceAccount에는 status 쓰기만, 사용자에게는 spec 쓰기만" 같은 권한 분리가 가능해진다. (RBAC 문법과 ServiceAccount는 [Kubernetes ServiceAccount, RBAC](Kubernetes-ServiceAccount-RBAC.md)에서 다룬다.)

둘째, **덮어쓰기가 구조적으로 차단된다.** 공식 문서의 규칙이 명확하다 — 메인 리소스로 오는 `PUT`/`POST`/`PATCH` 요청은 `status` 변경을 무시하고, `/status`로 오는 `PUT` 요청은 `status` 외의 모든 변경을 무시한다. 메인 endpoint의 status 변경은 무시되고, `/status`를 통한 spec 변경도 무시된다. 다만 메인 리소스 write 권한을 가진 컨트롤러는 그 endpoint로 spec을 바꿀 수 있다. 실질적인 쓰기 권한 분리는 `databases` 읽기와 `databases/status` 쓰기를 나눈 RBAC으로 완성한다.

셋째, `.metadata.generation`의 증가 규칙이 쓸모 있어진다. 규칙은 이렇다.

> The `.metadata.generation` value is incremented for all changes, except for changes to `.metadata` or `.status`.

즉 **spec이 바뀔 때만 `generation`이 오른다.** 이것이 실무에서 꽤 중요한 필드 하나를 가능하게 한다.

스키마와 endpoint는 함께 설계해야 한다. 처음 CRD에는 `status.phase`와 `status.observedGeneration`의 타입도 선언했다. `/status`를 켜는 것만으로 임의의 status 필드가 보존되는 것은 아니다. 구조적 스키마에 없는 필드는 pruning 대상이 될 수 있기 때문이다. 컨트롤러가 `phase`를 썼는데 조회 시 사라진다면, 루프가 멈췄다고 단정하기 전에 스키마와 status update의 응답을 확인한다.

아래는 컨트롤러가 기록할 수 있는 관찰 결과의 구조 설명용 발췌다. 사용자가 apply할 실행 지시가 아니다.

```yaml
metadata:
  generation: 7
spec:
  version: '17'
  storageSize: 20Gi
status:
  observedGeneration: 7
  phase: Upgrading
```

여기서는 7세대를 읽었지만 아직 업그레이드 중이다. `observedGeneration`은 영수증의 역할을 하고, `phase`는 그 세대의 처리 결과를 말한다. 실제 Operator는 보통 Ready·Progressing·Degraded 같은 Condition과 이유·메시지를 더 제공한다. 그 필드들을 사용할 때도 CRD schema와 컨트롤러의 보고 규약이 일치해야 한다.

### observedGeneration — "컨트롤러가 아직 못 봤다"를 아는 방법

컨트롤러가 `status`에 `observedGeneration`을 기록하는 관행이 여기서 나온다. API 규약의 정의는 "원하는 상태의 변경에 반응할 책임이 있는 컴포넌트가 가장 최근에 관찰한 `generation`"이다.

이게 왜 필요한지는 아주 흔한 상황에서 드러난다. `Database`의 `spec.version`을 16에서 17로 바꾸고 바로 status를 봤다고 하자. `status.phase: Ready`가 찍혀 있다. 업그레이드가 벌써 끝난 걸까? 아니다. **컨트롤러가 아직 내 변경을 못 봤을 뿐** 이고, 그 `Ready`는 바꾸기 **전** 상태에 대한 보고다.

```bash
$ kubectl get database orders-db -n bookstore -o jsonpath='{.metadata.generation}{"\t"}{.status.observedGeneration}'
7	6      # spec은 7세대인데 컨트롤러는 6세대까지만 봤다 → status는 아직 옛 이야기
```

두 숫자가 같으면 현재 세대를 관찰했다는 의미다. 처리 성공은 별개이므로 현재 세대의 `phase` 또는 Ready Condition도 함께 읽어야 한다. 이 규약이 없다면 "적용이 끝났는지"를 판단할 방법이 없어, 배포 자동화가 옛 상태를 보고 성공을 선언하게 된다.

---

## 6. finalizer — 리소스를 지웠는데 사라지지 않는다

다음 함정은 삭제에서 나온다. 컨트롤러가 만든 것이 클러스터 안에만 있는 게 아닐 수 있다. 클라우드 로드밸런서, 외부 DNS 레코드, S3의 백업 파일 같은 것들이다. 그렇다면 `Database` 객체가 지워지는 순간 그것들은 누가 치우는가? 객체가 이미 사라졌다면 컨트롤러는 무엇을 치워야 할지조차 알 수 없다.

그래서 쿠버네티스는 **삭제를 두 단계로 나눈다.** `metadata.finalizers`에 키가 하나라도 있으면, 삭제 요청은 **즉시 삭제가 아니라 "삭제 예약"** 이 된다.

다음 명령과 출력은 삭제가 보류된 상황을 보여 주는 설명용 예시다. 실제 실행 기록이 아니다. YAML의 필드 순서에 기대지 않고 필요한 metadata 필드를 직접 조회한다.

```bash
$ kubectl delete database orders-db -n bookstore --wait=false
database.example.com "orders-db" deleted   # 메시지는 이렇게 나오지만

$ kubectl get database orders-db -n bookstore -o jsonpath='deletionTimestamp={.metadata.deletionTimestamp}{"\n"}{range .metadata.finalizers[*]}finalizer={.}{"\n"}{end}'
deletionTimestamp=2026-07-28T09:14:22Z
finalizer=example.com/cleanup-backups
```

삭제 예약 시각이 찍혔어도 이 finalizer 키가 남아 있는 동안은 객체가 사라지지 않는다.

공식 문서의 설명은 이렇다. finalizer가 있는 객체에 대한 첫 삭제 요청은 `metadata.deletionTimestamp`를 채우지만 객체를 지우지 않는다. 그 값이 설정되면 `finalizers` 목록에서는 **항목을 제거할 수만 있다**(추가는 불가). 그리고 `deletionTimestamp`를 본 컨트롤러가 자기가 담당하는 finalizer의 정리 작업을 수행하고, 끝나면 목록에서 자기 키를 뺀다. **목록이 비면 그때 쿠버네티스가 실제로 객체를 삭제한다.**

정상 동작은 이렇다. 삭제 요청 → `deletionTimestamp` 찍힘 → 컨트롤러가 마지막 백업을 뜨고 클라우드 리소스를 정리 → 자기 finalizer 제거 → 객체 소멸. finalizer는 삭제 완료를 보류하는 장치다. 정리가 실제로 성공하는지, 중간 실패를 재시도하는지, 중복 정리가 안전한지는 컨트롤러와 외부 API의 구현에 달려 있다.

### 실무 함정: 컨트롤러가 죽은 상태에서 지우면 영원히 Terminating

문제는 그 finalizer를 뗄 주체가 컨트롤러라는 점이다. **컨트롤러가 죽어 있거나 이미 삭제된 상태에서 리소스를 지우면, 뗄 사람이 없으므로 객체는 영원히 `Terminating`에 갇힌다.** 오퍼레이터를 uninstall한 뒤에 남은 커스텀 리소스를 정리하려다 이 상황에 빠지는 것이 가장 흔한 시나리오다. 네임스페이스 하나가 통째로 `Terminating`에서 안 내려가는 사건의 원인도 대개 그 안의 어떤 리소스에 남은 finalizer다.

여기서 반드시 알아야 할 사실이 있다. **`--force`로는 통과하지 못한다.** 공식 문서의 문장이다.

> While any finalizers remain it is also impossible to force the deletion of an object.

`kubectl delete --force --grace-period=0`은 Pod의 graceful 종료 대기를 건너뛰는 옵션이지, finalizer를 무시하는 옵션이 아니다. 두 개는 전혀 다른 메커니즘이고, 흔히 뒤섞여 쓰인다.

컨트롤러와 외부 API 권한을 복구해 정상 정리를 재개하는 것이 우선이다. 아래 finalizer 수동 제거는 정리를 다른 방법으로 끝냈거나 잔여 리소스의 책임을 확인한 경우에만 검토하는 최후의 수단이다.

```bash
# 최후의 수단 — 무엇을 포기하는지 알고 써야 한다
kubectl patch database orders-db -n bookstore -p '{"metadata":{"finalizers":[]}}' --type=merge
```

이 명령이 하는 일을 정확히 이해해야 한다. 이건 "정리를 완료했다고 통보하는" 것이 아니라 **"정리를 하지 않기로 결정하는" 것** 이다. 컨트롤러가 하려던 일 — 마지막 백업, 클라우드 로드밸런서 해제, 외부 DNS 레코드 삭제, 볼륨 스냅샷 — 이 전부 실행되지 않은 채 객체만 사라진다. 결과는 **아무도 소유권을 주장하지 않는 고아 리소스** 이고, 클라우드 리소스라면 조용히 과금이 계속된다. 쿠버네티스 문서가 이 행동에 경고를 붙인 이유다 — finalizer는 이유가 있어서 붙었으므로, 그 목적을 이해하고 **다른 방법으로 정리를 마쳤을 때만** 강제로 떼라.

그래서 올바른 순서는 이것이다. 먼저 컨트롤러를 되살려서 스스로 정리하게 하고, 그게 불가능하면 클라우드 콘솔에서 해당 리소스를 사람이 직접 지운 뒤, 그다음에 finalizer를 뗀다.

---

## 7. Operator = CRD + 컨트롤러 + 도메인 운영 지식

지금까지의 재료를 조립하면 Operator가 나온다. 공식 문서의 정의는 간결하다.

Operator는 custom resource로 애플리케이션과 구성 요소를 관리하며 Kubernetes의 control loop 원칙을 따르는 소프트웨어 확장이다.

그런데 왜 이런 것이 필요한가. 이 질문은 StatefulSet의 경계를 보면 선명해진다.

데이터베이스를 쿠버네티스에 올린다고 하자. [StatefulSet](Kubernetes-StatefulSet.md)은 Pod에 **안정적인 이름과 순서, 그리고 각자의 디스크** 를 준다. 여기까지는 훌륭하다. 그런데 실제 운영에서 필요한 것들을 떠올려 보라.

primary가 죽었을 때 세 replica 중 **어느 것을 primary로 승격** 해야 하는가? 복제 지연이 가장 적은 것을 골라야 하는데, 그 판단 기준은 그 데이터베이스의 복제 프로토콜에 있다. 백업은 **언제 어떤 방식으로** 떠야 하는가? 물리 백업인지 논리 백업인지, WAL을 어디까지 보관해야 하는지는 그 소프트웨어의 사정이다. 메이저 버전 업그레이드는 **어떤 순서로** 해야 하는가? replica를 먼저 올리고 primary를 나중에 올려야 하는지, 스키마 마이그레이션을 어느 시점에 끼워야 하는지도 마찬가지다.

**쿠버네티스는 이것을 알 수 없다.** 알아서도 안 된다. 이건 특정 소프트웨어의 도메인 지식이고, 쿠버네티스가 세상의 모든 데이터베이스의 승격 규칙을 코어에 담을 수는 없다. 그래서 지금까지 이 일은 사람이 했다 — 위키에 적힌 런북(runbook)을 보고, 새벽에 호출을 받아, 손으로 명령을 쳤다.

**Operator는 그 런북을 컨트롤러 코드로 옮긴 것이다.** 공식 문서가 이를 사람 운영자(SRE) 비유로 설명하는 이유다 — 특정 애플리케이션을 돌보는 사람은 "이 시스템이 어떻게 동작해야 하는지, 어떻게 배포하고, 문제가 생기면 어떻게 반응해야 하는지"에 대한 깊은 지식을 갖고 있고, Operator 패턴은 그 지식을 코드로 포착한다. 문서가 드는 예가 정확히 런북의 항목들이다 — 온디맨드 배포, 백업과 복원, 애플리케이션 코드와 DB 스키마의 동시 업그레이드, 실패 시뮬레이션, 그리고 **분산 애플리케이션의 리더 선출**.

### Operator Capability Level — 어디까지 자동화했는가

Operator라고 다 같은 수준이 아니다. Operator Framework는 성숙도를 5단계로 정의한다. 각 단계는 누적적이다.

| Level | 이름 | 자동화한 것 |
|-------|------|-------------|
| **I** | Basic install | 애플리케이션 프로비저닝과 설정 관리 자동화 |
| **II** | Seamless Upgrades | 패치·마이너 버전 업그레이드 지원 |
| **III** | Full lifecycle | 앱·스토리지 수명주기 — 백업, 장애 복구 |
| **IV** | Deep Insights | 메트릭, 알림, 로그 처리, 워크로드 분석 |
| **V** | Auto Pilot | 수평·수직 스케일링, 설정 자동 튜닝, 이상 감지, 스케줄링 튜닝 |

이 표를 읽는 법은 "몇 레벨이 좋다"가 아니다. **오퍼레이터를 도입할 때 "우리가 런북에서 지우고 싶은 항목이 몇 레벨에 있는가"를 확인하는 체크리스트** 로 쓰는 것이다. 설치만 자동화된 Level I 오퍼레이터를 도입하고 "이제 백업도 알아서 되겠지"라고 기대하면 사고가 난다.

> 어떤 Database Operator들이 있는지, 그리고 "StatefulSet을 직접 관리할까 vs Operator를 쓸까"의 판단 기준은 [Kubernetes StatefulSet의 8절](Kubernetes-StatefulSet.md#8-database-operator가-맡는-별도의-문제)에서 상세히 다룬다.

---

## 8. CRD가 안 맞는 자리 — Aggregated API Server

CRD가 만능은 아니다. 공식 문서는 쿠버네티스 API를 확장하는 방법이 **두 가지** 라고 명시하고, 그 둘을 쉬움과 유연함의 트레이드오프로 배치한다.

CRD는 별도 API 서버 코드 없이 타입을 등록하기 쉽고, API Aggregation은 직접 구현하는 부담 대신 저장·변환·응답 동작을 더 세밀하게 제어할 수 있다.

CRD는 **etcd에 저장되는 선언적 리소스** 에 맞는다. 개수가 적고, 크기가 작고, 자주 바뀌지 않고, 사람이 읽고 쓰며, 동작이 CRUD에 가까운 것들이다. 반대로 이런 경우에는 CRD로 안 된다 — **저장을 직접 통제해야 하거나**(자체 백엔드, 또는 대량·고빈도 데이터), **응답을 저장된 값이 아니라 그때그때 계산해서 만들어야 하는** 경우다. etcd는 그런 용도로 설계되지 않았고, 문서도 애플리케이션 데이터를 커스텀 리소스에 담지 말라고 명시적으로 경고한다.

그럴 때 쓰는 것이 **Aggregation Layer** 다. `APIService` 객체를 등록해 API 경로의 일부를 "찜"하면, `kube-apiserver`가 그 경로로 오는 요청을 **외부 서비스로 프록시** 한다. 사용자 입장에서는 그냥 쿠버네티스 API가 넓어진 것처럼 보인다.

| | CRD | Aggregated API (`APIService`) |
|---|-----|------------------------------|
| 구현 비용 | YAML 하나, 코딩 불필요 | API 서버를 직접 구현해 운영해야 한다 |
| 저장 | API 서버가 etcd에 저장 | 무엇을 어디에 저장할지(혹은 저장하지 않을지) 자유 |
| 응답 | 저장된 값을 돌려준다 | 요청 시점에 계산해서 만들 수 있다 |
| 적합한 것 | 선언적 설정 리소스 | 계산형·비영속 API, 버전 변환 세밀 제어 |

이 방식의 대표 사례가 **Metrics API** 다. `kubectl top`이 보여주는 숫자는 etcd에 저장된 값이 아니라 그 순간 수집·집계된 값이라, 애초에 CRD로 표현할 수 없다. 그래서 metrics-server는 `APIService`로 등록된 aggregated API로 구현된다. 이 파이프라인의 상세는 [Kubernetes Metrics Server, Prometheus](Kubernetes-Metrics-Server-Prometheus.md)에서 다룬다.

---

## 9. 실무 함정들

**CRD는 클러스터 스코프다.** 공식 문서의 표현대로 "CustomResourceDefinitions themselves are non-namespaced and are available to all namespaces". `spec.scope: Namespaced`는 **그 타입의 인스턴스** 가 네임스페이스에 속한다는 뜻이고, CRD 자체는 클러스터 전역이다. 결과는 이렇다 — 두 팀이 같은 오퍼레이터의 다른 버전을 원하면 **CRD 하나를 두고 충돌한다.** 네임스페이스로 격리할 수 없다. 한쪽이 CRD를 업그레이드하면 다른 쪽 리소스의 스키마도 함께 바뀐다. 멀티테넌트 클러스터에서 오퍼레이터 도입을 클러스터 관리자 승인 사항으로 두는 이유다.

**CRD를 삭제하면 그 타입의 모든 커스텀 리소스가 함께 삭제된다.** API에 저장된 해당 객체들을 제거하는 작업이다. 공식 문서는 다음처럼 설명한다.

> When you delete a CustomResourceDefinition, the server will uninstall the RESTful API endpoint and delete all custom objects stored in it.

그리고 "나중에 같은 CRD를 다시 만들면 비어 있는 상태로 시작한다"고 덧붙인다. 즉 CRD만 재등록해도 예전 객체가 돌아오지는 않는다. 복구에는 CR 백업·외부 데이터와 복원 절차가 별도로 필요하다. `kubectl delete crd databases.example.com` 한 줄이 클러스터의 모든 `Database` 객체를 지운다. 오퍼레이터를 정리할 때 순서가 중요한 이유가 이것이다.

**Chart의 `crds/` 디렉터리로 설치한 CRD는 오퍼레이터를 `helm uninstall`해도 남는다.** 이건 버그가 아니라 **의도된 안전장치** 다. Helm은 `crds/` 디렉터리의 CRD를 install 시점에만 설치하고 일반 upgrade·uninstall로 관리하지 않는다. `templates/` 등에서 렌더되어 Release manifest로 관리되는 CRD에 같은 보존을 가정하면 안 된다. 공식 문서의 표현은 "There is no support at this time for upgrading or deleting CRDs using Helm"이고, 그 이유를 "의도치 않은 데이터 손실의 위험 때문에 커뮤니티 논의를 거친 명시적 결정"이라고 밝힌다. 바로 위 함정과 이어 읽으면 납득이 된다 — CRD 삭제는 그 타입의 모든 데이터를 지우는 행동인데, `helm uninstall`의 부수 효과로 그런 일이 일어나면 안 된다. 대신 오퍼레이터를 완전히 걷어낼 때는 CRD를 사람이 명시적으로 지워야 한다는 부담이 남는다. (Helm의 릴리스 모델은 [Helm — 쿠버네티스의 패키지 매니저는 왜 필요한가](Helm-쿠버네티스의-패키지-매니저는-왜-필요한가.md)에서 다룬다.)

**컨트롤러는 넓은 RBAC을 요구한다.** 컨트롤러는 자기 CR뿐 아니라 **그것으로부터 만드는 모든 리소스** 에 대한 권한이 필요하다. `Database` 오퍼레이터라면 StatefulSet·Service·Secret·PVC에 대한 생성·수정·삭제 권한을 전부 요구하고, 대상 네임스페이스를 한정할 수 없으면 ClusterRole로 올라간다. 즉 **오퍼레이터 설치는 상당한 권한을 클러스터에 상주시키는 결정** 이다. 권한 설계는 [Kubernetes ServiceAccount, RBAC](Kubernetes-ServiceAccount-RBAC.md)에서 다룬다.

**검증은 사다리로 생각하라.** "스키마로 안 되면 웹훅"이 아니다. 세 단계다. 먼저 **구조적 스키마** 로 타입·필수 필드·범위를 잡고, 그것으로 부족하면 **CEL 검증 규칙**(`x-kubernetes-validations`)을 스키마 안에 직접 넣는다 — `self.minReplicas <= self.replicas` 같은 필드 간 규칙을 웹훅 없이 표현할 수 있고, **v1.29에서 stable** 이 됐다. 쿠버네티스가 이 기능을 만든 목표 자체가 "예전에 웹훅을 만들어야 했던 검증 사례의 대다수를 흡수하는 것"이었다. 그래도 남는 것 — 클러스터 밖 상태를 조회해야 하거나, 다른 객체와 교차 검증해야 하는 경우 — 에만 **검증 웹훅** 을 꺼낸다. 웹훅의 동작 방식은 [Kubernetes Admission Webhook](Kubernetes-Admission-Webhook.md)에서 다룬다.

**여러 버전을 공존시킬 때는 `served`와 `storage`를 구별하라.** CRD의 `spec.versions`에서 `served`는 "이 버전의 엔드포인트를 열어 둘 것인가"이고, `storage`는 "etcd에 저장할 때 어떤 버전으로 쓸 것인가"다. **`storage: true`는 정확히 하나만** 가능하다. `v1alpha1`과 `v1`을 동시에 서비스하면 API 서버는 저장 버전과 요청 버전 사이를 변환해야 하는데, 필드 이름이 그대로인 경우는 문제없지만 구조가 바뀌었으면 **conversion webhook** 을 등록해 변환을 직접 구현해야 한다. 오퍼레이터 업그레이드 시 리소스가 깨지는 사고의 흔한 원인이라, 다중 버전 CRD는 처음부터 변환 전략을 정하고 시작하는 게 좋다.

---

## 정리

### 핵심 포인트

1. **API 서버는 저장하고, 컨트롤러가 의미를 부여한다**
   - CRD를 apply하면 새 엔드포인트·스키마 검증·kubectl·RBAC·watch가 생긴다. 하지만 커스텀 리소스를 만들어도 **DB나 Pod가 자동 생성되지는 않는다.** CRD는 스키마가 있는 저장소일 뿐이고, 그것을 보고 움직이는 컨트롤러가 붙어야 실체가 생긴다.

2. **코어 리소스도 완전히 같은 구조다 — 이게 이 글의 결론**
   - Deployment 컨트롤러가 ReplicaSet을 만들고, ReplicaSet 컨트롤러가 Pod를 만든다. CRD + 컨트롤러는 예외적 확장 기법이 아니라 **쿠버네티스가 자기 자신을 만드는 방식** 이다. 동일한 reconcile 원리를 사용하지만 built-in API와 CRD의 등록·구현·업그레이드 책임은 다르다.

3. **level-triggered가 신뢰성의 근원이고, 그 대가가 멱등성이다**
   - 컨트롤러는 "무슨 이벤트가 왔는가"가 아니라 **"지금 상태가 어떤가"** 를 본다. 공식 설계 원칙은 "edge-triggered 동작은 최적화일 뿐"이라고 못 박는다. 그래서 이벤트를 놓쳐도, 컨트롤러가 재시작돼도, 누가 리소스를 손으로 지워도 다음 루프에서 복구된다. 대신 reconcile은 **몇 번 불려도 같은 결과** 여야 한다.

4. **spec은 사람이, status는 컨트롤러가 쓴다**
   - status 서브리소스로 분리하면 권한을 나눌 수 있고 서로 덮어쓰지 않는다. `spec`이 바뀔 때만 `metadata.generation`이 오르므로, `status.observedGeneration`과 비교해 **컨트롤러가 내 변경을 봤는지** 판별할 수 있다.

5. **finalizer는 삭제를 두 단계로 나눈다 — 그리고 `--force`로는 못 뚫는다**
   - finalizer가 남아 있으면 객체는 `deletionTimestamp`만 찍힌 채 `Terminating`에 머문다. 컨트롤러가 죽어 있으면 영원히 갇힌다. `finalizers`를 손으로 비우는 것은 "정리가 끝났다"가 아니라 **"정리를 하지 않기로 결정하는"** 행동이고, 고아 클라우드 리소스가 남는다.

6. **Operator는 런북을 컨트롤러 코드로 옮긴 것이다**
   - StatefulSet은 안정적인 이름·순서·디스크까지만 준다. primary 승격, 백업 시점, 업그레이드 순서는 그 소프트웨어의 도메인 지식이라 쿠버네티스가 알 수 없다. Capability Level(설치 → 업그레이드 → 백업·복구 → 심층 인사이트 → 자동 파일럿)은 "우리 런북에서 지우고 싶은 항목이 몇 레벨인가"를 확인하는 체크리스트로 쓴다.

---

## 생각해 볼 질문

1. **Database가 created인데 StatefulSet은 없다. 생성이 실패했을까?** API 저장 성공과 실행 처리는 별개다. CRD만 등록했는지, 해당 CR을 관찰하는 컨트롤러가 실행 중인지, watch 범위와 RBAC은 맞는지 차례로 확인한다.
2. **observedGeneration이 generation과 같은데 phase가 Failed다. 성공이라고 봐도 될까?** 현재 요청을 관찰했다는 뜻일 뿐이다. 현재 세대의 phase·Condition·이유를 읽어야 처리 성공을 판단할 수 있다.
3. **status subresource를 켜면 컨트롤러는 spec을 절대 수정하지 못할까?** endpoint별 필드 처리는 나뉘지만 메인 리소스 write 권한이 있으면 spec을 수정할 수 있다. RBAC도 목적에 맞게 나눠야 한다.

다음 [Admission Webhook](Kubernetes-Admission-Webhook.md)은 컨트롤러가 저장된 선언을 처리하기 전, API 요청 자체를 수정하거나 거절하는 자리를 설명한다. 외부 비밀을 Secret으로 만드는 실제 Operator 사례는 [ESO](Kubernetes-External-Secrets-Operator.md)에서 이어 읽을 수 있다.

## 출처

- [Custom Resources | Kubernetes](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/) — 공식 문서. CRD vs Aggregated API 비교, "custom resources let you store and retrieve structured data" 원문, 선언적 API의 책임 분리
- [Extend the Kubernetes API with CustomResourceDefinitions | Kubernetes](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/) — 공식 문서. `apiextensions.k8s.io/v1`, 구조적 스키마 필수화, CRD는 non-namespaced, CRD 삭제 시 모든 커스텀 객체 삭제, `served`/`storage`, status 서브리소스와 `.metadata.generation` 규칙, finalizer 동작, CEL 검증 규칙(v1.29 stable)
- [Kubernetes Controllers | Kubernetes](https://kubernetes.io/docs/concepts/architecture/controller/) — 공식 문서. 제어 루프와 온도조절기 비유, Job 컨트롤러가 Pod를 직접 실행하지 않는다는 설명, 컨트롤러를 컨트롤 플레인 밖에서 실행하기
- [Finalizers | Kubernetes](https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/) — 공식 문서. `deletionTimestamp`, `Terminating`, finalizer를 손으로 제거하지 말라는 경고
- [Operator pattern | Kubernetes](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) — 공식 문서. Operator 정의, 사람 운영자(SRE) 비유, 백업·업그레이드·리더 선출 등 자동화 대상
- [Kubernetes API Aggregation Layer | Kubernetes](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/) — 공식 문서. `APIService` 등록과 프록시, metrics-server 사례
- [Kubernetes API Conventions (sig-architecture)](https://github.com/kubernetes/community/blob/master/contributors/devel/sig-architecture/api-conventions.md) — 공식 규약. spec/status 분리와 권한 경계, level-based 동작, `metadata.generation`과 `status.observedGeneration`
- [Kubernetes Design Principles](https://github.com/kubernetes/design-proposals-archive/blob/main/architecture/principles.md) — 공식 설계 원칙(아카이브). "Functionality must be level-based... Edge-triggered behavior must be just an optimization"
- [Operator Capabilities | Operator Framework](https://operatorframework.io/operator-capabilities) — Capability Level I~V 정의
- [Custom Resource Definitions | Helm Docs](https://helm.sh/docs/chart_best_practices/custom_resource_definitions/) — `crds/` 디렉터리, Helm이 CRD를 업그레이드·삭제하지 않는 이유
- [Kubernetes 1.25: CRD Validation Rules Graduate to Beta](https://kubernetes.io/blog/2022/09/23/crd-validation-rules-beta/) — CEL 검증 규칙이 웹훅을 대체하는 배경
