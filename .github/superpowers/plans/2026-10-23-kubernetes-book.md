# Kubernetes Book Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 기존 Kubernetes 글을 외부 독자를 위한 연결된 한국어 기술서 본편 22장과 확장 읽기 14편으로 개정한다.
**Architecture:** Introduction을 목차 정본으로 두고 기존 경로와 자료를 보존하면서 장별 논리와 사례를 다시 쓴다. 장 묶음은 순차 집필하고 작성자와 다른 리뷰 및 전체 통합 검증을 거친다.
**Tech Stack:** Markdown, Mermaid, YAML, Python 정적 검증, 공식 문서, Claude/Antigravity 리뷰.
**Spec:** `.github/superpowers/specs/2026-10-23-kubernetes-book-design.md`

## Global Constraints

- 본문은 기본 인프라에 익숙한 백엔드 개발자 대상, 클러스터 동작의 이해와 설명이 우선이다. 책처럼 문단으로 인과관계를 쌓는다. 길이를 줄이는 것을 목표로 하지 않는다.
- 기존 경로와 H1 기술명 유지. `결론부터 말하면`, 장 연결, 생각해 볼 질문 2~3개와 해설, 공식 출처를 제공한다.
- 공통 설명용 앱 `order-api`, namespace `bookstore`, label `app: order-api`, 앱 port `8080`, Service port `80`, image `registry.example.com/book/order-api:1.0.0`. 가상 이미지·앱·health endpoint임을 밝힌다.
- 단순 예제 이외의 고유한 운영 지식은 후반 심화 또는 관련 확장 읽기에 보존한다. 문서 전체 삭제는 예정하지 않는다. 원문 백업은 저장소 밖, 경로는 work/kubernetes-book/backup-path.txt에 있다.
- YAML 파싱·문서 검증과 실환경 실행을 구분한다. 고객 시스템과 기본 kubeconfig에는 접근하지 않는다. 루트 README·실행 코드·워크플로는 변경하지 않는다. 커밋·푸시하지 않는다.
- 2026-10-23 기준 공식 출처를 확인한다. 버전 민감 검색은 2026 또는 2026-10을 포함한다. 검증되지 않은 현재 버전·릴리스 주장을 단정하지 않는다.
- 편집자의 세부 판단으로 계속 진행한다. 사용자의 '진행해'는 승인된 설계 안의 계획 작성과 개정 실행을 포함한다.

## Review Focus

1. 단순한 친절한 서문 추가로 끝나지 않고 본문 자체의 선행 개념·설명 순서·인과관계가 개선되는지 각 집필 작업에서 대조한다.
2. 제어 흐름과 데이터 경로, 객체와 실행 주체의 구분을 기술 리뷰에서 확인한다.
3. 가상 예제·과거 실측·이번 검증을 혼동시키는 문장을 각 집필 작업과 최종 검증에서 확인한다.
4. 변경된 heading으로 다른 문서의 깊은 링크가 끊어지는지 통합 검증에서 확인하고 참조를 수정하거나 호환 anchor를 남긴다.
5. 단순화하면서 운영상 중요한 조건을 삭제하지 않았는지 원문과 편집 기록을 대조한다.

## Task 1: 원문 보존과 작업 기록

**Files:** 기존 `kubernetes/*.md`, `tag-mapping.json` 읽기; `.github/superpowers/work/kubernetes-book/` 생성.
**Interfaces:** 원문 SHA-256, 백업 경로, 공통 설계와 파일 목록을 이후 작업에 전달한다.
- [x] 34개 원문과 태그를 저장소 밖에 백업하고 해시 manifest를 기록한다.
- [x] 승인된 설계와 현재 Git 상태를 기록한다.
- [x] 실제 수정 대상과 기록 경로가 승인 범위인지 확인한다.

## Task 2: 실행과 상태 유지 — 3~6장

**Files:** `Kubernetes-Pod.md`, `Kubernetes-ReplicaSet-Deployment.md`, `Kubernetes-Image-Tag-Digest.md`, `Kubernetes-ConfigMap-Secret.md` (모두 kubernetes/).
**Interfaces:** 설계 1부와 공통 앱을 소비, Pod 재시작/교체·소유·이미지·설정 반영 모델을 이후 장에 제공.
- [x] 네 원문 전체를 읽고 유지·이동·삭제할 개념을 기록한다.
- [x] 공식 출처를 확인하고 본문을 책의 설명 흐름에 맞춰 개정한다. 고유 심화 내용은 후반 선택 읽기로 보존한다.
- [x] YAML·링크·fence를 자체 점검하고 장별 질문/해설을 추가한다.
- [x] 변경 내역과 근거를 task-2-report.md에 남기고 별도 검토 후 필요한 수정 반영.

## Task 3: Service와 준비 상태 — 7~10장

**Files:** `Kubernetes-Service-Object.md`, `Kubernetes-Service-ClusterIP-NodePort-LoadBalancer.md`, `Kubernetes-Service-Internals.md`, `Kubernetes-Probe-Liveness-Readiness-Startup.md`.
**Interfaces:** Pod와 Deployment 이해를 소비, object 관계/노출 범위/실제 네트워크/건강 판단을 분리해 설명.
- [x] 네 원문 전문을 읽고 과거 실측 부분을 식별한다.
- [x] 역할·선택·DNS·EndpointSlice·네트워크 구현·Readiness의 연결을 개정하고 공식 근거 확인.
- [x] 새 예제와 과거 출력의 일치 여부, port-forward의 검증 한계를 확인한다.
- [x] 자체 검증과 task-3-report.md, 별도 검토 후 수정.

## Task 4: 외부 연결과 통신 경계 — 11~13장 및 네트워크 확장

**Files:** `Kubernetes-Ingress.md`, `Kubernetes-Gateway-API.md`, `Kubernetes-Ingress-vs-Egress.md`, `Kubernetes-Service-LoadBalancer-Cloud.md`, `Kubernetes-Egress-NetworkPolicy.md`.
**Interfaces:** Service·Probe 모델을 소비, 외부 진입점과 외부 의존성의 경계를 제공.
- [x] 다섯 원문 전문을 읽고 특정 구현체·버전 주장의 공식 근거 확인.
- [x] 본편 세 장 재구성, 확장 두 장 전제/오류/중복 보강. 2026년 상태는 날짜와 출처를 붙인다.
- [x] 리소스 선언과 controller/dataplane, 에어갭과 온프레미스를 구분한다.
- [x] 자체 검증과 task-4-report.md, 별도 검토 후 수정.

## Task 5: 저장·작업·배포·관측 — 14~18장

**Files:** `Kubernetes-Volume-PersistentVolume.md`, `Kubernetes-StatefulSet.md`, `Kubernetes-DaemonSet-Job-CronJob.md`, `Kubernetes-Deployment-Strategy.md`, `Kubernetes-Metrics-Server-Prometheus.md`.
**Interfaces:** 실행·요청 모델을 소비, 저장소 수명/배포 전환/관측 증거를 종합.
- [x] 다섯 원문을 읽고 공식 근거 확인.
- [x] 개념→관계→관찰 순으로 개정하고 기존 고유 운영 지식 보존. 동작을 과도하게 보장하는 표현 정정.
- [x] 저장소와 앱 복구, Job 중복, PDB·배포·자동 롤백, HPA·Node 용량을 구분.
- [x] 자체 검증과 task-5-report.md, 별도 검토 후 수정.

## Task 6: 권한·확장 — 19~21장 및 관련 확장

**Files:** `Kubernetes-ServiceAccount-RBAC.md`, `Kubernetes-CRD-Controller-Operator.md`, `Kubernetes-Admission-Webhook.md`, `Kubernetes-Service-Mesh.md`, `Istio-Ingress-Gateway-Ingress가-있는데-왜-VirtualService를-따로-쓸까.md`, `Kubernetes-External-Secrets-Operator.md`, `Kubernetes-GPU-Device-Plugin.md`.
**Interfaces:** API/Pod/Service 지식을 소비, 인증·인가·admission·controller의 구분을 제공.
- [x] 일곱 원문 전문을 읽고 공식 근거 확인.
- [x] 본편 세 장의 선행 개념과 설명 흐름을 재구성하고 네 확장 글은 필요한 보강을 적용.
- [x] 확장 리소스의 생성과 실제 처리, 신원과 네트워크 접근을 구분.
- [x] 자체 검증과 task-6-report.md, 별도 검토 후 수정.

## Task 7: 패키징·이미지 공급·CI 확장 읽기

**Files:** `Helm-쿠버네티스의-패키지-매니저는-왜-필요한가.md`, `Helm-내-첫-Helm-Chart-helm-create부터-helm-install까지.md`, `Harbor-왜-회사들은-사내-컨테이너-레지스트리를-두는가.md`, `Helm과-Harbor를-왜-같이-써야-하는가.md`, `Jenkins가-있는데-왜-Tekton이-빌드할까.md`, `Tekton의-Pipeline과-PipelineRun은-왜-따로-존재할까.md`, `Tekton-Triggers는-어떻게-git-push를-PipelineRun으로-바꿀까.md`, `Jenkins-Job에서-Tekton-EventListener로-webhook을-쏠-수-있을까.md`.
**Interfaces:** 본편의 리소스 모델을 실제 도구의 역할에 연결한다.
- [x] 여덟 원문 전문을 읽고 기술적 과장·현재 버전·예제 전제를 검토한다.
- [x] 필요한 본문 보강과 선행 읽기 연결. HTTP 응답·리소스 생성·실행·배포 성공을 구분한다.
- [x] 자체 검증과 task-7-report.md, 별도 검토 후 수정.

## Task 8: 책의 시작·전체 동작·종합 사례와 통합

**Files:** `Kubernetes-Introduction.md`, 신규 `Kubernetes-Architecture.md`, 신규 `Kubernetes-Troubleshooting-From-Apply-to-Request.md`, `tag-mapping.json`, 필요 시 기존 참조 글의 링크.
**Interfaces:** 앞 작업들의 개념을 연결하고 22장·14편의 정본 목차를 제공한다. 공통 nav는 통합 담당자만 일괄 편집.
- [x] Introduction 재집필, 아키텍처·종합 사례 집필, 22장과 14편 목차 및 이전/다음 연결.
- [x] 신규 두 파일 태그 등록, 기존 변경으로 끊기는 파일·anchor 링크 정리.
- [x] 전체 YAML/fence/태그/링크 확인, Mermaid 93개 렌더링과 핵심 그림 시각 확인.
- [x] 변경 원고마다 외부 검토를 실행하고 결과 본문을 읽어 타당한 지적 반영. 최종 SHA 일치 27편은 Claude PASS, Antigravity 11 PASS/16 ERROR. 9편은 최종 SHA 외부 재검토 없음. 재검토 상한·사용량 제한·마지막 제한 교정의 검증 경계를 editorial-report.md에 기록했으며 전체 외부 PASS를 주장하지 않는다.
- [x] 독립 최종 리뷰와 37개 항목 교정·범위 재검토 완료. 후속 5편·6항목은 공식 근거와 정적 검사로 교정. 편집 기록·검증 결과를 작성하고 커밋·푸시 없이 로컬 결과로 보존.

## 실행 판단 기록

- 사용자가 설계와 실행을 승인했으므로 추가 Plan 승인을 요구하지 않는다. 승인 범위의 작업 분해다.
- 문서 집필이므로 실행 코드에 대한 TDD는 해당하지 않는다. 예제 파싱·출처·링크·렌더링·독립 리뷰로 검증한다.
- 승인된 현재 저장소의 파일 경로에 결과를 남기고 백업을 보유한다. 별도 worktree 이동이나 commit은 하지 않는다.
- 순차 집필 담당자와 통합 담당자의 파일 소유권을 분리한다. 작업별 리뷰와 최종 교차 리뷰를 수행한다. 각 담당자는 다른 담당자의 파일을 고치지 않는다.
