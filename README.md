# Docker Compose Collection

이 저장소는 데이터 엔지니어링 및 DevOps 환경 구축을 위한 다양한 Docker Compose 스택과 유틸리티를 모아둔 모노레포입니다.
Base OS 이미지부터 데이터베이스, 모니터링, 플랫폼 서비스까지 모듈화하여 관리합니다.

## 1. 디렉토리 구조 (Directory Map)

| 분류           | 서비스 / 모듈  | 경로                          | 설명                                               |
| :------------- | :------------- | :---------------------------- | :------------------------------------------------- |
| **Base**       | OS Images      | [`base/`](./base)             | Ubuntu, Rocky, AmazonLinux 베이스 이미지           |
| **Database**   | RDBMS / NoSQL  | [`database/`](./database)     | MySQL, MSSQL, Redis 및 Data Generator              |
| **Platform**   | Big Data & Ops | [`platform/`](./platform)     | Superset, Iceberg, MinIO, Vault, Nexus, GitSync 등 |
| **Monitoring** | Observability  | [`monitoring/`](./monitoring) | Prometheus, Grafana, VictoriaMetrics, Exporters    |
| **Runtime**    | Language / AI  | [`runtime/`](./runtime)       | Python Runtime, Ollama(LLM)                        |

## 2. 필수 요구 사항 (Prerequisites)

- Docker Desktop or Docker Engine (Compose plugin 포함)
- Python 3.11+ (스크립트 실행용)

## 3. 시작하기 (Getting Started)

각 디렉토리의 README.md를 참조하여 개별 서비스를 실행할 수 있습니다.

## Appendix

### compose 예시

```yml
services:
  ubuntu: # app name
    build:
      dockerfile: ubuntu.Dockerfile
      context: . # Dockerfile location
      args: # arguments for docker build
        - GITHUB_HOST=address
        - GITHUB_ID=username
        - GITHUB_PW=password
    image: "blueriver97/ubuntu:2004" # image name
    container_name: "ubuntu2004"
    cputset: "0,1"
    mem_limit: 4G
    stdin_open: true
    tty: true # 컨테이너가 살아 있어야 할 때
    command: /bin/bash /root/run.sh
    restart: always
    deploy: # for resources
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["0", "1"]
              capabilities: [gpu]
    env_file:
      - environment.env
    ports:
      - "80:80"
    volumes:
      - "app-volume:/root/app"

volumes:
  app-volume:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: "/data/app"
```

### Dockerfile 예시

```docker
# how to use
# docker build -t <image name>:<tag name> -f <dockerfile name> [path]

# base image
FROM ubuntu:20.04

ENV LC_ALL=C.UTF-8
ENV TZ=Asia/Seoul
ARG DEBIAN_FRONTEND=noninteractive

ARG GITHUB_HOST
ARG GITHUB_ID
ARG GITHUB_PW

### base working directory
WORKDIR /root

### install haqe
RUN git clone http://${GITHUB_ID}:${GITHUB_PW}@${GITHUB_HOST}:8888/compose.git &&\
    cd /root/compose &&\
    python3 -m pip install -r requirements.txt &&\
    python3 -m pip install .

### entrypoint script
COPY entrypoint.sh /root
RUN  chmod +x /root/entrypoint.sh


ENTRYPOINT ["/bin/bash", "-c", "/root/entrypoint.sh"]
```
