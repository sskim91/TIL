# 첫 배포 예제 파일

실행 순서·전제·예상 결과·정리는 [Kubernetes 첫 배포](../../Kubernetes-First-Deployment.md)에 있다. 저장소 루트에서 시작하고, 로컬 Docker endpoint와 전용 kind cluster/kubeconfig를 확인한다. 본문 1절처럼 현재 터미널에서 `DOCKER_HOST`를 해제하고 `DOCKER_CONTEXT`를 설정한 뒤, 플래그 없는 `docker context show`·`docker info`로 kind가 사용할 접속 대상을 확인한다.

`Dockerfile`은 Python 표준 HTTP 서버로 `public/`을 제공한다. `DEMO_VERSION` build argument가 첫 페이지 버전을 바꾼다. `readyz`, `livez`, `startupz`의 `ok`는 HTTP 파일 제공만 확인하며 주문 처리·DB·인증 상태를 검증하지 않는다. 실서비스용 웹 서버가 아니다.

`deployment.yaml`은 `book/order-api:1.0.0` 로컬 이미지, `bookstore` namespace, 복제본 2개, 앱 포트 8080을 사용한다. `service.yaml`은 Service 포트 80을 앱 8080으로 연결한다. 원격 registry에 이 이미지를 게시하지 않는다. 뒤 장의 `registry.example.com/book/order-api`는 조직 registry를 가정한 설명용 자리표시자다.

새 버전을 `kubectl set image`로 바꾼 뒤 이 디렉터리를 다시 apply하면 파일에 기록된 1.0.0으로 되돌아간다. 변경의 source of truth를 파일로 유지하려면 Deployment manifest의 이미지도 갱신해야 한다.
