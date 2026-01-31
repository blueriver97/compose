#!/bin/bash

# .env 파일 읽기
while IFS='=' read -r key value; do
    if [[ $key == "SPARK_VERSION" ]]; then
        SPARK_VERSION=$value
        echo "$key=$value"
    elif [[ $key == "HADOOP_VERSION" ]]; then
        HADOOP_VERSION=$value
        echo "$key=$value"
    fi
done < ../.env


# (2026-01-31) Yarn 클러스터를 구성하는 Hadoop 버전와 PySpark 내 hadoop 버전이 맞아야 함.
# spark-without-hadoop 버전의 경우, 따로 설치할 jar 의존성이 너무 복잡해서 반드시 spark-with-hadoop3 버전을 사용해야 함.
# -----------------------------
# hadoop-client-api-x.y.z.jar
# hadoop-client-runtime-x.y.z.jar
# hadoop-aws-x.y.z.jar
# -----------------------------
# apache-airflow-providers-apache-spark 버전에 따라 pyspark 버전이 결정됨.
# apache-airflow-providers-apache-spark==5.5.0 => pyspark==4.1.1(hadoop-3.4.2)
if [[ $HADOOP_VERSION == "3.4.2" ]]; then
    AWS_SDK_VERSION="2.29.52"
fi
declare -a package_urls=(
    "https://archive.apache.org/dist/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop3.tgz"
    "https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/$AWS_SDK_VERSION/bundle-$AWS_SDK_VERSION.jar"
    "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/$HADOOP_VERSION/hadoop-aws-$HADOOP_VERSION.jar"
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
