# Dockerfile과 docker-compose의 차이

"Dockerfile은 뭐고 docker-compose.yml은 뭐야?" Docker를 처음 접하면 이 두 파일이 헷갈린다. 둘 다 Docker와 관련된 건 알겠는데, 왜 두 개가 필요한 걸까?

## 결론부터 말하면

**Dockerfile은 "이미지 레시피"** 이고, **docker-compose.yml은 "오케스트라 악보"** 다.

| 구분 | Dockerfile | docker-compose.yml |
|------|------------|-------------------|
| **역할** | 이미지 **빌드** 방법 정의 | 컨테이너 **실행** 방법 정의 |
| **비유** | 요리 레시피 | 코스 요리 구성표 |
| **산출물** | Docker 이미지 | 실행 중인 컨테이너들 |
| **대상** | 단일 이미지 | 여러 컨테이너 + 네트워크 + 볼륨 |
| **명령어** | `docker build` | `docker compose up` |

```mermaid
flowchart LR
    subgraph Build["빌드 단계"]
        DF["Dockerfile"]
        IMG["Docker Image"]
        DF -->|docker build| IMG
    end

    subgraph Run["실행 단계"]
        DC["docker-compose.yml"]
        C1["Container 1<br>(App)"]
        C2["Container 2<br>(DB)"]
        C3["Container 3<br>(Redis)"]
        DC -->|docker compose up| C1
        DC -->|docker compose up| C2
        DC -->|docker compose up| C3
    end

    IMG -.->|이미지 사용| DC

    style DF fill:#1565C0,color:#fff
    style DC fill:#2E7D32,color:#fff
    style IMG fill:#E65100,color:#fff
```

## 1. 왜 두 개가 필요한가?

### 만약 Dockerfile만 있다면?

웹 애플리케이션을 Docker로 실행한다고 생각해보자. 앱 하나만 띄우면 될까?

```
실제로 필요한 것들:
- 웹 애플리케이션 (Node.js, Spring Boot 등)
- 데이터베이스 (PostgreSQL, MySQL)
- 캐시 서버 (Redis)
- 메시지 큐 (RabbitMQ)
- 리버스 프록시 (Nginx)
```

Dockerfile만으로 이걸 관리하려면?

```bash
# 이미지 빌드
docker build -t my-app .

# 네트워크 생성
docker network create my-network

# 각 컨테이너 실행 (매번 이 긴 명령어를...)
docker run -d --name postgres \
  --network my-network \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=mydb \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15

docker run -d --name redis \
  --network my-network \
  redis:7

docker run -d --name my-app \
  --network my-network \
  -p 3000:3000 \
  -e DATABASE_URL=postgres://postgres:secret@postgres:5432/mydb \
  -e REDIS_URL=redis://redis:6379 \
  my-app
```

**매번 이 명령어들을 기억하고 순서대로 입력해야 한다.** 팀원이 새로 합류하면? 문서 보고 따라하다 오타 나면? 실수하기 딱 좋다.

### docker-compose가 해결한다

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgres://postgres:secret@postgres:5432/mydb
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=mydb          # 없으면 기본 DB는 postgres라 앱의 mydb 접속이 실패한다
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7

volumes:
  postgres_data:
```

```bash
# 이 한 줄로 모든 게 실행된다
docker compose up -d
```

**그래서 두 개가 필요하다:**
- Dockerfile: 내 애플리케이션을 이미지로 만드는 방법
- docker-compose.yml: 모든 컨테이너를 어떻게 조합해서 실행할지

## 2. Dockerfile - 이미지 빌드 레시피

### Dockerfile이 하는 일

Dockerfile은 "이 순서대로 명령을 실행하면 내 앱이 담긴 이미지가 만들어진다"를 정의한다.

```dockerfile
# 베이스 이미지 선택
FROM node:24-alpine

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치 (package-lock.json 기준으로 정확히 설치)
COPY package*.json ./
RUN npm ci

# 소스 코드 복사
COPY . .

# 앱 빌드
RUN npm run build

# 실행 명령
CMD ["npm", "start"]
```

이 Dockerfile을 빌드하면:

```bash
docker build -t my-app:1.0 .
```

`my-app:1.0` 이라는 이미지가 생성된다. 이 이미지는:
- 어디서든 동일하게 실행 가능
- Docker Hub에 푸시해서 공유 가능
- Kubernetes에서 Pod로 실행 가능

### Dockerfile의 레이어 구조

모든 명령어가 레이어를 만드는 건 아니다. 파일시스템을 바꾸는 명령(`RUN`, `COPY`, `ADD`, 그리고 디렉토리를 새로 만드는 `WORKDIR`)만 이미지 레이어를 만든다. `CMD`, `ENV`, `LABEL` 같은 명령은 레이어 없이 이미지 설정(메타데이터)만 바꾼다. `FROM`도 새 레이어를 만드는 게 아니라, 베이스 이미지의 레이어들을 그대로 가져와 그 위에 쌓기 시작하는 지점이다.

```mermaid
flowchart TB
    subgraph Image["my-app:1.0 이미지"]
        L1["베이스 레이어들<br>FROM node:24-alpine"]
        L2["WORKDIR /app"]
        L3["COPY package*.json"]
        L4["RUN npm ci"]
        L5["COPY . ."]
        L6["RUN npm run build"]
    end

    Meta["이미지 설정 (레이어 아님)<br>CMD npm start"]

    L1 --> L2 --> L3 --> L4 --> L5 --> L6
    L6 -.-> Meta

    style L4 fill:#E65100,color:#fff
    style L5 fill:#1565C0,color:#fff
```

> 자세한 내용은 [Docker의 Copy-on-Write 전략](./Docker의-Copy-on-Write-전략.md) 참고

## 3. docker-compose.yml - 컨테이너 오케스트레이션

### docker-compose가 하는 일

docker-compose.yml은 "이 컨테이너들을 이 설정으로 함께 실행하라"를 정의한다.

```yaml
services:
  # 내 애플리케이션
  app:
    build: .                    # Dockerfile로 빌드
    ports:
      - "3000:3000"             # 포트 매핑
    environment:
      - NODE_ENV=production     # 환경 변수
    depends_on:
      - db                      # 의존성 (db가 먼저 시작)
    restart: unless-stopped     # 재시작 정책

  # 데이터베이스
  db:
    image: postgres:15          # 공식 이미지 사용
    volumes:
      - db_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=secret

volumes:
  db_data:                      # 명명된 볼륨
```

> **파일 이름:** 지금 Compose가 권장하는 기본 파일 이름은 `compose.yaml`이고, `docker-compose.yml`은 하위 호환으로 계속 읽는다(둘 다 있으면 `compose.yaml` 우선). 명령도 예전 Python 기반 `docker-compose`(V1, 2023년 지원 종료) 대신 Docker CLI 플러그인인 `docker compose`를 쓴다. 이 문서는 익숙한 이름인 `docker-compose.yml`로 설명한다.

### docker-compose가 관리하는 것들

| 구성 요소 | 설명 | 예시 |
|----------|------|------|
| **services** | 실행할 컨테이너들 | app, db, redis |
| **networks** | 컨테이너 간 통신 네트워크 | frontend, backend |
| **volumes** | 데이터 영속성 | db_data, uploads |
| **configs** | 설정 파일 | nginx.conf |
| **secrets** | 민감한 정보 | db_password |

```mermaid
flowchart TB
    subgraph compose["docker-compose.yml"]
        direction TB
        subgraph services["Services"]
            app["app<br>(Port 3000)"]
            db["db<br>(PostgreSQL)"]
            redis["redis<br>(Cache)"]
        end

        subgraph network["Network: default"]
            app <--> db
            app <--> redis
        end

        subgraph volumes["Volumes"]
            v1["db_data"]
        end

        db --- v1
    end

    style app fill:#1565C0,color:#fff
    style db fill:#2E7D32,color:#fff
    style redis fill:#C62828,color:#fff
```

## 4. 실제 사용 시나리오

### 시나리오 1: 로컬 개발 환경

```yaml
# docker-compose.yml
services:
  app:
    build: .
    command: npm run dev        # 파일 변경을 감시하는 개발 서버 (Dockerfile의 CMD를 덮어씀)
    ports:
      - "3000:3000"
    volumes:
      - .:/app                  # 소스 코드 마운트
      - /app/node_modules       # node_modules는 컨테이너 것 사용
    environment:
      - NODE_ENV=development

  db:
    image: postgres:15
    ports:
      - "5432:5432"             # 로컬에서 DB 접속 가능
    environment:
      - POSTGRES_PASSWORD=dev_password
```

```bash
# 개발 환경 실행
docker compose up
```

여기서 `command: npm run dev`가 빠지면 "코드를 고쳤는데 왜 반영이 안 되지?"라는 상황을 만나게 된다. bind mount(`.:/app`)는 호스트에서 고친 파일이 컨테이너 안에서도 바로 보이게 할 뿐, 실행 중인 프로세스를 다시 띄워주지는 않는다. Dockerfile의 `CMD ["npm", "start"]`는 빌드된 결과물을 실행하므로 소스가 바뀌어도 그대로다. 그래서 개발용 compose에서는 파일 변경을 감시하는 개발 서버(`package.json`의 `dev` 스크립트, nodemon 등)를 `command`로 띄워야 코드 수정이 바로 반영된다.

> bind mount 대신 Compose Watch(`develop.watch`)를 쓰면 "이 경로가 바뀌면 컨테이너로 동기화, `package.json`이 바뀌면 이미지 재빌드" 같은 규칙을 선언할 수 있다. `docker compose up --watch` 또는 `docker compose watch`로 실행한다.

### 시나리오 2: 프로덕션 환경

```yaml
# docker-compose.prod.yml
services:
  app:
    image: my-registry/my-app:${APP_TAG:-1.0}  # CI에서 빌드·푸시한 이미지 사용
    # ports 없음: replica 3개가 같은 호스트 포트를 잡을 수 없다. 외부 트래픽은 nginx가 받는다
    environment:
      - NODE_ENV=production
    deploy:
      replicas: 3                  # 3개 인스턴스 실행
      restart_policy:
        condition: on-failure

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro   # upstream을 app:3000으로 지정
    depends_on:
      - app
```

> **주의:** `deploy` 키는 원래 **Docker Swarm** 을 위해 설계되었지만, 현재 Compose(v2 이후)는 `deploy.replicas` 등 일부 속성을 실제로 지원한다(공식 Compose Deploy Specification 참고). 다만 Compose는 `up` 시점에 컨테이너 개수를 맞출 뿐, 이후 개수를 감시하며 다시 채우는 루프는 없다. Swarm·Kubernetes 수준의 자동 로드밸런싱이나 무중단 배포도 제공하지 않는다. 그래서 위 예시처럼 nginx를 앞에 두고 `app:3000`으로 프록시한다. Docker 내장 DNS가 `app`이라는 이름에 replica들의 IP를 돌려주기 때문이다. 같은 이유로 replica가 여럿인 서비스에 `ports: "3000:3000"`처럼 호스트 포트를 고정하면 두 번째 replica부터 `port is already allocated`로 실패한다. 임시로 `docker compose up --scale app=3`을 쓸 때도 마찬가지다.

### 시나리오 3: CI/CD 파이프라인

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: docker/login-action@v4
        with:
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_TOKEN }}
      - name: Build and push
        run: |
          # 빌드할 때 붙인 태그와 push하는 태그가 같아야 한다
          docker build -t my-registry/my-app:${{ github.sha }} .
          docker push my-registry/my-app:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        # GitHub runner는 작업이 끝나면 사라지는 임시 VM이라, compose는 운영 서버에서 실행한다
        # (SSH 키 설정과 서버의 docker-compose.prod.yml 배치는 생략)
        run: |
          ssh deploy@my-server \
            "cd /srv/my-app && APP_TAG=${{ github.sha }} docker compose -f docker-compose.prod.yml up -d"
```

이미지 빌드(Dockerfile)는 CI에서 한 번만 하고, 실행(docker-compose)은 그 이미지를 받아 서버에서 한다. 이 문서의 주제인 두 파일의 분업이 파이프라인에서도 그대로 드러난다.

## 5. JetBrains IDE에서 Dockerfile만으로 개발하기

"docker-compose 없이 Dockerfile만으로 개발할 수 있나요?" **가능하다.** JetBrains IDE(IntelliJ, PyCharm, WebStorm 등)는 Dockerfile을 직접 인식해서 빌드하고 실행할 수 있다.

### IDE가 해주는 일

JetBrains IDE의 Docker 플러그인이 하는 일은 다음 명령과 같다:

```bash
# 1. Dockerfile로 이미지 빌드
docker build -t my-app:latest .

# 2. 빌드된 이미지로 컨테이너 실행
docker run -d -p 8080:8080 --name my-app my-app:latest
```

즉, **레지스트리 없이 로컬에서 빌드 → 실행** 이 가능하다.

### 설정 방법

1. **Docker 플러그인 확인**: `Settings → Plugins → Docker` (기본 설치됨)

2. **Docker 데몬 연결**: `Settings → Build, Execution, Deployment → Docker`
   - macOS/Windows: Docker Desktop 사용
   - Linux: Unix socket (`unix:///var/run/docker.sock`)

3. **Run Configuration 생성**: `Run → Edit Configurations → + → Docker → Dockerfile`

Run Configuration의 주요 설정 예시는 다음과 같다.

| 항목 | 값 |
|------|-----|
| Name | `My App Docker` |
| Dockerfile | `./Dockerfile` |
| Image tag | `my-app:dev` |
| Container name | `my-app-dev` |
| Bind ports | `8080:8080` |
| Bind mounts | `./src:/app/src` (핫 리로드용) |
| Environment | `NODE_ENV=development` |

### Dockerfile만 사용 vs docker-compose 사용

| 상황 | Dockerfile만 | docker-compose |
|------|-------------|----------------|
| 단일 컨테이너 앱 | ✅ 충분 | 불필요 |
| DB, Redis 등 의존성 필요 | ❌ 번거로움 | ✅ 편리 |
| 팀 공유 | ❌ 각자 설정 필요 | ✅ 설정 파일 공유 |
| CI/CD 연동 | ✅ 가능 | ✅ 가능 |

### 실제 워크플로우 예시

**단일 Spring Boot 앱 개발:**

```dockerfile
# Dockerfile
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY build/libs/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

JetBrains에서:
1. `Run → Edit Configurations → Docker → Dockerfile` 선택
2. Before launch에 `Gradle build` 추가
3. ▶️ 버튼 클릭 → 빌드 + 이미지 생성 + 컨테이너 실행

```mermaid
flowchart LR
    subgraph IDE["JetBrains IDE"]
        Code["소스 코드"]
        Build["Gradle/Maven<br>Build"]
        DF["Dockerfile"]
        Run["Run Config"]
    end

    subgraph Docker["Docker"]
        IMG["Image<br>(로컬)"]
        Container["Container"]
    end

    Code --> Build --> DF
    Run -->|docker build| IMG
    IMG -->|docker run| Container

    style Run fill:#1565C0,color:#fff
    style Container fill:#2E7D32,color:#fff
```

### 언제 docker-compose로 전환해야 하나?

```
처음: Dockerfile만으로 시작
  ↓
"DB 연결해야 하는데..."
  ↓
docker run으로 PostgreSQL 따로 실행? → 매번 귀찮음
  ↓
docker-compose.yml 작성 시점!
```

```yaml
# 이제 docker-compose가 필요한 시점
services:
  app:
    build: .                    # Dockerfile 사용
    ports:
      - "8080:8080"
    depends_on:
      - db

  db:
    image: postgres:15          # 공식 이미지 (Dockerfile 불필요)
    environment:
      - POSTGRES_PASSWORD=secret
```

> **핵심:** Dockerfile만으로 개발 가능하지만, 의존성(DB, 캐시 등)이 늘어나면 docker-compose가 편해진다.

## 6. Kubernetes와의 관계

"Dockerfile은 k8s 같은 컨테이너에 올릴 때 자동으로 적혀있는 대로 도커라이징 된다는 개념인가?" 라는 질문에 답하자면:

### Kubernetes가 사용하는 것

Kubernetes는 **이미 빌드된 이미지** 를 사용한다. Dockerfile을 직접 읽지 않는다.

```mermaid
flowchart LR
    subgraph Dev["개발 단계"]
        DF["Dockerfile"]
        Build["docker build"]
        IMG["Image<br>my-app:1.0"]
    end

    subgraph Registry["Registry"]
        Hub["Docker Hub<br>또는<br>Private Registry"]
    end

    subgraph K8s["Kubernetes"]
        API["API Server"]
        Worker["Node<br>(kubelet + containerd)"]
        Pod["Pod"]
    end

    Manifest["Deployment YAML"]

    DF --> Build --> IMG
    IMG -->|docker push| Hub
    Manifest -->|kubectl apply| API
    API -->|Pod 배치| Worker
    Hub -->|image pull| Worker
    Worker --> Pod

    style DF fill:#1565C0,color:#fff
    style Hub fill:#E65100,color:#fff
    style Pod fill:#2E7D32,color:#fff
```

`kubectl apply`는 Deployment 같은 매니페스트를 API Server에 제출할 뿐이다. 이미지를 레지스트리에서 받아오는 건 Pod가 배치된 노드의 kubelet과 컨테이너 런타임이다. 또 Kubernetes 1.24에서 kubelet에 내장돼 있던 `dockershim`이 제거되어, 대부분의 클러스터는 containerd·CRI-O 같은 CRI 런타임으로 컨테이너를 실행한다(Docker Engine을 계속 쓰려면 `cri-dockerd` 어댑터가 필요하다). 어떤 런타임이든 Dockerfile로 만든 이미지는 OCI 표준 형식이라 그대로 쓸 수 있다.

### 각 도구의 역할

| 단계 | 도구 | 역할 |
|------|------|------|
| 이미지 빌드 | **Dockerfile** | 애플리케이션을 이미지로 패키징 |
| 이미지 저장 | **Docker Registry** | 빌드된 이미지 저장/배포 |
| 로컬 실행 | **docker-compose** | 로컬에서 여러 컨테이너 실행 |
| 프로덕션 실행 | **Kubernetes** | 클러스터에서 컨테이너 오케스트레이션 |

### docker-compose vs Kubernetes

| 기능 | docker-compose | Kubernetes |
|------|---------------|------------|
| **규모** | 단일 호스트 | 멀티 호스트 클러스터 |
| **자동 복구** | 제한적 (`restart` 정책, unhealthy 컨테이너는 재시작 안 함) | 완전 자동 (Health check, Self-healing) |
| **스케일링** | 수동 (`scale` 명령) | 자동 (HPA, VPA) |
| **로드밸런싱** | 기본적 | 고급 (Ingress, Service Mesh) |
| **롤링 업데이트** | 제한적 | 기본 지원 |
| **용도** | 개발, 테스트, 소규모 운영 | 프로덕션 운영 |

```yaml
# docker-compose.yml에서...
services:
  app:
    image: my-app:1.0
    expose:
      - "3000"        # replica가 여럿이면 호스트 포트(ports)를 고정할 수 없다
    deploy:
      replicas: 3

# Kubernetes에서는...
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: my-app:1.0
        ports:
        - containerPort: 3000
```

## 7. 언제 무엇을 사용하는가?

### 판단 기준

```mermaid
flowchart TD
    Q1{"내 앱을 이미지로<br>만들어야 하나?"}
    Q2{"여러 컨테이너를<br>함께 실행해야 하나?"}
    Q3{"프로덕션 환경에서<br>고가용성이 필요한가?"}

    A1["Dockerfile 작성"]
    A2["docker-compose.yml 작성"]
    A3["Kubernetes 사용"]

    Q1 -->|Yes| A1
    A1 --> Q2
    Q2 -->|Yes| A2
    A2 --> Q3
    Q3 -->|Yes| A3
    Q3 -->|No| Done["docker-compose로 충분"]

    style A1 fill:#1565C0,color:#fff
    style A2 fill:#2E7D32,color:#fff
    style A3 fill:#E65100,color:#fff
```

### 정리

| 상황 | 필요한 것 |
|------|----------|
| 내 코드를 컨테이너로 패키징 | **Dockerfile** |
| 공식 이미지만 사용 (nginx, postgres 등) | docker-compose.yml (Dockerfile 불필요) |
| 로컬 개발 환경 구성 | **Dockerfile + docker-compose.yml** |
| CI/CD에서 이미지 빌드 | **Dockerfile** |
| Kubernetes 배포 | **Dockerfile** (빌드) + **K8s manifests** (실행) |

## 8. 자주 하는 실수

### 실수 1: `build`와 `image`의 동작 오해하기

`build`와 `image`를 한 서비스에 함께 쓰는 건 **잘못된 사용이 아니다.** 빌드할 때 Compose는 `build`로 이미지를 만들고 `image`에 지정된 태그를 붙이기 때문에, **레지스트리에 푸시할 이미지를 의도된 태그로 빌드할 때** 오히려 권장되는 패턴이다.

```yaml
services:
  app:
    build: .
    image: my-registry/my-app:1.0    # 빌드 결과에 이 태그가 붙고, 그대로 push 가능
```

다만 `docker compose up`이 매번 빌드한다고 오해하기 쉽다. `pull_policy`를 지정하지 않으면 Compose는 먼저 `image`의 이미지를 레지스트리나 로컬 캐시에서 찾고, 없을 때만 빌드한다. `build`만 있는 서비스도 이미 만들어 둔 이미지가 있으면 다시 빌드하지 않는다. 소스를 고친 뒤 새 이미지로 띄우려면 `docker compose up --build`나 `docker compose build`를 명시해야 한다.

또 하나 흔한 실수는 **환경별 의도가 섞이는 것**이다. 로컬 개발과 프로덕션은 한쪽만 쓰는 편이 명확하다:

```yaml
# 개발용 (로컬 소스로 빌드, 소스를 고쳤으면 up --build)
services:
  app:
    build: .

# 프로덕션용 (CI에서 빌드·푸시된 이미지를 pull만)
services:
  app:
    image: my-registry/my-app:1.0
```

### 실수 2: depends_on은 "준비 완료"를 보장하지 않는다

```yaml
# ❌ DB가 시작되었지만, 아직 연결 준비가 안 됐을 수 있음
services:
  app:
    depends_on:
      - db

# ✅ healthcheck와 함께 사용
services:
  app:
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### 실수 3: 볼륨 이름 없이 데이터베이스 실행

```yaml
# ❌ 컨테이너를 다시 만들면 데이터가 사라진 것처럼 보임
services:
  db:
    image: postgres:15

# ✅ 명명된 볼륨으로 데이터 영속화
services:
  db:
    image: postgres:15
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

정확히 말하면 첫 번째 예시에서도 데이터가 컨테이너와 함께 바로 지워지지는 않는다. postgres 공식 이미지는 Dockerfile에 `VOLUME`을 선언해 두었기 때문에, 볼륨을 지정하지 않으면 데이터가 이름 없는 익명 볼륨에 저장된다. 문제는 그다음이다. `docker compose down` 후 다시 `up`하면 새 컨테이너에는 새 익명 볼륨이 붙고, 이전 데이터는 어디에도 연결되지 않은 볼륨으로 남는다. 이름을 붙여 두어야 어떤 컨테이너가 떠도 같은 데이터를 찾아 연결할 수 있다.

> **버전을 올릴 때 주의:** postgres 18 이상 이미지는 볼륨 마운트 경로가 `/var/lib/postgresql`로 바뀌었고, 실제 데이터는 그 아래 버전별 디렉토리(`18/docker`)에 저장된다. 이 예시처럼 `/var/lib/postgresql/data`에 마운트한 채 18로 올리면 컨테이너가 시작되지 않으므로 마운트 경로도 함께 바꿔야 한다.

## 9. 정리

**Dockerfile** 은 "내 애플리케이션을 이미지로 굽는 레시피"다:
- 베이스 이미지 선택
- 의존성 설치
- 코드 복사
- 빌드 및 실행 명령 정의

**docker-compose.yml** 은 "여러 컨테이너를 조합해서 실행하는 악보"다:
- 어떤 이미지/Dockerfile 사용할지
- 포트, 환경변수, 볼륨 설정
- 컨테이너 간 의존성과 네트워크
- 재시작 정책

**Kubernetes** 는 여러 서버(클러스터)에 걸쳐 컨테이너를 운영하는 별개의 오케스트레이터다:
- Dockerfile로 빌드된 이미지를 사용
- Compose 파일 대신 Deployment·Service 같은 자체 매니페스트로 정의
- 자동 스케일링, 셀프 힐링, 롤링 업데이트

---

## 출처

- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/) - Docker 공식 문서
- [Docker Compose Overview](https://docs.docker.com/compose/) - Docker 공식 문서
- [Compose File Reference](https://docs.docker.com/reference/compose-file/) - Docker 공식 문서
- [Compose Build Specification - Using build and image](https://docs.docker.com/reference/compose-file/build/#using-build-and-image) - Docker 공식 문서
- [Use Compose Watch](https://docs.docker.com/compose/how-tos/file-watch/) - Docker 공식 문서
- [Images and layers](https://docs.docker.com/engine/storage/drivers/#images-and-layers) - Docker 공식 문서
- [postgres - Docker Official Image](https://hub.docker.com/_/postgres) - Docker Hub
