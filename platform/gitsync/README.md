# Git Sync

이 구성은 git-sync 이미지를 사용하여 지정된 원격 Git 저장소를 를 로컬 디렉토리와 실시간으로 동기화하는 구성입니다.

Airflow 등 최신 코드를 지속적으로 반영해야 하는 환경에서 Sidecar 패턴이나 독립된 동기화 에이전트로 활용됩니다.

## 1. 사전 요구사항 (Prerequisites)

이 컨테이너를 실행하기 전에 SSH 인증 정보가 호스트 머신의 ./ssh 디렉토리에 올바르게 구성되어 있어야 합니다.

### 1.1 SSH 키 구성 (SSH Key Configuration)

```bash
mkdir -p ~/.ssh
ssh-keygen -t ed25519 -C "" -f ~/.ssh/id_ed25519
chmod 600 ~/.ssh/id_ed25519
ssh-keyscan github.com >> ~/.ssh/known_hosts
```

- 생성된 파일
- `id_ed25519`: 프라이빗 키 (절대 외부 유출 금지)
- `id_ed25519.pub`: 퍼블릭 키 (GitHub 저장소에 미리 등록되어 있어야 동작)

## 2. 구성

| 환경 변수        | 값                   | 설명                                  |
| :--------------- | :------------------- | :------------------------------------ |
| `GITSYNC_REPO`   | `git@github.com:...` | 동기화할 Git 저장소 URL (SSH)         |
| `GITSYNC_REF`    | `main`               | 동기화할 브랜치 명                    |
| `GITSYNC_PERIOD` | `30s`                | 동기화 주기 (기본 30초)               |
| `GITSYNC_ROOT`   | `/git`               | 컨테이너 내부 루트 경로               |
| `GITSYNC_LINK`   | `datalake-iceberg`   | 최신 커밋을 가리키는 심볼릭 링크 이름 |

## 3. 실행

```bash
docker-compose up -d
```

- 동기화된 파일은 호스트의 ./git-data 디렉토리에 저장됩니다.
  - ./git-data/datalake-iceberg: 최신 소스 코드로 연결되는 심볼릭 링크 (이 경로를 사용하십시오)
  - ./git-data/312... (hash): 실제 커밋 ID 기반의 체크아웃 디렉토리

- 다른 애플리케이션(예: Airflow, Jupyter 등)에서 소스 코드를 참조할 때는 ./git-data/datalake-iceberg 경로를 볼륨으로 마운트하여 사용하면 됩니다.

## 5. 트러블슈팅 (Troubleshooting)

### 1. Host key verification failed

~/.ssh/known_hosts 파일이 없거나 GitHub의 키 정보가 올바르지 않은 경우입니다. Known Hosts 파일 생성 단계를 다시 수행하십시오.

### 2. Permission denied (publickey)

~/.ssh/id_ed25519 파일이 올바른 키인지, 그리고 GitHub 저장소의 Deploy Key 또는 사용자 설정에 해당 Public Key가 등록되어 있는지 확인하십시오.

호스트에서 ~/.ssh/id_ed25519 파일의 권한이 600인지 확인하십시오.

### 3. `./git: permission denied` 등 파일 쓰기 에러

git-sync 컨테이너는 보안상 root가 아닌 특정 사용자(UID 65533)로 실행될 수 있습니다.

호스트의 ./git-data 디렉토리에 쓰기 권한을 부여해야 합니다.

테스트를 위해 임시로 권한을 엽니다: chmod 777 ./git-data
