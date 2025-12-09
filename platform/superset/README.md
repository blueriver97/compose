# Apache Superset

### Superset All Configuration

https://github.com/apache/superset/blob/master/superset/config.py

## Build Custom Image

### LDAP 설치를 위한 이미지 빌드

```dockerfile
# how to use
# docker build -t <image name>:<tag name> -f <dockerfile name> [path]

# base image
FROM apache/superset:5.0.0-py311 as build

USER root
# 패키지 업데이트 및 필요한 개발 도구들 설치
RUN apt-get update && apt-get install -y \
    build-essential python3-dev libldap2-dev libsasl2-dev libssl-dev gcc &&\
    apt-get clean

USER superset
WORKDIR /app
```

```bash
docker-compose build
```

### LDAP 연결 테스트 (샘플)

```bash
# ldaps://ldap.example.com:636
ldapsearch -x -H ldaps://ldap.example.com:636 -D "CN=AdminUser,CN=Users,DC=exaple,DC=com" -W -b "DC=example,DC=com" -o TLS_REQCERT=never
```

## Database Connection URLs

### AWS Athena

```plaintext
awsathena+rest://${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}@athena.ap-northeast-2.amazonaws.com?s3_staging_dir=s3://mybucket/athena-result&work_group=primary
```

(주의)

1. Secret Key의 URL 인코딩 (필수) AWS Secret Key에는 종종 /, +, = 같은 특수문자가 포함됩니다. 이 문자들이 URI에 그대로 들어가면 연결 실패가 발생하므로 URL인코딩을 해야합니다.
2. 사용하는 AWS 인증 정보에 S3 쓰기 권한이 있는지 확인합니다.

## 실행

### SUPERSET_SECRET_KEY 설정

- docker/.env 파일 내 SUPERSET_SECRET_KEY 값을 설정해야 superset_init 과정에서 오류 없이 실행됩니다.

```
--------------------------------------------------------------------------------
                                    WARNING
--------------------------------------------------------------------------------
A Default SECRET_KEY was detected, please use superset_config.py to override it.
Use a strong complex alphanumeric string and use a tool to help you generate
a sufficiently random sequence, ex: openssl rand -base64 42
For more info, see: https://superset.apache.org/docs/configuration/configuring-superset#specifying-a-secret_key
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
Refusing to start due to insecure SECRET_KEY
```

- 키 생성

```bash
openssl rand -base64 42
```

### 초기 계정

- 기본 값은 (admin/admin)으로 설정되어 있습니다.
- 변경하고 싶은 경우, ADMIN_PASSWORD 환경변수를 설정한 상태로 Docker Compose를 실행하거나, docker/docker-init.sh 파일 내 값을 수정하여 사용합니다.

```
ADMIN_PASSWORD=xxxx docker-compose up -d
```

### Superset Features Enable

```

```
