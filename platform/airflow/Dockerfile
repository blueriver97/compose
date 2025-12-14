FROM apache/airflow:3.1.5-python3.11 AS build

USER root
WORKDIR /opt

COPY requirements.txt /opt

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
