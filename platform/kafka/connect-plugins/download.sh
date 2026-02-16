#!/bin/bash

# .env 파일 읽기
while IFS='=' read -r key value; do
    if [[ $key == "DEBEZIUM_VERSION" ]]; then
        DEBEZIUM_VERSION=$value
        echo "$key=$value"
    elif [[ $key == "GROOVY_VERSION" ]]; then
        GROOVY_VERSION=$value
        echo "$key=$value"
    elif [[ $key == "ICEBERG_VERSION" ]]; then
        ICEBERG_VERSION=$value
        echo "$key=$value"
    fi
done < ../.env

# 2025-09-26 최종 확인. (Debezium=3.2.3, Groovy=4.0.28)
# 2026-01-26 최종 확인. (Iceberg 1.10.1 추가, Github Release 사용)
declare -a jar_urls=(
  # For Source
  "https://repo1.maven.org/maven2/io/debezium/debezium-connector-mysql/$DEBEZIUM_VERSION.Final/debezium-connector-mysql-$DEBEZIUM_VERSION.Final-plugin.tar.gz"
  "https://repo1.maven.org/maven2/io/debezium/debezium-connector-sqlserver/$DEBEZIUM_VERSION.Final/debezium-connector-sqlserver-$DEBEZIUM_VERSION.Final-plugin.tar.gz"
  "https://repo1.maven.org/maven2/io/debezium/debezium-scripting/$DEBEZIUM_VERSION.Final/debezium-scripting-$DEBEZIUM_VERSION.Final.tar.gz"
  "https://repo1.maven.org/maven2/org/apache/groovy/groovy/$GROOVY_VERSION/groovy-$GROOVY_VERSION.jar"
  "https://repo1.maven.org/maven2/org/apache/groovy/groovy-jsr223/$GROOVY_VERSION/groovy-jsr223-$GROOVY_VERSION.jar"
  "https://repo1.maven.org/maven2/org/apache/groovy/groovy-json/$GROOVY_VERSION/groovy-json-$GROOVY_VERSION.jar"
  # For Sink
  "https://github.com/blueriver97/artifacts/releases/download/iceberg-kafka-connect-runtime/iceberg-kafka-connect-runtime-$ICEBERG_VERSION.zip"
  "https://hub-downloads.confluent.io/api/plugins/confluentinc/kafka-connect-s3/versions/12.0.1/confluentinc-kafka-connect-s3-12.0.1.zip"

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
