#!/bin/bash

# .env 파일 읽기
while IFS='=' read -r key value; do
    if [[ $key == "HADOOP_VERSION" ]]; then
        HADOOP_VERSION=$value
        echo "$key=$value"
    elif [[ $key == "SPARK_VERSION" ]]; then
        SPARK_VERSION=$value
        echo "$key=$value"
    elif [[ $key == "ZOOKEEPER_VERSION" ]]; then
        ZOOKEEPER_VERSION=$value
        echo "$key=$value"
    fi
done < ../.env

# package urls
# https://downloads.apache.org/hadoop/common/hadoop-3.4.2/ (Apache 패키지 다운로드 공식)
# lean 버전 출시 (AWS SDK 제외 버전)

# 테스트 이력
# 2025-09-23 최종 확인 (SPARK=3.5.6, HADOOP=3.3.4 수정 말고 그대로 사용할 것, 아래 패키지 외 필요 없음)
# 2025-09-26 최종 확인 (SPARK-without-hadoop=3.5.6, HADOOP=3.3.6 적용 가능, Airflow 통해서 rds_to_iceberg 동작 확인)
# 2026-01-30 최종 확인 (SPARK=4.0.1, HADOOP=3.4.2-lean 적용 가능, bundle-2.29.52.jar 필요)

declare -a package_urls=(
    "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}-lean.tar.gz"
    "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}-aarch64-lean.tar.gz"
    "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-without-hadoop.tgz"
    "https://archive.apache.org/dist/zookeeper/zookeeper-${ZOOKEEPER_VERSION}/apache-zookeeper-${ZOOKEEPER_VERSION}-bin.tar.gz"
)


declare -a packages=()

for url in "${package_urls[@]}"; do
    filename=$(basename "$url")
    packages+=("$filename")
done

for (( i=0; i<${#package_urls[@]}; i++ )); do
    if [ -f "${packages[$i]}" ]; then
        echo "${packages[$i]} ... existed"
    else
        wget "${package_urls[$i]}" -O "${packages[$i]}"
    fi
done
