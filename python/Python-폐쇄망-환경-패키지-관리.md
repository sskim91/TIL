# Python 폐쇄망 환경 패키지 관리

인터넷이 차단된 폐쇄망(Air-gapped) 환경에서 Python 패키지를 설치하고 관리하는 방법을 정리합니다.

## 결론부터 말하면

폐쇄망 환경에서는 **외부망에서 미리 패키지를 다운로드**하여 **오프라인 저장소를 구축**하거나, **wheel 파일을 직접 전달**하는 방식으로 패키지를 관리합니다. 핵심은 `pip download`로 의존성을 포함한 모든 패키지를 사전에 준비하는 것입니다.

```bash
# 외부망에서 준비
pip download -r requirements.txt -d ./packages

# USB/네트워크로 전달 후 폐쇄망에서 설치
pip install --no-index --find-links=./packages -r requirements.txt
```

## 1. 폐쇄망 환경이란?

### 정의

**폐쇄망 (Air-gapped Network)**
- 외부 인터넷과 물리적으로 분리된 네트워크
- 보안상의 이유로 인터넷 접속 차단
- 데이터 반입/반출이 엄격하게 통제됨

### 대표적인 사용 환경

```
✅ 금융권 (은행, 증권사)
✅ 공공기관 (정부 기관)
✅ 국방 관련 시설
✅ 중요 인프라 시설
✅ 연구소 (보안 연구실)
✅ 의료기관 (환자 정보 보호)
```

### 제약사항

```bash
# ❌ 불가능한 작업들
pip install requests          # PyPI 접속 불가
pip install --upgrade pip     # 인터넷 필요
git clone https://...         # Git 접속 불가
curl https://...              # 외부 URL 접속 불가

# ✅ 가능한 작업들
pip install --no-index ...    # 로컬 패키지 설치
python script.py              # 로컬 실행
```

## 2. 기본 전략: pip download

### 개념

외부망에서 **모든 패키지와 의존성을 미리 다운로드**하여 폐쇄망으로 전달

### 단계별 워크플로우

**Step 1: 외부망에서 패키지 다운로드**

```bash
# 1. requirements.txt 작성
cat > requirements.txt << EOF
django==4.2.0
requests==2.31.0
pandas==2.0.0
pytest==7.4.0
EOF

# 2. 패키지 및 의존성 모두 다운로드
pip download -r requirements.txt -d ./packages

# 결과: ./packages/ 폴더에 모든 wheel/tar.gz 파일 저장
# packages/
# ├── Django-4.2.0-py3-none-any.whl
# ├── requests-2.31.0-py3-none-any.whl
# ├── pandas-2.0.0-cp311-cp311-manylinux_2_17_x86_64.whl
# ├── pytest-7.4.0-py3-none-any.whl
# ├── asgiref-3.7.2-py3-none-any.whl  # Django의 의존성
# ├── certifi-2023.7.22-py3-none-any.whl  # requests의 의존성
# └── ... (모든 의존성 포함)
```

**Step 2: 패키지 전달**

```bash
# packages/ 폴더를 압축
tar -czf packages.tar.gz packages/
# 또는
zip -r packages.zip packages/

# USB, 내부 네트워크, 승인된 전달 방법으로 폐쇄망에 전달
```

**Step 3: 폐쇄망에서 설치**

```bash
# 1. 압축 해제
tar -xzf packages.tar.gz
# 또는
unzip packages.zip

# 2. 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate

# 3. 로컬 패키지에서 설치
pip install --no-index --find-links=./packages -r requirements.txt

# 옵션 설명:
# --no-index: PyPI를 사용하지 않음
# --find-links=./packages: 로컬 폴더에서 패키지 검색
```

### 특정 플랫폼용 다운로드

```bash
# Linux용 패키지 다운로드 (Windows에서)
pip download -r requirements.txt -d ./packages \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 3.11

# macOS용 패키지 다운로드
pip download -r requirements.txt -d ./packages \
    --platform macosx_10_9_x86_64 \
    --only-binary=:all:

# Windows용 패키지 다운로드
pip download -r requirements.txt -d ./packages \
    --platform win_amd64 \
    --only-binary=:all:

# 모든 플랫폼용 (pure Python만)
pip download -r requirements.txt -d ./packages \
    --only-binary=:none:
```

## 3. 로컬 PyPI 서버 구축

### 방법 1: pypiserver (간단)

**외부망 설정:**

```bash
# 1. pypiserver 설치
pip install pypiserver

# 2. 패키지 다운로드
mkdir -p /opt/pypi/packages
pip download -r requirements.txt -d /opt/pypi/packages

# 3. 서버 실행
pypi-server run -p 8080 /opt/pypi/packages
```

**폐쇄망 설정:**

```bash
# 1. pypiserver 설치 (사전에 wheel 파일 준비 필요)
pip install --no-index --find-links=./pypiserver_packages pypiserver

# 2. 서버 실행
pypi-server run -p 8080 /opt/pypi/packages

# 3. pip 설정
pip install --index-url http://localhost:8080/simple/ django

# 또는 pip.conf에 설정
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << EOF
[global]
index-url = http://pypi-server.internal:8080/simple/
trusted-host = pypi-server.internal
EOF
```

### 방법 2: devpi (고급)

**외부망 설정:**

```bash
# 1. devpi 설치
pip install devpi-server devpi-client

# 2. devpi 서버 초기화
devpi-init

# 3. 서버 시작
devpi-server --start --host=0.0.0.0 --port=3141

# 4. 클라이언트 설정
devpi use http://localhost:3141
devpi login root --password=''
devpi index -c dev bases=root/pypi

# 5. 패키지 업로드
devpi use root/dev
devpi upload --from-dir ./packages
```

**폐쇄망 설정:**

```bash
# pip 설정
pip install --index-url http://devpi.internal:3141/root/dev/+simple/ django
```

### 방법 3: Artifactory / Nexus (엔터프라이즈)

```bash
# Nexus Repository Manager
# 1. Nexus에 PyPI proxy repository 생성
# 2. 외부망에서 캐시 생성
# 3. 캐시를 폐쇄망 Nexus로 복제

# pip 설정
[global]
index-url = https://nexus.company.com/repository/pypi-hosted/simple
trusted-host = nexus.company.com
```

## 4. 실무 시나리오별 가이드

### 시나리오 1: 단일 프로젝트 배포

**준비 (외부망):**

```bash
# 1. 프로젝트 확인
cd myproject
cat requirements.txt

# 2. 모든 패키지 다운로드
mkdir -p deploy/packages
pip download -r requirements.txt -d deploy/packages

# 3. 추가 파일 준비
cp requirements.txt deploy/
cp install.sh deploy/

# 4. 압축
tar -czf myproject_deploy.tar.gz deploy/
```

**설치 스크립트 (install.sh):**

```bash
#!/bin/bash
# install.sh

set -e

echo "=== Python 패키지 설치 스크립트 ==="

# 가상환경 확인
if [ ! -d "venv" ]; then
    echo "가상환경 생성..."
    python3 -m venv venv
fi

# 활성화
source venv/bin/activate

# pip 버전 확인
pip --version

# 패키지 설치
echo "패키지 설치 중..."
pip install --no-index --find-links=./packages -r requirements.txt

echo "설치 완료!"
pip list
```

**배포 (폐쇄망):**

```bash
# 1. 압축 해제
tar -xzf myproject_deploy.tar.gz
cd deploy/

# 2. 설치 실행
chmod +x install.sh
./install.sh

# 3. 확인
source venv/bin/activate
python -c "import django; print(django.__version__)"
```

### 시나리오 2: 정기 업데이트

**월간 패키지 업데이트 프로세스:**

```bash
# 외부망에서 매월 1일 실행
#!/bin/bash
# monthly_package_update.sh

DATE=$(date +%Y%m)
PACKAGE_DIR="packages_${DATE}"

# 1. 최신 패키지 다운로드
mkdir -p ${PACKAGE_DIR}
pip download -r requirements.txt -d ${PACKAGE_DIR}

# 2. 보안 패키지 목록 확인
pip-audit -r requirements.txt --format json > security_report_${DATE}.json

# 3. 변경 사항 로그
pip list --outdated > changes_${DATE}.txt

# 4. 압축
tar -czf python_packages_${DATE}.tar.gz ${PACKAGE_DIR}

echo "패키지 업데이트 준비 완료: python_packages_${DATE}.tar.gz"
```

### 시나리오 3: 여러 Python 버전 지원

```bash
# Python 3.9, 3.10, 3.11 모두 지원

# 외부망에서
for version in 3.9 3.10 3.11; do
    echo "Python ${version} 패키지 다운로드..."
    pip download -r requirements.txt \
        -d packages/python${version//.} \
        --python-version ${version}
done

# 구조:
# packages/
# ├── python39/
# │   ├── Django-4.2.0-py3-none-any.whl
# │   └── ...
# ├── python310/
# │   └── ...
# └── python311/
#     └── ...

# 폐쇄망에서 Python 버전별 설치
PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+' | tr -d '.')
pip install --no-index --find-links=./packages/python${PYTHON_VERSION} -r requirements.txt
```

### 시나리오 4: 대규모 조직 (여러 프로젝트)

**중앙 패키지 저장소 운영:**

```bash
# 1. 조직 공통 패키지 다운로드
cat > common_packages.txt << EOF
django>=4.0
requests
pandas
numpy
pytest
black
flake8
EOF

pip download -r common_packages.txt -d /shared/pypi/packages

# 2. 프로젝트별 추가 패키지
pip download -r project_a_requirements.txt -d /shared/pypi/packages
pip download -r project_b_requirements.txt -d /shared/pypi/packages

# 3. 중복 제거
cd /shared/pypi/packages
ls -lh  # 중복 파일 확인 (같은 버전은 하나만 유지)

# 4. pypiserver로 서빙
pypi-server run -p 8080 /shared/pypi/packages
```

## 5. wheel 파일 직접 관리

### wheel이란?

```
Wheel (.whl) = Python의 빌드된 패키지 형식
- 설치 속도가 빠름
- 플랫폼별로 빌드된 바이너리 포함 가능
- pip의 기본 설치 형식
```

### wheel 빌드 및 설치

```bash
# 외부망: wheel 빌드
pip install wheel
pip wheel -r requirements.txt -w ./wheels

# 폐쇄망: wheel 설치
pip install --no-index --find-links=./wheels -r requirements.txt

# 또는 개별 설치
pip install --no-index ./wheels/Django-4.2.0-py3-none-any.whl
```

### 소스에서 wheel 빌드

```bash
# 소스 코드가 있는 경우
cd mypackage/
python setup.py bdist_wheel

# 생성된 wheel 파일
ls dist/
# mypackage-1.0.0-py3-none-any.whl

# 전달 후 설치
pip install mypackage-1.0.0-py3-none-any.whl
```

## 6. 의존성 해결 전략

### 완전한 의존성 파악

```bash
# 1. pipdeptree로 의존성 트리 확인
pip install pipdeptree
pipdeptree -fl

# 출력 예시:
# Django==4.2.0
#   - asgiref [required: >=3.6.0,<4, installed: 3.7.2]
#   - sqlparse [required: >=0.3.1, installed: 0.4.4]
#   - tzdata [required: Any, installed: 2023.3]

# 2. pip-compile로 정확한 버전 고정
pip install pip-tools
pip-compile requirements.in --output-file requirements.txt

# 3. 다운로드
pip download -r requirements.txt -d ./packages
```

### 숨겨진 의존성 처리

```bash
# 문제 상황: 런타임에 필요한 패키지가 requirements.txt에 없음
# 예: Django에서 PostgreSQL 사용시 psycopg2 필요

# 해결 1: 명시적 추가
cat >> requirements.txt << EOF
psycopg2-binary==2.9.6  # PostgreSQL driver
pillow==10.0.0          # 이미지 처리
EOF

# 해결 2: 실제 환경에서 freeze
# 개발환경에서 모든 기능 테스트 후
pip freeze > requirements_complete.txt

# 이를 기준으로 다운로드
pip download -r requirements_complete.txt -d ./packages
```

## 7. 보안 및 검증

### 패키지 무결성 검증

```bash
# 1. 해시값 기록 (외부망)
pip hash Django-4.2.0-py3-none-any.whl
# --hash=sha256:...

# 2. requirements.txt에 해시 포함
cat > requirements.txt << EOF
django==4.2.0 \
    --hash=sha256:abc123...
requests==2.31.0 \
    --hash=sha256:def456...
EOF

# 3. 폐쇄망에서 검증하며 설치
pip install --require-hashes -r requirements.txt
```

### 보안 취약점 스캔

```bash
# 외부망에서 취약점 검사
pip install pip-audit

# 패키지 검사
pip-audit -r requirements.txt

# JSON 보고서 생성
pip-audit -r requirements.txt --format json > security_report.json

# 취약점이 있으면 대체 버전 다운로드
pip download "django>=4.2.1" -d ./packages
```

### 승인 프로세스

```bash
# 1. 패키지 목록 생성
pip download -r requirements.txt -d ./packages --no-deps
ls ./packages > package_manifest.txt

# 2. 보안팀 승인 요청
# package_manifest.txt + security_report.json 제출

# 3. 승인 후 전체 의존성 다운로드
pip download -r requirements.txt -d ./packages
```

## 8. 트러블슈팅

### 문제 1: 플랫폼 불일치

```bash
# 증상: Windows에서 다운로드 → Linux에 설치 실패
ERROR: django-4.2.0-cp311-cp311-win_amd64.whl is not a supported wheel

# 해결: 타겟 플랫폼 명시
pip download -r requirements.txt -d ./packages \
    --platform manylinux2014_x86_64 \
    --only-binary=:all:
```

### 문제 2: Python 버전 불일치

```bash
# 증상: Python 3.11에서 다운로드 → Python 3.9에 설치 실패

# 해결: 타겟 Python 버전 명시
pip download -r requirements.txt -d ./packages \
    --python-version 3.9
```

### 문제 3: 일부 패키지만 업데이트 필요

```bash
# 외부망에서 특정 패키지만 다운로드
pip download django==4.2.1 -d ./packages_update

# 폐쇄망에서 기존 packages 폴더에 복사
cp ./packages_update/* ./packages/

# 업그레이드
pip install --no-index --find-links=./packages --upgrade django
```

### 문제 4: 용량 문제

```bash
# 큰 패키지들 (numpy, pandas, torch 등)이 수 GB

# 해결 1: 필수 패키지만 선별
cat > requirements_minimal.txt << EOF
django==4.2.0
requests==2.31.0
# numpy, pandas 제외 (용량 큼)
EOF

# 해결 2: 압축률 높은 포맷 사용
tar -czf packages.tar.gz packages/  # gzip
tar -cJf packages.tar.xz packages/  # xz (더 높은 압축률)

# 해결 3: 분할 압축
split -b 500M packages.tar.gz packages_part_
```

### 문제 5: pip 자체가 없는 환경

```bash
# Python은 있지만 pip가 없는 경우

# 외부망에서 get-pip.py 다운로드
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# 폐쇄망으로 전달 후
python get-pip.py --no-index --find-links=./pip_packages

# 또는 ensurepip 사용 (Python 3.4+)
python -m ensurepip --default-pip
```

## 9. 자동화 스크립트

### 완전 자동화 예제

```bash
#!/bin/bash
# prepare_offline_packages.sh
# 폐쇄망 배포를 위한 패키지 준비 스크립트

set -e

# 설정
PROJECT_NAME="myproject"
DATE=$(date +%Y%m%d)
DEPLOY_DIR="deploy_${PROJECT_NAME}_${DATE}"
REQUIREMENTS_FILE="requirements.txt"
PYTHON_VERSION="3.11"

echo "=== 폐쇄망 배포 패키지 준비 ==="
echo "프로젝트: ${PROJECT_NAME}"
echo "날짜: ${DATE}"
echo ""

# 1. 디렉토리 생성
mkdir -p ${DEPLOY_DIR}/{packages,scripts,docs}

# 2. requirements.txt 복사
cp ${REQUIREMENTS_FILE} ${DEPLOY_DIR}/

# 3. 패키지 다운로드
echo "패키지 다운로드 중..."
pip download -r ${REQUIREMENTS_FILE} \
    -d ${DEPLOY_DIR}/packages \
    --python-version ${PYTHON_VERSION}

# 4. 의존성 트리 생성
pip install pipdeptree
pipdeptree -fl > ${DEPLOY_DIR}/docs/dependencies.txt

# 5. 보안 체크
pip install pip-audit
pip-audit -r ${REQUIREMENTS_FILE} \
    --format json > ${DEPLOY_DIR}/docs/security_report.json || true

# 6. 설치 스크립트 생성
cat > ${DEPLOY_DIR}/scripts/install.sh << 'EOF'
#!/bin/bash
set -e

echo "=== 패키지 설치 시작 ==="

# 가상환경 생성
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# 패키지 설치
pip install --no-index \
    --find-links=../packages \
    -r ../requirements.txt

echo "=== 설치 완료 ==="
pip list
EOF

chmod +x ${DEPLOY_DIR}/scripts/install.sh

# 7. README 생성
cat > ${DEPLOY_DIR}/README.md << EOF
# ${PROJECT_NAME} 폐쇄망 배포 패키지

생성일: ${DATE}
Python 버전: ${PYTHON_VERSION}

## 설치 방법

\`\`\`bash
cd scripts
./install.sh
\`\`\`

## 포함된 패키지

$(pip list --format=freeze | head -20)

## 문서

- dependencies.txt: 전체 의존성 트리
- security_report.json: 보안 취약점 보고서
EOF

# 8. 압축
echo "압축 중..."
tar -czf ${DEPLOY_DIR}.tar.gz ${DEPLOY_DIR}/

# 9. 체크섬 생성
sha256sum ${DEPLOY_DIR}.tar.gz > ${DEPLOY_DIR}.tar.gz.sha256

# 10. 결과 출력
echo ""
echo "=== 준비 완료 ==="
echo "파일: ${DEPLOY_DIR}.tar.gz"
echo "크기: $(du -h ${DEPLOY_DIR}.tar.gz | cut -f1)"
echo "SHA256: $(cat ${DEPLOY_DIR}.tar.gz.sha256)"
echo ""
echo "전달 파일:"
echo "  - ${DEPLOY_DIR}.tar.gz"
echo "  - ${DEPLOY_DIR}.tar.gz.sha256"
```

### 검증 스크립트

```bash
#!/bin/bash
# verify_installation.sh
# 폐쇄망에서 설치 후 검증

set -e

echo "=== 설치 검증 ==="

# 1. Python 버전 확인
echo "Python 버전:"
python --version

# 2. pip 버전 확인
echo "pip 버전:"
pip --version

# 3. 필수 패키지 확인
echo "필수 패키지 확인:"
python << 'EOF'
import sys

packages_to_check = [
    'django',
    'requests',
    'pandas',
    'pytest',
]

all_ok = True
for package in packages_to_check:
    try:
        __import__(package)
        print(f"✓ {package}")
    except ImportError:
        print(f"✗ {package} - 없음!")
        all_ok = False

if all_ok:
    print("\n모든 패키지 설치 완료!")
    sys.exit(0)
else:
    print("\n일부 패키지 설치 실패!")
    sys.exit(1)
EOF

# 4. 간단한 테스트
echo "Django 버전 테스트:"
python -c "import django; print(f'Django {django.__version__}')"

echo ""
echo "=== 검증 완료 ==="
```

## 10. uv를 폐쇄망에서 사용하기 (⚠️ 실험적)

**uv는 폐쇄망에서 사용 가능하지만, 아직 일부 제약사항이 있습니다.**

### 지원되는 기능

uv는 pip와 동일하게 오프라인 모드를 지원합니다:

```bash
# 지원되는 옵션들
--offline          # 오프라인 모드
--no-index         # PyPI 인덱스 사용 안함
--find-links DIR   # 로컬 디렉토리에서 패키지 검색
```

### 기본 워크플로우

**외부망에서 준비:**

```bash
# 1. uv 설치 파일 준비
# uv 바이너리를 다운로드 (GitHub releases)
curl -LsSf https://astral.sh/uv/install.sh | sh
# → ~/.cargo/bin/uv 바이너리를 USB로 복사

# 2. 패키지 다운로드 (pip download와 동일)
uv pip compile pyproject.toml -o requirements.txt
uv pip download -r requirements.txt -d ./wheels

# 또는
mkdir -p offline_packages
uv pip download django requests pandas -d offline_packages

# 3. 압축
tar -czf uv_offline_packages.tar.gz offline_packages/ requirements.txt
```

**폐쇄망에서 설치:**

```bash
# 1. uv 바이너리 설치
cp uv ~/.local/bin/uv  # 또는 적절한 PATH에 복사
chmod +x ~/.local/bin/uv

# 2. 압축 해제
tar -xzf uv_offline_packages.tar.gz

# 3. 가상환경 생성 (매우 빠름!)
uv venv

# 4. 활성화
source .venv/bin/activate

# 5. 오프라인 설치
uv pip install --no-index \
    --find-links=./offline_packages \
    -r requirements.txt
```

### 실제 사용 예제

```bash
# 외부망: Django 프로젝트 준비
cat > requirements.txt << EOF
django==4.2.0
djangorestframework==3.14.0
celery==5.3.0
EOF

# 다운로드 (초고속)
uv pip download -r requirements.txt -d ./wheels

# 폐쇄망: 설치 (초고속)
uv venv
source .venv/bin/activate
uv pip install --no-index --find-links=./wheels -r requirements.txt
```

### ⚠️ 현재 제약사항 (2024년 기준)

#### 1. Git 의존성 문제

```bash
# 문제: pyproject.toml에 git 의존성이 있는 경우
[project]
dependencies = [
    "my-package @ git+https://github.com/user/repo.git",
]

# --offline 플래그를 사용해도 Git에서 가져오려고 시도함
# 해결: pyproject.toml에서 git 의존성 제거 필요
```

**임시 해결책:**
```bash
# 외부망에서 git 의존성을 wheel로 변환
git clone https://github.com/user/repo.git
cd repo
uv pip wheel . -w ../wheels

# pyproject.toml 수정 (폐쇄망용)
sed -i 's|@ git+https://.*|@ file:///path/to/wheels/my_package-1.0.0-py3-none-any.whl|' pyproject.toml
```

#### 2. uv run의 PyPI 접근 시도

```bash
# 문제: uv run이 --offline 플래그를 무시하고 PyPI 접근 시도
uv run --offline --no-index --find-links=./wheels python script.py
# → 여전히 PyPI에 접근 시도

# 해결: 가상환경을 명시적으로 활성화
uv venv
source .venv/bin/activate
python script.py  # uv run 대신 직접 실행
```

#### 3. uv sync의 불완전한 --no-index 지원

```bash
# 문제: uv sync가 --no-index를 완벽히 지원하지 않음
uv sync --frozen --no-index --find-links=./wheels
# → 간헐적으로 PyPI 접근 시도

# 해결: uv pip install 사용
uv pip install --no-index --find-links=./wheels -r requirements.txt
```

### 권장 워크플로우 (안정적)

```bash
# === 외부망 ===
# Step 1: requirements.txt 생성
uv pip compile pyproject.toml -o requirements.txt

# Step 2: wheel 다운로드
uv pip download -r requirements.txt -d ./wheels

# Step 3: uv 바이너리 포함
cp $(which uv) ./uv_binary

# Step 4: 패키징
tar -czf offline_bundle.tar.gz wheels/ requirements.txt uv_binary install.sh

# === 폐쇄망 ===
# install.sh
#!/bin/bash
set -e

# uv 설치
cp uv_binary ~/.local/bin/uv
chmod +x ~/.local/bin/uv
export PATH="$HOME/.local/bin:$PATH"

# 가상환경 생성
uv venv

# 활성화
source .venv/bin/activate

# 패키지 설치 (uv pip 명령어 사용)
uv pip install --no-index \
    --find-links=./wheels \
    -r requirements.txt

echo "설치 완료!"
uv pip list
```

### pyproject.toml 기반 프로젝트

```bash
# 외부망에서 lock 파일 생성
uv lock

# 모든 의존성을 wheel로 다운로드
uv export --format requirements-txt > requirements.txt
uv pip download -r requirements.txt -d ./wheels

# 폐쇄망에서 설치
uv venv
source .venv/bin/activate
uv pip install --no-index --find-links=./wheels -r requirements.txt
```

### uv의 장점 (폐쇄망 환경에서도)

```bash
# 성능 비교
# pip: 30초
pip install --no-index --find-links=./wheels -r requirements.txt

# uv: 3초 (10배 빠름!)
uv pip install --no-index --find-links=./wheels -r requirements.txt
```

**장점:**
- ✅ pip보다 훨씬 빠른 설치 속도
- ✅ 메모리 효율적
- ✅ pip 호환 명령어 (`uv pip`)
- ✅ 의존성 해결 속도 빠름

**단점:**
- ❌ Git 의존성 처리 불완전
- ❌ `uv run` 오프라인 모드 불안정
- ❌ `uv sync` --no-index 지원 불완전
- ❌ 문서화 부족 (베스트 프랙티스 미확립)

### 실전 팁

**1. uv pip 명령어 사용**
```bash
# ✅ 안정적
uv pip install --no-index ...

# ⚠️ 불안정
uv run --offline ...
uv sync --no-index ...
```

**2. Git 의존성 제거**
```bash
# pyproject.toml을 폐쇄망용과 개발용으로 분리
# pyproject.toml (개발)
# pyproject.offline.toml (폐쇄망)
```

**3. 검증 스크립트**
```bash
# uv 설치 검증
uv --version
uv pip list
```

### 언제 uv를 사용할까?

**✅ uv 사용 권장:**
- 순수 Python 패키지만 사용 (Git 의존성 없음)
- 설치 속도가 중요
- pip 호환 워크플로우 선호
- 최신 도구 실험 가능

**❌ pip 사용 권장:**
- Git 의존성이 많음
- 안정성이 최우선
- 검증된 워크플로우 필요
- 문서화된 베스트 프랙티스 필요

### 향후 전망

uv는 활발히 개발 중이며, 폐쇄망 지원이 개선될 예정입니다:
- GitHub 이슈: [#13587](https://github.com/astral-sh/uv/issues/13587)
- 커뮤니티에서 베스트 프랙티스 논의 중
- Astral팀이 적극 개발 중

**결론:** 2024년 현재 uv는 폐쇄망에서 **사용 가능하지만 pip보다 덜 성숙**합니다. 간단한 프로젝트는 속도 이점을 위해 시도해볼 만하지만, 복잡한 프로젝트는 pip를 권장합니다.

## 11. 베스트 프랙티스

### 체크리스트

```markdown
## 외부망 준비 단계

✅ requirements.txt 버전 고정 확인
✅ 타겟 플랫폼/Python 버전 확인
✅ pip download로 전체 의존성 다운로드
✅ 보안 취약점 스캔
✅ 의존성 트리 문서화
✅ 설치 스크립트 작성
✅ 검증 스크립트 작성
✅ README 작성
✅ 압축 및 체크섬 생성

## 전달 단계

✅ 승인 프로세스 진행
✅ 무결성 검증 (SHA256)
✅ 안전한 전달 매체 사용
✅ 전달 이력 기록

## 폐쇄망 설치 단계

✅ 체크섬 검증
✅ 압축 해제
✅ 가상환경 생성
✅ 오프라인 설치
✅ 설치 검증
✅ 동작 테스트
✅ 설치 이력 기록
```

### 주의사항

**❌ 하지 말아야 할 것:**
- 플랫폼 불일치 상태로 다운로드
- 버전 미고정 requirements.txt 사용
- 보안 검증 생략
- 의존성 누락
- 설치 검증 생략

**✅ 해야 할 것:**
- 정확한 버전 명시
- 전체 의존성 다운로드
- 보안 취약점 사전 확인
- 문서화 철저히
- 설치 자동화 스크립트 제공
- 검증 프로세스 수립

## 12. 도구 비교

| 도구 | 장점 | 단점 | 추천 상황 |
|------|------|------|-----------|
| **pip download** | 간단, 별도 설치 불필요 | 서버 기능 없음 | 소규모, 단발성 배포 |
| **uv** | 매우 빠름 (10배), pip 호환 | Git 의존성 문제, 덜 성숙 | 속도 중요, 순수 Python 패키지 |
| **pypiserver** | 설정 간단, 가벼움 | 기능 제한적 | 중소규모 조직 |
| **devpi** | 강력한 기능, 캐싱 | 복잡한 설정 | 개발팀 있는 조직 |
| **Artifactory** | 엔터프라이즈급, 통합 관리 | 비용, 무거움 | 대기업 |
| **Nexus** | 다양한 포맷 지원 | 설정 복잡 | 대기업 |

## 핵심 요약

### 가장 간단한 워크플로우

**pip 사용 (안정적):**
```bash
# === 외부망 ===
# 1. 준비
pip download -r requirements.txt -d packages

# 2. 전달
tar -czf packages.tar.gz packages/

# === 폐쇄망 ===
# 3. 설치
tar -xzf packages.tar.gz
pip install --no-index --find-links=./packages -r requirements.txt
```

**uv 사용 (빠름, 실험적):**
```bash
# === 외부망 ===
# 1. 준비
uv pip download -r requirements.txt -d wheels

# 2. 전달
tar -czf wheels.tar.gz wheels/

# === 폐쇄망 ===
# 3. 설치 (10배 빠름!)
tar -xzf wheels.tar.gz
uv venv && source .venv/bin/activate
uv pip install --no-index --find-links=./wheels -r requirements.txt
```

### 중요 옵션 정리

```bash
# 필수 옵션
--no-index              # PyPI 사용 안함
--find-links=DIR        # 로컬 디렉토리에서 검색
--python-version VER    # 타겟 Python 버전
--platform PLAT         # 타겟 플랫폼
--only-binary=:all:     # wheel만 다운로드
```

### 실무 팁

1. **항상 정확한 버전 명시** (`==`)
2. **타겟 환경 정확히 파악** (OS, Python 버전)
3. **의존성 트리 확인** (pipdeptree)
4. **보안 취약점 스캔** (pip-audit)
5. **자동화 스크립트 작성** (재현성 보장)
6. **철저한 문서화** (README, 체크리스트)
7. **검증 프로세스 필수** (설치 후 테스트)

폐쇄망 환경에서의 핵심은 **사전 준비의 완벽함**입니다!
