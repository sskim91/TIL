# Python pip 패키지 관리

Java의 Maven/Gradle처럼, Python에서 외부 라이브러리를 설치하고 관리하는 방법.

## 결론부터 말하면

**pip**는 Python Package Installer의 약자로, Python 패키지(라이브러리)를 설치하고 관리하는 **공식 패키지 관리 도구**입니다. PyPI(Python Package Index)에서 수십만 개의 패키지를 쉽게 설치할 수 있으며, **가상환경과 함께 사용**하는 것이 실무 표준입니다.

```bash
# pip의 핵심 사용법
# 1. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows

# 2. 패키지 설치
pip install requests django pytest

# 3. 의존성 저장
pip freeze > requirements.txt

# 4. 다른 환경에서 복원
pip install -r requirements.txt
```

## 1. pip란?

### 정의

**pip** = **P**ip **I**nstalls **P**ackages
- Python의 공식 패키지 관리자
- Python 3.4+ 버전에 기본 포함
- PyPI(Python Package Index)와 연동

### PyPI (Python Package Index)

```
https://pypi.org/

- 50만개 이상의 Python 패키지 저장소
- 누구나 패키지를 업로드/다운로드 가능
- pip는 기본적으로 PyPI에서 패키지 검색
```

**예시:**
```bash
# PyPI에서 requests 패키지 설치
pip install requests
# → https://pypi.org/project/requests/ 에서 다운로드
```

## 2. 기본 명령어

### 패키지 설치

```bash
# 최신 버전 설치
pip install requests

# 특정 버전 설치
pip install django==4.2.0

# 버전 범위 지정
pip install "flask>=2.0.0,<3.0.0"

# 최소 버전 지정
pip install numpy>=1.20.0

# 개발 버전(pre-release) 설치
pip install --pre black

# 여러 패키지 한번에
pip install requests beautifulsoup4 pandas

# 특정 인덱스에서 설치
pip install --index-url https://test.pypi.org/simple/ my-package
```

**실무 예제:**
```bash
# 웹 개발 스택 설치
pip install django djangorestframework celery redis

# 데이터 분석 스택 설치
pip install numpy pandas matplotlib scikit-learn jupyter

# 테스트 도구 설치
pip install pytest pytest-cov pytest-django black flake8
```

### 패키지 제거

```bash
# 기본 제거
pip uninstall requests

# 확인 없이 제거
pip uninstall -y requests

# 여러 패키지 제거
pip uninstall -y requests beautifulsoup4 pandas
```

### 패키지 업그레이드

```bash
# 특정 패키지 업그레이드
pip install --upgrade requests
pip install -U requests  # 축약형

# pip 자체 업그레이드
pip install --upgrade pip
python -m pip install --upgrade pip  # 권장

# 모든 패키지 업그레이드 (주의!)
pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U
```

### 패키지 정보 확인

```bash
# 설치된 패키지 목록
pip list

# 간단한 목록 (버전만)
pip freeze

# 특정 패키지 상세 정보
pip show requests

# 출력 예시:
# Name: requests
# Version: 2.31.0
# Summary: Python HTTP for Humans.
# Home-page: https://requests.readthedocs.io
# Author: Kenneth Reitz
# License: Apache 2.0
# Location: /path/to/site-packages
# Requires: charset-normalizer, idna, urllib3, certifi
# Required-by: my-project

# 오래된 패키지 확인
pip list --outdated

# 특정 패키지 검색
pip search requests  # (PyPI에서 제거됨, 대신 https://pypi.org 사용)
```

## 3. requirements.txt 사용법

### 기본 사용

```bash
# 현재 환경의 패키지 저장
pip freeze > requirements.txt

# requirements.txt에서 설치
pip install -r requirements.txt

# 업그레이드하면서 설치
pip install -r requirements.txt --upgrade
```

### requirements.txt 형식

```txt
# requirements.txt 예시

# 정확한 버전 (권장)
requests==2.31.0
django==4.2.0

# 최소 버전
numpy>=1.20.0

# 버전 범위
flask>=2.0.0,<3.0.0

# 특정 버전 제외
pandas!=1.0.0

# Git 저장소에서 설치
git+https://github.com/user/repo.git@main#egg=package-name

# 로컬 파일
./my-local-package

# 특정 플랫폼용
pywin32==306; sys_platform == 'win32'

# 주석
# 이것은 주석입니다
```

**실무 패턴:**
```txt
# requirements.txt (프로덕션)
django==4.2.0
djangorestframework==3.14.0
celery==5.3.0
redis==4.6.0
psycopg2-binary==2.9.6
gunicorn==21.2.0

# requirements-dev.txt (개발환경)
-r requirements.txt  # 프로덕션 의존성 포함
pytest==7.4.0
pytest-django==4.5.2
black==23.7.0
flake8==6.1.0
ipython==8.14.0
django-debug-toolbar==4.1.0
```

### 환경별 requirements 분리

```bash
project/
├── requirements/
│   ├── base.txt          # 공통 의존성
│   ├── production.txt    # 프로덕션
│   ├── development.txt   # 개발
│   └── test.txt          # 테스트
```

```txt
# requirements/base.txt
django==4.2.0
djangorestframework==3.14.0

# requirements/production.txt
-r base.txt
gunicorn==21.2.0
psycopg2-binary==2.9.6

# requirements/development.txt
-r base.txt
django-debug-toolbar==4.1.0
ipython==8.14.0

# requirements/test.txt
-r base.txt
pytest==7.4.0
pytest-django==4.5.2
```

**사용:**
```bash
# 프로덕션
pip install -r requirements/production.txt

# 개발
pip install -r requirements/development.txt

# 테스트
pip install -r requirements/test.txt
```

## 4. 가상환경과 함께 사용

### 가상환경이 필요한 이유

```python
# ❌ 문제 상황: 전역 환경에 설치
# 프로젝트 A: Django 3.2 필요
# 프로젝트 B: Django 4.2 필요
# → 충돌 발생!

# ✅ 해결: 각 프로젝트마다 가상환경 생성
```

### venv 사용법 (내장)

```bash
# 가상환경 생성
python -m venv venv
python3 -m venv venv  # 명시적

# 다른 이름으로 생성
python -m venv myenv
python -m venv .venv  # 숨김 폴더로 생성 (Git 무시하기 쉬움)

# 활성화
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate          # Windows (cmd)
venv\Scripts\Activate.ps1      # Windows (PowerShell)

# 활성화 확인
which python  # Mac/Linux
where python  # Windows
# → venv 경로가 나오면 성공

# 비활성화
deactivate
```

**실무 워크플로우:**
```bash
# 1. 프로젝트 시작
mkdir myproject
cd myproject

# 2. 가상환경 생성
python -m venv venv

# 3. 활성화
source venv/bin/activate  # (venv) 프롬프트 표시됨

# 4. pip 업그레이드
pip install --upgrade pip

# 5. 패키지 설치
pip install django djangorestframework

# 6. requirements.txt 저장
pip freeze > requirements.txt

# 7. Git에 커밋 (venv는 제외)
echo "venv/" >> .gitignore
git add requirements.txt
git commit -m "Add project dependencies"
```

### virtualenv 사용법 (서드파티)

```bash
# 설치
pip install virtualenv

# 가상환경 생성
virtualenv venv

# Python 버전 지정
virtualenv -p python3.11 venv

# 활성화/비활성화는 venv와 동일
```

### 가상환경 완전 제거

```bash
# 1. 비활성화
deactivate

# 2. 폴더 삭제
rm -rf venv/  # Mac/Linux
rmdir /s venv  # Windows
```

## 5. pip 고급 기능

### editable install (개발 모드)

```bash
# 개발 중인 패키지를 설치
pip install -e .
pip install --editable .

# 사용 예시
cd my-package/
pip install -e .
# → 소스 코드 수정하면 즉시 반영됨
```

**setup.py 예시:**
```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="my-package",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "click>=8.0.0",
    ],
)
```

### pip.conf 설정

```ini
# ~/.pip/pip.conf (Mac/Linux)
# %APPDATA%\pip\pip.ini (Windows)

[global]
timeout = 60
index-url = https://pypi.org/simple

[install]
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
```

### pip 캐시 관리

```bash
# 캐시 확인
pip cache info

# 캐시 목록
pip cache list

# 캐시 제거
pip cache purge

# 캐시 사용 안 함
pip install --no-cache-dir requests
```

## 6. 실무 베스트 프랙티스

### 1) 항상 가상환경 사용

```bash
# ❌ 나쁜 예
sudo pip install django  # 시스템 전체에 설치

# ✅ 좋은 예
python -m venv venv
source venv/bin/activate
pip install django
```

### 2) requirements.txt 버전 고정

```txt
# ❌ 나쁜 예
django
requests
pytest

# ✅ 좋은 예
django==4.2.0
requests==2.31.0
pytest==7.4.0

# 🤔 상황에 따라 (라이브러리 개발시)
django>=4.0.0,<5.0.0
```

### 3) 환경별 requirements 분리

```
requirements/
├── base.txt         # 공통
├── production.txt   # 프로덕션 전용
├── development.txt  # 개발 전용
└── test.txt         # 테스트 전용
```

### 4) pip 명시적 사용

```bash
# ❌ 애매한 방법
pip install requests   # 어떤 Python 버전의 pip?

# ✅ 명시적 방법
python -m pip install requests
python3.11 -m pip install requests  # 특정 버전
```

### 5) .gitignore 설정

```gitignore
# .gitignore
venv/
.venv/
env/
ENV/
*.pyc
__pycache__/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
```

## 7. 자주 발생하는 문제와 해결

### 문제 1: Permission Denied

```bash
# 문제
$ pip install django
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied

# ❌ 나쁜 해결법
sudo pip install django

# ✅ 올바른 해결법
# 가상환경 사용
python -m venv venv
source venv/bin/activate
pip install django

# 또는 --user 옵션 (비권장)
pip install --user django
```

### 문제 2: pip가 오래된 버전

```bash
# 증상
WARNING: You are using pip version 20.0.0; however, version 23.2.0 is available.

# 해결
python -m pip install --upgrade pip

# Windows에서 실패하면
python -m pip install --upgrade pip --user
```

### 문제 3: 패키지 충돌

```bash
# 증상
ERROR: package-a 2.0.0 has requirement package-b<2.0.0, but you have package-b 2.1.0.

# 해결 1: 특정 버전으로 다운그레이드
pip install package-b==1.9.0

# 해결 2: 호환되는 버전 찾기
pip install package-a package-b --upgrade

# 해결 3: 새 가상환경에서 재설치
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 문제 4: SSL 인증서 오류

```bash
# 증상
SSL: CERTIFICATE_VERIFY_FAILED

# 임시 해결 (보안상 비권장)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org requests

# 올바른 해결
# 1. certifi 업그레이드
pip install --upgrade certifi

# 2. 시스템 인증서 업데이트
# Mac: Install Certificates.command 실행
# Windows: certmgr.msc로 인증서 관리
```

### 문제 5: 의존성 지옥 (Dependency Hell)

```bash
# 문제: 복잡한 의존성 충돌

# 해결책 1: pip-tools 사용
pip install pip-tools

# requirements.in (느슨한 버전)
django>=4.0
requests

# 컴파일 (정확한 버전 생성)
pip-compile requirements.in
# → requirements.txt 생성

# 해결책 2: Poetry 사용 (더 나은 의존성 관리)
pip install poetry
poetry init
poetry add django requests
```

## 8. pip 대안 도구

### pip-tools

```bash
# 설치
pip install pip-tools

# requirements.in 작성
django>=4.0
requests

# 정확한 버전 고정 파일 생성
pip-compile requirements.in

# 동기화
pip-sync requirements.txt
```

### Poetry (현대적인 패키지 관리)

```bash
# 설치
pip install poetry

# 프로젝트 초기화
poetry init

# 패키지 추가
poetry add requests django

# 개발 의존성 추가
poetry add --dev pytest black

# 설치
poetry install

# 가상환경 활성화
poetry shell
```

### pipenv (pip + virtualenv)

```bash
# 설치
pip install pipenv

# 패키지 설치 (자동으로 가상환경 생성)
pipenv install requests django

# 개발 의존성
pipenv install --dev pytest

# 가상환경 활성화
pipenv shell

# 실행
pipenv run python script.py
```

### uv (🔥 최신 트렌드, 초고속!)

**uv**는 Rust로 작성된 차세대 Python 패키지 관리자로, **pip보다 10-100배 빠른** 성능을 자랑합니다. Astral(ruff 개발사)에서 개발했습니다.

**주요 특징:**
- ⚡ 극도로 빠른 속도 (Rust 기반)
- 🔄 pip, pip-tools, virtualenv를 하나로 통합
- 📦 의존성 해결 속도 10-100배 향상
- 🎯 pyproject.toml 완벽 지원
- 🔒 락 파일(uv.lock) 자동 생성

```bash
# 설치 (pip로)
pip install uv

# 또는 공식 설치 스크립트 (권장)
curl -LsSf https://astral.sh/uv/install.sh | sh  # Mac/Linux
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# 가상환경 생성 (매우 빠름!)
uv venv

# 활성화
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# 패키지 설치 (pip보다 훨씬 빠름)
uv pip install requests django

# requirements.txt에서 설치
uv pip install -r requirements.txt

# 동기화 (pip-sync 역할)
uv pip sync requirements.txt

# pip compile 대체 (매우 빠름)
uv pip compile requirements.in -o requirements.txt

# 프로젝트 초기화
uv init myproject
cd myproject

# 의존성 추가
uv add requests django

# 개발 의존성 추가
uv add --dev pytest black

# 실행
uv run python script.py

# Python 버전 설치도 가능!
uv python install 3.11
uv python install 3.12
```

**성능 비교:**
```bash
# pip: 30-60초
pip install -r requirements.txt

# uv: 1-3초
uv pip install -r requirements.txt

# 🚀 10-100배 빠름!
```

**pyproject.toml 지원:**
```toml
# pyproject.toml
[project]
name = "myproject"
version = "0.1.0"
dependencies = [
    "django>=4.2",
    "requests>=2.31",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
]
```

```bash
# pyproject.toml 기반 설치
uv pip install -e .        # 프로젝트 의존성
uv pip install -e ".[dev]" # 개발 의존성 포함
```

**실무 사용 예제:**
```bash
# 1. 프로젝트 시작
uv init myproject
cd myproject

# 2. 가상환경 생성 (초고속)
uv venv

# 3. 활성화
source .venv/bin/activate

# 4. 패키지 설치 (초고속)
uv pip install django djangorestframework celery

# 5. 개발 도구 설치
uv pip install pytest black ruff

# 6. requirements.txt 생성
uv pip freeze > requirements.txt

# 또는 uv.lock 사용 (권장)
uv lock
```

**왜 uv를 사용해야 하나?**
- ✅ 압도적인 속도 (CI/CD 시간 단축)
- ✅ 메모리 효율적
- ✅ pip, pip-tools 완벽 호환
- ✅ 활발한 개발 (Astral 지원)
- ✅ 현대적인 도구 (pyproject.toml 우선)

**2024년 기준 추천 순위:**
1. **uv** - 속도가 중요하고, 최신 도구 선호
2. **Poetry** - 의존성 관리가 복잡한 프로젝트
3. **pip + venv** - 전통적이고 안정적
4. **pip-tools** - requirements.txt 기반 워크플로우

## 9. 실전 예제

### Django 프로젝트 설정

```bash
# 1. 프로젝트 디렉토리 생성
mkdir myproject
cd myproject

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate

# 3. pip 업그레이드
pip install --upgrade pip

# 4. Django 및 필수 패키지 설치
pip install django djangorestframework psycopg2-binary celery redis

# 5. 개발 도구 설치
pip install black flake8 pytest pytest-django

# 6. requirements 저장
mkdir requirements
pip freeze > requirements/base.txt

# 7. 프로덕션/개발 분리
echo "-r base.txt" > requirements/production.txt
echo "gunicorn==21.2.0" >> requirements/production.txt

echo "-r base.txt" > requirements/development.txt
echo "django-debug-toolbar==4.1.0" >> requirements/development.txt
```

### 기존 프로젝트 클론 후 설정

```bash
# 1. 저장소 클론
git clone https://github.com/user/project.git
cd project

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 개발 서버 실행
python manage.py runserver
```

### 패키지 배포 준비

```bash
# 1. setup.py 작성
# (생략)

# 2. 빌드 도구 설치
pip install build twine

# 3. 패키지 빌드
python -m build

# 4. TestPyPI에 업로드 (테스트)
twine upload --repository testpypi dist/*

# 5. PyPI에 업로드 (실제 배포)
twine upload dist/*
```

## 10. pip vs pip3 vs python -m pip

```bash
# pip
pip install requests
# → 시스템의 기본 Python pip (애매함)

# pip3
pip3 install requests
# → Python 3 전용 pip (명확함)

# python -m pip (가장 권장)
python -m pip install requests
# → 현재 실행 중인 Python의 pip (가장 명확함)

# 특정 버전 명시
python3.11 -m pip install requests
python3.12 -m pip install requests
```

**왜 `python -m pip`가 좋은가?**
- 어떤 Python의 pip인지 명확
- 가상환경에서 더 안전
- 스크립트에서 일관성 보장

## 핵심 요약

### 필수 명령어 TOP 10

```bash
# 1. 설치
pip install requests

# 2. 특정 버전 설치
pip install django==4.2.0

# 3. requirements.txt에서 설치
pip install -r requirements.txt

# 4. 업그레이드
pip install --upgrade pip

# 5. 제거
pip uninstall requests

# 6. 목록 확인
pip list

# 7. 정확한 버전 목록
pip freeze

# 8. 패키지 정보
pip show requests

# 9. 오래된 패키지 확인
pip list --outdated

# 10. requirements.txt 생성
pip freeze > requirements.txt
```

### 실무 워크플로우

```bash
# 새 프로젝트 시작
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install django pytest black
pip freeze > requirements.txt

# 기존 프로젝트 작업
git clone <repo>
cd <repo>
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 베스트 프랙티스 체크리스트

```markdown
✅ 항상 가상환경 사용
✅ requirements.txt 버전 고정
✅ 환경별 requirements 분리
✅ python -m pip 사용
✅ .gitignore에 venv/ 추가
✅ 정기적으로 패키지 업데이트
✅ 보안 취약점 확인 (pip-audit)
```

### 주의사항

**❌ 하지 말아야 할 것:**
- `sudo pip install` (시스템 오염)
- 전역 환경에 설치
- requirements.txt 없이 배포
- 버전 고정 없이 프로덕션 배포

**✅ 해야 할 것:**
- 가상환경 사용
- 버전 명시
- requirements.txt 관리
- 정기적인 업데이트

Python 패키지 관리의 시작과 끝은 **가상환경 + pip + requirements.txt** 입니다!

---

## 출처

- [pip 공식 문서](https://pip.pypa.io/en/stable/)
- [Python venv 공식 문서](https://docs.python.org/3/library/venv.html)
- [uv 공식 문서](https://docs.astral.sh/uv/)
