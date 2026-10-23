# Kubernetes Logging and Events

> **개발자를 위한 쉬운 쿠버네티스 · 25장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [이전 장](./Kubernetes-Metrics-Server-Prometheus.md) · [다음 장](./Kubernetes-ServiceAccount-RBAC.md)

Pod를 재시작하자 주문 API는 살아났다. 그런데 아침에 원인을 찾으려 하니 어제의 로그가 없다. 프로세스를 복구하는 일과 장애의 흔적을 남기는 일은 왜 따로 준비해야 할까?

## 결론부터 말하면

앱이 `stdout`·`stderr`로 쓴 로그는 container runtime과 kubelet을 거쳐 Node에 남고, `kubectl logs`는 그중 조회 가능한 컨테이너 로그를 읽는다. Pod·Node의 수명을 넘어 기록을 보존하려면 수집기와 별도 저장소가 필요하다. Events는 Kubernetes 구성 요소가 관찰한 사건이며, 앱 로그나 영구 감사 기록을 대신하지 않는다.

| 질문 | 먼저 읽을 자료 | 이 자료만으로 알 수 없는 것 |
|---|---|---|
| 왜 컨테이너가 시작되지 않았나 | Pod status, Events | 시작하지 않은 앱의 내부 처리 |
| 시작한 앱이 어떤 오류를 냈나 | 컨테이너 로그 | 전체 요청 중 피해 비율 |
| 장애가 언제부터 얼마나 퍼졌나 | 시간에 따른 metrics | 개별 요청의 상세 맥락 |
| 한 요청이 어느 서비스에서 지연됐나 | 연결된 trace와 로그 | 계측·보존되지 않은 구간 |

[Metrics Server와 Prometheus](Kubernetes-Metrics-Server-Prometheus.md)에서 사용량과 시계열을 보았다면, 이번에는 숫자에 설명을 붙일 차례다. 목표는 수집 도구 이름을 외우는 것이 아니라 기록이 생기고 사라지는 경로를 설명하는 것이다.

## 1. 로그를 파일에서 프로세스의 출력으로 옮기는 이유

서버 한 대에서 운영하던 앱은 `/var/log/order-api/app.log` 같은 파일을 만들고 사람이 접속해 읽을 수 있었다. 하지만 Deployment의 Pod는 교체되고 여러 Node로 흩어진다. 컨테이너 내부의 파일만 찾는 방식은 어느 replica의 어떤 실행에서 생긴 기록인지부터 다시 추적하게 만든다.

그래서 컨테이너 앱은 일반적으로 표준 출력인 `stdout`과 표준 오류인 `stderr`에 로그를 쓴다. 앱은 로그 메시지를 만들고, 실행 환경은 출력 스트림을 수집한다. 두 스트림은 출력을 전달하는 통로일 뿐이다. `stderr` 한 줄이 HTTP 500 하나를 뜻하거나, `stdout`에는 오류가 없다는 규칙은 없다. severity는 앱의 로그 형식으로 표현해야 한다.

앱이 별도 파일에만 기록하면 그 파일이 자동으로 `kubectl logs`에 나타나지는 않는다. 파일을 읽는 수집기나 stdout으로 전달하는 sidecar 같은 추가 경로가 필요하다. 이 책의 첫 배포에 쓰는 정적 HTTP 데모도 실제 주문 처리 앱은 아니다. 그 데모에서 요청 로그를 볼 수 있다는 사실과 업무 오류·요청 ID를 갖춘 앱 로그가 준비되어 있다는 사실은 구분한다.

## 2. 한 줄의 로그가 Node를 떠나기까지

Linux Node의 일반적인 CRI 실행 경로에서 runtime은 컨테이너의 출력 스트림을 정해진 로그 형식으로 Node의 파일에 기록한다. kubelet은 로그 위치와 회전을 관리하고 로그 조회를 제공한다. Linux의 기본 Pod 로그 디렉터리는 보통 `/var/log/pods`지만, 설정과 운영체제에 따라 달라질 수 있다. 앱 컨테이너의 루트 파일시스템에 직접 보관하는 것과 다른 경로다. [Kubernetes logging architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)

이 경로는 장기 저장소가 아니다. 로그 회전은 파일이 디스크를 무한히 채우지 않도록 오래된 내용을 밀어내는 작업이다. 회전된 파일은 Node에 보존 설정에 따라 남아 있다가 삭제될 수 있다. Node가 사라지거나 Pod가 정리되거나 보존 설정에 따라 파일이 삭제되면 로컬 기록을 더는 읽지 못할 수 있다. 따라서 “앱이 로그를 출력했다”와 “운영자가 내일도 검색할 수 있다” 사이에 보존 설계가 필요하다.

중앙 수집에서는 보통 Node마다 수집기를 두어 파일을 읽고 namespace, Pod UID, container 이름, Node 같은 출처를 붙여 저장소로 보낸다. 모든 Node에 배치하는 [DaemonSet](Kubernetes-DaemonSet-Job-CronJob.md)이 이 역할에 잘 맞는다. 저장소는 받은 기록을 색인하고 조회·보존 정책을 적용한다. 앱이 직접 외부 저장소로 보내는 구조나 sidecar 수집도 가능하지만, 그 경우에도 전송 실패와 버퍼의 책임은 사라지지 않는다.

운영에서는 이 연결을 실제로 확인해야 한다. 앱 출력, Node의 기록, 수집기의 읽기·전송, 저장소의 수신·조회가 각각 성공했는지 본다. 수집기 Pod가 Running이라는 사실만으로 로그 도착을 증명할 수 없다. 저장소 장애 중 쌓인 버퍼가 얼마나 버티는지, 넘치면 버리는지 앱을 막는지, 재시도에서 중복이 생길 수 있는지도 수집기 설정으로 정해야 한다. 이는 모든 제품에 공통된 자동 보장이 아니라 해당 구성의 검증 항목이다.

## 3. `kubectl logs`는 정확히 무엇을 읽는가

`kubectl logs`는 중앙 로그 저장소를 검색하는 명령이 아니다. 사용자의 API 요청이 kube-apiserver를 거쳐 해당 Node의 kubelet 로그 조회 경로에 도달해야 한다. 따라서 앱 로그 읽기 권한뿐 아니라 API server와 kubelet의 통신 상태도 결과에 영향을 준다. 실행할 때는 조회를 허용받은 실습 kubeconfig와 context를 명시한다.

아래의 `POD_NAME`은 현재 조사하는 `bookstore`의 실제 Pod 이름으로 바꾼다. 이 책의 앱 컨테이너 이름은 `order-api`다. 첫 명령은 Pod와 Node의 대응을 확인하고, 다음 두 명령은 그 Pod의 같은 컨테이너에 대해 현재 실행과 직전 실행을 나누어 조회한다. 모두 읽기 요청이며 앱 상태를 변경하지 않는다.

```bash
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore get pods -l app=order-api -o wide
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore logs POD_NAME -c order-api --since=15m --timestamps --tail=200
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore logs POD_NAME -c order-api --previous --timestamps --tail=200
```

`--previous`는 같은 Pod 안에서 종료된 **직전 컨테이너 인스턴스** 의 로그가 남아 있을 때 읽는다. Deployment가 교체한 옛 Pod 전체를 찾아주거나 여러 번의 재시작 이력을 모두 펼쳐 주지 않는다. 지금 조사하는 Pod가 새로 생성되었다면 이전 Pod의 컨테이너는 다른 조사 대상이다. `restartCount`, Pod UID, container의 `lastState`를 함께 확인해야 재시작과 Pod 교체를 혼동하지 않는다. [kubectl logs 명령 참조](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/)

`--since`는 보존 기간을 늘리지 않고 읽을 범위를 줄인다. `--timestamps`도 앱 내부에서 사건이 발생한 시각과 수집 시각의 차이를 자동으로 해결하지 않는다. `kubectl logs`는 최신 로그 파일만 제공하며 회전된 모든 파일을 이어서 보여 주지 않으므로, 오래된 장애는 중앙 저장소의 보존 범위에서 찾아야 한다. 로그가 비었다면 정상이라고 결론내리기 전에 Pod·container 선택, 앱 출력 방식, 보존 여부, 권한·연결 실패를 구분한다.

## 4. Events는 앱 로그 앞쪽의 실패를 설명한다

이미지 다운로드가 실패했다면 앱 프로세스는 시작하지 않았다. 앱 로그에서 원인을 찾을 수 없는 이유다. 이때 kubelet이나 scheduler 같은 구성 요소가 기록한 Events에서 `FailedScheduling`, 이미지 pull 실패, volume mount 실패 같은 단서를 찾는다. Events는 Kubernetes 오브젝트와 관련된 사건을 API로 노출한 자료다.

```bash
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore describe pod POD_NAME
kubectl --kubeconfig "$LAB_KUBECONFIG" --context "$LAB_CONTEXT" \
  -n bookstore get events --field-selector involvedObject.name=POD_NAME \
  --sort-by=.metadata.creationTimestamp
```

`describe`에서는 Conditions와 container state를 읽은 뒤 아래의 Events를 연결한다. 두 번째 명령은 이름으로 좁히므로, 이름이 재사용되거나 서로 다른 종류의 오브젝트가 같은 이름을 쓰는 상황에서는 Events의 대상 kind·UID도 대조한다. creationTimestamp 정렬은 Event 오브젝트가 만들어진 순서를 보여 줄 뿐이다. 반복 사건이 한 Event의 count·최근 관측 시각으로 갱신되었다면 모든 발생을 개별 시간순 목록으로 복원하지 못한다.

2026-10-23 확인한 kube-apiserver 공식 참조에서 `--event-ttl` 기본값은 1시간이다. 실제 보존은 해당 클러스터의 설정으로 확인해야 한다. Events는 제한된 수명과 집계 특성을 갖는 진단 자료이므로, 아침에 Events가 없다는 사실은 어젯밤에 사건이 없었다는 증거가 아니다. 장기 분석이 필요하면 Events도 별도 수집·보존 대상을 정한다. [kube-apiserver 옵션](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/)

API 요청의 주체와 행위를 남기는 audit log는 또 다른 기록이다. 앱 로그나 Events를 켰다고 API audit 정책과 저장소가 구성되었다고 볼 수 없다. 보안 조사에서 “누가 Pod를 삭제했나”를 묻는다면 audit의 수집 여부와 보존 범위를 확인해야 한다. [Kubernetes auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)

## 5. metrics에서 발견한 문제를 요청 하나의 기록으로 좁힌다

Prometheus에서 오류율이 늘었다면 우선 영향의 시작 시각과 배포 revision을 고정한다. 그 시간대의 `order-api` 로그를 좁혀 DB timeout을 찾고, 해당 요청의 trace가 있다면 API 처리와 downstream 호출 중 어느 구간이 길었는지 확인한다. metrics는 집계된 변화, 로그는 사건의 맥락, trace는 한 요청의 작업 구간과 서비스 간 연결을 보여 준다. [Kubernetes observability](https://kubernetes.io/docs/concepts/cluster-administration/observability/)

이 연결은 같은 시각에 비슷한 문장이 있다는 이유로 자동 완성되지 않는다. 여러 replica가 동시에 처리하므로 요청 ID와 trace ID를 전달하고 기록해야 한다. 요청 ID는 앱에서 요청을 식별하는 값이고, trace ID는 계측한 분산 작업의 연결에 사용된다. 프레임워크의 계측과 로그 연동 설정이 없다면 Kubernetes가 앱 로그 문장에 trace ID를 만들어 넣어 주지 않는다. [OpenTelemetry logs](https://opentelemetry.io/docs/concepts/signals/logs/)

다음은 필드의 뜻을 설명하기 위한 가상 로그이며 정적 HTTP 데모의 실제 출력이 아니다. 시간대가 포함된 시각, 앱·revision, 요청과 trace 식별자, 고정된 사건 이름을 두면 Pod가 교체된 뒤에도 질문을 이어갈 수 있다. Pod UID 같은 실행 출처는 수집기가 추가할 수도 있으므로 필드 소유권을 정한다.

```json
{"timestamp":"2026-10-23T09:15:30.120+09:00","level":"ERROR","service":"order-api","revision":"1.0.0","request_id":"req-example-01","trace_id":"0123456789abcdef0123456789abcdef","event":"database_timeout","duration_ms":2000}
```

시각은 사람의 시간대와 저장소의 조회 시간대를 맞춰 읽는다. Node와 앱 호스트의 시간 동기화가 어긋나면 사건의 선후 관계와 TLS 진단까지 흔들린다. 또 metrics label에 요청 ID처럼 매번 달라지는 값을 그대로 넣으면 시계열 수가 급증한다. 요청별 식별자는 로그·trace의 상세 조회에 두고 metrics는 제한된 집계 차원으로 설계하는 편이 적합하다. [Prometheus instrumentation practices](https://prometheus.io/docs/practices/instrumentation/)

## 6. 기록의 양보다 남겨도 되는 내용과 남아 있는지를 관리한다

로그에 HTTP header와 body를 전부 남기면 장애 분석은 편해 보인다. 하지만 Authorization token, cookie, 개인정보, DB 연결 문자열까지 복제될 수 있다. 보안 필터링은 가능하면 앱에서 시작하고 수집·저장 경로에서도 점검한다. 원래 Secret 접근 권한이 없던 사람도 로그 검색 권한을 통해 값을 보게 되는 상황을 막아야 한다. 요청 ID는 전체 요청 내용을 복사하지 않고도 여러 기록을 연결하는 수단이 된다.

보존 기간은 무조건 길수록 좋은 값이 아니다. 사고 분석에 필요한 기간, 보안·개인정보 기준, 저장 비용과 조회 성능을 함께 정한다. 누가 어느 namespace의 로그를 읽는지, 전송·저장 암호화와 삭제가 어떻게 적용되는지도 저장소 운영 범위에 포함한다. 이 기준은 앱 로그, Events, audit log, trace마다 다를 수 있다. [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

로그 파이프라인에도 관찰이 필요하다. 최근 시험 로그가 저장소에 도착했는지, 수집 지연과 유실·버퍼 포화가 늘지 않는지, 저장소가 가득 차기 전에 알리는지 확인한다. 서비스 장애 때 로그가 폭증하면 수집기가 Node의 CPU·디스크를 쓰며 원래 장애를 키울 수도 있다. 그래서 로그량과 수집기 자원 한도도 [자원 관리](Kubernetes-Resource-Management.md)의 문제다.

에어갭에서는 외부 SaaS로 보낼 수 있다는 가정부터 제거한다. 내부 수집기 이미지와 플러그인, 저장소 용량, 사내 CA 신뢰, 전송 경로를 준비한다. 외부로 반출할 장애 자료는 원본 로그를 통째로 보내기보다 승인된 절차로 민감값을 제거하고 필요한 범위만 추출해야 한다. 인터넷 연결이 없어도 기록의 유실·민감값 노출·디스크 포화 문제는 그대로 존재한다.

## 7. 복구 전에 남길 근거가 다음 진단의 출발점이다

재시작은 증상을 줄일 수 있지만 프로세스 메모리와 직전 상태를 바꾼다. 허용된 범위에서 먼저 Pod UID·Node·image digest·시각, status와 Events, 현재·직전 로그를 확보하면 “어떤 실행에 무엇이 일어났는가”를 나중에도 설명할 수 있다. 다만 이미 사라진 기록까지 새 명령으로 되살릴 수는 없다. 보존 준비는 장애가 발생하기 전에 해야 한다.

이제 로그를 보며 찾은 `permission denied`가 무엇의 권한인지 구분할 수 있어야 한다. 다음 [ServiceAccount와 RBAC](Kubernetes-ServiceAccount-RBAC.md)에서는 API를 호출하는 신원과 허용된 작업을 살펴본다. 이어 [실행 보안](Kubernetes-Workload-Security.md)에서 앱 프로세스의 파일·커널 접근 권한을 구분하고, 마지막 [종합 장애 추적](Kubernetes-Troubleshooting-From-Apply-to-Request.md)에서 배포와 요청의 경로에 기록을 붙인다.

## 생각해 볼 질문

### 1. Deployment를 새 이미지로 교체한 뒤 `--previous`를 쓰면 어제 Pod의 로그를 읽을 수 있을까?

그렇지 않다. `--previous`는 지정한 Pod 안의 직전 컨테이너 인스턴스를 대상으로 한다. Pod 교체는 다른 UID를 가진 실행이므로 이전 Pod와 보존 위치를 별도로 찾아야 한다. Pod·Node가 사라진 이후까지 조회해야 한다면 중앙 수집과 보존이 미리 구성되어 있어야 한다.

### 2. Pod 로그는 없고 Events에는 이미지 pull 오류가 있다. 로그 수집기부터 고쳐야 할까?

앱 프로세스가 시작되지 않은 경우에는 앱이 쓸 로그 자체가 없다. container state와 Events로 pull 실패의 주체·원인을 먼저 읽는다. 같은 시각 다른 앱의 로그 수집도 끊겼다는 별도 증거가 있다면 수집기 문제를 병행 조사할 수 있지만, 빈 앱 로그만으로 수집 장애를 단정하지 않는다.

### 3. 오류 로그 한 줄과 CPU 그래프만으로 사용자 피해를 설명할 수 있을까?

한 줄의 오류는 발생 사실의 단서이고 CPU 그래프는 자원 사용의 변화다. 전체 요청 수와 실패율, 지연 분포로 영향 범위를 확인하고, 요청 ID·trace ID로 구체적인 실패를 연결해야 한다. 어느 자료든 계측·보존·시간 범위가 빠졌다면 그 구간은 미확인으로 남는다.

## 출처

공식 문서 확인 기준: 2026-10-23. 로그 경로·보존 설정은 배포한 runtime·kubelet·수집기의 실제 설정으로 다시 확인한다.

- [Kubernetes — Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Kubernetes — kubectl logs](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_logs/)
- [Kubernetes — kube-apiserver reference](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-apiserver/)
- [Kubernetes — Observability](https://kubernetes.io/docs/concepts/cluster-administration/observability/)
- [Kubernetes — Auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [OpenTelemetry — Logs](https://opentelemetry.io/docs/concepts/signals/logs/)
- [Prometheus — Instrumentation practices](https://prometheus.io/docs/practices/instrumentation/)
- [OWASP — Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
