# GitLab & GitLab Runner

이 디렉토리는 Docker Compose를 사용하여 GitLab Community Edition (CE) 및 CI/CD 파이프라인 처리를 위한 GitLab Runner를 구축하는 구성을 담고 있습니다.

## 구성 요소 (Components)

---

| 서비스명      | 파일명            | 설명                                               | 포트       |
| ------------- | ----------------- | -------------------------------------------------- | ---------- |
| gitlab        | compose.yml       | 소스 코드 저장소 및 DevOps 플랫폼 (GitLab CE 18.x) | 8888 (Web) |
| gitlab-runner | gitlab-runner.yml | CI/CD 파이프라인을 실행하는 에이전트               | 8093       |

## 사전 준비 (Prerequisites)

---

실행 전 .env 파일에 초기 루트 비밀번호를 설정해야 합니다.

```
# .env 예시
# 보안을 위해 복잡한 문자열 사용 권장 (openssl rand -base64 42 등 활용)
GITLAB_ROOT_PASSWORD=YourStrongPassword123!
```

주의: 비밀번호가 너무 간단하거나 사전적인 단어일 경우 GitLab 초기화 시 계정 생성이 실패할 수 있습니다. (하단 트러블슈팅 참조)

## 실행 방법 (Usage)

---

GitLab 서버와 Runner는 각각 독립적인 Compose 파일로 관리되므로, 필요에 따라 실행합니다.

### GitLab 서버 실행

```
docker compose -f compose.yml up -d
```

실행 후 브라우저에서 http://localhost:8888로 접속할 수 있습니다. (초기 부팅에 시간이 다소 소요될 수 있습니다.)

### GitLab Runner 실행

```
docker compose -f gitlab-runner.yml up -d
```

Runner 컨테이너를 실행한 후, GitLab 서버와 연동하기 위해 등록(Register) 절차를 거쳐야 합니다.
GitLab 접속 (http://localhost:8888) -> Admin Area -> CI/CD -> Runners 메뉴에서 Registration Token을 확인합니다.

```bash
docker exec -it gitlab-runner gitlab-runner register
```

입력 프롬프트에 따른 설정 값

- **GitLab instance URL**: http://gitlab:8888

주의: Docker 네트워크 내부 통신이므로 localhost가 아닌 서비스명 gitlab을 사용해야 합니다.

- **Registration token**: (1번 단계에서 확인한 토큰 입력)

- **Description**: docker-runner (임의 지정)

- **Tags**: (엔터로 생략 가능)

- **Maintenance** note: (엔터로 생략 가능)

- **Executor**: docker

- **Default Docker image**: alpine:latest (또는 ubuntu 등 기본 이미지)

## 트러블슈팅 (Troubleshooting)

---

### Could not create the default administrator account

- GitLab이 처음 뜰 때 DB에 root 계정을 생성(Seed)하려고 시도했지만, 초기 비밀번호가 너무 간단해 계정 생성 스크립트가 실패하여 발생함.
- .env 파일에 작성한 GITLAB_ROOT_PASSWORD 값을 복잡하게 설정하고, 볼륨 삭제 후 재시작 진행.
- 사전적 단어, 연속된 숫자, 혹은 너무 짧은 문자열은 사용할 수 없음.

```plaintext
gitlab         | Could not create the default administrator account:
gitlab         |
gitlab         | --> Password must not contain commonly used combinations of words and letters
```

1
