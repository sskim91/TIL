# Helm — 내 첫 Helm Chart, `helm create`부터 `helm install`까지

> **개발자를 위한 쉬운 쿠버네티스 · 확장 읽기** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서)

Maven으로 자바 프로젝트를 시작할 때 빈 폴더에서 `pom.xml`을 손으로 적지 않는다. `mvn archetype:generate` 한 줄로 뼈대를 받는다. Helm도 정확히 같은 흐름이 있다.

## 결론부터 말하면

**`helm create`는 Chart의 시작점을 만들고, `helm template`은 그것이 API에 보낼 선언을 보여 준다.** `helm install`부터는 클러스터에 쓰는 작업이며, Release의 `deployed` 상태와 앱의 실행·응답 성공은 따로 확인해야 한다. 이 글은 생성 파일을 읽어 그 경계를 이해하는 선택 실습이다.

[Helm의 패키지 모델](Helm-쿠버네티스의-패키지-매니저는-왜-필요한가.md)을 읽은 뒤 따라오면 좋다. 여기서는 `helm create`가 생성하는 nginx 계열 scaffold를 살펴보므로 본편의 가상 `order-api` 이미지를 그대로 넣지 않는다. 생성되는 기본 이미지와 probe·port는 사용한 Helm 버전의 결과에서 확인해야 한다.

| 단계 | 명령 | 하는 일 |
|------|------|--------|
| ① 스캐폴드 | `helm create my-app` | Chart 기본 뼈대 생성 |
| ② 설치 | `helm install my-first ./my-app -n helm-lab --create-namespace` | 클러스터에 Release 만들기 |
| ③ 변경 | `helm upgrade my-first ./my-app -n helm-lab --set replicaCount=3` | 새 리비전으로 갱신 |
| ④ 이력 | `helm history my-first -n helm-lab` | 리비전 목록 확인 |
| ⑤ 롤백 | `helm rollback my-first 1 -n helm-lab` | 1번 리비전 상태로 복귀 |
| ⑥ 정리 | `helm uninstall my-first -n helm-lab` | Release가 만든 리소스 일괄 삭제 |

> **예제와 검증 범위:** 2026-10-23 공식 문서를 기준으로 Chart 구조를 설명한다. 아래 디렉토리·메타데이터·출력은 설명용이며 특정 Helm 버전의 실측 기록이 아니다. Helm 3·4에 따라 HTTPRoute, helper, values가 달라질 수 있으므로 `helm version --short`와 자신이 생성한 파일을 먼저 확인한다. install 이후는 명시적으로 선택한 격리 실습 클러스터에서만 실행한다. 이 글을 위해 클러스터에 설치하거나 명령의 실제 성공을 측정하지는 않았다.

---

## 1. 빈 디렉토리부터 시작하지 마라

처음 Helm Chart를 만든다고 빈 폴더에서 시작하면 곤란하다. 알아야 할 것이 너무 많다.

- `Chart.yaml`의 정확한 형식과 필수 필드는?
- `templates/` 안에 어떤 매니페스트가 있어야 하는가?
- `_helpers.tpl`은 왜 존재하고 어떤 함수가 관습적으로 들어가는가?
- 레이블링 규칙은? (`app.kubernetes.io/name`, `helm.sh/chart` ...)
- 테스트는 어디 두는가?

자바 개발자라면 이 풍경에서 익숙한 데자뷰가 느껴질 것이다. **`pom.xml`을 처음 손으로 짜본 사람의 좌절감**이 정확히 같다. `<modelVersion>`은 뭘 적고, `<groupId>`/`<artifactId>` 규칙은 뭐고, `<build>` 섹션은 어떻게 짜야 하는지 — 모든 게 첫날 동시에 와닿는다.

Maven이 이 진입장벽을 해결한 방식이 `mvn archetype:generate`였다. **"표준 뼈대"** 를 자동으로 만들어 주고, 사용자는 거기서 필요한 부분만 수정하면 된다. Helm도 같은 카드를 들고 있다 — 그것이 `helm create`다.

| 자바/Maven | Helm |
|-----------|------|
| `mvn archetype:generate` | `helm create my-app` |
| `pom.xml` 자동 생성 | `Chart.yaml` 자동 생성 |
| `src/main/java`, `src/test/java` 구조 | `templates/`, `templates/tests/` 구조 |
| `App.java`, `AppTest.java` 샘플 코드 | `deployment.yaml`, `service.yaml` 샘플 매니페스트 |
| 빌드 가능한 상태로 즉시 시작 | 설치용 선언을 가진 샘플에서 시작 |

---

## 2. `helm create my-app` — 생성되는 기본 파일들의 정체

먼저 로컬 파일만 생성한다. 이 단계에는 Kubernetes 연결이 필요하지 않다.

```bash
helm version --short
helm create my-app
Creating my-app
```

생성된 디렉토리 구조는 다음과 같다.

```
my-app/
├── .helmignore             # 패키징 시 무시할 파일 패턴 (.gitignore와 유사)
├── Chart.yaml              # 패키지 메타 (이름, 버전, 의존성)
├── values.yaml             # 기본 설정값
├── charts/                 # 의존하는 sub-charts 자리 (처음엔 비어있음)
└── templates/              # K8s 매니페스트 템플릿들
    ├── NOTES.txt           # install 후 사용자에게 보여줄 안내문 (템플릿 가능)
    ├── _helpers.tpl        # 재사용 가능한 named template (Helper 함수)
    ├── deployment.yaml     # 컨테이너 배포 정의
    ├── hpa.yaml            # Horizontal Pod Autoscaler (기본 비활성)
    ├── ingress.yaml        # 외부 노출 (기본 비활성)
    ├── service.yaml        # Pod에 가상 IP 부여
    ├── serviceaccount.yaml # Pod의 ID
    └── tests/
        └── test-connection.yaml  # helm test로 실행되는 검증 작업
```

각 파일이 하는 일을 한눈에 보면 다음과 같다.

```mermaid
flowchart LR
    Vals[values.yaml<br>설정값] --> Engine{Helm<br>Template Engine}
    Tmpl1[deployment.yaml] --> Engine
    Tmpl2[service.yaml] --> Engine
    Tmpl3[ingress.yaml<br>enabled=false면 생략] --> Engine
    Tmpl4[serviceaccount.yaml] --> Engine
    Tmpl5[hpa.yaml<br>enabled=false면 생략] --> Engine
    Helpers[_helpers.tpl<br>named templates] -.->|include| Engine

    Engine --> K8s[K8s API Server]
    K8s --> Resources[Deployment<br>Service<br>ServiceAccount]

    style Engine fill:#1565C0,color:#fff
    style Vals fill:#2E7D32,color:#fff
    style Helpers fill:#6A1B9A,color:#fff
    style Tmpl1 fill:#37474F,color:#fff
    style Tmpl2 fill:#37474F,color:#fff
    style Tmpl3 fill:#37474F,color:#fff
    style Tmpl4 fill:#37474F,color:#fff
    style Tmpl5 fill:#37474F,color:#fff
    style K8s fill:#37474F,color:#fff
    style Resources fill:#37474F,color:#fff
```

핵심은 **`templates/` 아래의 파일이 그 자체로 K8s에 적용되는 것이 아니라, `values.yaml`과 합쳐져 렌더링된 결과가 적용된다는 점**이다. Helm 개념 글에서 다룬 "Helm은 클라이언트 사이드 템플릿 엔진"이라는 표현이 여기서 실체화된다.

---

## 3. 기본 Chart를 들여다보자 — 실제로 무엇이 만들어지는가

생성된 Chart에는 샘플 애플리케이션을 표현하는 기본값과 템플릿이 함께 들어 있다. 이미지 접근과 클러스터 조건이 충족되어야 실제로 실행된다. 핵심 파일 3개만 살펴보자.

### 3.1 `Chart.yaml` — 패키지 신원증명

```yaml
apiVersion: v2
name: my-app
description: A Helm chart for Kubernetes
type: application
version: 0.1.0           # Chart 자체의 버전 (SemVer)
appVersion: "1.16.0"     # 구조 설명을 위한 예시 값; 현재 기본값 주장이 아님
```

| 필드 | 역할 | Maven 비교 |
|------|------|-----------|
| `apiVersion: v2` | Helm 3 이상의 Chart 포맷 (v1은 Helm 2 시절) | `<modelVersion>4.0.0</modelVersion>` |
| `name` | 패키지 식별자 | `<artifactId>` |
| `version` | Chart 자체의 버전 | `<version>` (pom.xml) |
| `appVersion` | Chart가 배포하는 **앱의** 버전 (Chart 버전과 별개) | jar 내부의 `Implementation-Version` |
| `type` | `application` 또는 `library` | 패키징 타입 (jar/war) |

특히 **`version`과 `appVersion`이 다르다는 점이 헷갈리는 부분**이다. Chart 패키지는 `name + version`으로 식별되므로, `Chart.yaml`을 변경해 패키지를 다시 빌드/배포할 때는 **`version`을 반드시 올려야 한다**. 이때 안에 담긴 앱(컨테이너 이미지)의 새 버전을 기록하기 위해 `appVersion`도 함께 갱신하는 식이다. 반대로 설치 시점에 `--set image.tag=2.0`처럼 값만 오버라이드하는 것은 Chart 자체가 바뀐 게 아니므로 두 필드 다 손댈 필요 없다. `appVersion`은 패키지 식별자가 아니라 **정보성 필드** 라는 점을 기억해 두면 좋다. 앱 버전과 이미지 태그가 자동으로 연결되는 것도 아니다. 아래 템플릿이 `default .Chart.AppVersion`을 사용하기 때문에 이 Chart에서는 tag가 비었을 때 그 값이 쓰인다.

### 3.2 `values.yaml` — 기본 설정값

다음은 구조를 읽기 위해 줄인 `values.yaml` 예시다. 최신 scaffold 원문을 그대로 인용한 것은 아니다.

```yaml
replicaCount: 1

image:
  repository: nginx
  pullPolicy: IfNotPresent
  tag: ""              # 비어있으면 .Chart.AppVersion 사용 (대소문자 주의)

serviceAccount:
  create: true
  name: ""

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false       # 기본은 외부 노출 안 함
  className: ""
  hosts:
    - host: chart-example.local

autoscaling:
  enabled: false       # 기본은 HPA 안 만듦
  minReplicas: 1
  maxReplicas: 100

resources: {}          # 기본은 빈 객체 (limits/requests 미설정)
```

여기서 흥미로운 패턴이 `ingress.enabled`, `autoscaling.enabled` 같은 **on/off 스위치**다. 템플릿 안에 `{{- if .Values.ingress.enabled }}` 같은 가드가 있어, 스위치가 꺼지면 해당 매니페스트는 아예 렌더링되지 않는다 — **존재 자체를 옵션화**한 것이다.

### 3.3 `templates/deployment.yaml` — 변수가 실제로 어떻게 치환되는지

가장 중요한 파일이다. 다음은 selector·probe 등을 생략한 **템플릿 발췌** 이므로 직접 적용할 완전한 manifest가 아니다.

```gotemplate
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  template:
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
```

여기에 등장하는 문법이 Helm을 처음 만진 사람을 어지럽게 만든다. 핵심만 짚으면 다음과 같다.

| 표현 | 의미 |
|------|------|
| `{{ ... }}` | Go template 액션 (변수 치환, 함수 호출) |
| `{{- ...` | 좌측 공백 제거 (whitespace 제어) |
| `... -}}` | 우측 공백 제거 |
| `.Values.xxx` | `values.yaml`의 값. 키는 `values.yaml`에 적은 대로 (대소문자 그대로) |
| `.Chart.xxx` | `Chart.yaml`의 값. **필드명은 첫 글자 대문자**: `.Chart.Name`, `.Chart.Version`, `.Chart.AppVersion` |
| `.Release.xxx` | 설치 시점 정보. **필드명도 대문자**: `.Release.Name`, `.Release.Namespace`, `.Release.Revision` |
| `include "name" .` | `_helpers.tpl`에 정의된 named template 호출 |
| `\| default X` | 앞이 비어있으면 X 사용 (파이프 함수) |
| `\| nindent 4` | 새 줄로 시작하고 4칸 들여쓰기 |

**핵심 통찰**: `{{- if not .Values.autoscaling.enabled }} replicas: ... {{- end }}` 이 구조가 의미하는 것은 — HPA를 쓰면 `replicas`를 Deployment에 못 박지 않는다. HPA가 알아서 조정해야 하니까. HPA와 Helm이 같은 replicas 필드를 경쟁해서 관리하지 않게 하려는 의도다. 다만 생성 파일은 시작점이며, 자신의 앱에 맞는 probe·권한·resources 검토까지 대신해 주지는 않는다.

### 3.4 `_helpers.tpl` — 왜 분리되어 있나

`_`로 시작하는 파일은 Helm이 **K8s 매니페스트로 취급하지 않는다**. 대신 다른 템플릿에서 `include`로 불러쓰는 **헬퍼 함수 모음**이다. `helm create`가 생성하는 주요 헬퍼는 다음과 같다 (Helm 버전에 따라 추가 헬퍼가 더 있을 수 있다).

| 헬퍼 | 역할 |
|------|------|
| `my-app.name` | Chart 이름 (override 가능) |
| `my-app.fullname` | Release 이름 + Chart 이름 조합 (`my-first-my-app` 같은) |
| `my-app.chart` | `name-version` 형태 (`my-app-0.1.0`) |
| `my-app.labels` | 표준 K8s 레이블 세트 |
| `my-app.selectorLabels` | Pod selector용 부분 레이블 |
| `my-app.serviceAccountName` | ServiceAccount 이름 결정 (최신 버전에서 포함) |

이 헬퍼들이 분리된 이유는 **DRY(Don't Repeat Yourself)** 다. 같은 레이블 블록을 Deployment, Service, Ingress가 모두 써야 하는데, 매번 복붙하는 대신 `{{ include "my-app.labels" . }}` 한 줄로 끝낸다. Spring `@Component`처럼 런타임 객체를 만드는 개념이 아니라, **Thymeleaf의 fragment나 정적 유틸리티 메서드처럼 "텍스트 조각을 재사용"** 하는 발상에 가깝다. 런타임에는 이미 치환이 끝난 평범한 YAML만 클러스터로 간다.

### 3.5 `NOTES.txt` — 설치 후 안내문

설치가 끝나면 `helm install`이 화면에 출력하는 마지막 문구가 이 파일에서 나온다. 놀랍게도 **이것도 템플릿**이다.

```
1. Get the application URL by running these commands:
{{- if .Values.ingress.enabled }}
  http://{{ (index .Values.ingress.hosts 0).host }}/
{{- else if contains "NodePort" .Values.service.type }}
  export NODE_PORT=$(kubectl get -o jsonpath="..." services {{ include "my-app.fullname" . }})
  echo http://$NODE_IP:$NODE_PORT
{{- else if contains "LoadBalancer" .Values.service.type }}
  ...
```

`service.type`이 무엇인지, ingress가 켜졌는지에 따라 **사용자에게 보여줄 안내문이 동적으로 바뀐다**. 이것이 Helm의 사려 깊은 부분 중 하나다.

---

## 4. 한 사이클 돌려보기 — install → upgrade → rollback → uninstall

이 절은 선택 실행 경로다. 자신이 만든 격리 실습 클러스터, API 접근 권한, Node의 이미지 pull 경로가 필요하다. 아래 명령을 실행하기 전에 `--kube-context <실습-context>`를 명시하고 대상이 맞는지 확인한다. 여기 보이는 날짜·이름·IP·상태는 모두 **설명용 예상 출력** 이며 실제 설치 기록이 아니다. 기본 scaffold를 사용하므로 Release 이름 `my-first`와 helper가 만든 리소스 이름도 본편 사례와 다르다.

### 4.1 첫 설치

```bash
$ helm install my-first ./my-app --namespace helm-lab --create-namespace
NAME: my-first
LAST DEPLOYED: Mon May 25 15:32:01 2026
NAMESPACE: helm-lab
STATUS: deployed
REVISION: 1
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace helm-lab -l "app.kubernetes.io/name=my-app,app.kubernetes.io/instance=my-first" -o jsonpath="{.items[0].metadata.name}")
  ...
```

`STATUS: deployed`, `REVISION: 1`은 Helm이 첫 설치를 성공으로 기록한 예시다. `--wait` 없이 나온 이 상태만으로 앱이 Ready이거나 HTTP 요청에 응답한다고 판단할 수 없다. 기다리려면 사용 중인 Helm 버전의 `--wait` 동작과 timeout을 확인하고, Deployment rollout과 실제 Service 응답까지 분리해서 본다.

### 4.2 실제로 무엇이 만들어졌는지 확인

```bash
$ kubectl get all -n helm-lab -l app.kubernetes.io/instance=my-first
NAME                                    READY   STATUS    RESTARTS   AGE
pod/my-first-my-app-7b6f4c8c9d-x2vmz    1/1     Running   0          30s

NAME                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/my-first-my-app   ClusterIP   10.96.123.45    <none>        80/TCP    30s

NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/my-first-my-app   1/1     1            1           30s
```

Pod 이름이 `my-first-my-app-...`인 점에 주목하자. `_helpers.tpl`의 `my-app.fullname` 헬퍼가 만들어낸 결과다 — Release 이름(`my-first`)과 Chart 이름(`my-app`)이 합쳐져 있다. 같은 Chart를 다른 Release로 또 설치해도 충돌하지 않는 이유가 여기 있다.

### 4.3 Release 상태 확인

```bash
$ helm list -n helm-lab
NAME      NAMESPACE  REVISION  UPDATED         STATUS    CHART       APP VERSION
my-first  helm-lab    1         2026-05-25 ...  deployed  my-app-0.1.0  1.16.0
```

### 4.4 값 변경 → `helm upgrade`

replicas를 3개로 늘린다. 이 설명에서는 아래 명령을 **한 번만** 실행한 것을 revision 2로 가정한다.

```bash
helm upgrade my-first ./my-app -n helm-lab --set replicaCount=3
helm get values my-first -n helm-lab
helm get manifest my-first -n helm-lab
```

`helm get values`는 Release에 전달한 설정을, `helm get manifest`는 저장된 렌더링 결과를 보여 준다. 전체 계산된 values를 보고 싶으면 `helm get values --all`을 쓴다. 이 기록과 현재 Pod 상태는 같은 정보가 아니다. Pod 생성 실패나 외부 관리자의 변경을 찾으려면 `kubectl`로 live 리소스도 확인해야 한다.

다음은 위 명령 대신 선택할 수 있는 **대안** 이다. 둘을 모두 실행하면 upgrade가 두 번 기록되므로 뒤의 revision 숫자도 달라진다.

```bash
helm upgrade my-first ./my-app -n helm-lab -f prod-values.yaml
```

이 대안은 `prod-values.yaml`을 별도로 작성한 경우에만 사용한다. 우선순위는 Chart 기본값보다 `-f`가 높고, 그보다 `--set`이 높다. 여러 `-f`에서는 뒤에 지정한 파일이 같은 키를 덮는다. 운영 설정은 검토 가능한 파일로 남기고, 동적으로 전달하는 값도 최종 Release 기록과 맞춰 볼 수 있어야 한다.

### 4.5 이력 + 롤백

```bash
$ helm history my-first -n helm-lab
REVISION  UPDATED         STATUS      CHART         APP VERSION  DESCRIPTION
1         2026-05-25 ...  superseded  my-app-0.1.0  1.16.0       Install complete
2         2026-05-25 ...  deployed    my-app-0.1.0  1.16.0       Upgrade complete

$ helm rollback my-first 1 -n helm-lab
Rollback was a success! Happy Helming!

$ helm history my-first -n helm-lab
REVISION  UPDATED         STATUS      CHART         APP VERSION  DESCRIPTION
1         2026-05-25 ...  superseded  my-app-0.1.0  1.16.0       Install complete
2         2026-05-25 ...  superseded  my-app-0.1.0  1.16.0       Upgrade complete
3         2026-05-25 ...  deployed    my-app-0.1.0  1.16.0       Rollback to 1
```

**롤백도 새 리비전을 만든다는 점이 인상적**이다. "되돌렸다"는 사실 자체가 이력에 남는다. 운영 사고 사후 분석에서 이 흔적이 결정적인 단서가 된다.

### 4.6 정리

```bash
$ helm uninstall my-first -n helm-lab
release "my-first" uninstalled
```

이 명령은 `my-first`가 관리하는 Deployment/Service/ServiceAccount의 삭제를 요청한다. finalizer, hook, 리소스 보존 annotation과 CRD 같은 예외에 따라 남는 리소스가 있을 수 있다. `helm-lab` namespace는 이 명령으로 삭제되지 않는다. Helm 개념 글에서 강조했던 "Release 단위로 묶여 관리된다"의 가치가 가장 실감되는 순간이다.

---

## 5. 첫 디버깅 — 렌더링 결과를 미리 보는 3가지 방법

Chart를 수정하다 보면 반드시 마주치는 문제가 있다. **"내가 친 변수가 진짜 의도한 대로 치환됐을까?"** 클러스터에 실제로 적용하기 전에 확인하는 3가지 방법이 있다.

| 명령 | 하는 일 | 언제 |
|------|--------|------|
| `helm lint ./my-app` | Chart 구조 + YAML 문법 오류 검사 | 가장 먼저, CI에 넣기 좋음 |
| `helm template my-first ./my-app` | 렌더링 결과 매니페스트만 출력 (클러스터 안 건드림) | 변수 치환 확인 |
| `helm install my-first ./my-app --dry-run=client --debug --hide-secret` | client dry-run으로 설치 결과 미리 보기; 버전별 지원 옵션 확인 | 설치 직전 마지막 검증 |

특히 **`helm template`이 자주 쓰인다**. 다음처럼 파이프로 받아 보면 렌더링 결과가 그대로 나온다.

```bash
$ helm template my-first ./my-app --set replicaCount=5 | head -30
---
# Source: my-app/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-first-my-app
  ...
---
# Source: my-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 5    # ← 의도대로 치환됨
  ...
```

`helm template`·lint·client dry-run은 앱 실행 검증이 아니다. API 지원 여부·admission·스토리지·Node의 pull까지 모두 검증하지는 않는다. server dry-run은 클러스터에 요청하므로 별도 접근 권한과 대상 확인이 필요하다. 또한 `--dry-run --debug`는 Secret을 포함한 내용을 출력할 수 있으므로 공유 CI 로그에서는 지원되는 `--hide-secret` 옵션을 사용하고 values 자체의 민감정보도 남기지 않도록 한다.

Go 템플릿이 익숙해질 때까지 이 명령을 자주 쓰게 된다. 변수 한 줄 바꾸고 `helm template`으로 확인 → 또 바꾸고 확인하는 사이클이 학습에 매우 효과적이다.

---

## 6. 흔히 만나는 초보의 5가지 함정

| 함정 | 증상 | 해결 |
|------|------|------|
| **`helm install`을 다시 실행하면 에러** | "cannot re-use a name" | 같은 Release 이름으로 재설치 불가. `helm upgrade --install` 사용 (없으면 install, 있으면 upgrade) |
| **values 수정 후 적용 안 됨** | 클러스터에 변화 없음 | `helm upgrade`를 깜빡함. `helm install`은 첫 설치만 |
| **들여쓰기 한 칸 어긋남** | YAML 파싱 에러, 원인을 알 수 없는 메시지 | `helm template`으로 렌더링 결과 들여쓰기 확인. `\| nindent N` 활용 |
| **`--set` 값에 점/콤마 포함** | 파싱 어긋남 | 이스케이프하거나 `-f`로 빼기 |
| **Release 이름과 namespace 헷갈림** | "release not found" | `helm list -A`로 전체 namespace 조회. 기본은 현재 kubeconfig context의 namespace(미지정이면 `default`) |

이 5가지를 한 번씩 직접 만나보는 것이 가장 빠른 학습이다.

---

## 7. 다음에 무엇을 배워야 하는가

기본 Chart 한 바퀴를 돌렸다면 자연스러운 다음 학습 경로가 있다.

| 다음 주제 | 핵심 질문 |
|----------|----------|
| **Go 템플릿 함정과 패턴** | `_helpers.tpl`을 직접 작성하고, `tpl` 함수와 whitespace 제어를 마스터하는 단계 |
| **`values.yaml` 설계 패턴** | 환경별 분기, override 계층, `values.schema.json`으로 입력 검증 |
| **Subchart와 Library Chart** | 사내 공통 Chart를 만들어 여러 서비스가 공유하는 단계 |
| **`helm test`로 검증 자동화** | `templates/tests/` 안의 작업으로 배포 후 자동 검증 |
| **OCI Registry로 Chart 푸시** | Harbor 같은 OCI registry에 사내 Chart를 올리는 단계 |

환경별 Chart를 설계할 때는 helper가 만들어 낸 실제 이름과 selector부터 확인하면 좋다. 추상화가 잘되어 보여도 렌더링한 리소스 사이의 연결이 맞아야 한다.

---

## 8. 정리

Chart를 읽는 순서는 `Chart.yaml`의 신원, values의 입력, templates의 생성 규칙, 렌더링된 manifest다. 설치 후에는 Release 기록을 보고, 이어서 Deployment·Pod·Service를 확인한다. `NOTES.txt`의 접속 안내는 검증 결과가 아니라 Chart 작성자가 만든 안내문이다.

여기서 생긴 패키지를 외부에 전달하려면 저장·인증·버전 고정 문제가 남는다. [Harbor의 역할](Harbor-왜-회사들은-사내-컨테이너-레지스트리를-두는가.md)과 [Chart와 이미지의 협업 경로](Helm과-Harbor를-왜-같이-써야-하는가.md)에서 그 문제를 이어 간다.

## 생각해 볼 질문

1. **`appVersion`만 바꾸면 항상 다른 이미지가 배포될까?** 해당 템플릿이 그 필드를 이미지 문자열에 사용하는지에 달려 있다. image tag를 values로 명시했다면 `default`가 동작하지 않을 수도 있다.
2. **Release는 deployed인데 Service 호출은 실패할 수 있을까?** 렌더링·API 적용·controller 수렴·앱 준비·네트워크 연결이 서로 다른 단계이기 때문이다. 먼저 rollout과 Pod Ready 상태를 보고 Service 선택과 포트를 좁힌다.
3. **rollback 후 revision이 다시 1이 되지 않는 이유는 무엇일까?** 과거 선언을 재적용한 행위 자체를 새 revision으로 기록한다. 과거 데이터 상태까지 복원했다는 의미는 아니다.

## 출처

- [Helm 공식 문서 — helm create](https://helm.sh/docs/helm/helm_create/) — 공식 레퍼런스
- [Helm Chart Template Guide — Getting Started](https://helm.sh/docs/chart_template_guide/getting_started/) — 공식 입문 가이드
- [Helm 공식 문서 — Charts](https://helm.sh/docs/topics/charts/) — Chart 구조 상세
- [Helm install](https://helm.sh/docs/helm/helm_install/) — wait, dry-run과 Secret 출력 주의
- [Helm values](https://helm.sh/docs/chart_template_guide/values_files/) — 입력 우선순위
- [Helm get](https://helm.sh/docs/helm/helm_get/) — 저장된 Release 정보 조회
- [Helm 4 Overview](https://helm.sh/docs/overview/) — 2026-10-23 확인, 버전별 동작 차이
