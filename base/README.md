# Base Image Layer

이 디렉토리는 프로젝트의 기반이 되는 OS(Operating System) 베이스 이미지를 정의합니다.

팀 내 모든 서비스가 공통적으로 사용하는 OS 설정, 시스템 패키지, 보안 설정, 그리고 셸 환경(Dotfiles)을 표준화하여 관리합니다.

## 1. 목적 (Purpose)

- 모든 컨테이너에서 동일한 셸(`bash`), 에디터(`vim`), 기본 도구(`git`, `curl` 등) 환경을 제공합니다.
- `.bashrc`, `.vimrc`를 내장하여 컨테이너 내부 디버깅 시 로컬과 유사한 편의성을 제공합니다.

## 2. 지원하는 OS (Supported OS)

| OS                | 경로           | Dockerfile                           |
| :---------------- | :------------- | :----------------------------------- |
| Amazon Linux 2023 | `amazonlinux/` | [Dockerfile](amazonlinux/Dockerfile) |
| Rocky Linux 9     | `rockylinux/`  | [Dockerfile](rockylinux/Dockerfile)  |
| Ubuntu 24.04      | `ubuntu/`      | [Dockerfile](ubuntu/Dockerfile)      |

## 3. 주요 포함 패키지 (Pre-installed Packages)

다음 도구들은 모든 Base 이미지에 기본 설치됩니다.

- Core: `git`, `curl`, `wget`, `vim`, `tar`, `tree`
- Network: `net-tools`, `iputils` `ping`, `lsof`
- System: `htop`, `procps`, `findutils`
- Language Runtime: Java 17 (Amazon Corretto / OpenJDK) - 일부 도구 및 Jenkins 에이전트 호환용

## 4. 빌드 및 실행 (Build & Run)

각 OS 디렉토리 내에 `compose.yml`이 포함되어 있어 개별 테스트가 가능합니다.

```bash
# Amazon Linux 2023 빌드 및 실행
cd amazonlinux
docker compose up --build -d

# RockyLinux 9 빌드 및 실행
cd rockylinux
docker compose up --build -d

# Ubuntu 24.04 빌드 및 실행
cd ubuntu
docker compose up --build -d
```
