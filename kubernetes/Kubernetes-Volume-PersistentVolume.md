# Kubernetes Volume과 Persistent Storage

> **개발자를 위한 쉬운 쿠버네티스 · 14장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-Ingress-vs-Egress.md) · [다음 장](./Kubernetes-StatefulSet.md)

주문 API가 업로드 파일을 `/data`에 저장했다고 하자. 응답까지 성공했는데 새 버전으로 Pod를 교체하자 파일이 보이지 않는다. 프로세스를 다시 띄우는 일과 데이터를 다시 연결하는 일은 서로 다른 문제다. 앞에서 배운 [Pod](Kubernetes-Pod.md)와 [Deployment](Kubernetes-ReplicaSet-Deployment.md)는 실행을 복구하지만, 어떤 저장소를 다시 사용할지는 별도로 선언해야 한다.

## 결론부터 말하면

Volume은 컨테이너에 저장 공간을 연결하는 Pod의 선언이다. 그중 `emptyDir`은 같은 Pod 안의 컨테이너 재시작을 넘어 살아 있고, PVC를 참조하는 Volume은 Pod 교체를 넘어 유지되는 저장소를 연결할 수 있다. PV는 실제 저장소를 Kubernetes에서 표현하는 클러스터 범위의 오브젝트, PVC는 이를 요청하는 namespace 범위의 오브젝트다.

그러나 PVC가 `Bound`라는 사실은 연결할 저장소가 정해졌다는 뜻이다. Node 연결, 파일시스템 mount, 앱의 쓰기 성공, 백업으로부터의 복구 성공은 그다음에 각각 확인해야 한다.

| 확인한 사실 | 아직 답하지 못한 질문 |
|---|---|
| PVC가 Bound다 | Node와 컨테이너에 mount되었는가? |
| 컨테이너에 mount되었다 | 앱 UID의 권한으로 쓰고 다시 읽을 수 있는가? |
| 앱이 데이터를 썼다 | Pod 교체 후 같은 저장소를 참조하는가? |
| VolumeSnapshot이 준비되었다 | DB가 일관된 상태로 복구되고 앱이 읽을 수 있는가? |

## 1. 무엇의 수명보다 오래 살아야 하는가

컨테이너 이미지의 파일은 읽기 전용 계층에 있고, 실행 중 변경은 각 컨테이너의 writable layer에 기록된다. Kubernetes에서 컨테이너가 crash하여 kubelet이 새 인스턴스를 시작할 때 이 계층의 보존에 의존해서는 안 된다. 같은 Pod 안의 컨테이너 재시작이어도 새 컨테이너는 깨끗한 상태로 출발한다. Docker의 특정 `restart` 명령 동작을 Kubernetes의 복구 계약으로 옮겨 생각하면 이 경계를 놓친다. [Volumes 공식 문서](https://kubernetes.io/docs/concepts/storage/volumes/)가 Volume을 도입하는 이유도 이 문제다.

그렇다고 모든 데이터에 영구 디스크가 필요한 것은 아니다. 다운로드 중인 임시 파일이나 다시 만들 수 있는 캐시는 컨테이너 재시작까지만 견디면 될 수 있다. `emptyDir`은 Pod가 Node에 배치될 때 마련되는 빈 디렉터리이며, 같은 Pod의 여러 컨테이너가 공유할 수 있다. 컨테이너 하나가 crash해도 남지만 Pod가 제거되면 해당 데이터도 사라진다. 교체 Pod는 이름이나 label이 같아도 다른 Pod이므로 새 `emptyDir`을 받는다.

다음은 관계를 설명하는 가상 주문 API다. `bookstore` namespace가 있다고 가정하며 `registry.example.com/book/order-api:1.0.0`과 `/data`, `/scratch`에 파일을 쓰는 앱 동작은 설명용 계약이다. 공개 실습 이미지가 아니므로 그대로 실행 성공을 기대하는 예제는 아니다.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: order-api
  namespace: bookstore
  labels:
    app: order-api
spec:
  containers:
  - name: order-api
    image: registry.example.com/book/order-api:1.0.0
    ports:
    - containerPort: 8080
    volumeMounts:
    - name: scratch
      mountPath: /scratch
  volumes:
  - name: scratch
    emptyDir: {}
```

`volumeMounts`는 컨테이너 내부의 경로를 정하고, `volumes`는 그 이름에 어떤 저장 공간을 연결할지 정한다. 두 곳의 `name`이 연결점이다. 앱과 로그 전송 컨테이너가 같은 `emptyDir`을 서로 다른 경로로 mount하는 것도 가능하다. Init Container가 준비한 파일을 앱에 넘길 때도 같은 구조를 쓴다.

`emptyDir.medium: Memory`를 선택하면 메모리 기반 공간이 된다. 디스크 I/O를 피할 수 있지만 쓴 데이터가 메모리 회계에 들어가므로 무제한 임시 저장소처럼 쓰면 안 된다. 일반 `emptyDir`도 Node의 디스크 여유와 ephemeral-storage 관리에서 자유롭지 않다.

### Node의 경로를 연결하면 영구 저장소인가

`hostPath`는 Node의 파일시스템 경로를 컨테이너에 노출한다. Node의 파일은 Pod가 사라진 뒤에도 남을 수 있지만, 다른 Node로 이동한 Pod가 그 파일을 받는다는 뜻은 아니다. 같은 `/data`라는 문자열도 Node가 다르면 다른 디스크다.

로그 수집기나 Node 에이전트처럼 호스트를 관찰해야 하는 프로그램에는 정당한 용도가 있다. 이 경우에도 읽기 전용 mount, 필요한 경로와 권한의 제한, Node 디스크 사용 관리는 필요하다. 일반 API의 사용자 파일을 보존하기 위해 임의의 `hostPath`를 쓰면 배치 위치와 데이터 위치를 운영자가 직접 맞춰야 한다. 뒤의 [DaemonSet](Kubernetes-DaemonSet-Job-CronJob.md)은 이처럼 Node에 붙어야 하는 프로세스의 실행 모델을 설명한다.

## 2. Pod와 저장소의 생명주기를 분리한다

Pod마다 클라우드 볼륨 ID나 NFS 서버 경로를 적으면 앱 배포자가 인프라 세부 사항을 모두 알아야 한다. 개발과 운영의 스토리지도 다르므로 환경을 바꿀 때 Pod 정의가 바뀐다. 이를 분리하는 장치가 PV와 PVC다.

PV에는 용량, 접근 모드, 실제 저장소 연결 정보와 반환 정책이 들어간다. PVC에는 필요한 용량과 접근 모드, 사용할 StorageClass 같은 요구가 들어간다. Pod는 같은 namespace의 PVC 이름을 참조한다. Spring의 인터페이스와 구현 분리를 떠올려도 좋지만, 바인딩은 메서드 호출이 아니라 비동기 controller가 두 오브젝트의 상태를 맞추는 과정이다. 요구를 분리해도 저장소의 성능·장애 도메인·지원 모드까지 같아지는 것은 아니다.

```mermaid
flowchart LR
    Pod["Pod의 Volume<br>PVC 이름 참조"] --> PVC["PVC<br>namespace의 저장소 요청"]
    PVC ---|"1:1 binding"| PV["PV<br>클러스터의 저장소 표현"]
    PV --> Storage["외부 디스크 또는 파일 서버"]
    style Pod fill:#1565C0,color:#fff
    style PVC fill:#2E7D32,color:#fff
    style PV fill:#6A1B9A,color:#fff
    style Storage fill:#455A64,color:#fff
```

PV 자체는 데이터 바이트를 담는 Kubernetes DB가 아니다. 실제 바이트는 외부 디스크나 파일 서버에 있다. etcd에 오브젝트가 보존되었다고 사용자 파일 백업이 만들어지는 것도 아니다.

### 정적 프로비저닝은 이미 있는 저장소를 등록한다

다음은 관리자가 이미 준비한 NFS 서버를 등록하는 별도 인프라 예제다. 서버 주소와 export 경로는 가상이며, 모든 대상 Node에서의 네트워크 접근과 NFS mount 지원, 서버 측 권한이 필요하다. NFS 서버를 생성하는 YAML은 아니다.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: bookstore-nfs
spec:
  storageClassName: ""
  capacity:
    storage: 10Gi
  accessModes: [ReadWriteMany]
  persistentVolumeReclaimPolicy: Retain
  nfs:
    server: 192.0.2.10
    path: /export/bookstore
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: order-files
  namespace: bookstore
spec:
  storageClassName: ""
  volumeName: bookstore-nfs
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 5Gi
```

PVC의 `storageClassName: ""`는 기본 StorageClass를 사용하지 않겠다는 명시적 선택이다. 생략하면 default class가 할당될 수 있어서 class 없는 PV와 맞지 않을 수 있다. `volumeName`은 이번 예제에서 연결하려는 PV를 특정한다. 이 경우에도 class·access modes·capacity는 검사하지만, binding 단계의 node affinity 검사는 우회할 수 있다. 그렇다고 실제 Pod scheduling의 PV node affinity 제약이 사라지는 것은 아니다. 또한 PVC의 `volumeName` 지정과, 다른 PVC가 가져가지 못하도록 PV의 `claimRef`로 예약하는 것은 구분한다.

10Gi PV에 5Gi PVC가 바인딩되어도 남은 5Gi가 별도 PVC에 나뉘어 배정되지는 않는다. PV/PVC의 바인딩은 1:1이다. 실제 파일 서버의 사용량 제한은 Kubernetes에 적은 capacity 숫자만으로 보장되는지도 따로 확인해야 한다.

앞의 Pod에서 `volumes`를 다음처럼 바꾸고 `volumeMounts`도 `name: data`, `mountPath: /data`로 함께 바꾸면 같은 요청을 소비한다. 아래는 Pod 전체가 아니라 해당 필드의 발췌다.

```yaml
volumes:
- name: data
  persistentVolumeClaim:
    claimName: order-files
```

정적 프로비저닝은 레거시라는 뜻이 아니다. 이미 운영 중인 스토리지나 관리자가 명시적으로 배정하는 저장소에는 여전히 의미가 있다.

## 3. StorageClass와 CSI가 실제 저장소를 마련한다

PVC 요청마다 관리자가 PV를 미리 만들기는 번거롭다. 동적 프로비저닝에서는 StorageClass가 provisioner와 생성 정책을 정하고, 이를 감시하는 provisioner가 실제 저장소를 만들고 PV를 등록한다. StorageClass 오브젝트만 생성한다고 해당 드라이버나 스토리지 제품이 설치되는 것은 아니다.

CSI(Container Storage Interface)는 Kubernetes와 스토리지 드라이버가 통신하는 표준 인터페이스다. 예전처럼 벤더의 모든 구현을 Kubernetes 코드에 포함하는 대신 드라이버를 별도로 배포하고 업데이트할 수 있게 한다. Controller 측 기능은 볼륨 생성·삭제·연결 등을, Node 측 기능은 Node에서 사용할 준비와 Pod 경로 노출 등을 담당한다. 모든 드라이버가 같은 기능을 구현하는 것은 아니며 파일 스토리지처럼 별도 attach가 없는 경우도 있다.

다음은 AWS EKS의 standard EBS CSI driver가 설치되고 적절한 IAM 권한이 준비된 경우의 독립 예제다. 앞의 NFS PVC를 이 class로 변환하는 명령은 아니다.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: book-ebs
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  encrypted: "true"
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: order-export
  namespace: bookstore
spec:
  storageClassName: book-ebs
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 20Gi
```

### PVC가 Pending이어도 정상일 수 있다

`WaitForFirstConsumer`는 소비할 Pod의 배치 조건을 알 때까지 provisioning과 binding을 미룬다. 특히 특정 zone에만 붙을 수 있는 디스크를 Pod와 무관한 위치에 먼저 만드는 문제를 줄인다. 따라서 PVC만 만들었을 때 `Pending`인 것을 곧바로 장애라고 판정하지 않는다.

소비 Pod가 생기면 scheduler는 Node 자원, affinity, topology, 저장소 조건을 함께 고려한다. 적합한 Node 후보에 맞춰 볼륨을 마련하고 연결해야 하므로 어느 한쪽 조건이 막혀도 진행되지 않는다. `nodeName`으로 scheduler를 우회하면 이 협조 과정이 일어나지 않아 PVC가 대기할 수 있다. 특정 Node를 원할 때도 scheduler가 처리할 selector/affinity로 표현하는 것이 이 모델에 맞는다. [StorageClass 공식 문서](https://kubernetes.io/docs/concepts/storage/storage-classes/)는 두 binding mode의 전제를 설명한다.

`Immediate`는 consumer를 기다리지 않고 binding/provisioning을 시도한다. 네트워크 파일 스토리지나 topology 제약이 없는 구성에 적합할 수 있으므로 모든 환경에 `WaitForFirstConsumer`를 강제할 이유는 없다.

## 4. 연결 성공을 단계별로 읽는다

실제 진단에서는 PVC와 Pod를 따로 본다. 다음 명령은 독자가 허가받은 환경에서 관찰할 때의 예이며, 여기서 실행해 얻은 결과가 아니다.

```bash
kubectl get pvc -n bookstore
kubectl describe pvc order-files -n bookstore
kubectl describe pod order-api -n bookstore
kubectl get pv bookstore-nfs -o yaml
```

PVC가 `Pending`이면 class 존재, matching PV, provisioner Events, consumer 유무와 scheduler 조건을 먼저 확인한다. `Bound`인데 Pod가 `ContainerCreating`에 머무르면 저장소는 선택되었지만 attach/mount에서 막혔을 수 있다. `FailedAttachVolume`과 `FailedMount`를 같은 오류로 뭉개면 실제 디스크 연결과 Node의 mount 문제를 구분하기 어렵다.

CSI 볼륨이라면 관련 `VolumeAttachment`와 controller/Node plugin 로그가 추가 증거가 될 수 있다. 기존 Node에서 RWO 볼륨이 아직 사용 중인데 새 Node에 붙이려는 상황에서는 기존 인스턴스의 실제 종료와 detach를 확인해야 한다. API에서 Pod를 지웠다는 사실만으로 디스크 사용자가 사라졌다고 판단하지 않는다.

컨테이너가 시작된 뒤에도 앱 UID/GID, 파일 권한, readOnly 설정, 용량·inode 부족으로 쓰기가 실패할 수 있다. mount 성공 뒤의 검증은 앱이 사용하는 경로에서의 쓰기·읽기와 앱 오류를 확인하는 일이다. 데이터가 주문 처리의 일부라면 파일 존재뿐 아니라 DB의 참조와 실제 파일의 대응까지 확인해야 한다.

## 5. 접근 모드와 삭제 정책은 다른 질문이다

### 누가 동시에 연결할 수 있는가

| 접근 모드 | 의미 |
|---|---|
| ReadWriteOnce, RWO | 하나의 Node에서 읽기/쓰기 mount |
| ReadOnlyMany, ROX | 여러 Node에서 읽기 전용 mount |
| ReadWriteMany, RWX | 여러 Node에서 읽기/쓰기 mount |
| ReadWriteOncePod, RWOP | 클러스터에서 하나의 Pod만 읽기/쓰기 mount |

RWO를 단일 Pod 보장으로 해석하면 안 된다. 같은 Node의 여러 Pod가 접근할 수 있으며, RWX가 지원되어도 동시 쓰기의 잠금과 파일 형식 일관성은 앱이 책임진다. RWOP는 Kubernetes 1.29에서 stable이 된 CSI 전용 기능이며, CSI driver와 관련 sidecar의 지원 버전이 필요하다. 접근 모드는 스토리지의 지원 능력과 scheduling/mount 계약을 나타내며 DB transaction이나 쓰기 복제를 대신하지 않는다.

### PVC를 지우면 무엇이 남는가

PV의 reclaim policy는 PVC가 반환된 뒤 저장소를 어떻게 처리할지 정한다. `Delete`는 지원 provisioner가 PV와 외부 저장소를 삭제하는 경로이며, `Retain`은 잔존 데이터의 정리·재사용 결정을 관리자에게 남긴다. 동적 PV는 생성 시 StorageClass의 정책을 이어받으므로 중요한 데이터라면 실제 PV의 정책도 확인한다. 오래된 `Recycle`을 새 운영 설계의 선택지로 쓰지 않는다.

`Retain` PV의 `Released`는 이전 claim이 해제되었다는 상태다. 데이터가 자동으로 초기화되어 다음 사용자에게 넘겨도 된다는 뜻은 아니다. `claimRef`만 제거하면 과거 데이터가 새 claim에 노출될 수 있다. 원래 소유자, 기존 사용자의 실제 종료, 데이터 정리 또는 복구 목적, 백업, 스토리지 관리 절차를 확인한 다음 재배정해야 한다.

PVC가 `Terminating`에 남는 것도 곧바로 고장이 아니다. `kubernetes.io/pvc-protection` 같은 finalizer는 사용 중인 저장소를 삭제하는 사고를 막는다. 같은 이름의 claim이 다른 namespace에도 있을 수 있으므로 사용 Pod를 찾을 때 namespace를 맞춘다.

```bash
kubectl get pods -n bookstore -o json | jq -r \
  '.items[] | select(any(.spec.volumes[]?; .persistentVolumeClaim.claimName == "order-files")) | .metadata.name'
```

사용 Pod를 발견했다고 즉시 삭제하기보다 소유 controller와 중단 영향을 확인한다. finalizer 강제 제거는 데이터 사용자가 없음을 API 목록만으로 추정해 실행할 일반 해결책이 아니다. 담당 controller의 실패 원인과 실제 저장소의 사용·삭제 상태를 확인하고, 보호 절차를 우회할 책임과 복구 방안이 정해진 경우의 제한적 최후 수단이다.

## 6. 심화: 확장, 이동, snapshot은 복구와 연결해서 본다

### PVC 용량 확장

확장을 지원하는 드라이버와 `allowVolumeExpansion: true`인 StorageClass가 전제다. PVC의 요청 용량을 늘리면 저장소 백엔드 확장과 파일시스템 확장이 진행되며, 둘은 같은 순간에 끝나지 않을 수 있다. 온라인 확장 가능 여부도 driver·파일시스템에 달려 있다.

PVC Events/conditions와 실제 mount 경로의 용량을 함께 보아야 한다. `FileSystemResizePending`이면 파일시스템 단계가 남았다는 단서다. 문구 하나만 보고 중요한 DB Pod를 즉시 지우기보다 해당 driver의 지원 절차와 앱의 안전한 재시작 조건을 확인한다. 일반적으로 PVC 축소는 지원하지 않으므로 잘못 늘린 값을 단순히 되돌리는 방식도 피한다.

StatefulSet의 `volumeClaimTemplates`와 이미 생성된 각 PVC는 별개의 오브젝트다. 템플릿 수정만으로 모든 기존 디스크가 커진다고 생각하면 안 된다. 각 claim의 확장 상태와 이후 생성될 claim의 설정을 구분해 관리한다.

### 파일 복사와 데이터 이동

두 PVC를 임시 Pod에 mount하여 `cp`나 `rsync`로 복사하는 것은 일반 파일 이동에 쓸 수 있는 방법이다. 그러나 실행 중인 DB 파일을 복사하면 서로 다른 시점의 데이터 페이지와 로그가 섞일 수 있다. 파일이 모두 복사되었다는 결과는 DB 일관성 증거가 아니다.

이동 계획에는 쓰기 중단 또는 DB 고유의 backup/restore 도구, 권한·소유자·숨김 파일 보존, 검증, 앱 전환, 실패 시 되돌아갈 원본 보존이 포함되어야 한다. RWO 디스크 두 개가 다른 zone에 있으면 같은 임시 Pod에 mount할 수 없는 문제도 먼저 해결해야 한다.

### VolumeSnapshot과 복원용 PVC

VolumeSnapshot은 CSI가 제공하는 시점 복제를 Kubernetes API로 요청하는 기능이다. snapshot CRD, snapshot controller, 지원 CSI driver와 VolumeSnapshotClass가 필요하다. 다음 예제는 앞의 EBS driver와 `order-export` PVC를 사용하며, 앱의 일관성을 확보할 별도 절차가 있다는 전제다.

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: book-ebs-snapshot
driver: ebs.csi.aws.com
deletionPolicy: Retain
---
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: order-export-before-change
  namespace: bookstore
spec:
  volumeSnapshotClassName: book-ebs-snapshot
  source:
    persistentVolumeClaimName: order-export
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: order-export-restored
  namespace: bookstore
spec:
  storageClassName: book-ebs
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 20Gi
  dataSource:
    name: order-export-before-change
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

복원 전에 snapshot의 `readyToUse`와 오류를 확인하고, 복원 class의 driver·용량 등 호환 조건을 확인한다. 여기서는 같은 namespace의 snapshot을 새 PVC의 source로 사용한다. 실제 복원에서는 snapshot 생성과 준비 완료를 기다린 뒤 복원 claim을 생성하는 순서로 검증한다.

스토리지 시점 복제는 앱 일관성, 독립된 백업 보관, 다른 리전 복제, DB의 point-in-time recovery를 자동으로 제공하지 않는다. DB에는 제품이 지원하는 quiesce·backup 절차가 필요하고, flush 한 번을 모든 DB의 복구 보장으로 취급할 수 없다. 복원용 PVC가 Bound가 된 뒤 새 Pod에서 DB recovery, 스키마·데이터, 앱의 읽기·쓰기를 확인해야 비로소 복구 검증이라고 부를 수 있다. [VolumeSnapshot 공식 문서](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)는 스냅샷 API와 storage 구현의 역할을 구분한다.

## 7. 심화: 클라우드 이름보다 실제 class를 읽는다

2026-10-23 기준 AWS EKS의 standard EBS CSI 경로는 `ebs.csi.aws.com`이고, EKS Auto Mode의 EBS provisioner는 `ebs.csi.eks.amazonaws.com`이다. 설치와 관리 주체가 다르므로 모든 EKS에 동일 애드온 설치 명령을 적용하면 안 된다. Standard 경로에서도 IAM 구성은 IRSA만 있는 것이 아니라 EKS Pod Identity 등 지원 방식을 확인해야 한다. [AWS EBS CSI 문서](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)가 이 구분의 기준이다.

기존 class에 `kubernetes.io/aws-ebs`가 보인다면 in-tree 플러그인과 CSI migration 이력을 확인한다. `awsElasticBlockStore`는 1.19 deprecated, CSI migration은 1.23 기본 활성화, in-tree 코드는 1.27 제거라는 이력이 있다. 오래된 provisioner 문자열만으로 실제 I/O가 어떤 driver를 거치는지 단정하지 않는다. 새 구성은 해당 환경이 지원하는 CSI class를 명시하는 편이 관계를 읽기 쉽다.

GKE의 `standard-rwo`는 pd-balanced, `premium-rwo`는 pd-ssd를 사용하는 class의 예다. `premium-rwo`라는 이름 자체가 regional replication을 뜻하지는 않는다. Regional Persistent Disk에는 복제 유형과 zone topology 조건이 별도로 있다. AKS도 `managed-csi`, `managed-csi-premium`, Azure Files 계열처럼 block/file 선택이 갈린다. class 이름은 설치 모드와 버전에 따라 실제 정의를 확인한다.

```bash
kubectl get storageclass
kubectl get storageclass book-ebs -o yaml
```

가격표나 class의 이름보다 provisioner, binding mode, reclaim policy, 확장 지원, topology, 암호화 정책을 읽는 것이 먼저다. 여러 Node의 동시 파일 접근이 필요하다면 EFS/NFS/Filestore/Azure Files 같은 파일 저장소 경로를 검토하고, 단일 Node block disk와 같은 계약으로 취급하지 않는다. 관리형 DB나 object storage를 사용하면 API Pod의 영구 mount 자체가 필요 없어질 수도 있지만, 데이터의 복구 책임이 사라지는 것은 아니다.

## 생각해 볼 질문

### 1. 앱 컨테이너만 재시작했는데 임시 파일은 남고 `/tmp`의 다른 파일은 사라질 수 있는 이유는 무엇인가?

같은 Pod의 `emptyDir`에 둔 파일은 컨테이너 인스턴스의 수명과 분리되어 있다. 반면 writable layer에만 쓴 파일의 보존은 기대할 수 없다. 경로 문자열보다 그 경로에 연결된 Volume 종류와 수명이 중요하다.

### 2. PVC가 Pending인 환경에서 driver를 다시 설치하기 전에 무엇을 확인해야 하는가?

class의 binding mode와 소비 Pod의 존재·배치 조건이다. `WaitForFirstConsumer`라면 consumer 없는 Pending은 정상일 수 있다. consumer가 있는데도 진행되지 않으면 PVC/Pod Events와 topology·자원·권한을 이어서 확인한다.

### 3. snapshot에서 만든 PVC가 Bound이면 주문 데이터 복구가 끝난 것인가?

저장소 선택만 확인한 것이다. mount, DB recovery, 데이터 일관성, 앱의 실제 조회·쓰기까지 검증해야 한다. snapshot이 재해 때 접근 가능한 위치에 보관되었는지도 별도 조건이다.

## 다음 장으로

저장소를 Pod보다 오래 유지할 수 있게 되었다. 이제 복제본 세 개 각각이 자기 디스크를 다시 찾아야 한다면, 어느 Pod가 어느 PVC를 쓸지 구별해야 한다. [StatefulSet](Kubernetes-StatefulSet.md)은 이 인스턴스의 정체성을 관리하는 방법을 설명한다.

## 출처

- [Kubernetes Volumes](https://kubernetes.io/docs/concepts/storage/volumes/) — 컨테이너 재시작과 Volume 수명, emptyDir와 hostPath
- [Kubernetes Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) — binding, 접근 모드, reclaim, 보호와 확장
- [Kubernetes Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/) — provisioner, topology와 binding mode
- [Kubernetes Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/) — snapshot 구성 요소와 복원
- [AWS EKS EBS CSI](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html) — standard와 Auto Mode, IAM 전제
- [GKE Persistent Disk CSI driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/gce-pd-csi-driver) — class와 disk 유형
- [GKE Regional Persistent Disk](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/regional-pd) — 지역 복제 조건
- [AKS Azure Disk CSI](https://learn.microsoft.com/en-us/azure/aks/azure-csi-disk-storage-provision) — Azure Disk class와 provisioning
