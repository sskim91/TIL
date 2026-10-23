# Jenkins가 있는데 왜 Tekton이 빌드할까?

> **개발자를 위한 쉬운 쿠버네티스 · 확장 읽기** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서)

회사에는 이미 Jenkins가 돌아가고 있다고 가정하자. 그런데 새로 만드는 CI/CD 구성을 보면 **Jenkins는 실행 버튼만 누르고, 빌드는 Tekton 쪽에서 일어난다.** 왜 굳이 두 개를 쓸까? Jenkins가 그냥 다 하면 안 되나?

## 0. 먼저: Tekton이 대체 뭐하는 물건인가?

[Job과 Pod의 수명](Kubernetes-DaemonSet-Job-CronJob.md), [ServiceAccount와 RBAC](Kubernetes-ServiceAccount-RBAC.md), [CRD와 controller](Kubernetes-CRD-Controller-Operator.md)를 알고 있다면 Tekton을 새로운 마법처럼 볼 필요가 없다. 빌드의 원하는 상태를 API object로 기록하고 controller가 실행 Pod로 이어 주는 확장이다.

### "Tekton이 뭐예요?"

**Kubernetes에게 "이런 순서로 빌드해줘"라고 시키는 도구다.**

조금 더 정확히 말하면 — Tekton Pipelines는 CRD와 이를 처리하는 controller·webhook 같은 서버 구성 요소로 설치된다. 설치하면 Kubernetes에 두 가지가 생긴다.

1. **새로운 어휘.** `kubectl get pipeline`, `kubectl get pipelinerun` 같은 명령이 동작하게 된다. Kubernetes가 원래 모르던 `Pipeline`·`Task` 같은 단어를 알아듣게 만드는 것이다. (이렇게 어휘를 늘리는 방식을 **CRD** 라고 부른다)
2. **감시자.** 그 어휘로 만들어진 것들을 지켜보다가 실제로 일을 벌이는 프로그램. (이걸 **컨트롤러** 라고 부른다)

즉 Tekton을 설치한다는 것은 **Kubernetes에 "빌드"라는 말을 가르치고, 그 말을 알아듣는 직원 하나를 붙이는 일** 이다.

### "그래서 뭐하는 애예요?"

**빌드를 직접 하지 않는다. 빌드할 Pod를 띄운다.**

이 구분이 이 문서 전체에서 가장 중요하다. 순서를 따라가 보자.

1. `PipelineRun`을 API에 생성해 이번 실행의 소스·인자를 기록한다.
2. Pipelines controller가 이를 관찰하고 의존성에 맞춰 `TaskRun`을 만든다.
3. TaskRun 처리로 생성된 Pod를 scheduler가 Node에 배치한다.
4. 그 Node의 kubelet/runtime이 Step 컨테이너를 실행하며, 그 안의 도구가 clone·컴파일·이미지 빌드를 수행한다.
5. 실행 결과는 Run의 status에 기록된다. 완료 Pod와 PVC·로그의 보존·삭제는 별도 정리 정책에 따른다.

**컴파일하는 것은 Pod이고, Tekton은 그 Pod를 언제 어떤 순서로 띄울지 정하고 지시하는 층이다.** 공장으로 치면 Tekton은 작업 지시서를 쓰고 관리하는 사무실이지, 기계를 돌리는 작업장이 아니다.

### "그럼 Tekton이 빌드 서버인가요?"

Tekton을 도입해도 빌드를 수행할 컴퓨터와 저장 공간이 사라지는 것은 아니다. 서버 역할이 controller와 일회성 빌드 Pod가 사용하는 Node 자원으로 나뉜다. 따라서 용량은 controller replica 수뿐 아니라 동시 빌드 수·Step requests/limits·ephemeral storage·PVC·캐시·registry 대역폭으로 계획한다.

| 역할 | Jenkins | Tekton Pipelines |
|------|---------|------------------|
| 정의·일정·상태 관리 | Controller | controller와 API의 Run object |
| 실제 명령 실행 | 정적 또는 동적 Agent | TaskRun을 위해 만들어진 Pod의 Step 컨테이너 |
| Kubernetes 실행 환경 | Kubernetes 플러그인으로 동적 Agent 가능 | Pod 기반 실행을 기본 모델로 사용 |

Jenkins도 동적 Kubernetes Agent를 만들 수 있다. 이 글은 제품의 우열 비교가 아니라 **Jenkins는 승인·요청을 담당하고 빌드 실행 권한은 Tekton 쪽으로 모으는 구성** 을 설명한다. 기존 Jenkins의 Agent 운영·플러그인·권한 체계가 충분하다면 Jenkins만으로 구성하는 선택도 가능하다.

### 한 가지만 더: Tekton은 하나가 아니다

이름이 하나라 단일 프로그램처럼 보이지만, 필요한 것을 골라 설치한다. 이 시리즈에서 쓰는 건 두 개다.

| 구성요소 | 하는 일 | 언제 필요한가 |
|---|---|---|
| **Tekton Pipelines** | 빌드를 정의하고 실행 | 항상 (기반) |
| **Tekton Triggers** | 외부 HTTP 요청을 받는 창구를 제공 | **HTTP로 호출받으려면** |

설치할 때 매니페스트를 여러 번 `apply`하게 되는 이유가 이것이다. **Pipelines만 깔면 빌드는 되지만, 밖에서 HTTP로 부를 창구가 없다.**

Triggers가 항상 필수인 것은 아니다. Jenkins가 클러스터에 접근할 수 있다면 `kubectl`이나 `tkn` CLI로 빌드를 직접 만들 수도 있다. 다만 그러려면 **Jenkins에 클러스터 자격증명을 줘야 한다.** 어느 쪽을 택하느냐는 결국 "Jenkins에 무엇을 허용할 것인가"의 문제이며, 이 문서는 자격증명을 주지 않는 쪽(HTTP 호출)을 전제로 한다.

## 결론부터 말하면

**이 구성에서는 Jenkins가 승인과 실행 요청을 맡고, Tekton이 관리하는 Pod에서 실제 빌드를 실행하도록 책임을 나눴기 때문이다.** Jenkins의 한계 때문에 반드시 둘을 사용해야 하는 것은 아니다. Jenkins에는 HTTP 요청을 실행할 최소 환경이 필요하고, Tekton 쪽에는 실제 빌드를 감당할 Node·스토리지·권한이 필요하다.

```mermaid
flowchart LR
    J["Jenkins Job<br>승인·입력 구성"] -->|HTTP POST| EL["EventListener Pod"]
    EL -->|API create| PR["PipelineRun"]
    PR -.->|Pipelines controller가 관찰| TR["TaskRun"]
    TR -.->|controller가 실행 Pod 생성| P["Node의 빌드 Pod<br>clone·컴파일·이미지 생성"]
    G["Source Repository"] -->|소스 응답| P
    P -->|image push| R["Image Registry"]
    style J fill:#BF360C,color:#fff
    style EL fill:#1565C0,color:#fff
    style PR fill:#6A1B9A,color:#fff
    style TR fill:#6A1B9A,color:#fff
    style P fill:#2E7D32,color:#fff
    style G fill:#37474F,color:#fff
    style R fill:#37474F,color:#fff
```

화살표 중 점선은 API object의 상태를 관찰해 다음 object를 만드는 비동기 제어 관계다. PipelineRun이 TaskRun을 네트워크 호출로 직접 실행한다는 뜻은 아니다.

**여기서 가장 헷갈리기 쉬운 지점 하나를 미리 못 박고 가자. 소스 코드를 가져오는 것도 Jenkins가 아니라 Tekton 쪽이다.** Jenkins는 소스를 내려받아 전달하지 않는다. "이 저장소의 이 커밋을 빌드해줘"라는 **주소만** 넘긴다. 실제로 `git clone`을 하는 것은 Tekton이 띄운 빌드 Pod다.

이 문서에서 앞으로 **"Tekton이 빌드한다"** 고 쓰는 것은 편의상의 줄임말이다. 정확히는 **"Tekton이 띄운 Pod가 빌드한다"** 이며, 0절에서 본 대로 이 구분이 "빌드 서버가 몇 대냐"는 질문의 답을 바꾼다.

| | Jenkins | Tekton 쪽 |
|---|---|---|
| 역할 | CI 실행의 **진입점** | **지시자(컨트롤러) + 실행자(Pod)** |
| 소스 clone | ❌ | ✅ (Pod가) |
| 컴파일·테스트 | ❌ | ✅ (Pod가) |
| 이미지 빌드 | ❌ | ✅ (Pod가) |
| 이미지 push | ❌ | ✅ (Pod가) |
| 하는 일 | 파라미터 구성 + HTTP 요청 1번 | 위의 전부를 Pod에 시킴 |

## 1. "Jenkins는 있는데 빌드 서버가 없다"가 무슨 말일까?

이 말이 바로 안 와닿는다면, Jenkins가 어떻게 생긴 물건인지부터 봐야 한다. **Jenkins는 한 덩어리가 아니라 두 종류의 구성원으로 이루어진 조직이다.**

```mermaid
flowchart TD
    subgraph Jenkins["Jenkins 조직"]
        C["Controller (구 master)<br>웹 UI · Job 정의 · 스케줄링<br>자격증명 보관"]
        A1["Agent 1<br>(빌드 실행)"]
        A2["Agent 2<br>(빌드 실행)"]
        C -->|"이 Job 실행해"| A1
        C -->|"이 Job 실행해"| A2
    end

    style C fill:#1565C0,color:#fff
    style A1 fill:#2E7D32,color:#fff
    style A2 fill:#2E7D32,color:#fff
```

**Controller** 는 관리자다. 웹 화면을 띄우고, Job이 어떻게 생겼는지 기억하고, 언제 무엇을 돌릴지 정하고, 자격증명을 보관한다. 하지만 **빌드 명령 실행은 Agent에 맡기는 구성이 권장된다.**

**Agent** 는 실무자다. 실제로 `mvn package`를 실행하고, 이미지를 만들고, 테스트를 돌리는 것은 전부 Agent다. Jenkins 공식 문서의 표현을 빌리면 "Agent가 executor를 제공해 Controller가 요청한 작업을 수행한다".

### 왜 Controller가 직접 빌드하면 안 될까?

"그냥 Controller에서 빌드하면 되지 않나?" 기술적으로는 가능하다. Jenkins에는 `Built-In Node`라는 게 있어서 Controller 자신에게도 일을 시킬 수 있다. 그런데 **Jenkins 공식 보안 가이드는 이걸 하지 말라고 한다.** 이유가 두 가지다.

**첫째, 보안이다.** Controller에서 도는 빌드는 `$JENKINS_HOME`을 읽고 쓸 수 있다. 그 안에는 **모든 Job의 설정과 저장된 자격증명이 들어 있다.** 즉 누군가 빌드 스크립트에 코드 한 줄만 넣으면 Jenkins 전체의 비밀번호를 빼갈 수 있다. 그래서 CloudBees 문서는 아예 "Controller의 executor를 0으로 설정하라"고 권고한다.

**둘째, 안정성이다.** 빌드는 CPU와 디스크를 많이 먹는다. Controller가 빌드하느라 바쁘면 웹 UI가 느려지고 다른 Job의 스케줄링이 밀린다.

### 그래서 "빌드 서버가 없다"의 정확한 의미

정리하면 이렇다. **Jenkins Controller는 있는데, 빌드를 맡길 만한 Agent가 준비돼 있지 않은 상태.**

### 여기서 반드시 구분해야 할 것: "실행할 곳"과 "빌드할 곳"은 다르다

"빌드 서버가 없다"를 **"Jenkins에 아무것도 없다"** 로 읽으면 안 된다. 협의 자리에서 "그럼 Jenkins 쪽엔 아무 준비도 필요 없나요?"라는 질문이 반드시 나오는데, 답은 "아니오"다.

Jenkins Job이 `curl` 한 줄을 실행하려 해도, 그걸 **실행할 주체(executor)** 는 있어야 한다. Jenkins Pipeline의 `sh` 스텝은 어딘가에서 셸을 띄우는 일이라, 돌릴 곳이 없으면 적합한 executor가 할당될 때까지 Job은 큐에서 대기한다. 즉 필요한 것이 두 층으로 나뉜다.

| 무엇 | 이번 구성에서 | 왜 |
|------|--------------|-----|
| **빌드용 Agent**<br>(JDK·Maven·컨테이너 빌더·대용량 디스크) | **필요 없음** | 빌드를 Tekton이 하므로 |
| **최소 실행 주체**<br>(`curl`을 돌릴 executor 하나) | **필요함** | Jenkins가 HTTP 요청을 보내려면 |

**이 구분이 실무에서 갖는 의미가 크다.** 이 구성에서 Jenkins 운영자가 준비할 것은 "빌드 서버 도입"이 아니라 **"HTTP 요청 한 번 보낼 수 있는 최소 실행 환경 + Tekton까지의 아웃바운드 네트워크 경로"** 다. 요구사항의 무게가 완전히 달라진다.

그 최소 실행 환경은 여러 형태가 될 수 있다 — 가벼운 Agent 한 대, 혹은 `curl`만 돌릴 수 있는 제한적인 노드, 혹은 HTTP 호출을 대신해주는 Jenkins 플러그인. 어느 쪽이든 **빌드 도구가 설치된 서버를 새로 세우는 일에 비하면 비교가 안 되게 가볍다.**

그래서 이렇게 갈린다.

| Jenkins가 하는 일 | Jenkins가 안 하는 일 |
|------------------|---------------------|
| Job 정의·실행·이력 관리 | 소스 컴파일 |
| 파라미터 구성 | 컨테이너 이미지 빌드 |
| **HTTP 요청 보내기** | 이미지 레지스트리에 push |
| 승인·감사 흔적 남기기 | 대용량 작업 |

컨테이너 이미지를 빌드하려면 Agent에 **빌드 도구와 충분한 디스크·CPU** 가 있어야 하고, 그걸 새로 갖추는 건 서버를 도입하고 운영 인력을 붙이는 일이다. 금융권이라면 여기에 반입 심사와 보안 검토까지 붙는다.

**그럼 이미 Kubernetes 클러스터가 있는데, 거기서 빌드하면 안 되나?** 이게 바로 Tekton이 등장하는 지점이다.

## 2. Tekton은 왜 빌드 서버가 필요 없을까?

Tekton의 구조는 [Pipeline과 PipelineRun 문서](Tekton의-Pipeline과-PipelineRun은-왜-따로-존재할까.md)에서 자세히 다뤘지만, 지금 필요한 것은 딱 한 줄이다.

**Tekton에서 작업 하나가 실행되면 Kubernetes Pod 하나가 뜬다. 작업이 끝나면 그 Pod는 실행을 멈추고 CPU·메모리를 반환한다.**

완료 컨테이너는 CPU·메모리 실행 자원을 계속 사용하는 프로세스가 아니지만, Pod object·로그·이미지 캐시·PVC 데이터는 남을 수 있다. 정리 정책과 저장 비용을 별도로 고려한다.

이게 Jenkins Agent와 결정적으로 다른 점이다.

아래 비교는 **전통적인(정적) Jenkins Agent 구성** 기준이다. Jenkins도 Kubernetes 플러그인을 쓰면 빌드할 때만 Pod를 띄우는 동적 Agent가 가능하지만, 그러려면 **Jenkins에 클러스터 Pod 생성 권한을 줘야 한다** — 이번 구성이 피하려는 바로 그 지점이다.

| | Jenkins Agent (정적 구성) | Tekton |
|---|---|---|
| 실행 용량 | Agent 서버의 자원 | Node의 자원과 스토리지 |
| 실행 환경 수명 | 상시 Agent가 대기 | 빌드 Pod가 일회성으로 실행; 완료 object는 남을 수 있음 |
| 실행 환경 생성 | Agent 관리자가 준비 | controller의 Pod 생성 후 scheduler·kubelet이 실행 |
| 빌드 도구 설치 | Agent에 미리 설치 | **컨테이너 이미지에 들어 있음** |
| 동시 빌드 10개 | executor 10개 분량의 용량을 **미리 확보** | Pod 10개를 그때 생성 |
| 대기 비용 | Agent 유지 비용 | controller·Node·캐시·스토리지의 유지 비용 |

**세 번째와 네 번째 행이 핵심이다.** Jenkins에서 Java 17로 빌드하려면 Agent 서버에 JDK 17을 설치해야 한다. 다른 팀이 Java 21을 쓰면 그것도 설치해야 하고, 버전이 충돌하면 Agent를 나눠야 한다. **Agent는 관리 대상 서버다.**

Tekton은 각 작업이 "어떤 컨테이너 이미지로 실행할지"를 지정한다. Java 17이 필요하면 `maven:3.9-eclipse-temurin-17` 이미지를 쓰고, Java 21이 필요하면 다른 이미지를 쓴다. 도구 버전을 실행 이미지로 묶을 수 있다. 다만 registry pull, CPU 아키텍처, user·filesystem 권한, Maven 의존성 다운로드와 cache까지 확인해야 한다.

```yaml
# 구조 설명용 Task spec 발췌; workspace·권한·인증 준비는 별도
steps:
  - name: build
    image: maven:3.9-eclipse-temurin-17   # 도구 버전을 담은 실행 이미지
    script: mvn package
```

그래서 **"빌드 서버가 없어서 Tekton을 쓴다"는 말은 정확히는 "빌드 서버를 안 만들어도 되니까 Tekton을 쓴다"** 는 뜻이다. 이미 클러스터가 있어도 빌드 부하를 수용할 여유가 없다면 Node나 별도 빌드용 node pool을 늘려야 한다. 운영 앱과 같은 클러스터를 쓴다면 quota·동시 실행 수·배치 정책으로 간섭을 줄인다.

## 3. 그래서 Jenkins는 정확히 무엇을 넘기나?

이제 가장 실무적인 질문이다. Jenkins가 빌드를 안 한다면, Tekton에게 **무엇을** 줘야 할까?

답은 **"소스 코드"가 아니라 "소스 코드가 어디 있는지"** 다.

```mermaid
sequenceDiagram
    participant J as Jenkins Job
    participant T as EventListener
    participant P as TaskRun의 빌드 Pod
    participant G as Source Repository
    participant R as Image Registry

    rect rgba(230, 81, 0, 0.3)
        Note over J: Jenkins가 하는 일은 여기까지
        J->>T: POST { repoUrl, revision, imageTag }
        T-->>J: 접수 완료
    end
    rect rgba(46, 125, 50, 0.3)
        Note over P,R: API object와 controller를 거쳐 빌드 Pod 실행
        P->>G: git clone
        G-->>P: 소스 코드
        P->>P: 빌드 · 테스트 · 이미지 생성
        P->>R: 이미지 push
    end
```

넘기는 것과 넘기지 않는 것을 명확히 구분하자.

| 넘기는 것 (주소·지시) | 넘기지 않는 것 (실물) |
|---------------------|---------------------|
| 저장소 URL | 소스 코드 파일 |
| 커밋 해시 또는 브랜치 이름 | 빌드 산출물(jar 등) |
| 만들 이미지 이름과 태그 | 컨테이너 이미지 |
| 빌드 옵션·환경 구분(dev/prod) | — |

실제 요청은 이런 모습이 된다. 특별할 게 없다 — **JSON 하나를 HTTP POST로 보내는 것** 이 전부다.

```json
{
  "repoUrl":   "https://gitlab.example.com/team/order-api.git",
  "revision":  "3ac79d5c3a1d415351a12edbf68c1a8cbca2bcbf",
  "imageName": "registry.example.com/book/order-api",
  "imageTag":  "20260816-3ac79d5"
}
```

Jenkins Job 쪽에서는 이렇게 보낸다.

```groovy
stage('Tekton 빌드 요청') {
    steps {
        sh '''
            curl --fail --silent --show-error \
              -X POST "$TEKTON_URL" \
              -H 'Content-Type: application/json' \
              --data @payload.json
        '''
    }
}
```

**`curl` 한 줄이면 된다는 게 중요하다.** 빌드 도구도, Docker도, 큰 디스크도 필요 없다. 앞서 구분했듯 **빌드용 Agent 없이, `curl`을 실행할 최소 executor 하나만 있으면 된다** — 그래서 이 구조가 성립한다.

### 그럼 빌드가 실패하면 누가 알까?

여기서 자연스럽게 따라오는 질문이다. Jenkins는 요청만 보내고 끝나는데, 빌드 실패는 어떻게 확인할까?

**책임 경계가 권한과 함께 이동했다는 점을 알아야 한다.**

| 무엇이 실패했나 | 어디서 확인하나 |
|----------------|----------------|
| Tekton에 요청이 도달하지 못함 (네트워크·인증) | **Jenkins Job이 실패** |
| `git clone` 실패, 컴파일 오류, 이미지 push 실패 | **Tekton의 PipelineRun 상태와 로그** |

즉 **Jenkins Job이 초록불이라고 빌드가 성공한 게 아니다.** 이 예시처럼 HTTP 응답만 검사하면 Jenkins가 확인한 것은 요청이 접수됐다는 사실까지다. filter·권한 오류로 Run이 아예 없을 수도 있다. 이 간극을 그대로 두면 "Jenkins는 성공인데 이미지가 안 올라왔다"는 상황이 생긴다.

그래서 실제 구성에서는 **Jenkins가 Tekton의 실행 결과를 되확인하거나, Tekton이 끝난 뒤 결과를 알려주는 장치** 를 함께 설계한다. 구체적인 방법과 이때 물리는 함정은 [Jenkins Job에서 Tekton EventListener로 webhook을 쏠 수 있을까](Jenkins-Job에서-Tekton-EventListener로-webhook을-쏠-수-있을까.md)에서 다룬다 — 호출 방법, 인증, 응답 확인이 모두 거기 있다.

## 4. 이 구조에서 진짜 중요한 것: 권한이 이동한다

여기가 실무에서 가장 자주 놓치는 부분이고, 협의할 때 반드시 짚어야 할 지점이다.

**Jenkins가 빌드를 안 한다는 것은, Jenkins가 빌드에 필요한 권한도 갖지 않는다는 뜻이다.** 그 권한은 전부 Tekton 쪽으로 옮겨간다.

```mermaid
flowchart TD
    subgraph Old["Jenkins가 빌드하는 일반적인 구성"]
        J1["Jenkins Agent"] -->|"Git 자격증명"| G1["Source Repo"]
        J1 -->|"push 권한"| R1["Registry"]
    end
    subgraph New["이번 구성"]
        J2["Jenkins"] -->|"호출 권한만"| T2["Tekton"]
        T2 -->|"Git 자격증명"| G2["Source Repo"]
        T2 -->|"push 권한"| R2["Registry"]
    end

    style J1 fill:#BF360C,color:#fff
    style J2 fill:#BF360C,color:#fff
    style T2 fill:#2E7D32,color:#fff
    style G1 fill:#1565C0,color:#fff
    style G2 fill:#1565C0,color:#fff
    style R1 fill:#1565C0,color:#fff
    style R2 fill:#1565C0,color:#fff
```

정리하면 이렇게 나뉜다.

| 필요한 것 | 누가 가져야 하나 | 왜 |
|-----------|----------------|-----|
| 소스 저장소 읽기 권한 | **Tekton** | Tekton이 직접 clone하므로 |
| 이미지 레지스트리 push 권한 | **Tekton** | Tekton이 이미지를 만들고 올리므로 |
| Tekton 호출 권한 | **Jenkins** | Jenkins가 하는 유일한 일 |
| Tekton까지의 네트워크 경로 | **Jenkins → Tekton** | 요청이 이 방향으로 흐름 |

**이걸 놓치면 어떻게 되냐면**, Jenkins 쪽에 Git 자격증명을 준비해놓고 "왜 빌드가 안 되지?"라고 헤매게 된다. Tekton이 소스를 못 가져오는 게 원인인데, 자격증명은 엉뚱한 곳에 있는 것이다.

반대로 이 구조의 장점도 분명하다. **Jenkins에는 클러스터 자격증명이나 레지스트리 비밀번호를 두지 않아도 된다.** 금융권처럼 시스템 간 책임 분리를 따지는 환경에서 이건 설명하기 좋은 성질이다.

**다만 "그래서 Jenkins가 뚫려도 안전하다"고 말하면 과장이다.** Jenkins가 침해되면 자격증명을 직접 훔칠 수는 없지만, **Tekton을 호출해서 원하는 것을 빌드시킬 수는 있다.** `repoUrl`을 공격자 저장소로, `imageTag`를 운영 태그로 지정해 보내면 Tekton이 대신 이미지를 만들어 push해준다. 자격증명은 Tekton이 갖고 있으니 실행은 정상적으로 된다.

그래서 **자격증명을 옮기는 것만으로는 절반** 이고, Tekton 쪽에서 요청 내용을 검증해야 나머지 절반이 채워진다.

| 무엇을 검증하나 | 왜 |
|----------------|-----|
| 허용된 저장소와 revision인지 (타입·정확한 주소·commit 정책) | 임의 소스를 클러스터 안에서 빌드하지 못하게 |
| 허용된 출력 repository와 tag인지 (정확한 허용 목록) | 남의 이미지 태그를 덮어쓰지 못하게 |
| 요청자가 맞는지 (공유 토큰) | 아무나 호출하지 못하게 |

이 검증을 어디에 어떻게 거는지는 [Jenkins Job에서 Tekton EventListener로 webhook을 쏠 수 있을까](Jenkins-Job에서-Tekton-EventListener로-webhook을-쏠-수-있을까.md) 5·6절에서 다룬다.

<a id="5-한-가지-더-kubernetes-안에서는-docker-build를-못-쓴다"></a>

## 5. Kubernetes 안에서 이미지를 빌드하려면 실행 조건이 더 필요하다

마지막으로 알아두면 좋은 함정이다. "Tekton이 이미지를 빌드한다"고 했는데, **일반적인 Kubernetes 구성에서 Tekton은 `docker build`를 쓰지 않는다.**

이유는 이렇다. `docker build` 명령은 사실 혼자 일하지 않는다. **뒤에서 도는 Docker 데몬에게 "이거 만들어줘"라고 요청** 할 뿐이다. 그런데 Kubernetes Pod 안에는 그 데몬이 없다.

억지로 뚫는 방법이 두 가지 있긴 하다. 호스트의 `/var/run/docker.sock`을 Pod에 마운트하거나, Pod를 `privileged` 모드로 띄우는 것이다. Docker-in-Docker 같은 구성도 가능하지만 추가 daemon·권한·격리·스토리지 운영이 필요하다. Docker 소켓에 접근할 수 있다는 것은 사실상 그 노드 전체를 장악할 수 있다는 뜻이고, `privileged` Pod는 대부분의 기업 클러스터에서 정책으로 금지된다. 허용 여부는 조직의 보안 정책과 격리 설계에 따라 판단해야 한다.

그래서 Kubernetes에서는 **Docker 데몬 없이, 관리자 권한을 요구하지 않는 방식으로 이미지를 만드는 전용 도구** 를 쓴다. (Buildah는 데몬 자체가 없고, BuildKit은 자체 데몬 `buildkitd`를 쓰되 rootless로 띄울 수 있다.)

| 도구 | 상태 | 특징 |
|------|------|------|
| **Buildah** | 활발 (Red Hat / containers 프로젝트) | rootless 지원, Dockerfile 호환, 데몬 없음 |
| **BuildKit** | 활발 (Docker 진영) | 빠름, 캐싱 우수, 멀티아키텍처 |
| ~~kaniko~~ | **2025-06 아카이브** | 기존 예제에서 사용되지만 upstream은 archive |

**kaniko를 조심해야 한다.** 검색하면 "Kubernetes에서 이미지 빌드는 kaniko"라는 글이 압도적으로 많고, 오래된 Tekton 예제도 대부분 kaniko를 쓴다. 하지만 Google이 2025년 6월 저장소를 read-only로 전환했다.

### 이미 kaniko를 쓰고 있다면

**당장 고장나지는 않는다.** 아카이브는 "개발 중단"이지 "동작 중단"이 아니다. 이미 반입한 이미지가 자동으로 실행 불가가 되는 것은 아니다. 다만 과거 registry 경로의 현재 가용성이나 특정 클러스터의 실행 성공을 여기서 보장할 수는 없다.

다만 **아카이브된 프로젝트에는 새 CVE가 나와도 패치가 나오지 않는다.** 정기 이미지 취약점 스캔을 도는 환경이라면 새 CVE의 수정 가능성과 사용 기간을 검토해야 한다. "지금 당장 교체"는 아니고 **"계획은 지금"** 이 맞는 온도다.

선택지를 정리하면 이렇다.

| 경로 | 내용 | 걸리는 지점 |
|------|------|------------|
| 그대로 둔다 | Google 최종 이미지 `v1.24.0` 유지 | upstream 수정 중단에 따른 취약점·지원 위험 검토 |
| Chainguard fork | 해당 fork의 유지·지원 범위를 확인 | 해당 소스 저장소는 binary artifact를 게시하지 않음 (아래) |
| **Buildah로 이전** | Dockerfile 호환·권한·cache·인증 검증 후 Task 전환 | 새 이미지 반입 절차 |
| BuildKit으로 이전 | 성능·캐싱 우수 | 데몬 구성 필요, 권한 요건 확인 |

**Chainguard fork에는 함정이 있다.** kaniko를 만든 개발자들이 Chainguard로 옮겨 fork(`chainguard-forks/kaniko`)를 유지하고 있어서 좋은 선택처럼 보이지만, 2026-10-23 확인한 저장소 README는 다음과 같이 안내한다.

> Binary release artifacts such as container images are not published.

즉 **이 소스 저장소는 컨테이너 이미지 같은 binary artifact를 게시하지 않는다.** 이 README만으로 모든 유통 채널과 가격 조건을 일반화할 수는 없다. 공급자의 제품·라이선스·지원 계약을 따로 확인해야 한다. 소스에서 자체 빌드하는 경로를 선택하면 **"직접 빌드 + 반입"** 부담이 생긴다. 게다가 "No major feature work is planned" — 해당 fork가 안내하는 유지 범위를 확인해야 한다.

정리하면, **반입 절차를 다시 밟아야 하는 건 Chainguard든 Buildah든 마찬가지다.** 같은 비용이라면 활발히 개발되는 쪽으로 가는 편이 낫다.

### 전환할 때 실제로 물리는 것

Dockerfile을 재사용할 수 있는 경우가 많아도 Task의 image와 인자만 바꾸면 끝난다고 가정하면 안 된다. Dockerfile 지원 옵션, UID와 user namespace, seccomp·AppArmor, storage driver, 인증 파일 위치, cache 권한과 출력 digest를 같은 소스로 비교해야 한다. rootless는 무조건 어떤 Pod 보안 정책에서도 실행된다는 뜻이 아니다.

**진짜 비용은 두 가지다.**

**첫째, 반입 절차.** 이미 kaniko 이미지를 반입해둔 상태라면, 새 이미지(`quay.io/buildah/stable` 등)는 보안 검토와 반입을 처음부터 다시 받아야 한다. YAML 수정보다 이쪽이 몇 배 무겁다. **일정을 잡을 때 이걸 기준으로 삼아야 한다.**

**둘째, 캐시 모델이 다르다.** 이걸 모르고 옮기면 빌드가 느려진 원인을 못 찾는다.

| | kaniko | Buildah |
|---|--------|---------|
| 레이어 캐시 저장 위치 | registry (`--cache-repo`로 지정 가능) | local storage; 원격 registry cache도 선택 가능 |
| 활성 조건 | `--cache=true`로 활성화 | `--layers`로 활성화; 원격 `--cache-to`/`--cache-from`에도 `--layers` 필요 |
| 새 Pod에서 재사용 조건 | registry cache 접근 권한과 같은 cache 설정 | local storage를 보존·재사용하거나 원격 cache를 명시 |

Tekton이 새 TaskRun Pod를 만들 때 **캐시 저장소를 보존·재사용하지 않으면 local cache도 사라진다.** Buildah로 옮길 때는 `--layers` 활성화와 함께 저장소 보존 또는 원격 cache 설정을 확인해야 한다.

그리고 rootless로 돌릴 때 **스토리지 드라이버를 무엇으로 잡느냐** 가 성능을 좌우한다. 클러스터가 rootless overlay나 fuse-overlayfs를 지원하지 않으면 `--storage-driver=vfs`로 내려가야 하는데, **VFS는 각 레이어를 통째로 복사하는 방식이라 느리고 디스크를 더 쓴다.** 커널 버전과 보안 정책(user namespace, AppArmor 등)에 따라 갈리는 부분이라 **환경에서 직접 확인하고 빌드 시간을 미리 측정해두는 게 안전하다.**

이 이야기가 왜 중요하냐면, Tekton 빌드 Task를 열어봤을 때 `docker build`가 아니라 낯선 명령이 들어 있는 이유를 설명해주기 때문이다. 그건 이상한 게 아니라 **Kubernetes에서 이미지를 만드는 정상적인 방법** 이다.

## 6. 정리

Jenkins와 Tekton을 나누는 이점은 실행 도구의 숫자가 아니라 책임과 권한의 위치를 설명할 수 있다는 데 있다. Jenkins는 승인과 호출을, EventListener는 요청 검증과 Run 생성을, Pipelines controller는 TaskRun·Pod 제어를 담당한다. 실제 clone·컴파일·push는 Node 위의 Step 컨테이너에서 실행된다.

그만큼 결과도 나눠 보아야 한다. HTTP 접수, PipelineRun 생성, TaskRun 성공, image digest의 registry 존재, 배포 rollout·응답은 서로 다른 증거다. 빌드 성공만으로 배포가 일어나는 것도 아니다. 배포 Task나 GitOps 변경처럼 그 다음 단계를 명시적으로 설계해야 한다.

**에어갭 환경에서 짚어볼 점.** 빌더 이미지만 반입해도 Maven plugin·라이브러리·base image·Task resolver 다운로드가 남을 수 있다. 필요한 dependency를 내부 저장소와 cache로 공급하고, Node의 Step image pull 경로와 Step 안의 빌더 push·다운로드 경로를 나눠 확인한다.

### 더 깊이 들어가려면

이 문서는 "왜 이런 구조인가"만 다뤘다. 실제로 만들려면 순서대로 읽으면 된다.

1. [Tekton의 Pipeline과 PipelineRun은 왜 따로 존재할까](Tekton의-Pipeline과-PipelineRun은-왜-따로-존재할까.md) — Tekton이 빌드를 어떻게 구성하는지
2. [Tekton Triggers는 어떻게 git push를 PipelineRun으로 바꿀까](Tekton-Triggers는-어떻게-git-push를-PipelineRun으로-바꿀까.md) — 외부 요청을 받는 창구를 만드는 법
3. [Jenkins Job에서 Tekton EventListener로 webhook을 쏠 수 있을까](Jenkins-Job에서-Tekton-EventListener로-webhook을-쏠-수-있을까.md) — Jenkins에서 실제로 호출하는 법

---

## 생각해 볼 질문

1. **Jenkins도 Kubernetes Agent를 만들 수 있는데 왜 Tekton을 추가할까?** 필수 조합이 아니라 실행 정의·권한·운영 책임을 Kubernetes API와 Tekton controller로 모으려는 선택이다. 기존 Agent 체계로 요구가 충족된다면 추가 계층의 비용도 비교해야 한다.
2. **Jenkins의 호출 Job은 성공했는데 이미지가 없으면 어디부터 볼까?** eventID에 대응하는 PipelineRun 생성부터 보고, 이후 TaskRun·Step 로그와 registry push digest를 확인한다. 접수 응답은 빌드 결과가 아니다.
3. **빌드 Pod가 일회성이면 용량 계획이 필요 없을까?** 동시 빌드는 Node CPU·메모리·디스크·PVC·registry 대역폭을 경쟁한다. requests·quota·동시성·cache 정책으로 운영 앱과의 간섭을 제한해야 한다.

## 출처

- [Using Jenkins agents (Jenkins 공식 문서)](https://www.jenkins.io/doc/book/using/using-agents/) - Controller와 Agent의 역할 분담, executor 개념
- [Set up agents on CloudBees CI](https://docs.cloudbees.com/docs/cloudbees-ci/latest/setup/installing-build-agents) - Controller에서 빌드하면 안 되는 이유, executor 0 권고
- [Tekton Tasks 공식 문서](https://tekton.dev/docs/pipelines/tasks/) - Step이 컨테이너 이미지로 실행되는 구조
- [kaniko GitHub 저장소](https://github.com/GoogleContainerTools/kaniko) - 프로젝트 아카이브 공지 (2025-06 read-only), `--cache=true` 레이어 캐시
- [chainguard-forks/kaniko](https://github.com/chainguard-forks/kaniko) - 해당 소스 저장소의 binary artifact 미게시와 유지 범위
- [Fork Yeah: We're Bringing Kaniko Back (Chainguard)](https://www.chainguard.dev/unchained/fork-yeah-were-bringing-kaniko-back) - fork 배경과 상용 이미지 제공 정책
- [Buildah - replacement of Kaniko after its archival (Strimzi 제안서)](https://github.com/strimzi/proposals/blob/main/114-use-buildah-instead-of-kaniko.md) - Chainguard fork 대신 Buildah를 택한 판단 근거
- [buildah-bud(1) man page](https://man.archlinux.org/man/buildah-bud.1.en) - `--layers`·`--cache-to`/`--cache-from` 캐시 동작이 kaniko와 다른 점
- [Kaniko vs. Buildah: Rootless, Daemonless Container Builds in Kubernetes](https://ayedo.de/en/posts/kaniko-buildah-rootless-builds) - 데몬 없는 빌더가 필요한 이유, privileged·docker.sock의 보안 문제
- [How to Set Up Buildah for Rootless Container Image Builds](https://oneuptime.com/blog/post/2026-02-09-buildah-rootless-builds-kubernetes/view) - Buildah rootless 빌드 구성
- [Jenkins Controller Isolation](https://www.jenkins.io/doc/book/security/controller-isolation/) — built-in node 실행의 위험
- [Jenkins Kubernetes plugin](https://plugins.jenkins.io/kubernetes/) — 동적 Pod Agent
- [Tekton compute resources](https://tekton.dev/docs/pipelines/compute-resources/) — 실행 자원 요구량
- [Buildah 공식 build 문서](https://github.com/containers/buildah/blob/main/docs/buildah-build.1.md) — builder·cache·storage 옵션
- [BuildKit rootless](https://github.com/moby/buildkit/blob/master/docs/rootless.md) — rootless 실행 제약
