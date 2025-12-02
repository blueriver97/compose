# Nexus Repository Manager 3 설정 및 클라이언트 연동 가이드

이 문서는 Docker Compose를 사용하여 Sonatype Nexus 3를 구축하고, 내부망에 격리된 클라이언트(`inter-pc`)가 Nexus를 통해 외부 패키지(APT, PyPI, Docker)를 가져올
수 있도록 설정하는 방법을 설명합니다.

## 1. 사전 준비 및 실행

`docker-compose.yml` 파일이 있는 디렉토리에서 다음 명령어로 서비스를 실행합니다.

```bash
docker-compose up -d
```

## 2. Nexus 초기 설정

- Nexus 컨테이너 내부에서 초기 관리자 비밀번호를 확인합니다. 아래 명령어로 출력된 문자열이 초기 비밀번호입니다.
- 초기 계정은 admin 입니다.

```bash
docker exec -it nexus cat /nexus-data/admin.password
```

- 브라우저에서 `http://localhost:8081` 접속 후, 로그인(admin/초기 비밀번호)을 하면 비밀번호를 변경합니다.
- 초기화 과정에서 Anonymous Access를 활성화합니다. (보안을 위해 Disable 권장)

## 3. 저장소(Repository) 생성 가이드

### APT Proxy 설정

- ⚠️ CPU 아키텍처 확인 (Intel/AMD, ARM/Apple Silicon, Remote storage 주소가 다름)
- Settings → Repositories → Create repository를 클릭하여 각 저장소를 생성합니다.
  - APT Proxy
    - Recipe: apt(proxy)
    - Name: apt-proxy
    - Distribution: noble (Ubuntu 24.04 Codename) / jammy(22.04) / focal(20.04) 등
    - Flat: 체크 해제 (기본값)
    - Remote storage
      - (Intel/AMD) Arch: https://archive.ubuntu.com/ubuntu/
      - (ARM/Apple Silicon) Arch: https://ports.ubuntu.com/ubuntu-ports/
    - SSL/TLS Certificate
      - [View certificate] 버튼 클릭 → [Add to truststore] 클릭
      - Use certificates stored in the Nexus Repository truststore...: 체크
    - HTTP Client Settings: Auto-block 해제

  - APT Security Proxy
    - Recipe: apt(security proxy)
    - Name: apt-security-proxy
    - Distribution: noble (Ubuntu 24.04 Codename) / jammy(22.04) / focal(20.04) 등
    - Flat: 체크 해제 (기본값)
    - Remote storage
      - (Intel/AMD) Arch: https://security.ubuntu.com/ubuntu/
      - (ARM/Apple Silicon) Arch: https://ports.ubuntu.com/ubuntu-ports/
      - (ARM 환경은 보안 업데이트도 ports 저장소에서 통합 관리)
    - SSL/TLS Certificate
      - [View certificate] 버튼 클릭 → [Add to truststore] 클릭
      - Use certificates stored in the Nexus Repository truststore...: 체크
    - HTTP Client Settings: Auto-block 해제

### Amazon Linux 2023 Proxy 설정

- AL2023은 EPEL을 지원하지 않으며, 자체 저장소를 사용합니다.
- AL2023은 RHEL/CentOS 기반이 아니며 Fedora를 베이스로 하는 독자적인 OS입니다.
- Settings → Repositories → Create repository를 클릭하여 각 저장소를 생성합니다.
  - Amazon Linux 2023 Proxy
    - Recipe: yum (proxy)
    - Name: al2023-proxy
    - Remote storage: https://cdn.amazonlinux.com
    - SSL/TLS Certificate
      - [View certificate] 버튼 클릭 → [Add to truststore] 클릭
      - Use certificates stored in the Nexus Repository truststore...: 체크
    - HTTP Client Settings: Auto-block 해제

### PyPI (Python) Proxy 설정

- Settings → Repositories → Create repository를 클릭하여 각 저장소를 생성합니다.
  - PyPI Proxy
    - Recipe: pypi (proxy) 선택
    - Name: pypi-proxy
    - Remote storage: https://pypi.org
    - SSL/TLS Certificate:
      - [View certificate] 버튼 클릭 → [Add to truststore] 클릭
      - Use certificates stored in the Nexus Repository truststore...: 체크
    - HTTP Client Settings: Auto-block 해제

### Docker Proxy 설정

- Settings → Repositories → Create repository를 클릭하여 각 저장소를 생성합니다.
  - Docker Proxy
    - Recipe: docker (proxy) 선택
    - Name: docker-proxy
    - Remote storage: https://registry-1.docker.io
    - Docker Index: Use Docker Hub 선택
    - SSL/TLS Certificate:
      - [View certificate] 버튼 클릭 → [Add to truststore] 클릭
      - Use certificates stored in the Nexus Repository truststore...: 체크
    - HTTP Client Settings: Auto-block 해제

### Helm Proxy 설정

- 개별 저장소마다 등록 필요
- Settings → Repositories → Create repository를 클릭하여 각 저장소를 생성합니다.
  - Bitnami
    - Recipe: helm (proxy) 선택
    - Name: helm-proxy
    - Remote storage: https://charts.bitnami.com/bitnami
      - SSL/TLS Certificate:
        - [View certificate] 버튼 클릭 → [Add to truststore] 클릭
        - Use certificates stored in the Nexus Repository truststore...: 체크
    - HTTP Client Settings: Auto-block 해제

## 클라이언트 설정

### APT 설정 (Ubuntu)

- apt-proxy와 apt-security-proxy 두 주소를 모두 바라보도록 설정합니다.

```bash
# 기존 파일 백업
mv /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources.bak

# 새 설정 파일 생성
cat <<EOF > /etc/apt/sources.list.d/nexus.sources
# 1. Main Packages (apt-proxy or apt-proxy-arm -> noble)
Types: deb
URIs: http://nexus:8081/repository/apt-proxy-arm/
Suites: noble
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg

# 2. Security Packages (apt-security-proxy or apt-security-proxy-arm -> noble-security)
Types: deb
URIs: http://nexus:8081/repository/apt-security-proxy-arm/
Suites: noble-security
Components: main restricted universe multiverse
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
EOF
```

- Nexus 인증 사용 시

```bash
# 인증 정보 설정 파일 생성
# machine [호스트명]:[포트] login [아이디] password [비밀번호] 형식
cat <<EOF > /etc/apt/auth.conf
machine nexus:8081 login admin password $NEXUS_ADMIN_PASSWORD
EOF

# 권한 설정
chmod 600 /etc/apt/auth.conf
```

- 테스트

```bash
apt update
apt install curl -y
```

### Amazon Linux 2023 설정

- AL2023은 $releasever 변수를 사용하여 URL을 동적으로 생성합니다.
  - 버전 불일치를 막기 위한 'Deterministic Upgrades' 정책으로 인해, URL에 해시값(GUID)으로 된 경로를 강제합니다.
  - 인터넷이 가능한 PC에서 현재 사용하는 GUID 값을 찾아 적용해야 합니다.
    ```bash
    curl https://cdn.amazonlinux.com/al2023/core/mirrors/latest/aarch64/mirror.list
    # https://cdn.amazonlinux.com/al2023/core/guids/8c978296cb2b51259bcd168169eb5e8193568ea4590c79d76d9def8d00b49b22/aarch64/%
    # GUID: 8c978296cb2b51259bcd168169eb5e8193568ea4590c79d76d9def8d00b49b22
    ```
- 기본 mirrorlist 방식을 끄고 Nexus의 baseurl로 고정해야 합니다.

```bash
# 기존 repo 파일 백업
mv /etc/yum.repos.d/amazonlinux.repo /etc/yum.repos.d/amazonlinux.repo.bak

# Nexus를 바라보는 새 repo 파일 생성
# AL2023의 저장소 구조: /al2023/core/mirrors/$releasever/$basearch/mirror.list
# 하지만 Nexus Proxy를 통하므로 바로 repodata가 있는 경로를 지정하는 것이 안전합니다.
# 아래는 'latest' 버전을 기준으로 한 예시입니다.

cat <<EOF > /etc/yum.repos.d/nexus-al2023.repo
[nexus-core]
name=Nexus AL2023 Core
# Nexus URL 뒤에 실제 CDN 경로를 붙여줍니다.
baseurl=http://nexus:8081/repository/al2023-proxy/al2023/core/guids/[확인한_GUID]/x86_64/
enabled=1
gpgcheck=0
priority=1

# --- 인증 정보 추가 ---
# username=admin
# password=$NEXUS_ADMIN_PASSWORD
EOF
# (참고) 만약 ARM(Mac M1/M2) 환경이라면 x86_64 대신 aarch64를 사용하세요.
# baseurl=http://nexus:8081/repository/al2023-proxy/al2023/core/guids/[확인한_GUID]/aarch64/

# 2파일 권한 보안 설정 (비밀번호가 들어있으므로 root만 읽을 수 있게)
chmod 600 /etc/yum.repos.d/nexus-al2023.repo
```

- 테스트

```bash
dnf clean all
dnf repolist
dnf install htop -y
```

### PyPI 설정 (Python)

- pip가 Nexus를 바라보도록 설정합니다.

```bash
# 시스템 파이썬 보호 조치 해제 (원래는 venv 사용 필수)
# 이 파일을 삭제하면 --break-system-packages 옵션 없이도 pip 사용 가능
rm /usr/lib/python3.*/EXTERNALLY-MANAGED

# pip 설정 디렉토리 생성
mkdir -p /etc/pip

# Nexus 연결 설정
cat <<EOF > /etc/pip.conf
[global]
index-url = http://nexus:8081/repository/pypi-proxy/simple
trusted-host = nexus
EOF
```

- Nexus 인증 사용 시

```bash
cat <<EOF > /etc/pip.conf
[global]
index-url = http://admin:$NEXUS_ADMIN_PASSWORD@nexus:8081/repository/pypi-proxy/simple
trusted-host = nexus
root-user-action = ignore
EOF
```

- 테스트

```bash
# --ignore-installed 옵션
# apt가 설치한 구버전을 삭제하려고 시도하지 않고, 새로운 버전을 덮어씌워 설치하도록 강제하는 옵션
pip install -U pip setuptools wheel --ignore-installed
pip install requests
```

### Docker 설정

- /etc/docker/daemon.json을 수정하여 Nexus를 레지스트리 미러로 등록합니다.

```bash
mkdir -p /etc/docker

# insecure-registries: HTTPS 인증서 문제 무시 (사설 인증서 사용 시)
# registry-mirrors: docker pull 시 Nexus를 거치도록 설정
cat <<EOF > /etc/docker/daemon.json
{
  "insecure-registries" : ["nexus:8081"],
  "registry-mirrors": ["http://nexus:8081"]
}
EOF
```

- Nexus 인증 사용 시

```bash
docker login nexus:8081 -u admin -p $NEXUS_ADMIN_PASSWORD
```

- 테스트

```bash
# Docker 설치 (Nexus apt-proxy를 통한 설치) 및 Docker Daemon 실행
apt update
apt install -y docker.io docker-compose
systemctl start docker

docker pull nginx:latest
```

### Helm 설정

- apt-proxy를 통해 Helm 클라이언트를 설치하고, Nexus의 helm-proxy를 등록합니다.

```bash
# Helm 클라이언트 설치 (Nexus apt-proxy를 통해 다운로드됨)
apt update && apt install -y helm

# Nexus 저장소 등록 (인증 사용 시, 계정 정보 포함)
# 형식: helm repo add [별칭] [Nexus주소] --username [ID] --password [PW]
helm repo add bitnami http://nexus:8081/repository/helm-proxy-bitnami/ --username admin --password $NEXUS_ADMIN_PASSWORD

# 저장소 업데이트 및 확인
helm repo update
helm search repo bitnami/nginx
```

## 트러블슈팅

### 401 Unauthorized

- Nexus의 Anonymous Access가 켜져 있는지 확인하거나, 클라이언트 설정 파일에 ID/PW를 명시해야 합니다.
