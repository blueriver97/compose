# how to use
# docker build -t <image name>:<tag name> -f <dockerfile name> [path]

# base image
FROM apache/superset:5.0.0-py311 AS build

USER root
# 패키지 업데이트 및 필요한 개발 도구들 설치
RUN apt-get update && apt-get install -y \
    build-essential python3-dev libldap2-dev libsasl2-dev libssl-dev gcc &&\
    apt-get clean

USER superset
WORKDIR /app
