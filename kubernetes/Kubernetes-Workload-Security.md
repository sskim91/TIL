# Kubernetes Workload Security

> **개발자를 위한 쉬운 쿠버네티스 · 27장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-ServiceAccount-RBAC.md) · [다음 장](./Kubernetes-CRD-Controller-Operator.md)

ServiceAccount에 아무 권한도 주지 않았는데 보안 점검은 컨테이너가 root로 실행된다고 지적한다. API를 부를 권한이 없으면 앱 프로세스도 제한된 것 아닌가? 두 권한은 어디에서 만나고 어디에서 갈라질까?

## 결론부터 말하면

RBAC는 Kubernetes API에 어떤 요청을 허용할지 정하고, `securityContext`는 Node에서 실행되는 프로세스의 사용자·권한·파일시스템·시스템 호출 제약을 정한다. 실행 권한을 줄일 때는 앱이 실제로 필요한 쓰기 경로와 동작을 확인한 뒤 적용해야 한다. 필드를 많이 붙였다는 사실은 호환성이나 안전한 실행의 증명이 아니다.

| 경계 | 대표 설정·장치 | 확인하려는 질문 |
|---|---|---|
| Kubernetes API | ServiceAccount, RBAC | 이 주체가 Secret을 읽거나 Pod를 만들 수 있나 |
| 앱 프로세스 | UID/GID, capabilities, seccomp | 이 프로세스가 어떤 OS 작업을 할 수 있나 |
| 파일 쓰기 | 읽기 전용 root, volume 권한 | 무엇을 어디에 쓸 수 있나 |
| 생성 시 정책 | Pod Security Admission | 이 Pod 명세를 이 namespace에서 받아들일 것인가 |

이 장은 Linux 컨테이너를 기준으로 설명한다. Windows의 사용자·보안 필드는 다르다. 또한 컨테이너가 host kernel을 공유한다는 [컨테이너 기초](Kubernetes-Container-Fundamentals.md)의 전제를 유지한다. 아래 설정은 kernel 취약점, 과도한 API 권한, 네트워크 접근, 공급망 문제를 모두 해결하는 격리 경계가 아니다.

## 1. API의 사용자와 Linux의 사용자는 다른 신분이다

[ServiceAccount와 RBAC](Kubernetes-ServiceAccount-RBAC.md)에서 앱은 token으로 API에 자신을 증명했다. API server는 그 주체가 `get secrets` 같은 동작을 할 수 있는지 판단한다. 반면 컨테이너 안의 프로세스가 `/app/config.json`에 쓰려 할 때는 Linux가 UID, GID, 파일 권한과 마운트 속성을 확인한다. 여기서는 ServiceAccount의 RoleBinding을 읽지 않는다.

그래서 `Forbidden`과 `Permission denied`를 같은 처방으로 해결하면 안 된다. API의 403 응답은 요청 주체·resource·verb를 확인할 문제다. 파일 쓰기의 `Permission denied`나 `Read-only file system`은 프로세스 신분과 파일·volume 경로를 확인할 문제다. 파일 쓰기 오류를 없애려고 `cluster-admin`을 주어도 OS 파일 권한은 바뀌지 않고 API 공격 범위만 늘어난다.

반대 조합도 가능하다. UID가 0이 아닌 프로세스라도 `cluster-admin` token을 읽을 수 있으면 강한 API 권한을 행사할 수 있다. UID 0 프로세스가 항상 Kubernetes 관리자인 것도 아니다. 따라서 API 권한 최소화, token 전달 필요성, 실행 권한 최소화를 각각 점검하고 서로의 빈틈을 메운다. 이 구분이 [NetworkPolicy](Kubernetes-Egress-NetworkPolicy.md) 같은 다른 경계를 함께 쓰는 이유다.

## 2. non-root는 숫자와 이미지의 준비 상태로 확인한다

Linux에서 UID 0은 root다. 컨테이너 안의 root가 곧바로 host root와 동일한 전체 권한을 갖는 것은 아니지만, 공유 kernel과 마운트·capabilities의 조합에서 피해를 키울 수 있다. 일반 앱에 불필요한 root 실행을 줄이는 것은 그 공격 여지를 줄이기 위한 출발점이다. [Linux kernel security constraints](https://kubernetes.io/docs/concepts/security/linux-kernel-security-constraints/)

`runAsNonRoot: true`는 이미지가 root로 실행되지 않도록 확인하는 조건이다. 스스로 새 사용자를 만들거나 파일의 소유권을 바꾸지 않는다. `runAsUser`는 실제 실행 UID를 정한다. 이미지에 이름으로만 지정된 사용자 등 kubelet이 non-root 여부를 확인할 수 없는 조합에서는 실행이 거절될 수 있으므로, Dockerfile의 사용자 설정과 Pod의 숫자 UID를 함께 읽는다.

UID를 65532로 바꿨더니 기존 앱이 실패할 수 있다. 시작 스크립트가 `/app`의 소유권을 바꾸거나 설정 파일을 만들고, 특정 home directory를 기대하고, 기존 volume이 다른 UID 소유일 수 있기 때문이다. Java나 Python이라는 언어 이름만으로 non-root 호환성을 보장하지 못한다. 이미지 빌드 때 필요한 파일 권한을 준비하고, 시작 시점과 실제 요청 처리 중 무엇을 쓰는지 확인해야 한다.

GID와 보조 그룹도 파일 접근에 관여한다. volume 공유 권한을 위해 `runAsGroup`이나 `fsGroup`을 검토할 수 있지만, 모든 volume에 일괄 `chown`이 수행된다고 가정하지 않는다. volume 종류와 CSI driver 지원에 따라 처리 주체와 동작이 다르다. 큰 volume의 권한 변경은 시작 시간에도 영향을 줄 수 있으므로 [Volume과 Persistent Storage](Kubernetes-Volume-PersistentVolume.md)의 실제 저장소 조건과 연결한다. [Security Context 설정](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)

## 3. root 여부만으로 남은 권한을 설명할 수는 없다

Linux capabilities는 전통적인 root 권한을 여러 작업 단위로 나눈 것이다. 앱이 단순 HTTP 응답만 한다면 네트워크 관리나 시스템 관리 capability가 필요하지 않을 수 있다. `capabilities.drop: [ALL]`은 불필요한 권한을 제거하는 시작점이지만, 필요한 기능이 있는 앱은 제거 후 실제 동작을 검증해야 한다. 막혔다는 이유로 광범위한 `SYS_ADMIN`을 다시 추가하기 전에 어떤 작업을 왜 수행하는지부터 확인한다.

`allowPrivilegeEscalation: false`는 프로세스가 실행 중 자식 프로그램 등의 경로로 더 높은 권한을 얻는 것을 제한하며 Linux의 `no_new_privs`와 연결된다. 현재 부여된 모든 권한을 제거하는 필드는 아니다. `privileged: true`와 `allowPrivilegeEscalation: false` 조합은 API 검증에서 거절된다. 또한 이 필드는 이미 부여한 `SYS_ADMIN` 같은 강한 capability를 제거하지 않으므로 필요한 capability를 별도로 줄여야 한다. [Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)

따라서 UID, capabilities, privilege escalation은 겹치는 듯 보여도 질문이 다르다. 누구로 시작하는가, 시작할 때 어떤 특권이 남아 있는가, 실행하면서 특권을 더 얻을 수 있는가를 각각 좁힌다. 필요성을 설명하지 못하는 권한은 제거 후보로 삼되 정상 요청·배치·종료 처리까지 확인해야 줄인 권한으로 운영할 수 있다.

이 책의 앱은 컨테이너의 8080에서 듣고 Service가 80을 제공한다. Service port가 80이라는 이유로 앱에 낮은 포트 바인딩 권한을 추가할 필요는 없다. 실제 프로세스가 바인딩하는 포트를 기준으로 판단한다. 낮은 포트에 대한 제약은 runtime과 kernel 설정의 영향도 받으므로, 다른 앱에 `NET_BIND_SERVICE`를 기계적으로 넣는 처방으로 일반화하지 않는다.

## 4. 읽기 전용 root를 쓰려면 쓰기 경로를 먼저 알아야 한다

`readOnlyRootFilesystem: true`는 컨테이너 root filesystem에 대한 쓰기를 막는다. 정상 앱이 임시 파일을 만들거나 디스크 캐시를 쓰는 것까지 불필요하다는 뜻은 아니다. 앱이 `/tmp`, 업로드 경로, 압축 해제 디렉터리, JVM 임시 경로에 무엇을 쓰는지 조사하고 필요한 경로만 별도 volume으로 제공한다.

예를 들어 임시 변환 파일이라면 `emptyDir`를 검토할 수 있다. Pod가 지워지면 잃어도 되는 데이터인지, 디스크 또는 memory medium의 사용량과 한도를 어떻게 관리할지 정해야 한다. 주문 원장이나 업로드 원본처럼 보존해야 할 데이터는 적절한 영속 저장소를 써야 한다. 읽기 전용 root가 volume까지 자동으로 읽기 전용으로 만드는 것은 아니며, volume의 mount 속성과 UID/GID 권한은 별도로 적용된다.

다음은 필요한 쓰기 경로가 `/tmp`라고 확인된 앱에만 참고할 **Pod template 조각** 이다. 독립 실행 가능한 전체 manifest가 아니며 이 책의 정적 HTTP 데모는 이 volume을 필요로 하지 않았다.

```yaml
spec:
  containers:
    - name: order-api
      securityContext:
        readOnlyRootFilesystem: true
      volumeMounts:
        - name: scratch
          mountPath: /tmp
  volumes:
    - name: scratch
      emptyDir:
        sizeLimit: 64Mi
```

`sizeLimit`를 선언했다고 디스크가 미리 예약되거나 디스크 부족이 해결되지는 않는다. `emptyDir`와 로그·이미지가 함께 쓰는 Node 저장 공간도 고려해야 한다. 또 민감한 임시 파일을 쓰는 앱이라면 접근 권한과 삭제 시점을 확인한다. 쓰기 경로를 아는 일은 보안 필드를 적용하기 위한 준비이면서 [클러스터 용량 운영](Kubernetes-Cluster-Operations.md)의 입력이기도 하다.

## 5. seccomp는 허용할 kernel 진입점을 제한한다

앱 프로세스는 파일 열기나 네트워크 연결 같은 작업을 system call로 kernel에 요청한다. seccomp는 이 호출에 제한을 걸어 공격에 사용할 수 있는 kernel 진입점을 줄인다. UID나 파일 소유권 검사와 다른 층이므로, non-root와 함께 사용할 이유가 있다.

`seccompProfile.type: RuntimeDefault`는 설치한 container runtime의 기본 profile을 사용한다. Kubernetes 전체에서 고정된 동일 syscall 목록을 뜻하지는 않는다. runtime 교체나 업데이트에서 동작을 다시 확인해야 하며, 특정 기능이 막혔을 때 무조건 `Unconfined`로 풀기보다 어떤 호출이 왜 필요한지 조사한다. [Seccomp and Kubernetes](https://kubernetes.io/docs/reference/node/seccomp/)

직접 만든 `Localhost` profile은 더 세밀한 제한을 줄 수 있지만, 배치될 Node에 profile을 공급하고 앱·라이브러리 업데이트마다 호환성을 관리해야 한다. profile 한 개가 악성 동작을 전부 판별하지도 않는다. 허용한 syscall을 통한 취약점 공격은 여전히 가능하므로 앱 패치, host 보안, 네트워크·API 권한 통제와 함께 사용한다.

에어갭에서 custom profile을 쓴다면 파일의 내부 배포와 버전 대응도 운영 대상이다. 이미지가 준비되어 있어도 새 Node에 profile이 없으면 실행이 실패할 수 있다. runtime 기본 profile을 택하더라도 어떤 runtime 버전과 설정으로 검증했는지 남겨야 한다.

## 6. 확인된 작은 앱에서 필드의 관계를 읽는다

책의 첫 배포 예제는 `book/order-api:1.0.0`이라는 로컬 빌드 이미지다. Python 표준 라이브러리 HTTP server가 정적 파일을 제공하며, 실제 주문 저장이나 결제를 구현하지 않는다. 기존 장의 `registry.example.com/...`는 구조를 설명하는 가상 주소이므로 이 로컬 이미지와 구분한다. 로컬 이미지는 해당 실습 Node에 반입되어 있어야 하며 공개 registry에서 받을 수 있다고 가정하지 않는다.

이 작은 데모는 기동 중 패키지를 설치하거나 설정 파일을 만들지 않고, 읽을 정적 파일이 UID 65532에서 접근 가능하며, 8080에서 요청을 받는다. 이 조건에서 아래 설정을 적용한 전용 로컬 kind 실습은 rollout 완료, 프로세스 UID 65532, Service를 통한 정적 HTTP 응답을 확인했다. 아래는 해당 Deployment의 **Pod template에서 뽑은 보안 필드** 이다. 앱 이미지·포트·selector 등을 포함한 전체 배포 manifest를 대신하지 않는다.

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 65532
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: order-api
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: [ALL]
```

Pod 수준 `securityContext`의 사용자·seccomp 설정은 container에 적용할 기본값이고, container 수준에는 그 container의 권한과 root filesystem 제약을 뒀다. 모든 필드를 어느 위치에나 쓸 수 있는 것은 아니다. init container나 sidecar가 있다면 그 실행 조건까지 읽어야 한다.

이 실행 결과가 입증한 범위는 이 이미지가 이 조합으로 기동하고 단순 HTTP 응답을 했다는 점이다. root 쓰기나 금지 syscall을 시도하는 부정 시험을 모두 수행한 보안 인증 결과가 아니며, 임의의 Spring/Python 앱·다른 runtime의 호환성을 보장하지 않는다. 실제 앱에는 시작, 정상 요청, 오류·재시도, 파일 처리, 종료, volume 권한을 포함한 검증 조건을 따로 정한다.

## 7. Pod Security Admission은 실행 전의 정책 관문이다

팀이 매번 필드를 빠뜨리지 않도록 Pod 생성 단계에서 기준을 검사할 수 있다. Kubernetes의 Pod Security Admission은 namespace에 적용한 Pod Security Standards를 기준으로 명세를 평가하는 내장 admission 장치다. `privileged`, `baseline`, `restricted` 수준과 `enforce`, `warn`, `audit` 모드를 구분한다. [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)

`enforce`는 위반하는 Pod 생성을 거절한다. `warn`은 사용자에게 경고하고 허용하며, `audit`은 API audit event에 관련 annotation을 남기고 허용한다. audit 모드를 설정했다는 사실만으로 audit log의 저장과 보존까지 마련된 것은 아니다. 기존 앱의 영향을 파악할 때 warn·audit으로 위반을 확인하고, 이미지와 명세를 고친 뒤 검증한 policy version으로 enforce하는 순서가 유용하다. [Pod Security Standards 적용 지침](https://kubernetes.io/docs/setup/best-practices/enforcing-pod-security-standards/)

중요한 비동기 함정이 있다. Deployment의 Pod template에는 warn·audit 평가가 적용되지만 enforce는 실제 생성되는 Pod에 적용된다. 따라서 Deployment 저장은 성공했는데 ReplicaSet이 만드는 Pod가 정책에 거절되어 replica가 늘지 않을 수 있다. 이 경우 앱 프로세스 로그가 아니라 ReplicaSet의 Events와 거절 이유를 읽어야 한다. 뒤의 [Admission Webhook](Kubernetes-Admission-Webhook.md)에서 살펴볼 “저장 전 관문”을 어느 오브젝트의 요청에 적용하는지 구분하는 장면이다.

`restricted`가 이 장의 모든 권고를 포함한다고 생각해서도 안 된다. 예를 들어 읽기 전용 root filesystem은 그 수준의 필수 조건이 아니다. 2026-10-23 확인한 표준은 Linux Pod의 non-root, privilege escalation 제한, seccomp, capabilities 등 여러 필드를 다루지만 내용은 policy version에 따라 읽어야 한다. `latest`는 업그레이드 뒤 새 기준을 따르므로, 적용 version과 예외 책임자를 기록하고 다음 version의 경고를 먼저 검토한다. [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

Node 네트워크·스토리지 같은 시스템 agent에는 일반 앱과 다른 권한이 필요할 수 있다. 예외를 아무 앱이나 우회할 수 있는 namespace로 만들기보다 필요한 기능·주체·범위를 설명하고 RBAC와 별도 통제로 좁힌다. 정책이 통과해도 이미지의 취약점이나 앱의 데이터 접근 정책까지 검증된 것은 아니다.

## 8. 적용 결과는 명세와 동작을 함께 읽는다

실습에서 허용된 읽기 조회로 먼저 Deployment template과 실제 Pod를 비교할 수 있다. 아래 명령은 배포를 변경하거나 container 내부 프로그램을 실행하지 않는다. 두 출력은 실행 조건의 근거이며 실제 UID나 모든 제한의 효과를 직접 증명하지는 않는다.

```bash
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore get deployment order-api -o yaml
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore get pod POD_NAME -o yaml
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore describe pod POD_NAME
```

template에는 없던 필드가 Pod에 있다면 mutating admission 등의 개입을 조사하고, container별 덮어쓰기와 init container도 확인한다. Pod가 생성되지 않았다면 상위 controller의 Events를 읽는다. Pod는 있지만 컨테이너가 시작되지 않았다면 container waiting/state와 Pod Events에서 non-root 확인·profile·runtime 준비 실패를 읽는다. 앱이 시작됐다가 실패하면 [현재·직전 로그](Kubernetes-Logging-and-Events.md)로 쓰기 경로·권한·syscall 관련 단서를 찾는다. 런타임 검증을 위해 프로세스 실행이나 부정 시험이 필요하다면 운영 Pod에서 즉흥적으로 시도하지 않고 허용된 검증 환경과 절차에서 수행한다.

실행 권한과 API 권한을 구분했으니 다음 [CRD·Controller·Operator](Kubernetes-CRD-Controller-Operator.md)에서는 API 권한을 가진 프로그램이 새 리소스의 의미를 어떻게 실행하는지 살펴본다. 이어 Admission에서 저장 전 정책 적용을 배우고, [클러스터 운영](Kubernetes-Cluster-Operations.md)에서는 그 제약을 실행하는 Node·runtime의 유지보수·버전·인증서·복구 계획으로 연결한다.

## 생각해 볼 질문

### 1. non-root 앱이 Secret을 전부 읽을 수 있다면 `runAsUser`가 잘못 적용된 것일까?

그 사실만으로는 판단할 수 없다. UID는 프로세스의 OS 신분이고 Secret 조회는 API의 인증·인가 문제다. 사용한 ServiceAccount와 token, Role·RoleBinding·ClusterRoleBinding을 확인한다. token이 파일로 전달되었다면 파일 접근 권한도 중요하지만 UID를 바꾸는 것만으로 이미 부여된 API 권한이 축소되지는 않는다.

### 2. 읽기 전용 root 적용 후 `/tmp`에서 실패하면 root 실행을 허용해야 할까?

root로 바꾸어도 읽기 전용 mount의 목적은 그대로다. 앱이 그 임시 파일을 왜 쓰는지 확인하고, 필요한 경우 수명·용량·권한을 정한 volume을 해당 경로에 제공한다. 임시 데이터인지 영속 데이터인지 판단하지 않고 전체 root를 쓰기 가능으로 되돌리면 필요 이상으로 쓰기 범위를 넓힐 수 있다.

### 3. `restricted` 정책을 쓰는 namespace에서 Deployment 생성이 성공하면 앱은 실행 가능한가?

아직 알 수 없다. 실제 Pod 생성의 enforce 평가, 이미지 pull, volume 준비, runtime의 보안 제약 적용, 앱 시작과 readiness가 뒤따른다. 정책 통과와 앱 호환성은 별개이므로 controller Events, Pod state, 로그와 실제 기능 확인을 연결해야 한다.

## 출처

공식 문서 확인 기준: 2026-10-23. 실행 결과는 이 책의 전용 로컬 정적 HTTP 데모 범위이며 일반 앱이나 고객 클러스터의 검증 결과가 아니다.

- [Kubernetes — Configure a Security Context for a Pod or Container](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Kubernetes — Linux kernel security constraints for Pods and containers](https://kubernetes.io/docs/concepts/security/linux-kernel-security-constraints/)
- [Kubernetes — Seccomp and Kubernetes](https://kubernetes.io/docs/reference/node/seccomp/)
- [Kubernetes — Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Kubernetes — Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes — Enforcing Pod Security Standards](https://kubernetes.io/docs/setup/best-practices/enforcing-pod-security-standards/)
- [Kubernetes — Volumes: emptyDir](https://kubernetes.io/docs/concepts/storage/volumes/#emptydir)
