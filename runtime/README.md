# Runtime Environment Layer

이 디렉토리는 `Base Image` 위에 애플리케이션 실행에 필요한 언어별 런타임(Language Runtime)을 구축합니다.

소스 컴파일 방식과 멀티 스테이지 빌드 전략을 사용하여 성능 최적화와 이미지 경량화를 동시에 달성하는 것을 목표로 합니다.

---

## 1. 아키텍처 전략 (Architectural Strategy)

### Multi-stage Build 적용

빌드 도구(`gcc`, `make` 등)가 포함된 Builder 이미지와, 실행에 필요한 라이브러리만 포함된 Runtime 이미지를 분리하여 보안 공격 면적을 줄이고 이미지 크기를 최적화합니다.

1.  Builder Stage: 소스 코드 다운로드, 컴파일, 의존성 빌드 수행
2.  Runtime Stage: 컴파일된 아티팩트(`/usr/local`)와 공유 라이브러리(`.so`)만 복사

### PGO & LTO 최적화

Python 등 인터프리터 언어 빌드 시 `Profile Guided Optimization (PGO)` 및 `Link Time Optimization (LTO)` 옵션을 활성화하여 실행 속도를 10~20% 향상시킵니다.

---

## 2. 지원하는 런타임 (Supported Runtimes)

### Python

- 경로: `python/`
- 기반 이미지: `blueriver97/amazonlinux:2023`
- 특징:
  - 소스 코드 컴파일 설치 (원하는 버전의 Python을 명시적으로 제어 가능)
  - 필수 공유 라이브러리(`openssl`, `libffi`, `sqlite` 등) 의존성 해결
  - `.pyc` 파일 생성 방지 및 버퍼링 해제 설정 적용

---

## 3. 환경 변수 설정 (Configuration)

빌드 시 `ARG`를 통해 버전을 제어하고, 실행 시 `.env`를 통해 환경 변수를 주입합니다.

| 변수명           | 설명                    | 예시      |
| :--------------- | :---------------------- | :-------- |
| `PYTHON_VERSION` | 전체 버전 (빌드용)      | `3.11.14` |
| `SHORT_VERSION`  | 단축 버전 (태그/경로용) | `3.11`    |

---

## 4. 빌드 방법 (How to Build)

목적에 따라 두 가지 빌드 전략을 지원합니다. 개발 단계에서는 빠른 빌드를 위해 Standard Build를, 프로덕션 배포 시에는 성능 최적화를 위해 Optimized Build를 권장합니다.

### A. Standard Build (Development)

패키지 매니저(`dnf`)를 통해 사전 빌드된 Python을 설치합니다.

빌드 속도가 빠르며, 기능 개발 및 테스트 용도로 적합합니다.

- 사용 파일: `Dockerfile`
- 설치 방식: OS 기본 저장소 또는 미러를 통한 패키지 설치

  ```bash
  cd runtime/python

  # docker compose를 이용한 간편 빌드 (추천)
  docker compose build --no-cache

  # 또는 docker build 직접 실행
  docker build -t blueriver97/python:3.11 -f Dockerfile .
  ```

### B. Optimized Build (Production)

소스 코드를 직접 컴파일하여 이미지를 생성합니다.

PGO(Profile Guided Optimization) 및 LTO(Link Time Optimization)가 적용되어 런타임 성능이 향상됩니다.

- 사용 파일: `pybuild.Dockerfile`
- 설치 방식: Source Code Compile (Multi-stage build)

  ```bash
  cd runtime/python

  # 빌드 인자(ARG)를 통해 버전 지정 가능
  docker build \
    -t blueriver97/python:3.11-optimized \
    -f pybuild.Dockerfile \
    --build-arg PYTHON_VERSION=3.11.14 \
    .
  ```
