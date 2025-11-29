# Common Resources

이 문서는 중복을 방지하기 위해 추출된 공통 리소스를 설명하는 `common` 디렉토리의 문서입니다.

# Common Resources

이 디렉토리는 여러 Docker 이미지(Base, Runtime 등)에서 공통적으로 사용되는 스크립트와 설정 파일을 관리합니다.

DRY(Don't Repeat Yourself) 원칙에 따라, 특정 OS나 런타임에 종속되지 않는 로직을 이곳에 중앙화합니다.

## 1. 구성 요소 (Components)

### entrypoint.sh

컨테이너가 시작될 때 실행되는 초기화 스크립트입니다. 주로 SSH 접근 제어와 관련된 보안 설정을 자동화합니다.

- SSH Host Key 생성: `/etc/ssh/ssh_host_rsa_key`가 없을 경우 생성 (서버 신원 보증)
- User Key 생성: `/root/.ssh/id_ed25519` 생성 (클러스터 내 통신용)
- Self-Access 허용: 생성된 공개키를 `authorized_keys`에 등록하여 비밀번호 없는 로컬 접속 허용
- SSH Daemon 실행: 백그라운드에서 `sshd`를 실행 후, Docker CMD로 전달된 메인 프로세스 실행

## 2. 사용법 (Usage)

Dockerfile에서 이 디렉토리의 스크립트를 `COPY`하여 사용합니다.

```dockerfile
# 예시: Dockerfile 내 적용 방법
COPY common/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]
```
