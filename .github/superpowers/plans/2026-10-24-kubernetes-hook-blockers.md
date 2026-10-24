# Kubernetes 책 리뷰 hook Blocker 4건 수정 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 1차 수정 중 리뷰 hook(Codex)이 Blocker로 짚은 기존 사실 오류 4건을 공식 문서 기준으로 고친다.

**Architecture:** 원고 3개 파일의 해당 문장과 표 행만 바꾼다. 장 구조·heading·예제 YAML은 건드리지 않는다. 각 Task는 "옛 문구 확인 → 고침 → 옛 문구 0건·새 문구 확인" 순서로 검증한다.

**Tech Stack:** Markdown, Python 3 정적 검사(`check_links.py`).

**Spec:** `.github/superpowers/work/2026-10-24-hook-findings.md`의 Blocker 4행(git 제외 로컬). 아래 Task마다 2026-10-24에 직접 확인한 공식 근거를 적었으므로 계획만으로 실행할 수 있다.

## Global Constraints

- 1차 계획(`2026-10-24-kubernetes-book-review-fixes.md`)의 Global Constraints를 그대로 따른다. 예외는 하나뿐이다: 커밋·push는 사용자 요청이 있을 때만 하고, 이번에도 실행 끝에 묻는다.
- 원고 편집은 Edit 도구로 한 파일씩 순서대로 한다. 리뷰 hook의 범위 밖 지적은 고치지 않고 `.github/superpowers/work/2026-10-24-hook-findings.md`에 이어서 기록한다.
- 새로 쓰는 사실에는 확인 날짜 `2026-10-24`를 붙인다. 공식 문서에 없는 일반화는 쓰지 않는다. 특히 RBAC의 Namespace 예외는 공식 문서가 명시한 `cluster-admin` 사례로만 서술한다.
- 모든 명령은 저장소 루트 `/Users/sskim/dev/TIL`에서 실행한다.

## Review Focus

1. **새 문장이 같은 장의 다른 곳과 모순되지 않아야 한다.**
   - RBAC: 312행 표와 598행 핵심 포인트가 316행의 예외와 같은 말을 해야 한다.
   - Admission: 186행 표의 "기본값" 열이 281행 본문과 맞아야 한다.
   - Task별 Step 3 grep이 세 위치를 모두 확인한다.
2. **Kyverno 서술이 "이 책의 예제"를 가리키면 안 된다.** 책에는 `ClusterPolicy` YAML이 없다(저장소 grep 결과 446행 한 곳뿐). Task 1 Step 3에서 `이 책의 Kyverno` 0건을 확인한다.
3. **8장 9.4절 바로 뒤 "selector를 바꿔야 한다면?" 절차와 새 설명이 어긋나면 안 된다.** 새 Deployment를 만들고 트래픽을 옮기는 절차는 그대로 유효하다. Task 2에서는 설명 문단만 바꾼다.
4. **같은 사실이 다른 장에도 있을 수 있다.**
   - Helm·Harbor 확장 글 361행의 출처가 Kyverno `cluster-policy` 문서를 가리킨다. 서술이 아니라 출처 링크라 이번 범위 밖으로 두고, 보고에만 적는다.
   - Task 4 Step 2에서 저장소 전체를 grep해 다른 장에 같은 오류 문장이 없는지 확인한다.
5. **hook이 다시 범위 밖 지적을 낼 수 있다.** 변경 파일이 아래 3개와 정확히 같은지 Task 4 Step 3에서 확인한다.

## 변경 파일

| 파일 (`kubernetes/`) | Task |
|---|---|
| `Kubernetes-Admission-Webhook.md` | 1 |
| `Kubernetes-ReplicaSet-Deployment.md` | 2 |
| `Kubernetes-ServiceAccount-RBAC.md` | 3 |

---

### Task 1: 29장 `caBundle` 필수 서술과 Kyverno `ClusterPolicy` 상태

**Files:**
- Modify: `kubernetes/Kubernetes-Admission-Webhook.md:186, 281, 446, 560 다음 줄`

**근거 (2026-10-24 확인):**
- https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/ (URL 절)
  - "expects the TLS certificate to be verified using system trust roots, so does not specify a caBundle"
  - Service reference 예시는 custom CA bundle을 쓴다.
- https://kyverno.io/blog/2026/08/20/announcing-kyverno-release-1.19/
  - "Official deprecation of `ClusterPolicy` and `Policy`, with removal planned for v1.20" (v1.20은 2026-11 예정)
  - `verifyImages` → `ImageValidatingPolicy`

- [ ] **Step 1: 옛 문구 확인**

```bash
grep -c 'API 서버가 그 인증서를 검증할 CA를 `caBundle`\|이 책의 Kyverno ClusterPolicy\|웹훅 서버의 TLS 인증서를 검증할 CA | 없음' kubernetes/Kubernetes-Admission-Webhook.md
```
Expected: `3`

- [ ] **Step 2: 수정**

186행 old:
```text
| `caBundle` | API 서버가 웹훅 서버의 TLS 인증서를 검증할 CA | 없음 |
```
new:
```text
| `caBundle` | API 서버가 웹훅 서버의 TLS 인증서를 검증할 CA | 생략하면 API 서버의 system trust roots |
```

281행 old:
```text
그래서 웹훅 호출은 HTTPS만 허용되고, API 서버가 그 인증서를 검증할 CA를 `caBundle`(PEM을 base64로 담은 필드)로 미리 알려줘야 한다.
```
new:
```text
그래서 웹훅 호출은 HTTPS만 허용되고, API 서버는 웹훅 서버의 인증서를 검증한다. `caBundle`(PEM을 base64로 담은 필드)은 그 검증에 쓸 CA를 지정하는 선택 필드다. 생략하면 API 서버의 system trust roots로 검증하므로, 사설 CA나 자체 서명 CA로 발급한 인증서라면 `caBundle`로 그 CA를 알려줘야 한다. 공인 CA는 `.svc` 같은 클러스터 내부 이름으로 인증서를 발급하지 않으므로, 클러스터 안 Service로 호출하는 웹훅은 보통 이 경우다.
```

446행 old:
```text
이 책의 Kyverno ClusterPolicy 이미지 검증은 [공식 실행 단계 설명](https://kyverno.io/docs/policy-types/cluster-policy/verify-images/overview/)처럼 mutation webhook 단계에서도 수행된다.
```
new:
```text
Kyverno의 기존 `ClusterPolicy` `verifyImages` 규칙은 [공식 실행 단계 설명](https://kyverno.io/docs/policy-types/cluster-policy/verify-images/overview/)처럼 mutation webhook 단계에서도 수행된다. 다만 2026-10-24 확인 기준 `ClusterPolicy`와 `Policy`는 Kyverno v1.19(2026-08-20)에서 deprecated되었고 v1.20에서 제거될 예정이다. 이미지 검증의 대체 정책 타입은 `ImageValidatingPolicy`이며, 새 정책 타입이 어느 webhook 단계에서 동작하는지는 이 설명을 그대로 적용하지 말고 해당 문서에서 확인한다.
```

출처 절의 `- [Kyverno — Installation / Troubleshooting](https://kyverno.io/docs/installation/) …` 줄 바로 아래에 한 줄을 추가한다:
```text
- [Kyverno 1.19 발표](https://kyverno.io/blog/2026/08/20/announcing-kyverno-release-1.19/) — `ClusterPolicy`·`Policy` deprecated(v1.20 제거 예정), `verifyImages` → `ImageValidatingPolicy`, 2026-10-24 확인
```

- [ ] **Step 3: 검증**

```bash
grep -c 'API 서버가 그 인증서를 검증할 CA를 `caBundle`\|이 책의 Kyverno\|웹훅 서버의 TLS 인증서를 검증할 CA | 없음' kubernetes/Kubernetes-Admission-Webhook.md
grep -c '선택 필드다\|생략하면 API 서버의 system trust roots' kubernetes/Kubernetes-Admission-Webhook.md
grep -c 'ImageValidatingPolicy' kubernetes/Kubernetes-Admission-Webhook.md
python3 -I .github/superpowers/work/check_links.py kubernetes | tail -1
```
Expected: `0`, `2`, `2`, `total 0`

---

### Task 2: 8장 9.4절 selector 고아화 일반화

**Files:**
- Modify: `kubernetes/Kubernetes-ReplicaSet-Deployment.md:627`

**근거 (2026-10-24 확인):** https://kubernetes.io/docs/concepts/workloads/controllers/deployment/ 의 "Label selector updates" 절
- selector는 생성 후 immutable이다. 바꾸려면 Deployment를 지우고 다시 만들어야 하며, Pod를 유지하려면 `--cascade=orphan`을 쓴다.
- Additions·Value Updates: 옛 ReplicaSet이 orphaned되고 새 ReplicaSet이 만들어진다.
- Removals: "Existing ReplicaSets are not orphaned, and a new ReplicaSet is not created" (지운 label은 기존 Pod·ReplicaSet에 남는다).

- [ ] **Step 1: 옛 문구 확인**

```bash
grep -c 'selector가 변경되면 기존의 모든 ReplicaSet과 Pod가' kubernetes/Kubernetes-ReplicaSet-Deployment.md
```
Expected: `1`

- [ ] **Step 2: 627행의 앞 두 문장 교체 (세 번째 문장 "안정적인 workload identity를 위해…"는 그대로 둔다)**

old:
```text
selector가 변경되면 기존의 모든 ReplicaSet과 Pod가 **고아(orphan)** 가 된다. 실행 중인 관리 집합의 경계가 바뀌어 소유 관계와 교체가 복잡해진다.
```
new:
```text
selector를 바꿀 수 있다면 결과가 변경 방향에 따라 갈린다. 조건을 더하거나 값을 바꾸면 새 selector가 기존 Pod를 고르지 못해, 옛 ReplicaSet은 Deployment와의 소유 관계를 잃은 **고아(orphan)** 가 되고 새 ReplicaSet이 따로 만들어진다. 조건을 빼면 기존 Pod도 계속 선택되므로 고아는 생기지 않지만, 지운 label은 기존 Pod와 ReplicaSet에 남는다. selector를 바꾸려고 Deployment를 `--cascade=orphan`으로 지우고 다시 만들 때도 같은 갈림이 생긴다.
```

- [ ] **Step 3: 검증**

```bash
grep -c 'selector가 변경되면 기존의 모든 ReplicaSet과 Pod가' kubernetes/Kubernetes-ReplicaSet-Deployment.md
grep -c '결과가 변경 방향에 따라 갈린다' kubernetes/Kubernetes-ReplicaSet-Deployment.md
grep -c '안정적인 workload identity를 위해 생성 시 selector를 정하며' kubernetes/Kubernetes-ReplicaSet-Deployment.md
```
Expected: `0`, `1`, `1`

---

### Task 3: 26장 RoleBinding의 Namespace 오브젝트 예외

**Files:**
- Modify: `kubernetes/Kubernetes-ServiceAccount-RBAC.md:312, 316, 555, 598`

**근거 (2026-10-24 확인):** https://kubernetes.io/docs/reference/access-authn-authz/rbac/#user-facing-roles
- cluster-admin: "When used in a RoleBinding, it gives full control over every resource in the role binding's namespace, including the namespace itself."
- admin: "This role does not allow write access to resource quota or to the namespace itself."

- [ ] **Step 1: 옛 상태 확인**

```bash
grep -c 'namespace itself\|그 Namespace 자체' kubernetes/Kubernetes-ServiceAccount-RBAC.md
grep -c '`RoleBinding`으로 주면 해당 namespace 안의 namespaced 리소스 |' kubernetes/Kubernetes-ServiceAccount-RBAC.md
```
Expected: `0`, `1`

- [ ] **Step 2: 수정**

312행 표 셀 old: `| **namespaced resource 규칙만 Binding의 네임스페이스 안** |` → new: `| **namespaced resource 규칙만 Binding의 네임스페이스 안** (Namespace 오브젝트 예외는 아래) |`

316행 끝 문장 old:
```text
Node·PV 같은 cluster-scoped resource 규칙은 이 Binding으로 부여되지 않으며, namespace 권한으로 변환되는 것도 아니다.
```
new:
```text
Node·PV 같은 cluster-scoped resource 규칙은 이 Binding으로 부여되지 않으며, namespace 권한으로 변환되는 것도 아니다. 예외는 그 Namespace 오브젝트 자체다. 공식 문서는 `cluster-admin`을 RoleBinding으로 주면 그 네임스페이스의 모든 리소스를 "네임스페이스 자체를 포함해" 완전히 제어한다고 설명한다. Namespace는 cluster-scoped 리소스지만, 이 경우 해당 Namespace를 수정하거나 삭제할 권한까지 생긴다. 반면 기본 `admin` 역할은 Namespace 자체에 대한 쓰기를 허용하지 않는다.
```

555행 old:
```text
`RoleBinding`으로 주면 해당 namespace 안의 namespaced 리소스 |
```
new:
```text
`RoleBinding`으로 주면 해당 namespace 안의 리소스와 그 Namespace 자체 |
```

598행 old:
```text
cluster-scoped 규칙까지 부여하는 조합은 아니다.
```
new:
```text
cluster-scoped 규칙까지 부여하는 조합은 아니다. 단, `cluster-admin`을 RoleBinding으로 주면 그 Namespace 자체도 제어할 수 있다.
```

- [ ] **Step 3: 검증**

```bash
grep -c '그 Namespace 자체' kubernetes/Kubernetes-ServiceAccount-RBAC.md
grep -c 'Namespace 오브젝트 예외는 아래\|예외는 그 Namespace 오브젝트 자체다' kubernetes/Kubernetes-ServiceAccount-RBAC.md
grep -c '`RoleBinding`으로 주면 해당 namespace 안의 namespaced 리소스 |' kubernetes/Kubernetes-ServiceAccount-RBAC.md
```
Expected: `2`, `2`, `0`

---

### Task 4: 전체 검증과 보고

**Files:** 원고는 읽기만 한다. 결과는 `.github/superpowers/work/2026-10-24-fix-report.md` 끝에 "## 2차: hook Blocker 4건" 절로 이어 쓴다.

- [ ] **Step 1: 링크·공백**

```bash
python3 -I .github/superpowers/work/check_links.py kubernetes | tail -1
git diff --check && echo diff-check-ok
```
Expected: `total 0`, `diff-check-ok`

- [ ] **Step 2: 같은 오류 문장이 저장소에 더 있는지**

```bash
command grep -rn --include='*.md' '모든 ReplicaSet과 Pod가 \*\*고아\|CA를 `caBundle`(PEM을 base64로 담은 필드)로 미리 알려줘야\|이 책의 Kyverno ClusterPolicy' . | command grep -v '\.github/superpowers/' | wc -l
```
Expected: `0` (수정 전에는 `3`: Admission 281·446행, ReplicaSet-Deployment 627행. 계획 파일 자신도 옛 문구를 담고 있으므로 `.github/superpowers/`를 제외한다.)

- [ ] **Step 3: 변경 범위**

```bash
git -c core.quotepath=false diff --name-only | sort
```
Expected: 위 "변경 파일" 3개와 정확히 같다.

- [ ] **Step 4: 최종 리뷰와 보고**

- 최종 리뷰어 1명(가장 성능 좋은 모델)에게 diff와 이 계획, 근거 URL을 주고 검토받는다.
- 결과를 보고서에 적는다.
- Review Focus 4번의 Helm·Harbor 출처 링크는 "범위 밖, 다음 정리 대상"으로 보고한다.
- 사용자에게 요약을 보고하고 커밋·push 여부를 묻는다.
