# Kubernetes Introduction

> **개발자를 위한 쉬운 쿠버네티스 · 1장** | [전체 목차](./Kubernetes-Introduction.md#이-시리즈의-읽는-순서) · [다음 장](./Kubernetes-Container-Fundamentals.md)

개발자를 위한 쉬운 쿠버네티스 — 프로그램을 배포하는 일에서 실행 상태를 관리하는 일까지

## 결론부터 말하면

**Kubernetes는 애플리케이션을 여러 서버에서 실행하고, 원하는 실행 상태를 계속 유지하도록 돕는 시스템이다.** 다만 이 문장을 이해하려면 먼저 프로그램이 실행되는 방식, 실행에 필요한 파일을 묶는 방법, 서버에 전달한 뒤에도 남는 운영 문제를 알아야 한다. 이 책은 그 출발점부터 설명한다. Docker를 먼저 능숙하게 다룰 수 있어야 읽는 책은 아니다.

프로그램을 한 번 시작하는 일과 서비스를 계속 제공하는 일 사이에는 거리가 있다. 실행 환경을 맞추고, 장애가 나면 복구하고, 새 버전으로 교체하며, 호출하는 쪽이 올바른 대상으로 접속하게 해야 한다. Kubernetes의 여러 설정은 이런 문제를 나누어 표현하기 위해 존재한다. 이름을 먼저 외우기보다 어떤 문제에서 나온 설정인지 이해하면, 실행이 멈춘 곳과 확인할 대상을 자신의 말로 설명할 수 있다.

## 1. 내 컴퓨터에서 실행한 프로그램을 서버로 옮긴다면

웹 애플리케이션을 만들어 로컬에서 HTTP 응답까지 확인했다고 생각해 보자. 이제 동료가 사용할 수 있도록 다른 서버에 배포하려 한다. 실행 파일이나 소스 코드를 복사했는데 서버에서는 시작되지 않는다. 개발 컴퓨터에 있던 Java나 Python이 없을 수도 있고, 필요한 라이브러리의 버전이 다를 수도 있다. 설정 파일 경로나 파일 접근 권한이 달라도 같은 프로그램이 다른 결과를 낸다.

여기서 배포는 단순한 파일 복사를 넘어선다. 어떤 실행 환경이 필요한지 정하고, 그 환경에서 프로그램을 시작하고, 다른 사람이 연결할 수 있도록 준비하는 일이다. 팀은 설치 문서, 자동화 스크립트, 서버 이미지 등 여러 방식으로 이 과정을 반복 가능하게 만든다. 컨테이너도 그중 하나다. 컨테이너의 구조는 다음 장에서 다루겠지만, 지금은 프로그램에 필요한 파일과 실행 환경을 일정하게 묶어 다루는 방법으로 받아들여도 된다.

환경을 맞춘 뒤 첫 요청에 응답하면 배포의 한 고비를 넘은 것이다. 하지만 서버를 재부팅하면 누가 앱을 다시 시작할까? 접속이 늘면 어느 서버에 실행 개수를 늘릴까? 새 버전으로 바꾸는 동안 기존 요청은 누가 처리할까? 이런 질문은 한 번의 실행 성공 이후에도 계속 남는다. 이 책이 다루는 대상은 바로 그 다음의 일이다.

## 2. 배포는 끝나도 실행 상태는 계속 바뀐다

앱이 실행 중이라는 사실은 영구적인 조건이 아니다. 프로그램 오류로 종료될 수 있고, 메모리가 부족해질 수도 있다. 서버 점검이나 네트워크 장애로 접근할 수 없게 될 수도 있다. 장애가 없어도 서비스는 바뀐다. 사용량이 늘고 새 버전을 내며, 보안 업데이트를 위해 실행 환경을 교체한다.

서버 한 대에서는 운영자가 프로세스 관리 도구와 스크립트를 조합해 이 일을 처리할 수 있다. 서버가 늘면 개별 앱의 실행뿐 아니라 서로의 관계도 관리해야 한다. 새 서버에 앱을 시작했더라도 요청을 나눠 보내는 장비가 그 주소를 모르면 사용자는 접근하지 못한다. 기존 앱을 먼저 내렸는데 새 앱이 준비되지 않았다면 실행 명령 몇 개는 성공했어도 서비스는 중단된다.

따라서 운영에서 묻는 질문은 “명령이 성공했나”만이 아니다. “지금 어떤 버전이 어디에서 실행 중인가”, “필요한 개수만큼 준비되어 있나”, “사용자는 그 앱까지 도달할 수 있나”를 함께 묻는다. 반복 가능한 명령에 더해, 바뀌는 상태를 관찰하고 조정하는 체계가 필요한 이유다.

## 3. Kubernetes를 배우기 전에 먼저 연결할 세 가지

첫째는 프로그램의 실행 방식이다. 실행 파일과 실행 중인 프로세스는 다르다. 컨테이너는 별도의 컴퓨터처럼 보일 때가 있지만, 이 책에서 다룰 일반적인 Linux 컨테이너는 Linux 커널을 공유하며 격리된 환경에서 실행되는 프로세스다. VM과 무엇이 다르고 macOS에서 Linux 컨테이너가 어떻게 가능한지부터 알아야, 컨테이너가 해결하는 환경 문제와 남기는 제약을 구분할 수 있다.

둘째는 실행할 내용을 전달하는 방식이다. 컨테이너 이미지라는 묶음을 만들고 저장소에 올리는 일과, 서버가 그 이미지를 받아 컨테이너를 실행하는 일은 서로 다른 단계다. 개발 컴퓨터에서 만든 이미지가 서버에 자동으로 생기지는 않는다. 이미지가 같아도 실행 시 전달한 설정이나 외부 DB가 다르면 앱의 결과는 달라질 수 있다.

셋째는 여러 서버의 운영 방식이다. 이미지를 전달할 수 있게 되면 어느 서버에서 몇 개를 실행할지, 장애와 배포 때 어떻게 바꿀지가 다음 문제가 된다. [컨테이너의 기초](./Kubernetes-Container-Fundamentals.md), [이미지의 생성과 전달](./Kubernetes-Image-Build-Ship-Run.md), [오케스트레이션이 필요한 이유](./Kubernetes-Why-Orchestration.md)는 이 순서대로 이어진다. 이후 첫 배포에서 이 개념을 실제 앱 하나와 연결한다.

## 4. 이 책에서 답하려는 질문

Kubernetes에 실행 설정을 제출했는데 앱이 시작되지 않는 상황을 만날 수 있다. 반대로 앱은 실행 중이라고 나오는데 사용자는 접속하지 못할 수 있다. 두 상황을 설명하려면 관리 설정이 전달되는 길과 사용자 요청이 전달되는 길을 나누어 보아야 한다. 설정을 받아들였다는 응답은 그 설정이 요구한 결과까지 완성됐다는 확인과 다르기 때문이다.

그래서 본편은 “배포 요청이 실행 중인 앱이 되는 과정”과 “사용자 요청이 그 앱에 도달하는 과정”을 차례로 따라간다. 이어서 앱이 교체되어도 데이터가 남는 조건, 새 버전으로 바꾸는 방법, 상태를 관찰하는 방법, 누가 설정을 바꿀 수 있는지를 다룬다. 실행과 연결, 저장과 권한은 함께 작동하지만 실패 지점을 이해하려면 각 책임을 나누어 배워야 한다.

뒤에서는 Kubernetes가 관리하는 대상을 종류별 API로 표현하는 리소스와, 현재 상태를 원하는 상태에 가깝게 맞추는 반복 동작을 배운다. 여기서 그 이름과 내부 절차를 모두 익힐 필요는 없다. 선행 개념과 첫 배포를 경험한 뒤 구조를 읽으면 각 구성 요소가 필요한 이유가 보인다.

## 5. 자동화가 해결하는 범위를 알아야 하는 이유

컨테이너와 Kubernetes를 사용해도 앱의 정상 동작 조건까지 자동으로 결정되지는 않는다. 프로세스가 살아 있어도 DB 인증에 실패할 수 있고, 새 버전이 시작되어도 기존 데이터와 호환되지 않을 수 있다. 앱을 다시 시작하는 기능만으로 데이터 불일치나 잘못된 설정이 고쳐지는 것은 아니다.

환경의 구현도 결과에 영향을 준다. 저장 공간이나 외부 접속 주소를 요청하는 설정을 작성할 수 있지만, 이를 실제로 제공할 장치와 프로그램이 준비되어 있어야 한다. Kubernetes 공식 문서 역시 애플리케이션 빌드, DB 같은 앱 수준 서비스, 종합적인 모니터링을 모두 내장한 제품으로 규정하지 않는다. 이 책에서는 선언한 의도와 그 의도를 실행하는 조건을 함께 확인한다. [Kubernetes Overview](https://kubernetes.io/docs/concepts/overview/)

에어갭 환경에서는 이 구분이 특히 잘 드러난다. 에어갭은 외부 인터넷과의 연결이 차단되거나 엄격하게 제한된 환경을 뜻한다. 평소 외부에서 받던 이미지와 패키지를 어디에서 공급할지, 내부 주소를 누가 해석할지, 사내 인증서를 어떻게 신뢰할지 준비해야 한다. 같은 Kubernetes 개념을 사용하더라도 이 조건이 갖춰졌는지는 별도로 확인해야 한다. 각 장의 에어갭 보충은 일반 원리를 실제 공급 경로에 연결하기 위해 둔다.

## 6. 이 책을 읽고 예제를 받아들이는 방법

이 책은 HTTP 앱을 개발해 본 일반 백엔드 독자를 기준으로 썼다. 서버를 직접 운영하거나 Docker를 사용해 본 경험은 필수가 아니다. 특정 언어와 프레임워크의 세부 구현보다 프로그램, 파일, 네트워크 연결이라는 공통 바탕에서 출발한다. 처음부터 모든 설정을 기억하려고 하기보다 “이 설정을 누가 읽고 무엇을 바꾸는가”라는 질문을 유지하며 읽으면 된다.

첫 배포 장부터는 주문 API를 공통 사례로 삼는다. 이때 필요한 앱 이름, 실행 포트, Kubernetes 설정을 처음부터 소개하고 이후 장에서 같은 관계를 반복해 사용한다. 첫 실행용 로컬 예제는 직접 만들고 확인하는 학습 경로다. 한편 기존 개념 설명에 나오는 `registry.example.com` 이미지 주소는 조직의 레지스트리를 가정한 자리표시자이며, 실제 공개 이미지 주소가 아니다. 로컬 예제를 실행할 때 그 주소의 이미지를 받을 수 있다고 가정해서는 안 된다.

일부 필드만 보여 주는 설정은 발췌로 표시하며, 별도의 준비가 필요한 예제는 조건을 먼저 설명한다. 앱이 제공하는 건강 확인 경로도 모든 프레임워크에서 자동으로 생기는 기능으로 취급하지 않는다. 설정을 읽어 이해한 것, 문법을 검사한 것, 실제 환경에서 실행한 것은 서로 다른 확인이다. 각 장의 질문도 명령어 암기보다 이 조건들이 달라질 때 결과를 설명할 수 있는지에 초점을 둔다.

## 이 시리즈의 읽는 순서

### 1부. 배포 요청은 어떻게 실행 중인 앱이 되는가

| 장 | 제목 | 중심 질문 |
|---|---|---|
| 1 | [Introduction](./Kubernetes-Introduction.md) | 코드 전달에서 서비스 운영까지 무엇을 준비해야 하는가? |
| 2 | [컨테이너의 기초](./Kubernetes-Container-Fundamentals.md) | 프로세스·VM·컨테이너는 실행 환경을 어떻게 나누는가? |
| 3 | [이미지의 생성과 전달](./Kubernetes-Image-Build-Ship-Run.md) | 파일 묶음이 실행할 서버까지 어떻게 전달되는가? |
| 4 | [오케스트레이션이 필요한 이유](./Kubernetes-Why-Orchestration.md) | 여러 서버의 배치·복구·접속·버전 교체를 누가 맞추는가? |
| 5 | [첫 배포](./Kubernetes-First-Deployment.md) | 직접 만든 이미지에서 HTTP 버전 확인까지 어떻게 연결하는가? |
| 6 | [클러스터의 동작 구조](./Kubernetes-Architecture.md) | apply 이후 누가 만들고, 배치하고, 실행하는가? |
| 7 | [Pod](./Kubernetes-Pod.md) | 컨테이너 재시작과 Pod 교체는 어떻게 다른가? |
| 8 | [ReplicaSet과 Deployment](./Kubernetes-ReplicaSet-Deployment.md) | 실행 개수와 버전은 어떻게 관리되는가? |
| 9 | [이미지 태그와 Digest](./Kubernetes-Image-Tag-Digest.md) | 같은 선언에서 다른 코드가 실행될 수 있는가? |
| 10 | [ConfigMap과 Secret](./Kubernetes-ConfigMap-Secret.md) | 설정은 언제 앱에 반영되는가? |

### 2부. 사용자 요청은 어떻게 앱을 찾아가는가

| 장 | 제목 | 중심 질문 |
|---|---|---|
| 11 | [Service라는 오브젝트](./Kubernetes-Service-Object.md) | Service와 Pod는 어떤 관계인가? |
| 12 | [Service의 접속 범위](./Kubernetes-Service-ClusterIP-NodePort-LoadBalancer.md) | ClusterIP, NodePort, LoadBalancer는 무엇이 다른가? |
| 13 | [Service 내부 동작](./Kubernetes-Service-Internals.md) | 이름과 주소가 실제 연결로 바뀌는 과정은 무엇인가? |
| 14 | [Probe](./Kubernetes-Probe-Liveness-Readiness-Startup.md) | 실행 중인 앱은 요청을 받을 준비도 된 것인가? |
| 15 | [Ingress](./Kubernetes-Ingress.md) | HTTP 경로를 누가 실제로 처리하는가? |
| 16 | [Gateway API](./Kubernetes-Gateway-API.md) | 진입점과 경로의 책임을 왜 나누는가? |
| 17 | [Ingress와 Egress](./Kubernetes-Ingress-vs-Egress.md) | 리소스 이름과 통신 방향은 어떻게 다른가? |

### 3부. 데이터와 작업의 생명주기를 다루는 방법

| 장 | 제목 | 중심 질문 |
|---|---|---|
| 18 | [Volume, PV, PVC](./Kubernetes-Volume-PersistentVolume.md) | 앱이 교체되어도 데이터는 어떻게 남는가? |
| 19 | [StatefulSet](./Kubernetes-StatefulSet.md) | 각 인스턴스의 이름과 저장소가 중요한 때는 언제인가? |
| 20 | [DaemonSet, Job, CronJob](./Kubernetes-DaemonSet-Job-CronJob.md) | 서비스·종료되는 작업·Node별 작업은 어떻게 다른가? |

### 4부. 실행 중인 시스템의 변경과 관찰

| 장 | 제목 | 중심 질문 |
|---|---|---|
| 21 | [자원 관리](./Kubernetes-Resource-Management.md) | 배치 판단과 실행 중 제한은 어떻게 다른가? |
| 22 | [스케줄링](./Kubernetes-Scheduling.md) | 실행할 Node는 어떤 조건으로 선택되는가? |
| 23 | [배포 전략](./Kubernetes-Deployment-Strategy.md) | 새 버전으로 바뀔 때 요청과 실행 상태는 어떻게 변하는가? |
| 24 | [관측과 확장](./Kubernetes-Metrics-Server-Prometheus.md) | 숫자는 누가 측정하고 무엇을 판단하는 데 쓰는가? |
| 25 | [로그와 Events](./Kubernetes-Logging-and-Events.md) | 실행의 흔적은 어디에 생기고 언제 사라지는가? |

### 5부. 클러스터의 권한과 확장을 이해하기

| 장 | 제목 | 중심 질문 |
|---|---|---|
| 26 | [ServiceAccount와 RBAC](./Kubernetes-ServiceAccount-RBAC.md) | 누가 어떤 API 작업을 할 수 있는가? |
| 27 | [워크로드 보안](./Kubernetes-Workload-Security.md) | 앱 프로세스의 권한과 파일·커널 접근을 어떻게 제한하는가? |
| 28 | [CRD, Controller, Operator](./Kubernetes-CRD-Controller-Operator.md) | 새 리소스를 등록하면 누가 그 의미를 실행하는가? |
| 29 | [Admission Webhook](./Kubernetes-Admission-Webhook.md) | 저장되기 전에 누가 요청을 바꾸거나 거절하는가? |
| 30 | [클러스터 운영](./Kubernetes-Cluster-Operations.md) | 앱을 지탱하는 Node·제어·저장소를 어떻게 유지하는가? |
| 31 | [배포부터 접속까지, 하나의 장애를 설명하기](./Kubernetes-Troubleshooting-From-Apply-to-Request.md) | 원하는 상태와 실제 상태가 어긋난 곳을 어떻게 찾는가? |

## 본편에서 이어 읽는 주제

아래 글은 본편을 이해하기 위한 필수 선행 학습이 아니다. 관련 업무를 만났을 때 본편의 모델을 실제 도구와 환경으로 확장하는 읽기다.

| 분야 | 문서 | 먼저 읽으면 좋은 본편 |
|---|---|---|
| 외부 연결 | [LoadBalancer와 클라우드](./Kubernetes-Service-LoadBalancer-Cloud.md) | 12·15장 |
| 통신 정책 | [Egress와 NetworkPolicy](./Kubernetes-Egress-NetworkPolicy.md) | 17장 |
| 서비스 간 통신 | [Service Mesh](./Kubernetes-Service-Mesh.md) → [Istio Gateway와 VirtualService](./Istio-Ingress-Gateway-Ingress가-있는데-왜-VirtualService를-따로-쓸까.md) | 16·26·29장 |
| 설정 공급 경로 | [Secret 전달 통합](./Kubernetes-Secret-Delivery-Integrations.md) | 10·26장 |
| 설정 공급 | [External Secrets Operator](./Kubernetes-External-Secrets-Operator.md) | 10·26·28장 |
| 장치 확장 | [GPU Device Plugin](./Kubernetes-GPU-Device-Plugin.md) | 7·20·28장 |
| 패키징 | [Helm의 역할](./Helm-쿠버네티스의-패키지-매니저는-왜-필요한가.md) → [첫 Helm Chart 읽기와 실습](./Helm-내-첫-Helm-Chart-helm-create부터-helm-install까지.md) | 10장 이후 |
| 이미지 공급 | [Harbor](./Harbor-왜-회사들은-사내-컨테이너-레지스트리를-두는가.md) → [Helm과 Harbor의 연결](./Helm과-Harbor를-왜-같이-써야-하는가.md) | 9장, Helm 개념 |
| CI 실행 | [Jenkins와 Tekton의 역할](./Jenkins가-있는데-왜-Tekton이-빌드할까.md) → [Pipeline과 PipelineRun](./Tekton의-Pipeline과-PipelineRun은-왜-따로-존재할까.md) | 20·26·28장 |
| 이벤트 연결 | [Tekton Triggers](./Tekton-Triggers는-어떻게-git-push를-PipelineRun으로-바꿀까.md) → [Jenkins에서 EventListener 호출하기](./Jenkins-Job에서-Tekton-EventListener로-webhook을-쏠-수-있을까.md) | Pipeline과 PipelineRun |

## 생각해 볼 질문

**로컬에서 잘 실행된 코드를 서버로 복사했는데 시작되지 않는다면 무엇부터 구분해야 할까?** 코드와 실행 환경을 나누어 보아야 한다. 실행기, 라이브러리, 파일 경로, 권한, 설정 중 무엇이 필요한지 확인해야 하며, 파일 전달의 성공만으로 배포가 완성됐다고 판단할 수 없다.

**프로그램을 한 번 시작하는 것과 서비스를 계속 운영하는 것은 무엇이 다를까?** 운영에는 종료 후 복구, 사용량 변화, 버전 교체, 접속 대상 관리가 포함된다. Kubernetes를 배우는 이유는 이런 변화 속에서 실행 상태를 지속해서 관리하는 구조를 이해하기 위해서다.

**설정이 저장됐다는 응답을 받으면 사용자가 앱을 사용할 수 있다고 말해도 될까?** 실행 환경과 이미지 공급, 앱 준비, 네트워크 연결이 뒤따라야 한다. 관리 요청의 성공과 앱을 실제로 사용할 수 있다는 확인을 나누어야 한다. 다음 장에서는 먼저 그 앱을 실행하는 프로세스와 컨테이너의 관계부터 살펴본다.

## 출처

공식 문서 확인 기준일: 2026-10-23. 이 도입부는 특정 최신 버전의 기능을 전제로 하지 않는다.

- [Kubernetes Overview](https://kubernetes.io/docs/concepts/overview/) — Kubernetes의 역할과 제공하지 않는 범위.
- [Docker: What is a container?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/) — 실행 환경을 분리하는 컨테이너와 VM의 관계.
- [Docker: What is an image?](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/) — 앱 파일을 묶어 전달하는 이미지의 역할.
