# Kubernetes 기초편 그림

`generate.py`가 같은 디렉터리의 SVG 여섯 개를 만든다. 저장소 루트에서 `python3 kubernetes/assets/book/generate.py`로 재생성한다. 외부 Python 패키지가 필요하지 않다. SVG는 편집 가능한 텍스트이며 각 파일에 접근성을 위한 `title`과 `desc`가 있다.

| 파일 | 본문 | 표현하는 경계 |
|---|---|---|
| `execution-boundaries.svg` | 컨테이너의 기초 | 프로세스·게스트 커널·공유 Linux 커널 |
| `image-supply-path.svg` | 이미지의 생성과 전달 | 이미지 파일의 전달과 프로세스 시작 |
| `desired-state-operations.svg` | 오케스트레이션이 필요한 이유 | 원하는 상태·관찰 상태·반복 조정 |
| `cluster-map.svg` | 클러스터 구조 | API를 중심으로 한 구성 요소의 역할 |
| `control-and-request-paths.svg` | 클러스터 구조 | 관리의 논리적 진행과 앱 트래픽 |
| `airgap-dependencies.svg` | 첫 배포 | 승인 반입과 내부 공급·실행 의존성 |

그림은 본문 캡션과 함께 읽는다. 관리 경로의 순차 화살표는 controller가 kubelet에 직접 RPC한다는 뜻이 아니며, port-forward는 일반적인 Service 데이터 경로와 다르다. 에어갭의 반입 화살표는 외부·내부의 직접 네트워크 연결을 가정하지 않는다. 다이어그램의 구성 요소 상자는 물리 서버 한 대씩을 의미하지 않는다.
