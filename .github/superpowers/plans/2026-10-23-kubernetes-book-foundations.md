# Kubernetes 책 선행 개념·운영·그림 보강 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development.

**Goal:** 승인된 권장안에 따라 개념의 선행 관계와 운영 학습 흐름을 완성한다.

**Architecture:** 기존 경로를 유지하고 10개 장을 추가/분리한다. 작업별 파일 소유권을 분리하고 마지막에 목차·그림·예제를 통합한다.

**Tech Stack:** Markdown, SVG, YAML, Docker, kind, Python 정적 검사.

**Spec:** `.github/superpowers/specs/2026-10-23-kubernetes-book-foundations-design.md`

## Global Constraints

- 한국어 책의 연결된 문단, 일반 백엔드 독자, 필요한 곳에 에어갭 보충.
- 기존 36개 파일 경로/H1 유지. 새 장은 Kubernetes로 시작하는 H1. 본편마다 질문 2~3개와 해설, 공식 출처.
- order-api/bookstore/app: order-api/8080→80은 첫 배포부터 사용. 그 전은 일반 앱으로 설명.
- 가상 registry.example.com 이미지를 실제 공개 이미지로 주장하지 않는다. 새 로컬 예제와 기존 가상 예제의 관계 명시.
- 작업 담당자는 배정 파일만 수정. 공통 nav·태그·그림 삽입 통합은 Task 4만 수행.
- 현재 checkout에서 변경, 커밋·푸시·고객 환경·기본 kubeconfig 조작 금지. .github/superpowers/work만 임시 기록.
- 2026-10-23 기준 공식 자료를 확인. 시간 민감 검색에는 2026을 포함. 버전 주장에 날짜·근거.
- 원고와 단순 설정 예제는 정적/실행 검증을 사용하며 구현을 복제하는 테스트를 추가하지 않는다.

## Review Focus

1. 배경 없이 주문 API/Pod/YAML로 건너뛰는가 — Task 1/4 선행 개념 읽기 검토.
2. VM/container/kernel/namespace 경계가 그림·본문에서 일치하는가 — Task 1/4 공식 대조·시각 확인.
3. 이전 문서의 운영 지식과 deep links가 이동 중 사라지는가 — Task 2/4 이동표·링크 검사.
4. 원고 예제와 실제 실행 확인을 혼동하는가 — Task 4 명령 기록·runtime 범위 표시.
5. 특정 보안·복구 설정이 운영 성공을 보장한다고 쓰는가 — Task 3 조건·책임 검토.

## Task 1: 컨테이너에서 Kubernetes까지 도입부 집필

**Files:** Modify `kubernetes/Kubernetes-Introduction.md`; Create `kubernetes/Kubernetes-Container-Fundamentals.md`, `kubernetes/Kubernetes-Image-Build-Ship-Run.md`, `kubernetes/Kubernetes-Why-Orchestration.md`.
**Interfaces:** 첫 배포 이전 지식 제공. 다음 글 `Kubernetes-First-Deployment.md`는 Task 4 생성. Introduction 목차는 Task 4 통합 담당자가 변경한다.
- [ ] 기존 Introduction과 관련 Docker 노트 읽기, 공식 Docker/Kubernetes 자료 확인.
- [ ] Introduction의 주문 API 시작을 제거하고 배포 환경·반복 운영 문제와 책의 필요성을 설명. 시작은 구체적 배포 상황이되 컨테이너를 이미 안다고 가정하지 않는다. 리소스 나열과 상세 reconciliation은 후속 장으로 연결. 기존 목차 구간은 유지한다.
- [ ] 프로세스/VM/컨테이너, kernel 공유와 격리·자원, Linux namespaces와 Kubernetes Namespace 차이, Docker Desktop Linux VM을 문단과 비교로 설명.
- [ ] 이미지 생성/파일층/실행층/레지스트리/push/pull, Docker·containerd·Kubernetes 책임, Compose 역할·범위, 외부 의존성을 설명. 명령은 짧은 설명용, 첫 실행 전체 절차는 Task 4로 연결.
- [ ] 다중 서버의 배치·복구·접속 대상·배포 전환에서 선언적 상태 관리의 필요성을 쌓고 관리 비용·대안·미도입 조건 설명. 새 기술이 이전 기술을 폐기한다는 서술 금지.
- [ ] 각 신규 장은 연결된 서술 최소 6개 논리 절과 질문/해설 2~3개. 분량을 채우는 목록 대신 설명을 충분히 작성. 실제 독자 관점으로 초안 읽고 정적 검사.
- [ ] 변경과 공식 출처/선행 개념 순서/검증을 보고하고 독립 작업 리뷰 반영.

## Task 2: 자원·배치·설정의 학습 깊이 분리

**Files:** Modify `kubernetes/Kubernetes-Pod.md`, `kubernetes/Kubernetes-ConfigMap-Secret.md`; Create `kubernetes/Kubernetes-Resource-Management.md`, `kubernetes/Kubernetes-Scheduling.md`, `kubernetes/Kubernetes-Secret-Delivery-Integrations.md`.
**Interfaces:** 기존 Pod/설정 본편에서 분리한 장을 목차에 제공. 다른 파일의 nav/링크는 Task 4가 통합한다.
- [ ] 두 원문 전문과 deep-link 사용처 확인, 보존·이동 목록 작성.
- [ ] Resource Management와 Pod Scheduling 상세 본문을 새 본편으로 옮겨 원리·조건·관찰 흐름으로 재집필. Pod 기본 자원 설명은 간결히 유지하고 기존 심화 heading/anchor에는 이동 안내를 남긴다.
- [ ] requests/limits/allocatable/CPU throttling/memory OOM/QoS/eviction/LimitRange/ResourceQuota를 조건과 함께 연결. Scheduling은 filter/score 개념, nodeSelector/affinity/taints/tolerations/topology/Pending 판단을 설명. 통과·생존 보장 오해 금지.
- [ ] ConfigMap·Secret 외부 저장소/CSI/GitOps 상세 연동은 새 확장 글로 이동. 기본 주입·업데이트·보안은 본편 유지. 원문 운영 지식은 보존하되 중복 정리. 기존 deep anchor 보존 또는 참조 이동을 보고.
- [ ] 새 3편에 선행 읽기·질문/해설·공식 출처. 정적 검사와 원문 보존 대조, 독립 작업 리뷰 반영.

## Task 3: 로그·실행 보안·클러스터 운영 보강

**Files:** Create `kubernetes/Kubernetes-Logging-and-Events.md`, `kubernetes/Kubernetes-Workload-Security.md`, `kubernetes/Kubernetes-Cluster-Operations.md`; Modify `kubernetes/Kubernetes-Metrics-Server-Prometheus.md` only to connect logging topic.
**Interfaces:** 후반 본편 세 장. 기존 RBAC/Admission/Volume/Deployment 문서와 연결. 마지막 종합 장애 글로 이어진다.
- [ ] 기존 관련 글·공식 문서를 확인하고 비어 있는 운영 연결 설명 집필.
- [ ] 로그: stdout/stderr→runtime/node→수집기→보관, kubectl logs/previous 범위, Events 수명, 로그/metrics/trace 차이와 요청 식별·민감값·시간·보존. 수집도구 설치 목록보다 흐름 설명.
- [ ] 실행 보안: API 권한과 프로세스 권한 분리, non-root/UID, capabilities, privilege escalation, read-only root와 writable volumes, seccomp, Pod Security Admission, 호환성 판단. 검증되지 않은 앱에 무조건 보안 필드 붙이는 예제 금지.
- [ ] 클러스터 운영: runtime/CNI/DNS/CSI 역할과 소유권, control plane/worker 장애·비동기 관측, cordon/drain/uncordon·PDB·용량·DaemonSet·local data, etcd 상태와 볼륨/DB 백업 구분, 복구 검증, 구성요소 버전·upgrade·CA/인증서·시간·에어갭 공급망을 연결. 고객 명령 실행 금지. 파괴적 복구 명령 대신 원리와 조건 제시.
- [ ] 각 장 최소 6개 논리 절, 질문/해설 2~3개, 공식 출처. 읽기 전용 진단 예제는 범위와 해석 설명. 정적 검사와 독립 작업 리뷰 반영.

## Task 4: 첫 배포 예제·그림·전체 통합

**Files:** Create `kubernetes/Kubernetes-First-Deployment.md`, `kubernetes/examples/first-deployment/` example files, `kubernetes/assets/book/` six SVG diagrams; Modify `kubernetes/Kubernetes-Introduction.md`, `kubernetes/Kubernetes-Architecture.md`, main chapter nav and references, `tag-mapping.json`; add durable figure source generator if useful in assets directory.
**Interfaces:** Tasks 1–3 manuscripts. Parent provides local runtime probe and figure prototypes. Final main sequence in work/chapters.json.
- [ ] 작은 HTTP 응답·버전 확인·health endpoint를 가진 실제 빌드 가능한 데모 준비. local image `book/order-api:1.0.0`/`2.0.0`, namespace `bookstore`, app port 8080/Service 80. 고객 데이터·외부 등록·실제 주문 로직 없음.
- [ ] Docker와 kind의 명시적인 로컬 context/전용 kubeconfig로 배포·조회·로그·HTTP 확인·업데이트 과정을 작성. 전제·첫 성공·관찰 결과·정리 범위 명확히. 데모와 기존 registry.example.com 가상 예제를 구분. 가능한 검증 수행, 불가능한 runtime 단계는 사실대로 표시.
- [ ] 6개 SVG를 생성·렌더·시각 확인하고 해당 장에 alt/caption과 삽입. kernel/VM 경계·이미지와 프로세스·관리/트래픽 경로·에어갭 반입 경계 오해 금지.
- [ ] 31장 본편·15편 확장 목차/이전다음/선행 링크를 일치시킴. Architecture 도입을 첫 배포의 관찰에서 연결. 새 10편 태그 등록. 기존 깊은 링크 확인.
- [ ] 전체 Markdown/YAML/이미지/태그/목차 검사, 새/변경 Mermaid 렌더, 보존·scope 확인. 실제 가능한 데모 테스트. 외부 CLI 리뷰는 가용성 확인 후 결과 전문 읽기, quota 오류는 재시도하지 않는다.
- [ ] 작업 리뷰와 최종 독립 전체 흐름 리뷰, 필요한 제한 수정, 편집·검증 보고. 커밋·푸시 없음.
