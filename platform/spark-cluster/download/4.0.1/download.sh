#!/bin/bash

# .env 파일 읽기
while IFS='=' read -r key value; do
    if [[ $key == "HADOOP_VERSION" ]]; then
        HADOOP_VERSION=$value
        echo "$key=$value"
    elif [[ $key == "SPARK_VERSION" ]]; then
        SPARK_VERSION=$value
        SPARK_SHORT_VERSION=$(echo "$value" | awk -F. '{print $1 "." $2}')
        echo "$key=$value"
    elif [[ $key == "ZOOKEEPER_VERSION" ]]; then
        ZOOKEEPER_VERSION=$value
        echo "$key=$value"
    elif [[ $key == "ICEBERG_VERSION" ]]; then
        ICEBERG_VERSION=$value
        echo "$key=$value"
    fi
done < ../../.env

# kafka-clients 버전은 카프카 버전을 따라감. (3.9.1 버전 사용, KAFKA 4.0.0 호환됨)
# 2025-11-17:
# - commons-pool2 버전은 현재 최신 버전을 사용함. (2.12.1)
# - ICEBERG는 1.10.0이 최신버전 사용
# - Database, Kafka, Iceberg 연동 관련해서 아래 패키지 외 필요 없음.
# 2025-11-21: iceberg-aws-bundle 대신 iceberg-aws 의존성을 사용하는 이유에 대해서 README.md 6번 내용 참조.
# 2025-12-18: Apache Polaris 패키지 추가, 아직 Spark 4.0.1 대응 버전이 없음.
# 2026-02-25: OpenLineage 패키지 추가, spark with hadoop 버전 사용해서 테스트 함.
declare -a jar_urls=(
    # Hadoop 3.4.2 (Spark에 포함된 기존 버전은 Dockerfile에서 제거, Hadoop 버전에 맞는 Jar 직접 추가)
    "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client-api/${HADOOP_VERSION}/hadoop-client-api-${HADOOP_VERSION}.jar"
    "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client-runtime/${HADOOP_VERSION}/hadoop-client-runtime-${HADOOP_VERSION}.jar"
    # Spark Log4j/slf4j
    "https://repo1.maven.org/maven2/org/apache/logging/log4j/log4j-slf4j-impl/2.24.3/log4j-slf4j-impl-2.24.3.jar"
    # AWS SDK v2
    "https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar"
    # Iceberg / Kafka / JDBC
    "https://repo1.maven.org/maven2/org/apache/spark/spark-connect_2.13/${SPARK_VERSION}/spark-connect_2.13-${SPARK_VERSION}.jar"
    "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws/${ICEBERG_VERSION}/iceberg-aws-${ICEBERG_VERSION}.jar"
    "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-${SPARK_SHORT_VERSION}_2.13/${ICEBERG_VERSION}/iceberg-spark-runtime-${SPARK_SHORT_VERSION}_2.13-${ICEBERG_VERSION}.jar"
    "https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.13/${SPARK_VERSION}/spark-sql-kafka-0-10_2.13-${SPARK_VERSION}.jar"
    "https://repo1.maven.org/maven2/org/apache/spark/spark-streaming-kafka-0-10_2.13/${SPARK_VERSION}/spark-streaming-kafka-0-10_2.13-${SPARK_VERSION}.jar"
    "https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.13/${SPARK_VERSION}/spark-token-provider-kafka-0-10_2.13-${SPARK_VERSION}.jar"
    "https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.13/${SPARK_VERSION}/spark-avro_2.13-${SPARK_VERSION}.jar"
    "https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.9.1/kafka-clients-3.9.1.jar"
    "https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.12.1/commons-pool2-2.12.1.jar"
    "https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/12.2.0.jre11/mssql-jdbc-12.2.0.jre11.jar"
    "https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.33/mysql-connector-java-8.0.33.jar"
    # Polaris
    "https://repo1.maven.org/maven2/org/apache/polaris/polaris-spark-3.5_2.13/1.2.0-incubating/polaris-spark-3.5_2.13-1.2.0-incubating.jar"
    "https://repo1.maven.org/maven2/org/apache/polaris/polaris-core/1.2.0-incubating/polaris-core-1.2.0-incubating.jar"
    # OpenLineage
    "https://repo1.maven.org/maven2/io/openlineage/openlineage-spark_2.13/1.44.0/openlineage-spark_2.13-1.44.0.jar"
    "https://repo1.maven.org/maven2/org/apache/spark/spark-hive_2.13/${SPARK_VERSION}/spark-hive_2.13-${SPARK_VERSION}.jar"
)


declare -a jars=()

for url in "${jar_urls[@]}"; do
    filename=$(basename "$url")
    jars+=("$filename")
done

for (( i=0; i<${#jar_urls[@]}; i++ )); do
    if [ -f "${jars[$i]}" ]; then
        echo "${jars[$i]} ... existed"
    else
        wget "${jar_urls[$i]}" -O "${jars[$i]}"
    fi
done
