# Kubernetes Cluster Operations

> **개발자를 위한 쉬운 쿠버네티스 · 30장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-Admission-Webhook.md) · [다음 장](./Kubernetes-Troubleshooting-From-Apply-to-Request.md)

주문 API를 replica 두 개로 배포했고 readiness도 통과했다. 그렇다면 Node 한 대를 껐다 켜도 괜찮을까? 앱의 YAML이 정상이라는 사실만으로는 그 질문에 답할 수 없다. 새 Pod가 실행될 자리, 네트워크와 저장소, 상태를 조정하는 control plane까지 계속 작동해야 하기 때문이다.

## 결론부터 말하면

클러스터 운영은 Kubernetes 구성 요소와 Node·네트워크·저장소가 앱의 실행 계약을 계속 지키게 하는 일이다. Node 유지보수는 Pod를 지우는 작업에 그치지 않고, 남은 용량·PDB·종료 처리·데이터 이동 조건을 확인하는 과정이다. 백업과 업그레이드도 명령 성공보다 앱과 데이터가 다시 사용 가능한지로 검증해야 한다.

| 운영 대상 | 유지해야 하는 계약 | 앱에서 보일 수 있는 실패 |
|---|---|---|
| control plane·etcd | 의도 저장, 조회, 배치·복구 조정 | API 실패, 새 Pod 배치·교체 지연 |
| kubelet·runtime | Node에서 이미지와 프로세스 실행 | 이미지 pull, sandbox·container 시작 실패 |
| CNI·DNS·Service 구현 | 주소, 이름, 요청 전달 | 통신 timeout, 이름 해석 실패 |
| CSI·저장소 | volume 준비, 연결, 데이터 접근 | PVC Pending, mount 실패, I/O 오류 |
| 인증서·시간·공급망 | 신뢰와 유효기간, 필요한 산출물 공급 | TLS 거절, 인증 실패, 재생성 실패 |

[Architecture](Kubernetes-Architecture.md)에서는 이 구성 요소가 새 앱을 실행하는 흐름을 보았다. 이번에는 그 구성 요소 자체를 바꾸거나 잃었을 때를 생각한다. 이 장의 명령 예시는 허용된 실습 환경의 읽기 조회이며, 고객 클러스터에 유지보수나 복구를 수행하는 절차서는 아니다.

## 1. 클러스터 운영의 첫 작업은 책임 경계를 찾는 것이다

개발자는 Deployment를 선언하지만 kubelet은 Node에서 container runtime에 실행을 요청한다. 그 연결 계약이 CRI이고, containerd나 CRI-O 같은 runtime이 실제 컨테이너 실행을 맡는다. runtime 장애나 Node 디스크 부족으로 이미지 준비가 실패하면 Deployment의 replica 수를 바꾸어도 원인이 사라지지 않는다. [Container Runtime Interface](https://kubernetes.io/docs/concepts/containers/cri/)

CNI 플러그인은 Pod 네트워크를 준비하는 실행 경로에 참여한다. 네트워크 구현에 따라 라우팅·터널·NetworkPolicy·Service 처리의 담당 범위가 달라진다. DNS는 앱이 Service 이름을 주소로 찾는 경로이고, 흔히 CoreDNS가 그 역할을 맡는다. CNI와 DNS는 모두 통신에 필요하지만 같은 구성 요소는 아니다. 이름은 해석되는데 연결이 실패하는 상황과 이름 조회부터 실패하는 상황을 나누어야 한다. [Network Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/), [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)

CSI driver는 [PVC와 실제 저장소](Kubernetes-Volume-PersistentVolume.md) 사이에서 volume 생성·연결·마운트 등의 작업을 구현한다. 그러나 저장소 제품 자체의 장애·용량·복제 정책까지 Kubernetes API가 대신 책임지지는 않는다. 같은 `FailedMount`라도 driver 상태, Node에서의 접속, 저장소 권한, backend 장애를 따라가며 담당자를 찾아야 한다. [CSI 개념](https://kubernetes.io/docs/concepts/storage/volumes/#csi)

그래서 운영 인수인계에는 “Kubernetes 담당” 하나만 적기 어렵다. 배포판 또는 managed service가 control plane을 맡는지, 누가 OS·runtime·CNI·DNS·CSI를 업데이트하는지, 앱 팀과 DB·스토리지·인증서 담당자가 누구인지 정한다. 관리형 클러스터도 앱의 readiness·PDB·데이터 정합성까지 제공자가 대신 설계하는 것은 아니다. 장애 알림을 누구에게 보낼지 정하려면 먼저 정상 경로의 소유권부터 알아야 한다.

## 2. control plane 장애와 worker 장애는 관측부터 다르다

API server에 접근할 수 없으면 `kubectl get pods`가 실패한다. 하지만 이 실패만으로 모든 앱 프로세스가 멈췄다고 말할 수는 없다. 이미 worker에서 실행 중인 컨테이너와 구성된 통신 경로는 일부 계속 동작할 수 있다. 동시에 새 배치, 상태 변경, endpoint 갱신이나 복구 조정은 지연될 수 있다. 외부에서의 실제 요청 결과와 API 접근 가능성을 분리해 관찰한다.

control plane이 여러 대라도 etcd의 다수결인 quorum이나 API 앞단의 load balancer, 인증서, 공통 네트워크가 실패하면 정상 운영을 보장하지 못한다. 단순히 “서버 세 대”인지보다 어떤 장애를 서로 독립적으로 견디는지 확인해야 한다. 예를 들어 세 etcd member가 같은 디스크 장애 영역에 있으면 member 수가 데이터 보존을 보장하지 않는다. [Operating etcd clusters](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)

worker가 응답하지 않을 때도 상태는 즉시 확정되지 않는다. Node의 heartbeat와 Lease를 통해 마지막 관측을 확인하고, controller가 실패를 판단한 뒤 taint와 Pod 처리 등이 이어진다. 배치된 Pod를 다른 Node로 옮기는 것은 실행 중 프로세스의 이동이 아니라, controller가 새 Pod를 만들고 다른 Node에서 다시 시작하는 일이다. 그 사이 이미지 준비·volume 연결·readiness에 시간이 든다. [Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/)

특히 네트워크 단절은 “Node가 멈춤”과 다르다. control plane은 Node를 못 보아도 그 Node의 프로세스가 여전히 데이터에 쓰고 있을 수 있다. 상태가 Unknown이라는 이유만으로 stateful workload를 강제로 중복 실행하면 데이터 손상 위험이 생긴다. 저장소와 애플리케이션의 fencing, 즉 옛 실행 주체의 쓰기를 확실히 막는 장치와 복구 절차가 필요한 이유다. [StatefulSet](Kubernetes-StatefulSet.md)의 안정된 신원도 이 상황을 자동으로 해결하지는 않는다.

## 3. 읽기 조회로 마지막 정상 지점을 고정한다

운영자가 처음 확보할 것은 변경 명령보다 시간과 대상이다. 어느 context·namespace에서 어떤 Pod UID와 Node를 보고 있는지, 변경 직전 어떤 버전이었는지 남긴다. 아래의 `NODE_NAME`은 실제 조사 대상을 넣는 자리다. 명령을 실행할 계정에 해당 조회 권한이 필요하고, 출력에는 내부 주소와 구성이 담길 수 있으므로 공유 범위를 제한한다.

```bash
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" get nodes -o wide
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" describe node NODE_NAME
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  get pods -A --field-selector spec.nodeName=NODE_NAME -o wide
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n kube-system get pods -o wide
```

Node의 Ready condition과 DiskPressure·MemoryPressure 등을 읽고, 그 Node에 배치된 앱·시스템 Pod의 실패가 같은 시각에 모이는지 본다. 여러 앱이 한 Node에서만 실패하면 공통 실행 기반이 가설이 되고, 여러 Node에서 DNS 조회만 실패하면 DNS 경로가 가설이 된다. `kube-system`의 Pod가 Running이어도 CNI 전달이나 DNS 응답이 정상이라는 증거는 아니므로 실제 기능을 확인하는 관찰이 뒤따라야 한다.

반대로 API 자체에 도달하지 못하는데 이 명령을 반복하면 새 정보를 얻지 못한다. API endpoint의 네트워크·TLS·인증, control plane과 etcd의 상태를 해당 운영 담당자의 절차로 확인한다. control plane 구성 요소가 항상 `kube-system`의 일반 Deployment로 노출되는 것도 아니다. static Pod나 host 서비스, managed service 등 설치 형태를 먼저 확인한다.

명령 결과는 조회 시점의 관측이다. desired state와 observed state가 비동기로 달라질 수 있으므로 현재 출력 하나만으로 장애 순서를 재구성하지 않는다. [로그와 Events](Kubernetes-Logging-and-Events.md), 시계열, 변경 기록을 같은 시각·같은 실행 대상으로 연결해야 “언제부터 어느 계층이 실패했는가”를 설명할 수 있다.

## 4. cordon과 drain은 서로 다른 결정을 수행한다

계획된 Node 재부팅을 생각해 보자. 새 Pod가 들어오는 동안 기존 Pod를 빼면 유지보수가 끝나지 않는다. 먼저 `cordon`으로 Node를 일반적인 새 스케줄링 대상에서 제외하고, `drain`으로 퇴거 가능한 Pod의 종료를 진행한다. `cordon`만으로 이미 실행 중인 Pod가 지워지거나 요청이 중단되지는 않는다. 또한 DaemonSet이나 scheduler를 우회하는 직접적인 `nodeName` 지정 같은 예외까지 절대적으로 차단하는 울타리도 아니다.

`drain`은 기본적으로 Eviction API를 사용하여 PDB와 정상 종료 유예를 존중한다. 하지만 Pod를 Node 사이에서 복사하지는 않는다. Deployment 등 controller가 replacement Pod를 만들고 scheduler와 kubelet이 새 실행을 준비한다. 그러므로 drain이 진행되는 동안 남은 replica의 실제 처리 능력과 새 Pod의 Ready 도달을 함께 보아야 한다. [Safely Drain a Node](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/)

Node의 네트워크·로그 수집 agent 같은 DaemonSet Pod는 보통 그 Node가 살아 있는 동안 필요하다. drain의 `--ignore-daemonsets`는 이를 다른 곳으로 옮기는 옵션이 아니라 처리 대상에서 건너뛰는 옵션이다. mirror Pod 등 drain이 삭제하지 않는 대상도 있으므로, drain 성공을 “Node에 프로세스가 하나도 없다”로 해석하지 않는다.

유지보수 뒤 `uncordon`은 Node를 다시 스케줄링 가능한 상태로 돌린다. 앱을 이전 Node에 원상 배치하거나 이미 지운 임시 데이터를 복구하지는 않는다. 다시 열기 전에 Node Ready와 runtime·네트워크·스토리지 기능, 필요한 시스템 agent, 앱의 정상 응답을 확인해야 한다. 세 명령은 각각 다른 목적의 상태 변경이므로 이 장에서는 대상 검토 없이 복사 실행할 유지보수 명령 묶음을 제시하지 않는다.

## 5. PDB는 남은 처리 능력과 데이터의 안전을 대신 계산하지 않는다

PodDisruptionBudget은 Eviction API를 존중하는 계획된 중단에서 동시에 사용할 수 없게 되는 Pod 수를 제한한다. 예를 들어 replica 2개에 `minAvailable: 1`이면 다른 Pod가 건강할 때 한 개의 eviction을 허용할 수 있다. 하지만 이 한 개가 평소 트래픽을 혼자 처리할 수 있는지는 PDB가 계산하지 않는다. [Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)

새 Pod가 갈 곳도 필요하다. CPU·메모리 requests를 수용할 남은 Node가 있는지, taint·affinity·topology 조건과 volume의 zone·접근 모드가 맞는지 확인한다. Ready replica 하나만으로 업무를 버틸 수 없거나 남은 Node가 가득 찼다면 먼저 여유 용량을 마련해야 한다. PDB를 낮추어 drain을 통과시키는 것은 용량을 늘리는 일이 아니다. [Scheduling](Kubernetes-Scheduling.md), [Resource Management](Kubernetes-Resource-Management.md)에서 본 조건이 유지보수의 사전 조건이 된다.

```bash
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore get deployment order-api
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore get pdb -o wide
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore get pods -l app=order-api -o wide
```

이 조회는 현재 replica·PDB·배치의 일부 근거다. `disruptionsAllowed: 0`은 지금 허용할 수 있는 추가 중단이 없다는 단서이므로 PDB selector·현재 건강 상태·목표 replica를 함께 읽는다. PDB가 없다는 결과도 “안전하게 중단 가능”을 뜻하지 않는다. 앱의 종료 처리, readiness가 트래픽에서 빠지는 시간, 진행 중 요청, DB 연결·큐 작업의 재처리를 확인해야 한다.

PDB는 갑작스러운 전원 장애를 막지 못하고, Pod 직접 삭제나 Deployment 자체의 rolling update를 같은 방식으로 제한하지도 않는다. rollout의 가용성은 [Deployment Strategy](Kubernetes-Deployment-Strategy.md)의 `maxUnavailable` 등 해당 controller 설정도 봐야 한다. 노드 점검과 앱 배포가 겹치면 각각의 설정을 따로 읽고 같은 replica를 동시에 잃는지 확인한다.

local data는 또 다른 중단 조건이다. `emptyDir` 데이터는 Pod 퇴거 시 사라지고, `hostPath`나 local PV의 파일은 다른 Node에 자동 복제되지 않는다. drain의 `--delete-emptydir-data`는 손실을 없애는 옵션이 아니라 그 손실을 감수하고 진행하게 하는 옵션이다. `--force`는 controller 없는 Pod 처리와 관련되고, `--disable-eviction`은 PDB 검사를 우회한다. 막힌 drain에 옵션을 순서대로 덧붙이기 전에 어떤 보호 조건을 포기하는지 판단해야 한다. [kubectl drain 옵션](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_drain/)

## 6. etcd 백업과 앱 데이터 백업은 서로 다른 복구 재료다

etcd에는 Kubernetes API 오브젝트의 상태가 저장된다. Deployment, Secret, PVC·PV의 메타데이터를 복구하는 데 중요하지만, PVC가 가리키는 외부 volume 안의 주문 DB 파일을 함께 저장하지는 않는다. etcd snapshot이 있다는 이유로 주문 데이터가 백업되었다고 말할 수 없다.

반대로 DB 백업만 있으면 ServiceAccount, storage 설정, workload 명세, 인증서·암호화 키와 같은 실행 조건이 자동 복원되는 것도 아니다. Git의 선언, etcd snapshot, volume snapshot, DB의 논리·물리 백업은 서로 다른 범위를 가진다. 운영자가 정할 것은 필요한 복구 재료의 묶음과 각 재료의 시점이다.

| 복구 재료 | 복구에 기여하는 범위 | 별도로 확인할 것 |
|---|---|---|
| Git·배포 산출물 | 선언한 manifest·chart·설정 이력 | 실제 적용 차이, secret·외부 의존성 |
| etcd snapshot | 그 시점의 Kubernetes API 상태 | 앱 volume 내용, PKI·암호화 키·외부 KMS 접근 |
| volume snapshot | storage가 저장한 특정 시점의 내용 | 앱·DB 정합성, 다른 장소에서의 접근·복원 가능성 |
| DB 백업·트랜잭션 로그 | DB 도구가 보장하는 데이터 복구 | 지원 버전, 복원 시점, 앱과의 호환성 |

[VolumeSnapshot](Kubernetes-Volume-PersistentVolume.md#volumesnapshot과-복원용-pvc)은 지원하는 CSI driver와 snapshot 구성 요소가 있어야 사용할 수 있다. storage 수준 snapshot은 DB가 쓰기 중일 때의 앱 정합성을 자동 보장하지 않는다. DB의 flush·backup 기능이나 트랜잭션 로그와 어떻게 맞출지 해당 제품의 공식 절차로 정한다. 같은 장비의 snapshot이 장비 전체 손실까지 견디는 외부 백업인지도 별도 확인한다. [Kubernetes Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)

etcd snapshot은 Secret 등 민감한 상태를 포함할 수 있으므로 접근과 암호화·보관을 통제한다. 저장 시 암호화가 적용된 API 데이터를 복원하려면 해당 암호화 설정·키 또는 KMS 경로도 사용할 수 있어야 한다. CA private key와 복구 credential은 무분별하게 같은 위치에 복사하기보다 승인된 보관·접근 절차로 보호하고, 복구 시 누가 가져올 수 있는지 검증한다.

## 7. 복구 검증은 API가 켜진 뒤에도 계속된다

백업 파일 생성 성공은 복구 가능성의 일부 증거다. 무결성 확인과 격리된 환경의 복원 연습을 통해 파일을 읽을 수 있는지, 필요한 버전·키·이미지·저장소가 함께 준비되는지 확인해야 한다. 운영 데이터와 외부 시스템에 중복 쓰기가 발생하지 않도록 시험의 연결 범위도 통제한다.

etcd 복원은 살아 있는 클러스터의 디렉터리에 파일을 덮어쓰는 작업으로 단순화하면 안 된다. member와 cluster 신원, snapshot 시점, topology, 기존 실행 주체의 차단을 검토해야 한다. Kubernetes의 watch·controller 캐시는 과거 revision으로 돌아가는 영향을 받으므로, 2026-10-23 확인한 etcd v3.6 복구 문서는 Kubernetes 복원 시 revision bump와 compaction 표시를 다룬다. 실제 절차는 설치 버전과 배포판에 맞춰 책임자가 검증해야 한다. 여기서는 파괴적인 복원 명령을 제공하지 않는다. [etcd v3.6 Disaster recovery](https://etcd.io/docs/v3.6/op-guide/recovery/)

복원 뒤에는 API 접근만 확인하고 끝내지 않는다. controller가 상태를 다시 관찰하는지, Node와 시스템 agent가 정상인지, volume과 DB가 맞는 시점으로 연결되는지, 앱이 기존 데이터를 읽고 새 요청을 올바르게 처리하는지 이어서 검증한다. 주문 API라면 health endpoint 응답뿐 아니라 합의된 시험 데이터의 조회·변경 결과까지 보아야 한다. 정적 HTTP 데모는 이 DB 복구 검증을 대신하지 못한다.

복구 목표도 구체적으로 정한다. RPO는 어느 시점 이후의 데이터 손실까지 허용하는지, RTO는 서비스를 얼마 안에 복구해야 하는지에 대한 목표다. snapshot 간격만으로 RPO를 달성했다고 볼 수 없고, 파일 다운로드·키 확보·이미지 반입·DB 복원·검증까지 걸린 실제 연습 시간이 RTO의 근거가 된다. 복구 재료와 사람의 권한을 함께 준비하는 이유다.

## 8. 업그레이드는 구성 요소들의 호환성을 한 단계씩 바꾸는 일이다

클러스터에는 API server·scheduler·controller-manager·kubelet만 있는 것이 아니다. etcd, runtime, CNI, CSI, DNS, admission webhook, metrics·로그 수집기와 앱이 서로 API와 실행 조건을 공유한다. Kubernetes 버전 하나가 지원된다는 사실만으로 이 조합 전체가 검증된 것은 아니다. 먼저 현재 버전·설치 방식·지원 종료·목표 조합과 소유권을 정리한다.

2026-10-23 확인한 upstream Version Skew Policy에서 kubelet은 통신하는 API server보다 새 버전일 수 없고, kubectl은 API server의 한 minor 이내 차이를 지원한다. 고가용성 API server가 섞인 전환기에는 허용 조합이 더 좁아질 수 있다. 이는 최대 허용 범위이며 배포판과 관리 도구가 더 엄격한 조건을 둘 수 있다. 임의로 minor를 건너뛰는 업그레이드를 일반 절차로 제시하지 않는다. [Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)

따라서 배포판의 절차에 따라 control plane과 worker를 단계적으로 바꾸며 각 단계에서 API·시스템 기능·업무 요청을 검증한다. worker 변경에는 앞서 본 용량과 drain 조건이 따라온다. 새 API에서 삭제·변경되는 필드, webhook의 TLS·요청 처리, CRD·controller의 호환성, runtime 기본 seccomp의 변화도 대상이다. [실행 보안](Kubernetes-Workload-Security.md)의 명세가 같아도 실행 기반이 달라질 수 있다.

실패 시 대응도 미리 정한다. Node를 다시 만드는 선택, 앱 revision을 되돌리는 선택, control plane 상태를 복원하는 선택은 서로 다른 일이다. 이미 바뀐 etcd 데이터 형식이나 API 저장 상태 때문에 control plane binary만 낮추는 방식이 지원되지 않을 수 있으므로 단순 downgrade를 rollback의 보장으로 삼지 않는다. 사전 백업과 시험, 중단 기준, 복구 책임자를 목표 버전의 공식 절차에 맞춰 준비한다.

## 9. 인증서·시간·에어갭 공급망은 조용히 다가오는 운영 조건이다

TLS는 API server만의 설정이 아니다. etcd peer·client, API server와 kubelet, admission webhook, registry, 외부 저장소에도 서로 다른 인증서와 CA 신뢰 경로가 있다. 만료일, 갱신 주체, 배포와 reload 방식, SAN·접속 주소를 목록으로 관리한다. “인증서를 갱신했다”는 말은 관련 프로세스가 새 인증서를 사용하고 상대가 신뢰한다는 확인까지 이어져야 한다.

kubeadm 기반 환경은 `kubeadm certs check-expiration`으로 kubeadm이 관리하는 로컬 PKI의 만료 상태를 점검할 수 있지만, 모든 클러스터에 적용되는 만료 진단기는 아니다. 외부 CA, kubelet의 회전 인증서, webhook·registry 인증서는 관리 범위가 다르다. 2026-10-23 공식 문서는 kubeadm의 기본 기능이 CA 교체를 자동으로 지원하지 않는다고 설명한다. leaf 인증서 갱신과 신뢰 루트인 CA 교체를 같은 작업으로 취급하지 않는다. [Certificate Management with kubeadm](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)

시간도 신뢰 판단의 입력이다. 호스트 시계가 어긋나면 아직 유효하지 않거나 만료된 인증서라는 오류가 발생하고, token 유효기간과 로그의 선후 관계도 해석하기 어려워진다. 에어갭에서는 승인된 내부 시간원과 CA 배포 경로가 있어야 하며, 외부 NTP·공인 registry에 접근한다는 기본 가정을 그대로 가져오지 않는다.

이미 실행 중인 앱이 정상이어도 재생성·확장·새 Node에서는 이미지가 필요하다. 내부 registry에 앱 이미지뿐 아니라 control plane·CNI·CSI·DNS·pause 이미지와 필요한 chart·binary·CRD를 목표 버전에 맞게 준비한다. 이미지 digest와 출처·무결성 검증, CPU architecture, 사내 CA와 credential, 취약점 수정 산출물의 반입 경로를 점검한다. Node에 우연히 남은 캐시가 재해 복구의 공급망을 대신하지 못한다. [Images](https://kubernetes.io/docs/concepts/containers/images/)

클러스터 운영의 완료 기준은 “설치 스크립트가 끝남”보다 길다. Node를 교체해도 필요한 산출물을 받아 실행할 수 있고, 데이터를 복구하고, 신뢰 경로를 유지하고, 앱 요청의 결과로 정상성을 확인해야 한다. 다음 [종합 장애 추적](Kubernetes-Troubleshooting-From-Apply-to-Request.md)에서는 이 운영 조건을 배포부터 사용자 응답까지의 한 경로에 놓고 마지막 정상 지점을 찾는다.

## 생각해 볼 질문

### 1. replica 2개와 `minAvailable: 1`인 PDB가 있으면 Node 재부팅은 무중단인가?

아직 보장할 수 없다. PDB는 허용하는 eviction 수를 제한한다. 남은 replica의 처리 용량, 새 Pod의 배치 자리와 readiness, 트래픽 전환·진행 중 요청의 종료, volume과 데이터 조건을 확인해야 한다. 두 replica가 같은 장애 영역에 있다면 갑작스러운 Node 장애도 별도로 고려해야 한다.

### 2. etcd snapshot을 복원했고 PVC가 Bound면 DB도 백업 시점으로 돌아온 것일까?

그렇지 않다. PVC·PV 상태는 저장소를 참조하는 API 메타데이터이고 DB 내용은 별도 volume에 있다. DB backup·로그·snapshot의 복원 시점과 정합성을 확인해야 한다. Bound는 연결 관계의 단서이며 데이터의 의미와 정상 조회를 증명하지 않는다.

### 3. API가 실패하지만 기존 주문 요청은 성공한다면 클러스터는 정상인가?

기존 data plane 경로가 아직 작동한다는 사실은 확인할 수 있다. 하지만 새 배포·복구·확장과 상태 갱신이 가능한지는 확인되지 않았다. API의 연결·인증서·control plane·etcd를 조사하고 사용자 요청도 계속 관찰한다. 현재 성공이 이후의 Node 장애나 Pod 재생성까지 견딘다는 보장은 아니다.

## 출처

공식 문서 확인 기준: 2026-10-23. 구체적인 설치·업그레이드·복구 순서는 배포판과 설치 버전의 공식 절차를 우선한다.

- [Kubernetes — Container Runtime Interface](https://kubernetes.io/docs/concepts/containers/cri/)
- [Kubernetes — Network Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/)
- [Kubernetes — DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Kubernetes — Nodes](https://kubernetes.io/docs/concepts/architecture/nodes/)
- [Kubernetes — Safely Drain a Node](https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/)
- [Kubernetes — kubectl drain](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_drain/)
- [Kubernetes — Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)
- [Kubernetes — Operating etcd clusters for Kubernetes](https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/)
- [Kubernetes — Volume Snapshots](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)
- [etcd v3.6 — Disaster recovery](https://etcd.io/docs/v3.6/op-guide/recovery/)
- [Kubernetes — Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)
- [Kubernetes — Certificate Management with kubeadm](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/)
- [Kubernetes — Images](https://kubernetes.io/docs/concepts/containers/images/)
