# how to use
# docker build -t <image name>:<tag name> -f <dockerfile name> [path]

ARG DATAHUB_VERSION

# base image
FROM acryldata/datahub-actions:${DATAHUB_VERSION}-slim

USER root

SHELL ["/bin/bash", "-c"]
# 패키지 업데이트 및 필요한 개발 도구들 설치
RUN /datahub-ingestion/.venv/bin/python3 -m pip install -U pip setuptools wheel &&\
    /datahub-ingestion/.venv/bin/python3 -m pip install acryl-datahub[all] &&\
    /datahub-ingestion/.venv/bin/python3 -m pip cache purge

# /datahub-ingestion/.venv/bin/python3 -m pip install acryl-datahub[mysql,dbt,kafka,superset,airflow,ldap] &&\
