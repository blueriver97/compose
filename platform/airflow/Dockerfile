# ----------------------------------------------------------------
# 1. Builder Stage: 의존성 다운로드 및 빌드
# ----------------------------------------------------------------
FROM apache/airflow:3.1.5-python3.11 AS build
ARG SPARK_VERSION
USER root
WORKDIR /opt

COPY requirements.txt /opt
COPY download/spark-$SPARK_VERSION-bin-hadoop3.tgz /opt

ENV HADOOP_HOME=/opt/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV SPARK_HOME=/opt/spark
ENV SPARK_CONF_DIR=$SPARK_HOME/conf
ENV PYSPARK_PYTHON=./environment/bin/python

# Apache Spark with hadoop
# 2025-09-23 최종 확인 => 반드시 with-hadoop3 버전 사용해야 함, without-hadoop 버전은 따로 설정할 jar 의존성이 너무 복잡함
RUN umask 0002 &&\
    tar -zxvf spark-$SPARK_VERSION-bin-hadoop3.tgz &&\
    ln -s spark-$SPARK_VERSION-bin-hadoop3 spark &&\
    rm -rf spark-$SPARK_VERSION-bin-hadoop3.tgz
COPY download/*.jar /opt/spark/jars
COPY config/spark /opt/spark/conf
COPY config/hadoop /opt/hadoop/etc/hadoop

# ----------------------------------------------------------------
# 2. Final Stage: 최종 이미지 생성
# ----------------------------------------------------------------
FROM apache/airflow:3.1.5-python3.11
COPY --from=build /opt/hadoop /opt/hadoop
COPY --from=build /opt/spark /opt/spark
COPY --from=build /opt/requirements.txt /opt/requirements.txt
WORKDIR /opt
USER root

RUN umask 0002 &&\
    apt-get update &&\
    apt-get install -y --no-install-recommends \
         openjdk-17-jre-headless procps curl unzip wget git vim &&\
    apt-get autoremove -yqq --purge &&\
    apt-get clean &&\
    rm -rf /var/lib/apt/lists/* &&\
    echo "export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))" >> /root/.bashrc &&\
    chown -R airflow:root /opt

USER airflow
WORKDIR /opt

RUN umask 0002 &&\
    pip install -U pip setuptools wheel &&\
    pip install --no-cache-dir -r /opt/requirements.txt &&\
    echo "export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))" >> /home/airflow/.bashrc
